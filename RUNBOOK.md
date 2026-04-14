# SF6 Session Review Runbook

End-to-end setup and daily workflow for scraping your ranked losses, generating a review doc, and writing the completed review back to Postgres.

---

## Prerequisites

- PostgreSQL running with a `games` database (schema `sf` already exists from the buckler ingest setup)
- The `street_fighter` project at `C:\Users\zking\Projects\street_fighter` — buckler cookies refreshed
- Python venv for this project (`sf6-training`)

---

## One-Time Setup

### Step 1 — Install new dependencies

```powershell
cd C:\Users\zking\sf6-training
.venv\Scripts\pip install python-dotenv "httpx[http2]"
```

**What this does:** `python-dotenv` lets the tools read your `.env` file automatically. `httpx[http2]` is required if you use the `--scrape` flag to hit the Buckler API directly from this project.

---

### Step 2 — Create your `.env` file

Copy the example and fill in your values:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and set:

```
# Supabase connection string — find it in Supabase dashboard → Project Settings → Database → Connection string (URI)
# Use the Session Mode pooler (port 6543) or direct connection (port 5432); both work.
DATABASE_URL=postgresql+psycopg2://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
PLAYER_CFN=braventooth
MY_PLAYER_ID=<your numeric Buckler player ID>
BUCKLER_PROJECT_PATH=C:\Users\zking\Projects\street_fighter
SESSION_GAP_HOURS=3
```

**What each variable does:**
- `DATABASE_URL` — Supabase connection string; SSL is auto-applied for any non-localhost host
- `PLAYER_CFN` — your CFN as it appears in the DB; used to filter your matches
- `MY_PLAYER_ID` — your numeric Buckler profile ID (visible in the Buckler URL: `/profile/<ID>/`); only needed for the `--scrape` flag
- `BUCKLER_PROJECT_PATH` — tells `prep_session.py` where to find `buckler_ingest` when scraping
- `SESSION_GAP_HOURS` — hours of inactivity that mark a new session boundary (default 3); tune if your sessions are getting merged or split incorrectly

---

### Step 3 — Run the schema migration

Open the Supabase dashboard → **SQL Editor**, paste the contents of `sql/add_session_review.sql`, and run it.

Or if you have `psql` pointed at Supabase:

```powershell
psql "[your-supabase-connection-string]" -f sql/add_session_review.sql
```

**What this does:** Creates two new tables in the `sf` schema:

- `sf.session_log` — one row per training session (date, character, MR start/end, focus, energy, mental state, totals)
- `sf.session_loss` — one row per ranked loss within a session (opponent, character, rounds, category, subcategory, what beat you, execution gap, actionable takeaways, replay notes)

Also creates `sf.v_loss_review` — a denormalized view joining both tables for easy downstream querying.

Safe to re-run; all statements use `IF NOT EXISTS` / `CREATE OR REPLACE`.

---

## Daily Workflow

### Step 4 — Prep the session markdown

Run this **before or right after a ranked session** while the matches are in the DB.

```powershell
cd C:\Users\zking\sf6-training

# If your main buckler ingest already ran and DB is current:
.venv\Scripts\python tools\prep_session.py

# If you want to do a fresh scrape of just your player first:
.venv\Scripts\python tools\prep_session.py --scrape

# Extra options:
.venv\Scripts\python tools\prep_session.py --date 2026-04-13 --character ryu --force
```

**What this does:**

1. (If `--scrape`) Hits the Buckler API for your player's rank battlelog only — a microcosm of the full buckler ingest. Upserts new matches into `sf.raw_match`.
2. Queries `sf.v_match_player` for your most recent ranked session. "Session" is detected using a sliding window: any gap > `SESSION_GAP_HOURS` between consecutive matches starts a new cluster; the last cluster is your session.
3. Separates wins from losses.
4. Generates `sessions/YYYY/MM/YYYY-MM-DD.md` with:
   - Frontmatter pre-filled (date, CFN, character, start/end MR inferred from DB)
   - Match summary totals
   - One `### Loss NN` block per loss — opponent CFN, opponent character, and match time already inserted
   - All review fields left blank for you to fill in

