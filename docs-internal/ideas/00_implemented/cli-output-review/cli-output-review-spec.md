# CLI Output Review Specification

## 1. Purpose

This specification defines a first normalized **CLI Output Presentation**
model for the AXIS terminal interface.

The purpose of this model is to improve the usability of AXIS in interactive
terminal sessions by making human-oriented output:

- more structurally consistent
- more semantically explicit
- easier to scan
- and easier to evolve without command-by-command formatting drift

This specification is based on the initial design analysis in:

- [CLI Output Review Draft](./cli_output_review.md)


## 2. Scope

This specification defines:

- the normative output categories used by human-oriented CLI text mode
- the structural conventions for text-mode command output
- the distinction between text-mode output and machine-readable output
- the required behavior of semantic status lines, sections, and field rows
- the minimum consistency rules for command families
- the relationship between command output and runtime episode logging

This specification does **not** define:

- a graphical terminal UI
- changes to JSON output payloads
- repository persistence formats
- comparison semantics
- workspace semantics
- parser argument structure except where help rendering is affected


## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be
interpreted normatively.


## 4. Output Modes

AXIS CLI output must be treated as occurring in two distinct output modes:

- `text`
- `json`

### 4.1 Text Mode

Text mode is the human-oriented terminal presentation layer.

This specification applies primarily to text mode.

### 4.2 JSON Mode

JSON mode is the machine-readable output mode.

JSON mode must remain semantically stable and must not be restructured merely
to satisfy text-presentation goals.

### 4.3 Strict Separation

Text-mode presentation concerns must not force degradation of JSON output.

Likewise, JSON output concerns must not force text mode to remain visually
flat if a more structured human-readable presentation is possible.


## 5. Core Model

Human-oriented AXIS CLI output must be treated as a semantic presentation
layer rather than as ad hoc strings assembled independently by each command.

This means text-mode output must be constructed from reusable semantic
building blocks rather than raw command-local formatting conventions.

At minimum, the presentation model must support:

- title lines
- semantic status lines
- section headings
- field rows
- list rows
- validation finding groups
- short hints for corrective next steps where appropriate


## 6. Semantic Output Categories

Text-mode AXIS CLI output must support the following semantic categories:

- `info`
- `success`
- `warning`
- `error`
- `result`
- `secondary`

### 6.1 Info

`info` is used for neutral state descriptions, headings, and non-problem
status context.

### 6.2 Success

`success` is used for completed actions, successful creation of artifacts, and
completed operational steps.

### 6.3 Warning

`warning` is used for recoverable issues, partial validity states, drift, or
other conditions that do not abort the operation.

### 6.4 Error

`error` is used for invalid input, missing artifacts, failed validation,
resolution failures, or execution aborts.

### 6.5 Result

`result` is used for the primary domain outcome of a command where that
outcome is neither merely informational nor a simple completion banner.

Examples:

- comparison summaries
- workspace inspection summaries
- sweep result summaries

### 6.6 Secondary

`secondary` is used for explanatory lines, hints, and low-priority metadata.

It must be used sparingly.


## 7. Structural Conventions

### 7.1 General Rules

All text-mode command output must remain:

- plain-text readable
- line-oriented
- pipe-friendly
- usable without color

Color may be added only as a semantic enhancement.

### 7.2 Indentation Hierarchy

The default text hierarchy should be:

- title line: no indent
- primary field rows: 2 spaces
- child details: 4 spaces
- deeper nesting: only when necessary

### 7.3 Section Separation

Major sections should be separated by one blank line.

Commands should avoid visually unbroken print streams when the output contains
multiple semantic blocks.

### 7.4 Decorative Formatting

Commands must not rely on decorative box drawing, heavy terminal widgets, or
dense pseudo-layout tricks as a requirement for clarity.

The first presentation layer must remain conservative.


## 8. Title Lines

Detail-oriented commands should use a stable title line as the first line of
text output.

Preferred forms include:

- `Experiment <id>`
- `Run <id>`
- `Workspace <id>`
- `Comparison`
- `Sweep Result <experiment-id>`

The title line should identify the object being shown before subordinate field
rows begin.


## 9. Field Rows

Field rows are the standard representation for labeled metadata.

Preferred form:

- `  Label: value`

Field rows should be used for:

- identity metadata
- status metadata
- short state summaries
- path references
- compact quantitative fields

Commands should avoid mixing multiple incompatible field styles within one
detail view.


