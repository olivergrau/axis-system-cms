# System A Cheat Sheet

System A is the minimal AXIS baseline: one drive, no world model, no planning,
no predictive memory.

Use this sheet when you need the shortest mathematically precise reminder of
how the baseline agent works.

See also:

- [System A Formal Specification](../system-design/system-a/01_System%20A%20Baseline.md)
- [System A Worked Examples](../system-design/system-a/02_System%20A%20Baseline%20Worked%20Examples.md)
- [Drives](../construction-kit/drives.md)

## 1. Core Model

System A can be viewed as

$$
x_t = (e_t, m_t)
$$

with

- $e_t \in [0, E_{\max}]$: current energy
- $m_t$: finite observation buffer

The agent does **not** have:

- a world model
- global coordinates
- a predictive model
- explicit curiosity or arbitration

## 2. Observation

The system receives a local observation

$$
u_t = S(s_t^{world})
$$

where $S$ is the sensor model over the current cell plus the four von Neumann
neighbors.

For the resource part of the observation, write

$$
u_t = (r_c, r_u, r_d, r_l, r_r, \dots)
$$

with:

- $r_c$: resource at the current cell
- $r_u, r_d, r_l, r_r$: resource values in the four directions

The system uses the von Neumann neighborhood in the fixed order:

$$
(UP, DOWN, LEFT, RIGHT)
$$

## 3. Hunger Drive

The only motivational source is hunger.

### Activation

$$
d_H(t) = \mathrm{clamp}\!\left(1 - \frac{e_t}{E_{\max}},\, 0,\, 1\right)
$$

### Per-action scores

Using the action order

$$
(UP, DOWN, LEFT, RIGHT, CONSUME, STAY)
$$

the hunger drive produces:

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

where:

- $w_c$: consume bonus weight
- $\lambda_{\text{stay}}$: stay suppression coefficient

There is no second drive and no later arbitration stage in System A. These
hunger contributions are the decisive action scores before policy selection.

## 4. Policy

The policy consumes the action scores and performs softmax selection over
admissible actions:

$$
\pi(a \mid u_t, x_t)
=
\frac{\exp\!\left(\tau\,\varphi_H(a)\right)}
{\sum_{a' \in \mathcal{A}_{adm}(u_t)} \exp\!\left(\tau\,\varphi_H(a')\right)}
$$

where $\tau > 0$ is the temperature.

Lower $\tau$ means flatter sampling. Higher $\tau$ means greedier selection.

## 5. Transition

After the framework has applied the chosen action, the system receives:

- the action outcome
- the post-action observation $u_{t+1}$

### Energy update

$$
e_{t+1} = \mathrm{clip}\!\left(e_t - \mathrm{cost}(a_t) + g \cdot \rho_t,\; E_{\max}\right)
$$

where:

- $\rho_t$: amount of resource consumed in this step
- $g$: energy gain factor

### Observation-buffer update

$$
m_{t+1} = M(m_t, u_{t+1})
$$

Here $M$ is FIFO buffer update:

- append $u_{t+1}$ to the buffer
- if capacity is exceeded, drop the oldest entry

### Termination

The episode terminates when

$$
e_{t+1} \le 0
$$

## 6. System / Framework Loop

System A participates in the loop like this:

1. **System decide**  
   Observe locally, compute hunger, produce action scores, sample an action.

2. **Framework world step**  
   The framework updates the world, applies the chosen action, and produces an
   `ActionOutcome`.

3. **System transition**  
   Update energy and observation buffer from the outcome and the new local
   observation.

So the quick loop picture is:

$$
u_t \rightarrow d_H(t) \rightarrow \varphi_H(a) \rightarrow \pi(a) \rightarrow a_t
$$

then

$$
(a_t,\; \text{world step}) \rightarrow \text{ActionOutcome} \rightarrow e_{t+1}, m_{t+1}
$$

### Loop-stage mapping

