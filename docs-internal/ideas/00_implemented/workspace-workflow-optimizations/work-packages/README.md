# Workspace Workflow Optimizations -- Work Packages

**Spec**: [../workspace-workflow-optimizations-spec.md](../workspace-workflow-optimizations-spec.md)  
**Engineering spec**: [../workspace-workflow-optimizations-engineering-spec.md](../workspace-workflow-optimizations-engineering-spec.md)  
**Roadmap**: [../workspace-workflow-optimizations-work-packages.md](../workspace-workflow-optimizations-work-packages.md)  
**Phase**: Initial implementation pass

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|----|-------|--------------|-------|------------|
| [WP-01](wp-01-workflow-enum-and-manifest-update.md) | Workflow enum and manifest update | None | Medium | Tighten workflow enums and reject removed legacy values |
| [WP-02](wp-02-close-mutation-and-workflow-service.md) | Close mutation and workflow service | WP-01 | Medium | Add canonical manifest mutation and service support for closing workspaces |
| [WP-03](wp-03-cli-close-command-integration.md) | CLI close command integration | WP-02 | Small | Add `axis workspaces close <workspace>` with text and JSON output |
| [WP-04](wp-04-closed-workspace-enforcement.md) | Closed-workspace enforcement | WP-01, WP-02 | Medium | Block run, compare, and candidate mutation for closed workspaces |
| [WP-05](wp-05-summary-validation-and-scaffold-alignment.md) | Summary, validation, and scaffold alignment | WP-01, WP-03, WP-04 | Medium | Align read-only surfaces and scaffolding with the new workflow model |
| [WP-06](wp-06-test-hardening-fixture-migration-and-doc-touchups.md) | Test hardening, fixture migration, and doc touch-ups | WP-01 through WP-05 | Medium | Update tests, example workspaces, and workflow-facing docs/help text |

---

## Dependency Graph

```text
WP-01 (workflow enum and manifest update)
  └── WP-02 (close mutation and workflow service)
         └── WP-03 (CLI close command integration)

WP-01 + WP-02
  └── WP-04 (closed-workspace enforcement)

WP-01 + WP-03 + WP-04
  └── WP-05 (summary, validation, and scaffold alignment)

WP-01 through WP-05
  └── WP-06 (test hardening, fixture migration, and doc touch-ups)
```

---

## Execution Strategy

- `WP-01` must land first.
- `WP-02` should establish the single canonical close path before CLI wiring.
- `WP-03` should stay thin and delegate to the workflow service.
- `WP-04` should enforce closed-state policy in services, not only in CLI code.
- `WP-05` should align inspection and scaffolding after the actual behavior is
  in place.
- `WP-06` should update real workspace fixtures and explicitly test failure on
  removed legacy values.

---

## Architectural Rule

The workspace manifest remains authoritative.

Primary workflow logic belongs under:

- `src/axis/framework/workspaces/`

The CLI remains a delegating surface:

- parse arguments
- call services
- render results

The implementation bias for this phase is:

> explicit built-in workflow semantics, no silent legacy mapping, and service-
> layer enforcement for closed workspaces
