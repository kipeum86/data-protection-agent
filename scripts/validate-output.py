#!/usr/bin/env python3
"""Validate data-protection-agent output files.

The v19 answering layer writes a finished memo plus metadata. The existing
deterministic runner still writes a legacy research packet; this validator
supports that packet as a compatibility mode while enforcing stricter checks
for v19 memos.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


AGENT_ID = "data-protection-agent"
RESULT_FILENAME = "data-protection-agent-result.md"
META_FILENAME = "data-protection-agent-meta.json"

VALID_MODES = {
    "ca_only",
    "kr_only",
    "eu_only",
    "multi_jurisdiction",
    "comparative",
    "fallback_us",
    "fallback",
}

LEGACY_MODE_ALIASES = {
    "california": "ca_only",
    "pipa": "kr_only",
    "gdpr": "eu_only",
}

VALID_JURISDICTIONS = {"US-CA", "KR", "EU"}
VALID_NAMESPACES = {"us-ca", "kr-pipa", "eu-gdpr"}

FALLBACK_MODES = {"fallback", "fallback_us"}

# v21: output_mode is the orthogonal axis to research_mode. canonical = the
# default 9-section research memo. legal_opinion = vendored from
# legal-research-agent (formal opinion-letter format with cover page,
# auto-numbered headings, classification footer, optional DOCX render).
VALID_OUTPUT_MODES = {
    "canonical",
    "legal_opinion",
    "executive_brief",
    "comparative_matrix",
    "enforcement_case_law",
    "black_letter_commentary",
}

VALID_OUTPUT_FORMATS = {"markdown", "docx_ready_markdown"}

REQUIRED_KEYS = {
    "meta_version",
    "summary",
    "research_mode",
    "mode_source",
    "active_profile",
    "jurisdictions",
    "namespaces",
    "domains",
    "issue_map",
    "key_findings",
    "sources",
    "coverage_gaps",
    "error",
}

LEGACY_REQUIRED_KEYS = {
    "summary",
    "research_mode",
    "jurisdictions",
    "domains",
    "issue_map",
    "key_findings",
    "sources",
    "coverage_gaps",
    "error",
}

REQUIRED_RESULT_SECTIONS = (
    "## Question",
    "## Route Context",
    "## Short Answer",
    "## Sources",
    "## Coverage Gaps",
    "## Handoff Notes",
)

LEGACY_REQUIRED_RESULT_SECTIONS = (
    "## Key Findings",
    "## Issue Map",
    "## Sources",
)

NULLABLE_OR_EMPTY_KEYS = {
    "classification_warnings",
    "co_running_agents",
    "comparison_matrix",
    "coverage_gaps",
    "error",
    "fallback_reason",
    "handoff_notes",
    "orchestrator_route_mode",
}

SOURCE_ID_RE = re.compile(r"^src_\d{3}$")
SOURCE_ID_IN_TEXT_RE = re.compile(r"\bsrc_\d{3}\b")
PLACEHOLDER_RE = re.compile(r"\b(TBD|tbd|to be determined|n/a)\b")


def add_finding(
    findings: list[dict[str, str]],
    severity: str,
    code: str,
    message: str,
    *,
    path: str = "",
) -> None:
    findings.append({
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
    })


def is_empty_load_bearing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def has_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if stripped in {"-", ""}:
        return True
    return bool(PLACEHOLDER_RE.search(stripped))


def section_present(text: str, section: str) -> bool:
    return section in text


def normalize_mode(raw_mode: Any) -> str | None:
    if not isinstance(raw_mode, str):
        return None
    return LEGACY_MODE_ALIASES.get(raw_mode, raw_mode)


def source_id_set(meta: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for source in meta.get("sources", []):
        if isinstance(source, dict) and isinstance(source.get("id"), str):
            ids.add(source["id"])
    return ids


def source_by_id(meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        source["id"]: source
        for source in meta.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("id"), str)
    }


def detect_result_kind(meta: dict[str, Any], result_text: str) -> str:
    if "meta_version" not in meta and result_text.startswith("# Data Protection Agent Research Packet"):
        return "legacy_packet"
    return "v19_result"


FALLBACK_NULLABLE_KEYS = {"jurisdictions", "namespaces", "sources", "issue_map", "key_findings"}


def validate_output_mode_fields(meta: dict[str, Any], findings: list[dict[str, str]]) -> None:
    """v21: validate the orthogonal output_mode axis. Optional fields; absence
    is treated as the implicit canonical research-memo default for backward
    compat with v19/v20 metas."""
    output_mode = meta.get("output_mode")
    if output_mode is not None:
        if not isinstance(output_mode, str) or output_mode not in VALID_OUTPUT_MODES:
            add_finding(
                findings,
                "error",
                "invalid_output_mode",
                f"invalid output_mode `{output_mode}`; expected one of {sorted(VALID_OUTPUT_MODES)}",
                path="output_mode",
            )
    output_format = meta.get("output_mode_format")
    if output_format is not None:
        if not isinstance(output_format, str) or output_format not in VALID_OUTPUT_FORMATS:
            add_finding(
                findings,
                "error",
                "invalid_output_mode_format",
                f"invalid output_mode_format `{output_format}`; expected one of {sorted(VALID_OUTPUT_FORMATS)}",
                path="output_mode_format",
            )
    audience = meta.get("output_mode_audience")
    if audience is not None and not isinstance(audience, str):
        add_finding(
            findings,
            "error",
            "invalid_output_mode_audience",
            "output_mode_audience must be a string or null",
            path="output_mode_audience",
        )


def validate_required_keys(
    meta: dict[str, Any],
    findings: list[dict[str, str]],
    *,
    strict: bool,
) -> None:
    required = REQUIRED_KEYS if strict else LEGACY_REQUIRED_KEYS
    missing = sorted(required - set(meta))
    for key in missing:
        add_finding(findings, "error", "missing_meta_key", f"missing required meta key `{key}`", path=key)

    raw_mode = meta.get("research_mode")
    is_fallback = normalize_mode(raw_mode) in FALLBACK_MODES
    nullable = NULLABLE_OR_EMPTY_KEYS | (FALLBACK_NULLABLE_KEYS if is_fallback else set())

    for key in sorted(required & set(meta)):
        if key in nullable:
            continue
        if is_empty_load_bearing(meta.get(key)):
            add_finding(findings, "error", "empty_meta_key", f"meta key `{key}` is empty", path=key)

    if not strict:
        missing_v19 = sorted(REQUIRED_KEYS - set(meta))
        if missing_v19:
            add_finding(
                findings,
                "warn",
                "legacy_missing_v19_keys",
                "legacy research packet is missing v19-only keys: " + ", ".join(missing_v19),
            )


def validate_mode_and_scope(
    meta: dict[str, Any],
    findings: list[dict[str, str]],
    *,
    strict: bool,
) -> str:
    raw_mode = meta.get("research_mode")
    normalized = normalize_mode(raw_mode)
    if normalized not in VALID_MODES:
        add_finding(findings, "error", "invalid_mode", f"invalid research_mode `{raw_mode}`", path="research_mode")
        normalized = "fallback"
    elif strict and raw_mode != normalized:
        add_finding(
            findings,
            "error",
            "legacy_mode_in_v19_meta",
            f"v19 metadata must use `{normalized}`, not legacy mode `{raw_mode}`",
            path="research_mode",
        )
    elif raw_mode != normalized:
        add_finding(
            findings,
            "warn",
            "legacy_mode_alias",
            f"legacy mode `{raw_mode}` is treated as `{normalized}`",
            path="research_mode",
        )

    jurisdictions = meta.get("jurisdictions", [])
    if not isinstance(jurisdictions, list):
        add_finding(findings, "error", "invalid_jurisdictions", "`jurisdictions` must be a list", path="jurisdictions")
        jurisdictions = []
    for idx, jurisdiction in enumerate(jurisdictions):
        if jurisdiction not in VALID_JURISDICTIONS:
            add_finding(
                findings,
                "error",
                "invalid_jurisdiction",
                f"invalid jurisdiction `{jurisdiction}`",
                path=f"jurisdictions[{idx}]",
            )

    namespaces = meta.get("namespaces", [])
    if namespaces:
        if not isinstance(namespaces, list):
            add_finding(findings, "error", "invalid_namespaces", "`namespaces` must be a list", path="namespaces")
        else:
            for idx, namespace in enumerate(namespaces):
                if namespace not in VALID_NAMESPACES:
                    add_finding(
                        findings,
                        "error",
                        "invalid_namespace",
                        f"invalid namespace `{namespace}`",
                        path=f"namespaces[{idx}]",
                    )
    elif strict and normalized not in FALLBACK_MODES:
        add_finding(findings, "error", "missing_namespaces", "`namespaces` must be present outside fallback modes")

    return normalized


def validate_sources(
    meta: dict[str, Any],
    findings: list[dict[str, str]],
    *,
    mode: str,
) -> None:
    sources = meta.get("sources", [])
    if not isinstance(sources, list):
        add_finding(findings, "error", "invalid_sources", "`sources` must be a list", path="sources")
        return
    if mode not in FALLBACK_MODES and not sources:
        add_finding(findings, "error", "empty_sources", "`sources` must be non-empty outside fallback modes", path="sources")

    seen: set[str] = set()
    for idx, source in enumerate(sources):
        path = f"sources[{idx}]"
        if not isinstance(source, dict):
            add_finding(findings, "error", "invalid_source", "source entry must be an object", path=path)
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not SOURCE_ID_RE.match(sid):
            add_finding(findings, "error", "invalid_source_id", f"invalid source id `{sid}`", path=f"{path}.id")
        elif sid in seen:
            add_finding(findings, "error", "duplicate_source_id", f"duplicate source id `{sid}`", path=f"{path}.id")
        else:
            seen.add(sid)
        if not source.get("authority_id"):
            add_finding(findings, "error", "missing_authority_id", "source authority_id is empty", path=f"{path}.authority_id")
        namespace = source.get("namespace")
        if namespace and namespace not in VALID_NAMESPACES:
            add_finding(findings, "error", "invalid_source_namespace", f"invalid namespace `{namespace}`", path=f"{path}.namespace")
        jurisdiction = source.get("jurisdiction")
        if jurisdiction and jurisdiction not in VALID_JURISDICTIONS:
            add_finding(findings, "error", "invalid_source_jurisdiction", f"invalid jurisdiction `{jurisdiction}`", path=f"{path}.jurisdiction")


def validate_issues_and_findings(
    meta: dict[str, Any],
    findings: list[dict[str, str]],
    *,
    strict: bool,
) -> None:
    ids = source_id_set(meta)
    issues = meta.get("issue_map", [])
    if not isinstance(issues, list):
        add_finding(findings, "error", "invalid_issue_map", "`issue_map` must be a list", path="issue_map")
        issues = []
    if not issues:
        add_finding(findings, "error", "empty_issue_map", "`issue_map` must not be empty", path="issue_map")

    checks = meta.get("claim_checks", [])
    direct_claim_issue_ids = {
        check.get("issue_id")
        for check in checks
        if isinstance(check, dict) and check.get("support_strength") == "direct"
    } if isinstance(checks, list) else set()

    for issue_idx, issue in enumerate(issues):
        path = f"issue_map[{issue_idx}]"
        if not isinstance(issue, dict):
            add_finding(findings, "error", "invalid_issue", "issue entry must be an object", path=path)
            continue
        for field in ("issue", "answer", "confidence"):
            if is_empty_load_bearing(issue.get(field)):
                add_finding(findings, "error", "empty_issue_field", f"issue field `{field}` is empty", path=f"{path}.{field}")
        if has_placeholder(issue.get("answer")):
            add_finding(findings, "error", "placeholder_issue_answer", "issue answer contains a placeholder", path=f"{path}.answer")
        authority_ids = issue.get("authority_ids", [])
        if not isinstance(authority_ids, list):
            add_finding(findings, "error", "invalid_issue_authority_ids", "authority_ids must be a list", path=f"{path}.authority_ids")
            authority_ids = []
        for ref in authority_ids:
            if ref not in ids:
                add_finding(findings, "error", "unknown_issue_source", f"issue references unknown source `{ref}`", path=f"{path}.authority_ids")
        if strict and issue.get("confidence") == "high":
            issue_id = issue.get("issue_id")
            if checks and issue_id not in direct_claim_issue_ids:
                add_finding(
                    findings,
                    "error",
                    "high_confidence_without_direct_claim",
                    "high-confidence issue lacks a direct claim_check",
                    path=path,
                )

    key_findings = meta.get("key_findings", [])
    if not isinstance(key_findings, list):
        add_finding(findings, "error", "invalid_key_findings", "`key_findings` must be a list", path="key_findings")
        return
    if not key_findings:
        add_finding(findings, "error", "empty_key_findings", "`key_findings` must not be empty", path="key_findings")
    for idx, finding in enumerate(key_findings):
        path = f"key_findings[{idx}]"
        if not isinstance(finding, str) or not finding.strip():
            add_finding(findings, "error", "invalid_key_finding", "key finding must be a non-empty string", path=path)
            continue
        if ids and not SOURCE_ID_IN_TEXT_RE.search(finding):
            severity = "error" if strict else "warn"
            add_finding(
                findings,
                severity,
                "key_finding_missing_source_anchor",
                "key finding should cite at least one src_NNN anchor",
                path=path,
            )


def validate_claim_checks(meta: dict[str, Any], findings: list[dict[str, str]]) -> None:
    checks = meta.get("claim_checks")
    if checks is None:
        return
    if not isinstance(checks, list):
        add_finding(findings, "error", "invalid_claim_checks", "`claim_checks` must be a list", path="claim_checks")
        return
    ids = source_id_set(meta)
    for idx, check in enumerate(checks):
        path = f"claim_checks[{idx}]"
        if not isinstance(check, dict):
            add_finding(findings, "error", "invalid_claim_check", "claim_check entry must be an object", path=path)
            continue
        for ref in check.get("authority_ids", []):
            if ref not in ids:
                add_finding(findings, "error", "unknown_claim_source", f"claim_check references unknown source `{ref}`", path=path)


def validate_sections(
    result_text: str,
    findings: list[dict[str, str]],
    *,
    strict: bool,
    mode: str,
) -> None:
    if strict:
        for section in REQUIRED_RESULT_SECTIONS:
            if not section_present(result_text, section):
                add_finding(findings, "error", "missing_result_section", f"missing result section `{section}`")
        if mode in {"ca_only", "kr_only", "eu_only"}:
            for section in ("## Issues", "## Analysis"):
                if not section_present(result_text, section):
                    add_finding(findings, "error", "missing_single_juris_section", f"missing `{section}`")
        if mode == "comparative" and not section_present(result_text, "## Comparison Matrix"):
            add_finding(findings, "error", "missing_comparison_matrix", "comparative mode requires `## Comparison Matrix`")
        if mode == "multi_jurisdiction":
            if "## Issues -" not in result_text and "## Issues" not in result_text:
                add_finding(findings, "error", "missing_multi_juris_issues", "multi_jurisdiction mode requires labelled issue sections")
            if "## Analysis -" not in result_text and "## Analysis" not in result_text:
                add_finding(findings, "error", "missing_multi_juris_analysis", "multi_jurisdiction mode requires labelled analysis sections")
        return

    if not result_text.startswith("# Data Protection Agent Research Packet"):
        add_finding(findings, "warn", "legacy_title_unexpected", "legacy packet title was not found")
    for section in LEGACY_REQUIRED_RESULT_SECTIONS:
        if not section_present(result_text, section):
            add_finding(findings, "error", "missing_legacy_result_section", f"missing legacy result section `{section}`")


def validate_placeholders(meta: dict[str, Any], findings: list[dict[str, str]]) -> None:
    if has_placeholder(meta.get("summary")):
        add_finding(findings, "error", "placeholder_summary", "summary contains a placeholder", path="summary")
    for idx, gap in enumerate(meta.get("coverage_gaps", [])):
        if not isinstance(gap, str) or not gap.strip():
            add_finding(findings, "error", "invalid_coverage_gap", "coverage gap must be a non-empty string", path=f"coverage_gaps[{idx}]")
        elif has_placeholder(gap):
            add_finding(findings, "error", "placeholder_coverage_gap", "coverage gap contains a placeholder", path=f"coverage_gaps[{idx}]")


def validate_source_coverage(meta: dict[str, Any], findings: list[dict[str, str]], *, mode: str) -> None:
    by_id = source_by_id(meta)
    for idx, issue in enumerate(meta.get("issue_map", [])):
        if not isinstance(issue, dict):
            continue
        if issue.get("confidence") not in {"medium", "high"}:
            continue
        refs = issue.get("authority_ids", [])
        if not refs:
            add_finding(findings, "warn", "confident_issue_without_sources", "medium/high confidence issue has no source refs", path=f"issue_map[{idx}]")
            continue
        if not any(by_id.get(ref, {}).get("grade") == "A" for ref in refs):
            add_finding(findings, "warn", "confident_issue_without_grade_a", "medium/high confidence issue lacks a Grade A source", path=f"issue_map[{idx}]")

    if mode == "comparative":
        counts: dict[str, int] = {}
        for source in meta.get("sources", []):
            if isinstance(source, dict):
                jurisdiction = source.get("jurisdiction")
                if jurisdiction:
                    counts[jurisdiction] = counts.get(jurisdiction, 0) + 1
        for jurisdiction in meta.get("jurisdictions", []):
            if counts.get(jurisdiction, 0) < 2:
                add_finding(
                    findings,
                    "warn",
                    "comparative_low_source_count",
                    f"comparative mode has fewer than 2 sources for {jurisdiction}",
                )


def validate_output_dir(output_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    result_path = output_dir / RESULT_FILENAME
    meta_path = output_dir / META_FILENAME

    if not result_path.exists():
        add_finding(findings, "error", "missing_result_file", f"missing {RESULT_FILENAME}", path=str(result_path))
    if not meta_path.exists():
        add_finding(findings, "error", "missing_meta_file", f"missing {META_FILENAME}", path=str(meta_path))
    if findings:
        return report(output_dir, "unknown", findings)

    result_text = result_path.read_text(encoding="utf-8")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_finding(findings, "error", "invalid_meta_json", f"meta JSON parse failed: {exc}", path=str(meta_path))
        return report(output_dir, "unknown", findings)

    if not isinstance(meta, dict):
        add_finding(findings, "error", "invalid_meta_root", "meta JSON root must be an object", path=str(meta_path))
        return report(output_dir, "unknown", findings)

    kind = detect_result_kind(meta, result_text)
    strict = kind == "v19_result"
    validate_required_keys(meta, findings, strict=strict)
    mode = validate_mode_and_scope(meta, findings, strict=strict)
    validate_sources(meta, findings, mode=mode)
    validate_issues_and_findings(meta, findings, strict=strict)
    validate_claim_checks(meta, findings)
    validate_sections(result_text, findings, strict=strict, mode=mode)
    validate_placeholders(meta, findings)
    validate_source_coverage(meta, findings, mode=mode)
    validate_output_mode_fields(meta, findings)

    return report(output_dir, kind, findings)


def report(output_dir: Path, result_kind: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    errors = sum(1 for finding in findings if finding["severity"] == "error")
    warnings = sum(1 for finding in findings if finding["severity"] == "warn")
    return {
        "type": "data_protection_agent_validation",
        "agent_id": AGENT_ID,
        "output_dir": str(output_dir),
        "result_kind": result_kind,
        "status": "fail" if errors else "pass",
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "findings": len(findings),
        },
        "findings": findings,
    }


def print_plain(validation: dict[str, Any]) -> None:
    summary = validation["summary"]
    print(
        f"validate-output {validation['status']}: "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s); "
        f"kind={validation['result_kind']}"
    )
    for finding in validation["findings"]:
        path = f" [{finding['path']}]" if finding.get("path") else ""
        print(f"{finding['severity'].upper()} {finding['code']}{path}: {finding['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    validation = validate_output_dir(args.output_dir)
    if args.json:
        print(json.dumps(validation, indent=2, ensure_ascii=False))
    else:
        print_plain(validation)
    return 0 if validation["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
