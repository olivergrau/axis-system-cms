# **AXIS – Predictive Drive Extension (Working Draft)**

### *Action-Modulated Prediction in Mechanistic Agent Systems*

---

## **1. Objective**

The goal of this document is to introduce a **predictive extension** to the AXIS agent architecture that:

* integrates **expectation and prediction error**
* **does not alter drive activation directly**
* instead modifies **action-specific drive projection**

This preserves the core AXIS principle:

> Drives remain scalar motivational sources, while behavior emerges through structured action projection.

---

## **2. Motivation**

### **2.1 Limitation of System A / A+W**

In current systems:

* drives are scalar (e.g. hunger)
* action selection is based on **current perception only**
* no notion of:

  * expectation
  * reliability
  * disappointment

Thus:

> All decisions are myopic with respect to experience.

---

### **2.2 Naïve Extension (Rejected)**

A first idea would be:

$$
d_H(t) = h_t + \lambda \cdot \varepsilon_t
$$

This modifies only **drive magnitude**.

Problem:

* no action-specific differentiation
* no context sensitivity
* no structural change in behavior

Result:

> Only intensity changes, not strategy.

---

### **2.3 Key Insight**

Prediction error is inherently:

* **action-dependent**
* **context-dependent**

Therefore:

> It must enter the system at the level where actions are evaluated.

---

## **3. Architectural Principle**

We introduce a strict separation:

### **Layer A – Drive Activation**

$$
d_i(t)
$$

Scalar motivational intensity (unchanged).

---

### **Layer B – Action Projection (Modified)**

$$
\phi_i(a)
$$

Mapping from drive to action preferences.

**Prediction enters here.**

---

### **Layer C – Arbitration**

$$
\psi(a) = \sum_i w_i(t), d_i(t), \phi_i(a)
$$

Combination of drives (unchanged).

---

### **Core Principle**

> Prediction modifies **how drives act**, not **how strong they are**.

---

## **4. Predictive System Overview**

We introduce three new components:

---

### **4.1 Predictive Memory**

$$
q_t
$$

Stores expectations:

$$
\hat{u}_{t+1} = P(q_t, u_t, a_t)
$$

Minimal version:

* conditioned on local observation + action
* predicts next local resource configuration

---

### **4.2 Prediction Error**

$$
\delta_t = u_{t+1} - \hat{u}_{t+1}
$$

For hunger-specific interpretation:

$$
\epsilon_t^{food,-} = \max(\hat{r}_{t+1,c} - r_{t+1,c}, 0)
$$

Only negative deviations matter (resource disappointment).

---

### **4.3 Action-Specific Frustration Trace**

$$
f_t(s,a)
$$

Where:

* $s = C(u_t)$: discretized local context
* $a$: action

Update rule:

$$
f_{t+1}(s_t,a_t) =
(1-\eta_f) f_t(s_t,a_t)

* \eta_f \cdot \epsilon_t^{food,-}
$$

---

## **5. Action Modulation with Prediction**

### **5.1 Baseline (System A)**

$$
\psi(a) = d_H(t) \cdot \phi_H(a,u_t)
$$

---

### **5.2 Predictive Extension**

We introduce a **reliability factor**:

$$
\rho_t(s,a) = \exp(-\lambda_f f_t(s,a))
$$

Modified action score:

$$
\psi(a) =
d_H(t) \cdot \phi_H(a,u_t) \cdot \rho_t(s_t,a)
$$

---

### **5.3 Interpretation**

Each term has a clear meaning:

* $d_H(t)$: *how strong is the need?*
* $\phi_H(a,u_t)$: *what does perception suggest?*
* $\rho_t(s,a)$: *how reliable was this action historically?*

---

### **5.4 Resulting Behavior**

The agent now prefers actions that are:

* currently promising
* **and historically reliable in similar contexts**

---

## **6. Biological Analogy (Interpretative Layer)**

This structure aligns with known biological mechanisms:

---

### **6.1 Dopaminergic Prediction Error**

In neuroscience:

$$
\delta = \text{expected reward} - \text{actual reward}
$$

This signal:

* does **not directly encode drives**
* instead modifies **action selection pathways**

---

### **6.2 Basal Ganglia Analogy**

* actions are represented in parallel pathways
* dopaminergic signals modulate:

  * reinforcement (Go)
  * suppression (No-Go)

Functional equivalent:

* increase or decrease probability of specific actions

---

### **6.3 Mapping to AXIS**

| AXIS Component | Biological Analogy                         |
| -------------- | ------------------------------------------ |
| $d_H$          | motivational state (e.g. hypothalamus)     |
| $\phi_H$       | sensory-action mapping (cortex)            |
| $\rho$         | learned action reliability (basal ganglia) |
| $\delta$       | dopaminergic prediction error              |

---

