# System A+W Cheat Sheet

System A+W extends System A with:

- a second drive: curiosity
- a minimal world model: visit counts in a relative coordinate frame
- dynamic drive arbitration between hunger and curiosity

See also:

- [System A+W Formal Model](../system-design/system-a+w/01_System%20A+W%20Model.md)
- [System A+W Worked Examples](../system-design/system-a+w/02_System%20A+W%20Worked%20Examples.md)
- [Drives](../construction-kit/drives.md)
- [Arbitration](../construction-kit/arbitration.md)

## 1. Core Model

System A+W can be viewed as

$$
x_t = (e_t, m_t, \hat p_t, w_t)
$$

with:

- $e_t$: energy
- $m_t$: observation buffer
- $\hat p_t \in \mathbb{Z}^2$: internal relative position estimate
- $w_t$: visit-count world model

The key extension over System A is:

- hunger says what is valuable now
- curiosity says what is novel
- arbitration decides how much each drive matters

## 2. Observation

Observation is still purely local:

$$
u_t = S(s_t^{world})
$$

with the same local resource tuple

$$
(r_c, r_u, r_d, r_l, r_r, \dots)
$$

No global map is observed directly.

## 3. Hunger Component

The hunger part is unchanged from System A.

### Activation

$$
d_H(t) = \mathrm{clamp}\!\left(1 - \frac{e_t}{E_{\max}},\, 0,\, 1\right)
$$

### Contributions

$$
\varphi_H(UP) = d_H \cdot r_u
$$

$$
\varphi_H(DOWN) = d_H \cdot r_d
$$

$$
\varphi_H(LEFT) = d_H \cdot r_l
$$

$$
\varphi_H(RIGHT) = d_H \cdot r_r
$$

$$
\varphi_H(CONSUME) = d_H \cdot w_c \cdot r_c
$$

$$
\varphi_H(STAY) = -\lambda_{\text{stay}} \cdot d_H
$$

## 4. Curiosity Component

Curiosity is built from two novelty signals.

### Spatial novelty

For each direction:

$$
\nu^{spatial}_{dir} = \frac{1}{(1 + w(\text{neighbor}_{dir}))^k}
$$

where:

- $w(\text{neighbor}_{dir})$: visit count of the neighbor cell in the internal
  world model
- $k$: novelty sharpness

### Sensory novelty

For each direction:

$$
\nu^{sensory}_{dir} = \left|r_{dir}(t) - \bar r_{dir}\right|
$$

where $\bar r_{dir}$ is the mean remembered resource value for that direction
in the observation buffer.

### Composite novelty

$$
\nu_{dir} = \alpha \nu^{spatial}_{dir} + (1-\alpha)\nu^{sensory}_{dir}
$$

where $\alpha \in [0,1]$ balances spatial and sensory novelty.

### Curiosity activation

Let $\bar\nu_t$ be novelty saturation derived from the buffer. Then

$$
d_C(t) = \mu_C \cdot (1 - \bar\nu_t)
$$

where $\mu_C$ is the base-curiosity level.

### Curiosity action contributions

$$
\varphi_C(UP) = d_C \cdot \nu_u
$$

$$
\varphi_C(DOWN) = d_C \cdot \nu_d
$$

$$
\varphi_C(LEFT) = d_C \cdot \nu_l
$$

$$
\varphi_C(RIGHT) = d_C \cdot \nu_r
$$

$$
\varphi_C(CONSUME) = -d_C \cdot \lambda_{\text{explore}}
$$

$$
\varphi_C(STAY) = -d_C \cdot \lambda_{\text{explore}}
$$

## 5. Drive Arbitration

Hunger gates curiosity through dynamic weights.

### Weight functions

$$
w_H(t) = w_H^{base} + (1 - w_H^{base}) \cdot d_H(t)^\gamma
$$

$$
w_C(t) = w_C^{base} \cdot (1 - d_H(t))^\gamma
$$

where:

- $w_H^{base}$: minimum hunger weight
- $w_C^{base}$: maximum curiosity weight
- $\gamma$: gating sharpness

### Combined action score

For each action $a$:

$$
\psi(a,t) = w_H(t)\,\varphi_H(a) + w_C(t)\,\varphi_C(a)
$$

Then the softmax policy selects from $\psi(a,t)$:

$$
\pi(a \mid x_t, u_t)
=
\frac{\exp(\tau\,\psi(a,t))}
{\sum_{a' \in \mathcal{A}_{adm}(u_t)} \exp(\tau\,\psi(a',t))}
$$

## 6. Transition and World Model Update

