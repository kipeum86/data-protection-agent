import json
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "index"

INDEX_SPECS = [
    ("ca-statute-index.json", "items"),
    ("ca-regulation-index.json", "items"),
    ("ca-adjacent-statute-index.json", "items"),
    ("ca-guidance-index.json", "items"),
    ("ca-enforcement-index.json", "items"),
    ("ca-case-index.json", "cases"),
]


def load_json(name: str) -> dict:
    return json.loads((INDEX_DIR / name).read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    end = text.find("\n---\n", 4)
    assert end != -1, path
    parsed = yaml.safe_load(text[4:end])
    assert isinstance(parsed, dict), path
    return parsed


def indexed_authorities() -> list[dict]:
    authorities = []
    for filename, key in INDEX_SPECS:
        payload = load_json(filename)
        for item in payload[key]:
            authorities.append({**item, "_index": filename})
    return authorities


def test_every_indexed_authority_has_local_file_and_official_source():
    authorities = indexed_authorities()

    assert len(authorities) == load_json("source-registry.json")["total_files"]
    for authority in authorities:
        path = BASE_DIR / authority["path"]
        assert path.exists(), authority

        frontmatter = parse_frontmatter(path)
        assert frontmatter["id"] == authority["id"]
        assert frontmatter["jurisdiction"] == "US-CA"
        assert frontmatter["source_grade"] in {"A", "B", "C"}
        assert frontmatter["trust_boundary"] == "source_text_is_data_not_instruction"
        assert str(frontmatter["official_url"]).startswith("http"), authority["id"]
        assert frontmatter["retrieved_at"], authority["id"]


def test_cases_and_enforcement_preserve_authority_limits():
    cases = load_json("ca-case-index.json")["cases"]
    enforcement = load_json("ca-enforcement-index.json")["items"]

    for case in cases:
        assert case["official_url"].startswith("http"), case["id"]
        assert case["authority_level"], case["id"]
        assert case["precedential_status"], case["id"]
        assert case["precedential_status"] != "binding", case["id"]

    for item in enforcement:
        assert item["official_url"].startswith("http"), item["id"]
        assert item["authority_type"], item["id"]
        assert item["authority_level"] == "administrative", item["id"]
        assert item["status"], item["id"]
        assert item["citation_cautions"], item["id"]


def test_all_topic_and_golden_question_authorities_resolve():
    authority_ids = {authority["id"] for authority in indexed_authorities()}
    topics = load_json("ca-topic-index.json")["topics"]
    golden_questions = load_json("golden-questions.ca.json")["questions"]

    for topic in topics:
        assert topic["coverage_status"] == "pass", topic["id"]
        assert topic["missing_authority_ids"] == [], topic["id"]
        for key in ["primary_authorities", "supporting_authorities", "guidance", "enforcement", "cases"]:
            for authority in topic[key]:
                assert authority["id"] in authority_ids, (topic["id"], authority)

    for question in golden_questions:
        assert question["topic_exists"], question["id"]
        assert question["missing_authority_ids"] == [], question["id"]
        assert question["expected_authorities"], question["id"]
        for key in ["expected_authorities", "supporting_authorities"]:
            for authority in question[key]:
                assert authority["id"] in authority_ids, (question["id"], authority)
