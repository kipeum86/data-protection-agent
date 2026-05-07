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


def test_ccpa_only_with_personal_data_warns():
    text = "Under CCPA, the business must protect personal data of California residents."
    result = audit(text)
    assert any(
        "personal data" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_gdpr_only_with_personal_information_warns():
    text = "Under GDPR, the controller must protect personal information of EU residents."
    result = audit(text)
    assert any(
        "personal information" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_comparative_answer_passes_vocabulary_check():
    """비교 답변은 vocab 체크에서도 false positive 안 떠야."""
    text = (
        "GDPR uses 'personal data' and 'controller'. CCPA uses "
        "'personal information' and 'business'."
    )
    result = audit(text)
    vocab_findings = [
        f for f in result["findings"]
        if "terminology but answer signals" in f["message"]
    ]
    assert not vocab_findings


def test_pipa_only_with_controller_warns():
    text = "개인정보 보호법에 따라 controller는 동의를 받아야 한다."
    result = audit(text)
    assert any(
        "controller" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_multi_juris_with_labels_passes():
    text = (
        "EU GDPR: GDPR Article 6 sets lawful bases.\n\n"
        "California: CCPA gives consumers the right to opt-out."
    )
    result = audit(text)
    label_findings = [
        f for f in result["findings"]
        if "lacks explicit jurisdiction labels" in f["message"]
    ]
    assert not label_findings


def test_multi_juris_without_labels_warns():
    text = "GDPR Article 6 sets lawful bases. CCPA gives consumers the right to opt-out."
    result = audit(text)
    assert any(
        "lacks explicit jurisdiction labels" in f["message"]
        for f in result["findings"]
    )


def test_single_juris_no_label_required():
    text = "Under CCPA, the business must honor opt-out within 15 days."
    result = audit(text)
    label_findings = [
        f for f in result["findings"]
        if "lacks explicit jurisdiction labels" in f["message"]
    ]
    assert not label_findings


def test_partial_labels_pass():
    """Partial labelling counts as structured (don't perfectionism-block)."""
    text = (
        "California: CCPA covers personal information.\n\n"
        "GDPR Article 6 sets lawful bases."
    )
    result = audit(text)
    label_findings = [
        f for f in result["findings"]
        if "lacks explicit jurisdiction labels" in f["message"]
    ]
    assert not label_findings


def test_ccpa_only_with_right_to_erasure_warns():
    text = "Under CCPA, consumers have a right to erasure of their personal information."
    result = audit(text)
    assert any(
        "right to erasure" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_gdpr_only_with_right_to_delete_warns():
    text = "Under GDPR, the data subject has a right to delete their personal data."
    result = audit(text)
    assert any(
        "right to delete" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_ccpa_only_with_dpo_warns():
    text = "Under CCPA, businesses must appoint a data protection officer."
    result = audit(text)
    assert any(
        "data protection officer" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_gdpr_only_with_korean_susuctaja_warns():
    text = "Under GDPR, the controller must conclude a contract with the 수탁자."
    result = audit(text)
    assert any(
        "수탁자" in f.get("citation", "")
        for f in result["findings"]
    )


def test_vague_law_reference_alone_warns():
    text = "The law requires businesses to obtain explicit consent before collection."
    result = audit(text)
    assert any(
        "Vague law reference" in f["message"] for f in result["findings"]
    )


def test_vague_law_reference_with_nearby_id_passes():
    """Specific authority within 200 chars → vague phrase is acceptable shorthand."""
    text = (
        "Per ca-civ-1798.100, businesses must provide notice. "
        "The law requires this notice to appear at or before collection."
    )
    result = audit(text)
    vague_findings = [
        f for f in result["findings"] if "Vague law reference" in f["message"]
    ]
    assert not vague_findings


def test_in_some_jurisdictions_warns():
    text = "In some jurisdictions, opt-in consent is required for tracking pixels."
    result = audit(text)
    assert any(
        "Vague law reference" in f["message"]
        and "in some jurisdictions" in f.get("citation", "").lower()
        for f in result["findings"]
    )


def test_applicable_law_with_nearby_id_passes():
    text = (
        "Applicable law may require additional consent for sensitive data. "
        "See gdpr-art9 and ca-civ-1798.121 for the relevant provisions."
    )
    result = audit(text)
    vague_findings = [
        f for f in result["findings"] if "Vague law reference" in f["message"]
    ]
    assert not vague_findings


def test_strict_mode_partial_labels_warns(monkeypatch):
    monkeypatch.setenv("STRICT_JURISDICTION_LABELS", "true")
    text = (
        "California: CCPA covers personal information.\n\n"
        "GDPR Article 6 sets lawful bases."
    )
    result = audit(text)
    assert any(
        "missing labels for" in f["message"] for f in result["findings"]
    )


def test_strict_mode_all_labels_passes(monkeypatch):
    monkeypatch.setenv("STRICT_JURISDICTION_LABELS", "true")
    text = (
        "California: CCPA covers personal information.\n\n"
        "EU GDPR: GDPR Article 6 sets lawful bases."
    )
    result = audit(text)
    label_findings = [
        f for f in result["findings"]
        if "missing labels" in f["message"] or "lacks explicit" in f["message"]
    ]
    assert not label_findings


def test_default_mode_partial_labels_passes(monkeypatch):
    monkeypatch.delenv("STRICT_JURISDICTION_LABELS", raising=False)
    text = (
        "California: CCPA covers personal information.\n\n"
        "GDPR Article 6 sets lawful bases."
    )
    result = audit(text)
    label_findings = [
        f for f in result["findings"]
        if "missing labels" in f["message"] or "lacks explicit" in f["message"]
    ]
    assert not label_findings
