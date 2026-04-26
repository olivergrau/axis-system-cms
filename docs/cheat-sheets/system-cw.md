# System C+W Cheat Sheet

System C+W combines the dual-drive architecture of System A+W with the
predictive layer of System C.

The basic idea is:

> Hunger and curiosity still generate their own raw action preferences, but
> one shared predictive memory is interpreted through two separate trace
> systems, producing separate hunger-side and curiosity-side modulation before
> arbitration.

See also:

- [System C+W Formal Model](../system-design/system-cw/01_System%20C+W%20Model.md)
- [System C+W Worked Examples](../system-design/system-cw/02_System%20C+W%20Worked%20Examples.md)
- [Prediction](../construction-kit/prediction.md)
- [Traces](../construction-kit/traces.md)
- [Modulation](../construction-kit/modulation.md)
- [Arbitration](../construction-kit/arbitration.md)

## 1. Core Model

System C+W can be viewed as

$$
x_t = (e_t, m_t, w_t, q_t, z_t^H, z_t^C)
$$

with:

- $e_t$: energy
- $m_t$: observation buffer
- $w_t$: minimal visit-count world model
- $q_t$: shared predictive memory
- $z_t^H = (f_t^H, c_t^H)$: hunger frustration/confidence traces
- $z_t^C = (f_t^C, c_t^C)$: curiosity frustration/confidence traces

So C+W has:

- two drives: hunger and curiosity
- one shared predictive representation
- one shared predictive memory
- two separate predictive trust states

## 2. Raw Drive Layer

### Hunger

As before:

$$
d_H(t) = \mathrm{clamp}\!\left(1 - \frac{e_t}{E_{\max}},\, 0,\, 1\right)
$$

with raw scores

$$
h_t(a) = d_H(t)\,\phi_H(a,u_t)
$$

where $\phi_H$ is the usual local resource-based hunger projection.

### Curiosity

Curiosity computes directional novelty from:

- spatial novelty from visit counts
- sensory novelty from observation-buffer contrast

For each movement direction $dir \in \{UP,DOWN,LEFT,RIGHT\}$, spatial novelty is

$$
\nu_t^{spatial}(dir) = \frac{1}{(1 + N_t(dir))^k}
$$

where:

- $N_t(dir)$ is the visit count of the neighbor cell in that direction
- $k$ is the novelty sharpness

Sensory novelty is

$$
\nu_t^{sensory}(dir) = \left|r_{dir}(t) - \bar r_{dir}^{buffer}(t)\right|
$$

where $\bar r_{dir}^{buffer}(t)$ is the mean remembered resource value
for that direction in the observation buffer.

Composite novelty per direction is

$$
\nu_t(dir)
=
\alpha\,\nu_t^{spatial}(dir)
+
(1-\alpha)\,\nu_t^{sensory}(dir)
$$

with $\alpha \in [0,1]$ the spatial/sensory balance.

Mean local novelty is

$$
\bar\nu_t
=
\frac{
\nu_t(UP)+\nu_t(DOWN)+\nu_t(LEFT)+\nu_t(RIGHT)
}{4}
$$

Curiosity activation is

$$
d_C(t) = \mu_C \cdot (1 - \bar\nu_t)
$$

where $\mu_C$ is the base-curiosity parameter.

Then the raw curiosity movement scores are

$$
c_t(dir) = d_C(t)\,\nu_t(dir)
$$

and the non-movement raw curiosity scores are

$$
c_t(CONSUME) = -d_C(t)\,\lambda_{explore}
$$

$$
c_t(STAY) = -d_C(t)\,\lambda_{explore}
$$

So at the raw-drive level, C+W still looks like A+W.

## 3. Shared Predictive Representation

System C+W extracts one shared predictive feature vector:

$$
y_t^{CW} = \Omega_{CW}(u_t,\nu_t)
$$

In the concrete v1 system this is:

$$
y_t^{CW} =
(r_c, r_u, r_d, r_l, r_r,\nu_u,\nu_d,\nu_l,\nu_r,\bar\nu)
$$

So the predictive target mixes:

- exogenous local resource features
- endogenous novelty-derived features

