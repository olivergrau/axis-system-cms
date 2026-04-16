# System C: A Minimal Predictive Drive Agent

## 1. Ziel

System C erweitert System A um einen prädiktiven Mechanismus. Der Agent soll nicht nur auf aktuelle Wahrnehmung und internen Zustand reagieren, sondern zusätzlich auf die Diskrepanz zwischen:

* einer **erwarteten nächsten Wahrnehmung**
* und der **tatsächlich eingetretenen nächsten Wahrnehmung**

Die Erweiterung bleibt bewusst minimal:

* kein Planen
* kein mehrschrittiges Rollout
* kein explizites Weltmodell
* keine globale Repräsentation
* keine counterfactual simulation aller Aktionsfolgen

Stattdessen führt System C ein neues internes Modul ein:

> ein **predictive memory**, das lokale aktions- und beobachtungsabhängige Erwartungswerte für die nächste Beobachtung speichert.

Der zentrale neue Mechanismus ist daher:

$$
\text{Prediction} \rightarrow \text{Prediction Error} \rightarrow \text{drive-specific modulation}
$$

---

## 2. Beziehung zu System A

System C übernimmt aus System A:

* dieselbe Umweltstruktur
* dieselbe lokale Sensorik
* dieselbe Aktionsmenge
* dieselbe Energiedynamik
* dieselbe Grundidee drive-basierter Aktionsmodulation
* dieselbe kausale Ausführungslogik

System A ist ein rein reaktives System ohne Verhaltensnutzung von Memory. Memory ist dort nur passive Aufzeichnung. 

System C erweitert dies um:

* ein eigenes prädiktives Gedächtnis
* eine retrospektive Fehlerberechnung
* drive-spezifische Nutzung des Prediction Error

Der Prediction Error ist **kein eigener Drive**, sondern ein zusätzlicher Input für bestehende oder neue Drives.

---

## 3. Formale Definition

Ich würde System C als 9-Tupel definieren:

$$
A^{(C)} = (\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{Q}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi)
$$

wobei:

* $\mathcal{X}$ der interne Zustandsraum ist
* $\mathcal{U}$ der sensorische Beobachtungsraum ist
* $\mathcal{M}$ der episodische Beobachtungsspeicher ist
* $\mathcal{Q}$ der Raum des **predictive memory** ist
* $\mathcal{A}$ der Aktionsraum ist
* $\mathcal{D}$ der Raum der Drives ist
* $F$ die gemeinsame Zustandsübergangsfunktion ist
* $\Gamma$ die Aktionsmodulation ist
* $\pi$ die Policy ist

Das ist strukturell analog zu A und A+W, nur mit einem neuen Zustandsteil $\mathcal{Q}$. System A hat bereits $(\mathcal{X},\mathcal{U},\mathcal{M},\mathcal{A},\mathcal{D},F,\Gamma,\pi)$, A+W fügt zusätzlich ein World-Model hinzu.

---

## 4. Interner Zustand

Der interne Zustand wird zu:

$$
x_t = (e_t, \xi_t, q_t)
$$

wobei:

* $e_t \in [0,E_{\max}]$: interner Energiezustand
* $\xi_t$: optionale weitere interne Hilfsgrößen
* $q_t \in \mathcal{Q}$: Zustand des prädiktiven Gedächtnisses

Im Unterschied zu A+W gibt es hier noch kein räumliches Weltmodell $w_t$ und keine relative Positionsschätzung $\hat p_t$. A+W führt diese nur für räumliche Neuheit ein.

---

## 5. Beobachtung und bestehendes episodisches Memory

Die Sensorik bleibt unverändert:

$$
u_t = S(s_t^{world})
$$

mit lokalem, instantanem Beobachtungsvektor aus aktueller Zelle und vier Nachbarn. Der Sensor enthält nur Traversability- und Resource-Signale, keine globalen Informationen, keine Position und keine implizite Weltstruktur. 

Das episodische Memory bleibt als FIFO-artiger Beobachtungsspeicher bestehen:

$$
m_{t+1} = M(m_t, u_{t+1})
$$

Seine Rolle bleibt:

* Rohspur vergangener lokaler Beobachtungen
* kein explizites Modell
* keine prädiktive Semantik

Damit gilt eine klare Trennung:

* $m_t$: was wurde wahrgenommen?
* $q_t$: was wird erwartet?

Diese Trennung ist wichtig, weil sonst der observation buffer semantisch überladen würde.

---

## 6. Predictive Memory

Jetzt der neue Kern.

