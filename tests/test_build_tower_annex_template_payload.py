import json

from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.scripts.build_tower_annex_template_payload import main
from tests.artifact_helpers import ROOT, require_artifact_es

INPUT_PATH = ROOT / "working" / "ivirma" / "T5" / "approved_annex_t5.refined.json"


def test_build_tower_annex_template_payload_matches_schema(tmp_path):
    output_path = tmp_path / "approved_annex_t5.template_payload.json"

    main(
        [
            "build_tower_annex_template_payload",
            str(require_artifact_es(INPUT_PATH)),
            str(output_path),
            "ivirma",
            "short",
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    validated = AnnexPayload.model_validate(payload)

    assert validated.executive_summary.headline
    assert isinstance(validated.executive_summary.summary_body, str)
    assert validated.executive_summary.key_business_impacts
    assert validated.domain_introduction.technological_domain