System A+W keeps the System A energy update and adds dead reckoning plus
visit-count updating.

### Energy

$$
e_{t+1} = \mathrm{clip}\!\left(e_t - \mathrm{cost}(a_t) + g \cdot \rho_t,\; E_{\max}\right)
$$

### Observation-buffer update

$$
m_{t+1} = M(m_t, u_{t+1})
$$

where $M$ is FIFO update:

- append $u_{t+1}$
- drop the oldest entry if capacity is exceeded

### Relative position update

Let $\Delta(a_t)$ be the movement vector for the action and let
$\mu_t^{move} \in \{0,1\}$ indicate whether movement actually happened.

$$
\hat p_{t+1} = \hat p_t + \mu_t^{move}\,\Delta(a_t)
$$

### Visit-count update

$$
w_{t+1}(\hat p) =
\begin{cases}
w_t(\hat p) + 1 & \text{if } \hat p = \hat p_{t+1} \\
w_t(\hat p) & \text{otherwise}
\end{cases}
$$

The key constraint is:

> The world model does not read absolute coordinates. It updates only from
> chosen action + movement success/failure.

## 7. System / Framework Loop

System A+W inserts its components into the loop like this:

1. **System decide**
   - observe locally
   - compute hunger
   - compute curiosity
   - compute arbitration weights
   - combine action scores
   - select action

2. **Framework world step**
   - update world dynamics
   - apply chosen action
   - report outcome including whether movement occurred

3. **System transition**
   - update energy
   - update observation buffer
   - update relative position
   - update visit-count map

Quick picture:

$$
u_t \rightarrow (d_H,\varphi_H),\ (d_C,\varphi_C) \rightarrow (w_H,w_C)
\rightarrow \psi(a,t) \rightarrow \pi(a) \rightarrow a_t
$$

then

$$
(a_t,\mu_t^{move},\rho_t) \rightarrow e_{t+1},\,\hat p_{t+1},\,w_{t+1}
$$

### Loop-stage mapping

| Stage | Mathematical role in System A+W |
|---|---|
| `observation` | Read local sensor state $u_t$ |
| `decide` | Compute hunger $(d_H,\varphi_H)$, curiosity $(d_C,\varphi_C)$, then arbitration weights $(w_H,w_C)$ and combined score $\psi(a,t)$ |
| `action` | Emit chosen action $a_t$ |
| `world update` | Framework advances the world, applies the action, and reports movement success $\mu_t^{move}$ plus consumption outcome $\rho_t$ |
| `transition` | Update energy, observation buffer, relative position $\hat p_{t+1}$, and visit-count model $w_{t+1}$ |

## 8. One Worked Step

Assume:

- $E_{\max}=100$, $e_t=80$
- therefore $d_H = 1 - 80/100 = 0.2$
- current-cell resource $r_c = 0$
- neighbor resources:

$$
r_u=0.2,\quad r_d=0,\quad r_l=0.5,\quad r_r=0.1
$$

- curiosity parameters:
  - $\mu_C = 1.0$
  - $\alpha = 0.7$
  - $\lambda_{\text{explore}}=0.3$
  - $k=1$
- novelty saturation $\bar\nu_t = 0.3$, so:

$$
d_C = 1.0 \cdot (1 - 0.3) = 0.7
$$

### Step 1: Hunger contributions

$$
\varphi_H(UP)=0.2\cdot0.2=0.04,\quad
\varphi_H(DOWN)=0,\quad
\varphi_H(LEFT)=0.2\cdot0.5=0.10,\quad
\varphi_H(RIGHT)=0.2\cdot0.1=0.02
$$

$$
\varphi_H(CONSUME)=0,\quad
\varphi_H(STAY)=-0.1\cdot0.2=-0.02
$$

### Step 2: Curiosity contributions

Suppose visit counts for the four neighbors are:

$$
(3, 0, 1, 5)
$$

Then spatial novelty is:

$$
\left(\frac14,\ 1,\ \frac12,\ \frac16\right)
\approx (0.25,\ 1.00,\ 0.50,\ 0.17)
$$

Assume sensory novelty is:

$$
(0.10,\ 0.40,\ 0.20,\ 0.00)
$$

Then composite novelty becomes:

$$
\nu_u = 0.7\cdot0.25 + 0.3\cdot0.10 = 0.205
$$

$$
\nu_d = 0.7\cdot1.00 + 0.3\cdot0.40 = 0.82
$$

$$
\nu_l = 0.7\cdot0.50 + 0.3\cdot0.20 = 0.41
$$

