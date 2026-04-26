```text
   █████╗ ██╗  ██╗██╗███████╗
  ██╔══██╗╚██╗██╔╝██║██╔════╝
  ███████║ ╚███╔╝ ██║███████╗
  ██╔══██║ ██╔██╗ ██║╚════██║
  ██║  ██║██╔╝ ██╗██║███████║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝

        C M S
  Complex Mechanistic Systems
```

# AXIS Experimentation Framework

AXIS is a modular agent-environment experimentation framework. It provides
a protocol-based architecture where **systems** (agent logic) and **worlds**
(environment dynamics) are pluggable components, composed via registries and
executed through a unified CLI.

## Project Method

AXIS was developed spec-first and implemented with AI assistance.

The repository should be read as the result of an engineering process centered on explicit specifications, formalized concepts, protocol contracts, and testable behavior. AI tools were used as implementation accelerators, not as substitutes for architecture or conceptual ownership.

## Architecture

```
src/axis/
  sdk/                  Protocol contracts and shared types
    interfaces.py         SystemInterface, SensorInterface, DriveInterface, ...
    world_types.py        WorldView, MutableWorldProtocol, BaseWorldConfig, ...
    types.py              DecideResult, TransitionResult, PolicyResult
    trace.py              BaseStepTrace, BaseEpisodeTrace
    snapshot.py           WorldSnapshot
    position.py           Position
    actions.py            BASE_ACTIONS, MOVEMENT_DELTAS

  framework/            Orchestration, persistence, CLI
    cli.py                axis CLI entry point
    config.py             ExperimentConfig, FrameworkConfig, OFAT path parsing
    runner.py             Episode loop (setup_episode, run_episode)
    run.py                RunExecutor, RunResult, RunSummary
    experiment.py         ExperimentExecutor, OFAT, resume
    persistence.py        ExperimentRepository (file-based)
    registry.py           System registry (register_system, create_system)
    comparison/           Paired trace comparison and run-level analysis
    workspaces/           Experiment workspaces (scaffold, execute, compare, sync)

  plugins.py            Plugin discovery (entry points + YAML)

  systems/              Pluggable system implementations
    construction_kit/     Reusable system-internal building blocks
      observation/          Von Neumann sensor, cell/observation types
      drives/               Hunger drive, curiosity drive, drive output types
      policy/               Softmax policy with admissibility masking
      arbitration/          Drive weight computation, score combination
      energy/               Energy clipping, vitality, termination checks
      memory/               Observation buffer, world model (visit counts)
      prediction/           Predictive memory, context encoding, error decomposition
      traces/               Dual-trace dynamics (frustration, confidence)
      modulation/           Action score modulation from traces
      types/                Shared config types, action handlers (consume)
    system_a/             Energy-driven forager (composes kit components)
    system_aw/            Dual-drive agent with curiosity and world model
    system_c/             Predictive action modulation agent
    system_cw/            Predictive dual-drive agent with shared memory
    system_b/             Scout agent with scan action

  world/                Pluggable world implementations
    registry.py           World registry (register_world, create_world_from_config)
    actions.py            ActionRegistry, base movement handlers
    grid_2d/              Standard 2D rectangular grid (default)
    toroidal/             Wraparound grid (edges connect)
    signal_landscape/     Dynamic signal-based world with drifting hotspots

  visualization/        Adapter-based interactive episode viewer
    registry.py           Visualization adapter registry
    launch.py             Viewer entry point
    ui/                   Qt-based UI components
```

## Engineering Principles

The framework is built around a small number of explicit principles:

- protocol-based extensibility over inheritance-heavy coupling
- deterministic execution and replayability by default
- separation of system logic, world dynamics, and framework orchestration
- inspectable experiment artifacts and structured persistence
- visualization as an analysis tool, not just a demo layer

## CLI

```
axis experiments run <config.yaml>             Run experiment from config
axis experiments list                          List all experiments
axis experiments show <experiment_id>          Inspect experiment details
axis experiments resume <experiment_id>        Resume incomplete experiment

axis runs list --experiment <experiment_id>    List runs in an experiment
axis runs show <run_id> --experiment <eid>     Inspect a specific run

axis visualize --experiment <eid> --run <rid> --episode 1
                                               Open interactive episode viewer

axis compare --reference-experiment <eid> --reference-run <rid> \
             --candidate-experiment <eid> --candidate-run <rid>
                                               Compare all episodes across two runs

axis compare --reference-experiment <eid> --reference-run <rid> --reference-episode 1 \
             --candidate-experiment <eid> --candidate-run <rid> --candidate-episode 1
                                               Compare a single episode pair

axis workspaces scaffold                       Create a new experiment workspace
axis workspaces show <path>                    Inspect workspace state and artifacts
axis workspaces run <path>                     Execute workspace configs
axis workspaces run <path> --baseline-only     Run only baseline (development)
axis workspaces run <path> --candidate-only    Run only candidate (development)
axis workspaces set-candidate <path> <config>  Set candidate config (development)
axis workspaces compare <path>                 Compare workspace experiments
axis workspaces comparison-summary <path>       Display comparison results
axis workspaces check <path>                   Validate workspace structure
```

