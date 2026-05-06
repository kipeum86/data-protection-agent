import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "index"


def load_json(name: str):
    return json.loads((INDEX_DIR / name).read_text(encoding="utf-8"))


def test_topic_index_has_core_topics_without_missing_authorities():
    topic_index = load_json("ca-topic-index.json")
    topics = {topic["id"]: topic for topic in topic_index["topics"]}

    for topic_id in [
        "notice_at_collection",
        "opt_out_sale_share_gpc",
        "data_breach_private_right",
        "risk_assessments",
        "admt",
        "cipa_website_tracking",
    ]:
        assert topic_id in topics
        assert topics[topic_id]["coverage_status"] == "pass"
        assert topics[topic_id]["missing_authority_ids"] == []
        assert topics[topic_id]["primary_authorities"]


def test_golden_questions_resolve_expected_authorities():
    golden = load_json("golden-questions.ca.json")

    assert golden["count"] >= 10
    for question in golden["questions"]:
        assert question["topic_exists"], question["id"]
        assert question["expected_authorities"], question["id"]
        assert question["missing_authority_ids"] == [], question["id"]


def test_reverse_topic_lookup_includes_cipa_and_gpc_authorities():
    topic_index = load_json("ca-topic-index.json")
    reverse = topic_index["authority_to_topics"]

    assert "cipa_website_tracking" in reverse["ca-pen-631"]
    assert "opt_out_sale_share_gpc" in reverse["ca-11-ccr-7025"]


def test_state_published_case_coverage_includes_mirror_warning():
    case_index = load_json("ca-case-index.json")
    state_published = [
        case
        for case in case_index["cases"]
        if case["court_system"] == "state" and case["precedential_status"] == "published_citable"
    ]
    mirror_cases = [
        case
        for case in state_published
        if case["source_family"] == "ca-courts-published-opinion-mirrors"
    ]

    assert len(state_published) >= 7
    assert len(mirror_cases) >= 6
    assert all(case["source_grade"] == "B" for case in mirror_cases)
    assert all(case["source_url"].startswith("https://scocal.stanford.edu/") for case in mirror_cases)
    assert all(case["official_url"].startswith("https://www.courts.ca.gov/") for case in mirror_cases)
    assert all(case["source_mirror_warning"] for case in mirror_cases)


def test_golden_questions_reference_mirror_cases():
    """Phase 3 mirror cases must be expected by at least one golden question
    so retrieval drift (case dropped from index) is caught by the test suite.
    """
    text = json.dumps(load_json("golden-questions.ca.json"))
    for case_id in [
        "ca-supreme-kearney-v-salomon-smith-barney-2006",
        "ca-supreme-raines-v-us-healthworks-2023",
    ]:
        assert case_id in text, (
            f"mirror case {case_id} not referenced by any golden question; "
            f"add to supporting_authority_ids of the appropriate golden question "
            f"in config/california-topic-seeds.json"
        )


def test_topic_index_includes_mirror_cases():
    """Phase 3 mirror cases must appear in the topic index so retrieval
    can surface them under the matching ccpa_topics.
    """
    text = json.dumps(load_json("ca-topic-index.json"))
    for case_id in [
        "ca-supreme-kearney-v-salomon-smith-barney-2006",
        "ca-supreme-facebook-v-superior-court-2018",
    ]:
        assert case_id in text, (
            f"mirror case {case_id} not in topic index; "
            f"add to case_ids of the relevant topic in "
            f"config/california-topic-seeds.json"
        )
