# Sytem C - Prediction

## 1. Zuerst die Grundentscheidung: Was soll „Prediction“ in System C bedeuten?

Es gibt mindestens drei verschiedene Bedeutungen, und die muss man auseinanderhalten.

### Typ 1: Sensorische Erwartung

Der Agent erwartet, was er **als Nächstes wahrnehmen** wird.

Beispiel:

* Wenn ich nach rechts gehe, erwarte ich dort eine gewisse Ressourcensignatur.
* Wenn ich stehen bleibe, erwarte ich weiter eine ähnliche lokale Beobachtung.

Das ist die naheliegendste Form und passt gut zu deinem bisherigen System, weil deine Agenten ohnehin nur lokal wahrnehmen. Der Sensor ist lokal und memoryless, die Welt ist extern, der Agent kennt keine absolute Position.  

### Typ 2: Zustandsbezogene Erwartung

Der Agent erwartet, wie sich **sein eigener interner Zustand** entwickeln wird.

Beispiel:

* Wenn ich `CONSUME` ausführe, erwarte ich Energiewinn.
* Wenn ich laufe, erwarte ich Energieverlust.

Das ist ebenfalls interessant, aber fast noch näher an homeostatischen Drives als an Weltmodellbildung.

### Typ 3: Struktur-Erwartung

Der Agent erwartet **Regelmäßigkeiten der Umwelt**.

Beispiel:

* In dieser Region ist oft Ressource.
* Nach einer Ressourcenphase folgt oft Leere.
* Diese Richtung ist meistens blockiert.

Das ist schon deutlich mächtiger. Hier beginnt ein echtes prädiktives Innenmodell.

Für **System C als ersten Schritt** würde ich sehr klar sagen:

> **Nimm nur Typ 1 als Kern und optional Typ 2 als kleine Erweiterung. Typ 3 noch nicht.**

Warum? Weil Typ 3 dich sofort in Richtung World Model 2.0 zieht. Dann ist System C nicht mehr „Predictive Drive System“, sondern schon fast ein primitives Modell-basiertes Kognitionssystem.

---

## 2. Wo soll Erwartung wohnen?

Hier gibt es vier mögliche Orte. Drei davon sind problematisch.

### Möglichkeit A: Erwartung im Observation Buffer

Das wäre die einfachste Idee: Aus vergangenen Beobachtungen den Erwartungswert ableiten.

Das Problem ist: Der aktuelle Observation Buffer in System A ist im Kern nur ein FIFO von Beobachtungen, also eine passive Spur dessen, was gesehen wurde. In System A ist er behaviorally inactive, in A+W wird er für sensory novelty benutzt.  

Wenn du jetzt einfach sagst „Prediction = Mittelwert aus Buffer“, dann ist das **kein eigentliches Prädiktionsgedächtnis**, sondern nur Statistik über Vergangenes.

Das kann für den ersten Wurf reichen, aber es ist begrifflich unsauber. Denn eine Erwartung ist mehr als Vergangenheitsmittelung. Sie ist idealerweise **konditional**.

### Möglichkeit B: Erwartung im Drive selbst

Dann hätte jeder Drive seine eigene Erwartungslogik.

Beispiel:

* Hunger erwartet energierelevante Beobachtungen
* Curiosity erwartet Neuheitsniveau
* später vielleicht Safety erwartet Gefahrenniveau

Das ist elegant, weil es drive-zentriert ist, und du ja genau dort den Schwerpunkt setzen willst. Aber es hat ein Risiko:

> Du duplizierst Vorhersagelogik in jedem Drive.

Dann wird das System schwer wartbar und theoretisch unklar.

### Möglichkeit C: Erwartung in einem eigenen Memory-Modul

Das halte ich für den saubersten Weg.

Dann hättest du neben:

* episodic observation memory
* visit map / world model

ein drittes Gedächtnis bzw. eine dritte interne Struktur:

> **predictive memory** oder **expectation memory**

Dieses Modul speichert nicht rohe Beobachtungen, sondern **verdichtete Erwartungsparameter**.

Das ist sauber, weil dann klar ist:

* Observation Buffer = „Was habe ich gesehen?“
* Visit Map = „Wo war ich?“
* Predictive Memory = „Was erwarte ich unter bestimmten Bedingungen?“

### Möglichkeit D: Erwartung auf Policy-Ebene

Davon würde ich abraten.