**Output example:**
```
sessions/2026/04/2026-04-13.md
  5 loss block(s) pre-populated.
```

---

### Step 5 — Fill in the session markdown

Open the generated file and complete each loss block:

```markdown
### Loss 01

- opponent_cfn: some_guy
- opponent_character: ken
- rounds: 0-2
- replay_watched: false          ← must become true before closing
- loss_category: knowledge_gap   ← knowledge_gap | execution | mental | conditioning
- loss_subcategory: neutral      ← neutral | oki | punish_miss | wake-up_option | drive_gauge | general

#### What beat me
- He was consistently beating my st.HP with jump-in MK

#### Execution gap (if any)
- Missed two anti-air confirms

#### Actionable takeaway
- drill: anti-air-reaction
- concept: jump-arc-reading
- matchup_note: ken-pressure

#### Replay timestamp notes
- Round 2, 0:34 — late AA, should have been 2MP
```

Also fill in the `## Session Close` block (energy_post, mental_state, end_mr, notes) and update `## Intent`.

---

### Step 6 — Gate check (session_close.py)

Before writing to the DB, validate the session meets the review protocol:

```powershell
.venv\Scripts\python tools\session_close.py --file sessions/2026/04/2026-04-13.md
```

**What this does:** Checks that every loss block has:
- `replay_watched: true`
- A valid `loss_category` and `loss_subcategory`
- At least one actionable takeaway (drill, concept, or matchup_note)

Returns `SESSION CLOSE: PASS` or lists exactly what's still missing. Nothing is written to the DB here — this is a hard gate only.

---

### Step 7 — Write reviews to the DB

```powershell
.venv\Scripts\python tools\write_reviews.py --file sessions/2026/04/2026-04-13.md
```

**What this does:**

1. Parses the markdown frontmatter → writes one row to `sf.session_log` (upserts on `session_date + player_cfn`)
2. Parses each `### Loss NN` block → writes one row per loss to `sf.session_loss` (upserts on `session_id + loss_number`)
3. Pulls `end_mr`, `energy_post`, `mental_state`, and `notes` from the `## Session Close` block
4. Re-runnable safely — every write is an upsert, so you can edit the markdown and re-run to update

**Output example:**
```
Parsed: 2026-04-13.md
  session_date : 2026-04-13
  character    : ryu
  wins / losses: 7 / 5
  loss blocks  : 5
  end_mr       : 1341
  session_log row: session_id=4  date=2026-04-13
  session_loss rows upserted: 5

Done. 5 loss review(s) written for 2026-04-13.
```

---

## Querying the data downstream

```sql
-- All reviewed losses, newest first
SELECT * FROM sf.v_loss_review ORDER BY session_date DESC, loss_number;

-- Most common loss categories
SELECT loss_category, loss_subcategory, COUNT(*) AS n
FROM sf.session_loss
GROUP BY 1, 2
ORDER BY n DESC;

-- Losses by opponent character
SELECT opponent_character, COUNT(*) AS losses,
       ROUND(AVG(CASE WHEN loss_category = 'knowledge_gap' THEN 1 ELSE 0 END)::NUMERIC, 2) AS kg_rate
FROM sf.session_loss
WHERE opponent_character IS NOT NULL
GROUP BY 1
ORDER BY losses DESC;

-- MR trend by session
SELECT session_date, start_mr, end_mr, total_wins, total_losses, mental_state
FROM sf.session_log
ORDER BY session_date DESC;
```

---

## Quick reference

| Command | When to run |
|---|---|
| `prep_session.py` | Right after queuing ranked — generates the review doc |
| `prep_session.py --scrape` | Same, but pulls fresh matches from Buckler first |
| `session_close.py --file ...` | After filling in losses — validates before writing |
| `write_reviews.py --file ...` | After passing the gate — persists reviews to Postgres |

```
TYPICAL SESSION ORDER
─────────────────────
play ranked
  → prep_session.py [--scrape]
  → edit sessions/YYYY/MM/YYYY-MM-DD.md
  → session_close.py --file ...
  → write_reviews.py --file ...
```
