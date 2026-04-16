# AXIS Experimentation Framework

AXIS is a modular agent-environment experimentation framework. It provides a
protocol-based architecture where **systems** (agent logic) and **worlds**
(environment dynamics) are pluggable components, composed via registries and
executed through a unified CLI.

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Run an experiment
axis experiments run experiments/configs/system-a-baseline.yaml

# Run System A+W with curiosity
axis experiments run experiments/configs/system-aw-baseline.yaml
```

## Documentation Overview

| Section | Description |
|---|---|
| [Concepts](concepts/index.md) | Mathematical foundations and design philosophy behind AXIS agents. Start here to understand the theory. |
| [Tutorials](tutorials/index.md) | Step-by-step guides that build a complete system or world from scratch, with tests alongside each chapter. |
| [Construction Kit](construction-kit/index.md) | Reusable building blocks for systems: sensors, drives, policy, arbitration, energy, memory, and shared types. |
| [Manuals](manuals/index.md) | Reference documentation for using and extending the framework: CLI, configuration, visualization, and developer guides. |


## Systems

| System | Description |
|---|---|
| **System A** | Energy-driven forager with hunger drive and softmax policy |
| **System A+W** | Dual-drive agent adding curiosity and spatial world model |
| **System B** | Scout agent with scan action on signal landscapes |
| **System C** | Predictive hunger agent with local predictive memory and action-level modulation |

## Plugin System

AXIS discovers plugins through two mechanisms:

1. **Setuptools entry points** (`axis.plugins` group) -- for installed packages
2. **`axis-plugins.yaml`** -- for local development and unpackaged plugins
