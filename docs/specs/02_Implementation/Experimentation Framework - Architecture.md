# Experimentation Framework – Architecture

## 1. Purpose and Scope
The **Experimentation Framework** introduces a structured layer on top of the AXIS System A runtime to enable controlled, reproducible, and statistically meaningful experimentation.

While the core system (WP1–WP10) provides a fully functional simulation pipeline, it operates primarily at the level of individual episode execution. This is insufficient for systematic analysis, comparison of configurations, or empirical validation of system behavior.

The purpose of this framework is therefore to:

- Enable execution of **multiple episodes under a shared configuration** (Run)
- Support **structured collections of runs** for comparative analysis (Experiment)
- Provide **persistent storage of configurations and results** for reproducibility
- Establish a **standardized interface (CLI)** for managing experiments
- Allow **post-hoc statistical evaluation** based on aggregated results

---

### Scope
The Experimentation Framework includes:

- Definition and orchestration of:
    
    - Runs (multi-episode executions)
    - Experiments (collections of runs)

- Configuration handling for runs and experiments (JSON/YAML-based)
    
- Execution components:
    
    - `RunExecutor`
    - `ExperimentExecutor`

- Integration with:
    
    - Existing `EpisodeRunner` (WP7)
    - Result structures (`EpisodeResult`, `RunResult`, WP8)
    - Logging system (WP10, via references only)

- File-system-based persistence of:
    
    - Configurations
    - Results
    - Experiment metadata

- A minimal but functional **CLI interface** for:
    
    - Running experiments
    - Listing and inspecting results
    - Resuming interrupted executions

---

### Out of Scope
The following aspects are explicitly **not part of this framework** and are handled separately or deferred:

- Live visualization or interactive dashboards
- Database-backed storage systems
- Advanced experiment optimization strategies (e.g., Bayesian optimization)
- Distributed or parallel execution (initially single-process, sequential execution)
- Modification of core runtime logic (agent, world, transition function)

---

### Position in Overall Architecture
The Experimentation Framework sits **above the core runtime layer** and acts as an orchestration and analysis layer:

```text
[ Experimentation Framework ]
            ↓
[ Run / Experiment Execution ]
            ↓
[ Episode Execution (WP7) ]
            ↓
[ Core Runtime (State, Policy, Transition) ]
```

It transforms the system from a **simulation engine** into an **experimental platform**, enabling systematic exploration of agent behavior under controlled conditions.

---

## 2. Conceptual Model
The Experimentation Framework is built around a small set of well-defined hierarchical concepts that structure execution, data collection, and analysis.

These concepts define _what is being executed_, _at which granularity_, and _how results are grouped and interpreted_.

---

### 2.1 Core Entities

#### Episode
An **Episode** is the smallest executable unit in the system.

It represents a single, complete interaction cycle of the agent within the environment, starting from an initial state and terminating when a stopping condition is reached (e.g., agent death or max steps).

**Properties:**

- Executed via the `EpisodeRunner` (WP7)
- Deterministic given:
    
    - Initial state
    - Configuration
    - Random seed

- Produces:
    
    - `EpisodeResult` (WP8)
    - Optional step-level traces

**Role in the framework:**

- Atomic data source for all higher-level aggregation
- Not directly compared across configurations in isolation

---

#### Run
A **Run** is a collection of multiple episodes executed under a **single, fixed configuration**.

It represents the minimal unit for **statistical evaluation**.

**Properties:**

- Defined by:
    
    - A fully specified configuration (agent, environment, policy, etc.)
    - A set of seeds (one per episode)
    - A fixed number of episodes

- Executed via the `RunExecutor`
    
- Produces:
    
    - Multiple `EpisodeResults`
    - One aggregated `RunResult`

**Role in the framework:**

- Provides statistical robustness
- Enables computation of:
    
    - Means, variances, rates (e.g., survival, consumption)

- Serves as the primary unit for comparison across configurations

---

#### Experiment
An **Experiment** is a structured collection of runs.

It represents a **controlled study** over one or more configurations.

**Properties:**

- Defined by:
    
    - A baseline configuration (optional but strongly recommended)
    - A set of derived configurations (e.g., parameter variations)

- Executed via the `ExperimentExecutor`
- Produces:
    
    - Multiple `RunResult`s
    - Experiment-level metadata and summaries


**Role in the framework:**

- Enables:
    
    - Parameter studies (e.g., OFAT)
    - Comparative analysis between configurations
        
- Represents the highest-level unit of organization and analysis

---

### 2.2 Hierarchical Structure
The relationship between the core entities is strictly hierarchical:

```text
Experiment
 ├── Run (Configuration A)
 │    ├── Episode 1
 │    ├── Episode 2
 │    └── ...
 │
 ├── Run (Configuration B)
 │    ├── Episode 1
 │    ├── Episode 2
 │    └── ...
 │
 └── ...
```

**Key implications:**

- Episodes are **never shared** between runs
- Runs are **independent statistical units**
- Experiments define the **comparison space**

---

### 2.3 Configuration Binding
Each level binds configuration differently:

- **Episode**
    
    - Inherits configuration from its parent run
    - Adds a unique random seed

- **Run**
    
    - Owns a **fully resolved configuration snapshot**
    - Configuration must be immutable during execution

- **Experiment**
    
    - Defines how multiple run configurations are generated
    - May reference a **baseline configuration**


---

### 2.4 Determinism and Seeds
Determinism is enforced at the episode level and propagated upward:

- Each episode is associated with a **unique seed**
    
- A run defines:
    
    - Seed strategy (e.g., fixed list, generated sequence)

- All seeds must be:
    
    - Stored in results
    - Reproducible

**Implication:**  
A run can be re-executed exactly if:

- Configuration snapshot is identical
- Seed list is identical

---

### 2.5 Data Flow Overview

```text
Configuration
    ↓
RunExecutor
    ↓
EpisodeRunner (per episode)
    ↓
EpisodeResult
    ↓
Aggregation
    ↓
RunResult
    ↓
Experiment Aggregation
    ↓
Experiment Summary
```

---

### 2.6 Conceptual Boundaries
To avoid conceptual drift, the following boundaries are enforced:

- **Episode**
    
    - No knowledge of runs or experiments

- **Run**
    
    - No knowledge of other runs
    - Pure aggregation layer

- **Experiment**
    
    - No influence on execution logic inside runs
    - Only responsible for orchestration and comparison

---

## 3. Design Principles
The Experimentation Framework is guided by a set of design principles that ensure consistency, reproducibility, and long-term extensibility.

These principles constrain implementation decisions across all components, including execution, storage, and interfaces.

---

### 3.1 Reproducibility as a First-Class Concern
Every run and experiment must be reproducible without ambiguity.

**Requirements:**

- Each run stores a **fully resolved configuration snapshot**
- Each episode uses a **recorded random seed**
- All relevant parameters must be persisted alongside results

**Implication:**  
A run can be re-executed exactly if:

- Configuration snapshot is identical
- Seed list is identical

No hidden state, implicit defaults, or external dependencies are allowed to influence execution.

---

### 3.2 Run as the Primary Statistical Unit
The framework treats the **Run** as the minimal unit of analysis.

**Rationale:**

- Single episodes are inherently noisy
- Statistical interpretation requires aggregation

**Consequences:**

- Metrics are defined at the run level, not episode level
- Comparisons between configurations are always run-to-run
- Episode-level data is considered raw input, not final output

---

### 3.3 Strict Separation of Concerns
The framework enforces clear boundaries between layers:

- **Core Runtime (WP1–WP7):**
    
    - State transitions, policy, execution logic

- **Results Layer (WP8):**
    
    - Structured outputs (`EpisodeResult`, `RunResult`)

- **Logging Layer (WP10):**
    
    - Observability and debugging information

- **Experimentation Framework:**
    
    - Orchestration, aggregation, and comparison

**Implication:**

- No duplication of responsibilities
- No leakage of orchestration logic into runtime
- No analysis logic embedded in execution components

---

### 3.4 File-System-Based Persistence (Initial Strategy)
All experiment artifacts are stored using a **file-system-based approach**.

**Rationale:**

- Simplicity and transparency
- Easy inspection and debugging
- No infrastructure dependencies

**Requirements:**

- Deterministic directory structure
- Explicit file formats (JSON, JSONL, YAML)
- No reliance on external services

**Constraint:**

- Future database integration must remain optional and non-breaking

---

### 3.5 Immutable Configuration and Results
Configurations and results are treated as **immutable artifacts**.

**Requirements:**

- Run configurations must not change after execution starts
- Results must not be modified post-write
- Any transformation produces a new artifact

**Implication:**

- Guarantees auditability
- Prevents silent corruption of experimental data

---

### 3.6 Post-Hoc Analysis Only
All evaluation and interpretation is performed **after execution**.

**Rationale:**

