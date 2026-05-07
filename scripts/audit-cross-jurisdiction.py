#!/usr/bin/env python3
"""CLI wrapper for the cross-jurisdiction citation auditor."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cross_jurisdiction_auditor.audit import main


if __name__ == "__main__":
    raise SystemExit(main())
