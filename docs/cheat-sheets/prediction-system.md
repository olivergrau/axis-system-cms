# Prediction System Cheat Sheet

This page is a compact mental-model sheet for the current explicit AXIS
prediction system used by System C and extended by System C+W.

The emphasis is not on every detail, but on rebuilding the core picture fast:

- what is predicted
- what is stored
- how error is split
- how frustration and confidence traces work
- how those traces affect the next action selection

See also:

- [System C](system-c.md)
- [System C+W](system-cw.md)
- [Prediction](../construction-kit/prediction.md)
- [Traces](../construction-kit/traces.md)
- [Modulation](../construction-kit/modulation.md)

## 1. One-Sentence Summary

The prediction system learns:

> for a given local context and a given action, what next local sensory outcome
> is expected, and whether this action has tended to under-deliver or
> over-deliver in that context.

## 2. The Core Objects

| Symbol | Meaning |
|---|---|
| $y_t$ | current predictive feature vector |
| $s_t$ | discrete context encoded from $y_t$ |
| $a_t$ | chosen action |
| $q_t(s,a)$ | predicted next feature vector for context-action pair |
| $\\delta_t^+, \\delta_t^-$ | component-wise positive / negative prediction error |
| $\\varepsilon_t^+, \\varepsilon_t^-$ | scalar aggregated positive / negative surprise |
| $f_t(s,a)$ | frustration trace for context-action pair |
| $c_t(s,a)$ | confidence trace for context-action pair |
| $\\mu_t(a)$ | action modulation factor derived from traces |

## 3. The Main Mental Model

```text
observe current local state
        |
        v
extract predictive features y_t
        |
        v
encode context s_t
        |
        v
for each action a: read q_t(s_t, a)
        |
        v
choose action using base scores + prediction modulation
        |
        v
execute action, observe y_(t+1)
        |
        v
compare predicted vs observed outcome
        |
        v
update:
- predictive memory q(s_t, a_t)
- frustration f(s_t, a_t)
- confidence c(s_t, a_t)
```

## 4. What Is Predicted?

In System C, the predictive feature vector is:

\[
y_t = (r_c, r_u, r_d, r_l, r_r)
\]

where:

- $r_c$: resource on current cell
- $r_u$: resource above
- $r_d$: resource below
- $r_l$: resource left
- $r_r$: resource right

So the predictor stores:

\[
q_t(s,a) = \hat y_{t+1}^{(s,a)}
\]

Interpretation:

> "If I do action $a$ in local context $s$, what next local resource pattern do I expect?"

## 5. Context Is Discrete

Prediction is not keyed by absolute world coordinates.
It is keyed by a quantized local context:

\[
s_t = C(y_t)
\]

So the system does **not** learn:

- "cell (12, 7) is good"

It learns something more like:

- "in this kind of local pattern, action RIGHT usually leads to this kind of next local pattern"

ASCII intuition:

```text
local observation  ---->  quantized context id

(0.2, 0.8, 0.1, 0.0, 0.0)   ->   s = 17
(0.1, 0.7, 0.0, 0.0, 0.0)   ->   maybe same s
(0.0, 0.0, 0.0, 0.8, 0.0)   ->   different s
```

## 6. Traces Are NOT Global

This is the most important structural point.

The system does **not** store one global frustration value and one global
confidence value.

It stores them per **context-action pair**:

\[
f_t(s,a), \qquad c_t(s,a)
\]

So each row in the conceptual table is separate:

```text
(context, action)   frustration   confidence
--------------------------------------------
(12, UP)              0.31          0.08
(12, RIGHT)           0.04          0.22
(7, CONSUME)          0.00          0.41
(7, STAY)             0.18          0.02
```

Interpretation:

- `UP` can be mistrusted in one context but trusted in another
- `RIGHT` can be good in one context and bad in another
- the memory is local and conditional

## 7. Prediction Error Pipeline

After action execution, the system compares:

- prediction: $\hat y_{t+1}$
- reality: $y_{t+1}$

### Step 1: component-wise positive and negative error

\[
\delta_{t,j}^+ = \max(y_{t+1,j} - \hat y_{t+1,j}, 0)
\]

\[
\delta_{t,j}^- = \max(\hat y_{t+1,j} - y_{t+1,j}, 0)
\]

These are still vectors.

### Step 2: weighted scalar aggregation

\[
\varepsilon_t^+ = \sum_j w_j^+\delta_{t,j}^+
\]

\[
\varepsilon_t^- = \sum_j w_j^-\delta_{t,j}^-
\]

These are scalars.

ASCII view:

```text
vector error per feature

current   up   down  left  right
  |       |      |     |      |
  v       v      v     v      v
 delta+ / delta- per channel
  |       |      |     |      |
  +-------+------+-----+------+-----> weighted sum

result:
  epsilon+   epsilon-
```

