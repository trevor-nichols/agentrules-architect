import json
import xml.etree.ElementTree as ET

from core.utils.parsers.agent_parser import (
    extract_from_json,
    extract_from_markdown_block,
    clean_and_fix_xml,
    parse_agent_definition,
    parse_agents_from_phase2,
)


def test_extract_from_json_dict_and_string():
    assert extract_from_json({"plan": "X"}) == "X"
    assert extract_from_json({"nope": 1}) == ""

    assert extract_from_json('{"plan": "P"}') == "P"
    assert extract_from_json("not-json") == "not-json"


def test_extract_from_markdown_block_three_and_four_backticks():
    three = """```xml\n<analysis_plan>ok</analysis_plan>\n```"""
    four = """````xml\n<analysis_plan>ok4</analysis_plan>\n```"""
    assert extract_from_markdown_block(three).startswith("<analysis_plan>")
    assert extract_from_markdown_block(four).startswith("<analysis_plan>")


def test_clean_and_fix_xml_fixes_attributes_and_wraps():
    raw = (
        '<agent_1="Agent & Co">\n'
        "  <description>Uses A & B</description>\n"
        "  <file_assignments>\n"
        "    <file_path>a.py</file_path>\n"
        "  </file_assignments>\n"
        "</agent_1>"
    )
    fixed = clean_and_fix_xml(raw)
    assert fixed.startswith("<analysis_plan>")
    assert '<agent_1 name="Agent &amp; Co">' in fixed
    assert "Uses A &amp; B" in fixed


def test_parse_agent_definition_minimal():
    xml = (
        "<agent_1>"
        "  <name>Alpha</name>"
        "  <description>desc</description>"
        "  <expertise>python, js</expertise>"
        "  <responsibilities>"
        "    <responsibility>r1</responsibility>"
        "    <responsibility>r2</responsibility>"
        "  </responsibilities>"
        "  <file_assignments>"
        "    <file_path>file.py</file_path>"
        "    <file_path> </file_path>"
        "  </file_assignments>"
        "</agent_1>"
    )
    elem = ET.fromstring(xml)
    info = parse_agent_definition(elem)
    assert info["id"] == "agent_1"
    assert info["name"] == "Alpha"
    assert info["description"] == "desc"
    assert info["expertise"] == ["python", "js"]
    assert info["responsibilities"] == ["r1", "r2"]
    assert info["file_assignments"] == ["file.py"]


def test_parse_agents_from_phase2_preparsed_and_markdown_xml():
    # Pre-parsed path returns as-is
    inp = {"agents": [{"id": "agent_1", "file_assignments": ["a.py"]}]}
    out = parse_agents_from_phase2(inp)
    assert out == inp["agents"]

    # Markdown-wrapped XML
    md = (
        "```xml\n"
        "<analysis_plan>\n"
        "  <agent_1 name=\"A\">\n"
        "    <file_assignments><file_path>a.py</file_path></file_assignments>\n"
        "  </agent_1>\n"
        "</analysis_plan>\n"
        "```"
    )
    out2 = parse_agents_from_phase2({"plan": md})
    assert isinstance(out2, list) and len(out2) == 1
    assert out2[0]["id"].startswith("agent_")
    assert out2[0]["file_assignments"] == ["a.py"]