- Keeps runtime simple and deterministic
- Avoids coupling execution with analysis or visualization

**Consequences:**

- No live dashboards or streaming analytics
- All summaries derived from persisted results
- Visualization layer operates on stored data only

---

### 3.7 Incremental and Fault-Tolerant Execution
The system must tolerate interruptions and support continuation.

**Requirements:**

- Partial results must be persisted incrementally
- Runs and experiments must be resumable
- Completed work must never be recomputed unintentionally

**Implication:**

- Execution must be idempotent at the run level
- Resume logic must detect and skip completed units

---

### 3.8 Explicit and Minimal Interfaces
Interfaces must be:

- Explicit
- Minimal
- Directly mapped to domain concepts

**Applied to CLI:**

- Commands reflect real entities (`experiment`, `run`)
- No artificial abstraction layers for presentation

**Implication:**

- System remains scriptable and predictable
- No hidden transformations between user input and execution

---

### 3.9 Controlled Complexity via Canonical Experiment Types
The framework limits complexity by defining **canonical experiment types**.

Initial supported types:

- Single Run
- OFAT (One-Factor-At-a-Time)

**Rationale:**

- Prevents uncontrolled feature growth
- Keeps implementation tractable

**Extension strategy:**

- New experiment types must be explicitly introduced and justified
- No ad-hoc parameter combinations at runtime

---

### 3.10 Extensibility Without Premature Generalization
The system must be extensible, but not over-engineered.

**Approach:**

- Introduce clear extension points (executors, config generators)
- Avoid generic plugin systems at this stage

**Examples:**

- Future parallel execution
- Additional experiment strategies
- Alternative storage backends

**Constraint:**

- Extensions must not break existing artifacts or workflows

---

### 3.11 Alignment with Existing System Contracts
The framework must fully align with previously defined components:

- `EpisodeRunner` (WP7)
- `EpisodeResult`, `RunResult` (WP8)
- Logging system (WP10, via references only)

**Implication:**

- No redefinition of existing concepts
- No duplication of data structures
- Strict reuse of established contracts

---

## 4. Execution Architecture
The execution architecture defines how the Experimentation Framework orchestrates the existing runtime components in order to execute:

- multiple episodes under one configuration
- multiple runs within one experiment
- resumable and reproducible experiment workflows

This architecture must remain strictly layered above the core runtime and must not introduce any back-dependencies from execution to experimentation. This separation is a hard requirement of the engineering pre-specification.

---

### 4.1 Architectural Role
The Experimentation Framework is an orchestration layer above the existing runtime.

Its role is to:

- prepare resolved run configurations
- execute runs composed of multiple episodes
- aggregate episode-level outputs into run-level outputs
- organize multiple runs into experiments
- persist artifacts incrementally
- support resume and inspection workflows

It is not responsible for:

- policy computation
- transition logic
- episode-internal decision making
- live visualization
- statistical interpretation beyond lightweight summaries

---

### 4.2 Layered Execution Structure
The execution architecture is composed of three levels:

```text
ExperimentExecutor
    └── RunExecutor
            └── EpisodeRunner
```

#### EpisodeRunner
The `EpisodeRunner` is the existing runtime component from WP7.

It is responsible for:

- initializing and executing a single episode
- orchestrating:
    
    - observation
    - drive computation
    - policy
    - transition

- returning one `EpisodeResult`

The `EpisodeRunner` has no knowledge of runs or experiments. This must remain unchanged.

---

#### RunExecutor
The `RunExecutor` is the first new orchestration layer introduced by the Experimentation Framework.

It is responsible for:

- receiving one fully resolved `RunConfig`
- generating or resolving episode seeds
- executing multiple episodes under identical configuration
- collecting all `EpisodeResult` objects
- computing a `RunSummary`
- constructing and persisting a `RunResult`

The `RunExecutor` is the minimal statistical execution unit.

---

#### ExperimentExecutor
The `ExperimentExecutor` is the top-level orchestration component.

It is responsible for:

- loading one `ExperimentConfig`
- expanding declarative sweep definitions into concrete `RunConfig` objects
- assigning stable run identifiers
- invoking the `RunExecutor` sequentially
- persisting experiment-level metadata and status
- collecting `RunResult` references
- computing an `ExperimentSummary`
- constructing and persisting an `ExperimentResult`

The `ExperimentExecutor` does not execute episodes directly.

---

### 4.3 Execution Flow
The high-level execution flow is:

```text
ExperimentConfig
    ↓
ExperimentExecutor
    ↓
RunConfig expansion
    ↓
RunExecutor (per run)
    ↓
EpisodeRunner (per episode)
    ↓
EpisodeResult collection
    ↓
RunResult aggregation
    ↓
ExperimentResult aggregation
```

This preserves the strict hierarchy already defined conceptually:

```text
Step → Episode → Run → Experiment
```

The execution architecture must mirror this hierarchy exactly.

---

### 4.4 Episode Execution within a Run
A run consists of multiple episodes executed under the same resolved configuration.

#### Run-Level Invariants
Within a single run:

- all episodes use the same resolved system configuration
- all episodes use the same run identity
- all episode results belong exclusively to that run
- statistical summaries are derived only from the episodes of that run

#### Episode Variation
Episodes within a run may differ only in:

- episode seed
- any deterministic consequences of that seed
- resulting trajectories and outcomes

This means a run can capture stochastic variability while preserving configuration identity.

---

### 4.5 Configuration Resolution Boundary
The architecture must enforce a clear boundary between:

- experiment-level configuration
- run-level resolved configuration
- episode-level execution parameters

#### Experiment Level

Defines:

- experiment identifier
- experiment type
- baseline reference config
- sweep definition
- persistence settings
- aggregation options

#### Run Level
Defines:

- one fully resolved configuration snapshot
- episode count
- seed strategy
- logging / observability settings
- run metadata

#### Episode Level
Receives:

- resolved runtime configuration inherited from the run
- one concrete episode seed

This ensures that the `EpisodeRunner` remains simple and does not need to understand experiment structure.

---

### 4.6 Seed and Determinism Architecture
The execution architecture must implement deterministic seed handling across all levels.

#### Experiment Seed Context
An experiment may define a `base_seed`.

This base seed is used to deterministically derive:

- run seeds
- episode seeds within each run

#### Run Seed Context
Each run must have a stable run seed, derived deterministically from experiment context or defined explicitly.

#### Episode Seed Context
Each episode must have its own explicit seed.
This seed is the effective seed passed into runtime execution.

#### Determinism Requirement
Given identical:

- experiment configuration
- baseline config
- sweep definition
- seed definitions
- execution order

the experiment must produce identical:

- run configurations
- episode seed assignments
- episode results
- run summaries
- experiment summaries

This is mandatory for reproducibility.

---

### 4.7 Sequential Execution Strategy
The baseline experimentation architecture shall execute runs sequentially.

This means:

- one run at a time
- one episode at a time within each run
- no parallel execution in the baseline implementation

#### Rationale
This preserves:

- implementation simplicity
- deterministic ordering
- easier debugging
- simpler persistence and resume semantics

The pre-spec explicitly treats parallelization as future-ready, but deferred.

---

### 4.8 Resume-Oriented Execution Model
The execution architecture must support resumable experiments.

#### Required Capability
If execution is interrupted:

- completed runs must remain valid
- partially completed experiments must be restartable
- rerun of already completed work must be avoidable

#### Execution Consequence
This requires:

- incremental persistence after each completed run
- stable identifiers for experiments, runs, and episodes
- explicit status tracking
- ability to detect completed vs. incomplete units

#### Recommended Resume Boundary
The baseline resume boundary should be the **run**.

That means:

- completed runs are skipped
- incomplete or missing runs are executed
- optional finer-grained resume inside partially completed runs may be supported if architecturally simple, but is not required as the primary mechanism

This keeps the implementation tractable while still supporting useful recovery behavior.

---

### 4.9 Status and Lifecycle Model
The execution architecture should define explicit lifecycle states for persisted experiment entities.

#### Experiment Status
At minimum:

- `CREATED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `PARTIAL`

#### Run Status
At minimum:

- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`

These statuses are needed for:

- CLI inspection
- resume logic
- fault diagnosis
- reliable persistence semantics

---

### 4.10 Result Construction Responsibilities
The execution architecture must assign result construction responsibilities clearly.

#### EpisodeRunner
Produces:

- `EpisodeResult`

#### RunExecutor
Produces:

- ordered collection of `EpisodeResult`
- `RunSummary`
- `RunResult`

#### ExperimentExecutor
Produces:

- ordered collection of run references and/or `RunResult` objects
- `ExperimentSummary`
- `ExperimentResult`

This avoids ambiguity about where aggregation happens.

---

### 4.11 Observability Integration Boundary
The execution architecture integrates with the logging / observability layer, but does not delegate meaning to it.

