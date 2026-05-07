"""Unit tests for the authority detail CLI."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "who-is.py"

spec = importlib.util.spec_from_file_location("who_is", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_who_is_ca_known_authority():
    result = mod.who_is("ca-civ-1798.150")
    assert result["jurisdiction"] == "us-ca"
    assert "error" not in result, result.get("error")
    assert result["path"].endswith(".md")
    assert result["frontmatter"]
    assert "id" in result["frontmatter"]


def test_who_is_eu_gdpr_article():
    result = mod.who_is("gdpr-art6")
    assert result["jurisdiction"] == "eu-gdpr"
    assert "error" not in result, result.get("error")
    assert result["body_excerpt"]
    assert result["total_citations"] > 0


def test_who_is_kr_article_via_index():
    result = mod.who_is("pipa-art15")
    assert result["jurisdiction"] == "kr-pipa"
    if "error" in result:
        # If KR sub-KB not imported, accept the path-not-found error
        assert "No path" in result["error"] or "missing" in result["error"]
    else:
        assert result["frontmatter"]


def test_who_is_unknown_id_errors():
    result = mod.who_is("totally-fake-id-xyz")
    assert result["jurisdiction"] == "unknown"
    assert "error" in result


def test_parse_frontmatter_basic():
    text = '---\nid: foo\ntitle: "Bar"\n---\nBody here.'
    fm, body = mod.parse_frontmatter_and_body(text)
    assert fm["id"] == "foo"
    assert fm["title"] == "Bar"
    assert body.startswith("Body here.")


def test_parse_frontmatter_missing_returns_empty():
    text = "No frontmatter here, just body."
    fm, body = mod.parse_frontmatter_and_body(text)
    assert fm == {}
    assert body.startswith("No frontmatter")
