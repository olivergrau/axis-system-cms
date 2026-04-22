# CLI Output Review

## Scope

This document reviews the current terminal-facing output of the AXIS CLI and
related runtime console logging.

It is an analysis/specification document only.

No implementation changes are proposed here beyond design guidance and
prioritized recommendations.

## Short Assessment

The current CLI output is functional, portable, and technically conservative,
but it is also visually flat, inconsistent across commands, and only weakly
structured for scanning in an interactive terminal.

The output style is currently dominated by raw `print(...)` calls with ad hoc
indentation and formatting choices per command. JSON output paths are generally
fine, but text output lacks a shared presentation layer, so command families
look related only in content, not in structure.

The result is an interface that:

- works reliably
- is easy to pipe and test
- but feels uneven and older than the underlying feature set

The main opportunity is not to add “fancy terminal UI”, but to introduce a
small, consistent, restrained output system with clear semantic structure.

## Relevant CLI Entry Points

Primary CLI surface:

- `src/axis/framework/cli/__init__.py`
- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/dispatch.py`

Command modules:

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`
- `src/axis/framework/cli/commands/compare.py`
- `src/axis/framework/cli/commands/visualize.py`
- `src/axis/framework/cli/commands/workspaces.py`

Related terminal/runtime output:

- `src/axis/framework/logging.py`
- `src/axis/plugins.py`

## Quick Inventory Of Output Mechanisms

### 1. Raw `print(...)` text output

This is the dominant pattern across the CLI.

Approximate direct `print(...)` hotspots:

- `workspaces.py`: 68
- `compare.py`: 54
- `experiments.py`: 29
- `runs.py`: 18
- `logging.py`: 4
- `visualize.py`: 1
- `dispatch.py`: 1

Observation:

- the CLI is already large enough that output formatting is effectively a
  shared concern, but it is still implemented command-by-command

### 2. Direct stderr error output

Current error reporting uses:

- `print(..., file=sys.stderr)`
- `sys.exit(1)`
- top-level fallback in `dispatch.py`:
  `print(f"Error: {exc}", file=sys.stderr)`

Observation:

- error handling is semantically correct
- but formatting is duplicated and inconsistent in where it is performed

### 3. `rich` used only in workspace scaffolding

`workspaces scaffold` uses:

- `rich.console.Console`
- minimal bold/green output

Observation:

- there is already a precedent for styled terminal output
- but it is isolated to one interactive command and not reused elsewhere

### 4. Runtime episode logging

`src/axis/framework/logging.py` emits step/episode lines like:

- `[E1 S000] action=... pos=(...)->(...) vitality=...`
- `[E1 DONE] steps=... terminated=...`

Observation:

- this is compact and relatively scan-friendly
- but it is stylistically disconnected from the rest of the CLI
- verbose mode dumps raw JSON blobs inline, which is dense and noisy

### 5. Python logging for plugin discovery

`src/axis/plugins.py` uses `logger.warning(...)` and `logger.debug(...)`.

Observation:

- this is appropriate for library-level internals
- but it means terminal-facing behavior here depends on global logging
  configuration rather than the CLI output conventions

## Categorized Inventory Of Current Output Styles And Issues

## A. Listing Output

Examples:

- `experiments list`
- `runs list`
- workspace comparison listings

Current style:

- one-line records assembled with `"  ".join(parts)`
- inline `key=value` fragments

Strengths:

- compact
- pipe-friendly
- easy to test

Problems:

- inconsistent field ordering across commands
- no shared header row or section title
- visually flat when many items are listed
- mixed prose and key-value output in the same command family
- low scannability once lines become long

Example problem:

- list commands often omit a clear leading noun or status marker, so the eye
  has to parse each line from scratch

## B. Detail / Show Output

Examples:

- `experiments show`
- `runs show`
- `workspaces show`
- `workspaces comparison-result`
- `workspaces sweep-result`

Current style:

- top label line such as `Experiment: ...` or `Workspace: ...`
- indented child lines
- occasional mini-sections like `--- Per-episode results ---`