Dann würde die Policy nicht mehr nur scores über bestehende drive outputs in Wahrscheinlichkeiten überführen, sondern selbst antizipative Semantik enthalten. Das wäre ein Bruch mit deiner bisherigen klaren Arbeitsteilung. In A und A+W ist die Policy bewusst relativ neutral gehalten, die Struktur kommt aus Drives und Modulation. 

**Mein Vorschlag:**

> Erwartung sollte **nicht** primär im Observation Buffer und **nicht** primär in der Policy wohnen.
> Sie sollte als **eigene interne Struktur** eingeführt werden, die von den Drives genutzt wird.

---

## 3. Braucht System C ein neues Memory?

Ich würde sagen: **Ja, aber klein und streng begrenzt.**

Nicht deshalb, weil es technisch nötig ist, sondern weil es konzeptionell sauberer ist.

### Warum der bestehende Observation Buffer nicht ganz reicht

Der Observation Buffer beantwortet diese Frage:

> Was habe ich zuletzt gesehen?

Für Prediction brauchst du eher:

> Was erwarte ich **unter einer Bedingung**?

Das ist ein Unterschied.

Denn eine brauchbare Erwartung ist nicht einfach der globale Mittelwert aller Beobachtungen, sondern typischerweise abhängig von etwas wie:

* aktueller Observation
* letzter Aktion
* vielleicht aktuellem internen Zustand

Also eher:

$$
\hat{u}*{t+1} = E[u*{t+1} \mid u_t, a_t, x_t]
$$

Das ist eine **konditionale Erwartung**.

Ein roher FIFO-Buffer speichert die nötigen Rohdaten, aber nicht die konditionale Struktur. Das spricht für ein separates Modul.

---

## 4. Was wäre die kleinste saubere Form eines Predictive Memory?

Nicht zu groß denken. Sonst landest du sofort bei einem Lernsystem.

Die minimalste sinnvolle Form wäre:

### Predictive Memory als Action-Conditioned Local Expectation Store

Für jede Aktion $a \in \mathcal{A}$ speichert das System eine Erwartung darüber, wie die nächste lokale Beobachtung aussehen könnte.

Formal etwa:

$$
P_t(a) = \hat{u}_{t+1}^{(a)}
$$

oder etwas allgemeiner:

$$
P_t : (\text{context}, a) \mapsto \hat{u}_{t+1}
$$

Wobei „context“ am Anfang extrem klein bleiben sollte.

### Minimalvariante

Nur aktionsbasiert:

$$
P_t(a) = \text{erwartete nächste Beobachtung nach Aktion } a
$$

Das ist simpel, aber grob.

### Bessere Minimalvariante

Aktions- und beobachtungsbasiert:

$$
P_t(u_t, a_t) \rightarrow \hat{u}_{t+1}
$$

Das heißt:

* aus aktuellem lokalen Kontext und beabsichtigter Aktion
* wird eine erwartete nächste Beobachtung erzeugt

Das ist meines Erachtens der sweet spot für System C.

---

## 5. Wann wird Erwartung berechnet?

Hier muss man sehr sauber zwischen drei Dingen unterscheiden:

### 5.1 Erwartung abrufen

Vor der Entscheidung.

Für jede mögliche Aktion (a) erzeugt oder liest das System eine Vorhersage:

$$
\hat{u}_{t+1}^{(a)} = \mathrm{Predict}(u_t, x_t, a, p_t^{pred})
$$

Das ist der hypothetische Teil.

### 5.2 Erwartungsverletzung auswerten

Das kann auf zwei verschiedene Arten passieren.

#### Variante A: Counterfactual scoring

Der Agent bewertet schon vorab, welche Aktion voraussichtlich gute oder schlechte Prediction Error Profile haben wird.

Das wäre stark antizipativ.

#### Variante B: Retrospective error

Nach Ausführung von $a_t$ wird geschaut:

$$
\delta_t = u_{t+1} - \hat{u}_{t+1}^{(a_t)}
$$

und dieser Fehler beeinflusst spätere Drive-Aktivierung oder Gedächtnisupdate.

Das ist viel konservativer und sauberer.

Für einen ersten Schritt würde ich sagen:

> Nutze **Prediction Error zuerst retrospektiv**, nicht counterfactual in voller Breite.

Warum? Weil du sonst sofort in interne Simulation pro Aktion rutschst. Das wolltest du zwar perspektivisch, aber für System C würde ich noch vorsichtig bleiben.

### 5.3 Erwartung updaten

