"""Prototype demonstrating Reverse-FAIR Actuarial Synthesis with deterministic math anchoring.

Evaluates two contrasting enterprise profiles:
1. Starling Bank (UK FinTech, GBP £, 100% AWS cloud-native)
2. Rede D'Or São Luiz (Brazil Healthcare, BRL R$, On-premise clinical hospital core)

Enforces:
- Deterministic Python pre-computation of all loss figures (Zero Hallucinated Math)
- Causal engineering threat titles (Zero Generic Formulaic Rubrics)
- Tech-stack grounded failure modes citing real transcript evidence
- 100% native language synthesis (EN for Starling, PT for Rede D'Or)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)


def test_starling_bank_reverse_fair() -> dict[str, any]:
    """Test Case 1: Starling Bank - Payment Ledger Failover."""
    # Deterministic Python Actuarial Calculations (Immutable Physical Constants)
    hourly_rate = 140000.0  # £140,000/hr
    downtime_minutes = 23
    stoppage_loss = 32000.0  # Direct transactional stoppage
    sre_burn = 18000.0       # Senior SRE ledger reconciliation labor
    sla_penalty = 5000.0     # Pay.UK / Vocalink clearing SLA penalty
    total_sle = stoppage_loss + sre_burn + sla_penalty  # £55,000.00
    lef = 0.80               # 1 incident every 1.25 years
    ale = round(total_sle * lef, 2)  # £44,000.00

    transcript_excerpt = """
    Edward Albright (CTO): We operate a 100% cloud-native architecture on AWS across London (eu-west-2) and Ireland (eu-west-1).
    Our primary database layer is Amazon Aurora Global PostgreSQL. Cross-region replication latency sits at approximately 180ms.
    We run our proprietary core banking ledger, 'ApexLedger', in Go and Java 21 on an event-sourcing model backed by Apache Kafka.
    In unannounced DR simulations, Route 53 Application Recovery Controller shifted traffic in 3m40s.
    Our biggest headache under DORA is managing cross-region state synchronization and preventing split-brain states in Kafka offsets during unscripted failovers.
    """

    prompt = f"""You are a Principal SRE and Quantitative Risk Assessor conducting a formal Open FAIR audit for Starling Bank.
You must synthesize a specific, highly credible Risk Card in British English based strictly on the transcript evidence and exact pre-computed actuarial numbers.

IMMUTABLE ACTUARIAL CONSTANTS (CALCULATED DETERMINISTICALLY BY PYTHON):
- Target Currency: GBP (£)
- Baseline Downtime Rate: £{hourly_rate:,.2f}/hr
- Incident Recovery Duration: {downtime_minutes} minutes
- Direct Operational Stoppage Loss: £{stoppage_loss:,.2f}
- Emergency SRE & Engineering Recovery Burn: £{sre_burn:,.2f}
- Clearing / Scheme SLA Breach Penalty: £{sla_penalty:,.2f}
- Single Loss Expectancy (SLE): £{total_sle:,.2f}
- Loss Event Frequency (LEF): {lef:.2f} events/year (1 incident every 1.25 years)
- Annualized Loss Expectancy (ALE): £{ale:,.2f}/year

TRANSCRIPT EXCERPT:
{transcript_excerpt}

MANDATORY OUTPUT FORMAT (Raw JSON only):
{{
  "risk_id": "RSK-T05-01",
  "causal_risk_title": "<Specific threat statement following: [Exact Component Failure] leading to [Specific Operational Impact]. BANNED: Do NOT use formulaic titles like 'Operational Risk Scenario: ...'>",
  "technical_failure_mechanism": "<Deep technical explanation citing Amazon Aurora Global PostgreSQL, Kafka offsets, and Route 53 ARC from the transcript, explaining the exact sequence of events causing the {downtime_minutes}-minute disruption>",
  "actuarial_justification": "<Cohesive narrative explaining exactly why the £{total_sle:,.2f} SLE and £{ale:,.2f}/year ALE occur, explicitly decomposing the £{stoppage_loss:,.2f} stoppage, £{sre_burn:,.2f} SRE burn, and £{sla_penalty:,.2f} SLA penalty within Starling Bank's Faster Payments clearing context>",
  "remediation_architecture": "<Concrete engineering solution referencing DORA Article 11, automated Route 53 ARC health checks, and Kafka mirror-maker reconciliation>"
}}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    raw = response.text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())


