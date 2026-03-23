# PSVaG Formular - Deployment & Sharing

**Version:** 1.0  
**Datum:** 2026-02-18

---

## 📋 Übersicht

Es gibt verschiedene Möglichkeiten, das Formular mit Kollegen zu teilen:

| Methode | Geeignet für | Setup-Zeit | Kosten |
|---------|--------------|------------|--------|
| **Streamlit Cloud** | Kleine Teams (2-5 Personen) | 10 Min | Kostenlos |
| **Shared Network Drive** | Teams im gleichen Netzwerk | 5 Min | - |
| **Interner Server** | Größere Teams, Produktiv | 30-60 Min | Hardware |
| **Docker Container** | IT-gestützter Betrieb | 20 Min | Hardware |

---

## 🚀 Option 1: Streamlit Cloud (Empfohlen für Start)

**Vorteile:**
- ✅ Schnellster Start
- ✅ Von überall erreichbar
- ✅ Automatische Updates
- ✅ HTTPS gesichert

**Nachteile:**
- ⚠️ Daten liegen in der Cloud (DSGVO beachten!)
- ⚠️ Kostenloser Plan: begrenzte Ressourcen

### Schritt-für-Schritt

#### 1. Repository erstellen

```bash
# Lokale Projekt-Struktur erstellen
mkdir psvag-formular
cd psvag-formular

# Dateien kopieren
cp -r /mnt/user-data/outputs/pages .
cp -r /mnt/user-data/outputs/firmen .
mkdir personen
cp /mnt/user-data/outputs/personen/personen.json personen/

# Leere pruefungen.json erstellen
echo '{}' > pruefungen.json
```

#### 2. requirements.txt erstellen

```bash
cat > requirements.txt << 'EOF'
streamlit==1.31.0
EOF
```

#### 3. .streamlit/config.toml (optional)

```bash
mkdir .streamlit
cat > .streamlit/config.toml << 'EOF'
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"

[server]
headless = true
EOF
```

#### 4. Git Repository initialisieren

```bash
git init
git add .
git commit -m "Initial commit"

# GitHub Repository erstellen (github.com)
# Dann:
git remote add origin https://github.com/IHR_USERNAME/psvag-formular.git
git push -u origin main
```

#### 5. Streamlit Cloud Deployment

1. Gehe zu https://share.streamlit.io
2. Melde dich mit GitHub an
3. Klicke "New app"
4. Wähle dein Repository
5. Main file: `pages/1_Auswahl.py`
6. Deploy!

**Fertig!** Link teilen: `https://IHR_USERNAME-psvag-formular.streamlit.app`

---

## 🏢 Option 2: Shared Network Drive

**Geeignet für:** Teams im gleichen Büro/Netzwerk

**Vorteile:**
- ✅ Sehr einfach
- ✅ Alle arbeiten auf denselben Daten
- ✅ Keine Cloud

**Nachteile:**
- ⚠️ Jeder muss Python/Streamlit installieren
- ⚠️ Nur im Netzwerk erreichbar
- ⚠️ Gleichzeitige Zugriffe können Probleme machen

### Setup

#### 1. Netzlaufwerk einrichten

```
Z:\psvag-formular\
├── pages\
│   ├── 1_Auswahl.py
│   └── 2_Formular.py
├── firmen\
│   ├── acme_gmbh.json
│   ├── techcorp_ag.json
│   └── global_services.json
├── personen\
│   └── personen.json
└── pruefungen.json
```

#### 2. Startskript für Kollegen

**Windows (start.bat):**
```batch
@echo off
cd /d Z:\psvag-formular
python -m streamlit run pages\1_Auswahl.py
pause
```

**Mac/Linux (start.sh):**
```bash
#!/bin/bash
cd /Volumes/psvag-formular
streamlit run pages/1_Auswahl.py
```

#### 3. Kollegen-Installation

```bash
# Python installieren (python.org)
# Dann:
pip install streamlit

# Startskript ausführen
# → Browser öffnet automatisch
```

**Wichtig:** Bei gleichzeitigen Schreibzugriffen können Konflikte auftreten!

---

## 🖥️ Option 3: Interner Server (Produktiv)

**Geeignet für:** Produktivbetrieb, mehrere gleichzeitige Nutzer

**Vorteile:**
- ✅ Zentral gehostet
- ✅ Alle greifen auf denselben Server zu
- ✅ Professionell
- ✅ Datenschutz-konform (on-premise)

**Nachteile:**
- ⚠️ Benötigt Server/IT-Unterstützung
- ⚠️ Wartungsaufwand

### Setup

#### 1. Server vorbereiten (Linux)

```bash
# Ubuntu/Debian Server
sudo apt update
sudo apt install python3 python3-pip nginx

# Benutzer erstellen
sudo useradd -m -s /bin/bash psvag
sudo su - psvag
```

#### 2. Anwendung installieren

```bash
cd /home/psvag
git clone https://github.com/IHR_REPO/psvag-formular.git
cd psvag-formular

python3 -m venv venv
source venv/bin/activate
pip install streamlit
```

#### 3. Systemd Service einrichten

```bash
sudo nano /etc/systemd/system/psvag.service
```

```ini
[Unit]
Description=PSVaG Formular
After=network.target

[Service]
Type=simple
User=psvag
WorkingDirectory=/home/psvag/psvag-formular
ExecStart=/home/psvag/psvag-formular/venv/bin/streamlit run pages/1_Auswahl.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable psvag
sudo systemctl start psvag
```

