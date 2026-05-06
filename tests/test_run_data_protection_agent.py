import json
from pathlib import Path

from scripts.run_data_protection_agent import (
    META_FILENAME,
    RESULT_FILENAME,
    generate_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_runner_writes_output_contract_files(tmp_path):
    generated = generate_outputs(
        "Does the CCPA require honoring Global Privacy Control opt-out signals?",
        tmp_path,
        top_k=10,
    )

    result_path = tmp_path / RESULT_FILENAME
    meta_path = tmp_path / META_FILENAME
    assert result_path.exists()
    assert meta_path.exists()
    assert generated["result_path"] == str(result_path)
    assert generated["meta_path"] == str(meta_path)

    meta = read_json(meta_path)
    assert meta["research_mode"] == "california"
    assert meta["jurisdictions"] == ["US-CA"]
    assert meta["domains"] == ["data_protection"]
    assert meta["error"] is None
    assert meta["sources"]
    assert meta["issue_map"]
    assert any(source["authority_id"] == "us-ca:ca-11-ccr-7025" for source in meta["sources"])
    assert any(source["authority_id"] == "us-ca:ca-civ-1798.120" for source in meta["sources"])

    result_md = result_path.read_text(encoding="utf-8")
    assert "Data Protection Agent Research Packet" in result_md
    assert "## Sources" in result_md


def test_runner_source_paths_exist(tmp_path):
    generate_outputs("Under GDPR Article 28, what must a processor contract include?", tmp_path, top_k=8)
    meta = read_json(tmp_path / META_FILENAME)

    assert meta["research_mode"] == "gdpr"
    assert any(source["authority_id"] == "eu-gdpr:gdpr-art28" for source in meta["sources"])
    for source in meta["sources"]:
        assert (ROOT / source["local_path"]).exists(), source["authority_id"]


def test_runner_comparative_meta_has_matrix(tmp_path):
    generate_outputs("Compare GDPR and CCPA automated decisionmaking obligations.", tmp_path, top_k=12)
    meta = read_json(tmp_path / META_FILENAME)

    assert meta["research_mode"] == "comparative"
    assert set(meta["jurisdictions"]) == {"EU", "US-CA"}
    assert meta["comparison_matrix"]
    assert any(source["authority_id"] == "eu-gdpr:gdpr-art22" for source in meta["sources"])
    assert any(source["authority_id"] == "us-ca:ca-11-ccr-7200" for source in meta["sources"])


def test_runner_records_fallback_coverage_gap(tmp_path):
    generate_outputs("What does the Colorado privacy law require for opt-out signals?", tmp_path, top_k=5)
    meta = read_json(tmp_path / META_FILENAME)

    assert meta["research_mode"] == "fallback_us"
    assert meta["coverage_gaps"]
    assert meta["error"] is None