Nach Beobachtung des tatsächlichen Nachfolgezustands.

Also:

1. Wahrnehmung $u_t$
2. Aktion $a_t$
3. Welttransition
4. neue Wahrnehmung $u_{t+1}$
5. Prediction Error berechnen
6. Predictive Memory aktualisieren

Das passt sehr gut zu deiner bisherigen kausalen Struktur. In A wird erst Welt aktualisiert, dann Observation, dann Agent/Memory. 

---

## 6. Gehört Prediction Error in die Drive-Berechnung oder in die Drive-Komposition?

Das ist die eigentliche Architekturfrage. Ich sehe drei Modelle.

### Modell 1: Prediction als eigener Drive

Also etwa:

* Hunger
* Curiosity
* Prediction / Surprise

Dann wäre:

$$
d_P(t) = f(\delta_t)
$$

Das ist sauber und modular. Aber ich halte es für den **falschen ersten Schritt**.

Warum? Weil „prediction error“ nicht einfach eine neue Motivation ist wie Hunger. Er ist eher ein **Signal**, das verschiedene Drives unterschiedlich interpretieren können.

### Modell 2: Prediction Error wirkt drive-spezifisch

Das finde ich viel stärker.

Dann hat jeder Drive:

* seine eigene Erwartung
* seinen eigenen relevanten Fehlerbegriff

Beispiel:

#### Hunger

interessiert sich nur für energierelevante Erwartungsverletzung:

* erwartete Ressource da, aber keine da
* erwarteter Konsumerfolg bleibt aus

#### Curiosity

interessiert sich gerade für Abweichung:

* etwas Unerwartetes passiert
* Novelty steigt

Also:

$$
d_i(t) = D_i(x_t, u_t, m_t, q_t)
$$

wobei $q_t$ das predictive memory oder predictive state ist.

Dann ist prediction **kein eigener Drive**, sondern ein Input in die Drive-Funktionen.

### Modell 3: Prediction Error wirkt nur in der Komposition

Also die Drives bleiben wie sie sind, und erst die Aggregation $\Gamma$ reagiert auf Prediction Error.

Das halte ich für zu spät im System. Dann wäre Prediction ein globaler Modulator, aber nicht Teil der motivationalen Semantik.

**Mein Vorschlag:**

> Prediction gehört primär **in die Drive-Berechnung**, nicht in die finale Komposition.

Und zwar drive-spezifisch.

Das passt auch perfekt zu deinem Wunsch nach drive-zentrierter Weiterentwicklung.

---

## 7. Eine saubere formale Skizze für System C

Ich würde System C nicht als „A+W plus Prediction“ formulieren, sondern als neue Erweiterung von A, eventuell mit optionalem W.

### Zustandsraum

Bisher in A:

$$
x_t = (e_t, \xi_t)
$$

In A+W:

$$
x_t = (e_t, \xi_t, \hat{p}_t, w_t)
$$

Für System C würde ich ergänzen:

$$
x_t^{(C)} = (e_t, \xi_t, q_t)
$$

oder wenn du W behalten willst:

$$
x_t^{(C)} = (e_t, \xi_t, \hat{p}_t, w_t, q_t)
$$

wobei $q_t$ der predictive state ist.

### Predictive state

$$
q_t \in \mathcal{Q}
$$

und enthält z. B. eine Menge von Erwartungsparametern.

Minimal:

$$
q_t = { \hat{u}^{(a)} : a \in \mathcal{A} }
$$

oder konditionaler:

$$
q_t = \text{Parameter einer Funktion } \mathrm{Predict}(u,a) \mapsto \hat{u}'
$$

### Prediction error

Nach Ausführung von $a_t$:

$$
\delta_t = \Delta_{\text{pred}}(u_{t+1}, \hat{u}_{t+1}^{(a_t)})
$$

wobei $\Delta_{\text{pred}}$ eine Distanz oder component-wise error function ist.

Da dein Sensorvektor aus traversability- und resource-Signalen besteht, würde ich den Fehler auch aufspalten:

$$
\delta_t = (\delta_t^{b}, \delta_t^{r})
$$

oder sogar nur ressourcenbezogen anfangen, wenn du minimal bleiben willst.

### Drive-Funktionen

Dann etwa:

$$
d_i(t) = D_i(x_t, u_t, m_t, q_t, \delta_{t-1})
$$

