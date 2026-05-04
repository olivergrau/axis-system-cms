# System A — Baseline Investigation

## Overview

This workspace investigates **System A**, the minimal agent architecture within the AXIS framework.

System A is designed as a **purely reactive, mechanistic agent** with:

- strictly **local perception**
- a single **homeostatic drive (hunger)**
- no world model
- no planning or prediction
- no explicit exploration mechanism

The purpose of this workspace is to analyze what kind of behavior can emerge from these minimal assumptions.

---

## Objectives

The investigation focuses on the following questions:

- What behavior arises from a **single drive system** coupled to local sensory input?
- Under which conditions does the agent **move, stay, or consume**?
- Does any form of **exploration** emerge without explicit mechanisms?
- How does **policy design** (e.g. argmax vs. stochastic sampling) influence behavior?
- What are the **limits** of purely reactive control?

This workspace does not aim to optimize performance.  
It aims to understand **mechanistic consequences**.

---

## System Description

System A consists of the following components:

### Sensor

- Observes only the **current cell** and its **four direct neighbors**
- Provides:
  - traversability (blocked / free)
  - resource intensity (normalized)

No global information or derived signals are available.

---

### Drive

- Single drive: **Hunger**
- Activation increases as internal energy decreases
- Directly modulates action preferences based on local resource availability

---

### Action Space

- Movement: `UP`, `DOWN`, `LEFT`, `RIGHT`
- `CONSUME`: extract resource from current cell
- `STAY`: no movement

---

### Policy

This workspace focuses on:

- **Argmax policy with stochastic tie-break**
  - deterministic selection when a unique best action exists
  - random selection among equally scored best actions

Softmax-based sampling may be used for comparison.

---

### Environment

- Grid-based world
- Local resource fields with regeneration
- No global structure is exposed to the agent

The environment is intentionally simple to isolate agent behavior.

---

## What This Workspace Is Not

- Not a reinforcement learning setup
- Not a planning or model-based system
- Not an optimization benchmark

There is no learning algorithm involved.

---

## Experimental Approach

The investigation is based on:

- controlled initial conditions
- step-by-step behavioral observation
- inspection of action scores and decision dynamics
- comparison of policy variants

The focus is on **qualitative behavior patterns**, not metrics.

---

## Expected Insights

This workspace is intended to clarify:

- what a **minimal agent can and cannot do**
- how behavior follows from **drive + perception + policy**
- where additional mechanisms become necessary

---

## Relation to Other Systems

System A serves as the **baseline** for more advanced agents in AXIS.

In particular:

- **System A+W** extends this model with:
  - curiosity drive
  - spatial world model
  - novelty-based modulation

Understanding System A is essential before interpreting these extensions.

---

## Usage

Run experiments using the AXIS CLI:

```bash
axis experiments run <config>
````

Visualize episodes:

```bash
axis visualize --experiment <eid> --run <rid> --episode 1
```

---

## Notes

This workspace intentionally keeps the system minimal.

If behavior appears limited, repetitive, or locally constrained,
this should be interpreted as part of the investigation, not as an implementation issue.
