# Neural Submodules in AXIS

This initiative explores how neural-network-based submodules could be
introduced into AXIS systems without abandoning the framework's explicit,
interpretable, and mathematically structured character.

The focus is not on replacing AXIS with end-to-end learned agents. The focus
is narrower and more useful: identify concrete subcomponents such as
predictors, maps, action policies, or bounded behavior modules where neural
approximators could extend the current systems while preserving scientific
clarity, controllability, and reduction paths.

The initiative currently has two practical tracks:

- analysis and evaluation of the existing explicit prediction system
- neural extension of that prediction layer, but only after the explicit baseline is understood

## Documents

| Document | Description |
|---|---|
| [Initial Draft](neural-submodules-draft.md) | First overview of why neural submodules are relevant for AXIS and where they could fit. |
| [Online Learning and Immediate Use](online-learning-and-immediate-use.md) | Analysis of whether AXIS-style agents can learn and use neural updates continuously instead of separating training and inference. |
| [Stabilization Principles](stabilization-principles.md) | Nature-oriented constraints and stabilization rules for online-learning neural modules inside AXIS systems. |
| [Manual vs Neural Predictor in System C and C+W](manual-vs-neural-predictor-in-c-and-cw.md) | Recapitulation of the existing explicit predictor and a concrete replacement path using a neural predictor. |
| [Prediction System Recap](prediction-system-recap.md) | Mathematical and intuitive re-entry guide into the current explicit prediction system: predictive memory, signed error decomposition, frustration/confidence traces, and action modulation. |
| [Prediction System World-Fit Analysis](prediction-system-world-fit-analysis.md) | Systematic analysis of which existing AXIS world classes can plausibly benefit from the current prediction system, where aliasing and depletion break it, and why earlier experiments may have shown weak results. |
| [PyTorch Integration Architecture](pytorch-integration-architecture.md) | Technical notes on integrating PyTorch-based neural components, including optional GPU use, into AXIS runtime architecture. |
