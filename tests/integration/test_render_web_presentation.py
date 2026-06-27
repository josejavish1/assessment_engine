from __future__ import annotations

import re
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from assessment_engine.adapters.render_web_presentation import (
    _render_html,  # noqa: E402
)


def test_strategic_terminal_is_self_contained_and_splits_dto_state() -> None:
    html = _render_html("redeia", _sample_nexus_data())

    assert "https://d3js.org" not in html
    assert "fonts.googleapis.com" not in html
    assert "cdnjs.cloudflare.com" not in html
    assert 'id="nexus-data"' in html
    assert 'id="dto-state"' in html

    nexus_json = _script_json(html, "nexus-data")
    dto_json = _script_json(html, "dto-state")
    assert '"dto_state"' not in nexus_json
    assert '"strategy"' in nexus_json
    assert '"topology"' in dto_json
    assert "Nodo critico" in dto_json


def test_strategic_terminal_escapes_json_for_script_blocks() -> None:
    payload = _sample_nexus_data()
    payload["strategy"]["narrative"] = "</script><script>alert('x')</script>"

    html = _render_html("redeia", payload)
    nexus_json = _script_json(html, "nexus-data")

    assert "</script>" not in nexus_json
    assert "\\u003c/script\\u003e" in nexus_json


def _script_json(html: str, script_id: str) -> str:
    match = re.search(
        rf'<script id="{script_id}" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def _sample_nexus_data() -> dict:
    return {
        "meta": {"client": "REDEIA", "version": "test"},
        "strategy": {
            "headline": "Redeia executive headline",
            "narrative": "Redeia executive narrative",
            "global_score": "3.0",
            "burning_platform": [{"theme": "risk"}],
        },
        "roadmap": {
            "horizons": {
                "quick_wins_0_3_months": [
                    {
                        "title": "Primer entregable",
                        "business_case": "Caso ejecutivo",
                        "start_month": 0,
                        "duration_months": 3,
                    }
                ]
            }
        },
        "heatmap": [{"id": "T5", "name": "Continuity", "score": "3.0"}],
        "towers": {},
        "dto_state": {
            "meta": {"client": "redeia"},
            "topology": {
                "nodes": [
                    {
                        "id": "risk-1",
                        "label": "Nodo critico",
                        "type": "RISK",
                        "score": None,
                        "tower_id": "T5",
                        "metadata": {},
                    },
                    {
                        "id": "initiative-1",
                        "label": "Entregable ejecutivo",
                        "type": "INITIATIVE",
                        "score": None,
                        "tower_id": "T5",
                        "metadata": {},
                    },
                ],
                "edges": [
                    {
                        "source": "initiative-1",
                        "target": "risk-1",
                        "relation": "ADDRESSES",
                    }
                ],
            },
            "roadmap": [
                {
                    "wave": "Wave 0: Foundation",
                    "projects": ["initiative-1"],
                }
            ],
        },
    }
