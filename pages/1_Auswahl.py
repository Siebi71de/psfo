#!/usr/bin/env python3
"""
Seite 1: Auswahl von Firma und Person
Nutzt modulare Firmen-Struktur
"""

import streamlit as st
import json
from pathlib import Path

# ============================================================
# SEITEN-TITEL
# ============================================================

st.title("Auswahl: Firma & Person")
st.markdown("---")

# ============================================================
# DATEN LADEN
# ============================================================

@st.cache_data
def load_json(filename: str):
    path = Path(__file__).parent.parent / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Lade Index
try:
    firmen_index = load_json('firmen_index.json')
except Exception as e:
    st.error(f"Fehler beim Laden des Firmen-Index: {e}")
    st.stop()

# ============================================================
# FIRMA AUSWÄHLEN
# ============================================================

st.subheader("1. Firma auswählen")

# Erstelle Firma-Optionen
firma_optionen = [(f['id'], f['name']) for f in firmen_index['firmen']]
firma_namen = [name for _, name in firma_optionen]

# Finde aktuellen Index
current_index = 0
if st.session_state.get('firma_id'):
    for i, (fid, _) in enumerate(firma_optionen):
        if fid == st.session_state.firma_id:
            current_index = i
            break

# Selectbox
selected_firma_name = st.selectbox(
    "Wählen Sie eine Firma:",
    options=firma_namen,
    index=current_index,
    key="firma_select"
)

# Finde ID und Config-File
selected_firma_id = None
selected_config_file = None
for firma_info in firmen_index['firmen']:
    if firma_info['name'] == selected_firma_name:
        selected_firma_id = firma_info['id']
        selected_config_file = firma_info['config_file']
        break

# Lade Firma-Config
if selected_firma_id and selected_config_file:
    try:
        firma_config = load_json(selected_config_file)
        firma = firma_config['firma']
        versorgungsordnung = firma_config['versorgungsordnung']
        personen = firma_config.get('personen', [])
        
        # Speichere in Session State
        st.session_state.firma_config = firma_config
        st.session_state.firma_id = selected_firma_id
        
        # Firma-Details
        with st.expander(f"Details: {firma['name']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Beschreibung**")
                st.info(firma.get('beschreibung', 'Keine Beschreibung'))
                
            with col2:
                st.markdown("**Versorgungsordnung**")
                st.markdown(f"- {versorgungsordnung['name']}")
                st.markdown(f"- Regelung: **{versorgungsordnung['regelung'].upper()}**")
                
                if 'parameter' in versorgungsordnung:
                    params = versorgungsordnung['parameter']
                    if 'satz_pro_jahr' in params:
                        st.markdown(f"- Satz: **{params['satz_pro_jahr']} EUR/Jahr**")
                    if 'prozentsatz' in params:
                        st.markdown(f"- Prozentsatz: **{params['prozentsatz']*100}%**")
    
    except Exception as e:
        st.error(f"Fehler beim Laden der Firma-Config: {e}")
        personen = []

st.markdown("---")

# ============================================================
# PERSON AUSWÄHLEN
# ============================================================

st.subheader("2. Person auswählen")

if selected_firma_id and personen:
    # Erstelle Person-Optionen
    person_optionen = [(p['id'], f"{p['name']} - {p['profil']}") for p in personen]
    person_namen = [name for _, name in person_optionen]
    
    # Finde aktuellen Index
    current_person_index = 0
    if st.session_state.get('person_id'):
        for i, (pid, _) in enumerate(person_optionen):
            if pid == st.session_state.person_id:
                current_person_index = i
                break
    
    # Selectbox
    selected_person_name = st.selectbox(
        "Wählen Sie eine Person:",
        options=person_namen,
        index=current_person_index,
        key="person_select"
    )
    
    # Finde Person
    selected_person_id = None
    selected_person = None
    for pid, pname in person_optionen:
        if pname == selected_person_name:
            selected_person_id = pid
            selected_person = next(p for p in personen if p['id'] == pid)
            break
    
    # Speichere in Session State
    if selected_person_id:
        st.session_state.person_id = selected_person_id
        
        # Person-Details
        with st.expander(f"Details: {selected_person['name']}", expanded=False):
            st.markdown(f"**Profil:** {selected_person['profil']}")
            st.markdown(f"**Hinweise:** {selected_person.get('notizen', 'Keine')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Vorhandene Daten**")
                if selected_person.get('daten'):
                    for key, value in selected_person['daten'].items():
                        if isinstance(value, list):
                            st.markdown(f"- {key}: [{len(value)} Werte]")
                        else:
                            st.markdown(f"- {key}: {value}")
                else:
                    st.warning("Keine Daten vorhanden")
            
            with col2:
                st.markdown("**Overrides**")
                if selected_person.get('overrides'):
                    for key, value in selected_person['overrides'].items():
                        st.markdown(f"- {key}: {value} (manuell)")
                else:
                    st.info("Keine Overrides")

elif selected_firma_id and not personen:
    st.warning(f"Keine Personen für {firma['name']} gefunden")
else:
    st.info("Bitte zuerst eine Firma auswählen")

# ============================================================
# STATUS & NAVIGATION
# ============================================================

st.markdown("---")

if st.session_state.get('firma_id') and st.session_state.get('person_id'):
    st.success(f"""
    **Auswahl gespeichert:**
    - Firma: {selected_firma_name}
    - Person: {selected_person['name']}
    """)
    
    st.info("Navigieren Sie nun zur Seite 'Formular' um die Berechnung durchzuführen")
    
    # Reset-Button
    if st.button("Auswahl zurücksetzen", use_container_width=True):
        st.session_state.firma_id = None
        st.session_state.person_id = None
        st.session_state.firma_config = None
        st.session_state.evaluator = None
        st.session_state.zeitraeume = None
        st.rerun()
