# Loss Analysis Protocol (Hard Gate)

## Objective

Break the autopilot loop by forcing replay review and actionable extraction after every ranked loss.

## Mandatory Rule

You may not close a ranked session until every ranked loss in that session has:

1. `replay_watched: true`
2. A valid `loss_category`
3. A valid `loss_subcategory`
4. At least one actionable item (`drill`, `concept`, or `matchup_note`)

This is enforced by `tools/session_close.py`.

## Per-Loss Process

1. Load replay immediately after the loss.
2. Watch at least the decisive rounds.
3. Identify the highest-leverage mistake pattern.
4. Categorize it.
5. Convert it into a lab action.
6. Add/update matchup note if applicable.

## Categories

### `knowledge_gap`
Use this when you did not know the answer to a move, sequence, spacing trap, or matchup option.

### `execution`
Use this when you recognized the answer but failed to execute (drop, wrong input, bad timing).

### `mental`
Use this when decision quality degraded due to tilt, frustration, panic, or autopilot.

### `conditioning`
Use this when the opponent adapted to your repeated options and you failed to re-adapt.

## Subcategories

- `wake-up_option`
- `neutral`
- `punish_miss`
- `oki`
- `drive_gauge`
- `general`

## Closing Checklist

- [ ] All ranked losses reviewed
- [ ] All losses categorized
- [ ] At least one drill added to lab queue
- [ ] Matchup notes updated for repeated patterns
- [ ] Session close gate passes (`session_close.py`)
