"""Unit tests for cross-jurisdiction citation auditor."""

from cross_jurisdiction_auditor.audit import (
    audit,
    detect_cited_jurisdictions,
    detect_jurisdictions_from_signals,
    jurisdiction_for_id,
)


def test_detect_jurisdiction_from_ccpa_signal():
    s = detect_jurisdictions_from_signals("CCPA grants consumers the right to delete.")
    assert "us-ca" in s


def test_detect_jurisdiction_from_korean_signal():
    s = detect_jurisdictions_from_signals("개인정보 보호법에 따라 동의를 받는다.")
    assert "kr-pipa" in s


def test_detect_jurisdiction_from_gdpr_signal():
    s = detect_jurisdictions_from_signals("GDPR Article 6 sets lawful bases.")
    assert "eu-gdpr" in s


def test_jurisdiction_for_id_ca():
    assert jurisdiction_for_id("ca-civ-1798.150") == "us-ca"
    assert jurisdiction_for_id("us-fed-graham-v-noom") == "us-ca"
    assert jurisdiction_for_id("ca-supreme-smith-v-loanme-2021") == "us-ca"


def test_jurisdiction_for_id_kr():
    assert jurisdiction_for_id("pipa-art15") == "kr-pipa"
    assert jurisdiction_for_id("network-act-enforcement-rule-art3") == "kr-pipa"
    assert jurisdiction_for_id("pipc-guideline-1") == "kr-pipa"


def test_jurisdiction_for_id_eu():
    assert jurisdiction_for_id("gdpr-art6") == "eu-gdpr"
    assert jurisdiction_for_id("a-precedent-c-131-12-google-spain") == "eu-gdpr"
    assert jurisdiction_for_id("a-guideline-guidelines-01-2020") == "eu-gdpr"
    assert jurisdiction_for_id("eu-ai-act-art5") == "eu-gdpr"


def test_ca_only_signal_with_gdpr_citation_warns():
    """California 답변에 GDPR 인용 섞이면 v6까지는 silent. v7이 잡음."""
    text = "Under CCPA, businesses must honor opt-out. See gdpr-art6 for parallels."
    result = audit(text)
    assert result["status"] == "warn"
    assert any(
        "Authority from eu-gdpr" in f["message"] for f in result["findings"]
    )


def test_kr_only_signal_with_ca_citation_warns():
    text = "개인정보 보호법 제15조에 따라 동의를 받는다. ca-civ-1798.150 also relevant."
    result = audit(text)
    assert any(
        "Authority from us-ca" in f["message"] for f in result["findings"]
    )


def test_multi_jurisdiction_comparative_passes():
    """비교 답변은 false positive 안 떠야."""
    text = (
        "GDPR Article 6 sets lawful bases. CCPA does not have an analogous "
        "concept; ca-civ-1798.100 covers notice instead."
    )
    result = audit(text)
    routing_findings = [
        f for f in result["findings"] if "Authority from" in f["message"]
    ]
    assert not routing_findings


def test_no_signal_no_finding():
    """Routing terms 없으면 의도 판단 불가, skip."""
    text = "Privacy is important. Article 5 of some law applies."
    result = audit(text)
    routing_findings = [
        f for f in result["findings"] if "Authority from" in f["message"]
    ]
    assert not routing_findings


def test_detect_cited_jurisdictions_finds_all_three():
    text = "ca-civ-1798.150, gdpr-art6, and pipa-art15 are all relevant."
    cited = detect_cited_jurisdictions(text)
    assert "us-ca" in cited
    assert "eu-gdpr" in cited
    assert "kr-pipa" in cited
