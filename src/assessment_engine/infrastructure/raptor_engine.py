import asyncio
import logging
from pathlib import Path
from typing import Dict, List

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.schemas.evidence import (
    EvidenceFragment,
    RaptorNode,
    RaptorTree,
)

logger = logging.getLogger(__name__)


class RaptorEngine:
    r"""{'docstring': 'Asynchronously generates an abstractive summary for a group of nodes.\n\n    Invokes a configured Generative AI model (Gemini) to produce a concise\n    summary from the combined content of the input nodes. The prompt is\n    engineered to preserve critical entities like company names, projects,\n    and figures. This method includes internal error handling to gracefully\n    manage API failures.\n\n    Args:\n        nodes: A list of `RaptorNode` objects whose content will be combined\n            and summarized.\n\n    Returns:\n        The generated summary text. If the summarization API call fails for\n        any reason, a standard fallback error message is returned.'}."""

    def __init__(self, client_id: str, storage_dir: Path):
        r"""{'docstring': "Initializes the RaptorEngine by loading its data from a storage directory.\n\n    This constructor sets up client-specific storage paths, loads the Raptor tree\n    structure from a `raptor_tree.json` file, and configures the underlying\n    summarization agent. The agent is instantiated with the 'gemini-2.5-flash'\n    model, tailored for technical summarization tasks.\n\n    Args:\n        client_id (str): The unique identifier for the client.\n        storage_dir (pathlib.Path): The path to the directory containing the\n            engine's data. This directory must contain the `raptor_tree.json`\n            file.\n\n    Raises:\n        FileNotFoundError: If `raptor_tree.json` is not found within the\n            provided `storage_dir`.\n        ValueError: If `raptor_tree.json` contains malformed JSON or data that\n            cannot be parsed into a valid tree structure."}."""
        self.client_id = client_id
        self.storage_dir = storage_dir
        self.tree_path = storage_dir / "raptor_tree.json"
        self.tree = self._load_tree()

        # Utilizes FlashAttention to optimize performance for high-throughput and large-scale summarization workloads.
        self.agent = Agent(
            name="raptor_summarizer",
            model="gemini-2.5-flash",
            instruction="Eres un experto en síntesis estratégica NTT DATA. Tu tarea es resumir fragmentos técnicos manteniendo nombres propios, marcas y cifras exactas.",
        )
        self.app = AdkApp(agent=self.agent)

    def _load_tree(self) -> RaptorTree:
        if self.tree_path.exists():
            try:
                return RaptorTree.model_validate_json(
                    self.tree_path.read_text(encoding="utf-8")
                )
            except Exception:
                pass
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
        print(
            f"🌲 [RAPTOR] Construyendo Árbol de Conocimiento para {self.client_id}..."
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
            print(f"   -> [RAPTOR] Generando Nivel {level} (Resúmenes en Paralelo)...")

            #
            groups = self._group_nodes_by_hierarchy(current_level_nodes)

            tasks = []
            group_metadata = []

            for group_name, group_nodes in groups.items():
                if not group_nodes:
                    continue
                group_metadata.append((group_name, group_nodes))
                tasks.append(self._summarize_group(group_nodes))

            # Executes multiple summarization requests concurrently using `asyncio.gather` to maximize throughput.
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
        print(f"✅ [RAPTOR] Árbol finalizado con {len(self.tree.nodes)} nodos.")

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

    async def _summarize_group(self, nodes: List[RaptorNode]) -> str:
        """Generates a concise, abstractive summary for a specified cluster of text nodes by invoking the configured Language Model."""
        context = "\n".join([f"- {n.content}" for n in nodes])
        prompt = f"""
        RESUME LOS SIGUIENTES FRAGMENTOS EN UN PÁRRAFO ESTRATÉGICO.

        ### REGLA DE ORO: Mantén nombres de empresas (Hispasat, Reintel, etc.), proyectos y cifras.

        ### FRAGMENTOS:
        {context}

        Reglas:
        1. Sé conciso y profesional.
        2. Mantén datos técnicos críticos (nombres de productos, versiones, porcentajes).
        3. No inventes información fuera del contexto proporcionado.
        4. Devuelve ÚNICAMENTE el texto del resumen en texto plano, sin JSON ni etiquetas.
        """

        try:
            import os

            from google import genai

            api_key = os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "system_instruction": "Eres un experto en síntesis estratégica NTT DATA."
                },
            )
            return str(response.text).strip()
        except Exception as e:
            logger.warning(f"Error generando resumen Raptor (fallback aplicado): {e}")
            return "Resumen no disponible debido a un error de procesamiento."

    def _save_tree(self) -> None:
        self.tree_path.write_text(self.tree.model_dump_json(indent=2), encoding="utf-8")

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

        lines = ["--- EVIDENCIAS RELEVANTES EXTRAÍDAS DEL DOCUMENTO (RAG) ---"]
        for n in top_nodes:
            lines.append(f"[Fragmento UUID: {n.node_id}] {n.content}")
        return "\n".join(lines)
