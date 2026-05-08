#!/usr/bin/env python3
"""Import existing expert KBs under jurisdiction namespaces and build unified indexes."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
KB_ROOT = ROOT / "kb"
INDEX_ROOT = ROOT / "index"

KB_SOURCES = [
    {
        "namespace": "eu-gdpr",
        "jurisdiction": "EU",
        "label": "EU GDPR Expert KB",
        "source": ROOT.parent / "GDPR-expert",
        "primary_law": "GDPR",
        "routing_terms": ["gdpr", "eu", "europe", "edpb", "cjeu", "eprivacy", "ai act", "data act"],
    },
    {
        "namespace": "kr-pipa",
        "jurisdiction": "KR",
        "label": "Korea PIPA Expert KB",
        "source": ROOT.parent / "PIPA-expert",
        "primary_law": "PIPA",
        "routing_terms": ["pipa", "korea", "kr", "korean", "개인정보", "개보법", "보호법", "pipc"],
    },
    {
        "namespace": "us-ca",
        "jurisdiction": "US-CA",
        "label": "California Privacy Expert KB",
        "source": ROOT / "sources" / "us-ca",
        "primary_law": "CCPA",
        "routing_terms": ["ccpa", "cpra", "california", "cppa", "cipa", "caloppa", "gpc"],
    },
]

COPY_DIRS = ["library", "index", "config"]
SKIP_INDEX_FILES = {
    "source-registry.json",
    "article-index.compact.json",
    "cross-reference-graph.json",
    "ca-citation-map.json",
    "ca-topic-index.json",
    "external-law-candidates.json",
    "validation-report.json",
    "golden-questions.ca.json",
}
LIST_KEYS = ["articles", "recitals", "cases", "items", "documents", "proposals", "candidates", "topics"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_reference(src_root: Path) -> str:
    try:
        return str(src_root.relative_to(ROOT))
    except ValueError:
        return f"external:{src_root.name}"


def ignored_names(path: str, names: list[str]) -> set[str]:
    ignored = {
        name for name in names
        if name in {".DS_Store", "__pycache__", ".pytest_cache"} or name.endswith(".pyc")
    }
    if Path(path).name == "library":
        ignored.add("inbox")
    return ignored


def copy_kb(source: dict[str, Any], clean: bool = False) -> dict[str, Any]:
    src_root = source["source"]
    if not src_root.exists():
        raise FileNotFoundError(f"Missing source KB: {src_root}")
    dst_root = KB_ROOT / source["namespace"]
    dst_root.mkdir(parents=True, exist_ok=True)

    copied_dirs = []
    for dirname in COPY_DIRS:
        src = src_root / dirname
        dst = dst_root / dirname
        if not src.exists():
            continue
        if clean and dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignored_names)
        copied_dirs.append(dirname)

    manifest = {
        "namespace": source["namespace"],
        "jurisdiction": source["jurisdiction"],
        "label": source["label"],
        "primary_law": source["primary_law"],
        "source_ref": source_reference(src_root),
        "imported_at": utc_now(),
        "clean_import": clean,
        "copied_dirs": copied_dirs,
        "file_counts": {
            dirname: count_files(dst_root / dirname)
            for dirname in copied_dirs
        },
    }
    write_json(dst_root / "manifest.json", manifest)
    return manifest


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file() and item.name != ".DS_Store")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".md":
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    parsed = yaml.safe_load(text[4:end])
    return parsed if isinstance(parsed, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_unified_source_registry(manifests: list[dict[str, Any]]) -> None:
    entries = []
    for source, manifest in zip(KB_SOURCES, manifests, strict=True):
        registry = read_json(KB_ROOT / source["namespace"] / "index" / "source-registry.json")
        entries.append({
            "namespace": source["namespace"],
            "jurisdiction": source["jurisdiction"],
            "label": source["label"],
            "primary_law": source["primary_law"],
            "kb_path": f"kb/{source['namespace']}",
            "manifest_path": f"kb/{source['namespace']}/manifest.json",
            "source_registry_path": f"kb/{source['namespace']}/index/source-registry.json",
            "library_files": manifest["file_counts"].get("library", 0),
            "index_files": manifest["file_counts"].get("index", 0),
            "original_registry": registry,
        })

    write_json(INDEX_ROOT / "unified-source-registry.json", {
        "type": "unified_source_registry",
        "generated_at": utc_now(),
        "count": len(entries),
        "sources": entries,
    })


def build_jurisdiction_routing() -> None:
    routes = []
    for source in KB_SOURCES:
        namespace = source["namespace"]
        routes.append({
            "namespace": namespace,
            "jurisdiction": source["jurisdiction"],
            "label": source["label"],
            "primary_law": source["primary_law"],
            "routing_terms": source["routing_terms"],
            "library_root": f"kb/{namespace}/library",
            "index_root": f"kb/{namespace}/index",
            "source_registry": f"kb/{namespace}/index/source-registry.json",
            "authority_index_filter": {"namespace": namespace},
        })

    write_json(INDEX_ROOT / "jurisdiction-routing.json", {
        "type": "jurisdiction_routing",
        "generated_at": utc_now(),
        "routes": routes,
        "fallback_order": ["us-ca", "eu-gdpr", "kr-pipa"],
    })


def build_unified_authority_index() -> None:
    authorities: list[dict[str, Any]] = []
    by_namespace = Counter()
    by_authority_group = Counter()
    duplicate_original_ids: dict[str, list[str]] = {}

    for source in KB_SOURCES:
        namespace = source["namespace"]
        index_dir = KB_ROOT / namespace / "index"
        for index_path in sorted(index_dir.glob("*.json")):
            if index_path.name in SKIP_INDEX_FILES:
                continue
            payload = read_json(index_path)
            list_key = first_list_key(payload)
            if not list_key:
                continue
            authority_group = infer_authority_group(index_path.name, list_key)
            for offset, item in enumerate(payload[list_key]):
                if not isinstance(item, dict):
                    continue
                original_id = item.get("id") or synthesize_id(index_path.stem, item, offset)
                unified_id = f"{namespace}:{original_id}"
                duplicate_original_ids.setdefault(original_id, []).append(unified_id)
                path = item.get("path", "")
                frontmatter = read_frontmatter(KB_ROOT / namespace / path) if path else {}
                authorities.append({
                    "unified_id": unified_id,
                    "namespace": namespace,
                    "jurisdiction": source["jurisdiction"],
                    "primary_law": source["primary_law"],
                    "original_id": original_id,
                    "authority_group": authority_group,
                    "source_index": f"kb/{namespace}/index/{index_path.name}",
                    "source_index_type": payload.get("type", index_path.stem),
                    "title": authority_title(item, original_id),
                    "citation": item.get("citation", ""),
                    "path": f"kb/{namespace}/{path}" if path else "",
                    "source_family": item.get("source_family") or frontmatter.get("source_family") or infer_source_family(path),
                    "source_grade": item.get("source_grade") or frontmatter.get("source_grade", ""),
                    "authority_level": item.get("authority_level") or frontmatter.get("authority_level", ""),
                    "precedential_status": item.get("precedential_status") or frontmatter.get("precedential_status", ""),
                    "official_url": item.get("official_url") or item.get("source_url") or frontmatter.get("official_url") or frontmatter.get("source_url") or "",
                    "keywords": item.get("keywords", []),
                    "topics": item.get("topics") or item.get("ccpa_topics") or [],
                })
                by_namespace[namespace] += 1
                by_authority_group[authority_group] += 1

    duplicate_original_ids = {
        original_id: sorted(unified_ids)
        for original_id, unified_ids in duplicate_original_ids.items()
        if len(unified_ids) > 1
    }
    write_json(INDEX_ROOT / "unified-authority-index.json", {
        "type": "unified_authority_index",
        "generated_at": utc_now(),
        "count": len(authorities),
        "by_namespace": dict(sorted(by_namespace.items())),
        "by_authority_group": dict(sorted(by_authority_group.items())),
        "duplicate_original_ids": duplicate_original_ids,
        "authorities": authorities,
    })


TOPIC_INDEX_FILENAMES = {
    "us-ca": "ca-topic-index.json",
    "kr-pipa": "kr-topic-index.json",
    "eu-gdpr": "eu-topic-index.json",
}


def build_unified_topic_index() -> None:
    topics = []
    for source in KB_SOURCES:
        namespace = source["namespace"]
        filename = TOPIC_INDEX_FILENAMES.get(namespace)
        if not filename:
            continue
        topic_index = read_json(KB_ROOT / namespace / "index" / filename)
        if not topic_index:
            continue
        for topic in topic_index.get("topics", []):
            original_id = topic.get("id")
            if not original_id:
                continue
            topics.append({
                "unified_id": f"{namespace}:{original_id}",
                "namespace": namespace,
                "jurisdiction": source["jurisdiction"],
                "original_id": original_id,
                "title": topic.get("title", ""),
                "summary": topic.get("summary", ""),
                "search_terms": topic.get("search_terms", []),
                "authority_refs": collect_topic_refs(namespace, topic),
                "answer_cautions": topic.get("answer_cautions", []),
                "comparative_hooks": topic.get("comparative_hooks", []),
                "coverage_status": topic.get("coverage_status", ""),
            })

    write_json(INDEX_ROOT / "unified-topic-index.json", {
        "type": "unified_topic_index",
        "generated_at": utc_now(),
        "count": len(topics),
        "note": "Imports per-namespace topic indexes (ca-topic-index.json / kr-topic-index.json / eu-topic-index.json).",
        "topics": topics,
    })


def first_list_key(payload: dict[str, Any]) -> str:
    for key in LIST_KEYS:
        if isinstance(payload.get(key), list):
            return key
    return ""


def infer_authority_group(filename: str, list_key: str) -> str:
    if "case" in filename:
        return "case"
    if "recital" in filename:
        return "recital"
    if "enforcement" in filename:
        return "enforcement"
    if "guideline" in filename or "guidance" in filename or "edpb-document" in filename:
        return "guidance"
    if "proposal" in filename:
        return "legislative_proposal"
    if "topic" in filename:
        return "topic"
    if "regulation" in filename:
        return "regulation"
    if "statute" in filename:
        return "statute"
    if "article" in filename:
        return "article"
    return list_key.rstrip("s")


def synthesize_id(index_stem: str, item: dict[str, Any], offset: int) -> str:
    for key in ["path", "citation", "title", "case_name", "name"]:
        value = str(item.get(key, "")).strip()
        if value:
            return f"{index_stem}-{slug(value)}"
    return f"{index_stem}-{offset + 1}"


def slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:120] or "item"


def authority_title(item: dict[str, Any], fallback: str) -> str:
    for key in ["title", "article_title", "case_name", "matter_name", "name", "citation"]:
        value = item.get(key)
        if value:
            return str(value)
    return fallback


def infer_source_family(path: str) -> str:
    parts = Path(path).parts
    if len(parts) >= 3 and parts[0] == "library":
        return parts[2]
    return ""


def collect_topic_refs(namespace: str, topic: dict[str, Any]) -> list[str]:
    refs = []
    for key in ["primary_authorities", "supporting_authorities", "guidance", "enforcement", "cases"]:
        for item in topic.get(key, []):
            source_id = item.get("id")
            if source_id:
                refs.append(f"{namespace}:{source_id}")
    return sorted(set(refs))


def import_kbs(clean: bool = False) -> None:
    KB_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    manifests = [copy_kb(source, clean=clean) for source in KB_SOURCES]
    build_unified_source_registry(manifests)
    build_jurisdiction_routing()
    build_unified_authority_index()
    build_unified_topic_index()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check that source KB directories exist without copying.")
    parser.add_argument("--clean", action="store_true", help="Replace managed library/index/config directories before copying.")
    args = parser.parse_args()

    missing = [str(source["source"]) for source in KB_SOURCES if not source["source"].exists()]
    if missing:
        raise SystemExit(f"Missing source KB directories: {', '.join(missing)}")
    if args.check:
        for source in KB_SOURCES:
            print(f"ok {source['namespace']}: {source['source']}")
        return 0

    import_kbs(clean=args.clean)
    print(f"imported {len(KB_SOURCES)} KB namespaces into {KB_ROOT}")
    print(f"wrote unified indexes into {INDEX_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
