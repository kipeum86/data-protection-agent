#!/usr/bin/env python3
"""Build a local California privacy law KB from public official sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "california-sources.json"
TOPIC_CONFIG_PATH = BASE_DIR / "config" / "california-topic-seeds.json"
RAW_DIR = BASE_DIR / "raw"
LIBRARY_DIR = BASE_DIR / "library"
INDEX_DIR = BASE_DIR / "index"
LOG_DIR = BASE_DIR / "scripts" / "logs"

STATUTE_SECTIONS = [
    "1798.100", "1798.105", "1798.106", "1798.110", "1798.115", "1798.120",
    "1798.121", "1798.125", "1798.130", "1798.135", "1798.136", "1798.140",
    "1798.145", "1798.146", "1798.148", "1798.150", "1798.155", "1798.160",
    "1798.175", "1798.180", "1798.185", "1798.190", "1798.192", "1798.194",
    "1798.196", "1798.198", "1798.199", "1798.199.10", "1798.199.15",
    "1798.199.20", "1798.199.25", "1798.199.30", "1798.199.35",
    "1798.199.40", "1798.199.45", "1798.199.50", "1798.199.55",
    "1798.199.60", "1798.199.65", "1798.199.70", "1798.199.75",
    "1798.199.80", "1798.199.85", "1798.199.90", "1798.199.95",
    "1798.199.100",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_topic_config() -> dict[str, Any]:
    if not TOPIC_CONFIG_PATH.exists():
        return {"topics": [], "golden_questions": []}
    return json.loads(TOPIC_CONFIG_PATH.read_text(encoding="utf-8"))


def ensure_dirs() -> None:
    dirs = [
        RAW_DIR / "official" / "cppa",
        RAW_DIR / "official" / "leginfo",
        RAW_DIR / "official" / "oag",
        RAW_DIR / "official" / "ca-courts",
        RAW_DIR / "official" / "govinfo",
        RAW_DIR / "mirrors" / "scocal",
        RAW_DIR / "discovery" / "manual",
        LIBRARY_DIR / "grade-a" / "ca-ccpa-statute",
        LIBRARY_DIR / "grade-a" / "ca-ccpa-regulations",
        LIBRARY_DIR / "grade-a" / "ca-cppa-guidance",
        LIBRARY_DIR / "grade-a" / "ca-oag-guidance",
        LIBRARY_DIR / "grade-a" / "ca-courts-published-opinions",
        LIBRARY_DIR / "grade-a" / "us-federal-ccpa-opinions",
        LIBRARY_DIR / "grade-b" / "ca-enforcement-actions",
        LIBRARY_DIR / "grade-b" / "ca-administrative-orders",
        LIBRARY_DIR / "grade-b" / "ca-courts-published-opinion-mirrors",
        LIBRARY_DIR / "grade-b" / "ca-rulemaking-reasons",
        LIBRARY_DIR / "grade-b" / "ca-courts-unpublished-opinions",
        LIBRARY_DIR / "grade-b" / "case-materials",
        LIBRARY_DIR / "grade-c" / "case-discovery",
        INDEX_DIR,
        LOG_DIR,
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    print(message)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / f"build-{today()}.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{utc_now()} {message}\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def fetch_url(url: str, raw_path: Path, force: bool = False) -> dict[str, Any]:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists() and not force:
        return {
            "path": relative(raw_path),
            "url": url,
            "status": "cached",
            "checksum": sha256_file(raw_path),
            "bytes": raw_path.stat().st_size,
        }

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "California-KB-Builder/0.1 (+local legal research corpus)",
            "Accept": "*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read()
            final_url = resp.geturl()
            content_type = resp.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error while fetching {url}: {exc}") from exc

    raw_path.write_bytes(content)
    meta = {
        "path": relative(raw_path),
        "url": url,
        "final_url": final_url,
        "content_type": content_type,
        "status": "fetched",
        "checksum": sha256_file(raw_path),
        "bytes": raw_path.stat().st_size,
    }
    (raw_path.with_suffix(raw_path.suffix + ".meta.json")).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return meta


def pdf_to_text(path: Path) -> str:
    txt_path = path.with_suffix(".txt")
    if not txt_path.exists() or txt_path.stat().st_mtime < path.stat().st_mtime:
        if not shutil.which("pdftotext"):
            raise RuntimeError("pdftotext is required for PDF parsing")
        subprocess.run(["pdftotext", "-layout", str(path), str(txt_path)], check=True)
    return txt_path.read_text(encoding="utf-8", errors="replace")


def html_to_markdown(path: Path) -> tuple[str, str, list[dict[str, str]]]:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = normalize_space(h1.get_text(" "))
    if not title and soup.title:
        title = normalize_space(soup.title.get_text(" "))

    root = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile("field-name-body|node-content|content-body", re.I))
        or soup.find(id="block-system-main")
        or soup.body
        or soup
    )
    if len(normalize_space(root.get_text(" "))) < 100 and soup.body:
        root = soup.body
    parts: list[str] = []
    links: list[dict[str, str]] = []
    for elem in root.find_all(["h1", "h2", "h3", "p", "li", "table"], recursive=True):
        text = normalize_space(elem.get_text(" "))
        if not text:
            continue
        if elem.name == "h1":
            parts.append(f"# {text}")
        elif elem.name == "h2":
            parts.append(f"\n## {text}")
        elif elem.name == "h3":
            parts.append(f"\n### {text}")
        elif elem.name == "li":
            parts.append(f"- {text}")
        else:
            parts.append(text)
        for anchor in elem.find_all("a", href=True):
            href = urllib.parse.urljoin("", anchor["href"])
            label = normalize_space(anchor.get_text(" "))
            if href:
                links.append({"label": label, "href": href})
    return title, "\n\n".join(parts), links


def html_links(path: Path, base_url: str) -> list[dict[str, str]]:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    links: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(base_url, anchor["href"])
        label = normalize_space(anchor.get_text(" "))
        links.append({"label": label, "href": href})
    return links


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_pdf_text(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = re.sub(r"\n\s*Page\s+\d+\s+of\s+\d+\s*\n", "\n", text, flags=re.I)
    text = re.sub(r"\n\s*CPPA\s*\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_statute_pdf_text(text: str, *, seed_sections: list[str] | None = None) -> list[dict[str, Any]]:
    seed_sections = seed_sections or STATUTE_SECTIONS
    seed_set = set(seed_sections)
    start = text.find("\f1798.100.")
    if start == -1:
        matches_1798_100 = list(re.finditer(r"(?m)^1798\.100\.", text))
        if len(matches_1798_100) >= 2:
            start = matches_1798_100[1].start()
        elif matches_1798_100:
            start = matches_1798_100[0].start()
        else:
            start = 0
    content = text[start:]
    pattern = re.compile(r"(?m)^\f?(1798\.\d+(?:\.\d+)?)[.]?\s*(.*?)\s*$")
    matches = [m for m in pattern.finditer(content) if m.group(1) in seed_set]
    found = {m.group(1) for m in matches}
    missing = [section for section in seed_sections if section not in found]
    if missing and seed_sections is not STATUTE_SECTIONS:
        raise ValueError(f"missing seed sections: {', '.join(missing)}")
    if not matches:
        raise RuntimeError("No statute section headings found")

    parsed = []
    for idx, match in enumerate(matches):
        section = match.group(1)
        next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section_text = clean_pdf_text(content[match.start():next_start])
        heading_line = normalize_space(section_text.splitlines()[0]) if section_text.splitlines() else ""
        title = normalize_space(heading_line.replace(f"{section}.", "", 1))
        parsed.append({
            "section": section,
            "title": title,
            "body": section_text,
            "raw_offsets": {"start": start + match.start(), "end": start + next_start},
        })
    return parsed


def parse_regulation_pdf_text(text: str) -> list[dict[str, Any]]:
    start = text.find("\f                               ARTICLE 1.")
    if start == -1:
        start = text.find("ARTICLE 1. GENERAL PROVISIONS")
    content = text[start if start != -1 else 0:]
    pattern = re.compile(r"(?m)^\f?§\s+(7\d{3})\.\s*(.*?)\s*$")
    matches = list(pattern.finditer(content))
    if not matches:
        raise RuntimeError("No regulation section headings found")

    parsed = []
    for idx, match in enumerate(matches):
        section = match.group(1)
        next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section_text = clean_pdf_text(content[match.start():next_start])
        heading_line = normalize_space(section_text.splitlines()[0]) if section_text.splitlines() else ""
        title = normalize_space(re.sub(r"^§\s*\d+\.\s*", "", heading_line))
        before = content[:match.start()]
        article_match = list(re.finditer(r"ARTICLE\s+(\d+)\.\s+([^\n]+)", before))
        article_number = article_match[-1].group(1) if article_match else ""
        article_title = normalize_space(article_match[-1].group(2)) if article_match else ""
        authority = extract_statute_ids(re.sub(r"Reference:.*", "", section_text, flags=re.I | re.S))
        references = extract_statute_ids(section_text)
        parsed.append({
            "section": section,
            "title": title,
            "body": section_text,
            "article_number": article_number,
            "article_title": article_title,
            "authority_cited": authority,
            "reference_sections": references,
            "raw_offsets": {"start": start + match.start(), "end": start + next_start},
        })
    return parsed


def parse_case_html(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = normalize_space(soup.get_text(" "))
    title = normalize_space((soup.title.get_text(" ") if soup.title else "") or text[:120])
    court = ""
    if re.search(r"United States District Court", text, flags=re.I):
        court_match = re.search(r"United States District Court[^.|\n]+", text, flags=re.I)
        court = normalize_space(court_match.group(0)) if court_match else "United States District Court"
    elif re.search(r"Ninth Circuit|United States Court of Appeals", text, flags=re.I):
        court = "United States Court of Appeals for the Ninth Circuit"
    elif re.search(r"Supreme Court of California|California Supreme Court", text, flags=re.I):
        court = "Supreme Court of California"
    elif re.search(r"Court of Appeal", text, flags=re.I):
        court_match = re.search(r"(?:California )?Court of Appeal[^.|\n]+", text, flags=re.I)
        court = normalize_space(court_match.group(0)) if court_match else "California Court of Appeal"

    case_name = title
    heading = soup.find(["h1", "h2"])
    if heading:
        case_name = normalize_space(heading.get_text(" "))
    decision_date_match = re.search(r"\b(\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2}, \d{4})\b", text)
    official_citation_match = re.search(r"\b\d+\s+Cal\.(?:App\.)?\d*[A-Za-z]*\s+\d+\b", text)
    unpublished = re.search(r"not\s+certified\s+for\s+publication|unpublished|not\s+citable", text, flags=re.I)
    federal = "United States" in court or "Ninth Circuit" in court
    state_published = not federal and not unpublished
    return {
        "case_name": case_name,
        "court": court,
        "court_system": "federal" if federal else "state",
        "decision_date": decision_date_match.group(1) if decision_date_match else "",
        "official_citation": official_citation_match.group(0) if official_citation_match else "",
        "precedential_status": (
            "unpublished_non_citable" if unpublished
            else "district_court_persuasive" if federal and "District Court" in court
            else "published_citable"
        ),
        "authority_level": (
            "persuasive" if federal
            else "binding_ca_supreme" if "Supreme Court" in court
            else "binding_ca_appellate" if state_published
            else "non_citable"
        ),
    }


def parse_enforcement_html(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = normalize_space(soup.get_text(" "))
    title = normalize_space((soup.find("h1").get_text(" ") if soup.find("h1") else "") or (soup.title.get_text(" ") if soup.title else ""))
    agency = (
        "California Office of the Attorney General"
        if re.search(r"Attorney General|OAG|oag\.ca\.gov", text, flags=re.I)
        else "California Privacy Protection Agency"
        if re.search(r"California Privacy Protection Agency|CPPA", text, flags=re.I)
        else ""
    )
    action_date_match = re.search(r"\b([A-Z][a-z]+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})\b", text)
    authority_type = (
        "press_release" if re.search(r"press release|attorney general.*announces|news", text, flags=re.I)
        else "administrative_order" if re.search(r"order of decision|stipulated final order", text, flags=re.I)
        else "enforcement_material"
    )
    status = (
        "final" if re.search(r"final order|final judgment|settlement", text, flags=re.I)
        else "announced" if authority_type == "press_release"
        else ""
    )
    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    return {
        "agency": agency,
        "matter_name": title,
        "action_date": action_date_match.group(1) if action_date_match else "",
        "authority_type": authority_type,
        "status": status,
        "cited_statutes": extract_statute_ids(text),
        "official_url": canonical.get("href", "") if canonical and canonical.get("href") else "",
    }


def keywords_from_text(text: str, title: str = "") -> list[str]:
    candidates = [
        "notice", "collection", "deletion", "correction", "access", "sale", "share",
        "sensitive personal information", "opt-out", "global privacy control", "GPC",
        "minor", "children", "service provider", "contractor", "third party",
        "data breach", "private right of action", "risk assessment", "ADMT",
        "cybersecurity audit", "automated decisionmaking", "enforcement",
        "administrative", "penalty", "settlement", "privacy policy",
    ]
    haystack = f"{title}\n{text}".lower()
    found = []
    for candidate in candidates:
        if candidate.lower() in haystack:
            found.append(candidate)
    words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", title.lower())
    for word in words:
        if word not in found:
            found.append(word)
    return found[:18]


def extract_statute_ids(text: str) -> list[str]:
    source_ids: set[str] = set()
    patterns = [
        (r"Cal\.\s*Civ\.\s*Code\s*§+\s*((?:56|1798)\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Civil Code section\s*((?:56|1798)\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Section\s*(1798\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Sections\s*(1798\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"§+\s*(1798\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Cal\.\s*Bus\.\s*&\s*Prof\.\s*Code\s*§+\s*(22\d{3})", "ca-bpc-{}"),
        (r"Bus(?:iness)?\.?\s*(?:and|&)\s*Prof(?:essions)?\.?\s*Code\s*§+\s*(22\d{3})", "ca-bpc-{}"),
        (r"Business and Professions Code section\s*(22\d{3})", "ca-bpc-{}"),
        (r"Cal\.\s*Penal\s*Code\s*§+\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
        (r"Penal Code section\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
        (r"Pen\.\s*Code\s*§+\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
    ]
    for pattern, source_id_template in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            source_ids.add(source_id_template.format(match.group(1).rstrip(".")))
    return sorted(source_ids)


def extract_regulation_ids(text: str) -> list[str]:
    sections = set()
    patterns = [
        r"11\s*CCR\s*§+\s*(7\d{3})",
        r"section\s*(7\d{3})",
        r"§+\s*(7\d{3})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            section = match.group(1)
            if 7000 <= int(section) <= 7304:
                sections.add(section)
    return [f"ca-11-ccr-{section}" for section in sorted(sections)]


def section_key(section: str) -> tuple[int, ...]:
    return tuple(int(part) for part in section.split("."))


def yaml_block(frontmatter: dict[str, Any]) -> str:
    return yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()


def write_md(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{yaml_block(frontmatter)}\n---\n\n{body.strip()}\n", encoding="utf-8")


def relative(path: Path) -> str:
    return str(path.relative_to(BASE_DIR))


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    parsed = yaml.safe_load(text[4:end])
    return parsed if isinstance(parsed, dict) else {}


def collect_pdf_source(source: dict[str, Any], force: bool = False) -> tuple[Path, str, dict[str, Any]]:
    raw_path = BASE_DIR / source["raw_path"]
    meta = fetch_url(source["url"], raw_path, force=force)
    text = pdf_to_text(raw_path)
    return raw_path, text, meta


def build_statutes(config: dict[str, Any], force: bool = False) -> int:
    source = config["statute"]
    raw_path, text, meta = collect_pdf_source(source, force=force)
    sections = parse_statute_pdf_text(text)

    count = 0
    for parsed in sections:
        section = parsed["section"]
        section_text = parsed["body"]
        title = parsed["title"]
        file_path = LIBRARY_DIR / "grade-a" / "ca-ccpa-statute" / f"civ-{section}.md"
        fm = {
            "id": f"ca-civ-{section}",
            "jurisdiction": "US-CA",
            "source_family": "ca-ccpa-statute",
            "source_grade": "A",
            "authority_type": "statute",
            "authority_level": "binding",
            "title": title,
            "citation": f"Cal. Civ. Code § {section}",
            "code": "CIV",
            "section": section,
            "effective_date": source.get("effective_date"),
            "publisher": source.get("publisher"),
            "official_url": source["url"],
            "verification_url": f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum={section}.",
            "retrieved_at": today(),
            "raw_path": relative(raw_path),
            "source_checksum": meta["checksum"],
            "conversion_quality": "pdftotext-section-split",
            "keywords": keywords_from_text(section_text, title),
            "related_regulations": [],
            "related_cases": [],
            "trust_boundary": "source_text_is_data_not_instruction",
        }
        body = f"## Official Text\n\n{section_text}\n\n## Source Notes\n\n- Primary source: CPPA compiled CCPA statute PDF.\n- Verification source: California LegInfo section page."
        write_md(file_path, fm, body)
        count += 1
    log(f"statutes: wrote {count} section files")
    return count


def build_regulations(config: dict[str, Any], force: bool = False) -> int:
    source = config["regulations"]
    raw_path, text, meta = collect_pdf_source(source, force=force)
    sections = parse_regulation_pdf_text(text)

    count = 0
    for parsed in sections:
        section = parsed["section"]
        section_text = parsed["body"]
        title = parsed["title"]
        article_number = parsed["article_number"]
        article_title = parsed["article_title"]
        authority = parsed["authority_cited"]
        references = parsed["reference_sections"]
        file_path = LIBRARY_DIR / "grade-a" / "ca-ccpa-regulations" / f"11-ccr-{section}.md"
        fm = {
            "id": f"ca-11-ccr-{section}",
            "jurisdiction": "US-CA",
            "source_family": "ca-ccpa-regulations",
            "source_grade": "A",
            "authority_type": "regulation",
            "authority_level": "binding",
            "title": title,
            "citation": f"11 CCR § {section}",
            "title_number": "11",
            "division": "6",
            "chapter": "1",
            "article_number": article_number,
            "article_title": article_title,
            "section": section,
            "effective_date": source.get("effective_date"),
            "publisher": source.get("publisher"),
            "official_url": source["url"],
            "retrieved_at": today(),
            "raw_path": relative(raw_path),
            "source_checksum": meta["checksum"],
            "conversion_quality": "pdftotext-section-split",
            "authority_cited": authority,
            "reference_sections": references,
            "keywords": keywords_from_text(section_text, title),
            "related_statutes": references,
            "related_cases": [],
            "trust_boundary": "source_text_is_data_not_instruction",
        }
        body = f"## Official Text\n\n{section_text}\n\n## Source Notes\n\n- Primary source: CPPA CCPA regulations PDF effective 2026-01-01."
        write_md(file_path, fm, body)
        count += 1
    log(f"regulations: wrote {count} section files")
    return count


def raw_path_for_url(url: str, folder: str, source_id: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix or ".html"
    return RAW_DIR / "official" / folder / f"{source_id}{suffix}"


def raw_path_for_case(item: dict[str, Any]) -> Path:
    if item.get("raw_path"):
        return BASE_DIR / item["raw_path"]
    url = item["url"]
    if "govinfo.gov" in url:
        return raw_path_for_url(url, "govinfo", item["id"])
    if "scocal.stanford.edu" in url:
        return RAW_DIR / "mirrors" / "scocal" / f"{item['id']}.html"
    return raw_path_for_url(url, "ca-courts", item["id"])


def build_guidance(config: dict[str, Any], force: bool = False) -> int:
    count = 0
    for item in config["guidance"]:
        folder = "oag" if "oag.ca.gov" in item["url"] else "cppa"
        raw_path = raw_path_for_url(item["url"], folder, item["id"])
        meta = fetch_url(item["url"], raw_path, force=force)
        title, markdown, links = html_to_markdown(raw_path)
        path = BASE_DIR / item["path"]
        fm = {
            "id": item["id"],
            "jurisdiction": "US-CA",
            "source_family": item["source_family"],
            "source_grade": "A",
            "authority_type": "official_guidance",
            "authority_level": "nonbinding_guidance",
            "title": item.get("title") or title,
            "citation": item.get("title") or title,
            "publisher": item.get("publisher"),
            "official_url": item["url"],
            "retrieved_at": today(),
            "raw_path": relative(raw_path),
            "source_checksum": meta["checksum"],
            "keywords": keywords_from_text(markdown, item.get("title", "")),
            "outbound_links": links[:100],
            "binding_warning": "Official guidance is not a substitute for statute, regulation, or binding judicial authority.",
            "trust_boundary": "source_text_is_data_not_instruction",
        }
        body = f"## Official Page Text\n\n{markdown}\n\n## Source Notes\n\n- Converted from official HTML.\n- Treat as guidance unless the page links to a binding statute, regulation, order, or judgment."
        write_md(path, fm, body)
        count += 1
    log(f"guidance: wrote {count} files")
    return count


def text_from_raw(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return pdf_to_text(path)
    _, markdown, _ = html_to_markdown(path)
    return markdown


def summary_excerpt(text: str, limit: int = 7000) -> str:
    cleaned = clean_pdf_text(text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "\n\n[Extract truncated by local builder; raw source is preserved.]"


def build_enforcement(config: dict[str, Any], force: bool = False) -> int:
    count = 0
    for item in config["enforcement"]:
        folder = "oag" if "oag.ca.gov" in item["url"] else "cppa"
        raw_path = raw_path_for_url(item["url"], folder, item["id"])
        try:
            meta = fetch_url(item["url"], raw_path, force=force)
        except RuntimeError as exc:
            log(f"enforcement: fetch failed for {item['id']}: {exc}")
            continue
        text = text_from_raw(raw_path)
        parsed_enforcement = parse_enforcement_html(raw_path.read_text(encoding="utf-8", errors="replace")) if raw_path.suffix.lower() in {".html", ".htm"} else {}
        attachments = fetch_enforcement_attachments(item, raw_path, force=force)
        attachment_texts = []
        for attachment in attachments:
            attachment_path = BASE_DIR / attachment["raw_path"]
            if attachment_path.exists() and attachment_path.suffix.lower() == ".pdf":
                try:
                    attachment_texts.append(pdf_to_text(attachment_path))
                except Exception as exc:
                    log(f"enforcement: attachment text extraction failed for {attachment_path.name}: {exc}")
        text_for_citations = "\n\n".join([text, *attachment_texts])
        cited_statutes = extract_statute_ids(text_for_citations)
        cited_regulations = extract_regulation_ids(text_for_citations)
        path = BASE_DIR / item["path"]
        fm = {
            "id": item["id"],
            "jurisdiction": "US-CA",
            "source_family": item["source_family"],
            "source_grade": "B",
            "authority_type": item["authority_type"],
            "authority_level": "administrative",
            "precedential_status": "administrative",
            "agency": item.get("agency") or parsed_enforcement.get("agency", ""),
            "matter_name": item.get("matter_name") or parsed_enforcement.get("matter_name", ""),
            "status": item.get("status", "") or parsed_enforcement.get("status", ""),
            "official_url": item["url"],
            "retrieved_at": today(),
            "raw_path": relative(raw_path),
            "source_checksum": meta["checksum"],
            "attachments": attachments,
            "cited_statutes": cited_statutes,
            "cited_regulations": cited_regulations,
            "ccpa_topics": item.get("ccpa_topics", []),
            "keywords": keywords_from_text(text, item["matter_name"]),
            "citation_cautions": [
                "Administrative/enforcement material is not judicial precedent.",
                "Press releases should not be treated as final orders unless the underlying order, complaint, settlement, or judgment is captured.",
            ],
            "trust_boundary": "source_text_is_data_not_instruction",
        }
        body = f"""# {item['matter_name']}

