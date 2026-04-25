# System A vs. System AW

Comparison workspace for evaluating `system_aw` against `system_a` under shared conditions.

Workspace classification: `investigation` / `system_comparison`.

Primary purpose:

- compare `system_a` as the reference system against `system_aw` as the candidate
- answer: Does `system_aw` provide a measurable behavioral or performance advantage over `system_a`?

This workspace contains:

- reference and candidate configs in `configs/`
- authoritative workspace semantics in `workspace.yaml`
- workspace-owned execution artifacts under `results/`
- numbered comparison outputs under `comparisons/`
- running experiment notes and interpretation in `notes.md`

Recommended working style:

- keep world, seed, execution, and episode settings aligned unless the experiment explicitly tests a changed condition
- use `axis workspaces compare-configs .` before a run to verify the intended config delta
- run both sides with `axis workspaces run .`
- generate a numbered comparison with `axis workspaces compare .`
- record the exact config intent, run summaries, and conclusions in `notes.md`

The default expectation for this workspace is a fair side-by-side comparison: same environment, same execution budget, different system architecture.
