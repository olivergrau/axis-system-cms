# Neural Submodules in AXIS

## 1. Purpose

This initiative explores how neural networks could be introduced into AXIS
without collapsing the existing mechanistic architecture into a single opaque
controller.

The working assumption is:

> neural networks should enter AXIS first as bounded functional submodules,
> not as replacements for drives, arbitration, transition semantics, or the
> overall cognitive architecture.

This is explicitly an exploratory line of work. The aim is not to build a
high-performing agent immediately. The aim is to understand:

- which subproblems are natural candidates for learned approximation
- how training and inference should interact in AXIS
- how far neural components can be introduced while preserving architectural
  intelligibility

---

## 2. Architectural Position

The current AXIS systems are built around explicit state, explicit drives,
explicit transitions, and traceable decision pipelines.

This should remain true at the system level.

Neural components should therefore be treated as:

- local approximators
- compact predictive modules
- latent memory refiners
- bounded policy-expression modules

They should **not** initially be treated as:

- full policy replacements
- full world-model replacements
- full-system controllers
- end-to-end cognitive architectures

The principle is:

> keep the system-level architecture mechanistic and decomposable, while
> allowing selected subfunctions to become learned.

---

## 3. Most Natural Integration Targets

### 3.1 Predictive Memory Replacement

The cleanest first target is the predictive layer in `System C` and
`System C+W`.

Today, these systems already contain:

- explicit predictive features
- explicit context encoding
- explicit prediction error decomposition
- explicit trace updates
- explicit modulation logic

This makes them ideal for replacing only the predictor itself.

Candidate replacement:

$$
\hat y_{t+1} = f_\theta(s_t, a_t)
$$

or, if desired, directly

$$
\hat y_{t+1} = f_\theta(y_t, a_t)
$$

while keeping the rest unchanged:

- signed prediction error
- frustration / confidence traces
- bounded modulation
- softmax policy

This is attractive because:

- the learned part stays narrow
- the output remains interpretable
- the surrounding system already knows how to use the prediction

### 3.2 Latent World-Model Refinement

The second natural target is the world-model side of `System A+W` and
`System C+W`.

Today, the world model is deliberately minimal:

- visit counts
- relative position update
- no planner
- no route memory

A neural submodule could augment this with a compact latent representation of
local environmental regularity, for example:

- expected resource density around the current local regime
- expected movement reliability
- expected novelty yield

This should remain a **local and bounded** module, not a hidden planner.

### 3.3 Policy Expression Module

A more aggressive option is to keep drives explicit but learn the final action
expression.

Instead of:

$$
\psi(a) \rightarrow \pi(a)
$$

through a fixed softmax-only mapping, one could use:

$$
\ell(a) = g_\theta(\psi(a), u_t, z_t, \ldots)
$$

followed by softmax over learned logits.

This is possible, but riskier than predictive substitution because it pushes
learning closer to final behavior.

### 3.4 Learned Curiosity / Salience Estimator

Another option is to keep hunger explicit while replacing or augmenting the
curiosity scoring logic.

For example, instead of fully hand-designed novelty composition:

$$
\nu_{dir} = \alpha \nu^{spatial}_{dir} + (1-\alpha)\nu^{sensory}_{dir}
$$

one could learn:

$$
\nu_{dir} = h_\theta(u_t, m_t, w_t)
$$

This is viable, but less attractive as a first experiment because the current
curiosity formulation is one of the clearer hand-designed mechanisms in AXIS.

### 3.5 Action-Outcome Model

A neural module could estimate action consequences before full planning is ever
introduced.

Examples:

- probability that movement succeeds
- expected resource yield of consume
- expected novelty yield of movement
- expected post-action feature vector

This is especially relevant for `System C+W`, where prediction is already
conceptually close to action-outcome modeling.

---

## 4. Best First Experimental Targets

### 4.1 System C with Neural Predictor

This is the strongest first experiment.

Keep:

- hunger drive
- explicit action scoring
- signed prediction error
- frustration / confidence traces
- modulation
- transition semantics

Replace only:

- explicit predictive memory table / update with a small neural predictor

This gives a very controlled experiment:

- same agent architecture
- same observation regime
- same modulation pipeline
- different predictive substrate

### 4.2 System C+W with Shared Neural Predictor

This is the second best target.

`System C+W` already combines:

- local resource features
- novelty-derived features
- shared prediction
- dual drive-specific traces

A shared neural predictor would let us test whether a learned predictive
submodule can support both:

- homeostatic evaluation
- exploratory evaluation

without replacing the drive structure itself.

### 4.3 A+W with Latent Spatial Memory

A more exploratory direction is to augment `System A+W` with a tiny latent
memory module that tracks regularities beyond simple visit counts.

