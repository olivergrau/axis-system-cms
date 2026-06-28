# System A+W — Dual-Drive Investigation

## Overview

This workspace investigates **System A+W**, an extension of the baseline System A within the AXIS framework.

System A+W introduces a second drive and minimal internal structure, transforming the agent from purely reactive to **multi-drive regulated behavior**.

The system combines:

- **Hunger** (homeostatic drive)
- **Curiosity** (novelty-seeking drive)
- A minimal **spatial world model** (visit counts)
- **Dynamic drive arbitration**

The objective is to analyze how behavior emerges from the **interaction of competing drives under strict architectural constraints**.

---

## Objectives

This investigation focuses on:

- How **competing drives** influence action selection
- Under which conditions the agent **exploits vs. explores**
- How **drive arbitration** shapes behavior over time
- The role of **novelty signals** in guiding movement
- The effect of **internal state (energy)** on behavioral regimes

This is not a performance study.  
The goal is to understand **mechanistic behavior generation**.

---

## System Description

### Drives

#### Hunger (Homeostatic)

- Depends on internal energy level
- Promotes:
  - movement toward resource-rich cells
  - consumption of resources
- Represents immediate survival pressure

---

#### Curiosity (Epistemic)

- Depends on novelty signals derived from:
  - **spatial novelty** (visit counts)
  - **sensory novelty** (difference from recent observations)
- Promotes:
  - movement toward less explored or changing areas
- Suppresses:
  - `CONSUME`
  - `STAY`

---

### World Model

- Internal **visit-count map**
- Tracks how often each relative position has been visited
- Provides input for spatial novelty

Important constraints:

- No storage of resource values
- No map of obstacles or environment structure
- No prediction

---

### Memory

- Short-term observation buffer
- Used for sensory novelty estimation
- No long-term knowledge accumulation

---

### Drive Arbitration

- Dynamic weighting between hunger and curiosity
- Hunger suppresses curiosity as energy decreases
- Curiosity dominates when energy is high

This creates **continuous behavioral transitions**, not discrete modes.

---

### Policy

- **Argmax with stochastic tie-break**
  - deterministic when a unique best action exists
  - random selection among equally scored top actions

Softmax mode may be used for comparison but is not the primary focus.

---

### Environment

- Grid-based world
- Local resource fields with regeneration
- Optional variants (e.g. delayed regeneration / cooldown)

The environment remains intentionally simple to isolate agent dynamics.

---

## Behavioral Questions

This workspace explores questions such as:

- When does the agent leave a known resource patch?
- How strong must curiosity be to override hunger?
- How does repeated visitation reduce exploration pressure?
- What patterns emerge from long-term interaction?

---

## Experimental Approach

- Controlled initial conditions
- Step-by-step inspection of:
  - observations
  - drive activations
  - arbitration weights
  - action scores
- Use of visualization tools for detailed trace analysis

Focus is on **causal understanding**, not aggregate metrics.

---

## What This System Is Not

- Not a planning agent
- Not a reinforcement learning system
- Not a predictive model

All behavior arises from **instantaneous evaluation of current state and memory**.

---

## Relation to System A

System A+W extends System A by introducing:

- a second drive (curiosity)
- internal spatial structure (visit counts)
- novelty-based modulation

System A serves as the **baseline reference** for interpreting results.

---

## Expected Insights

This workspace aims to clarify:

- how exploration can emerge from **internal drives**
- how competing motivations shape behavior
- how minimal internal structure changes system dynamics

---

## Usage

Run experiments:

```bash
axis experiments run <config>
````

Visualize episodes:

```bash
axis visualize --experiment <eid> --run <rid> --episode 1
```

---

## Notes

Behavior in this system is often non-trivial due to:

* competing drives
* nonlinear weighting
* local information constraints

Unexpected behavior should be analyzed as a **result of system dynamics**, not assumed to be an error.