These are compressed into a compact discrete context:

$$
s_t = C_{CW}(y_t^{CW})
$$

In the v1 system this is a 6-bit encoder:

$$
b_1 = \mathbf{1}[r_c \ge \theta_r]
$$

$$
b_2 = \mathbf{1}\!\left[\frac{r_u+r_d+r_l+r_r}{4} \ge \theta_r\right]
$$

$$
b_3 = \mathbf{1}[\max(r_u,r_d,r_l,r_r) \ge \theta_r]
$$

$$
b_4 = \mathbf{1}[\bar\nu \ge \theta_\nu]
$$

$$
b_5 = \mathbf{1}[\max(\nu_u,\nu_d,\nu_l,\nu_r) \ge \theta_\nu]
$$

$$
b_6 = \mathbf{1}[\max(\nu)-\min(\nu) \ge \theta_{\Delta\nu}]
$$

and

$$
s_t = 32b_1 + 16b_2 + 8b_3 + 4b_4 + 2b_5 + b_6
$$

Prediction is therefore keyed by:

$$
(s_t, a_t)
$$

not by absolute world coordinates.

## 4. Shared Predictive Memory

Predictive memory stores expected next shared features:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

After the next observation is seen, memory is updated by EMA:

$$
q_{t+1}(s_t,a_t)
=
(1-\eta_q)\,q_t(s_t,a_t)
+
\eta_q\,y_{t+1}^{CW}
$$

The memory is shared by both drives.

## 5. Drive-Specific Predictive Outcomes

The shared prediction is interpreted in two different ways.

### Hunger-side outcome

Define a local resource-value functional

$$
V_R(u_t) = w_{cur}\,r_c + w_{nbr}\,\bar r_n
$$

with

$$
\bar r_n = \frac{r_u+r_d+r_l+r_r}{4}
$$

Then

$$
Y_t^H(a_t) = V_R(u_{t+1}) - V_R(u_t)
$$

$$
\hat Y_t^H(a_t) = \hat V_R(q_t(s_t,a_t)) - V_R(u_t)
$$

If

$$
q_t(s_t,a_t) = (\hat r_c,\hat r_u,\hat r_d,\hat r_l,\hat r_r,\dots)
$$

then

$$
\hat V_R(q_t(s_t,a_t))
=
w_{cur}\,\hat r_c
+
w_{nbr}\,\frac{\hat r_u+\hat r_d+\hat r_l+\hat r_r}{4}
$$

### Curiosity-side outcome

For movement actions:

$$
Y_t^C(a_t) = \nu_{a_t}(t)\,Y_t^H(a_t)
$$

$$
\hat Y_t^C(a_t) = \nu_{a_t}(t)\,\hat Y_t^H(a_t)
$$

Important:

- $\nu_{a_t}(t)$ is a **pre-action contextual weight**
- in v1 it is **not** itself a predicted multiplier

### Non-movement curiosity rule

For `CONSUME` and `STAY`:

$$
Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

$$
\hat Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

So non-movement actions cannot create curiosity-positive yield in v1.

## 6. Separate Predictive Errors and Traces

Hunger-side signed errors:

$$
\varepsilon_{H,t}^+ = \max(Y_t^H - \hat Y_t^H, 0)
$$

$$
\varepsilon_{H,t}^- = \max(\hat Y_t^H - Y_t^H, 0)
$$

Curiosity-side signed errors:

$$
\varepsilon_{C,t}^+ = \max(Y_t^C - \hat Y_t^C, 0)
$$

$$
\varepsilon_{C,t}^- = \max(\hat Y_t^C - Y_t^C, 0)
$$

The trace updates are separate:

$$
f_{t+1}^H = (1-\eta_f^H)f_t^H + \eta_f^H\varepsilon_{H,t}^-
$$

$$
c_{t+1}^H = (1-\eta_c^H)c_t^H + \eta_c^H\varepsilon_{H,t}^+
$$

$$
f_{t+1}^C = (1-\eta_f^C)f_t^C + \eta_f^C\varepsilon_{C,t}^-
$$

