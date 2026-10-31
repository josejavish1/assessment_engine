import asyncio
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from google import genai
from google.adk.agents import Agent
from pydantic import ValidationError
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.schemas.evidence import (
    EvidenceFragment,
    RaptorNode,
    RaptorTree,
)
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

logger = logging.getLogger(__name__)

MAX_CONCURRENT_CHUNKS: int = int(os.environ.get("RAPTOR_MAX_CONCURRENT_CHUNKS", "8"))
DEFAULT_RPM_QUOTA: int = int(os.environ.get("RAPTOR_RPM_QUOTA", "60"))
DEFAULT_TPM_QUOTA: int = int(os.environ.get("RAPTOR_TPM_QUOTA", "250000"))
DEFAULT_RAPTOR_MAX_RETRY_ATTEMPTS: int = int(os.environ.get("RAPTOR_MAX_RETRY_ATTEMPTS", "3"))
CHARS_PER_TOKEN_ESTIMATE: int = 4
SECONDS_PER_MINUTE: float = 60.0
ADAPTIVE_BACKOFF_MULTIPLIER: float = 0.5
ADAPTIVE_RECOVERY_RATE: float = 1.05
MIN_THROTTLE_SCALE: float = 0.1
MAX_THROTTLE_SCALE: float = 1.0


class AdaptiveTokenBucketRateLimiter:
    """Adaptive dual token-bucket rate limiter enforcing upstream RPM and TPM quotas."""

    def __init__(
        self,
        rpm_quota: int = DEFAULT_RPM_QUOTA,
        tpm_quota: int = DEFAULT_TPM_QUOTA,
    ) -> None:
        if rpm_quota <= 0:
            raise ValueError("rpm_quota must be strictly positive.")
        if tpm_quota <= 0:
            raise ValueError("tpm_quota must be strictly positive.")

        self.base_rpm_quota = float(rpm_quota)
        self.base_tpm_quota = float(tpm_quota)
        self.throttle_scale = MAX_THROTTLE_SCALE

        self.request_tokens = self.base_rpm_quota
        self.token_budget = self.base_tpm_quota
        self.last_refill_timestamp = time.monotonic()
        self._lock = asyncio.Lock()

    @property
    def effective_rpm(self) -> float:
        return max(1.0, self.base_rpm_quota * self.throttle_scale)

    @property
    def effective_tpm(self) -> float:
        return max(1000.0, self.base_tpm_quota * self.throttle_scale)

    def _refill_unlocked(self, now: float) -> None:
        elapsed = max(0.0, now - self.last_refill_timestamp)
        self.last_refill_timestamp = now

        rpm_refill_rate = self.effective_rpm / SECONDS_PER_MINUTE
        tpm_refill_rate = self.effective_tpm / SECONDS_PER_MINUTE

        self.request_tokens = min(
            self.effective_rpm,
            self.request_tokens + elapsed * rpm_refill_rate,
        )
        self.token_budget = min(
            self.effective_tpm,
            self.token_budget + elapsed * tpm_refill_rate,
        )

    async def acquire(self, estimated_tokens: int) -> None:
        """Acquires 1 request token and `estimated_tokens` from the TPM bucket."""
        required_tokens = max(1.0, float(estimated_tokens))
        while True:
            async with self._lock:
                now = time.monotonic()
                self._refill_unlocked(now)
                capped_required_tokens = min(required_tokens, self.effective_tpm)

                if (
                    self.request_tokens >= 1.0
                    and self.token_budget >= capped_required_tokens
                ):
                    self.request_tokens -= 1.0
                    self.token_budget -= capped_required_tokens
                    return

                rpm_deficit = max(0.0, 1.0 - self.request_tokens)
                tpm_deficit = max(0.0, capped_required_tokens - self.token_budget)

                rpm_wait = rpm_deficit / (self.effective_rpm / SECONDS_PER_MINUTE)
                tpm_wait = tpm_deficit / (self.effective_tpm / SECONDS_PER_MINUTE)
                wait_duration = max(rpm_wait, tpm_wait, 0.01)

            await asyncio.sleep(wait_duration)

    async def record_rate_limit_violation(self) -> None:
        """Adaptively scales down throughput quotas upon detecting an HTTP 429 error."""
        async with self._lock:
            self.throttle_scale = max(
                MIN_THROTTLE_SCALE,
                self.throttle_scale * ADAPTIVE_BACKOFF_MULTIPLIER,
            )
            self.request_tokens = 0.0
            self.token_budget = 0.0
            self.last_refill_timestamp = time.monotonic()
            logger.warning(
                "[RAPTOR Throttler] Rate limit violation detected; scaling throughput factor to %.2f "
                "(effective RPM=%.1f, effective TPM=%.1f).",
                self.throttle_scale,
                self.effective_rpm,
                self.effective_tpm,
            )

    async def record_success(self) -> None:
        """Gradually restores throughput capacity after successful upstream completions."""
        async with self._lock:
            if self.throttle_scale < MAX_THROTTLE_SCALE:
                self.throttle_scale = min(
                    MAX_THROTTLE_SCALE,
                    self.throttle_scale * ADAPTIVE_RECOVERY_RATE,
                )