Use `--output json` on any command for machine-readable output.
Use `--root <path>` to point to a non-default repository location.

## Execution Modes

AXIS supports three execution trace modes through `execution.trace_mode`:

- `full` -- richest replay artifacts; best for detailed replay/debugging
- `delta` -- replay-compatible compact traces; good default when you still want visualization and comparison with lower artifact cost
- `light` -- fastest summary-oriented mode; not replay-compatible and therefore not visualizable

AXIS also supports explicit parallelization controls through `execution.parallelism_mode`:

- `sequential` -- baseline serial execution
- `episodes` -- parallelize episodes within one run
- `runs` -- parallelize runs within an OFAT/sweep experiment

Example:

```yaml
execution:
  max_steps: 200
  trace_mode: delta
  parallelism_mode: episodes
  max_workers: 4
```

Rule of thumb:

- use `full` when you want maximum replay richness
- use `delta` when you want replay plus better throughput/storage behavior
- use `light` when you only need summaries and do not need the visualizer

## Experiment Configs

Ready-to-use configs ship at `experiments/configs/`:

| Config | Description |
|---|---|
| `system-a-baseline.yaml` | Single-run baseline (10x10, sparse regen) |
| `system-a-energy-gain-sweep.yaml` | OFAT sweep over energy gain factor |
| `system-a-toroidal-demo.yaml` | System A on a toroidal (wraparound) grid |
| `system-aw-baseline.yaml` | System A+W dual-drive baseline (10x10, sparse regen) |
| `system-aw-curiosity-sweep.yaml` | OFAT sweep over curiosity strength (μ_C = 0.0 to 1.0) |
| `system-aw-exploration-demo.yaml` | Exploration demo (20x20, high curiosity, verbose) |
| `system-b-sdk-demo.yaml` | System B scout agent on a signal landscape |
| `system-c-baseline.yaml` | System C predictive modulation baseline |
| `system-c-prediction-demo.yaml` | System C prediction demo with verbose output |
| `system-cw-baseline.yaml` | System C+W predictive dual-drive baseline |

```bash
axis experiments run experiments/configs/system-a-baseline.yaml

# System A+W dual-drive with curiosity
axis experiments run experiments/configs/system-aw-baseline.yaml

# Sweep over curiosity strength (μ_C = 0.0 to 1.0)
axis experiments run experiments/configs/system-aw-curiosity-sweep.yaml

# Exploration demo (large grid, high curiosity)
axis experiments run experiments/configs/system-aw-exploration-demo.yaml

# System C+W predictive dual-drive baseline
axis experiments run experiments/configs/system-cw-baseline.yaml
```

## Systems

### System A — Energy-Driven Forager

A single-drive agent that seeks resources to maintain energy. Composes
reusable components from the **System Construction Kit**: Von Neumann
sensor, hunger drive, softmax policy, and shared config/action types.
System A adds its own transition logic and agent state on top of these
kit components.

### System A+W — Dual-Drive Agent with Curiosity and World Model

System A+W extends System A with a second drive (curiosity) and a spatial world model.
The agent balances hunger-driven resource-seeking with curiosity-driven exploration,
modulated by a dynamic weight function that implements a Maslow-like hierarchy:
hunger gates curiosity.

Key additions over System A (all sourced from the Construction Kit):
- **Curiosity drive** with composite novelty (spatial + sensory)
- **Spatial world model** (visit-count map via dead reckoning)
- **Dynamic drive arbitration** (hunger suppresses curiosity as energy decreases)

When curiosity parameters are zeroed, System A+W reduces exactly to System A.

System A+W configuration adds two optional sub-sections to the `system:` block:

```yaml
system:
  curiosity:
    base_curiosity: 1.0             # μ_C: overall curiosity strength (0 = disabled)
    spatial_sensory_balance: 0.5    # α: weight of spatial vs sensory novelty
    explore_suppression: 0.3        # penalty for non-exploring actions
  arbitration:
    hunger_weight_base: 0.3         # w_H_base: minimum hunger weight
    curiosity_weight_base: 1.0      # w_C_base: curiosity weight at zero hunger
    gating_sharpness: 2.0           # γ: how sharply hunger suppresses curiosity
```

