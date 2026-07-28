"""
BITÁCORA STREAMLIT v1.0
Sistema de integración WhatsApp → Joplin (versión web)
Todas las funciones del prompt maestro en interfaz Streamlit
"""

import streamlit as st
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import json
from pathlib import Path

# --- Configuración de la página ---
st.set_page_config(
    page_title="BITÁCORA",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2ecc71;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #bdc3c7;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #1a3a2a;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2ecc71;
    }
    .warning-box {
        background-color: #3a2a1a;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f1c40f;
    }
    .error-box {
        background-color: #3a1a1a;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #e74c3c;
    }
    .stTextArea textarea {
        font-family: 'Consolas', monospace;
        font-size: 14px;
    }
    .stCodeBlock {
        font-family: 'Consolas', monospace;
        font-size: 14px;
    }
    .dict-tag {
        background-color: #2c3e50;
        padding: 0.2rem 0.6rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
</style>
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
        'palabra_editar': ''
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
        # Diccionario base español (simplificado)
        self._diccionario_base = self._cargar_diccionario_base()
        # Diccionario personal desde sesión
        self.diccionario_personal = st.session_state.diccionario_personal
    
    def _cargar_diccionario_base(self) -> set:
        """Carga diccionario base (simplificado para demo)"""
        # Palabras comunes en español
        palabras = {
            'hola', 'como', 'estas', 'bien', 'gracias', 'por', 'favor',
            'buenos', 'dias', 'tardes', 'noches', 'adios', 'hasta', 'luego',
            'si', 'no', 'tal', 'vez', 'casa', 'trabajo', 'amigo', 'familia',
            'tiempo', 'dia', 'semana', 'mes', 'año', 'hoy', 'mañana', 'ayer',
            'feliz', 'triste', 'contento', 'cansado', 'ocupado', 'libre',
            'comer', 'beber', 'dormir', 'leer', 'escribir', 'pensar', 'sentir',
            'filosofia', 'existencia', 'ser', 'estar', 'tener', 'hacer', 'decir',
            'ir', 'venir', 'ver', 'mirar', 'escuchar', 'hablar', 'callar',
            'amor', 'vida', 'muerte', 'sueño', 'realidad', 'conciencia',
            'alma', 'espiritu', 'cuerpo', 'mente', 'razon', 'emocion'
        }
        return palabras
    
    def corregir_texto(self, texto: str, solo_seguro: bool = True) -> Tuple[str, List[str]]:
        """Corrige texto y retorna cambios realizados"""
        if not texto:
            return texto, []
        
        cambios = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        
        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            
            # Verificar en diccionario personal
            if palabra.lower() in self.diccionario_personal:
                continue
            
            # Verificar en diccionario base
            if palabra.lower() in self._diccionario_base:
                continue
            
            # Buscar corrección
            corregida = self._buscar_correccion(palabra, solo_seguro)
            
            if corregida and corregida != palabra:
                # Preservar mayúsculas
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
        
        return texto, cambios
    
    def _buscar_correccion(self, palabra: str, solo_seguro: bool) -> Optional[str]:
        """Busca corrección para una palabra"""
        # Cache
        if palabra in self._cache_correcciones:
            return self._cache_correcciones[palabra]
        
        # Reglas simples de corrección
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
        
        # Reglas de acentuación
        reglas = [
            # Palabras sin acento que deberían tenerlo
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
            ('podria', 'podría'),
            ('podemos', 'podemos'),
            ('tenemos', 'tenemos'),
            ('vamos', 'vamos'),
            ('estamos', 'estamos'),
            ('somos', 'somos'),
            # Errores comunes
            ('impreativo', 'imperativo'),
            ('existencialismo', 'existencialismo'),
            ('fenomenologia', 'fenomenología'),
            ('hermeneutica', 'hermenéutica'),
        ]
        
        palabra_lower = palabra.lower()
        for incorrecta, correcta in reglas:
            if palabra_lower == incorrecta:
                correcciones.append(correcta)
        
        # Regla: reemplazar 's' por 'c' en algunas palabras
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
            
            # Buscar sugerencias
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
        
        # Usar reglas de corrección
        correcciones = self._reglas_correccion(palabra)
        sugerencias.extend(correcciones)
        
        # Si no hay sugerencias, buscar palabras similares
        if not sugerencias:
            palabra_base = palabra.lower()
            for dict_word in self._diccionario_base:
                if len(dict_word) > 3 and abs(len(dict_word) - len(palabra_base)) <= 2:
                    # Similitud simple
                    if self._similitud_simple(palabra_base, dict_word) > 0.7:
                        sugerencias.append(dict_word)
                        if len(sugerencias) >= 3:
                            break
        
        return sugerencias
    
    def _similitud_simple(self, s1: str, s2: str) -> float:
        """Calcula similitud simple entre dos palabras"""
        if not s1 or not s2:
            return 0
        
        # Comparación de caracteres
        matches = sum(1 for a, b in zip(s1, s2) if a == b)
        return matches / max(len(s1), len(s2))

class ProcesadorMensajes:
    """Procesa mensajes de WhatsApp"""
    
    PATRON_MENSAJE = r'(\d{1,2}/\d{1,2}/\d{2,4})[,\s]+(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.*)'
    PATRON_FECHA = r'(\d{1,2}/\d{1,2}/\d{2,4})'
    PATRON_MULTIMEDIA = r'<Multimedia omitido>|IMG[_-]\d+|VIDEO[_-]\d+'
    PATRON_ADJUNTO = r'Documento omitido|Audio omitido|Archivo omitido'
    PATRON_ENLACE = r'https?://[^\s]+'
    
    def __init__(self):
        self.corrector = CorrectorOrtografico()
    
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
        match = re.match(self.PATRON_MENSAJE, linea)
        if not match:
            return None
        
        fecha_str = match.group(1)
        hora = match.group(2)
        autor = match.group(3).strip()
        contenido = match.group(4).strip()
        
        # Formatear fecha
        try:
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%d-%m')
        except:
            try:
                fecha = datetime.strptime(fecha_str, '%d/%m/%y').strftime('%d-%m')
            except:
                fecha = fecha_str
        
        # Detectar tipos
        es_multimedia = bool(re.search(self.PATRON_MULTIMEDIA, contenido))
        es_enlace = bool(re.search(self.PATRON_ENLACE, contenido))
        es_adjunto = bool(re.search(self.PATRON_ADJUNTO, contenido))
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
    
    def limpiar_mensaje(self, msg: Mensaje, eliminar_enlaces: bool = True, 
                        eliminar_adjuntos: bool = True) -> str:
        """Limpia el contenido de un mensaje"""
        contenido = msg.contenido
        
        if eliminar_enlaces:
            contenido = re.sub(self.PATRON_ENLACE, '', contenido)
        
        if eliminar_adjuntos:
            contenido = re.sub(self.PATRON_MULTIMEDIA, '', contenido)
            contenido = re.sub(self.PATRON_ADJUNTO, '', contenido)
        
        # Eliminar menciones de hora repetidas
        contenido = re.sub(r'\d{1,2}:\d{2}', '', contenido)
        
        return contenido.strip()
    
    def generar_markdown(self, mensajes: List[Mensaje], opciones: Dict) -> str:
        """Genera markdown formateado"""
        if not mensajes:
            return ""
        
        # Filtrar y agrupar
        mensajes_por_dia = defaultdict(list)
        autores = set()
        
        for msg in mensajes:
            # Filtrar metadatos
            if msg.es_metadato and opciones.get('eliminar_adjuntos', True):
                continue
            
            # Limpiar contenido
            contenido = self.limpiar_mensaje(
                msg,
                eliminar_enlaces=opciones.get('eliminar_enlaces', True),
                eliminar_adjuntos=opciones.get('eliminar_adjuntos', True)
            )
            
            if not contenido:
                continue
            
            autores.add(msg.autor)
            mensajes_por_dia[msg.fecha].append(contenido)
        
        # Generar markdown
        lineas = []
        
        # Título mensual
        if opciones.get('incluir_titulo', True):
            mes_actual = datetime.now().month
            meses_romanos = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
                            7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'}
            titulo_personalizado = opciones.get('titulo_personalizado', '')
            titulo_mes = meses_romanos.get(mes_actual, '')
            titulo = f"# {titulo_mes}: {titulo_personalizado or datetime.now().strftime('%B')}"
            lineas.append(titulo)
            lineas.append("")
        
        # Notas diarias
        for fecha, contenidos in sorted(mensajes_por_dia.items()):
            lineas.append(f"## {fecha}")
            
            # Agrupar si está activado
            if opciones.get('agrupar', False):
                contenidos = self._agrupar_contenidos(contenidos)
            
            for contenido in contenidos:
                # Aplicar corrección ortográfica
                if opciones.get('corregir', False):
                    contenido, _ = self.corrector.corregir_texto(
                        contenido, 
                        solo_seguro=opciones.get('correccion_segura', True)
                    )
                
                # Agregar prefijo de autor
                if opciones.get('mostrar_autores', False) and len(autores) > 1:
                    # Intentar extraer autor del mensaje original
                    contenido = f"**{msg.autor}:** {contenido}"
                
                lineas.append(contenido)
            
            lineas.append("")
        
        # Estadísticas
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
    st.sidebar.markdown("### 📚 Diccionario Personal")
    
    # Mostrar palabras actuales
    if st.session_state.diccionario_personal:
        palabras = sorted(st.session_state.diccionario_personal)
        st.sidebar.markdown(f"**{len(palabras)} palabras:**")
        
        # Mostrar como tags
        cols = st.sidebar.columns(3)
        for i, palabra in enumerate(palabras[:30]):  # Limitar a 30 para no saturar
            cols[i % 3].markdown(f'<span class="dict-tag">{palabra}</span>', 
                               unsafe_allow_html=True)
        
        if len(palabras) > 30:
            st.sidebar.markdown(f"... y {len(palabras) - 30} más")
    else:
        st.sidebar.info("No hay palabras en el diccionario personal")
    
    # Agregar palabra
    st.sidebar.markdown("#### ➕ Agregar palabra")
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        nueva_palabra = st.text_input("Palabra:", key="nueva_palabra_input", 
                                     placeholder="ej: Omniutopia")
    with col2:
        if st.button("➕", key="btn_agregar_palabra", use_container_width=True):
            if nueva_palabra and nueva_palabra.strip():
                palabra_limpia = nueva_palabra.strip().lower()
                if palabra_limpia not in st.session_state.diccionario_personal:
                    st.session_state.diccionario_personal.add(palabra_limpia)
                    st.success(f"✅ '{palabra_limpia}' agregada")
                    st.rerun()
                else:
                    st.warning(f"⚠️ '{palabra_limpia}' ya existe")
    
    # Eliminar palabra
    if st.session_state.diccionario_personal:
        st.sidebar.markdown("#### 🗑️ Eliminar palabra")
        palabra_eliminar = st.sidebar.selectbox(
            "Seleccionar:", 
            options=sorted(st.session_state.diccionario_personal),
            key="select_eliminar"
        )
        if st.button("🗑️ Eliminar", key="btn_eliminar_palabra"):
            if palabra_eliminar:
                st.session_state.diccionario_personal.discard(palabra_eliminar)
                st.success(f"✅ '{palabra_eliminar}' eliminada")
                st.rerun()
    
    # Importar/Exportar
    st.sidebar.markdown("#### 📦 Importar/Exportar")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📤 Exportar", key="btn_exportar_dict"):
            dict_json = json.dumps(list(st.session_state.diccionario_personal))
            st.download_button(
                label="📥 Descargar JSON",
                data=dict_json,
                file_name="diccionario_personal.json",
                mime="application/json"
            )
    with col2:
        uploaded_file = st.file_uploader(
            "📂 Importar JSON", 
            type=['json'],
            key="upload_dict"
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
        st.sidebar.markdown("### 📜 Historial")
        
        for i, entry in enumerate(st.session_state.historial[-5:]):  # Últimos 5
            with st.sidebar.expander(f"{entry['fecha']} - {entry['mensajes']} msgs"):
                st.text(entry['preview'][:200] + "...")
                if st.button(f"📋 Usar", key=f"hist_{i}"):
                    st.session_state.texto_salida = entry['contenido']
                    st.rerun()

def mostrar_estadisticas(mensajes: List[Mensaje], texto_salida: str):
    """Muestra estadísticas del procesamiento"""
    if mensajes:
        # Estadísticas
        total_mensajes = len(mensajes)
        mensajes_por_dia = defaultdict(int)
        autores = set()
        palabras_totales = 0
        
        for msg in mensajes:
            mensajes_por_dia[msg.fecha] += 1
            autores.add(msg.autor)
            palabras_totales += len(msg.contenido.split())
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📨 Mensajes", total_mensajes)
        col2.metric("📅 Días", len(mensajes_por_dia))
        col3.metric("👤 Autores", len(autores))
        col4.metric("📝 Palabras", palabras_totales)
        
        # Longitud del resultado
        if texto_salida:
            st.info(f"📄 Texto generado: {len(texto_salida)} caracteres, {len(texto_salida.split())} palabras")

def main():
    """Función principal de la app"""
    
    # --- Header ---
    st.markdown('<div class="main-header">📓 BITÁCORA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sistema de integración WhatsApp → Joplin</div>', 
                unsafe_allow_html=True)
    
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        
        # Opciones principales en sidebar
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
                "Título personalizado (opcional):",
                placeholder="ej: Omniutopia"
            )
        
        # Diccionario personal
        mostrar_diccionario_personal()
        
        # Historial
        mostrar_historial()
    
    # --- Área principal ---
    
    # Input de texto
    st.markdown("### 📝 Mensajes de WhatsApp")
    st.markdown("Copia y pega el texto de la exportación de WhatsApp")
    
    texto_input = st.text_area(
        "Pega aquí los mensajes:",
        height=200,
        placeholder="28/7/2026 14:30 - Juan: Hola, como estas?\n28/7/2026 14:32 - María: Bien, y vos?",
        key="input_textarea"
    )
    
    # Botones
    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
    with col1:
        btn_generar = st.button("🚀 Generar", type="primary", use_container_width=True)
    with col2:
        btn_limpiar = st.button("🗑️ Limpiar", use_container_width=True)
    with col3:
        if st.button("📋 Copiar", use_container_width=True):
            if st.session_state.texto_salida:
                st.write("📋 ¡Copiado al portapapeles!")
                # Usar JavaScript para copiar
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
                # Instanciar procesador
                procesador = ProcesadorMensajes()
                
                # Procesar mensajes
                mensajes = procesador.procesar(texto_input)
                st.session_state.mensajes_procesados = mensajes
                
                if not mensajes:
                    st.warning("⚠️ No se encontraron mensajes válidos")
                else:
                    # Opciones
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
                    
                    # Generar markdown
                    texto_salida = procesador.generar_markdown(mensajes, opciones)
                    st.session_state.texto_salida = texto_salida
                    
                    # Detectar errores si está activado
                    errores = []
                    if deteccion and corregir:
                        errores = procesador.corrector.detectar_errores(texto_salida)
                    
                    # Guardar en historial
                    st.session_state.historial.append({
                        'fecha': datetime.now().strftime('%d-%m-%Y %H:%M'),
                        'mensajes': len(mensajes),
                        'preview': texto_salida[:100],
                        'contenido': texto_salida
                    })
                    
                    st.session_state.contador_procesados += 1
                    
                    # Mostrar resultados
                    st.markdown("---")
                    st.markdown("### 📄 Resultado")
                    
                    # Mostrar estadísticas
                    mostrar_estadisticas(mensajes, texto_salida)
                    
                    # Mostrar errores si los hay
                    if errores:
                        with st.expander(f"🔍 Errores ortográficos detectados ({len(errores)})"):
                            for error in errores[:20]:
                                st.warning(f"**{error['palabra']}** → {', '.join(error['sugerencias'])}")
                            if len(errores) > 20:
                                st.info(f"... y {len(errores) - 20} errores más")
                    
                    # Mostrar resultado
                    st.code(texto_salida, language="markdown")
                    
                    # Botón para copiar
                    st.download_button(
                        label="📥 Descargar Markdown",
                        data=texto_salida,
                        file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                    
                    st.success(f"✅ Procesados {len(mensajes)} mensajes")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    elif btn_generar:
        st.warning("⚠️ Por favor, pega algunos mensajes primero")
    
    # Limpiar
    if btn_limpiar:
        st.session_state.texto_salida = ""
        st.session_state.mensajes_procesados = []
        st.rerun()
    
    # --- Footer ---
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: gray; font-size: 0.8rem;'>
        BITÁCORA v1.0 | Procesados: {st.session_state.contador_procesados} archivos | 
        Diccionario: {len(st.session_state.diccionario_personal)} palabras personalizadas
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()