# CLI Output Review Engineering Spec

## 1. Purpose

This engineering specification translates the CLI presentation goals described
in:

- [CLI Output Review Draft](./cli_output_review.md)
- [CLI Output Review Specification](./cli-output-review-spec.md)

into a practical implementation direction for the current AXIS CLI codebase.

The goal is to introduce a small shared text-rendering layer for human-facing
terminal output, then migrate high-value command surfaces onto it without
disrupting JSON output or underlying domain behavior.


## 2. Implementation Goal

The AXIS framework should gain a normalized internal CLI output layer for
human-oriented terminal presentation.

The first wave should provide:

- shared semantic rendering helpers for text mode
- centralized text-mode error framing
- normalized command output templates for list, detail, completion, and
  validation views
- optional conservative ANSI styling for interactive terminals
- a later aligned cleanup of runtime episode logging

This should be treated as a presentation refactor rather than a command
semantics refactor.


## 3. Architectural Placement

### 3.1 New CLI output module

The normalized text-mode rendering layer should be introduced under:

- `src/axis/framework/cli/output.py`

This module should remain internal to the framework CLI layer in the first
wave.

### 3.2 Responsibilities of `output.py`

The module should contain:

- semantic output helpers for text mode
- optional ANSI-style helpers or a small style policy
- rendering helpers for:
  - title lines
  - section headings
  - field rows
  - list rows
  - status lines
  - hints
- TTY-aware styling decisions

The module should **not** contain:

- business logic for experiments, runs, comparisons, or workspaces
- repository IO
- CLI argument parsing
- JSON output rendering logic

### 3.3 Optional supporting split

If `output.py` becomes too dense, a small internal split may be introduced:

- `src/axis/framework/cli/output.py`
- `src/axis/framework/cli/output_styles.py`

This split should only be introduced if it materially improves clarity.


## 4. Existing Code Areas Affected

Based on the current codebase, the first wave will affect at least:

### 4.1 CLI dispatch and top-level failure handling

- `src/axis/framework/cli/dispatch.py`

### 4.2 Command modules with dense text-mode formatting

- `src/axis/framework/cli/commands/compare.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`

### 4.3 Lower-priority command modules

- `src/axis/framework/cli/commands/visualize.py`

### 4.4 Parser help text

- `src/axis/framework/cli/parser.py`

### 4.5 Runtime episode logging

- `src/axis/framework/logging.py`

### 4.6 Possibly related terminal-facing behavior

- `src/axis/plugins.py`

Plugin discovery logging should not be forced into the CLI rendering layer in
the first wave, but terminal-facing interactions here should be kept in mind
when evaluating output consistency.


## 5. Current Implementation Constraints

The existing CLI already has several constraints that should be preserved.

### 5.1 JSON output stability

The current `json` mode is already serviceable and should remain unchanged
unless a separate semantic need is identified.

### 5.2 Command-local formatting

Many current commands format text directly via `print(...)`.

The first migration should reduce duplication, but should not attempt a risky
full rewrite in one pass.

### 5.3 Conservative dependency posture

The CLI currently uses `rich` only in workspace scaffolding.

The output refactor should not require a broad redesign around `rich`.

The first shared layer should work with plain text and optional ANSI styling,
even if selected commands continue to use `rich` opportunistically.


## 6. New Internal Presentation Model

### 6.1 Rendering context

The first wave should introduce a lightweight CLI text rendering context.

This may be a small class or a collection of stateless helpers.

Possible shape:

- `CLITextOutput`

Its responsibilities may include:

- whether styling is enabled
- whether the current stream is interactive
- how semantic prefixes and headings are rendered

### 6.2 Minimum helper surface

The shared layer should provide helpers equivalent to:

- `print_title(...)`
- `print_section(...)`
- `print_kv(...)`
- `print_info(...)`
- `print_success(...)`
- `print_warning(...)`
- `print_error(...)`
- `print_hint(...)`
- `print_list_row(...)`

The exact function names may differ, but the semantic surface should remain
small and stable.

### 6.3 Rendering policy

The rendering layer should define:

- default indentation rules
- default blank-line rules between sections
- status-prefix wording
- optional style mapping


## 7. Centralized Error Framing

### 7.1 Top-level dispatch

`dispatch.py` currently falls back to:

- `print(f"Error: {exc}", file=sys.stderr)`

This should be replaced with shared error framing from the CLI output layer.

### 7.2 Command-level errors

Command modules should gradually stop duplicating raw stderr formatting where a
shared framing helper is appropriate.

This does not require removing all `SystemExit`-based control flow in the
first wave, but it does require normalizing the text presentation of errors.

### 7.3 Hint support

The shared error path should support an optional next-step hint for clear
operational failures.


## 8. Command Migration Strategy

The migration should proceed by highest value and lowest conceptual risk.

### 8.1 Phase 1: Shared output foundation

Add the shared CLI output module and migrate the top-level error path first.

Scope:

- add `src/axis/framework/cli/output.py`
- define semantic helpers
- add plain-text-first rendering behavior
- add optional TTY-sensitive styling policy
- update `dispatch.py` to use shared error framing

### 8.2 Phase 2: Comparison output normalization

Refactor:

- `src/axis/framework/cli/commands/compare.py`

Why first:

