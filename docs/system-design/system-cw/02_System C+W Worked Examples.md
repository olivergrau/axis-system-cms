# System C+W Worked Examples

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Type: Worked Example / Formal Companion Note
- Status: Draft v1.0
- Companion: System C+W Model (01_System C+W Model.md)

---

## 1. Purpose

This document provides step-by-step numerical examples for **System C+W**.

The goals are:

- to illustrate how shared prediction and separate drive traces interact,
- to show how hunger and curiosity can interpret the same predictive context differently,
- to make the non-movement curiosity rule explicit,
- and to give later engineering work a compact numerical reference.

The examples are pedagogical design walkthroughs, not execution traces.

---

## 2. Shared Assumptions

Unless stated otherwise:

| Parameter | Symbol | Value |
|---|---|---|
| Max energy | $E_{\max}$ | 100 |
| Hunger weight | $w_H$ | 0.55 |
| Curiosity weight | $w_C$ | 0.45 |
| Hunger activation | $d_H$ | 0.40 |
| Curiosity activation | $d_C$ | 0.60 |
| Non-move curiosity penalty | $\kappa_{nonmove}^C$ | 0.20 |

For the local resource-value functional use:

$$
V_R(u_t) = 0.7\,r_c + 0.3\,\bar r_n
$$

where $\bar r_n$ is the mean neighbor resource value.

We consider the action set:

$$
\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}
$$

---

## 3. Example A: Shared Prediction, Divergent Drive Interpretation

### 3.1 Setup

Assume the current local observation has:

- current resource: $r_c = 0.2$
- neighbor resources: $(0.8, 0.1, 0.2, 0.4)$ for $(up, down, left, right)$
- directional novelty: $(0.9, 0.1, 0.2, 0.5)$

Then the shared predictive feature vector is:

$$
y_t^{CW} = (0.2, 0.8, 0.1, 0.2, 0.4, 0.9, 0.1, 0.2, 0.5, 0.425)
$$

Suppose the chosen compact context is:

$$
s_t = 37
$$

and the predictive memory for action `UP` expects:

$$
q_t(s_t,\text{UP}) = (0.1, 0.6, 0.1, 0.2, 0.3, 0.7, 0.1, 0.2, 0.4, 0.35)
$$

### 3.2 Hunger-Side Outcome

Current local resource value:

$$
\bar r_n = \frac{0.8 + 0.1 + 0.2 + 0.4}{4} = 0.375
$$

$$
V_R(u_t) = 0.7 \cdot 0.2 + 0.3 \cdot 0.375 = 0.2525
$$

Predicted next resource value from $q_t(s_t,\text{UP})$:

$$
\hat{\bar r}_n = \frac{0.6 + 0.1 + 0.2 + 0.3}{4} = 0.30
$$

$$
\hat V_R = 0.7 \cdot 0.1 + 0.3 \cdot 0.30 = 0.16
$$

So the predicted hunger-side yield is:

$$
\hat Y_t^H(\text{UP}) = 0.16 - 0.2525 = -0.0925
$$

Now suppose the actual next observation after moving up gives:

- current resource = 0.5
- neighbor mean resource = 0.20

Then:

$$
V_R(u_{t+1}) = 0.7 \cdot 0.5 + 0.3 \cdot 0.2 = 0.41
$$

Hence:

$$
Y_t^H(\text{UP}) = 0.41 - 0.2525 = 0.1575
$$

Hunger-side signed errors:

$$
\varepsilon_{H,t}^+ = \max(0.1575 - (-0.0925), 0) = 0.25
$$

$$
\varepsilon_{H,t}^- = 0
$$

### 3.3 Curiosity-Side Outcome

For action `UP`, use the pre-action novelty weight:

$$
\nu_{up}(t) = 0.9
$$

Predicted curiosity yield:

$$
\hat Y_t^C(\text{UP}) = 0.9 \cdot (-0.0925) = -0.08325
$$

Actual curiosity yield:

$$
Y_t^C(\text{UP}) = 0.9 \cdot 0.1575 = 0.14175
$$

