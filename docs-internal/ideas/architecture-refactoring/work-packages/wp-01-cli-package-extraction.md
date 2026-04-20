# WP-01 CLI Package Extraction

## Goal

Refactor the monolithic CLI implementation into a package while preserving the
current external entrypoint contract.

## Why This Package Exists

The current CLI is concentrated in:

- `src/axis/framework/cli.py`

This file currently combines:

- parser construction
- command dispatch
- rendering helpers
- command orchestration
- error handling

It is the single largest framework hotspot and the first practical extraction
target.

The packaging entrypoint currently points to:

- `axis.framework.cli:main`

That compatibility must be preserved.

## Scope

### Introduce a CLI package boundary

Refactor toward:

- `src/axis/framework/cli/`

The exact implementation may use one of two compatibility strategies:

1. convert `cli.py` into a package boundary (`cli/__init__.py`)
2. keep a thin compatibility shim at the old import location

Either is acceptable as long as:

- `axis.framework.cli:main` remains valid

### Extract parser and dispatch responsibilities

The CLI package should introduce at minimum:

- parser module
- dispatch module

This package does not yet need to finish all command extraction, but it must
establish the new structural seam.

## Files To Change

- `src/axis/framework/cli.py` or replacement CLI package modules
- `pyproject.toml` if needed for compatibility preservation

## Deliverables

- CLI package structure exists
- `main()` compatibility preserved
- parser and dispatch are no longer trapped in one monolithic file

## Non-Goals

- full command extraction belongs next
- DI registration is not the main focus here
- no business-logic redesign in this package

## Tests

Update/add tests to confirm:

- `axis.framework.cli:main` remains callable
- core command entry behavior is preserved

Likely targets:

- `tests/framework/test_cli.py`

## Acceptance Criteria

- the CLI no longer depends on a single monolithic implementation module
- the script entrypoint remains externally stable
