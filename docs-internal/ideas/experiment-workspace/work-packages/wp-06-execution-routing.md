# WP-06: Workspace Execution Routing

**Phase**: 2 -- Workspace Run  
**Dependencies**: WP-05  
**Scope**: Medium  
**Engineering reference**: Sections 4.5, 9.4

---

## Objective

Implement workspace-aware execution with result placement under `results/`.

This WP introduces the actual `run` behavior for workspaces while reusing the
existing experiment execution stack.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/execute.py`
- `tests/framework/workspaces/test_execute.py`

Modify:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

No SDK changes are expected in this WP.

---

## Required Behavior

Implement:

- `axis workspaces run <workspace-path>` as a CLI entrypoint
- delegation from CLI into `framework/workspaces/execute.py`
- use of the execution plan from WP-05
- structured placement of execution artifacts under `results/`

The CLI remains a delegator only.

The actual workspace execution logic belongs in `framework/workspaces/`.

---

## Implementation Steps

1. Define a workspace execution service in `execute.py`.
2. Reuse existing `ExperimentExecutor` and repository logic where possible.
3. Decide how workspace-owned artifacts are named and placed under `results/`.
4. Return a structured execution result to the CLI.
5. Add `workspaces` subcommands to `cli.py`, but keep CLI logic thin.

---

## Design Notes

- Do not fork a separate execution engine.
- Reuse the current experiment/run execution path and adapt artifact placement.
- Keep the existing `axis experiments run <config>` untouched.
- Artifact naming conventions can remain simple in this WP; refinement can happen later.

---

## Verification

1. `axis workspaces run <workspace-path>` can execute a `single_system` workspace.
2. Produced execution artifacts are written under the workspace `results/`.
3. The old `axis experiments run <config>` path still works unchanged.
4. CLI remains a delegator and does not contain business logic.

---

## Files Created

- `src/axis/framework/workspaces/execute.py`
- `tests/framework/workspaces/test_execute.py`

## Files Modified

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
