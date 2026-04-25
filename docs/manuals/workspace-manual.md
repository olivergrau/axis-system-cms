# Experiment Workspaces

Experiment Workspaces provide structured containers for AXIS work contexts. A workspace bundles intent, configuration, execution outputs, comparisons, and notes into a single coherent directory.

> **Supported experiment types:** Workspaces support `experiment_type: single_run` configs across all workspace types. Additionally, `investigation / single_system` workspaces also support `experiment_type: ofat` configs for one-factor-at-a-time parameter sweeps. OFAT is **not** supported in `system_comparison` or `system_development` workspaces — use `axis experiments run` directly for OFAT experiments in those contexts.

## Quick Start

### Create a workspace

```bash
axis workspaces scaffold
```

This launches an interactive prompt that guides you through workspace creation, collecting:

- Workspace ID and title
- Class (development or investigation) and type
- Type-specific fields (system under test, reference/candidate systems, etc.)
- Workflow state:
  - `status`: `draft`, `active`, `analyzing`, `completed`, `closed`
  - `lifecycle_stage`: `idea`, `draft`, `spec`, `implementation`, `analysis`, `documentation`, `final`

### Validate a workspace

```bash
axis workspaces check workspaces/my-workspace
```

Reports errors, warnings, and drift issues. Use `--output json` for machine-readable output.

### Inspect a workspace

```bash
axis workspaces show workspaces/my-workspace
```

Displays identity, classification, status, and declared artifacts with existence checks. Each entry under `primary_configs`, `primary_results`, and `primary_comparisons` is shown with an `[OK]` or `[MISSING]` marker indicating whether the referenced file or directory exists on disk.

If a workspace is closed, `show` makes that explicit and warns that execution
and comparison commands are disabled.

For `primary_results`, the summary also shows any stored configuration changes
relative to the previous comparable result. In single-system workspaces this is
the previous run. In workspaces with roles (for example reference/candidate or
baseline/candidate), the comparison is against the previous result with the
same role.

For development workspaces, the output also shows the current development state (pre-candidate / post-candidate), baseline and candidate configs, results lists, and the current validation comparison. When a validation comparison exists, the reference and candidate experiment IDs used in that comparison are displayed, so you can trace exactly which runs were compared.

### Execute workspace configs

```bash
axis workspaces run workspaces/my-workspace
```

Resolves and executes all workspace configs. Results are written into the workspace's own `results/` directory and the manifest is updated with workspace-relative paths to the produced artifacts.

For `investigation / single_system` workspaces, configs may use either `experiment_type: single_run` or `experiment_type: ofat`. All other workspace types require `single_run`. The command will fail before execution if any config uses a disallowed experiment type.

The command also fails before execution if the resolved workspace run would not
change anything relevant compared to the previous comparable result already
recorded in the workspace. This helps prevent accidental duplicate runs. In
single-system workspaces the comparison is against the previous run. In
workspaces with roles, each target is compared against the previous result with
the same role, and the run is blocked only when all resolved targets are still
effectively unchanged.

If the workspace has `status: closed`, the run command aborts before execution.

By default, the duplicate-run guard treats world-only edits as
insufficient to count as a new comparable run. If you intentionally
want to rerun a workspace because only the world configuration changed,
opt in explicitly:

```bash
axis workspaces run workspaces/my-workspace --allow-world-changes
```

This is especially useful for controlled world-manipulation studies
where the systems remain unchanged but the environment is the variable
under investigation.

If you intentionally need to rerun unchanged configs, for example after fixing
an earlier mismatched run setup outside the config delta that the guard treats
as relevant, bypass the duplicate-run guard explicitly:

```bash
axis workspaces run workspaces/my-workspace --override-guard
```

This only bypasses the duplicate-run guard. Workspace closure, config
validation, and execution errors still apply.

You can also attach an optional note to each result entry produced by the run:

```bash
axis workspaces run workspaces/my-workspace --notes "My notes for this run"
```

The note is stored in each new `primary_results` entry as `run_notes` and is
shown in `axis workspaces show` and `axis workspaces run-summary`.

