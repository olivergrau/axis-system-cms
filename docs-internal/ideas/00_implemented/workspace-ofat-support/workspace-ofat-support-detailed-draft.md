# Workspace OFAT Support Detailed Draft

## Purpose

This detailed draft defines a first concrete direction for adding `ofat`
support to AXIS Experiment Workspaces.

The draft builds on the previously established decisions:

- OFAT support, if added to Workspaces, should first be limited to
  `investigation / single_system`
- Workspaces already distinguish between:
  - point outputs
  - sweep outputs
- Workspace comparison must not be overloaded with sweep semantics too early


## Design Position

### 1. OFAT remains an experiment-level concept

OFAT is still defined at the config / experiment level through:

- `experiment_type: "ofat"`
- `parameter_path`
- `parameter_values`

The Workspace should not redefine that concept.

Instead:

- the config chooses whether the experiment is a point or sweep experiment
- the framework produces the corresponding Experiment Output
- the Workspace reacts accordingly

### 2. Workspace type stays unchanged

OFAT support should be added only within the existing workspace type:

- `investigation / single_system`

No new workspace type is introduced in v1.


## Core Workflow Decision

The operational workflow for Workspace OFAT support is:

1. Create or open an existing `investigation / single_system` workspace
2. Place or edit a config in `configs/`
3. Set `experiment_type: "ofat"` in that config
4. Run the workspace via `axis workspaces run <workspace>`
5. The execution produces a **sweep output**
6. The sweep output is recorded as one primary result entry
7. The user inspects the sweep via a dedicated sweep result command
8. The user may visualize one explicitly selected variation run
9. The user documents findings in `notes.md` or `measurements/`


## Scope Restriction

Workspace OFAT support in v1 is restricted to:

- `investigation / single_system`

It is explicitly not supported in:

- `investigation / system_comparison`
- `development / system_development`

This restriction is intentional and should be enforced clearly.


## Output Semantics

### Point Outputs

A config with:

- `experiment_type: "single_run"`

produces:

- a point output

### Sweep Outputs

A config with:

- `experiment_type: "ofat"`

produces:

- a sweep output

The Workspace does not invent this distinction. It consumes it from the
framework-level Experiment Output abstraction.


## Result Tracking

### One sweep = one result entry

Each completed OFAT execution must appear in the Workspace as:

- exactly one `primary_results` entry

The entry points to the experiment root:

- `results/<experiment-id>`

The sweep is therefore treated as:

- one coherent output artifact
- not a list of separate point-like results

### Historical ordering

Multiple sweep runs in the same workspace are allowed.

Their order in `primary_results` is meaningful only as:

- historical sequence of produced outputs

It is **not** a substitute for the internal ordering of variations within the
sweep.


## Command Behavior

### `axis workspaces run`

This command must support both:

- point configs
- OFAT configs

in `investigation / single_system` workspaces.

No additional OFAT-specific run flag is required.

The command should behave naturally:

- point config -> point output
- OFAT config -> sweep output


### `axis workspaces show`

`show` remains a Workspace management command.

It must continue to focus on:

- identity
- classification
- state
- declared artifacts
- existence checks

It must **not** become the primary result-inspection command for sweep outputs.

In particular:

- `show` should not be expanded into sweep analysis
- sweep interpretation belongs to a dedicated result command


### `axis workspaces compare`

`compare` remains a comparison command.

In `investigation / single_system`, v1 behavior should be:

- `point vs point` => supported
- `point vs sweep` => explicit error
- `sweep vs point` => explicit error
- `sweep vs sweep` => explicit error

No fallback behavior is allowed.

This is important because:

- a sweep is not just a special point result
- and comparing sweeps requires a dedicated model that is not yet defined


### `axis workspaces comparison-result`

This command remains comparison-specific.

It should continue to show:

- stored comparison artifacts

It must not be overloaded to display sweep results.


### `axis workspaces sweep-result`

This draft introduces a new command:

- `axis workspaces sweep-result <workspace>`

Its role is:

- inspect one stored sweep output in a Workspace

This command exists because:

- `compare` is the wrong semantic tool for a single sweep
- `show` should remain focused on workspace management

### Default behavior of `sweep-result`

In v1, the default should be:

- show the latest sweep output recorded in the workspace

Future extension could allow:

- explicit selection by experiment ID
- explicit selection by ordinal index

But that is not required in the first detailed model.


## Visualization Behavior

Visualization of sweep results must be explicit.

That means:

- no silent baseline default
- no silent first-run default

To visualize a sweep variation, the user must explicitly select a run.

Example shape:

- `axis visualize --workspace <path> --experiment <eid> --run <rid> --episode 1`

This keeps sweep visualization aligned with the explicit design philosophy of
the rest of the system.


## Manifest Impact

### No new sweep-specific workspace fields

The Workspace manifest should not gain special sweep-only fields in v1.

The sweep semantics already live in:

- the experiment config
- the Experiment Output abstraction

The Workspace should record the produced sweep output as a normal structured
result entry in `primary_results`.

That is sufficient for the first wave.


## Scaffolding

### Default behavior

The default scaffolded config for `investigation / single_system` remains:

- a point config

### Optional OFAT starter

The scaffolder should later be allowed to offer an optional choice:

- create an OFAT starter config

This should be optional, not mandatory.

That keeps the standard user path simple while still giving sweep-oriented
users a helpful starting point.


## Compare Semantics in `single_system`

This draft explicitly limits Workspace comparison in `single_system` to:

- point outputs only

This means:

- ordinary iterative runs can still be compared
- sweep outputs can be run and inspected
- but sweep outputs are not valid Workspace comparison targets in v1

This avoids premature and under-specified behaviors such as:

- comparing first vs last variation only
- comparing baseline run vs whole sweep
- silently flattening sweep outputs into point-like artifacts


## Example Workflow

### Point-style single-system iteration

1. run a baseline point config
2. edit config
3. run again
4. compare point vs point

### Sweep-style single-system investigation

1. edit config to:
   - `experiment_type: "ofat"`
   - define `parameter_path`
   - define `parameter_values`
2. run the workspace
3. obtain a sweep output in `results/`
4. inspect it using `axis workspaces sweep-result`
5. visualize one variation run explicitly if needed
6. document findings


## What v1 Does Not Support

The following are explicitly out of scope:

- sweep support in `system_comparison`
- sweep support in `system_development`
- point vs sweep workspace comparison
- sweep vs sweep workspace comparison
- treating `show` as a sweep-analysis tool
- implicit default variation selection during sweep visualization


## Detailed Draft Recommendation

Proceed with Workspace OFAT support as a bounded extension of:

- `investigation / single_system`

using the following rules:

- OFAT is activated by the config, not by a new workspace type
- `axis workspaces run` supports both point and sweep outputs
- each sweep appears as one primary result entry
- `show` remains management-only
- `compare` remains point-vs-point only
- a new `sweep-result` command becomes the first-class inspection tool for
  sweep outputs
- sweep visualization requires explicit run selection

This gives AXIS a controlled and semantically clean first step toward
Workspace-level OFAT support without distorting the existing comparison and
development workflows.
