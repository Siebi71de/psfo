# 3x-Prüfen-Regel - Wertabhängige Qualitätssicherung

**Version:** 2.0  
**Datum:** 2026-02-18

---

## 🎯 Prinzip

Eine **Formel** gilt als freigegeben wenn:

1. ✅ **Override** gesetzt ODER
2. ✅ **Von Ihnen geprüft** bei diesem AN ODER
3. ✅ **3+ AN geprüft** UND
   - Der **aktuelle Wert wurde schon geprüft** ODER
   - Es wurden **3+ verschiedene Werte** geprüft

---

## 📊 Beispiel: Teilzeitfaktor

### Szenario A: Gleicher Wert

| AN | Teilzeitfaktor | Aktion | Status |
|----|----------------|--------|--------|
| #1 | 1.0 | ✅ Geprüft | 1/3 AN, 1 Wert |
| #2 | 1.0 | ✅ Geprüft | 2/3 AN, 1 Wert |
| #3 | 1.0 | ✅ Geprüft | **3/3 AN, 1 Wert** |
| #4 | 1.0 | ✅ **Automatisch OK** | Wert 1.0 bereits geprüft! |
| #5 | **0.75** | ⚠️ **NEUE KONSTELLATION** | Wert 0.75 noch nie geprüft → Prüfung erforderlich! |

**Nach Prüfung von AN #5:**

| AN | Teilzeitfaktor | Status |
|----|----------------|--------|
| #6 | 0.75 | ✅ Automatisch OK (Wert 0.75 bereits bei #5 geprüft) |
| #7 | 1.0 | ✅ Automatisch OK (Wert 1.0 bereits geprüft) |

---

### Szenario B: Diverse Werte

| AN | Teilzeitfaktor | Aktion | Status |
|----|----------------|--------|--------|
| #1 | 1.0 | ✅ Geprüft | 1/3 AN, 1 Wert |
| #2 | 0.75 | ✅ Geprüft | 2/3 AN, 2 Werte |
| #3 | 0.5 | ✅ Geprüft | **3/3 AN, 3 Werte → FREIGEGEBEN** |
| #4 | **0.85** | ✅ **Automatisch OK** | 3+ verschiedene Werte bereits geprüft |
| #5 | **0.92** | ✅ **Automatisch OK** | 3+ verschiedene Werte bereits geprüft |

**Sobald 3 verschiedene Werte geprüft wurden, sind ALLE zukünftigen Werte automatisch freigegeben.**

---

## 💡 Hintergrund

### Warum wertabhängig?

**Problem:** Eine Formel kann sich **unterschiedlich verhalten** je nach Eingabewerten.

```python
# Beispiel: Berechnung mit Teilzeitfaktor
rente = dienstjahre * 30 * teilzeitfaktor

# Wenn teilzeitfaktor immer 1.0 war:
# → Formel wurde nur für Vollzeit getestet!

# Wenn teilzeitfaktor = 0.75:
# → Neue Konstellation, könnte Rundungsfehler zeigen
```

**Lösung:** Prüfung bei **neuen Wertekonstellationen** oder nach **3 verschiedenen Werten**.

### Zwei Freigabe-Modi

**Modus 1: Bekannter Wert**
```
3+ AN geprüft UND aktueller Wert wurde schon geprüft
→ Formel ist für diesen Wert validiert
```

**Modus 2: Diverse Werte**
```
3+ verschiedene Werte geprüft
→ Formel ist robust für verschiedene Eingaben
```

---

## 🔍 Status-Anzeigen

### ✅ Wert bereits geprüft — bei X AN (Y versch. Werte)

Der **aktuelle Wert** wurde bereits bei einem anderen AN geprüft.

**Keine Aktion erforderlich.**

**Beispiel:**
```
Dienstjahre = 22.5
✅ Wert bereits geprüft — bei 5 AN (3 versch. Werte)
```

---

### ✅ Formel freigegeben — X verschiedene Werte bei Y AN geprüft

Es wurden **3+ verschiedene Werte** geprüft. Die Formel gilt als robust.

**Keine Aktion erforderlich.** Alle zukünftigen Werte sind automatisch OK.

**Beispiel:**
```
Teilzeitfaktor = 0.85
✅ Formel freigegeben — 4 verschiedene Werte bei 6 AN geprüft
```

---

### 👤 Von Ihnen geprüft · Firma: X AN, Y versch. Werte

Sie haben die Formel bei diesem AN bereits geprüft.

**Keine weitere Aktion erforderlich.** Ihre Prüfung zählt für die Firma.

---