- it is the densest formatter
- it already contains natural section boundaries
- it has the highest payoff for structural cleanup

Goals:

- title / identity block
- validation block
- per-episode block
- statistical summary block
- fewer fragile sequential prints

### 8.3 Phase 3: Workspace inspection and validation normalization

Refactor:

- `src/axis/framework/cli/commands/workspaces.py`

Priority surfaces:

- `workspaces show`
- `workspaces check`
- `workspaces comparison-result`
- `workspaces sweep-result`
- completion messages from workspace mutations

Goals:

- clearer overview-first layout
- grouped validation and drift findings
- consistent artifact section rendering
- normalized success messages

### 8.4 Phase 4: Experiment and run command normalization

Refactor:

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`

Goals:

- consistent list row layout
- consistent detail command title + metadata structure
- normalized completion/result messaging

### 8.5 Phase 5: Help and lower-priority surfaces

Refine:

- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/commands/visualize.py`

Goals:

- remove duplicated help examples
- improve text grouping where easy
- align remaining human-visible command output

### 8.6 Phase 6: Runtime logging alignment

Refactor:

- `src/axis/framework/logging.py`

Goals:

- keep compact step prefixes
- add clearer episode boundaries
- render verbose decision / transition payloads as structured multi-line text
  instead of dense one-line JSON dumps


## 9. Command Output Contracts

To avoid style drift, the first wave should define explicit command-level
contracts for text rendering.

### 9.1 List contract

A list command should provide the renderer with:

- optional title
- iterable item rows
- item status where applicable
- one or two normalized qualifiers

### 9.2 Detail contract

A detail command should provide:

- object title
- primary metadata rows
- optional grouped sections

### 9.3 Validation contract

A validation command should provide:

- object title or identity
- validation state
- grouped findings
- grouped drift findings when applicable

### 9.4 Completion contract

A completion command should provide:

- completed action headline
- key artifact identifiers or paths

These contracts may initially be informal helper call patterns rather than
strict typed models.


## 10. Data Shaping vs Rendering

The migration should aim to separate data shaping from rendering wherever
practical.

That means command modules should increasingly follow this pattern:

1. resolve domain data
2. shape a small renderable view
3. hand that view to shared output helpers

The first wave does not require introducing a full presenter layer for every
command, but new formatting work should avoid embedding complex layout logic
deeply inside business flow.


## 11. Styling Policy

### 11.1 Styling principle

Styling should remain optional and conservative.

### 11.2 Activation

Styling should be enabled only when output is directed to an interactive
terminal and not explicitly disabled.

### 11.3 Scope of styling

The first styling pass should affect only:

- semantic prefixes
- headings
- title labels

It should not color entire paragraphs or large result blocks.

### 11.4 Non-interactive output

Redirected or piped output must remain readable and stable without color.


## 12. Runtime Logging Engineering Direction

The runtime logger in `src/axis/framework/logging.py` should remain separate
from command-level rendering helpers, but should adopt compatible principles.

The first cleanup should:

- preserve the existing step prefix contract
- add explicit episode-start or episode-boundary lines if helpful
- replace verbose inline JSON dumps with indented, labeled multi-line blocks

This work is lower priority than command-level CLI normalization and should
follow only after the shared text-output layer is stable.


## 13. Testing Strategy

The output refactor should be validated with focused text-mode tests.

### 13.1 Shared output helper tests

Add tests for:

- plain text rendering
- optional style-disabled behavior
- section and field formatting
- semantic error formatting

### 13.2 Command snapshot-style tests

Add or update tests for representative command output in text mode:

- compare
- workspace show
- workspace check
- experiments list / show
- runs list / show

### 13.3 JSON regression tests

Confirm that JSON mode remains unchanged for migrated commands.

### 13.4 Logging tests

When runtime logging is migrated, add focused tests for:

- compact step output
- verbose structured output
- JSONL behavior remaining unchanged


## 14. Risks And Mitigations

### 14.1 Risk: presentation refactor bleeds into behavior refactor

Mitigation:

- keep JSON unchanged
- avoid changing repository or comparison semantics
- migrate one command family at a time

### 14.2 Risk: styling introduces noisy or brittle output

Mitigation:

- make styling optional
- keep semantic prefixes in plain text
- test non-interactive output explicitly

### 14.3 Risk: helper layer becomes too abstract too early

Mitigation:

- start with a very small helper surface
- grow only when repeated rendering patterns justify it

### 14.4 Risk: command modules keep bypassing the shared layer

Mitigation:

- centralize top-level error framing first
- migrate the highest-traffic command surfaces early
- treat new text output changes as required to use the shared layer


## 15. Recommended Delivery Sequence

The first coarse delivery sequence should be:

1. shared CLI output helper layer
2. centralized error framing
3. comparison output migration
4. workspace output migration
5. experiment and run output migration
6. parser/help cleanup
7. optional styling pass
8. runtime logging cleanup

This ordering preserves low-risk structural gains before cosmetic polish.


## 16. Expected First-Wave Outcome

After the first implementation wave:

- AXIS text-mode CLI output should feel like one coherent interface rather
  than a collection of unrelated command-local print styles
- the highest-density commands should become significantly easier to scan
- stderr errors should present consistently
- JSON output should remain stable
- future CLI enhancements should have a clear presentation layer to build on
