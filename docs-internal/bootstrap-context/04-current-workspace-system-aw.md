# Current Context: `system_aw` Workspace

## Active Workspace

Current active workspace observed during context generation:

- `workspaces/system_aw-baseline/`

Manifest file:

- `workspaces/system_aw-baseline/workspace.yaml`

Current manifest interpretation:

- workspace class: `investigation`
- workspace type: `single_system`
- system under test: `system_aw`
- stated question: "Simply debug the System A+W"
- lifecycle stage: `documentation`
- status: `running`

This means the current work is not a two-system comparison workspace. It is a
single-system investigation container focused on understanding and debugging
`system_aw`.

## Current Config Under Focus

Config file:

- `workspaces/system_aw-baseline/configs/system_aw-baseline.yaml`

Observed setup:

- `system_type: system_aw`
- `experiment_type: single_run`
- seed: `7`
- max steps: `200`
- world type: `grid_2d`
- world size: `20x20`
- obstacle density: `0.05`
- regeneration mode: `sparse_fixed_ratio`
- regeneration eligible ratio: `0.10`
- agent start position: `(10, 10)`
- episodes per run: `5`

System profile in this config:

- selection mode: `argmax`
- high temperature parameter set to `10.0`
- curiosity enabled
- relatively strong curiosity/world-model emphasis
- arbitration configured to let curiosity dominate more when hunger is low

Practical interpretation:

- this is an exploration-oriented `system_aw` setup, not a strict apples-to-
  apples baseline against `system_a`
- behavior questions will likely center on curiosity, novelty, arbitration,
  and world-model updates

## Relevant System Files

When debugging `system_aw`, start here:

- `src/axis/systems/system_aw/system.py`
- `src/axis/systems/system_aw/transition.py`
- `src/axis/systems/system_aw/config.py`
- `src/axis/systems/system_aw/types.py`

Then inspect the construction-kit pieces it composes:

- `src/axis/systems/construction_kit/drives/curiosity.py`
- `src/axis/systems/construction_kit/drives/hunger.py`
- `src/axis/systems/construction_kit/arbitration/`
- `src/axis/systems/construction_kit/memory/world_model.py`
- `src/axis/systems/construction_kit/policy/softmax.py`
- `src/axis/systems/construction_kit/observation/sensor.py`

## Relevant Docs

Most relevant public docs:

- `docs/manuals/system-aw-manual.md`
- `docs/manuals/workspace-manual.md`
- `docs/manuals/visualization-manual.md`

Most relevant internal docs:

- `docs-internal/system-design/system-a+w/`
- `docs-internal/system-design/system-a+w/work-packages/`

## Current Result State

The workspace manifest already records multiple `primary_results` entries
under `workspaces/system_aw-baseline/results/`.

Practical implication:

- this workspace has already been used iteratively
- future sessions should check whether the newest result reflects the current
  config before drawing conclusions
- if behavior appears surprising, compare the latest run with earlier results
  rather than assuming a single clean baseline

## Suggested Fresh-Session Prompting Strategy

When opening a fresh agentic session for this workspace, provide:

1. this file
2. `01-solution-overview.md`
3. the active `workspace.yaml`
4. the active `system_aw` config

Then tell the agent whether the task is one of:

- architecture understanding
- debugging system behavior
- tracing curiosity/world-model logic
- validating workspace execution/comparison behavior
- interpreting replay visualization output

That should usually be enough to avoid a full repository rediscovery pass.
