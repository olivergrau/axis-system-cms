# System A Baseline Worked Examples

## Metadata
- Project: AXIS – Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Worked Example / Formal Companion Note
- Status: Draft v1.0

## 1. Purpose of this Document
This document provides **worked example scenarios** for _System A (Baseline)_.

The goal is:

- to **validate internal consistency** of the formal model
- to **demonstrate concrete execution behavior** of the agent
- to **prepare for implementation** by defining reproducible calculation paths

No new concepts are introduced.  
All examples strictly follow the definitions from:

- `System_A_Baseline.md`
- `The_World.md`
- `The_Sensor_Model.md`

---

## 2. Scope and Constraints
This document assumes:

- **Single drive only**: Hunger (no exploration, no multi-drive interaction)
- **No world model**
- **No planning**
- **No stochastic learning**
- **Deterministic policy evaluation (unless explicitly stated otherwise)**

Memory exists but is **not used for decision-making**.

---

## 3. Structure of Worked Examples
Each example follows the same structure:

1. **Initial State Definition**
2. **Local Observation (Sensor Input)**
3. **Drive Evaluation (Hunger)**
4. **Action Scoring**
5. **Policy Selection**
6. **State Transition**
7. **Post-State Analysis**

This mirrors the **execution cycle** and ensures traceability.

---

## 4. Common Definitions and Notation
To avoid ambiguity, all examples use:

### **4.1 State Variables**

- $x_t$: full system state at time $t$
- $E_t$: current energy level
- $h_t$: hunger level

### **4.2 Hunger Definition**

- $h_t = 1 - \frac{E_t}{E_{\text{max}}}$

### **4.3 Action Set**

- $A = \{ \text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{STAY}, \text{CONSUME} \}$

### **4.4 Sensor Output**

- Local observation window $u_t$ as defined in `The_Sensor_Model.md`

### **4.5 World Assumptions**

- Grid-based environment
- Discrete time steps
- Deterministic transitions
- Energy gain only via **CONSUME**

---

## 5. Example Categories
The examples are grouped by **behavioral function**.

---

## 5.1 Example Group A: Minimal Survival Dynamics

### A1. Random Movement Under Hunger Pressure (Worked Example)

#### 1. Objective
This example evaluates the agent’s behavior under the following conditions:

- The agent is **hungry**
- **No resource is visible** in the local observation
- No directional bias exists in the environment

The goal is to determine how the policy distributes action probabilities when **only the hunger drive is active**, but **no actionable resource signal is present**.

---

#### 2. Model Equations Used

##### 2.1 Hunger

$$  
h_t = 1 - \frac{e_t}{E_{\max}}  
$$

##### 2.2 Drive Activation

$$  
d_H(t) = h_t  
$$

##### 2.3 Action Scoring

$$
\psi(a) = d_H(t)\cdot \phi_H(a, u_t)  
$$

Special case for **STAY**: 

$$
\psi(\text{STAY}) = -\lambda_{stay}\cdot d_H(t)  
$$

##### 2.4 Coupling Function

- For **CONSUME**:  

    $$  
    \phi_H(\text{CONSUME}, u_t) = w_{consume} \cdot r_c(t)  
    $$
    
- For **movement actions**:  

$$
\phi_H(\text{UP}, u_t)=r_{up}(t)
$$

$$
\phi_H(\text{DOWN}, u_t)=r_{down}(t)
$$

$$
\phi_H(\text{LEFT}, u_t)=r_{left}(t)
$$

$$
\phi_H(\text{RIGHT}, u_t)=r_{right}(t)
$$ 

If no resource is present:  

$$  
r_c = r_{up} = r_{down} = r_{left} = r_{right} = 0  
$$ 

Therefore:

$$
\phi_H(\text{CONSUME},u_t)=0
$$

and

$$
\phi_H(\text{UP},u_t)=\phi_H(\text{DOWN},u_t)=\phi_H(\text{LEFT},u_t)=\phi_H(\text{RIGHT},u_t)=0
$$

---

##### 2.5 Policy (Softmax)

$$ 
P(a \mid x_t, u_t) =  
\frac{\exp(\beta \psi(a))}{\sum_{a'} \exp(\beta \psi(a'))}  
$$

---

#### 3. Scenario Definition

##### 3.1 Internal State

$$
E_{\max} = 100  
$$ 

$$
e_t = 50  
$$

$$ 
h_t = 1 - \frac{50}{100} = 0.5  
$$

$$
d_H(t) = 0.5  
$$

---

##### 3.2 Sensor Input
All cells are traversable, but no resource is present:

$$  
u_t =  
(1,0, 1,0, 1,0, 1,0, 1,0)  
$$

Interpretation:

- current cell: traversable, no resource
- all four neighbors: traversable, no resource

---

##### 3.3 Policy Parameters

$$  
\lambda_{stay} = 1  
$$ 

$$
\beta = 2  
$$

---

#### 4. Drive Evaluation

$$  
d_H(t) = h_t = 0.5  
$$

The agent is in a **moderate hunger state**.

---

#### 5. Action Scoring
Since no resource is visible:

$$
r_c = 0, \quad \bar{r}_{neighbors} = 0  
$$

---

##### 5.1 CONSUME

$$
\psi(\text{CONSUME})=d_H(t)\cdot w_{\text{consume}}\cdot r_c
=0.5\cdot w_{\text{consume}}\cdot 0=0
$$

---

##### 5.2 Movement Actions

$$  
\psi(\text{UP}) =  
\psi(\text{DOWN}) =  
\psi(\text{LEFT}) =  
\psi(\text{RIGHT}) =  
0.5 \cdot 0 = 0  
$$

---

##### 5.3 STAY

$$  
\psi(\text{STAY}) = -1 \cdot 0.5 = -0.5  
$$

---

#### 6. Resulting Scores

$$  
\psi(\text{UP}) = 0  
$$ 

$$
\psi(\text{DOWN}) = 0  
$$ 

$$
\psi(\text{LEFT}) = 0  
$$ 

$$
\psi(\text{RIGHT}) = 0  
$$ 

$$
\psi(\text{CONSUME}) = 0  
$$ 

$$
\psi(\text{STAY}) = -0.5  
$$

---

#### 7. Policy Computation

##### 7.1 Exponentials

$$
\exp(2 \cdot 0) = 1  
$$ 

$$
\exp(2 \cdot (-0.5)) = \exp(-1) \approx 0.367879  
$$

---

##### 7.2 Normalization Constant

$$  
Z = 5 \cdot 1 + 0.367879 = 5.367879  
$$

---

##### 7.3 Action Probabilities
For each of:

- UP, DOWN, LEFT, RIGHT, CONSUME:
    

$$
P(a) = \frac{1}{5.367879} \approx 0.186293  
$$

For STAY:

$$
P(\text{STAY}) = \frac{0.367879}{5.367879} \approx 0.068533  
$$

---

#### 8. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------- | ----------- |
| UP      | 0.0             | 0.1863      |
| DOWN    | 0.0             | 0.1863      |
| LEFT    | 0.0             | 0.1863      |
| RIGHT   | 0.0             | 0.1863      |
| CONSUME | 0.0             | 0.1863      |
| STAY    | -0.5            | 0.0685      |

---

#### 9. Interpretation
The result shows:

- **STAY is actively suppressed**    
- All other actions remain **equally likely**

This leads to:

- ~74.5% probability for movement (combined)
- ~18.6% probability for CONSUME (even though no resource exists)
- ~6.9% probability for STAY

---

#### 10. Behavioral Insight
This example demonstrates a key property of the baseline system:

> Hunger induces **non-passive stochastic behavior**, not pure directional movement.

The agent:

- avoids inactivity
- explores the environment through random action selection
- may attempt **invalid consumption actions**

This is not a flaw in the mathematical formulation, but a direct consequence of:

- the absence of a world model
- purely local perception
- lack of action filtering

---

#### 11. State Transition Implications (Qualitative)
Since no resource is present:

- $\Delta R_t^{cons} = 0$
    
- $\Delta e_t^{env} = 0$
    

All actions result in **energy loss only**:

- movement → $e_{t+1} = e_t - c_{move}$
- consume → $e_{t+1} = e_t - c_{consume}$
- stay → $e_{t+1} = e_t - c_{stay}$

---

#### 12. Conclusion
Under pure hunger activation without visible resources:

- the agent becomes **active but not directed**
- behavior is **stochastic with suppressed passivity**
- no meaningful goal-directed motion emerges

This example confirms that the baseline system:

- is internally consistent
- produces plausible primitive behavior
- is ready for further validation in resource-driven scenarios

---

### A2. Energy Depletion Over Time (Worked Example)

#### 1. Objective
This example evaluates whether the baseline system correctly produces **energy depletion over repeated action execution** when:

* no resource is encountered,
* no energy intake occurs,
* the agent continues to move through the environment.

The goal is to verify that:

* energy decreases monotonically under repeated movement,
* hunger increases accordingly,
* the terminal condition becomes inevitable if no resource is found.

This example does not test resource interaction.
It isolates the internal energy dynamics under sustained unsuccessful movement.

---

#### **2. Model Equations Used**

##### 2.1 Energy Update
For any action $a_t$, the baseline transition defines:

$$
e_{t+1} = \mathrm{clip}\Bigl(e_t - c(a_t) + \Delta e_t^{env}, 0, E_{\max}\Bigr)
$$

where:

* $c(a_t)$ is the action cost
* $\Delta e_t^{env}$ is the environmental energy gain from successful consumption

---

##### 2.2 Environmental Energy Transfer
If no resource is consumed:

$$
\Delta R_t^{cons} = 0
$$

therefore:

$$
\Delta e_t^{env} = \kappa \cdot \Delta R_t^{cons} = 0
$$

---

##### 2.3 Hunger

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

---

##### 2.4 Terminal Condition
The system terminates if:

$$
e_{t+1} = 0
$$

as defined in the baseline transition model. 

---

#### 3. Scenario Definition
We define a simple multi-step trajectory in which the agent repeatedly executes **movement actions** without encountering food.

##### 3.1 Internal Parameters

$$
E_{\max} = 100
$$

$$
e_0 = 60
$$

##### 3.2 Action Cost
For this example, we instantiate the movement cost as:

$$
c_{move} = 5
$$

Thus, for every movement action:

$$
c(a_t) = 5
$$

##### 3.3 Environmental Condition
No resource is encountered at any step, so:

$$
\Delta e_t^{env} = 0 \qquad \forall t
$$

##### 3.4 Action Sequence
We assume the agent executes a sequence of movement actions:

$$
a_0, a_1, a_2, \dots \in \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\}
$$

The specific directions do not matter for this example.
Only the movement cost matters.

---

#### 4. Reduced Transition Equation for This Scenario
Since every action is a movement action and no resource is consumed:

$$
e_{t+1} = e_t - c_{move}
$$

with:

$$
c_{move} = 5
$$

Thus:

$$
e_{t+1} = e_t - 5
$$

Because the value remains within bounds until depletion, clipping is inactive until the final step.

---

#### 5. Closed-Form Expression
After $n$ movement steps:

$$
e_n = e_0 - n \cdot c_{move}
$$

Substituting the scenario values:

$$
e_n = 60 - 5n
$$

and therefore:

$$
h_n = 1 - \frac{60 - 5n}{100}
$$

which simplifies to:

$$
h_n = 0.4 + 0.05n
$$

as long as $e_n > 0$.

---

#### 6. Step-by-Step Calculation
We now compute the trajectory explicitly.

##### Step 0

Initial state:

$$
e_0 = 60
$$

$$
h_0 = 1 - \frac{60}{100} = 0.4
$$

---

##### Step 1

$$
e_1 = 60 - 5 = 55
$$

$$
h_1 = 1 - \frac{55}{100} = 0.45
$$

---

##### Step 2

$$
e_2 = 55 - 5 = 50
$$

$$
h_2 = 1 - \frac{50}{100} = 0.50
$$

---

##### Step 3

$$
e_3 = 50 - 5 = 45
$$

$$
h_3 = 1 - \frac{45}{100} = 0.55
$$

---

##### Step 4

$$
e_4 = 45 - 5 = 40
$$

$$
h_4 = 1 - \frac{40}{100} = 0.60
$$

---

##### Step 5

$$
e_5 = 40 - 5 = 35
$$

$$
h_5 = 1 - \frac{35}{100} = 0.65
$$

---

##### Step 6

$$
e_6 = 35 - 5 = 30
$$

$$
h_6 = 1 - \frac{30}{100} = 0.70
$$

---

##### Step 7

$$
e_7 = 30 - 5 = 25
$$

$$
h_7 = 1 - \frac{25}{100} = 0.75
$$

---

##### Step 8

$$
e_8 = 25 - 5 = 20
$$

$$
h_8 = 1 - \frac{20}{100} = 0.80
$$

---

##### Step 9

$$
e_9 = 20 - 5 = 15
$$

$$
h_9 = 1 - \frac{15}{100} = 0.85
$$

---

##### Step 10

$$
e_{10} = 15 - 5 = 10
$$

$$
h_{10} = 1 - \frac{10}{100} = 0.90
$$

---

##### Step 11

$$
e_{11} = 10 - 5 = 5
$$

$$
h_{11} = 1 - \frac{5}{100} = 0.95
$$

---

##### Step 12

$$
e_{12} = 5 - 5 = 0
$$

$$
h_{12} = 1 - \frac{0}{100} = 1.0
$$

At this point the terminal condition is reached:

$$
e_{12} = 0 \Rightarrow \text{termination}
$$

---

#### 7. Tabular Summary

| Step $t$ | Action Type   | Energy $e_t$ | Hunger $h_t$ |
| -------- | ------------- | -----------: | -----------: |
| 0        | Initial state |           60 |         0.40 |
| 1        | Move          |           55 |         0.45 |
| 2        | Move          |           50 |         0.50 |
| 3        | Move          |           45 |         0.55 |
| 4        | Move          |           40 |         0.60 |
| 5        | Move          |           35 |         0.65 |
| 6        | Move          |           30 |         0.70 |
| 7        | Move          |           25 |         0.75 |
| 8        | Move          |           20 |         0.80 |
| 9        | Move          |           15 |         0.85 |
| 10       | Move          |           10 |         0.90 |
| 11       | Move          |            5 |         0.95 |
| 12       | Move          |            0 |         1.00 |

---

#### 8. Interpretation
This example shows that the baseline model produces exactly the expected depletion dynamics under sustained unsuccessful movement:

##### 8.1 Monotonic Energy Decline
Since no resource is consumed, energy decreases by a fixed amount at each step:

$$
e_{t+1} < e_t \qquad \forall t
$$

until the agent reaches zero energy.

---

##### 8.2 Monotonic Hunger Increase
Because hunger is defined as an inverse function of energy:

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

hunger increases steadily as energy declines.

---

##### 8.3 No Hidden Stabilization
The system contains no compensatory mechanism in this scenario:

* no passive recovery
* no metabolic adaptation
* no emergency policy override
* no hidden reward signal

Thus, starvation is inevitable if energy is consumed but never replenished. This is exactly what a correct baseline system should produce. 

---

#### 9. General Result
For any initial energy $e_0 > 0$, fixed movement cost $c_{move} > 0$, and no environmental intake, the depletion law is:

$$
e_n = e_0 - n c_{move}
$$

and termination occurs at the smallest $n$ such that:

$$
e_0 - n c_{move} \leq 0
$$

Therefore:

$$
n_{\text{death}} = \left\lceil \frac{e_0}{c_{move}} \right\rceil
$$

For this scenario:

$$
n_{\text{death}} = \left\lceil \frac{60}{5} \right\rceil = 12
$$

So the agent survives exactly **12 movement steps** before termination.

---

#### 10. Conclusion
This worked example confirms that the baseline model correctly implements:

* energy expenditure through action cost,
* zero gain in the absence of successful consumption,
* increasing hunger under depletion,
* and eventual termination at zero energy.

The result is fully consistent with the formal system definition and supports implementation readiness for the internal energy dynamics.

---

## 5.2 Example Group B: Local Food Interaction

### B1. Immediate Consumption (Worked Example)

#### 1. Objective
This example evaluates whether the baseline system correctly prioritizes the action **CONSUME** when:

* the agent is currently located on a resource-bearing cell,
* the hunger drive is active,
* and no stronger competing signal is present.

The goal is to verify that:

* the local resource signal at the current cell increases the score of **CONSUME**,
* the policy assigns the highest probability to **CONSUME**,
* successful consumption increases internal energy,
* and the resulting hunger level decreases accordingly.

---

#### 2. Model Equations Used

##### 2.1 Hunger

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

##### 2.2 Drive Activation

$$
d_H(t) = h_t
$$

##### 2.3 Action Scoring
In the baseline system:

$$
\psi(a) = d_H(t)\cdot \phi_H(a,u_t)
$$

Special case for **STAY**:

$$
\psi(\text{STAY}) = -\lambda_{stay}\cdot d_H(t)
$$

##### 2.4 Coupling Function
For **CONSUME**:

$$
\phi_H(\text{CONSUME},u_t)=w_{\text{consume}}\cdot r_c(t)
$$

For movement actions:

$$
\phi_H(\text{UP},u_t)=r_{up}(t)
$$

$$
\phi_H(\text{DOWN},u_t)=r_{down}(t)
$$

$$
\phi_H(\text{LEFT},u_t)=r_{left}(t)
$$

$$
\phi_H(\text{RIGHT},u_t)=r_{right}(t)
$$

##### 2.5 Policy

$$
P(a\mid x_t,u_t)=\frac{\exp(\beta\psi(a))}{\sum_{a'}\exp(\beta\psi(a'))}
$$

##### 2.6 Resource Consumption
If action **CONSUME** is selected:

$$
\Delta R_t^{cons}=\min(\widetilde{R}_{c_t}(t), c_{\max})
$$

##### 2.7 Environmental Energy Transfer

$$
\Delta e_t^{env}=\kappa \cdot \Delta R_t^{cons}
$$

##### 2.8 Energy Update

$$
e_{t+1}=\mathrm{clip}\bigl(e_t-c(a_t)+\Delta e_t^{env},0,E_{\max}\bigr)
$$

All equations above follow directly from the baseline agent, world, and sensor definitions.

---

#### 3. Scenario Definition
We define a local state in which the agent is standing directly on a resource-bearing cell.

##### 3.1 Internal State

$$
E_{\max}=100
$$

$$
e_t=40
$$

Therefore:

$$
h_t = 1-\frac{40}{100}=0.6
$$

and thus:

$$
d_H(t)=0.6
$$

So the agent is meaningfully hungry.

---

##### 3.2 Sensor Input
We assume:

* current cell is traversable and contains visible resource
* all neighboring cells are traversable
* no neighboring resource is present

Thus the observation is:

$$
u_t=(1,0.8, 1,0, 1,0, 1,0, 1,0)
$$

which means:

* current cell: $b_c=1,r_c=0.8$
* up: $b_{up}=1, r_{up}=0$
* down: $b_{down}=1, r_{down}=0$
* left: $b_{left}=1, r_{left}=0$
* right: $b_{right}=1, r_{right}=0$

---

##### 3.3 Policy Parameters

$$
\lambda_{stay}=1
$$

$$
\beta=2
$$

$$
w_{consume} = 6
$$

---

##### 3.4 World and Transition Parameters
We choose a concrete local resource amount and transition parameters.

Let:

$$
\widetilde{R}_{c_t}(t)=8
$$

This is the resource amount available at the current cell after the regeneration phase and before consumption.

Let:

$$
c_{\max}=5
$$

Then consumption is capped at 5 units.

Let:

$$
\kappa = 2
$$

So each consumed resource unit is converted into 2 internal energy units.

Let the action cost for **CONSUME** be:

$$
c(\text{CONSUME})=1
$$

These are valid example parameters because the baseline model explicitly leaves them configurable.

---

#### 4. Drive Evaluation
From the internal energy state:

$$
h_t = 1-\frac{40}{100}=0.6
$$

Therefore:

$$
d_H(t)=0.6
$$

---

#### **5. Action Scoring**

##### 5.1 Current-Cell Resource
From the observation:

$$
r_c=0.8
$$

##### 5.2 Neighbor Average
All neighboring resource values are zero:

$$
r_{up}=r_{down}=r_{left}=r_{right}=0
$$

---

##### 5.3 Score of CONSUME

$$
\psi(\text{CONSUME})=d_H(t)\cdot r_c = 0.6 \cdot 6 \cdot 0.8 = 2.88
$$

---

##### 5.4 Scores of Movement Actions
For each movement action:

$$
\psi(\text{UP})=\psi(\text{DOWN})=\psi(\text{LEFT})=\psi(\text{RIGHT})
$$

$$
= d_H(t)\cdot r_{neighbors}=0.6\cdot 0 = 0
$$

---

##### 5.5 Score of STAY

$$
\psi(\text{STAY})=-\lambda_{stay}\cdot d_H(t) = -1\cdot 0.6 = -0.6
$$

---

#### 6. Resulting Scores

$$
\psi(\text{CONSUME})=2.88
$$

$$
\psi(\text{UP})=\psi(\text{DOWN})=\psi(\text{LEFT})=\psi(\text{RIGHT})=0
$$

$$
\psi(\text{STAY})=-0.6
$$

So **CONSUME** has the highest score.

---

#### 7. Policy Computation
Using $\beta=2$:

##### 7.1 Exponential Terms
For **CONSUME**:

$$
\exp(2\cdot 2.88)=\exp(5.76)\approx 317.348
$$

For each movement action:

$$
\exp(2\cdot 0)=1
$$

For **STAY**:

$$
\exp(2\cdot -0.6)=\exp(-1.2)\approx 0.301194
$$

---

##### 7.2 Normalization Constant

$$
Z = 317.348 + 4\cdot 1 + 0.301194
$$

$$
Z = 321.649194
$$

---

##### 7.3 Action Probabilities

###### CONSUME

$$
P(\text{CONSUME})=\frac{317.348}{321.649194}\approx 0.9866
$$

###### Each Movement Action

$$
P(\text{UP})=P(\text{DOWN})=P(\text{LEFT})=P(\text{RIGHT})=\frac{1}{321.649194}\approx 0.00311
$$

###### STAY

$$
P(\text{STAY})=\frac{0.301194}{321.649194}\approx 0.000936
$$

---

#### 8. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            2.88 |      0.9866 |
| UP      |            0.00 |     0.00311 |
| DOWN    |            0.00 |     0.00311 |
| LEFT    |            0.00 |     0.00311 |
| RIGHT   |            0.00 |     0.00311 |
| STAY    |           -0.60 |    0.000936 |

---

#### 9. State Transition Under Successful Consumption
We now compute the post-action state **assuming that the sampled action is CONSUME**.

##### 10.1 Consumed Resource Amount

$$
\Delta R_t^{cons}=\min(\widetilde{R}_{c_t}(t),c_{\max})
$$

Substitute the example values:

$$
\Delta R_t^{cons}=\min(8,5)=5
$$

---

##### 10.2 Environmental Energy Gain

$$
\Delta e_t^{env}=\kappa \cdot \Delta R_t^{cons}
$$

$$
\Delta e_t^{env}=2 \cdot 5 = 10
$$

---

##### 10.3 Energy Update

$$
e_{t+1}=\mathrm{clip}(e_t-c(\text{CONSUME})+\Delta e_t^{env},0,E_{\max})
$$

Substitute:

$$
e_{t+1}=\mathrm{clip}(40-1+10,0,100)
$$

$$
e_{t+1}=49
$$

---

##### 10.4 Updated Hunger
If hunger is evaluated from the updated energy:

$$
h_{t+1}=1-\frac{49}{100}=0.51
$$

So the hunger level decreases from:

$$
0.60 \rightarrow 0.51
$$

---

##### 10.5 Updated Local Resource
The resource remaining in the current cell becomes:

$$
R_{c_t}(t+1)=\widetilde{R}_{c_t}(t)-\Delta R_t^{cons}
$$

$$
R_{c_t}(t+1)=8-5=3
$$

So the cell is partially depleted but not exhausted.

---

#### 10. Post-Transition Summary
Assuming **CONSUME** is selected and succeeds:

| Quantity              | Before | After |
| --------------------- | -----: | ----: |
| Energy $e$            |     40 |    49 |
| Hunger $h$            |   0.60 |  0.51 |
| Current-cell resource |      8 |     3 |

This is exactly the kind of local regulatory loop the baseline system is supposed to implement.

---

#### 11. Interpretation of the Policy Result
This is the first important result:

> **CONSUME becomes overwhelmingly dominant under the current parameterization.**

With the introduction of the consumption priority weight and the concrete choice

$$  
w_{\text{consume}} = 6  
$$

the current-cell resource signal is amplified strongly enough that **CONSUME** receives by far the highest action score and therefore dominates the Softmax distribution almost deterministically.

This means that, in the present configuration, the baseline agent exhibits a very strong tendency to consume immediately when resource is directly available at the current cell.

This is mathematically consistent with the baseline model and reflects the intended design change:

- directly accessible resource is behaviorally prioritized
- neighboring movement opportunities remain possible in principle
- but they become negligible under strong local consumption bias

From an engineering perspective, this is an important observation:

- the introduction of $w_{\text{consume}}$ successfully resolves the previous under-prioritization of **CONSUME**
- however, the concrete value $w_{\text{consume}} = 6$ makes consumption almost deterministic in this scenario

If a less extreme behavioral dominance is desired, the same mechanism can be retained while choosing a smaller value of (w_{\text{consume}}).

---

#### 13. Conclusion
This worked example confirms that the revised baseline system behaves consistently in a local food interaction scenario:

- the presence of food on the current cell strongly increases the score of **CONSUME**
- the consumption priority parameter $w_{\text{consume}}$ makes directly available resource behaviorally dominant
- successful consumption increases internal energy
- and hunger decreases accordingly

Thus, the baseline agent is capable of **immediate local feeding behavior** in a formally consistent and implementation-ready manner.

At the same time, this example also shows that the precise degree of dominance is now a matter of parameterization:

- high values of $w_{\text{consume}}$ produce near-deterministic feeding
- lower values would preserve stronger stochastic competition with movement actions

This makes $w_{\text{consume}}$ a central behavioral control parameter of the baseline system.

---

### B2. Adjacent Food Detection (Worked Example)

#### 1. Objective
This example evaluates whether the revised baseline system produces **directionally meaningful movement toward visible neighboring resource**, while also resolving competition between:

* **direct consumption of current-cell resource**
* and **movement toward neighboring resource**

Three representative cases are considered:

1. **Only neighboring cells contain resource**
2. **The current cell contains some resource, but less than a neighboring cell**
3. **The current cell contains more resource than the neighbors**

The goal is to test whether the revised coupling behaves plausibly across these local competitive situations.

---

#### 2. Shared Parameter Setting
The following values are used in all three subcases:

$$
E_{\max}=100,\qquad e_t=40,\qquad h_t=0.6,\qquad d_H(t)=0.6
$$

$$
w_{\text{consume}}=5,\qquad \lambda_{stay}=1,\qquad \beta=2
$$

Thus:

$$
\psi(\text{CONSUME}) = 0.6\cdot 5 \cdot r_c = 3r_c
$$

$$
\psi(\text{UP}) = 0.6r_{up},\quad
\psi(\text{DOWN}) = 0.6r_{down},\quad
\psi(\text{LEFT}) = 0.6r_{left},\quad
\psi(\text{RIGHT}) = 0.6r_{right}
$$

$$
\psi(\text{STAY})=-0.6
$$

---

#### B2a. Neighbor-Only Resource Gradient

##### 1. Scenario Definition
We assume the current cell is empty, while neighboring cells contain unequal amounts of resource:

$$
u_t=(1,0.0,;1,0.3,;1,0.1,;1,0.0,;1,0.8)
$$

Interpretation:

* current cell: $r_c=0.0$
* up: $r_{up}=0.3$
* down: $r_{down}=0.1$
* left: $r_{left}=0.0$
* right: $r_{right}=0.8$

So the strongest visible neighboring resource lies to the **RIGHT**.

---

##### 2. Action Scoring

###### CONSUME

$$
\psi(\text{CONSUME})=3r_c=3\cdot 0=0
$$

###### Movement Actions

$$
\psi(\text{UP})=0.6\cdot 0.3=0.18
$$

$$
\psi(\text{DOWN})=0.6\cdot 0.1=0.06
$$

$$
\psi(\text{LEFT})=0.6\cdot 0.0=0
$$

$$
\psi(\text{RIGHT})=0.6\cdot 0.8=0.48
$$

###### STAY

$$
\psi(\text{STAY})=-0.6
$$

---

##### 3. Resulting Scores

$$
\psi(\text{CONSUME})=0
$$

$$
\psi(\text{UP})=0.18,\quad
\psi(\text{DOWN})=0.06,\quad
\psi(\text{LEFT})=0,\quad
\psi(\text{RIGHT})=0.48
$$

$$
\psi(\text{STAY})=-0.6
$$

---

##### 4. Policy Computation
Using $\beta=2$:

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot 0.18)=\exp(0.36)\approx 1.4333
$$

$$
\exp(2\cdot 0.06)=\exp(0.12)\approx 1.1275
$$

$$
\exp(2\cdot 0.48)=\exp(0.96)\approx 2.6117
$$

$$
\exp(2\cdot -0.6)=\exp(-1.2)\approx 0.3012
$$

Normalization:

$$
Z \approx 1 + 1.4333 + 1.1275 + 1 + 2.6117 + 0.3012 = 7.4737
$$

---

##### 5. Action Probabilities

$$
P(\text{CONSUME})\approx 0.1338
$$

$$
P(\text{UP})\approx 0.1918
$$

$$
P(\text{DOWN})\approx 0.1509
$$

$$
P(\text{LEFT})\approx 0.1338
$$

$$
P(\text{RIGHT})\approx 0.3495
$$

$$
P(\text{STAY})\approx 0.0403
$$

---

##### 6. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            0.00 |      0.1338 |
| UP      |            0.18 |      0.1918 |
| DOWN    |            0.06 |      0.1509 |
| LEFT    |            0.00 |      0.1338 |
| RIGHT   |            0.48 |      0.3495 |
| STAY    |           -0.60 |      0.0403 |

---

##### 7. Interpretation
This is the first important success case of the revised baseline:

> The movement direction with the strongest visible neighboring resource, **RIGHT**, now receives the highest probability.

The agent no longer treats all movement directions as equivalent. Instead, the local perceptual gradient is preserved in the action scores, and the policy reacts accordingly.

The behavior remains stochastic, but it is now **directionally biased** in a way that is fully local and non-predictive.

---

#### B2b. Current Cell Has Resource, but Less Than a Neighbor