#### Principle
Structured results remain the source of truth.

This means:

- `EpisodeResult` and `RunResult` are primary data artifacts
- logs are derived artifacts
- experiment execution may store log references, but does not depend on logs for correctness

This is consistent with the existing WP8/WP10 contract.

---

### 4.12 Failure Handling
The execution architecture must fail explicitly, but preserve already completed work.

#### Requirements

- invalid configuration resolution must fail before execution begins
- run failure must not silently corrupt experiment state
- partial results must remain inspectable
- experiment state must reflect incomplete execution explicitly

#### Implication
A failed run should not invalidate previously completed runs in the same experiment.

This is necessary for meaningful resume behavior.

---

### 4.13 Architectural Constraints
The following constraints are mandatory:

#### 1. No Back-Dependency into Runtime
The `EpisodeRunner` and lower runtime layers must not know about:

- runs
- experiments
- sweeps
- experiment summaries
- CLI operations

#### 2. No Logic Duplication
The Experimentation Framework must not reimplement:

- episode execution
- decision logic
- transition logic
- logging semantics

It must orchestrate existing components.

#### 3. No Hidden Mutation
Experiment execution must not mutate stored configurations or results after persistence.

#### 4. Explicit State and Artifact Flow
All execution units must have:

- explicit inputs
- explicit outputs
- explicit persisted artifacts

---

### 4.14 Implementation Consequence
Any implementation of the Experimentation Framework must therefore provide:

- a dedicated `RunExecutor`
- a dedicated `ExperimentExecutor`
- deterministic seed derivation across experiment, run, and episode levels
- sequential execution as the baseline strategy
- explicit lifecycle/status handling
- incremental persistence suitable for resume
- strict reuse of the existing `EpisodeRunner`
- clean separation from runtime, logging, and visualization

---

## 5. Configuration Model
The Configuration Model defines how experiments, runs, and their parameters are specified, resolved, and persisted.

It provides the **single source of truth** for all execution-relevant parameters and ensures that every run can be reproduced exactly from its stored configuration snapshot.

---

### 5.1 Design Goals
The configuration system must satisfy the following goals:

- **Deterministic**: identical configs must produce identical execution behavior
- **Explicit**: no hidden defaults at execution time
- **Serializable**: all configurations must be stored as JSON or YAML
- **Composable**: experiments derive multiple run configurations from a base definition
- **Immutable**: resolved configurations must not change after execution starts

---

### 5.2 Configuration Levels
The configuration model is structured across three levels:

#### Experiment Configuration (`ExperimentConfig`)

Defines:

- experiment identity and metadata
- experiment type (e.g., single run, OFAT)
- baseline configuration (reference)
- parameter variation rules
- run generation strategy
- global seed (optional)
- persistence settings

---

#### Run Configuration (`RunConfig`)
Defines a **fully resolved configuration** for execution.

Includes:

- agent configuration
- environment configuration
- policy configuration
- number of episodes
- seed definition (or resolved seed list)
- logging references (if applicable)
- run metadata (e.g., labels, tags)

**Important:**  
A `RunConfig` must be _fully concrete_.  
No unresolved parameters or variation rules are allowed at this level.

---

#### Episode Configuration (Implicit)
Episodes do not have their own config object.

They inherit:

- the full `RunConfig`
- a single episode seed

This keeps the runtime simple and avoids duplication.

---

### 5.3 Configuration Resolution
Configuration resolution is a one-way transformation:

```text
ExperimentConfig
    ↓ (expansion)
RunConfig (multiple)
    ↓ (execution)
Episode (implicit config + seed)
```

#### Rules:

- All parameter variations must be resolved **before execution**
- Each run receives a **fully materialized configuration snapshot**
- The snapshot must be persisted exactly as used

---

### 5.4 Experiment Types (Canonical)
To control complexity, the framework defines **canonical experiment types**.

#### 1. Single Run

- One `RunConfig`
- No parameter variation
- Used for:
    
    - debugging
    - baseline inspection


---

#### 2. OFAT (One-Factor-At-a-Time)
- Based on a **baseline configuration**
- One parameter varied per run
- All other parameters remain fixed

**Example:**

```text
baseline:
  policy.beta: 1.0

variation:
  policy.beta: [0.5, 1.0, 2.0]
```

This produces multiple runs, each differing only in one parameter.

---

#### Future (Not Implemented Yet)

- Grid search
- Random search
- Adaptive strategies

These must be explicitly introduced later and are not part of the baseline scope.

---

### 5.5 Baseline Configuration
Experiments may define a **baseline configuration**.

#### Purpose:

- Serves as reference point for comparisons
- Defines default values for all parameters

#### Requirements:

- Must be a complete, valid configuration
- Must be resolvable into a `RunConfig`

#### Usage in OFAT:

- All variations are applied relative to the baseline

---

### 5.6 Parameter Addressing
Parameters must be addressable using a **stable path-based system**.

#### **Example:**

```text
agent.energy.initial
policy.beta
environment.resource.regen_rate
```

#### Requirements:

- Paths must map directly to config structure
- Must support:
    
    - reading values
    - overriding values

- No dynamic or computed parameter names

This ensures predictable variation behavior.

---

### 5.7 Seed Strategy
The configuration model must define how seeds are handled.

#### **Options:**

**1. Explicit Seed List**

```text
seeds: [42, 43, 44, 45]
```

**2. Derived Seeds**

```text
base_seed: 42
num_episodes: 10
```

Seeds are then deterministically derived.

---

#### Requirements:

- Each episode must have a concrete seed
- Seeds must be stored in results
- Seed generation must be deterministic

---

### 5.8 Persistence of Configuration
Every run must persist its configuration:

```text
run_config.json
```

#### Requirements:

- Must represent the exact configuration used during execution
- Must not contain unresolved parameters
- Must include:
    
    - all runtime-relevant fields
    - resolved seed information


---

### 5.9 Validation
Configuration must be validated **before execution begins**.

#### Validation Scope:

- Required fields present
- Parameter paths valid
- Variation definitions consistent
- Seed definitions valid
- Experiment type constraints satisfied

#### Failure Behavior:

- Invalid configurations must fail fast
- No partial execution allowed for invalid configs

---

### 5.10 Minimal Schema Constraints
To avoid overengineering:

- No dynamic schema generation
- No plugin-based config extensions
- No runtime mutation of config structure

Instead:

- Use simple, explicit schemas
- Prefer flat, readable structures over too deeply nested abstractions

---

### 5.11 Relationship to Existing System
The configuration model must integrate with existing definitions:

- Must align with:
    
    - runtime configuration structures (agent, world, policy)

- Must not redefine:
    
    - state structures
    - result structures

- Must only orchestrate parameterization of existing components

---

## 6. Persistence Model
The Persistence Model defines how experiment definitions, run artifacts, results, and metadata are stored on disk.

Its purpose is to ensure that experiments are:

- reproducible
- inspectable
- resumable
- analyzable after execution
- independent of any database or external service

The baseline persistence strategy is intentionally **file-system-based**. This aligns with the current scope, keeps the system transparent, and avoids introducing infrastructure complexity too early. This is consistent with the broader architecture, where supporting systems must remain separate from runtime behavior and where reproducibility and inspectability are explicit design goals.

---

### 6.1 Design Goals
The persistence model must satisfy the following goals:

- **Transparency**  
    All persisted artifacts must be human-inspectable.
    
- **Deterministic Organization**  
    Directory and file structure must be stable and predictable.
    
- **Incremental Persistence**  
    Results must be written progressively during execution.
    
- **Resume Support**  
    Persisted state must allow interrupted experiments to continue safely.
    
- **Separation of Artifact Types**  
    Configurations, results, summaries, logs, and metadata must not be conflated.
    
- **Compatibility with Later Layers**  
    Stored artifacts must support:
    
    - CLI inspection
    - summary generation
    - posterior visualization
    - later offline analysis

---

### 6.2 Persistence Strategy
The baseline framework shall use a **directory-per-experiment** storage model.

Each experiment is represented by a dedicated directory containing:

- experiment definition
- execution metadata
- run-level artifacts
- references to observability outputs
- summaries

This approach supports:

- easy manual inspection
- robust resume behavior
- straightforward archival and copying
- decoupling from database infrastructure

---

### 6.3 Artifact Hierarchy on Disk
The persistence hierarchy mirrors the conceptual hierarchy of the framework:

```text
experiments/
  <experiment_id>/
    experiment_config.json
    experiment_metadata.json
    experiment_status.json
    experiment_summary.json

    runs/
      <run_id>/
        run_config.json
        run_metadata.json
        run_status.json
        run_summary.json
        run_result.json

        episodes/
          episode_0001.json
          episode_0002.json
          ...

        logs/
          run.log.jsonl
```

