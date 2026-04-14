"""
write_reviews.py — Parse a completed session markdown and write the loss
review data to sf.session_log + sf.session_loss.

Usage:
    python tools/write_reviews.py --file sessions/2026/04/2026-04-04.md [--force]

Flags:
    --file   Path to the session markdown (relative to project root or absolute).
    --force  Re-upsert even if a session_log row already exists for this date.

Config (.env in project root):
    DATABASE_URL   SQLAlchemy DSN  (default: postgres://localhost:5432/games)
    PLAYER_CFN     Your Buckler CFN  (default: braventooth)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/games",
)
PLAYER_CFN = os.getenv("PLAYER_CFN", "braventooth").strip().lower()

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _field(block: str, name: str) -> str:
    m = re.search(rf"^-\s*{re.escape(name)}:\s*(.*)$", block, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _section(content: str, heading: str) -> str:
    """Extract the text under a given markdown heading (up to the next heading)."""
    pattern = re.compile(
        rf"^####\s+{re.escape(heading)}\s*$(.+?)(?=^####|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        return ""
    return m.group(1).strip()


def _bullet_lines(text: str) -> str:
    """Collect non-empty bullet lines into a single string."""
    lines = [
        re.sub(r"^-\s*", "", ln).strip()
        for ln in text.splitlines()
        if ln.strip() and ln.strip() != "-"
    ]
    return "\n".join(lines)


def parse_loss_blocks(content: str) -> List[Dict[str, Any]]:
    pattern = re.compile(r"^###\s+Loss\s+(\d+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(content))
    losses: List[Dict[str, Any]] = []

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        replay_raw = _field(block, "replay_watched").lower()
        replay_watched = replay_raw in {"true", "yes", "1"}

        what_beat_me  = _bullet_lines(_section(block, "What beat me"))
        exec_gap      = _bullet_lines(_section(block, "Execution gap (if any)"))
        replay_notes  = _bullet_lines(_section(block, "Replay timestamp notes"))

        losses.append({
            "loss_number":          int(m.group(1)),
            "opponent_cfn":         _field(block, "opponent_cfn") or None,
            "opponent_character":   _field(block, "opponent_character").lower() or None,
            "rounds":               _field(block, "rounds") or None,
            "replay_watched":       replay_watched,
            "loss_category":        _field(block, "loss_category") or None,
            "loss_subcategory":     _field(block, "loss_subcategory") or None,
            "what_beat_me":         what_beat_me or None,
            "execution_gap":        exec_gap or None,
            "actionable_drill":     _field(block, "drill") or None,
            "actionable_concept":   _field(block, "concept") or None,
            "actionable_matchup":   _field(block, "matchup_note") or None,
            "replay_notes":         replay_notes or None,
        })

    return losses


def parse_session_close(content: str) -> Dict[str, Any]:
    """Parse the Session Close block for energy_post, mental_state, end_mr, notes."""
    close_pattern = re.compile(
        r"^##\s+Session Close\s*$(.*?)(?=^##|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = close_pattern.search(content)
    block = m.group(1) if m else ""

    def _f(name: str) -> str:
        return _field(block, name)

    raw_mr = _f("end_mr")
    end_mr: Optional[int] = None
    try:
        end_mr = int(raw_mr) if raw_mr else None
    except ValueError:
        pass

    return {
        "energy_post":  _f("energy_post") or None,
        "mental_state": _f("mental_state") or None,
        "end_mr":       end_mr,
        "notes":        _f("notes") or None,
    }


def parse_match_summary(content: str) -> Dict[str, int]:
    """Parse Total wins / Total losses from the Match Summary block."""
    wins = losses = 0
    m = re.search(r"^-\s*Total wins:\s*(\d+)", content, re.MULTILINE)
    if m:
        wins = int(m.group(1))
    m = re.search(r"^-\s*Total losses:\s*(\d+)", content, re.MULTILINE)
    if m:
        losses = int(m.group(1))
    return {"total_wins": wins, "total_losses": losses}


# ---------------------------------------------------------------------------
# DB write
# ---------------------------------------------------------------------------

_UPSERT_SESSION_LOG = """
INSERT INTO sf.session_log (
    session_date, player_cfn, character, session_type,
    start_mr, end_mr, focus, energy_pre, energy_post,
    mental_state, total_wins, total_losses, session_notes, source_file, updated_at
) VALUES (
    :session_date, :player_cfn, :character, :session_type,
    :start_mr, :end_mr, :focus, :energy_pre, :energy_post,
    :mental_state, :total_wins, :total_losses, :session_notes, :source_file, NOW()
)
ON CONFLICT (session_date, player_cfn)
DO UPDATE SET
    character       = EXCLUDED.character,
    session_type    = EXCLUDED.session_type,
    start_mr        = EXCLUDED.start_mr,
    end_mr          = EXCLUDED.end_mr,
    focus           = EXCLUDED.focus,
    energy_pre      = EXCLUDED.energy_pre,
    energy_post     = EXCLUDED.energy_post,
    mental_state    = EXCLUDED.mental_state,
    total_wins      = EXCLUDED.total_wins,
    total_losses    = EXCLUDED.total_losses,
    session_notes   = EXCLUDED.session_notes,
    source_file     = EXCLUDED.source_file,
    updated_at      = NOW()
