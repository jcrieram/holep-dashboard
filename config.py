"""
Configuración del Dashboard HoLEP — Dr. Juan Carlos Riera M.
Edita solo este archivo si cambia el Sheet ID o la API Key.
"""

SHEET_ID  = "13RtylsSwwWg3dIhoFXpJW5_mmb2XkcyVlvZWcoYMOiw"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Google Gemini — se lee desde st.secrets en Streamlit Cloud, o directamente en local
def _get_gemini_key():
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return "AIzaSyBYBgf6p2wKA-iS7HDKbiTYoigC4n4NZLM"

GEMINI_API_KEY = _get_gemini_key()

# Columnas del sheet (si el sheet cambia de nombres, edita aquí)
COL_NUM       = "Marca temporal"
COL_CLINICA   = "Clinica"
COL_NOMBRE    = "Nombre Paciente"
COL_RUT       = "RUT"
COL_EDAD      = "Edad"
COL_FECHA     = "Fecha de cirugía"
COL_VOLUMEN   = "Volumen Próstata en Gr "
COL_LITIASIS  = "Litiasis vesical "
COL_RPM_PRE   = "RPM en (%)"
COL_TIEMPO    = "Tiempo de Cirugía (minutos)"
COL_PESO      = "Peso obtenido en pabellón (Gr)"
COL_REINGRESO = "Reingreso"
COL_MOT_REING = "Motivo reingreso"
COL_INCONT    = "Incontinencia"
COL_BIOPSIA   = "Biopsia (Gr)"
COL_HALLAZGO  = "Hallazgo Biosia"
COL_COMPLIC   = "Complicaciones e incidentes"
COL_PESO_ECO  = "Peso Eco Postop"
COL_RPM_POST  = "RPM %"