### 6.1 Idee

Das predictive memory speichert erwartete nächste Beobachtungen **konditional auf aktuelle Beobachtung und Aktion**.

Die Grundfunktion lautet:

$$
\hat u_{t+1}^{(a)} = P(q_t, u_t, a)
$$

wobei:

* $u_t$: aktuelle lokale Beobachtung
* $a \in \mathcal{A}$: betrachtete Aktion
* $q_t$: aktueller prädiktiver Speicherzustand
* $\hat u_{t+1}^{(a)}$: erwartete nächste Beobachtung bei Ausführung von (a)

Da du dich für die beobachtungs-konditionierte Variante entschieden hast, ist Prediction also nicht einfach nur aktional, sondern kontextsensitiv.

### 6.2 Semantik

Das predictive memory speichert **nicht** die Welt, sondern Erwartungsstruktur im Beobachtungsraum:

$$
q_t \approx \text{Parameter einer Funktion } (u_t, a_t) \mapsto \hat u_{t+1}
$$

Damit bleibt das System lokal und minimal.

### 6.3 Minimaler Zustandsraum

Formal kann man $\mathcal{Q}$ noch abstrakt lassen. Für das Grundmodell reicht:

$$
q_t \in \mathcal{Q}
$$

mit der Eigenschaft, dass $q_t$ die Funktion $P$ parametrisiert.

Das ist sauberer, als schon jetzt eine konkrete Implementierung wie Lookup-Table, Exponential Average oder Cluster State festzuschreiben.

---

## 7. Retrospektiver Prediction Error

Du hast dich ausdrücklich für retrospektiven Fehler entschieden. Das ist auch die sauberste Wahl.

Nach Ausführung der tatsächlich gewählten Aktion $a_t$ und nach Eintreffen der realen Folgebeobachtung $u_{t+1}$ wird der Fehler definiert als:

$$
\delta_t = \Delta_{pred}(u_{t+1}, \hat u_{t+1}^{(a_t)})
$$

mit

$$
\hat u_{t+1}^{(a_t)} = P(q_t, u_t, a_t)
$$

und einer Fehlerfunktion

$$
\Delta_{pred} : \mathcal{U} \times \mathcal{U} \rightarrow \mathcal{E}
$$

wobei $\mathcal{E}$ der Raum der Fehlersignale ist.

### 7.1 Komponentenweise Form

Da der Sensorvektor aus Blockierungs- und Ressourcensignalen besteht, ist eine komponentenweise Zerlegung sinnvoll:

$$
u_t =
(b_c, r_c, b_{up}, r_{up}, b_{down}, r_{down}, b_{left}, r_{left}, b_{right}, r_{right})
$$



Daher kann man den Fehler schreiben als:

$$
\delta_t = (\delta_t^{b}, \delta_t^{r})
$$

wobei

* $\delta_t^{b}$: Fehler auf Traversability-Komponenten
* $\delta_t^{r}$: Fehler auf Resource-Komponenten

Oder explizit:

$$
\delta_t^{b} = \lVert b_{t+1} - \hat b_{t+1}^{(a_t)} \rVert
$$

$$
\delta_t^{r} = \lVert r_{t+1} - \hat r_{t+1}^{(a_t)} \rVert
$$

mit geeigneter Norm oder komponentenweiser Absolutdifferenz.

### 7.2 Signierte vs. unsignierte Fehler

Für spätere Drive-Nutzung ist eine weitere Zerlegung sinnvoll:

$$
\epsilon_t^{+} = \max(u_{t+1} - \hat u_{t+1}^{(a_t)}, 0)
$$

$$
\epsilon_t^{-} = \max(\hat u_{t+1}^{(a_t)} - u_{t+1}, 0)
$$

Damit kann man unterscheiden zwischen:

* **positive surprise**: etwas tritt stärker auf als erwartet
* **negative surprise / frustration**: etwas bleibt hinter Erwartung zurück

Diese Unterscheidung ist für drive-spezifische Interpretation fast unverzichtbar.

---

## 8. Update des Predictive Memory

Nach Berechnung des Fehlers wird das predictive memory aktualisiert:

$$
q_{t+1} = Q(q_t, u_t, a_t, u_{t+1}, \delta_t)
$$

Das ist bewusst allgemein gehalten.

Wichtig ist nur die kausale Reihenfolge:

1. aktuelle Beobachtung $u_t$
2. Aktion $a_t$
3. Weltübergang
4. neue Beobachtung $u_{t+1}$
5. Prediction Error $\delta_t$
6. Update von $q_t$