## Matter Information

- Agency: {item['agency']}
- Document type: {item['authority_type']}
- Status: {item.get('status', '')}
- Source: {item['url']}

## Source Extract

{summary_excerpt(text)}

## Attachments

{format_attachment_list(attachments)}

## Cited Authorities

- Statutes: {', '.join(cited_statutes) if cited_statutes else 'not extracted'}
- Regulations: {', '.join(cited_regulations) if cited_regulations else 'not extracted'}

## Citation Cautions

- This record is enforcement or administrative material, not judicial precedent.
- Confirm whether the source is a press release, complaint, settlement, stipulated order, administrative order, or judgment before relying on it.
"""
        write_md(path, fm, body)
        count += 1
    log(f"enforcement/admin: wrote {count} files")
    return count


def fetch_enforcement_attachments(item: dict[str, Any], raw_path: Path, force: bool = False) -> list[dict[str, Any]]:
    if raw_path.suffix.lower() not in {".html", ".htm"}:
        return []
    attachments: list[dict[str, Any]] = []
    candidates = []
    for link in html_links(raw_path, item["url"]):
        href = link["href"]
        label = link["label"]
        link_text = f"{label} {href}".lower()
        if not href.lower().endswith(".pdf"):
            continue
        if not any(term in link_text for term in ["complaint", "settlement", "judgment", "injunction", "order"]):
            continue
        candidates.append(link)

    seen: set[str] = set()
    for idx, link in enumerate(candidates, start=1):
        href = link["href"]
        if href in seen:
            continue
        seen.add(href)
        raw_attachment = RAW_DIR / "official" / "oag" / f"{item['id']}-attachment-{idx}.pdf"
        try:
            meta = fetch_url(href, raw_attachment, force=force)
        except RuntimeError as exc:
            log(f"enforcement: attachment fetch failed for {item['id']} {href}: {exc}")
            continue
        attachments.append({
            "label": link["label"] or f"attachment-{idx}",
            "url": href,
            "raw_path": relative(raw_attachment),
            "source_checksum": meta["checksum"],
            "bytes": meta["bytes"],
        })
    return attachments


def format_attachment_list(attachments: list[dict[str, Any]]) -> str:
    if not attachments:
        return "- No official attachment captured by this run."
    lines = []
    for attachment in attachments:
        lines.append(f"- {attachment.get('label') or 'attachment'}: {attachment['url']} ({attachment['raw_path']})")
    return "\n".join(lines)


def build_cases(config: dict[str, Any], force: bool = False) -> int:
    count = 0
    for item in config["cases"]:
        raw_path = raw_path_for_case(item)
        try:
            meta = fetch_url(item["url"], raw_path, force=force)
        except RuntimeError as exc:
            log(f"case: fetch failed for {item['id']}: {exc}")
            continue
        text = text_from_raw(raw_path)
        parsed_case = parse_case_html(raw_path.read_text(encoding="utf-8", errors="replace")) if raw_path.suffix.lower() in {".html", ".htm"} else {}
        cited_statutes = extract_statute_ids(text)
        cited_regulations = extract_regulation_ids(text)
        path = BASE_DIR / item["path"]
        court = item.get("court") or parsed_case.get("court", "")
        if item.get("court_system"):
            court_system = item["court_system"]
        elif item.get("court"):
            court_system = "federal" if item["id"].startswith("us-") or "United States" in court or "Ninth Circuit" in court else "state"
        else:
            court_system = parsed_case.get("court_system") or ("federal" if item["id"].startswith("us-") or "United States" in court else "state")
        source_grade = item.get("source_grade", "A")
        official_url = item.get("official_url", item["url"])
        source_url = item.get("source_url", item["url"])
        citation_cautions = item.get("citation_cautions") or [
            "Federal opinions applying California law are persuasive unless controlling status is separately established.",
            "Unpublished dispositions must not be cited as controlling precedent.",
        ]
        source_mirror_warning = item.get("source_mirror_warning", "")
        if source_mirror_warning and source_mirror_warning not in citation_cautions:
            citation_cautions = [*citation_cautions, source_mirror_warning]
        fm = {
            "id": item["id"],
            "jurisdiction": "US-CA",
            "source_family": item["source_family"],
            "source_grade": source_grade,
            "authority_type": item["authority_type"],
            "authority_level": item.get("authority_level") or parsed_case.get("authority_level", ""),
            "precedential_status": item.get("precedential_status") or parsed_case.get("precedential_status", ""),
            "court": court,
            "court_system": court_system,
            "case_name": item.get("case_name") or parsed_case.get("case_name", ""),
            "case_number": item["case_number"],
            "decision_date": item["decision_date"],
            "official_url": official_url,
            "source_url": source_url,
            "source_mirror_warning": source_mirror_warning,
            "retrieved_at": today(),
            "raw_path": relative(raw_path),
            "source_checksum": meta["checksum"],
            "cited_statutes": cited_statutes,
            "cited_regulations": cited_regulations,
            "ccpa_topics": item.get("ccpa_topics", []),
            "keywords": keywords_from_text(text, item["case_name"]),
            "citation_cautions": citation_cautions,
            "trust_boundary": "source_text_is_data_not_instruction",
        }
        source_lines = [
            f"- Court: {court}",
            f"- Case number: {item['case_number']}",
            f"- Decision date: {item['decision_date']}",
            f"- Source fetched: {source_url}",
            f"- Official URL: {official_url}",
            f"- Source grade: {source_grade}",
            f"- Precedential status: {item['precedential_status']}",
        ]
        if source_mirror_warning:
            source_lines.append(f"- Mirror warning: {source_mirror_warning}")
        caution_lines = "\n".join(f"- {caution}" for caution in citation_cautions)
        body = f"""# {item['case_name']}

