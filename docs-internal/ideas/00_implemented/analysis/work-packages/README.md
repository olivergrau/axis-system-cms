# Paired Trace Comparison -- Work Packages

**Spec**: [paired-trace-comparison-spec.md](../paired-trace-comparison-spec.md)  
**Engineering spec**: [paired-trace-comparison-engineering-spec.md](../paired-trace-comparison-engineering-spec.md)  
**Phase**: Initial implementation pass

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|----|-------|--------------|-------|------------|
| [WP-01](wp-01-result-models.md) | Comparison result models | None | Medium | Create typed comparison result schema |
| [WP-02](wp-02-pair-validation.md) | Pair validation | WP-01 | Medium | Strict paired validation and seed resolution |
| [WP-03](wp-03-alignment.md) | Shared-prefix alignment | WP-01 | Small | Add alignment helpers and summary |
| [WP-04](wp-04-actions-usage.md) | Action-space and usage metrics | WP-01, WP-02, WP-03 | Medium | Shared labels, counts, deltas, most-used action |
| [WP-05](wp-05-divergence-metrics.md) | Divergence metrics | WP-01, WP-03 | Medium | Action, position, vitality metric families |
| [WP-06](wp-06-outcome-comparison.md) | Outcome comparison | WP-01, WP-03 | Small | Whole-episode outcome block |
| [WP-07](wp-07-top-level-compare.md) | Top-level compare entry point | WP-01 through WP-06 | Medium | Orchestrate validation, alignment, metrics |
| [WP-08](wp-08-cli-integration.md) | CLI integration via `axis` | WP-07 | Medium | Add `axis compare` command path |
| [WP-09](wp-09-extension-dispatch.md) | Minimal extension dispatch | WP-07 | Small | Optional system-specific comparison blocks |
| [WP-10](wp-10-system-c-extension.md) | System C prediction extension | WP-09 | Medium | First comparison extension for prediction |
| [WP-11](wp-11-synthetic-tests.md) | Synthetic comparison test suite | WP-01 through WP-10 | Medium | Deterministic edge-case coverage |
| [WP-12](wp-12-persisted-trace-checks.md) | Persisted trace compatibility checks | WP-07 through WP-10 | Small | Real artifact compatibility checks |

---

## Dependency Graph

```text
WP-01 (result models)
  ├── WP-02 (pair validation)
  ├── WP-03 (alignment)
  ├── WP-04 (actions + usage)      [depends on WP-02, WP-03]
  ├── WP-05 (divergence metrics)   [depends on WP-03]
  └── WP-06 (outcome comparison)   [depends on WP-03]

WP-07 (top-level compare)          [depends on WP-01..WP-06]
  ├── WP-08 (CLI integration)
  └── WP-09 (extension dispatch)
         └── WP-10 (System C extension)

WP-11 (synthetic tests)            [depends on implemented core]
WP-12 (persisted trace checks)     [depends on implemented core + extension]
```

---

## Execution Strategy

- `WP-01` must be done first.
- `WP-02` and `WP-03` should follow immediately.
- `WP-04`, `WP-05`, and `WP-06` can then proceed in parallel.
- `WP-07` should only start when the generic core is in place.
- `WP-08` should be done after `WP-07`.
- `WP-09` and `WP-10` should be kept separate so the extension boundary stays clean.
- `WP-11` and `WP-12` should run last.

---

## Verification

After completing all work packages:

1. The comparison package exists under `src/axis/framework/comparison/`.
2. `axis compare ...` can load two persisted episodes and return a structured comparison result.
3. Invalid pairs fail with explicit validation errors.
4. Generic metrics match the paired comparison spec.
5. A `System C` extension block can be attached without importing live system runtime classes.
