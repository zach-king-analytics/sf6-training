from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = ROOT / "sessions"
OUTPUT_DIR = ROOT / "artifacts"
OUTPUT_FILE = OUTPUT_DIR / "sessions-summary.json"


def _session_files() -> Iterable[Path]:
    return sorted(SESSIONS_DIR.glob("**/*.md"))


def _parse_losses(content: str) -> List[Dict[str, Any]]:
    blocks = []
    pattern = re.compile(r"^###\s+Loss\s+\d+\s*$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        def _field(name: str) -> str:
            f = re.search(rf"^-\s*{re.escape(name)}:\s*(.*)$", block, re.MULTILINE)
            return f.group(1).strip() if f else ""

        replay_raw = _field("replay_watched").lower()
        replay_watched = replay_raw in {"true", "yes", "1"}

        blocks.append(
            {
                "opponent_character": _field("opponent_character").lower() or None,
                "replay_watched": replay_watched,
                "loss_category": _field("loss_category") or None,
                "loss_subcategory": _field("loss_subcategory") or None,
                "drill": _field("drill") or None,
                "concept": _field("concept") or None,
                "matchup_note": _field("matchup_note") or None,
            }
        )

    return blocks


def build_summary() -> Dict[str, Any]:
    sessions: List[Dict[str, Any]] = []
    category_counter: Counter[str] = Counter()
    subcategory_counter: Counter[str] = Counter()
    matchup_kg_counter: Counter[str] = Counter()

    total_losses = 0
    reviewed_losses = 0

    for file in _session_files():
        post = frontmatter.load(file)
        losses = _parse_losses(post.content)

        wins = int(post.metadata.get("wins", 0) or 0)
        losses_count = int(post.metadata.get("losses", len(losses)) or len(losses))

        session_record = {
            "file": str(file.relative_to(ROOT)).replace("\\", "/"),
            "date": post.metadata.get("date"),
            "player_cfn": post.metadata.get("player_cfn"),
            "character": post.metadata.get("character"),
            "session_type": post.metadata.get("session_type"),
            "start_mr": post.metadata.get("start_mr"),
            "end_mr": post.metadata.get("end_mr"),
            "wins": wins,
            "losses": losses_count,
            "loss_entries": losses,
        }
        sessions.append(session_record)

        total_losses += len(losses)
        reviewed_losses += sum(1 for x in losses if x["replay_watched"])

        for x in losses:
            if x["loss_category"]:
                category_counter[x["loss_category"]] += 1
            if x["loss_subcategory"]:
                subcategory_counter[x["loss_subcategory"]] += 1
            if x["loss_category"] == "knowledge_gap" and x["opponent_character"]:
                matchup_kg_counter[x["opponent_character"]] += 1

    review_compliance = (reviewed_losses / total_losses) if total_losses > 0 else 0.0

    by_week = defaultdict(lambda: {"sessions": 0, "wins": 0, "losses": 0})
    for s in sessions:
        date_str = str(s.get("date") or "")
        week_key = date_str[:8] if len(date_str) >= 8 else "unknown"
        by_week[week_key]["sessions"] += 1
        by_week[week_key]["wins"] += int(s.get("wins") or 0)
        by_week[week_key]["losses"] += int(s.get("losses") or 0)

    return {
        "meta": {
            "sessions_count": len(sessions),
            "total_losses": total_losses,
            "reviewed_losses": reviewed_losses,
            "review_compliance_rate": round(review_compliance, 4),
        },
        "loss_category_counts": dict(category_counter),
        "loss_subcategory_counts": dict(subcategory_counter),
        "knowledge_gap_by_matchup": dict(matchup_kg_counter),
        "weekly_rollup": dict(by_week),
        "sessions": sessions,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    OUTPUT_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Sessions: {summary['meta']['sessions_count']}")
    print(f"Review compliance: {summary['meta']['review_compliance_rate']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
