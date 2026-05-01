# Top-down Systemrichtungen (keine Details, nur Klassen)

# 1. **System C – Predictive Drive System**

## Idee **(Umgesetzt)**

Drives reagieren nicht mehr nur auf *aktuellen Zustand*, sondern auf:

> **Abweichung zwischen Erwartung und Realität**

---

## Was sich ändert

* Memory speichert nicht nur Vergangenheit
* sondern erzeugt **Erwartungswerte**
* Drives arbeiten auf:

  * Prediction Error

---

## Beispiel

* Agent erwartet Nahrung in Richtung X
* findet nichts
  → **Frustration / Exploration-Drive steigt**

---

## Warum das spannend ist

* Erste Form von:

  * Überraschung
  * Enttäuschung
* Verhalten wird:

  * weniger reaktiv
  * mehr “gerichtet”

---

## Skepsis

Wenn du nicht aufpasst:

→ wird das schnell einfach ein “besserer Curiosity Drive”

Der Unterschied muss klar sein:

* Curiosity = Neuheit
* Prediction = Erwartungsverletzung

---

# 2. **System D – Competing Drive Field**

## Idee

Drives sind nicht nur Gewichte, sondern:

> **räumliche Felder über Actions / Weltzustand**

---

## Was sich ändert

Aktuell:

* scalar drive → beeinflusst Policy

Neu:

* jeder Drive erzeugt:

  * ein **Action-Potential-Feld**

→ Policy ist nur noch:

* Aggregator dieser Felder

---

## Beispiel

* Hunger zieht zu Nahrung
* Curiosity zieht zu Unbekanntem
* Avoidance (neu!) drückt weg von Gefahr

→ resultierendes Verhalten = Vektor-Superposition

---

## Warum das spannend ist

* echte Konflikte
* lokale Instabilitäten
* emergente Pfade

---

## Skepsis

Kann schnell werden:

* “nur anderes Softmax”

Der Unterschied muss sein:
→ Drives erzeugen Struktur, nicht nur Gewichtung

---

# 3. **System E – Active Memory System**

## Idee

Memory ist kein Speicher, sondern:

> **ein aktiver Transformator**

---

## Was sich ändert

Memory kann:

* vergessen
* verstärken
* abstrahieren

---

## Beispiel

* häufig gesehene Zustände werden:

  * komprimiert
* seltene:

  * hervorgehoben

→ Drives reagieren auf:

* “wichtige Vergangenheit”, nicht rohe Daten

---

## Warum das spannend ist

Das ist der erste Schritt zu:

* Bedeutung
* Relevanz

---

## Skepsis

Gefahr:
→ du baust unbewusst ein World Model durch die Hintertür

Du musst entscheiden:

* ist Memory noch “Gedächtnis”
* oder schon “Modell”?

---

# 4. **System F – Internal Simulation Loop**

Jetzt wird’s interessant.

## Idee

Der Agent kann intern:

> **mögliche Aktionen durchspielen**

---

## Minimalform

Keine echte Planung.

Nur:

* simuliere 1–2 Schritte
* bewerte Ergebnis über Drives

---

## Wichtig

Das muss sauber bleiben:

* Simulation basiert auf:

  * eigenem Weltmodell (unvollständig!)
* nicht auf echter Welt

---

## Warum das spannend ist

Das ist:

> der erste echte Bruch zur reinen Reaktivität

---

## Skepsis (groß!)

Hier lauert die größte Gefahr:

* du baust sofort ein RL-System
* oder eine klassische Planning Engine

Dann verlierst du:

→ dein mechanistisches Paradigma

Die Simulation muss:

* billig
* fehlerhaft
* lokal

sein

---

# 5. **System G – World-Reactive System**

## Idee

Die Welt reagiert auf Verhalten des Agents:

> ohne dass der Agent direkten Zugriff bekommt

---

## Beispiele

* Ressourcen erschöpfen sich global
* Wege werden “ausgetreten”
* Regionen verändern sich durch Nutzung

---

## Warum das spannend ist

→ Feedback-Loops:

* Verhalten verändert Welt
* Welt verändert Verhalten

---

## Skepsis

Sehr wichtig:

Du darfst NICHT:

* Agent Zugriff auf globale Effekte geben

Sonst:

→ brichst du dein eigenes Prinzip

---

# 🧠 Meta-Beobachtung

Diese 5 Systeme sind nicht unabhängig.

Du kannst später kombinieren:

* C + F → Prediction + Simulation
* D + G → Drive Fields + Umweltfeedback
* E + C → Memory erzeugt Erwartungen

---

# 🔥 Mein Vorschlag (nicht neutral)

Wenn ich wählen müsste, würde ich NICHT mit Simulation anfangen.

Zu riskant.

Ich würde:

### Schritt 1:

→ **System C (Prediction)**

### Schritt 2:

→ **System D (Drive Fields)**

### Schritt 3:

→ **System F (Simulation)**

---

Warum?

Weil:

> Simulation ohne Erwartung = blindes Raten

---

# 👉 Nächster Schritt

Ich würde dich jetzt nicht fragen:

“Welches System willst du bauen?”

Das ist zu früh.

Sondern:

👉 **Welche zwei dieser Richtungen fühlen sich für dich “grundlegend neu” an?**

Nicht interessant, sondern:

> “Das verändert das System wirklich”

Dann gehen wir eine Ebene tiefer.
