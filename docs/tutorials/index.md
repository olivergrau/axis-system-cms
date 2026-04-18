# Tutorials

Step-by-step guides that build a complete AXIS component from scratch.
Each tutorial is incremental -- every chapter builds on the previous one --
and includes tests alongside each step.

## Available Tutorials

| Tutorial | What You Build | Chapters |
|---|---|---|
| [Building a System](building-a-system.md) | System A from contract to visualization adapter | 16 |
| [Building a World](building-a-world.md) | Grid 2D world from cell model to plugin registration | 12 |
| [Understanding Prediction-Error-Driven Behavior](prediction-error-tutorial.md) | A conceptual walkthrough of prediction, context quantization, traces, and behavior shaping | -- |

## Workspace Tutorials

Hands-on guides for using experiment workspaces to structure your work.

| Tutorial | Workspace Type | What You Do |
|---|---|---|
| [Investigating a Single System](workspace-single-system.md) | investigation / single_system | Study how a parameter change affects one system |
| [Comparing Two Systems](workspace-system-comparison.md) | investigation / system_comparison | Compare two systems under identical conditions |
| [Developing a System](workspace-system-development.md) | development / system_development | Build and validate a new system with baseline/candidate workflow |

## Prerequisites

- Familiarity with Python 3.11+ and Pydantic v2
- A working AXIS development environment (`pip install -e ".[dev]"`)
- For conceptual background, see the [Concepts](../concepts/index.md) series
