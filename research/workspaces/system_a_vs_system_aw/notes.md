# Workspace Notes

This workspace now manages the `system_a` vs `system_aw` investigation through
registered experiment series under `series/`.

The workspace was reset, so older manual runs, ad-hoc comparisons, and earlier
interpretation notes are no longer treated as current evidence for this
investigation.

Primary registered series:

- `system-parameter-variations`: `series/system-parameter-variations/experiment.yaml`
- `world-variations`: `series/world-variations/experiment.yaml`

Intended division of labor:

- `system-parameter-variations` keeps the shared world fixed and varies only
  the candidate-side `system_aw` parameters.
- `world-variations` keeps both systems fixed and varies the world symmetrically
  across reference and candidate configs.

Recommended workflow:

1. Run one series with `axis workspaces run-series . --series <series-id>`.
2. Inspect the generated series-local measurements, comparisons, and summaries.
3. Record interpretation in the series-local `notes.md` for that series.

Series-specific notes live in:

- `series/system-parameter-variations/notes.md`
- `series/world-variations/notes.md`
