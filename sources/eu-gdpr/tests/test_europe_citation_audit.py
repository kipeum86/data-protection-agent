"""Unit tests for EU GDPR citation auditor.

Tests use real ids from kb/eu-gdpr/index/ rather than hardcoded fixtures so
they remain accurate as the upstream GDPR-expert KB evolves.
"""

from citation_auditor.europe_citation import audit, load_valid_ids


def test_load_valid_ids_returns_articles_and_recitals():
    ids = load_valid_ids()
    assert "articles" in ids
    assert "recitals" in ids
    assert len(ids["articles"]) > 0, (
        "article-index.json empty? run python3 scripts/import_namespaced_kbs.py --clean"
    )
    assert len(ids["recitals"]) > 0


def test_existing_gdpr_article_citation_passes():
    ids = load_valid_ids()
    arts = sorted(i for i in ids["articles"] if i.startswith("gdpr-art"))
    if not arts:
        return
    art_num = arts[0].replace("gdpr-art", "")
    result = audit(f"GDPR Article {art_num} requires the controller to act.")
    article_findings = [f for f in result["findings"] if "Article citation" in f["message"]]
    assert not article_findings, (
        f"unexpected article findings for gdpr-art{art_num}: {result['findings']}"
    )


def test_existing_eu_ai_act_citation_passes():
    ids = load_valid_ids()
    arts = sorted(i for i in ids["articles"] if i.startswith("eu-ai-act-art"))
    if not arts:
        return
    art_num = arts[0].replace("eu-ai-act-art", "")
    result = audit(f"EU AI Act Article {art_num} applies to high-risk systems.")
    article_findings = [f for f in result["findings"] if "Article citation" in f["message"]]
    assert not article_findings


def test_missing_article_fails():
    result = audit("GDPR Article 9999 imposes new duties.")
    assert result["status"] == "fail"
    assert any("Article citation" in f["message"] for f in result["findings"])


def test_recital_as_binding_warns():
    result = audit("GDPR Recital 30 requires controllers to log all access.")
    assert result["status"] in {"warn", "fail"}
    assert any("Recital cited as binding" in f["message"] for f in result["findings"])


def test_recital_as_interpretive_aid_passes():
    result = audit(
        "GDPR Article 6 sets the lawful bases. Recital 47 helps interpret legitimate interests."
    )
    binding_findings = [f for f in result["findings"] if "Recital cited as binding" in f["message"]]
    assert not binding_findings