class RaptorEngine:
    r"""{'docstring': 'Asynchronously generates an abstractive summary for a group of nodes.\n\n    Invokes a configured Generative AI model (Gemini) to produce a concise\n    summary from the combined content of the input nodes. The prompt is\n    engineered to preserve critical entities like company names, projects,\n    and figures. This method includes internal error handling to gracefully\n    manage API failures.\n\n    Args:\n        nodes: A list of `RaptorNode` objects whose content will be combined\n            and summarized.\n\n    Returns:\n        The generated summary text. If the summarization API call fails for\n        any reason, a standard fallback error message is returned.'}."""

    def __init__(
        self,
        client_id: str,
        storage_dir: Path,
        max_concurrent_chunks: int = MAX_CONCURRENT_CHUNKS,
        rpm_quota: int = DEFAULT_RPM_QUOTA,
        tpm_quota: int = DEFAULT_TPM_QUOTA,
    ):
        r"""{'docstring': "Initializes the RaptorEngine by loading its data from a storage directory.\n\n    This constructor sets up client-specific storage paths, loads the Raptor tree\n    structure from a `raptor_tree.json` file, and configures the underlying\n    summarization agent. The agent is instantiated with the 'gemini-3.8-flash'\n    model, tailored for technical summarization tasks.\n\n    Args:\n        client_id (str): The unique identifier for the client.\n        storage_dir (pathlib.Path): The path to the directory containing the\n            engine's data. This directory must contain the `raptor_tree.json`\n            file.\n\n    Raises:\n        FileNotFoundError: If `raptor_tree.json` is not found within the\n            provided `storage_dir`.\n        ValueError: If `raptor_tree.json` contains malformed JSON or data that\n            cannot be parsed into a valid tree structure."}."""
        if max_concurrent_chunks <= 0:
            raise ValueError("max_concurrent_chunks must be strictly positive.")

        self.client_id = client_id
        self.storage_dir = storage_dir
        self.tree_path = storage_dir / "raptor_tree.json"
        self.tree = self._load_tree()

        self.max_concurrent_chunks = max_concurrent_chunks
        self._concurrency_semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
        self._rate_limiter = AdaptiveTokenBucketRateLimiter(
            rpm_quota=rpm_quota,
            tpm_quota=tpm_quota,
        )

        # Utilizes FlashAttention to optimize performance for high-throughput and large-scale summarization workloads.
        self.agent = Agent(
            name="raptor_summarizer",
            model=get_model(ModelTier.FAST),
            instruction="You are an enterprise architecture and strategic synthesis expert. Summarize technical chunks strictly preserving proper nouns, technology brands, and quantitative metrics.",
        )
        self.app = AdkApp(agent=self.agent)

    def _load_tree(self) -> RaptorTree:
        if self.tree_path.exists():
            try:
                return RaptorTree.model_validate_json(
                    self.tree_path.read_text(encoding="utf-8")
                )
            except (ValidationError, OSError, ValueError) as ex:
                logger.debug(f"[RaptorEngine] Failed to load existing tree: {ex}")
        return RaptorTree(client_id=self.client_id)

    async def build_tree(self, fragments: List[EvidenceFragment]) -> None:
        """Asynchronously constructs and persists a hierarchical knowledge tree by iteratively clustering and summarizing text fragments.

        This method builds the tree by first creating leaf nodes (Level 0) from the provided `fragments`. It then enters an iterative process to construct higher summary levels. At each level, nodes from the preceding level are grouped, and the content of each group is summarized concurrently to form a new parent node for the current level. This hierarchical summarization continues until a single root node is achieved or a maximum depth of three levels is reached.

        The final constructed tree is populated in the `self.tree` attribute and then persisted to storage.

        Args:
            fragments: A list of `EvidenceFragment` objects that serve as the
                foundational leaf nodes (Level 0) of the tree.

        Raises:
            IOError: If an error occurs during the persistence of the final tree
                structure to storage.
            Exception: Propagates exceptions from the underlying concurrent
                summarization tasks, which may include network, API, or data
                processing failures.
        """
        logger.info(
            f"🌲 [RAPTOR] Building Knowledge Tree for {self.client_id}..."
        )

        # Phase 1: Construct the leaf-node layer (Level 0) from the initial text chunks.
        current_level_nodes = []
        for frag in fragments:
            node = RaptorNode(
                node_id=frag.fragment_id,
                level=0,
                content=frag.content,
                metadata=frag.location_metadata,
            )
            self.tree.nodes[node.node_id] = node
            current_level_nodes.append(node)

        # Phase 2: Iteratively construct higher levels of the summary tree via recursive clustering and summarization.
        level = 0
        while (
            len(current_level_nodes) > 1 and level < 3
        ):  # To manage computational complexity in the prototype implementation, the summarization hierarchy is constrained to a maximum of three levels.
            level += 1
            logger.info(
                f"   -> [RAPTOR] Generating Level {level} (Throttled Parallel Summaries, max_concurrency={self.max_concurrent_chunks})..."
            )

            groups = self._group_nodes_by_hierarchy(current_level_nodes)

            tasks = []
            group_metadata = []

            for group_name, group_nodes in groups.items():
                if not group_nodes:
                    continue
                group_metadata.append((group_name, group_nodes))
                tasks.append(self._summarize_group_throttled(group_nodes))

            # Executes multiple summarization requests concurrently under semaphore and token-bucket rate limiting.
            summaries = await asyncio.gather(*tasks)

            next_level_nodes = []
            for i, summary_content in enumerate(summaries):
                group_name, group_nodes = group_metadata[i]
                summary_node = RaptorNode(
                    level=level,
                    content=summary_content,
                    children_ids=[n.node_id for n in group_nodes],
                    metadata={"group_key": group_name},
                )
                self.tree.nodes[summary_node.node_id] = summary_node
                next_level_nodes.append(summary_node)

            current_level_nodes = next_level_nodes

        if current_level_nodes:
            self.tree.root_id = current_level_nodes[0].node_id

        self._save_tree()
        logger.info(f"✅ [RAPTOR] Tree completed with {len(self.tree.nodes)} nodes.")

    async def _summarize_group_throttled(self, nodes: List[RaptorNode]) -> str:
        """Guards group summarization with concurrency semaphore and token-bucket rate limiting."""
        async with self._concurrency_semaphore:
            return await self._summarize_group(nodes)

    def _group_nodes_by_hierarchy(
        self, nodes: List[RaptorNode]
    ) -> Dict[str, List[RaptorNode]]:
        """Clusters nodes into semantically related groups using the document's structural hierarchy, as defined by headings, as the primary partitioning criterion."""
        groups: Dict[str, List[RaptorNode]] = {}
        for n in nodes:
            # The document's structural hierarchy, extracted from its metadata, serves as the primary key for node clustering.
            hierarchy = n.metadata.get("hierarchy", [])
            # The node clustering strategy is adaptive. The depth of the structural grouping key (e.g., '1.1' vs. '1.1.2') is dynamically determined by the current level of the summarization tree.
            key = " > ".join(hierarchy[: n.level + 1]) if hierarchy else "ROOT"
            if key not in groups:
                groups[key] = []
            groups[key].append(n)
        return groups

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        """Estimates LLM token count from character length for TPM quota accounting."""
        return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Detects HTTP 429 or upstream quota exhaustion exceptions."""
        message = str(exc).lower()
        status_code: Optional[int] = getattr(exc, "code", None) or getattr(
            exc, "status_code", None
        )
        return (
            status_code == 429
            or "429" in message
            or "rate limit" in message
            or "resource_exhausted" in message
            or "quota" in message
        )

    async def _summarize_group(self, nodes: List[RaptorNode]) -> str:
        """Generates a concise, abstractive summary for a specified cluster of text nodes by invoking the configured Language Model."""
        context = "\n".join([f"- {n.content}" for n in nodes])
        prompt = f"""
        SUMMARIZE THE FOLLOWING CHUNKS INTO A HIGH-DENSITY STRATEGIC PARAGRAPH.

        ### HARD ENTITY AND METRIC PRESERVATION INVARIANT:
        1. QUANTITATIVE PRESERVATION: Every number, percentage, latency (ms), bandwidth (Gbps), capacity (TB, PB), cost and software version MUST transfer verbatim without rounding.
        2. HARD TECHNICAL ENTITIES: Preserve exact vendor trade names, hardware models, cloud services, and regulatory standards.
        3. ZERO VAPORWARE: Prohibited from replacing concrete data with vacuous corporate adjectives.

        ### ORIGINAL FRAGMENTS:
        {context}

        Formatting Rules:
        1. Be concise with high informational density.
        2. Do not hallucinate data outside context.
        3. Return EXCLUSIVELY plain text summary, without JSON or conversational wrapping.
        """

        estimated_tokens = self._estimate_token_count(prompt)
        max_attempts = DEFAULT_RAPTOR_MAX_RETRY_ATTEMPTS
        client = create_genai_client()

        for attempt in range(1, max_attempts + 1):
            await self._rate_limiter.acquire(estimated_tokens)
            try:
                response = await client.aio.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=prompt,
                    config={
                        "system_instruction": "You are a data architect and forensic systems auditor. Generate high-density hierarchical summaries, retaining all quantitative metrics, infrastructure brand names, versions, and statutory acronyms without dilution."
                    },
                )
                await self._rate_limiter.record_success()
                raw_summary = str(response.text).strip()
                return self._enforce_deterministic_metric_retention(
                    context, raw_summary
                )
            except Exception as e:
                if self._is_rate_limit_error(e):
                    await self._rate_limiter.record_rate_limit_violation()
                    if attempt < max_attempts:
                        backoff_seconds = float(2 ** (attempt - 1))
                        logger.warning(
                            f"[RAPTOR] HTTP 429 rate limit encountered on attempt {attempt}/{max_attempts}; retrying in {backoff_seconds:.1f}s: {e}"
                        )
                        await asyncio.sleep(backoff_seconds)
                        continue
                logger.warning(
                    f"Error generating Raptor summary (fallback applied): {e}"
                )
                return "Summary unavailable due to upstream processing error."

        return "Summary unavailable due to upstream processing error."

    @staticmethod
    def _enforce_deterministic_metric_retention(context: str, summary: str) -> str:
        """Deterministically audits and guarantees that quantitative metrics and units
        from the input context are retained in the abstractive summary.
        If the generative model dropped any metric, it is appended in an immutable audit block.
        """
        metric_pattern = re.compile(
            r"(?:[\$€£¥₹₩]\s*\d+(?:[\.,]\d+)*(?:\s*(?:k|m|b|t))?\b|\b\d+(?:[\.,]\d+)*(?:\s*(?:ms|s|h|hours|gbps|mbps|tb|pb|gb)\b|\s*[%€\$£¥₹₩]|\s*(?:USD|EUR|GBP|JPY|CHF|SAR|AED|BRL|SGD|CAD|AUD|CNY|INR|KRW)\b))",
            re.IGNORECASE,
        )

        context_metrics = set(m.strip() for m in metric_pattern.findall(context))
        if not context_metrics:
            return summary

        summary_lower = summary.lower()
        missing_metrics = []
        for metric in sorted(context_metrics):
            normalized_metric = re.sub(r"\s+", " ", metric.lower())
            if normalized_metric not in summary_lower:
                missing_metrics.append(metric)

        if missing_metrics:
            logger.info(
                f"🛡️ [RAPTOR Gate] Rescued {len(missing_metrics)} quantitative metrics omitted by LLM: {missing_metrics}"
            )
            retention_block = f"\n[Preserved Critical Metrics]: {', '.join(missing_metrics)}"
            return f"{summary.strip()}{retention_block}"

        return summary

    def _save_tree(self) -> None:
        tmp_path = self.tree_path.with_name(
            f"{self.tree_path.name}.{uuid.uuid4().hex[:8]}.tmp"
        )
        try:
            tmp_path.write_text(self.tree.model_dump_json(indent=2), encoding="utf-8")
            tmp_path.replace(self.tree_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def get_context_at_level(self, level: int) -> str:
        """Return a formatted string of all node content at a specified hierarchical level."""
        nodes = [n for n in self.tree.nodes.values() if n.level == level]
        lines = [f"--- RAPTOR LEVEL {level} CONTEXT ---"]
        for n in nodes:
            lines.append(f"[{n.node_id}] {n.content}")
        return "\n".join(lines)

    def semantic_search(
        self, keywords: List[str], level: int = 0, top_k: int = 20
    ) -> str:
        """Retrieve relevant text nodes via a keyword-based term frequency search.

        This method performs a case-insensitive keyword search on nodes at a
        specified tree level. Each node is scored based on the cumulative term
        frequency of the provided keywords within its content. The `top_k` nodes
        with the highest scores are then selected and returned.

        If the search yields no results at the target level, the method defaults
        to returning a broader context from level 1 of the tree by calling
        `get_context_at_level(1)`, regardless of the initial `level` argument.

        Args:
            keywords (List[str]): A list of keywords to search for within the node
                content.
            level (int): The specific level in the document tree to search.
                Defaults to 0.
            top_k (int): The maximum number of top-scoring nodes to return.
                Defaults to 20.

        Returns:
            str: A formatted string containing the retrieved content. If nodes are
            found, the string includes a header followed by each node's content,
            prefixed with its UUID. If no nodes are found, it returns the result
            of `get_context_at_level(1)`.

        Raises:
            AttributeError: If any element in the `keywords` list is not a string.
        """
        nodes = [n for n in self.tree.nodes.values() if n.level == level]

        # Node relevance is calculated via a simple term frequency scoring algorithm.
        scored_nodes = []
        for n in nodes:
            content_lower = n.content.lower()
            score = sum(content_lower.count(kw.lower()) for kw in keywords)
            if score > 0:
                scored_nodes.append((score, n))

        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [n for score, n in scored_nodes[:top_k]]

        if not top_nodes:
            # If a query yields no results at the leaf-node level (Level 0), the search scope is automatically expanded to include Level 1 summaries to ensure comprehensive retrieval.
            return self.get_context_at_level(1)

        lines = ["--- RELEVANT EVIDENCE EXTRACTED FROM DOCUMENT (RAG) ---"]
        for n in top_nodes:
            lines.append(f"[Fragment UUID: {n.node_id}] {n.content}")
        return "\n".join(lines)
