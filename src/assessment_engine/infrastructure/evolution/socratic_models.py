"""
Define structured Pydantic models for Socratic deliberation.
Decoupled from socratic_deliberator.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SymbolicAnchorReport(BaseModel):
    """Step 0: Anchor pre-existing symbols and define protective boundaries."""
    existing_symbols: list[str] = Field(default_factory=list, description="Símbolos relevantes detectados")
    existing_tables: list[str] = Field(default_factory=list, description="Tablas SQLite preexistentes")
    existing_routers: list[str] = Field(default_factory=list, description="Routers de API ya montados")
    candidate_targets: list[str] = Field(default_factory=list, description="Rutas sugeridas para la misión")
    untouchable_core_files: list[str] = Field(
        default_factory=lambda: ["server.py", "core/runtime_bundle.py", "adk_lean_factory.py"],
        description="Archivos del núcleo cuya mutación está prohibida",
    )


class TeleologicalBoundary(BaseModel):
    """Step 1: Delimit scope and per-layer responsibilities."""
    domain_scope: str = Field(..., description="Alcance global (ej. Fullstack Component + API Router)")
    ui_responsibilities: list[str] = Field(default_factory=list, description="Responsabilidades de la capa de interfaz")
    api_responsibilities: list[str] = Field(default_factory=list, description="Responsabilidades de la capa de API")
    database_responsibilities: list[str] = Field(default_factory=list, description="Responsabilidades de persistencia")
    strictly_forbidden_actions: list[str] = Field(default_factory=list, description="Acciones expresamente vetadas")


class SotaEpistemicGrounding(BaseModel):
    """Step 2: Mine specifications from industry standards and benchmarks."""
    industry_benchmarks: list[str] = Field(default_factory=list, description="Líderes de referencia analizados")
    must_have_invariants: list[str] = Field(default_factory=list, description="Invariantes obligatorios de clase mundial")
    unfair_advantages: list[str] = Field(default_factory=list, description="Ventajas asimétricas a coste $0.00")
    deliberate_anti_features: list[str] = Field(default_factory=list, description="Anti-features descartadas por sobreingeniería")


class SkepticProbeReport(BaseModel):
    """Step 3: Probe for hidden pitfalls and failure modes in naive approaches."""
    hidden_traps: list[str] = Field(default_factory=list, description="Trampas ocultas que arruinan la solución ingenua")
    failure_modes: list[str] = Field(default_factory=list, description="Casos borde donde fallará en producción")
    must_address_flaws: list[str] = Field(default_factory=list, description="Defectos que el diseño final debe neutralizar")


class PragmaticReuseAudit(BaseModel):
    """Step 4: Audit currently installed packages and primitives."""
    installed_frontend_packages: list[str] = Field(default_factory=list, description="Librerías en package.json")
    existing_ui_components: list[str] = Field(default_factory=list, description="Componentes en @/components/ui")
    reusable_backend_primitives: list[str] = Field(default_factory=list, description="Módulos en core/primitives/")


class SituationalContextGauge(BaseModel):
    """Paso 5: Gobernanza y restricciones inmutables de NUESTRO repositorio."""
    zero_new_dependency_mandate: bool = Field(default=True, description="Prohibición de añadir paquetes externos")
    max_cyclomatic_complexity: int = Field(default=10, description="Límite McCabe V(G) <= 10")
    max_nesting_depth: int = Field(default=3, description="Límite de anidamiento de control")
    hard_constraints: list[str] = Field(default_factory=list, description="Restricciones no negociables del proyecto")


class AsymmetricSynthesis(BaseModel):
    """Step 6: Engineer Pareto-optimal solutions to neutralize pitfalls at zero cost."""
    pareto_solutions: list[str] = Field(default_factory=list, description="Soluciones ingeniosas que evitan dependencias pesadas")
    technical_tradeoffs_resolved: list[str] = Field(default_factory=list, description="Compensaciones de diseño cerradas")
    mitigations_for_hidden_traps: list[str] = Field(default_factory=list, description="Cómo se evita cada trampa del Paso 3")


class ModuleExecutionStep(BaseModel):
    """Step 7: Represent an individual step within the execution directed acyclic graph."""
    id: str = Field(..., description="Identificador único del módulo (ej. MOD_API_ANALYTICS)")
    name: str = Field(..., description="Nombre descriptivo de la capacidad")
    target_file: str = Field(..., description="Ruta relativa del archivo a crear/modificar")
    test_file: str = Field(..., description="Ruta relativa del test asociado")
    layer: str = Field(..., description="Capa de arquitectura (backend_api, frontend_ui, shell_integration)")
    purpose: str = Field(..., description="Propósito del módulo")
    invariants: list[str] = Field(default_factory=list, description="Invariantes que debe cumplir")
    dependencies: list[str] = Field(default_factory=list, description="Módulos previos requeridos")


class TopologicalDagPlan(BaseModel):
    """Step 7: Define an acyclic ordered execution graph for multi-file operations."""
    ordered_steps: list[ModuleExecutionStep] = Field(default_factory=list, description="Secuencia topológica estricta")
    dag_rationale: str = Field(..., description="Justificación del orden de compilación")


class TddOracleSpecification(BaseModel):
    """Step 8: Define the formal verification contract for sandbox execution."""
    unit_test_targets: list[str] = Field(default_factory=list, description="Tests unitarios a ejecutar")
    compilation_commands: list[str] = Field(default_factory=list, description="Comandos de compilación estricta")
    required_assertions: list[str] = Field(default_factory=list, description="Aserciones empíricas indispensables")


class SocraticDeliberationReport(BaseModel):
    """Represent the consolidated master dossier across all nine deliberation steps."""
    task: str
    sector: str
    step_0: SymbolicAnchorReport
    step_1: TeleologicalBoundary
    step_2: SotaEpistemicGrounding
    step_3: SkepticProbeReport
    step_4: PragmaticReuseAudit
    step_5: SituationalContextGauge
    step_6: AsymmetricSynthesis
    step_7: TopologicalDagPlan
    step_8: TddOracleSpecification

    def to_module_plans(self) -> list[Any]:
        """Convert topological steps into ModulePlan objects compatible with AutonomousProductDirector."""
        from assessment_engine.infrastructure.evolution.autonomous_product_director import ModulePlan
        plans = []
        for s in self.step_7.ordered_steps:
            plans.append(ModulePlan(
                id=s.id,
                name=s.name,
                target_file=s.target_file,
                test_file=s.test_file,
                purpose=s.purpose,
                invariants=s.invariants,
                is_yagni_approved=True,
            ))
        return plans
