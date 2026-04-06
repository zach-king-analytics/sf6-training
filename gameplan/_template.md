---
version: 1
updated: YYYY-MM-DD
character: ryu
base_mr: null
gameplan_override: none
---

# Ryu Gameplan — [Version Title]

## Win Conditions

1. **[Primary]** — description
2. **[Secondary]** — description
3. **[Tertiary]** — description

---

## Neutral Framework

### Range Map

| Range | Stance | Primary Tools |
|-------|--------|---------------|
| Full screen | | |
| Mid range | | |
| Close range | | |

### Neutral Decision Tree

```mermaid
graph TD
    A[Neutral Start] --> B{Their range?}
    B --> |Full screen| C[...]
    B --> |Mid range| D[...]
    B --> |Close range| E[...]
```

### Anti-Air Branch

```mermaid
graph TD
    AA[Jump Detected] --> B{Arc?}
    B --> |Steep / close| C[...]
    B --> |Mid arc| D[...]
    B --> |Crossup| E[...]
```

---

## Pressure Framework

```mermaid
graph TD
    A[Knockdown] --> B[Meaty setup]
    B --> C{Result?}
    C --> |Hit| D[Confirm route]
    C --> |Block| E[Continue]
    C --> |Reversal| F[Bait → punish]
```

---

## Defense Framework

```mermaid
graph TD
    A[Under Pressure] --> B{Situation?}
    B --> |Repeated pressure| C[...]
    B --> |Meaty on wake| D[...]
    B --> |DI incoming| E[...]
```

---

## Drive Gauge Philosophy

| Gauge State | Decision |
|-------------|----------|
| ≥ 4 bars | |
| 2–4 bars | |
| < 2 bars | |
| Opponent burnout | |
| Self near burnout | |

---

## Non-Negotiables

- 
- 
- 

---

## Matchup Overrides

| Character | Phase | Override | Reason |
|-----------|-------|----------|--------|
| — | — | None | |

---

## Adaptation Log

| Date | Version | Change Summary |
|------|---------|----------------|
| YYYY-MM-DD | 1 | Initial |
