# WP-10 Rendering Cleanup

## Goal

Reduce residual rendering and command-edge complexity after command extraction.

## Why This Package Exists

Even after command extraction, rendering can easily remain tangled with
orchestration if it is not cleaned up deliberately.

The goal is not a global rendering framework.

The goal is to keep rendering local, explicit, and not mixed back into business
logic.

## Scope

### Keep rendering local to command modules

Move remaining central CLI formatting helpers into:

- command modules
- or small subsystem-local rendering helpers where justified

### Separate rendering from use-case services

Services should return structured data or domain models.

Command modules should render those results.

## Files To Change

- CLI command modules
- any residual central rendering helpers

## Deliverables

- reduced central formatting baggage
- clearer command-module responsibility boundaries

## Non-Goals

- no global rendering subsystem

## Tests

Add/update tests covering:

- text/json output remains stable where required

## Acceptance Criteria

- rendering is local and explicit
- command modules do not accumulate business logic while taking over rendering