RETURNING session_id;
"""

_UPSERT_LOSS = """
INSERT INTO sf.session_loss (
    session_id, loss_number, opponent_cfn, opponent_character,
    player_character, rounds, replay_watched, loss_category, loss_subcategory,
    what_beat_me, execution_gap, actionable_drill, actionable_concept,
    actionable_matchup, replay_notes
) VALUES (
    :session_id, :loss_number, :opponent_cfn, :opponent_character,
    :player_character, :rounds, :replay_watched, :loss_category, :loss_subcategory,
    :what_beat_me, :execution_gap, :actionable_drill, :actionable_concept,
    :actionable_matchup, :replay_notes
)
ON CONFLICT (session_id, loss_number)
DO UPDATE SET
    opponent_cfn        = EXCLUDED.opponent_cfn,
    opponent_character  = EXCLUDED.opponent_character,
    player_character    = EXCLUDED.player_character,
    rounds              = EXCLUDED.rounds,
    replay_watched      = EXCLUDED.replay_watched,
    loss_category       = EXCLUDED.loss_category,
    loss_subcategory    = EXCLUDED.loss_subcategory,
    what_beat_me        = EXCLUDED.what_beat_me,
    execution_gap       = EXCLUDED.execution_gap,
    actionable_drill    = EXCLUDED.actionable_drill,
    actionable_concept  = EXCLUDED.actionable_concept,
    actionable_matchup  = EXCLUDED.actionable_matchup,
    replay_notes        = EXCLUDED.replay_notes;
"""


def write_to_db(
    source_file: Path,
    fm: Dict[str, Any],
    close: Dict[str, Any],
    summary: Dict[str, int],
    losses: List[Dict[str, Any]],
) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)

    raw_start_mr = fm.get("start_mr")
    start_mr: Optional[int] = None
    try:
        start_mr = int(raw_start_mr) if raw_start_mr not in (None, "null", "") else None
    except (TypeError, ValueError):
        pass

    session_params = {
        "session_date":  str(fm.get("date", "")),
        "player_cfn":    str(fm.get("player_cfn") or PLAYER_CFN),
        "character":     str(fm.get("character") or ""),
        "session_type":  str(fm.get("session_type") or "ranked"),
        "start_mr":      start_mr,
        "end_mr":        close.get("end_mr"),
        "focus":         str(fm.get("focus") or "") or None,
        "energy_pre":    str(fm.get("energy_pre") or "") or None,
        "energy_post":   close.get("energy_post"),
        "mental_state":  close.get("mental_state"),
        "total_wins":    summary.get("total_wins", 0),
        "total_losses":  summary.get("total_losses", 0),
        "session_notes": close.get("notes"),
        "source_file":   str(source_file),
    }

    with engine.begin() as conn:
        row = conn.execute(text(_UPSERT_SESSION_LOG), session_params).fetchone()
        session_id = row[0]
        print(f"  session_log row: session_id={session_id}  date={session_params['session_date']}")

        player_character = str(fm.get("character") or "")
        for loss in losses:
            loss_params = {
                "session_id":         session_id,
                "player_character":   player_character,
                **loss,
            }
            conn.execute(text(_UPSERT_LOSS), loss_params)

        print(f"  session_loss rows upserted: {len(losses)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a completed session markdown and write reviews to the DB."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to session markdown (relative to project root or absolute).",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()

    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    import frontmatter as fm_lib

    post = fm_lib.load(str(path))
    fm   = dict(post.metadata)
    body = post.content

    losses  = parse_loss_blocks(body)
    close   = parse_session_close(body)
    summary = parse_match_summary(body)

    print(f"Parsed: {path.name}")
    print(f"  session_date : {fm.get('date')}")
    print(f"  character    : {fm.get('character')}")
    print(f"  wins / losses: {summary['total_wins']} / {summary['total_losses']}")
    print(f"  loss blocks  : {len(losses)}")
    print(f"  end_mr       : {close.get('end_mr')}")

    if not losses:
        print("WARNING: no loss blocks found — nothing to write.")
        return 0

    try:
        write_to_db(path, fm, close, summary, losses)
    except Exception as exc:
        print(f"ERROR writing to DB: {exc}")
        return 1

    print(f"\nDone. {len(losses)} loss review(s) written for {fm.get('date')}.")
    print("Query: SELECT * FROM sf.v_loss_review ORDER BY session_date DESC, loss_number;")
    return 0


if __name__ == "__main__":
    sys.exit(main())