### ⚠️ Neuer Wert — bitte prüfen

Es wurden bereits **3+ AN** geprüft, aber der **aktuelle Wert ist neu**.

**Aktion:** Formel und Ergebnis prüfen, dann bestätigen.

**Beispiel:**
```
Teilzeitfaktor = 0.33
⚠️ Neuer Wert — bitte prüfen (Firma: 5 AN geprüft, aber dieser Wert ist neu)
```

---

### ⚠️ Formel noch ungeprüft · Firma: X/3 AN, Y versch. Werte

Weniger als 3 AN wurden geprüft.

**Aktion:** 
☑️ **"Formel für diese Firma als richtig bestätigen (AN #X)"**

---

## 🔄 Abhängigkeiten

**Implementiert:** Wenn ein Input-Wert einen **neuen Wert** annimmt, werden abhängige Formeln invalidiert.

### Wie es funktioniert

```
Input: teilzeitfaktor = 0.75 (NEU, war bisher immer 1.0)
↓
System prüft: Welche Formeln verwenden teilzeitfaktor?
↓
Formeln die invalidiert werden:
- mittlerer_teilzeitfaktor (verwendet teilzeitfaktor direkt)
- grundrente_monatlich (verwendet mittlerer_teilzeitfaktor)
- altersrente_monatlich (verwendet grundrente_monatlich)
↓
Warnung: "Neue Input-Werte erkannt: teilzeitfaktor
         Abhängige Formeln müssen neu geprüft werden."
```

### Trigger

**Neue Input-Werte werden erkannt wenn:**

1. Ein Wert in der **Zeitraumtabelle** geändert wird (z.B. teilzeitfaktor: 1.0 → 0.75)
2. Ein **Input-Feld** einen neuen Wert bekommt (z.B. mittlerer_teilzeitfaktor)

**Das System prüft:**
- Wurde dieser Wert schon mal bei einem anderen AN dieser Firma verwendet?
- Wenn NEIN → Neuer Wert → Abhängige Formeln invalidieren

### Beispiel-Szenario

```
ACME GmbH - Teilzeitfaktor-Historie:

AN #1: mittlerer_teilzeitfaktor = 1.0
  → grundrente_monatlich geprüft ✓

AN #2: mittlerer_teilzeitfaktor = 1.0
  → grundrente_monatlich automatisch OK (Wert 1.0 bekannt)

AN #3: mittlerer_teilzeitfaktor = 1.0
  → grundrente_monatlich automatisch OK

AN #4: mittlerer_teilzeitfaktor = 0.75 (NEU!)
  ⚠️ Warnung: "Neue Input-Werte: mittlerer_teilzeitfaktor"
  🔄 Formeln invalidiert: grundrente_monatlich, altersrente_monatlich
  → Beide Formeln müssen für AN #4 neu geprüft werden

Nach Prüfung von AN #4:
AN #5: mittlerer_teilzeitfaktor = 0.75
  → grundrente_monatlich automatisch OK (Wert 0.75 jetzt bekannt)
```

### Abhängigkeitsbaum (Beispiel)

```
eintrittsdatum
├─→ dienstjahre
│   ├─→ grundrente_monatlich
│   │   └─→ altersrente_monatlich
│   └─→ mn_regel_faktor
│       └─→ altersrente_monatlich
└─→ unverfallbarkeitspruefung

teilzeitfaktor (Zeitraum)
└─→ mittlerer_teilzeitfaktor
    └─→ grundrente_monatlich
        └─→ altersrente_monatlich
```

**Wenn `eintrittsdatum` geändert wird:**
→ Invalidiert: dienstjahre, grundrente_monatlich, altersrente_monatlich, mn_regel_faktor, unverfallbarkeitspruefung

**Wenn `teilzeitfaktor` in Zeitraum geändert wird:**
→ Invalidiert: mittlerer_teilzeitfaktor, grundrente_monatlich, altersrente_monatlich

### Gespeicherte Daten

```json
{
  "acme_gmbh__grundrente_monatlich": {
    "person_001": {
      "wert": 1102.5,
      "geprueft_am": "2026-02-18 10:25",
      "inputs": {
        "dienstjahre": 36.75,
        "mittlerer_teilzeitfaktor": 1.0,
        "eintrittsdatum": "2005-09-01"
      }
    }
  }
}
```

Das `inputs`-Feld speichert alle relevanten Input-Werte zum Zeitpunkt der Prüfung.

---

## 📁 Technische Umsetzung

### pruefungen.json

