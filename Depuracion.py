"""
BITÁCORA MATRIX v3.1
Sistema de transcripción WhatsApp → Markdown
Corrección ortográfica real con pyspellchecker + diccionario personal
Estilo Matrix minimalista
"""

import streamlit as st
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import json
import random
import sys
import subprocess

# --- Instalar dependencias si no están ---
try:
    from spellchecker import SpellChecker
except ImportError:
    st.warning("Instalando pyspellchecker...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyspellchecker"])
    from spellchecker import SpellChecker

# --- Configuración de página ---
st.set_page_config(
    page_title="BITÁCORA MATRIX",
    page_icon="⌨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilo Matrix minimalista ---
st.markdown("""
<style>
    .stApp { background: #0a0a0a !important; }
    h1, h2, h3, .main-header {
        font-family: 'Courier New', monospace;
        color: #00ff41 !important;
        text-shadow: 0 0 5px #00ff41;
        letter-spacing: 2px;
    }
    .stTextArea textarea {
        background: #000000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
    }
    .stButton button {
        background: #000000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        box-shadow: 0 0 10px rgba(0,255,65,0.2);
    }
    .stButton button:hover {
        background: #00ff41 !important;
        color: #000000 !important;
        box-shadow: 0 0 30px #00ff41;
    }
    .stCheckbox label {
        color: #00cc33 !important;
        font-family: 'Courier New', monospace !important;
    }
    .stCodeBlock {
        background: #000000 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
    }
    .stCodeBlock code {
        color: #00ff41 !important;
        font-family: 'Courier New', monospace !important;
    }
    .css-1xarl3l {
        background: #000000 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
    }
    .css-1d391kg {
        background: #000000 !important;
        border-right: 1px solid #00ff41 !important;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000000; }
    ::-webkit-scrollbar-thumb { background: #00ff41; border-radius: 0; }
    hr { border: 0; border-top: 1px solid #00ff41; opacity: 0.3; }
    .debug-box {
        background: #0a0a0a;
        border: 1px solid #ff0044;
        padding: 10px;
        font-family: 'Courier New', monospace;
        color: #ff4444;
        font-size: 0.8rem;
        margin: 10px 0;
    }
    @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0;} }
    .blink { animation: blink 1s step-end infinite; }
</style>
""", unsafe_allow_html=True)

# --- Inicialización de estado ---
def init_state():
    defaults = {
        'texto_salida': '',
        'diccionario_personal': set(),
        'historial': [],
        'contador': 0,
        'debug_lines': []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- Clase Corrector (con pyspellchecker) ---
class CorrectorOrtografico:
    def __init__(self):
        # Cargar el corrector en español
        self.spell = SpellChecker(language='es')
        # Diccionario personal desde sesión
        self.personal = st.session_state.diccionario_personal
        # Cache para correcciones rápidas
        self.cache = {}
        # Agregar palabras personalizadas al diccionario
        for palabra in self.personal:
            self.spell.word_frequency.add(palabra)

    def agregar_palabra(self, palabra):
        """Agrega una palabra al diccionario personal y al corrector"""
        self.personal.add(palabra.lower())
        self.spell.word_frequency.add(palabra.lower())
        st.session_state.diccionario_personal = self.personal

    def eliminar_palabra(self, palabra):
        """Elimina una palabra del diccionario personal"""
        self.personal.discard(palabra.lower())
        st.session_state.diccionario_personal = self.personal

    def corregir_texto(self, texto: str, solo_seguro: bool = True) -> Tuple[str, List[str]]:
        """
        Corrige el texto usando pyspellchecker.
        solo_seguro: si True, solo corrige si hay una única sugerencia.
        """
        if not texto:
            return texto, []

        cambios = []
        # Extraer palabras (solo letras y acentos)
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)

        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            # Si está en el diccionario personal, no tocar
            if palabra.lower() in self.personal:
                continue

            # Buscar en caché
            if palabra in self.cache:
                corregida = self.cache[palabra]
            else:
                # Obtener sugerencias
                sugerencias = list(self.spell.candidates(palabra))
                if solo_seguro:
                    # Solo si hay UNA sugerencia
                    if len(sugerencias) == 1:
                        corregida = sugerencias[0]
                    else:
                        corregida = None
                else:
                    # Si hay sugerencias, tomar la primera
                    if sugerencias:
                        corregida = sugerencias[0]
                    else:
                        corregida = None

                if corregida:
                    self.cache[palabra] = corregida

            if corregida and corregida != palabra:
                # Preservar mayúsculas
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")

        return texto, cambios

    def detectar_errores(self, texto: str) -> List[Dict]:
        """
        Detecta palabras desconocidas (que no están en el diccionario)
        y devuelve sugerencias.
        """
        errores = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)

        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            if palabra.lower() in self.personal:
                continue
            # Verificar si es desconocida
            if self.spell.unknown([palabra]):
                sugerencias = list(self.spell.candidates(palabra))[:3]
                if sugerencias:
                    errores.append({
                        'palabra': palabra,
                        'sugerencias': sugerencias
                    })

        return errores

# --- Procesador de mensajes ---
@dataclass
class Mensaje:
    fecha: str
    hora: str
    autor: str
    contenido: str
    es_metadato: bool = False

