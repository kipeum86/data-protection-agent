from citation_auditor.california_citation import audit


def test_missing_statute_and_regulation_fail():
    result = audit("Cal. Civ. Code § 1798.999 and 11 CCR § 7999 apply.")

    assert result["status"] == "fail"
    messages = [finding["message"] for finding in result["findings"]]
    assert any("ca-statute-index" in message for message in messages)
    assert any("ca-regulation-index" in message for message in messages)


def test_cpra_standalone_warns():
    result = audit("CPRA requires businesses to honor this right.")

    assert result["status"] == "warn"
    assert any("standalone" in finding["message"] for finding in result["findings"])


def test_cpra_amendment_context_passes():
    result = audit("The CCPA as amended by CPRA includes this obligation.")

    assert result["status"] == "pass"


def test_adjacent_statute_citations_pass():
    result = audit("Cal. Bus. & Prof. Code § 22575 and Cal. Civ. Code § 56.10 apply.")

    assert result["status"] == "pass"


def test_cipa_citation_passes():
    result = audit("Cal. Penal Code § 631 and Penal Code section 632.7 apply.")

    assert result["status"] == "pass"


def test_federal_district_as_ca_binding_warns():
    result = audit("Per us-fed-graham-v-noom-2021-dismissal, this is binding California precedent.")

    assert result["status"] == "warn"
    assert any("Federal court" in finding["message"] for finding in result["findings"])


def test_ninth_circuit_published_federal_authority_passes():
    result = audit("Per us-9th-in-re-california-pizza-kitchen-2025, this is published Ninth Circuit authority.")

    assert result["status"] == "pass"
    assert not any("Federal court" in finding["message"] for finding in result["findings"])


def test_ninth_circuit_published_as_binding_california_precedent_warns():
    result = audit("Per us-9th-in-re-california-pizza-kitchen-2025, this is binding California precedent.")

    assert result["status"] == "warn"
    assert any("Federal court" in finding["message"] for finding in result["findings"])


def test_unpublished_9th_cir_as_controlling_errors():
    result = audit("Per us-9th-javier-v-assurance-iq-2022, this is controlling precedent.")

    assert result["status"] == "fail"
    assert any("Unpublished" in finding["message"] for finding in result["findings"])


def test_regulation_2026_with_wrong_source_warns():
    result = audit("Under 11 CCR § 7150 effective 2026, citing the 2024 draft text.")

    assert result["status"] == "warn"
    assert any("2026-effective regulation" in finding["message"] for finding in result["findings"])


def test_regulation_2026_with_correct_source_passes():
    result = audit(
        "Per 11 CCR § 7150 effective 2026-01-01, "
        "citing https://cppa.ca.gov/regulations/pdf/ccpa_statute_eff_20260101.pdf."
    )

    assert not any("2026-effective regulation" in finding["message"] for finding in result["findings"])


def test_mirror_case_cited_without_disclosure_warns():
    result = audit(
        "Per ca-supreme-kearney-v-salomon-smith-barney-2006, "
        "this is binding California Supreme Court precedent."
    )

    assert result["status"] == "warn"
    assert any(
        "Mirror-backed opinion" in finding["message"]
        for finding in result["findings"]
    )


def test_mirror_case_cited_with_english_disclosure_passes():
    result = audit(
        "Per ca-supreme-kearney-v-salomon-smith-barney-2006 "
        "(local copy fetched from the SCOCAL mirror; official URL: "
        "https://www.courts.ca.gov/opinions/archive/S124739.PDF), "
        "this is binding California Supreme Court precedent."
    )

    assert not any(
        "Mirror-backed opinion" in finding["message"]
        for finding in result["findings"]
    )


def test_mirror_case_cited_with_korean_disclosure_passes():
    result = audit(
        "ca-supreme-raines-v-us-healthworks-2023 (로컬 KB는 미러에서 수집됨, "
        "공식 출처는 California Courts archive)는 controlling Supreme Court 선례."
    )

    assert not any(
        "Mirror-backed opinion" in finding["message"]
        for finding in result["findings"]
    )


def test_non_mirror_case_not_warned_for_disclosure():
    result = audit(
        "Per ca-supreme-smith-v-loanme-2021, this is binding California precedent."
    )

    assert not any(
        "Mirror-backed opinion" in finding["message"]
        for finding in result["findings"]
    )


def test_load_future_effective_returns_dict():
    """Smoke: function returns dict and doesn't crash on real index."""
    from citation_auditor.california_citation import load_future_effective_authorities
    from datetime import date
    result = load_future_effective_authorities()
    assert isinstance(result, dict)
    for aid, eff in result.items():
        # Each value should be a date string parseable as ISO
        assert date.fromisoformat(eff)


def test_future_effective_cited_with_present_tense_warns():
    """If the live index has any future-effective authorities, citing one
    with present-tense language should warn. Skip if none exist."""
    from citation_auditor.california_citation import load_future_effective_authorities
    future = load_future_effective_authorities()
    if not future:
        return  # no future-effective authorities — graceful skip
    aid = next(iter(future))
    result = audit(f"Per {aid}, businesses currently require additional consent.")
    assert any(
        "(future)" in finding.get("message", "")
        and aid in finding.get("citation", "")
        for finding in result["findings"]
    )


def test_future_effective_cited_with_future_framing_passes():
    from citation_auditor.california_citation import load_future_effective_authorities
    future = load_future_effective_authorities()
    if not future:
        return
    aid, eff = next(iter(future.items()))
    result = audit(
        f"Per {aid}, businesses will require additional consent effective {eff}."
    )
    future_findings = [
        f for f in result["findings"]
        if "(future)" in f.get("message", "") and aid in f.get("citation", "")
    ]
    assert not future_findings


def test_load_authority_body_returns_text():
    from citation_auditor.california_citation import (
        BASE_DIR,
        _build_path_lookup,
        load_authority_body,
    )
    body = load_authority_body("ca-civ-1798.100", _build_path_lookup(), BASE_DIR)
    assert body and "personal information" in body.lower()


def test_quote_matching_body_passes():
    text = (
        'Per Cal. Civ. Code § 1798.100, the statute states "at or before the '
        'point of collection, inform consumers of the following".'
    )
    result = audit(text)
    quote_findings = [
        f for f in result["findings"]
        if "Quoted text not found" in f.get("message", "")
    ]
    assert not quote_findings, f"unexpected quote findings: {result['findings']}"


def test_fabricated_quote_near_citation_warns():
    text = (
        'Per Cal. Civ. Code § 1798.100, the statute states "all businesses must '
        'encrypt all biometric data within twenty-four hours of collection".'
    )
    result = audit(text)
    assert any(
        "Quoted text not found" in f.get("message", "")
        and "ca-civ-1798.100" in f.get("citation", "")
        for f in result["findings"]
    )


def test_quote_without_citation_skipped():
    text = '"Some random made-up text that does not appear in any KB authority body."'
    result = audit(text)
    quote_findings = [
        f for f in result["findings"]
        if "Quoted text not found" in f.get("message", "")
    ]
    assert not quote_findings
