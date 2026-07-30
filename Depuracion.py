"""
Transcripción Bitácora v4.0
Sistema de transcripción WhatsApp → Markdown + Corrección de tildes
Estilo consola Matrix - Minimalista
Sin dependencias externas (solo streamlit)

MEJORAS v4.0:
- Tildes diacríticas con análisis de contexto (el/él, tu/tú, si/sí, mas/más...)
- Distancia de Levenshtein real para sugerencias
- Diccionario expandido con conjugaciones de verbos
- Capitalización inteligente post-punto
- Regex de parseo corregidos
- Reglas de acentuación mejoradas
"""
import streamlit as st
import re
import unicodedata
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import random

# --- Configuración de página ---
st.set_page_config(
    page_title="Transcripción Bitácora",
    page_icon="⌨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilo Matrix completo (consola) ---
st.markdown("""
<style>
/* Fondo negro puro */
.stApp {
    background: #0a0a0a !important;
}
/* Todos los textos en verde neón */
.stApp, .stApp * {
    font-family: 'Courier New', monospace !important;
}
h1, h2, h3, .main-header {
    color: #00ff41 !important;
    text-shadow: 0 0 5px #00ff41;
    letter-spacing: 2px;
}
h1 { font-size: 2.5rem; }
/* Cajas de texto estilo terminal */
.stTextArea textarea {
    background: #000000 !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
    font-size: 14px !important;
}
.stTextArea textarea:focus {
    box-shadow: 0 0 20px rgba(0,255,65,0.2) !important;
}
/* Botones consola */
.stButton button {
    background: #000000 !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
    font-weight: bold !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    box-shadow: 0 0 10px rgba(0,255,65,0.2);
    transition: all 0.3s !important;
}
.stButton button:hover {
    background: #00ff41 !important;
    color: #000000 !important;
    box-shadow: 0 0 30px #00ff41;
    transform: scale(1.02);
}
.stButton button:disabled {
    opacity: 0.3 !important;
    cursor: not-allowed !important;
}
/* Checkboxes y labels */
.stCheckbox label {
    color: #00cc33 !important;
    font-size: 0.9rem !important;
}
.stCheckbox input[type="checkbox"] {
    accent-color: #00ff41 !important;
}
/* Selectbox y otros inputs */
.stSelectbox select, .stTextInput input {
    background: #000000 !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
    font-family: 'Courier New', monospace !important;
}
/* Código (resultado) */
.stCodeBlock {
    background: #000000 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
}
.stCodeBlock code {
    color: #00ff41 !important;
    font-family: 'Courier New', monospace !important;
}
/* Métricas */
.css-1xarl3l {
    background: #000000 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
}
.css-1xarl3l label {
    color: #00cc33 !important;
}
.css-1xarl3l .css-1ht1j8u {
    color: #00ff41 !important;
    text-shadow: 0 0 10px rgba(0,255,65,0.3);
}
/* Sidebar */
.css-1d391kg {
    background: #000000 !important;
    border-right: 1px solid #00ff41 !important;
}
.css-1d391kg .stMarkdown {
    color: #00cc33 !important;
}
.css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
    color: #00ff41 !important;
    text-shadow: 0 0 10px rgba(0,255,65,0.3);
}
/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #000000;
}
::-webkit-scrollbar-thumb {
    background: #00ff41;
    border-radius: 0;
}
::-webkit-scrollbar-thumb:hover {
    background: #00cc33;
    box-shadow: 0 0 20px rgba(0,255,65,0.5);
}
/* Línea separadora */
hr {
    border: 0;
    border-top: 1px solid #00ff41;
    opacity: 0.3;
    margin: 20px 0;
}
/* Mensajes de estado */
.success-box {
    background: rgba(0,255,65,0.05);
    border-left: 4px solid #00ff41;
    padding: 0.8rem 1rem;
    color: #00ff41;
    font-family: 'Courier New', monospace;
    margin: 10px 0;
}
.warning-box {
    background: rgba(255,215,0,0.05);
    border-left: 4px solid #ffd700;
    padding: 0.8rem 1rem;
    color: #ffd700;
    font-family: 'Courier New', monospace;
    margin: 10px 0;
}
.error-box {
    background: rgba(255,0,0,0.05);
    border-left: 4px solid #ff0044;
    padding: 0.8rem 1rem;
    color: #ff4444;
    font-family: 'Courier New', monospace;
    margin: 10px 0;
}
/* Debug/No parseadas */
.debug-box {
    background: rgba(255,0,68,0.05);
    border: 1px solid #ff0044;
    padding: 10px;
    font-family: 'Courier New', monospace;
    color: #ff6666;
    font-size: 0.8rem;
    margin: 10px 0;
}
.debug-box code {
    color: #ff4444;
    background: #1a0000;
    padding: 2px 6px;
    display: block;
    margin: 2px 0;
    border-left: 2px solid #ff0044;
}
/* Blink para efecto Matrix */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
.blink {
    animation: blink 1s step-end infinite;
}
/* Etiquetas de diccionario */
.dict-tag {
    background: rgba(0,255,65,0.1);
    border: 1px solid #00ff41;
    padding: 0.2rem 0.6rem;
    border-radius: 0;
    margin: 0.2rem;
    display: inline-block;
    font-size: 0.75rem;
    color: #00ff41;
    box-shadow: 0 0 10px rgba(0,255,65,0.1);
}
/* Footer */
.footer {
    text-align: center;
    color: #006622;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    opacity: 0.6;
    margin-top: 20px;
    border-top: 1px solid #00ff41;
    padding-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# --- Inicialización de estado ---
def init_state():
    defaults = {
        'texto_salida': '',
        'diccionario_personal': set(),
        'historial': [],
        'contador': 0,
        'debug_lines': [],
        'matrix_effect': True
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================================
# CORRECTOR ORTOGRÁFICO MEJORADO v4.0
# ============================================================================
class CorrectorOrtografico:
    """Corrector con análisis contextual, Levenshtein y tildes diacríticas."""
    
    def __init__(self):
        self.personal = st.session_state.diccionario_personal
        self.base = self._cargar_diccionario_base()
        self.cache = {}
        self.reglas_acento = self._cargar_reglas_acento()
        self.reglas_errores = self._cargar_reglas_errores()
        self.reglas_diacriticas = self._cargar_reglas_diacriticas()
        self.verbos_comunes = self._cargar_verbos_comunes()
    
    # --- Diccionario base expandido ---
    def _cargar_diccionario_base(self) -> set:
        base = {
            # Pronombres y artículos
            'yo','tú','él','ella','ello','nosotros','vosotros','ellos','ellas',
            'usted','ustedes','vos',
            'mi','ti','sí','conmigo','contigo','consigo',
            'con','sin','para','por','de','en','a','ante','bajo','cabe',
            'contra','desde','durante','entre','hacia','hasta','mediante
