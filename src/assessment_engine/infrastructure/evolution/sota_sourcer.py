"""
Execute clean-room source mining and reference analysis:
1. Ground formal standards (RFC/W3C) via web search and 3-Cube Matrix analysis.
2. Resolve public reference repositories on GitHub.
3. Clone reference repositories ephemerally into /tmp (--depth 1).
4. Apply deterministic tree-slicing to discard lockfiles, binaries, configuration files, tests, and documentation.
5. Compute AST symbol centrality to locate core algorithms via PageRank (RepoMap).
6. Perform clean-room extraction of reference implementations (functions, state machines, and edge cases).
"""
from __future__ import annotations


import ast
import concurrent.futures
import logging
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.error
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from assessment_engine.infrastructure.evolution.epistemic_distiller import (
    EpistemicDistiller,
    ProductStrategyDossier,
    epistemic_distiller,
)
from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model
from assessment_engine.infrastructure.primitives.repomap import (
    RepoMapPrimitive,
    repomap,
)

logger = logging.getLogger("assessment_engine.infrastructure.evolution.sota_sourcer")

# DETERMINISTIC TREE-SLICING CONSTANTS

EXCLUDED_TREE_DIRS: set[str] = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".github",
    ".circleci",
    ".gitlab",
    "docs",
    "documentation",
    "doc",
    "test",
    "tests",
    "__tests__",
    "coverage",
    "examples",
    "example",
    "samples",
    "benchmarks",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

EXCLUDED_FILE_EXTENSIONS: set[str] = {
    ".lock",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".pdf",
    ".md",
    ".markdown",
    ".txt",
    ".min.js",
    ".min.css",
    ".map",
    ".wasm",
    ".exe",
    ".bin",
    ".pyc",
    ".tar",
    ".gz",
    ".zip",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
}

EXCLUDED_FILENAME_SUBSTRINGS: tuple[str, ...] = (
    ".config.",
    "tailwind.config",
    "vite.config",
    "next.config",
    "postcss.config",
    "webpack.config",
    "eslint.config",
    "tsconfig",
    ".d.ts",
    "setupTests",
    "reportWebVitals",
)

SUPPORTED_SOURCE_EXTENSIONS: tuple[str, ...] = (
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".c",
    ".cpp",
    ".java",
)


@dataclass(frozen=True)
class CleanRoomFile:
    """Represent a core source file extracted from a reference repository."""
    rel_path: str
    centrality_score: float
    code: str
    sloc: int
    definitions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "rel_path": self.rel_path,
            "centrality_score": self.centrality_score,
            "code": self.code,
            "sloc": self.sloc,
            "definitions": list(self.definitions),
        }


@dataclass
class CleanRoomPayload:
    """Store parsed and filtered reference source code."""
    repo_name: str
    files: list[CleanRoomFile] = field(default_factory=list)
    total_files_scanned: int = 0
    total_files_retained: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert the object to a dictionary representation."""
        return {
            "repo_name": self.repo_name,
            "files": [f.to_dict() for f in self.files],
            "total_files_scanned": self.total_files_scanned,
            "total_files_retained": self.total_files_retained,
        }


@dataclass
class SotaIntelligenceReport:
    """Represent a consolidated report merging formal specifications and reference code."""
    task: str
    sector: str
    dossier: ProductStrategyDossier
    clean_room_payloads: list[CleanRoomPayload] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the instance."""
        return {
            "task": self.task,
            "sector": self.sector,
            "dossier": self.dossier.to_dict(),
            "clean_room_payloads": [p.to_dict() for p in self.clean_room_payloads],
        }

    def to_markdown_brief(self) -> str:
        """Generate a comprehensive Markdown briefing combining formal specifications with reference code."""
        base_md = self.dossier.to_markdown_brief()
        if not self.clean_room_payloads:
            return base_md

        code_sections: list[str] = []
        for payload in self.clean_room_payloads:
            if not payload.files:
                continue
            code_sections.extend([
                f"\n#### 5. REFERENCIA CLEAN-ROOM DE CÓDIGO REAL (Repo: {payload.repo_name})",
                f"Archivos analizados por PageRank: {payload.total_files_retained} de {payload.total_files_scanned}",
            ])
            for cf in payload.files:
                defs_str = ", ".join(cf.definitions[:6]) or "lógica interna"
                code_sections.append(
                    f"\n##### [{cf.rel_path}] — Centralidad: {cf.centrality_score:.4f} | SLOC: {cf.sloc}\n"
                    f"Símbolos exportados: `{defs_str}`\n"
                    f"```typescript\n{cf.code[:1500]}\n# ... [código completo disponible en payload]\n```"
                )

        return base_md + "\n" + "\n".join(code_sections)



