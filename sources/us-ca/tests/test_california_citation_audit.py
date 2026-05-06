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
