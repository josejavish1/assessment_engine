from __future__ import annotations

from assessment_engine.domain.schemas.blueprint import TargetArchitectureToBe


def test_target_architecture_tobe_levers_contract() -> None:
    """Verifica que el esquema TargetArchitectureToBe contiene los campos de palancas estructurados y hereda valores por defecto correctos."""
    # Instanciamos con solo el campo requerido 'vision'
    tobe = TargetArchitectureToBe(
        vision="Visión de infraestructura moderna e inmutable"
    )

    # Validamos que los tres campos de palancas existen y se inicializan como listas vacías por defecto
    assert isinstance(tobe.levers_technology, list)
    assert isinstance(tobe.levers_process, list)
    assert isinstance(tobe.levers_operation, list)

    # Validamos que podemos poblar datos estructurados de palancas
    tobe_populated = TargetArchitectureToBe(
        vision="Visión de nube híbrida soberana",
        levers_technology=["AWS Resilience Hub", "EC2 Auto Scaling"],
        levers_process=["ITIL v4 Change Management", "SRE Blameless Post-Mortems"],
        levers_operation=["Guardias 24x7 integradas en NOC", "Formación en AWS SysOps"],
    )

    assert len(tobe_populated.levers_technology) == 2
    assert "AWS Resilience Hub" in tobe_populated.levers_technology
    assert "ITIL v4 Change Management" in tobe_populated.levers_process
    assert "Formación en AWS SysOps" in tobe_populated.levers_operation
