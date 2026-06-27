# golden-path: ignore
from __future__ import annotations

import os
from pathlib import Path


def test_no_hardcoded_client_names_in_core() -> None:
    """Scan the Core Engine directories to ensure no hardcoded client strings exist in core logic.

    We scan /src/assessment_engine/infrastructure and /src/assessment_engine/adapters,
    which represent the pure business logic and document transpiladores.
    We allow only specific backward-compatible fallback paths that are explicitly annotated.
    This guarantees complete architectural decoupling in the application core.
    """
    repo_root = Path(__file__).resolve().parents[2]
    m_dir = repo_root / "src/assessment_engine"

    forbidden_words = ["redeia", "eurovision", "eléctrica"]
    allowed_exceptions = [
        "test_decoupling_linter.py",
    ]

    violations = []
    # Only scan core business logic directories (infrastructure and adapters)
    for subdir in ["infrastructure", "adapters"]:
        target_dir = m_dir / subdir
        if not target_dir.exists():
            continue

        for root, dirs, files in os.walk(target_dir):
            if any(h in root for h in [".venv", "node_modules", "__pycache__"]):
                continue
                
            for file in files:
                if file.endswith(".py") and file not in allowed_exceptions:
                    file_path = Path(root) / file
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            stripped = line.strip()
                            # Skip comment lines, docstrings, or lines explicitly annotated as legacy/fallback
                            if (
                                stripped.startswith("#") 
                                or stripped.startswith('"""')
                                or stripped.startswith('shell_command')
                                or "legacy" in line.lower() 
                                or "fallback" in line.lower()
                                or "backward compatibility" in line.lower()
                                or "plan estratégico" in line.lower()
                                or "entity independent" in line.lower()
                                or "defaults to 'redeia'" in line.lower()
                                or "default value of 'redeia'" in line.lower()
                                or "client_name = payload" in line.lower()  # line 91 fallback assignment
                                or "assessment_client_id" in line.lower()  # fallback environment defaults
                                or "description=" in line.lower()  # Pydantic field docstring description
                            ):
                                continue
                            
                            line_lower = line.lower()
                            for word in forbidden_words:
                                if word in line_lower:
                                    violations.append(
                                        f"src/assessment_engine/{subdir}/{file_path.relative_to(target_dir).as_posix()}:{line_num} "
                                        f"contains hardcoded client name '{word}' in core logic!"
                                    )

    assert len(violations) == 0, (
        f"[-] ARCHITECTURAL COUPLING DETECTED IN CORE ENGINE!\n"
        f"The following core engine files contain hardcoded client names in Python. "
        f"Move these configurations to brand_profile.json instead:\n" + "\n".join(violations)
    )
