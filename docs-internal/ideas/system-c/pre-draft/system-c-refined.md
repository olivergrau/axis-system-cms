# 1. Ziel von System C₀

System C₀ soll prüfen:

> Entsteht neues, plausibles Verhalten, wenn Hunger nicht nur auf Energiezustand reagiert, sondern zusätzlich auf enttäuschte lokale Ressourcenerwartung?

Das ist absichtlich enger als „Prediction allgemein“.

Nicht:

* allgemeine Überraschung
* allgemeines Lernen
* kognitive Simulation

sondern ganz konkret:

* Agent nimmt lokal Ressourcen wahr
* bildet Erwartung über nächste lokale Beobachtung unter einer Aktion
* erlebt Abweichung
* Hunger reagiert auf negative ressourcenbezogene Erwartungsverletzung

---

# 2. Zustandsraum

Wir präzisieren den internen Zustand zu:

$$
x_t = (e_t, q_t, \varepsilon_t)
$$

wobei:

* $e_t \in [0, E_{\max}]$: Energie
* $q_t \in \mathcal{Q}$: predictive memory
* $\varepsilon_t \in \mathbb{R}_{\ge 0}$: letzter aggregierter ressourcenbezogener Vorhersagefehler

Ich lasse $\xi_t$ aus dem allgemeinen Modell jetzt weg, weil es für diese Minimalinstanz nur unnötig abstrakt wäre.

### Interpretation

* $e_t$: homeostatischer Zustand
* $q_t$: Erwartungsstruktur
* $\varepsilon_t$: „frische Frustrationsspur“ aus dem letzten Schritt

Das ist sauberer, als $\delta_{t-1}$ immer lose herumzureichen. Du machst daraus einen expliziten internen Zustandsteil.

---

# 3. Was genau speichert das Predictive Memory?

Jetzt müssen wir konkret werden.

Du hast dich für beobachtungs-konditionierte Erwartung entschieden:

$$
\hat u_{t+1} = P(q_t, u_t, a_t)
$$

Die Frage ist: Wie parametrisieren wir $q_t$ minimal?

## 3.1 Minimal saubere Wahl

Ich würde **nicht** sofort den vollen 10-dimensionalen Beobachtungsvektor vorhersagen.

Warum nicht?

Weil das zu groß und für den Anfang unnötig ist. Der relevante Teil für den ersten predictive hunger drive ist die **Ressourcenstruktur**.

Der Sensor enthält zwar Traversability- und Ressourcensignale für aktuelle Zelle und Nachbarschaft. 
Für C₀ würde ich aber nur die Resource-Komponenten prädiktiv modellieren:

$$
r_t =
(r_c, r_{up}, r_{down}, r_{left}, r_{right})
$$

und die Vorhersage definieren als:

$$
\hat r_{t+1} = P(q_t, r_t, a_t)
$$

Damit bleibt das Modell eng an Hunger gekoppelt.

## 3.2 Form des predictive memory

Die kleinste sinnvolle Form ist aus meiner Sicht:

$$
q_t : (\tilde r, a) \mapsto \hat r'
$$

wobei $\tilde r$ kein kontinuierlicher Vektor im Rohzustand sein sollte, sondern eine **diskretisierte lokale Ressourcenkonfiguration**.

Warum?

Weil du sonst formal sofort in Funktionsapproximation, Regression oder Netzwerke rutschst. Das wäre viel zu früh.

---

# 4. Diskretisierung des Beobachtungskontexts

Damit das predictive memory mathematisch und implementatorisch einfach bleibt, führen wir eine Zustandsabbildung ein:

$$
C : [0,1]^5 \rightarrow \mathcal{S}
$$

mit:

* $r_t \mapsto s_t^{obs}$

wobei $s_t^{obs}$ ein diskreter Beobachtungskontext ist.

## 4.1 Minimalvariante

Jede Resource-Komponente wird grob quantisiert, zum Beispiel in drei Klassen:

$$
Q(r) \in {0,1,2}
$$

mit etwa:

