"""Unit tests for unified citation auditor."""

from unified_auditor.run import audit_unified, load_auditors


def test_load_auditors_returns_4():
    auditors = load_auditors()
    assert len(auditors) == 4
    names = [name for name, _ in auditors]
    assert "us-ca" in names
    assert "kr-pipa" in names
    assert "eu-gdpr" in names
    assert "cross-jurisdiction" in names


def test_unified_audit_clean_text_passes():
    result = audit_unified(
        "This is a generic privacy discussion without specific authorities."
    )
    assert result["status"] == "pass"
    assert result["finding_count"] == 0


def test_unified_audit_aggregates_findings():
    """CA-only signal + GDPR citation should warn from cross-juris auditor."""
    text = "Under CCPA, businesses must honor opt-out. See gdpr-art6 for parallels."
    result = audit_unified(text)
    assert result["status"] == "warn"
    cross_findings = [
        f for f in result["findings"] if f["auditor"] == "cross-jurisdiction"
    ]
    assert cross_findings


def test_unified_audit_per_auditor_reports():
    text = "Cal. Civ. Code § 1798.150 grants a private right of action."
    result = audit_unified(text)
    assert "us-ca" in result["per_auditor"]
    assert "kr-pipa" in result["per_auditor"]
    assert "eu-gdpr" in result["per_auditor"]
    assert "cross-jurisdiction" in result["per_auditor"]


def test_unified_audit_invalid_citation_fails():
    text = "Cal. Civ. Code § 1798.999 provides..."
    result = audit_unified(text)
    assert result["status"] == "fail"
    ca_findings = [f for f in result["findings"] if f["auditor"] == "us-ca"]
    assert ca_findings
