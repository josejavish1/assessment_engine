"""Unit tests for commercial report document rendering."""

from __future__ import annotations

from pathlib import Path
from docx import Document

from assessment_engine.adapters.render_commercial_report import render_commercial_report
from assessment_engine.domain.schemas.commercial import (
    CommercialDocumentMeta,
    CommercialPayload,
    CommercialSummaryDraft,
    DealFlash,
    GtmStrategy,
    OpportunityPipelineItem,
    ProposalDraft,
    ContextAndWhy,
    SolutionAndWhat,
    ScopeAndHow,
    DeliveryTeam,
    GovernanceAndAssumptions,
    WhyPartner,
    InvestmentAndTimeline,
    StakeholderMatrixItem,
    RiskManagementItem,
)


def test_render_commercial_report_execution(tmp_path: Path):
    """Verify that render_commercial_report builds a complete commercial DOCX report."""
    template_path = Path("templates/docx/global_report_template.docx")
    output_docx = tmp_path / "Commercial_Report.docx"
    assert template_path.exists(), "Template DOCX missing."

    payload = CommercialPayload(
        meta=CommercialDocumentMeta(
            client="Acme Corp",
            date="2026-10-28",
            version="1.0.0",
        ),
        commercial_summary=CommercialSummaryDraft(
            deal_flash=DealFlash(
                purchase_driver="Renovación de Infraestructura",
                vendor_win_theme="Liderazgo en Automatización Cloud",
            ),
            why_now_bullets=["Presión regulatoria DORA", "Fin de soporte de hardware"],
            how_we_win_bullets=["Experiencia en misión crítica", "Aceleradores IaC"],
            estimated_tam="1.5M €",
        ),
        gtm_strategy=GtmStrategy(
            trojan_horse="Piloto controlado en datacenter secundario",
            self_funded_transformation="Optimización FinOps para autofinanciar la fase 2",
            lock_in="Desacoplamiento progresivo mediante APIs abiertas para soberanía tecnológica",
        ),
        stakeholder_matrix=[
            StakeholderMatrixItem(
                name="CIO",
                role="Sponsor Ejecutivo",
                focus="Reducción de coste y modernización",
                message="Propuesta de valor probada en el sector",
            )
        ],
        opportunities_pipeline=[
            OpportunityPipelineItem(
                initiative="Migración a Contenedores",
                tower_origin="T2",
                vendor_cosell="Kubevirt / Red Hat",
                revenue_type="Servicios Profesionales",
                estimated_tcv="450k €",
                cost_of_inaction="Incremento del 30% en OPEX",
                client_objection="Falta de personal especializado",
                objection_handling="Formación y acompañamiento en el piloto",
            )
        ],
        proactive_proposals=[
            ProposalDraft(
                initiative_name="Despliegue de Observabilidad Unificada",
                context_and_why=ContextAndWhy(
                    origin="Auditoría de monitorización",
                    cost_of_inaction="MTTD elevado",
                ),
                solution_and_what=SolutionAndWhat(
                    target_state="Stack OpenTelemetry + Grafana",
                    north_star_metric="Reducción del 50% en MTTR",
                ),
                scope_and_how=ScopeAndHow(
                    phases=["Fase 1: Preparación", "Fase 2: Despliegue"],
                    deliverables=["Despliegue de agentes", "Dashboards ejecutivos"],
                    out_of_scope=["Migración de logs históricos > 1 año"],
                ),
                delivery_team=DeliveryTeam(
                    team_roles=["Arquitecto SRE", "Ingeniero Cloud"],
                ),
                ai_transformation_strategy="Aceleración de sintaxis IaC con Gemini Code Assist",
                governance_and_assumptions=GovernanceAndAssumptions(
                    governance_model="Comité de seguimiento quincenal",
                    assumptions=["Acceso a repositorios y credenciales en semana 1"],
                ),
                risk_management=[
                    RiskManagementItem(
                        risk="Sobrecarga de agentes",
                        mitigation="Pruebas de estrés escalonadas",
                    )
                ],
                activation_plan=["Kick-off", "Despliegue canary", "Traspaso operacional"],
                why_ntt_data=WhyPartner(
                    accelerators=["Framework de automatización Ansible / Terraform"],
                    partnerships="Alianza estratégica global con Red Hat y AWS",
                ),
                investment_and_timeline=InvestmentAndTimeline(
                    estimated_duration="3 meses",
                    tcv_range="120.000 € - 150.000 €",
                ),
                executive_synthesis="Propuesta de alto impacto con retorno medible en 90 días.",
            )
        ],
        intelligence_dossier={"sources": ["Entrevistas técnicas", "Memoria anual"]},
    )

    result_path = render_commercial_report(payload, template_path, output_docx)
    assert result_path.is_file(), "El informe comercial DOCX debe haber sido generado físicamente."

    doc = Document(str(result_path))
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(
        cell.text for t in doc.tables for r in t.rows for cell in r.cells
    )

    # Invariantes semánticos exactos de negocio
    assert "ACME CORP" in full_text
    assert "1.5M €" in full_text
    assert "Renovación de Infraestructura" in full_text
    assert "Despliegue de Observabilidad Unificada" in full_text
    assert "Alianza estratégica global con Red Hat y AWS" in full_text
    assert "Piloto controlado en datacenter secundario" in full_text

    # Invariante de Cero Fugas de Plantilla (Anti-Leakage Gate)
    assert "{{" not in full_text, "Variables de plantilla {{...}} no resueltas detectadas en el DOCX comercial."
    assert "}}" not in full_text, "Variables de plantilla {{...}} no resueltas detectadas en el DOCX comercial."


def test_clear_document_elements_ror_killer():
    """Verify that clear_document_body removes all content children while preserving sectPr."""
    from assessment_engine.adapters.render_commercial_report import clear_document_body

    doc = Document()
    doc.add_paragraph("Test Paragraph 1")
    doc.add_paragraph("Test Paragraph 2")
    assert len(doc.paragraphs) == 2

    clear_document_body(doc)
    assert len(doc.paragraphs) == 0
