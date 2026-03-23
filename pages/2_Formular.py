#!/usr/bin/env python3
"""
Seite 2: Interaktives Formular mit Zeitraum-Tabelle
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Any, Optional

# ============================================================
# LAZY EVALUATOR
# ============================================================

class LazyEvaluator:
    def __init__(self, schema: Dict, functions: Dict):
        self.schema = schema
        self.functions = functions
        self.cache = {}
        self.input_data = {}
        self.overrides = {}
        self.computing = set()
        self.log = []
        self.firma = None
    
    def get_value(self, field_id: str) -> Any:
        if field_id in self.overrides:
            self.log.append(f"{field_id} = {self.overrides[field_id]} (Override)")
            return self.overrides[field_id]
        
        if field_id in self.cache:
            return self.cache[field_id]
        
        if field_id in self.input_data:
            return self.input_data[field_id]
        
        if field_id in self.computing:
            raise ValueError(f"Zirkuläre Abhängigkeit: {field_id}")
        
        field_def = self._find_field(field_id)
        if not field_def:
            raise ValueError(f"Feld '{field_id}' nicht definiert!")
        
        self.computing.add(field_id)
        self.log.append(f"Berechne {field_id}...")
        
        try:
            value = self._evaluate_field(field_def)
            self.cache[field_id] = value
            self.log.append(f"{field_id} = {value}")
            return value
        finally:
            self.computing.discard(field_id)
    
    def _evaluate_field(self, field_def: Dict) -> Any:
        formula = field_def.get('formula', {})
        formula_type = formula.get('type')
        
        if formula_type == 'zeitraum_aggregation':
            # Zeitraum-basierte Aggregation
            return self._evaluate_zeitraum_aggregation(formula)
        
        elif formula_type == 'function':
            func_id = formula['function_id']
            data_proxy = LazyDataProxy(self, field_def['id'])
            func = self.functions[func_id]
            return func(data_proxy)
        
        elif formula_type == 'constant':
            # Konstanter Wert
            return formula.get('value', 0)
        
        elif formula_type == 'expression':
            # Expression mit variables und parameters
            expression = formula['expression']
            variables = formula.get('variables', [])
            parameters = formula.get('parameters', [])
            
            # Sammle Daten
            data = {}
            
            # Hole variables aus input_data
            for var in variables:
                data[var] = self.get_value(var)
            
            # Hole parameters aus versorgungsordnung
            if self.firma and 'versorgungsordnung' in self.firma:
                vo_params = self.firma['versorgungsordnung'].get('parameter', {})
                for param in parameters:
                    if param in vo_params:
                        data[param] = vo_params[param]
                    else:
                        # Fallback für stichtag
                        if param == 'stichtag' and 'stichtag' in self.firma['versorgungsordnung']:
                            data[param] = self.firma['versorgungsordnung']['stichtag']
            
            # Evaluiere Expression
            return eval(expression, {"__builtins__": {}}, data)
        
        elif formula_type == 'conditional':
            # Conditional: if condition then if_true else if_false
            condition = formula['condition']
            
            # Hole condition variable und parameter
            var_name = condition['variable']
            operator = condition['operator']
            param_name = condition.get('parameter')
            
            # Hole Werte
            var_value = self.get_value(var_name)
            
            if param_name:
                # Parameter aus versorgungsordnung
                if self.firma and 'versorgungsordnung' in self.firma:
                    param_value = self.firma['versorgungsordnung'].get(param_name)
                    if param_value is None:
                        param_value = self.firma['versorgungsordnung'].get('parameter', {}).get(param_name)
                else:
                    param_value = condition.get('value')
            else:
                param_value = condition.get('value')
            
            # Evaluiere Bedingung
            condition_result = False
            if operator == '<':
                condition_result = var_value < param_value
            elif operator == '<=':
                condition_result = var_value <= param_value
            elif operator == '>':
                condition_result = var_value > param_value
            elif operator == '>=':
                condition_result = var_value >= param_value
            elif operator == '==':
                condition_result = var_value == param_value
            elif operator == '!=':
                condition_result = var_value != param_value
            
            # Evaluiere entsprechenden Branch
            if condition_result:
                branch_formula = formula['if_true']
            else:
                branch_formula = formula['if_false']
            
            # Rekursiv evaluieren
            return self._evaluate_field({'formula': branch_formula})
        
        elif formula_type == 'input':
            # Direkter Input
            input_id = formula['input_id']
            return self.get_value(input_id)
        
        else:
            raise ValueError(f"Unknown formula type: {formula_type}")
    
    def _evaluate_zeitraum_aggregation(self, formula: Dict) -> Any:
        """Evaluiert Zeitraum-Aggregationen basierend auf Schema"""
        quelle = formula.get('quelle', 'zeitraeume')
        aggregation = formula.get('aggregation')
        
        # Hole Zeiträume
        if quelle not in self.input_data:
            # Fallback-Funktion verwenden
            if 'fallback' in formula:
                return self._evaluate_field({'formula': formula['fallback']})
            raise ValueError(f"{quelle} nicht vorhanden")
        
        zeitraeume = self.input_data[quelle]
        if not zeitraeume:
            if 'fallback' in formula:
                return self._evaluate_field({'formula': formula['fallback']})
            raise ValueError(f"{quelle} ist leer")
        
        # Filter anwenden
        if 'filter' in formula:
            zeitraeume = self._filter_zeitraeume(zeitraeume, formula['filter'])
        
        # Aggregation durchführen
        if aggregation == 'summe_tage_als_jahre':
            return self._agg_summe_tage_als_jahre(zeitraeume)
        
        elif aggregation == 'gewichteter_durchschnitt':
            feld = formula.get('feld')
            gewicht = formula.get('gewicht', 'tage')
            return self._agg_gewichteter_durchschnitt(zeitraeume, feld, gewicht)
        
        elif aggregation == 'letzter_wert':
            feld = formula.get('feld')
            return self._agg_letzter_wert(zeitraeume, feld)
        
        elif aggregation == 'erster_wert':
            feld = formula.get('feld')
            return self._agg_erster_wert(zeitraeume, feld)
        
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
    
    def _filter_zeitraeume(self, zeitraeume, filter_def):
        """Filtert Zeiträume basierend auf Filter-Definition"""
        feld = filter_def.get('feld')
        operator = filter_def.get('operator', '==')
        wert = filter_def.get('wert')
        
        result = []
        for zr in zeitraeume:
            if feld not in zr:
                continue
            
            zr_wert = zr[feld]
            
            if operator == '==' or operator == '=':
                if zr_wert == wert:
                    result.append(zr)
            elif operator == '>':
                if zr_wert > wert:
                    result.append(zr)
            elif operator == '<':
                if zr_wert < wert:
                    result.append(zr)
            elif operator == '>=':
                if zr_wert >= wert:
                    result.append(zr)
            elif operator == '<=':
                if zr_wert <= wert:
                    result.append(zr)
        
        return result
    
    def _agg_summe_tage_als_jahre(self, zeitraeume):
        """Summiert Tage und konvertiert zu Jahren"""
        from datetime import date
        total_tage = 0
        for zr in zeitraeume:
            von = date.fromisoformat(zr['von'])
            bis = date.fromisoformat(zr['bis'])
            total_tage += (bis - von).days + 1
        return int(total_tage / 365.25)
    
    def _agg_gewichteter_durchschnitt(self, zeitraeume, feld, gewicht_typ):
        """Berechnet gewichteten Durchschnitt"""
        from datetime import date
        total_gewicht = 0
        weighted_sum = 0
        
        for zr in zeitraeume:
            if gewicht_typ == 'tage':
                von = date.fromisoformat(zr['von'])
                bis = date.fromisoformat(zr['bis'])
                gewicht = (bis - von).days + 1
            else:
                gewicht = zr.get(gewicht_typ, 1)
            
            wert = zr.get(feld, 0)
            weighted_sum += wert * gewicht
            total_gewicht += gewicht
        
        return weighted_sum / total_gewicht if total_gewicht > 0 else 0
    
    def _agg_letzter_wert(self, zeitraeume, feld):
        """Gibt letzten nicht-null Wert zurück"""
        for zr in reversed(zeitraeume):
            wert = zr.get(feld)
            if wert is not None and wert != 0:
                return wert
        return 0
    
    def _agg_erster_wert(self, zeitraeume, feld):
        """Gibt ersten nicht-null Wert zurück"""
        for zr in zeitraeume:
            wert = zr.get(feld)
            if wert is not None and wert != 0:
                return wert
        return 0
    
    def _find_field(self, field_id: str) -> Optional[Dict]:
        # Suche erst in leistungsteile
        for field in self.schema.get('leistungsteile', []):
            if field['id'] == field_id:
                return field
        # Fallback: calculated_fields (Legacy)
        for field in self.schema.get('calculated_fields', []):
            if field['id'] == field_id:
                return field
        return None
    
    def set_input(self, field_id: str, value: Any):
        # Prüfe ob sich der Wert tatsächlich geändert hat
        alt = self.input_data.get(field_id)
        if alt != value:
            self.input_data[field_id] = value
            self.cache.clear()
            
            # Bei Datumswechsel: zeitraeume invalidieren
            if field_id in ['eintrittsdatum', 'austrittsdatum', 'geburtsdatum']:
                self.input_data.pop('zeitraeume', None)
                # session_state Marker löschen
                import streamlit as st
                for key in ['zeitraeume', 'zeitraeume_beginn', 'zeitraeume_ende', 
                           'zeitraeume_eintritt', 'zeitraeume_austritt']:
                    st.session_state.pop(key, None)
            
            # Markiere dass sich Eingaben geändert haben (für Override-Warnung)
            if not hasattr(self, 'input_changed'):
                self.input_changed = set()
            self.input_changed.add(field_id)
        else:
            self.input_data[field_id] = value
    
    def clear_all_overrides(self):
        """Löscht alle Overrides, Cache und zugehörige Widget-States."""
        self.overrides.clear()
        self.cache.clear()
        if hasattr(self, 'input_changed'):
            self.input_changed.clear()
        
        # Session-State Widget-Keys für Overrides löschen
        import streamlit as st
        for key in list(st.session_state.keys()):
            if key.startswith('ovr_check_') or key.startswith('ovr_val_'):
                del st.session_state[key]
    
    def get_missing_inputs(self, input_fields: list) -> list:
        """Gibt Liste der Felder zurück, die benötigt aber noch nicht befüllt sind."""
        missing = []
        for field in input_fields:
            fid = field['id']
            # Bereits vorhanden und befüllt?
            if fid in self.input_data and self.input_data[fid] not in (None, '', 0.0):
                continue
            if fid in self.overrides:
                continue
            # Conditional: Feld nur relevant wenn Bedingung erfüllt
            if field.get('conditional'):
                cond = field['conditional']
                cond_val = self.input_data.get(cond['field'])
                if cond_val is None:
                    continue  # Bedingungsfeld fehlt → überspringen
                op  = cond['operator']
                ref = cond['value']
                visible = False
                if op == '>=': visible = cond_val >= ref
                elif op == '<=': visible = cond_val <= ref
                elif op == '>':  visible = cond_val > ref
                elif op == '<':  visible = cond_val < ref
                elif op == '==': visible = cond_val == ref
                elif op == '!=': visible = cond_val != ref
                if not visible:
                    continue  # Bedingung nicht erfüllt → Feld nicht benötigt
            # Nur wenn required
            if field.get('required'):
                missing.append(field)
        return missing
    
    def override(self, field_id: str, value: Any):
        self.overrides[field_id] = value
        self.cache.clear()
    
    def clear_override(self, field_id: str):
        if field_id in self.overrides:
            del self.overrides[field_id]
            self.cache.clear()
    
    def get_log(self):
        return self.log


class LazyDataProxy:
    def __init__(self, evaluator, field_id):
        self._evaluator = evaluator
        self._field_id = field_id
    
    def __getitem__(self, key):
        if key == '_firma':
            return self._evaluator.firma if hasattr(self._evaluator, 'firma') else None
        if key == '_versorgungsordnung':
            return self._evaluator.firma['versorgungsordnung'] if hasattr(self._evaluator, 'firma') else None
        return self._evaluator.get_value(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except Exception:
            return default


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def jahre_zwischen(von: date, bis: date) -> float:
    """
    Berechnet Jahre zwischen zwei Daten präzise:
    1. Volle Jahre zählen
    2. Resttage als Bruchteil von 365.25
    Beispiel: 2005-09-01 bis 2042-06-01
      → 36 volle Jahre (2005-09-01 bis 2041-09-01)
      → + 273 Tage (2041-09-01 bis 2042-06-01)
      → = 36 + 273/365.25 = 36,75 Jahre
    """
    if bis < von:
        return 0.0
    
    # Volle Jahre
    volle_jahre = bis.year - von.year
    # Jahrestag im Zieljahr
    jahrestag = date(bis.year, von.month, von.day)
    
    # Wenn noch nicht erreicht → ein Jahr abziehen
    if bis < jahrestag:
        volle_jahre -= 1
        jahrestag = date(bis.year - 1, von.month, von.day)
    
    # Resttage ab letztem Jahrestag
    resttage = (bis - jahrestag).days
    
    return round(volle_jahre + resttage / 365.25, 2)


# ============================================================
# INSOLVENZ: EFFEKTIVES AUSTRITTSDATUM
# ============================================================

def effektives_austrittsdatum(versorgungsordnung, austrittsdatum_str):
    """
    Effektives Austrittsdatum = min(eingegebenes Austrittsdatum, Insolvenzdatum).
    Gibt (datum_str, insolvenzfall: bool) zurück.
    """
    insolvenzdatum_str = versorgungsordnung.get('insolvenzdatum')
    if not insolvenzdatum_str:
        return austrittsdatum_str, False
    
    if insolvenzdatum_str < austrittsdatum_str:
        return insolvenzdatum_str, True
    return austrittsdatum_str, False


# ============================================================
# GESETZLICHER RENTENBEGINN (§ 235 SGB VI)
# ============================================================

def gesetzlicher_rentenbeginn(geburtsdatum_str, zum_zeitpunkt_str=None):
    """
    Gesetzliche Regelaltersgrenze nach § 235 SGB VI — maßgeblich sind die
    Regelungen zum angegebenen Zeitpunkt (Veränderungssperre).

    Rechtsänderungen:
      - Vor 20.04.2007 (RV-Altersgrenzenanpassungsgesetz): einheitlich 65 Jahre
      - Ab 20.04.2007: stufenweise Anhebung auf 67 Jahre (§ 235 Abs. 2 SGB VI)

    zum_zeitpunkt_str: Insolvenzdatum oder aktuelles Datum — bestimmt welche
                       Rechtslage gilt (Veränderungssperre).
    """
    from datetime import date as _date

    geb = _date.fromisoformat(geburtsdatum_str)

    # Veränderungssperre: welche Rechtslage gilt?
    if zum_zeitpunkt_str:
        zeitpunkt = _date.fromisoformat(zum_zeitpunkt_str)
    else:
        zeitpunkt = _date.today()

    inkrafttreten_anpassungsgesetz = _date(2007, 4, 20)

    if zeitpunkt < inkrafttreten_anpassungsgesetz:
        # Alte Rechtslage: einheitlich 65 Jahre
        return _date(geb.year + 65, geb.month, 1), "65 Jahre (Rechtslage vor 20.04.2007)"

    # Neue Rechtslage: § 235 Abs. 2 SGB VI — stufenweise Anhebung
    jahr = geb.year

    if jahr <= 1946:
        alter_monate = 65 * 12
    elif jahr <= 1963:
        tabelle = {
            1947: (65, 1),  1948: (65, 2),  1949: (65, 3),  1950: (65, 4),
            1951: (65, 5),  1952: (65, 6),  1953: (65, 7),  1954: (65, 8),
            1955: (65, 9),  1956: (65, 10), 1957: (65, 11), 1958: (66, 0),
            1959: (66, 2),  1960: (66, 4),  1961: (66, 6),  1962: (66, 8),
            1963: (66, 10),
        }
        basis_jahre, extra_monate = tabelle[jahr]
        alter_monate = basis_jahre * 12 + extra_monate
    else:
        alter_monate = 67 * 12

    ziel_monat = geb.month + alter_monate
    ziel_jahr  = geb.year + ziel_monat // 12
    ziel_monat = ziel_monat % 12 or 12

    jahre  = alter_monate // 12
    monate = alter_monate % 12
    beschreibung = (
        f"{jahre} Jahre" if monate == 0
        else f"{jahre} Jahre {monate} Monate"
    ) + " (§ 235 Abs. 2 SGB VI)"

    return _date(ziel_jahr, ziel_monat, 1), beschreibung


# ============================================================
# M/N-REGEL (§ 2 BetrAVG)
# ============================================================

def berechne_mn_regel(versorgungsordnung, eintrittsdatum_str, austrittsdatum_str,
                      geburtsdatum_str, vollleistung, zeitraeume=None):
    """
    Ratierliche Kürzung nach § 2 BetrAVG — taggenau.

    n = max_endalter − individueller Zusagebeginn  (Tage)
    m = Summe der Zeiträume mit als_dienstzeit=true (Tage),
        begrenzt auf [Zusagebeginn, Austritt]
        Fallback: Austritt − Zusagebeginn

    Veränderungssperre: gesetzl. Rentenbeginn richtet sich nach Rechtslage zum Insolvenzdatum.
    """
    try:
        eintritt      = date.fromisoformat(eintrittsdatum_str)
        austritt      = date.fromisoformat(austrittsdatum_str)
        geburt        = date.fromisoformat(geburtsdatum_str)
        zusage_vo     = date.fromisoformat(versorgungsordnung.get('zusagedatum') or eintrittsdatum_str)
        zusage_beginn = max(zusage_vo, eintritt)

        regelaltersgrenze     = versorgungsordnung.get('parameter', {}).get('regelaltersgrenze', 67)
        beginn_altersleistung = date(geburt.year + regelaltersgrenze, geburt.month, 1)

        insolvenzdatum_str_local = versorgungsordnung.get('insolvenzdatum')
        gesetzl_rente, gesetzl_rente_beschreibung = gesetzlicher_rentenbeginn(
            geburtsdatum_str, zum_zeitpunkt_str=insolvenzdatum_str_local
        )

        max_endalter = max(min(beginn_altersleistung, gesetzl_rente), austritt)

        # n taggenau
        n_tage = (max_endalter - zusage_beginn).days
        if n_tage <= 0:
            return {'fehler': 'n = 0 Tage, Berechnung nicht möglich'}

        # m: Summe anrechenbarer Zeiträume, taggenau
        # Nur Zeiten mit als_dienstzeit=true UND ggf=false zählen für m
        m_tage    = 0
        m_details = []
        if zeitraeume:
            for zr in zeitraeume:
                # Zählt nur wenn Dienstzeit UND nicht GGF
                ist_dienstzeit = zr.get('als_dienstzeit', True)
                ist_ggf        = zr.get('ggf', False)
                
                if not ist_dienstzeit or ist_ggf:
                    continue
                    
                von_d   = date.fromisoformat(zr['von'])
                bis_d   = date.fromisoformat(zr['bis'])
                von_eff = max(von_d, zusage_beginn)
                bis_eff = min(bis_d, austritt)
                if bis_eff >= von_eff:
                    tage = (bis_eff - von_eff).days + 1
                    m_tage += tage
                    m_details.append({
                        'von': von_eff.isoformat(), 'bis': bis_eff.isoformat(),
                        'tage': tage,
                        'teilzeitfaktor': zr.get('teilzeitfaktor', 1.0),
                        'ggf': ist_ggf
                    })
        else:
            # Fallback ohne Zeitraumtabelle
            m_tage = (austritt - zusage_beginn).days + 1

        faktor             = min(m_tage / n_tage, 1.0)
        gekuerzte_leistung = vollleistung * faktor if vollleistung is not None else None

        # m_jahre/n_jahre nur zur besseren Lesbarkeit — Berechnung ist taggenau
        return {
            'zusage_beginn':              zusage_beginn.isoformat(),
            'austritt':                   austritt.isoformat(),
            'max_endalter':               max_endalter.isoformat(),
            'beginn_altersleistung':      beginn_altersleistung.isoformat(),
            'gesetzl_rentenbeginn':       gesetzl_rente.isoformat(),
            'gesetzl_rentenbeginn_regel': gesetzl_rente_beschreibung,
            'insolvenzdatum':             insolvenzdatum_str_local or '—',
            'm_tage':                     m_tage,
            'n_tage':                     n_tage,
            'm_jahre':                    round(m_tage / 365.25, 2),
            'n_jahre':                    jahre_zwischen(zusage_beginn, max_endalter),
            'faktor':                     round(faktor, 6),
            'faktor_anzeige':             f"{m_tage} / {n_tage} Tage = {faktor * 100:.4f}%",
            'gekuerzte_leistung':         round(gekuerzte_leistung, 2) if gekuerzte_leistung is not None else None,
            'm_details':                  m_details,
        }
    except Exception as e:
        return {'fehler': str(e)}


# ============================================================
# UNVERFALLBARKEITS-CHECK § 1b BetrAVG / § 30f BetrAVG
# ============================================================

def pruefe_unverfallbarkeit(versorgungsordnung, eintrittsdatum_str, austrittsdatum_str, geburtsdatum_str):
    """
    Prüft gesetzliche Unverfallbarkeit nach § 1b BetrAVG i.V.m. § 30f Abs. 3 BetrAVG.
    Gibt dict zurück mit: erfuellt (bool), regel (str), begruendung (str), details (dict)
    """
    try:
        eintritt  = date.fromisoformat(eintrittsdatum_str)
        austritt  = date.fromisoformat(austrittsdatum_str)
        geburt    = date.fromisoformat(geburtsdatum_str)
        zusage_vo = date.fromisoformat(versorgungsordnung.get('zusagedatum') or eintrittsdatum_str)
        # Konkretes Zusagedatum = max(allgemeines VO-Datum, Eintrittsdatum)
        zusage    = max(zusage_vo, eintritt)
    except Exception as e:
        return {'erfuellt': None, 'begruendung': f'Fehlende Daten: {e}', 'regel': None, 'details': {}}

    # Alter bei Austritt
    alter_bei_austritt = jahre_zwischen(geburt, austritt)

    # Betriebszugehörigkeit in Jahren
    dienstjahre = jahre_zwischen(eintritt, austritt)

    # Alter bei Zusage (Eintrittsdatum als Proxy)
    alter_bei_zusage = jahre_zwischen(geburt, eintritt)

    # 1. Entgeltumwandlung → sofort unverfallbar
    if versorgungsordnung.get('entgeltumwandlung'):
        return {
            'erfuellt': True,
            'regel': 'Entgeltumwandlung',
            'rechtsgrundlage': '§ 1b Abs. 5 BetrAVG',
            'begruendung': 'Entgeltumwandlung ist sofort unverfallbar.',
            'details': {}
        }

    # Welche Regel gilt je nach Zusagedatum?
    if zusage >= date(2018, 1, 1):
        # Aktuelle Regel: Mindestalter 21, Mindestdauer 3 Jahre
        mindestalter   = 21
        mindestdauer   = 3
        regel_id       = 'neu_ab_2018'
        rechtsgrundlage = '§ 1b Abs. 1 BetrAVG'
        regel_text     = 'Zusage ab 01.01.2018'

    elif zusage >= date(2001, 1, 1):
        # Übergangsregel: Mindestalter 25, Mindestdauer 5 Jahre
        mindestalter   = 25
        mindestdauer   = 5
        regel_id       = 'uebergang_2001_2017'
        rechtsgrundlage = '§ 30f Abs. 1 BetrAVG'
        regel_text     = 'Zusage 2001–2017'

    else:
        # Alte Regel: Mindestalter 35, Mindestdauer 10 Jahre (oder 12 BZ)
        mindestalter   = 35
        mindestdauer   = 10
        alternativ_dj  = 12
        regel_id       = 'alt_vor_2001'
        rechtsgrundlage = '§ 30f Abs. 3 BetrAVG'
        regel_text     = 'Zusage vor 01.01.2001'

        # Alternativbedingung: Alter 35 + 12 Jahre Betriebszugehörigkeit
        alternativ_ok = (alter_bei_austritt >= 35 and dienstjahre >= alternativ_dj)
        haupt_ok      = (alter_bei_austritt >= mindestalter and dienstjahre >= mindestdauer)
        erfuellt      = haupt_ok or alternativ_ok

        if erfuellt:
            genutzte_regel = f"{'Hauptregel' if haupt_ok else 'Alternativregel (12 Dienstjahre)'}"
            begruendung = (
                f"Unverfallbarkeit gegeben ({regel_text}): "
                f"Alter bei Austritt {alter_bei_austritt:.1f} Jahre, "
                f"Dienstjahre {dienstjahre:.1f}. "
                f"Genutzte Regel: {genutzte_regel}."
            )
        else:
            fehlend = []
            if alter_bei_austritt < mindestalter:
                fehlend.append(f"Alter {alter_bei_austritt:.1f} < {mindestalter} Jahre")
            if dienstjahre < mindestdauer:
                fehlend.append(f"Dienstjahre {dienstjahre:.1f} < {mindestdauer} Jahre")
            begruendung = (
                f"Unverfallbarkeit NICHT gegeben ({regel_text}): {', '.join(fehlend)}. "
                f"Auch Alternativregel (35 Jahre + 12 Dienstjahre) nicht erfüllt."
            )

        return {
            'erfuellt': erfuellt,
            'regel': regel_text,
            'rechtsgrundlage': rechtsgrundlage,
            'begruendung': begruendung,
            'details': {
                'zusagedatum_vo': zusage_vo.isoformat(),
                'zusagedatum_konkret': zusage.isoformat(),
                'alter_bei_austritt': round(alter_bei_austritt, 1),
                'dienstjahre': round(dienstjahre, 1),
                'mindestalter': mindestalter,
                'mindestdauer': mindestdauer,
            }
        }

    # Standardprüfung für Regeln ab 2001
    erfuellt = (alter_bei_austritt >= mindestalter and dienstjahre >= mindestdauer)

    if erfuellt:
        begruendung = (
            f"Unverfallbarkeit gegeben ({regel_text}): "
            f"Alter bei Austritt {alter_bei_austritt:.1f} ≥ {mindestalter} Jahre, "
            f"Dienstjahre {dienstjahre:.1f} ≥ {mindestdauer} Jahre."
        )
    else:
        fehlend = []
        if alter_bei_austritt < mindestalter:
            fehlend.append(f"Alter {alter_bei_austritt:.1f} < {mindestalter} Jahre")
        if dienstjahre < mindestdauer:
            fehlend.append(f"Dienstjahre {dienstjahre:.1f} < {mindestdauer} Jahre")
        begruendung = f"Unverfallbarkeit NICHT gegeben ({regel_text}): {', '.join(fehlend)}."

    return {
        'erfuellt': erfuellt,
        'regel': regel_text,
        'rechtsgrundlage': rechtsgrundlage,
        'begruendung': begruendung,
        'details': {
            'zusagedatum_vo': zusage_vo.isoformat(),
            'zusagedatum_konkret': zusage.isoformat(),
            'alter_bei_austritt': round(alter_bei_austritt, 1),
            'dienstjahre': round(dienstjahre, 1),
            'mindestalter': mindestalter,
            'mindestdauer': mindestdauer,
        }
    }


# ============================================================
# BERECHNUNGSFUNKTIONEN (Fallback für alte Methode)
# ============================================================

def calculate_dienstjahre(data) -> float:
    """
    Theoretisch erreichbare Dienstjahre (= n):
    max_endalter − individueller Zusagebeginn, taggenau.
    """
    eintritt = date.fromisoformat(str(data['eintrittsdatum']))
    austritt = date.fromisoformat(str(data['austrittsdatum']))
    geburt   = date.fromisoformat(str(data['geburtsdatum']))

    # Individueller Zusagebeginn
    zusage_vo_str = data.get('zusagedatum') or str(data['eintrittsdatum'])
    zusage_beginn = max(date.fromisoformat(str(zusage_vo_str)), eintritt)

    # VO-Parameter
    firma          = data.get('_firma')
    insolvenzdatum = None
    regelalter     = 67
    if firma and 'versorgungsordnung' in firma:
        vo          = firma['versorgungsordnung']
        regelalter  = vo.get('parameter', {}).get('regelaltersgrenze', 67)
        insolvenzdatum = vo.get('insolvenzdatum')

    beginn_altersleistung = date(geburt.year + regelalter, geburt.month, 1)
    gesetzl_rente, _      = gesetzlicher_rentenbeginn(str(data['geburtsdatum']),
                                                       zum_zeitpunkt_str=insolvenzdatum)
    max_endalter = max(min(beginn_altersleistung, gesetzl_rente), austritt)

    return jahre_zwischen(zusage_beginn, max_endalter)


def calculate_tarifgruppen_rente(data) -> float:
    """
    TechCorp: Tarifgruppen-basierte Rente.
    Formel: Summe über alle Zeiträume von (Monate × Tarifgruppen-Faktor)
    
    - TG A: 1 €/Monat
    - TG B: 2 €/Monat
    - TG C: 3 €/Monat
    - TG D: 5 €/Monat
    - TG E: 10 €/Monat
    """
    firma = data.get('_firma')
    if not firma or 'versorgungsordnung' not in firma:
        return 0.0
    
    tarifgruppen = firma['versorgungsordnung'].get('tarifgruppen', {})
    zeitraeume = data.get('zeitraeume', [])
    
    if not zeitraeume:
        return 0.0
    
    eintritt = date.fromisoformat(str(data['eintrittsdatum']))
    austritt = date.fromisoformat(str(data['austrittsdatum']))
    
    # Individueller Zusagebeginn
    zusage_vo_str = data.get('zusagedatum') or str(data['eintrittsdatum'])
    zusage_vo = date.fromisoformat(str(zusage_vo_str))
    zusage_beginn = max(zusage_vo, eintritt)
    
    gesamt_rente = 0.0
    
    for zr in zeitraeume:
        # Nur anrechnen wenn Dienstzeit und nicht GGF
        if not zr.get('als_dienstzeit', True) or zr.get('ggf', False):
            continue
        
        von_d = date.fromisoformat(zr['von'])
        bis_d = date.fromisoformat(zr['bis'])
        
        # Effektive Grenzen
        von_eff = max(von_d, zusage_beginn)
        bis_eff = min(bis_d, austritt)
        
        if bis_eff < von_eff:
            continue
        
        # Monate berechnen (taggenau → gerundet)
        tage = (bis_eff - von_eff).days + 1
        monate = round(tage / 30.44, 2)  # Durchschnittliche Monatslänge
        
        # Tarifgruppen-Faktor
        tg = zr.get('tarifgruppe', 'TG_C')
        faktor = tarifgruppen.get(tg, {}).get('faktor_pro_monat', 3.0)
        
        # Teilzeitfaktor berücksichtigen
        teilzeit = zr.get('teilzeitfaktor', 1.0)
        
        gesamt_rente += monate * faktor * teilzeit
    
    return round(gesamt_rente, 2)


def calculate_avg_teilzeit(data) -> float:
    """Fallback: Berechne aus Teilzeit-Tabelle"""
    try:
        tabelle = data['teilzeit_tabelle']
        if not tabelle or len(tabelle) == 0:
            raise ValueError("teilzeit_tabelle ist leer")
        return sum(tabelle) / len(tabelle)
    except (KeyError, ValueError):
        raise ValueError("teilzeit_tabelle wird benötigt oder aktivieren Sie den Override")

FUNCTIONS = {
    'calculate_avg_teilzeit': calculate_avg_teilzeit,
    'calculate_dienstjahre': calculate_dienstjahre,
    'calculate_tarifgruppen_rente': calculate_tarifgruppen_rente,
}

# ============================================================
# KOMPAKTE ZEITRAUM-TABELLE
# ============================================================

def should_show_zeitraum_spalte(spalte, zeitraum_daten):
    """Prüft ob eine Spalte in einem bestimmten Zeitraum angezeigt werden soll (conditional logic)."""
    if 'conditional' not in spalte:
        return True
    
    cond = spalte['conditional']
    field_id = cond['field']
    operator = cond['operator']
    cond_value = cond['value']
    
    current_value = zeitraum_daten.get(field_id)
    
    if operator == 'in':
        return current_value in cond_value
    elif operator == '==':
        return current_value == cond_value
    elif operator == '!=':
        return current_value != cond_value
    elif operator == '>=':
        return current_value >= cond_value
    elif operator == '<=':
        return current_value <= cond_value
    elif operator == '>':
        return current_value > cond_value
    elif operator == '<':
        return current_value < cond_value
    
    return True


def resolve_tabelle_datum(config_datum, evaluator, versorgungsordnung):
    """Berechnet Beginn oder Ende einer Zeitraum-Tabelle aus Schema-Definition."""
    dtype = config_datum.get('type')
    
    if dtype == 'input':
        return evaluator.input_data.get(config_datum['input_id'])
    
    elif dtype == 'parameter':
        param_id = config_datum['parameter_id']
        return (versorgungsordnung.get(param_id) or 
                versorgungsordnung.get('parameter', {}).get(param_id))
    
    elif dtype == 'fixed':
        return config_datum['value']
    
    elif dtype == 'max':
        werte = [resolve_tabelle_datum(w, evaluator, versorgungsordnung) for w in config_datum['werte']]
        werte = [w for w in werte if w]
        return max(werte) if werte else None
    
    elif dtype == 'min':
        werte = [resolve_tabelle_datum(w, evaluator, versorgungsordnung) for w in config_datum['werte']]
        werte = [w for w in werte if w]
        return min(werte) if werte else None
    
    return None


def show_zeitraum_tabelle_from_schema(evaluator, firma, eintritt_str, austritt_str, versorgungsordnung, tabelle_config):
    """Zeigt kompakte Zeitraum-Tabelle basierend auf Schema"""
    
    spalten_config = tabelle_config.get('spalten', [])
    
    # Beginn und Ende aus Schema berechnen
    beginn_config = tabelle_config.get('beginn', {'type': 'input', 'input_id': 'eintrittsdatum'})
    ende_config   = tabelle_config.get('ende',   {'type': 'input', 'input_id': 'austrittsdatum'})
    
    tabelle_beginn = resolve_tabelle_datum(beginn_config, evaluator, versorgungsordnung) or eintritt_str
    tabelle_ende   = resolve_tabelle_datum(ende_config,   evaluator, versorgungsordnung) or austritt_str
    
    beginn_beschreibung = beginn_config.get('beschreibung', 'Beginn')
    ende_beschreibung   = ende_config.get('beschreibung', 'Ende')
    
    # Info über den zu erfassenden Zeitraum
    st.info(
        f"📅 **Zeitraum-Erfassung:** {beginn_beschreibung} ({tabelle_beginn}) "
        f"bis {ende_beschreibung} ({tabelle_ende})"
    )
    
    # Alle Spalten sind sichtbar (keine Aktivierung mehr)
    spalten_state = {s['id']: True for s in spalten_config}
    
    # Initialisiere Zeiträume beim ersten Aufruf
    if 'zeitraeume' not in st.session_state or not st.session_state.zeitraeume:
        default_zeitraum = {'bis': tabelle_ende}
        for spalte in spalten_config:
            if spalte['id'] not in ['von', 'bis']:
                default_zeitraum[spalte['id']] = spalte.get('default', None)
        st.session_state.zeitraeume = [default_zeitraum]
        st.session_state['zeitraeume_beginn'] = tabelle_beginn
        st.session_state['zeitraeume_ende']   = tabelle_ende
    
    # Beginn oder Ende hat sich geändert → Tabelle anpassen
    beginn_geaendert = st.session_state.get('zeitraeume_beginn') != tabelle_beginn
    ende_geaendert   = st.session_state.get('zeitraeume_ende')   != tabelle_ende
    
    if beginn_geaendert:
        # Zeiträume die komplett vor dem neuen Beginn enden → entfernen
        st.session_state.zeitraeume = [
            zr for zr in st.session_state.zeitraeume
            if zr['bis'] > tabelle_beginn
        ]
        if not st.session_state.zeitraeume:
            default_zeitraum = {'bis': tabelle_ende}
            for spalte in spalten_config:
                if spalte['id'] not in ['von', 'bis']:
                    default_zeitraum[spalte['id']] = spalte.get('default', None)
            st.session_state.zeitraeume = [default_zeitraum]
        st.session_state['zeitraeume_beginn'] = tabelle_beginn
    
    if ende_geaendert:
        # Letzten Zeitraum auf neues Ende setzen
        st.session_state.zeitraeume[-1]['bis'] = tabelle_ende
        # Zeiträume bereinigen die nach dem neuen Ende liegen
        bereinigt = [st.session_state.zeitraeume[0]]
        for zr in st.session_state.zeitraeume[1:]:
            prev_bis = date.fromisoformat(bereinigt[-1]['bis'])
            naechstes_von = (prev_bis + timedelta(days=1)).isoformat()
            if naechstes_von <= tabelle_ende:
                bereinigt.append(zr)
        bereinigt[-1]['bis'] = tabelle_ende
        st.session_state.zeitraeume = bereinigt
        st.session_state['zeitraeume_ende'] = tabelle_ende
    
    # Berechne Von-Felder (immer ab tabelle_beginn)
    zeitraeume_mit_von = []
    aktuelles_von = date.fromisoformat(tabelle_beginn)
    for zr in st.session_state.zeitraeume:
        z = zr.copy()
        z['von'] = aktuelles_von.isoformat()
        zeitraeume_mit_von.append(z)
        aktuelles_von = date.fromisoformat(zr['bis']) + timedelta(days=1)
    
    st.markdown("---")
    
    # Tabellen-Kopfzeile
    visible_spalten = [
        s for s in spalten_config 
        if s['id'] not in ['von', 'split', 'merge']
    ]
    
    num_cols = len(visible_spalten) + 2  # +2 für Split/Merge
    header_cols = st.columns([1] * len(visible_spalten) + [0.6, 0.6])
    
    for col_idx, spalte in enumerate(visible_spalten):
        with header_cols[col_idx]:
            st.markdown(f"**{spalte.get('label', spalte['id'])}**")
    with header_cols[-2]:
        st.markdown("**✂️**")
    with header_cols[-1]:
        st.markdown("**🔗**")
    
    # Zeiträume anzeigen
    for i, zr in enumerate(zeitraeume_mit_von):
        von_date = date.fromisoformat(zr['von'])
        bis_date = date.fromisoformat(zr['bis'])
        
        with st.container():
            # Header
            col1, col2, col3, col4 = st.columns([4, 1, 1, 2])
            
            with col1:
                st.markdown(f"**Zeitraum {i+1}:** {von_date.strftime('%d.%m.%Y')} - {bis_date.strftime('%d.%m.%Y')}")
            
            with col2:
                if st.button("Split", key=f"split_{i}"):
                    st.session_state[f'show_split_{i}'] = True
            
            with col3:
                if i < len(zeitraeume_mit_von) - 1:
                    if st.button("Merge", key=f"merge_{i}"):
                        st.session_state.zeitraeume[i]['bis'] = st.session_state.zeitraeume[i+1]['bis']
                        st.session_state.zeitraeume.pop(i+1)
                        st.rerun()
            
            # Split-Dialog
            if st.session_state.get(f'show_split_{i}', False):
                with st.form(key=f'split_form_{i}'):
                    split_date = st.date_input(
                        "Datum:",
                        value=von_date + timedelta(days=(bis_date - von_date).days // 2),
                        min_value=von_date,
                        max_value=bis_date - timedelta(days=1)
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.form_submit_button("Teilen"):
                            erster = st.session_state.zeitraeume[i].copy()
                            erster['bis'] = split_date.isoformat()
                            zweiter = st.session_state.zeitraeume[i].copy()
                            st.session_state.zeitraeume[i] = erster
                            st.session_state.zeitraeume.insert(i+1, zweiter)
                            st.session_state[f'show_split_{i}'] = False
                            st.rerun()
                    with col_b:
                        if st.form_submit_button("Abbrechen"):
                            st.session_state[f'show_split_{i}'] = False
                            st.rerun()
            
            # Daten-Felder (alle Spalten außer von/split/merge, mit conditional check)
            visible_spalten = [
                s for s in spalten_config 
                if s['id'] not in ['von', 'split', 'merge']
                and should_show_zeitraum_spalte(s, zr)
            ]
            
            cols = st.columns(len(visible_spalten))
            
            for col, spalte in zip(cols, visible_spalten):
                with col:
                    spalten_id = spalte['id']
                    spalten_type = spalte['type']
                    
                    if spalten_id == 'bis':
                        if i == len(zeitraeume_mit_von) - 1:
                            st.text_input("Bis", value=bis_date.strftime('%d.%m.%Y'), disabled=True, key=f"bis_d_{i}", label_visibility="collapsed")
                        else:
                            neues_bis = st.date_input("Bis", value=bis_date, min_value=von_date, key=f"bis_{i}", label_visibility="collapsed")
                            if neues_bis != bis_date:
                                st.session_state.zeitraeume[i]['bis'] = neues_bis.isoformat()
                                st.rerun()
                    
                    elif spalten_type == 'slider':
                        # Teilzeitfaktor: erlaubt sowohl Dezimalzahl als auch Bruch (z.B. "22/38")
                        current_value = zr.get(spalten_id, spalte.get('default', 1.0))
                        
                        # Zeige als Dezimalzahl wenn verfügbar
                        if isinstance(current_value, (int, float)):
                            display_value = f"{current_value:.2f}"
                        else:
                            display_value = str(current_value)
                        
                        eingabe = st.text_input(
                            spalte['label'],
                            value=display_value,
                            key=f"{spalten_id}_{i}",
                            label_visibility="collapsed",
                            help="Dezimalzahl (z.B. 0.58) oder Bruch (z.B. 22/38)"
                        )
                        
                        # Parse Eingabe
                        try:
                            if '/' in eingabe:
                                # Bruch-Eingabe (z.B. "22/38")
                                teile = eingabe.strip().split('/')
                                if len(teile) == 2:
                                    zaehler = float(teile[0].strip())
                                    nenner = float(teile[1].strip())
                                    if nenner > 0:
                                        parsed_value = round(zaehler / nenner, 4)
                                    else:
                                        parsed_value = float(current_value)
                                else:
                                    parsed_value = float(current_value)
                            else:
                                # Direkte Dezimalzahl
                                parsed_value = float(eingabe.replace(',', '.'))
                            
                            # Auf gültigen Bereich prüfen
                            min_val = spalte.get('min', 0.0)
                            max_val = spalte.get('max', 1.0)
                            parsed_value = max(min_val, min(max_val, parsed_value))
                            
                            st.session_state.zeitraeume[i][spalten_id] = parsed_value
                            
                            # Zeige berechneten Wert wenn Formel eingegeben wurde
                            if '/' in eingabe and parsed_value != float(display_value):
                                st.caption(f"= {parsed_value:.4f}")
                        except ValueError:
                            # Bei ungültiger Eingabe: behalte alten Wert
                            st.caption("⚠️ Ungültige Eingabe")
                            st.session_state.zeitraeume[i][spalten_id] = float(current_value)
                    
                    elif spalten_type == 'checkbox':
                        value = st.checkbox(
                            spalte['label'],
                            value=bool(zr.get(spalten_id, spalte.get('default', False))),
                            key=f"{spalten_id}_{i}",
                            label_visibility="collapsed"
                        )
                        st.session_state.zeitraeume[i][spalten_id] = value
                    
                    elif spalten_type == 'number':
                        value = st.number_input(
                            spalte['label'],
                            spalte.get('min', 0.0),
                            spalte.get('max', 50000.0),
                            float(zr.get(spalten_id, spalte.get('default', 0.0))),
                            spalte.get('step', 100.0),
                            key=f"{spalten_id}_{i}",
                            label_visibility="collapsed",
                            format="%.0f"
                        )
                        st.session_state.zeitraeume[i][spalten_id] = value
                    
                    elif spalten_type == 'dropdown':
                        options = spalte.get('options', [])
                        option_values = [opt['value'] for opt in options]
                        option_labels = [opt['label'] for opt in options]
                        
                        current_value = zr.get(spalten_id, spalte.get('default', option_values[0]))
                        current_index = option_values.index(current_value) if current_value in option_values else 0
                        
                        selected_index = st.selectbox(
                            spalte['label'],
                            range(len(option_labels)),
                            index=current_index,
                            format_func=lambda i: option_labels[i],
                            key=f"{spalten_id}_{i}",
                            label_visibility="collapsed"
                        )
                        st.session_state.zeitraeume[i][spalten_id] = option_values[selected_index]
    
    # Validierung und Berechnungen
    st.markdown("---")
    
    letztes_bis = date.fromisoformat(zeitraeume_mit_von[-1]['bis'])
    if letztes_bis == date.fromisoformat(tabelle_ende):
        evaluator.set_input('zeitraeume', zeitraeume_mit_von)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                dj = evaluator.get_value('dienstjahre')
                st.metric("Dienstjahre (n)", f"{dj}", 
                         help="Theoretisch erreichbare Dienstjahre = max. Endalter − Zusagebeginn")
            except:
                pass
        
        with col2:
            try:
                tz = evaluator.get_value('mittlerer_teilzeitfaktor')
                st.metric("Ø Teilzeit", f"{tz:.2f}")
            except:
                pass
        
        with col3:
            try:
                gh = evaluator.get_value('letztes_gehalt')
                st.metric("Letztes Gehalt", f"{gh:.0f} EUR")
            except:
                pass


def show_zeitraum_tabelle(evaluator, firma, eintritt_str, austritt_str, versorgungsordnung):
    """Legacy-Wrapper für Abwärtskompatibilität"""
    # Erstelle Standard-Config
    default_config = {
        "enabled": True,
        "spalten": [
            {"id": "von", "label": "Von", "type": "date", "auto_calculated": True, "disabled": True},
            {"id": "bis", "label": "Bis", "type": "date", "required": True},
            {"id": "als_dienstzeit", "label": "Als Dienstzeit", "type": "checkbox", "default": True, "aktivierbar": True},
            {"id": "teilzeitfaktor", "label": "Teilzeitfaktor", "type": "slider", "min": 0.0, "max": 1.0, "step": 0.05, "default": 1.0, "always_visible": True},
            {"id": "gehalt", "label": "Gehalt (EUR)", "type": "number", "min": 0.0, "max": 50000.0, "step": 100.0, "default": 0.0, "aktivierbar": True}
        ]
    }
    show_zeitraum_tabelle_from_schema(evaluator, firma, eintritt_str, austritt_str, versorgungsordnung, default_config)

# ============================================================
# SEITEN-TITEL
# ============================================================

st.title("Interaktives Formular")
st.markdown("---")

# ============================================================
# DATEN LADEN
# ============================================================

@st.cache_data
def load_json(filename: str):
    path = Path(__file__).parent.parent / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# PRÜFUNGS-PERSISTENZ (3x-Prüfen-Regel)
# ============================================================

PRUEFUNGEN_PATH = Path(__file__).parent.parent / 'pruefungen.json'

def lade_pruefungen() -> dict:
    """Lädt den globalen Prüfungsstand aus pruefungen.json."""
    if PRUEFUNGEN_PATH.exists():
        with open(PRUEFUNGEN_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def speichere_pruefungen(pruefungen: dict):
    """Speichert den Prüfungsstand in pruefungen.json."""
    with open(PRUEFUNGEN_PATH, 'w', encoding='utf-8') as f:
        json.dump(pruefungen, f, ensure_ascii=False, indent=2)

# ============================================================
# QUALITÄTSSICHERUNGS-SYSTEM
# ============================================================

def extrahiere_formel_abhaengigkeiten(leistungsteile: list) -> dict:
    """
    Erstellt ein Dictionary mit Abhängigkeiten:
    {
      'formel_id': ['input1', 'input2', ...]
    }
    """
    abhaengigkeiten = {}
    
    for teil in leistungsteile:
        feld_id = teil.get('id')
        formula = teil.get('formula', {})
        
        # Inputs aus formula extrahieren
        inputs = formula.get('inputs', [])
        
        # Bei expression: Parse expression für verwendete Felder
        if formula.get('type') == 'expression':
            expr = formula.get('expression', '')
            # Einfaches Parsing: Finde alle Wörter (Feldnamen)
            import re
            gefundene = re.findall(r'\b[a-z_][a-z0-9_]*\b', expr)
            inputs = list(set(inputs + gefundene))
        
        # Bei zeitraum_aggregation: field verwenden
        if formula.get('type') == 'zeitraum_aggregation':
            field = formula.get('field')
            if field:
                inputs.append(field)
            zeitraeume_id = formula.get('zeitraeume_id', 'zeitraeume')
            inputs.append(zeitraeume_id)
        
        abhaengigkeiten[feld_id] = inputs
    
    return abhaengigkeiten


def finde_abhaengige_formeln(feld_id: str, abhaengigkeiten: dict) -> list:
    """
    Findet alle Formeln die von einem Feld abhängen (direkt oder indirekt).
    """
    abhaengige = []
    
    def _rekursiv_finden(feld, bereits_besucht=None):
        if bereits_besucht is None:
            bereits_besucht = set()
        
        if feld in bereits_besucht:
            return
        bereits_besucht.add(feld)
        
        for formel_id, inputs in abhaengigkeiten.items():
            if feld in inputs and formel_id not in abhaengige:
                abhaengige.append(formel_id)
                # Rekursiv: Formeln die von dieser Formel abhängen
                _rekursiv_finden(formel_id, bereits_besucht)
    
    _rekursiv_finden(feld_id)
    return abhaengige


def invalidiere_abhaengige_formeln(pruefungen: dict, firma_id: str, 
                                   geaendertes_feld: str, abhaengigkeiten: dict):
    """
    Löscht Prüfungen für Formeln die von einem geänderten Feld abhängen.
    """
    abhaengige = finde_abhaengige_formeln(geaendertes_feld, abhaengigkeiten)
    
    geloeschte = []
    for formel_id in abhaengige:
        key = pruefungs_key(firma_id, formel_id)
        if key in pruefungen:
            del pruefungen[key]
            geloeschte.append(formel_id)
    
    if geloeschte:
        speichere_pruefungen(pruefungen)
    
    return geloeschte


def ist_input_wert_neu(pruefungen: dict, firma_id: str, input_id: str, 
                       wert: any, person_id: str = None) -> bool:
    """
    Prüft ob ein Input-Wert bei dieser Firma schon geprüft wurde.
    Speichert Input-Werte nicht separat, sondern durchsucht alle Prüfungen.
    """
    # Durchsuche alle Prüfungen dieser Firma
    for key in pruefungen.keys():
        if key.startswith(f"{firma_id}__"):
            feld_pruefungen = pruefungen[key]
            for p_id, p_data in feld_pruefungen.items():
                # Überspringe die aktuelle Person wenn angegeben
                if person_id and p_id == person_id:
                    continue
                
                # Prüfe ob gespeicherte Input-Daten vorhanden sind
                inputs = p_data.get('inputs', {})
                if input_id in inputs:
                    gespeicherter_wert = inputs[input_id]
                    # Runde für Vergleich
                    if isinstance(wert, (int, float)) and isinstance(gespeicherter_wert, (int, float)):
                        if round(float(wert), 2) == round(float(gespeicherter_wert), 2):
                            return False  # Wert ist nicht neu
                    elif wert == gespeicherter_wert:
                        return False
    
    return True  # Wert ist neu


def pruefungs_key(firma_id: str, feld_id: str) -> str:
    return f"{firma_id}__{feld_id}"

def get_pruefungen_fuer_feld(pruefungen: dict, firma_id: str, feld_id: str) -> dict:
    """Gibt alle Prüfungen für ein Feld zurück: {person_id: {wert, timestamp}}"""
    return pruefungen.get(pruefungs_key(firma_id, feld_id), {})

def registriere_pruefung(pruefungen: dict, firma_id: str, feld_id: str,
                          person_id: str, wert: float, input_werte: dict = None):
    """
    Trägt eine Prüfung ein und speichert.
    
    Regel:
    - Pro AN (person_id) kann nur EINMAL geprüft werden
    - Ein Prüfer kann beliebig viele verschiedene AN prüfen
    
    Args:
        person_id: Arbeitnehmer-ID (nicht Prüfer-ID!)
        input_werte: Dict mit Input-Werten die zu diesem Ergebnis geführt haben
    
    Returns:
        True wenn Prüfung registriert wurde, False wenn AN bereits geprüft
    """
    from datetime import datetime
    key = pruefungs_key(firma_id, feld_id)
    if key not in pruefungen:
        pruefungen[key] = {}
    
    # Prüfe ob dieser AN (person_id) schon geprüft wurde
    if person_id in pruefungen[key]:
        # AN wurde bereits geprüft
        return False
    
    pruef_eintrag = {
        'wert': wert,
        'geprueft_am': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    # Speichere Input-Werte falls vorhanden
    if input_werte:
        pruef_eintrag['inputs'] = input_werte
    
    pruefungen[key][person_id] = pruef_eintrag
    speichere_pruefungen(pruefungen)
    return True

def loesche_pruefung(pruefungen: dict, firma_id: str, feld_id: str, person_id: str):
    """Entfernt eine Einzelprüfung."""
    key = pruefungs_key(firma_id, feld_id)
    if key in pruefungen and person_id in pruefungen[key]:
        del pruefungen[key][person_id]
        speichere_pruefungen(pruefungen)

def pruefstatus(pruefungen: dict, firma_id: str, feld_id: str,
                person_id: str, ist_override: bool, aktueller_wert: float = None) -> dict:
    """
    Gibt Prüfstatus zurück mit wertabhängiger Logik:
    
    Freigegeben wenn:
    1. Override gesetzt ODER
    2. Von dieser Person geprüft ODER
    3. 3+ Prüfungen UND (
         aktueller Wert wurde schon geprüft ODER
         3+ verschiedene Werte wurden geprüft
       )
    
    Returns:
      valide:           bool   — darf das Ergebnis verwendet werden
      grund:            str    — Begründung
      anzahl:           int    — Anzahl Prüfungen
      anzahl_werte:     int    — Anzahl verschiedener Werte
      individuell:      bool   — diese Person hat geprüft
      wert_geprueft:    bool   — aktueller Wert wurde schon geprüft
    """
    if ist_override:
        return {
            'valide': True, 
            'grund': 'override', 
            'anzahl': 0, 
            'anzahl_werte': 0,
            'individuell': False,
            'wert_geprueft': False
        }

    feld_pruefungen = get_pruefungen_fuer_feld(pruefungen, firma_id, feld_id)
    anzahl = len(feld_pruefungen)
    individuell = person_id in feld_pruefungen

    # Individuelle Prüfung → immer valide
    if individuell:
        return {
            'valide': True,
            'grund': 'individuell',
            'anzahl': anzahl,
            'anzahl_werte': 0,
            'individuell': True,
            'wert_geprueft': False
        }

    # Analysiere geprüfte Werte
    geprueft_werte = []
    for p_id, p_data in feld_pruefungen.items():
        wert = p_data.get('wert')
        if wert is not None:
            # Runden auf 2 Dezimalstellen für Vergleich
            geprueft_werte.append(round(float(wert), 2))
    
    anzahl_verschiedene_werte = len(set(geprueft_werte))
    
    # Prüfe ob aktueller Wert schon geprüft wurde
    wert_bereits_geprueft = False
    if aktueller_wert is not None:
        aktueller_wert_gerundet = round(float(aktueller_wert), 2)
        wert_bereits_geprueft = aktueller_wert_gerundet in geprueft_werte
    
    # Freigabe-Bedingungen
    if anzahl >= 3:
        # Fall 1: Aktueller Wert wurde schon geprüft
        if wert_bereits_geprueft:
            return {
                'valide': True,
                'grund': 'wert_bekannt',
                'anzahl': anzahl,
                'anzahl_werte': anzahl_verschiedene_werte,
                'individuell': False,
                'wert_geprueft': True
            }
        
        # Fall 2: Mindestens 3 verschiedene Werte wurden geprüft
        if anzahl_verschiedene_werte >= 3:
            return {
                'valide': True,
                'grund': 'diverse_werte',
                'anzahl': anzahl,
                'anzahl_werte': anzahl_verschiedene_werte,
                'individuell': False,
                'wert_geprueft': False
            }

    # Nicht freigegeben
    return {
        'valide': False,
        'grund': 'ungeprueft',
        'anzahl': anzahl,
        'anzahl_werte': anzahl_verschiedene_werte,
        'individuell': False,
        'wert_geprueft': wert_bereits_geprueft
    }

# ============================================================
# AUSWAHL PRÜFEN
# ============================================================

if not st.session_state.get('firma_id') or not st.session_state.get('person_id'):
    st.warning("Bitte zuerst Firma und Person auswählen")
    st.info("Navigieren Sie zur Seite 'Auswahl'")
    st.stop()

if not st.session_state.get('firma_config'):
    st.error("Firma-Konfiguration nicht geladen")
    st.info("Bitte gehen Sie zurück zur Auswahl")
    st.stop()

# ============================================================
# DATEN LADEN
# ============================================================

# Aus Session State
firma_config = st.session_state.firma_config
firma = firma_config
versorgungsordnung = firma_config['versorgungsordnung']
schema = firma_config.get('schema', {})
personen = firma_config.get('personen', [])

# Aktuelle IDs
aktuelle_firma_id  = st.session_state.firma_id
aktuelle_person_id = st.session_state.person_id

# Globaler Prüfungsstand laden
pruefungen = lade_pruefungen()

# Formel-Abhängigkeiten extrahieren
leistungsteile = schema.get('leistungsteile', [])
formel_abhaengigkeiten = extrahiere_formel_abhaengigkeiten(leistungsteile)

# Widget-Keys bereinigen wenn Person/Firma gewechselt hat
# (verhindert dass Streamlit alte Datumswerte einfriert)
letzte_person = st.session_state.get('_letzte_person_id')
letzte_firma  = st.session_state.get('_letzte_firma_id')
if letzte_person != aktuelle_person_id or letzte_firma != aktuelle_firma_id:
    # Alle field_* Keys löschen damit Widgets neu initialisiert werden
    for key in list(st.session_state.keys()):
        if key.startswith('field_') or key.startswith('ovr_') or key.startswith('pruef_') \
                or key.startswith('missing_') or key in ('zeitraeume', 'zeitraeume_beginn',
                'zeitraeume_ende', 'zeitraeume_eintritt', 'zeitraeume_austritt'):
            del st.session_state[key]
    st.session_state['_letzte_person_id'] = aktuelle_person_id
    st.session_state['_letzte_firma_id']  = aktuelle_firma_id
    # Warnung für neue Werte zurücksetzen
    st.session_state.pop('_neue_werte_warnung_shown', None)
    # Evaluator neu initialisieren
    st.session_state.evaluator = None

# Finde ausgewählte Person
person = next((p for p in personen if p['id'] == st.session_state.person_id), None)
if not person:
    st.error("Person nicht gefunden")
    st.stop()

# Header
st.success(f"""
**Aktuelle Auswahl:**
- Firma: {firma['firma']['name']}
- Person: {person['name']} ({person['profil']})
""")

st.markdown("---")

# ============================================================
# EVALUATOR
# ============================================================

if 'evaluator' not in st.session_state or st.session_state.evaluator is None:
    evaluator = LazyEvaluator(schema, FUNCTIONS)
    evaluator.firma = firma
    
    for key, value in person['daten'].items():
        evaluator.set_input(key, value)
    
    if person.get('overrides'):
        for key, value in person['overrides'].items():
            evaluator.override(key, value)
    
    st.session_state.evaluator = evaluator
else:
    evaluator = st.session_state.evaluator
    evaluator.firma = firma

# ============================================================
# NEUE INPUT-WERTE PRÜFEN & ABHÄNGIGE FORMELN INVALIDIEREN
# ============================================================

# Prüfe welche Input-Felder neue Werte haben
neue_input_werte = []
for field in schema.get('input_fields', []):
    field_id = field['id']
    aktueller_wert = evaluator.input_data.get(field_id)
    
    if aktueller_wert is not None:
        if ist_input_wert_neu(pruefungen, aktuelle_firma_id, field_id, 
                              aktueller_wert, aktuelle_person_id):
            neue_input_werte.append((field_id, aktueller_wert))

# Wenn neue Input-Werte: Zeige Warnung und invalidiere abhängige Formeln
if neue_input_werte and not st.session_state.get('_neue_werte_warnung_shown'):
    st.warning(
        f"⚠️ **Neue Input-Werte erkannt:** "
        + ", ".join([f"{fid}" for fid, _ in neue_input_werte]) +
        "  \nAbhängige Formeln müssen neu geprüft werden."
    )
    
    # Invalidiere abhängige Formeln
    alle_geloeschten = []
    for field_id, wert in neue_input_werte:
        geloeschte = invalidiere_abhaengige_formeln(
            pruefungen, aktuelle_firma_id, field_id, formel_abhaengigkeiten
        )
        alle_geloeschten.extend(geloeschte)
    
    if alle_geloeschten:
        st.info(
            f"🔄 **Formeln invalidiert:** " +
            ", ".join(set(alle_geloeschten)) +
            "  \nDiese müssen für diesen AN neu geprüft werden."
        )
    
    # Zeige Warnung nur einmal pro Session
    st.session_state['_neue_werte_warnung_shown'] = True

# ============================================================
# SCHEMA-BASIERTER FORM GENERATOR
# ============================================================

def generate_input_field(field_def, evaluator, person_data, mode_id="default"):
    """Generiert ein Eingabefeld basierend auf Schema-Definition"""
    field_id = field_def['id']
    field_type = field_def['type']
    label = field_def.get('label', field_id)
    
    # Hole aktuellen Wert
    if field_id in evaluator.overrides:
        current_value = evaluator.overrides[field_id]
        is_override = True
    elif field_id in evaluator.input_data:
        current_value = evaluator.input_data[field_id]
        is_override = False
    elif field_id in person_data:
        current_value = person_data[field_id]
        is_override = False
    else:
        current_value = field_def.get('default')
        is_override = False
    
    # Unique Key mit mode_id
    widget_key = f"field_{mode_id}_{field_id}"
    
    # Generiere Widget basierend auf Typ
    if field_type == 'date':
        # Initialisierung: session_state direkt setzen wenn nicht vorhanden
        if widget_key not in st.session_state:
            if current_value:
                initial_date = date.fromisoformat(current_value) if isinstance(current_value, str) else current_value
            else:
                initial_date = date.today()
            st.session_state[widget_key] = initial_date
        
        # Widget OHNE value= - nutzt session_state[key]
        st.date_input(
            label,
            key=widget_key,
            help=field_def.get('help')
        )
        
        # Wert aus session_state holen und in Evaluator setzen
        value = st.session_state[widget_key]
        evaluator.set_input(field_id, str(value))
        return value
    
    elif field_type == 'slider':
        # Teilzeitfaktor: erlaubt Dezimalzahl oder Bruch (z.B. "22/38")
        if isinstance(current_value, (int, float)) and current_value is not None:
            display_value = f"{current_value:.2f}"
        elif current_value:
            display_value = str(current_value)
        else:
            display_value = f"{field_def.get('default', 1.0):.2f}"
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            eingabe = st.text_input(
                label,
                value=display_value,
                key=widget_key,
                help=field_def.get('help', '') + " (z.B. 0.75 oder 30/40)"
            )
        
        # Parse Eingabe
        try:
            if '/' in eingabe:
                # Bruch-Eingabe (z.B. "22/38")
                teile = eingabe.strip().split('/')
                if len(teile) == 2:
                    zaehler = float(teile[0].strip())
                    nenner = float(teile[1].strip())
                    if nenner > 0:
                        parsed_value = round(zaehler / nenner, 4)
                    else:
                        parsed_value = float(current_value) if current_value else 1.0
                else:
                    parsed_value = float(current_value) if current_value else 1.0
            else:
                # Direkte Dezimalzahl
                parsed_value = float(eingabe.replace(',', '.'))
            
            # Auf gültigen Bereich prüfen
            min_val = field_def.get('min', 0.0)
            max_val = field_def.get('max', 1.0)
            parsed_value = max(min_val, min(max_val, parsed_value))
            
            value = parsed_value
            
            # Zeige berechneten Wert
            with col2:
                if '/' in eingabe:
                    st.metric("=", f"{parsed_value:.4f}")
        except ValueError:
            # Bei ungültiger Eingabe: behalte alten Wert
            value = float(current_value) if current_value else field_def.get('default', 1.0)
            with col2:
                st.caption("⚠️ Ungültig")
        
        evaluator.set_input(field_id, value)
        
        # Override-Option wenn overridable
        if field_def.get('overridable', False):
            use_override = st.checkbox(
                "Als manuellen Wert speichern",
                value=is_override,
                key=f"override_{mode_id}_{field_id}"
            )
            
            if use_override:
                evaluator.override(field_id, value)
            else:
                if field_id in evaluator.overrides:
                    evaluator.clear_override(field_id)
                evaluator.set_input(field_id, value)
        else:
            evaluator.set_input(field_id, value)
        
        return value
    
    elif field_type == 'number':
        value = st.number_input(
            label,
            min_value=field_def.get('min', 0.0),
            max_value=field_def.get('max', 100000.0),
            value=float(current_value) if current_value is not None else field_def.get('default', 0.0),
            step=field_def.get('step', 1.0),
            key=widget_key,
            help=field_def.get('help'),
            format=field_def.get('format', "%.2f")
        )
        
        # Override-Option wenn overridable
        if field_def.get('overridable', False):
            use_override = st.checkbox(
                "Als manuellen Wert speichern",
                value=is_override,
                key=f"override_{mode_id}_{field_id}"
            )
            
            if use_override:
                evaluator.override(field_id, value)
            else:
                if field_id in evaluator.overrides:
                    evaluator.clear_override(field_id)
                evaluator.set_input(field_id, value)
        else:
            evaluator.set_input(field_id, value)
        
        return value
    
    elif field_type == 'checkbox':
        value = st.checkbox(
            label,
            value=bool(current_value) if current_value is not None else field_def.get('default', False),
            key=widget_key,
            help=field_def.get('help')
        )
        evaluator.set_input(field_id, value)
        return value
    
    else:
        st.warning(f"Unbekannter Feldtyp: {field_type}")
        return None


def should_show_field(field_def, evaluator):
    """Prüft ob Feld angezeigt werden soll (conditional logic)"""
    if 'conditional' not in field_def:
        return True
    
    cond = field_def['conditional']
    cond_field = cond['field']
    operator = cond['operator']
    cond_value = cond['value']
    
    # Hole aktuellen Wert des condition-Feldes
    if cond_field in evaluator.input_data:
        current = evaluator.input_data[cond_field]
    else:
        return False
    
    # Prüfe Bedingung
    if operator == '>=':
        return current >= cond_value
    elif operator == '<=':
        return current <= cond_value
    elif operator == '>':
        return current > cond_value
    elif operator == '<':
        return current < cond_value
    elif operator == '==':
        return current == cond_value
    elif operator == '!=':
        return current != cond_value
    
    return True


# ============================================================
# EINGABEFELDER (SCHEMA-BASIERT)
# ============================================================

st.subheader("Eingabefelder")

# Hole Schema
schema = firma_config.get('schema', {})
input_fields = schema.get('input_fields', [])
ui_layout = schema.get('ui_layout', {})
modes = ui_layout.get('modes', [])

if not modes:
    st.error("Kein UI-Layout im Schema definiert")
    st.stop()

# ============================================================
# BASIS-FELDER (immer sichtbar)
# ============================================================

input_fields = schema.get('input_fields', [])
basis_fields = [f for f in input_fields if f.get('category') == 'basis']

if basis_fields:
    st.markdown("**Basis-Daten**")
    cols = st.columns(len(basis_fields))
    for col, field_def in zip(cols, basis_fields):
        with col:
            generate_input_field(field_def, evaluator, person['daten'], mode_id='basis')

st.markdown("---")

# ============================================================
# PERSONEN-FELDER
# ============================================================

person_fields = [f for f in input_fields if f.get('category') == 'person']

if person_fields:
    st.markdown("**Personen-Daten**")
    cols = st.columns(len(person_fields))
    for col, field_def in zip(cols, person_fields):
        if should_show_field(field_def, evaluator):
            with col:
                generate_input_field(field_def, evaluator, person['daten'], mode_id='person')

st.markdown("---")

# ============================================================
# BERECHNUNGS-FELDER
# ============================================================

berechnung_fields = [
    f for f in input_fields 
    if f.get('category') == 'berechnung' 
    and should_show_field(f, evaluator)
]

if berechnung_fields:
    st.markdown("**Berechnungsparameter**")
    num_cols = min(len(berechnung_fields), 3)
    cols = st.columns(num_cols)
    
    for i, field_def in enumerate(berechnung_fields):
        with cols[i % num_cols]:
            generate_input_field(field_def, evaluator, person['daten'], mode_id='berechnung')

st.markdown("---")

# ============================================================
# ZEITRAUM-TABELLE
# ============================================================

# Finde ersten Mode mit Zeitraum-Tabelle
zeitraum_mode = next(
    (m for m in modes if 'zeitraum_tabelle' in m and m['zeitraum_tabelle'].get('enabled')),
    None
)

if zeitraum_mode:
    show_zeitraum_tabelle_from_schema(
        evaluator,
        firma,
        evaluator.input_data.get('eintrittsdatum', '2000-01-01'),
        evaluator.input_data.get('austrittsdatum', '2025-02-01'),
        versorgungsordnung,
        zeitraum_mode['zeitraum_tabelle']
    )

# ============================================================
# ERGEBNISSE
# ============================================================

import re

st.markdown("---")
st.subheader("Berechnungs-Ergebnisse")
st.caption("Automatische Berechnung nach jeder Änderung")

evaluator.log.clear()

# ── Override-Warnung bei geänderten Eingaben ─────────────────
if hasattr(evaluator, 'input_changed') and evaluator.input_changed and evaluator.overrides:
    geaenderte = ', '.join(sorted(evaluator.input_changed))
    anzahl_overrides = len(evaluator.overrides)
    
    st.warning(
        f"⚠️ **Eingaben geändert:** {geaenderte}  \n"
        f"Es gibt {anzahl_overrides} manuelle Überschreibung(en). "
        f"Diese basieren möglicherweise auf veralteten Eingaben."
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🗑️ Alle Overrides löschen", use_container_width=True):
            evaluator.clear_all_overrides()
            st.rerun()
    with col2:
        st.caption(
            "Overrides werden beibehalten. Wenn Sie neue Berechnungen wollen, "
            "löschen Sie die Overrides oder deaktivieren Sie sie einzeln."
        )

# ── Effektives Austrittsdatum (min von Eingabe und Insolvenzdatum) ────────────
eff_austritt_str, ist_insolvenzfall = effektives_austrittsdatum(
    versorgungsordnung,
    evaluator.input_data.get('austrittsdatum', '')
)
if ist_insolvenzfall:
    st.warning(
        f"Insolvenzfall: Maßgebliches Austrittsdatum ist das Insolvenzdatum "
        f"**{versorgungsordnung['insolvenzdatum']}** "
        f"(eingegeben: {evaluator.input_data.get('austrittsdatum', '—')})"
    )
    evaluator.set_input('austrittsdatum', eff_austritt_str)

# ── Unverfallbarkeits-Check ──────────────────────────────────
uv = pruefe_unverfallbarkeit(
    versorgungsordnung,
    evaluator.input_data.get('eintrittsdatum', ''),
    evaluator.input_data.get('austrittsdatum', ''),
    evaluator.input_data.get('geburtsdatum', ''),
)

if uv['erfuellt'] is None:
    st.warning(f"Unverfallbarkeit: Daten fehlen — {uv['begruendung']}")
    st.stop()
elif not uv['erfuellt']:
    st.error(f"Unverfallbarkeit nicht gegeben — {uv['begruendung']}")
    with st.expander("Details"):
        d = uv['details']
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Zusage (VO)",          d.get('zusagedatum_vo', '—'))
        col2.metric("Zusage (konkret)",      d.get('zusagedatum_konkret', '—'))
        col3.metric("Alter bei Austritt",    f"{d.get('alter_bei_austritt', '—')} J.")
        col4.metric("Dienstjahre",           f"{d.get('dienstjahre', '—')} J.")
        col5.metric("Rechtsgrundlage",       uv.get('rechtsgrundlage', '—'))
    st.stop()
else:
    with st.expander(f"Unverfallbarkeit gegeben — {uv['rechtsgrundlage']}", expanded=False):
        st.caption(uv['begruendung'])
        d = uv['details']
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Zusage (VO)",           d.get('zusagedatum_vo', '—'))
        col2.metric("Zusage (konkret)",       d.get('zusagedatum_konkret', '—'))
        col3.metric("Alter bei Austritt",     f"{d.get('alter_bei_austritt', '—')} J.")
        col4.metric("Dienstjahre",            f"{d.get('dienstjahre', '—')} J.")
        col5.metric("Mindestvoraussetzung",   f"≥ {d.get('mindestalter','—')} J. / {d.get('mindestdauer','—')} DJ")


def format_wert(wert, einheit):
    """Formatiert einen Wert mit Einheit"""
    if isinstance(wert, float):
        return f"{wert:,.2f} {einheit}".strip()
    return f"{wert} {einheit}".strip()


def resolve_placeholders(text, versorgungsordnung):
    """Ersetzt {parameter} Platzhalter generisch aus der Versorgungsordnung"""
    if not text:
        return text
    params = versorgungsordnung.get('parameter', {})
    for placeholder in re.findall(r'\{(\w+)\}', text):
        if placeholder in params:
            value = params[placeholder]
        elif placeholder in versorgungsordnung:
            value = versorgungsordnung[placeholder]
        else:
            continue
        text = text.replace(f"{{{placeholder}}}", str(value))
    return text


def show_leistungsteil_details(teil, wert, versorgungsordnung):
    """Zeigt Details in 3 Spalten: Art der Leistung | Wert (individuell) | Beschreibung (abstrakt)"""

    def row(art, wert_str, beschreibung):
        col1, col2, col3 = st.columns([3, 4, 4])
        with col1:
            st.markdown(art)
        with col2:
            st.markdown(f"**{wert_str}**" if wert_str else "")
        with col3:
            st.caption(beschreibung if beschreibung else "")

    # 1. Art der Leistung
    row("Art der Leistung", teil.get('art', teil['label']), "")

    # 2. Höhe der Leistung
    einheit = teil.get('einheit', 'EUR')
    formel = resolve_placeholders(teil.get('formel_anzeige', ''), versorgungsordnung)
    row("Höhe der Leistung",
        format_wert(wert, einheit) if wert is not None else "",
        formel)

    # 3. Erster Termin
    termin = teil.get('erster_termin', {})
    termin_wert = ""
    geburtsdatum = evaluator.input_data.get('geburtsdatum')
    if geburtsdatum and termin.get('type') == 'calculated':
        try:
            from datetime import date
            geb = date.fromisoformat(geburtsdatum)
            jahre = versorgungsordnung.get('parameter', {}).get('regelaltersgrenze', 67)
            termin_datum = date(geb.year + jahre, geb.month, 1)
            termin_wert = termin_datum.strftime('%d.%m.%Y')
        except Exception:
            pass
    row("Erster Termin",
        termin_wert,
        termin.get('beschreibung', ''))

    # 4. Dynamisierung vor Rentenbeginn
    anpassung = teil.get('anpassungsregeln', {})
    dyn_vor = anpassung.get('dynamisierung_vor_rentenbeginn', {})
    if dyn_vor.get('aktiviert'):
        row("Dynamisierung vor Rentenbeginn",
            dyn_vor.get('beschreibung', ''),
            "")

    # 5. Dynamisierung ab Rentenbeginn
    dyn_ab = anpassung.get('dynamisierung_ab_rentenbeginn', anpassung.get('dynamisierung', {}))
    if dyn_ab.get('aktiviert'):
        row("Dynamisierung ab Rentenbeginn",
            dyn_ab.get('beschreibung', ''),
            "")

    # 6. Vorzeitige Inanspruchnahme
    vorzeitig = teil.get('vorzeitige_leistung', {})
    if vorzeitig.get('erlaubt'):
        abschlag = vorzeitig.get('abschlag', {})
        row("Vorzeitige Inanspruchnahme",
            abschlag.get('beschreibung', ''),
            vorzeitig.get('beschreibung', ''))

    # 7. Invalidenleistung
    invalide = teil.get('invalidenleistung', {})
    if invalide.get('aktiviert'):
        hoehe = invalide.get('hoehe', {})
        if hoehe.get('type') == 'conditional':
            # Bedingung auswerten und passenden Branch zeigen
            bedingung = hoehe.get('bedingung', {})
            feld_wert = evaluator.input_data.get(bedingung.get('field', ''))
            param_name = bedingung.get('parameter')
            vergleichswert = versorgungsordnung.get(param_name) or versorgungsordnung.get('parameter', {}).get(param_name) if param_name else bedingung.get('value')
            operator = bedingung.get('operator', '<')
            
            bedingung_erfuellt = False
            if feld_wert and vergleichswert:
                if operator == '<':
                    bedingung_erfuellt = feld_wert < vergleichswert
                elif operator == '<=':
                    bedingung_erfuellt = feld_wert <= vergleichswert
                elif operator == '>':
                    bedingung_erfuellt = feld_wert > vergleichswert
                elif operator == '>=':
                    bedingung_erfuellt = feld_wert >= vergleichswert
            
            branch = hoehe.get('if_true') if bedingung_erfuellt else hoehe.get('if_false')
            hoehe_text = branch.get('beschreibung', '') if branch else ''
        else:
            hoehe_text = hoehe.get('beschreibung', '')
        wartezeit = invalide.get('wartezeit', {})
        row("Invalidenleistung",
            hoehe_text,
            wartezeit.get('beschreibung', ''))

    # 8. Hinterbliebenenleistung — alle in einer Zeile zusammengefasst
    todesfall = teil.get('todesfallleistung', {})
    hb_teile = []
    hb_beschreibung = todesfall.get('beschreibung', '')

    witwe = todesfall.get('witwenrente', {})
    if witwe.get('aktiviert'):
        hb_teile.append(witwe.get('hoehe', {}).get('beschreibung', ''))

    waise = todesfall.get('waisenrente', {})
    if waise.get('aktiviert'):
        hb_teile.append(waise.get('hoehe', {}).get('beschreibung', ''))

    sterbegeld_hb = todesfall.get('sterbegeld', {})
    if sterbegeld_hb.get('aktiviert'):
        hb_teile.append(sterbegeld_hb.get('hoehe', {}).get('beschreibung', ''))

    if hb_teile:
        row("Hinterbliebenenleistung",
            ", ".join(hb_teile),
            hb_beschreibung)

    # 9. Rechtsgrundlage
    rg = teil.get('rechtsgrundlage', {})
    if rg:
        row("Rechtsgrundlage",
            rg.get('volltext', f"{rg.get('dokument', '')} {rg.get('paragraf', '')}").strip(),
            "")


try:
    leistungsteile = schema.get('leistungsteile', schema.get('calculated_fields', []))

    # Gruppiere nach Art
    berechnungsgrundlagen = [t for t in leistungsteile if t.get('art') == 'Berechnungsgrundlage']
    renten = [t for t in leistungsteile if 'Rente' in t.get('art', '')]
    sonstige = [t for t in leistungsteile if t not in berechnungsgrundlagen and t not in renten]

    # Fehlende Pflichtfelder prüfen und abfragen
    input_fields = schema.get('input_fields', [])
    missing = evaluator.get_missing_inputs(input_fields)
    
    if missing:
        st.warning(f"Für die Berechnung werden noch {len(missing)} Angabe(n) benötigt:")
        for field in missing:
            fid = field['id']
            widget_key = f"missing_{fid}"
            label = field.get('label', fid)
            ftype = field.get('type', 'number')
            
            if ftype == 'number':
                val = st.number_input(
                    label,
                    min_value=field.get('min', 0.0),
                    max_value=field.get('max', 100000.0),
                    value=float(field.get('default', 0.0)),
                    step=field.get('step', 100.0),
                    key=widget_key,
                    help=field.get('help', '')
                )
                if val and val > 0:
                    evaluator.set_input(fid, val)
            
            elif ftype == 'date':
                val = st.date_input(label, key=widget_key, help=field.get('help', ''))
                if val:
                    evaluator.set_input(fid, str(val))
        
        st.markdown("---")

    def zeige_pruef_widget(teil_id, wert, einheit, label, ist_override):
        """
        Zeigt Override-Eingabe und Prüf-Checkbox für ein berechnetes Ergebnis.
        Gibt (wert_final, ist_valide) zurück.
        """
        status = pruefstatus(pruefungen, aktuelle_firma_id, teil_id,
                             aktuelle_person_id, ist_override, aktueller_wert=wert)

        # Override-Eingabe
        col_wert, col_override = st.columns([3, 2])
        with col_wert:
            st.metric(label, format_wert(wert, einheit))
        with col_override:
            override_aktiv = st.checkbox(
                "Manuell überschreiben",
                value=ist_override,
                key=f"ovr_check_{teil_id}"
            )
            if override_aktiv:
                # Widget-Key für diesen Override
                widget_key_val = f"ovr_val_{teil_id}"
                
                # Initialisierung NUR wenn Key nicht existiert
                # UND noch kein Override gesetzt ist
                if widget_key_val not in st.session_state:
                    # Wenn bereits ein Override existiert, den nehmen, sonst berechneten Wert
                    initial = evaluator.overrides.get(teil_id, wert or 0.0)
                    st.session_state[widget_key_val] = float(initial)
                
                # Callback um Override zu synchronisieren
                def sync_override():
                    evaluator.override(teil_id, st.session_state[widget_key_val])
                
                # Widget ohne value= - nutzt nur session_state
                st.number_input(
                    "Wert",
                    step=1.0,
                    format="%.2f",
                    key=widget_key_val,
                    label_visibility="collapsed",
                    on_change=sync_override
                )
                
                # Override-Wert aus Widget holen
                wert = st.session_state[widget_key_val]
                evaluator.override(teil_id, wert)
            else:
                if ist_override:
                    evaluator.clear_override(teil_id)
                # Widget-Key löschen wenn Override deaktiviert wird
                widget_key_val = f"ovr_val_{teil_id}"
                if widget_key_val in st.session_state:
                    del st.session_state[widget_key_val]

        ist_override_aktuell = teil_id in evaluator.overrides
        status = pruefstatus(pruefungen, aktuelle_firma_id, teil_id,
                             aktuelle_person_id, ist_override_aktuell, aktueller_wert=wert)

        # Prüf-Status anzeigen
        if status['valide']:
            if status['grund'] == 'override':
                st.caption("✏️ Manuell überschrieben — kein Prüfnachweis erforderlich")
            elif status['grund'] == 'wert_bekannt':
                st.caption(f"✅ Wert bereits geprüft — bei {status['anzahl']} AN ({status['anzahl_werte']} versch. Werte)")
            elif status['grund'] == 'diverse_werte':
                st.caption(f"✅ Formel freigegeben — {status['anzahl_werte']} verschiedene Werte bei {status['anzahl']} AN geprüft")
            elif status['grund'] == 'individuell':
                st.caption(f"👤 Von Ihnen geprüft · Firma: {status['anzahl']} AN, {status['anzahl_werte']} versch. Werte")
        else:
            if status['anzahl'] >= 3:
                st.warning(f"⚠️ Neuer Wert — bitte prüfen (Firma: {status['anzahl']} AN geprüft, aber dieser Wert ist neu)")
            else:
                st.caption(f"⚠️ Formel noch ungeprüft · Firma: {status['anzahl']}/3 AN, {status['anzahl_werte']} versch. Werte")
            
            geprueft = st.checkbox(
                f"Formel für diese Firma als richtig bestätigen (AN #{status['anzahl']+1})",
                value=False,
                key=f"pruef_{teil_id}",
                help="Wenn dieser Wert oder 3 verschiedene Werte geprüft wurden, gilt die Formel als freigegeben"
            )
            if geprueft:
                # Extrahiere relevante Input-Werte für diese Formel
                relevante_inputs = formel_abhaengigkeiten.get(teil_id, [])
                input_werte = {}
                for inp in relevante_inputs:
                    if inp in evaluator.input_data:
                        input_werte[inp] = evaluator.input_data[inp]
                
                erfolg = registriere_pruefung(pruefungen, aktuelle_firma_id, teil_id,
                                               aktuelle_person_id, float(wert or 0), 
                                               input_werte=input_werte)
                if not erfolg:
                    st.error("⚠️ Dieser AN wurde bereits geprüft. Pro AN ist nur eine Prüfung möglich.")
                st.rerun()

        return wert, status['valide']

    # ── Berechnungsgrundlagen ────────────────────────────────────
    if berechnungsgrundlagen:
        with st.expander("Berechnungsgrundlagen", expanded=True):
            for teil in berechnungsgrundlagen:
                try:
                    wert       = evaluator.get_value(teil['id'])
                    ist_ovr    = teil['id'] in evaluator.overrides
                    zeige_pruef_widget(
                        teil['id'], wert,
                        teil.get('einheit', ''),
                        teil['label'],
                        ist_ovr
                    )
                except Exception as e:
                    st.warning(f"{teil['label']}: {e}")

    # ── Renten — Hauptergebnisse ─────────────────────────────────
    alle_valide = True
    if renten:
        for teil in renten:
            try:
                wert    = evaluator.get_value(teil['id'])
                ist_ovr = teil['id'] in evaluator.overrides

                wert_final, valide = zeige_pruef_widget(
                    teil['id'], wert,
                    teil.get('einheit', 'EUR'),
                    teil.get('art', teil['label']),
                    ist_ovr
                )
                if not valide:
                    alle_valide = False

                with st.expander(f"Details: {teil['label']}", expanded=False):
                    show_leistungsteil_details(teil, wert_final, versorgungsordnung)

            except KeyError as e:
                st.warning(f"Eingabe fehlt: {e} wird für diese Berechnung benötigt.")
                alle_valide = False
            except ValueError as e:
                st.warning(str(e))
                alle_valide = False
            except Exception as e:
                st.error(f"Fehler bei {teil['label']}: {e}")
                alle_valide = False

    # ── Sonstige Leistungen (z.B. Sterbegeld) ───────────────────
    if sonstige:
        st.markdown("---")
        st.markdown("**Weitere Leistungen**")
        for teil in sonstige:
            try:
                wert    = evaluator.get_value(teil['id'])
                ist_ovr = teil['id'] in evaluator.overrides

                wert_final, valide = zeige_pruef_widget(
                    teil['id'], wert,
                    teil.get('einheit', 'EUR'),
                    teil.get('art', teil['label']),
                    ist_ovr
                )
                if not valide:
                    alle_valide = False

                with st.expander(f"Details: {teil['label']}", expanded=False):
                    show_leistungsteil_details(teil, wert_final, versorgungsordnung)

            except Exception as e:
                st.error(f"Fehler bei {teil['label']}: {e}")
                alle_valide = False

    if not alle_valide:
        st.info("Bitte alle Ergebnisse prüfen oder überschreiben — m/n-Berechnung wird trotzdem angezeigt.")

    # ── m/n-Regel ──────────────────────────────────────────────
    st.markdown("---")

    # Vollleistung = letzter berechneter/overridden Renten-Wert
    vollleistung = None
    vollleistung_label = ''
    for teil in renten:
        if 'monatlich' in teil['id'].lower() or teil == renten[0]:
            try:
                vollleistung = evaluator.overrides.get(teil['id']) or evaluator.get_value(teil['id'])
                vollleistung_label = teil.get('art', teil['label'])
                break
            except Exception:
                pass

    mn = berechne_mn_regel(
        versorgungsordnung,
        evaluator.input_data.get('eintrittsdatum', ''),
        eff_austritt_str,
        evaluator.input_data.get('geburtsdatum', ''),
        vollleistung,
        zeitraeume=evaluator.input_data.get('zeitraeume')
    )

    if 'fehler' in mn:
        st.warning(f"m/n-Regel: {mn['fehler']}")
    else:
        gekuerzt = mn.get('gekuerzte_leistung')
        label = f"Ratierliche Leistung (m/n) — {mn['faktor_anzeige']}"
        if gekuerzt is not None:
            st.metric(label, f"{gekuerzt:,.2f} EUR/Monat")

        with st.expander("Details m/n-Regel (§ 2 BetrAVG)", expanded=False):
            def mn_row(art, wert, beschreibung=""):
                c1, c2, c3 = st.columns(3)
                c1.markdown(art)
                c2.markdown(f"**{wert}**" if wert else "")
                c3.caption(beschreibung)

            mn_row("Individueller Zusagebeginn", mn['zusage_beginn'],
                   "max(VO-Zusagedatum, Eintrittsdatum)")
            mn_row("Austritt (maßgeblich)",      mn['austritt'],
                   "Insolvenzdatum" if ist_insolvenzfall else "Eingegebenes Austrittsdatum")
            mn_row("Beginn Altersleistung (VO)", mn['beginn_altersleistung'],
                   f"Regelaltersgrenze {versorgungsordnung.get('parameter',{}).get('regelaltersgrenze',67)} Jahre")
            mn_row("Gesetzl. Rentenbeginn",      mn['gesetzl_rentenbeginn'],
                   f"Veränderungssperre: {mn['gesetzl_rentenbeginn_regel']} (Rechtslage zum {mn['insolvenzdatum']})")
            mn_row("Maximales Endalter (n-Basis)",mn['max_endalter'],
                   "max(min(Beginn Altersleistung, gesetzl. Rente), Austritt)")
            mn_row("n (theoretisch erreichbar)",  f"{mn['n_tage']} Tage ({mn['n_jahre']:.2f} Jahre)",
                   "Zusagebeginn → Maximales Endalter — taggenau")
            mn_row("m (anrechenbare Dienstzeit)", f"{mn['m_tage']} Tage ({mn['m_jahre']:.2f} Jahre)",
                   "Summe Zeiträume mit als_dienstzeit=true — taggenau" if evaluator.input_data.get('zeitraeume') else "Fallback: Austritt − Zusagebeginn — taggenau")
            mn_row("m/n-Faktor",                  f"{mn['faktor']*100:.4f}%", "")
            if gekuerzt is not None:
                mn_row("Ratierliche Leistung",    f"{gekuerzt:,.2f} EUR/Monat",
                       f"{vollleistung_label} {vollleistung:,.2f} × {mn['faktor']*100:.4f}%")

            # Zeitraum-Detailtabelle wenn vorhanden
            if mn.get('m_details'):
                st.markdown("**Anrechenbare Zeiträume (m):**")
                header = st.columns([2, 2, 1, 1])
                header[0].caption("Von"); header[1].caption("Bis")
                header[2].caption("Tage"); header[3].caption("TZ-Faktor")
                for zr in mn['m_details']:
                    cols = st.columns([2, 2, 1, 1])
                    cols[0].text(zr['von']); cols[1].text(zr['bis'])
                    cols[2].text(zr['tage']); cols[3].text(f"{zr['teilzeitfaktor']:.2f}")

    # Log
    if evaluator.log:
        with st.expander("Berechnungs-Log", expanded=False):
            for entry in evaluator.log:
                st.text(entry)

except Exception as e:
    st.warning("Berechnung noch nicht möglich")
    st.info(str(e))
    with st.expander("Details"):
        st.text(str(e))
        if evaluator.log:
            for entry in evaluator.log:
                st.text(entry)

# ============================================================
# AKTIONEN
# ============================================================

st.markdown("---")

if st.button("Andere Person wählen", use_container_width=True):
    st.session_state.firma_id = None
    st.session_state.person_id = None
    st.session_state.evaluator = None
    st.session_state.zeitraeume = None
    st.switch_page("pages/1_Auswahl.py")
