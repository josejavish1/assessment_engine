from pathlib import Path

import yaml  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "assessment_engine" / "prompts" / "registry"


def _load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_prompt_registry_files_load():
    files = sorted(REGISTRY_DIR.glob("*.yaml"))
    assert files, "No YAML prompt files found in registry"
    for path in files:
        data = _load_yaml(path)
        assert isinstance(data, dict), f"{path.name} must load as a mapping"
        assert data, f"{path.name} must not be empty"


def test_annex_executive_synthesizer_prompt_shape():
    path = REGISTRY_DIR / "annex_executive_synthesizer.yaml"
    data = _load_yaml(path)
    required = [
        "role",
        "expertise",
        "mission",
        "context_description",
        "task",
        "instructions",
        "tone_rules",
        "handover",
    ]
    for key in required:
        assert key in data, f"Missing key {key} in {path.name}"
    assert isinstance(data["instructions"], list) and data["instructions"]
    assert isinstance(data["tone_rules"], list) and data["tone_rules"]


def test_blueprint_prompt_shapes():
    expected_keys = {
        "blueprint_architect_instruction.yaml": [
            "role",
            "expertise",
            "mission",
            "critical_rules",
        ],
        "blueprint_pilar_architect_prompt.yaml": [
            "role",
            "context_description",
            "task",
            "golden_rules",
        ],
        "blueprint_closing_orchestrator_prompt.yaml": [
            "role",
            "task_and_tone",
            "structure_requirements",
        ],
    }
    for filename, keys in expected_keys.items():
        data = _load_yaml(REGISTRY_DIR / filename)
        for key in keys:
            assert key in data, f"Missing key {key} in {filename}"
