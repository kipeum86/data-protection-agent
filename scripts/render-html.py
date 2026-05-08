#!/usr/bin/env python3
"""Render a deliverable Markdown file to HTML.

The renderer reads the source Markdown, uses `marko` (already in
project dependencies) to convert to HTML, and wraps the result in a
minimal styled HTML document. Output is intended for client-facing
distribution via email or browser, not for further conversion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       max-width: 760px; margin: 2em auto; padding: 0 1em;
       color: #1a1a1a; line-height: 1.55; }}
h1, h2, h3 {{ color: #0f172a; }}
h1 {{ border-bottom: 2px solid #0f172a; padding-bottom: 0.2em; }}
h2 {{ border-bottom: 1px solid #94a3b8; padding-bottom: 0.15em;
      margin-top: 1.4em; }}
table {{ border-collapse: collapse; margin: 1em 0; }}
th, td {{ border: 1px solid #94a3b8; padding: 0.4em 0.6em;
          vertical-align: top; }}
th {{ background: #e2e8f0; }}
code {{ background: #f1f5f9; padding: 0.1em 0.3em; border-radius: 3px;
        font-size: 0.92em; }}
pre {{ background: #f1f5f9; padding: 0.8em; border-radius: 4px;
       overflow-x: auto; }}
blockquote {{ border-left: 4px solid #94a3b8; margin: 1em 0;
              padding: 0.3em 1em; color: #475569; }}
.banner {{ background: #fef3c7; border-left: 4px solid #f59e0b;
           padding: 0.6em 1em; margin: 1em 0;
           font-weight: 600; color: #78350f; }}
</style>
</head>
<body>
{content}
</body>
</html>
"""


def render_markdown(text: str) -> str:
    try:
        import marko
    except ImportError as exc:
        raise SystemExit(
            "FAIL: marko is required. Install via `pip install marko`."
        ) from exc
    return marko.convert(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to deliverable .md")
    parser.add_argument("output", type=Path, help="path for rendered .html")
    parser.add_argument("--title", default=None, help="HTML <title>")
    parser.add_argument("--lang", default="en", choices=("en", "ko"),
                        help="document language hint for <html lang>")
    args = parser.parse_args(argv)

    if not args.source.exists():
        print(f"FAIL: source not found: {args.source}", file=sys.stderr)
        return 1

    text = args.source.read_text(encoding="utf-8")
    body_html = render_markdown(text)
    title = args.title or args.source.stem
    html = HTML_TEMPLATE.format(lang=args.lang, title=title, content=body_html)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"OK: rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
