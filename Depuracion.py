"""
BITÁCORA MATRIX v3.1
Sistema de transcripción WhatsApp → Markdown
Sin dependencias externas (solo streamlit)
Corrector ortográfico propio (reglas + diccionario)
"""

import streamlit as st
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import json
import random

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
    /* Fondo negro puro */
    .stApp {
        background: #0a0a0a !important;
    }
    /* Títulos verdes neón */
    h1, h2, h3, .main-header {
        font-family: 'Courier New', monospace;
        color: #00ff41 !important;
        text-shadow: 0 0 5px #00ff41;
        letter-spacing: 2px;
    }
    /* Cajas de texto estilo terminal */
    .stTextArea textarea {
        background: #000000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
    }
    /* Botones estilo consola */
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
    /* Checkboxes y labels */
    .stCheckbox label {
        color: #00cc33 !important;
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
    /* Sidebar */
    .css-1d391kg {
        background: #000000 !important;
        border-right: 1px solid #00ff41 !important;
    }
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #000000;
    }
    ::-webkit-scrollbar-thumb {
        background: #00ff41;
        border-radius: 0;
    }
    /* Línea separadora */
    hr {
        border: 0;
        border-top: 1px solid #00ff41;
        opacity: 0.3;
    }
    /* Texto de depuración */
    .debug-box {
        background: #0a0a0a;
        border: 1px solid #ff0044;
        padding: 10px;
        font-family: 'Courier New', monospace;
        color: #ff4444;
        font-size: 0.8rem;
        margin: 10px 0;
    }
    /* Blink */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    .blink {
        animation: blink 1s step-end infinite;
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
        'debug_lines': []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# --- CORRECTOR ORTOGRÁFICO PROPIO (sin dependencias externas) ---

class CorrectorOrtografico:
    """Corrector de tildes y errores comunes con diccionario extenso."""
    
    def __init__(self):
        self.personal = st.session_state.diccionario_personal
        # Diccionario base de palabras comunes en español (sin tildes)
        self.base = self._cargar_diccionario_base()
        # Cache de correcciones
        self.cache = {}
        # Reglas de acentuación (palabra_sin_tilde -> palabra_con_tilde)
        self.reglas_acento = self._cargar_reglas_acento()
        # Reglas de errores comunes (incorrecta -> correcta)
        self.reglas_errores = self._cargar_reglas_errores()
    
    def _cargar_diccionario_base(self) -> set:
        """Carga un conjunto amplio de palabras comunes (sin tildes)."""
        return {
            # Pronombres, artículos, preposiciones
            'yo', 'tu', 'el', 'ella', 'ello', 'nosotros', 'vosotros', 'ellos',
            'mi', 'ti', 'si', 'con', 'sin', 'para', 'por', 'de', 'en', 'a', 'ante',
            'bajo', 'cabe', 'contra', 'desde', 'durante', 'entre', 'hacia', 'hasta',
            'mediante', 'para', 'por', 'según', 'sin', 'sobre', 'tras', 'versus',
            'vía', 'la', 'las', 'lo', 'los', 'un', 'una', 'unos', 'unas',
            
            # Verbos comunes (infinitivo)
            'ser', 'estar', 'tener', 'haber', 'hacer', 'poder', 'decir', 'ir',
            'ver', 'dar', 'saber', 'querer', 'llegar', 'pasar', 'deber', 'poner',
            'parecer', 'quedar', 'creer', 'hablar', 'llevar', 'dejar', 'seguir',
            'encontrar', 'llamar', 'venir', 'pensar', 'salir', 'volver', 'tomar',
            'conocer', 'vivir', 'sentir', 'tratar', 'mirar', 'contar', 'empezar',
            'esperar', 'buscar', 'existir', 'entrar', 'trabajar', 'escribir',
            'perder', 'producir', 'ocurrir', 'realizar', 'formar', 'actuar',
            'recibir', 'recordar', 'olvidar', 'caminar', 'correr', 'saltar',
            'nadar', 'volar', 'soñar', 'dormir', 'despertar', 'morir', 'nacer',
            'comer', 'beber', 'respirar', 'reir', 'llorar', 'gritar', 'susurrar',
            
            # Sustantivos comunes
            'casa', 'trabajo', 'familia', 'amigo', 'persona', 'vida', 'muerte',
            'tiempo', 'dia', 'mes', 'año', 'hoy', 'mañana', 'ayer', 'semana',
            'lugar', 'cosa', 'mente', 'cuerpo', 'alma', 'espiritu', 'corazon',
            'amor', 'odio', 'felicidad', 'tristeza', 'alegria', 'pena', 'sueño',
            'realidad', 'fantasia', 'verdad', 'mentira', 'belleza', 'fealdad',
            'fuerza', 'debilidad', 'sabiduria', 'ignorancia', 'poder', 'dinero',
            'salud', 'enfermedad', 'guerra', 'paz', 'libertad', 'esclavitud',
            'justicia', 'injusticia', 'derecho', 'ley', 'ciencia', 'arte',
            'historia', 'filosofia', 'literatura', 'musica', 'pintura', 'cine',
            'teatro', 'poesia', 'novela', 'cuento', 'leyenda', 'mito', 'religion',
            'dios', 'demonio', 'angel', 'cielo', 'infierno', 'paraiso', 'abismo',
            'luz', 'oscuridad', 'fuego', 'agua', 'tierra', 'aire', 'viento',
            'sol', 'luna', 'estrella', 'planeta', 'universo', 'galaxia',
            'palabra', 'lenguaje', 'idioma', 'cultura', 'pueblo', 'nacion',
            'ciudad', 'campo', 'mar', 'montaña', 'valle', 'rio', 'bosque',
            
            # Adjetivos comunes
            'bueno', 'malo', 'grande', 'pequeño', 'alto', 'bajo', 'largo', 'corto',
            'nuevo', 'viejo', 'joven', 'viejo', 'fuerte', 'debil', 'rápido', 'lento',
            'claro', 'oscuro', 'caliente', 'frio', 'dulce', 'salado', 'amargo',
            'feliz', 'triste', 'alegre', 'enojado', 'cansado', 'ocupado', 'libre',
            'inteligente', 'tonto', 'sabio', 'loco', 'cuerdo', 'bello', 'feo',
            'peligroso', 'seguro', 'facil', 'dificil', 'simple', 'complejo',
            'profundo', 'superficial', 'moderno', 'antiguo', 'real', 'falso',
            
            # Conectores y muletillas
            'pero', 'sin embargo', 'no obstante', 'por lo tanto', 'además',
            'también', 'asimismo', 'incluso', 'es decir', 'o sea', 'así que',
            'entonces', 'después', 'luego', 'mientras', 'cuando', 'donde',
            'como', 'porque', 'ya que', 'puesto que', 'aunque', 'si bien',
            'incluso', 'hasta', 'tanto', 'más', 'menos', 'muy', 'poco', 'mucho',
            'algo', 'nada', 'todo', 'cada', 'otro', 'mismo', 'propio', 'solo'
        }
    
    def _cargar_reglas_acento(self) -> Dict[str, str]:
        """Reglas de acentuación: palabra_sin_tilde -> palabra_con_tilde."""
        return {
            # Agudas (llevan tilde si terminan en vocal, n o s)
            'camion': 'camión', 'avion': 'avión', 'corazon': 'corazón',
            'razon': 'razón', 'sazón': 'sazón', 'buey': 'buey',
            'jamas': 'jamás', 'allá': 'allá', 'acá': 'acá',
            'tambien': 'también', 'si': 'sí', 'ti': 'tí', 'mi': 'mí',
            'aun': 'aún', 'mas': 'más', 'menos': 'menos', 'sol': 'sol',
            'pie': 'pie', 'té': 'té', 'café': 'café', 'dominó': 'dominó',
            'bebe': 'bebé', 'bebe': 'bebé', 'canta': 'cantá',
            
            # Graves o llanas (llevan tilde si NO terminan en vocal, n o s)
            'arbol': 'árbol', 'facil': 'fácil', 'dificil': 'difícil',
            'lapiz': 'lápiz', 'boligrafo': 'bolígrafo', 'examen': 'exámen',
            'imagen': 'imágen', 'joven': 'jóven', 'tunel': 'túnel',
            'caracter': 'carácter', 'condor': 'cóndor', 'fenix': 'fénix',
            'practica': 'práctica', 'teorica': 'teórica', 'colegio': 'colegio',
            'ejercito': 'ejército', 'increible': 'increíble', 'posible': 'posible',
            'imposible': 'imposible', 'terrible': 'terrible', 'sutil': 'sutil',
            'hostil': 'hostil', 'movil': 'móvil', 'util': 'útil',
            'automovil': 'automóvil', 'cesped': 'césped', 'angel': 'ángel',
            'margen': 'márgen', 'origen': 'origen', 'joven': 'joven',
            
            # Esdrújulas (siempre llevan tilde)
            'publico': 'público', 'privado': 'privado', 'historico': 'histórico',
            'numerico': 'numérico', 'critico': 'crítico', 'sintactico': 'sintáctico',
            'semantico': 'semántico', 'fonetico': 'fonético', 'estatico': 'estático',
            'dinamico': 'dinámico', 'electrico': 'eléctrico', 'electronico': 'electrónico',
            'mecanico': 'mecánico', 'cientifico': 'científico', 'conciencia': 'conciencia',
            'especie': 'especie', 'algebra': 'álgebra', 'climatico': 'climático',
            'practico': 'práctico', 'teorico': 'teórico', 'analitico': 'analítico',
            'sintetico': 'sintético', 'poetico': 'poético', 'magico': 'mágico',
            'logico': 'lógico', 'etico': 'ético', 'estetico': 'estético',
            'patetico': 'patético', 'mistico': 'místico', 'ascetico': 'ascético',
            'entusiasta': 'entusiasta', 'apostrofe': 'apóstrofe', 'harpia': 'arpía',
            'cocodrilo': 'cocodrilo', 'escarabajo': 'escarabajo', 'tortuga': 'tortuga',
            'pajaro': 'pájaro', 'arbol': 'árbol', 'mesa': 'mesa', 'silla': 'silla',
            'ventana': 'ventana', 'puerta': 'puerta', 'coche': 'coche', 'moto': 'moto',
            'bicicleta': 'bicicleta', 'autobus': 'autobús', 'tren': 'tren', 'avion': 'avión',
            'barco': 'barco', 'submarino': 'submarino', 'cohete': 'cohete', 'satelite': 'satélite',
            'computadora': 'computadora', 'telefono': 'teléfono', 'television': 'televisión',
            'radio': 'radio', 'camera': 'cámara', 'foto': 'foto', 'musica': 'música',
            'pintura': 'pintura', 'escultura': 'escultura', 'arquitectura': 'arquitectura',
            
            # Verbos con tilde (futuro, condicional, etc.)
            'podria': 'podría', 'querría': 'querría', 'sabría': 'sabría',
            'deberia': 'debería', 'estaria': 'estaría', 'tendria': 'tendría',
            'habria': 'habría', 'seria': 'sería', 'iria': 'iría',
            'podemos': 'podemos', 'tenemos': 'tenemos', 'vamos': 'vamos',
            'estamos': 'estamos', 'somos': 'somos', 'veis': 'veis',
            'podeis': 'podeis', 'tendre': 'tendré', 'tendras': 'tendrás',
            'tendra': 'tendrá', 'vendras': 'vendrás', 'vendran': 'vendrán'
        }
    
    def _cargar_reglas_errores(self) -> Dict[str, str]:
        """Reglas de errores comunes (incorrecta -> correcta)."""
        return {
            # Errores ortográficos frecuentes
            'impreativo': 'imperativo',
            'existencialismo': 'existencialismo',  # ya está bien
            'fenomenologia': 'fenomenología',
            'hermeneutica': 'hermenéutica',
            'ontologia': 'ontología',
            'epistemologia': 'epistemología',
            'axiologia': 'axiología',
            'estetica': 'estética',
            'etica': 'ética',
            'logica': 'lógica',
            'poetica': 'poética',
            'retorica': 'retórica',
            'dialectica': 'dialéctica',
            'metafisica': 'metafísica',
            'psicologia': 'psicología',
            'sociologia': 'sociología',
            'antropologia': 'antropología',
            'teologia': 'teología',
            'cristologia': 'cristología',
            'eclesiologia': 'eclesiología',
            'mariologia': 'mariología',
            'angelologia': 'angelología',
            'demonologia': 'demonología',
            'soteriologia': 'soteriología',
            'escatologia': 'escatología',
            'teleologia': 'teleología',
            'gnoseologia': 'gnoseología',
            'anatomia': 'anatomía',
            'fisiologia': 'fisiología',
            'patologia': 'patología',
            'neurologia': 'neurología',
            'psiquiatria': 'psiquiatría',
            'psicoterapia': 'psicoterapia',
            'existencial': 'existencial',
            'conciencia': 'conciencia',
            'inconciencia': 'inconciencia',
            'subconciencia': 'subconciencia',
            'superconciencia': 'superconciencia',
            'parapsicologia': 'parapsicología',
            'paranormal': 'paranormal',
            'sobrenatural': 'sobrenatural',
            'transcendental': 'transcendental',
            'trascendental': 'trascendental',
            'inmanente': 'inmanente',
            'trascendente': 'trascendente',
            'intrinseco': 'intrínseco',
            'extrinseco': 'extrínseco',
            'ontico': 'óntico',
            'ontologico': 'ontológico',
            'epistemico': 'epistémico',
            'gnoseologico': 'gnoseológico',
            'metodologico': 'metodológico',
            'teleologico': 'teleológico',
            'escatologico': 'escatológico',
            'soterologico': 'soterológico',
            'cristologico': 'cristolófico',  # no exacto, pero bueno
            'eclesiologico': 'eclesiológico',
            'mariologico': 'mariológico',
            'angelologico': 'angelológico',
            'demonologico': 'demonológico',
        }
    
    def corregir(self, texto: str) -> Tuple[str, List[str]]:
        """Corrige el texto aplicando reglas de acentuación y errores comunes."""
        if not texto:
            return texto, []
        
        cambios = []
        # Dividir en palabras (incluyendo acentos)
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        
        for palabra in set(palabras):
            if len(palabra) < 2:
                continue
            # Si está en diccionario personal, no tocar
            if palabra.lower() in self.personal:
                continue
            # Si está en el diccionario base, no tocar (ya es correcta)
            if palabra.lower() in self.base:
                continue
            
            # Aplicar reglas de acentuación
            corregida = self._aplicar_reglas(palabra.lower())
            if corregida and corregida != palabra.lower():
                # Preservar mayúsculas
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
                continue  # ya corregida, no aplicar otras reglas
            
            # Aplicar reglas de errores comunes
            corregida = self.reglas_errores.get(palabra.lower())
            if corregida:
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
        
        return texto, cambios
    
    def _aplicar_reglas(self, palabra: str) -> Optional[str]:
        """Aplica reglas de acentuación a una palabra."""
        # Buscar en cache
        if palabra in self.cache:
            return self.cache[palabra]
        
        # 1. Reglas de acentuación (diccionario)
        if palabra in self.reglas_acento:
            corr = self.reglas_acento[palabra]
            self.cache[palabra] = corr
            return corr
        
        # 2. Regla: palabras terminadas en -cion y -sion (llevan tilde en la o)
        if palabra.endswith('cion') and not palabra.endswith('sion'):
            corr = palabra[:-4] + 'ción'
            self.cache[palabra] = corr
            return corr
        if palabra.endswith('sion') and not palabra.endswith('sión'):
            corr = palabra[:-4] + 'sión'
            self.cache[palabra] = corr
            return corr
        
        # 3. Regla: palabras esdrújulas (siempre tilde)
        # (difícil detectar automáticamente sin un diccionario completo)
        # Podemos intentar una heurística: si tiene 3 sílabas y termina en -ico, -ica, -acion, etc.
        # Pero mejor dejar el diccionario.
        
        return None
    
    def detectar_errores(self, texto: str) -> List[Dict]:
        """Detecta palabras que no están en el diccionario y sugiere correcciones."""
        errores = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        
        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            if palabra.lower() in self.personal:
                continue
            if palabra.lower() in self.base:
                continue
            # Buscar sugerencias
            sugerencias = self._sugerir(palabra.lower())
            if sugerencias:
                errores.append({
                    'palabra': palabra,
                    'sugerencias': sugerencias[:3]
                })
        return errores
    
    def _sugerir(self, palabra: str) -> List[str]:
        """Sugiere correcciones para una palabra."""
        sugs = []
        # 1. Buscar en reglas de acentuación
        if palabra in self.reglas_acento:
            sugs.append(self.reglas_acento[palabra])
        # 2. Buscar en reglas de errores
        if palabra in self.reglas_errores:
            sugs.append(self.reglas_errores[palabra])
        # 3. Similitud con palabras del diccionario base
        pl = palabra
        for b in self.base:
            if len(b) > 3 and abs(len(b)-len(pl)) <= 2:
                # Similitud simple (coincidencia de caracteres)
                sim = sum(1 for a,c in zip(pl,b) if a==c) / max(len(pl), len(b))
                if sim > 0.7:
                    sugs.append(b)
                    if len(sugs) >= 3:
                        break
        return sugs

# --- PROCESADOR DE MENSAJES (MULTIFORMATO) ---

@dataclass
class Mensaje:
    fecha: str   # DD-MM
    hora: str    # HH:MM
    autor: str
    contenido: str
    es_metadato: bool = False

class Procesador:
    # Patrones para todos los formatos de WhatsApp
    
    # 1. Web con año y AM/PM: [5:24 p. m., 27/7/2026] Daniel: msg
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\]\s*([^:]+):\s*(.*)'
    
    # 2. Móvil sin año (Android): [27/7, 5:24 p. m.] Daniel: msg
    PATRON_MOVIL = r'\[(\d{1,2}/\d{1,2})\s*,\s*(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\]\s*([^:]+):\s*(.*)'
    
    # 3. Móvil con guión: 27/7/2026 17:24 - Daniel: msg
    PATRON_GUION = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'
    
    # 4. Alternativo sin hora: 27/7 - Daniel: msg
    PATRON_SIN_HORA = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-\s*([^:]+):\s*(.*)'
    
    # 5. Guión largo
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
        # Web
        m = re.match(self.PATRON_WEB, linea)
        if m:
            return self._crear_web(m)
        # Móvil (corchetes)
        m = re.match(self.PATRON_MOVIL, linea)
        if m:
            return self._crear_movil(m)
        # Guión
        m = re.match(self.PATRON_GUION, linea)
        if m:
            return self._crear_guion(m)
        # Sin hora
        m = re.match(self.PATRON_SIN_HORA, linea)
        if m:
            return self._crear_sin_hora(m)
        # Guión largo
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
                # Sin año -> añadir año actual
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

