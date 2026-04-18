# Experiment Workspaces

Experiment Workspaces provide structured containers for AXIS work contexts. A workspace bundles intent, configuration, execution outputs, comparisons, measurements, and notes into a single coherent directory.

## Quick Start

### Create a workspace

```bash
axis workspaces scaffold
```

This launches an interactive prompt that guides you through workspace creation, collecting:

- Workspace ID and title
- Class (development or investigation) and type
- Type-specific fields (system under test, reference/candidate systems, etc.)

### Validate a workspace

```bash
axis workspaces check workspaces/my-workspace
```

Reports errors, warnings, and drift issues. Use `--output json` for machine-readable output.

### Inspect a workspace

```bash
axis workspaces show workspaces/my-workspace
```

Displays identity, classification, status, and declared artifacts with existence checks. Each entry under `primary_configs`, `primary_results`, `primary_comparisons`, and `primary_measurements` is shown with an `[OK]` or `[MISSING]` marker indicating whether the referenced file or directory exists on disk.

For development workspaces, the output also shows the current development state (pre-candidate / post-candidate), baseline and candidate configs, results lists, and the current validation comparison. When a validation comparison exists, the reference and candidate experiment IDs used in that comparison are displayed, so you can trace exactly which runs were compared.

### Execute workspace configs

```bash
axis workspaces run workspaces/my-workspace
```

Resolves and executes all workspace configs. Results are written into the workspace's own `results/` directory and the manifest is updated with workspace-relative paths to the produced artifacts.

### Run a workspace comparison

```bash
axis workspaces compare workspaces/my-workspace
```

For `system_comparison` and `system_development` workspaces, resolves reference and candidate experiments from workspace-local results and runs the comparison. Each comparison produces a sequentially numbered, self-contained output file (`comparisons/comparison-001.json`, `comparison-002.json`, etc.) that includes:

- Full copies of both experiment configurations at comparison time
- The complete comparison metrics (per-episode results and statistical summary)
- A timestamp and sequential comparison number

Multiple comparisons can be run without overwriting previous results.

#### Comparison target resolution

By default, the system auto-resolves which experiments to compare:

- **Different system types**: matches experiments by `system_type` from the manifest.
- **Same system type**: uses `primary_results` ordering from the manifest — the first entry maps to reference, the second to candidate.
- **Ambiguous**: if multiple experiments match and ordering doesn't resolve, an error is raised listing the options.

You can override auto-resolution with explicit experiment IDs:

```bash
axis workspaces compare workspaces/my-workspace \
  --reference-experiment <experiment-id> \
  --candidate-experiment <experiment-id>
```

Both flags must be provided together. The referenced experiments must exist under `<workspace>/results/`.

If no execution results exist in the workspace, the compare command aborts with a clear error directing you to run `axis workspaces run` first.

### Inspect comparison results

```bash
axis workspaces comparison-result workspaces/my-workspace
```

Displays stored comparison results. If only one comparison exists, it is shown directly. If multiple comparisons exist, a listing is displayed with comparison numbers, system types, and timestamps.

Select a specific comparison by number:

```bash
axis workspaces comparison-result workspaces/my-workspace --number 2
```

The output includes the comparison metrics (same format as `axis compare`) followed by a summary of the reference and candidate configurations that were in effect when the comparison was run.

This command is only valid for `system_comparison`, `system_development`, and `single_system` workspaces.

### Visualize from a workspace

```bash
axis visualize --workspace workspaces/my-workspace --episode 1
```

For comparison workspaces, add `--role reference` or `--role candidate` to select which side to visualize. If the workspace contains multiple experiments and the role alone is not enough to disambiguate, specify the experiment directly:

```bash
axis visualize --workspace workspaces/my-workspace --experiment <experiment-id> --episode 1
```

Visualization uses the workspace-local results — the experiment ID must exist under `<workspace>/results/`.

---

## Workflows by Workspace Type

Each workspace class/type combination has a distinct workflow. The sections below describe the intended usage pattern for each.

### Investigation / System Comparison

**Purpose**: Compare two systems (or two configurations of the same system) under identical conditions to answer a question like *"Which system performs better on grid_2d?"* or *"How does changing consume_weight affect system_a?"*.

