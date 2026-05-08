"""End-to-end smoke for the v19 agent pipeline scaffolding.

These tests exercise deterministic retrieval, output validation, and citation
auditing. They do not exercise LLM-driven memo composition; that happens inside
Claude Code through the v19 skills and `/answer` command.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parent.parent
GOLDEN = json.loads((ROOT / "config" / "golden-set.json").read_text(encoding="utf-8"))
FIXTURES = GOLDEN.get("fixtures") or GOLDEN.get("cases", [])

MODE_ALIASES = {
    "california": "ca_only",
    "pipa": "kr_only",
    "gdpr": "eu_only",
}


def run_packet(tmp_path: Path, fixture: dict[str, Any]) -> Path:
    out = tmp_path / fixture["id"]
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_data_protection_agent.py",
            fixture["question"],
            "--output-dir",
            str(out),
            "--top-k",
            str(fixture.get("top_k", GOLDEN.get("default_top_k", 14))),
            "--print-summary",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return out


def read_meta(out: Path) -> dict[str, Any]:
    return json.loads((out / "data-protection-agent-meta.json").read_text(encoding="utf-8"))


def normalized_mode(mode: str) -> str:
    return MODE_ALIASES.get(mode, mode)


def authority_matches_prefix(authority_id: str, expected_prefix: str) -> bool:
    suffix = authority_id.split(":", 1)[-1]
    return authority_id.startswith(expected_prefix) or suffix.startswith(expected_prefix)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_packet_runner_produces_valid_outputs(tmp_path: Path, fixture: dict[str, Any]) -> None:
    out = run_packet(tmp_path, fixture)

    result_path = out / "data-protection-agent-result.md"
    meta_path = out / "data-protection-agent-meta.json"
    assert result_path.exists()
    assert meta_path.exists()

    val = subprocess.run(
        [sys.executable, "scripts/validate-output.py", str(out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert val.returncode == 0, val.stdout + val.stderr

    meta = read_meta(out)
    raw_mode = meta["research_mode"]
    expected_runner_mode = fixture.get("expected_runner_mode", fixture["expected_mode"])
    assert raw_mode == expected_runner_mode or normalized_mode(raw_mode) == fixture["expected_mode"], meta

    assert set(meta["jurisdictions"]) == set(fixture["expected_jurisdictions"])
    assert len(meta["sources"]) >= fixture.get("min_sources", 1)

    source_namespaces = {source["namespace"] for source in meta["sources"]}
    assert set(fixture.get("expected_namespaces", [])) <= source_namespaces
    for namespace in fixture.get("forbidden_authority_namespaces", []):
        assert namespace not in source_namespaces, (
            f"forbidden namespace {namespace} leaked into sources for {fixture['id']}"
        )

    authority_ids = [source["authority_id"] for source in meta["sources"]]
    for expected_prefix in fixture.get("expected_authority_prefixes", []):
        assert any(authority_matches_prefix(authority_id, expected_prefix) for authority_id in authority_ids), (
            f"missing expected authority prefix {expected_prefix}; got {authority_ids}"
        )

    if "expected_coverage_gaps" in fixture:
        assert meta.get("coverage_gaps", []) == fixture["expected_coverage_gaps"]

    result_text = result_path.read_text(encoding="utf-8")
    if expected_runner_mode == "comparative":
        assert "## Comparison Matrix" in result_text


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_packet_passes_citation_auditor(tmp_path: Path, fixture: dict[str, Any]) -> None:
    out = run_packet(tmp_path, fixture)
    audit = subprocess.run(
        [
            sys.executable,
            "scripts/audit-unified.py",
            "--json",
            str(out / "data-protection-agent-result.md"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert audit.returncode == 0, f"audit-unified failed for {fixture['id']}:\n{audit.stdout}"


# ---------------------------------------------------------------------------
# v21: DOCX renderer smoke (basic + legal-opinion).
# ---------------------------------------------------------------------------

DOCX_MIN_BYTES = 10_000  # An empty DOCX is ~5 KB; rendered fixtures are 30-50 KB.


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_packet_renders_basic_docx(tmp_path: Path, fixture: dict[str, Any]) -> None:
    pytest.importorskip("docx")
    out = run_packet(tmp_path, fixture)
    docx_path = out / "data-protection-agent-result.docx"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/render-docx.py",
            str(out / "data-protection-agent-result.md"),
            str(docx_path),
            "--language", "en",
            "--jurisdiction", "us",
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, f"render-docx failed for {fixture['id']}:\n{proc.stderr}"
    assert docx_path.exists(), f"DOCX not written for {fixture['id']}"
    assert docx_path.stat().st_size > DOCX_MIN_BYTES, (
        f"DOCX suspiciously small for {fixture['id']}: {docx_path.stat().st_size} bytes"
    )


def test_legal_opinion_renderer_smoke(tmp_path: Path) -> None:
    """Render the first fixture as a legal-opinion DOCX with the cover-page
    metadata the /answer command would supply when output_mode=legal_opinion."""
    pytest.importorskip("docx")
    fixture = FIXTURES[0]
    out = run_packet(tmp_path, fixture)
    docx_path = out / "data-protection-agent-result.docx"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/render-legal-opinion-docx.py",
            str(out / "data-protection-agent-result.md"),
            str(docx_path),
            "--title", "v21 e2e smoke — legal-opinion render",
            "--recipient", "사내 법무팀 귀중",
            "--date", "2026년 5월 8일",
            "--classification", "TEST — NOT FOR DISTRIBUTION",
            "--author", "Data Protection Agent (data-protection-agent)",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, f"render-legal-opinion-docx failed:\n{proc.stderr}"
    assert docx_path.exists()
    assert docx_path.stat().st_size > DOCX_MIN_BYTES


# ---------------------------------------------------------------------------
# v22: HTML renderer smoke (marko-based).
# ---------------------------------------------------------------------------

HTML_MIN_BYTES = 2_000  # boilerplate + minimal content; rendered fixtures are 20-40 KB.


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_packet_renders_html(tmp_path: Path, fixture: dict[str, Any]) -> None:
    pytest.importorskip("marko")
    out = run_packet(tmp_path, fixture)
    html_path = out / "data-protection-agent-result.html"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/render-html.py",
            str(out / "data-protection-agent-result.md"),
            str(html_path),
            "--lang", "en",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, f"render-html failed for {fixture['id']}:\n{proc.stderr}"
    assert html_path.exists(), f"HTML not written for {fixture['id']}"
    assert html_path.stat().st_size > HTML_MIN_BYTES, (
        f"HTML suspiciously small for {fixture['id']}: {html_path.stat().st_size} bytes"
    )
    # Sanity: HTML wraps the rendered markdown content.
    text = html_path.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>")
    assert "<title>" in text and "</title>" in text