Strengths:

- generally understandable
- indentation gives some structure

Problems:

- sectioning is inconsistent across commands
- headings vary between plain labels and ad hoc dashed separators
- no semantic distinction between metadata, warnings, summary, and details
- long outputs become dense blocks of left-aligned text
- repeated field/value lines are readable but visually monotonous

Specific issue in `workspaces show`:

- output is informative, but very long for richer workspaces
- artifact sections are useful, but visually similar to identity metadata
- no strong “overview vs details” split

## C. Success Output

Examples:

- `Experiment completed.`
- `Workspace execution completed: ...`
- `Workspace comparison #... completed.`
- `Candidate config set: ...`

Strengths:

- explicit, short, readable

Problems:

- success messaging vocabulary is inconsistent
- some commands show a noun-first summary, others a sentence
- no consistent success prefix or summary block pattern
- some commands feel terse to the point of being visually under-signaled

## D. Error Output

Examples:

- `Error: Config file not found: ...`
- `Error: Experiment not found: ...`
- `Error: No comparison results found.`

Strengths:

- clear enough
- exit behavior is correct
- stderr separation exists

Problems:

- formatting is duplicated in many files
- there is no distinction between user input errors, missing data, validation
  failures, and internal execution errors
- errors are often one-line only, even when the user would benefit from the
  next action
- some command modules print their own errors and exit, while others rely on
  the top-level dispatcher

Net effect:

- semantically “error” is present
- diagnostically and visually it is underdeveloped

## E. Validation / Diagnostic Output

Examples:

- `workspaces check`
- comparison validation failures
- unchanged-config guard in workspace run

Strengths:

- problems are reported directly
- some messages already carry good domain meaning

Problems:

- severity markers are plain text only
- output format differs substantially by command
- validation output is not normalized into a shared pattern like:
  summary line + grouped findings

## F. Compare Output

`compare.py` is the densest formatter in the CLI.

Strengths:

- rich content
- semantic grouping exists
- good domain detail

Problems:

- many sequential `print(...)` calls make structure fragile
- explanatory paragraphs are mixed inline with metrics
- dashed pseudo-section markers are inconsistent with other commands
- per-episode and statistical sections are readable but verbose and visually
  heavy
- validation failures and successful comparisons do not share a normalized
  output frame

This module is one of the highest-value targets for output cleanup.

## G. Parser Help / CLI Help

Current parser help is default `argparse` with a custom epilog.

Strengths:

- portable
- familiar

Problems:

- the help text is functional but visually unrefined
- duplicate example line:
  `axis experiments run config.yaml` appears twice
- command families are not visually grouped beyond argparse defaults
- long help strings are fine semantically but not especially elegant

## H. Runtime Logging Output

`EpisodeLogger` is a separate output mode from the command-level CLI.

Strengths:

- compact step prefix
- stable line-oriented format
- JSONL separation is good

Problems:

- verbose mode prints full JSON blobs inline, which quickly becomes noisy
- no consistent semantic style shared with command output
- step and episode lines are compact, but not sectioned for multi-episode runs

## Overall Quality By Criterion

### Readability

Moderate.

The content is understandable, but many outputs are text-dense and visually
flat.

### Visual hierarchy

Weak to moderate.

Some commands use indentation or dashed section lines, but there is no
consistent hierarchy system.

### Consistency

Weak.

Patterns differ noticeably between commands:

- sentence-style success output
- key-value lists
- pseudo-sections with dashes
- inline list records
- isolated use of `rich`

### Semantic clarity

Moderate.

The domain terms are generally strong, but semantic output categories are not
consistently encoded in presentation.

### Spacing and indentation

Moderate.

Mostly acceptable, but uneven. Some commands breathe well; others stack too
many similar lines with no visual reset.

### Distinction between info / success / warning / error / debug / result

Weak.

The text content carries the distinction, but the presentation mostly does not.

### Suitability for interactive terminal usage

Moderate.

The CLI is usable, but not optimized for quick scanning during repeated
engineering workflows.

## Concrete Improvement Proposals

