"""
BITÁCORA CYBERPUNK v2.0 - Streamlit
Sistema de integración WhatsApp → Joplin
Estética: Matrix/Cyberpunk con efectos de consola
"""

import streamlit as st
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import json
import time
import random

# --- Configuración de la página ---
st.set_page_config(
    page_title="BITÁCORA CYBERPUNK",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CYBERPUNK MATRIX ---
st.markdown("""
<style>
    /* Fondo Matrix */
    .stApp {
        background: #0a0a0a !important;
        background-image: 
            linear-gradient(rgba(0, 255, 65, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 65, 0.03) 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    /* Texto principal estilo terminal */
    .main-header {
        font-family: 'Courier New', monospace;
        font-size: 2.8rem;
        font-weight: bold;
        color: #00ff41;
        text-align: center;
        text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 40px #00ff41;
        animation: glow 2s ease-in-out infinite alternate;
        letter-spacing: 8px;
        border-bottom: 2px solid #00ff41;
        padding-bottom: 20px;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
        to { text-shadow: 0 0 20px #00ff41, 0 0 40px #00ff41, 0 0 60px #00ff41; }
    }
    
    .sub-header {
        font-family: 'Courier New', monospace;
        font-size: 1rem;
        color: #00cc33;
        text-align: center;
        opacity: 0.7;
        letter-spacing: 4px;
        margin-bottom: 2rem;
        border: 1px solid #00ff41;
        padding: 10px;
        background: rgba(0, 255, 65, 0.05);
        border-radius: 4px;
    }
    
    /* Cajas tipo terminal */
    .terminal-box {
        background: rgba(0, 0, 0, 0.8);
        border: 1px solid #00ff41;
        border-radius: 4px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.1);
    }
    
    .success-box {
        background: rgba(0, 255, 65, 0.05);
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #00ff41;
        color: #00ff41;
        font-family: 'Courier New', monospace;
    }
    
    .warning-box {
        background: rgba(255, 215, 0, 0.05);
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #ffd700;
        color: #ffd700;
        font-family: 'Courier New', monospace;
    }
    
    .error-box {
        background: rgba(255, 0, 0, 0.05);
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #ff0044;
        color: #ff0044;
        font-family: 'Courier New', monospace;
    }
    
    /* Inputs estilo terminal */
    .stTextArea textarea {
        background: rgba(0, 0, 0, 0.9) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    
    .stTextArea textarea:focus {
        border-color: #00ff41 !important;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.2) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #006622 !important;
        font-style: italic;
    }
    
    /* Botones cyberpunk */
    .stButton button {
        background: rgba(0, 0, 0, 0.8) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s !important;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    
    .stButton button:hover {
        background: #00ff41 !important;
        color: #000000 !important;
        box-shadow: 0 0 30px rgba(0, 255, 65, 0.4) !important;
        transform: scale(1.02);
        border-color: #00ff41 !important;
    }
    
    .stButton button:disabled {
        opacity: 0.3 !important;
        cursor: not-allowed !important;
    }
    
    /* Checkboxes cyberpunk */
    .stCheckbox label {
        color: #00cc33 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .stCheckbox input[type="checkbox"] {
        accent-color: #00ff41 !important;
    }
    
    /* Selectbox cyberpunk */
    .stSelectbox select {
        background: rgba(0, 0, 0, 0.9) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Code blocks - Matrix style */
    .stCodeBlock {
        background: rgba(0, 0, 0, 0.9) !important;
        border: 1px solid #00ff41 !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.1);
    }
    
    .stCodeBlock code {
        color: #00ff41 !important;
    }
    
    /* Sidebar cyberpunk */
    .css-1d391kg {
        background: rgba(0, 0, 0, 0.95) !important;
        border-right: 1px solid #00ff41 !important;
    }
    
    .css-1d391kg .stMarkdown {
        color: #00cc33 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Títulos de sidebar */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #00ff41 !important;
        font-family: 'Courier New', monospace !important;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    /* Métricas cyberpunk */
    .css-1xarl3l {
        background: rgba(0, 0, 0, 0.8) !important;
        border: 1px solid #00ff41 !important;
        border-radius: 4px !important;
        padding: 10px !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.05);
    }
    
    .css-1xarl3l label {
        color: #00cc33 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .css-1xarl3l .css-1ht1j8u {
        color: #00ff41 !important;
        font-family: 'Courier New', monospace !important;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    /* Separador cyberpunk */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #00ff41, transparent);
        margin: 20px 0;
    }
    
    /* Scrollbar cyberpunk */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff41;
        border-radius: 4px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00cc33;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
    }
    
    /* Etiquetas de diccionario */
    .dict-tag {
        background: rgba(0, 255, 65, 0.1);
        border: 1px solid #00ff41;
        padding: 0.2rem 0.6rem;
        border-radius: 2px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
        font-family: 'Courier New', monospace;
        color: #00ff41;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    
    /* Animación de titileo para texto de carga */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    
    .blink {
        animation: blink 1s step-end infinite;
    }
    
    /* Terminal prompt */
    .prompt {
        color: #00ff41;
        font-family: 'Courier New', monospace;
        margin: 5px 0;
    }
    
    .prompt::before {
        content: "> ";
        color: #00ff41;
        opacity: 0.5;
    }
    
    /* Matriz de fondo animado (efecto) */
    .matrix-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
        opacity: 0.03;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 10px,
            rgba(0, 255, 65, 0.05) 10px,
            rgba(0, 255, 65, 0.05) 11px
        );
    }
    
    /* Tooltips cyberpunk */
    .stTooltipIcon {
        color: #00ff41 !important;
    }
    
    /* Input de texto para diccionario */
    .stTextInput input {
        background: rgba(0, 0, 0, 0.9) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .stTextInput input:focus {
        border-color: #00ff41 !important;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.2) !important;
    }
</style>

<div class="matrix-bg"></div>
""", unsafe_allow_html=True)

# --- Inicialización de Estado ---
def init_session_state():
    """Inicializa el estado de la sesión"""
    defaults = {
        'mensajes_procesados': [],
        'texto_salida': '',
        'diccionario_personal': set(),
        'historial': [],
        'contador_procesados': 0,
        'ultima_fecha': datetime.now().strftime('%d-%m-%Y'),
        'modo_edicion': False,
        'palabra_editar': '',
        'matrix_effect': True,
        'scan_lines': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Clases Principales ---

@dataclass
class Mensaje:
    """Representa un mensaje de WhatsApp"""
    fecha: str
    hora: str
    autor: str
    contenido: str
    es_metadato: bool = False
    es_multimedia: bool = False
    es_enlace: bool = False
    es_adjunto: bool = False

class CorrectorOrtografico:
    """Sistema de corrección ortográfica con diccionario personal"""
    
    def __init__(self):
        self._cache_correcciones = {}
        self._diccionario_base = self._cargar_diccionario_base()
        self.diccionario_personal = st.session_state.diccionario_personal
    
    def _cargar_diccionario_base(self) -> set:
        """Carga diccionario base"""
        # Palabras comunes en español
        return {
            'hola', 'como', 'estas', 'bien', 'gracias', 'por', 'favor',
            'buenos', 'dias', 'tardes', 'noches', 'adios', 'hasta', 'luego',
            'si', 'no', 'tal', 'vez', 'casa', 'trabajo', 'amigo', 'familia',
            'tiempo', 'dia', 'semana', 'mes', 'año', 'hoy', 'mañana', 'ayer',
            'feliz', 'triste', 'contento', 'cansado', 'ocupado', 'libre',
            'comer', 'beber', 'dormir', 'leer', 'escribir', 'pensar', 'sentir',
            'filosofia', 'existencia', 'ser', 'estar', 'tener', 'hacer', 'decir',
            'ir', 'venir', 'ver', 'mirar', 'escuchar', 'hablar', 'callar',
            'amor', 'vida', 'muerte', 'sueño', 'realidad', 'conciencia',
            'alma', 'espiritu', 'cuerpo', 'mente', 'razon', 'emocion',
            'mundo', 'universo', 'tiempo', 'espacio', 'energia', 'materia'
        }
    
    def corregir_texto(self, texto: str, solo_seguro: bool = True) -> Tuple[str, List[str]]:
        """Corrige texto y retorna cambios realizados"""
        if not texto:
            return texto, []
        
        cambios = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        
        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            
            if palabra.lower() in self.diccionario_personal:
                continue
            
            if palabra.lower() in self._diccionario_base:
                continue
            
            corregida = self._buscar_correccion(palabra, solo_seguro)
            
            if corregida and corregida != palabra:
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
        
        return texto, cambios
    
    def _buscar_correccion(self, palabra: str, solo_seguro: bool) -> Optional[str]:
        """Busca corrección para una palabra"""
        if palabra in self._cache_correcciones:
            return self._cache_correcciones[palabra]
        
        correcciones = self._reglas_correccion(palabra)
        
        if len(correcciones) == 1:
            self._cache_correcciones[palabra] = correcciones[0]
            return correcciones[0]
        elif not solo_seguro and correcciones:
            self._cache_correcciones[palabra] = correcciones[0]
            return correcciones[0]
        
        return None
    
    def _reglas_correccion(self, palabra: str) -> List[str]:
        """Aplica reglas de corrección"""
        correcciones = []
        palabra_lower = palabra.lower()
        
        reglas = [
            ('filosofia', 'filosofía'),
            ('psicologia', 'psicología'),
            ('sociologia', 'sociología'),
            ('antropologia', 'antropología'),
            ('teologia', 'teología'),
            ('metafisica', 'metafísica'),
            ('epistemologia', 'epistemología'),
            ('axiologia', 'axiología'),
            ('estetica', 'estética'),
            ('etica', 'ética'),
            ('logica', 'lógica'),
            ('poetica', 'poética'),
            ('retorica', 'retórica'),
            ('deberia', 'debería'),
            ('podria', 'podría'),
            ('querria', 'querría'),
            ('tendria', 'tendría'),
            ('habria', 'habría'),
            ('seria', 'sería'),
            ('estaria', 'estaría'),
            ('sabria', 'sabría'),
            ('tenemos', 'tenemos'),
            ('vamos', 'vamos'),
            ('estamos', 'estamos'),
            ('somos', 'somos'),
            ('impreativo', 'imperativo'),
            ('existencialismo', 'existencialismo'),
            ('fenomenologia', 'fenomenología'),
            ('hermeneutica', 'hermenéutica'),
            ('ontologia', 'ontología'),
            ('gnoseologia', 'gnoseología'),
            ('teleologia', 'teleología'),
            ('escatologia', 'escatología'),
            ('soteriologia', 'soteriología'),
            ('cristologia', 'cristología'),
            ('eclesiologia', 'eclesiología'),
            ('mariologia', 'mariología'),
            ('angelologia', 'angelología'),
            ('demonologia', 'demonología')
        ]
        
        for incorrecta, correcta in reglas:
            if palabra_lower == incorrecta:
                correcciones.append(correcta)
        
        # Regla: reemplazar 's' por 'c' en palabras que terminan en 'cion'
        if palabra_lower.endswith('cion') and not palabra_lower.endswith('sion'):
            correcciones.append(palabra[:-4] + 'ción')
        
        return correcciones
    
    def detectar_errores(self, texto: str) -> List[Dict]:
        """Detecta errores dudosos"""
        errores = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        
        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            if palabra.lower() in self.diccionario_personal:
                continue
            if palabra.lower() in self._diccionario_base:
                continue
            
            sugerencias = self._buscar_sugerencias(palabra)
            if sugerencias:
                errores.append({
                    'palabra': palabra,
                    'sugerencias': sugerencias[:3]
                })
        
        return errores
    
    def _buscar_sugerencias(self, palabra: str) -> List[str]:
        """Busca sugerencias para una palabra"""
        sugerencias = []
        correcciones = self._reglas_correccion(palabra)
        sugerencias.extend(correcciones)
        
        if not sugerencias:
            palabra_base = palabra.lower()
            for dict_word in self._diccionario_base:
                if len(dict_word) > 3 and abs(len(dict_word) - len(palabra_base)) <= 2:
                    if self._similitud_simple(palabra_base, dict_word) > 0.7:
                        sugerencias.append(dict_word)
                        if len(sugerencias) >= 3:
                            break
        
        return sugerencias
    
    def _similitud_simple(self, s1: str, s2: str) -> float:
        """Calcula similitud simple entre dos palabras"""
        if not s1 or not s2:
            return 0
        
        matches = sum(1 for a, b in zip(s1, s2) if a == b)
        return matches / max(len(s1), len(s2))

class ProcesadorMensajes:
    """Procesa mensajes de WhatsApp - Soporta múltiples formatos"""
    
    # Formato 1: WhatsApp Web/Desktop (con corchetes)
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.m\.|p\.m\.)?,\s*(\d{1,2}/\d{1,2}/\d{2,4})\]\s*([^:]+):\s*(.*)'
    
    # Formato 2: WhatsApp móvil (sin corchetes)
    PATRON_MOVIL = r'(\d{1,2}/\d{1,2}/\d{2,4})[,\s]+(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.*)'
    
    # Formato 3: Con hora en 24h sin AM/PM
    PATRON_WEB_24H = r'\[(\d{1,2}:\d{2}),\s*(\d{1,2}/\d{1,2}/\d{2,4})\]\s*([^:]+):\s*(.*)'
    
    PATRON_MULTIMEDIA = r'<Multimedia omitido>|IMG[_-]\d+|VIDEO[_-]\d+|\.(jpg|png|gif|mp4|pdf|docx?)'
    PATRON_ADJUNTO = r'Documento omitido|Audio omitido|Archivo omitido|Archivo adjunto'
    PATRON_ENLACE = r'https?://[^\s]+'
    
    def __init__(self):
        self.corrector = CorrectorOrtografico()
        self._cache_fechas = {}
    
    def procesar(self, texto: str) -> List[Mensaje]:
        """Procesa texto y extrae mensajes"""
        mensajes = []
        
        for linea in texto.strip().split('\n'):
            if not linea.strip():
                continue
            
            msg = self._parsear_linea(linea)
            if msg:
                mensajes.append(msg)
        
        return mensajes
    
    def _parsear_linea(self, linea: str) -> Optional[Mensaje]:
        """Parsea una línea de mensaje"""
        # Intentar formato 1: WhatsApp Web con AM/PM
        match = re.match(self.PATRON_WEB, linea)
        if match:
            return self._crear_mensaje_desde_web(match)
        
        # Intentar formato 2: WhatsApp móvil
        match = re.match(self.PATRON_MOVIL, linea)
        if match:
            return self._crear_mensaje_desde_movil(match)
        
        # Intentar formato 3: WhatsApp Web sin AM/PM
        match = re.match(self.PATRON_WEB_24H, linea)
        if match:
            return self._crear_mensaje_desde_web_24h(match)
        
        return None
    
    def _crear_mensaje_desde_web(self, match) -> Mensaje:
        """Crea mensaje desde formato WhatsApp Web"""
        hora = match.group(1)
        ampm = match.group(2) or ''
        fecha_str = match.group(3)
        autor = match.group(4).strip()
        contenido = match.group(5).strip()
        
        hora_24 = self._convertir_hora(hora, ampm)
        fecha = self._formatear_fecha(fecha_str)
        
        return self._crear_mensaje(fecha, hora_24, autor, contenido)
    
    def _crear_mensaje_desde_movil(self, match) -> Mensaje:
        """Crea mensaje desde formato WhatsApp móvil"""
        fecha_str = match.group(1)
        hora = match.group(2)
        autor = match.group(3).strip()
        contenido = match.group(4).strip()
        
        fecha = self._formatear_fecha(fecha_str)
        
        return self._crear_mensaje(fecha, hora, autor, contenido)
    
    def _crear_mensaje_desde_web_24h(self, match) -> Mensaje:
        """Crea mensaje desde formato WhatsApp Web 24h"""
        hora = match.group(1)
        fecha_str = match.group(2)
        autor = match.group(3).strip()
        contenido = match.group(4).strip()
        
        fecha = self._formatear_fecha(fecha_str)
        
        return self._crear_mensaje(fecha, hora, autor, contenido)
    
    def _crear_mensaje(self, fecha: str, hora: str, autor: str, contenido: str) -> Mensaje:
        """Crea objeto Mensaje con detección de metadatos"""
        es_multimedia = bool(re.search(self.PATRON_MULTIMEDIA, contenido, re.IGNORECASE))
        es_enlace = bool(re.search(self.PATRON_ENLACE, contenido))
        es_adjunto = bool(re.search(self.PATRON_ADJUNTO, contenido, re.IGNORECASE))
        es_metadato = es_multimedia or es_enlace or es_adjunto
        
        return Mensaje(
            fecha=fecha,
            hora=hora,
            autor=autor,
            contenido=contenido,
            es_metadato=es_metadato,
            es_multimedia=es_multimedia,
            es_enlace=es_enlace,
            es_adjunto=es_adjunto
        )
    
    def _convertir_hora(self, hora: str, ampm: str) -> str:
        """Convierte hora AM/PM a 24h"""
        if not ampm:
            return hora
        
        try:
            h, m = map(int, hora.split(':'))
            if 'p.m.' in ampm.lower() and h < 12:
                h += 12
            elif 'a.m.' in ampm.lower() and h == 12:
                h = 0
            return f"{h:02d}:{m:02d}"
        except:
            return hora
    
    def _formatear_fecha(self, fecha_str: str) -> str:
        """Formatea fecha a DD-MM"""
        if fecha_str in self._cache_fechas:
            return self._cache_fechas[fecha_str]
        
        try:
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
            resultado = fecha.strftime('%d-%m')
        except ValueError:
            try:
                fecha = datetime.strptime(fecha_str, '%d/%m/%y')
                resultado = fecha.strftime('%d-%m')
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                    resultado = fecha.strftime('%d-%m')
                except ValueError:
                    resultado = fecha_str
        
        self._cache_fechas[fecha_str] = resultado
        return resultado
    
    def limpiar_mensaje(self, msg: Mensaje, eliminar_enlaces: bool = True, 
                        eliminar_adjuntos: bool = True) -> str:
        """Limpia el contenido de un mensaje"""
        contenido = msg.contenido
        
        if eliminar_enlaces:
            contenido = re.sub(self.PATRON_ENLACE, '', contenido)
        
        if eliminar_adjuntos:
            contenido = re.sub(self.PATRON_MULTIMEDIA, '', contenido, flags=re.IGNORECASE)
            contenido = re.sub(self.PATRON_ADJUNTO, '', contenido, flags=re.IGNORECASE)
        
        contenido = re.sub(r'\d{1,2}:\d{2}', '', contenido)
        
        return contenido.strip()
    
    def generar_markdown(self, mensajes: List[Mensaje], opciones: Dict) -> str:
        """Genera markdown formateado"""
        if not mensajes:
            return ""
        
        mensajes_por_dia = defaultdict(list)
        autores = set()
        
        for msg in mensajes:
            if msg.es_metadato and opciones.get('eliminar_adjuntos', True):
                continue
            
            contenido = self.limpiar_mensaje(
                msg,
                eliminar_enlaces=opciones.get('eliminar_enlaces', True),
                eliminar_adjuntos=opciones.get('eliminar_adjuntos', True)
            )
            
            if not contenido:
                continue
            
            autores.add(msg.autor)
            mensajes_por_dia[msg.fecha].append(contenido)
        
        lineas = []
        
        if opciones.get('incluir_titulo', True):
            mes_actual = datetime.now().month
            meses_romanos = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
                            7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'}
            titulo_personalizado = opciones.get('titulo_personalizado', '')
            titulo_mes = meses_romanos.get(mes_actual, '')
            titulo = f"# {titulo_mes}: {titulo_personalizado or datetime.now().strftime('%B')}"
            lineas.append(titulo)
            lineas.append("")
        
        for fecha, contenidos in sorted(mensajes_por_dia.items()):
            lineas.append(f"## {fecha}")
            
            if opciones.get('agrupar', False):
                contenidos = self._agrupar_contenidos(contenidos)
            
            for contenido in contenidos:
                if opciones.get('corregir', False):
                    contenido, _ = self.corrector.corregir_texto(
                        contenido, 
                        solo_seguro=opciones.get('correccion_segura', True)
                    )
                
                lineas.append(contenido)
            
            lineas.append("")
        
        if opciones.get('incluir_estadisticas', False):
            lineas.append("---")
            lineas.append("")
            lineas.append(f"**Estadísticas:**")
            lineas.append(f"- Mensajes procesados: {len(mensajes)}")
            lineas.append(f"- Días: {len(mensajes_por_dia)}")
            lineas.append(f"- Autores: {', '.join(autores)}")
        
        return '\n'.join(lineas)
    
    def _agrupar_contenidos(self, contenidos: List[str]) -> List[str]:
        """Agrupa contenidos cortos consecutivos"""
        agrupados = []
        i = 0
        
        while i < len(contenidos):
            if i + 1 < len(contenidos) and len(contenidos[i]) < 80 and len(contenidos[i+1]) < 80:
                agrupados.append(contenidos[i] + ' ' + contenidos[i+1])
                i += 2
            else:
                agrupados.append(contenidos[i])
                i += 1
        
        return agrupados