#### 4. Nginx Reverse Proxy (optional)

```nginx
# /etc/nginx/sites-available/psvag
server {
    listen 80;
    server_name psvag.ihre-firma.de;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/psvag /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

**Zugriff:** http://psvag.ihre-firma.de

---

## 🐳 Option 4: Docker Container

**Geeignet für:** IT-gestützten Betrieb, einfaches Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pages ./pages
COPY firmen ./firmen
COPY personen ./personen
COPY pruefungen.json .

EXPOSE 8501

CMD ["streamlit", "run", "pages/1_Auswahl.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  psvag:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./firmen:/app/firmen
      - ./personen:/app/personen
      - ./pruefungen.json:/app/pruefungen.json
    restart: unless-stopped
```

### Starten

```bash
docker-compose up -d
```

**Zugriff:** http://SERVER_IP:8501

---

## 📦 Daten-Management

### Gemeinsame Datenhaltung

**Problem:** Mehrere Nutzer müssen auf dieselben Daten zugreifen.

**Lösungen:**

#### A) Shared Files (Einfach)

Alle greifen auf dieselben JSON-Dateien zu:
- ✅ Einfach
- ⚠️ Race Conditions bei gleichzeitigen Schreibzugriffen

**Aktueller Stand:** Das System verwendet File-Locks nicht → nur für sequentielle Nutzung geeignet!

#### B) Datenbank (Zukunft)

Migration zu SQLite/PostgreSQL:
- ✅ Gleichzeitige Zugriffe möglich
- ✅ Transaktionen
- ⚠️ Benötigt Code-Anpassungen

---

## 🔐 Sicherheit & Zugriffskontrolle

### Aktueller Stand

**Keine Authentifizierung!** Jeder mit Zugriff kann:
- Alle Daten sehen
- Alle Daten ändern
- Prüfungen durchführen

### Empfehlungen

#### 1. Netzwerk-Ebene (Kurzfristig)

```bash
# Streamlit nur für internes Netz
streamlit run pages/1_Auswahl.py --server.address 192.168.1.100
```

#### 2. Reverse Proxy mit Auth (Mittelfristig)

Nginx mit HTTP Basic Auth:
```nginx
location / {
    auth_basic "PSVaG Zugang";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8501;
}
```

```bash
sudo htpasswd -c /etc/nginx/.htpasswd mueller
sudo htpasswd /etc/nginx/.htpasswd schmidt
```

#### 3. Streamlit Auth (Langfristig)

Erweiterung mit Streamlit-Authenticator:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Formular anzeigen
    ...
else:
    st.error('Username/password is incorrect')
```

---

## 🔄 Updates verteilen

### Streamlit Cloud

```bash
git add .
git commit -m "Update"
git push

# → Automatisches Deployment
```

### Shared Drive

```bash
# Neue Version auf Netzlaufwerk kopieren
# Kollegen müssen Browser neu laden
```

### Server

```bash
ssh user@server
cd /home/psvag/psvag-formular
git pull
sudo systemctl restart psvag
```

---

## 📊 Backup-Strategie

### Was muss gesichert werden?

| Datei | Wichtigkeit | Änderungshäufigkeit |
|-------|-------------|---------------------|
| `firmen/*.json` | Hoch | Selten (VO-Änderungen) |
| `personen/personen.json` | Hoch | Mittel (neue AN) |
| `pruefungen.json` | **Kritisch** | Hoch (täglich) |

### Backup-Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/psvag"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR/$DATE"

cp pruefungen.json "$BACKUP_DIR/$DATE/"
cp -r firmen "$BACKUP_DIR/$DATE/"
cp -r personen "$BACKUP_DIR/$DATE/"

# Alte Backups löschen (älter als 30 Tage)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "Backup erstellt: $BACKUP_DIR/$DATE"
```

**Cron-Job (täglich um 2 Uhr):**
```bash
0 2 * * * /home/psvag/backup.sh
```

---

## 🐛 Troubleshooting

### "Module not found: streamlit"

```bash
pip install streamlit
```

### "Address already in use"

```bash
# Port 8501 belegt - anderen Port verwenden
streamlit run pages/1_Auswahl.py --server.port 8502
```

### "Permission denied" bei pruefungen.json

```bash
chmod 666 pruefungen.json
```

### Gleichzeitige Zugriffe → Daten überschrieben

**Problem:** JSON-Dateien unterstützen keine Transaktionen.

**Lösung (kurzfristig):** Organisatorisch regeln (z.B. nur eine Person ändert Daten)

**Lösung (langfristig):** Migration zu Datenbank

---

## 📞 Checkliste: Kollegen onboarden

- [ ] Zugang einrichten (Cloud-Link / Netzlaufwerk / Server-Zugang)
- [ ] Benutzerhandbuch teilen (`BENUTZERHANDBUCH.md`)
- [ ] QS-Regel erklären (`3X_PRUEFEN_REGEL.md`)
- [ ] Testdatensatz anlegen zum Üben
- [ ] Erste Prüfung gemeinsam durchgehen
- [ ] Backup-Verantwortlichkeiten klären

---

**Letzte Aktualisierung:** 18.02.2026  
**Version:** 1.0
