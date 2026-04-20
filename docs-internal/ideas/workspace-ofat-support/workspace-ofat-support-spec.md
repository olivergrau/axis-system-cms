# Workspace OFAT Support Spec

## 1. Purpose

This specification defines the first supported form of `ofat` execution inside
AXIS Experiment Workspaces.

The purpose is to allow controlled parameter sweeps inside Workspace mode
without distorting the existing semantics of:

- Workspace management
- Workspace comparison
- system development workflows


## 2. Scope

This spec covers:

- where OFAT is supported in Workspace mode
- how OFAT execution behaves in a Workspace
- how sweep results are tracked
- how sweep results are inspected
- how Workspace comparison behaves when both point and sweep outputs exist

This spec does **not** define:

- sweep-vs-sweep Workspace comparison
- point-vs-sweep Workspace comparison
- sweep support for development workspaces
- sweep support for system comparison workspaces


## 3. Supported Workspace Scope

In v1, Workspace OFAT support is allowed only for:

- `workspace_class = investigation`
- `workspace_type = single_system`

OFAT is not supported in Workspace mode for:

- `investigation / system_comparison`
- `development / system_development`


## 4. Source of OFAT Semantics

Workspace OFAT support is activated by the experiment config, not by a new
Workspace type and not by a new Workspace manifest field.

The decisive field is:

- `experiment_type`

The rules are:

- `experiment_type = single_run` => point output
- `experiment_type = ofat` => sweep output

The Workspace must consume this distinction from the framework-level Experiment
Output abstraction.


## 5. Single-System Workspace Behavior

An `investigation / single_system` Workspace may contain both:

- point outputs
- sweep outputs

This is explicitly allowed.

The Workspace is therefore a mixed investigation space, not a point-only or
sweep-only container.


## 6. Execution Behavior

### 6.1 `axis workspaces run`

For `investigation / single_system`, `axis workspaces run <workspace>` must
support:

- point configs
- OFAT configs

No OFAT-specific run flag is required.

### 6.2 One active config

In v1, the operational single-system workflow remains based on one active
investigation config at a time.

Therefore, `axis workspaces run` for `investigation / single_system` continues
to execute one operative config, not multiple config files in parallel.


## 7. Result Semantics

### 7.1 Sweep as one result artifact

A completed OFAT execution in Workspace mode must be recorded as:

- exactly one result entry in `primary_results`

That result entry points to the experiment root:

- `results/<experiment-id>`

and represents one coherent sweep output.

### 7.2 Historical ordering

If a Workspace accumulates multiple results over time, the order of
`primary_results` is meaningful only as:

- chronological / historical result order

It must not be interpreted as the internal ordering of variation runs within a
sweep.


## 8. Workspace Show

`axis workspaces show <workspace>` remains a Workspace management command.

It must continue to show:

- workspace identity
- classification
- state
- declared artifacts
- existence checks

It may show that a result artifact has:

- `output_form = point`
- `output_form = sweep`

But it must not become a sweep-analysis command.


## 9. Sweep Result Inspection

### 9.1 New command

This spec introduces:

- `axis workspaces sweep-result <workspace>`

This is the first-class command for inspecting a single sweep output inside a
Workspace.

### 9.2 Command applicability

`sweep-result` is valid only when the Workspace contains at least one sweep
output.

If no sweep outputs are present, the command must fail explicitly.

### 9.3 Default target selection

Without explicit selection, `sweep-result` must:

- filter `primary_results` to sweep outputs only
- select the newest sweep output

### 9.4 Explicit target selection

The command must support explicit selection by:

- `--experiment <experiment-id>`

If the selected experiment exists but is not a sweep output, the command must
fail explicitly.

### 9.5 Required information shown

In text or JSON form, `sweep-result` must expose at least:

- `experiment_id`
- `system_type`
- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- variation run list
- variation descriptions
- experiment-level sweep summary including delta fields

### 9.6 Output formats

`sweep-result` must support:

- text output
- JSON output


## 10. Workspace Comparison Behavior

### 10.1 Comparison remains comparison-only

`axis workspaces compare` remains a comparison command.