$$
\nu_r = 0.7\cdot0.17 + 0.3\cdot0.00 \approx 0.12
$$

So:

$$
\varphi_C = (0.205,\ 0.82,\ 0.41,\ 0.12,\ -0.3,\ -0.3)
$$

### Step 3: Arbitration

Let:

- $w_H^{base}=0.3$
- $w_C^{base}=1.0$
- $\gamma=2$

Then:

$$
w_H = 0.3 + 0.7\cdot(0.2)^2 = 0.328
$$

$$
w_C = 1.0\cdot(1-0.2)^2 = 0.64
$$

Now compare two directions:

For `DOWN`:

$$
\psi(DOWN) = 0.328\cdot0.2\cdot0 + 0.64\cdot0.7\cdot0.82 \approx 0.367
$$

For `LEFT`:

$$
\psi(LEFT) = 0.328\cdot0.2\cdot0.10 + 0.64\cdot0.7\cdot0.41 \approx 0.190
$$

So `DOWN` wins despite containing no visible resource, because it is much more
novel.

### Step 4: Transition

Assume the chosen action is `DOWN` and movement succeeds.

Then with

$$
\Delta(DOWN) = (0,-1), \qquad \mu_t^{move}=1
$$

the internal relative position updates as:

$$
\hat p_{t+1} = \hat p_t + (0,-1)
$$

and the visit count at that new relative location increases by one.

## 9. Config Parameters -> Mathematical Effect

System A+W inherits the shared `agent`, `policy`, and `transition` sections and
adds:

- `curiosity`
- `arbitration`

### Shared parameters inherited from System A

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `agent.initial_energy` | initial $e_0$ | Higher values start the agent in a more curiosity-permissive regime; lower values start it closer to hunger-dominance. |
| `agent.max_energy` | $E_{\max}$ in $d_H(t)=1-e_t/E_{\max}$ | Rescales hunger and therefore indirectly gates curiosity. |
| `agent.buffer_capacity` | size of $m_t$ | Changes how much recent sensory history is available for novelty saturation and sensory novelty estimates. |
| `policy.temperature` | softmax temperature $\tau$ | Higher values make the combined score $\psi(a,t)$ more decisive; lower values flatten the policy. |
| `policy.consume_weight` | $w_c$ in the hunger consume term | Makes hunger more or less willing to trade exploration for immediate consumption. |
| `policy.stay_suppression` | $\lambda_{\text{stay}}$ in $\varphi_H(STAY)$ | Penalizes hunger-driven inactivity. |
| `transition.move_cost` / `consume_cost` / `stay_cost` | $\mathrm{cost}(a_t)$ | Sets the energy economics after action selection. |
| `transition.max_consume` | cap on $\rho_t$ | Limits how much a consume step can restore energy. |
| `transition.energy_gain_factor` | gain factor $g$ | Controls how strongly successful consumption restores energy, which in turn feeds back into $d_H$ and the arbitration regime. |

### `curiosity`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `base_curiosity` | $\mu_C$ in $d_C(t)=\mu_C(1-\bar\nu_t)$ | Global scale of curiosity activation. Setting it to 0 collapses the model toward System A. |
| `spatial_sensory_balance` | $\alpha$ in $\nu=\alpha\nu^{spatial}+(1-\alpha)\nu^{sensory}$ | Moves curiosity toward visit-count novelty (`1.0`) or observation-difference novelty (`0.0`). |
| `explore_suppression` | $\lambda_{\text{explore}}$ in $\varphi_C(CONSUME)$ and $\varphi_C(STAY)$ | Higher values make curiosity more anti-consume and anti-stay. |
| `novelty_sharpness` | exponent $k$ in $\nu^{spatial}=1/(1+w)^k$ | Higher values make revisits decay in novelty faster; lower values keep revisited places more interesting. |

### `arbitration`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `hunger_weight_base` | $w_H^{base}$ in $w_H(t)=w_H^{base}+(1-w_H^{base})d_H^\gamma$ | Minimum hunger influence even when satiated. |
| `curiosity_weight_base` | $w_C^{base}$ in $w_C(t)=w_C^{base}(1-d_H)^\gamma$ | Maximum curiosity influence in low-hunger regimes. |
| `gating_sharpness` | $\gamma$ | Controls how abruptly the system shifts from exploration-dominant to hunger-dominant behavior. |

## 10. Mental Shortcut

System A+W is:

> System A + curiosity + visit-count map + hunger-gated arbitration

The main difference from System A is that behavior is no longer only
resource-seeking; it is resource-seeking under competition with novelty.