Das ist konsistent mit deiner bisherigen Execution-Idee, in der erst die Welt evolviert, dann die neue Beobachtung berechnet und danach interne Speicher aktualisiert werden. 

---

## 9. Drive-System von System C

Jetzt kommt der eigentliche Unterschied.

In System A hängt ein Drive allgemein von internem Zustand, aktueller Beobachtung und Memory ab:

$$
D_i : (x_t, u_t, m_t) \rightarrow \mathbb{R}
$$



In System C erweitern wir dies zu:

$$
D_i : (x_t, u_t, m_t, q_t, \delta_{t-1}) \rightarrow \mathbb{R}
$$

oder kompakter:

$$
d_i(t) = D_i(x_t, u_t, m_t, q_t, \delta_{t-1})
$$

Wichtig ist:

* $q_t$ ist die aktuelle Erwartungsstruktur
* $\delta_{t-1}$ ist der zuletzt realisierte Fehler
* Prediction Error wird **drive-spezifisch interpretiert**
* Prediction Error ist **kein eigener Drive**

Das war genau deine Architekturentscheidung.

---

## 10. Beispiel: Hunger-Drive in System C

In System A ist Hunger rein energiegetrieben:

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

$$
d_H(t) = h_t
$$



In System C kann der Hunger-Drive erweitert werden um einen Frustrationsanteil, der reagiert, wenn erwartete ressourcenbezogene Wahrnehmung ausbleibt.

Definiere dazu einen ressourcenbezogenen negativen Fehler:

$$
\varepsilon_t^{food,-} = g_H(\delta_t^{r,-})
$$

mit $g_H \ge 0$ als Aggregation der relevanten negativen Resource-Fehler.

Dann:

$$
d_H(t) = h_t + \lambda_H \cdot \varepsilon_{t-1}^{food,-}
$$

mit $\lambda_H \ge 0$.

Interpretation:

* niedrige Energie erzeugt Hunger wie bisher
* zusätzlich erhöht enttäuschte Ressourcenerwartung den Hunger-Druck

Damit wird Hunger nicht mehr nur Defizit, sondern auch **frustrierte Erwartung auf Versorgbarkeit**.

---

## 11. Beispiel: Curiosity-Drive in System C

Falls du schon in System C eine Form von Curiosity zulassen willst, aber noch ohne World Model, kann Curiosity aus sensorischer Überraschung gespeist werden.

Definiere:

$$
\varepsilon_t^{surprise} = g_C(\delta_t)
$$

Dann etwa:

$$
d_C(t) = \mu_C + \lambda_C \cdot \varepsilon_{t-1}^{surprise}
$$

oder, falls du eine Sättigung willst:

$$
d_C(t) = \mu_C \cdot (1 - \bar \sigma_t) + \lambda_C \cdot \varepsilon_{t-1}^{surprise}
$$

Das wäre die Brücke zu A+W, wo Curiosity bereits sensorische Neuheit und novelty saturation benutzt. Dort stammt Curiosity aus novelty-Strukturen über Memory und Visit-Map.

Der Unterschied in System C wäre:

* nicht bloß Neuheit im Sinn von Andersartigkeit
* sondern explizit **Erwartungsverletzung**

Das ist konzeptionell stärker.

---

## 12. Aktionsmodulation

Die allgemeine Modulationsform von System A bleibt erhalten:

$$
\psi(a) = \psi_0(a) + \sum_i d_i(t),\phi_i(a, u_t, m_t)
$$

System A formuliert genau diese generische Multi-Drive-Struktur, auch wenn die Baseline nur Hunger instanziiert. 

Für System C würde ich sie erweitern zu:

$$
\psi(a) = \psi_0(a) + \sum_i d_i(t),\phi_i(a, u_t, m_t, q_t)
$$

Die Drive-Aktivierung enthält also bereits prediction-sensitive interne Dynamik, und optional kann auch die drive-spezifische Aktionsmodulation auf Erwartungsstruktur zugreifen.

Wichtig ist aber:

> Die Prediction-Semantik sitzt primär in den Drives, nicht in der Policy.

---

## 13. Policy

Die Policy selbst kann unverändert bleiben, etwa als Softmax über modulierter Aktionswerte:

$$
P(a \mid x_t,u_t,m_t,q_t) =
\frac{\exp(\beta \psi(a))}
{\sum_{a'} \exp(\beta \psi(a'))}
$$