$$
c_{t+1}^C = (1-\eta_c^C)c_t^C + \eta_c^C\varepsilon_{C,t}^+
$$

This is the key distinction from a single shared predictive trust signal.

## 7. Dual Predictive Modulation

Each drive gets its own modulation factor:

$$
\mu_H(s_t,a)
=
\mathrm{clip}\!\left(
\exp(\lambda_+^H c_t^H(s_t,a) - \lambda_-^H f_t^H(s_t,a)),
\mu_{\min}^H,\mu_{\max}^H
\right)
$$

$$
\mu_C(s_t,a)
=
\mathrm{clip}\!\left(
\exp(\lambda_+^C c_t^C(s_t,a) - \lambda_-^C f_t^C(s_t,a)),
\mu_{\min}^C,\mu_{\max}^C
\right)
$$

Then, in multiplicative mode:

$$
\tilde h_t(a)
=
\begin{cases}
h_t(a)\,\mu_H(s_t,a), & h_t(a)\ge 0 \\
h_t(a)\,/\,\mu_H(s_t,a), & h_t(a)<0
\end{cases}
$$

$$
\tilde c_t(a)
=
\begin{cases}
c_t(a)\,\mu_C(s_t,a), & c_t(a)\ge 0 \\
c_t(a)\,/\,\mu_C(s_t,a), & c_t(a)<0
\end{cases}
$$

So prediction is applied:

1. separately for hunger
2. separately for curiosity
3. before arbitration

## 8. Arbitration and Policy

After modulation, the two channels are combined:

$$
\psi_t(a) = w_H(t)\,\tilde h_t(a) + w_C(t)\,\tilde c_t(a)
$$

Then the policy selects over $\psi_t(a)$:

$$
\pi(a \mid x_t, u_t)
=
\frac{\exp(\tau\,\psi_t(a))}
{\sum_{a' \in \mathcal{A}_{adm}(u_t)} \exp(\tau\,\psi_t(a'))}
$$

So the layering is:

$$
\text{raw drive} \rightarrow \text{predictive modulation} \rightarrow \text{arbitration} \rightarrow \text{policy}
$$

## 9. Transition

System C+W keeps the A+W transition core and adds the predictive update
cycle.

### Energy

$$
e_{t+1} = \mathrm{clip}\!\left(e_t - \mathrm{cost}(a_t) + g \cdot \rho_t,\; E_{\max}\right)
$$

### Memory and world model

$$
m_{t+1} = M(m_t, u_{t+1})
$$

$$
\hat p_{t+1} = \hat p_t + \mu_t^{move}\,\Delta(a_t)
$$

$$
w_{t+1}(\hat p) =
\begin{cases}
w_t(\hat p)+1, & \hat p = \hat p_{t+1} \\
w_t(\hat p), & \text{otherwise}
\end{cases}
$$

### Predictive cycle

Using:

- pre-action observation $u_t$
- chosen action $a_t$
- post-action observation $u_{t+1}$

the system performs:

1. shared feature extraction
2. shared context encoding
3. shared prediction lookup
4. hunger-side outcome evaluation
5. curiosity-side outcome evaluation
6. separate trace updates
7. shared memory update

## 10. System / Framework Loop

### Decide side

1. observe locally
2. compute hunger raw scores
3. compute curiosity raw scores
4. extract shared predictive features and context
5. apply hunger-side predictive modulation
6. apply curiosity-side predictive modulation
7. arbitrate the two modulated channels
8. select an action

### Transition side

1. framework advances the world
2. system updates energy, observation buffer, and world model
3. system compares predicted and observed next shared features
4. system computes hunger-side and curiosity-side predictive outcomes
5. system updates the two trace states
6. system updates the shared predictive memory

Quick picture:

$$
u_t \rightarrow (h_t, c_t) \rightarrow y_t^{CW}, s_t
\rightarrow (\mu_H,\mu_C)
\rightarrow (\tilde h_t,\tilde c_t)
\rightarrow \psi_t(a) \rightarrow \pi(a) \rightarrow a_t
$$

then

