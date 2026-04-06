from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
LAB_LOG = ROOT / "drills" / "lab-log.md"
OUTPUT_DIR = ROOT / "artifacts"
OUTPUT_FILE = OUTPUT_DIR / "drill-mastery.json"


def parse_lab_log() -> List[Dict[str, Any]]:
    if not LAB_LOG.exists():
        return []

    lines = LAB_LOG.read_text(encoding="utf-8").splitlines()
    entries: List[Dict[str, Any]] = []

    current_date = None
    current: Dict[str, Any] = {}

    date_re = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
    field_re = re.compile(r"^-\s*([a-z_]+):\s*(.*)$")

    for line in lines:
        m_date = date_re.match(line.strip())
        if m_date:
            current_date = m_date.group(1)
            continue

        m_field = field_re.match(line.strip())
        if not m_field:
            if current.get("drill_id") and current_date:
                current["date"] = current_date
                entries.append(current)
                current = {}
            continue

        key, value = m_field.group(1), m_field.group(2).strip()
        current[key] = value

    if current.get("drill_id") and current_date:
        current["date"] = current_date
        entries.append(current)

    return entries


def build_tracker(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    timeline = defaultdict(list)
    latest_stage = {}

    for e in entries:
        drill_id = e.get("drill_id")
        if not drill_id:
            continue

        event = {
            "date": e.get("date"),
            "reps": int(e.get("reps") or 0),
            "stage_before": e.get("stage_before"),
            "stage_after": e.get("stage_after"),
            "success_rate": float(e.get("success_rate") or 0.0),
            "notes": e.get("notes"),
        }
        timeline[drill_id].append(event)
        latest_stage[drill_id] = e.get("stage_after")

    return {
        "meta": {
            "entries": len(entries),
            "tracked_drills": len(timeline),
        },
        "latest_stage": latest_stage,
        "timeline": dict(timeline),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = parse_lab_log()
    payload = build_tracker(entries)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Tracked drills: {payload['meta']['tracked_drills']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
