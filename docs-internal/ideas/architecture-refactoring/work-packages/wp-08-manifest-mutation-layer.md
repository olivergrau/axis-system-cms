# WP-08 Manifest Mutation Layer

## Goal

Extract typed manifest mutation semantics from raw YAML dictionary update logic.

## Why This Package Exists

`workspaces/sync.py` currently combines:

- YAML roundtrip IO
- mutation semantics
- development-workflow pointer maintenance

That is an obvious future maintenance hotspot.

The YAML library itself is not the issue.

The problem is growing business semantics expressed as ad hoc dictionary edits.

## Scope

### Introduce a typed mutation layer

Add a focused mutation component, for example:

- `manifest_mutator.py`

### Move semantic updates there

Candidate operations:

- append primary result
- append primary comparison
- update or initialize `primary_configs` where workspace writes own that
  responsibility, especially in scaffold-related manifest updates
- update baseline/candidate result pointers
- update current candidate result
- update current validation comparison

### Keep YAML roundtrip IO separate

`sync.py` may remain as the roundtrip coordinator but should delegate semantic
changes to the new mutator.

### Operate on roundtrip-preserving YAML structures

The mutator should operate on YAML / `ruamel.yaml` roundtrip data structures,
not on a separate Pydantic write model.

The goal is:

- typed mutation operations
- explicit business update methods
- preserved comments and formatting where possible

## Files To Change

- `src/axis/framework/workspaces/sync.py`
- new mutation-layer module(s)

## Deliverables

- typed manifest mutation layer exists
- `sync.py` is thinner and less business-heavy

## Non-Goals

- do not build a full second writable manifest persistence system

## Tests

Add/update tests covering:

- result append semantics
- comparison append semantics
- development-state updates
- preservation of YAML roundtrip behavior
- comment-preserving update behavior where practical

## Acceptance Criteria

- manifest business updates are no longer primarily encoded as raw dictionary
  mutation logic in sync code