### **Key Alignment**

> Biological systems modulate **action pathways**, not raw motivational signals.

This supports the design choice.

---

## **7. Generalization Beyond Hunger**

The predictive system is **not drive-specific**.

---

### **7.1 Shared Prediction Layer**

$$
q_t,\ \delta_t
$$

are global.

---

### **7.2 Drive-Specific Interpretation**

Each drive defines:

$$
\zeta_i(t) = I_i(\delta_t, u_t, a_t)
$$

Examples:

* Hunger:

  * negative resource surprise → frustration
* Curiosity:

  * absolute surprise → attraction
* Safety:

  * unpredictability → avoidance

---

### **7.3 Drive-Specific Projection**

$$
\phi_i(a) =
\phi_i^{sense}(a,u_t)
+
\phi_i^{pred}(a,q_t,\zeta_i)
$$

---

### **7.4 Combined Policy**

$$
\psi(a)=\sum_i w_i(t), d_i(t), \phi_i(a)
$$

---

## **8. Design Advantages**

### **8.1 Minimal Intrusion**

* no change to drive definitions
* no change to arbitration

---

### **8.2 Structural Clarity**

* prediction handled in one layer
* interpretation delegated to drives

---

### **8.3 Extensibility**

* new drives can define new interpretations
* predictive memory remains shared

---

### **8.4 Experimental Control**

* can disable prediction via:

  * $\lambda_f = 0$
* direct comparison to System A possible

---

## **9. Limitations (Explicit)**

This system:

* does not perform planning
* does not simulate future trajectories
* only uses **retrospective error**
* relies on local context discretization

---

## **10. Outlook**

This predictive extension enables:

* transition from reactive to experience-sensitive agents
* emergence of:

  * local avoidance strategies
  * reliability-aware exploration

Next steps:

1. Extend to:

   * Curiosity (positive prediction error)
   * Safety (variance-based prediction)
2. Evaluate:

   * behavioral divergence vs System A
3. Introduce:

   * multi-step prediction (later systems)

---

# **Summary**

The predictive extension introduces a fundamental shift:

> From *“act based on what is visible”*
> to *“act based on what is visible and has proven reliable”*

Crucially:

> This is achieved without modifying the drives themselves, but by transforming their action-level expression.

---

# Extension for confident actions

---

# 1. Grundproblem: Nur Frustration ist asymmetrisch

Bisher haben wir:

$
\rho_t(s,a)=\exp(-\lambda_f f_t(s,a))
$

Das bedeutet:

* schlechte Erfahrungen → Aktion wird schlechter
* gute Erfahrungen → **kein zusätzlicher Effekt**

Das führt zu einem impliziten Bias:

> Das System lernt nur, was es vermeiden soll, aber nicht aktiv, was es bevorzugen soll.

---

# 2. Was fehlt: Positive Verstärkung

Biologisch ist das klar:

* negative Prediction Error → Abschwächung
* **positive Prediction Error → Verstärkung**

Das ist kein optionales Feature, sondern ein zentrales Prinzip.

---

# 3. Saubere Erweiterung: Zwei Spuren statt einer

Wir führen zwei getrennte Größen ein:

## 3.1 Frustration (negative error)

$$
f_t(s,a)
$$

## 3.2 Reinforcement / Confidence (positive error)

$$
c_t(s,a)
$$

---

# 4. Definition der positiven Komponente

Prediction Error:

$$
\delta_t = r_{t+1} - \hat r_{t+1}
$$

Dann:

$$
\epsilon_t^{+} = \max(r_{t+1,c} - \hat r_{t+1,c}, 0)
$$

Also:

> mehr Ressource als erwartet → positive Überraschung

---

# 5. Update-Regeln

## 5.1 Frustration

$$
f_{t+1}(s_t,a_t) =
(1-\eta_f) f_t(s_t,a_t)

* \eta_f \epsilon_t^{-}
$$

## 5.2 Reinforcement

$$
c_{t+1}(s_t,a_t) =
(1-\eta_c) c_t(s_t,a_t)

* \eta_c \epsilon_t^{+}
$$

---

# 6. Integration in die Action-Modulation

Jetzt gibt es mehrere Möglichkeiten. Die wichtigste Entscheidung ist:

> Additiv vs. Multiplikativ vs. Exponentiell

---

## Variante A: Additiv (intuitiv, aber etwas grob)

$$
\psi(a)=d_H \cdot \phi_H(a,u_t)

* \lambda_c c_t(s,a)

- \lambda_f f_t(s,a)
$$

Problem:

* mischt Skalen
* weniger sauber interpretierbar

---

## Variante B: Multiplikativ (strukturtreu)

$$
\psi(a)=d_H \cdot \phi_H(a,u_t) \cdot (1 + \lambda_c c_t(s,a)) \cdot (1 - \lambda_f f_t(s,a))
$$

