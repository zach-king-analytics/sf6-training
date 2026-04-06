# SF6 Training Protocol

A metric-driven skill development system for Street Fighter 6.

**Player:** BravenTooth | **Character:** Ryu | **Current MR:** ~1350 | **Target:** 1600

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Quick Start](#2-quick-start)
3. [Directory Structure](#3-directory-structure)
4. [Session Protocol](#4-session-protocol)
   - [Pre-Session Intent](#41-pre-session-intent)
   - [Per-Match Loss Entry](#42-per-match-loss-entry)
   - [Session Close — Hard Gate](#43-session-close--hard-gate)
   - [Weekly Review](#44-weekly-review)
5. [Loss Classification System](#5-loss-classification-system)
   - [Categories](#51-categories)
   - [Subcategories](#52-subcategories)
6. [Gameplan](#6-gameplan)
   - [Structure](#61-structure)
   - [Matchup Overrides](#62-matchup-overrides)
   - [Versioning and Snapshots](#63-versioning-and-snapshots)
7. [Concept Library](#7-concept-library)
   - [Dictionary Format](#71-dictionary-format)
   - [Fundamentals](#72-fundamentals)
   - [Ryu-Specific](#73-ryu-specific)
8. [Drill Library](#8-drill-library)
   - [Mastery Stages](#81-mastery-stages)
   - [Combo Drills](#82-combo-drills)
   - [Defense Drills](#83-defense-drills)
   - [Neutral Drills](#84-neutral-drills)
   - [Lab Log](#85-lab-log)
9. [Matchup Notes](#9-matchup-notes)
10. [Combo Repository](#10-combo-repository)
11. [Python Tooling](#11-python-tooling)
    - [session_close.py](#111-session_closepy--hard-gate)
    - [parse_sessions.py](#112-parse_sessionspy)
    - [drill_tracker.py](#113-drill_trackerpy)
    - [training_report.py](#114-training_reportpy)
    - [gameplan_snapshot.py](#115-gameplan_snapshotpy)
12. [Metrics Reference](#12-metrics-reference)
13. [Build Phases](#13-build-phases)

---

## 1. Philosophy

Stop autopiloting ranked. Every loss is a data point. This system turns those data points into a compounding knowledge base.

The core loop:

```
Play (with intent) → Loss → Replay Review → Lab → Measure → Repeat
```

The **hard gate**: you cannot close a session until every ranked loss has been watched and categorized. No exceptions. This is enforced by `tools/session_close.py`, which exits non-zero if any loss entry is missing a review confirmation, a valid category, or an actionable takeaway.

The goal is not grinding reps blindly. It is deliberate accumulation: every session adds to the concept library, every loss either triggers a drill or updates a matchup note, and every week surfaces the patterns most responsible for stalled MR.

---

## 2. Quick Start

### Setup

```bash
git clone https://github.com/zach-king-analytics/sf6-training.git
cd sf6-training
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL and PLAYER_CFN
```

### Starting a session

```bash
# Windows
$today = Get-Date -Format "yyyy-MM-dd"
$dir   = "sessions/$(Get-Date -Format 'yyyy/MM')"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Copy-Item protocol/session-template.md "$dir/$today.md"

# macOS/Linux
today=$(date +%F); dir="sessions/$(date +%Y/%m)"
mkdir -p $dir && cp protocol/session-template.md $dir/$today.md
```

Open the new file, fill in frontmatter (`focus`, `start_mr`), then queue.

### Closing a session (hard gate)

```bash
python tools/session_close.py --file sessions/2026/04/2026-04-04.md
```

Exits 0 on pass, exits 1 with specific error messages if any loss is incomplete. Fix the flagged entries and re-run.

### Weekly review (Sundays)

```bash
# Scaffold the week file
cp protocol/weekly-review-template.md weekly-reviews/2026-W15.md

# Generate artifacts
python tools/parse_sessions.py     # sessions/**/*.md  ->  artifacts/sessions-summary.json
python tools/drill_tracker.py      # drills/lab-log.md ->  artifacts/drill-mastery.json
python tools/training_report.py    # Supabase + above  ->  artifacts/training-report.json
```

All three artifacts land in `artifacts/` (gitignored). Commit the weekly review markdown when complete.

---

## 3. Directory Structure

```
sf6-training/
├── .env.example                       # environment variable template
├── .gitignore
├── README.md                          # this file (canonical spec)
├── requirements.txt
│
├── protocol/
│   ├── loss-analysis.md               # full protocol rules + rationale
│   ├── session-template.md            # copy to start each session
│   └── weekly-review-template.md      # copy every Sunday
│
├── sessions/                          # one .md per session
│   └── YYYY/
│       └── MM/
│           └── YYYY-MM-DD.md
│
├── weekly-reviews/                    # one .md per week
│   └── YYYY-WXX.md
│
├── concepts/
│   ├── index.md                       # mastery status table for all concepts
│   ├── fundamentals/
│   │   ├── drive-system.md
│   │   ├── neutral-footsies.md
│   │   ├── anti-air.md
│   │   └── mental-resilience.md
│   └── ryu-specific/
│       ├── normals-guide.md
│       ├── punish-combos.md
│       └── oki-pressure.md
│
├── gameplan/
│   ├── current.md                     # live gameplan with Mermaid decision trees
│   ├── _template.md                   # blank template for new versions
│   └── history/                       # timestamped snapshots (gitignored)
│       └── YYYY-MM-DD.md
│
├── drills/
│   ├── index.md                       # drill library + mastery table
│   ├── lab-log.md                     # running log of every lab session
│   ├── combo/
│   │   ├── light-confirm.md
│   │   ├── drive-rush-bnb.md
│   │   └── punish-optimal.md
│   ├── defense/
│   │   ├── anti-air-reaction.md
│   │   ├── dp-bait.md
│   │   └── parry-timing.md
│   └── neutral/
│       └── footsies-spacing.md
│
├── matchup-notes/
│   ├── index.md                       # all matchups at a glance
│   ├── _template.md                   # copy when starting a new matchup
│   └── ryu.md                         # mirror matchup
│
├── combos/
│   ├── index.md                       # master combo table + notation key
│   ├── _entry_template.md             # copy when adding a new combo
│   ├── confirms.md                    # hit-confirm strings (light, cr.MK, st.MP starters)
│   ├── punish.md                      # punish routes by resource state (0–5 bars)
│   └── oki-setups.md                  # post-knockdown meaty setups by position
│
├── tools/
│   ├── session_close.py               # hard gate validator
│   ├── parse_sessions.py              # session logs -> sessions-summary.json
│   ├── drill_tracker.py               # lab-log.md -> drill-mastery.json
│   ├── training_report.py             # Supabase + sessions -> training-report.json
│   └── gameplan_snapshot.py           # snapshots current.md -> gameplan/history/
│
└── artifacts/                         # gitignored build outputs
    ├── sessions-summary.json
    ├── drill-mastery.json
    └── training-report.json
```

---

## 4. Session Protocol

### 4.1 Pre-Session Intent

Before queuing, fill in the session frontmatter:

```yaml
---
date: 2026-04-05
player_cfn: braventooth
character: ryu
session_type: ranked         # ranked | lab | both
start_mr: 1362
end_mr: null                 # fill at close
focus: anti-air consistency  # 1-3 word focus for the session
energy_pre: medium           # low | medium | high
---
```

Then write your intent in prose under `## Intent`:
- Primary focus
- Secondary focus
- One thing to actively avoid autopiloting

This commit binds you to a game plan before the first match.

### 4.2 Per-Match Loss Entry

After every ranked loss, **before re-queuing**, fill in a loss block:

```markdown
### Loss 01

- opponent_cfn: <cfn>
- opponent_character: <character>
- rounds: 1-2
- replay_watched: true
- loss_category: knowledge_gap
- loss_subcategory: neutral

#### What beat me

- Describe the specific tool, spacing trap, or sequence that decided the match.

#### Execution gap (if any)

- Describe what you recognized but failed to convert.

#### Actionable takeaway

- drill: <drill-id>
- concept: <concept-file>
- matchup_note: <character>

#### Replay timestamp notes

- Round X, Xs: <observation>
```

`replay_watched: true` is the minimum requirement for the gate to pass. Everything else builds the database.

### 4.3 Session Close — Hard Gate

Run before ending the session:

```bash
python tools/session_close.py --file sessions/YYYY/MM/YYYY-MM-DD.md
```

The script validates every `### Loss NN` block in the file and enforces:

| Check | Rule |
|-------|------|
| `replay_watched` | Must be `true` |
| `loss_category` | Must be one of the four valid categories |
| `loss_subcategory` | Must be one of the six valid subcategories |
| Actionable takeaway | At least one of `drill`, `concept`, or `matchup_note` must be non-empty |

On failure it prints the specific violations and exits 1. Fix each one and re-run. On pass it prints a summary and exits 0.

Fill in the `## Session Close` section after the gate passes:

```markdown
## Session Close

- energy_post: medium
- mental_state: neutral
- end_mr: 1368
- notes: <anything worth carrying forward>
```

### 4.4 Weekly Review

Every Sunday, scaffold this week's review file and fill it in after running the three pipeline scripts:

```bash
python tools/parse_sessions.py
python tools/drill_tracker.py
python tools/training_report.py
```

Key fields:
- MR delta for the week
- Win/loss record
- Most common loss category
- Most common loss subcategory
- Drill progress
- Next week's single primary focus

Commit the weekly review file to main.

---

## 5. Loss Classification System

### 5.1 Categories

| Category | When to use |
|----------|------------|
| `knowledge_gap` | Didn't know what to do vs. that tool or situation |
| `execution` | Knew the answer but dropped the combo/punish |
| `mental` | Tilted, rushed, or autopiloted after a bad round |
| `conditioning` | Opponent adapted to your patterns; you didn't re-adapt |

### 5.2 Subcategories

| Subcategory | Description |
|-------------|-------------|
| `wake-up_option` | Lost to or missed a wake-up decision point |
| `neutral` | Lost ground/momentum due to neutral spacing or poke error |
| `punish_miss` | Missed a punish window on opponent's unsafe move |
| `oki` | Post-knockdown offense or defense went wrong |
| `drive_gauge` | Gauge management error (overextension, burnout) |
| `general` | None of the above; add a descriptive note |

**Derived metric**: `knowledge_gap` losses grouped by `opponent_character` produce the **matchup knowledge gap density** — which characters you are least prepared for.

---

## 6. Gameplan

`gameplan/current.md` is the canonical statement of how you currently play Ryu. It is versioned, updated deliberately, and snapshotted to `gameplan/history/` on each weekly review. It is **not** a drill or concept file — it is the meta-level decision framework you execute in matches.

### 6.1 Structure

The gameplan document contains:

| Section | Purpose |
|---------|---------|
| Win Conditions | The three paths to winning a match, in priority order |
| Neutral Framework | Range map + Mermaid decision tree for neutral situations |
| Anti-Air Branch | Decision tree for jump-in responses by arc |
| Pressure Framework | Post-knockdown and blocked-string decision trees |
| Defense Framework | Under-pressure and wake-up decision trees |
| Drive Gauge Philosophy | Table of decisions by gauge state |
| Non-Negotiables | Always-on rules that override matchup specifics |
| Matchup Overrides | Per-character deviations from the base gameplan |
| Adaptation Log | Running history of significant changes |

### 6.2 Matchup Overrides

When facing a character that requires a different neutral philosophy or pressure approach, add a row to the **Matchup Overrides** table in `current.md` and set `gameplan_override: <character>` in the session frontmatter. This flags the session as playing under modified rules.

### 6.3 Versioning and Snapshots

The gameplan is versioned with a simple integer. After editing `current.md` during a weekly review, run:

```bash
python tools/gameplan_snapshot.py [--date YYYY-MM-DD]
```

This:
1. Copies the current gameplan to `gameplan/history/YYYY-MM-DD.md`
2. Bumps the `version` field in `current.md`
3. Updates the `updated` date

`gameplan/history/` is gitignored to keep the main history clean; only `current.md` is committed. To reconstruct the evolution, review the **Adaptation Log** in `current.md` or check local history files.

---

## 7. Concept Library

Each concept file is a **dictionary entry** — a reference card structured around: definition, recognition cues, core tools/mechanics, and failure modes. The format is intentionally short and scannable, not educational prose. You should be able to open any concept file mid-session and get the answer in seconds.

YAML frontmatter in each file tracks `stage`, `drills`, and `related` concepts.

### 7.1 Dictionary Format

Each file contains:
- **Definition** — one sentence: what is this and why does it matter in context
- **Quick Reference** — table of stage, priority, linked drills, related concepts
- **Recognition Cues** — observable signals that this concept is in play right now
- **Core Tools / Mechanics** — the actionable table (tools, arcs, routes, etc.)
- **Failure Modes** — table of failure → cause → correction
- **Notes** — running session-specific observations

### 7.2 Fundamentals

| Term | File | Stage | Updated |
|------|------|-------|---------|
| Drive System | `fundamentals/drive-system.md` | Not Started | 2026-04-04 |
| Neutral / Footsies | `fundamentals/neutral-footsies.md` | Not Started | 2026-04-04 |
| Anti-Air | `fundamentals/anti-air.md` | Not Started | 2026-04-04 |
| Mental Resilience | `fundamentals/mental-resilience.md` | Not Started | 2026-04-04 |

### 7.3 Ryu-Specific

| Term | File | Stage | Updated |
|------|------|-------|---------|
| Normals Guide | `ryu-specific/normals-guide.md` | Not Started | 2026-04-04 |
| Punish Combos | `ryu-specific/punish-combos.md` | Not Started | 2026-04-04 |
| Oki Pressure | `ryu-specific/oki-pressure.md` | Not Started | 2026-04-04 |

---

## 8. Drill Library

### 8.1 Mastery Stages

| Stage | Meaning |
|-------|---------|
| `Not Started` | In the library; not yet attempted |
| `In Drill` | Actively working it; inconsistent |
| `Consistent` | Lands reliably in training mode |
| `Mastered` | Executes in match under pressure |

Each drill file contains: goal, training mode setup, target reps, pass criteria, and common failure notes. Mastery is promoted only after criterion is met across multiple sessions — no single-session passes.

### 8.2 Combo Drills

| Drill ID | File | Goal |
|----------|------|------|
| `light-confirm` | `combo/light-confirm.md` | Close-range light starter confirm |
| `drive-rush-bnb` | `combo/drive-rush-bnb.md` | Drive Rush conversion reliability |
| `punish-optimal` | `combo/punish-optimal.md` | Punish route by resource state |

### 8.3 Defense Drills

| Drill ID | File | Goal |
|----------|------|------|
| `anti-air-reaction` | `defense/anti-air-reaction.md` | Anti-air response rate + tool selection |
| `dp-bait` | `defense/dp-bait.md` | Reversal bait and punish |
| `parry-timing` | `defense/parry-timing.md` | Controlled parry on known pressure strings |

### 8.4 Neutral Drills

| Drill ID | File | Goal |
|----------|------|------|
| `footsies-spacing` | `neutral/footsies-spacing.md` | Spacing discipline and whiff punish |

### 8.5 Lab Log

All drill attempts are logged in `drills/lab-log.md` with one entry per lab session:

```markdown
## YYYY-MM-DD

- drill_id: drive-rush-bnb
  reps: 50
  stage_before: Not Started
  stage_after: In Drill
  success_rate: 0.56
  notes: Timing drops at max range.
```

`drill_tracker.py` reads this log and produces a mastery timeline per drill in `artifacts/drill-mastery.json`.

---

## 9. Matchup Notes

`matchup-notes/` is the evolving character knowledge base built from replay analysis.

Each file follows `_template.md`:
- Primary threats (neutral, pressure, wake-up)
- Evidence log (loss date + context entry)
- Verified punishes
- Identified defensive answers
- Win conditions
- Linked drills
- Review trigger threshold

**Workflow**: after any `knowledge_gap` loss, update or create the opponent's matchup note during the post-loss review. Files should be evidence-based — no assumptions without replay backing.

**Review trigger**: revisit a matchup file when three new `knowledge_gap` losses vs. that character occur in one week, or when ranked win rate vs. that character drops below 45% over 20 games.

Currently seeded:

| File | Status |
|------|--------|
| `ryu.md` | Starter draft |
| `_template.md` | Copy for new matchups |

Suggested next matchup files to create as losses accumulate: `ken.md`, `luke.md`, `marisa.md`, `jp.md`.

---

## 10. Combo Repository

`combos/` is a personal reference library of Ryu's combo routes and oki setups, each with notation, resource cost, and an embedded video.

> **Obsidian:** iframes render when Restricted Mode is off — Settings → Editor → disable Restricted Mode.
> **MkDocs:** raw HTML renders by default via the `md_in_html` extension.

### Structure

| File | Contents |
|------|----------|
| `index.md` | Master table of all combos + notation key |
| `confirms.md` | Hit-confirm strings (light starter, cr.MK DR BnB, st.MP check) |
| `punish.md` | Punish routes by resource state (0, 2, 3, 5 bars) |
| `oki-setups.md` | Meaty setups by knockdown source and position |
| `_entry_template.md` | Copy when adding a new combo |

### Adding a combo

1. Copy `_entry_template.md` and paste it into the relevant category file
2. Fill in notation, resource cost, damage, timing notes, and drop points
3. Upload or find a YouTube clip demonstrating the combo
4. Replace `VIDEO_ID` in the iframe `src` with the YouTube video ID (e.g. `dQw4w9WgXcQ`)
5. Set `?start=XX` to the timestamp in seconds where the combo demo begins
6. Update `combos/index.md` master table with the new entry

### Video embed format

```html
<iframe
  width="560"
  height="315"
  src="https://www.youtube.com/embed/VIDEO_ID?start=0"
  title="Combo Name"
  frameborder="0"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen>
</iframe>
```

---

## 11. Python Tooling

All scripts are in `tools/`. Run from the repo root using the `.venv` Python.

### 11.1 `session_close.py` — Hard Gate

**Input**: path to a single session file via `--file`

**Validates per `### Loss NN` block**:
- `replay_watched` is `true`
- `loss_category` is one of: `knowledge_gap`, `execution`, `mental`, `conditioning`
- `loss_subcategory` is one of: `wake-up_option`, `neutral`, `punish_miss`, `oki`, `drive_gauge`, `general`
- At least one actionable item (`drill`, `concept`, or `matchup_note`) is non-empty

**Exit codes**: `0` = pass, `1` = validation failure with messages, `2` = file not found

```bash
python tools/session_close.py --file sessions/2026/04/2026-04-05.md
```

### 11.2 `parse_sessions.py`

**Input**: all `sessions/**/*.md` files

**Output**: `artifacts/sessions-summary.json`

**Produces**:
- Total sessions, losses, reviewed losses
- Review compliance rate (% losses with `replay_watched: true`)
- Loss category counts
- Loss subcategory counts
- Knowledge gap counts by opponent character
- Weekly rollup (sessions, W-L per week)
- Full session array with all loss entries

```bash
python tools/parse_sessions.py
```

### 11.3 `drill_tracker.py`

**Input**: `drills/lab-log.md`

**Output**: `artifacts/drill-mastery.json`

**Produces**:
- Latest mastery stage per drill ID
- Full timeline of stage changes with dates, reps, and success rates

```bash
python tools/drill_tracker.py
```

### 11.4 `training_report.py`

**Input**: `artifacts/sessions-summary.json` + `artifacts/drill-mastery.json` + Supabase DB (`sf.v_match_player_norm` filtered to `player_cfn = 'braventooth'`)

**Output**: `artifacts/training-report.json`

**Produces**:
- Ranked winrate and MR snapshot from Supabase
- Per-matchup win rate table
- Total and ranked match counts
- Full session metrics from `parse_sessions.py`
- Full drill mastery state from `drill_tracker.py`
- DB connection status (graceful degradation if DB is unavailable)

**Requires** `DATABASE_URL` in `.env` pointing to the Supabase/Postgres instance from the `street_fighter` repo.

```bash
python tools/training_report.py
```

### 11.5 `gameplan_snapshot.py`

**Input**: `gameplan/current.md`

**Output**: `gameplan/history/YYYY-MM-DD.md` (snapshot copy)

**Effect on `current.md`**: bumps the `version` integer and updates the `updated` date

Run once per weekly review when you have made meaningful changes to the gameplan.

```bash
python tools/gameplan_snapshot.py [--date YYYY-MM-DD]
```

---

## 12. Metrics Reference

| Metric | Source | Script | Purpose |
|--------|--------|--------|---------|
| MR trend | Supabase `sf.v_match_player_norm` | `training_report.py` | Track progress toward 1600 |
| Ranked win rate overall | Supabase | `training_report.py` | Baseline performance signal |
| Win rate per matchup | Supabase | `training_report.py` | Identify structurally weak matchups |
| Review compliance rate | Session logs | `parse_sessions.py` | Protocol habit adherence |
| Loss category breakdown | Session logs | `parse_sessions.py` | Identify highest-leverage failure mode |
| Loss subcategory breakdown | Session logs | `parse_sessions.py` | Narrow the failure mode further |
| Matchup knowledge gap density | Session logs | `parse_sessions.py` | Which characters are least understood |
| Weekly W-L | Session logs | `parse_sessions.py` | Volume and trend |
| Drill mastery timeline | `lab-log.md` | `drill_tracker.py` | Lab progress over time |
| Drill → match correlation | Session + drill | `training_report.py` | Did the drill reduce that loss subcategory? |

---

## 13. Build Phases

| Phase | Focus | Status |
|-------|-------|--------|
| **1** | Protocol, templates, session close hard gate | ✅ Complete |
| **2** | Concept library seed (all 6 areas, dictionary format), drill library seed (7 drills) | ✅ Complete |
| **3** | `parse_sessions.py` + `drill_tracker.py` functional | ✅ Complete |
| **4** | `training_report.py` Supabase integration + graceful degradation | ✅ Complete |
| **5** | Gameplan system: `current.md`, `_template.md`, `gameplan_snapshot.py`, weekly review integration | ✅ Complete |
| **6** | Combo repository: `combos/` with notation, video embeds, confirms / punish / oki files | ✅ Complete |
| **7** | CLI helper to scaffold a new session file by date | ⏳ Queued |
| **8** | CI workflow — run gate + parse on every push | ⏳ Queued |
| **9** | Community site publication under `personal_site` | ⏳ Deferred |
