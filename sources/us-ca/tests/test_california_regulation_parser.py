from pathlib import Path

from scripts.build_california_kb import parse_regulation_pdf_text


FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_regulation_sections():
    text = (FIXTURES / "regulation_sample.txt").read_text(encoding="utf-8")
    sections = parse_regulation_pdf_text(text)

    assert {section["section"] for section in sections} == {"7002", "7025", "7150"}


def test_extracts_authority_cited_block():
    text = (FIXTURES / "regulation_sample.txt").read_text(encoding="utf-8")
    section = next(item for item in parse_regulation_pdf_text(text) if item["section"] == "7002")

    assert section["authority_cited"]
    assert "ca-civ-1798.185" in section["authority_cited"]