def test_rede_dor_reverse_fair() -> dict[str, any]:
    """Test Case 2: Rede D'Or - Hospital Clinical ERP Outage."""
    # Deterministic Python Actuarial Calculations (Immutable Physical Constants)
    hourly_rate = 420000.0   # R$ 420.000/h
    downtime_minutes = 45
    stoppage_loss = 180000.0 # Parada clínica de centro cirúrgico e UTI
    recovery_burn = 65000.0  # Equipe de banco de dados e contingência manual
    compliance_cost = 15000.0 # Notificação regulatória ANVISA e auditoria LGPD
    total_sle = stoppage_loss + recovery_burn + compliance_cost  # R$ 260.000,00
    lef = 0.35               # 1 incidente a cada 2.85 anos
    ale = round(total_sle * lef, 2)  # R$ 91.000,00

    transcript_excerpt = """
    Dr. Henrique Coutinho (Diretor Executivo de TI): A Rede D'Or opera 73 hospitais e 11.500 leitos ativos.
    Nossa infraestrutura suporta o prontuário eletrônico Philips Tasy e MV Soul sobre bancos Oracle em servidores Dell PowerEdge e Cisco UCS.
    Nosso custo de parada clínica é de R$ 420.000 por hora.
    Mariana Castro (Infraestrutura): No datacenter de Pinheiros temos geradores e nobreaks robustos, mas em hospitais regionais os nobreaks têm apenas 12 minutos de autonomia.
    Em T4, o storage SAN Dell EMC Unity armazena 1,2 PB de imagens PACS.
    Carlos Eduardo (CISO): Backups usam Veeam com fitas LTO, mas testes de restauração do banco Tasy levaram mais de 6 horas em simulação recente.
    """

    prompt = f"""Você é o Arquiteto Líder de Cibersegurança e Avaliador Atuarial realizando uma auditoria formal Open FAIR para a Rede D'Or São Luiz.
Sintetize uma Ficha de Risco específica e altamente crível em Português do Brasil com base estrita no depoimento da entrevista e nos cálculos atuariais pré-computados.

CONSTANTES ATUARIAIS IMUTÁVEIS (CALCULADAS PELO PYTHON):
- Moeda: BRL (R$)
- Custo Horário de Parada Clínica: R$ {hourly_rate:,.2f}/h
- Duração do Incidente: {downtime_minutes} minutos
- Prejuízo de Parada Assistencial Direta: R$ {stoppage_loss:,.2f}
- Custo de Contingência e Recuperação de Banco de Dados: R$ {recovery_burn:,.2f}
- Custos Regulatórios e Notificação ANVISA/ANS: R$ {compliance_cost:,.2f}
- Single Loss Expectancy (SLE): R$ {total_sle:,.2f}
- Loss Event Frequency (LEF): {lef:.2f} eventos/ano (1 incidente a cada 2.85 anos)
- Annualized Loss Expectancy (ALE): R$ {ale:,.2f}/ano

TRECHO DA ENTREVISTA:
{transcript_excerpt}

FORMATO OBRIGATÓRIO DE SAÍDA (Apenas JSON válido):
{{
  "risk_id": "RSK-T04-01",
  "causal_risk_title": "<Título de ameaça causal no padrão: [Falha de Componente Específico] provocando [Impacto Operacional Específico]. PROIBIDO usar títulos genéricos como 'Cenário de Risco Operacional:...'>",
  "technical_failure_mechanism": "<Explicação técnica detalhada citando o ERP Philips Tasy, banco de dados Oracle, storage Dell EMC e autonomia de nobreak dos hospitais regionais, detalhando o modo de falha>",
  "actuarial_justification": "<Narrativa coesa justificando exatamente por que ocorrem os valores de R$ {total_sle:,.2f} de SLE e R$ {ale:,.2f}/ano de ALE, decompondo os R$ {stoppage_loss:,.2f} de parada clínica, R$ {recovery_burn:,.2f} de contingência e R$ {compliance_cost:,.2f} regulatórios no contexto hospitalar da Rede D'Or>",
  "remediation_architecture": "<Solução concreta de engenharia citando LGPD, RDC ANVISA 50 e replicação contínua imutável>"
}}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    raw = response.text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())


def main() -> None:
    print("=" * 80)
    print("EXECUTING REVERSE-FAIR PROTOTYPE: STARLING BANK (UK FINTECH)")
    print("=" * 80)
    res_starling = test_starling_bank_reverse_fair()
    print(f"\nRisk ID: {res_starling['risk_id']}")
    print(f"Title:   {res_starling['causal_risk_title']}")
    print(f"\nTechnical Failure Mechanism:\n{res_starling['technical_failure_mechanism']}")
    print(f"\nActuarial Justification (Bottom-Up Loss Decomposition):\n{res_starling['actuarial_justification']}")
    print(f"\nRemediation Architecture:\n{res_starling['remediation_architecture']}")

    # Validation: Check that Python scalars are cited exactly
    assert "£44,000" in res_starling["actuarial_justification"] or "£44,000.00" in res_starling["actuarial_justification"] or "44,000" in res_starling["actuarial_justification"]
    assert "£55,000" in res_starling["actuarial_justification"] or "55,000" in res_starling["actuarial_justification"]
    print("\n✓ Starling Bank: Exact mathematical scalar citation verified!")

    print("\n" + "=" * 80)
    print("EXECUTING REVERSE-FAIR PROTOTYPE: REDE D'OR SÃO LUIZ (BRAZIL HEALTHCARE)")
    print("=" * 80)
    res_rededor = test_rede_dor_reverse_fair()
    print(f"\nRisk ID: {res_rededor['risk_id']}")
    print(f"Title:   {res_rededor['causal_risk_title']}")
    print(f"\nTechnical Failure Mechanism:\n{res_rededor['technical_failure_mechanism']}")
    print(f"\nActuarial Justification (Bottom-Up Loss Decomposition):\n{res_rededor['actuarial_justification']}")
    print(f"\nRemediation Architecture:\n{res_rededor['remediation_architecture']}")

    # Validation: Check that Python scalars are cited exactly
    assert "91.000" in res_rededor["actuarial_justification"] or "91,000" in res_rededor["actuarial_justification"]
    assert "260.000" in res_rededor["actuarial_justification"] or "260,000" in res_rededor["actuarial_justification"]
    print("\n✓ Rede D'Or: Exact mathematical scalar citation verified in Portuguese!")


if __name__ == "__main__":
    main()
