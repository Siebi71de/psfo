# PSVaG Leistungsverwaltung

Streamlit-basiertes Formularsystem für die Berechnung von Betriebsrentenansprüchen im Insolvenzfall.

## 🚀 Deployment auf Streamlit Cloud

1. Dieses Verzeichnis zu GitHub hochladen:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/IHR_USERNAME/psvag-formular.git
   git push -u origin main
   ```

2. Zu https://share.streamlit.io gehen
3. "Sign in with GitHub"
4. "New app" klicken
5. Repository auswählen
6. Main file: `pages/1_Auswahl.py`
7. Deploy!

## 💻 Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run pages/1_Auswahl.py
```

## 📁 Struktur

```
psvag-formular/
├── pages/
│   ├── 1_Auswahl.py          # Firmen- und Personenauswahl
│   └── 2_Formular.py          # Hauptformular mit Berechnungen
├── firmen/                    # Versorgungsordnungen
│   ├── acme_gmbh.json
│   ├── techcorp_ag.json
│   └── global_services.json
├── personen/
│   └── personen.json          # Mitarbeiterdaten
├── pruefungen.json            # Qualitätssicherungs-Status
└── requirements.txt

```

## 📚 Features

- **3x-Prüfen-Regel** mit wertabhängiger Qualitätssicherung
- **Zeitraumtabelle** mit Split/Merge-Funktionalität
- **m/n-Regel** nach § 2 BetrAVG
- **Unverfallbarkeitsprüfung** nach § 1b BetrAVG
- **Tarifgruppen-System** (TechCorp)
- **Override-Funktionen** für Sonderfälle
- **Abhängigkeits-Tracking** bei Eingabeänderungen

## 🔐 Hinweis

Das System enthält aktuell **keine Authentifizierung**. Für Produktivbetrieb sollte:
- Zugriff über Firewall beschränkt werden ODER
- Reverse Proxy mit Authentication verwendet werden

## 📖 Dokumentation

Siehe Dateien im Repository:
- `BENUTZERHANDBUCH.md` - Anleitung für Endanwender
- `JSON_SCHNITTSTELLEN.md` - Technische Dokumentation
- `3X_PRUEFEN_REGEL.md` - Qualitätssicherung
- `DEPLOYMENT.md` - Deployment-Optionen

## 📝 Version

1.0 - Initial Release (2026-02-18)
