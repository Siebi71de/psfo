# PSVaG Leistungsverwaltung - Benutzerhandbuch

**Version:** 1.0  
**Datum:** 2026-02-18  
**Zielgruppe:** Sachbearbeiter, Pensionsverwalter

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Erste Schritte](#erste-schritte)
3. [Dateneingabe](#dateneingabe)
4. [Zeitraumtabelle](#zeitraumtabelle)
5. [Berechnungen](#berechnungen)
6. [Qualitätssicherung](#qualitätssicherung)
7. [Tipps & Tricks](#tipps--tricks)

---

## Übersicht

Das PSVaG-Formularsystem ermöglicht die **Erfassung und Berechnung von Betriebsrentenansprüchen** im Insolvenzfall nach BetrAVG.

### Was kann das System?

✅ **Personendaten erfassen** - Geburtsdatum, Ein-/Austritt, Gehalt  
✅ **Zeiträume detailliert erfassen** - Mit Teilzeit, GGF-Status, Tarifgruppen  
✅ **Automatische Berechnungen** - Dienstjahre, m/n-Regel, Rentenansprüche  
✅ **Unverfallbarkeitsprüfung** - Nach § 1b BetrAVG (Alt-/Neu-Regelung)  
✅ **Qualitätssicherung** - 3x-Prüfen-Regel für alle Ergebnisse  
✅ **Manuelle Overrides** - Bei Sonderfällen individuelle Anpassungen

### Firmen-spezifische Unterschiede

Jede Firma hat ihre eigene **Versorgungsordnung** mit unterschiedlichen Parametern:

| Firma | Besonderheit | Zeitraumtabelle |
|-------|--------------|-----------------|
| **ACME GmbH** | Pauschale Grundrente | Stundensatz |
| **TechCorp AG** | Tarifgruppen-System (TG A-E) | Tarifgruppe, Bonus |
| **Global Services** | Gehaltsabhängige Rente | Gehalt monatlich |

---

## Erste Schritte

### 1. Firma auswählen

Wählen Sie in der Seitenleiste die **Firma** aus. Dies lädt die entsprechende Versorgungsordnung.

### 2. Person auswählen

Wählen Sie die zu bearbeitende **Person** aus der Liste. Das Formular zeigt die hinterlegten Daten.

### 3. Daten prüfen

Die Oberfläche gliedert sich in Bereiche:

```
┌─────────────────────────────────────┐
│ Basis-Daten                         │
│ - Eintrittsdatum                    │
│ - Austrittsdatum                    │
│ - Geburtsdatum                      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Personen-Daten                      │
│ - Geburtsdatum (falls nicht oben)  │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Berechnungsparameter                │
│ - Mittlerer Teilzeitfaktor          │
│ - Letztes Gehalt (bei Neu-Regelung)│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Zeitraum-Erfassung                  │
│ [Detaillierte Tabelle]              │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Berechnungs-Ergebnisse              │
│ - Unverfallbarkeit                  │
│ - Dienstjahre                       │
│ - m/n-Regel                         │
│ - Rentenansprüche                   │
└─────────────────────────────────────┘
```

---

## Dateneingabe

### Basis-Daten

**Eintrittsdatum** und **Austrittsdatum** sind die wichtigsten Felder.

💡 **Tipp:** Bei Insolvenz wird automatisch das **Insolvenzdatum** verwendet, wenn es vor dem eingegebenen Austrittsdatum liegt.

```
Beispiel:
Eingegebenes Austrittsdatum: 01.02.2025
Insolvenzdatum (Firma):      30.06.2024
→ Effektiv verwendet:        30.06.2024 ⚠️ "Austritt durch Insolvenz"
```

### Teilzeitfaktor-Eingabe

Der Teilzeitfaktor kann auf **zwei Arten** eingegeben werden:

**1. Als Dezimalzahl:**
```
0.75  →  75% Teilzeit
1.0   →  Vollzeit
0.5   →  50% Teilzeit
```

**2. Als Bruch (Wochenstunden):**
```
22/38  →  = 0.5789  (22 Std. bei 38 Std. Vollzeit)
30/40  →  = 0.7500  (30 Std. bei 40 Std. Vollzeit)
35/38  →  = 0.9211  (35 Std. bei 38 Std. Vollzeit)
```

Das System berechnet automatisch den Dezimalwert und zeigt ihn an.

### Conditional Fields

Manche Felder erscheinen nur unter bestimmten Bedingungen:

**"Letztes Gehalt"** → Nur sichtbar bei **Eintritt ab 2008** (Neu-Regelung)

---

## Zeitraumtabelle

Die Zeitraumtabelle ermöglicht die **detaillierte Erfassung** von Beschäftigungsverläufen.

### Grundprinzip

Jede Person hat **eine durchgehende Zeitlinie** vom Erfassungsbeginn bis zum Erfassungsende:

```
┌───────────────────────────────────────────────────┐
│ Erfassungsbeginn          →          Erfassungsende│
│ 01.09.2005                           30.06.2024   │
└───────────────────────────────────────────────────┘
```

Diese wird in **Zeiträume** unterteilt, die unterschiedliche Eigenschaften haben können.

### Spalten

**Standardspalten (alle Firmen):**

| Spalte | Beschreibung | Eingabe |
|--------|--------------|---------|
| **Bis** | Ende des Zeitraums | Datum (nur änderbar bei Zwischen-Zeiträumen) |
| **Dienstzeit** | Zählt für m-Berechnung? | ☑ Checkbox |
| **GGF** | Gesellschafter-Geschäftsführer | ☑ Checkbox |
| **Teilzeitfaktor** | Arbeitszeit-Anteil | Dezimal oder Bruch (z.B. 30/40) |

**Firmen-spezifische Spalten:**

- **ACME:** Stundensatz (€)
- **TechCorp:** Tarifgruppe (TG A-E), Bonus % (nur bei TG D/E)
- **Global Services:** Gehalt (EUR/Monat)

### Zeiträume bearbeiten

#### Zeitraum teilen (Split)

Klicken Sie auf **✂️** um einen Zeitraum zu teilen:

```
Vorher:
├─────────────────────────────────┤
  01.09.2005 - 30.06.2024

Split-Datum: 01.01.2008

Nachher:
├───────────────┼─────────────────┤
  01.09.2005      01.01.2008
  - 31.12.2007    - 30.06.2024
```

💡 **Verwendung:** Wechsel von Teilzeit zu Vollzeit, Änderung der Tarifgruppe, etc.

#### Zeiträume zusammenführen (Merge)

Klicken Sie auf **🔗** um zwei aufeinanderfolgende Zeiträume zu vereinen:

```
Vorher:
├───────────────┼─────────────────┤
  Zeitraum 1      Zeitraum 2

Nachher:
├─────────────────────────────────┤
  Zeitraum 1 (vereint)
```

💡 **Verwendung:** Korrektur von versehentlichen Splits

### m-Berechnung

Für die **m/n-Regel** (§ 2 BetrAVG) zählen nur Zeiträume mit:

✅ **Dienstzeit = Ja** (als_dienstzeit = true)  
✅ **GGF = Nein** (ggf = false)

**Beispiel:**

```
Zeitraum 1: 2005-2010, Dienstzeit=Ja, GGF=Nein, TZ=1.0
→ Zählt für m: 5 Jahre × 1.0 = 5 Jahre

Zeitraum 2: 2010-2015, Dienstzeit=Ja, GGF=Ja, TZ=1.0
→ Zählt NICHT (GGF-Zeit)

Zeitraum 3: 2015-2024, Dienstzeit=Nein, GGF=Nein, TZ=0.75
→ Zählt NICHT (keine Dienstzeit)

Gesamt m = 5 Jahre
```

### Tarifgruppen (TechCorp)

Bei TechCorp bestimmt die **Tarifgruppe** den Rentenfaktor:

| Tarifgruppe | Rentenfaktor | Beschreibung |
|-------------|--------------|--------------|
| **TG A** | 1 €/Monat | Einstieg |
| **TG B** | 2 €/Monat | Junior |
| **TG C** | 3 €/Monat | Standard |
| **TG D** | 5 €/Monat | Senior (+ Bonus möglich) |
| **TG E** | 10 €/Monat | Expert (+ Bonus möglich) |

**Berechnung:**
```
Monatsrente = Summe(Monate × Tarifgruppen-Faktor × Teilzeit)

Beispiel:
- 60 Monate TG C, Vollzeit: 60 × 3 × 1.0 = 180 EUR
- 24 Monate TG E, Teilzeit 0.75: 24 × 10 × 0.75 = 180 EUR
→ Gesamt: 360 EUR/Monat
```

Die **Bonus-Spalte** erscheint nur bei TG D und E und erhöht den Faktor prozentual.

---

## Berechnungen

### Unverfallbarkeitsprüfung

Das System prüft automatisch nach **§ 1b BetrAVG**:

**Alt-Regelung (Eintritt vor 2008):**
- Mindestalter 30 + 5 Jahre Betriebszugehörigkeit ODER
- Mindestalter 35 (unabhängig von Betriebszugehörigkeit)

**Neu-Regelung (Eintritt ab 2008):**
- 3 Jahre Betriebszugehörigkeit

**Entgeltumwandlung:**
- Sofort unverfallbar (kein Mindestalter/Dienstzeit)

```
Beispiel:
Anna Schneider
- Geburt: 15.06.1975
- Eintritt: 01.09.2005
- Austritt: 30.06.2024 (Insolvenz)
- Alter bei Austritt: 48.96 Jahre
- Dienstjahre: 18.83 Jahre
→ Erfüllt Alt-Regelung (Alter > 35)
→ ✅ Unverfallbar
```

### Dienstjahre (n)

**Theoretisch erreichbare Dienstjahre** = max. Endalter − individueller Zusagebeginn

```
Komponenten:
- Zusagebeginn = max(VO-Datum, Eintrittsdatum)
- Max. Endalter = max(min(Beginn Altersleistung, gesetzl. Rente), Austritt)
- Beginn Altersleistung = Geburtsdatum + Regelaltersgrenze (meist 67)
- Gesetzl. Rentenbeginn = nach § 235 SGB VI mit Veränderungssperre

Beispiel Anna Schneider:
- Zusagebeginn: 01.09.2005
- Gesetzl. Rentenbeginn: 01.06.2042 (67 Jahre)
- Dienstjahre (n): 36.75 Jahre
```

### m/n-Regel (§ 2 BetrAVG)

**Ratierliche Kürzung** bei vorzeitigem Ausscheiden:

```
Faktor = m / n

m = anrechenbare Dienstzeit (taggenau, nur Dienstzeit & nicht-GGF)
n = theoretisch erreichbare Dienstjahre (taggenau)

Gekürzte Leistung = Vollleistung × (m/n)
```

**Detailansicht:**

Das System zeigt eine ausführliche Aufschlüsselung:

```
Details m/n-Regel (§ 2 BetrAVG):
  Individueller Zusagebeginn    2005-09-01
  Austritt (maßgeblich)         2024-06-30    Insolvenzdatum
  Beginn Altersleistung (VO)    2042-06-01    Regelaltersgrenze 67
  Gesetzl. Rentenbeginn         2042-06-01    Veränderungssperre: 67 Jahre
  Maximales Endalter (n-Basis)  2042-06-01
  n (theoretisch erreichbar)    13,421 Tage (36.75 Jahre)
  m (anrechenbare Dienstzeit)   6,877 Tage (18.83 Jahre)
  m/n-Faktor                    51.24%
  Ratierliche Leistung          256.20 EUR/Monat

Anrechenbare Zeiträume (m):
  Von          Bis          Tage    TZ-Faktor  Anrechnung
  2005-09-01   2024-06-30   6,877   1.00       ✅ Dienstzeit, kein GGF
```

### Rentenansprüche

Die Berechnung variiert je nach Firma:

**Global Services (gehaltsabhängig):**
```
Grundrente monatlich = (Dienstjahre × 30) EUR
Altersrente monatlich = Grundrente × m/n-Faktor
```

**TechCorp (tarifgruppen-basiert):**
```
Für jeden Zeitraum:
  Monate × Tarifgruppen-Faktor × Teilzeitfaktor
Gesamt: Summe aller Zeiträume
```

**ACME (pauschale Grundrente):**
```
Fester Betrag × m/n-Faktor
```

---

## Qualitätssicherung

### 3x-Prüfen-Regel (Wertabhängig)

Jede **Formel** wird **pro Firma** qualitätsgesichert. Die Prüfung ist **wertabhängig**:

**Freigegeben wenn:**
1. ✅ Override gesetzt ODER
2. ✅ Von Ihnen geprüft bei diesem AN ODER
3. ✅ 3+ AN geprüft UND (aktueller Wert wurde schon geprüft ODER 3+ verschiedene Werte geprüft)

**Status-Anzeige:**

🟢 **Wert bereits geprüft — bei X AN (Y versch. Werte)**  
→ Der aktuelle Wert (z.B. Teilzeitfaktor = 1.0) wurde bereits bei einem anderen AN geprüft

🟢 **Formel freigegeben — X verschiedene Werte bei Y AN geprüft**  
→ 3+ verschiedene Werte wurden geprüft, Formel ist robust für alle Eingaben

🟡 **Von Ihnen geprüft · Firma: X AN, Y versch. Werte**  
→ Sie haben die Formel bei diesem AN geprüft

🔴 **Neuer Wert — bitte prüfen**  
→ 3+ AN wurden geprüft, aber dieser spezifische Wert ist neu

🔴 **Formel noch ungeprüft · Firma: X/3 AN, Y versch. Werte**  
→ Checkbox: "Formel für diese Firma als richtig bestätigen (AN #X)"

**Workflow-Beispiel:**

```
ACME - Teilzeitfaktor:

AN #1: 1.0 → geprüft ✓ (1 AN, 1 Wert)
AN #2: 1.0 → geprüft ✓ (2 AN, 1 Wert)
AN #3: 1.0 → geprüft ✓ (3 AN, 1 Wert)
AN #4: 1.0 → ✅ Automatisch OK (Wert 1.0 bereits geprüft)
AN #5: 0.75 → ⚠️ NEUER WERT → Prüfung erforderlich!

Nach Prüfung:
AN #6: 0.75 → ✅ Automatisch OK (Wert 0.75 jetzt bekannt)
AN #7: 0.5 → ⚠️ NEUER WERT → Prüfung erforderlich!

Nach Prüfung (jetzt 3 verschiedene Werte):
AN #8: 0.85 → ✅ Automatisch OK (3 verschiedene Werte → freigegeben)
```

**Abhängigkeiten:**

Wenn ein Input-Wert einen **neuen Wert** annimmt, werden **abhängige Formeln invalidiert**:

```
⚠️ Neue Input-Werte erkannt: mittlerer_teilzeitfaktor
   Abhängige Formeln müssen neu geprüft werden.

🔄 Formeln invalidiert: grundrente_monatlich, altersrente_monatlich
   Diese müssen für diesen AN neu geprüft werden.
```

**Hintergrund:**

Die Regel stellt sicher, dass:
- Formeln mit **verschiedenen Eingabewerten** getestet werden
- **Neue Wertekonstellationen** separat geprüft werden
- Nach **3 verschiedenen Werten** die Formel als robust gilt
- **Abhängige Formeln** bei neuen Inputs neu geprüft werden

### Override-Funktion

Für **Sonderfälle** können Werte manuell überschrieben werden:

1. ☑ "Manuell überschreiben" aktivieren
2. Wert eingeben
3. Automatisch gespeichert

**Wichtig:** Bei Änderung von Eingabedaten erscheint eine Warnung:

```
⚠️ Eingaben geändert: eintrittsdatum
Es gibt 2 manuelle Überschreibung(en).
Diese basieren möglicherweise auf veralteten Eingaben.

[🗑️ Alle Overrides löschen]
```

Sie können entscheiden, ob Sie die Overrides löschen oder beibehalten möchten.

---

## Tipps & Tricks

### 💡 Reaktive Berechnungen

Das System berechnet **automatisch** bei jeder Eingabe-Änderung:

```
Eintrittsdatum ändern
  → Dienstjahre aktualisieren
  → m/n-Regel neu berechnen
  → Rentenansprüche anpassen
```

### 💡 Zeitraum-Shortcuts

**Schnell-Split bei Vollzeit → Teilzeit:**

1. Klicken Sie ✂️ beim Vollzeit-Zeitraum
2. Geben Sie das Wechseldatum ein
3. Bestätigen Sie mit "Teilen"
4. Im zweiten Zeitraum: Teilzeitfaktor anpassen

**Beispiel:** `30/40` für 30-Stunden-Woche bei 40-Std-Vollzeit

### 💡 Berechnungs-Log

Bei Problemen hilft der **Berechnungs-Log** (unten aufklappbar):

```
Berechne dienstjahre...
dienstjahre = 36.75
Berechne grundrente_monatlich...
grundrente_monatlich = 1102.5
```

Zeigt alle Berechnungsschritte chronologisch.

### 💡 Datums-Formate

Das System akzeptiert verschiedene Eingaben:

```
Kalender-Widget: 18.02.2026
Direkteingabe: 2026-02-18
```

Beide Formate funktionieren in allen Datumsfeldern.

### 💡 Personen-Wechsel

Beim Wechsel zwischen Personen werden **alle Widget-States zurückgesetzt**, um "eingefrorene" Werte zu vermeiden. Änderungen werden automatisch gespeichert.

---

## Häufige Fragen (FAQ)

**Q: Warum ändert sich die Dienstzeit nicht, wenn ich das Eintrittsdatum ändere?**  
A: Prüfen Sie, ob Sie manuelle Overrides gesetzt haben. Diese werden bei der Warnung angezeigt. Klicken Sie ggf. "Alle Overrides löschen".

**Q: Muss ich die Formel bei jedem Arbeitnehmer einzeln prüfen?**  
A: Nein! Die 3x-Prüfen-Regel ist **firmenbezogen**. Wenn die Formel "Dienstjahre" bei ACME bereits bei 3 verschiedenen AN geprüft wurde, ist sie automatisch für alle weiteren AN dieser Firma freigegeben. Bei einer anderen Firma (z.B. TechCorp) muss die Formel separat geprüft werden.

**Q: Ich habe die Formel schon bei 2 AN geprüft. Kann ich auch beim gleichen AN nochmal prüfen?**  
A: Nein. Pro AN kann nur **einmal** geprüft werden. Sie können aber beliebig viele verschiedene AN prüfen.

**Q: Kann ein anderer Prüfer denselben AN auch prüfen?**  
A: Nein. Pro AN ist nur **eine Prüfung** möglich - egal von welchem Prüfer. Jeder AN wird nur einmal für die QS herangezogen.

**Q: Was passiert wenn die Formel nach der Freigabe geändert wird?**  
A: Der Prüfungsstand bleibt bestehen. Bei größeren Änderungen (z.B. neue Versorgungsordnung) sollte der Prüfungsstand manuell zurückgesetzt werden.

**Q: Die Zeitraumtabelle zeigt nicht alle Spalten.**  
A: Manche Spalten sind **conditional** und erscheinen nur unter bestimmten Bedingungen (z.B. Bonus nur bei TG D/E).

**Q: Kann ich Zeiträume löschen?**  
A: Nein, aber Sie können sie zusammenführen (Merge 🔗) oder auf "Dienstzeit = Nein" setzen, dann zählen sie nicht für m.

**Q: Was ist der Unterschied zwischen "Dienstzeit" und "GGF"?**  
A: Beide müssen richtig sein damit m zählt:
- Dienstzeit = Ja → Grundsätzlich anrechenbar
- GGF = Nein → Nicht als Gesellschafter-Geschäftsführer beschäftigt

**Q: Wie funktioniert die Veränderungssperre beim gesetzlichen Rentenbeginn?**  
A: Die **Rechtslage zum Insolvenzdatum** wird eingefroren. Bei Insolvenz 2024 gilt die damalige Regelaltersgrenze (67 Jahre für Geburtsjahr 1964+), auch wenn sich das Gesetz später ändern sollte.

---

---

**Letzte Aktualisierung:** 18.02.2026  
**Version:** 1.0

