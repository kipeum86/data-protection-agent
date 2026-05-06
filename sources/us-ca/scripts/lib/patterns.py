"""Prompt-injection patterns for CA sub-KB sanitizer.

Each PATTERN entry: (pattern_id, severity, regex_str).
severity in {"role-marker", "jailbreak", "forged-firewall", "role-tag"}.
Regexes are compiled in sanitize.py with re.IGNORECASE | re.MULTILINE.
"""

from __future__ import annotations

PATTERNS: tuple[tuple[str, str, str], ...] = (
    # Role markers
    ("openai-system", "role-marker", r"<\|im_start\|>\s*system"),
    ("openai-assistant", "role-marker", r"<\|im_start\|>\s*assistant"),
    ("anthropic-human", "role-marker", r"^Human:\s"),
    ("anthropic-assistant", "role-marker", r"^Assistant:\s"),
    ("system-tag", "role-tag", r"\[system\]|\[/system\]"),
    ("assistant-tag", "role-tag", r"\[assistant\]|\[/assistant\]"),

    # Jailbreak phrases
    ("ignore-previous", "jailbreak", r"ignore (?:all |the )?previous instructions?"),
    ("disregard-above", "jailbreak", r"disregard (?:all |the )?(?:above|prior)"),
    ("you-are-now", "jailbreak", r"you are now (?:a |an )?(?:different|new)"),
    ("forget-instructions", "jailbreak", r"forget (?:all |your )?(?:previous |prior )?(?:instructions?|rules?|context)"),

    # Forged firewall / agent control
    ("forged-tool-use", "forged-firewall", r"<tool_use\b[^>]*>"),
    ("forged-stop-sequence", "forged-firewall", r"<\|endoftext\|>|<\|stop\|>"),
    ("system-reminder-spoof", "forged-firewall", r"<system-reminder>"),
)
