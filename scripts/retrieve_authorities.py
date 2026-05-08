#!/usr/bin/env python3
"""Classify a privacy-law query and retrieve local KB authorities.

This is a lightweight, deterministic retrieval helper for the merged
data-protection-agent. It intentionally uses local JSON indexes only; no
external search or model call is performed here.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "index"
CONFIG_PATH = ROOT / "config" / "rag-config.json"

MODE_BY_NAMESPACE = {
    "eu-gdpr": "gdpr",
    "kr-pipa": "pipa",
    "us-ca": "california",
}

JURISDICTION_BY_NAMESPACE = {
    "eu-gdpr": "EU",
    "kr-pipa": "KR",
    "us-ca": "US-CA",
}

US_NON_CA_TERMS = {
    "colorado",
    "connecticut",
    "utah",
    "virginia",
    "texas",
    "florida",
    "new york",
    "washington",
    "oregon",
    "delaware",
    "iowa",
    "tennessee",
    "montana",
}

PRIVACY_TERMS = {
    "privacy",
    "data",
    "personal",
    "consent",
    "transfer",
    "processor",
    "controller",
    "notice",
    "breach",
    "sensitive",
    "children",
    "automated",
    "profiling",
    "개인정보",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "california",
    "does",
    "for",
    "from",
    "how",
    "in",
    "include",
    "into",
    "is",
    "it",
    "must",
    "of",
    "or",
    "question",
    "require",
    "requires",
    "the",
    "to",
    "under",
    "what",
    "when",
    "with",
    "obligation",
    "obligations",
    "right",
    "rights",
}

QUERY_AUTHORITY_HINTS = [
    {
        "namespace": "kr-pipa",
        "terms": {"overseas", "transfer", "cross-border", "국외", "이전"},
        "authority_ids": {
            "kr-pipa:pipa-art28-8": 28,
            "kr-pipa:pipa-art28-9": 18,
            "kr-pipa:pipa-enforcement-decree-art29-10": 22,
            "kr-pipa:pipa-enforcement-decree-art29-7": 14,
            "kr-pipa:pipa-enforcement-decree-art29-8": 14,
        },
    },
    {
        "namespace": "kr-pipa",
        "terms": {"vendor", "contract", "outsourcing", "processor", "위탁", "수탁"},
        "authority_ids": {
            "kr-pipa:pipa-art26": 26,
            "kr-pipa:pipa-enforcement-decree-art28": 20,
        },
    },
    {
        "namespace": "kr-pipa",
        "terms": {"notice", "policy", "privacy", "처리방침", "고지", "통지"},
        "authority_ids": {
            "kr-pipa:pipa-art30": 24,
            "kr-pipa:pipa-art20": 14,
            "kr-pipa:pipa-enforcement-decree-art31": 18,
            "kr-pipa:pipa-enforcement-decree-art15-2": 12,
        },
    },
    {
        "namespace": "kr-pipa",
        "terms": {"children", "child", "minor", "minors", "아동", "청소년"},
        "authority_ids": {
            "kr-pipa:pipa-art22-2": 26,
            "kr-pipa:pipa-enforcement-decree-art17-2": 20,
        },
    },
    {
        "namespace": "eu-gdpr",
        "terms": {"children", "child", "minor", "minors"},
        "authority_ids": {
            "eu-gdpr:gdpr-art8": 28,
        },
    },
    {
        "namespace": "us-ca",
        "terms": {"applicability", "threshold", "thresholds"},
        "authority_ids": {
            "us-ca:ca-civ-1798.140": 24,
            "us-ca:ca-cppa-cpi-adjustment": 18,
        },
    },
    {
        "namespace": "us-ca",
        "terms": {"children", "child", "minor", "minors"},
        "authority_ids": {
            "us-ca:ca-civ-1798.120": 20,
            "us-ca:ca-11-ccr-7070": 26,
            "us-ca:ca-11-ccr-7071": 26,
            "us-ca:ca-bpc-22584": 14,
        },
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        return read_json(CONFIG_PATH)
    return {
        "default_top_k": 12,
        "per_namespace_top_k": 8,
        "topic_boost": 7,
        "citation_boost": 6,
        "title_boost": 4,
        "keyword_boost": 3,
        "body_metadata_boost": 1,
        "minimum_score": 2,
        "authority_group_priority": {},
    }


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣][A-Za-z0-9가-힣_.§-]*", text.lower())
    cleaned = [
        token.strip("._-")
        for token in tokens
        if len(token.strip("._-")) >= 2 and token.strip("._-") not in STOPWORDS
    ]
    expanded = []
    for token in cleaned:
        expanded.append(token)
        if token == "decisionmaking":
            expanded.append("decision-making")
        elif token == "admt":
            expanded.extend(["automated", "decisionmaking", "decision-making"])
    return expanded


def phrase_in(text: str, phrase: str) -> bool:
    text_lower = text.lower()
    phrase_lower = phrase.lower().strip()
    if not phrase_lower:
        return False
    if re.search(r"[가-힣]", phrase_lower):
        return phrase_lower in text_lower
    if re.fullmatch(r"[a-z0-9]+", phrase_lower):
        return re.search(rf"(?<![a-z0-9]){re.escape(phrase_lower)}(?![a-z0-9])", text_lower) is not None
    # Treat space and hyphen as interchangeable separators so that a search
    # term like "breach notification" matches "breach-notification" in the
    # query (and vice versa). Same for "decision making" / "decision-making".
    pattern = re.escape(phrase_lower).replace(r"\ ", r"[\s-]+").replace(r"\-", r"[\s-]+")
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text_lower) is not None


def classify_query(query: str) -> dict[str, Any]:
    routing = read_json(INDEX_DIR / "jurisdiction-routing.json")
    lower_query = query.lower()
    route_matches = []

    for route in routing.get("routes", []):
        matched_terms = [
            term
            for term in route.get("routing_terms", [])
            if phrase_in(lower_query, term)
        ]
        if matched_terms:
            route_matches.append({
                "namespace": route["namespace"],
                "jurisdiction": route["jurisdiction"],
                "primary_law": route["primary_law"],
                "matched_terms": matched_terms,
                "score": len(matched_terms),
            })

    namespaces = sorted({match["namespace"] for match in route_matches})
    jurisdictions = [JURISDICTION_BY_NAMESPACE[namespace] for namespace in namespaces]
    coverage_gaps: list[str] = []

    if len(namespaces) >= 2:
        research_mode = "comparative"
    elif len(namespaces) == 1:
        research_mode = MODE_BY_NAMESPACE[namespaces[0]]
    elif any(term in lower_query for term in US_NON_CA_TERMS):
        research_mode = "fallback_us"
        coverage_gaps.append("Built-in US coverage is California-focused; no full non-California state KB is loaded.")
    elif any(term in lower_query for term in PRIVACY_TERMS):
        research_mode = "fallback"
        coverage_gaps.append("No jurisdiction-specific routing term matched. Ask for KR, EU/GDPR, or California/CCPA for grounded retrieval.")
    else:
        research_mode = "fallback"
        coverage_gaps.append("The query does not appear to be a privacy/data-protection research request.")

    return {
        "research_mode": research_mode,
        "namespaces": namespaces,
        "jurisdictions": jurisdictions,
        "route_matches": sorted(route_matches, key=lambda item: (-item["score"], item["namespace"])),
        "coverage_gaps": coverage_gaps,
    }


def topic_scores(query: str, namespaces: set[str], config: dict[str, Any]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    topic_index = read_json(INDEX_DIR / "unified-topic-index.json")
    query_tokens = set(tokenize(query))
    authority_scores: dict[str, int] = defaultdict(int)
    matched_topics: list[dict[str, Any]] = []

    for topic in topic_index.get("topics", []):
        if namespaces and topic.get("namespace") not in namespaces:
            continue
        search_text = " ".join([
            topic.get("title", ""),
            topic.get("summary", ""),
            " ".join(topic.get("search_terms", [])),
        ]).lower()
        score = 0
        for term in topic.get("search_terms", []):
            if phrase_in(query, term):
                score += 4
        score += len(query_tokens.intersection(tokenize(search_text)))
        if score <= 0:
            continue
        boost = score + int(config.get("topic_boost", 7))
        for authority_ref in topic.get("authority_refs", []):
            authority_scores[authority_ref] += boost
        matched_topics.append({
            "unified_id": topic["unified_id"],
            "namespace": topic["namespace"],
            "jurisdiction": topic["jurisdiction"],
            "title": topic.get("title", ""),
            "score": score,
            "answer_cautions": topic.get("answer_cautions", []),
            "authority_refs": topic.get("authority_refs", []),
        })

    matched_topics.sort(key=lambda item: (-item["score"], item["unified_id"]))
    return dict(authority_scores), matched_topics[:5]


def authority_text(authority: dict[str, Any]) -> dict[str, str]:
    title = str(authority.get("title", ""))
    citation = str(authority.get("citation", ""))
    metadata = " ".join([
        str(authority.get("unified_id", "")),
        str(authority.get("original_id", "")),
        str(authority.get("source_family", "")),
        str(authority.get("authority_group", "")),
        str(authority.get("authority_level", "")),
        str(authority.get("precedential_status", "")),
        " ".join(str(item) for item in authority.get("topics", [])),
    ])
    keywords = " ".join(str(item) for item in authority.get("keywords", []))
    return {
        "title": title.lower(),
        "citation": citation.lower(),
        "metadata": metadata.lower(),
        "keywords": keywords.lower(),
    }


def score_authority(authority: dict[str, Any], query: str, topic_boost: int, config: dict[str, Any]) -> tuple[int, list[str]]:
    query_tokens = set(tokenize(query))
    texts = authority_text(authority)
    score = topic_boost
    reasons: list[str] = []
    specific_match = bool(topic_boost)

    if topic_boost:
        reasons.append("topic")

    for token in query_tokens:
        if token in texts["citation"]:
            score += int(config.get("citation_boost", 6))
            reasons.append(f"citation:{token}")
            specific_match = True
        if token in texts["title"]:
            score += int(config.get("title_boost", 4))
            reasons.append(f"title:{token}")
            specific_match = True
        if token in texts["keywords"]:
            score += int(config.get("keyword_boost", 3))
            reasons.append(f"keyword:{token}")
            specific_match = True
        if token in texts["metadata"]:
            score += int(config.get("body_metadata_boost", 1))

    citation_patterns = re.findall(r"\b(?:art(?:icle)?\.?\s*)?\d{1,4}(?:-\d+|\.\d+)?\b|§\s*\d{1,4}(?:\.\d+)*", query.lower())
    for pattern in citation_patterns:
        normalized = pattern.replace("§", "").replace("article", "").replace("art.", "").strip()
        if normalized and normalized in texts["citation"] + " " + texts["title"] + " " + texts["metadata"]:
            score += int(config.get("citation_boost", 6))
            reasons.append(f"pinpoint:{normalized}")
            specific_match = True

    priority = config.get("authority_group_priority", {}).get(authority.get("authority_group", ""), 0)
    score += int(priority)
    if priority:
        reasons.append(f"group:{authority.get('authority_group')}")

    query_lower = query.lower()
    source_family = authority.get("source_family", "")
    if specific_match and "gdpr" in query_lower and source_family in {"gdpr", "gdpr-recitals"}:
        score += 8
        reasons.append("primary-law:gdpr")
    ca_primary_families = {
        "ca-ccpa-statute", "ca-ccpa-regulations",
        # Adjacent California privacy statutes the user naturally expects
        # to surface for a "California" question:
        "ca-customer-records", "ca-caloppa", "ca-cipa", "ca-cmia",
        "ca-data-broker-delete-act", "ca-age-appropriate-design-code",
    }
    if specific_match and ("ccpa" in query_lower or "cpra" in query_lower or "california" in query_lower) and source_family in ca_primary_families:
        score += 8
        reasons.append("primary-law:ca")
    if specific_match and "pipa" in query_lower and source_family in {"pipa", "pipa-enforcement-decree"}:
        score += 8
        reasons.append("primary-law:pipa")

    for hint in QUERY_AUTHORITY_HINTS:
        if authority.get("namespace") != hint["namespace"]:
            continue
        hint_boost = hint["authority_ids"].get(authority.get("unified_id"))
        if not hint_boost:
            continue
        if query_tokens.intersection(hint["terms"]):
            score += hint_boost
            reasons.append("query-hint")

    return score, sorted(set(reasons))[:8]


def retrieve_authorities(query: str, top_k: int | None = None, namespaces: list[str] | None = None) -> dict[str, Any]:
    config = load_config()
    classification = classify_query(query)
    selected_namespaces = set(namespaces or classification["namespaces"])
    if not selected_namespaces and classification["research_mode"] in {"fallback", "fallback_us"}:
        return {
            "query": query,
            "research_mode": classification["research_mode"],
            "jurisdictions": classification["jurisdictions"],
            "namespaces": classification["namespaces"],
            "route_matches": classification["route_matches"],
            "matched_topics": [],
            "authorities": [],
            "coverage_gaps": classification["coverage_gaps"],
        }

    topic_boosts, matched_topics = topic_scores(query, selected_namespaces, config)
    authority_index = read_json(INDEX_DIR / "unified-authority-index.json")
    minimum_score = int(config.get("minimum_score", 2))
    scored = []

    for authority in authority_index.get("authorities", []):
        if selected_namespaces and authority.get("namespace") not in selected_namespaces:
            continue
        score, reasons = score_authority(
            authority,
            query,
            topic_boosts.get(authority.get("unified_id", ""), 0),
            config,
        )
        if score < minimum_score:
            continue
        scored.append({
            "score": score,
            "match_reasons": reasons,
            "unified_id": authority.get("unified_id", ""),
            "namespace": authority.get("namespace", ""),
            "jurisdiction": authority.get("jurisdiction", ""),
            "primary_law": authority.get("primary_law", ""),
            "authority_group": authority.get("authority_group", ""),
            "title": authority.get("title", ""),
            "citation": authority.get("citation", ""),
            "path": authority.get("path", ""),
            "source_family": authority.get("source_family", ""),
            "source_grade": authority.get("source_grade", ""),
            "authority_level": authority.get("authority_level", ""),
            "precedential_status": authority.get("precedential_status", ""),
            "official_url": authority.get("official_url", ""),
            "topics": authority.get("topics", []),
        })

    limit = top_k or int(config.get("default_top_k", 12))
    authorities = select_ranked(scored, limit, selected_namespaces)

    return {
        "query": query,
        "research_mode": classification["research_mode"],
        "jurisdictions": classification["jurisdictions"],
        "namespaces": sorted(selected_namespaces) if selected_namespaces else classification["namespaces"],
        "route_matches": classification["route_matches"],
        "matched_topics": matched_topics,
        "authorities": authorities,
        "coverage_gaps": classification["coverage_gaps"],
    }


def select_ranked(scored: list[dict[str, Any]], limit: int, selected_namespaces: set[str]) -> list[dict[str, Any]]:
    scored.sort(key=lambda item: (-item["score"], item["namespace"], item["authority_group"], item["unified_id"]))
    if len(selected_namespaces) <= 1:
        return scored[:limit]

    by_namespace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in scored:
        by_namespace[item["namespace"]].append(item)

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    namespace_order = sorted(selected_namespaces)
    offset = 0
    while len(selected) < limit:
        added = False
        for namespace in namespace_order:
            bucket = by_namespace.get(namespace, [])
            if offset >= len(bucket):
                continue
            item = bucket[offset]
            if item["unified_id"] in seen:
                continue
            selected.append(item)
            seen.add(item["unified_id"])
            added = True
            if len(selected) >= limit:
                break
        if not added:
            break
        offset += 1

    return selected


def format_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Retrieval Result",
        "",
        f"- Query: {result['query']}",
        f"- Mode: {result['research_mode']}",
        f"- Jurisdictions: {', '.join(result.get('jurisdictions') or []) or 'not classified'}",
        "",
        "## Authorities",
    ]
    for item in result.get("authorities", []):
        label = item.get("citation") or item.get("title") or item.get("unified_id")
        lines.append(
            f"- {item['unified_id']} ({item['score']}): {label} "
            f"[{item.get('source_grade') or '?'}; {item.get('authority_group')}]"
        )
    if result.get("coverage_gaps"):
        lines.extend(["", "## Coverage Gaps"])
        lines.extend(f"- {gap}" for gap in result["coverage_gaps"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Privacy/data-protection research query")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--namespace", action="append", choices=sorted(MODE_BY_NAMESPACE), help="Restrict retrieval to namespace; can repeat")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    result = retrieve_authorities(args.query, top_k=args.top_k, namespaces=args.namespace)
    if args.format == "markdown":
        print(format_markdown(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
