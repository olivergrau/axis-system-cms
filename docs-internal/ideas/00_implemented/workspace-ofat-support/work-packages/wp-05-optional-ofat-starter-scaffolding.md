# WP-05 Optional OFAT Starter Scaffolding

## Goal

Allow `single_system` workspace scaffolding to optionally create an OFAT starter
config.

## Why This Package Exists

OFAT support should not require manual YAML authoring from scratch every time.

At the same time, the current default scaffold should remain simple and
point-oriented:

- one baseline `single_run` config

This package adds an optional convenience path without changing the default
Workspace shape.

## Scope

### Preserve the current default

Default `single_system` scaffolding should continue to create:

- one baseline point config

### Add optional OFAT starter support

Interactive scaffolding may optionally create:

- an OFAT starter config

The starter should include plausible placeholder values for:

- `experiment_type: "ofat"`
- `parameter_path`
- `parameter_values`

These values are only starter content and remain user-editable.

### Keep scope bounded

This package should not introduce:

- automatic multiple configs in the default scaffold
- implicit conversion of an existing point config to OFAT

## Files To Change

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/scaffold.py`
- `src/axis/framework/workspaces/handlers/single_system.py`

## Deliverables

- optional OFAT starter path during scaffolding
- default scaffold unchanged

## Non-Goals

- OFAT support must not depend on this convenience feature
- no change to other workspace types

## Tests

Add or update tests covering:

- default single-system scaffold still creates point baseline config
- optional OFAT starter creates a valid OFAT starter config
- scaffolded manifest remains valid

Suggested primary test target:

- `tests/framework/workspaces/test_scaffold.py`

## Acceptance Criteria

- the normal scaffold path stays simple
- users can optionally generate an OFAT starter without manual boilerplate
