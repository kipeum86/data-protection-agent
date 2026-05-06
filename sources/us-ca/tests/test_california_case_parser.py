from pathlib import Path

from scripts.build_california_kb import parse_case_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_state_appellate_published_metadata():
    case = parse_case_html((FIXTURES / "case_sample_state.html").read_text(encoding="utf-8"))

    assert case["court_system"] == "state"
    assert case["precedential_status"] == "published_citable"
    assert case["authority_level"] == "binding_ca_appellate"


def test_federal_district_marked_persuasive():
    case = parse_case_html((FIXTURES / "case_sample_federal.html").read_text(encoding="utf-8"))

    assert case["court_system"] == "federal"
    assert case["authority_level"] == "persuasive"
    assert case["precedential_status"] == "district_court_persuasive"


def test_state_unpublished_metadata():
    case = parse_case_html((FIXTURES / "case_sample_unpublished.html").read_text(encoding="utf-8"))

    assert case["precedential_status"] == "unpublished_non_citable"