class EphemeralRepo:
    """Provide a secure context manager for cloning or inspecting repositories ephemerally in /tmp, guaranteeing directory deletion upon exit."""

    def __init__(self, repo_source: str | Path) -> None:
        self.source = str(repo_source)
        self.temp_dir: Path | None = None
        self.is_remote = self.source.startswith("http://") or self.source.startswith("https://") or self.source.startswith("git@")

    def __enter__(self) -> Path:
        token = uuid.uuid4().hex[:8]
        if self.is_remote:
            self.temp_dir = Path(tempfile.gettempdir()) / f"autonomuos_sota_{token}"
            logger.info(f"[SotaSourcer] Clonando efímeramente {self.source} en {self.temp_dir} (--depth 1)...")
            cmd = ["git", "clone", "--depth", "1", self.source, str(self.temp_dir)]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                if self.temp_dir and self.temp_dir.exists():
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                raise RuntimeError(f"Fallo al clonar repositorio de referencia '{self.source}': {ex}") from ex
            return self.temp_dir
        else:
            local_path = Path(self.source).resolve()
            if not local_path.exists():
                raise FileNotFoundError(f"Directorio local de referencia '{local_path}' no existe.")
            return local_path

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.is_remote and self.temp_dir and self.temp_dir.exists():
            logger.info(f"[SotaSourcer] Limpiando repositorio efímero {self.temp_dir}...")
            shutil.rmtree(self.temp_dir, ignore_errors=True)


