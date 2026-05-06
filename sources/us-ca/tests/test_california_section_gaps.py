import json

from scripts.build_california_kb import INDEX_DIR, load_config, section_gap_report


def test_validation_report_includes_section_gaps():
    report = json.loads((INDEX_DIR / "validation-report.json").read_text(encoding="utf-8"))

    assert "section_gaps" in report
    aadc = report["section_gaps"]["ca-age-appropriate-design-code"]
    assert aadc["status"] in {"ok", "unverified"}
    assert isinstance(aadc.get("missing", []), list)


def test_verified_absent_section_gaps_are_ok():
    report = section_gap_report(load_config())

    assert report["ca-age-appropriate-design-code"]["status"] == "ok"
    assert report["ca-data-broker-delete-act"]["status"] == "ok"
    assert report["ca-age-appropriate-design-code"]["unverified"] == []
    assert report["ca-data-broker-delete-act"]["unverified"] == []