## 8. Meaning of Positive and Negative Surprise

| Quantity | Meaning |
|---|---|
| $\delta^+$ / $\varepsilon^+$ | observed outcome was better / richer than expected |
| $\delta^-$ / $\varepsilon^-$ | observed outcome was worse / poorer than expected |

In System C that is directly about local resource structure.

Example intuition:

```text
expected next current cell: 0.6
observed next current cell: 0.8

-> positive surprise on that feature
```

```text
expected next current cell: 0.6
observed next current cell: 0.2

-> negative surprise on that feature
```

## 9. Trace Update

Only the actually experienced context-action pair gets updated.

\[
f_{t+1}(s_t,a_t) = (1-\eta_f)f_t(s_t,a_t) + \eta_f\varepsilon_t^-
\]

\[
c_{t+1}(s_t,a_t) = (1-\eta_c)c_t(s_t,a_t) + \eta_c\varepsilon_t^+
\]

Everything else stays unchanged.

ASCII intuition:

```text
current step uses:   context = 12, action = UP

update only:
- f(12, UP)
- c(12, UP)

leave untouched:
- f(12, RIGHT)
- c(12, RIGHT)
- f(7, UP)
- c(7, UP)
- ...
```

## 10. Why Traces Matter

The traces are EMA-compressed history.

That means:

- recent experience matters more
- older experience still matters, but decays
- action modulation is based on remembered local history, not just the last error

So yes:

> the next decision is influenced by the past history of that context-action pair,
> but only through the compressed trace values.

## 11. What Action Modulation Uses

This is the key answer to the usual confusion:

> action modulation does **not** use the fresh raw error directly.
> It uses the stored traces $f_t(s_t,a)$ and $c_t(s_t,a)$.

For each candidate action $a$ in the current context $s_t$:

\[
\sigma_t(a) = \lambda_+ c_t(s_t,a) - \lambda_- f_t(s_t,a)
\]

\[
\tilde \mu_t(a) = \exp(\sigma_t(a))
\]

\[
\mu_t(a) = \mathrm{clip}(\tilde \mu_t(a), \mu_{min}, \mu_{max})
\]

So the data flow is:

```text
past outcomes in (s,a)
        |
        v
stored in traces f(s,a), c(s,a)
        |
        v
sigma(a) = + confidence - frustration
        |
        v
mu(a) modulation factor
        |
        v
base action score gets amplified or damped
```

## 12. Per-Action Modulation in the Current Context

Suppose the current context is `s = 12`.
Then for the next decision the system reads:

```text
(12, UP)
(12, DOWN)
(12, LEFT)
(12, RIGHT)
(12, CONSUME)
(12, STAY)
```

Each action gets its own local trace pair.

Example:

| Action | $f_t(12,a)$ | $c_t(12,a)$ | likely effect |
|---|---:|---:|---|
| UP | 0.30 | 0.05 | suppressed |
| RIGHT | 0.02 | 0.20 | amplified |
| CONSUME | 0.00 | 0.25 | amplified |
| STAY | 0.12 | 0.00 | suppressed |

This is how the system expresses local trust and mistrust.

## 13. Timeline of One Decision Cycle

```text
Before decision:
- read current context s_t
- read traces f_t(s_t,a), c_t(s_t,a) for every action a
- modulate base scores
- select action a_t

After outcome:
- observe y_(t+1)
- compute delta+ / delta-
- compute epsilon+ / epsilon-
- update q(s_t, a_t)
- update f(s_t, a_t), c(s_t, a_t)

Effect:
- the current outcome influences the NEXT decision, not the already completed one
```

## 14. What the System Is Really Learning

The cleanest intuition is:

- baseline drive says what looks attractive now
- prediction says what has historically been reliable here

So the system is learning **local action trust**.

Not:

- global world structure
- long-horizon planning
- generic reinforcement values

But:

- in this local context, which action tends to under-deliver?
- in this local context, which action tends to over-deliver?

## 15. Failure Mode to Keep in Mind

The biggest conceptual risk is context aliasing.

That means:

- same local context id
- same action
- but different hidden world state
- therefore different actual outcomes

Then the system may learn a bad average.

ASCII intuition:

```text
same-looking local context s
        |
        +-- world state A -> action RIGHT -> good outcome
        |
        +-- world state B -> action RIGHT -> poor outcome

Predictor sees only s, not the hidden difference.
```

This is why the prediction system may fail or become misleading in worlds with:

- depletion history
- hidden regrowth phase
- strong hidden-state dependence

## 16. Fast Mental Model

If you want the fastest possible reconstruction, use this chain:

```text
observation
   -> context
   -> predicted next local outcome per action
   -> action chosen
   -> observed next local outcome
   -> positive/negative surprise
   -> update local traces for (context, chosen action)
   -> next time: use those traces to amplify or suppress actions in that context
```

That is the current prediction system in one line.