| Stage | Mathematical role in System A |
|---|---|
| `observation` | Read local sensor state $u_t$ |
| `decide` | Compute $d_H(t)$, build $\varphi_H(a)$, apply $\pi(a \mid u_t, x_t)$ |
| `action` | Emit chosen action $a_t$ |
| `world update` | Framework advances the world and resolves the action outcome |
| `transition` | Update $e_{t+1}$ and buffer state $m_{t+1}$ from outcome + $u_{t+1}$ |

## 7. One Worked Step

Assume:

- $E_{\max} = 100$
- $e_t = 40$
- $w_c = 2.5$
- $\lambda_{\text{stay}} = 0.1$
- local resources:

$$
r_c = 0.8,\quad r_u = 0.2,\quad r_d = 0,\quad r_l = 0.5,\quad r_r = 0.1
$$

### Step 1: Hunger activation

$$
d_H = 1 - \frac{40}{100} = 0.6
$$

### Step 2: Action scores

$$
\varphi_H(UP) = 0.6 \cdot 0.2 = 0.12
$$

$$
\varphi_H(DOWN) = 0.6 \cdot 0 = 0
$$

$$
\varphi_H(LEFT) = 0.6 \cdot 0.5 = 0.30
$$

$$
\varphi_H(RIGHT) = 0.6 \cdot 0.1 = 0.06
$$

$$
\varphi_H(CONSUME) = 0.6 \cdot 2.5 \cdot 0.8 = 1.20
$$

$$
\varphi_H(STAY) = -0.1 \cdot 0.6 = -0.06
$$

So the strongest score is `CONSUME`.

### Step 3: Framework applies action

Assume:

- action = `CONSUME`
- consume cost = $0.5$
- resource consumed $\rho_t = 0.4$
- energy gain factor $g = 10$

Then:

$$
e_{t+1} = 40 - 0.5 + 10 \cdot 0.4 = 43.5
$$

The buffer is then updated with the new observation $u_{t+1}$.

## 8. Config Parameters -> Mathematical Effect

System A uses only the shared config blocks:

- `agent`
- `policy`
- `transition`

### `agent`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `initial_energy` | initial value of $e_0$ | Higher values make early hunger weaker; lower values make the agent immediately more food-seeking. |
| `max_energy` | upper bound $E_{\max}$ in $d_H(t)=1-e_t/E_{\max}$ and clipping | Larger `max_energy` makes the same absolute energy feel less full; smaller `max_energy` makes hunger rise faster. |
| `buffer_capacity` | memory size in $m_t$ | Does not change the hunger formula directly, but changes how much recent observation history is retained. |

### `policy`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `temperature` | softmax temperature $\tau$ | Lower values flatten probabilities; higher values make selection greedier. |
| `consume_weight` | weight $w_c$ in $\varphi_H(CONSUME)=d_H \cdot w_c \cdot r_c$ | Raises or lowers the relative attractiveness of `CONSUME` versus movement. |
| `stay_suppression` | coefficient $\lambda_{\text{stay}}$ in $\varphi_H(STAY)=-\lambda_{\text{stay}} d_H$ | Higher values suppress `STAY` more strongly. |
| `selection_mode` | policy sampling mode, not part of the continuous model itself | `sample` keeps stochastic exploration; `argmax` makes the highest-probability action deterministic. |

### `transition`

| Config field | Mathematical role | Effect on behavior |
|---|---|---|
| `move_cost` | movement cost inside $\mathrm{cost}(a_t)$ | Higher values make exploratory movement more expensive in energy terms. |
| `consume_cost` | consume cost inside $\mathrm{cost}(a_t)$ | Higher values reduce the net gain from `CONSUME`. |
| `stay_cost` | stay cost inside $\mathrm{cost}(a_t)$ | Higher values punish inactivity even if `STAY` is selected. |
| `max_consume` | cap on resource intake $\rho_t$ | Limits how much resource can be converted into energy in one consume step. |
| `energy_gain_factor` | gain factor $g$ in $e_{t+1}=e_t-\mathrm{cost}(a_t)+g\rho_t$ | Higher values make consumed resource more valuable; lower values weaken the benefit of foraging. |

## 9. Mental Shortcut

System A is:

> local observation + hunger projection + softmax + energy/buffer update

No curiosity, no map, no prediction.
