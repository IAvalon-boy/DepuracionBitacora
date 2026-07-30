"""
Transcripción Bitácora v4.4
Sistema de transcripción WhatsApp → Markdown + Corrector ortográfico con spaCy y pyspellchecker
Estilo consola Matrix
Dependencias: streamlit, spacy, pyspellchecker (vía requirements.txt)
"""

import streamlit as st
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import json
import random
import os
import tempfile

# --- Importar dependencias ---
import spacy
from spellchecker import SpellChecker

# --- Configuración de página ---
st.set_page_config(
    page_title="Transcripción Bitácora",
    page_icon="⌨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Función para cargar spaCy con caché ---
@st.cache_resource
def load_spacy_model():
    """Carga el modelo de español de spaCy con caché en disco."""
    model_name = "es_core_news_sm"
    try:
        # Intentar cargar el modelo
        nlp = spacy.load(model_name)
        return nlp
    except OSError:
        # Si no existe, descargar sin bloquear (streamlit lo maneja en segundo plano)
        with st.spinner("⏳ Descargando modelo de español de spaCy (solo la primera vez)..."):
            spacy.cli.download(model_name)
        nlp = spacy.load(model_name)
        return nlp

# --- Cargar modelo (con caché) ---
nlp = load_spacy_model()

# --- Inicializar pyspellchecker (ligero) ---
spell = SpellChecker(language='es')

# --- Estilo Matrix (consola) ---
st.markdown("""
<style>
    .stApp { background: #0a0a0a !important; }
    .stApp, .stApp * { font-family: 'Courier New', monospace !important; }
    h1, h2, h3, .main-header { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; letter-spacing: 2px; }
    h1 { font-size: 2.5rem; }
    .stTextArea textarea {
        background: #000000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
        font-size: 14px !important;
    }
    .stTextArea textarea:focus { box-shadow: 0 0 20px rgba(0,255,65,0.2) !important; }
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
    .stButton button:disabled { opacity: 0.3 !important; cursor: not-allowed !important; }
    .stCheckbox label { color: #00cc33 !important; font-size: 0.9rem !important; }
    .stCheckbox input[type="checkbox"] { accent-color: #00ff41 !important; }
    .stSelectbox select, .stTextInput input {
        background: #000000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
        font-family: 'Courier New', monospace !important;
    }
    .stCodeBlock { background: #000000 !important; border: 1px solid #00ff41 !important; border-radius: 0 !important; }
    .stCodeBlock code { color: #00ff41 !important; font-family: 'Courier New', monospace !important; }
    .css-1xarl3l { background: #000000 !important; border: 1px solid #00ff41 !important; border-radius: 0 !important; }
    .css-1xarl3l label { color: #00cc33 !important; }
    .css-1xarl3l .css-1ht1j8u { color: #00ff41 !important; text-shadow: 0 0 10px rgba(0,255,65,0.3); }
    .css-1d391kg { background: #000000 !important; border-right: 1px solid #00ff41 !important; }
    .css-1d391kg .stMarkdown { color: #00cc33 !important; }
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 { color: #00ff41 !important; text-shadow: 0 0 10px rgba(0,255,65,0.3); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #000000; }
    ::-webkit-scrollbar-thumb { background: #00ff41; border-radius: 0; }
    ::-webkit-scrollbar-thumb:hover { background: #00cc33; box-shadow: 0 0 20px rgba(0,255,65,0.5); }
    hr { border: 0; border-top: 1px solid #00ff41; opacity: 0.3; margin: 20px 0; }
    .success-box { background: rgba(0,255,65,0.05); border-left: 4px solid #00ff41; padding: 0.8rem 1rem; color: #00ff41; font-family: 'Courier New', monospace; margin: 10px 0; }
    .warning-box { background: rgba(255,215,0,0.05); border-left: 4px solid #ffd700; padding: 0.8rem 1rem; color: #ffd700; font-family: 'Courier New', monospace; margin: 10px 0; }
    .error-box { background: rgba(255,0,0,0.05); border-left: 4px solid #ff0044; padding: 0.8rem 1rem; color: #ff4444; font-family: 'Courier New', monospace; margin: 10px 0; }
    .debug-box { background: rgba(255,0,68,0.05); border: 1px solid #ff0044; padding: 10px; font-family: 'Courier New', monospace; color: #ff6666; font-size: 0.8rem; margin: 10px 0; }
    .debug-box code { color: #ff4444; background: #1a0000; padding: 2px 6px; display: block; margin: 2px 0; border-left: 2px solid #ff0044; }
    @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0;} }
    .blink { animation: blink 1s step-end infinite; }
    .dict-tag { background: rgba(0,255,65,0.1); border: 1px solid #00ff41; padding: 0.2rem 0.6rem; border-radius: 0; margin: 0.2rem; display: inline-block; font-size: 0.75rem; color: #00ff41; box-shadow: 0 0 10px rgba(0,255,65,0.1); }
    .footer { text-align: center; color: #006622; font-family: 'Courier New', monospace; font-size: 0.8rem; opacity: 0.6; margin-top: 20px; border-top: 1px solid #00ff41; padding-top: 15px; }
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

# --- CORRECTOR ORTOGRÁFICO CON SPACY + PYSPELLCHECKER ---

class CorrectorOrtografico:
    """Corrector ortográfico basado en spaCy (contexto) y pyspellchecker (errores tipográficos)."""
    
    def __init__(self):
        self.personal = st.session_state.diccionario_personal
        self.base = self._cargar_diccionario_base()
        self.nlp = nlp
        self.spell = spell
        self.cache = {}
    
    def _cargar_diccionario_base(self) -> set:
        """Diccionario de palabras comunes (sin tildes) para no corregir, excepto diacríticas."""
        return {
            'yo','tu','el','ella','ello','nosotros','vosotros','ellos',
            'mi','ti','si','con','sin','para','por','de','en','a','ante',
            'bajo','cabe','contra','desde','durante','entre','hacia','hasta',
            'mediante','para','por','según','sin','sobre','tras','versus',
            'vía','la','las','lo','los','un','una','unos','unas',
            'ser','estar','tener','haber','hacer','poder','decir','ir',
            'ver','dar','saber','querer','llegar','pasar','deber','poner',
            'parecer','quedar','creer','hablar','llevar','dejar','seguir',
            'encontrar','llamar','venir','pensar','salir','volver','tomar',
            'conocer','vivir','sentir','tratar','mirar','contar','empezar',
            'esperar','buscar','existir','entrar','trabajar','escribir',
            'perder','producir','ocurrir','realizar','formar','actuar',
            'recibir','recordar','olvidar','caminar','correr','saltar',
            'nadar','volar','soñar','dormir','despertar','morir','nacer',
            'comer','beber','respirar','reir','llorar','gritar','susurrar',
            'casa','trabajo','familia','amigo','persona','vida','muerte',
            'tiempo','dia','mes','año','hoy','mañana','ayer','semana',
            'lugar','cosa','mente','cuerpo','alma','espiritu','corazon',
            'amor','odio','felicidad','tristeza','alegria','pena','sueño',
            'realidad','fantasia','verdad','mentira','belleza','fealdad',
            'fuerza','debilidad','sabiduria','ignorancia','poder','dinero',
            'salud','enfermedad','guerra','paz','libertad','esclavitud',
            'justicia','injusticia','derecho','ley','ciencia','arte',
            'historia','filosofia','literatura','musica','pintura','cine',
            'teatro','poesia','novela','cuento','leyenda','mito','religion',
            'dios','demonio','angel','cielo','infierno','paraiso','abismo',
            'luz','oscuridad','fuego','agua','tierra','aire','viento',
            'sol','luna','estrella','planeta','universo','galaxia',
            'palabra','lenguaje','idioma','cultura','pueblo','nacion',
            'ciudad','campo','mar','montaña','valle','rio','bosque',
            'bueno','malo','grande','pequeño','alto','bajo','largo','corto',
            'nuevo','viejo','joven','fuerte','debil','rápido','lento',
            'claro','oscuro','caliente','frio','dulce','salado','amargo',
            'feliz','triste','alegre','enojado','cansado','ocupado','libre',
            'inteligente','tonto','sabio','loco','cuerdo','bello','feo',
            'peligroso','seguro','facil','dificil','simple','complejo',
            'profundo','superficial','moderno','antiguo','real','falso',
            'pero','sin','embargo','no','obstante','por','lo','tanto','además',
            'también','asimismo','incluso','es','decir','o','sea','así','que',
            'entonces','después','luego','mientras','cuando','donde',
            'como','porque','ya','puesto','aunque','si','bien',
            'hasta','tanto','más','menos','muy','poco','mucho',
            'algo','nada','todo','cada','otro','mismo','propio','solo'
        }
    
    def _palabras_diacriticas(self) -> set:
        """Palabras que pueden tener tilde diacrítica según contexto."""
        return {'mas', 'si', 'te', 'mi', 'de', 'se', 'el', 'tu', 'que', 'cual', 'quien', 'como', 'cuando', 'donde', 'cuanto'}
    
    def _corregir_token(self, token) -> Optional[str]:
        """Decide la corrección basada en la etiqueta POS de spaCy y reglas diacríticas."""
        palabra = token.text.lower()
        pos = token.pos_
        
        # Casos especiales con tilde diacrítica
        if palabra == 'mas':
            if pos == 'SCONJ':       # conjunción subordinante (sin tilde)
                return 'mas'
            elif pos in ['ADV', 'CCONJ']:
                return 'más'
        elif palabra == 'si':
            if pos == 'SCONJ':       # conjunción condicional
                return 'si'
            elif pos in ['PRON', 'PART', 'INTJ']:
                return 'sí'
        elif palabra == 'te':
            if pos == 'PRON':        # pronombre personal
                return 'te'
            elif pos == 'NOUN':      # sustantivo (té)
                return 'té'
        elif palabra == 'mi':
            if pos in ['DET', 'PRON']:
                return 'mi'
            elif pos == 'NOUN':
                return 'mí'
        elif palabra == 'de':
            if pos == 'ADP':         # preposición
                return 'de'
            elif pos == 'VERB':      # verbo dar (subjuntivo)
                return 'dé'
        elif palabra == 'se':
            if pos == 'PRON':        # reflexivo
                return 'se'
            elif pos in ['VERB', 'AUX']:
                return 'sé'
        elif palabra == 'el':
            if pos == 'DET':         # artículo
                return 'el'
            elif pos == 'PRON':      # pronombre personal
                return 'él'
        elif palabra == 'tu':
            if pos == 'DET':         # posesivo
                return 'tu'
            elif pos == 'PRON':      # pronombre personal
                return 'tú'
        # Para interrogativos/exclamativos (que, cual, quien, como, cuando, donde, cuanto)
        if palabra in ['que', 'cual', 'quien', 'como', 'cuando', 'donde', 'cuanto']:
            # Si el token es pronombre interrogativo o exclamativo (heurística)
            if (token.dep_ in ['advmod', 'ROOT', 'nsubj', 'obj'] and 
                (token.i == 0 or (token.i > 0 and token.nbor(-1).text in ['¿', '¡']))):
                tilde_map = {
                    'que': 'qué', 'cual': 'cuál', 'quien': 'quién',
                    'como': 'cómo', 'cuando': 'cuándo', 'donde': 'dónde',
                    'cuanto': 'cuánto'
                }
                return tilde_map.get(palabra, palabra)
        
        # Si no es diacrítica, usar pyspellchecker para errores tipográficos
        if palabra not in self.base and palabra not in self.personal:
            if self.spell.unknown([palabra]):
                sugerencias = self.spell.candidates(palabra)
                if sugerencias:
                    return list(sugerencias)[0]
        return None
    
    def corregir(self, texto: str) -> Tuple[str, List[str]]:
        """
        Corrige el texto usando spaCy para contexto y pyspellchecker para errores.
        Retorna (texto_corregido, lista_de_cambios).
        """
        if not texto:
            return texto, []
        
        doc = self.nlp(texto)
        correcciones = []  # (inicio, fin, palabra_corregida)
        cambios = []
        
        for token in doc:
            palabra = token.text
            if not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+$', palabra):
                continue
            if palabra.lower() in self.personal:
                continue
            if palabra.lower() in self.base and palabra.lower() not in self._palabras_diacriticas():
                continue
            
            corregida = self._corregir_token(token)
            if corregida and corregida != palabra:
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                inicio = token.idx
                fin = inicio + len(palabra)
                correcciones.append((inicio, fin, corregida))
                cambios.append(f"{palabra} → {corregida}")
        
        if correcciones:
            chars = list(texto)
            for inicio, fin, corr in sorted(correcciones, reverse=True):
                chars[inicio:fin] = list(corr)
            texto_corregido = ''.join(chars)
        else:
            texto_corregido = texto
        
        return texto_corregido, cambios
    
    def detectar_errores(self, texto: str) -> List[Dict]:
        """Detecta posibles errores usando pyspellchecker y spaCy para contexto."""
        errores = []
        doc = self.nlp(texto)
        for token in doc:
            palabra = token.text
            if not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+$', palabra):
                continue
            if palabra.lower() in self.personal:
                continue
            if self.spell.unknown([palabra]):
                sugerencias = self.spell.candidates(palabra)
                if sugerencias:
                    errores.append({
                        'palabra': palabra,
                        'sugerencias': list(sugerencias)[:3]
                    })
        return errores

# --- PROCESADOR DE MENSAJES DE WHATSAPP ---

@dataclass
class Mensaje:
    fecha: str
    hora: str
    autor: str
    contenido: str
    es_metadato: bool = False

class Procesador:
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\]\s*([^:]+):\s*(.*)'
    PATRON_MOVIL = r'\[(\d{1,2}/\d{1,2})\s*,\s*(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\]\s*([^:]+):\s*(.*)'
    PATRON_GUION = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'
    PATRON_SIN_HORA = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-\s*([^:]+):\s*(.*)'
    
    def __init__(self):
        self.corrector = CorrectorOrtografico()
    
    def procesar(self, texto: str) -> Tuple[List[Mensaje], List[str]]:
        mensajes = []
        no_parseadas = []
        for linea in texto.strip().split('\n'):
            if not linea.strip():
                continue
            msg = self._parsear_linea(linea)
            if msg:
                mensajes.append(msg)
            else:
                no_parseadas.append(linea.strip())
        return mensajes, no_parseadas
    
    def _parsear_linea(self, linea: str) -> Optional[Mensaje]:
        m = re.match(self.PATRON_WEB, linea)
        if m:
            return self._crear_web(m)
        m = re.match(self.PATRON_MOVIL, linea)
        if m:
            return self._crear_movil(m)
        m = re.match(self.PATRON_GUION, linea)
        if m:
            return self._crear_guion(m)
        m = re.match(self.PATRON_SIN_HORA, linea)
        if m:
            return self._crear_sin_hora(m)
        return None
    
    def _crear_web(self, m):
        hora = m.group(1)
        ampm = m.group(2) or ''
        fecha_str = m.group(3)
        autor = m.group(4).strip()
        contenido = m.group(5).strip()
        return self._construir(fecha_str, hora, ampm, autor, contenido)
    
    def _crear_movil(self, m):
        fecha_str = m.group(1)
        hora = m.group(2)
        ampm = m.group(3) or ''
        autor = m.group(4).strip()
        contenido = m.group(5).strip()
        return self._construir(fecha_str, hora, ampm, autor, contenido)
    
    def _crear_guion(self, m):
        fecha_str = m.group(1)
        hora_ampm = m.group(2).strip()
        autor = m.group(3).strip()
        contenido = m.group(4).strip()
        ampm = ''
        if re.search(r'a\.?\s*m\.?|p\.?\s*m\.?', hora_ampm, re.IGNORECASE):
            partes = re.split(r'\s+(?=a\.?\s*m\.?|p\.?\s*m\.?)', hora_ampm, flags=re.IGNORECASE)
            if len(partes) == 2:
                hora_ampm = partes[0]
                ampm = partes[1]
        return self._construir(fecha_str, hora_ampm, ampm, autor, contenido)
    
    def _crear_sin_hora(self, m):
        fecha_str = m.group(1)
        autor = m.group(2).strip()
        contenido = m.group(3).strip()
        return self._construir(fecha_str, "00:00", "", autor, contenido)
    
    def _construir(self, fecha_str, hora, ampm, autor, contenido):
        if ampm:
            try:
                h, mn = map(int, hora.split(':'))
                ampm_clean = ampm.lower().replace(' ', '').replace('.', '')
                if 'pm' in ampm_clean and h < 12:
                    h += 12
                elif 'am' in ampm_clean and h == 12:
                    h = 0
                hora = f"{h:02d}:{mn:02d}"
            except:
                pass
        if '/' in fecha_str:
            partes = fecha_str.split('/')
            if len(partes) == 2:
                anio = datetime.now().year
                fecha_str = f"{partes[0]}/{partes[1]}/{anio}"
        try:
            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
            fecha = fecha_dt.strftime('%d-%m')
        except:
            try:
                fecha_dt = datetime.strptime(fecha_str, '%d/%m/%y')
                fecha = fecha_dt.strftime('%d-%m')
            except:
                fecha = fecha_str.replace('/', '-')
        es_mult = bool(re.search(r'<Multimedia omitido>|IMG|VIDEO|\.(jpg|png|gif|mp4)', contenido, re.IGNORECASE))
        es_enlace = bool(re.search(r'https?://', contenido))
        es_adj = bool(re.search(r'Documento omitido|Audio omitido', contenido, re.IGNORECASE))
        es_meta = es_mult or es_enlace or es_adj
        return Mensaje(fecha, hora, autor, contenido, es_meta)
    
    def limpiar(self, msg: Mensaje, elim_enlaces=True, elim_adj=True):
        cont = msg.contenido
        if elim_enlaces:
            cont = re.sub(r'https?://[^\s]+', '', cont)
        if elim_adj:
            cont = re.sub(r'<Multimedia omitido>|IMG[_-]\d+|VIDEO[_-]\d+|Documento omitido|Audio omitido', '', cont, flags=re.IGNORECASE)
        cont = re.sub(r'\d{1,2}:\d{2}', '', cont)
        return cont.strip()
    
    def generar_markdown(self, mensajes: List[Mensaje], opciones: Dict) -> str:
        if not mensajes:
            return ""
        agrupados = defaultdict(list)
        autores = set()
        for msg in mensajes:
            if msg.es_metadato and opciones.get('elim_adj', True):
                continue
            cont = self.limpiar(msg, opciones.get('elim_enlaces', True), opciones.get('elim_adj', True))
            if not cont:
                continue
            autores.add(msg.autor)
            agrupados[msg.fecha].append(cont)
        
        lineas = []
        if opciones.get('titulo', True):
            mes = datetime.now().month
            romanos = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
                       7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'}
            tit = opciones.get('titulo_pers', '') or datetime.now().strftime('%B')
            lineas.append(f"# {romanos[mes]}: {tit}")
            lineas.append("")
        for fecha, conts in sorted(agrupados.items()):
            lineas.append(f"## {fecha}")
            if opciones.get('agrupar', False):
                conts = self._agrupar(conts)
            for c in conts:
                if opciones.get('corregir', False):
                    c, _ = self.corrector.corregir(c)
                lineas.append(c)
            lineas.append("")
        if opciones.get('stats', False):
            lineas.append("---")
            lineas.append(f"**Estadísticas:** {len(mensajes)} msgs, {len(agrupados)} días, {', '.join(autores)}")
        return '\n'.join(lineas)
    
    def _agrupar(self, conts):
        res = []
        i = 0
        while i < len(conts):
            if i+1 < len(conts) and len(conts[i]) < 80 and len(conts[i+1]) < 80:
                res.append(conts[i] + ' ' + conts[i+1])
                i += 2
            else:
                res.append(conts[i])
                i += 1
        return res

# --- FUNCIONES DE INTERFAZ ---

def sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ CONFIG")
        corregir = st.checkbox("🔤 Corregir tildes y ortografía", True)
        detectar = st.checkbox("🔍 Detectar errores", True)
        elim_enlaces = st.checkbox("🔗 Eliminar enlaces", True)
        elim_adj = st.checkbox("📎 Eliminar adjuntos", True)
        agrupar = st.checkbox("📝 Agrupar notas", False)
        
        st.markdown("---")
        titulo = st.checkbox("📌 Título mensual", True)
        tit_pers = ""
        if titulo:
            tit_pers = st.text_input("Título personalizado", placeholder="Omniutopia")
        stats = st.checkbox("📊 Estadísticas", False)
        
        st.markdown("---")
        st.markdown("### 📚 Diccionario personal")
        if st.session_state.diccionario_personal:
            st.write(f"**{len(st.session_state.diccionario_personal)} palabras**")
            cols = st.columns(3)
            for i, p in enumerate(sorted(st.session_state.diccionario_personal)[:30]):
                cols[i % 3].markdown(f'<span class="dict-tag">{p}</span>', unsafe_allow_html=True)
            if len(st.session_state.diccionario_personal) > 30:
                st.markdown(f"... y {len(st.session_state.diccionario_personal)-30} más")
        else:
            st.info("⚠️ No hay palabras en el diccionario personal")
        
        nueva = st.text_input("Agregar palabra", key="nueva_pal", placeholder="ej: Omniutopia")
        if st.button("➕ Agregar", use_container_width=True) and nueva.strip():
            st.session_state.diccionario_personal.add(nueva.strip().lower())
            st.rerun()
        
        if st.session_state.diccionario_personal:
            elim = st.selectbox("Eliminar", sorted(st.session_state.diccionario_personal), key="select_elim")
            if st.button("🗑️ Eliminar", use_container_width=True):
                st.session_state.diccionario_personal.discard(elim)
                st.rerun()
        
        st.markdown("---")
        if st.button("🌀 MATRIX EFFECT", use_container_width=True):
            st.session_state.matrix_effect = not st.session_state.matrix_effect
            st.rerun()
        
        if st.session_state.matrix_effect:
            chars = "01"
            for _ in range(8):
                st.text(''.join(random.choice(chars) for _ in range(45)))
        
        return {
            'corregir': corregir, 'detectar': detectar,
            'elim_enlaces': elim_enlaces, 'elim_adj': elim_adj,
            'agrupar': agrupar, 'titulo': titulo,
            'titulo_pers': tit_pers, 'stats': stats
        }

# --- MAIN ---

def main():
    st.markdown("<div style='text-align:center;'><h1>⌨️ Transcripción Bitácora</h1></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#00cc33;font-family:Courier New;font-size:0.9rem;'>[ SISTEMA DE TRANSCRIPCIÓN WHATSAPP → MARKDOWN + CORRECTOR ORTOGRÁFICO CON SPACY ]</p>", unsafe_allow_html=True)
    
    opts = sidebar()
    
    texto = st.text_area(
        "",
        height=250,
        placeholder="[27/7, 5:24 p. m.] Daniel Díaz: Mensaje\n\nO texto plano para corregir tildes...",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        generar = st.button("🚀 GENERAR", use_container_width=True)
    with col2:
        limpiar = st.button("🗑️ LIMPIAR", use_container_width=True)
    with col3:
        if st.button("📋 COPIAR", use_container_width=True) and st.session_state.texto_salida:
            st.write("📋 ¡Copiado!")
            st.markdown(f"""
            <script>
            function copy() {{
                navigator.clipboard.writeText(`{st.session_state.texto_salida}`);
            }}
            copy();
            </script>
            """, unsafe_allow_html=True)
    
    if limpiar:
        st.session_state.texto_salida = ""
        st.session_state.debug_lines = []
        st.rerun()
    
    if generar and texto:
        with st.spinner("⏳ Procesando..."):
            proc = Procesador()
            mensajes, no_parseadas = proc.procesar(texto)
            
            if not mensajes and texto.strip():
                st.info("📝 No se detectaron mensajes con formato WhatsApp. Procesando como texto plano...")
                if opts['corregir']:
                    texto_corregido, cambios = proc.corrector.corregir(texto)
                else:
                    texto_corregido = texto
                    cambios = []
                st.session_state.texto_salida = texto_corregido
                
                if cambios:
                    with st.expander(f"🔧 {len(cambios)} correcciones realizadas"):
                        for c in cambios[:20]:
                            st.text(c)
                        if len(cambios) > 20:
                            st.text(f"... y {len(cambios)-20} más")
                
                st.markdown("### 📄 Texto corregido")
                st.code(texto_corregido, language="markdown")
                st.download_button(
                    "📥 Descargar .txt",
                    texto_corregido,
                    file_name=f"texto_corregido_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                st.success("✅ Texto corregido y listo para copiar.")
            
            else:
                if not mensajes:
                    st.error("⚠️ No se encontraron mensajes válidos.")
                    if no_parseadas:
                        with st.expander(f"🔍 Líneas no reconocidas ({len(no_parseadas)})", expanded=True):
                            st.markdown("**Estas líneas no pudieron ser parseadas:**")
                            for ln in no_parseadas[:15]:
                                st.code(ln, language="text")
                            if len(no_parseadas) > 15:
                                st.info(f"... y {len(no_parseadas)-15} líneas más")
                else:
                    md = proc.generar_markdown(mensajes, opts)
                    st.session_state.texto_salida = md
                    
                    if no_parseadas:
                        with st.expander(f"⚠️ Líneas no reconocidas ({len(no_parseadas)})", expanded=True):
                            st.markdown("**Estas líneas no se pudieron procesar como mensajes de WhatsApp:**")
                            for ln in no_parseadas[:15]:
                                st.code(ln, language="text")
                            if len(no_parseadas) > 15:
                                st.info(f"... y {len(no_parseadas)-15} líneas más")
                    
                    if opts['detectar'] and opts['corregir']:
                        errores = proc.corrector.detectar_errores(md)
                        if errores:
                            with st.expander(f"🔍 Errores ortográficos detectados ({len(errores)})"):
                                for e in errores[:20]:
                                    st.warning(f"**{e['palabra']}** → {', '.join(e['sugerencias'])}")
                                if len(errores) > 20:
                                    st.info(f"... y {len(errores)-20} errores más")
                    
                    st.markdown("### 📄 Resultado Markdown")
                    st.code(md, language="markdown")
                    
                    col_dl, _ = st.columns([1, 4])
                    with col_dl:
                        st.download_button(
                            "📥 Descargar .md",
                            md,
                            file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown"
                        )
                    
                    st.success(f"✅ Procesados {len(mensajes)} mensajes correctamente.")
                    
                    st.session_state.historial.append({
                        'fecha': datetime.now().strftime('%d-%m %H:%M'),
                        'msgs': len(mensajes),
                        'preview': md[:100]
                    })
                    st.session_state.contador += 1
    
    elif generar:
        st.warning("⚠️ Pega algunos mensajes o texto primero.")
    
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
    Procesados: {st.session_state.contador} | Historial: {len(st.session_state.historial)} | Diccionario: {len(st.session_state.diccionario_personal)}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