**Manifest requirements**: `question`, `reference_system`, `candidate_system`.

#### Step-by-step workflow

**1. Scaffold the workspace**

```bash
axis workspaces scaffold
```

Choose `investigation` / `system_comparison`. The scaffolder creates two config files in `configs/` — one for the reference system and one for the candidate. Both configs share identical world and execution settings to ensure a fair comparison.

**2. Configure the experiment**

Edit the configs in `configs/` to set up the systems you want to compare. The key parameters to consider:

- `general.seed` — use the same seed for reproducible, fair comparisons
- `system.*` — the system-specific parameters that differ between the two sides
- `execution.max_steps`, `num_episodes_per_run` — shared experiment parameters

**3. Execute**

```bash
axis workspaces run workspaces/my-comparison
```

Both configs are executed. Results land in `results/` and the manifest is updated with `primary_results` entries.

**4. Compare**

```bash
axis workspaces compare workspaces/my-comparison
```

The system auto-resolves which experiments belong to each side (by `system_type` or manifest ordering). A self-contained comparison file is written to `comparisons/comparison-001.json` with full config copies embedded.

If auto-resolution is ambiguous (e.g. after multiple runs), use explicit IDs:

```bash
axis workspaces compare workspaces/my-comparison \
  --reference-experiment <eid> \
  --candidate-experiment <eid>
```

**5. Analyze**

```bash
axis workspaces comparison-result workspaces/my-comparison
```

Displays per-episode metrics, statistical summary, and the full configurations that produced the result. Use `--number N` to inspect a specific comparison when multiple exist.

**6. Visualize**

```bash
axis visualize --workspace workspaces/my-comparison --role reference --episode 1
axis visualize --workspace workspaces/my-comparison --role candidate --episode 1
```

If multiple experiments exist for the same role, add `--experiment <eid>`.

**7. Iterate**

Modify the configs in `configs/`, then repeat steps 3–6. Each comparison run is preserved as a separate numbered file with its own config snapshot, so you can trace how parameter changes affected behavior across iterations.

#### Example: comparing system_a vs system_c on grid_2d

```bash
# Scaffold
axis workspaces scaffold
# → workspace_id: system-a-vs-system-c-grid2d
# → class: investigation, type: system_comparison
# → reference_system: system_a, candidate_system: system_c

# Run
axis workspaces run workspaces/system-a-vs-system-c-grid2d

# Compare
axis workspaces compare workspaces/system-a-vs-system-c-grid2d

# Inspect results
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d

# Tweak candidate config, re-run, re-compare
# Edit configs/candidate-system_c.yaml — change prediction parameters
axis workspaces run workspaces/system-a-vs-system-c-grid2d
axis workspaces compare workspaces/system-a-vs-system-c-grid2d

# Compare both iterations side by side
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d --number 1
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d --number 2
```

---

### Investigation / Single System

**Purpose**: Study a single system's behavior under varying configurations to answer questions like *"How does changing consume_weight affect system_a's survival rate?"* or *"What is system_a's behavior on a dense grid?"*.

**Manifest requirements**: `question`, `system_under_test`.

#### Step-by-step workflow

**1. Scaffold the workspace**

```bash
axis workspaces scaffold
```

Choose `investigation` / `single_system`. The scaffolder creates one baseline config in `configs/`.

**2. Configure and run the baseline**

Edit the config in `configs/` to set up the baseline parameters, then execute:

```bash
axis workspaces run workspaces/my-workspace
```

Results are written to `results/` and `primary_results` is updated in the manifest.

**3. Modify config and run again**

Change the parameters you want to investigate in the config file, then run again:

```bash
axis workspaces run workspaces/my-workspace
```

Each run creates a new experiment with its own ID. Results accumulate — previous runs are never overwritten.

**4. Compare**

```bash
axis workspaces compare workspaces/my-workspace
```

Auto-resolution uses manifest ordering: the first recorded experiment becomes the reference, the most recent becomes the candidate. This naturally compares the baseline against your latest run.

For explicit control over which runs to compare:

```bash
axis workspaces compare workspaces/my-workspace \
  --reference-experiment <baseline-eid> \
  --candidate-experiment <modified-eid>
```

At least two runs must exist before comparison is possible.

**5. Analyze**

```bash
axis workspaces comparison-result workspaces/my-workspace
```

Displays per-episode metrics, statistical summary, and the full configurations for both runs. Since configs are embedded as copies, you can see exactly which parameter changes produced the observed differences.

**6. Iterate**

Modify configs, run again, compare again. Each comparison is numbered and preserved with its own config snapshot.

#### Example: investigating consume_weight on system_a

```bash
# Scaffold
axis workspaces scaffold
# → workspace_id: system-a-consume-weight
# → class: investigation, type: single_system
# → system_under_test: system_a

# Run baseline (consume_weight=2.5)
axis workspaces run workspaces/system-a-consume-weight

# Edit config: change consume_weight to 5.0
# Run modified version
axis workspaces run workspaces/system-a-consume-weight

# Compare baseline vs modified
axis workspaces compare workspaces/system-a-consume-weight

# Inspect the comparison
axis workspaces comparison-result workspaces/system-a-consume-weight

# Try another value: consume_weight=1.0
# Edit config, run, compare
axis workspaces run workspaces/system-a-consume-weight
axis workspaces compare workspaces/system-a-consume-weight \
  --reference-experiment <baseline-eid> \
  --candidate-experiment <latest-eid>

# Review both comparisons
axis workspaces comparison-result workspaces/system-a-consume-weight --number 1
axis workspaces comparison-result workspaces/system-a-consume-weight --number 2
```

---

### Development / System Development

**Purpose**: Develop and iterate on a new system implementation. The workspace provides a structured baseline/candidate workflow for testing changes against a known baseline.

**Manifest requirements**: `development_goal`, `artifact_kind` (= `system`), `artifact_under_development`.

**Additional directories**: `concept/` for conceptual modeling, `engineering/` for engineering specs and work packages.

**Development-specific manifest fields** (set automatically at scaffold time):

| Field | Description |
|---|---|
| `baseline_config` | Path to the baseline config file |
| `candidate_config` | Path to the candidate config file (null until created) |
| `baseline_results` | List of workspace-relative paths to baseline run results |
| `candidate_results` | List of workspace-relative paths to candidate run results |
| `current_candidate_result` | Latest candidate run result path |
| `current_validation_comparison` | Latest comparison result path |

**Development state**: The workspace is either in **pre-candidate** state (only baseline, no `candidate_config`) or **post-candidate** state (both baseline and candidate configs present). The `axis workspaces show` command displays the current state.

#### Step-by-step workflow

**1. Scaffold the workspace**

```bash
axis workspaces scaffold
```

Choose `development` / `system_development`. The scaffolder creates:
- A baseline config `configs/baseline-<artifact_name>.yaml`
- Development directories `concept/` and `engineering/`
- Manifest with `baseline_config` set, `candidate_config` null (pre-candidate state)

**2. Document and plan**

Use `concept/` for conceptual modeling (design docs, diagrams) and `engineering/` for engineering specs and work packages.

**3. Run the baseline**

```bash
axis workspaces run workspaces/my-dev-workspace
# or explicitly:
axis workspaces run workspaces/my-dev-workspace --baseline-only
```

In pre-candidate state, only the baseline is run. Results are recorded in both `primary_results` and `baseline_results`.

**4. Create the candidate**

Copy and modify the baseline config to create a candidate:

```bash
cp workspaces/my-dev-workspace/configs/baseline-system_d.yaml \
   workspaces/my-dev-workspace/configs/candidate-system_d.yaml
```

Edit the candidate config with your changes, then register it with the workspace:

```bash
axis workspaces set-candidate workspaces/my-dev-workspace configs/candidate-system_d.yaml
```

This sets `candidate_config` in the manifest and adds the config to `primary_configs`. The workspace is now in **post-candidate** state.

**5. Run the candidate**

```bash
axis workspaces run workspaces/my-dev-workspace --candidate-only
```

Or run both baseline and candidate together:

```bash
axis workspaces run workspaces/my-dev-workspace
```

Results are recorded in `candidate_results` and `current_candidate_result` is set.