```json
{
  "acme_gmbh__teilzeitfaktor": {
    "person_001": {
      "wert": 1.0,
      "geprueft_am": "2026-02-18 10:23"
    },
    "person_005": {
      "wert": 1.0,
      "geprueft_am": "2026-02-18 11:15"
    },
    "person_009": {
      "wert": 1.0,
      "geprueft_am": "2026-02-18 14:30"
    },
    "person_012": {
      "wert": 0.75,
      "geprueft_am": "2026-02-18 15:00"
    }
  }
}
```

**Key-Struktur:**
- Key = `person_id` (Arbeitnehmer-ID)
- Jeder AN kann nur einmal geprüft werden
- Ein Prüfer kann beliebig viele verschiedene AN prüfen

**Optional:** Das Feld `geprueft_von` kann für Audit-Zwecke hinzugefügt werden (benötigt Login-System).

**Analyse:**
- Geprüfte Werte: `[1.0, 1.0, 1.0, 0.75]`
- Verschiedene Werte: `{1.0, 0.75}` → 2 Werte
- Anzahl Prüfungen: 4

**Für neuen AN mit Wert 1.0:**
→ ✅ Wert bereits geprüft (bei person_001, _005, _009)

**Für neuen AN mit Wert 0.5:**
→ ⚠️ Neuer Wert (noch nicht geprüft, obwohl 4 AN bereits geprüft wurden)

**Nach Prüfung von 0.5:**
- Verschiedene Werte: `{1.0, 0.75, 0.5}` → **3 Werte**
→ ✅ Formel freigegeben für alle zukünftigen Werte!

---

## ❓ FAQ

**Q: Was ist der Unterschied zwischen "Wert bereits geprüft" und "Formel freigegeben"?**  
A: 
- **Wert bereits geprüft:** Dieser spezifische Wert (z.B. 1.0) wurde schon mal geprüft → nur dieser Wert ist OK
- **Formel freigegeben:** 3+ verschiedene Werte wurden geprüft → ALLE zukünftigen Werte sind OK

**Q: Wann ist eine Formel "robust genug"?**  
A: Sobald **3 verschiedene Werte** geprüft wurden. Dann wird angenommen, dass die Formel für verschiedene Eingaben korrekt funktioniert.

**Q: Was passiert wenn ich denselben Wert nochmal prüfe?**  
A: Die Prüfung wird registriert, aber die Anzahl **verschiedener Werte** erhöht sich nicht. Beispiel: Prüfung von 1.0, 1.0, 1.0, 1.0 → nur 1 verschiedener Wert.

**Q: Warum muss ich 0.75 prüfen obwohl schon 5 AN geprüft wurden?**  
A: Weil alle bisherigen Prüfungen mit Wert 1.0 waren. Der Wert 0.75 ist eine **neue Konstellation** die separat geprüft werden muss.

**Q: Wie viele verschiedene Werte muss ich mindestens prüfen?**  
A: Entweder:
- 1 Wert bei 3+ AN (dann ist nur dieser Wert freigegeben) ODER
- 3+ verschiedene Werte (dann sind alle Werte freigegeben)

**Q: Was passiert wenn ich einen Input-Wert ändere?**  
A: Das System erkennt ob dieser Wert neu ist (noch nie bei einem anderen AN verwendet). Wenn ja:
1. Warnung: "Neue Input-Werte erkannt: [feldname]"
2. Alle Formeln die von diesem Feld abhängen werden invalidiert
3. Diese Formeln müssen für diesen AN neu geprüft werden

**Q: Wie weiß das System welche Formeln zusammenhängen?**  
A: Aus den Formel-Definitionen im Schema. Beispiel:
```json
{
  "formula": {
    "type": "expression",
    "expression": "dienstjahre * 30",
    "inputs": ["dienstjahre"]
  }
}
```
→ Diese Formel hängt von "dienstjahre" ab.

**Q: Kann ich die Invalidierung rückgängig machen?**  
A: Nein, aber Sie können die Formeln einfach neu prüfen. Die Invalidierung dient der Qualitätssicherung - wenn sich Input-Werte ändern, muss die Formel für diese neue Konstellation geprüft werden.

---

## 🔧 Zurücksetzen (Admin)

```python
# Einzelne Formel bei einer Firma zurücksetzen
import json
with open('pruefungen.json') as f:
    data = json.load(f)

# Prüfungen für teilzeitfaktor bei ACME löschen
if 'acme_gmbh__teilzeitfaktor' in data:
    del data['acme_gmbh__teilzeitfaktor']

with open('pruefungen.json', 'w') as f:
    json.dump(data, f, indent=2)
```

---

