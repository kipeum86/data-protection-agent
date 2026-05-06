#!/usr/bin/env python3
"""Write data-protection-agent result/meta files from local KB retrieval.

This runner intentionally does not synthesize a final legal opinion. It creates
a grounded research packet that satisfies the orchestrator output contract and
points the next writing step to local authority files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.retrieve_authorities import retrieve_authorities

RESULT_FILENAME = "data-protection-agent-result.md"
META_FILENAME = "data-protection-agent-meta.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_entry(authority: dict[str, Any], ordinal: int) -> dict[str, Any]:
    source_id = f"src_{ordinal:03d}"
    return {
        "id": source_id,
        "authority_id": authority["unified_id"],
        "jurisdiction": authority.get("jurisdiction", ""),
        "namespace": authority.get("namespace", ""),
        "title": authority.get("title", "") or authority.get("citation", "") or authority["unified_id"],
        "grade": authority.get("source_grade", ""),
        "authority_group": authority.get("authority_group", ""),
        "authority_level": authority.get("authority_level", ""),
        "precedential_status": authority.get("precedential_status", ""),
        "citation": authority.get("citation", ""),
        "pinpoint": authority.get("citation", ""),
        "url_or_access": authority.get("official_url", ""),
        "local_path": authority.get("path", ""),
        "match_score": authority.get("score", 0),
        "match_reasons": authority.get("match_reasons", []),
    }


def build_sources(authorities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [source_entry(authority, idx) for idx, authority in enumerate(authorities, start=1)]


def source_ids_by_jurisdiction(sources: list[dict[str, Any]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for source in sources:
        grouped.setdefault(source.get("jurisdiction", ""), []).append(source["id"])
    return grouped


def build_issue_map(result: dict[str, Any], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not sources:
        return [{
            "issue": "Coverage check",
            "answer": "No local authority was retrieved for a grounded legal answer.",
            "authority_ids": [],
            "confidence": "low",
        }]

    by_jurisdiction = source_ids_by_jurisdiction(sources)
    issue_map = []
    matched_topics = result.get("matched_topics", [])

    if matched_topics:
        for topic in matched_topics[:3]:
            topic_refs = set(topic.get("authority_refs", []))
            authority_ids = [
                source["id"]
                for source in sources
                if source.get("authority_id") in topic_refs
            ]
            if not authority_ids:
                continue
            caution = "; ".join(topic.get("answer_cautions", [])[:2])
            answer = f"Local KB topic match: {topic.get('title', '')}. Use the listed authorities before drafting a legal conclusion."
            if caution:
                answer = f"{answer} Cautions: {caution}"
            issue_map.append({
                "issue": topic.get("title", "Matched topic"),
                "answer": answer,
                "authority_ids": authority_ids,
                "confidence": "high" if topic.get("score", 0) >= 4 else "medium",
            })

    if not issue_map:
        for jurisdiction, source_ids in sorted(by_jurisdiction.items()):
            issue_map.append({
                "issue": f"{jurisdiction or 'Unclassified'} authority grounding",
                "answer": "Local KB authorities were retrieved. Read the cited markdown files and preserve source-grade caveats when drafting.",
                "authority_ids": source_ids[:6],
                "confidence": "medium",
            })

    return issue_map


def build_comparison_matrix(result: dict[str, Any], sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    if result.get("research_mode") != "comparative":
        return []

    grouped: dict[str, list[str]] = {}
    for source in sources:
        label = source.get("citation") or source.get("title") or source.get("authority_id", "")
        grouped.setdefault(source.get("jurisdiction", ""), []).append(label)

    return [{
        "topic": "Retrieved local authority coverage",
        "KR": "; ".join(grouped.get("KR", [])[:4]) or "No KR authority retrieved.",
        "EU": "; ".join(grouped.get("EU", [])[:4]) or "No EU authority retrieved.",
        "US-CA": "; ".join(grouped.get("US-CA", [])[:4]) or "No California authority retrieved.",
        "practical_delta": "Analyze each jurisdiction separately before stating a unified compliance recommendation.",
    }]


def key_findings(result: dict[str, Any], sources: list[dict[str, Any]]) -> list[str]:
    findings = [
        f"Classified research mode as `{result.get('research_mode')}`.",
    ]
    jurisdictions = result.get("jurisdictions", [])
    if jurisdictions:
        findings.append(f"Selected jurisdiction(s): {', '.join(jurisdictions)}.")
    if sources:
        grade_a = [source for source in sources if source.get("grade") == "A"]
        findings.append(f"Retrieved {len(sources)} local authorities, including {len(grade_a)} Grade A source(s).")
        top = sources[0]
        label = top.get("citation") or top.get("title") or top.get("authority_id")
        findings.append(f"Top ranked authority: {label} (`{top.get('authority_id')}`).")
    else:
        findings.append("No local authority was retrieved.")
    for gap in result.get("coverage_gaps", []):
        findings.append(f"Coverage gap: {gap}")
    return findings


def build_summary(result: dict[str, Any], sources: list[dict[str, Any]]) -> str:
    jurisdictions = ", ".join(result.get("jurisdictions", [])) or "unclassified"
    return (
        f"Local KB research packet for `{result.get('research_mode')}` mode "
        f"({jurisdictions}); {len(sources)} source(s) retrieved. "
        "Use cited local paths for grounded drafting."
    )


def build_meta(query: str, result: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    issue_map = build_issue_map(result, sources)
    return {
        "summary": build_summary(result, sources),
        "research_mode": result.get("research_mode", "fallback"),
        "jurisdictions": result.get("jurisdictions", []),
        "domains": ["data_protection"],
        "legacy_scope": legacy_scope(result.get("namespaces", [])),
        "query": query,
        "generated_at": utc_now(),
        "issue_map": issue_map,
        "comparison_matrix": build_comparison_matrix(result, sources),
        "key_findings": key_findings(result, sources),
        "sources": sources,
        "matched_topics": result.get("matched_topics", []),
        "route_matches": result.get("route_matches", []),
        "coverage_gaps": result.get("coverage_gaps", []),
        "error": None,
    }


def legacy_scope(namespaces: list[str]) -> list[str]:
    scope = []
    if "kr-pipa" in namespaces:
        scope.append("PIPA-expert")
    if "eu-gdpr" in namespaces:
        scope.append("GDPR-expert")
    if "us-ca" in namespaces:
        scope.append("California-local-kb")
    return scope


def markdown_table(sources: list[dict[str, Any]]) -> list[str]:
    if not sources:
        return ["No local sources retrieved."]
    lines = [
        "| ID | Authority | Citation | Grade | Type | Local path |",
        "|---|---|---|---|---|---|",
    ]
    for source in sources:
        title = escape_pipe(source.get("title", ""))
        citation = escape_pipe(source.get("citation", ""))
        local_path = escape_pipe(source.get("local_path", ""))
        lines.append(
            f"| `{source['id']}` | `{source['authority_id']}` {title} | {citation} | "
            f"{source.get('grade', '')} | {source.get('authority_group', '')} | `{local_path}` |"
        )
    return lines


def escape_pipe(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_result_markdown(query: str, result: dict[str, Any], meta: dict[str, Any]) -> str:
    lines = [
        "# Data Protection Agent Research Packet",
        "",
        f"Question: {query}",
        "",
        f"- Research mode: `{meta['research_mode']}`",
        f"- Jurisdictions: {', '.join(meta['jurisdictions']) or 'not classified'}",
        f"- Generated at: {meta['generated_at']}",
        "",
        "This file is a grounded research packet, not a final legal opinion. Draft from the cited local authorities and preserve source-grade caveats.",
        "",
        "## Key Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in meta["key_findings"])

    if meta.get("coverage_gaps"):
        lines.extend(["", "## Coverage Gaps", ""])
        lines.extend(f"- {gap}" for gap in meta["coverage_gaps"])

    lines.extend(["", "## Issue Map", ""])
    for issue in meta["issue_map"]:
        authority_ids = ", ".join(f"`{source_id}`" for source_id in issue.get("authority_ids", [])) or "none"
        lines.append(f"### {issue['issue']}")
        lines.append("")
        lines.append(issue["answer"])
        lines.append("")
        lines.append(f"- Confidence: {issue['confidence']}")
        lines.append(f"- Sources: {authority_ids}")
        lines.append("")

    if meta.get("comparison_matrix"):
        lines.extend(["## Comparison Matrix", ""])
        lines.append("| Topic | KR | EU | US-CA | Practical delta |")
        lines.append("|---|---|---|---|---|")
        for row in meta["comparison_matrix"]:
            lines.append(
                f"| {escape_pipe(row['topic'])} | {escape_pipe(row['KR'])} | "
                f"{escape_pipe(row['EU'])} | {escape_pipe(row['US-CA'])} | "
                f"{escape_pipe(row['practical_delta'])} |"
            )
        lines.append("")

    lines.extend(["## Sources", ""])
    lines.extend(markdown_table(meta["sources"]))

    if result.get("matched_topics"):
        lines.extend(["", "## Matched Topics", ""])
        for topic in result["matched_topics"]:
            cautions = "; ".join(topic.get("answer_cautions", []))
            line = f"- `{topic['unified_id']}` ({topic.get('score', 0)}): {topic.get('title', '')}"
            if cautions:
                line = f"{line}. Cautions: {cautions}"
            lines.append(line)

    return "\n".join(lines).rstrip() + "\n"


def generate_outputs(
    query: str,
    output_dir: Path,
    *,
    top_k: int = 12,
    namespaces: list[str] | None = None,
) -> dict[str, Any]:
    result = retrieve_authorities(query, top_k=top_k, namespaces=namespaces)
    sources = build_sources(result.get("authorities", []))
    meta = build_meta(query, result, sources)
    markdown = build_result_markdown(query, result, meta)

    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / RESULT_FILENAME
    meta_path = output_dir / META_FILENAME
    result_path.write_text(markdown, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "result_path": str(result_path),
        "meta_path": str(meta_path),
        "meta": meta,
    }


def default_output_dir() -> Path:
    env_value = os.environ.get("OUTPUT_DIR")
    if env_value:
        return Path(env_value)
    return ROOT / "outputs" / "data-protection-agent"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Privacy/data-protection research query")
    parser.add_argument("--output-dir", type=Path, default=None, help="Defaults to OUTPUT_DIR or outputs/data-protection-agent")
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--namespace", action="append", help="Restrict retrieval to namespace; can repeat")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir or default_output_dir()
    generated = generate_outputs(args.query, output_dir, top_k=args.top_k, namespaces=args.namespace)
    if args.print_summary:
        print(json.dumps({
            "result_path": generated["result_path"],
            "meta_path": generated["meta_path"],
            "summary": generated["meta"]["summary"],
            "sources": len(generated["meta"]["sources"]),
        }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