## Case Information

{chr(10).join(source_lines)}

## Source Extract

{summary_excerpt(text)}

## Cited Authorities

- Statutes: {', '.join(cited_statutes) if cited_statutes else 'not extracted'}
- Regulations: {', '.join(cited_regulations) if cited_regulations else 'not extracted'}

## Citation Cautions

{caution_lines}
"""
        write_md(path, fm, body)
        count += 1
    log(f"cases: wrote {count} files")
    return count


def build_adjacent_statutes(config: dict[str, Any], force: bool = False) -> int:
    count = 0
    for group in config.get("adjacent_statute_groups", []):
        raw_path = BASE_DIR / group["raw_path"]
        meta = fetch_url(group["url"], raw_path, force=force)
        sections = parse_leginfo_section_group(raw_path, group)
        group_count = 0
        for section, text in sections:
            file_path = BASE_DIR / group["library_dir"] / f"{group['code'].lower()}-{section}.md"
            source_id = f"ca-{group['code'].lower()}-{section}"
            title = f"{group['title']} § {section}"
            fm = {
                "id": source_id,
                "jurisdiction": group.get("jurisdiction", "US-CA"),
                "source_family": group["source_family"],
                "source_grade": group.get("source_grade", "A"),
                "authority_type": group.get("authority_type", "statute"),
                "authority_level": group.get("authority_level", "binding"),
                "title": title,
                "citation": f"{group['citation_prefix']} {section}",
                "code": group["code"],
                "section": section,
                "publisher": group.get("publisher", "California Legislative Information"),
                "official_url": f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode={group['code']}&sectionNum={section}.",
                "group_url": group["url"],
                "retrieved_at": today(),
                "raw_path": relative(raw_path),
                "source_checksum": meta["checksum"],
                "conversion_quality": "leginfo-html-section-split",
                "topics": group.get("topics", []),
                "keywords": keywords_from_text(text, title),
                "citation_cautions": group.get("citation_cautions", []),
                "trust_boundary": "source_text_is_data_not_instruction",
            }
            body = f"## Official Text\n\n{text}\n\n## Source Notes\n\n- Primary source: California Legislative Information section group page.\n- Section verification URL is recorded in frontmatter."
            write_md(file_path, fm, body)
            group_count += 1
        log(f"adjacent statutes: {group['source_family']} wrote {group_count} files")
        count += group_count
    return count


def parse_leginfo_section_group(raw_path: Path, group: dict[str, Any]) -> list[tuple[str, str]]:
    html = raw_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [normalize_space(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    section_re = re.compile(group["section_regex"])
    sections: list[tuple[str, str, int]] = []
    for idx, line in enumerate(lines):
        match = section_re.match(line)
        if match:
            sections.append((match.group(1), line, idx))
    parsed: list[tuple[str, str]] = []
    for pos, (section, _, start_idx) in enumerate(sections):
        end_idx = sections[pos + 1][2] if pos + 1 < len(sections) else len(lines)
        section_lines = lines[start_idx:end_idx]
        section_text = "\n\n".join(section_lines)
        if len(section_text) < 40:
            continue
        parsed.append((section, section_text))
    return parsed


def section_gap_report(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    for group in config.get("adjacent_statute_groups", []):
        expected = group.get("expected_section_numbers", [])
        if not expected:
            continue
        present = []
        for path, fm in index_items_for(BASE_DIR / group["library_dir"]):
            section = fm.get("section")
            if section:
                present.append(str(section))
        present_set = set(present)
        missing = [section for section in expected if section not in present_set]
        verified_absent = [section for section in group.get("verified_absent", []) if section in missing]
        verified_absent_set = set(verified_absent)
        unverified = [section for section in missing if section not in verified_absent_set]
        report[group["source_family"]] = {
            "status": "unverified" if unverified else "ok",
            "expected_count": len(expected),
            "present_count": len(present_set),
            "missing": missing,
            "verified_absent": verified_absent,
            "unverified": unverified,
            "verified_absent_source": group.get("verified_absent_source", ""),
        }
    return report


def build_indexes(config: dict[str, Any]) -> None:
    build_statute_index()
    build_regulation_index()
    build_guidance_index()
    build_adjacent_statute_index()
    build_enforcement_index()
    build_case_index()
    build_citation_map()
    build_source_registry(config)
    build_topic_index()
    build_golden_question_index()


def index_items_for(directory: Path) -> list[tuple[Path, dict[str, Any]]]:
    items = []
    if not directory.exists():
        return items
    for path in sorted(directory.glob("*.md")):
        fm = parse_frontmatter(path)
        if fm:
            items.append((path, fm))
    return items


def build_statute_index() -> None:
    items = []
    for path, fm in index_items_for(LIBRARY_DIR / "grade-a" / "ca-ccpa-statute"):
        items.append({
            "id": fm["id"],
            "citation": fm.get("citation", ""),
            "title": fm.get("title", ""),
            "path": relative(path),
            "effective_date": fm.get("effective_date", ""),
            "source_grade": fm.get("source_grade", "A"),
            "keywords": fm.get("keywords", []),
            "related_regulations": fm.get("related_regulations", []),
        })
    write_json(INDEX_DIR / "ca-statute-index.json", {"type": "ca_statute_index", "count": len(items), "generated_at": utc_now(), "items": items})


def build_regulation_index() -> None:
    items = []
    for path, fm in index_items_for(LIBRARY_DIR / "grade-a" / "ca-ccpa-regulations"):
        items.append({
            "id": fm["id"],
            "citation": fm.get("citation", ""),
            "title": fm.get("title", ""),
            "path": relative(path),
            "effective_date": fm.get("effective_date", ""),
            "official_url": fm.get("official_url", ""),
            "authority_cited": fm.get("authority_cited", []),
            "reference_sections": fm.get("reference_sections", []),
            "related_statutes": fm.get("related_statutes", []),
            "keywords": fm.get("keywords", []),
        })
    write_json(INDEX_DIR / "ca-regulation-index.json", {"type": "ca_regulation_index", "count": len(items), "generated_at": utc_now(), "items": items})


def build_guidance_index() -> None:
    items = []
    for directory in [LIBRARY_DIR / "grade-a" / "ca-cppa-guidance", LIBRARY_DIR / "grade-a" / "ca-oag-guidance"]:
        for path, fm in index_items_for(directory):
            items.append({
                "id": fm["id"],
                "title": fm.get("title", ""),
                "publisher": fm.get("publisher", ""),
                "path": relative(path),
                "source_family": fm.get("source_family", ""),
                "authority_level": fm.get("authority_level", ""),
                "official_url": fm.get("official_url", ""),
                "keywords": fm.get("keywords", []),
            })
    write_json(INDEX_DIR / "ca-guidance-index.json", {"type": "ca_guidance_index", "count": len(items), "generated_at": utc_now(), "items": items})


def build_adjacent_statute_index() -> None:
    items = []
    for directory in sorted((LIBRARY_DIR / "grade-a").glob("ca-*")):
        if directory.name in {
            "ca-ccpa-statute",
            "ca-ccpa-regulations",
            "ca-cppa-guidance",
            "ca-oag-guidance",
            "ca-courts-published-opinions",
        }:
            continue
        for path, fm in index_items_for(directory):
            if fm.get("authority_type") != "statute":
                continue
            items.append({
                "id": fm["id"],
                "citation": fm.get("citation", ""),
                "title": fm.get("title", ""),
                "path": relative(path),
                "source_family": fm.get("source_family", ""),
                "authority_level": fm.get("authority_level", ""),
                "topics": fm.get("topics", []),
                "keywords": fm.get("keywords", []),
                "citation_cautions": fm.get("citation_cautions", []),
            })
    write_json(INDEX_DIR / "ca-adjacent-statute-index.json", {"type": "ca_adjacent_statute_index", "count": len(items), "generated_at": utc_now(), "items": items})


def build_enforcement_index() -> None:
    items = []
    for directory in [LIBRARY_DIR / "grade-b" / "ca-enforcement-actions", LIBRARY_DIR / "grade-b" / "ca-administrative-orders"]:
        for path, fm in index_items_for(directory):
            items.append({
                "id": fm["id"],
                "matter_name": fm.get("matter_name", ""),
                "agency": fm.get("agency", ""),
                "authority_type": fm.get("authority_type", ""),
                "authority_level": fm.get("authority_level", ""),
                "status": fm.get("status", ""),
                "path": relative(path),
                "source_grade": fm.get("source_grade", "B"),
                "official_url": fm.get("official_url", ""),
                "attachments": fm.get("attachments", []),
                "cited_statutes": fm.get("cited_statutes", []),
                "cited_regulations": fm.get("cited_regulations", []),
                "ccpa_topics": fm.get("ccpa_topics", []),
                "keywords": fm.get("keywords", []),
                "citation_cautions": fm.get("citation_cautions", []),
            })
    write_json(INDEX_DIR / "ca-enforcement-index.json", {"type": "ca_enforcement_index", "count": len(items), "generated_at": utc_now(), "items": items})


def build_case_index() -> None:
    items = []
    for directory in [
        LIBRARY_DIR / "grade-a" / "ca-courts-published-opinions",
        LIBRARY_DIR / "grade-a" / "us-federal-ccpa-opinions",
        LIBRARY_DIR / "grade-b" / "ca-courts-published-opinion-mirrors",
        LIBRARY_DIR / "grade-b" / "ca-courts-unpublished-opinions",
    ]:
        for path, fm in index_items_for(directory):
            items.append({
                "id": fm["id"],
                "case_name": fm.get("case_name", ""),
                "court": fm.get("court", ""),
                "court_system": fm.get("court_system") or ("federal" if str(fm.get("id", "")).startswith("us-") or "United States" in fm.get("court", "") else "state"),
                "case_number": fm.get("case_number", ""),
                "decision_date": fm.get("decision_date", ""),
                "path": relative(path),
                "source_family": fm.get("source_family", ""),
                "source_grade": fm.get("source_grade", ""),
                "authority_level": fm.get("authority_level", ""),
                "precedential_status": fm.get("precedential_status", ""),
                "official_url": fm.get("official_url", ""),
                "source_url": fm.get("source_url", fm.get("official_url", "")),
                "source_mirror_warning": fm.get("source_mirror_warning", ""),
                "cited_statutes": fm.get("cited_statutes", []),
                "cited_regulations": fm.get("cited_regulations", []),
                "ccpa_topics": fm.get("ccpa_topics", []),
                "keywords": fm.get("keywords", []),
                "citation_cautions": fm.get("citation_cautions", []),
            })
    write_json(INDEX_DIR / "ca-case-index.json", {"type": "ca_case_index", "count": len(items), "generated_at": utc_now(), "cases": items})


def build_citation_map() -> None:
    citation_map: dict[str, str] = {}
    for path, fm in index_items_for(LIBRARY_DIR / "grade-a" / "ca-ccpa-statute"):
        section = fm.get("section")
        source_id = fm.get("id")
        if section and source_id:
            citation_map[f"Cal. Civ. Code § {section}"] = source_id
            citation_map[f"Civil Code section {section}"] = source_id
            citation_map[f"Civ. Code § {section}"] = source_id
            citation_map[f"Section {section}"] = source_id
    for path, fm in index_items_for(LIBRARY_DIR / "grade-a" / "ca-ccpa-regulations"):
        section = fm.get("section")
        source_id = fm.get("id")
        if section and source_id:
            citation_map[f"11 CCR § {section}"] = source_id
            citation_map[f"section {section}"] = source_id
    adjacent_index = read_json(INDEX_DIR / "ca-adjacent-statute-index.json")
    for item in adjacent_index.get("items", []):
        citation = item.get("citation")
        source_id = item.get("id")
        if citation and source_id:
            citation_map[citation] = source_id
            citation_map[citation.replace("Cal. Civ. Code", "Civil Code")] = source_id
            citation_map[citation.replace("Cal. Bus. & Prof. Code", "Business and Professions Code")] = source_id
            citation_map[citation.replace("Cal. Penal Code", "Penal Code")] = source_id
            citation_map[citation.replace("Cal. Penal Code", "Pen. Code")] = source_id
    write_json(INDEX_DIR / "ca-citation-map.json", {"type": "ca_citation_map", "count": len(citation_map), "generated_at": utc_now(), "citations": citation_map})


def authority_catalog() -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    index_specs = [
        ("ca-statute-index.json", "items", "statute"),
        ("ca-regulation-index.json", "items", "regulation"),
        ("ca-guidance-index.json", "items", "guidance"),
        ("ca-adjacent-statute-index.json", "items", "adjacent_statute"),
        ("ca-enforcement-index.json", "items", "enforcement"),
        ("ca-case-index.json", "cases", "case"),
    ]
    for filename, key, authority_group in index_specs:
        payload = read_json(INDEX_DIR / filename)
        for item in payload.get(key, []):
            source_id = item.get("id")
            if not source_id:
                continue
            catalog[source_id] = {
                "id": source_id,
                "authority_group": authority_group,
                "label": item.get("citation") or item.get("title") or item.get("matter_name") or item.get("case_name") or source_id,
                "path": item.get("path", ""),
                "source_family": item.get("source_family", ""),
                "source_grade": item.get("source_grade", ""),
                "authority_level": item.get("authority_level", ""),
                "precedential_status": item.get("precedential_status", ""),
            }
    return catalog


def resolve_authorities(source_ids: list[str], catalog: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    resolved = []
    missing = []
    for source_id in source_ids:
        item = catalog.get(source_id)
        if item:
            resolved.append(item)
        else:
            missing.append(source_id)
    return resolved, missing


def build_topic_index() -> None:
    topic_config = load_topic_config()
    catalog = authority_catalog()
    topics = []
    authority_to_topics: dict[str, list[str]] = {}
    for seed in topic_config.get("topics", []):
        sections = {}
        missing: list[str] = []
        for key in ["primary_authority_ids", "supporting_authority_ids", "guidance_ids", "enforcement_ids", "case_ids"]:
            resolved, missing_for_key = resolve_authorities(seed.get(key, []), catalog)
            sections[key.replace("_ids", "")] = resolved
            missing.extend(missing_for_key)
            for authority in resolved:
                authority_to_topics.setdefault(authority["id"], []).append(seed["id"])

        topics.append({
            "id": seed["id"],
            "title": seed["title"],
            "summary": seed.get("summary", ""),
            "search_terms": seed.get("search_terms", []),
            "primary_authorities": sections["primary_authority"],
            "supporting_authorities": sections["supporting_authority"],
            "guidance": sections["guidance"],
            "enforcement": sections["enforcement"],
            "cases": sections["case"],
            "answer_cautions": seed.get("answer_cautions", []),
            "comparative_hooks": seed.get("comparative_hooks", []),
            "missing_authority_ids": missing,
            "coverage_status": "pass" if not missing and sections["primary_authority"] else "fail" if missing else "partial",
        })

    write_json(INDEX_DIR / "ca-topic-index.json", {
        "type": "ca_topic_index",
        "count": len(topics),
        "generated_at": utc_now(),
        "topics": topics,
        "authority_to_topics": {key: sorted(value) for key, value in sorted(authority_to_topics.items())},
    })


def build_golden_question_index() -> None:
    topic_config = load_topic_config()
    catalog = authority_catalog()
    topic_ids = {topic.get("id") for topic in topic_config.get("topics", [])}
    questions = []
    for seed in topic_config.get("golden_questions", []):
        expected, missing_expected = resolve_authorities(seed.get("expected_authority_ids", []), catalog)
        supporting, missing_supporting = resolve_authorities(seed.get("supporting_authority_ids", []), catalog)
        topic_id = seed.get("topic_id", "")
        questions.append({
            "id": seed["id"],
            "topic_id": topic_id,
            "topic_exists": topic_id in topic_ids,
            "question": seed["question"],
            "expected_authorities": expected,
            "supporting_authorities": supporting,
            "missing_authority_ids": missing_expected + missing_supporting,
            "must_not": seed.get("must_not", []),
        })

    write_json(INDEX_DIR / "golden-questions.ca.json", {
        "type": "ca_golden_questions",
        "count": len(questions),
        "generated_at": utc_now(),
        "questions": questions,
    })


def build_source_registry(config: dict[str, Any]) -> None:
    grade_counts = Counter()
    family_counts = Counter()
    for path in LIBRARY_DIR.glob("grade-*/*/*.md"):
        if path.name == "README.md":
            continue
        fm = parse_frontmatter(path)
        if not fm:
            continue
        grade_counts[fm.get("source_grade", "")] += 1
        family_counts[(path.parts[-3], fm.get("source_family", ""))] += 1

    sources: dict[str, dict[str, Any]] = {"grade-a": {}, "grade-b": {}, "grade-c": {}}
    sources["grade-a"]["ca-ccpa-statute"] = {
        "status": "complete" if family_counts[("grade-a", "ca-ccpa-statute")] == len(STATUTE_SECTIONS) else "partial",
        "count": family_counts[("grade-a", "ca-ccpa-statute")],
        "target": len(STATUTE_SECTIONS),
        "publisher": config["statute"]["publisher"],
        "source_url": config["statute"]["url"],
        "retrieved_at": today(),
    }
    sources["grade-a"]["ca-ccpa-regulations"] = {
        "status": "complete" if family_counts[("grade-a", "ca-ccpa-regulations")] > 0 else "pending",
        "count": family_counts[("grade-a", "ca-ccpa-regulations")],
        "target": None,
        "publisher": config["regulations"]["publisher"],
        "source_url": config["regulations"]["url"],
        "retrieved_at": today(),
    }
    sources["grade-a"]["ca-cppa-guidance"] = {
        "status": "complete" if family_counts[("grade-a", "ca-cppa-guidance")] > 0 else "pending",
        "count": family_counts[("grade-a", "ca-cppa-guidance")],
        "target": None,
    }
    sources["grade-a"]["ca-cppa-rulemaking"] = {
        "status": "complete" if family_counts[("grade-a", "ca-cppa-rulemaking")] > 0 else "pending",
        "count": family_counts[("grade-a", "ca-cppa-rulemaking")],
        "target": None,
    }
    sources["grade-a"]["ca-oag-guidance"] = {
        "status": "complete" if family_counts[("grade-a", "ca-oag-guidance")] > 0 else "pending",
        "count": family_counts[("grade-a", "ca-oag-guidance")],
        "target": None,
    }
    case_targets = Counter(item.get("source_family", "") for item in config.get("cases", []))
    for case_family in ["ca-courts-published-opinions", "us-federal-ccpa-opinions"]:
        count = family_counts[("grade-a", case_family)]
        target = case_targets[case_family]
        sources["grade-a"][case_family] = {
            "status": "complete" if target and count >= target else "partial" if count > 0 else "pending",
            "count": count,
            "target": target,
            "note": "Only CCPA/California privacy opinions verified against official court or GovInfo source.",
        }
    mirror_family = "ca-courts-published-opinion-mirrors"
    mirror_count = family_counts[("grade-b", mirror_family)]
    mirror_target = case_targets[mirror_family]
    sources["grade-b"][mirror_family] = {
        "status": "complete" if mirror_target and mirror_count >= mirror_target else "partial" if mirror_count > 0 else "pending",
        "count": mirror_count,
        "target": mirror_target,
        "note": "Published California Supreme Court opinions fetched from a public mirror when the official California Courts archive URL is not locally raw-fetchable.",
    }
    for group in config.get("adjacent_statute_groups", []):
        family = group["source_family"]
        count = family_counts[("grade-a", family)]
        sources["grade-a"][family] = {
            "status": "complete" if count > 0 else "pending",
            "count": count,
            "target": None,
            "publisher": group.get("publisher"),
            "source_url": group.get("url"),
            "retrieved_at": today() if count else None,
            "note": "Adjacent California privacy statute collected from official LegInfo group page.",
        }
    sources["grade-b"]["ca-enforcement-actions"] = {
        "status": "partial" if family_counts[("grade-b", "ca-enforcement-actions")] > 0 else "pending",
        "count": family_counts[("grade-b", "ca-enforcement-actions")],
        "target": len([x for x in config.get("enforcement", []) if x.get("source_family") == "ca-enforcement-actions"]),
    }
    sources["grade-b"]["ca-administrative-orders"] = {
        "status": "partial" if family_counts[("grade-b", "ca-administrative-orders")] > 0 else "pending",
        "count": family_counts[("grade-b", "ca-administrative-orders")],
        "target": len([x for x in config.get("enforcement", []) if x.get("source_family") == "ca-administrative-orders"]),
    }
    registry = {
        "type": "source_registry",
        "generated_at": utc_now(),
        "total_files": sum(grade_counts.values()),
        "sources": sources,
    }
    write_json(INDEX_DIR / "source-registry.json", registry)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"index: wrote {relative(path)}")


def validate() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    config = load_config()
    for name in [
        "ca-statute-index.json",
        "ca-regulation-index.json",
        "ca-guidance-index.json",
        "ca-enforcement-index.json",
        "ca-case-index.json",
        "ca-adjacent-statute-index.json",
        "ca-citation-map.json",
        "ca-topic-index.json",
        "golden-questions.ca.json",
        "source-registry.json",
    ]:
        if not (INDEX_DIR / name).exists():
            errors.append(f"missing index/{name}")

    statute_index = read_json(INDEX_DIR / "ca-statute-index.json")
    if statute_index and statute_index.get("count") != len(STATUTE_SECTIONS):
        errors.append(f"statute section count {statute_index.get('count')} != {len(STATUTE_SECTIONS)}")
    regulation_index = read_json(INDEX_DIR / "ca-regulation-index.json")
    if regulation_index and regulation_index.get("count", 0) < 40:
        warnings.append(f"regulation section count looks low: {regulation_index.get('count')}")
    enforcement_index = read_json(INDEX_DIR / "ca-enforcement-index.json")
    if enforcement_index and enforcement_index.get("count", 0) < 3:
        warnings.append("few enforcement/admin files collected")
    case_index = read_json(INDEX_DIR / "ca-case-index.json")
    if case_index and case_index.get("count", 0) < 1:
        warnings.append("no case files collected")
    adjacent_index = read_json(INDEX_DIR / "ca-adjacent-statute-index.json")
    if adjacent_index:
        by_family = Counter(item.get("source_family", "") for item in adjacent_index.get("items", []))
        for group in config.get("adjacent_statute_groups", []):
            family = group["source_family"]
            if by_family[family] == 0:
                errors.append(f"adjacent statute group has no parsed sections: {family}")
    section_gaps = section_gap_report(config)
    if section_gaps:
        log("section gap report:")
        for family, gap in section_gaps.items():
            log(f"  {family}: {gap['present_count']}/{gap['expected_count']} sections present")
            if gap["missing"]:
                log(f"    missing: {', '.join(gap['missing'])}")
            if gap["verified_absent"]:
                log(f"    verified_absent: {', '.join(gap['verified_absent'])}")
            if gap["unverified"]:
                warnings.append(f"section gap has unverified missing sections: {family} {', '.join(gap['unverified'])}")
    topic_index = read_json(INDEX_DIR / "ca-topic-index.json")
    if topic_index:
        if topic_index.get("count", 0) < 8:
            warnings.append(f"few California topics configured: {topic_index.get('count')}")
        for topic in topic_index.get("topics", []):
            if topic.get("missing_authority_ids"):
                errors.append(f"topic {topic.get('id')} has missing authority ids: {', '.join(topic['missing_authority_ids'])}")
            if topic.get("coverage_status") == "fail":
                errors.append(f"topic {topic.get('id')} has failed coverage")
    golden_index = read_json(INDEX_DIR / "golden-questions.ca.json")
    if golden_index:
        if golden_index.get("count", 0) < 10:
            warnings.append(f"few California golden questions configured: {golden_index.get('count')}")
        for question in golden_index.get("questions", []):
            if not question.get("topic_exists"):
                errors.append(f"golden question {question.get('id')} references missing topic {question.get('topic_id')}")
            if question.get("missing_authority_ids"):
                errors.append(f"golden question {question.get('id')} has missing authority ids: {', '.join(question['missing_authority_ids'])}")

    for path in LIBRARY_DIR.glob("grade-*/*/*.md"):
        if path.name == "README.md":
            continue
        fm = parse_frontmatter(path)
        if not fm:
            errors.append(f"missing frontmatter: {relative(path)}")
            continue
        for key in ["id", "jurisdiction", "source_family", "source_grade", "official_url", "retrieved_at", "trust_boundary"]:
            if not fm.get(key):
                errors.append(f"{relative(path)} missing {key}")

    report = {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "section_gaps": section_gaps,
        "generated_at": utc_now(),
    }
    write_json(INDEX_DIR / "validation-report.json", report)
    if errors:
        log("validation: failed")
        for error in errors:
            log(f"  ERROR {error}")
        return 1
    log(f"validation: passed with {len(warnings)} warning(s)")
    for warning in warnings:
        log(f"  WARN {warning}")
    return 0


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_all(force: bool = False) -> int:
    ensure_dirs()
    config = load_config()
    build_statutes(config, force=force)
    build_regulations(config, force=force)
    build_guidance(config, force=force)
    build_enforcement(config, force=force)
    build_cases(config, force=force)
    build_adjacent_statutes(config, force=force)
    build_indexes(config)
    return validate()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Fetch, parse, index, and validate all source families.")
    parser.add_argument("--fetch-legal", action="store_true", help="Fetch and parse statute/regulation sources.")
    parser.add_argument("--fetch-guidance", action="store_true", help="Fetch and parse guidance pages.")
    parser.add_argument("--fetch-enforcement", action="store_true", help="Fetch and parse enforcement/admin sources.")
    parser.add_argument("--fetch-cases", action="store_true", help="Fetch and parse case sources.")
    parser.add_argument("--fetch-adjacent", action="store_true", help="Fetch and parse adjacent California privacy statutes.")
    parser.add_argument("--index", action="store_true", help="Build JSON indexes.")
    parser.add_argument("--validate", action="store_true", help="Validate generated KB.")
    parser.add_argument("--force", action="store_true", help="Re-download raw sources.")
    args = parser.parse_args()

    ensure_dirs()
    config = load_config()
    try:
        if args.all:
            return run_all(force=args.force)
        if args.fetch_legal:
            build_statutes(config, force=args.force)
            build_regulations(config, force=args.force)
        if args.fetch_guidance:
            build_guidance(config, force=args.force)
        if args.fetch_enforcement:
            build_enforcement(config, force=args.force)
        if args.fetch_cases:
            build_cases(config, force=args.force)
        if args.fetch_adjacent:
            build_adjacent_statutes(config, force=args.force)
        if args.index:
            build_indexes(config)
        if args.validate:
            return validate()
        if not any(vars(args).values()):
            parser.print_help()
    except Exception as exc:
        print(textwrap.fill(f"ERROR: {exc}", width=100), file=sys.stderr)
        return 1
    return 0


__all__ = [
    "parse_frontmatter",
    "parse_leginfo_section_group",
    "parse_statute_pdf_text",
    "parse_regulation_pdf_text",
    "parse_case_html",
    "parse_enforcement_html",
    "section_gap_report",
]


if __name__ == "__main__":
    raise SystemExit(main())