This structure is intended as the baseline target.  
Exact file naming may later be refined, but the structural separation must remain.

---

### 6.4 Persistence Units
The model distinguishes the following persistence units.

#### Experiment-Level Artifacts
Stored once per experiment:

- `experiment_config`
- experiment metadata
- experiment lifecycle/status
- experiment summary
- references to run artifacts

#### Run-Level Artifacts
Stored once per run:

- fully resolved `RunConfig`
- run metadata
- run lifecycle/status
- `RunSummary`
- `RunResult`
- references to episode artifacts and logs

#### Episode-Level Artifacts
Stored once per episode:

- `EpisodeResult`
- optional per-episode trace data, if not already embedded sufficiently in the result structure

The framework should avoid scattering equivalent information across multiple files unless the duplication is clearly intentional.

---

### 6.5 Source of Truth
The source of truth remains:

- `EpisodeResult`
- `RunResult`
- later `ExperimentResult`

Logs are not the primary data model.  
They are derived artifacts or references only. This follows the result-first contract already established in WP8 and WP10.

#### Implication

- Summaries must be derivable from results
- Resume must not depend on parsing logs
- Visualization must rely primarily on structured results and only secondarily on logs if needed later. This is also consistent with the pre-spec’s posterior replay principle.

---

### 6.6 File Formats
The baseline persistence model uses simple, explicit formats.

#### Configurations

- JSON or YAML for authoring
- JSON preferred for resolved persisted snapshots

#### Results and Summaries

- JSON

#### Step-Level or Log-Like Records

- JSONL where incremental append behavior is beneficial

This gives a practical split:

- **JSON/YAML** for structured configuration artifacts
- **JSON** for stable resolved result artifacts
- **JSONL** for append-oriented observability files

---

### 6.7 Experiment Metadata
Each experiment must persist explicit metadata separate from configuration.

At minimum this metadata should include:

- experiment identifier
- experiment type
- creation timestamp
- last updated timestamp
- baseline reference identifier or reference config marker
- total number of runs expected
- number of completed runs
- number of failed runs
- current lifecycle status

This metadata is needed for:

- CLI listing
- status inspection
- resume logic
- partial execution tracking

---

### 6.8 Run Metadata
Each run must persist metadata separate from its resolved `RunConfig`.

At minimum this metadata should include:

- run identifier
- parent experiment identifier
- run index or ordering position
- canonical experiment type association
- parameter variation descriptor
- resolved seed context
- episode count
- lifecycle status
- timestamps

This allows the framework to inspect and manage runs without loading full runtime results first.

---

### 6.9 Lifecycle and Status Persistence
Status must be persisted explicitly, not inferred indirectly from missing files.

#### Experiment Status
At minimum:

- `CREATED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `PARTIAL`

#### Run Status
At minimum:

- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`

This explicit persistence is required for:

- robust resume behavior
- crash recovery
- CLI inspection
- failure diagnosis

---

### 6.10 Incremental Write Strategy
Persistence must be incremental.

#### Requirements

- experiment metadata written before run execution starts
- run metadata and run config written before a run begins
- episode results written as episodes complete
- run summary and run result written when run completes
- experiment summary updated as runs complete or when the experiment ends

This ensures that interruption at any point leaves meaningful persisted state behind.

---

### 6.11 Resume Semantics
The persistence model must support resumable execution.

#### Baseline Resume Rule
Resume should operate primarily at the **run level**.

That means:

- completed runs are detected from persisted status/artifacts
- completed runs are not recomputed
- pending or failed runs may be resumed or rerun depending on framework policy

#### Primary Requirement
Persistence must make it possible to determine unambiguously:

- which runs exist
- which runs completed successfully
- which runs failed
- which runs remain unexecuted

Optional finer-grained episode-level resume may be introduced later if needed, but the run-level boundary is the baseline design target.

---

### 6.12 Artifact Immutability
Persisted configuration and result artifacts should be treated as immutable once finalized.

#### **Implications**

- `run_config.json` must not be rewritten after execution starts
- completed `run_result.json` must not be silently mutated
- experiment summary may be recomputed if explicitly designed to do so, but raw results must remain unchanged

This is essential for auditability and reproducibility.

---

### 6.13 Identifier Strategy
The persistence model requires stable identifiers.

#### Experiment IDs
Must be unique within the experiment repository.

#### Run IDs
Must be unique within an experiment and stable across resume operations.

#### Episode IDs
Must be unique within a run and derivable from run context plus episode index.

The exact formatting convention can be defined later, but the persistence model assumes that all artifacts can be addressed deterministically via these IDs.

---

### 6.14 References to Observability Artifacts
The persistence model shall store references to observability artifacts rather than duplicating them unnecessarily.

Examples include:

- path to run-level JSONL log
- path to step-level trace files if separated
- future replay-specific derived artifact paths

This is directly aligned with the experimentation framework requirement to integrate with observability without replacing it.

---

### 6.15 Repository Root and Discovery
The framework should assume a single configurable repository root for experiment storage, for example:

```text
./experiments/
```

This root acts as the discovery location for:

- experiment listing
- experiment lookup by ID
- resume operations
- summary inspection

CLI commands should operate against this repository root by default.

---

### 6.16 Failure Handling and Persistence Safety
The persistence model must preserve already completed work even when execution fails.

#### Requirements

- failed run must not invalidate completed runs
- partially written artifacts must be detectable
- status must reflect incomplete state explicitly
- framework must prefer explicit failure markers over silent inconsistency

If needed, temporary write files or atomic rename patterns may be introduced later, but the baseline architecture should already assume that partially written state is possible and must be handled safely.

---

### 6.17 Relationship to Visualization
The persistence model must support later posterior visualization.

This means persisted artifacts must preserve or reference all information needed for replay, including at minimum:

- step ordering
- agent position
- action sequence
- energy state
- resource/world state sufficient for replay
- run and episode identity

This follows directly from the pre-spec’s visualization requirements, which require posterior replay from recorded execution data and strict read-only visualization.

---

### 6.18 Architectural Constraints
The following constraints are mandatory:

#### 1. No Database Dependency
The baseline persistence model must work entirely on the file system.

#### 2. No Hidden In-Memory State
All information required for resume and inspection must be derivable from persisted artifacts.

#### 3. No Log-Only Correctness
Correctness and reconstruction must not depend on parsing human-readable logs.

#### 4. Clear Artifact Boundaries
Configuration, results, summaries, metadata, and logs must remain structurally separated.

#### 5. Stable On-Disk Contract
The directory and file conventions must be stable enough that CLI tooling and later visualization can rely on them.

---

### 6.19 Implementation Consequence
Any implementation of the persistence model must therefore provide:

- a deterministic experiment directory structure
- explicit persisted artifacts for experiment, run, and episode levels
- JSON/YAML-based configuration storage
- JSON-based result and summary storage
- JSONL support where incremental append is useful
- explicit lifecycle/status files or equivalent persisted status fields
- incremental write behavior suitable for resume
- immutable finalized raw artifacts
- references to observability outputs
- artifact completeness sufficient for later replay and analysis

---

## 7. Result and Summary Model
The Result and Summary Model defines how execution outcomes are represented, aggregated, and interpreted across episodes, runs, and experiments.

It builds directly on the result structures introduced in WP8 and extends them with **standardized summaries** required for statistical analysis and comparison.

The key design principle is:

> **Results are the source of truth. Summaries are derived views.**

---

### 7.1 Design Goals
The model must satisfy the following goals:

- **Consistency**  
    All summaries must be derivable from persisted results.
    
- **Clarity**  
    Clear separation between raw results and aggregated metrics.
    
- **Minimalism**  
    Only a small, well-defined set of summary metrics is required initially.
    
- **Determinism**  
    Summary computation must be deterministic and reproducible.
    
- **Extensibility**  
    Additional metrics can be added later without breaking existing artifacts.

---

### 7.2 Result Hierarchy
The Result Model follows the execution hierarchy:

```text
EpisodeResult → RunResult → ExperimentResult
```

Each level aggregates information from the level below.

---

### 7.3 EpisodeResult (WP8 Reference)
The `EpisodeResult` is the atomic output of the system.

It contains:

- final state (e.g., final energy)
- termination condition (e.g., death, max steps)
- total steps
- total consumption events
- optional step-level trace or references
- seed used for the episode

**Role:**

- Primary raw data unit
- Input for all aggregation

No statistical interpretation is performed at this level.

---

### 7.4 RunResult (WP8 Reference)
The `RunResult` represents the outcome of multiple episodes under a single configuration.

It contains:

- reference to `RunConfig`
- list (or references) of `EpisodeResult`s
- run metadata (IDs, timestamps, status)
- `RunSummary` (defined below)

**Role:**

- Primary unit for statistical analysis
- Boundary between raw execution and aggregated insight

---

