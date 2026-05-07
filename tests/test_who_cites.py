"""Unit tests for the reverse citation lookup CLI."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "who-cites.py"

spec = importlib.util.spec_from_file_location("who_cites", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_jurisdiction_routing():
    assert mod.jurisdiction_for("ca-civ-1798.150") == "us-ca"
    assert mod.jurisdiction_for("us-fed-graham-v-noom") == "us-ca"
    assert mod.jurisdiction_for("pipa-art15") == "kr-pipa"
    assert mod.jurisdiction_for("network-act-art10") == "kr-pipa"
    assert mod.jurisdiction_for("gdpr-art6") == "eu-gdpr"
    assert mod.jurisdiction_for("a-precedent-c-131-12") == "eu-gdpr"
    assert mod.jurisdiction_for("totally-unknown") == "unknown"


def test_who_cites_known_ca_authority():
    """ca-civ-1798.150 (private right of action) is most-cited per v11 report."""
    result = mod.who_cites("ca-civ-1798.150")
    assert result["jurisdiction"] == "us-ca"
    assert result["total_citations"] > 0
    cit = result["citations"]
    assert cit["golden_questions"] or cit["topics"]


def test_who_cites_eu_gdpr_article():
    """gdpr-art6 (lawful basis) is most-cited per v12 report (66 refs)."""
    result = mod.who_cites("gdpr-art6")
    assert result["jurisdiction"] == "eu-gdpr"
    assert result["total_citations"] > 0
    cit = result["citations"]
    assert cit["cases"] or cit["edpb_docs"]


def test_who_cites_unknown_authority_returns_error():
    result = mod.who_cites("totally-fake-id-xyz")
    assert result["jurisdiction"] == "unknown"
    assert "error" in result
    assert result["total_citations"] == 0


def test_who_cites_kr_article():
    """KR pipa-art15 should resolve to kr-pipa and search cross-ref-graph."""
    result = mod.who_cites("pipa-art15")
    assert result["jurisdiction"] == "kr-pipa"
    assert "cross_reference_edges" in result["citations"]
