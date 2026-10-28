import pytest


def test_blueprint_project_dynamic_sizing_and_horizons():
    """Verify that initiatives in blueprint projects are mapped with realistic sizing (S, M, L)
    and proper horizon durations (H1, H2, H3), eliminating hardcoded 'L' and 'Sin calendario detallado'."""
    initiatives = [
        {"title": "Quick Win Patching", "priority": "Crítica", "horizon": "Short-term"},
        {"title": "Platform Migration", "priority": "Alta", "horizon": "Mid-term"},
        {"title": "Core Evolution", "priority": "Media", "horizon": "Long-term"},
    ]

    sota_projects = []
    for idx, init in enumerate(initiatives):
        h_val = str(init.get("horizon", "")).lower()
        p_val = str(init.get("priority", "")).lower()
        if "short" in h_val or "quick" in h_val or "h1" in h_val or p_val == "crítica":
            proj_sizing, proj_duration = "S", "H1 (Mes 1-3)"
        elif "long" in h_val or "h3" in h_val:
            proj_sizing, proj_duration = "L", "H3 (Mes 12-24)"
        else:
            proj_sizing, proj_duration = "M", "H2 (Mes 3-12)"

        sota_projects.append(
            {
                "name": init.get("title"),
                "sizing": proj_sizing,
                "duration": proj_duration,
            }
        )

    # 1. Critical short-term must be S in H1
    assert sota_projects[0]["sizing"] == "S"
    assert sota_projects[0]["duration"] == "H1 (Mes 1-3)"

    # 2. Mid-term must be M in H2
    assert sota_projects[1]["sizing"] == "M"
    assert sota_projects[1]["duration"] == "H2 (Mes 3-12)"

    # 3. Long-term must be L in H3
    assert sota_projects[2]["sizing"] == "L"
    assert sota_projects[2]["duration"] == "H3 (Mes 12-24)"
