# CLI Output Review Work Packages

## Purpose

This document defines a first coarse-grained implementation roadmap for the
CLI output review effort.

It is derived from:

- `cli-output-review-spec.md`
- `cli-output-review-engineering-spec.md`

The goal of this document is not to fully specify implementation details.

The goal is to define a pragmatic delivery structure that can later be
executed by human contributors or coding agents in bounded packages.

---

## 1. Implementation Goal

The first implementation goal is:

> introduce a shared, conservative, human-oriented CLI presentation layer for
> AXIS without disrupting existing command semantics or JSON output

This means:

- text-mode output becomes more consistent across command families
- JSON output remains stable
- the CLI gains a shared rendering layer instead of ad hoc print formatting
- high-density commands become easier to scan
- terminal polish remains subordinate to structural clarity

---

## 2. Delivery Strategy

The recommended delivery strategy is incremental.

Do not attempt to rewrite all CLI output in one pass.

Instead, introduce the new presentation layer in stages:

1. shared text-output foundation
2. top-level error normalization
3. comparison command migration
4. workspace command migration
5. experiments and runs migration
6. parser/help cleanup
7. optional styling and runtime logging alignment
8. hardening and regression coverage

This keeps early implementation risk low while ensuring that each stage
produces visible user-facing improvement.

---

## 3. Proposed Work Package Structure

### WP-01 Shared CLI Output Foundation

Implement the shared human-oriented text rendering layer.

Primary scope:

- new `src/axis/framework/cli/output.py`
- semantic text helpers
- indentation and section rules
- plain-text-first rendering behavior
- optional TTY-aware style policy hooks

Primary outcome:

- command modules have a single place to obtain normalized text-mode helpers

---

### WP-02 Error Framing And Dispatch Integration

Normalize user-facing stderr error presentation.

Primary scope:

- centralize top-level error framing in `dispatch.py`
- define shared error and hint helpers
- reduce duplicated raw stderr prints where practical

Primary outcome:

- AXIS errors present consistently in text mode

---

### WP-03 Comparison Output Normalization

Refactor the comparison command onto the shared output layer.

Primary scope:

- `compare.py` text rendering cleanup
- identity block
- validation block
- per-episode results block
- summary block

Primary outcome:

- `axis compare ...` becomes the first major command family on the new output
  model

---

### WP-04 Workspace Output Normalization

Refactor workspace inspection and validation output.

Primary scope:

- `workspaces show`
- `workspaces check`
- `workspaces comparison-result`
- `workspaces sweep-result`
- workspace success/completion messaging

Primary outcome:

- workspace surfaces adopt overview-first, sectioned output

---

### WP-05 Experiments And Runs Output Normalization

Refactor experiment and run inspection output.

Primary scope:

- `experiments list`
- `experiments show`
- `experiments run`
- `experiments resume`
- `runs list`
- `runs show`

Primary outcome:

- experiment and run commands follow the same list/detail/completion patterns

---

### WP-06 Parser Help And Remaining CLI Surface Cleanup

Clean up lower-priority terminal-facing surfaces.

Primary scope:

- parser help text cleanup
- duplicate example removal
- grouping improvements where feasible
- alignment of any remaining direct text outputs

Primary outcome:

- help output and secondary command surfaces no longer feel stylistically
  separate from the main CLI

---

### WP-07 Optional Styling And Runtime Logging Alignment

Add conservative semantic styling and align runtime logging later.

Primary scope:

- optional ANSI styling for labels, prefixes, and headings
- non-interactive fallback behavior
- runtime `EpisodeLogger` verbose output cleanup
- clearer episode boundaries where useful

Primary outcome:

- interactive terminal use gains polish without sacrificing portability

---

### WP-08 Test Hardening And Regression Coverage

Add focused tests and protect JSON stability.

Primary scope:

- shared output helper tests
- representative command text-output tests
- JSON regression tests
- runtime logging tests if WP-07 lands

Primary outcome:

- the new presentation layer becomes safe to evolve

---

## 4. Suggested Execution Order

The recommended order is:

1. `WP-01`
2. `WP-02`
3. `WP-03`
4. `WP-04`
5. `WP-05`
6. `WP-06`
7. `WP-07`
8. `WP-08`

`WP-08` should begin partially earlier if tests are added alongside each
package, but it should still exist as a distinct hardening pass.

---

## 5. Delivery Principle

The CLI output review effort should remain:

- presentation-focused
- command-semantics-preserving
- JSON-safe
- incrementally adoptable

The rendering layer should support command modules.

It should not become a second business-logic layer.