Design documents: `docs/system-design/system-a+w/`

### System C — Predictive Action Modulation

System C extends System A with a prediction-based modulation factor that
learns action reliability from experience:

$$\psi_C(a) = d_H(t) \cdot \phi_H(a, u_t) \cdot \mu_H(s_t, a)$$

The agent builds a predictive memory of expected outcomes per (context, action)
pair. When predictions are violated, dual traces (frustration and confidence)
accumulate and modulate future action scores -- suppressing unreliable actions
and reinforcing positively surprising ones.

Key additions over System A (all sourced from the Construction Kit):
- **Predictive memory** with binary context encoding (32 discrete states)
- **Dual traces** (frustration/confidence) with asymmetric EMA learning
- **Exponential modulation** with loss-averse parameterization (λ- > λ+)

When prediction sensitivities are zeroed (λ+ = λ- = 0), System C reduces
exactly to System A.

System C configuration adds an optional `prediction` sub-section:

```yaml
system:
  prediction:
    memory_learning_rate: 0.3       # η_q: predictive memory learning rate
    context_threshold: 0.5          # binary threshold for context encoding
    frustration_rate: 0.2           # η_f: frustration trace EMA rate
    confidence_rate: 0.15           # η_c: confidence trace EMA rate
    positive_sensitivity: 1.0       # λ+: confidence modulation strength
    negative_sensitivity: 1.5       # λ-: frustration modulation strength
    modulation_min: 0.3             # μ_min: modulation floor
    modulation_max: 2.0             # μ_max: modulation ceiling
```

Design documents: `docs/system-design/system-c/`

### System C+W — Predictive Dual-Drive Agent

System C+W combines the dual-drive structure of System A+W with the
predictive layer of System C.

The key design is:

- **shared predictive memory** over compact local contexts
- **shared predictive feature representation** mixing resource and novelty-derived features
- **separate hunger-side and curiosity-side predictive outcomes**
- **separate hunger and curiosity trace states**
- **separate predictive modulation parameters per drive**
- **predictive modulation before arbitration**

This means the agent can share one expectation model of the local
agent-environment loop while still learning different predictive trust
for homeostatic value and exploratory value.

System C+W configuration adds `curiosity`, `arbitration`, and a structured
`prediction` subtree:

```yaml
system:
  curiosity:
    base_curiosity: 1.0
    spatial_sensory_balance: 0.5
    explore_suppression: 0.3
    novelty_sharpness: 1.0
  arbitration:
    hunger_weight_base: 0.3
    curiosity_weight_base: 1.0
    gating_sharpness: 2.0
  prediction:
    shared:
      memory_learning_rate: 0.3
      resource_threshold: 0.5
      novelty_threshold: 0.35
      novelty_contrast_threshold: 0.15
    hunger:
      frustration_rate: 0.2
      confidence_rate: 0.15
      positive_sensitivity: 1.0
      negative_sensitivity: 1.5
      modulation_min: 0.3
      modulation_max: 2.0
    curiosity:
      frustration_rate: 0.2
      confidence_rate: 0.15
      positive_sensitivity: 1.0
      negative_sensitivity: 1.5
      modulation_min: 0.3
      modulation_max: 2.0
    outcomes:
      nonmove_curiosity_penalty: 0.2
```

Design documents: `docs/system-design/system-cw/`

### System B — Scout Agent

A scan-based scout agent that operates on signal landscapes.

## Key Concepts

- **System**: Encapsulates all agent logic (sensing, decision-making, state
  transitions). Implements `SystemInterface`. Plugged in via `register_system()`.
- **World**: Encapsulates environment topology and dynamics. Implements
  `MutableWorldProtocol`. Plugged in via `register_world()`.
- **Experiment**: One or more runs with a shared config. Supports single-run
  and OFAT (one-factor-at-a-time) sweep modes.
- **Run**: Multiple episodes with a shared configuration and independent seeds.
- **Episode**: One agent lifetime from initialization to termination.
- **Workspace**: Structured container bundling intent, configs, results,
  comparisons, and notes for a coherent research or development task.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run a specific test module