* 0 = niedrig / leer
* 1 = mittel
* 2 = hoch

Dann:

$$
s_t^{obs} = (Q(r_c), Q(r_{up}), Q(r_{down}), Q(r_{left}), Q(r_{right}))
$$

Das ist viel gröber als der echte Sensor, aber für ein erstes Grundmodell sinnvoll.

## 4.2 Warum das vernünftig ist

Damit speichert das predictive memory nicht einen unendlichen Raum von Erwartungswerten, sondern einen endlichen Kontext-Aktions-Raum:

$$
q_t(s,a)
$$

für:

* diskreten Beobachtungskontext $s \in \mathcal{S}$
* Aktion $a \in \mathcal{A}$

---

# 5. Präzise Definition des predictive memory

Nun definieren wir:

$$
q_t(s,a) = \hat r^{(s,a)}_t
$$

wobei:

* $s \in \mathcal{S}$: diskretisierter Beobachtungskontext
* $a \in \mathcal{A}$: Aktion
* $\hat r^{(s,a)}_t \in [0,1]^5$: erwarteter nächster Ressourcenvektor

Die Vorhersagefunktion ist dann einfach:

$$
P(q_t,r_t,a_t) = q_t(C(r_t), a_t)
$$

Das ist sehr sauber:

* Kontext rein
* Aktion rein
* erwarteter nächster Ressourcenvektor raus

---

# 6. Initialisierung des predictive memory

Du brauchst eine explizite Anfangsbedingung.

## 6.1 Neutrale Initialisierung

Für alle Kontexte und Aktionen:

$$
q_0(s,a) = \mathbf{0}
$$

also:

$$
q_0(s,a) = (0,0,0,0,0)
$$

Interpretation:

* anfangs erwartet der Agent nirgends Ressourcen

Das ist konservativ und minimal.

## 6.2 Alternative

Eine andere Möglichkeit wäre eine schwach informative Initialisierung, etwa der aktuelle Kontext selbst oder ein globaler Mittelwert. Aber für das Basismodell würde ich bei Null bleiben, weil das theoretisch sauberer ist.

---

# 7. Prediction Error

Jetzt wird es konkret.

Nach Ausführung der tatsächlich gewählten Aktion $a_t$ gilt:

$$
\hat r_{t+1} = q_t(C(r_t), a_t)
$$

und nach Eintreffen der realen Folgebeobachtung $r_{t+1}$ definieren wir den komponentenweisen Fehler:

$$
\delta_t = r_{t+1} - \hat r_{t+1}
$$

Da wir für Hunger speziell die **negative Ressourcendiskrepanz** brauchen, definieren wir:

$$
\delta_t^{-} = \max(\hat r_{t+1} - r_{t+1}, 0)
$$

komponentenweise.

Das bedeutet:

* nur dort, wo mehr Ressource erwartet wurde als tatsächlich erschien,
* entsteht negativer Fehler.

## 7.1 Aggregierter Frustrationswert

Nun aggregieren wir diesen Fehler zu einem Skalar:

$$
\varepsilon_{t+1} = G(\delta_t^{-})
$$

Die einfachste Wahl ist:

$$
\varepsilon_{t+1} = \sum_{j \in {c,up,down,left,right}} w_j \cdot \delta_{t,j}^{-}
$$

mit Gewichten $w_j \ge 0$.

## 7.2 Minimalste Gewichtung

Für C₀ würde ich zuerst nur den **aktuellen Zellfehler** verwenden:

$$
\varepsilon_{t+1} = \delta_{t,c}^{-}
$$

Das heißt:

> Hunger reagiert nur darauf, ob am aktuellen Ort weniger Ressource anliegt als erwartet.

Warum nur current cell?

Weil Hunger in System A ebenfalls am stärksten an direkt verfügbarer lokaler Ressource hängt, insbesondere über `CONSUME` auf der aktuellen Zelle.

Später kannst du Nachbarzellen hinzufügen.

---

# 8. Update-Regel für das predictive memory

Jetzt brauchen wir eine Lernregel.