**6. Compare baseline vs candidate**

```bash
axis workspaces compare workspaces/my-dev-workspace
```

Auto-resolution uses the latest baseline result as reference and `current_candidate_result` as candidate. A comparison envelope is written to `comparisons/comparison-001.json`.

**7. Analyze**

```bash
axis workspaces comparison-result workspaces/my-dev-workspace
```

Shows per-episode metrics, statistical summary, and the full configs for both sides.

**8. Iterate**

Modify the candidate config, re-run with `--candidate-only`, and compare again. Each comparison is numbered and preserved. The `current_candidate_result` always points to the latest candidate run.

#### Example: developing system_d

```bash
# Scaffold
axis workspaces scaffold
# → workspace_id: develop-system-d
# → class: development, type: system_development
# → artifact_kind: system, artifact_under_development: system_d

# Run baseline
axis workspaces run workspaces/develop-system-d

# Design and implement system_d changes...

# Create candidate config
cp workspaces/develop-system-d/configs/baseline-system_d.yaml \
   workspaces/develop-system-d/configs/candidate-system_d.yaml
# Edit candidate config with system_d changes

# Register candidate config
axis workspaces set-candidate workspaces/develop-system-d configs/candidate-system_d.yaml

# Run candidate
axis workspaces run workspaces/develop-system-d --candidate-only

# Compare
axis workspaces compare workspaces/develop-system-d

# Inspect
axis workspaces comparison-result workspaces/develop-system-d

# Iterate: modify candidate, re-run, re-compare
axis workspaces run workspaces/develop-system-d --candidate-only
axis workspaces compare workspaces/develop-system-d
axis workspaces comparison-result workspaces/develop-system-d --number 2

# Check workspace state at any time
axis workspaces show workspaces/develop-system-d
```

---

### Development / World Development

**Purpose**: Develop and iterate on a new world implementation. Similar to system development but focused on world environments.

**Manifest requirements**: `development_goal`, `artifact_kind` (= `world`), `artifact_under_development`.

**Additional directories**: `concept/` for conceptual modeling, `engineering/` for engineering specs and work packages.

*Workflow documentation to be added once the development lifecycle commands are refined.*

---

## Workspace Classification

Every workspace defines two classification fields:

| Field | Values |
|---|---|
| `workspace_class` | `development`, `investigation` |
| `workspace_type` | `system_development`, `world_development`, `single_system`, `system_comparison` |

### Valid combinations

| Class | Type |
|---|---|
| `development` | `system_development` |
| `development` | `world_development` |
| `investigation` | `single_system` |
| `investigation` | `system_comparison` |

### Development vs Investigation

**Development** workspaces create or modify artifacts (systems or worlds). They require `concept/` and `engineering/` directories and a `development_goal`.

**Investigation** workspaces study existing artifacts under defined conditions. They require a `question`.

---

## Workspace Manifest (`workspace.yaml`)

The manifest is the authoritative source of workspace identity and semantics.

### Required fields

| Field | Description |
|---|---|
| `workspace_id` | Unique identifier |
| `title` | Human-readable title |
| `workspace_class` | `development` or `investigation` |
| `workspace_type` | One of the four workspace types |
| `status` | `idea`, `draft`, `running`, `analyzing`, `completed` |
| `lifecycle_stage` | `idea`, `draft`, `spec`, `implementation`, `documentation` |
| `created_at` | Creation date (YYYY-MM-DD) |

### Type-specific required fields

| Type | Required fields |
|---|---|
| `single_system` | `question`, `system_under_test` |
| `system_comparison` | `question`, `reference_system`, `candidate_system` |
| `system_development` | `development_goal`, `artifact_kind` (= `system`), `artifact_under_development` |
| `world_development` | `development_goal`, `artifact_kind` (= `world`), `artifact_under_development` |

### Optional fields

- `description`, `tags`
- `baseline_artifacts`, `validation_scenarios`
- `primary_configs`, `primary_results`, `primary_comparisons`, `primary_measurements`
- `linked_experiments`, `linked_runs`, `linked_comparisons`

### Primary artifact tracking

The manifest tracks workspace-produced artifacts via four list fields:

- **`primary_configs`** — workspace-relative paths to config files (populated at scaffold time).
- **`primary_results`** — workspace-relative paths to run output directories (populated after `axis workspaces run`). Entries point to individual run directories, e.g. `results/<experiment-id>/runs/<run-id>`.
- **`primary_comparisons`** — workspace-relative paths to comparison output files (accumulated after each `axis workspaces compare`), e.g. `comparisons/comparison-001.json`.
- **`primary_measurements`** — workspace-relative paths to processed metrics.

These fields are updated automatically by the workspace commands. The manifest uses comment-preserving YAML round-trip writes, so manual comments and ordering in `workspace.yaml` are retained.

---

## Directory Structure

Every workspace contains:

```
my-workspace/
  workspace.yaml          # Manifest (required)
  README.md               # Description (required)
  notes.md                # Working notes (required)
  configs/                # Executable config files
  results/                # Execution result artifacts
  comparisons/            # Comparison outputs
  measurements/           # Processed metrics
  exports/                # Curated export artifacts
  concept/                # Conceptual modeling (development only)
  engineering/            # Engineering planning (development only)
```

---

## Result Placement

Workspaces use **workspace-owned mode**: all execution artifacts are written directly into the workspace's `results/` directory, and comparison outputs go into `comparisons/`. The workspace manifest is updated with references to the produced artifacts after each operation.

This is distinct from the direct `axis experiments run <config>` mode, which writes artifacts to the repository root (`experiments/results/` by default). The two modes are independent — workspace commands always write into the workspace, direct commands always write to the repository root.

---

## Comparison Output Format

Each comparison file (`comparisons/comparison-NNN.json`) is a self-contained envelope containing:

```json
{
  "comparison_number": 1,
  "timestamp": "2026-04-17T14:30:00+00:00",
  "reference_config": { ... },
  "candidate_config": { ... },
  "comparison_result": {
    "reference_experiment_id": "...",
    "candidate_experiment_id": "...",
    "reference_system_type": "system_a",
    "candidate_system_type": "system_c",
    "episode_results": [ ... ],
    "summary": { ... }
  }
}
```

The `reference_config` and `candidate_config` fields contain complete copies of the experiment configurations as they existed when the comparison was run. The `comparison_result` field contains the standard `RunComparisonResult` payload with per-episode metrics and statistical summary.

---

## Drift Detection

The checker includes drift detection that identifies:

- Declared primary artifacts that no longer exist on disk
- Undeclared files in `results/` or `comparisons/` that look like primary artifacts
- Incomplete comparison roles (reference without candidate)

```bash
axis workspaces check workspaces/my-workspace --output json
```

The JSON output includes a `drift_issues` array alongside the standard validation issues.

---

## CLI Reference

| Command | Description |
|---|---|
| `axis workspaces scaffold` | Interactive workspace creation |
| `axis workspaces check <path>` | Validate workspace structure and manifest |
| `axis workspaces show <path>` | Display workspace summary with artifact existence checks |
| `axis workspaces run <path>` | Execute all workspace configs |
| `axis workspaces run <path> --baseline-only` | Run only baseline config (system_development) |
| `axis workspaces run <path> --candidate-only` | Run only candidate config (system_development) |
| `axis workspaces set-candidate <path> <config>` | Set candidate config for a development workspace |
| `axis workspaces compare <path>` | Run workspace comparison (sequential, self-contained) |
| `axis workspaces comparison-result <path>` | Display stored comparison result(s) |
| `axis visualize --workspace <path> --episode N` | Visualize from workspace |

### Flags

| Flag | Command | Description |
|---|---|---|
| `--output json` | All commands | Machine-readable JSON output |
| `--reference-experiment <id>` | `compare` | Explicit reference experiment ID |
| `--candidate-experiment <id>` | `compare` | Explicit candidate experiment ID |
| `--number <N>` | `comparison-result` | Select a specific comparison by number |
| `--baseline-only` | `run` | Run only baseline config (system_development) |
| `--candidate-only` | `run` | Run only candidate config (system_development) |
| `--experiment <id>` | `visualize --workspace` | Select a specific experiment to visualize |
