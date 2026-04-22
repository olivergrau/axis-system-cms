# WP-05: Experiments And Runs Output Normalization

**Phase**: 2 -- Command Migration  
**Dependencies**: WP-01, WP-02  
**Scope**: Medium  
**Engineering reference**: Sections 4.2, 8.4, 9

---

## Objective

Normalize experiment and run command output around the shared list/detail and
completion patterns.

This WP should make the core inspection commands feel clearly related to the
new comparison and workspace surfaces.

---

## Deliverables

Modify:

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`

Add or update tests:

- experiment/run CLI output tests under `tests/framework/cli/`

---

## Priority Surfaces

Cover at minimum:

- `experiments list`
- `experiments show`
- `experiments run`
- `experiments resume`
- `runs list`
- `runs show`

---

## Required Output Shape

This migration should introduce:

- normalized list rows
- normalized detail titles and field rows
- consistent completion messages
- stable field ordering within each command family

---

## Implementation Steps

1. Standardize list rows around identifier, status, and one or two qualifiers.
2. Standardize detail views around title + metadata + sections where needed.
3. Normalize success/completion messaging for run/resume flows.
4. Keep JSON command outputs unchanged.

---

## Design Notes

- This WP should prefer consistency over clever formatting.
- Avoid over-engineering tables unless the command really benefits from them.
- Field ordering should remain stable across commands in the same family.

---

## Verification

1. Experiment and run lists scan more easily than the previous ad hoc formats.
2. Detail views use consistent titles and field rows.
3. Completion messaging is semantically aligned with the rest of the CLI.
4. JSON output remains unchanged.

---

## Files Created

None required.

## Files Modified

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`
- related CLI output tests

## Files Deleted

None.

