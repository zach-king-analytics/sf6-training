from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
SESSIONS_SUMMARY = ARTIFACTS / "sessions-summary.json"
DRILL_MASTERY = ARTIFACTS / "drill-mastery.json"
OUT_FILE = ARTIFACTS / "training-report.json"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/games",
)
PLAYER_CFN = os.getenv("PLAYER_CFN", "braventooth").lower().strip()

MATCH_QUERY = """
SELECT
    lower(player_cfn) AS player_cfn,
    player_character,
    opponent_character,
    player_lp AS player_mr,
    opponent_lp AS opponent_mr,
    match_timestamp,
    is_winner,
    lower(match_mode) AS match_mode
FROM sf.v_match_player_norm
WHERE lower(player_cfn) = lower(:player_cfn)
ORDER BY match_timestamp;
"""


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_supabase_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "matches": 0,
            "ranked_matches": 0,
            "overall_winrate": 0.0,
            "ranked_winrate": 0.0,
            "mr_latest": None,
            "matchups": {},
        }

    df["is_win"] = df["is_winner"].astype(str).str.lower().isin(["true", "1", "yes"])
    overall_winrate = float(df["is_win"].mean())

    ranked = df[df["match_mode"] == "rank"]
    ranked_winrate = float(ranked["is_win"].mean()) if not ranked.empty else 0.0
    mr_latest = int(ranked["player_mr"].dropna().iloc[-1]) if not ranked.empty else None

    matchup = (
        ranked.groupby("opponent_character", dropna=False)
        .agg(games=("is_win", "size"), winrate=("is_win", "mean"))
        .reset_index()
        .sort_values("games", ascending=False)
    )

    matchup_payload = {}
    for _, row in matchup.iterrows():
        key = (row["opponent_character"] or "unknown").lower()
        matchup_payload[key] = {
            "games": int(row["games"]),
            "winrate": round(float(row["winrate"]), 4),
        }

    return {
        "matches": int(len(df)),
        "ranked_matches": int(len(ranked)),
        "overall_winrate": round(overall_winrate, 4),
        "ranked_winrate": round(ranked_winrate, 4),
        "mr_latest": mr_latest,
        "matchups": matchup_payload,
    }


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    sessions = _load_json(SESSIONS_SUMMARY)
    drills = _load_json(DRILL_MASTERY)

    df = pd.DataFrame()
    db_error = None
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            df = pd.read_sql(text(MATCH_QUERY), conn, params={"player_cfn": PLAYER_CFN})
    except Exception as exc:
        db_error = str(exc)

    supabase_metrics = _build_supabase_metrics(df)

    report = {
        "player_cfn": PLAYER_CFN,
        "supabase": supabase_metrics,
        "sessions": sessions,
        "drills": drills,
        "meta": {
            "database_connected": db_error is None,
            "database_error": db_error,
        },
    }

    OUT_FILE.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    if db_error is None:
        print(f"Ranked winrate: {supabase_metrics['ranked_winrate']:.1%}")
    else:
        print("Database connection unavailable. Wrote report with session and drill metrics only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