class SotaSourcer:
    """Resolve GitHub repositories autonomously, filter noise, and extract the algorithmic core."""

    def __init__(
        self,
        distiller: EpistemicDistiller | None = None,
        repomap_primitive: RepoMapPrimitive | None = None,
    ) -> None:
        self.distiller = distiller or epistemic_distiller
        self.repomap = repomap_primitive or repomap

    def _is_url_reachable(self, url: str) -> bool:
        """Pre-sondeo HTTP HEAD (0.05s) para descartar URLs alucinadas o privadas (404/403)."""
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Autonomuos/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return False

    def _parse_and_validate_repo_urls(self, text: str, seen: set[str], resolved_urls: list[str]) -> bool:
        matches = re.findall(r"https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)", text)
        for owner, repo_name in matches:
            clean_repo = repo_name.rstrip("/").rstrip(".")
            if owner.lower() in ("features", "topics", "orgs", "search", "site"): continue
            if clean_repo.lower() in ("topics", "features", "pricing", "explore"): continue
            url = f"https://github.com/{owner}/{clean_repo}"
            if url not in seen:
                seen.add(url)
                if self._is_url_reachable(url):
                    resolved_urls.append(url)
                    logger.info(f"[SotaSourcer] Repositorio resuelto y vivo: {url}")
                else:
                    logger.debug(f"[SotaSourcer] Descartada URL alucinada o privada (404/403): {url}")
            if len(resolved_urls) >= 3:
                return True
        return False

    def resolve_reference_repo_urls(
        self, task: str, sector: str = "General", force_fallback: bool = False,
    ) -> list[str]:
        """AUTONOMOUS REPO RESOLUTION (Nivel Tier-1)."""
        if force_fallback:
            return []

        try:
            client = create_genai_client()
            from google.genai import types

            chat = client.chats.create(
                model=get_model(ModelTier.FAST),
                config=types.GenerateContentConfig(temperature=0.1, tools=[types.Tool(google_search=types.GoogleSearch())]),
            )

            prompt = (
                f"Identify the top 1 to 3 non-redundant open-source GitHub repositories that solve parts of this technical task:\n"
                f"Task: '{task}' in the sector '{sector}'.\n\n"
                "To prevent 'monorepo bias' or UI-only bias, select complementary repositories.\n"
                "Return exclusively their canonical GitHub URLs formatted exactly as https://github.com/owner/repo"
            )

            resolved_urls = []
            seen = set()

            for attempt in range(2):
                resp = chat.send_message(prompt)
                if not resp or not resp.text:
                    continue

                if self._parse_and_validate_repo_urls(resp.text, seen, resolved_urls):
                    return resolved_urls
                        
                if resolved_urls:
                    return resolved_urls
                else:
                    logger.info(f"[SotaSourcer] Intento {attempt+1} fallido (404). Re-intentando...")
                    prompt = "Las URLs proporcionadas anteriormente devuelven error 404. Por favor, busca repositorios DIFERENTES vivos hoy."

            return resolved_urls

        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[SotaSourcer] Resolución autónoma omitida: {ex}")

        return []

    def _should_retain_file(self, f: str, file_path: Path) -> bool:
        f_lower = f.lower()
        if file_path.suffix.lower() in EXCLUDED_FILE_EXTENSIONS:
            return False
        if file_path.suffix.lower() not in SUPPORTED_SOURCE_EXTENSIONS:
            return False
        if any(sub in f_lower for sub in EXCLUDED_FILENAME_SUBSTRINGS):
            return False
        if f.startswith("test_") or f.endswith("_test.py") or f.endswith(".test.ts") or f.endswith(".spec.ts"):
            return False
        return True

    def slice_tree(self, repo_dir: Path) -> tuple[list[Path], int]:
        """Apply deterministic pruning (tree-slicing) to discard lockfiles, binaries, configuration files, CI workflows, documentation, and tests. Return source files and the total scanned count."""
        retained: list[Path] = []
        total_scanned = 0

        for root, dirs, files in os.walk(str(repo_dir), topdown=True):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_TREE_DIRS and not d.startswith(".")]

            for f in files:
                total_scanned += 1
                file_path = Path(root) / f
                if self._should_retain_file(f, file_path):
                    retained.append(file_path)

        return retained, total_scanned

    def rank_central_files(self, repo_dir: Path, retained_files: list[Path], task_keywords: list[str], top_k: int = 3) -> list[tuple[str, float, list[str]]]:
        """Apply symbol PageRank (RepoMap) over retained files and weight them semantically against task keywords to mitigate monorepo bias."""
        if not retained_files:
            return []

        rel_files = [str(p.relative_to(repo_dir)) for p in retained_files]
        file_tags: dict[str, list[Any]] = {}

        for p in retained_files:
            rel = str(p.relative_to(repo_dir))
            if p.suffix == ".py":
                file_tags[rel] = self.repomap.extract_python_tags(repo_dir, p)
            elif p.suffix in {".ts", ".js", ".tsx", ".jsx"}:
                file_tags[rel] = self.repomap.extract_js_ts_tags(repo_dir, p)

        edges = self.repomap._build_reference_edges(file_tags)
        ranks = self.repomap.calculate_pagerank(rel_files, edges)

        semantic_ranks = {}
        for f in rel_files:
            base_score = ranks.get(f, 0.0)
            f_lower = f.lower()
            keyword_matches = sum(1 for kw in task_keywords if kw in f_lower)
            semantic_multiplier = 1.0 + (keyword_matches * 0.5)
            semantic_ranks[f] = base_score * semantic_multiplier

        sorted_files = sorted(rel_files, key=lambda f: semantic_ranks.get(f, 0.0), reverse=True)

        results: list[tuple[str, float, list[str]]] = []
        for f in sorted_files[:top_k]:
            score = semantic_ranks.get(f, 0.0)
            tags = file_tags.get(f, [])
            defs = [t.name for t in tags if getattr(t, "kind", "") == "def"]
            results.append((f, score, defs))

        return results

    def extract_clean_room_payload(self, repo_dir: Path, task_keywords: list[str], repo_name: str = "reference_repo", top_k: int = 3) -> CleanRoomPayload:
        """
        Execute clean-room extraction on the repository in /tmp.
        """
        retained, total_scanned = self.slice_tree(repo_dir)
        ranked = self.rank_central_files(repo_dir, retained, task_keywords, top_k=top_k)

        clean_files: list[CleanRoomFile] = []
        for rel_path, score, defs in ranked:
            file_path = repo_dir / rel_path
            try:
                code_text = file_path.read_text(encoding="utf-8", errors="ignore")
                sloc = len([line for line in code_text.splitlines() if line.strip() and not line.strip().startswith("#")])
                clean_files.append(CleanRoomFile(
                    rel_path=rel_path,
                    centrality_score=score,
                    code=code_text,
                    sloc=sloc,
                    definitions=tuple(defs),
                ))
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.warning(f"[SotaSourcer] Error leyendo '{rel_path}': {ex}")

        return CleanRoomPayload(
            repo_name=repo_name,
            files=clean_files,
            total_files_scanned=total_scanned,
            total_files_retained=len(retained),
        )

    def _process_single_repo(self, repo: str | Path, task_keywords: list[str], top_k: int) -> CleanRoomPayload | None:
        try:
            repo_str = str(repo)
            repo_name = repo_str.rstrip("/").split("/")[-1].replace(".git", "")
            with EphemeralRepo(repo) as temp_path:
                payload = self.extract_clean_room_payload(
                    repo_dir=temp_path,
                    task_keywords=task_keywords,
                    repo_name=repo_name,
                    top_k=top_k,
                )
            logger.info(f"[SotaSourcer-Paso1] Clean-Room exitoso en '{repo_name}': {len(payload.files)} archivos nucleares.")
            return payload
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f"[SotaSourcer-Paso1] No se pudo extraer Clean-Room de '{repo}': {ex}")
            return None

    def discover_and_mine(
        self,
        task: str,
        sector: str = "Fintech & Web Architecture",
        reference_repo: str | Path | None = None,
        force_fallback: bool = False,
        top_k: int = 3,
    ) -> SotaIntelligenceReport:
        """
        Execute multi-repository source mining.
        """
        logger.info(f"[SotaSourcer-Paso1] Minando estándares para tarea: '{task[:60]}'...")

        dossier = self.distiller.distill(
            task_description=task,
            sector=sector,
            force_fallback=force_fallback,
        )

        target_repos = [reference_repo] if reference_repo else []
        if not target_repos and not force_fallback:
            target_repos = self.resolve_reference_repo_urls(task, sector, force_fallback=force_fallback)

        clean_room_payloads: list[CleanRoomPayload] = []
        task_keywords = [w.lower() for w in task.replace(":", "").replace("-", " ").split() if len(w) > 3]

        if target_repos:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(target_repos)) as executor:
                futures = [
                    executor.submit(self._process_single_repo, repo, task_keywords, top_k)
                    for repo in target_repos
                ]
                for future in concurrent.futures.as_completed(futures):
                    payload = future.result()
                    if payload:
                        clean_room_payloads.append(payload)

        return SotaIntelligenceReport(
            task=task,
            sector=sector,
            dossier=dossier,
            clean_room_payloads=clean_room_payloads,
        )


sota_sourcer = SotaSourcer()
