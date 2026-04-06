---
version: 1
updated: 2026-04-05
character: ryu
base_mr: 1362
gameplan_override: none
---

# Ryu Gameplan — Current

## Win Conditions

In priority order — pursue the highest-yield path available given the current round state.

1. **Whiff punish loop** — hold mid-range, bait a poke, convert with cr.MK or st.HK into Drive Rush BnB
2. **Anti-air control into corner carry** — shut down jump-in attempts, carry to corner, run oki
3. **Fireball rhythm into walk-in mix** — establish fireball cadence, walk in behind it, threaten throw or Drive Rush

---

## Neutral Framework

### Range Map

| Range | Stance | Primary Tools |
|-------|--------|---------------|
| Full screen | Patient / fireball | HP Hadouken, walk forward, react to DR |
| Mid range (footsies) | Controlled | cr.MK (poke), st.HK (counter poke), wait |
| Close range | Drive Rush or throw mix | st.MP check, cr.LP, throw, DR pressure |

### Neutral Decision Tree

```mermaid
graph TD
    A[Neutral Start] --> B{Their range?}

    B --> |Full screen| C{Their action?}
    C --> |Advancing| D[Hold ground / fireball / walk back if DR]
    C --> |Jumping| E[Anti-Air branch]
    C --> |Waiting| F[Walk forward slowly / bait / fireball rhythm]

    B --> |Mid range| G{Their action?}
    G --> |Poking| H[st.HK whiff punish OR wait + cr.MK]
    G --> |Jumping| E
    G --> |Walking in| I[cr.MK check → throw → backdash option]

    B --> |Close range| J{Their action?}
    J --> |Pressing buttons| K[Parry or reversal]
    J --> |Going for throw| L[Tech or jump]
    J --> |Standing off| M[st.MP check → DR mix → throw]
```

### Anti-Air Branch

```mermaid
graph TD
    AA[Jump Detected] --> B{Arc?}
    B --> |Steep / close| C[cr.HP → combo]
    B --> |Mid arc| D[st.HP or HP DP → corner carry]
    B --> |Crossup arc| E[Walk under → punish / reversal]
    B --> |Early / high jump| F[LP DP or st.HK by range]
```

---

## Pressure Framework

### Post-Knockdown / Corner

```mermaid
graph TD
    A[Knockdown Achieved] --> B[Meaty: cr.MK or cr.LP on wake]
    B --> C{Result?}
    C --> |Hit| D[Confirm → DR BnB]
    C --> |Block| E[Plus frames → throw threat or continue]
    C --> |Reversal DP| F[Bait → full punish]
    C --> |Backdash| G[Walk in → reset pressure]
```

### Blocked String

```mermaid
graph TD
    A[String Blocked] --> B{Resources?}
    B --> |DR available + positive| C[Drive Rush mix]
    B --> |DR low or negative| D[Reset to mid range]
    D --> E[Re-establish footsies]
```

---

## Defense Framework

```mermaid
graph TD
    A[Under Pressure] --> B{Situation?}
    B --> |2+ consecutive blocks| C[Look for parry window on known string]
    B --> |Meaty on wake-up| D{Resources?}
    D --> |Have DP| E[Reversal or block — read their pattern]
    D --> |Low resources| F[Block and look for reversal bait]
    B --> |Grabbed repeatedly| G[Track rhythm → tech timing]

    H[DI Incoming] --> I{Corner behind me?}
    I --> |No| J[Absorb with own DI]
    I --> |Yes| K[Backdash or DR out if reaction allows]
    I --> |Trade range| L[DI trade]
```

---

## Drive Gauge Philosophy

| Gauge State | Decision |
|-------------|----------|
| ≥ 4 bars | DR BnB available — play offensively |
| 2–4 bars | Limited DR — prefer whiff punish and anti-air routes |
| < 2 bars | **No offensive DR** — conserve; parry over DI |
| Opponent in burnout | Maximize pressure window; DR corner carry |
| Self near burnout | Parry over DI; no aggressive DR; escape cleanly |

---

## Non-Negotiables

These apply every session regardless of matchup or focus:

- Anti-air **every** jump unless it is a true crossup
- Check Drive Gauge **before** committing to DR or DI
- No re-queue after a ranked loss without writing the loss entry first

---

## Matchup Overrides

When playing a character listed here, deviations from the base gameplan are in effect.
In session frontmatter, set `gameplan_override: <character>` to flag it.

| Character | Phase | Override | Reason |
|-----------|-------|----------|--------|
| — | — | No active overrides | |

---

## Adaptation Log

Significant gameplan changes are recorded here. Full snapshots are in `gameplan/history/`.

| Date | Version | Change Summary |
|------|---------|----------------|
| 2026-04-05 |  | Seeded placeholder gameplan |