Curiosity-side signed errors:

$$
\varepsilon_{C,t}^+ = \max(0.14175 - (-0.08325), 0) = 0.225
$$

$$
\varepsilon_{C,t}^- = 0
$$

### 3.4 Interpretation

The important point is that **the same shared prediction** generated:

- hunger-side positive surprise
- curiosity-side positive surprise

but the curiosity side scaled the same event through the pre-action
novelty weight.

If hunger and curiosity had different historical trace states at
$(s_t,\text{UP})$, they would still produce different modulation for the
next occurrence of the same context.

---

## 4. Example B: Separate Trace States, Separate Modulation

Assume that for context-action pair $(s_t,\text{RIGHT})$ the current
trace values are:

$$
f_t^H = 0.10,\qquad c_t^H = 0.50
$$

$$
f_t^C = 0.45,\qquad c_t^C = 0.05
$$

Use the same modulation function:

$$
\mu = \exp(\lambda_+ c - \lambda_- f)
$$

with drive-specific sensitivities:

- hunger: $\lambda_+^H = 1.0,\ \lambda_-^H = 1.2$
- curiosity: $\lambda_+^C = 0.8,\ \lambda_-^C = 1.5$

### 4.1 Hunger Modulation

$$
\mu_H = \exp(1.0 \cdot 0.50 - 1.2 \cdot 0.10)
= \exp(0.38)
\approx 1.46
$$

### 4.2 Curiosity Modulation

$$
\mu_C = \exp(0.8 \cdot 0.05 - 1.5 \cdot 0.45)
= \exp(-0.635)
\approx 0.53
$$

### 4.3 Interpretation

The same shared context-action memory can therefore be:

- confidence-amplified on the hunger side
- frustration-suppressed on the curiosity side

This is the defining C+W pattern:

- **shared predictive memory**
- **separate drive-specific trust**

---

## 5. Example C: Non-Movement Curiosity Semantics

Consider action `CONSUME` with:

$$
d_C(t) = 0.60,\qquad \kappa_{nonmove}^C = 0.20
$$

Then for v1:

$$
Y_t^C(\text{CONSUME}) = -0.20 \cdot 0.60 = -0.12
$$

$$
\hat Y_t^C(\text{CONSUME}) = -0.20 \cdot 0.60 = -0.12
$$

Thus:

$$
\varepsilon_{C,t}^+ = 0,\qquad \varepsilon_{C,t}^- = 0
$$

### Interpretation

`CONSUME` receives no curiosity-positive evidence in v1.

Its curiosity-side role is only:

- suppressive
- or neutral

This does **not** say consume is globally bad. It only says that the
curiosity channel does not reward non-movement actions with positive
exploration yield.

---

## 6. Example D: Reduction to A+W

Suppose both predictive channels are neutral:

$$
\mu_H(s,a) = 1,\qquad \mu_C(s,a) = 1
$$

for all actions in the current context.

Then:

$$
\tilde \Pi_H(a,t) = d_H(t)\,\phi_H(a,u_t)
$$

$$
\tilde \Pi_C(a,t) = d_C(t)\,\phi_C(a,u_t,m_t,w_t)
$$

and the combined score becomes:

$$
\Psi_{CW}(a,t) =
w_H(t)\,d_H(t)\,\phi_H(a,u_t) +
w_C(t)\,d_C(t)\,\phi_C(a,u_t,m_t,w_t)
$$

which is exactly the A+W scoring structure.

### Interpretation

This is the primary sanity check:

- prediction is behaviorally meaningful only when traces have learned,
- but when predictive influence is neutralized, the system collapses
  back to standard A+W behavior.

---

## 7. Summary

These examples illustrate the main System C+W commitments:

- one shared predictive representation,
- one shared predictive memory,
- separate hunger and curiosity outcome semantics,
- separate hunger and curiosity traces,
- separate modulation parameters,
- and prediction applied before arbitration.

Together, these make C+W a predictive dual-drive system rather than a
simple combination of A+W with a single shared trust signal.