### 7.5 ExperimentResult (New)
The `ExperimentResult` aggregates multiple runs.

It contains:

- reference to `ExperimentConfig`
- collection of run references or `RunResult`s
- experiment metadata (IDs, timestamps, status)
- `ExperimentSummary` (defined below)

**Role:**

- Provides comparative view across configurations
- Enables parameter impact analysis

---

### 7.6 RunSummary (New)
The `RunSummary` provides a fixed set of aggregated metrics derived from all episodes in a run.

#### Purpose

- Provide a compact statistical representation of a run
- Enable comparison between runs without inspecting individual episodes

---

#### Minimal Required Metrics
The initial schema should include:

- `num_episodes`
- `mean_steps`
- `std_steps`
- `mean_final_energy`
- `std_final_energy`
- `death_rate`  
    (fraction of episodes where agent energy reached zero)
- `mean_consumption_count`
- `std_consumption_count`

---

#### Optional Metrics (If Available in EpisodeResult)

- distribution histograms (not required initially)
- min / max values
- time-to-death statistics
- survival ratio over time

---

#### Computation Rules

- All metrics must be computed **only from EpisodeResult data**
- No dependence on logs
- Missing or invalid episodes must be handled explicitly (not silently ignored)

---

### 7.7 ExperimentSummary (New)
The `ExperimentSummary` aggregates results across multiple runs.

#### Purpose

- Enable comparison between configurations
- Provide a high-level overview of experiment outcomes

---

#### Core Elements
For each run:

- reference to run ID
- key parameter variation descriptor
- `RunSummary`

Additionally:

- ranking or ordering (optional, but useful)
- comparison relative to baseline (if defined)

---

#### Baseline Comparison (If Applicable)
If a baseline configuration is defined:

- compute relative differences:
    
    - delta in mean steps
    - delta in death rate
    - delta in energy metrics


This enables direct interpretation of parameter effects.

---

### 7.8 Summary Determinism
All summaries must be:

- reproducible from stored results
- independent of execution order
- independent of external state

#### Implication

- Summaries may be recomputed at any time
- Stored summaries are caches, not authoritative sources

---

### 7.9 Relationship to Persistence
The following artifacts must be persisted:

#### Run Level

- `run_result.json`
- `run_summary.json` (or embedded in run result)

#### Experiment Level

- `experiment_summary.json`

#### Design Choice
Summaries may be:

- embedded within result objects  
    **or**
- stored as separate artifacts

Both are acceptable, but the structure must be consistent.

---

### 7.10 Handling Partial and Failed Data
The model must explicitly handle incomplete or failed runs.

#### Run Level

- Failed episodes must be:
    
    - recorded
    - excluded or flagged in summary computation

#### Experiment Level

- Failed runs must:
    
    - remain visible
    - not invalidate other runs

#### Summary Behavior

- Summaries must clearly indicate:
    
    - number of valid episodes
    - number of failed episodes

---

### 7.11 Minimal Schema Stability
The initial summary schema must remain stable.

#### Constraints

- Do not frequently change field names
- Additive changes are allowed
- Breaking changes must be avoided

This is important for:

- CLI tooling
- downstream analysis
- visualization layer

---

### 7.12 Relationship to Logging
The Result and Summary Model must not depend on logs.

#### Principle

- Results are structured, validated data
- Logs are observational and optional

#### Implication

- All metrics must be derivable from results alone
- Logs may provide additional debugging context, but not required for correctness

---

### 7.13 Relationship to Visualization
The Result Model must support later visualization requirements.

This implies:

- Episode-level data must contain or reference:
    
    - step sequence
    - actions
    - positions
    - energy evolution
    - relevant world state information

- Summaries must support:
    
    - filtering
    - selection of interesting runs/episodes
    - identification of outliers

Visualization remains a separate layer that operates on these persisted artifacts.

---

### 7.14 Implementation Consequence
Any implementation must therefore provide:

- deterministic aggregation from `EpisodeResult` to `RunSummary`
- deterministic aggregation from `RunSummary` to `ExperimentSummary`
- stable schemas for:
    
    - `RunSummary`
    - `ExperimentSummary`

- explicit handling of partial and failed data
- persistence of summaries alongside results
- strict independence from logging data

---

## 8. CLI Interface
The CLI Interface provides a minimal, scriptable entry point to the Experimentation Framework.

It enables users to:

- execute experiments
- inspect results
- manage experiment lifecycle (including resume)
- navigate persisted artifacts

The CLI is intentionally designed as a **thin operational layer** over the underlying system. It does not introduce new abstractions, nor does it reinterpret domain models.

---

### 8.1 Design Goals
The CLI must satisfy the following goals:

- **Directness**  
    Commands map directly to domain concepts (`experiment`, `run`)
    
- **Simplicity**  
    Minimal command surface, no unnecessary abstraction layers
    
- **Scriptability**  
    All commands must be usable in automation pipelines
    
- **Deterministic Behavior**  
    No interactive prompts required for core operations
    
- **Transparency**  
    CLI output reflects real persisted data, not derived or hidden views

---

### 8.2 Conceptual Mapping
The CLI mirrors the conceptual model:

|Concept|CLI Entity|
|---|---|
|Experiment|`experiments`|
|Run|`runs`|
|Execution|`run` / `resume`|
|Inspection|`list` / `show`|

No additional abstraction layer is introduced.

---

### 8.3 Command Structure
The CLI follows a hierarchical command structure:

```text
axis <entity> <action> [arguments]
```

Where:

- `<entity>` ∈ { `experiments`, `runs` }
- `<action>` defines the operation

---

### 8.4 Core Commands
#### List Experiments

```bash
axis experiments list
```

**Purpose:**

- List all experiments in the repository root

**Output (example):**

- experiment_id
- status
- number of runs
- number of completed runs
- creation timestamp

---

#### Run Experiment

```bash
axis experiments run <path_to_experiment_config>
```

**Purpose:**

- Execute a new experiment from configuration

**Behavior:**

- validates configuration
- creates experiment directory
- initializes metadata
- executes all runs sequentially
- persists results incrementally

---

#### Resume Experiment

```bash
axis experiments resume <experiment_id>
```

**Purpose:**

- Resume an interrupted or partial experiment

**Behavior:**

- loads experiment metadata
- detects completed runs
- executes only missing or incomplete runs

---

#### Show Experiment

```bash
axis experiments show <experiment_id>
```

**Purpose:**

- Inspect experiment-level information

**Output includes:**

- configuration reference
- status
- run overview
- experiment summary (if available)

---

#### **List Runs (within Experiment)**

```bash
axis runs list --experiment <experiment_id>
```

**Purpose:**

- List all runs belonging to an experiment

---

#### Show Run

```bash
axis runs show <run_id>
```

**Purpose:**

- Inspect a single run

**Output includes:**

- resolved configuration
- run status
- run summary
- episode count
- references to stored artifacts

---

### 8.5 Output Philosophy
The CLI must expose **real system data**, not presentation abstractions.

#### Principles:

- Output reflects persisted artifacts directly
- No hidden aggregation beyond defined summaries
- Prefer structured output formats (e.g., JSON) where appropriate

#### Optional Modes (future):

- human-readable table view
- JSON output for scripting

---

### 8.6 Interaction Model
The CLI is:

- **non-interactive by default**
- driven entirely by arguments and configuration files

#### Implications:

- No prompts during execution
- No runtime decision-making via CLI input
- All behavior defined via config or command flags

---

### 8.7 Integration with Persistence
All CLI operations are backed by the persistence model.

#### Examples:

- `experiments list` → scans experiment directory
- `experiments show` → reads `experiment_metadata.json`, `experiment_summary.json`
- `runs show` → reads run-level artifacts

The CLI must not rely on in-memory state.

---

### 8.8 Error Handling
The CLI must fail explicitly and clearly.

#### Examples:

- unknown experiment ID → error
- invalid config → error before execution
- missing artifacts → explicit failure message

#### Constraint:

- No silent fallbacks
- No implicit default behavior

---

### 8.9 Minimal Flags (Initial Scope)
The initial CLI should support only essential flags.

Examples:

```bash
--experiment <experiment_id>
--output json
--root <path_to_experiment_repository>
```

Advanced CLI features (filtering, querying, formatting) are out of scope initially.

---

### 8.10 Relationship to Execution Layer
The CLI must act as a thin wrapper over:

- `ExperimentExecutor`
- `RunExecutor`

#### Constraint:

- No business logic in CLI layer
- CLI only:
    
    - parses arguments
    - loads configs
    - invokes executors
    - displays results

---

### 8.11 Determinism and Idempotency
CLI commands must be safe to repeat where appropriate.

#### Examples:

- `resume` should not duplicate completed runs
- `run` should fail if experiment ID already exists (unless explicitly allowed in future)

---