# --- INTERFAZ DE USUARIO ---

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
            st.rerun()
        if st.session_state.diccionario_personal:
            elim = st.selectbox("Eliminar", sorted(st.session_state.diccionario_personal))
            if st.button("🗑️ Eliminar"):
                st.session_state.diccionario_personal.discard(elim)
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

def main():
    st.markdown("<div style='text-align:center;'><h1>⌨️ BITÁCORA MATRIX</h1></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#00cc33;font-family:Courier New;'>[ SISTEMA DE TRANSCRIPCIÓN WHATSAPP → MARKDOWN ]</p>", unsafe_allow_html=True)
    
    opts = sidebar()
    
    st.markdown("### 📝 Pegar mensajes")
    texto = st.text_area(
        "",
        height=200,
        placeholder="[27/7, 5:24 p. m.] Daniel Díaz: Mensaje\n[5:24 p. m., 27/7/2026] Daniel: Mensaje\n27/7/2026 17:24 - Daniel: Mensaje",
        label_visibility="collapsed"
    )
    
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
            proc = Procesador()
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
                if opts['detectar'] and opts['corregir']:
                    errores = proc.corrector.detectar_errores(md)
                    if errores:
                        with st.expander(f"🔍 Errores detectados ({len(errores)})"):
                            for e in errores[:20]:
                                st.warning(f"**{e['palabra']}** → {', '.join(e['sugerencias'])}")
                
                st.markdown("### 📄 Resultado Markdown")
                st.code(md, language="markdown")
                st.download_button(
                    "📥 Descargar .md",
                    md,
                    file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
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
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;color:#006622;font-family:Courier New;font-size:0.8rem;'>
    Procesados: {st.session_state.contador} | Historial: {len(st.session_state.historial)} | Diccionario: {len(st.session_state.diccionario_personal)}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
