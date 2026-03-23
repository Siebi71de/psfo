# PSVaG Leistungsverwaltung - JSON-Schnittstellen

**Version:** 1.0  
**Datum:** 2026-02-18  
**Zielgruppe:** Entwickler, Systemadministratoren

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Firmen-JSON Struktur](#firmen-json-struktur)
3. [Schema-Definition](#schema-definition)
4. [Formel-System](#formel-system)
5. [UI-Layout](#ui-layout)
6. [Zeitraumtabelle](#zeitraumtabelle)
7. [Personen-Daten](#personen-daten)
8. [Prüfungs-System (3x-Regel)](#prüfungs-system-3x-regel)
9. [Best Practices](#best-practices)

---

## Übersicht

Das System verwendet **JSON-Konfigurationsdateien** zur vollständigen Definition von:

- Versorgungsordnungen und Firmenparametern
- Berechnungsformeln und Leistungsteilen
- UI-Layout und Eingabefelder
- Zeitraumtabellen-Konfiguration
- Personendaten und Overrides

### Datei-Struktur

```
/firmen/
├── acme_gmbh.json           # ACME GmbH Versorgungsordnung
├── techcorp_ag.json         # TechCorp AG mit Tarifgruppen
└── global_services.json     # Global Services gehaltsabhängig

/personen/
└── personen.json            # Alle Personen mit Firmenzuordnung

/pruefungen.json             # Globaler Prüfungsstand (3x-Regel)
```

---

## Firmen-JSON Struktur

Jede Firma hat eine eigene JSON-Datei mit folgender Top-Level-Struktur:

```json
{
  "firma": {
    "id": "techcorp_ag",
    "name": "TechCorp AG",
    "beschreibung": "IT-Dienstleister mit Tarifgruppen-System"
  },
  "versorgungsordnung": {
    "name": "TechCorp Pensionsplan 2010",
    "zusagedatum": "2010-01-01",
    "insolvenzdatum": "2023-11-30",
    "entgeltumwandlung": false,
    "parameter": { ... },
    "tarifgruppen": { ... }
  },
  "schema": {
    "input_fields": [ ... ],
    "leistungsteile": [ ... ],
    "ui_layout": { ... }
  }
}
```

### Firma-Objekt

```json
{
  "firma": {
    "id": "unique_identifier",
    "name": "Display Name",
    "beschreibung": "Kurze Beschreibung für UI"
  }
}
```

### Versorgungsordnung

```json
{
  "versorgungsordnung": {
    "name": "Offizielle Bezeichnung der VO",
    "zusagedatum": "YYYY-MM-DD",
    "insolvenzdatum": "YYYY-MM-DD",
    "entgeltumwandlung": true|false,
    
    "parameter": {
      "regelaltersgrenze": 67,
      "stichtag": "2008-01-01",
      "custom_param": "value"
    },
    
    "tarifgruppen": {
      "TG_A": {
        "name": "Tarifgruppe A",
        "faktor_pro_monat": 1.0
      }
    }
  }
}
```

**Wichtige Felder:**

- **zusagedatum**: Datum der Versorgungszusage (für m/n-Regel)
- **insolvenzdatum**: Effektives Austrittsdatum bei Insolvenz
- **entgeltumwandlung**: Wenn true → sofortige Unverfallbarkeit
- **parameter**: Beliebige Key-Value-Pairs für Berechnungen
- **tarifgruppen**: Firmenspezifische Tarifstrukturen

---

## Schema-Definition

### Input Fields

Definiert alle Eingabefelder:

```json
{
  "input_fields": [
    {
      "id": "eintrittsdatum",
      "label": "Eintrittsdatum",
      "type": "date",
      "required": true,
      "category": "basis",
      "order": 1,
      "help": "Beginn der Betriebszugehörigkeit",
      "visible_in": ["all"]
    },
    {
      "id": "letztes_gehalt",
      "label": "Letztes Gehalt (EUR/Monat)",
      "type": "number",
      "min": 0.0,
      "max": 50000.0,
      "step": 100.0,
      "default": 0.0,
      "required": true,
      "category": "berechnung",
      "order": 5,
      "help": "Nur bei Neu-Regelung (Eintritt ab 2008) erforderlich",
      "visible_in": ["einfach"],
      "conditional": {
        "field": "eintrittsdatum",
        "operator": ">=",
        "value": "2008-01-01"
      }
    },
    {
      "id": "mittlerer_teilzeitfaktor",
      "label": "Mittlerer Teilzeitfaktor",
      "type": "slider",
      "min": 0.0,
      "max": 1.0,
      "step": 0.05,
      "default": 1.0,
      "category": "berechnung",
      "help": "Dezimalzahl (z.B. 0.75) oder Bruch (z.B. 30/40)"
    }
  ]
}
```

**Feld-Typen:**

| Type | Widget | Beschreibung |
|------|--------|--------------|
| `date` | Date Picker | YYYY-MM-DD Format |
| `number` | Number Input | Min/Max/Step konfigurierbar |
| `slider` | Text Input | Akzeptiert Dezimal oder Bruch (z.B. 22/38) |
| `checkbox` | Checkbox | true/false |
| `dropdown` | Selectbox | Vordefinierte Optionen |

**Kategorien:**

- `basis`: Immer sichtbar, vor Tabs (z.B. Eintrittsdatum)
- `person`: Personendaten (z.B. Geburtsdatum)
- `berechnung`: Berechnungsparameter (z.B. Teilzeitfaktor)

**Conditional Logic:**

```json
{
  "conditional": {
    "field": "eintrittsdatum",
    "operator": ">=",
    "value": "2008-01-01"
  }
}
```

**Operatoren:** `>=`, `<=`, `>`, `<`, `==`, `!=`, `in`

### Leistungsteile

Definiert berechnete Felder:

```json
{
  "leistungsteile": [
    {
      "id": "dienstjahre",
      "label": "Dienstjahre",
      "art": "Berechnungsgrundlage",
      "einheit": "Jahre",
      "formula": {
        "type": "function",
        "function_id": "calculate_dienstjahre",
        "inputs": ["eintrittsdatum", "austrittsdatum", "geburtsdatum"]
      }
    },
    {
      "id": "grundrente_monatlich",
      "label": "Grundrente monatlich",
      "art": "Altersrente",
      "einheit": "EUR/Monat",
      "formula": {
        "type": "expression",
        "expression": "dienstjahre * 30"
      },
      "rechtsgrundlage": {
        "dokument": "VO",
        "paragraf": "§ 3 Abs. 1",
        "volltext": "30 EUR pro Dienstjahr"
      }
    },
    {
      "id": "mittlerer_teilzeitfaktor",
      "label": "Mittlerer Teilzeitfaktor",
      "art": "Berechnungsgrundlage",
      "einheit": "Faktor",
      "formula": {
        "type": "zeitraum_aggregation",
        "aggregation": "gewichteter_durchschnitt",
        "field": "teilzeitfaktor",
        "zeitraeume_id": "zeitraeume"
      }
    }
  ]
}
```

**Arten (art):**

- `Berechnungsgrundlage`: Zwischenwerte (Dienstjahre, Teilzeitfaktor)
- `Altersrente`: Rentenansprüche
- `Invaliditätsrente`: Erwerbsminderungsrenten
- `Hinterbliebenenrente`: Witwen-/Waisenrenten

---

## Formel-System

### Expression

Einfache mathematische Ausdrücke:

```json
{
  "type": "expression",
  "expression": "dienstjahre * 30 + letztes_gehalt * 0.02"
}
```

**Unterstützte Operatoren:** `+`, `-`, `*`, `/`, `(`, `)`

### Function

Python-Funktion aufrufen:

```json
{
  "type": "function",
  "function_id": "calculate_tarifgruppen_rente",
  "inputs": ["eintrittsdatum", "austrittsdatum", "geburtsdatum"]
}
```

**Verfügbare Funktionen:**

| Function ID | Beschreibung | Inputs |
|-------------|--------------|--------|
| `calculate_dienstjahre` | Theoretisch erreichbare Dienstjahre (n) | eintritt, austritt, geburt |
| `calculate_avg_teilzeit` | Gewichteter Durchschnitt aus Zeiträumen | zeitraeume |
| `calculate_tarifgruppen_rente` | TechCorp: Tarifgruppen-basiert | zeitraeume, eintritt, austritt |

**Custom Functions:**

```python
# In 2_Formular.py
def calculate_my_custom_formula(data) -> float:
    """
    data ist ein dict-ähnliches Objekt mit:
    - data['eintrittsdatum']: str (ISO-Format)
    - data['austrittsdatum']: str
    - data['geburtsdatum']: str
    - data['zeitraeume']: list[dict]
    - data['_firma']: dict (Zugriff auf Versorgungsordnung)
    - data.get('field_id', default): Sichere Abfrage
    """
    firma = data.get('_firma')
    vo = firma['versorgungsordnung']
    parameter = vo.get('parameter', {})
    
    # ... Berechnung ...
    
    return round(result, 2)

# Registrieren
FUNCTIONS = {
    'calculate_my_custom_formula': calculate_my_custom_formula,
}
```

### Zeitraum-Aggregation

Für Berechnungen über Zeiträume:

```json
{
  "type": "zeitraum_aggregation",
  "aggregation": "gewichteter_durchschnitt",
  "field": "teilzeitfaktor",
  "zeitraeume_id": "zeitraeume"
}
```

**Aggregations-Typen:**

- `gewichteter_durchschnitt`: Durchschnitt gewichtet nach Zeitraum-Länge
- `summe`: Aufsummierung
- `minimum`: Niedrigster Wert
- `maximum`: Höchster Wert

---

## UI-Layout

### Modes

Definiert verschiedene Eingabe-Modi:

```json
{
  "ui_layout": {
    "modes": [
      {
        "id": "einfach",
        "label": "Einfache Eingabe",
        "description": "Schnelle Erfassung mit durchschnittlichem Teilzeitfaktor",
        "fields": [
          "eintrittsdatum",
          "austrittsdatum",
          "geburtsdatum",
          "mittlerer_teilzeitfaktor",
          "letztes_gehalt"
        ]
      },
      {
        "id": "zeitraum",
        "label": "Zeitraum-Details",
        "description": "Detaillierte Erfassung mit Zeitraumtabelle",
        "fields": [
          "eintrittsdatum",
          "austrittsdatum"
        ],
        "zeitraum_tabelle": {
          "enabled": true,
          "beginn": { ... },
          "ende": { ... },
          "spalten": [ ... ]
        }
      }
    ]
  }
}
```

**Wichtig:** Mit der aktuellen Implementierung werden Basis-Felder (category: "basis") **immer** angezeigt, unabhängig von Modes. Nur Personen- und Berechnungsfelder sind mode-spezifisch.

---

## Zeitraumtabelle

### Konfiguration

```json
{
  "zeitraum_tabelle": {
    "enabled": true,
    
    "beginn": {
      "type": "max",
      "werte": [
        {
          "type": "input",
          "input_id": "eintrittsdatum"
        },
        {
          "type": "parameter",
          "parameter_id": "stichtag"
        }
      ],
      "beschreibung": "Erfassungsbeginn"
    },
    
    "ende": {
      "type": "input",
      "input_id": "austrittsdatum",
      "beschreibung": "Erfassungsende"
    },
    
    "spalten": [ ... ]
  }
}
```

**Beginn/Ende Typen:**

| Type | Beschreibung | Beispiel |
|------|--------------|----------|
| `input` | Aus Eingabefeld | `{"type": "input", "input_id": "eintrittsdatum"}` |
| `parameter` | Aus VO-Parameter | `{"type": "parameter", "parameter_id": "stichtag"}` |
| `max` | Maximum mehrerer Werte | `{"type": "max", "werte": [...]}` |
| `min` | Minimum mehrerer Werte | `{"type": "min", "werte": [...]}` |

### Spalten-Definition

```json
{
  "spalten": [
    {
      "id": "von",
      "label": "Von",
      "type": "date"
    },
    {
      "id": "bis",
      "label": "Bis",
      "type": "date"
    },
    {
      "id": "als_dienstzeit",
      "label": "Als Dienstzeit",
      "type": "checkbox",
      "default": true,
      "always_visible": true,
      "help": "Für m/n-Regel anrechenbar?"
    },
    {
      "id": "ggf",
      "label": "GGF",
      "type": "checkbox",
      "default": false,
      "always_visible": true,
      "help": "Gesellschafter-Geschäftsführer (zählt nicht für m)"
    },
    {
      "id": "teilzeitfaktor",
      "label": "Teilzeitfaktor",
      "type": "slider",
      "min": 0.0,
      "max": 1.0,
      "default": 1.0,
      "step": 0.05,
      "always_visible": true
    },
    {
      "id": "tarifgruppe",
      "label": "TG",
      "type": "dropdown",
      "options": [
        {
          "value": "TG_A",
          "label": "TG A",
          "faktor": 1
        },
        {
          "value": "TG_B",
          "label": "TG B",
          "faktor": 2
        }
      ],
      "default": "TG_C",
      "always_visible": true
    },
    {
      "id": "bonus",
      "label": "Bonus %",
      "type": "number",
      "min": 0,
      "max": 100,
      "default": 0,
      "step": 5,
      "always_visible": false,
      "conditional": {
        "field": "tarifgruppe",
        "operator": "in",
        "value": ["TG_D", "TG_E"]
      },
      "help": "Zusätzlicher Bonus nur für TG D und E"
    }
  ]
}
```

**Spalten-Typen:**

| Type | Widget | Value | Beschreibung |
|------|--------|-------|--------------|
| `date` | Date Input | `"YYYY-MM-DD"` | Datum |
| `checkbox` | Checkbox | `true/false` | Boolean |
| `slider` | Text Input | `float` | Akzeptiert Dezimal oder Bruch |
| `number` | Number Input | `int/float` | Zahlenbereich |
| `dropdown` | Selectbox | `string` | Auswahl aus Optionen |

**Conditional Spalten:**

Spalten können basierend auf **anderen Spalten des gleichen Zeitraums** ein-/ausgeblendet werden:

```json
{
  "conditional": {
    "field": "tarifgruppe",
    "operator": "in",
    "value": ["TG_D", "TG_E"]
  }
}
```

**Verfügbare Operatoren:** `in`, `==`, `!=`, `>=`, `<=`, `>`, `<`

### Zeitraum-Datenstruktur

Intern wird jeder Zeitraum als Objekt gespeichert:

```json
{
  "von": "2010-01-01",
  "bis": "2015-12-31",
  "als_dienstzeit": true,
  "ggf": false,
  "teilzeitfaktor": 0.75,
  "tarifgruppe": "TG_C",
  "gehalt": 3500
}
```

Diese Struktur wird als `zeitraeume` Array an Formeln übergeben.

---

## Personen-Daten

### personen.json

```json
{
  "personen": [
    {
      "id": "person_001",
      "name": "Anna Schneider",
      "profil": "Senior Developer",
      "firma_id": "global_services",
      
      "daten": {
        "eintrittsdatum": "2005-09-01",
        "austrittsdatum": "2025-02-01",
        "geburtsdatum": "1975-06-15",
        "mittlerer_teilzeitfaktor": 1.0,
        "letztes_gehalt": 0
      },
      
      "overrides": {
        "dienstjahre": 35.0
      }
    }
  ]
}
```

**Felder:**

- **id**: Eindeutige Person-ID
- **name**: Anzeigename
- **profil**: Kurzbeschreibung (optional)
- **firma_id**: Referenz zu Firmen-JSON
- **daten**: Input-Feld-Werte
- **overrides**: Manuelle Überschreibungen von berechneten Werten

---

## Prüfungs-System (3x-Regel)

### pruefungen.json

Das globale Prüfungssystem speichert den Freigabestatus von Formeln **pro Firma**:

```json
{
  "acme_gmbh__dienstjahre": {
    "person_001": {
      "geprueft_am": "2026-02-18 10:23",
      "geprueft_von": "mueller"
    },
    "person_005": {
      "geprueft_am": "2026-02-18 11:15",
      "geprueft_von": "schmidt"
    },
    "person_009": {
      "geprueft_am": "2026-02-18 14:30",
      "geprueft_von": "weber"
    }
  },
  "acme_gmbh__grundrente_monatlich": {
    "person_001": {
      "geprueft_am": "2026-02-18 10:25",
      "geprueft_von": "mueller"
    }
  },
  "techcorp_ag__tarifgruppen_rente": {
    "person_010": {
      "geprueft_am": "2026-02-18 09:00",
      "geprueft_von": "mueller"
    }
  }
}
```

**Struktur:**

```
{
  "<firma_id>__<feld_id>": {
    "<person_id>": {
      "geprueft_am": "YYYY-MM-DD HH:MM",
      "geprueft_von": "sachbearbeiter_login"
    },
    ...
  }
}
```

**Schlüssel-Logik:**

- **Key:** `firma_id__feld_id` (z.B. `acme_gmbh__dienstjahre`)
- **Value:** Dictionary mit Prüfungen pro Person
- **Regel:** Wenn ≥3 verschiedene Personen geprüft haben → Formel freigegeben für diese Firma

**Wichtig:**

- Prüfungen sind **firmenbezogen**, nicht personenbezogen
- Jede Person kann pro Formel nur **einmal** prüfen (bei einem beliebigen AN)
- Nach 3 Prüfungen gilt die Formel für **alle AN dieser Firma**
- Andere Firmen haben separate Prüfungsstände

**Beispiel-Workflow:**

```python
# Laden
pruefungen = lade_pruefungen()

# Status prüfen
status = pruefstatus(
    pruefungen,
    firma_id="acme_gmbh",
    feld_id="dienstjahre",
    person_id="person_001",
    ist_override=False
)

# status = {
#   'valide': True,           # Darf verwendet werden
#   'grund': 'global_3x',     # 3+ Prüfungen
#   'anzahl': 3,              # Anzahl Prüfungen
#   'individuell': True       # Diese Person hat auch geprüft
# }

# Neue Prüfung registrieren
registriere_pruefung(
    pruefungen,
    firma_id="acme_gmbh",
    feld_id="grundrente_monatlich",
    person_id="person_005",
    wert=1102.50
)

# Speichern
speichere_pruefungen(pruefungen)
```

**Status-Werte:**

| Grund | Valide | Bedeutung |
|-------|--------|-----------|
| `override` | ✅ | Manuell überschrieben, keine Prüfung nötig |
| `global_3x` | ✅ | 3+ verschiedene AN haben die Formel geprüft |
| `individuell` | ✅ | Aktueller User hat bei diesem AN geprüft (aber <3 gesamt) |
| `ungeprueft` | ❌ | Noch nicht geprüft |

**Anti-Patterns vermeiden:**

```python
# ❌ FALSCH: Dieselbe Person mehrfach zählen lassen
for i in range(3):
    registriere_pruefung(pruefungen, "acme", "feld", "person_001", val)

# ✅ RICHTIG: Verschiedene Personen
registriere_pruefung(pruefungen, "acme", "feld", "person_001", val)
registriere_pruefung(pruefungen, "acme", "feld", "person_005", val)
registriere_pruefung(pruefungen, "acme", "feld", "person_009", val)
```

Die Funktion `registriere_pruefung` verhindert automatisch Mehrfachprüfungen derselben Person.

---

## Best Practices

### 1. ID-Namenskonventionen

```
Firmen:           snake_case       (acme_gmbh, techcorp_ag)
Felder:           snake_case       (eintrittsdatum, letztes_gehalt)
Personen:         person_NNN       (person_001, person_042)
Tarifgruppen:     TG_X             (TG_A, TG_B)
Enums:            UPPER_SNAKE      (TG_A, TG_E)
```

### 2. Formeln testen

Verwenden Sie den Berechnungs-Log für Debugging:

```python
def calculate_my_formula(data) -> float:
    # Debug-Output erscheint im UI
    evaluator.log.append(f"Debug: Wert X = {data['field_x']}")
    
    result = ...
    return result
```

### 3. Conditional Logic

**Input Fields:** Conditional basiert auf anderen **Eingabefeldern**
```json
{
  "conditional": {
    "field": "eintrittsdatum",
    "operator": ">=",
    "value": "2008-01-01"
  }
}
```

**Zeitraum-Spalten:** Conditional basiert auf **anderen Spalten des gleichen Zeitraums**
```json
{
  "conditional": {
    "field": "tarifgruppe",
    "operator": "in",
    "value": ["TG_D", "TG_E"]
  }
}
```

### 4. Default-Werte

Immer sinnvolle Defaults setzen:

```json
{
  "type": "checkbox",
  "default": true,      // ✅ Explizit
  
  "type": "slider",
  "default": 1.0,       // ✅ Vollzeit als Standard
  
  "type": "number",
  "default": 0.0        // ✅ Kein Gehalt als Fallback
}
```

### 5. Validierung

Min/Max-Werte für Plausibilität:

```json
{
  "type": "number",
  "min": 0.0,
  "max": 50000.0,      // ✅ Verhindert Tippfehler
  "step": 100.0
}
```

### 6. Help-Texte

Immer aussagekräftige Hilfe bereitstellen:

```json
{
  "help": "Nur bei Neu-Regelung (Eintritt ab 2008) erforderlich"
}
```

### 7. Versionierung

Dokumentieren Sie Änderungen:

```json
{
  "versorgungsordnung": {
    "name": "TechCorp Pensionsplan 2010 v2.1",
    "aenderungen": [
      {
        "datum": "2024-01-15",
        "beschreibung": "TG E Faktor von 8 auf 10 erhöht"
      }
    ]
  }
}
```

### 8. Zeitraum-Performance

Bei vielen Zeiträumen (>50) kann die Performance leiden. Optimierung:

```python
# Verwenden Sie Caching in Funktionen
@functools.lru_cache(maxsize=128)
def expensive_calculation(key):
    ...
```

---

## Beispiel: Neue Firma hinzufügen

### 1. Firmen-JSON erstellen

```json
{
  "firma": {
    "id": "neue_firma_gmbh",
    "name": "Neue Firma GmbH",
    "beschreibung": "Beschreibung"
  },
  "versorgungsordnung": {
    "name": "Pensionsplan 2015",
    "zusagedatum": "2015-01-01",
    "insolvenzdatum": "2024-12-31",
    "entgeltumwandlung": false,
    "parameter": {
      "regelaltersgrenze": 67
    }
  },
  "schema": {
    "input_fields": [
      {
        "id": "eintrittsdatum",
        "label": "Eintrittsdatum",
        "type": "date",
        "required": true,
        "category": "basis"
      },
      {
        "id": "austrittsdatum",
        "label": "Austrittsdatum",
        "type": "date",
        "required": true,
        "category": "basis"
      },
      {
        "id": "geburtsdatum",
        "label": "Geburtsdatum",
        "type": "date",
        "required": true,
        "category": "person"
      }
    ],
    "leistungsteile": [
      {
        "id": "dienstjahre",
        "label": "Dienstjahre",
        "art": "Berechnungsgrundlage",
        "einheit": "Jahre",
        "formula": {
          "type": "function",
          "function_id": "calculate_dienstjahre"
        }
      },
      {
        "id": "rente_monatlich",
        "label": "Rente monatlich",
        "art": "Altersrente",
        "einheit": "EUR/Monat",
        "formula": {
          "type": "expression",
          "expression": "dienstjahre * 50"
        }
      }
    ],
    "ui_layout": {
      "modes": [
        {
          "id": "einfach",
          "label": "Eingabe",
          "fields": [
            "eintrittsdatum",
            "austrittsdatum",
            "geburtsdatum"
          ]
        }
      ]
    }
  }
}
```

### 2. Datei speichern

```
/firmen/neue_firma_gmbh.json
```

### 3. Im Code laden

Die Firma erscheint automatisch im Dropdown, wenn die Datei im `/firmen/`-Verzeichnis liegt.

---

## Fehlerbehandlung

### JSON-Validierung

Bei ungültigen JSON-Strukturen:

```python
try:
    with open(firma_pfad) as f:
        firma = json.load(f)
except json.JSONDecodeError as e:
    st.error(f"Fehler in {firma_pfad}: {e}")
```

### Missing Fields

```python
# Sichere Abfrage mit Defaults
regelalter = vo.get('parameter', {}).get('regelaltersgrenze', 67)

# Oder explizit prüfen
if 'insolvenzdatum' not in vo:
    st.warning("Kein Insolvenzdatum definiert")
```

### Formula Errors

```python
try:
    result = evaluator.get_value('feldname')
except Exception as e:
    st.error(f"Fehler bei Berechnung: {e}")
    evaluator.log.append(f"ERROR: {e}")
```

---

## API-Referenz

### Evaluator-Methoden

```python
# Wert setzen
evaluator.set_input(field_id: str, value: Any)

# Wert abrufen (cached)
result = evaluator.get_value(field_id: str) -> Any

# Override setzen
evaluator.override(field_id: str, value: Any)

# Override löschen
evaluator.clear_override(field_id: str)

# Alle Overrides löschen
evaluator.clear_all_overrides()

# Cache leeren
evaluator.cache.clear()

# Fehlende Felder
missing = evaluator.get_missing_inputs(input_fields: list) -> list
```

### LazyDataProxy

Wird an Formeln übergeben:

```python
def calculate_formula(data) -> float:
    # Dict-ähnlicher Zugriff
    eintritt = data['eintrittsdatum']      # KeyError wenn nicht vorhanden
    gehalt = data.get('letztes_gehalt', 0) # Sicher mit Default
    
    # Spezielle Keys
    firma = data['_firma']                  # Firmen-Objekt
    vo = data['_versorgungsordnung']        # Versorgungsordnung direkt
    
    # Zeiträume
    zeitraeume = data.get('zeitraeume', [])
```

---

## Changelog

### Version 1.0 (2026-02-18)

- Initiale Dokumentation
- Support für dropdown, number, slider, checkbox, date
- Conditional Logic für Input Fields und Zeitraum-Spalten
- Tarifgruppen-System (TechCorp)
- m/n-Regel mit GGF-Ausschluss
- Teilzeitfaktor mit Bruch-Eingabe (22/38)

---

---

**Letzte Aktualisierung:** 18.02.2026  
**Version:** 1.0