Wichtig ist $\delta_{t-1}$, also der zuletzt erfahrene Fehler, nicht der hypothetische aller Aktionen. Sonst rutschst du wieder zu früh in Simulation.

### Beispiel Hunger

Hunger könnte nicht nur von Energie abhängen, sondern von **frustrierter Erwartung auf Ressourcenzugang**:

$$
d_H(t) = h_t + \lambda_H \cdot \varepsilon_t^{food}
$$

wobei $\varepsilon_t^{food}$ ein aus $\delta$ abgeleiteter Fehlerscore ist, etwa:

* hohe Erwartung an Ressource
* tatsächliche Ressource niedriger als erwartet

### Beispiel Curiosity

Curiosity könnte auf positive Überraschung reagieren:

$$
d_C(t) = \mu_C (1-\bar{\nu}_t) + \lambda_C \cdot \varepsilon_t^{surprise}
$$

Also nicht nur novelty, sondern prediction violation.

Damit würdest du Curiosity sauber vom bloßen Neuheitsmittelwert wegheben.

---

## 8. Welche Rolle spielt der bestehende Observation Buffer dann noch?

Er wird nicht obsolet. Im Gegenteil, er bekommt eine klarere Funktion.

### Observation Buffer

Bleibt:

* episodische Rohspur
* kurzfristiger Verlauf
* Grundlage für novelty und eventuell für das Training oder Update des predictive memory

### Predictive Memory

Neu:

* enthält verdichtete Erwartungen
* nicht rohe Beobachtungen
* konditional auf Kontext oder Aktion

Das ist eine gute Trennung.

Also nicht:

* Buffer ersetzen

sondern:

* Buffer behalten
* Predictive Memory ergänzen

---

## 9. Muss Prediction drive-spezifisch sein?

Hier würde ich fein unterscheiden.

### Die prädiktive Repräsentation selbst

muss **nicht** pro Drive getrennt sein.

Ein gemeinsames predictive memory ist sauberer:

* eine gemeinsame Quelle interner Erwartung

### Die Interpretation des Fehlers

sollte **drive-spezifisch** sein.

Das ist der entscheidende Punkt.

Denn dieselbe Erwartungsverletzung kann für verschiedene Drives etwas anderes bedeuten.

Beispiel:

* Ressource bleibt aus

Für Hunger:

* schlecht, frustrierend

Für Curiosity:

* vielleicht interessant, weil Umwelt unerwartet

Das ist eigentlich genau die Art Konflikt, die du ja erforschen willst.

---

## 10. Mein vorläufiges Architektururteil

Wenn ich das jetzt als sauberes erstes Modell formulieren müsste, würde ich System C so definieren:

### System C in einem Satz

Ein mechanistischer Agent mit lokalem prädiktivem Gedächtnis, dessen Drives nicht nur auf aktuellen Zustand und Erinnerung reagieren, sondern auch auf die Diskrepanz zwischen erwarteter und tatsächlicher Wahrnehmung.

### Die saubere Struktur wäre dann:

1. **Observation Buffer bleibt bestehen**
2. **Predictive Memory kommt neu hinzu**
3. **Prediction wird vor allem retrospektiv ausgewertet**
4. **Prediction Error ist kein eigener Drive, sondern drive-spezifischer Input**
5. **Policy bleibt weitgehend neutral**
6. **Komposition aggregiert weiterhin Drives, nicht rohe prediction errors**

---

## 11. Was ich ausdrücklich vermeiden würde

Drei Dinge.

### Erstens

Nicht sofort pro Aktion vollständige interne Zukunftssimulation mit mehrschrittigem Rollout.

Das ist zu früh.

### Zweitens

Nicht den Prediction-Mechanismus in die Policy schieben.

Dann verlierst du die schöne mechanistische Architektur.

### Drittens

Nicht den Observation Buffer semantisch überfrachten.

Er ist gut als Rohgedächtnis. Lass ihn das bleiben.

---

## 12. Der nächste sinnvolle Schritt

Bevor wir irgendeine Mathematik fixieren, sollten wir als Nächstes genau **eine** Designfrage entscheiden:

> **Soll das predictive memory nur die nächste Beobachtung nach einer Aktion erwarten, oder schon kontextabhängig auf $u_t$ konditioniert sein?**

Das ist die eigentliche Gabelung.

* **Variante 1:** action-only expectation
  sehr einfach, aber grob

* **Variante 2:** observation-conditioned expectation
  deutlich sauberer und interessanter

Ich würde klar zu Variante 2 tendieren.

