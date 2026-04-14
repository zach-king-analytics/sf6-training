"""
prep_session.py — Scrape latest ranked matches for MY player, identify last
session losses from the DB, and generate a pre-populated session markdown file.

Usage:
    python tools/prep_session.py [--date YYYY-MM-DD] [--scrape] [--force]

Flags:
    --date      Target session date. Defaults to today.
    --scrape    Run a fresh buckler scrape for MY player before querying.
                Requires BUCKLER_PROJECT_PATH + COOKIES_PATH in .env.
    --force     Overwrite the markdown file if it already exists.

Config (.env in project root):
    DATABASE_URL          SQLAlchemy DSN  (default: postgres://localhost:5432/games)
    PLAYER_CFN            Your Buckler CFN  (default: braventooth)
    MY_PLAYER_ID          Your Buckler numeric player ID  (required for --scrape)
    BUCKLER_PROJECT_PATH  Absolute path to the street_fighter project root
    COOKIES_PATH          Path to buckler_cookies.json
    SESSION_GAP_HOURS     Hours of inactivity that separates sessions (default: 3)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional: load .env from project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass  # dotenv not required; set vars in your shell

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/games",
)
PLAYER_CFN = os.getenv("PLAYER_CFN", "braventooth").strip().lower()
MY_PLAYER_ID = os.getenv("MY_PLAYER_ID", "").strip()
BUCKLER_PROJECT_PATH = os.getenv("BUCKLER_PROJECT_PATH", "").strip()
COOKIES_PATH = os.getenv(
    "COOKIES_PATH",
    str(Path(BUCKLER_PROJECT_PATH) / "buckler_cookies.json") if BUCKLER_PROJECT_PATH else "",
)
SESSION_GAP_HOURS = float(os.getenv("SESSION_GAP_HOURS", "3"))

SESSIONS_DIR = ROOT / "sessions"

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_engine():
    from sqlalchemy import create_engine
    return create_engine(DATABASE_URL)


# ---------------------------------------------------------------------------
# Session clustering query
# ---------------------------------------------------------------------------

_LAST_SESSION_SQL = """
WITH my_matches AS (
    SELECT
        match_timestamp_local                     AS ts,
        is_winner,
        player_cfn,
        opponent_cfn,
        player_character,
        opponent_character,
        player_lp                                 AS player_mr,
        match_hash
    FROM sf.v_match_player
    WHERE lower(player_cfn) = lower(:cfn)
      AND lower(match_mode)  = 'rank'
    ORDER BY match_timestamp
),
with_gap AS (
    SELECT *,
        EXTRACT(EPOCH FROM (
            ts - LAG(ts) OVER (ORDER BY ts)
        )) / 3600.0 AS gap_hours
    FROM my_matches
),
labeled AS (
    SELECT *,
        SUM(CASE WHEN gap_hours > :gap OR gap_hours IS NULL THEN 1 ELSE 0 END)
            OVER (ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        AS session_num
    FROM with_gap
),
last_session_num AS (
    SELECT MAX(session_num) AS max_sn FROM labeled
)
SELECT
    l.ts,
    l.is_winner,
    l.player_cfn,
    l.opponent_cfn,
    l.opponent_character,
    l.player_character,
    l.player_mr
FROM labeled l
JOIN last_session_num lsn ON l.session_num = lsn.max_sn
ORDER BY l.ts;
"""


def fetch_last_session(cfn: str, gap_hours: float) -> List[Dict[str, Any]]:
    """Return all matches (wins + losses) for the most recent ranked session."""
    from sqlalchemy import text
    import pandas as pd

    engine = _get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(
            text(_LAST_SESSION_SQL),
            conn,
            params={"cfn": cfn, "gap": gap_hours},
        )

    if df.empty:
        return []

    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Buckler scrape (optional, --scrape flag)
# ---------------------------------------------------------------------------

def _add_buckler_to_path() -> None:
    if not BUCKLER_PROJECT_PATH:
        raise RuntimeError(
            "BUCKLER_PROJECT_PATH not set. Add it to .env pointing at the "
            "street_fighter project root."
        )
    p = Path(BUCKLER_PROJECT_PATH)
    if not p.exists():
        raise RuntimeError(f"BUCKLER_PROJECT_PATH does not exist: {p}")
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


async def _do_scrape() -> None:
    if not MY_PLAYER_ID:
        raise RuntimeError(
            "MY_PLAYER_ID not set. Add your Buckler numeric player ID to .env."
        )

    _add_buckler_to_path()

    # Import buckler_ingest components — these live in the street_fighter project
    import buckler_ingest.config as bcfg
    from buckler_ingest.scraper_nextjs import (
        load_cookies_for_httpx,
        detect_locale_and_build_id,
        scrape_player_screen,
    )
    from buckler_ingest.validate import prewrite_checks
    from buckler_ingest.db import connect_pg, get_table_columns
    from buckler_ingest.sink_pg import sink_postgres

    cookies_path = COOKIES_PATH or bcfg.COOKIES_PATH
    cookies = load_cookies_for_httpx(cookies_path)

    import httpx  # installed via buckler_ingest deps

    headers = {
        "User-Agent": bcfg.USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{bcfg.BUCKLER_BASE}/en",
        "X-Nextjs-Data": "1",
    }
    timeout = httpx.Timeout(connect=15.0, read=30.0, write=15.0, pool=30.0)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=3)

    rows: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(
        headers=headers,
        cookies=cookies,
        http2=True,
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    ) as client:
        locale, build_id = await detect_locale_and_build_id(client)
        print(f"  locale={locale}  buildId={build_id}")

        print(f"  Scraping player {MY_PLAYER_ID} rank screen...")
        try:
            rows = await scrape_player_screen(
                client, build_id, locale, MY_PLAYER_ID, "rank",
                bcfg.MAX_PER_SCREEN,
            )
        except Exception as exc:
            print(f"  WARNING: scrape failed: {exc}")
            return

    print(f"  Fetched {len(rows)} ranked rows")
    if not rows:
        return

    prewrite_checks(rows)

    # Parse DB connection from DATABASE_URL (psycopg2 style)
    from urllib.parse import urlparse, parse_qs
    _url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(_url)
    # Honour sslmode from query string (e.g. Supabase requires sslmode=require)
    qs = parse_qs(parsed.query)
    sslmode = qs.get("sslmode", [None])[0]
    # Auto-require SSL for non-local hosts (Supabase, RDS, etc.)
    host = parsed.hostname or "localhost"
    if sslmode is None and host not in ("localhost", "127.0.0.1", "::1"):
        sslmode = "require"
    conn = connect_pg(
        host=host,
        port=parsed.port or 5432,
        dbname=(parsed.path or "/postgres").lstrip("/"),
        user=parsed.username or "postgres",
        password=parsed.password or "",
        sslmode=sslmode,
    )
    try:
        sink_postgres(conn, rows)
        print("  DB upsert complete.")
    finally:
        conn.close()


def run_scrape() -> None:
    print("Running fresh buckler scrape for my player (rank only)...")
    asyncio.run(_do_scrape())


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _loss_block(n: int, row: Dict[str, Any]) -> str:
    opp_cfn = (row.get("opponent_cfn") or "").strip() or "unknown"
    opp_char = (row.get("opponent_character") or "").strip().lower() or "unknown"
    ts = row.get("ts")
    ts_str = ts.strftime("%H:%M") if isinstance(ts, datetime) else str(ts)

    return dedent(f"""\
        ### Loss {n:02d}

        - opponent_cfn: {opp_cfn}
        - opponent_character: {opp_char}
        - rounds: 0-2
        - replay_watched: false
        - loss_category: knowledge_gap
        - loss_subcategory: neutral

        #### What beat me

        -

        #### Execution gap (if any)

        -

        #### Actionable takeaway

        - drill:
        - concept:
        - matchup_note:

        #### Replay timestamp notes

        - ({ts_str})

        ---
    """)


def generate_session_md(
    session_date: date,
    losses: List[Dict[str, Any]],
    all_matches: List[Dict[str, Any]],
    character: str = "ryu",
) -> str:
    wins = sum(1 for m in all_matches if str(m.get("is_winner", "")).lower() in ("true", "1"))
    total_losses = len(losses)
    total = len(all_matches)

    # Infer MR from last match in session (player_mr column)
    start_mr_val: Optional[int] = None
    end_mr_val: Optional[int] = None
    if all_matches:
        first_mr = all_matches[0].get("player_mr")
        last_mr  = all_matches[-1].get("player_mr")
        if first_mr is not None:
            try:
                start_mr_val = int(first_mr)
            except (TypeError, ValueError):
                pass
        if last_mr is not None:
            try:
                end_mr_val = int(last_mr)
            except (TypeError, ValueError):
                pass

    session_start = all_matches[0]["ts"] if all_matches else datetime.now(timezone.utc)
    session_end   = all_matches[-1]["ts"] if all_matches else session_start

    start_str = session_start.strftime("%H:%M") if isinstance(session_start, datetime) else str(session_start)
    end_str   = session_end.strftime("%H:%M")   if isinstance(session_end,   datetime) else str(session_end)

    frontmatter = dedent(f"""\
        ---
        date: {session_date.isoformat()}
        player_cfn: {PLAYER_CFN}
        character: {character}
        session_type: ranked
        start_mr: {start_mr_val if start_mr_val is not None else "null"}
        end_mr: {end_mr_val if end_mr_val is not None else "null"}
        focus:
        energy_pre:
        gameplan_version: 1
        gameplan_override: none
        ---
    """)

    loss_blocks = "\n".join(_loss_block(i + 1, row) for i, row in enumerate(losses))
    if not loss_blocks:
        loss_blocks = "<!-- No ranked losses found in this session -->\n"

    return dedent(f"""\
        {frontmatter}
        # Session Log — {session_date.isoformat()}

        > Auto-generated by `tools/prep_session.py` from buckler data.
        > Session window: {start_str} – {end_str}  ({total} matches, {wins}W / {total_losses}L)

        ## Gameplan Check

        - Override active: none
        - One non-negotiable to actively reinforce this session:

        ## Intent

        - Primary focus:
        - Secondary focus:
        - One thing to avoid autopiloting:

        ## Match Summary

        - Total wins: {wins}
        - Total losses: {total_losses}
        - Ranked losses reviewed: 0/{total_losses}

        ## Loss Entries

        {loss_blocks}

        ## Lab Queue From This Session

        - [ ]

        ## Session Close

        - energy_post:
        - mental_state:
        - end_mr: {end_mr_val if end_mr_val is not None else ""}
        - notes:

        ## Gate Command

        ```bash
        python tools/session_close.py --file sessions/{session_date.strftime('%Y/%m')}/{session_date.isoformat()}.md
        ```
    """)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prep a session review markdown from last ranked session losses."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Session date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Run a fresh buckler scrape before querying the DB.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing session file.",
    )
    parser.add_argument(
        "--character",
        default="ryu",
        help="Character played this session (default: ryu)",
    )
    args = parser.parse_args()

    try:
        session_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"ERROR: invalid date '{args.date}'. Use YYYY-MM-DD.")
        return 2

    # --- output path
    out_dir = SESSIONS_DIR / str(session_date.year) / f"{session_date.month:02d}"
    out_path = out_dir / f"{session_date.isoformat()}.md"

    if out_path.exists() and not args.force:
        print(
            f"ERROR: {out_path} already exists. "
            "Use --force to overwrite, or pick a different --date."
        )
        return 2

    # --- optional fresh scrape
    if args.scrape:
        try:
            run_scrape()
        except Exception as exc:
            print(f"ERROR during scrape: {exc}")
            return 1

    # --- query DB for last session
    print(f"Querying last ranked session for {PLAYER_CFN!r} (gap threshold: {SESSION_GAP_HOURS}h)...")
    try:
        matches = fetch_last_session(PLAYER_CFN, SESSION_GAP_HOURS)
    except Exception as exc:
        print(f"ERROR querying DB: {exc}")
        return 1

    if not matches:
        print("No ranked matches found in DB. Run --scrape first or check PLAYER_CFN.")
        return 1

    losses = [m for m in matches if str(m.get("is_winner", "")).lower() not in ("true", "1")]
    wins   = len(matches) - len(losses)

    first_ts = matches[0]["ts"]
    last_ts  = matches[-1]["ts"]
    print(
        f"Last session: {len(matches)} matches "
        f"({wins}W / {len(losses)}L) "
        f"from {first_ts} → {last_ts}"
    )

    if not losses:
        print("No losses in last session — nothing to review. Well played.")

    # --- generate markdown
    md_content = generate_session_md(session_date, losses, matches, args.character)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_content, encoding="utf-8")

    print(f"\nCreated: {out_path}")
    print(f"  {len(losses)} loss block(s) pre-populated.")
    print("Next: open the file, fill in each Loss block, then run session_close.py to gate.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