## 1. Introduce a shared text rendering layer

Create a small internal output helper module for text mode.

It should provide restrained helpers such as:

- `print_error(...)`
- `print_warning(...)`
- `print_success(...)`
- `print_info(...)`
- `print_section(title)`
- `print_kv(label, value, indent=2)`
- `print_list_item(...)`
- `print_metric_row(...)`

Why:

- removes duplicated formatting
- centralizes semantic prefixes and optional ANSI styling
- makes future styling changes low-risk

## 2. Normalize command output frames

Each text-mode command should follow one of a few templates.

Suggested templates:

### List command

- optional section heading
- short summary line
- uniform item rows

### Show/detail command

- title line
- metadata block
- optional summary block
- optional sections for artifacts/details

### Completion command

- one-line success headline
- short result block with IDs/counts/paths

### Validation/error command

- one-line error headline
- optional reason lines
- optional next-step hint

## 3. Standardize status prefixes and semantic wording

Current wording is good enough, but should be normalized.

Examples:

- success: `Success:` or `Completed:`
- warning: `Warning:`
- error: `Error:`
- info: `Info:`

For text-only mode without color, prefixes alone should still communicate
meaning.

## 4. Apply conservative ANSI styling optionally in text mode

Do not redesign around color; color should reinforce existing structure.

Conservative mapping:

- success = bold green prefix/headline
- warning = bold yellow prefix/headline
- error = bold red prefix/headline
- info = bold blue or cyan prefix/headline
- secondary/debug = neutral or dim

Important:

- color should be applied mainly to labels/prefixes/headings
- not to whole paragraphs
- styling should be easy to disable or bypass when output is non-interactive

## 5. Improve section hierarchy

Replace ad hoc separators like:

- `--- Per-episode results ---`
- `--- Statistical summary ---`

with a normalized section style, for example:

- `Per-episode Results`
- `Statistical Summary`

And render them consistently using:

- blank line before section
- optional bold title
- stable indentation beneath

## 6. Make comparison output more layered

`compare.py` should be restructured later into a clearer hierarchy:

- overall comparison outcome
- identity block
- validation block
- per-episode block
- summary block
- optional extension block

Keep the numeric detail, but reduce the feeling of an unbroken print stream.

## 7. Make list outputs more scannable

Without requiring heavy tables, normalize item rows.

Possible pattern:

- identifier first
- short status token second
- concise metadata after

Example direction:

`run-0000  [completed]  summary=yes  variation=max_steps=50`

This would scan better than mixed freeform spacing.

## 8. Improve error outputs with “what next” hints

For user-facing operational errors, add one short follow-up hint where useful.

Examples:

- missing experiment:
  suggest `axis experiments list`
- missing comparison results:
  suggest `axis workspaces compare <path>`
- unchanged workspace config:
  suggest editing the config or using a future force flag if added

## 9. Separate overview and detail in workspace output

`workspaces show` is already useful, but should eventually become more clearly
tiered:

- workspace identity
- high-level state
- artifact summary
- detailed artifact sections
- validation result

This command should optimize for “What is the current situation?” before “Show
every recorded field.”

## 10. Refine runtime episode logging

For runtime console logging:

- keep the compact step prefix style
- add clearer episode boundaries
- make verbose decision/transition payloads multi-line and structured rather
  than raw one-line JSON blobs

This would preserve portability while improving readability dramatically.

## Proposed Semantic Output Style Guide

## General Rules

- Default to plain text that remains useful without color.
- Use color only as a semantic enhancement.
- Keep output line-oriented and pipe-friendly.
- Prefer consistent prefixes and labels over decorative formatting.
- Use blank lines to separate major sections.
- Indentation should reflect hierarchy:
  - top-level title: no indent
  - primary fields: 2 spaces
  - child details: 4 spaces
  - nested detail/metrics: 6-8 spaces only when needed

## Semantic Levels

### Success

- label/prefix: `Success:` or `Completed:`
- color: green
- use for completed actions and created artifacts

### Warning

- label/prefix: `Warning:`
- color: yellow
- use for recoverable problems or partial states