### 8.12 Extensibility Constraints
The CLI must remain minimal.

#### Avoid:

- embedding analysis logic
- embedding visualization logic
- adding ad-hoc commands without architectural justification

#### Allowed Extensions:

- additional inspection commands
- filtering capabilities
- export functions (later)

---

### 8.13 Implementation Consequence
Any CLI implementation must:

- map directly to domain entities (`experiment`, `run`)
- operate purely on persisted artifacts
- invoke execution through defined executors
- remain stateless between invocations
- support resume semantics
- provide deterministic and explicit outputs

---

## 9. Fault Tolerance and Resume
The Fault Tolerance and Resume model defines how the Experimentation Framework behaves under interruption, failure, and partial execution.

Its purpose is to ensure that:

- no completed work is lost
- partial progress remains usable
- experiments can be safely continued
- failures are explicit and diagnosable

This is a critical requirement for long-running experiments and aligns directly with the design principles of reproducibility and incremental persistence.

---

### 9.1 Design Goals
The system must guarantee:

- **Durability**  
    Completed runs and episodes are never lost after persistence
- **Resumability**  
    Interrupted experiments can continue without recomputing completed work
- **Transparency**  
    System state must be inspectable at all times
- **Determinism**  
    Resume behavior must be predictable and consistent
- **Isolation of Failures**  
    Failure in one run must not invalidate other runs

---

### 9.2 Failure Scope
Failures may occur at different levels:

#### 1. Episode-Level Failure

- Failure during execution of a single episode

#### 2. Run-Level Failure

- Failure during execution of a run (e.g., crash mid-run)

#### 3. Experiment-Level Failure

- Failure affecting orchestration across runs

#### 4. System-Level Interruption

- External interruption (process kill, machine shutdown)

The framework must handle all of these without corrupting already completed work.

---

### 9.3 Persistence as the Foundation of Fault Tolerance
Fault tolerance is achieved through **incremental persistence**.

#### Requirements:

- Experiment metadata written before execution begins
- Run metadata and config written before run execution
- Episode results written immediately after completion
- Run results written immediately after run completion

#### Implication:
At any interruption point, the system must be able to reconstruct:

- which runs exist
- which runs completed
- which runs failed or are incomplete

---

### 9.4 Resume Boundary
The primary resume boundary is the **Run**.

#### Behavior:

- Completed runs → skipped
- Pending runs → executed
- Failed runs → re-executed or flagged (policy-defined)

#### Rationale:

- Keeps implementation manageable
- Aligns with statistical unit (Run)
- Avoids complex intra-run recovery logic

---

### 9.5 Run-Level Resume Semantics
A run is considered **completed** if:

- `run_status == COMPLETED`
- required artifacts exist:
    
    - `run_result`
    - `run_summary`

A run is considered **incomplete** if:

- status is `RUNNING` or `FAILED`
- artifacts are missing or partial

#### Resume Behavior:

- Incomplete runs are candidates for re-execution
- Partial episode data may be:
    
    - discarded (simplest baseline)
    - or reused (optional future extension)

---

### 9.6 Episode-Level Handling
Episode-level resume is not required in the baseline design.

#### Baseline Behavior:

- If a run is restarted:
    
    - all episodes are re-executed

#### Rationale:

- Avoids complexity in:
    
    - partial aggregation
    - seed tracking
    - consistency guarantees

#### Future Extension:

- Episode-level resume may be introduced if needed
    

---

### 9.7 Status-Driven Execution Control
Resume logic must rely on **explicit persisted status**, not inference.

#### Run Status Transitions:

```text
PENDING → RUNNING → COMPLETED
                 ↘ FAILED
```

#### Experiment Status Transitions:

```text
CREATED → RUNNING → COMPLETED
                   ↘ PARTIAL
                   ↘ FAILED
```

#### Rules:

- Status must be updated explicitly
- No implicit status inference from missing files
- Status must reflect real execution state

---

### 9.8 Idempotency Guarantees
Execution operations must be idempotent where possible.

#### Examples:

- Running `resume` multiple times:
    
    - must not duplicate completed runs

- Re-running a completed experiment:
    
    - must not overwrite existing results unless explicitly allowed (future)


---

### 9.9 Failure Handling Strategy

#### Episode Failure

- Episode failure must be recorded
- Episode may be:
    
    - marked as failed
    - excluded or flagged in summary computation

#### Run Failure

- Run status set to `FAILED`
- Partial episode results remain persisted
- Does not affect other runs

#### Experiment Failure

- Experiment status set to:
    
    - `PARTIAL` if some runs completed
    - `FAILED` if no valid runs completed

---

### 9.10 Detection of Incomplete State
The system must detect incomplete or inconsistent artifacts.

#### Indicators:

- missing `run_result`
- missing `run_summary`
- status mismatch with artifacts
- partially written files

#### Behavior:

- treat as incomplete
- mark run as `FAILED` or `PENDING`
- allow re-execution

---

### 9.11 Safe Write Strategy
To reduce risk of corruption:

#### Recommended (Baseline-Compatible):

- write files only after data is complete
- avoid overwriting existing valid artifacts

#### Optional (Future):

- temporary files + atomic rename
- checksum validation

The baseline design must already assume that partial writes are possible and handle them safely.

---

### 9.12 Consistency Guarantees
The system guarantees:

- completed runs remain valid across restarts
- experiment state can always be reconstructed from disk
- resume will not produce duplicated or conflicting results

The system does **not guarantee**:

- recovery of partially completed runs at episode granularity
- recovery from corrupted artifacts without re-execution

---

### 9.13 Interaction with CLI
CLI commands must respect resume semantics.

#### **Examples:**

- `axis experiments resume <id>`
    
    - continues incomplete runs only

- `axis experiments run <config>`
    
    - fails if experiment already exists (baseline behavior)

CLI must not override fault tolerance logic.

---

### 9.14 Observability and Failure Diagnosis
Failures must be diagnosable using:

- run and experiment status
- structured results (partial if needed)
- referenced logs

Logs provide context, but correctness must not depend on them.

---

### 9.15 Implementation Consequence
Any implementation must therefore provide:

- explicit status tracking for runs and experiments
- incremental persistence at all execution levels
- deterministic detection of completed vs. incomplete runs
- run-level resume as baseline mechanism
- safe handling of partial or failed runs
- idempotent resume behavior
- strict isolation between runs
- clear failure signaling without silent recovery

---

## **10. Testing Strategy**
## 9. Fault Tolerance and Resume**

The Fault Tolerance and Resume model defines how the Experimentation Framework behaves under interruption, failure, and partial execution.

Its purpose is to ensure that:

* no completed work is lost
* partial progress remains usable
* experiments can be safely continued
* failures are explicit and diagnosable

This is a critical requirement for long-running experiments and aligns directly with the design principles of reproducibility and incremental persistence.

---

### 9.1 Design Goals**

The system must guarantee:

* **Durability**
  Completed runs and episodes are never lost after persistence

* **Resumability**
  Interrupted experiments can continue without recomputing completed work

* **Transparency**
  System state must be inspectable at all times

* **Determinism**
  Resume behavior must be predictable and consistent

* **Isolation of Failures**
  Failure in one run must not invalidate other runs

---

### 9.2 Failure Scope**

Failures may occur at different levels:

#### 1. Episode-Level Failure**

* Failure during execution of a single episode

#### 2. Run-Level Failure**

* Failure during execution of a run (e.g., crash mid-run)

#### 3. Experiment-Level Failure**

* Failure affecting orchestration across runs

#### 4. System-Level Interruption**

* External interruption (process kill, machine shutdown)

The framework must handle all of these without corrupting already completed work.

---

### 9.3 Persistence as the Foundation of Fault Tolerance**

Fault tolerance is achieved through **incremental persistence**.

#### Requirements:**

* Experiment metadata written before execution begins
* Run metadata and config written before run execution
* Episode results written immediately after completion
* Run results written immediately after run completion

#### Implication:**

At any interruption point, the system must be able to reconstruct:

* which runs exist
* which runs completed
* which runs failed or are incomplete

---

### 9.4 Resume Boundary**

The primary resume boundary is the **Run**.

#### Behavior:**

* Completed runs → skipped
* Pending runs → executed
* Failed runs → re-executed or flagged (policy-defined)

#### Rationale:**

* Keeps implementation manageable
* Aligns with statistical unit (Run)
* Avoids complex intra-run recovery logic

---

### 9.5 Run-Level Resume Semantics**

A run is considered **completed** if:

* `run_status == COMPLETED`
* required artifacts exist:

  * `run_result`
  * `run_summary`

A run is considered **incomplete** if:

* status is `RUNNING` or `FAILED`
* artifacts are missing or partial

#### Resume Behavior:**

* Incomplete runs are candidates for re-execution
* Partial episode data may be:

  * discarded (simplest baseline)
  * or reused (optional future extension)