# --- Funciones de la UI ---

def mostrar_diccionario_personal():
    """Muestra y gestiona el diccionario personal"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 DICCIONARIO PERSONAL")
    
    if st.session_state.diccionario_personal:
        palabras = sorted(st.session_state.diccionario_personal)
        st.sidebar.markdown(f"**{len(palabras)} palabras cargadas:**")
        
        cols = st.sidebar.columns(3)
        for i, palabra in enumerate(palabras[:30]):
            cols[i % 3].markdown(f'<span class="dict-tag">{palabra}</span>', 
                               unsafe_allow_html=True)
        
        if len(palabras) > 30:
            st.sidebar.markdown(f"... y {len(palabras) - 30} más")
    else:
        st.sidebar.info("⚠️ No hay palabras en el diccionario personal")
    
    st.sidebar.markdown("#### ➕ AGREGAR PALABRA")
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        nueva_palabra = st.text_input("", key="nueva_palabra_input", 
                                     placeholder="ej: Omniutopia",
                                     label_visibility="collapsed")
    with col2:
        if st.button("➕", key="btn_agregar_palabra", use_container_width=True):
            if nueva_palabra and nueva_palabra.strip():
                palabra_limpia = nueva_palabra.strip().lower()
                if palabra_limpia not in st.session_state.diccionario_personal:
                    st.session_state.diccionario_personal.add(palabra_limpia)
                    st.success(f"✅ '{palabra_limpia}' agregada al diccionario")
                    st.rerun()
                else:
                    st.warning(f"⚠️ '{palabra_limpia}' ya existe")
    
    if st.session_state.diccionario_personal:
        st.sidebar.markdown("#### 🗑️ ELIMINAR PALABRA")
        palabra_eliminar = st.sidebar.selectbox(
            "Seleccionar:", 
            options=sorted(st.session_state.diccionario_personal),
            key="select_eliminar",
            label_visibility="collapsed"
        )
        if st.button("🗑️ Eliminar", key="btn_eliminar_palabra"):
            if palabra_eliminar:
                st.session_state.diccionario_personal.discard(palabra_eliminar)
                st.success(f"✅ '{palabra_eliminar}' eliminada")
                st.rerun()
    
    st.sidebar.markdown("#### 📦 IMPORTAR/EXPORTAR")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📤 Exportar", key="btn_exportar_dict", use_container_width=True):
            dict_json = json.dumps(list(st.session_state.diccionario_personal))
            st.download_button(
                label="📥 Descargar JSON",
                data=dict_json,
                file_name="diccionario_personal.json",
                mime="application/json"
            )
    with col2:
        uploaded_file = st.file_uploader(
            "📂 Importar", 
            type=['json'],
            key="upload_dict",
            label_visibility="collapsed"
        )
        if uploaded_file:
            try:
                palabras = json.load(uploaded_file)
                if isinstance(palabras, list):
                    for p in palabras:
                        st.session_state.diccionario_personal.add(p.lower())
                    st.success(f"✅ Importadas {len(palabras)} palabras")
                    st.rerun()
            except:
                st.error("❌ Error al importar archivo")

def mostrar_historial():
    """Muestra el historial de procesamiento"""
    if st.session_state.historial:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📜 HISTORIAL")
        
        for i, entry in enumerate(st.session_state.historial[-5:]):
            with st.sidebar.expander(f"⚡ {entry['fecha']} - {entry['mensajes']} msgs"):
                st.text(entry['preview'][:200] + "...")
                if st.button(f"📋 Usar", key=f"hist_{i}"):
                    st.session_state.texto_salida = entry['contenido']
                    st.rerun()

def mostrar_estadisticas(mensajes: List[Mensaje], texto_salida: str):
    """Muestra estadísticas del procesamiento"""
    if mensajes:
        total_mensajes = len(mensajes)
        mensajes_por_dia = defaultdict(int)
        autores = set()
        palabras_totales = 0
        
        for msg in mensajes:
            mensajes_por_dia[msg.fecha] += 1
            autores.add(msg.autor)
            palabras_totales += len(msg.contenido.split())
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📨 MENSAJES", total_mensajes)
        col2.metric("📅 DÍAS", len(mensajes_por_dia))
        col3.metric("👤 AUTORES", len(autores))
        col4.metric("📝 PALABRAS", palabras_totales)
        
        if texto_salida:
            st.info(f"📄 Texto generado: {len(texto_salida)} caracteres, {len(texto_salida.split())} palabras")

def mostrar_efecto_matrix():
    """Muestra el efecto Matrix en la consola"""
    if st.session_state.matrix_effect:
        matrix_chars = "01"
        matrix_lines = []
        for _ in range(10):
            line = ''.join(random.choice(matrix_chars) for _ in range(50))
            matrix_lines.append(line)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ MATRIX")
        for line in matrix_lines:
            st.sidebar.text(line)

# --- Función Principal ---
def main():
    """Función principal de la app"""
    
    # --- Header Cyberpunk ---
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div class="main-header">⚡ BITÁCORA CYBERPUNK</div>
        <div class="sub-header">[ SYSTEM v2.0 ] :: [ INTEGRACIÓN WHATSAPP → JOPLIN ] :: [ MATRIX MODE ]</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### ⚙️ CONFIGURACIÓN")
        
        corregir = st.checkbox("🔤 Corregir tildes", value=True)
        deteccion = st.checkbox("🔍 Detectar errores", value=True)
        eliminar_enlaces = st.checkbox("🔗 Eliminar enlaces", value=True)
        eliminar_adjuntos = st.checkbox("📎 Eliminar adjuntos", value=True)
        agrupar = st.checkbox("📝 Agrupar notas consecutivas", value=False)
        correccion_segura = st.checkbox("🔒 Solo corrección segura", value=True)
        
        st.markdown("---")
        
        # Opciones adicionales
        mostrar_autores = st.checkbox("👤 Mostrar autores", value=False)
        incluir_titulo = st.checkbox("📌 Incluir título mensual", value=True)
        incluir_estadisticas = st.checkbox("📊 Incluir estadísticas", value=False)
        
        titulo_personalizado = ""
        if incluir_titulo:
            titulo_personalizado = st.text_input(
                "Título personalizado:",
                placeholder="ej: Omniutopia"
            )
        
        # Diccionario personal
        mostrar_diccionario_personal()
        
        # Historial
        mostrar_historial()
        
        # Efecto Matrix
        if st.sidebar.button("🌀 ACTIVAR MATRIX", use_container_width=True):
            st.session_state.matrix_effect = not st.session_state.matrix_effect
            st.rerun()
        
        if st.session_state.matrix_effect:
            mostrar_efecto_matrix()
    
    # --- Área principal ---
    
    # Input de texto
    st.markdown("### 📝 MENSAJES DE WHATSAPP")
    st.markdown("""
    <div style="font-family: 'Courier New', monospace; color: #00cc33; font-size: 0.9rem; opacity: 0.7;">
    [ Sistema de reconocimiento automático de formatos ]
    </div>
    """, unsafe_allow_html=True)
    
    texto_input = st.text_area(
        "",
        height=200,
        placeholder="[5:24 p. m., 27/7/2026] Daniel Diaz: Violent delights\n[5:24 p. m., 27/7/2026] Daniel Diaz: La entera historia humana...",
        key="input_textarea",
        label_visibility="collapsed"
    )
    
    # Botones
    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
    with col1:
        btn_generar = st.button("🚀 GENERAR", type="primary", use_container_width=True)
    with col2:
        btn_limpiar = st.button("🗑️ LIMPIAR", use_container_width=True)
    with col3:
        if st.button("📋 COPIAR", use_container_width=True):
            if st.session_state.texto_salida:
                st.write("📋 ¡Copiado al portapapeles!")
                st.markdown(f"""
                <script>
                function copyText() {{
                    navigator.clipboard.writeText(`{st.session_state.texto_salida}`);
                }}
                copyText();
                </script>
                """, unsafe_allow_html=True)
    
    # Procesamiento
    if btn_generar and texto_input:
        with st.spinner("⏳ Procesando mensajes..."):
            try:
                procesador = ProcesadorMensajes()
                mensajes = procesador.procesar(texto_input)
                st.session_state.mensajes_procesados = mensajes
                
                if not mensajes:
                    st.markdown("""
                    <div class="error-box">
                    ⚠️ No se encontraron mensajes válidos<br>
                    <span style="font-size: 0.8rem; opacity: 0.7;">
                    Asegúrate de que el formato sea: [HH:MM AM/PM, DD/MM/YYYY] Nombre: Mensaje
                    </span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    opciones = {
                        'corregir': corregir,
                        'detectar': deteccion,
                        'eliminar_enlaces': eliminar_enlaces,
                        'eliminar_adjuntos': eliminar_adjuntos,
                        'agrupar': agrupar,
                        'correccion_segura': correccion_segura,
                        'mostrar_autores': mostrar_autores,
                        'incluir_titulo': incluir_titulo,
                        'incluir_estadisticas': incluir_estadisticas,
                        'titulo_personalizado': titulo_personalizado
                    }
                    
                    texto_salida = procesador.generar_markdown(mensajes, opciones)
                    st.session_state.texto_salida = texto_salida
                    
                    errores = []
                    if deteccion and corregir:
                        errores = procesador.corrector.detectar_errores(texto_salida)
                    
                    st.session_state.historial.append({
                        'fecha': datetime.now().strftime('%d-%m-%Y %H:%M'),
                        'mensajes': len(mensajes),
                        'preview': texto_salida[:100],
                        'contenido': texto_salida
                    })
                    
                    st.session_state.contador_procesados += 1
                    
                    st.markdown("---")
                    st.markdown("### 📄 RESULTADO")
                    
                    mostrar_estadisticas(mensajes, texto_salida)
                    
                    if errores:
                        with st.expander(f"🔍 Errores ortográficos detectados ({len(errores)})"):
                            for error in errores[:20]:
                                st.warning(f"**{error['palabra']}** → {', '.join(error['sugerencias'])}")
                            if len(errores) > 20:
                                st.info(f"... y {len(errores) - 20} errores más")
                    
                    st.code(texto_salida, language="markdown")
                    
                    st.download_button(
                        label="📥 DESCARGAR MARKDOWN",
                        data=texto_salida,
                        file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Procesados {len(mensajes)} mensajes correctamente
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                ❌ Error: {str(e)}
                </div>
                """, unsafe_allow_html=True)
                import traceback
                st.code(traceback.format_exc())
    
    elif btn_generar:
        st.markdown("""
        <div class="warning-box">
        ⚠️ Por favor, pega algunos mensajes primero
        </div>
        """, unsafe_allow_html=True)
    
    if btn_limpiar:
        st.session_state.texto_salida = ""
        st.session_state.mensajes_procesados = []
        st.rerun()
    
    # --- Footer Cyberpunk ---
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; font-family: "Courier New", monospace; color: #00cc33; opacity: 0.5; font-size: 0.8rem;'>
    ⚡ BITÁCORA CYBERPUNK v2.0 ⚡<br>
    Procesados: {st.session_state.contador_procesados} archivos | 
    Diccionario: {len(st.session_state.diccionario_personal)} palabras personalizadas<br>
    <span style='font-size: 0.7rem; opacity: 0.3;'>
    [ MATRIX MODE ACTIVE ] :: [ SYSTEM READY ] :: [ AWAITING INPUT ]
    </span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
