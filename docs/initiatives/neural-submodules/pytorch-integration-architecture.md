# PyTorch Integration Architecture

## Short Answer

Yes. AXIS can integrate PyTorch-based neural modules cleanly into the existing
system architecture, including optional GPU-backed execution, without breaking
the current framework model.

The important point is that PyTorch should be introduced as an implementation
technology for bounded submodules inside systems, not as a second parallel
framework that bypasses AXIS runtime structure.

## Why This Fits AXIS

AXIS systems already have explicit substructures:

- observation handling
- drive updates
- memory or prediction updates
- action scoring and selection
- trace and metrics emission

A PyTorch component can therefore be inserted at a specific seam, for example:

- a predictor module
- a novelty estimator
- a bounded policy refinement block
- a compact map encoder

In each case, AXIS still owns the outer system loop.

## Architectural Position

The recommended architecture is:

1. AXIS system remains the top-level behavioral module.
2. A neural submodule is owned by the system implementation.
3. The system calls the submodule during normal step execution.
4. If online learning is enabled, the system also triggers updates through a controlled update path.

This means PyTorch is embedded inside a system, not wrapped around the whole runtime.

## Runtime Layers

A neuralized AXIS system should conceptually separate three layers.

### 1. Structural System Logic

This is ordinary AXIS logic:

- explicit drives
- explicit action inventory
- explicit arbitration logic
- explicit loop ordering

### 2. Neural Module Object

This is a PyTorch `nn.Module` or a small set of modules.

It is responsible only for a narrow learned function such as:

\[
\hat{y}_t = f_\theta(x_t)
\]

### 3. Learning State

If online adaptation is enabled, the system may additionally own:

- optimizer object
- replay buffer or short transition history
- target network if used
- per-run transient hidden state

These should not be conflated with the structural system configuration.

## GPU Use

GPUs are not required for the first AXIS neural modules.

For small predictors or bounded scoring modules in grid worlds, CPU execution
is sufficient and likely preferable for early development because it is simpler,
more reproducible, and easier to debug.

GPU support becomes useful when:

- models become materially larger
- world/state encoding becomes richer
- update frequency increases
- experiments scale to many runs or long trajectories

So the correct stance is:

- CPU should be the default baseline
- device placement should be configurable
- GPU should be optional, not assumed

## PyTorch Integration Pattern

A clean first pattern would look like this.

The system owns a neural submodule wrapper such as:

- `PredictorModule`
- `PredictorTrainer`
- `PredictorRuntimeState`

where responsibilities are separated:

- module: forward computation
- trainer: update logic and optimizer handling
- runtime state: transient per-run state if needed

This keeps the system code organized and avoids scattering training logic
across the main step function.

## Persistence Implications

A PyTorch-based AXIS module may require multiple persistence layers:

1. Static configuration
   Architectural choices and hyperparameters from the experiment config.

2. Learned parameters
   Model weights such as `state_dict`.

3. Optimizer state
   Only if continuing online adaptation across resumed runs matters.

4. Run-local transient state
   Hidden state, short buffers, or temporary adaptation memory.

AXIS should keep these separate. Not every experiment needs all of them.

## Inference and Online Update in One Loop

PyTorch fully supports immediate-use online learning.

A step can be:

1. encode input features
2. forward pass through the module
3. use prediction/modulation in action selection
4. observe realized outcome
5. compute loss
6. update parameters
7. continue next step with updated weights

That is technically seamless in PyTorch.

The real challenge is behavioral stabilization, not framework compatibility.

## Config Implications

AXIS config would likely need explicit neural-submodule fields such as:

- module enabled/disabled
- architecture kind
- input feature selection
- hidden size or layer structure
- device selection (`cpu`, `cuda`)
- learning enabled/disabled
- learning rate
- update cadence
- gradient clipping
- replay or smoothing options

This should be explicit configuration, not hidden magic.

## Visualization and Diagnostics

Once PyTorch modules exist inside systems, AXIS should expose diagnostics such as:

- predictor output
- prediction error
- update trigger or learning gate
- confidence or uncertainty proxy if defined
- current device
- parameter/update statistics where useful

This is essential if neural submodules are to remain scientifically inspectable.

## Reduction Path

Every PyTorch-based system should preserve a non-neural or reduced fallback.

That means:

- the same system should ideally support a manual predictor mode
- experiments should compare manual and neural variants under matched conditions
- failure or instability should not trap the framework in one opaque implementation path

## Conclusion

PyTorch can be integrated cleanly into AXIS as the implementation technology for
bounded neural submodules, with optional GPU use when needed.

The correct architectural model is not "run PyTorch beside AXIS." The correct
model is "embed PyTorch modules inside explicit AXIS systems at carefully chosen
seams, with configuration, persistence, and diagnostics that remain aligned
with the framework's explicit design philosophy."
