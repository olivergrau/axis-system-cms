# System C Cheat Sheet

System C extends System A with prediction.

The basic idea is:

> Hunger still provides the base action scores, but prediction learns which
> actions in similar local contexts are unreliable or unexpectedly good, and
> modulates those action scores before policy selection.

See also:

- [System C Formal Model](../system-design/system-c/01_System%20C%20Model.md)
- [System C Worked Examples](../system-design/system-c/02_System%20C%20Worked%20Examples.md)
- [Prediction](../construction-kit/prediction.md)
- [Traces](../construction-kit/traces.md)
- [Modulation](../construction-kit/modulation.md)

## 1. Core Model

System C can be viewed as

$$
x_t = (e_t, m_t, q_t, z_t)
$$

with:

- $e_t$: energy
- $m_t$: observation buffer
- $q_t$: predictive memory over context-action pairs
- $z_t = (f_t, c_t)$: frustration/confidence trace state

System C still has:

- one drive only: hunger
- no world model
- no planning rollout
- only local observation

## 2. Hunger Base Layer

As in System A:

$$
d_H(t) = \mathrm{clamp}\!\left(1 - \frac{e_t}{E_{\max}},\, 0,\, 1\right)
$$

and the raw hunger-based action scores are:

$$
h_t(UP) = d_H \cdot r_u,\quad
h_t(DOWN) = d_H \cdot r_d,\quad
h_t(LEFT) = d_H \cdot r_l,\quad
h_t(RIGHT) = d_H \cdot r_r
$$

$$
h_t(CONSUME) = d_H \cdot w_c \cdot r_c,\quad
h_t(STAY) = -\lambda_{\text{stay}} \cdot d_H
$$

System C does **not** replace hunger. It reshapes hunger’s action expression.

## 3. Predictive Representation

### Feature extraction

From the local observation, System C extracts:

$$
y_t = \Omega(u_t) = (r_c, r_u, r_d, r_l, r_r)
$$

### Context encoding

These features are binarized and packed into a discrete context:

$$
s_t = C(y_t) \in \{0,\dots,31\}
$$

So prediction is keyed by:

$$
(s_t, a_t)
$$

not by global coordinates.

## 4. Predictive Memory

Predictive memory stores expected next features for each context-action pair:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

After the actual next observation has been seen, memory is updated by an EMA:

$$
q_{t+1}(s_t, a_t)
=
(1-\eta_q)\,q_t(s_t, a_t)
+
\eta_q\,y_{t+1}
$$

where $\eta_q$ is the memory learning rate.

## 5. Signed Prediction Error

Let the predicted next feature vector be $\hat y_{t+1}$ and the actual one be
$y_{t+1}$.

### Positive and negative components

$$
\delta_t^+ = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

$$
\delta_t^- = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

### Scalar aggregated errors

$$
\varepsilon_t^+ = \sum_j w_j^+ \delta_{t,j}^+
$$

$$
\varepsilon_t^- = \sum_j w_j^- \delta_{t,j}^-
$$

These produce:

- positive surprise / opportunity
- disappointment / unreliability

## 6. Trace Update

For the chosen context-action pair $(s_t,a_t)$:

$$
f_{t+1}(s_t,a_t)=(1-\eta_f)\,f_t(s_t,a_t) + \eta_f\,\varepsilon_t^-
$$

$$
c_{t+1}(s_t,a_t)=(1-\eta_c)\,c_t(s_t,a_t) + \eta_c\,\varepsilon_t^+
$$

where:

- $f$: frustration
- $c$: confidence
- $\eta_f,\eta_c$: trace learning rates

## 7. Predictive Modulation

Prediction acts on the hunger scores action-wise.

For each action:

$$
\tilde\mu_t(a) = \exp\!\left(\lambda_+\,c_t(s_t,a) - \lambda_-\,f_t(s_t,a)\right)
$$

$$
\mu_t(a) = \mathrm{clip}\!\left(\tilde\mu_t(a), \mu_{\min}, \mu_{\max}\right)
$$

The final action score is:

$$
\psi_t^{mult}(a) = h_t(a)\,\mu_t(a)
$$

So:

- frustration suppresses an action
- confidence amplifies an action
- hunger still provides the base motivational structure

### Additive and hybrid modes

System C also supports two richer action-level correction modes:

$$
\psi_t^{add}(a) = h_t(a) + \lambda_{\mathrm{pred}} \cdot \delta_t(a)
$$

$$
\psi_t^{hyb}(a) = h_t(a)\,\mu_t(a) + \lambda_{\mathrm{pred}} \cdot \delta_t(a)
$$

where:

- $\delta_t(a)$ is a bounded prediction bias derived from the same
  confidence/frustration trace state