### Run a workspace comparison

```bash
axis workspaces compare workspaces/my-workspace
```

For `system_comparison` and `system_development` workspaces, resolves reference and candidate experiments from workspace-local results and runs the comparison. Each comparison produces a sequentially numbered, self-contained output file (`comparisons/comparison-001.json`, `comparison-002.json`, etc.) that includes:

- Full copies of both experiment configurations at comparison time
- The complete comparison metrics (per-episode results and statistical summary)
- A timestamp and sequential comparison number

Multiple comparisons can be run without overwriting previous results.

If you intentionally want to compare runs where only the world
configuration changed, opt in explicitly:

```bash
axis workspaces compare workspaces/my-workspace --allow-world-changes
```

This relaxes only the `world_config_mismatch` validation rule. World
type, start position, seed pairing, and shared action-label validation
remain strict.

#### Comparison target resolution

By default, the system auto-resolves which experiments to compare:

- **Different system types** (`system_comparison`): uses the latest result for the reference system and the latest result for the candidate system.
- **Same system type** (`system_comparison`): prefers the latest `reference` and latest `candidate` point outputs recorded in `primary_results`. If role metadata is unavailable, it falls back to the latest two point outputs.
- **Single system** (`single_system`): filters `primary_results` to **point outputs only** (sweep outputs are excluded) and compares the latest two point outputs. This means sweep outputs never interfere with comparison resolution.
- **Ambiguous**: if multiple experiments match and ordering doesn't resolve, an error is raised listing the options.

You can override auto-resolution with explicit experiment IDs:

```bash
axis workspaces compare workspaces/my-workspace \
  --reference-experiment <experiment-id> \
  --candidate-experiment <experiment-id>
```

Both flags must be provided together. The referenced experiments must exist under `<workspace>/results/`.

If no execution results exist in the workspace, the compare command aborts with a clear error directing you to run `axis workspaces run` first.

If the workspace has `status: closed`, the compare command aborts before
comparison.

### Compare workspace configs

```bash
axis workspaces compare-configs workspaces/my-workspace
```

For `system_comparison` workspaces, displays the config delta between the
manifest-declared reference config and candidate config before running any
experiments. This is useful when you want to review exactly what changed between
the two sides of a comparison.

This command requires `primary_configs` entries with explicit roles:

```yaml
primary_configs:
- path: configs/reference-system_a.yaml
  role: reference
- path: configs/candidate-system_c.yaml
  role: candidate
```

The scaffolder writes these roles automatically for new workspaces. Older or
manually edited workspaces that still use plain string entries must be updated
before `compare-configs` can resolve the two sides.

`compare-configs` is currently supported only for `system_comparison`
workspaces. For `single_system` workspaces, compare concrete run outputs with
`axis workspaces compare` after at least two point runs exist.

### Close a workspace

```bash
axis workspaces close workspaces/my-workspace
```

Closes the workspace by updating the manifest to:

- `status: closed`
- `lifecycle_stage: final`

Closed workspaces remain fully inspectable:

- `axis workspaces show`
- `axis workspaces check`
- `axis workspaces run-summary`
- `axis workspaces run-metrics`
- `axis workspaces sweep-result`
- `axis visualize --workspace ...`

But they are operationally read-only. These commands are rejected for closed
workspaces:

- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces set-candidate`

### Inspect comparison results

```bash
axis workspaces comparison-summary workspaces/my-workspace
```

Displays stored comparison results. If only one comparison exists, it is shown directly. If multiple comparisons exist, a listing is displayed with comparison numbers, system types, and timestamps.

If multiple comparison results exist and `--number` is omitted, AXIS now shows the latest comparison by default.

Select a specific comparison by number:

```bash
axis workspaces comparison-summary workspaces/my-workspace --number 2
```

The output includes the comparison metrics (same format as `axis compare`) followed by a summary of the reference and candidate configurations that were in effect when the comparison was run.

If a stored comparison was created under the default strict rules, you
can re-render it with relaxed world-config validation:

```bash
axis workspaces comparison-summary workspaces/my-workspace --number 2 --allow-world-changes
```

In that case AXIS recomputes the comparison from the stored run
identities for display, without overwriting the saved comparison file.

This command is only valid for `system_comparison`, `system_development`, and `single_system` workspaces.

### Inspect sweep results

```bash
axis workspaces sweep-result workspaces/my-workspace
```

Displays sweep (OFAT) results from a `single_system` workspace. Shows each parameter variation with its metrics and delta values relative to the baseline run.

Select a specific sweep experiment:

```bash
axis workspaces sweep-result workspaces/my-workspace --experiment <experiment-id>
```

If multiple sweep outputs exist, the most recent is shown by default. Use `--output json` for machine-readable output.

### Inspect one run in a workspace

```bash
axis workspaces run-summary workspaces/my-workspace
```

This command is the workspace-native equivalent of `axis runs show`. It
resolves a run from the workspace-local `results/` directory and then
displays the same run-level inspection output.

Default behavior:

- **`single_system`**: resolves the newest manifest-declared result and shows its primary run
- **`system_comparison`**: requires `--role reference` or `--role candidate`
- **`system_development`**: requires `--role baseline` or `--role candidate`

Examples:

```bash
axis workspaces run-summary workspaces/my-single-system
axis workspaces run-summary workspaces/my-comparison --role reference
axis workspaces run-summary workspaces/my-dev-workspace --role candidate
```

If you want to inspect a specific experiment explicitly:

```bash
axis workspaces run-summary workspaces/my-workspace --experiment <experiment-id>
```

For sweep (OFAT) outputs, you must also specify the run:

```bash
axis workspaces run-summary workspaces/my-workspace \
  --experiment <experiment-id> --run <run-id>
```

### Inspect behavioral metrics for one run in a workspace

```bash
axis workspaces run-metrics workspaces/my-workspace
```

This command is the workspace-native equivalent of:

```bash
axis runs metrics <run-id> --experiment <experiment-id>
```

It resolves a run from the workspace-local `results/` directory using the same
resolution rules as `run-summary`, then computes or loads:

- framework-standard behavioral metrics
- optional system-specific extension metrics

Examples:

```bash
axis workspaces run-metrics workspaces/my-single-system
axis workspaces run-metrics workspaces/my-comparison --role reference
axis workspaces run-metrics workspaces/my-dev-workspace --role candidate
```

For sweep (OFAT) outputs, specify both experiment and run:

```bash
axis workspaces run-metrics workspaces/my-workspace \
  --experiment <experiment-id> --run <run-id>