**Letzte Aktualisierung:** 18.02.2026  
**Version:** 2.0 (Wertabhängige QS)

---

## 🔍 Status-Anzeigen

### ✅ Formel freigegeben — geprüft bei 3 verschiedenen AN dieser Firma

Die Formel wurde bereits 3× geprüft. Sie ist für **alle AN** dieser Firma freigegeben.

**Keine weitere Aktion erforderlich.**

---

### 👤 Von Ihnen geprüft bei diesem AN · Firma: 2/3 AN geprüft

Sie haben diese Formel bei dem aktuellen AN geprüft. Insgesamt wurden bei dieser Firma erst 2 AN geprüft.

**Noch 1 Prüfung bis zur Freigabe.**

---

### ⚠️ Formel noch ungeprüft · Firma: 1/3 AN geprüft

Sie haben diese Formel bei diesem AN noch nicht geprüft. Insgesamt wurden bei dieser Firma bereits 1 AN geprüft.

**Aktion:** Prüfen Sie Formel und Ergebnis, dann:  
☑️ **"Formel für diese Firma als richtig bestätigen (AN #2/3)"**

---

### ✏️ Manuell überschrieben

Der Wert wurde manuell gesetzt. Keine Prüfung erforderlich.

---

## 📁 Technische Umsetzung

### pruefungen.json

```json
{
  "acme_gmbh__dienstjahre": {
    "person_001": {
      "geprueft_am": "2026-02-18 10:23"
    },
    "person_005": {
      "geprueft_am": "2026-02-18 11:15"
    },
    "person_009": {
      "geprueft_am": "2026-02-18 14:30"
    }
  }
}
```

**Key-Format:** `<firma_id>__<feld_id>`  
**Value:** Dictionary mit Prüfungen pro Person  
**Regel:** `len(value) >= 3` → Freigegeben

---

## 💡 Warum diese Regel?

### Qualitätssicherung

- **Mehraugenprinzip:** 3 verschiedene Sachbearbeiter prüfen
- **Systematische Fehler:** Werden wahrscheinlich erkannt
- **Plausibilität:** Verschiedene AN-Konstellationen getestet

### Effizienz

- **Einmalig:** Nach 3 Prüfungen keine weiteren nötig
- **Skalierbar:** Bei 100 AN nur 3 Prüfungen statt 100
- **Zeitsparend:** Routine-Fälle laufen automatisch durch

### Compliance

- **Nachvollziehbar:** Wer hat wann geprüft?
- **Dokumentiert:** Prüfungsstand in pruefungen.json
- **Auditierbar:** Prüfhistorie verfügbar

---

## ❓ FAQ

**Q: Kann ich die Formel bei demselben AN mehrmals prüfen?**  
A: Nein. Pro AN ist nur **eine Prüfung** möglich - egal von welchem Prüfer.

**Q: Ich habe die Formel schon bei AN #1 geprüft. Kann ich auch bei AN #2 prüfen?**  
A: Ja! Ein Prüfer kann **beliebig viele verschiedene AN** prüfen. In der Praxis gibt es meist 2 Prüfer pro Firma.

**Q: Kann ein anderer Prüfer denselben AN auch prüfen?**  
A: Nein. Pro AN ist nur **eine Prüfung** möglich. Jeder AN wird nur einmal für die QS herangezogen.

**Q: Was passiert wenn sich die Formel ändert?**  
A: Der Prüfungsstand bleibt bestehen. Bei größeren Änderungen sollte `pruefungen.json` manuell zurückgesetzt werden.

**Q: Muss ich alle 3 Formeln (Dienstjahre, Grundrente, etc.) separat prüfen?**  
A: Ja. Jede Formel hat ihren eigenen Prüfungsstand.

**Q: Gilt die Freigabe auch für andere Firmen?**  
A: Nein. Jede Firma hat separate Prüfungsstände. ACME freigegeben ≠ TechCorp freigegeben.

---

## 🔧 Zurücksetzen (Admin)

Bei größeren Änderungen der Versorgungsordnung:

```bash
# Kompletter Reset
rm pruefungen.json
echo '{}' > pruefungen.json

# Nur eine Firma zurücksetzen
python3 << 'EOF'
import json
with open('pruefungen.json') as f:
    data = json.load(f)

# Alle Keys für ACME entfernen
keys_to_remove = [k for k in data.keys() if k.startswith('acme_gmbh__')]
for key in keys_to_remove:
    del data[key]

with open('pruefungen.json', 'w') as f:
    json.dump(data, f, indent=2)
EOF
```

---

**Letzte Aktualisierung:** 18.02.2026  
**Version:** 1.0
