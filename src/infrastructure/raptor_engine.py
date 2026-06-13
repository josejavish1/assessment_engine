import asyncio
import logging
from pathlib import Path
from typing import Dict, List

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from domain.schemas.evidence import EvidenceFragment, RaptorNode, RaptorTree
from infrastructure.ai_client import run_agent

logger = logging.getLogger(__name__)


class RaptorEngine:
    """
    SOTA 2026 Recursive Abstractive Processing Engine.
    Builds a hierarchical tree of summaries for deep document understanding.
    """

    def __init__(self, client_id: str, storage_dir: Path):
        self.client_id = client_id
        self.storage_dir = storage_dir
        self.tree_path = storage_dir / "raptor_tree.json"
        self.tree = self._load_tree()

        # SOTA 2026: Usamos Flash para tareas de alta velocidad y volumen
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
        """
        Builds the tree from raw fragments (Level 0).
        """
        print(
            f"🌲 [RAPTOR] Construyendo Árbol de Conocimiento para {self.client_id}..."
        )

        # 1. Initialize Level 0 (Leaves)
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

        # 2. Recursive Summarization
        level = 0
        while len(current_level_nodes) > 1 and level < 3:  # Max 3 levels for prototype
            level += 1
            print(f"   -> [RAPTOR] Generando Nivel {level} (Resúmenes en Paralelo)...")

            # Group nodes
            groups = self._group_nodes_by_hierarchy(current_level_nodes)

            tasks = []
            group_metadata = []

            for group_name, group_nodes in groups.items():
                if not group_nodes:
                    continue
                group_metadata.append((group_name, group_nodes))
                tasks.append(self._summarize_group(group_nodes))

            # ÉLITE: Ejecución paralela masiva con asyncio.gather
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
        """Groups nodes based on their heading hierarchy."""
        groups: Dict[str, List[RaptorNode]] = {}
        for n in nodes:
            # Use the hierarchy from metadata as grouping key
            hierarchy = n.metadata.get("hierarchy", [])
            # We group by the first few levels of hierarchy depending on current depth
            key = " > ".join(hierarchy[: n.level + 1]) if hierarchy else "ROOT"
            if key not in groups:
                groups[key] = []
            groups[key].append(n)
        return groups

    async def _summarize_group(self, nodes: List[RaptorNode]) -> str:
        """Calls LLM to summarize a cluster of nodes."""
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
                config={"system_instruction": "Eres un experto en síntesis estratégica NTT DATA."}
            )
            return str(response.text).strip()
        except Exception as e:
            logger.warning(f"Error generando resumen Raptor (fallback aplicado): {e}")
            return "Resumen no disponible debido a un error de procesamiento."

    def _save_tree(self) -> None:
        self.tree_path.write_text(self.tree.model_dump_json(indent=2), encoding="utf-8")

    def get_context_at_level(self, level: int) -> str:
        """Returns all summaries at a specific level for global reasoning."""
        nodes = [n for n in self.tree.nodes.values() if n.level == level]
        lines = [f"--- RAPTOR LEVEL {level} CONTEXT ---"]
        for n in nodes:
            lines.append(f"[{n.node_id}] {n.content}")
        return "\n".join(lines)

    def semantic_search(
        self, keywords: List[str], level: int = 0, top_k: int = 20
    ) -> str:
        """Retrieves nodes that match the domain keywords to feed specific harvesters."""
        nodes = [n for n in self.tree.nodes.values() if n.level == level]

        # Simple frequency scoring
        scored_nodes = []
        for n in nodes:
            content_lower = n.content.lower()
            score = sum(content_lower.count(kw.lower()) for kw in keywords)
            if score > 0:
                scored_nodes.append((score, n))

        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [n for score, n in scored_nodes[:top_k]]

        if not top_nodes:
            # Fallback to level 1 summaries if no specific matches found at level 0
            return self.get_context_at_level(1)

        lines = ["--- EVIDENCIAS RELEVANTES EXTRAÍDAS DEL DOCUMENTO (RAG) ---"]
        for n in top_nodes:
            lines.append(f"[Fragmento UUID: {n.node_id}] {n.content}")
        return "\n".join(lines)
