# Experiment Workspace -- Work Packages

**Spec**: [../experiment-workspace-spec.md](../experiment-workspace-spec.md)  
**Engineering spec**: [../experiment-workspace-engineering-spec.md](../experiment-workspace-engineering-spec.md)  
**Roadmap**: [../experiment-workspace-work-packages.md](../experiment-workspace-work-packages.md)  
**Phase**: Initial implementation pass

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|----|-------|--------------|-------|------------|
| [WP-01](wp-01-manifest-model.md) | Workspace manifest model | None | Medium | Create typed `workspace.yaml` representation under `framework/workspaces` |
| [WP-02](wp-02-workspace-checker.md) | Workspace checker | WP-01 | Medium | Structural and semantic workspace validation |
| [WP-03](wp-03-workspace-scaffolder.md) | Workspace scaffolder | WP-01 | Medium | Interactive creation of valid workspaces |
| [WP-04](wp-04-workspace-show.md) | Workspace show/summary | WP-01, WP-02 | Small | Human-readable workspace inspection |
| [WP-05](wp-05-run-resolution.md) | Workspace run resolution | WP-01 | Medium | Resolve executable configs from `workspace.yaml` |
| [WP-06](wp-06-execution-routing.md) | Workspace execution routing | WP-05 | Medium | Add `axis workspaces run` with result placement under `results/` |
| [WP-07](wp-07-visualization-resolution.md) | Workspace visualization resolution | WP-01, WP-06 | Small | Resolve replay targets for `axis visualize --workspace ...` |
| [WP-08](wp-08-compare-resolution.md) | Workspace compare resolution | WP-01, WP-06 | Medium | Resolve comparison targets from workspace state |
| [WP-09](wp-09-comparison-routing.md) | Workspace comparison routing | WP-08 | Medium | Add `axis workspaces compare` with output placement under `comparisons/` |
| [WP-10](wp-10-manifest-synchronization.md) | Manifest synchronization | WP-06, WP-09 | Medium | Keep `workspace.yaml` aligned with produced artifacts |
| [WP-11](wp-11-drift-detection.md) | Drift detection and stronger consistency | WP-02, WP-10 | Medium | Detect stale or undeclared workspace artifacts |
| [WP-12](wp-12-integration-hardening.md) | Integration hardening | WP-01 through WP-11 | Medium | End-to-end CLI, persistence, and compatibility checks |
| [WP-13](wp-13-public-docs.md) | Public docs and examples | WP-12 | Small | Publish stable user-facing workspace guidance |

---

## Dependency Graph

```text
WP-01 (manifest model)
  ├── WP-02 (workspace checker)
  ├── WP-03 (workspace scaffolder)
  ├── WP-04 (workspace show)           [depends on WP-02]
  └── WP-05 (run resolution)

WP-05 (run resolution)
  └── WP-06 (execution routing)
         ├── WP-07 (visualization resolution)
         └── WP-08 (compare resolution)
                └── WP-09 (comparison routing)

WP-06 + WP-09
  └── WP-10 (manifest synchronization)
         └── WP-11 (drift detection)

WP-12 (integration hardening)          [depends on implemented core]
  └── WP-13 (public docs)
```

---

## Execution Strategy

- `WP-01` must be done first.
- `WP-02`, `WP-03`, and `WP-05` can start after `WP-01`.
- `WP-04` should follow once manifest loading and checking exist.
- `WP-06` should only start when run resolution is stable.
- `WP-07` should reuse existing visualization loading paths rather than inventing a new replay model.
- `WP-08` and `WP-09` should build directly on the existing comparison package, not reimplement it.
- `WP-10` should start only after real artifacts are written into workspaces.
- `WP-11` should be kept separate so basic workspace behavior can land before stronger drift semantics.
- `WP-12` and `WP-13` should remain late.

---

## Architectural Rule

The `axis` CLI remains a delegating entrypoint.

Primary logic belongs under:

- `src/axis/framework/workspaces/`

SDK additions should be introduced only if a true reusable public contract is
required. The default implementation bias for this phase is:

> framework-first, SDK-minimal

---

## Verification

After completing all work packages:

1. AXIS can scaffold a valid workspace via `axis workspaces scaffold`.
2. AXIS can validate and summarize a workspace via `check` and `show`.
3. AXIS can execute a workspace into `results/` via `axis workspaces run`.
4. AXIS can compute a workspace comparison into `comparisons/` via `axis workspaces compare`.
5. `workspace.yaml` remains authoritative and is kept aligned with produced artifacts.
