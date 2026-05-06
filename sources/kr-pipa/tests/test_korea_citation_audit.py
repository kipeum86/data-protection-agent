"""Unit tests for KR PIPA citation auditor.

Tests use real ids from kb/kr-pipa/index/ rather than hardcoded fixtures so
they remain accurate as the upstream PIPA-expert KB evolves.
"""

from citation_auditor.korea_citation import audit, load_valid_ids


def test_load_valid_ids_returns_articles_and_guidelines():
    ids = load_valid_ids()
    assert "articles" in ids
    assert "guidelines" in ids
    assert len(ids["articles"]) > 0, (
        "article-index.json empty? run python3 scripts/import_namespaced_kbs.py --clean"
    )
    assert len(ids["guidelines"]) > 0


def test_existing_pipa_article_citation_passes():
    """개인정보 보호법 제N조 형태의 known-good 인용은 통과."""
    ids = load_valid_ids()
    pipa_arts = sorted(i for i in ids["articles"] if i.startswith("pipa-art")
                       and "decree" not in i)
    if not pipa_arts:
        return  # KR sub-KB가 비었으면 skip
    art_num = pipa_arts[0].replace("pipa-art", "")
    result = audit(f"개인정보 보호법 제{art_num}조에 따라 처리한다.")
    article_findings = [f for f in result["findings"] if "Article citation" in f["message"]]
    assert not article_findings, (
        f"unexpected article findings for pipa-art{art_num}: {result['findings']}"
    )


def test_existing_network_act_citation_passes():
    ids = load_valid_ids()
    net_arts = sorted(i for i in ids["articles"] if i.startswith("network-act-art")
                      and "decree" not in i)
    if not net_arts:
        return
    art_num = net_arts[0].replace("network-act-art", "")
    result = audit(f"정보통신망법 제{art_num}조에 따라.")
    article_findings = [f for f in result["findings"] if "Article citation" in f["message"]]
    assert not article_findings


def test_missing_article_fails():
    result = audit("개인정보 보호법 제9999조에 따라.")
    assert result["status"] == "fail"
    assert any("Article citation" in f["message"] for f in result["findings"])


def test_pipc_guideline_as_binding_warns():
    result = audit("PIPC 가이드라인은 법적 구속력이 있다.")
    assert result["status"] in {"warn", "fail"}
    assert any("PIPC guideline" in f["message"] for f in result["findings"])


def test_local_id_for_unknown_warns():
    result = audit("Per kr-court-doesnotexist-2099, holding...")
    assert any("Local KR KB id" in f["message"] for f in result["findings"])


def test_existing_network_act_enforcement_rule_citation_passes():
    ids = load_valid_ids()
    rule_arts = sorted(
        i for i in ids["articles"] if i.startswith("network-act-enforcement-rule-art")
    )
    if not rule_arts:
        return
    art_num = rule_arts[0].replace("network-act-enforcement-rule-art", "")
    result = audit(f"정보통신망법 시행규칙 제{art_num}조에 따라 보고한다.")
    assert not any("Article citation" in f["message"] for f in result["findings"])


def test_missing_enforcement_rule_fails():
    result = audit("정보통신망법 시행규칙 제9999조에 따라.")
    assert result["status"] == "fail"
    assert any(
        "Article citation" in f["message"]
        and "network-act-enforcement-rule" in f["message"]
        for f in result["findings"]
    )