##### 1. Scenario Definition
We now assume that the current cell contains some resource, but the strongest visible resource still lies to the **RIGHT**:

$$
u_t=(1,0.2, 1,0.3, 1,0.1, 1,0.0, 1,0.8)
$$

Interpretation:

* current cell: $r_c=0.2$
* up: $r_{up}=0.3$
* down: $r_{down}=0.1$
* left: $r_{left}=0.0$
* right: $r_{right}=0.8$

So the neighboring cell to the **RIGHT** has the strongest raw resource signal, but the current cell is non-empty.

---

##### 2. Action Scoring

###### CONSUME

$$
\psi(\text{CONSUME})=3r_c=3\cdot 0.2=0.6
$$

###### Movement Actions

$$
\psi(\text{UP})=0.6\cdot 0.3=0.18
$$

$$
\psi(\text{DOWN})=0.6\cdot 0.1=0.06
$$

$$
\psi(\text{LEFT})=0.6\cdot 0.0=0
$$

$$
\psi(\text{RIGHT})=0.6\cdot 0.8=0.48
$$

###### STAY

$$
\psi(\text{STAY})=-0.6
$$

---

##### 3. Resulting Scores

$$
\psi(\text{CONSUME})=0.6
$$

$$
\psi(\text{UP})=0.18,\quad
\psi(\text{DOWN})=0.06,\quad
\psi(\text{LEFT})=0,\quad
\psi(\text{RIGHT})=0.48
$$

$$
\psi(\text{STAY})=-0.6
$$

---

##### 4. Policy Computation
Using $\beta=2$:

$$
\exp(2\cdot 0.6)=\exp(1.2)\approx 3.3201
$$

$$
\exp(2\cdot 0.18)\approx 1.4333
$$

$$
\exp(2\cdot 0.06)\approx 1.1275
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot 0.48)\approx 2.6117
$$

$$
\exp(2\cdot -0.6)\approx 0.3012
$$

Normalization:

$$
Z \approx 3.3201 + 1.4333 + 1.1275 + 1 + 2.6117 + 0.3012 = 9.7938
$$

---

##### 5. Action Probabilities

$$
P(\text{CONSUME})\approx 0.3390
$$

$$
P(\text{UP})\approx 0.1464
$$

$$
P(\text{DOWN})\approx 0.1151
$$

$$
P(\text{LEFT})\approx 0.1021
$$

$$
P(\text{RIGHT})\approx 0.2667
$$

$$
P(\text{STAY})\approx 0.0308
$$

---

##### 6. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            0.60 |      0.3390 |
| UP      |            0.18 |      0.1464 |
| DOWN    |            0.06 |      0.1151 |
| LEFT    |            0.00 |      0.1021 |
| RIGHT   |            0.48 |      0.2667 |
| STAY    |           -0.60 |      0.0308 |

---

##### 7. Interpretation
This is an especially revealing mixed-competition case.

Even though the neighboring cell to the **RIGHT** has the strongest raw neighboring resource signal, the weighted current-cell consumption signal becomes slightly stronger:

$$
\psi(\text{CONSUME})=0.6 > \psi(\text{RIGHT})=0.48
$$

As a result, **CONSUME** becomes the most probable action.

This means the revised baseline now encodes the intended priority:

> directly accessible resource may outweigh stronger neighboring opportunity, depending on parameterization.

That is exactly the function of $w_{\text{consume}}$. 

---

#### B2c. Current Cell Has More Resource Than the Neighbors

##### 1. Scenario Definition
Finally, we consider a case in which the current cell contains more resource than any neighboring cell:

$$
u_t=(1,0.6, 1,0.3, 1,0.1, 1,0.0, 1,0.4)
$$

Interpretation:

* current cell: $r_c=0.6$
* up: $r_{up}=0.3$
* down: $r_{down}=0.1$
* left: $r_{left}=0.0$
* right: $r_{right}=0.4$

So the current cell is clearly the richest locally available option.

---

##### 2. Action Scoring

###### CONSUME

$$
\psi(\text{CONSUME})=3r_c=3\cdot 0.6=1.8
$$

###### Movement Actions

$$
\psi(\text{UP})=0.6\cdot 0.3=0.18
$$

$$
\psi(\text{DOWN})=0.6\cdot 0.1=0.06
$$

$$
\psi(\text{LEFT})=0.6\cdot 0.0=0
$$

$$
\psi(\text{RIGHT})=0.6\cdot 0.4=0.24
$$

###### STAY

$$
\psi(\text{STAY})=-0.6
$$

---

##### 3. Resulting Scores

$$
\psi(\text{CONSUME})=1.8
$$

$$
\psi(\text{UP})=0.18,\quad
\psi(\text{DOWN})=0.06,\quad
\psi(\text{LEFT})=0,\quad
\psi(\text{RIGHT})=0.24
$$

$$
\psi(\text{STAY})=-0.6
$$

---

##### 4. Policy Computation
Using $\beta=2$:

$$
\exp(2\cdot 1.8)=\exp(3.6)\approx 36.5982
$$

$$
\exp(2\cdot 0.18)\approx 1.4333
$$

$$
\exp(2\cdot 0.06)\approx 1.1275
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot 0.24)=\exp(0.48)\approx 1.6161
$$

$$
\exp(2\cdot -0.6)\approx 0.3012
$$

Normalization:

$$
Z \approx 36.5982 + 1.4333 + 1.1275 + 1 + 1.6161 + 0.3012 = 42.0763
$$

---

##### 5. Action Probabilities

$$
P(\text{CONSUME})\approx 0.8698
$$

$$
P(\text{UP})\approx 0.0341
$$

$$
P(\text{DOWN})\approx 0.0268
$$

$$
P(\text{LEFT})\approx 0.0238
$$

$$
P(\text{RIGHT})\approx 0.0384
$$

$$
P(\text{STAY})\approx 0.0072
$$

---

##### 6. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            1.80 |      0.8698 |
| UP      |            0.18 |      0.0341 |
| DOWN    |            0.06 |      0.0268 |
| LEFT    |            0.00 |      0.0238 |
| RIGHT   |            0.24 |      0.0384 |
| STAY    |           -0.60 |      0.0072 |

---

##### 7. Interpretation
This is the strongest local-feeding case.

Because the current cell has the largest local resource value and the current-cell signal is additionally amplified by $w_{\text{consume}}=5$, the action **CONSUME** becomes strongly dominant.

This is exactly the intended baseline behavior:

* consume immediately when local resource is clearly available and attractive
* move directionally when resource is visible nearby but not yet directly accessible
* preserve stochasticity without losing local plausibility

---

#### 8. Comparative Interpretation Across the Three Cases
Taken together, the three B2 subcases show that the revised baseline now supports a much more plausible local decision structure:

###### Case B2a
Only neighbors contain resource
→ the agent is biased toward the strongest visible direction (**RIGHT**)

###### Case B2b
Current cell contains some resource, but less than the strongest neighbor
→ due to $w_{\text{consume}}=5$, **CONSUME** slightly outranks movement to the strongest neighbor

###### Case B2c
Current cell contains more resource than the neighbors
→ **CONSUME** becomes strongly dominant

This means the revised baseline no longer suffers from the original symmetry problem. It now supports both:

* **directional approach behavior**
* and **prioritized local exploitation**

through a single consistent mechanistic scoring scheme.

---

#### 9. Conclusion
These worked examples confirm that the revised baseline system is now capable of meaningful **adjacent food detection and response**.

More precisely, the model now supports:

* movement toward the strongest visible neighboring resource
* immediate prioritization of directly available resource
* parameter-controlled competition between local consumption and neighboring movement

Thus, the combination of:

* **direction-specific movement coupling**
* and **weighted current-cell consumption**

appears sufficient to produce a plausible baseline form of primitive foraging behavior without introducing:

* a world model
* planning
* memory-based inference
* or semantic concepts.

---

## 5.3 Example Group C: Competitive Action Scoring

### C1. Movement vs Consumption Tradeoff (Worked Example)

#### **1. Objective**
This example evaluates whether the revised baseline system correctly prioritizes **movement toward visible neighboring resource** over **premature consumption attempts** when:

* the current cell contains **no resource**
* one or more neighboring cells contain visible resource
* the hunger drive is active

The goal is to verify that:

* `CONSUME` does **not** receive artificial priority when the current cell is empty
* movement actions compete according to their **direction-specific local resource signals**
* the strongest neighboring resource direction becomes the most probable action

This example therefore isolates the tradeoff between:

* **invalid local consumption**
* and **resource-directed movement**.

---

#### 2. Model Equations Used

##### 2.1 Hunger

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

##### 2.2 Drive Activation

$$
d_H(t)=h_t
$$

##### 2.3 Action Scoring

$$
\psi(a)=d_H(t)\cdot \phi_H(a,u_t)
$$

Special case for **STAY**:
$$
\psi(\text{STAY})=-\lambda_{stay}\cdot d_H(t)
$$

##### 2.4 Coupling Function

For **CONSUME**:
$$
\phi_H(\text{CONSUME},u_t)=w_{\text{consume}}\cdot r_c(t)
$$

For **movement** actions:
$$
\phi_H(\text{UP},u_t)=r_{up}(t)
$$
$$
\phi_H(\text{DOWN},u_t)=r_{down}(t)
$$
$$
\phi_H(\text{LEFT},u_t)=r_{left}(t)
$$
$$
\phi_H(\text{RIGHT},u_t)=r_{right}(t)
$$

##### 2.5 Policy

$$
P(a\mid x_t,u_t)=\frac{\exp(\beta\psi(a))}{\sum_{a'}\exp(\beta\psi(a'))}
$$

All equations follow directly from the revised baseline system. 

---

#### 3. Scenario Definition
We define a local state in which the current cell is empty, but multiple neighboring cells contain visible resource with different intensities.

##### 3.1 Internal State

$$
E_{\max}=100
$$
$$
e_t=40
$$

Therefore:

$$
h_t = 1-\frac{40}{100}=0.6
$$

and thus:

$$
d_H(t)=0.6
$$

So the agent is in a moderate hunger state.

---

##### 3.2 Sensor Input
We choose the following local observation:

$$
u_t=(1,0.0, 1,0.4, 1,0.1, 1,0.0, 1,0.7)
$$

Interpretation:

* current cell: $r_c=0.0$
* up: $r_{up}=0.4$
* down: $r_{down}=0.1$
* left: $r_{left}=0.0$
* right: $r_{right}=0.7$

