import json
from pathlib import Path

from scripts.build_california_kb import BASE_DIR, INDEX_DIR, parse_enforcement_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_press_release_classified_as_press_release():
    item = parse_enforcement_html((FIXTURES / "enforcement_sample.html").read_text(encoding="utf-8"))

    assert item["authority_type"] == "press_release"
    assert item["agency"] == "California Office of the Attorney General"
    assert item["matter_name"]


def test_cited_statutes_resolve_through_citation_map():
    item = parse_enforcement_html((FIXTURES / "enforcement_sample.html").read_text(encoding="utf-8"))
    citation_map = json.loads((INDEX_DIR / "ca-citation-map.json").read_text(encoding="utf-8"))["citations"]

    indexed_ids = set(citation_map.values())
    for cited_statute in item["cited_statutes"]:
        assert cited_statute in indexed_ids

    assert BASE_DIR.name == "us-ca"