### Error

- label/prefix: `Error:`
- color: red
- use for invalid input, missing artifacts, failed resolution, execution aborts

### Info

- label/prefix: `Info:` or section headings
- color: blue or cyan
- use for neutral state descriptions and headings

### Secondary / debug

- color: dim or neutral
- use sparingly for explanations, hints, and secondary metadata

## Structural Conventions

### Title lines

Use for show/detail commands:

- `Experiment <id>`
- `Run <id>`
- `Workspace <id>`
- `Comparison #3`

### Field rows

Preferred form:

- `  Status: completed`
- `  System: system_a`

### Section blocks

Preferred form:

```text
Workspace system-a-baseline
  Status: running
  Type: single_system

Primary Results
  [OK] results/...
```

### List rows

Keep compact and consistent, ideally with:

- identifier
- status
- one or two important qualifiers

## Optional Before vs After Examples

## Example 1: experiments run

### Current

```text
Experiment completed.
  ID: 1234abcd
  Runs: 1
```

### Proposed direction

```text
Completed: experiment run
  Experiment ID: 1234abcd
  Runs: 1
```

With optional conservative styling:

- `Completed:` in green/bold

## Example 2: runs list

### Current

```text
run-0000  status=completed  summary=yes
run-0001  status=completed  max_steps=50  summary=yes
```

### Proposed direction

```text
Runs
  run-0000  [completed]  summary=yes
  run-0001  [completed]  variation=max_steps=50  summary=yes
```

## Example 3: workspaces check

### Current

```text
Workspace 'my-ws': VALID (with drift warnings)
  [warning] ...
  [drift:warning] ...
```

### Proposed direction

```text
Workspace my-ws
  Validation: valid with drift warnings

Warnings
  - ...

Drift Warnings
  - ...
```

## Example 4: compare output

### Current

Dense sequential print stream with ad hoc dashed headings.

### Proposed direction

```text
Comparison
  Reference: system_a  run=run-0000
  Candidate: system_c  run=run-0000
  Result: comparison_succeeded

Alignment
  Aligned steps: 163
  Reference steps: 163
  Candidate steps: 200

Per-episode Results
  Episode 1: mismatch=19.6%  pos_div=2.34  survivor=candidate

Statistical Summary
  Action mismatch rate: mean=...
  Mean trajectory distance: mean=...
```

## Prioritized Recommendations

## Priority 1

- Introduce a shared output helper layer for text-mode CLI rendering.
- Normalize semantic prefixes for success, warning, error, and info.
- Centralize error formatting instead of duplicating raw stderr prints.

Reason:

- highest leverage
- low conceptual risk
- improves consistency immediately

## Priority 2

- Refactor `compare.py` output into a normalized section hierarchy.
- Refactor `workspaces.py` detail views to separate overview from detail.
- Normalize list output patterns in `experiments.py` and `runs.py`.

Reason:

- these are the most user-visible and text-heavy surfaces

## Priority 3

- Add optional conservative ANSI styling to labels/headings only.
- Use non-color fallbacks so piped/logged output remains readable.
- Keep JSON mode unchanged.

Reason:

- visual payoff is high
- should happen only after structural normalization

## Priority 4

- Improve runtime `EpisodeLogger` verbose console formatting.
- Consider lightweight episode separators and structured multi-line payloads.

Reason:

- valuable, but less central than command-level CLI coherence

## Priority 5

- Refine argparse help text and examples.
- Remove duplication and make examples more curated and grouped.

Reason:

- useful polish
- lower urgency than command output normalization

## Summary

The current AXIS CLI already has solid fundamentals:

- plain-text portability
- JSON alternatives for machine use
- reasonably explicit wording
- low dependency complexity

Its main weakness is the lack of a shared terminal presentation system.

The best next step is not a heavy UI framework, but a restrained output
convention layer that standardizes hierarchy, semantics, prefixes, spacing,
and optional conservative color. That would make the CLI feel significantly
more modern and readable while remaining professional, portable, and safe for
engineering workflows.