So the strongest visible neighboring resource lies to the **RIGHT**.

---

##### 3.3 Policy Parameters

$$
\lambda_{stay}=1
$$
$$
\beta=2
$$
$$
w_{\text{consume}}=5
$$

---

#### 4. Drive Evaluation

$$
d_H(t)=h_t=0.6
$$

The hunger drive is active but not maximal.

---

#### 5. Action Scoring

##### 5.1 Score of CONSUME
Since the current cell contains no resource:

$$
r_c=0
$$

Therefore:

$$
\phi_H(\text{CONSUME},u_t)=w_{\text{consume}}\cdot r_c = 5\cdot 0 = 0
$$

and thus:

$$
\psi(\text{CONSUME})=d_H(t)\cdot \phi_H(\text{CONSUME},u_t)
=0.6\cdot 0 = 0
$$

So the consume weight has no effect in this case.

---

##### 5.2 Scores of Movement Actions

###### UP

$$
\psi(\text{UP})=0.6\cdot 0.4=0.24
$$

###### DOWN

$$
\psi(\text{DOWN})=0.6\cdot 0.1=0.06
$$

###### LEFT

$$
\psi(\text{LEFT})=0.6\cdot 0.0=0
$$

###### RIGHT

$$
\psi(\text{RIGHT})=0.6\cdot 0.7=0.42
$$

---

##### 5.3 Score of STAY

$$
\psi(\text{STAY})=-\lambda_{stay}\cdot d_H(t)
=-1\cdot 0.6=-0.6
$$

---

#### 6. Resulting Scores

$$
\psi(\text{CONSUME})=0
$$

$$
\psi(\text{UP})=0.24
$$

$$
\psi(\text{DOWN})=0.06
$$

$$
\psi(\text{LEFT})=0
$$

$$
\psi(\text{RIGHT})=0.42
$$

$$
\psi(\text{STAY})=-0.6
$$

Thus, the score ordering is:

$$
\psi(\text{RIGHT}) > \psi(\text{UP}) > \psi(\text{DOWN}) > \psi(\text{CONSUME})=\psi(\text{LEFT}) > \psi(\text{STAY})
$$

---

#### **7. Policy Computation**
Using $\beta=2$:

##### 7.1 Exponential Terms

###### CONSUME

$$
\exp(2\cdot 0)=1
$$

###### UP

$$
\exp(2\cdot 0.24)=\exp(0.48)\approx 1.6161
$$

###### DOWN

$$
\exp(2\cdot 0.06)=\exp(0.12)\approx 1.1275
$$

###### LEFT

$$
\exp(2\cdot 0)=1
$$

###### RIGHT

$$
\exp(2\cdot 0.42)=\exp(0.84)\approx 2.3170
$$

###### STAY

$$
\exp(2\cdot -0.6)=\exp(-1.2)\approx 0.3012
$$

---

##### 7.2 Normalization Constant

$$
Z = 1 + 1.6161 + 1.1275 + 1 + 2.3170 + 0.3012
$$

$$
Z \approx 7.3618
$$

---

##### 7.3 Action Probabilities

###### CONSUME

$$
P(\text{CONSUME})=\frac{1}{7.3618}\approx 0.1358
$$

###### UP

$$
P(\text{UP})=\frac{1.6161}{7.3618}\approx 0.2195
$$

###### DOWN

$$
P(\text{DOWN})=\frac{1.1275}{7.3618}\approx 0.1532
$$

###### LEFT

$$
P(\text{LEFT})=\frac{1}{7.3618}\approx 0.1358
$$

###### RIGHT

$$
P(\text{RIGHT})=\frac{2.3170}{7.3618}\approx 0.3147
$$

###### STAY

$$
P(\text{STAY})=\frac{0.3012}{7.3618}\approx 0.0409
$$

---

#### **8. Policy Output**

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            0.00 |      0.1358 |
| UP      |            0.24 |      0.2195 |
| DOWN    |            0.06 |      0.1532 |
| LEFT    |            0.00 |      0.1358 |
| RIGHT   |            0.42 |      0.3147 |
| STAY    |           -0.60 |      0.0409 |

---

#### 9. Interpretation
This example shows the intended baseline behavior under a genuine movement-versus-consumption tradeoff:

> When the current cell is empty, `CONSUME` receives no special advantage, even though $w_{\text{consume}}>1$.

This is important. The consumption-priority parameter does **not** create a blind bias toward `CONSUME`. It only amplifies actually present current-cell resource.

As a result:

* `CONSUME` remains possible as a stochastic action
* but it is **not competitively favored**
* movement actions are ranked entirely by their local directional resource signals

In this concrete scenario, the strongest visible resource lies to the **RIGHT**, and therefore:

$$
P(\text{RIGHT}) > P(\text{UP}) > P(\text{DOWN})
$$

This confirms that the revised baseline system now supports the intended form of local competitive action scoring:

* no premature consumption dominance
* no loss of directional structure
* no need for planning or world modeling

---

#### 10. Behavioral Insight
This example reveals an important structural property of the revised baseline:

> The `CONSUME` weighting is conditional, not unconditional.

If the current cell contains no resource, then:

$$
\psi(\text{CONSUME}) = 0
$$

regardless of how large $w_{\text{consume}}$ is.

Therefore, $w_{\text{consume}}$ only affects situations where direct consumption is physically meaningful.

This preserves the mechanistic plausibility of the model and prevents the consume bias from becoming an unrealistic hardcoded reflex.

---

#### 11. Conclusion
This worked example confirms that the revised baseline system handles the **movement vs. consumption tradeoff** consistently when resource is visible only in neighboring cells:

* `CONSUME` is not artificially preferred when the current cell is empty
* movement actions compete according to their direction-specific local signals
* the strongest neighboring resource direction becomes the most probable action
* the consumption-priority parameter $w_{\text{consume}}$ remains inactive unless direct local resource is actually present

Thus, the baseline agent now exhibits a plausible form of **conditional local exploitation versus directional approach**, fully within the constraints of a reactive, non-model-based system.

---

### C2. High vs Low Hunger Regimes (Worked Example)

#### 1. Objective
This example evaluates how the policy changes when the **local environment is held constant**, but the agent’s **internal hunger level** varies strongly.

The goal is to verify that:

* low hunger produces weak action differentiation
* high hunger sharpens competition between actions
* the same local resource structure leads to different action distributions depending on internal state

This example therefore isolates the effect of **internal deficit intensity** on action selection. 

---

#### 2. Shared Environment and Policy Setting
To make the comparison meaningful, both subcases use the **same local observation** and the same policy parameters.

##### 2.1 Sensor Input

We use a mixed local scenario in which:

* the current cell contains some resource
* the strongest neighboring resource lies to the **RIGHT**
* another neighbor also contains weaker resource

$$
u_t=(1,0.2, 1,0.3, 1,0.1, 1,0.0, 1,0.8)
$$

Interpretation:

* current cell: $r_c=0.2$
* up: $r_{up}=0.3$
* down: $r_{down}=0.1$
* left: $r_{left}=0.0$
* right: $r_{right}=0.8$

So this is a genuine competition case between:

* **CONSUME** at the current cell
* movement toward **RIGHT**

---

##### 2.2 Fixed Parameters

$$
E_{\max}=100
$$

$$
w_{\text{consume}}=5,\qquad \lambda_{stay}=1,\qquad \beta=2
$$

##### 2.3 Action Scoring Equations

$$
\psi(a)=d_H(t)\cdot \phi_H(a,u_t)
$$

with:

$$
\phi_H(\text{CONSUME},u_t)=w_{\text{consume}}\cdot r_c=5\cdot 0.2=1
$$

$$
\phi_H(\text{UP},u_t)=r_{up}=0.3
$$

$$
\phi_H(\text{DOWN},u_t)=r_{down}=0.1
$$

$$
\phi_H(\text{LEFT},u_t)=r_{left}=0
$$

$$
\phi_H(\text{RIGHT},u_t)=r_{right}=0.8
$$

and:

$$
\psi(\text{STAY})=-\lambda_{stay}\cdot d_H(t)
$$

So, in compact form:

$$
\psi(\text{CONSUME}) = d_H(t)\cdot 1
$$

$$
\psi(\text{UP}) = d_H(t)\cdot 0.3
$$

$$
\psi(\text{DOWN}) = d_H(t)\cdot 0.1
$$

$$
\psi(\text{LEFT}) = 0
$$

$$
\psi(\text{RIGHT}) = d_H(t)\cdot 0.8
$$

$$
\psi(\text{STAY}) = -d_H(t)
$$

---

#### C2a. Full Saturation Regime (No Hunger)

##### 1. Internal State
We choose full saturation:

$$
e_t = E_{\max} = 100
$$

Therefore:

$$
h_t = 1-\frac{100}{100}=0
$$

and thus:

$$
d_H(t)=0
$$

---

##### 2. Action Scoring
Because all hunger-modulated terms are multiplied by zero:

###### CONSUME

$$
\psi(\text{CONSUME}) = 0\cdot 1 = 0
$$

###### Movement

$$
\psi(\text{UP}) = 0\cdot 0.3 = 0
$$

$$
\psi(\text{DOWN}) = 0\cdot 0.1 = 0
$$

$$
\psi(\text{LEFT}) = 0
$$

$$
\psi(\text{RIGHT}) = 0\cdot 0.8 = 0
$$

###### STAY

$$
\psi(\text{STAY})=-1\cdot 0 = 0
$$

---

##### 3. Resulting Scores

$$
\psi(\text{CONSUME})=\psi(\text{UP})=\psi(\text{DOWN})=\psi(\text{LEFT})=\psi(\text{RIGHT})=\psi(\text{STAY})=0
$$

---

##### 4. Policy Computation
Using $\beta=2$:

$$
\exp(2\cdot 0)=1
$$

for all six actions.

Normalization:

$$
Z = 6
$$

Therefore:

$$
P(a)=\frac{1}{6}\approx 0.1667
\qquad \forall a\in\mathcal{A}
$$

---

##### 5. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |            0.00 |      0.1667 |
| UP      |            0.00 |      0.1667 |
| DOWN    |            0.00 |      0.1667 |
| LEFT    |            0.00 |      0.1667 |
| RIGHT   |            0.00 |      0.1667 |
| STAY    |            0.00 |      0.1667 |

---

##### 6. Interpretation
This is an important baseline result:

> With zero hunger, the local resource structure has no behavioral effect at all.

Because the entire modulation system is gated by $d_H(t)$, full saturation removes all action differentiation, including:

* resource attraction
* directional bias
* stay suppression

The resulting policy is completely uniform.

That is mathematically consistent with the current baseline formulation, but it is also a meaningful modeling observation:

* hunger is not just one influence among others
* in the current baseline, hunger is the **only active motivational gate**

So if hunger vanishes, the policy loses all structured preference.

---

#### C2b. Near-Terminal Regime (Almost Maximal Hunger)

##### 1. Internal State
We choose a state that is still alive, but very close to terminal depletion:

$$
e_t = 1
$$

with:

$$
E_{\max}=100
$$

Therefore:

$$
h_t = 1-\frac{1}{100}=0.99
$$

and thus:

$$
d_H(t)=0.99
$$

So the agent is still alive, but almost maximally hungry.

---

##### 2. Action Scoring

###### CONSUME

$$
\psi(\text{CONSUME}) = 0.99\cdot 1 = 0.99
$$

###### Movement

$$
\psi(\text{UP}) = 0.99\cdot 0.3 = 0.297
$$

$$
\psi(\text{DOWN}) = 0.99\cdot 0.1 = 0.099
$$

$$
\psi(\text{LEFT}) = 0
$$

$$
\psi(\text{RIGHT}) = 0.99\cdot 0.8 = 0.792
$$

###### STAY

$$
\psi(\text{STAY})=-1\cdot 0.99=-0.99
$$

---

##### 3. Resulting Scores

$$
\psi(\text{CONSUME})=0.99
$$

$$
\psi(\text{UP})=0.297
$$

$$
\psi(\text{DOWN})=0.099
$$

$$
\psi(\text{LEFT})=0
$$

$$
\psi(\text{RIGHT})=0.792
$$

$$
\psi(\text{STAY})=-0.99
$$

Thus, the score ordering is:

$$
\psi(\text{CONSUME}) > \psi(\text{RIGHT}) > \psi(\text{UP}) > \psi(\text{DOWN}) > \psi(\text{LEFT}) > \psi(\text{STAY})
$$

---

##### 4. Policy Computation
Using $\beta=2$:

###### 4.1 Exponential Terms

$$
\exp(2\cdot 0.99)=\exp(1.98)\approx 7.2427
$$

$$
\exp(2\cdot 0.297)=\exp(0.594)\approx 1.8112
$$

$$
\exp(2\cdot 0.099)=\exp(0.198)\approx 1.2190
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot 0.792)=\exp(1.584)\approx 4.8744
$$

$$
\exp(2\cdot -0.99)=\exp(-1.98)\approx 0.1381
$$

---

###### 4.2 Normalization Constant

$$
Z \approx 7.2427 + 1.8112 + 1.2190 + 1 + 4.8744 + 0.1381
$$

$$
Z \approx 16.2854
$$

---

###### 4.3 Action Probabilities

$$
P(\text{CONSUME})\approx 0.4447
$$

$$
P(\text{UP})\approx 0.1112
$$

$$
P(\text{DOWN})\approx 0.0748
$$

$$
P(\text{LEFT})\approx 0.0614
$$

$$
P(\text{RIGHT})\approx 0.2993
$$

$$
P(\text{STAY})\approx 0.0085
$$

---

##### 5. Policy Output

| Action  | Score $\psi(a)$ | Probability |
| ------- | --------------: | ----------: |
| CONSUME |           0.990 |      0.4447 |
| UP      |           0.297 |      0.1112 |
| DOWN    |           0.099 |      0.0748 |
| LEFT    |           0.000 |      0.0614 |
| RIGHT   |           0.792 |      0.2993 |
| STAY    |          -0.990 |      0.0085 |

---

##### 6. Interpretation
This regime shows the opposite extreme:

> When hunger is near maximal, the same local resource structure becomes behaviorally decisive.

The action ranking is unchanged relative to the observation structure, but the score differences are now strongly amplified.

As a result:

* `CONSUME` becomes the most probable action
* movement toward the strongest neighboring resource (`RIGHT`) becomes the second strongest option
* `STAY` is almost fully suppressed

This means that high hunger does not create new structure, but it makes the existing local structure matter much more strongly.

---

#### 7. Comparative Interpretation
Taken together, the two subcases reveal the exact role of hunger in the current baseline system:

###### Full saturation

$$
d_H(t)=0
$$
→ all action scores collapse to zero
→ policy becomes completely uniform

###### Near-terminal hunger

$$
d_H(t)\approx 1
$$
→ local action differences are strongly expressed
→ policy becomes sharply structured

So the hunger variable acts as a **global intensity control** on local action competition.

This is elegant and consistent, but it also implies an important limitation:

> In the current baseline, a fully satiated agent has no reason to prefer even obviously resource-relevant actions.

That is not an inconsistency. It is simply the consequence of a model in which hunger is the sole active drive.

---

#### 8. Conclusion
This worked example confirms that the baseline system responds strongly to different hunger regimes while keeping the local environment fixed:

* at full saturation, the policy becomes completely uniform
* near the terminal condition, local resource-based preferences become strongly expressed
* the same observation can therefore produce radically different action distributions depending on internal energy state

Thus, the current baseline implements hunger as a **global behavioral activation factor**:

* low hunger flattens action competition
* high hunger sharpens it
* and stay suppression grows naturally with increasing deficit

This is fully consistent with the mechanistic architecture of System A and provides a clear, implementation-ready interpretation of how internal deficit modulates action selection.

---

## 5.4 Example Group D: Edge Cases

### D1. No Available Food (Expected Starvation Loop)

#### 1. Objective
This example evaluates whether the baseline system behaves consistently under complete local and global food absence.

The goal is to verify that:

* no action can produce energy gain
* invalid `CONSUME` attempts remain possible but ineffective
* action probabilities remain policy-consistent
* expected internal energy decreases monotonically over time
* the system eventually reaches the terminal condition in expectation

This example also implicitly covers the invalid-consumption case, because `CONSUME` may still be selected although no resource is present.

---

#### 2. Model Equations Used

##### 2.1 No-resource condition

In this scenario:

$$
r_c=r_{up}=r_{down}=r_{left}=r_{right}=0
$$

Therefore:

$$
\phi_H(\text{CONSUME},u_t)=w_{\text{consume}}\cdot r_c = 0
$$

and:

$$
\phi_H(\text{UP},u_t)=\phi_H(\text{DOWN},u_t)=\phi_H(\text{LEFT},u_t)=\phi_H(\text{RIGHT},u_t)=0
$$

So the only non-zero score is:

$$
\psi(\text{STAY})=-\lambda_{stay}\cdot d_H(t)
$$

with:

$$
d_H(t)=h_t=1-\frac{e_t}{E_{\max}}
$$

---

##### 2.2 Softmax policy
Since the five non-STAY actions all have score 0, and STAY has score $-\lambda_{stay}h_t$, the policy becomes:

$$
P(a\neq \text{STAY}\mid e_t)=\frac{1}{5+\exp(-\beta\lambda_{stay}h_t)}
$$

for each of:

* `UP`
* `DOWN`
* `LEFT`
* `RIGHT`
* `CONSUME`

and:

$$
P(\text{STAY}\mid e_t)=\frac{\exp(-\beta\lambda_{stay}h_t)}{5+\exp(-\beta\lambda_{stay}h_t)}
$$

---

##### 2.3 Expected energy update
Because no resource exists anywhere:

$$
\Delta R_t^{cons}=0
\qquad\Rightarrow\qquad
\Delta e_t^{env}=0
$$

Thus energy can only decrease through action cost.

Let:

* $c_{move}=5$
* $c_{consume}=1$
* $c_{stay}=0$

These are representative baseline-compatible example values. The key structural property does not depend on the exact numbers, only on the fact that no action can restore energy.

Then the expected cost at time $t$ is:

$$
\mathbb{E}[c(a_t)\mid e_t]
=

4P_{ns}(e_t)\cdot c_{move}
+
P_{ns}(e_t)\cdot c_{consume}
+
P_{stay}(e_t)\cdot c_{stay}
$$

where:

$$
P_{ns}(e_t)=\frac{1}{5+\exp(-\beta\lambda_{stay}h_t)}
$$

Since $c_{stay}=0$, this simplifies to:

$$
\mathbb{E}[c(a_t)\mid e_t]
=

P_{ns}(e_t)\cdot(4c_{move}+c_{consume})
$$

Substituting the chosen costs:

$$
\mathbb{E}[c(a_t)\mid e_t]
=

\frac{21}{5+\exp(-\beta\lambda_{stay}h_t)}
$$

With $\beta=2$ and $\lambda_{stay}=1$:

$$
\mathbb{E}[c(a_t)\mid e_t]
=

\frac{21}{5+\exp(-2h_t)}
$$

Therefore the expected energy update is:

$$
\mathbb{E}[e_{t+1}\mid e_t]
= e_t - \frac{21}{5+\exp(-2h_t)}
$$

with:

$$
h_t=1-\frac{e_t}{E_{\max}}
$$

---

#### 3. Scenario Definition

##### 3.1 Internal parameters

$$
E_{\max}=100
$$
$$
e_0=60
$$

##### 3.2 Policy parameters

$$
\beta=2
$$
$$
\lambda_{stay}=1
$$$$
w_{\text{consume}}=5
$$

Note:

$$
w_{\text{consume}}
$$

has no effect here, because $r_c=0$.

##### 3.3 Action costs

$$
c_{move}=5,\qquad c_{consume}=1,\qquad c_{stay}=0
$$

##### 3.4 Environmental condition
No food is present anywhere in the environment.

Thus for all time steps:

$$
\Delta R_t^{cons}=0,\qquad \Delta e_t^{env}=0
$$

---

#### 4. Step-by-Step Expected Loop Calculation
We iterate the expected update:

$$
e_{t+1}^{exp}=e_t^{exp}-\mathbb{E}[c(a_t)\mid e_t^{exp}]
$$

---

##### Step 0
Initial energy:

$$
e_0=60
$$

$$
h_0=1-\frac{60}{100}=0.40
$$

$$
P_{ns}=\frac{1}{5+\exp(-0.8)}\approx 0.18351
$$

$$
P(\text{STAY})\approx 0.08246
$$

Expected action cost:

$$
\mathbb{E}[c(a_0)\mid e_0] = 21\cdot 0.18351 \approx 3.85369
$$

Expected next energy:

$$
e_1^{exp}\approx 60-3.85369=56.14631
$$

---

##### Step 1

$$
e_1^{exp}\approx 56.14631
$$

$$
h_1\approx 0.43854
$$

$$
P_{ns}\approx 0.18464,\qquad P(\text{STAY})\approx 0.07681
$$

$$
\mathbb{E}[c(a_1)\mid e_1]\approx 3.87740
$$

$$
e_2^{exp}\approx 52.26891
$$

---

##### Step 2

$$
e_2^{exp}\approx 52.26891
$$

$$
h_2\approx 0.47731
$$

$$
P_{ns}\approx 0.18570,\qquad P(\text{STAY})\approx 0.07149
$$

$$
\mathbb{E}[c(a_2)\mid e_2]\approx 3.89975
$$

$$
e_3^{exp}\approx 48.36916
$$

---

##### Step 3

$$
e_3^{exp}\approx 48.36916
$$

$$
h_3\approx 0.51631
$$

$$
P_{ns}\approx 0.18670,\qquad P(\text{STAY})\approx 0.06648
$$

$$
\mathbb{E}[c(a_3)\mid e_3]\approx 3.92078
$$

$$
e_4^{exp}\approx 44.44838
$$

---

##### Step 4
The calculation goes on in the same manner. See the following table for the results.

We skip the notation of the next steps here and jump directly to the terminal state with `Step 15`.

---

##### Step 15
Finally:

$$
e_{15}^{exp}\approx 0.25811
$$

$$
h_{15}\approx 0.99742
$$

$$
P_{ns}\approx 0.19470,\qquad P(\text{STAY})\approx 0.02649
$$

$$
\mathbb{E}[c(a_{15})\mid e_{15}]\approx 4.08876
$$

$$
e_{16}^{exp}=\max(0, 0.25811-4.08876)=0
$$

Expected terminal condition is reached.

---

#### **5. Tabular Summary**

| Step $t$ | $e_t^{exp}$ |   $h_t$ | $P_{ns}$ each | $P(\text{STAY})$ | Expected Cost | $e_{t+1}^{exp}$ |
| -------- | ----------: | ------: | ------------: | ---------------: | ------------: | --------------: |
| 0        |     60.0000 |  0.4000 |       0.18351 |          0.08246 |       3.85369 |        56.14631 |
| 1        |    56.14631 | 0.43854 |       0.18464 |          0.07681 |       3.87740 |        52.26891 |
| 2        |    52.26891 | 0.47731 |       0.18570 |          0.07149 |       3.89975 |        48.36916 |
| 3        |    48.36916 | 0.51631 |       0.18670 |          0.06648 |       3.92078 |        44.44838 |
| 4        |    44.44838 | 0.55552 |       0.18764 |          0.06178 |       3.94054 |        40.50784 |
| 5        |    40.50784 | 0.59492 |       0.18853 |          0.05736 |       3.95908 |        36.54876 |
| 6        |    36.54876 | 0.63451 |       0.18935 |          0.05323 |       3.97644 |        32.57232 |
| 7        |    32.57232 | 0.67428 |       0.19013 |          0.04936 |       3.99269 |        28.57964 |
| 8        |    28.57964 | 0.71420 |       0.19085 |          0.04575 |       4.00787 |        24.57177 |
| 9        |    24.57177 | 0.75428 |       0.19153 |          0.04237 |       4.02204 |        20.54972 |
| 10       |    20.54972 | 0.79450 |       0.19216 |          0.03919 |       4.03526 |        16.51447 |
| 11       |    16.51447 | 0.83486 |       0.19276 |          0.03620 |       4.04757 |        12.46690 |
| 12       |    12.46690 | 0.87533 |       0.19331 |          0.03343 |       4.05901 |         8.40789 |
| 13       |     8.40789 | 0.91592 |       0.19384 |          0.03080 |       4.06963 |         4.33826 |
| 14       |     4.33826 | 0.95662 |       0.19429 |          0.02853 |       4.08015 |         0.25811 |
| 15       |     0.25811 | 0.99742 |       0.19470 |          0.02649 |       4.08876 |         0.00000 |

---

#### 6. Interpretation
This example confirms the expected starvation behavior of the baseline system under complete food absence.

##### 6.1 No action can restore energy
Because no resource exists anywhere:

$$
\Delta R_t^{cons}=0
\qquad\Rightarrow\qquad
\Delta e_t^{env}=0
$$

Therefore even sampled `CONSUME` actions are invalid in effect. They remain possible policy outputs, but they never replenish energy. This implicitly covers the invalid-consumption case.

##### 6.2 Hunger gradually suppresses STAY
As energy decreases, hunger rises, and therefore:

$$
\psi(\text{STAY})=-\lambda_{stay}h_t
$$

becomes more negative.

This is reflected in the probability of `STAY`, which drops from about:

$$
0.0825 \rightarrow 0.0265
$$

over the course of the loop.

##### 6.3 Expected energy decreases monotonically
Since no energy can be gained and expected action cost is always positive:

$$
\mathbb{E}[e_{t+1}\mid e_t] < e_t
\qquad \forall t \text{ before termination}
$$

So starvation is unavoidable in expectation.

##### 6.4 The expected cost slightly increases over time
This is a subtle but important result.

As hunger rises, `STAY` becomes less likely, while non-STAY actions become slightly more likely. Since non-STAY actions carry positive cost, the expected energy loss per step increases slightly:

$$
3.85 \rightarrow 4.09
$$

So the system does not merely drift toward death. It becomes progressively less passive while starving.

---

#### 7. Conclusion
This worked example confirms that the baseline system behaves consistently in the edge case of complete food absence:

* no action can generate energy gain
* invalid `CONSUME` attempts remain possible but ineffective
* `STAY` becomes increasingly unlikely as hunger rises
* expected energy decreases monotonically
* the agent reaches the terminal condition in expectation after repeated steps

Thus, the baseline system exhibits a coherent starvation dynamic without requiring:

* planning
* learning
* memory-based adaptation
* or any hidden fallback mechanism.

---

## 5.5 Example Group E: Multi-Step Trajectories

### E1. Short Survival Episode (Worked Example)

#### 1. Objective
This example evaluates a short multi-step survival episode in which the agent:

1. detects resource in a neighboring cell,
2. moves toward it,
3. consumes it successfully,
4. updates its internal energy,
5. then continues toward another visible resource patch and consumes again.

The goal is to verify that the **full execution cycle** behaves consistently across multiple steps, including:

* local observation update,
* hunger recomputation,
* action scoring,
* stochastic policy evaluation,
* world transition,
* energy update,
* and memory update.

This makes E1 a compact hand-worked integration test of the baseline system.

---

#### 2. Scenario Setup

#### 2.1 Fixed Parameters
We use the following baseline-compatible parameters:

$$
E_{\max}=100
$$

$$
e_0=40
$$

$$
w_{\text{consume}}=5,\qquad \lambda_{stay}=1,\qquad \beta=2
$$

$$
c_{move}=5,\qquad c_{consume}=1,\qquad c_{stay}=0
$$

$$
\kappa=2,\qquad c_{\max}=5
$$

$$
R_{\text{scale}}=5
$$

We also assume:

* all relevant cells are traversable,
* no obstacles are present,
* local regeneration is disabled for the episode by setting:
  $$
  \alpha_i=0
  $$
  for the cells involved.

This keeps the arithmetic transparent and isolates the action-transition logic. All of this is consistent with the environment and sensor definitions.

---

#### 2.2 Local World Layout
We consider a short horizontal corridor of three relevant cells:

* $x_0$: starting cell
* $x_1$: first food cell
* $x_2$: second food cell

Initial resource values:

$$
R(x_0)=0,\qquad R(x_1)=4,\qquad R(x_2)=3
$$

With $R_{\text{scale}}=5$, the corresponding normalized sensor signals are:

$$
r(x_0)=0,\qquad r(x_1)=0.8,\qquad r(x_2)=0.6
$$

The agent starts at $x_0$.

---

#### 2.3 Episode Structure
We compute the following representative episode:

* **Step 0**: move RIGHT from $x_0$ to $x_1$
* **Step 1**: consume at $x_1$
* **Step 2**: move RIGHT from $x_1$ to $x_2$
* **Step 3**: consume at $x_2$

At each step, the chosen action is the **highest-probability sampled action** under the current policy.

---

### 3. Step 0: Detect Neighboring Food and Move Toward It
#### 3.1 Current State

Position:

$$
p_0 = x_0
$$

Energy:

$$
e_0 = 40
$$

Hunger:

$$
h_0 = 1 - \frac{40}{100} = 0.6
$$

Thus:

$$
d_H(0)=0.6
$$

---

#### 3.2 Observation
At $x_0$, the current cell is empty, and the right neighbor contains strong resource:

$$
u_0=(1,0.0, 1,0.0, 1,0.0, 1,0.0, 1,0.8)
$$

Interpretation:

* current cell: $r_c=0.0$
* up: $r_{up}=0.0$
* down: $r_{down}=0.0$
* left: $r_{left}=0.0$
* right: $r_{right}=0.8$

---

#### 3.3 Action Scoring

##### CONSUME

$$
\psi(\text{CONSUME}) = 0.6 \cdot 5 \cdot 0 = 0
$$

##### Movement

$$
\psi(\text{UP})=0
$$
$$
\psi(\text{DOWN})=0
$$
$$
\psi(\text{LEFT})=0
$$
$$
\psi(\text{RIGHT})=0.6\cdot 0.8=0.48
$$

##### STAY

$$
\psi(\text{STAY})=-1\cdot 0.6=-0.6
$$

---

#### 3.4 Policy Computation
With $\beta=2$:

$$
\exp(2\cdot 0)=1
$$
$$
\exp(2\cdot 0.48)=\exp(0.96)\approx 2.6117
$$
$$
\exp(2\cdot -0.6)=\exp(-1.2)\approx 0.3012
$$

Normalization:

$$
Z = 1+1+1+1+2.6117+0.3012 \approx 6.9129
$$

Probabilities:

$$
P(\text{CONSUME})\approx 0.1447
$$
$$
P(\text{UP})\approx 0.1447
$$
$$
P(\text{DOWN})\approx 0.1447
$$
$$
P(\text{LEFT})\approx 0.1447
$$
$$
P(\text{RIGHT})\approx 0.3778
$$
$$
P(\text{STAY})\approx 0.0436
$$