---

### 9.6 Episode-Level Handling**

Episode-level resume is not required in the baseline design.

#### Baseline Behavior:**

* If a run is restarted:

  * all episodes are re-executed

#### Rationale:**

* Avoids complexity in:

  * partial aggregation
  * seed tracking
  * consistency guarantees

#### Future Extension:**

* Episode-level resume may be introduced if needed

---

### 9.7 Status-Driven Execution Control**

Resume logic must rely on **explicit persisted status**, not inference.

#### Run Status Transitions:**

```text id="1n6b2c"
PENDING → RUNNING → COMPLETED
                 ↘ FAILED
```

#### Experiment Status Transitions:**

```text id="q7t3lh"
CREATED → RUNNING → COMPLETED
                   ↘ PARTIAL
                   ↘ FAILED
```

#### Rules:**

* Status must be updated explicitly
* No implicit status inference from missing files
* Status must reflect real execution state

---

### 9.8 Idempotency Guarantees**

Execution operations must be idempotent where possible.

#### Examples:**

* Running `resume` multiple times:

  * must not duplicate completed runs
* Re-running a completed experiment:

  * must not overwrite existing results unless explicitly allowed (future)

---

### 9.9 Failure Handling Strategy**

#### Episode Failure**

* Episode failure must be recorded
* Episode may be:

  * marked as failed
  * excluded or flagged in summary computation

#### Run Failure**

* Run status set to `FAILED`
* Partial episode results remain persisted
* Does not affect other runs

#### Experiment Failure**

* Experiment status set to:

  * `PARTIAL` if some runs completed
  * `FAILED` if no valid runs completed

---

### 9.10 Detection of Incomplete State**

The system must detect incomplete or inconsistent artifacts.

#### Indicators:**

* missing `run_result`
* missing `run_summary`
* status mismatch with artifacts
* partially written files

#### Behavior:**

* treat as incomplete
* mark run as `FAILED` or `PENDING`
* allow re-execution

---

### 9.11 Safe Write Strategy**

To reduce risk of corruption:

#### Recommended (Baseline-Compatible):**

* write files only after data is complete
* avoid overwriting existing valid artifacts

#### Optional (Future):**

* temporary files + atomic rename
* checksum validation

The baseline design must already assume that partial writes are possible and handle them safely.

---

### 9.12 Consistency Guarantees**

The system guarantees:

* completed runs remain valid across restarts
* experiment state can always be reconstructed from disk
* resume will not produce duplicated or conflicting results

The system does **not guarantee**:

* recovery of partially completed runs at episode granularity
* recovery from corrupted artifacts without re-execution

---

### 9.13 Interaction with CLI**

CLI commands must respect resume semantics.

#### Examples:**

* `axis experiments resume <id>`

  * continues incomplete runs only

* `axis experiments run <config>`

  * fails if experiment already exists (baseline behavior)

CLI must not override fault tolerance logic.

---

### 9.14 Observability and Failure Diagnosis**

Failures must be diagnosable using:

* run and experiment status
* structured results (partial if needed)
* referenced logs

Logs provide context, but correctness must not depend on them.

---

### 9.15 Implementation Consequence**

Any implementation must therefore provide:

* explicit status tracking for runs and experiments
* incremental persistence at all execution levels
* deterministic detection of completed vs. incomplete runs
* run-level resume as baseline mechanism
* safe handling of partial or failed runs
* idempotent resume behavior
* strict isolation between runs
* clear failure signaling without silent recovery

---

## 10. Testing Strategy
The Testing Strategy defines how the Experimentation Framework is validated across its major responsibilities:

* configuration resolution
* run orchestration
* experiment orchestration
* persistence behavior
* summary computation
* fault tolerance and resume
* CLI integration

Because this framework sits above an already implemented and tested runtime, the goal is not to retest the full core simulation logic in detail, but to ensure that the new orchestration layer is:

* correct
* reproducible
* robust under interruption
* aligned with existing system contracts

This is fully consistent with the general engineering principle that every module must be testable in isolation and that deterministic execution must be validated explicitly.

---

### 10.1 Testing Objectives
The testing strategy must ensure:

* **Correctness**
  The framework produces valid runs, experiments, summaries, and persisted artifacts.

* **Reproducibility**
  Identical configurations and seeds produce identical results.

* **Robustness**
  Interruptions and failures do not corrupt completed work.

* **Contract Alignment**
  The framework respects the interfaces and invariants of:

  * `EpisodeRunner`
  * `EpisodeResult`
  * `RunResult`
  * logging/observability references

* **Usability**
  The CLI behaves predictably and transparently.

---

### 10.2 Scope of Testing
The Experimentation Framework testing strategy covers:

#### In Scope

* configuration parsing and validation
* experiment type resolution
* sweep expansion
* seed derivation
* run execution orchestration
* experiment execution orchestration
* persistence of artifacts
* summary computation
* status transitions
* resume behavior
* CLI behavior

#### Out of Scope

* revalidation of detailed runtime internals already covered by WP1–WP10 unit tests
* visualization correctness
* parallel execution
* database integration
* advanced statistical analysis correctness

The framework should reuse confidence from the existing runtime test base rather than duplicate it unnecessarily.

---

### 10.3 Testing Layers
The testing strategy shall be multi-layered.

---

#### 1. Unit Tests
Unit tests validate individual components in isolation.

Target components include:

* configuration resolvers
* sweep expanders
* seed generators
* summary calculators
* status evaluators
* persistence helpers
* CLI argument parsing helpers

**Goal:**

* verify local correctness
* detect regressions early
* keep failures easy to diagnose

---

#### 2. Integration Tests
Integration tests validate interaction between components.

Examples:

* `ExperimentExecutor -> RunExecutor -> EpisodeRunner`
* persistence + summary generation
* resume logic over actual stored artifacts
* CLI command invoking real execution path

**Goal:**

* verify that components cooperate correctly
* validate artifact flow and lifecycle behavior

---

#### 3. End-to-End Tests
End-to-end tests validate complete experiment workflows.

Examples:

* execute a full single-run experiment from config file
* execute an OFAT experiment
* interrupt and resume an experiment
* inspect summaries via CLI after execution

**Goal:**

* validate user-visible behavior
* validate end-to-end reproducibility

---

### 10.4 Core Test Categories
The following categories must be covered explicitly.

---

#### A. Configuration Tests
Validate:

* `ExperimentConfig` parsing
* `RunConfig` resolution
* baseline config handling
* canonical experiment type validation
* invalid parameter paths
* invalid sweep definitions
* invalid seed specifications

These tests must fail fast and explicitly on malformed input.

---

#### B. Sweep Expansion Tests
Validate:

* single-run experiment produces exactly one `RunConfig`
* OFAT produces one run per candidate value
* OFAT uses the baseline config correctly
* only the targeted parameter changes
* run ordering is deterministic

This is especially important because the pre-spec explicitly requires declarative sweeps and deterministic expansion.

---

#### C. Seed Strategy Tests
Validate:

* deterministic seed derivation from `base_seed`
* stable episode seed generation within a run
* identical config + identical seed strategy -> identical seed assignments
* different seeds -> different assignments where expected

These tests are critical because reproducibility is one of the primary reasons this framework exists.

---

#### D. Run Execution Tests
Validate:

* a run executes the configured number of episodes
* each episode receives the correct resolved config and seed
* `RunResult` is constructed correctly
* `RunSummary` is derived correctly
* failed episodes are handled explicitly

These tests treat the `RunExecutor` as the primary new statistical execution unit.

---

#### E. Experiment Execution Tests
Validate:

* multiple runs execute in correct order
* experiment metadata is created correctly
* `ExperimentSummary` is constructed correctly
* experiment status transitions are correct
* failed runs do not invalidate completed runs

---

#### F. Persistence Tests
Validate:

* correct directory structure is created
* required files are written
* run and experiment metadata persist correctly
* result artifacts are readable after execution
* partial state is detectable

These tests must operate on a temporary filesystem and not rely on global state.

---

#### G. Resume Tests
Validate:

* completed runs are skipped during resume
* incomplete runs are executed during resume
* repeated resume is idempotent
* interrupted experiment can be continued safely
* partial state is handled deterministically

This is one of the most important categories for the experimentation layer.

---

#### H. Summary Tests
Validate:

* `RunSummary` is computed only from `EpisodeResult`
* `ExperimentSummary` is computed only from run-level results
* summary values are numerically correct
* failed/partial data is handled explicitly
* stored summaries match recomputed summaries

This preserves the principle that summaries are derived, not primary.

---

#### I. CLI Tests
Validate:

* `experiments list`
* `experiments run`
* `experiments resume`
* `experiments show`
* `runs list`
* `runs show`

Tests should verify:

* exit behavior
* artifact creation
* correct resolution of IDs and paths
* explicit error messages for invalid input

