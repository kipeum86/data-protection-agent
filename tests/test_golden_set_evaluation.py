from pathlib import Path

from scripts.evaluate_golden_set import evaluate


ROOT = Path(__file__).resolve().parents[1]


def test_golden_set_evaluation_passes(tmp_path):
    report = evaluate(
        config_path=ROOT / "config" / "golden-set.json",
        output_dir=tmp_path,
        clean=True,
    )

    assert report["status"] == "pass"
    assert report["count"] == 13
    assert report["failed"] == 0
    assert (tmp_path / "golden-set-report.json").exists()
