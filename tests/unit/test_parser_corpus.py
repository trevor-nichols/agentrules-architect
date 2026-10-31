"""Representative Phase 2 outputs that must survive parser fallback."""

import json
from pathlib import Path

from agentrules.core.utils.parsers.agent_parser import parse_agents_from_phase2

CORPUS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "parser_corpus"


def test_structured_phase2_output_preserves_assignments() -> None:
    payload = json.loads((CORPUS_DIR / "structured_agents.json").read_text(encoding="utf-8"))

    agents = parse_agents_from_phase2(payload)

    assert [(agent["id"], agent["name"], agent["file_assignments"]) for agent in agents] == [
        ("agent_1", "Entry Points", ["src/main.py"]),
        ("agent_2", "Configuration", ["src/config.py"]),
    ]


def test_malformed_xml_fallback_recovers_file_assignment() -> None:
    response = {"plan": (CORPUS_DIR / "malformed_xml.md").read_text(encoding="utf-8")}

    agents = parse_agents_from_phase2(response)

    assert len(agents) == 1
    assert agents[0]["id"] == "agent_1"
    assert agents[0]["name"] == "Build & Release"
    assert agents[0]["file_assignments"] == ["src/main.py"]
