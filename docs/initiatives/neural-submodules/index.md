# Neural Submodules in AXIS

Status: `postponed`
Phase: `conceptual research`
Objective: define how neural-network-based submodules could be integrated into
AXIS systems without abandoning explicit mathematical structure and behavioral
inspectability.
Current assessment: the neural track is currently postponed because the explicit
prediction subsystem has not yet been shown to produce robust value in the
existing world family.
Next step: resume only after world/system alignment and explicit subsystem
usefulness are clarified.
Tags: `neural`, `prediction`, `postponed`, `architecture`
Last updated: `2026-06-28`

This initiative explores how neural-network-based submodules could be
introduced into AXIS systems without abandoning the framework's explicit,
interpretable, and mathematically structured character.

The focus is not on replacing AXIS with end-to-end learned agents. The focus
is narrower and more useful: identify concrete subcomponents such as
predictors, maps, action policies, or bounded behavior modules where neural
approximators could extend the current systems while preserving scientific
clarity, controllability, and reduction paths.

The initiative is currently paused until the explicit prediction/world fit
problem has been resolved more clearly in [World-System Alignment](../world-system-alignment/index.md).

## Documents

| Document | Description |
|---|---|
| [Initial Draft](neural-submodules-draft.md) | First overview of why neural submodules are relevant for AXIS and where they could fit. |
| [Online Learning and Immediate Use](online-learning-and-immediate-use.md) | Analysis of whether AXIS-style agents can learn and use neural updates continuously instead of separating training and inference. |
| [Stabilization Principles](stabilization-principles.md) | Nature-oriented constraints and stabilization rules for online-learning neural modules inside AXIS systems. |
| [Manual vs Neural Predictor in System C and C+W](manual-vs-neural-predictor-in-c-and-cw.md) | Recapitulation of the existing explicit predictor and a concrete replacement path using a neural predictor. |
| [PyTorch Integration Architecture](pytorch-integration-architecture.md) | Technical notes on integrating PyTorch-based neural components, including optional GPU use, into AXIS runtime architecture. |