$$
(u_t, a_t, u_{t+1}) \rightarrow
(Y_t^H,\hat Y_t^H,\varepsilon_H^\pm),\;
(Y_t^C,\hat Y_t^C,\varepsilon_C^\pm)
\rightarrow
(z_{t+1}^H, z_{t+1}^C, q_{t+1})
$$

## 11. One Worked Step

Assume:

- $E_{\max}=100$, $e_t=60$
- therefore $d_H = 1 - 60/100 = 0.4$
- curiosity activation $d_C = 0.6$
- arbitration weights $w_H=0.55$, $w_C=0.45$
- local resources:

$$
r_c=0.2,\quad r_u=0.8,\quad r_d=0.1,\quad r_l=0.2,\quad r_r=0.4
$$

- directional novelty:

$$
\nu_u=0.9,\quad \nu_d=0.1,\quad \nu_l=0.2,\quad \nu_r=0.5
$$

### Step 1: Raw drive tendencies

Hunger prefers `UP` because resource is strongest there.

Curiosity also prefers `UP` because novelty is strongest there.

So before prediction both drives lean toward `UP`, though for different
reasons.

### Step 2: Shared prediction

Suppose for the current context and action `UP`:

$$
\hat Y_t^H(UP) = -0.09
$$

and after the move:

$$
Y_t^H(UP)=0.16
$$

Then hunger-side surprise is strongly positive:

$$
\varepsilon_{H,t}^+ = 0.25,\qquad \varepsilon_{H,t}^- = 0
$$

Because the pre-action novelty weight for `UP` was

$$
\nu_{up}(t)=0.9
$$

the curiosity-side yield becomes:

$$
\hat Y_t^C(UP)=0.9\cdot(-0.09)=-0.081
$$

$$
Y_t^C(UP)=0.9\cdot0.16=0.144
$$

so curiosity also gets positive surprise.

### Step 3: Future effect

On a later visit to the same context:

- hunger-side confidence for `UP` increases
- curiosity-side confidence for `UP` increases
- both $\mu_H$ and $\mu_C$ for `UP` rise

If later experience diverges, the two trace systems can separate again.

That is the mental model:

> one shared expectation, two separate learned trust signals.

## 12. Config Parameters -> Mathematical Effect

System C+W uses the shared blocks

- `agent`
- `policy`
- `transition`

and adds the system-specific blocks

- `curiosity`
- `arbitration`
- `prediction.shared`
- `prediction.hunger`
- `prediction.curiosity`
- `prediction.outcomes`

### `agent`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `initial_energy` | initial value of $e_0$ | Higher values make early hunger weaker; lower values make the agent immediately more food-seeking. |
| `max_energy` | upper bound $E_{\max}$ in hunger activation and clipping | Larger `max_energy` makes the same absolute energy feel less full. |
| `buffer_capacity` | memory size of $m_t$ | Changes how much recent sensory history contributes to sensory novelty. |

### `policy`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `temperature` | softmax temperature $\tau$ | Higher values express the arbitrated score field $\psi_t(a)$ more sharply. |
| `consume_weight` | hunger consume bonus inside $h_t(CONSUME)$ | Makes consumption more or less attractive on the hunger side before prediction/arbitration. |
| `stay_suppression` | stay penalty inside $h_t(STAY)$ | Increases or decreases baseline suppression of inactivity. |
| `selection_mode` | sampling mode after score construction | Controls whether policy remains stochastic or becomes greedy. |

### `transition`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `move_cost` | movement term inside $\mathrm{cost}(a_t)$ | Makes exploration energetically cheaper or more expensive. |
| `consume_cost` | consume term inside $\mathrm{cost}(a_t)$ | Reduces or increases net hunger benefit of `CONSUME`. |
| `stay_cost` | stay term inside $\mathrm{cost}(a_t)$ | Punishes inactivity more or less strongly in the transition layer. |
| `max_consume` | cap on consumed resource $\rho_t$ | Limits energy intake per consume step. |
| `energy_gain_factor` | gain factor $g$ in energy update | Converts consumed resource into more or less energy. |

