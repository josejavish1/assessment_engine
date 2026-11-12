"""Polymorphic GoF Strategy Pattern for Section 4 Actuarial Decoupling.

Routes AST generation to the canonical Open FAIR Economic Receptor strategy.
100% Technical English, zero hardcoding, strictly localized via engine_config/locales.json.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from assessment_engine.domain.actuarial.receptor_allocator import (
    ActuarialVectorAllocator,
)
from assessment_engine.domain.schemas.ast import (
    BaseNode as ASTNode,
)
from assessment_engine.domain.schemas.ast import (
    CellNode,
    HeadingNode,
    ParagraphNode,
    SpacerNode,
    TableNode,
    TableRowNode,
)
from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)
from assessment_engine.infrastructure.localization import format_number, t


@dataclass(frozen=True)
class ActuarialReceptorContext:
    total_fair_ale: float
    currency: str
    meta_lang: str
    tower_name: str
    client_name: str
    loc_branch: Dict[str, Any]
    primary_color_rgb: List[int]
    alt_row_hex: str
    ch4_sec1_title: str
    callout_title: str
    callout_body: str
    delivery_model: str = "HYBRID"
    operational_archetype: str = "STANDARD_ENTERPRISE_B2B"
    cloud_intensity_gamma: float = 0.50
    buffering_elasticity_beta: float = 0.50


class IActuarialReceptorStrategy(ABC):
    """Interface for Open FAIR economic receptor AST builders."""

    @abstractmethod
    def build_ast_nodes(self, ctx: ActuarialReceptorContext) -> List[ASTNode]:
        pass


class BaseReceptorStrategy(IActuarialReceptorStrategy):
    """Base strategy implementing Open FAIR three-vector actuarial AST node generation."""

    receptor_type: LossArchetypeType

    def _get_locales(self, ctx: ActuarialReceptorContext) -> Dict[str, str]:
        loc = ctx.loc_branch.get("annex_ch4_receptors", {}).get(self.receptor_type.value, {})
        if not loc:
            from assessment_engine.infrastructure.localization import get_locales_data
            loc = get_locales_data().get("en", {}).get("annex_ch4_receptors", {}).get(self.receptor_type.value, {})
        return loc

    def _get_weights(self) -> Tuple[float, float, float]:
        registry = get_actuarial_archetype_registry()
        weights_obj = registry.receptor_weights.get(self.receptor_type) if registry.receptor_weights else None
        if weights_obj:
            return (
                weights_obj.vector_alpha_weight,
                weights_obj.vector_beta_weight,
                weights_obj.vector_gamma_weight,
            )
        fallbacks = {
            LossArchetypeType.AVAILABILITY_OUTAGE: (0.435, 0.342, 0.223),
            LossArchetypeType.CAPITAL_INEFFICIENCY: (0.485, 0.312, 0.203),
            LossArchetypeType.PRODUCTIVITY_TOIL: (0.448, 0.334, 0.218),
            LossArchetypeType.REGULATORY_AND_BREACH: (0.536, 0.268, 0.196),
        }
        return fallbacks.get(self.receptor_type, (0.435, 0.342, 0.223))

    def build_ast_nodes(self, ctx: ActuarialReceptorContext) -> List[ASTNode]:
        loc = self._get_locales(ctx)
        nodes: List[ASTNode] = []

        # 4.1 Section Heading
        section_title = loc.get("section_title") or ctx.ch4_sec1_title
        nodes.append(
            HeadingNode(
                text=section_title,
                level=2,
                primary_color_rgb=ctx.primary_color_rgb,
            )
        )

        # Methodology Intro Narrative (Safe format_map)
        from collections import defaultdict
        intro_tmpl = loc.get("methodology_intro", "")
        try:
            safe_map = defaultdict(str, domain_name=ctx.tower_name, client_name=ctx.client_name)
            intro_text = intro_tmpl.format_map(safe_map)
        except Exception:
            intro_text = intro_tmpl
        nodes.append(ParagraphNode(text=intro_text, space_after=6))

        # Centered Mathematical Equation
        formula_text = loc.get("formula_expression", "")
        nodes.append(SpacerNode(points=4))
        nodes.append(
            ParagraphNode(
                text=f"*{formula_text}*",
                align="CENTER",
            )
        )
        nodes.append(SpacerNode(points=8))

        # Vector Residual Allocation via Hare-Niemeyer
        w_alpha, w_beta, w_gamma = self._get_weights()
        split = ActuarialVectorAllocator.allocate(
            total_ale=ctx.total_fair_ale,
            weight_alpha=w_alpha,
            weight_beta=w_beta,
            weight_gamma=w_gamma,
        )

        v_alpha_fmt = f"{format_number(split.alpha_value, locale=ctx.meta_lang, decimals=0)} {ctx.currency}"
        v_beta_fmt = f"{format_number(split.beta_value, locale=ctx.meta_lang, decimals=0)} {ctx.currency}"
        v_gamma_fmt = f"{format_number(split.gamma_value, locale=ctx.meta_lang, decimals=0)} {ctx.currency}"
        total_val = split.alpha_value + split.beta_value + split.gamma_value
        total_fmt = f"{format_number(total_val, locale=ctx.meta_lang, decimals=0)} {ctx.currency}"

        # Discretize Percentage Weights to strictly sum to 100.0%
        p_a = round(w_alpha * 100.0, 1)
        p_b = round(w_beta * 100.0, 1)
        p_c = round(100.0 - (p_a + p_b), 1)
        p_alpha_str = f"{format_number(p_a, locale=ctx.meta_lang, decimals=1)}%"
        p_beta_str = f"{format_number(p_b, locale=ctx.meta_lang, decimals=1)}%"
        p_gamma_str = f"{format_number(p_c, locale=ctx.meta_lang, decimals=1)}%"
        p_tot_str = f"{format_number(100.0, locale=ctx.meta_lang, decimals=1)}%"

        # Dynamic Tenant Theme Colors
        rgb = ctx.primary_color_rgb or [48, 84, 150]
        header_bg_hex = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        header_text_color = [255, 255, 255]

        # Localized Column Headers with Universal Defaults
        col_vector = t("ch4_lineage_col_vector", locale=ctx.meta_lang)
        col_code = t("ch4_lineage_col_code", locale=ctx.meta_lang)
        col_desc = t("ch4_lineage_col_desc", locale=ctx.meta_lang)
        col_rate = t("ch4_lineage_col_rate", locale=ctx.meta_lang)
        col_share = t("ch4_lineage_col_share", locale=ctx.meta_lang)
        row_tot_name = t("ch4_lineage_row_total_ale", locale=ctx.meta_lang)
        row_tot_desc = t("ch4_lineage_row_total_desc", locale=ctx.meta_lang)

        lineage_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_vector, bold=True, bg_color=header_bg_hex, text_color_rgb=header_text_color),
                    CellNode(text=col_code, bold=True, bg_color=header_bg_hex, text_color_rgb=header_text_color, align="CENTER"),
                    CellNode(text=col_desc, bold=True, bg_color=header_bg_hex, text_color_rgb=header_text_color),
                    CellNode(text=col_rate, bold=True, bg_color=header_bg_hex, text_color_rgb=header_text_color, align="CENTER"),
                    CellNode(text=col_share, bold=True, bg_color=header_bg_hex, text_color_rgb=header_text_color, align="CENTER"),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(text=loc.get("vector_alpha_label", "Primary Vector Alpha"), bold=True, bg_color=ctx.alt_row_hex, font_size=8.5),
                    CellNode(text="V_alpha", bg_color=ctx.alt_row_hex, align="CENTER", font_size=8.5),
                    CellNode(text=loc.get("vector_alpha_desc", ""), bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=v_alpha_fmt, bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=p_alpha_str, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=loc.get("vector_beta_label", "Primary Vector Beta"), bold=True, bg_color=ctx.alt_row_hex, font_size=8.5),
                    CellNode(text="V_beta", bg_color=ctx.alt_row_hex, align="CENTER", font_size=8.5),
                    CellNode(text=loc.get("vector_beta_desc", ""), bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=v_beta_fmt, bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=p_beta_str, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=loc.get("vector_gamma_label", "Primary Vector Gamma"), bold=True, bg_color=ctx.alt_row_hex, font_size=8.5),
                    CellNode(text="V_gamma", bg_color=ctx.alt_row_hex, align="CENTER", font_size=8.5),
                    CellNode(text=loc.get("vector_gamma_desc", ""), bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=v_gamma_fmt, bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=p_gamma_str, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=row_tot_name, bold=True, bg_color="E2F0D9", font_size=9.0),
                    CellNode(text="ALE_total", bold=True, bg_color="E2F0D9", align="CENTER", font_size=9.0),
                    CellNode(text=row_tot_desc, italic=True, bg_color="E2F0D9", font_size=8.0),
                    CellNode(text=total_fmt, bold=True, bg_color="E2F0D9", align="CENTER", font_size=9.0),
                    CellNode(text=p_tot_str, bold=True, bg_color="E2F0D9", align="CENTER", font_size=9.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=lineage_rows, autofit=True, col_widths=[0.24, 0.12, 0.40, 0.14, 0.10]))
        nodes.append(SpacerNode(points=8))

        # Epistemic Callout Box
        nodes.append(
            ParagraphNode(
                text=f"**{ctx.callout_title}:** {ctx.callout_body}",
                italic=True,
                font_size=8.5,
                space_after=12,
            )
        )

        supp = self._build_supplementary_context(ctx)
        if supp:
            nodes.append(supp)

        return nodes

    def _build_supplementary_context(self, ctx: ActuarialReceptorContext) -> Optional[ParagraphNode]:
        """Hook for archetype-specific contextual narratives."""
        return None


class AvailabilityOutageStrategy(BaseReceptorStrategy):
    receptor_type = LossArchetypeType.AVAILABILITY_OUTAGE

    def _build_supplementary_context(self, ctx: ActuarialReceptorContext) -> Optional[ParagraphNode]:
        beta = ctx.buffering_elasticity_beta
        arch = ctx.operational_archetype.upper()
        beta_map = ctx.loc_branch.get("annex_ch4_context_beta", {})

        from assessment_engine.domain.actuarial.financial_profile import (
            IndustryArchetype,
        )
        resolved_arch = IndustryArchetype.from_str(arch)

        if resolved_arch in (IndustryArchetype.PROCESS_MANUFACTURING_OT, IndustryArchetype.DEFERRED_NETWORK_LOGISTICS):
            key = "buffered_silo" if beta < 0.70 else "high_tempo"
        elif resolved_arch == IndustryArchetype.LIFE_SAFETY_CRITICAL:
            key = "clinical"
        elif resolved_arch == IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH:
            key = "synchronous"
        elif resolved_arch in (IndustryArchetype.STANDARD_ENTERPRISE_B2B, IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION):
            return None
        else:
            key = "high_tempo"

        tmpl = beta_map.get(key, "")
        if not tmpl:
            return None

        from collections import defaultdict
        try:
            safe_b = defaultdict(str, beta=beta)
            formatted = tmpl.format_map(safe_b)
        except Exception:
            formatted = tmpl
        return ParagraphNode(text=f"*{formatted}*", font_size=8.5, space_after=10)


class CapitalInefficiencyStrategy(BaseReceptorStrategy):
    receptor_type = LossArchetypeType.CAPITAL_INEFFICIENCY

    def _build_supplementary_context(self, ctx: ActuarialReceptorContext) -> Optional[ParagraphNode]:
        gamma = ctx.cloud_intensity_gamma
        model = ctx.delivery_model.upper()
        gamma_map = ctx.loc_branch.get("annex_ch4_context_gamma", {})

        if model == "CLOUD_NATIVE" or gamma >= 0.70:
            key = "cloud_native"
        elif gamma <= 0.35 or "ON_PREM" in model:
            key = "on_prem"
        else:
            key = "hybrid"

        tmpl = gamma_map.get(key, "")
        if not tmpl:
            return None

        from collections import defaultdict
        try:
            safe_g = defaultdict(str, gamma=gamma)
            formatted = tmpl.format_map(safe_g)
        except Exception:
            formatted = tmpl
        return ParagraphNode(text=f"*{formatted}*", font_size=8.5, space_after=10)


class ProductivityToilStrategy(BaseReceptorStrategy):
    receptor_type = LossArchetypeType.PRODUCTIVITY_TOIL


class RegulatoryBreachStrategy(BaseReceptorStrategy):
    receptor_type = LossArchetypeType.REGULATORY_AND_BREACH


class ActuarialReceptorFactory:
    """Registry and Resolver for canonical Open FAIR Economic Receptors."""

    _strategies: Dict[LossArchetypeType, IActuarialReceptorStrategy] = {
        LossArchetypeType.AVAILABILITY_OUTAGE: AvailabilityOutageStrategy(),
        LossArchetypeType.CAPITAL_INEFFICIENCY: CapitalInefficiencyStrategy(),
        LossArchetypeType.PRODUCTIVITY_TOIL: ProductivityToilStrategy(),
        LossArchetypeType.REGULATORY_AND_BREACH: RegulatoryBreachStrategy(),
    }

    @classmethod
    def get_strategy(cls, receptor_type: LossArchetypeType) -> IActuarialReceptorStrategy:
        if receptor_type not in cls._strategies:
            raise ValueError(f"Unknown Economic Receptor: {receptor_type}")
        return cls._strategies[receptor_type]