class Procesador:
    # Patrones para todos los formatos
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\]\s*([^:]+):\s*(.*)'
    PATRON_MOVIL = r'\[(\d{1,2}/\d{1,2})\s*,\s*(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\]\s*([^:]+):\s*(.*)'
    PATRON_GUION = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'
    PATRON_SIN_HORA = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-\s*([^:]+):\s*(.*)'
    PATRON_GUION_LARGO = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*[–—-]\s*([^:]+):\s*(.*)'

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
        m = re.match(self.PATRON_GUION_LARGO, linea)
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
        # Convertir hora a 24h
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
        # Formatear fecha a DD-MM
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
        # Detectar metadatos
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
                    c, _ = self.corrector.corregir_texto(c, solo_seguro=True)
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

# --- UI ---
def sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ CONFIG")
        corregir = st.checkbox("🔤 Corregir tildes", True)
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
            st.write(f"{len(st.session_state.diccionario_personal)} palabras")
            for p in sorted(st.session_state.diccionario_personal)[:20]:
                st.markdown(f"`{p}`", unsafe_allow_html=True)
        nueva = st.text_input("Agregar palabra", key="nueva_pal")
        if st.button("➕ Agregar") and nueva.strip():
            st.session_state.diccionario_personal.add(nueva.strip().lower())
            # Actualizar el corrector si ya existe
            if 'corrector' in st.session_state:
                st.session_state.corrector.agregar_palabra(nueva.strip().lower())
            st.rerun()
        if st.session_state.diccionario_personal:
            elim = st.selectbox("Eliminar", sorted(st.session_state.diccionario_personal))
            if st.button("🗑️ Eliminar"):
                st.session_state.diccionario_personal.discard(elim)
                if 'corrector' in st.session_state:
                    st.session_state.corrector.eliminar_palabra(elim)
                st.rerun()

        st.markdown("---")
        if st.button("🌀 MATRIX ON/OFF"):
            st.session_state.matrix = not st.session_state.get('matrix', True)
        if st.session_state.get('matrix', True):
            chars = "01"
            for _ in range(8):
                st.text(''.join(random.choice(chars) for _ in range(40)))

        return {
            'corregir': corregir, 'detectar': detectar,
            'elim_enlaces': elim_enlaces, 'elim_adj': elim_adj,
            'agrupar': agrupar, 'titulo': titulo,
            'titulo_pers': tit_pers, 'stats': stats
        }

# --- Main ---
def main():
    st.markdown("<div style='text-align:center;'><h1>⌨️ BITÁCORA MATRIX</h1></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#00cc33;font-family:Courier New;'>[ SISTEMA DE TRANSCRIPCIÓN WHATSAPP → MARKDOWN ]</p>", unsafe_allow_html=True)

    opts = sidebar()

    st.markdown("### 📝 Pegar mensajes")
    texto = st.text_area("", height=200, placeholder="[27/7, 5:24 p. m.] Daniel Díaz: Mensaje\n[5:24 p. m., 27/7/2026] Daniel: Mensaje\n27/7/2026 17:24 - Daniel: Mensaje", label_visibility="collapsed")

    col1, col2, col3 = st.columns([1,1,4])
    with col1:
        generar = st.button("🚀 GENERAR", use_container_width=True)
    with col2:
        limpiar = st.button("🗑️ LIMPIAR", use_container_width=True)

    if limpiar:
        st.session_state.texto_salida = ""
        st.session_state.debug_lines = []
        st.rerun()

    if generar and texto:
        with st.spinner("Procesando..."):
            # Crear procesador con corrector
            proc = Procesador()
            # Guardar corrector en sesión para mantener diccionario personal
            st.session_state.corrector = proc.corrector

            mensajes, no_parseadas = proc.procesar(texto)
            st.session_state.debug_lines = no_parseadas

            if not mensajes:
                st.error("⚠️ No se encontraron mensajes válidos.")
                if no_parseadas:
                    with st.expander("🔍 Líneas no reconocidas (primeras 10)"):
                        for ln in no_parseadas[:10]:
                            st.code(ln, language="text")
            else:
                md = proc.generar_markdown(mensajes, opts)
                st.session_state.texto_salida = md

                # Detectar errores si está activado
                if opts['detectar'] and opts['corregir']:
                    errores = proc.corrector.detectar_errores(md)
                    if errores:
                        with st.expander(f"🔍 Errores detectados ({len(errores)})"):
                            for e in errores[:20]:
                                st.warning(f"**{e['palabra']}** → {', '.join(e['sugerencias'])}")

                st.markdown("### 📄 Resultado Markdown")
                st.code(md, language="markdown")
                st.download_button("📥 Descargar .md", md, file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")
                st.success(f"✅ Procesados {len(mensajes)} mensajes.")
                if no_parseadas:
                    st.warning(f"⚠️ {len(no_parseadas)} líneas no reconocidas (ver expandible arriba).")

                # Historial
                st.session_state.historial.append({
                    'fecha': datetime.now().strftime('%d-%m %H:%M'),
                    'msgs': len(mensajes),
                    'preview': md[:100]
                })
                st.session_state.contador += 1

    elif generar:
        st.warning("⚠️ Pega algunos mensajes primero.")

    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;color:#006622;font-family:Courier New;font-size:0.8rem;'>
    Procesados: {st.session_state.contador} | Historial: {len(st.session_state.historial)} | Diccionario: {len(st.session_state.diccionario_personal)}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