### `curiosity`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `base_curiosity` | $\mu_C$ in $d_C(t)=\mu_C(1-\bar\nu_t)$ | Scales the overall strength of the curiosity channel. |
| `spatial_sensory_balance` | $\alpha$ in $\nu_t(dir)=\alpha\nu^{spatial}+(1-\alpha)\nu^{sensory}$ | Shifts curiosity toward map novelty or sensory contrast. |
| `explore_suppression` | $\lambda_{explore}$ in raw curiosity non-movement penalties | Makes `CONSUME` and `STAY` more or less curiosity-negative. |
| `novelty_sharpness` | $k$ in $\nu_t^{spatial}(dir)=1/(1+N_t(dir))^k$ | Controls how quickly repeated visits destroy spatial novelty. |

### `arbitration`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `hunger_weight_base` | $w_H^{base}$ | Raises the minimum background influence of hunger. |
| `curiosity_weight_base` | $w_C^{base}$ | Raises the maximum available influence of curiosity when hunger is low. |
| `gating_sharpness` | $\gamma$ in the arbitration curves | Makes the handoff between hunger and curiosity softer or sharper. |

### `prediction.shared`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `memory_learning_rate` | $\eta_q$ in the shared memory EMA | Controls how quickly shared predictive expectations adapt. |
| `resource_threshold` | $\theta_r$ in context bits $b_1,b_2,b_3$ | Changes when local resource structure is treated as “present” in context encoding. |
| `novelty_threshold` | $\theta_\nu$ in context bits $b_4,b_5$ | Changes when novelty is treated as salient in the predictive context. |
| `novelty_contrast_threshold` | $\theta_{\Delta\nu}$ in bit $b_6$ | Controls when directional novelty differences matter for context identity. |
| `context_cardinality` | size of discrete context space | Must match the encoder granularity used by the system. |
| `local_resource_current_weight` | $w_{cur}$ in $V_R(u_t)$ | Increases emphasis on current-cell resource in hunger-side predictive outcomes. |
| `local_resource_neighbor_weight` | $w_{nbr}$ in $V_R(u_t)$ | Increases emphasis on average neighboring resource in hunger-side predictive outcomes. |
| `positive_weights` | weights in $\varepsilon_t^+ = \sum_j w_j^+\delta_{t,j}^+$ | Reweights which predicted feature dimensions count most as positive surprise. |
| `negative_weights` | weights in $\varepsilon_t^- = \sum_j w_j^-\delta_{t,j}^-$ | Reweights which predicted feature dimensions count most as disappointment. |

### `prediction.hunger` and `prediction.curiosity`

These two blocks have the same field structure but operate on different
trace states and therefore can shape the two drives differently.

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `frustration_rate` | $\eta_f$ in trace EMA | Makes negative surprise accumulate faster or slower for that drive. |
| `confidence_rate` | $\eta_c$ in trace EMA | Makes positive surprise accumulate faster or slower for that drive. |
| `positive_sensitivity` | $\lambda_+$ in modulation exponent | Strengthens the reinforcing effect of confidence for that drive. |
| `negative_sensitivity` | $\lambda_-$ in modulation exponent | Strengthens the suppressive effect of frustration for that drive. |
| `modulation_min` | $\mu_{\min}$ | Sets the lower bound on predictive suppression. |
| `modulation_max` | $\mu_{\max}$ | Sets the upper bound on predictive reinforcement. |
| `modulation_mode` | multiplicative/additive/hybrid modulation rule | Chooses whether prediction acts as gain control, bounded bias, or both. |
| `prediction_bias_scale` | additive bias scale in non-pure-multiplicative modes | Makes bounded prediction bias weaker or stronger. |
| `prediction_bias_clip` | clip bound for the tanh-based prediction bias | Caps additive prediction influence before scaling. |

### `prediction.outcomes`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `nonmove_curiosity_penalty` | $\kappa_{nonmove}^C$ in $Y_t^C=-\kappa_{nonmove}^C d_C(t)$ for non-movement | Controls how strongly curiosity suppresses `CONSUME` and `STAY` in the v1 outcome semantics. |

## 13. Mental Shortcut

System C+W is:

> A+W raw drives + shared prediction + separate hunger/curiosity traces +
> separate modulation + arbitration

If prediction is neutral, it collapses back to A+W.
