from pathlib import Path

import pytest

from scripts.build_california_kb import parse_statute_pdf_text


FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_three_sections():
    text = (FIXTURES / "statute_sample.txt").read_text(encoding="utf-8")
    sections = parse_statute_pdf_text(text)

    assert {section["section"] for section in sections} == {"1798.100", "1798.105", "1798.199.100"}


def test_preserves_subdivision_markers():
    text = (FIXTURES / "statute_sample.txt").read_text(encoding="utf-8")
    section = next(item for item in parse_statute_pdf_text(text) if item["section"] == "1798.100")

    assert "(a)" in section["body"]
    assert "(1)" in section["body"]


def test_missing_seed_section_raises():
    with pytest.raises(ValueError, match="missing seed sections"):
        parse_statute_pdf_text("1798.100. Stub.\n", seed_sections=["1798.100", "1798.105"])
