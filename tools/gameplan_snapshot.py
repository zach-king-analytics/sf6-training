#!/usr/bin/env python3
"""
gameplan_snapshot.py

Snapshots gameplan/current.md to gameplan/history/YYYY-MM-DD.md.
Run during weekly review whenever the gameplan has been meaningfully updated.
Bumps the version number and updated date in current.md after snapshotting.

Usage:
    python tools/gameplan_snapshot.py [--date YYYY-MM-DD]
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot the current gameplan.")
    parser.add_argument(
        "--date",
        default=str(date.today()),
        help="Snapshot date in YYYY-MM-DD format (default: today)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    current_path = root / "gameplan" / "current.md"
    history_dir = root / "gameplan" / "history"

    if not current_path.exists():
        print(f"ERROR: {current_path} not found", file=sys.stderr)
        return 2

    history_dir.mkdir(parents=True, exist_ok=True)
    dest_path = history_dir / f"{args.date}.md"

    if dest_path.exists():
        print(f"WARNING: Snapshot for {args.date} already exists at {dest_path}")
        print("Overwrite? [y/N] ", end="", flush=True)
        if input().strip().lower() != "y":
            print("Aborted.")
            return 0

    # Snapshot current state before bumping
    shutil.copy2(current_path, dest_path)
    print(f"Snapshot saved → {dest_path.relative_to(root)}")

    # Bump version and updated date in current.md
    text = current_path.read_text(encoding="utf-8")

    version_match = re.search(r"^version:\s*(\d+)", text, re.MULTILINE)
    if version_match:
        old_version = int(version_match.group(1))
        new_version = old_version + 1
        text = re.sub(
            r"^version:\s*\d+",
            f"version: {new_version}",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^updated:\s*\S+",
            f"updated: {args.date}",
            text,
            flags=re.MULTILINE,
        )
        current_path.write_text(text, encoding="utf-8")
        print(f"current.md bumped to version {new_version} (updated: {args.date})")
    else:
        print("NOTE: Could not find 'version' field in frontmatter — skipping bump.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
