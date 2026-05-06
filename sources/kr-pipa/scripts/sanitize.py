"""KR PIPA sub-KB sanitizer for prompt-injection patterns in untrusted text.

Per AGENTS.md Rule 3: untrusted text from kb/kr-pipa/library/, MCP outputs,
or external fetches must be sanitized before entering an LLM context window.

Patterns are identical to the CA sub-KB sanitizer (see
sources/us-ca/scripts/sanitize.py). Each sub-KB owns its own copy so
KR-specific patterns (e.g., Korean role-marker variants) can diverge later
without coupling to other sub-KBs.

Usage:
    from scripts.sanitize import sanitize
    result = sanitize(untrusted_text)
    if result.aborted:
        raise RuntimeError("[SANITIZER UNAVAILABLE]")
    safe_text = result.text     # role markers neutralized
    matches = result.matches    # what was found and where
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Literal

Severity = Literal["role-marker", "jailbreak", "forged-firewall", "role-tag"]


@dataclass(frozen=True)
class Match:
    pattern_id: str
    severity: Severity
    start: int
    end: int
    snippet: str


@dataclass
class SanitizeResult:
    text: str
    matches: list[Match] = field(default_factory=list)
    aborted: bool = False
    aborted_reason: str = ""


def _load_patterns() -> tuple[tuple[tuple[str, str, str], ...], bool]:
    """Returns (PATTERNS, aborted). aborted=True if patterns module is missing."""
    for module_path in (
        "sources.kr_pipa.scripts.lib.patterns",
        "scripts.lib.patterns",
    ):
        try:
            module = importlib.import_module(module_path)
        except Exception:
            continue
        return getattr(module, "PATTERNS", ()), False
    return (), True


def _truncate_snippet(text: str, limit: int = 80) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _neutralize(text: str, start: int, end: int) -> str:
    return text[:start] + f"[REDACTED-{end - start}-chars]" + text[end:]


def sanitize(text: str) -> SanitizeResult:
    patterns, aborted = _load_patterns()
    if aborted:
        return SanitizeResult(
            text=text,
            aborted=True,
            aborted_reason="patterns module not importable",
        )

    spans: list[tuple[int, int, str, Severity, str]] = []
    for pattern_id, severity, regex_str in patterns:
        for m in re.finditer(regex_str, text, flags=re.IGNORECASE | re.MULTILINE):
            spans.append((m.start(), m.end(), pattern_id, severity, m.group(0)))

    spans.sort(key=lambda x: x[0], reverse=True)
    sanitized = text
    matches: list[Match] = []
    for start, end, pid, sev, snip in spans:
        sanitized = _neutralize(sanitized, start, end)
        matches.append(Match(
            pattern_id=pid,
            severity=sev,
            start=start,
            end=end,
            snippet=_truncate_snippet(snip),
        ))

    matches.sort(key=lambda m: m.start)
    return SanitizeResult(text=sanitized, matches=matches)


def sanitize_to_json(text: str) -> str:
    result = sanitize(text)
    return json.dumps({
        "text": result.text,
        "matches": [asdict(m) for m in result.matches],
        "aborted": result.aborted,
        "aborted_reason": result.aborted_reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2)


def main() -> int:
    sub_kb_root = Path(__file__).resolve().parent.parent
    if str(sub_kb_root) not in sys.path:
        sys.path.insert(0, str(sub_kb_root))
    text = sys.stdin.read()
    print(sanitize_to_json(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
