# SF6 Training Protocol

A metric-driven skill development system for Street Fighter 6.

**Player:** BravenTooth | **Character:** Ryu | **Current MR:** ~1350 | **Target:** 1600

---

## Philosophy

Stop autopiloting ranked. Every loss is a data point. This system turns those data points into a compounding knowledge base.

The core loop:

```
Play (with intent) → Loss → Replay Review → Lab → Measure → Repeat
```

The **hard gate**: you cannot close a session until every ranked loss has been watched and categorized. No exceptions.

---

## Quick Start

### Setup

```bash
git clone https://github.com/zach-king-analytics/sf6-training.git
cd sf6-training
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL
```

### Starting a session

```bash
# Create today's session file (adjust path for current date)
mkdir -p sessions/2026/04
cp protocol/session-template.md sessions/2026/04/2026-04-04.md
# Set your focus and MR in the frontmatter, then queue
```

### Closing a session (hard gate)

```bash
python tools/session_close.py --file sessions/2026/04/2026-04-04.md
```

If any ranked loss is unreviewed or missing a category, this exits with an error. Fix it, then re-run.

### Weekly review (Sundays)

```bash
# Scaffold the week file (adjust week number)
cp protocol/weekly-review-template.md weekly-reviews/2026-W15.md

# Generate metrics
python tools/parse_sessions.py              # sessions/ -> sessions-summary.json
python tools/drill_tracker.py               # lab-log.md -> drill-mastery.json
python tools/training_report.py             # + Supabase -> training-report.json
```

---

## Directory Structure

```
sf6-training/
├── protocol/
│   ├── loss-analysis.md          # The full protocol explained
│   ├── session-template.md       # Copy this to start each session
│   └── weekly-review-template.md # Copy this every Sunday
├── sessions/                     # YYYY/MM/YYYY-MM-DD.md  (one per session)
├── weekly-reviews/               # YYYY-WXX.md  (one per week)
├── concepts/
│   ├── index.md                  # mastery status overview
│   ├── fundamentals/
│   │   ├── drive-system.md
│   │   ├── neutral-footsies.md
│   │   ├── anti-air.md
│   │   └── mental-resilience.md
│   └── ryu-specific/
│       ├── normals-guide.md
│       ├── punish-combos.md
│       └── oki-pressure.md
├── drills/
│   ├── index.md                  # drill library + mastery table
│   ├── lab-log.md                # running log of every lab session
│   ├── combo/
│   ├── defense/
│   └── neutral/
├── matchup-notes/
│   ├── index.md
│   ├── _template.md              # copy when starting a new matchup
│   └── ryu.md
└── tools/
    ├── session_close.py          # hard gate validator
    ├── parse_sessions.py         # session logs -> sessions-summary.json
    ├── training_report.py        # Supabase + sessions -> training-report.json
    └── drill_tracker.py          # lab-log -> drill-mastery.json
```

---

## Metrics

| Metric | Source | Script |
|--------|--------|--------|
| MR trend | Supabase `sf.v_match_player_norm` | `training_report.py` |
| Win rate per matchup | Supabase | `training_report.py` |
| Review compliance rate | Session logs | `parse_sessions.py` |
| Loss category breakdown | Session logs | `parse_sessions.py` |
| Matchup knowledge gap density | Session + Supabase | `training_report.py` |
| Drill mastery timeline | `drills/lab-log.md` | `drill_tracker.py` |

---

## Loss Categories

| Category | When to use |
|----------|------------|
| `knowledge_gap` | Didn't know what to do vs. that tool or situation |
| `execution` | Knew the answer but dropped the combo/punish |
| `mental` | Tilted, rushed, or autopiloted after a bad round |
| `conditioning` | Opponent adapted to your patterns and you didn't adjust |

## Loss Subcategories

`wake-up_option` | `neutral` | `punish_miss` | `oki` | `drive_gauge` | `general`

---

## Drill Mastery Stages

| Stage | Meaning |
|-------|---------|
| `Not Started` | In the library, not yet attempted |
| `In Drill` | Actively working it, inconsistent |
| `Consistent` | Lands reliably in training mode |
| `Mastered` | Executes in match under pressure |

---

## Build Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Protocol + templates + Python gate | ✅ Done |
| 2 | Concept + drill library seeded | 🔄 In Progress |
| 3 | `parse_sessions.py` + `session_close.py` functional | ✅ Done |
| 4 | `training_report.py` Supabase integration | ✅ Done |
| 5 | Community site publication | ⏳ Deferred |