It must not be repurposed as sweep inspection.

### 10.2 Supported comparison case

For `investigation / single_system`, Workspace comparison remains supported only
for:

- `point vs point`

### 10.3 Comparison selection rule for mixed histories

If both point and sweep outputs exist in the same single-system Workspace,
`compare` must:

- filter `primary_results` to point outputs only

Then it must resolve:

- reference = the first point output in historical order
- candidate = the newest point output in historical order

If fewer than two point outputs exist, comparison must fail explicitly.

### 10.4 Unsupported comparison cases

The following cases are not supported in v1:

- `point vs sweep`
- `sweep vs point`
- `sweep vs sweep`

When such a case would otherwise arise, the command must fail explicitly.


## 11. Visualization Behavior

### 11.1 Point outputs

Point outputs may continue to use the ordinary point-output visualization rules.

### 11.2 Sweep outputs

Sweep visualization must be explicit.

That means:

- no default baseline selection
- no default first-run selection
- no silent variation guessing

The user must provide:

- explicit experiment selection
- explicit run selection

Example shape:

- `axis visualize --workspace <path> --experiment <eid> --run <rid> --episode 1`

If explicit run selection is missing for a sweep output, visualization must
fail with a clear error.


## 12. Workspace Validation

### 12.1 Allowed config types

For `investigation / single_system`, Workspace validation must allow:

- `single_run`
- `ofat`

For all other Workspace types, Workspace validation must continue to allow only:

- `single_run`

### 12.2 OFAT validity

An OFAT config in a single-system Workspace is considered valid only if normal
framework OFAT requirements are satisfied:

- `parameter_path` present
- `parameter_values` present
- `parameter_values` non-empty

If these are not satisfied, validation must fail through the normal config
validation path.


## 13. Manifest Impact

No new sweep-specific top-level Workspace manifest fields are required in v1.

Sweep semantics remain located in:

- the config
- the Experiment Output abstraction
- the structured `primary_results` entry

This is sufficient for the first supported OFAT wave.


## 14. Scaffolding

### 14.1 Default scaffold

The default `single_system` scaffold remains:

- a point config starter

### 14.2 Optional OFAT starter

Scaffolding may additionally offer an optional choice to create:

- an OFAT starter config

This starter may include example values for:

- `parameter_path`
- `parameter_values`

These are starter values only and are expected to be edited by the user.


## 15. Error Handling

The Workspace system must prefer explicit errors over silent fallback behavior.

This applies in particular to:

- `sweep-result` called with no available sweep outputs
- `sweep-result --experiment <eid>` where `<eid>` is not a sweep output
- `compare` with fewer than two point outputs
- any attempted sweep-involved comparison
- sweep visualization without explicit run selection


## 16. Conformance Rules

An implementation conforms to this spec only if:

- OFAT is supported in Workspace mode only for
  `investigation / single_system`
- `axis workspaces run` can execute OFAT configs in that workspace type
- a sweep execution is recorded as one experiment-root result entry
- `axis workspaces sweep-result` exists and inspects sweep outputs
- `axis workspaces show` remains management-only
- `axis workspaces compare` continues to operate only on point outputs
- mixed point/sweep histories are filtered correctly for comparison
- sweep visualization requires explicit run selection
- validation allows OFAT only in `single_system`


## 17. Non-Goals for v1

The following are explicitly out of scope:

- sweep support in `system_comparison`
- sweep support in `system_development`
- sweep-vs-sweep comparison
- point-vs-sweep comparison
- sweep analysis through `show`
- implicit variation selection in sweep visualization
- new sweep-specific top-level manifest fields


## 18. Recommendation

Proceed with OFAT Workspace support as a bounded extension of
`investigation / single_system`.

The first implementation wave should:

- allow OFAT configs in single-system Workspaces
- produce sweep outputs naturally through `axis workspaces run`
- track each sweep as one result artifact
- add `axis workspaces sweep-result`
- keep `compare` strictly point-vs-point
- keep `show` management-only
- require explicit run selection for sweep visualization

This is the cleanest and safest first step toward Workspace-based OFAT support.
