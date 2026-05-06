import json
from pathlib import Path

from scripts.retrieve_authorities import classify_query, retrieve_authorities


ROOT = Path(__file__).resolve().parents[1]


def test_california_gpc_query_routes_and_retrieves_core_authorities():
    result = retrieve_authorities("Does the CCPA require honoring Global Privacy Control opt-out signals?", top_k=10)
    authority_ids = {item["unified_id"] for item in result["authorities"]}

    assert result["research_mode"] == "california"
    assert result["jurisdictions"] == ["US-CA"]
    assert "us-ca:ca-11-ccr-7025" in authority_ids
    assert "us-ca:ca-civ-1798.120" in authority_ids


def test_gdpr_processor_query_routes_to_gdpr():
    result = retrieve_authorities("Under GDPR Article 28, what must a processor contract include?", top_k=8)
    authority_ids = {item["unified_id"] for item in result["authorities"]}

    assert result["research_mode"] == "gdpr"
    assert result["jurisdictions"] == ["EU"]
    assert "eu-gdpr:gdpr-art28" in authority_ids


def test_korean_overseas_transfer_query_routes_to_pipa():
    result = retrieve_authorities("개인정보 국외 이전 시 PIPA상 어떤 조항을 봐야 하나?", top_k=10)
    authority_ids = {item["unified_id"] for item in result["authorities"]}

    assert result["research_mode"] == "pipa"
    assert result["jurisdictions"] == ["KR"]
    assert "kr-pipa:pipa-art28-8" in authority_ids


def test_comparative_query_selects_multiple_namespaces():
    result = retrieve_authorities("Compare GDPR and CCPA automated decisionmaking obligations.", top_k=12)
    authority_ids = {item["unified_id"] for item in result["authorities"]}

    assert result["research_mode"] == "comparative"
    assert set(result["jurisdictions"]) == {"EU", "US-CA"}
    assert any(item["namespace"] == "eu-gdpr" for item in result["authorities"])
    assert any(item["namespace"] == "us-ca" for item in result["authorities"])
    assert "eu-gdpr:gdpr-art22" in authority_ids
    assert "us-ca:ca-11-ccr-7200" in authority_ids


def test_non_california_us_query_reports_coverage_gap():
    classification = classify_query("What does the Colorado privacy law require for opt-out signals?")

    assert classification["research_mode"] == "fallback_us"
    assert classification["coverage_gaps"]


def test_short_routing_terms_do_not_match_inside_words():
    pipa = classify_query("Under PIPA Article 28-2, how is pseudonymized information handled?")
    california = retrieve_authorities("California CCPA applicability threshold question", top_k=8)
    authority_ids = {item["unified_id"] for item in california["authorities"]}

    assert pipa["research_mode"] == "pipa"
    assert pipa["jurisdictions"] == ["KR"]
    assert "us-ca:ca-pen-631" not in authority_ids


def test_retrieval_output_is_json_serializable():
    result = retrieve_authorities("California sensitive personal information limit use", top_k=5)

    json.dumps(result, ensure_ascii=False)
    for item in result["authorities"]:
        assert (ROOT / item["path"]).exists()