```

Behavioral metrics require replay-capable traces:

- `full`
- `delta`

`light` runs are not supported.

### Visualize from a workspace

```bash
axis visualize --workspace workspaces/my-workspace --episode 1
```

For comparison workspaces, add `--role reference` or `--role candidate` to select which side to visualize. If the workspace contains multiple experiments and the role alone is not enough to disambiguate, specify the experiment directly:

```bash
axis visualize --workspace workspaces/my-workspace --experiment <experiment-id> --episode 1
```

Visualization uses the workspace-local results — the experiment ID must exist under `<workspace>/results/`.

Trace-mode rule:

- `full` and `delta` workspace results are visualizable
- `light` workspace results are not visualizable

If a workspace run was executed in `light` mode, AXIS will reject visualization
explicitly because no replay-compatible artifacts exist for that result.

For sweep (OFAT) experiments, you must specify the run explicitly with `--run`:

```bash
axis visualize --workspace workspaces/my-workspace --experiment <experiment-id> --run <run-id> --episode 1
```

The `--run` flag is required for sweep experiments because they contain multiple runs (one per parameter variation). Use `axis workspaces sweep-result` to see the available run IDs.

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
axis workspaces comparison-summary workspaces/my-comparison
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
axis workspaces comparison-summary workspaces/system-a-vs-system-c-grid2d

# Tweak candidate config, re-run, re-compare
# Edit configs/candidate-system_c.yaml — change prediction parameters
axis workspaces run workspaces/system-a-vs-system-c-grid2d
axis workspaces compare workspaces/system-a-vs-system-c-grid2d

# Compare both iterations side by side
axis workspaces comparison-summary workspaces/system-a-vs-system-c-grid2d --number 1
axis workspaces comparison-summary workspaces/system-a-vs-system-c-grid2d --number 2
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

Choose `investigation` / `single_system`. The scaffolder creates a baseline config in `configs/`.

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

Auto-resolution uses manifest ordering: the first recorded **point** experiment becomes the reference, the most recent **point** experiment becomes the candidate. Sweep outputs are excluded from auto-resolution — workspace comparison is always point-vs-point.

At least two point runs must exist before comparison is possible.

**5. Run an OFAT sweep (optional)**

`single_system` workspaces also support OFAT configs. Create a sweep config in `configs/`, add it to `primary_configs`, and run:

```bash
# Create and configure an OFAT config, then add it to primary_configs
axis workspaces run workspaces/my-workspace
```

Sweep outputs are recorded in `primary_results` with `output_form: sweep`. They do not participate in workspace comparison.

**6. Inspect sweep results**

```bash
axis workspaces sweep-result workspaces/my-workspace
```

Displays the parameter variations, per-run metrics, and delta values relative to the baseline. Use `--experiment <eid>` to select a specific sweep when multiple exist.

**7. Analyze**

```bash
axis workspaces comparison-summary workspaces/my-workspace
```

Displays per-episode metrics, statistical summary, and the full configurations for both runs. Since configs are embedded as copies, you can see exactly which parameter changes produced the observed differences.

**8. Iterate**

Modify configs, run again, compare again. Each comparison is numbered and preserved with its own config snapshot.

For explicit control over which point runs to compare:

```bash
axis workspaces compare workspaces/my-workspace \
  --reference-experiment <baseline-eid> \
  --candidate-experiment <modified-eid>
```

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
axis workspaces comparison-summary workspaces/system-a-consume-weight

# Try another value: consume_weight=1.0
# Edit config, run, compare
axis workspaces run workspaces/system-a-consume-weight
axis workspaces compare workspaces/system-a-consume-weight \
  --reference-experiment <baseline-eid> \
  --candidate-experiment <latest-eid>

# Review both comparisons
axis workspaces comparison-summary workspaces/system-a-consume-weight --number 1
axis workspaces comparison-summary workspaces/system-a-consume-weight --number 2
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
axis workspaces comparison-summary workspaces/my-dev-workspace
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
axis workspaces comparison-summary workspaces/develop-system-d

# Iterate: modify candidate, re-run, re-compare
axis workspaces run workspaces/develop-system-d --candidate-only
axis workspaces compare workspaces/develop-system-d
axis workspaces comparison-summary workspaces/develop-system-d --number 2

# Check workspace state at any time
axis workspaces show workspaces/develop-system-d
```

---

## Workspace Classification

Every workspace defines two classification fields:

| Field | Values |
|---|---|
| `workspace_class` | `development`, `investigation` |
| `workspace_type` | `system_development`, `single_system`, `system_comparison` |

### Valid combinations

| Class | Type |
|---|---|
| `development` | `system_development` |
| `investigation` | `single_system` |
| `investigation` | `system_comparison` |

### Development vs Investigation

**Development** workspaces create or modify system artifacts. They require `concept/` and `engineering/` directories and a `development_goal`.

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
| `workspace_type` | One of the three workspace types |
| `status` | `draft`, `active`, `analyzing`, `completed`, `closed` |
| `lifecycle_stage` | `idea`, `draft`, `spec`, `implementation`, `analysis`, `documentation`, `final` |
| `created_at` | Creation date (YYYY-MM-DD) |

### Type-specific required fields

| Type | Required fields |
|---|---|
| `single_system` | `question`, `system_under_test` |
| `system_comparison` | `question`, `reference_system`, `candidate_system` |
| `system_development` | `development_goal`, `artifact_kind` (= `system`), `artifact_under_development` |