## 10. Section Blocks

Section blocks must be the standard way to group related fields or findings.

Common examples:

- `Primary Results`
- `Validation`
- `Per-episode Results`
- `Statistical Summary`
- `Warnings`

Ad hoc dashed separators should not be treated as the primary sectioning
mechanism in the normalized model.


## 11. List Rows

List-oriented commands must use consistent compact list rows.

Each list row should place:

- a leading identifier first
- a short status token second, where relevant
- one or two high-value qualifiers after that

Example direction:

- `run-0000  [completed]  summary=yes`
- `run-0001  [completed]  variation=max_steps=50  summary=yes`

List rows should remain compact, but should not require the reader to infer
structure from inconsistent key ordering.


## 12. Command Output Templates

Each human-oriented CLI command should follow one of a small number of output
templates.

### 12.1 List Command

A list command should render:

- optional title or section heading
- optional short summary line
- uniform list rows

### 12.2 Detail Command

A detail command should render:

- title line
- identity / metadata block
- optional summary block
- optional detail sections

### 12.3 Completion Command

A completion command should render:

- one-line success or completion headline
- a compact result block with identifiers, counts, or key paths

### 12.4 Validation Command

A validation-oriented command should render:

- title or object identity
- validation status line
- grouped findings
- optional hint line when user action is likely needed next

### 12.5 Comparison Command

A comparison-oriented command should render:

- comparison identity block
- validation block if comparison validity is in question
- per-item or per-episode result block
- summary block
- optional extension block


## 13. Error Output Requirements

All user-facing error output in text mode must use a normalized error
presentation.

At minimum, text-mode error output must provide:

- an explicit error line
- a short reason

Where a likely user next step is obvious, commands should additionally provide
a hint.

Examples of likely hint cases include:

- missing experiment
- missing comparison result
- missing workspace artifact
- invalid workspace path

Error output must be sent to stderr.


## 14. Validation Output Requirements

Validation-oriented commands must distinguish clearly between:

- valid
- valid with warnings
- invalid

If findings are present, they should be grouped in a normalized way rather
than being emitted only as mixed freeform lines.

Where drift findings exist, they should remain visibly distinct from ordinary
validation findings.


## 15. Optional Styling

Optional ANSI styling may be applied in text mode if and only if:

- the output remains fully understandable without color
- styling is conservative
- styling can be disabled automatically or explicitly

### 15.1 Styling Role

Color should reinforce semantic meaning, not replace it.

### 15.2 Preferred Mapping

Recommended semantic mapping:

- success: green
- warning: yellow
- error: red
- info: blue or cyan
- secondary: dim or neutral

### 15.3 Styling Boundary

Styling should primarily be applied to:

- prefixes
- headings
- labels

It should not be applied broadly to entire paragraphs.


## 16. Help Output

CLI help output remains a parser-generated surface, but the AXIS CLI should
still treat help readability as part of terminal experience quality.

The normalized CLI presentation model should therefore also aim to improve:

- duplicated examples
- inconsistent grouping cues
- overly flat family descriptions

This does not require replacing `argparse`, but does require treating help
text quality as a maintained surface.


## 17. Runtime Episode Logging

Runtime episode logging is a separate output surface from command-level CLI
inspection, but it should still follow the same high-level presentation
principles.

### 17.1 Required Continuity

Runtime logging should remain:

- compact
- line-oriented
- stable

### 17.2 Verbose Mode

Verbose console logging should not emit large opaque one-line JSON blobs where
a more structured multi-line text block is feasible.

### 17.3 Relationship To CLI Text Mode

Runtime logging does not need to use exactly the same layout templates as
detail and list commands, but it should share:

- semantic clarity
- stable prefixes
- readable boundaries between logical units


## 18. Compatibility Requirements

The first normalized CLI presentation layer must preserve:

- shell-friendly operation
- portability across ordinary terminals
- straightforward testability
- compatibility with redirected output

The CLI output review effort must therefore be treated as a structural
normalization effort, not as a terminal UI redesign.


## 19. Priority Requirements For First Adoption

The first implementation wave should prioritize the command surfaces where
current output density and inconsistency are highest.

The highest-priority surfaces are:

- run comparison text output
- workspace inspection and validation text output
- experiment and run list/detail text output
- centralized text-mode error output

Optional styling and runtime logging refinement should follow structural
normalization rather than precede it.