python -m pytest tests/framework/test_cli.py
```

- **Python 3.11+** with PySide6, Pydantic v2, NumPy
- **Testing**: pytest (2000+ tests across framework, SDK, systems, construction
  kit, worlds, visualization, and comparison)

## Documentation

Documentation is split into two directories:

- **`docs/`** -- Public documentation, served as a browsable website via
  [MkDocs](https://www.mkdocs.org/) with the
  [Material](https://squidfunk.github.io/mkdocs-material/) theme.
  Math notation is rendered with MathJax.
- **`docs-internal/`** -- Internal development documents (architecture evolution,
  implementation specs, work packages). Not served by mkdocs.

```bash
# Start the documentation server
make docs-serve

# Then open http://localhost:8000
```

### Conceptual Series

A five-part series covering the mathematical foundations and design philosophy
behind AXIS agents. Target audience: researchers and developers who want to
understand the theory before (or alongside) the code.

| Document | Topic |
|---|---|
| `concepts/00-axis-vision.md` | AXIS vision statement |
| `concepts/01-axis-cms-vision.md` | Biological inspiration and design principles |
| `concepts/02-math-as-modeling.md` | Why mathematical formalism; alternatives and trade-offs |
| `concepts/03-agent-framework.md` | Generic 8-tuple agent framework ($\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi$) |
| `concepts/04-system-a.md` | System A: hunger drive, modulation, softmax policy, energy dynamics |
| `concepts/05-system-aw.md` | System A+W: curiosity drive, world model, drive arbitration, reduction property |

### Tutorials

Step-by-step guides that build a complete system or world from scratch,
with tests alongside each chapter.

| Tutorial | What you build |
|---|---|
| `tutorials/building-a-system.md` | System A from scratch (16 chapters) |
| `tutorials/building-a-world.md` | Grid 2D world from scratch (12 chapters) |
| `tutorials/workspace-single-system.md` | Investigating a single system with a workspace |
| `tutorials/workspace-system-comparison.md` | Comparing two systems with a workspace |
| `tutorials/workspace-system-development.md` | Developing a system with baseline/candidate workflow |

### Manuals

Reference documentation for using and extending the framework.

| Manual | Content |
|---|---|
| `manuals/axis-overview.md` | Framework overview and architecture |
| `manuals/cli-manual.md` | CLI user guide |
| `manuals/config-manual.md` | Configuration reference |
| `manuals/visualization-manual.md` | Interactive viewer and overlays |
| `manuals/system-dev-manual.md` | Building custom systems |
| `manuals/system-aw-manual.md` | System A+W configuration and behavior |
| `manuals/world-dev-manual.md` | Building custom worlds |
| `manuals/comparison-manual.md` | Paired trace comparison and run analysis |
| `manuals/visualization-extension-manual.md` | Building system-specific visualization adapters |
| `manuals/comparison-extension-manual.md` | Building system-specific comparison extensions |
| `manuals/metrics-extension-manual.md` | Building system-specific behavioral metric extensions |
| `manuals/workspace-manual.md` | Experiment workspaces: scaffold, run, compare, iterate |

### Specifications and Design

| Path | Content |
|---|---|
| `docs/system-design/system-a/` | System A formal specification and worked examples |
| `docs/system-design/system-a+w/` | System A+W formal model and worked examples |
| `docs/system-design/system-c/` | System C formal model and worked examples |
| `docs/system-design/system-cw/` | System C+W formal model and worked examples |
| `docs/cheat-sheets/` | Compact mathematical quick references for Systems A, A+W, C, and C+W |
| `docs/construction-kit/` | Reusable system-building blocks and their mathematical role |
| `docs-internal/specs/` | Implementation briefs (work packages) for all framework components |
| `docs-internal/architecture/` | Architecture documents and evolution history |
| `docs-internal/ideas/system-cw/` | Drafts, specs, engineering specs, work packages, and open issues for System C+W |

The documents in `docs-internal/` are part of the development process and define
the conceptual and technical contracts the implementation is expected to follow.

## Plugin System

AXIS discovers plugins through two mechanisms:

1. **Setuptools entry points** (`axis.plugins` group) -- for installed packages.
   `pip install axis-system-foo` automatically registers the plugin.
2. **`axis-plugins.yaml`** -- for local development and unpackaged plugins.

Both sources call each plugin's `register()` function, which populates the
system, world, and visualization registries. Idempotency guards prevent
conflicts when both sources list the same plugin.

## Development Approach

AXIS was developed in a spec-first workflow with AI-assisted implementation.

Core concepts, architecture boundaries, protocol contracts, and system behavior were specified before implementation. AI coding tools were used to accelerate implementation and iteration, while design consistency, mathematical intent, and framework structure remained under explicit human guidance and review.

The repository is intended to be evaluated as an engineering artifact: by its coherence, extensibility, inspectability, and testability.

## License

Apache 2.0 license