This would be useful if the research question is:

> can a learned but still compact memory improve exploration before more
> sophisticated cognition is introduced?

---

## 5. Training vs Inference

This is the central design issue.

AXIS currently executes fixed equations from the first step onward. Neural
components introduce the distinction between:

- training
- inference

This needs to be handled explicitly.

### 5.1 Offline Pretraining

The neural submodule is trained outside the live episode loop on previously
generated trajectories.

Inference is then fixed during later experiments.

Advantages:

- clean separation
- reproducibility
- easy A/B comparison between trained and untrained modules

Disadvantages:

- biologically less direct
- less aligned with within-lifetime adaptation

### 5.2 Online Within-Lifetime Learning

The submodule learns during the episode or across episodes in the same run.

Advantages:

- biologically more plausible
- directly aligned with predictive adaptation
- especially appropriate for System C and System C+W

Disadvantages:

- harder to analyze
- introduces path dependence
- requires much clearer persistence and reset semantics

### 5.3 Hybrid Mode

A neural module may start from pretrained weights and continue adapting online
at a lower learning rate.

This may later become useful, but it is probably not the right first step.

### 5.4 Preferred AXIS Direction

For early AXIS experiments, the preferred order is:

1. offline-pretrained neural predictor
2. controlled online adaptation in the predictive layer
3. only later policy-side learning

That preserves interpretability while still letting us test learned
subcomponents.

---

## 6. Biological Orientation

If neural components are introduced, they should follow the same broad
biological constraints as the current AXIS systems.

That means:

- local inputs rather than global omniscient state
- small modules rather than very large models
- incremental learning rather than massive end-to-end training
- prediction before planning
- modulation before symbolic abstraction
- modular embedding rather than total replacement

In practice, this points toward:

- small MLPs
- small GRU-like recurrent modules
- simple online prediction-learning rules

and away from:

- large transformer controllers
- fully end-to-end RL as a first step
- monolithic policy networks controlling the whole agent

---

## 7. Concrete Candidate Designs

### Design A: Neural Next-Feature Predictor for System C

Input:

- predictive features $y_t$
- action $a_t$

Output:

- predicted next features $\hat y_{t+1}$

Training target:

- actual next features $y_{t+1}$

Loss:

- feature prediction loss, e.g. MSE

Everything else remains analytical.

This is the cleanest prototype because it only replaces one function.

### Design B: Shared Neural Predictor for System C+W

Input:

- shared predictive feature vector $y_t^{CW}$
- action $a_t$

Output:

- predicted next shared feature vector

Usage:

- hunger-side traces use the same prediction
- curiosity-side traces use the same prediction

This is conceptually strong because it directly tests shared learned prediction
under multi-drive interpretation.

### Design C: Latent Local Memory for A+W

Input:

- current observation
- recent observation history
- previous latent state

Output:

- updated latent state
- optional auxiliary local estimates

Usage:

- curiosity can consume the auxiliary estimates
- or the latent state can remain purely diagnostic at first

This is useful as a bridge toward richer memory without introducing planning.

---

## 8. What Should Not Be Done First

The following are poor first moves for AXIS:

- replace drives with a neural network
- replace arbitration with a neural network
- replace transition logic with a neural network
- replace the entire policy with RL training
- introduce a monolithic network that consumes observation and emits action

These options would make it too hard to tell what was gained, what was lost,
and whether the AXIS assumptions still hold.

---

## 9. Evaluation Questions

Early experiments should not ask:

- is the learned system best?
- does it beat all hand-designed baselines?

They should ask:

- does the learned submodule improve prediction quality?
- does it change behavior in a coherent way?
- does it preserve interpretability at the system level?
- what functional advantage does it provide?
- where does it introduce opacity or instability?

For predictive experiments specifically:

- does lower prediction error lead to better survival?
- does the learned predictor stabilize traces faster?
- does it change top-action ranking more often or more productively?
- does it improve exploration-foraging balance in `C+W`?

---

## 10. Initial Recommendation

The strongest first initiative is:

> integrate a small neural predictor into `System C`, while leaving drives,
> traces, modulation, policy, and transition semantics fully explicit.

Then:

1. repeat the same idea in `System C+W`
2. only afterwards explore latent spatial memory in `A+W`
3. postpone learned policy-expression modules until much later

This keeps AXIS close to its current philosophy while still allowing genuine
experimentation with more advanced technology.

---

## 11. Summary

Neural networks fit AXIS best when they are treated as:

- bounded submodules
- trained approximators of specific functions
- embedded inside a mechanistic cognitive architecture

The most promising first use is **prediction**, not full control.

That makes `System C` and `System C+W` the natural first laboratories for
testing how learned components can enter AXIS without dissolving the
architectural clarity that makes the project valuable.