So the most probable action is:

$$
a_0=\text{RIGHT}
$$

---

#### 3.5 State Transition
The movement succeeds, so:

$$
p_1=x_1
$$

Movement costs energy:

$$
e_1 = e_0 - c_{move} = 40 - 5 = 35
$$

No resource is consumed, so:

$$
\Delta R_0^{cons}=0,\qquad \Delta e_0^{env}=0
$$

Memory update:

$$
m_1 = G_{mem}(m_0,u_1)
$$

with the new observation stored after transition.

---

### 4. Step 1: Consume at the First Food Cell

#### 4.1 Updated State
Now the agent is located at $x_1$, which contains resource:

$$
e_1 = 35
$$

$$
h_1 = 1-\frac{35}{100}=0.65
$$

$$
d_H(1)=0.65
$$

---

#### 4.2 Observation
At $x_1$, the current cell contains resource $R=4$, and the right neighbor $x_2$ contains resource $R=3$:

$$
u_1=(1,0.8, 1,0.0, 1,0.0, 1,0.0, 1,0.6)
$$

Interpretation:

* current cell: $r_c=0.8$
* right neighbor: $r_{right}=0.6$
* all other visible cells: $r=0$

---

#### 4.3 Action Scoring

##### CONSUME

$$
\psi(\text{CONSUME}) = 0.65\cdot 5 \cdot 0.8 = 2.6
$$

##### Movement

$$
\psi(\text{UP})=0
$$
$$
\psi(\text{DOWN})=0
$$
$$
\psi(\text{LEFT})=0
$$
$$
\psi(\text{RIGHT})=0.65\cdot 0.6 = 0.39
$$

##### STAY

$$
\psi(\text{STAY})=-0.65
$$

---

#### 4.4 Policy Computation
With $\beta=2$:

$$
\exp(2\cdot 2.6)=\exp(5.2)\approx 181.2722
$$

$$
\exp(2\cdot 0.39)=\exp(0.78)\approx 2.1810
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot -0.65)=\exp(-1.3)\approx 0.2725
$$

Normalization:

$$
Z = 181.2722 + 1 + 1 + 1 + 2.1810 + 0.2725 \approx 186.7257
$$

Probabilities:

$$
P(\text{CONSUME})\approx 0.9708
$$

$$
P(\text{UP})\approx 0.00535
$$

$$
P(\text{DOWN})\approx 0.00535
$$

$$
P(\text{LEFT})\approx 0.00535
$$

$$
P(\text{RIGHT})\approx 0.01168
$$

$$
P(\text{STAY})\approx 0.00146
$$

So the dominant action is:

$$
a_1=\text{CONSUME}
$$

---

#### 4.5 State Transition
Because $R(x_1)=4$ and $c_{\max}=5$:

$$
\Delta R_1^{cons}=\min(4,5)=4
$$

Environmental energy gain:

$$
\Delta e_1^{env}=\kappa \cdot \Delta R_1^{cons}=2\cdot 4=8
$$

Energy update:

$$
e_2 = e_1 - c_{consume} + \Delta e_1^{env}
=35-1+8=42
$$

The current cell is fully depleted:

$$
R(x_1)\leftarrow 4-4=0
$$

Position remains unchanged during `CONSUME`:

$$
p_2=x_1
$$

Memory is updated with the post-consumption observation.

---

### 5. Step 2: Continue Toward the Second Food Cell

#### 5.1 Updated State

$$
e_2=42
$$

$$
h_2 = 1-\frac{42}{100}=0.58
$$

$$
d_H(2)=0.58
$$

---

#### 5.2 Observation
After the first food cell has been depleted, the current cell is empty, but the next food cell is still visible to the right:

$$
u_2=(1,0.0, 1,0.0, 1,0.0, 1,0.0, 1,0.6)
$$

Interpretation:

* current cell: $r_c=0.0$
* right neighbor: $r_{right}=0.6$
* all other visible cells: $r=0$

---

#### 5.3 Action Scoring

##### CONSUME

$$
\psi(\text{CONSUME})=0.58\cdot 5\cdot 0=0
$$

##### Movement

$$
\psi(\text{UP})=0
$$
$$
\psi(\text{DOWN})=0
$$
$$
\psi(\text{LEFT})=0
$$
$$
\psi(\text{RIGHT})=0.58\cdot 0.6=0.348
$$

##### STAY

$$
\psi(\text{STAY})=-0.58
$$

---

#### 5.4 Policy Computation
With $\beta=2$:

$$
\exp(2\cdot 0.348)=\exp(0.696)\approx 2.0057
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot -0.58)=\exp(-1.16)\approx 0.3135
$$

Normalization:

$$
Z = 1+1+1+1+2.0057+0.3135 \approx 6.3192
$$

Probabilities:

$$
P(\text{CONSUME})\approx 0.1582
$$
$$
P(\text{UP})\approx 0.1582
$$
$$
P(\text{DOWN})\approx 0.1582
$$
$$
P(\text{LEFT})\approx 0.1582
$$
$$
P(\text{RIGHT})\approx 0.3174
$$
$$
P(\text{STAY})\approx 0.0496
$$

So the most probable action is again:

$$
a_2=\text{RIGHT}
$$

---

#### 5.5 State Transition
The move succeeds:

$$
p_3=x_2
$$

Energy update:

$$
e_3 = e_2 - c_{move} = 42 - 5 = 37
$$

No resource is consumed during movement:

$$
\Delta R_2^{cons}=0,\qquad \Delta e_2^{env}=0
$$

---

### 6. Step 3: Consume at the Second Food Cell

#### 6.1 Updated State

$$
e_3=37
$$

$$
h_3 = 1-\frac{37}{100}=0.63
$$

$$
d_H(3)=0.63
$$

---

#### 6.2 Observation
At $x_2$, the current cell contains the second resource patch:

$$
u_3=(1,0.6, 1,0.0, 1,0.0, 1,0.0, 1,0.0)
$$

Interpretation:

* current cell: $r_c=0.6$
* all visible neighbors: $r=0$

---

#### 6.3 Action Scoring

##### CONSUME

$$
\psi(\text{CONSUME})=0.63\cdot 5 \cdot 0.6 = 1.89
$$

##### Movement

$$
\psi(\text{UP})=\psi(\text{DOWN})=\psi(\text{LEFT})=\psi(\text{RIGHT})=0
$$

##### STAY

$$
\psi(\text{STAY})=-0.63
$$

---

#### 6.4 Policy Computation

With $\beta=2$:

$$
\exp(2\cdot 1.89)=\exp(3.78)\approx 43.8165
$$

$$
\exp(2\cdot 0)=1
$$

$$
\exp(2\cdot -0.63)=\exp(-1.26)\approx 0.2837
$$

Normalization:

$$
Z = 43.8165 + 1 + 1 + 1 + 1 + 0.2837 \approx 48.1002
$$

Probabilities:

$$
P(\text{CONSUME})\approx 0.9109
$$

$$
P(\text{UP})=P(\text{DOWN})=P(\text{LEFT})=P(\text{RIGHT})\approx 0.02079
$$

$$
P(\text{STAY})\approx 0.00590
$$

So the dominant action is:

$$
a_3=\text{CONSUME}
$$

---

#### 6.5 State Transition
At $x_2$, the remaining raw resource is $R=3$, so:

$$
\Delta R_3^{cons}=\min(3,5)=3
$$

Environmental energy gain:

$$
\Delta e_3^{env}=2\cdot 3=6
$$

Energy update:

$$
e_4 = e_3 - c_{consume} + \Delta e_3^{env}
=37-1+6=42
$$

The second food cell is fully depleted:

$$
R(x_2)\leftarrow 3-3=0
$$

Position remains:

$$
p_4=x_2
$$

---

### 7. Episode Summary

| Step | Position | Observation summary                          | Most probable action | Energy before | Energy after |
| ---- | -------- | -------------------------------------------- | -------------------- | ------------: | -----------: |
| 0    | $x_0$    | food visible to RIGHT                        | RIGHT                |            40 |           35 |
| 1    | $x_1$    | food on current cell, more food to RIGHT     | CONSUME              |            35 |           42 |
| 2    | $x_1$    | current cell depleted, food visible to RIGHT | RIGHT                |            42 |           37 |
| 3    | $x_2$    | food on current cell                         | CONSUME              |            37 |           42 |

---

### 8. Interpretation
This short episode confirms that the revised baseline system supports a coherent reactive survival loop across multiple steps.

#### 8.1 Directional approach works
When food is visible in a neighboring direction but not on the current cell, the corresponding movement action becomes the most probable response.

#### 8.2 Immediate local consumption works
When food is present at the current cell, the weighted `CONSUME` action becomes strongly dominant.

#### 8.3 World and agent updates remain consistent
The episode correctly combines:

* movement without energy gain,
* consumption with resource depletion,
* energy restoration through successful consumption,
* and updated observations after each transition.

#### 8.4 No hidden cognition is required
The full episode looks purposive, but it remains entirely explainable through:

* local observation,
* hunger-driven score modulation,
* stochastic Softmax selection,
* and mechanistic state transition.

There is still:

* no world model,
* no planning,
* no memory-based inference.

---

### 9. Conclusion
This worked example shows that the revised baseline system can sustain a short, plausible survival episode through purely reactive local mechanisms.

Across four steps, the agent:

* moves toward visible neighboring food,
* consumes when food becomes directly available,
* updates its internal energy consistently,
* depletes local resource correctly,
* and continues responding to the changed environment in a coherent way.

Thus, E1 provides a strong hand-worked integration check that the baseline system is ready for simulation-level implementation.


---
## 6. Validation Objectives
The worked examples should answer:

1. **Does the system behave plausibly?**
2. **Are all transitions well-defined?**
3. **Do edge cases break the model?**
4. **Is the system implementation-ready?**

---

## 7. Expected Outcomes
After completing the calculations:

- The model should be **fully executable**
- No undefined variables or transitions remain
- Policy behavior should be **predictable and interpretable**
- The system should be ready for:
    
    - simulation
    - unit testing
    - incremental extension

---

## 8. Critical Notes

- If examples reveal inconsistencies, the baseline model must be revised
- Any ambiguity in action scoring must be resolved explicitly
- Determinism vs stochasticity must be clarified before implementation

---