Problem:

* kann numerisch instabil werden
* Clipping nötig

---

## Variante C: Exponentielle Form (beste Wahl)

$$
\psi(a)=d_H \cdot \phi_H(a,u_t)
\cdot \exp(\lambda_c c_t(s,a) - \lambda_f f_t(s,a))
$$

---

# 7. Warum die exponentielle Form ideal ist

Diese Form hat mehrere Vorteile:

### 7.1 Symmetrische Behandlung

* positive → Verstärkung
* negative → Dämpfung

### 7.2 Numerisch stabil

* keine negativen Faktoren
* keine Clipping-Probleme

### 7.3 Saubere Interpretation

$$
\rho_t(s,a)=\exp(\lambda_c c_t - \lambda_f f_t)
$$

→ ein **Netto-Vertrauensmaß**

---

# 8. Intuitive Interpretation

Jetzt passiert Folgendes:

## Fall 1: Aktion war oft enttäuschend

$$
f_t \uparrow \Rightarrow \psi(a) \downarrow
$$

## Fall 2: Aktion war oft besser als erwartet

$$
c_t \uparrow \Rightarrow \psi(a) \uparrow
$$

## Fall 3: gemischt

→ beide Effekte konkurrieren

---

# 9. Entscheidender Unterschied zu vorher

Vorher:

> System lernt nur Vermeidung

Jetzt:

> System lernt Präferenz + Vermeidung

Das ist ein qualitativer Sprung.

---

# 10. Verbindung zur Biologie

Das passt jetzt deutlich besser zu:

* Dopamin:

  * positive RPE → Verstärkung (LTP)
  * negative RPE → Abschwächung (LTD)

Also:

> zwei Richtungen der Anpassung, nicht nur eine

---

# 11. Wichtig: Warum zwei Spuren und nicht eine?

Man könnte auch sagen:

$$
g_t(s,a) = c_t(s,a) - f_t(s,a)
$$

und nur eine Variable nutzen.

Warum ich das **nicht** empfehlen würde:

## 11.1 Informationsverlust

Du verlierst:

* ob etwas oft gut war
* oder selten schlecht

beides kann denselben Netto-Wert ergeben.

---

## 11.2 Unterschiedliche Dynamik

In Realität:

* Lernen aus Fehlern ≠ Lernen aus Erfolg
* unterschiedliche Lernraten sinnvoll:

  * $\eta_f \neq \eta_c$

---

## 11.3 Erweiterbarkeit

Später kannst du z. B.:

* Risiko als Varianz modellieren
* Unsicherheit getrennt behandeln

---

# 12. Integration in Multi-Drive Setting

Jetzt wird es elegant.

Für jeden Drive (i):

$$
\psi_i(a)=d_i \cdot \phi_i(a) \cdot \exp(\lambda_c^i c_t(s,a) - \lambda_f^i f_t(s,a))
$$

Dann:

$$
\psi(a)=\sum_i w_i d_i \phi_i(a) \rho_i(s,a)
$$

Wichtig:

* gleiche Spuren $c_t, f_t$
* **aber unterschiedliche Interpretation pro Drive**

---

# 13. Beispiel: Hunger vs Curiosity

## Hunger

* positive Überraschung → gut → verstärken
* negative → schlecht → dämpfen

## Curiosity

* positive Überraschung → interessant → verstärken
* negative Überraschung → **auch interessant!**

→ könnte beide erhöhen

Das zeigt:

> Die Spuren sind gemeinsam, aber ihre Nutzung ist drive-spezifisch

---

# 14. Minimal vs. vollständiges Modell

## Minimal (für erste Implementierung)

* nur $f_t$
* keine Verstärkung

## Sauber / vollständig

* $f_t$ + $c_t$
* exponentielle Integration

---

# 15. Meine klare Empfehlung

Wenn du es ernsthaft untersuchen willst:

> Nimm direkt beide Spuren.

Warum?

* der Mehraufwand ist minimal
* der qualitative Unterschied ist groß
* du vermeidest ein strukturell einseitiges System

---

# 16. Der eigentliche Erkenntnispunkt

Mit beiden Spuren entsteht:

> ein primitives, kontextabhängiges Aktionswertsystem
> **ohne explizite Value Function**

Das ist interessant, weil:

* kein klassisches RL
* aber funktional ähnlich

---

# 17. Kurzformel (Finale Form)

Ich würde das als Kernformel festhalten:

$$
\psi(a)=d_H(t)\cdot \phi_H(a,u_t)\cdot
\exp\big(\lambda_c c_t(s_t,a)-\lambda_f f_t(s_t,a)\big)
$$

Das ist:

* kompakt
* interpretierbar
* biologisch plausibel
* architektonisch sauber

---