Die kleinste saubere Wahl ist ein exponentiell gleitendes Update:

$$
q_{t+1}(s_t^{obs}, a_t)
=

(1-\eta), q_t(s_t^{obs}, a_t)
+
\eta , r_{t+1}
$$

mit Lernrate

$$
\eta \in (0,1]
$$

und für alle anderen ((s,a)):

$$
q_{t+1}(s,a) = q_t(s,a)
\quad \text{für } (s,a) \neq (s_t^{obs}, a_t)
$$

wobei:

$$
s_t^{obs} = C(r_t)
$$

## Interpretation

Das predictive memory speichert für jeden diskreten lokalen Ressourcenkontext und jede Aktion die empirisch geglättete erwartete nächste Ressourcenkonfiguration.

Das ist:

* lokal
* action-conditioned
* observation-conditioned
* ohne Weltmodell
* ohne Planung

---

# 9. Hunger-Drive in System C₀

Jetzt präzisieren wir die neue Hunger-Definition.

## 9.1 Baseline-Hunger bleibt erhalten

Wie in System A:

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$



## 9.2 Prediction-sensitive Hunger

Wir erweitern:

$$
d_H(t) = h_t + \lambda_{pred},\varepsilon_t
$$

mit

$$
\lambda_{pred} \ge 0
$$

Interpretation:

* $h_t$: homeostatisches Defizit
* $\varepsilon_t$: zuletzt erfahrene ressourcenbezogene Erwartungsenttäuschung

Wenn $\lambda_{pred}=0$, reduziert sich System C₀ exakt auf System A bezüglich des Drives. Das ist eine schöne Reduktions-Eigenschaft.

## 9.3 Optional: Begrenzung

Damit (d_H(t)) nicht unbeschränkt wächst, kannst du clippen:

$$
d_H(t) = \mathrm{clip}\left(h_t + \lambda_{pred},\varepsilon_t,,0,,1\right)
$$

oder allgemeiner auf einen zulässigen Bereich.

Für das erste Grundmodell würde ich das sogar empfehlen.

---

# 10. Action Modulation

Die Hunger-Modulation bleibt strukturell gleich wie in System A:

$$
\psi(a) = \psi_0(a) + d_H(t),\phi_H(a,r_t)
$$

mit:

* (\psi_0(a)=0) als neutralem Basisterm
* (\phi_H) wie in System A über aktuelle lokale Resource-Signale

In System A gilt unter anderem:

* Bewegung wird durch Nachbarressourcen moduliert
* `CONSUME` durch current-cell resource
* `STAY` wird hungerabhängig unterdrückt 

Diese Struktur würde ich zunächst **nicht** verändern.

Warum?

Weil du sonst zwei Dinge zugleich änderst:

* Drive-Dynamik
* Aktionskopplung

Für C₀ sollte nur die Drive-Dynamik neu sein.

---

# 11. Policy

Die Policy bleibt unverändert als Softmax:

$$
P(a \mid x_t,r_t,m_t,q_t)
=========================

\frac{\exp(\beta \psi(a))}
{\sum_{a'} \exp(\beta \psi(a'))}
$$

Auch das ist absichtlich konservativ.

---

# 12. Übergangsdynamik von System C₀

Jetzt setzen wir alles in Reihenfolge.

## 12.1 Perception

$$
u_t = S(s_t^{world})
$$

Extrahiere daraus den Ressourcenvektor

$$
r_t = (r_c, r_{up}, r_{down}, r_{left}, r_{right})
$$

## 12.2 Drive evaluation

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

$$
d_H(t) = \mathrm{clip}(h_t + \lambda_{pred}\varepsilon_t, 0, 1)
$$

## 12.3 Action scoring

$$
\psi(a) = d_H(t)\phi_H(a,r_t)
$$

mit optionalem Stay-Suppression-Term wie in A. 

## 12.4 Action selection

$$
a_t \sim \pi(\psi)
$$

## 12.5 World transition

$$
s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)
$$

## 12.6 New observation

$$
u_{t+1} = S(s_{t+1}^{world})
$$

und daraus:

$$
r_{t+1} = (r'*c,r'*{up},r'*{down},r'*{left},r'_{right})
$$

## 12.7 Prediction retrieval

$$
\hat r_{t+1} = q_t(C(r_t), a_t)
$$

## 12.8 Prediction error

$$
\delta_t^{-} = \max(\hat r_{t+1} - r_{t+1}, 0)
$$

$$
\varepsilon_{t+1} = \delta_{t,c}^{-}
$$

Minimalvariante.

## 12.9 Predictive memory update

$$
q_{t+1}(C(r_t), a_t)
====================

(1-\eta)q_t(C(r_t), a_t) + \eta r_{t+1}
$$

sonst unverändert.

## 12.10 Energy update

Wie in System A:

$$
e_{t+1}=\mathrm{clip}(e_t-c(a_t)+\Delta e_t^{env},0,E_{\max})
$$



## 12.11 Episodic memory update

$$
m_{t+1}=M(m_t,u_{t+1})
$$

---

# 13. Was ist hier der neue Mechanismus?

Ganz einfach:

System A:

* Hunger steigt nur über Energieverlust

System C₀:

* Hunger steigt über Energieverlust
* **und** über enttäuschte Ressourcenerwartung

Das heißt, zwei Zustände mit gleicher Energie können in System C₀ verschiedenes Verhalten erzeugen, wenn ihre prädiktive Vorgeschichte verschieden ist.

Das ist bereits ein echter qualitativer Unterschied.

---

# 14. Welche Art Verhalten könnte daraus emergieren?

Noch vorsichtig formuliert, aber plausibel:

## 14.1 Frustrationsverstärkte Aktivierung

Wenn der Agent wiederholt Ressource erwartet und sie ausbleibt, wird der Hunger-Drive schärfer.

## 14.2 Abkehr von ineffektiven lokalen Mustern

Nicht durch Planung, sondern durch Fehlerspur.

## 14.3 Unterschied zwischen „bloß hungrig“ und „hungrig plus enttäuscht“

Das ist konzeptionell neu.

---

# 15. Was dieses Modell bewusst noch nicht tut

Wichtig, damit wir nicht zu viel hineinlesen:

* keine hypothetische Bewertung aller Aktionen über erwartete Zukunft
* keine positive Überraschungsauswertung
* keine Mehrschritt-Vorhersage
* keine regionenbezogene Weltannahme
* keine explizite Lernstrategie außer lokaler Erwartungsanpassung

Es bleibt ein kleines mechanistisches System.

---

# 16. Mein Urteil zu dieser Präzisierung

Ich halte das für eine **sehr gute erste Minimalinstanz**.

Sie hat vier Vorteile:

### 1. Saubere neue Komponente

Predictive Memory ist klar getrennt vom observation buffer.

### 2. Minimaler mathematischer Aufwand

Keine Netze, keine komplizierte Optimierung, keine versteckte Planning Engine.

### 3. Gute Reduktionsfähigkeit

Mit (\lambda_{pred}=0) bist du nahe bei System A.

### 4. Gute Erweiterbarkeit

Später kannst du schrittweise hinzufügen:

* Nachbarfehler statt nur current-cell error
* positive surprise
* curiosity-sensitive prediction
* action scoring mit erwarteter statt nur aktueller Beobachtung
* interne Schleifen

---

# 17. Wo ich noch skeptisch bin

Ein Punkt ist heikel:

> Nur current-cell frustration könnte zu eng sein.

Das ist für das erste Modell okay, aber mittelfristig könnte es zu wenig Struktur liefern, weil Bewegung ja oft durch Nachbarressourcen motiviert wird. System A koppelt Bewegung explizit an Nachbarressourcen. 

Deshalb sehe ich zwei sinnvolle nächste Varianten nach C₀:

* **C₁:** (\varepsilon_t) aggregiert auch Nachbarfehler
* **C₂:** Prediction Error geht nicht nur in den Drive, sondern teilweise in die action modulation

Aber C₀ sollte zuerst isoliert betrachtet werden.

---
