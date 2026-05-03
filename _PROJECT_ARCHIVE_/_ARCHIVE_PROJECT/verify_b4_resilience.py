import json
import logging
import sys
from pathlib import Path
from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.scripts.lib.contract_utils import robust_load_payload

# Configurar logging para ver las alertas de B4
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def test_resilience():
    print("\n--- INICIO PRUEBA DE RESILIENCIA B4 ---")

    # 1. Preparar un JSON "Roto" (Simulando fallo de IA)
    base_path = Path("working/smoke_ivirma/T5/approved_annex_t5.template_payload.json")
    with open(base_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # BORRADO INTENCIONADO DE CAMPOS OBLIGATORIOS
    print("💣 Borrando campos obligatorios: 'client_name' y 'executive_summary'...")
    if "client_name" in data:
        del data["client_name"]
    if "executive_summary" in data:
        del data["executive_summary"]

    broken_path = Path("working/smoke_ivirma/T5/BROKEN_PAYLOAD_TEST.json")
    with open(broken_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # 2. Intentar cargar con el validador B4
    print("⏳ Intentando cargar el JSON roto con robust_load_payload...")
    try:
        # Esto es lo que hacen ahora los renderizadores de Word
        payload = robust_load_payload(broken_path, AnnexPayload, "Annex Test")

        print("\n✅ RESULTADO: El sistema NO ha petado (Resiliencia B4 activa).")
        print(f"   - Tipo de objeto devuelto: {type(payload)}")
        print(
            f"   - ¿Tiene metadatos?: {'Sí' if payload.generation_metadata else 'No'}"
        )

        # Verificar que el objeto existe aunque falten campos
        if (
            not hasattr(payload, "executive_summary")
            or payload.executive_summary is None
        ):
            print(
                "   - Confirmado: El campo 'executive_summary' falta pero el objeto es usable."
            )

    except Exception as e:
        print(f"\n❌ ERROR: El sistema ha fallado (B4 no está funcionando): {e}")
        sys.exit(1)

    print("\n--- FIN PRUEBA DE RESILIENCIA B4 ---")


if __name__ == "__main__":
    test_resilience()
