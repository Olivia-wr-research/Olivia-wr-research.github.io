#!/usr/bin/env python3
"""Copy the standalone analytics event script into Quarto output folders."""

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "js" / "analytics-events.js"
MODE = sys.argv[1] if len(sys.argv) > 1 else "english"
DEST = ROOT / "docs" / "zh" / "assets" / "js" if MODE == "zh" else ROOT / "docs" / "assets" / "js"

if not SRC.exists():
    raise SystemExit(f"Missing analytics source: {SRC}")

DEST.mkdir(parents=True, exist_ok=True)
shutil.copy2(SRC, DEST / SRC.name)
