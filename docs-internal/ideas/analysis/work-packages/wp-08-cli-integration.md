# WP-08: CLI Integration Through `axis`

**Phase**: 3 -- Comparison Orchestration  
**Dependencies**: WP-07  
**Scope**: Medium  
**Spec reference**: Engineering spec Sections 5.1, 6.1

---

## Objective

Make paired trace comparison invokable through the existing `axis` command-line tool.

The CLI must remain a thin orchestration layer. It must not contain comparison logic itself.

---

## Deliverables

Modify:

- `src/axis/framework/cli.py`

Create if useful:

- `src/axis/framework/comparison/cli.py`
- `tests/framework/comparison/test_cli.py`

Likely reuse:

- `axis.framework.persistence.ExperimentRepository`
- `axis.visualization.replay_access.ReplayAccessService`

---

## Recommended Command Shape

Do not overdesign v1. Support one clean mode first.

Recommended initial command shape:

```text
axis compare \
  --reference-experiment <eid> --reference-run <rid> --reference-episode <n> \
  --candidate-experiment <eid> --candidate-run <rid> --candidate-episode <n>
```

Optional `--output json` must work consistently with the existing CLI.

---

## Implementation Steps

1. Add a top-level `compare` entity to the CLI parser.
2. Resolve the reference and candidate episode traces through the repository layer.
3. Load optional run metadata and run config for seed resolution.
4. Call `compare_episode_traces(...)`.
5. Render either text output or JSON output.
6. Ensure validation-failure results are shown clearly and do not crash the CLI.

---

## Design Notes

- Reuse the existing CLI style in `src/axis/framework/cli.py`.
- Prefer reuse of `ReplayAccessService` or repository loading patterns instead of inventing a second artifact-loading path.
- Keep formatting compact in text mode.

---

## Tests

Cover at least:

- parser accepts compare command
- compare command loads two valid episodes
- compare command emits JSON output
- compare command handles validation failure cleanly

---

## Verification

1. `axis compare ... --output json` returns structured comparison data.
2. CLI integration does not embed metric logic itself.

---

## Files Created

- `src/axis/framework/comparison/cli.py` (optional but recommended)
- `tests/framework/comparison/test_cli.py`

## Files Modified

- `src/axis/framework/cli.py`

## Files Deleted

None.