- $\lambda_{\mathrm{pred}}$ is a small scaling factor

Interpretation:

- `multiplicative` is the most conservative mode
- `additive` lets prediction gently shape actions even when $h_t(a)=0$
- `hybrid` preserves reliability scaling while also allowing small tie-breaks

Prediction still does not become a full drive in these modes, because the
additive bias is explicitly bounded and intended as a correction rather than a
new motivational layer

## 8. Transition

System C keeps the System A transition core and adds the predictive update
cycle.

### Energy

$$
e_{t+1} = \mathrm{clip}\!\left(e_t - \mathrm{cost}(a_t) + g \cdot \rho_t,\; E_{\max}\right)
$$

### Observation buffer

$$
m_{t+1} = M(m_t, u_{t+1})
$$

### Predictive cycle

Using:

- pre-action observation $u_t$
- chosen action $a_t$
- post-action observation $u_{t+1}$

the system performs:

1. feature extraction
2. context lookup
3. prediction lookup
4. signed error computation
5. trace update
6. predictive-memory update

## 9. System / Framework Loop

System C’s loop is best read in two halves.

### Decide side

1. observe locally
2. compute hunger scores
3. extract predictive features and context
4. read current traces for each action
5. modulate action scores
6. softmax selection

### Transition side

1. framework updates world and applies action
2. system updates energy and buffer
3. system compares predicted next features with actual next features
4. system updates traces and predictive memory

Quick picture:

$$
u_t \rightarrow h_t(a) \rightarrow s_t \rightarrow \mu_t(a) \rightarrow
\psi_t(a) \rightarrow \pi(a) \rightarrow a_t
$$

then

$$
(u_t, a_t, u_{t+1}) \rightarrow (\varepsilon_t^+,\varepsilon_t^-)
\rightarrow (f_{t+1}, c_{t+1}, q_{t+1})
$$

### Loop-stage mapping

| Stage | Mathematical role in System C |
|---|---|
| `observation` | Read local sensor state $u_t$ and extract predictive features $y_t=\Omega(u_t)$ |
| `decide` | Compute hunger scores $h_t(a)$, encode context $s_t$, read trace state, modulate into $\psi_t(a)$ |
| `action` | Emit chosen action $a_t$ |
| `world update` | Framework advances the world and yields post-action observation $u_{t+1}$ |
| `transition` | Update energy, buffer, prediction error $(\varepsilon_t^+,\varepsilon_t^-)$, traces, and predictive memory |

## 10. One Worked Step

Assume:

- $E_{\max}=100$, $e_t=40$
- therefore $d_H = 0.6$
- local resources:

$$
r_c=0.3,\quad r_u=0.2,\quad r_d=0,\quad r_l=0.5,\quad r_r=0.1
$$

- $w_c=2.5$
- $\lambda_{\text{stay}}=0.1$

### Step 1: Raw hunger scores

$$
h_t(UP)=0.6\cdot0.2=0.12
$$

$$
h_t(LEFT)=0.6\cdot0.5=0.30
$$

$$
h_t(CONSUME)=0.6\cdot2.5\cdot0.3=0.45
$$

$$
h_t(STAY)=-0.1\cdot0.6=-0.06
$$

Suppose the current trace state for the present context gives:

- for `UP`: $f=0.4,\ c=0.1$
- for `LEFT`: $f=0.05,\ c=0.2$
- for `CONSUME`: $f=0,\ c=0$

and predictive parameters:

- $\lambda_+=1.0$
- $\lambda_-=1.5$
- $\mu_{\min}=0.3$
- $\mu_{\max}=2.0$

### Step 2: Modulation factors

For `UP`:

$$
\tilde\mu(UP)=\exp(1.0\cdot0.1 - 1.5\cdot0.4)=\exp(-0.5)\approx0.607
$$

For `LEFT`:

$$
\tilde\mu(LEFT)=\exp(1.0\cdot0.2 - 1.5\cdot0.05)=\exp(0.125)\approx1.133
$$

For `CONSUME`:

$$
\tilde\mu(CONSUME)=\exp(0)=1
$$

### Step 3: Modulated action scores

$$
\psi_t(UP)=0.12\cdot0.607\approx0.073
$$

$$
\psi_t(LEFT)=0.30\cdot1.133\approx0.340
$$

$$
\psi_t(CONSUME)=0.45\cdot1 = 0.45
$$

So `CONSUME` still wins, but `UP` has been damped and `LEFT` has been boosted.

### Step 4: Retrospective predictive update

Suppose for the chosen context-action pair:

$$
\hat y_{t+1} = (0.3, 0.2, 0, 0, 0)
$$

and the actual next features are:

$$
y_{t+1} = (0.1, 0, 0.4, 0, 0)
$$

Then:

$$
\delta_t^+ = (0,\ 0,\ 0.4,\ 0,\ 0)
$$

$$
\delta_t^- = (0.2,\ 0.2,\ 0,\ 0,\ 0)
$$

Using default weights

$$
(0.5,\ 0.125,\ 0.125,\ 0.125,\ 0.125)
$$

gives:

$$
\varepsilon_t^+ = 0.125 \cdot 0.4 = 0.05
$$

$$
\varepsilon_t^- = 0.5\cdot0.2 + 0.125\cdot0.2 = 0.125
$$

So this action-context pair gets:

- a moderate disappointment update
- a smaller positive-surprise update

which will suppress it somewhat in similar future contexts.

## 11. Config Parameters -> Mathematical Effect

System C inherits the shared `agent`, `policy`, and `transition` sections and
adds a `prediction` section.

### Shared parameters inherited from System A

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `agent.initial_energy` | initial $e_0$ | Sets how strong hunger is at the beginning of an episode. |
| `agent.max_energy` | $E_{\max}$ in $d_H(t)=1-e_t/E_{\max}$ | Rescales hunger throughout the episode. |
| `agent.buffer_capacity` | size of $m_t$ | Affects retained observation history and trace/inspection context, though the predictive state itself is separate. |
| `policy.temperature` | softmax temperature $\tau$ | Controls how sharply the modulated action scores $\psi_t(a)$ are expressed. |
| `policy.consume_weight` | $w_c$ in $h_t(CONSUME)$ | Sets the baseline attractiveness of consumption before predictive modulation. |
| `policy.stay_suppression` | $\lambda_{\text{stay}}$ in $h_t(STAY)$ | Sets the baseline penalty on inactivity before predictive modulation. |
| `transition.move_cost` / `consume_cost` / `stay_cost` | $\mathrm{cost}(a_t)$ | Sets the energetic consequence of actions after selection. |
| `transition.max_consume` | cap on $\rho_t$ | Limits the physical gain available to `CONSUME`. |
| `transition.energy_gain_factor` | gain factor $g$ | Controls how strongly successful consumption restores energy, which then feeds back into hunger. |

### `prediction`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `memory_learning_rate` | $\eta_q$ in $q_{t+1}=(1-\eta_q)q_t+\eta_q y_{t+1}$ | Higher values adapt predictions quickly; lower values make expectations more stable. |
| `context_threshold` | threshold inside the context encoder $s_t=C(y_t)$ | Changes which local feature values count as active, thereby changing how many situations collapse into the same predictive context. |
| `frustration_rate` | $\eta_f$ in the frustration EMA | Higher values make negative surprise change behavior faster. |
| `confidence_rate` | $\eta_c$ in the confidence EMA | Higher values make positive surprise strengthen actions faster. |
| `positive_sensitivity` | $\lambda_+$ in $\tilde\mu=\exp(\lambda_+ c - \lambda_- f)$ | Increases how strongly confidence amplifies an action. |
| `negative_sensitivity` | $\lambda_-$ in $\tilde\mu=\exp(\lambda_+ c - \lambda_- f)$ | Increases how strongly frustration suppresses an action. |
| `modulation_min` | lower clip bound $\mu_{\min}$ | Prevents predictive suppression from driving an action below this multiplier. |
| `modulation_max` | upper clip bound $\mu_{\max}$ | Prevents predictive amplification from exceeding this multiplier. |
| `modulation_mode` | selects `multiplicative`, `additive`, or `hybrid` composition | Chooses whether prediction only rescales drive scores or also adds a bounded correction term. |
| `prediction_bias_scale` | $\lambda_{\mathrm{pred}}$ | Sets the weight of the additive prediction correction. |
| `prediction_bias_clip` | bound on $\delta_t(a)$ | Prevents the additive correction from dominating the drive layer. |
| `positive_weights` | weights $w_j^+$ in $\varepsilon_t^+=\sum_j w_j^+\delta_{t,j}^+$ | Redistributes which predicted feature improvements count most as positive surprise. |
| `negative_weights` | weights $w_j^-$ in $\varepsilon_t^-=\sum_j w_j^-\delta_{t,j}^-$ | Redistributes which predicted disappointments count most as negative surprise. |

### Practical reduction check

If you set:

- `positive_sensitivity = 0`
- `negative_sensitivity = 0`

then $\mu_t(a)=1$ for all actions after clipping, so System C collapses back to
pure hunger expression at the action-score level.

## 12. Mental Shortcut

System C is:

> System A + local predictive memory + signed error + action-wise modulation

It does not plan. It learns which actions in similar local situations tend to
underperform or overperform.
