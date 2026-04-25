# System A vs. System C (Prediction Analysis)

Comparison workspace for running two systems or configurations under shared conditions.

Workspace classification: `investigation` / `system_comparison`.

Primary purpose:

- compare `system_a` as reference against `system_c` as candidate
- answer: Does Prediction for a simple Hunger Forager has a real effect?

This workspace contains:

- reference and candidate configs in `configs/`
- authoritative workspace semantics in `workspace.yaml`
- workspace-owned execution artifacts under `results/`
- numbered comparison outputs under `comparisons/`

Both scaffolded configs start with shared world and execution settings so later comparisons have a fair baseline.