Das ist gut, weil damit die strukturelle Änderung klar dort liegt, wo du sie haben willst:

* intern im Agenten
* in seinen Drives
* in seinem neuen predictive memory

und nicht in einem aufgebohrten Policy-Modul.

System A verwendet genau diese softmax-basierte Struktur über drive-modulierte Scores. 

---

## 14. Gemeinsame Zustandsübergangsfunktion

Die gemeinsame Transition erweitert sich von der A-Struktur

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(x_t, m_t, s_t^{world}, a_t)
$$

zu:

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world})
= F(x_t, m_t, s_t^{world}, a_t)
$$

mit

$$
x_{t+1} = (e_{t+1}, \xi_{t+1}, q_{t+1})
$$

und intern folgender Ordnung:

### 14.1 Welttransition

$$
s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)
$$

### 14.2 neue Beobachtung

$$
u_{t+1} = S(s_{t+1}^{world})
$$

### 14.3 Prediction der tatsächlich gewählten Aktion

$$
\hat u_{t+1}^{(a_t)} = P(q_t, u_t, a_t)
$$

### 14.4 Fehlerberechnung

$$
\delta_t = \Delta_{pred}(u_{t+1}, \hat u_{t+1}^{(a_t)})
$$

### 14.5 Energie- und sonstige Agentenupdates

$$
e_{t+1} = \mathrm{clip}(e_t - c(a_t) + \Delta e_t^{env}, 0, E_{\max})
$$

Das ist unverändert aus A. 

### 14.6 episodisches Memory

$$
m_{t+1} = M(m_t, u_{t+1})
$$

### 14.7 predictive memory

$$
q_{t+1} = Q(q_t, u_t, a_t, u_{t+1}, \delta_t)
$$

Das ist die neue Kernphase.

---

## 15. Execution Cycle von System C

Damit ergibt sich folgender Zyklus:

1. **Perception**
   $$
   u_t = S(s_t^{world})
   $$

2. **Drive evaluation**
   $$
   d_i(t) = D_i(x_t, u_t, m_t, q_t, \delta_{t-1})
   $$

3. **Action modulation**
   $$
   \psi(a) = \psi_0(a) + \sum_i d_i(t)\phi_i(a, u_t, m_t, q_t)
   $$

4. **Action selection**
   $$
   a_t \sim \pi(\psi)
   $$

5. **World transition**
   $$
   s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)
   $$

6. **New observation**
   $$
   u_{t+1} = S(s_{t+1}^{world})
   $$

7. **Retrospective prediction**
   $$
   \hat u_{t+1}^{(a_t)} = P(q_t, u_t, a_t)
   $$

8. **Prediction error**
   $$
   \delta_t = \Delta_{pred}(u_{t+1}, \hat u_{t+1}^{(a_t)})
   $$

9. **Internal updates**

   * Energieupdate
   * episodisches Memory
   * predictive memory

10. **Termination check**

Das bleibt vollständig kausal, lokal und implementierbar.

---

## 16. Was dieses Modell schon kann und was noch nicht

### Es kann jetzt:

* Erwartung und Realität unterscheiden
* frustration-sensitive oder surprise-sensitive Drive-Dynamik erzeugen
* Verhalten durch Prediction Error indirekt strukturieren
* eine erste Form innerer Antizipation einführen

### Es kann noch nicht:

* mehrere Schritte simulieren
* echte Planung betreiben
* ein explizites Weltmodell aufbauen
* counterfactual branch evaluation machen

Das ist gut. Es bleibt ein sauberer nächster Schritt statt eines Sprungs.

---

## 17. Mein Urteil

Ja, das ist jetzt ein kohärentes mathematisches Grundmodell.

Die drei tragenden Entscheidungen sind aus meiner Sicht genau richtig:

* **predictive memory als eigenes Modul**
* **retrospektiver Prediction Error**
* **drive-spezifische Interpretation des Fehlers**

Dadurch bleibt dein System:

* mechanistisch
* modular
* formal erweiterbar
* noch nicht heimlich planend

---

Der nächste sinnvolle Schritt wäre nun, aus diesem Grundmodell eine **präzisierte Minimalinstanz von System C** abzuleiten, also konkret zu entscheiden:

* wie $q_t$ minimal parametrisiert wird,
* wie $\Delta_{pred}$ genau aussieht,
* und wie genau der erste prädiktive Hunger-Drive formuliert wird.

Ich würde dafür mit einer **sehr kleinen Instanz** anfangen: nur Hunger + Prediction Frustration, noch ohne Curiosity.