---

### 10.5 Determinism Testing
Determinism must be treated as a first-class testing concern.

#### Required Determinism Checks

* same experiment config + same seeds -> identical run configs
* same run config + same episode seeds -> identical `RunResult`
* same persisted artifacts -> same recomputed summaries
* repeated resume on a completed experiment -> no change

Where exact byte-for-byte equality is too strict because of timestamps or metadata, tests should compare the deterministic core fields explicitly.

---

### 10.6 Test Data Strategy
The Experimentation Framework should use controlled, minimal test data.

#### Preferred Test Inputs

* small handcrafted configs
* small episode counts
* deterministic seeds
* temporary directories for persistence tests

#### Avoid

* large sweeps
* unnecessary runtime complexity
* dependence on real external infrastructure

This keeps tests fast, stable, and understandable.

---

### 10.7 Reuse of Existing Test Support
The framework should reuse the testing support already introduced in WP9 wherever possible.

This includes:

* builders
* fixtures
* assertion helpers
* canonical behavioral scenarios

Examples:

* `WorldBuilder`
* `AgentStateBuilder`
* result assertion helpers
* deterministic runtime scenarios

This avoids duplication and keeps the experimentation tests aligned with the existing test system.

---

### 10.8 Recommended Test Structure
A reasonable structure could be:

```text id="r0wdx5"
tests/
  unit/
    experimentation/
      test_config_resolution.py
      test_sweep_expansion.py
      test_seed_strategy.py
      test_summary_calculation.py
      test_status_model.py

  integration/
    experimentation/
      test_run_executor.py
      test_experiment_executor.py
      test_persistence_flow.py
      test_resume_flow.py

  e2e/
    experimentation/
      test_single_run_experiment.py
      test_ofat_experiment.py
      test_cli_run_and_show.py
      test_cli_resume.py
```

This structure should remain consistent with the taxonomy already established in WP9. 

---

### 10.9 Failure Testing
The testing strategy must explicitly include failure cases.

Examples:

* invalid config path
* unknown experiment type
* invalid parameter address
* missing required artifact during resume
* inconsistent status vs. stored files
* simulated failure during run execution
* simulated partial artifact write

These tests are essential because the framework’s value depends heavily on graceful handling of imperfect execution conditions.

---

### 10.10 Test Philosophy for the CLI
CLI tests must not become “UI formatting tests”.

The primary goal is to verify:

* correct command routing
* correct use of executors
* correct interaction with persisted artifacts
* explicit and predictable failure behavior

Formatting details should only be tested where they affect machine usage or user comprehension materially.

---

### 10.11 Acceptance Criteria
The experimentation framework testing strategy is considered adequate when:

* each major component has isolated unit coverage
* core orchestration paths have integration coverage
* at least one full single-run and one OFAT workflow have end-to-end coverage
* determinism is explicitly validated
* resume behavior is explicitly validated
* artifact persistence and reconstruction are explicitly validated
* existing runtime tests are reused rather than duplicated unnecessarily

---

### 10.12 Implementation Consequence
Any implementation of the Experimentation Framework must therefore provide:

* unit-testable components for config, sweeps, seeds, summaries, and status logic
* integration-testable executors and persistence behavior
* end-to-end testable CLI workflows
* deterministic test fixtures and configs
* explicit failure tests for invalid and partial states
* reuse of WP9 test support where appropriate
* specific determinism and resume regression tests

---

## 11. Extension Points and Future Work Boundaries
The Experimentation Framework is designed to be extensible, but not open-ended.

This section defines:

* where extension is explicitly supported
* which areas are intentionally deferred
* which boundaries must not be violated by future changes

The goal is to enable evolution of the system without destabilizing the core architecture or introducing uncontrolled complexity.

---

### 11.1 Design Philosophy
The framework follows a constrained extensibility approach:

* **Extension points are explicit**
* **Core abstractions remain stable**
* **No premature generalization**
* **No plugin system in the baseline**

Future functionality must build on top of existing concepts, not bypass or replace them.

---

### 11.2 Stable Core Contracts
The following components are considered **architecturally stable** and must not be redefined:

* `EpisodeRunner` (WP7)
* `EpisodeResult` (WP8)
* Logging contracts and references (WP10)
* Conceptual hierarchy:

  * Episode → Run → Experiment

Any extension must operate within these boundaries.

---

### 11.3 Execution Layer Extensions

#### Future: Parallel Execution
The current execution model is strictly sequential.

A future extension may introduce:

* parallel execution of runs
* parallel execution of episodes within a run

**Constraints:**

* must preserve determinism where required
* must not break persistence model
* must not change result semantics
* must respect seed determinism

---

#### Future: Distributed Execution
Possible extension:

* distributing runs across multiple processes or nodes

**Constraints:**

* persistence model must remain valid
* experiment structure must not change
* results must remain mergeable without ambiguity

---

### 11.4 Experiment Strategy Extensions
The framework currently supports:

* Single Run
* OFAT

Future strategies may include:

* Grid Search
* Random Search
* Adaptive search (e.g., Bayesian optimization)

**Constraints:**

* must produce deterministic sets of `RunConfig`s (where applicable)
* must not introduce implicit behavior
* must integrate with existing `ExperimentExecutor`
* must not bypass baseline configuration semantics

---

### 11.5 Configuration System Extensions
Possible future additions:

* CLI-based parameter overrides
* configuration templating
* layered configuration systems

**Constraints:**

* resolved `RunConfig` must remain fully explicit and immutable
* no runtime mutation of configuration
* no hidden parameter resolution logic

---

### 11.6 Persistence Layer Extensions
Future enhancements may include:

#### Database Backend

* storing experiments and results in a database

#### Hybrid Storage

* combining file system with indexing layer

#### Artifact Compression

* reducing storage footprint for large experiments

**Constraints:**

* file-system-based model remains the reference implementation
* new backends must preserve artifact structure semantics
* existing artifacts must remain readable

---

### 11.7 Result and Summary Extensions
Future additions may include:

* richer statistical summaries
* distribution-based metrics
* time-series analysis
* custom metrics

**Constraints:**

* summaries must remain derived from results
* existing summary schema must not break
* new fields must be additive

---

### 11.8 Resume and Fault Tolerance Extensions
Possible enhancements:

* episode-level resume within runs
* checkpointing during long runs
* retry strategies for failed runs

**Constraints:**

* run-level resume must remain the baseline
* partial state must remain explicit
* no hidden recovery mechanisms

---

### 11.9 CLI Extensions
Future CLI capabilities may include:

* filtering and querying
* exporting results
* batch operations
* integration with external tools

**Constraints:**

* CLI must remain a thin layer
* no business logic in CLI
* no divergence from underlying domain model

---

### 11.10 Visualization Layer (Deferred)
Visualization is explicitly out of scope for this framework.

Future work may introduce:

* episode replay
* run comparison views
* experiment dashboards

**Constraints:**

* visualization must operate on persisted artifacts only
* no coupling with execution logic
* no influence on experiment results

---

### 11.11 Observability Enhancements
Possible future extensions:

* structured event streams
* richer tracing models
* integration with external monitoring tools

**Constraints:**

* results remain the source of truth
* logs remain secondary artifacts
* no dependency of correctness on observability layer

---

### 11.12 Testing Extensions
Future testing enhancements may include:

* property-based testing
* fuzz testing of configuration inputs
* large-scale experiment validation

**Constraints:**

* must align with deterministic execution requirements
* must not introduce non-reproducible behavior

---

### 11.13 Hard Boundaries (Non-Negotiable Constraints)**
The following must not be violated by any extension:

#### 1. No Back-Dependency into Runtime
The runtime (EpisodeRunner and below) must remain unaware of:

* experiments
* runs
* configuration sweeps
* summaries

---

#### 2. No Mutation of Results
Persisted results must remain immutable.

---

#### 3. No Log-Based Correctness
The system must not depend on logs for correctness or reconstruction.

---

#### 4. No Hidden Execution Logic
All execution behavior must be traceable through:

* configuration
* explicit code paths
* persisted artifacts

---

#### 5. No Implicit Parameter Behavior
All parameter variation must be explicit and visible in configuration.

---

### 11.14 Evolution Strategy
The framework should evolve incrementally:

1. Implement minimal experimentation
2. Stabilize execution and persistence
3. Add summaries and analysis capabilities
4. Introduce robustness improvements (resume, failure handling)
5. Extend toward parallelization and advanced strategies
6. Introduce visualization layer

Each step must preserve compatibility with previous artifacts.

---

### 11.15 Implementation Consequence
Any extension must:

* respect existing core contracts
* operate through defined extension points
* preserve determinism and reproducibility
* maintain compatibility with persisted artifacts
* avoid introducing hidden complexity
* remain aligned with the conceptual model

---