### Optional fields

- `description`, `tags`
- `baseline_artifacts`, `validation_scenarios`
- `primary_configs`, `primary_results`, `primary_comparisons`
- `linked_experiments`, `linked_runs`, `linked_comparisons`

### Primary artifact tracking

The manifest tracks workspace-produced artifacts via four list fields:

- **`primary_configs`** — workspace-relative config entries populated at scaffold time. New workspaces use structured entries with a `path` and role metadata such as `reference`, `candidate`, or `baseline`; legacy plain string entries are still accepted for compatibility.
- **`primary_results`** — workspace-relative paths to experiment output directories (populated after `axis workspaces run`). Entries point to experiment roots, e.g. `results/<experiment-id>`, and include output semantics such as `output_form` (`point` or `sweep`), `system_type`, `role`, and `primary_run_id` or `baseline_run_id`. Optional `run_notes` can be attached at run time via `axis workspaces run --notes "..."`. When possible, each entry also stores the changed config elements relative to the previous comparable result so `axis workspaces show` can surface iteration history directly from the manifest.
- **`primary_comparisons`** — workspace-relative paths to comparison output files (accumulated after each `axis workspaces compare`), e.g. `comparisons/comparison-001.json`.
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
| `axis workspaces close <path>` | Close a workspace and finalize its workflow state |
| `axis workspaces check <path>` | Validate workspace structure and manifest |
| `axis workspaces show <path>` | Display workspace summary with artifact existence checks |
| `axis workspaces run <path>` | Execute all workspace configs |
| `axis workspaces run <path> --baseline-only` | Run only baseline config (system_development) |
| `axis workspaces run <path> --candidate-only` | Run only candidate config (system_development) |
| `axis workspaces set-candidate <path> <config>` | Set candidate config for a development workspace |
| `axis workspaces compare <path>` | Run workspace comparison (sequential, self-contained) |
| `axis workspaces compare-configs <path>` | Display reference/candidate config deltas (system_comparison only) |
| `axis workspaces comparison-summary <path>` | Display stored comparison result(s) |
| `axis workspaces run-summary <path>` | Display one resolved run summary from workspace-local results |
| `axis workspaces run-metrics <path>` | Display behavioral metrics for one resolved run from workspace-local results |
| `axis workspaces sweep-result <path>` | Display sweep (OFAT) results (single_system only) |
| `axis visualize --workspace <path> --episode N` | Visualize from workspace |

### Flags

| Flag | Command | Description |
|---|---|---|
| `--output json` | All commands | Machine-readable JSON output |
| `--reference-experiment <id>` | `compare` | Explicit reference experiment ID |
| `--candidate-experiment <id>` | `compare` | Explicit candidate experiment ID |
| `--number <N>` | `comparison-summary` | Select a specific comparison by number |
| `--allow-world-changes` | `run`, `compare`, `comparison-summary` | Allow world-only changes as the intentional variable |
| `--override-guard` | `run` | Bypass the duplicate-run guard for an intentional rerun |
| `--notes "<text>"` | `run` | Store a free-text note in each created `primary_results` entry |
| `--role <name>` | `run-summary`, `visualize --workspace` | Select role-specific workspace output |
| `--experiment <id>` | `run-summary` | Select a specific experiment in workspace results |
| `--run <id>` | `run-summary` | Select a specific run (required for sweep outputs) |
| `--experiment <id>` | `sweep-result` | Select a specific sweep experiment |
| `--baseline-only` | `run` | Run only baseline config (system_development) |
| `--candidate-only` | `run` | Run only candidate config (system_development) |
| `--experiment <id>` | `visualize --workspace` | Select a specific experiment to visualize |
| `--run <id>` | `visualize --workspace` | Select a specific run (required for sweep experiments) |

### Workflow semantics

`status` is the operational workflow field.

- Open states:
  - `draft`
  - `active`
  - `analyzing`
  - `completed`
- Closed state:
  - `closed`

`lifecycle_stage` is descriptive in this version. It is shown in summaries but
does not independently grant or deny command permissions.
