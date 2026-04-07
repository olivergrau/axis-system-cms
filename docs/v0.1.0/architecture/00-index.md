# AXIS System A -- Architecture Documentation

This directory contains the technical architecture documentation for the **current implemented state** of AXIS System A, derived directly from the codebase.

## Document Index

| # | Document | Contents |
|---|----------|----------|
| 01 | [Purpose and Scope](01-purpose-and-scope.md) | What the system implements, architectural layers, out-of-scope items |
| 02 | [System Overview](02-system-overview.md) | High-level structure, maturity, core runtime vs. framework vs. infrastructure |
| 03 | [Repository Structure](03-repository-structure.md) | Package/module layout with responsibilities |
| 04 | [Runtime Architecture](04-runtime-architecture.md) | World, observation, memory, drives, policy, transition, runner, results |
| 05 | [Experimentation Framework](05-experimentation-framework.md) | RunConfig, ExperimentConfig, executors, seed handling, OFAT |
| 06 | [Persistence Architecture](06-persistence-architecture.md) | ExperimentRepository, artifact layout, immutable vs. mutable artifacts |
| 07 | [Resume and Fault Tolerance](07-resume-and-fault-tolerance.md) | Run completion detection, resume semantics, status handling |
| 08 | [CLI Architecture](08-cli-architecture.md) | Entry points, command structure, dispatch |
| 09 | [Visualization Architecture](09-visualization-architecture.md) | Snapshot resolver, viewer state, view models, UI layer, signal wiring |
| 10 | [Execution and Data Flow](10-execution-and-data-flow.md) | End-to-end flow from config to persistence |
| 11 | [Domain Models](11-domain-models.md) | Key models, fields, and contracts |
| 12 | [Testing Landscape](12-testing-landscape.md) | Test categories, coverage, fixtures, builders |
| 13 | [Strengths and Limitations](13-strengths-and-limitations.md) | Architectural strengths, current limitations, spec deviations |

## Conventions

- All class/function references point to actual implementation, not spec intent.
- Field types and constraints are as declared in Pydantic model definitions.
- Where implementation differs from spec documents, the implementation is authoritative.
