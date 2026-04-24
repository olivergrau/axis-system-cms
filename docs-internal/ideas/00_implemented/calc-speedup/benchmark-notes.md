# Calculation Speedup -- Benchmark Notes

**Based on:** `implementation-roadmap.md`, `engineering-spec.md`  
**Date:** 2026-04-24

---

## Status Note

This note captures the first benchmark pass before the introduction of the
`delta` trace mode.

It remains useful as a baseline for understanding why `light` was clearly
attractive and why replay-rich `full` mode needed a middle ground, but it is no
longer the complete picture after `delta` was added.

## Purpose

This document records an initial benchmark pass for the new execution-policy
surface introduced by the calculation-speedup work:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

The goal of this pass is not to produce final performance claims.

It is to answer the next engineering question:

> Which third-wave optimization path should be prioritized next?


## Benchmark Scope

The current measurements focus on directional comparison between:

- `full + sequential`
- `light + sequential`
- `full + episodes`
- `light + episodes`
- `full + runs`
- `light + runs`

This first pass intentionally uses small, reproducible workloads so the matrix
can be executed quickly during active development.

These numbers are therefore best interpreted as:

- **relative signals**
- **overhead indicators**
- **decision support for the next wave**

They should not be presented as external release-performance claims.


## Commands Used

Single-run / episode-parallel matrix:

```bash
python scripts/benchmark_execution_modes.py --episodes 5 --steps 80 --workers 4 --repeats 2
```

OFAT / run-parallel matrix:

```bash
python scripts/benchmark_execution_modes.py --episodes 3 --steps 80 --workers 4 --repeats 2 --ofat
```


## Results

### Single Run

| Scenario | Median seconds | Speedup vs `full-sequential` |
|---|---:|---:|
| `full-sequential` | `7.68s` | `1.00x` |
| `light-sequential` | `0.037s` | `207.41x` |
| `full-episodes-parallel` | `8.49s` | `0.90x` |
| `light-episodes-parallel` | `0.051s` | `150.06x` |

### OFAT

| Scenario | Median seconds | Speedup vs `full-sequential` |
|---|---:|---:|
| `full-sequential` | `12.27s` | `1.00x` |
| `light-sequential` | `0.070s` | `175.61x` |
| `full-runs-parallel` | `15.38s` | `0.80x` |
| `light-runs-parallel` | `0.076s` | `161.97x` |


## Findings

### 1. Trace richness is currently the dominant runtime cost

The difference between `full` and `light` is dramatic even on small workloads:

- about `207x` faster for the single-run benchmark
- about `176x` faster for the OFAT benchmark

This is the strongest signal in the entire benchmark pass.

It strongly suggests that the current runtime cost is dominated by:

- full replay-trace construction
- serialization of replay-rich artifacts
- persistence of large per-episode outputs

The simulation itself does not appear to be the primary bottleneck at this
stage.


### 2. Parallelism is not yet paying off for small workloads

Both parallel modes underperformed their sequential full-trace baselines in
this benchmark pass:

- `episodes` parallel: about `0.90x`
- `runs` parallel: about `0.80x`

This is not a failure of the architectural direction.

It indicates that, for small workloads, multiprocessing overhead currently
outweighs the compute saved. Likely contributors are:

- process start / worker orchestration cost
- serialization cost for config/result payloads
- repeated plugin discovery / worker initialization
- persistence cost that remains per execution unit


### 3. `light` already provides a strong practical fast path

Even without deeper trace redesign, `light` is already a meaningful fast mode.

This validates the decision to introduce:

- explicit trace modes
- a non-replay execution lane
- replay guard-rails around `light`

The new semantics are already paying off.


## Recommendation For Wave 3

The next optimization wave should prioritize:

## Recommended Path: `full`-mode persistence and serialization reduction

Reasoning:

1. The benchmark signal overwhelmingly points to replay-rich output generation
   and persistence as the dominant cost center.
2. Parallelism is not yet the next best lever on representative small
   workloads.
3. `light` already gives us a strong fast path for summary-oriented execution.
4. A narrower optimization of `full`-mode artifact production is lower risk
   than immediately jumping into a full delta-trace redesign.


## Recommended Work For The Next Pass

### Priority A -- Measure `full` cost composition more precisely

Add timing instrumentation around:

- simulation loop time
- trace object construction
- episode serialization
- episode persistence
- run summary generation

Without this split, we know that `full` is expensive, but not exactly which
subsystem deserves first optimization.


### Priority B -- Reduce overhead in replay-rich persistence

Potential targets:

- reduce redundant artifact writes in `full`
- reduce repeated JSON encoding overhead
- avoid unnecessary intermediate structures before persistence
- review whether some persisted metadata can be written once per run rather than
  per episode


### Priority C -- Make parallelism workload-aware rather than default-faster

Parallelism still matters, but should not be the immediate optimization focus.

The next step there should likely be:

- benchmark with larger workloads
- document that small workloads may regress under multiprocessing
- consider a future `auto` policy or workload threshold before enabling
  parallel workers


## Deferred For A Later Idea Or Later Wave

These remain interesting, but should not be the immediate next step:

- delta traces
- replay-format redesign
- binary or alternative trace persistence formats
- deep in-memory trace model replacement

These are higher-risk architectural changes and should be revisited only after
the measured `full`-mode cost composition is better understood.


## Decision

The current data supports the following conclusion:

> Third wave should focus on measuring and reducing the cost of `full` replay
> artifact generation and persistence, not on a deeper parallelization push as
> the immediate next move.
