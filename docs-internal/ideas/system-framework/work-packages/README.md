# System Construction Kit -- Phase 1 Work Packages

**Spec**: [system-construction-kit-spec.md](../system-construction-kit-spec.md)
**Phase**: 1 -- Foundation (pure structural refactoring, no behavioral change)

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|----|-------|-------------- |-------|------------|
| [WP-01](wp-01-package-skeleton.md) | Package skeleton | None | Small | Create directory structure |
| [WP-02](wp-02-observation.md) | Observation types and sensor | WP-01 | Medium | Move CellObservation, Observation, VonNeumannSensor |
| [WP-03](wp-03-memory.md) | Observation buffer | WP-01, WP-02 | Small | Move BufferEntry, ObservationBuffer, update fn |
| [WP-04](wp-04-energy.md) | Energy utilities | WP-01 | Small | Move clip_energy, add new utility fns |
| [WP-05](wp-05-hunger-drive.md) | Hunger drive | WP-01, WP-02 | Small | Move HungerDriveOutput, HungerDrive |
| [WP-06](wp-06-softmax-policy.md) | Softmax policy | WP-01, WP-02 | Medium | Move + generalize policy interface |
| [WP-07](wp-07-arbitration.md) | Drive arbitration | WP-01 | Medium | Move + generalize to N-drive |
| [WP-08](wp-08-curiosity-types.md) | Curiosity drive and spatial world model | WP-01, WP-02, WP-03 | Medium | Move CuriosityDrive, WorldModelState, world model fns |
| [WP-09](wp-09-shared-config-actions.md) | Shared config types and consume action | WP-01 | Medium | Move AgentConfig, PolicyConfig, TransitionConfig, handle_consume |
| [WP-10](wp-10-dependency-constraints.md) | Dependency constraint tests | WP-01 through WP-09 | Small | Automated import boundary tests |

## Dependency Graph

```text
WP-01 (skeleton)
  ├── WP-02 (observation)
  │     ├── WP-03 (memory)        [depends on observation types]
  │     │     └── WP-08 (curiosity drive) [depends on memory + observation]
  │     ├── WP-05 (hunger drive)  [depends on observation types]
  │     └── WP-06 (policy)        [depends on observation types]
  ├── WP-04 (energy)              [independent]
  ├── WP-07 (arbitration)         [independent]
  └── WP-09 (config + actions)    [independent]

WP-10 (constraints)               [depends on all above]
```

## Execution Strategy

- WP-01 must be done first.
- WP-02 should be done second (many WPs depend on it).
- WP-04, WP-07, WP-09 can run in parallel (independent of WP-02).
- WP-03, WP-05, WP-06 can run in parallel after WP-02.
- WP-08 can run after WP-03 (depends on memory types).
- WP-10 runs last after all extractions are complete.

## Verification

After completing all Phase 1 work packages:

1. `python -m pytest tests/ -x` -- all 1814 tests must pass
2. `grep -r "from axis.systems.system_a" src/axis/systems/system_aw/` -- must return zero hits
3. `grep -r "from axis.systems.system_a" src/axis/systems/system_b/` -- must return zero hits (already the case)
4. No changes to `src/axis/framework/`, `src/axis/sdk/`, or `src/axis/world/`
