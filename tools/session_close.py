from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import frontmatter

VALID_CATEGORIES = {"knowledge_gap", "execution", "mental", "conditioning"}
VALID_SUBCATEGORIES = {
    "wake-up_option",
    "neutral",
    "punish_miss",
    "oki",
    "drive_gauge",
    "general",
}


def _parse_loss_blocks(content: str) -> List[Dict[str, Any]]:
    blocks = []
    pattern = re.compile(r"^###\s+Loss\s+\d+\s*$", re.MULTILINE)
    matches = list(pattern.finditer(content))
    if not matches:
        return blocks

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        def _field(name: str) -> str:
            f = re.search(rf"^-\s*{re.escape(name)}:\s*(.*)$", block, re.MULTILINE)
            return f.group(1).strip() if f else ""

        replay_raw = _field("replay_watched").lower()
        replay_watched = replay_raw in {"true", "yes", "1"}

        actionable = {
            "drill": _field("drill"),
            "concept": _field("concept"),
            "matchup_note": _field("matchup_note"),
        }

        blocks.append(
            {
                "title": m.group(0).strip(),
                "opponent_character": _field("opponent_character"),
                "replay_watched": replay_watched,
                "loss_category": _field("loss_category"),
                "loss_subcategory": _field("loss_subcategory"),
                "actionable": actionable,
            }
        )

    return blocks


def _validate(losses: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if not losses:
        errors.append("No loss entries found. Add at least one '### Loss NN' block.")
        return False, errors

    for idx, loss in enumerate(losses, start=1):
        label = f"Loss {idx:02d}"

        if not loss["replay_watched"]:
            errors.append(f"{label}: replay_watched must be true.")

        if loss["loss_category"] not in VALID_CATEGORIES:
            errors.append(
                f"{label}: loss_category '{loss['loss_category']}' is invalid. "
                f"Expected one of: {', '.join(sorted(VALID_CATEGORIES))}."
            )

        if loss["loss_subcategory"] not in VALID_SUBCATEGORIES:
            errors.append(
                f"{label}: loss_subcategory '{loss['loss_subcategory']}' is invalid. "
                f"Expected one of: {', '.join(sorted(VALID_SUBCATEGORIES))}."
            )

        actionable = loss["actionable"]
        if not any(actionable.values()):
            errors.append(
                f"{label}: add at least one actionable item (drill, concept, matchup_note)."
            )

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Session close hard gate validator")
    parser.add_argument("--file", required=True, help="Path to session markdown file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    post = frontmatter.load(path)
    content = post.content
    losses = _parse_loss_blocks(content)

    ok, errors = _validate(losses)

    if not ok:
        print("SESSION CLOSE: FAILED")
        for err in errors:
            print(f" - {err}")
        return 1

    reviewed = sum(1 for x in losses if x["replay_watched"])
    print("SESSION CLOSE: PASS")
    print(f" - losses: {len(losses)}")
    print(f" - reviewed: {reviewed}/{len(losses)}")
    print(" - all losses categorized with actionable takeaways")
    return 0


if __name__ == "__main__":
    sys.exit(main())
