# CLI Output Review -- Work Packages

**Spec**: [../cli-output-review-spec.md](../cli-output-review-spec.md)  
**Engineering spec**: [../cli-output-review-engineering-spec.md](../cli-output-review-engineering-spec.md)  
**Roadmap**: [../cli-output-review-work-packages.md](../cli-output-review-work-packages.md)  
**Phase**: Initial implementation pass

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|----|-------|--------------|-------|------------|
| [WP-01](wp-01-shared-cli-output-foundation.md) | Shared CLI output foundation | None | Medium | Add `framework/cli/output.py` with semantic text rendering helpers |
| [WP-02](wp-02-error-framing-and-dispatch.md) | Error framing and dispatch integration | WP-01 | Small | Centralize stderr error presentation and shared hint/error rendering |
| [WP-03](wp-03-comparison-output-normalization.md) | Comparison output normalization | WP-01, WP-02 | Medium | Refactor `compare.py` onto normalized text-mode sections |
| [WP-04](wp-04-workspace-output-normalization.md) | Workspace output normalization | WP-01, WP-02 | Medium | Refactor workspace show/check/result surfaces onto the new output layer |
| [WP-05](wp-05-experiments-and-runs-output-normalization.md) | Experiments and runs output normalization | WP-01, WP-02 | Medium | Normalize list/detail/completion output for experiments and runs |
| [WP-06](wp-06-parser-help-and-surface-cleanup.md) | Parser help and remaining surface cleanup | WP-03, WP-04, WP-05 | Small | Improve help text and align remaining terminal-facing outputs |
| [WP-07](wp-07-optional-styling-and-runtime-logging.md) | Optional styling and runtime logging alignment | WP-03, WP-04, WP-05 | Medium | Add conservative ANSI styling and improve verbose episode logging |
| [WP-08](wp-08-test-hardening-and-regression.md) | Test hardening and regression coverage | WP-01 through WP-07 | Medium | Protect text output behavior and confirm JSON remains unchanged |

---

## Dependency Graph

```text
WP-01 (shared output foundation)
  └── WP-02 (error framing)
         ├── WP-03 (comparison output)
         ├── WP-04 (workspace output)
         └── WP-05 (experiments and runs output)

WP-03 + WP-04 + WP-05
  ├── WP-06 (help and remaining surfaces)
  └── WP-07 (optional styling and runtime logging)

WP-01 through WP-07
  └── WP-08 (test hardening and regression)
```

---

## Execution Strategy

- `WP-01` must be done first.
- `WP-02` should land immediately after the shared output layer exists.
- `WP-03`, `WP-04`, and `WP-05` can proceed in parallel once `WP-02` is stable.
- `WP-03` is the best first command migration because it has the densest formatting and clearest section structure.
- `WP-04` should emphasize overview-first output rather than raw field dumping.
- `WP-05` should standardize list rows before adding cosmetic styling.
- `WP-06` should stay late, after the main command families have converged.
- `WP-07` should not land before the structural normalization in `WP-03` through `WP-05`.
- `WP-08` should collect the remaining regression gaps and explicitly protect JSON mode.

---

## Architectural Rule

The `axis` CLI remains a delegating entrypoint.

Primary logic belongs under:

- `src/axis/framework/cli/`

The new presentation layer should remain lightweight and internal to the CLI.

The default implementation bias for this phase is:

> shared rendering helpers, minimal abstraction, no business-logic migration

---

## Verification

After completing all work packages:

1. AXIS text-mode output for core commands feels like one coherent interface.
2. Errors and validation states present consistently in stderr/stdout text mode.
3. Comparison and workspace outputs are clearly sectioned and easier to scan.
4. Experiments and runs use normalized list/detail/completion layouts.
5. JSON output remains unchanged for migrated command families.
6. Optional styling, if enabled, remains conservative and non-essential.

