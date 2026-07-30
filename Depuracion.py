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
            'contra','desde','durante','entre','hacia','hasta','mediante',
            'según','sobre','tras','versus','vía',
            'la','las','lo','los','un','una','unos','unas','ello',
            # Verbos auxiliares (infinitivos)
            'ser','estar','tener','haber','hacer','poder','decir','ir',
            'ver','dar','saber','querer','llegar','pasar','deber','poner',
            'parecer','quedar','creer','hablar','llevar','dejar','seguir',
            'encontrar','llamar','venir','pensar','salir','volver','tomar',
            'conocer','vivir','sentir','tratar','mirar','contar','empezar',
            'esperar','buscar','existir','entrar','trabajar','escribir',
            'perder','producir','ocurrir','realizar','formar','actuar',
            'recibir','recordar','olvidar','caminar','correr','saltar',
            'nadar','volar','soñar','dormir','despertar','morir','nacer',
            'comer','beber','respirar','reír','llorar','gritar','susurrar',
            # Presente indicativo - verbos comunes
            'soy','eres','es','somos','sois','son',
            'estoy','estás','está','estamos','estáis','están',
            'tengo','tienes','tiene','tenemos','tenéis','tienen',
            'he','has','ha','hemos','habéis','han',
            'hago','haces','hace','hacemos','hacéis','hacen',
            'puedo','puedes','puede','podemos','podéis','pueden',
            'digo','dices','dice','decimos','decís','dicen',
            'voy','vas','va','vamos','vais','van',
            'veo','ves','ve','vemos','veis','ven',
            'doy','das','da','damos','dais','dan',
            'sé','sabes','sabe','sabemos','sabéis','saben',
            'quiero','quieres','quiere','queremos','queréis','quieren',
            'hablo','hablas','habla','hablamos','habláis','hablan',
            'como','comes','come','comemos','coméis','comen',
            'vivo','vives','vive','vivimos','vivís','viven',
            'tengo','tienes','tiene','tenemos','tenéis','tienen',
            'dije','dijiste','dijo','dijimos','dijisteis','dijeron',
            'fui','fuiste','fue','fuimos','fuisteis','fueron',
            'hice','hiciste','hizo','hicimos','hicisteis','hicieron',
            'tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron',
            'pude','pudiste','pudo','pudimos','pudisteis','pudieron',
            'quise','quisiste','quiso','quisimos','quisisteis','quisieron',
            'vine','viniste','vino','vinimos','vinisteis','vinieron',
            'hablé','hablaste','habló','hablamos','hablasteis','hablaron',
            # Futuro
            'seré','serás','será','seremos','seréis','serán',
            'estaré','estarás','estará','estaremos','estaréis','estarán',
            'tendré','tendrás','tendrá','tendremos','tendréis','tendrán',
            'habré','habrás','habrá','habremos','habréis','habrán',
            'haré','harás','hará','haremos','haréis','harán',
            'podré','podrás','podrá','podremos','podréis','podrán',
            'diré','dirás','dirá','diremos','diréis','dirán',
            'iré','irás','irá','iremos','iréis','irán',
            'veré','verás','verá','veremos','veréis','verán',
            'daré','darás','dará','daremos','daréis','darán',
            'sabré','sabrás','sabrá','sabremos','sabréis','sabrán',
            'querré','querrás','querrá','querremos','querréis','querrán',
            # Condicional
            'sería','serías','sería','seríamos','seríais','serían',
            'estaría','estarías','estaría','estaríamos','estaríais','estarían',
            'tendría','tendrías','tendría','tendríamos','tendríais','tendrían',
            'habría','habrías','habría','habríamos','habríais','habría',
            'haría','harías','haría','haríamos','haríais','harían',
            'podría','podrías','podría','podríamos','podríais','podrían',
            'diría','dirías','diría','diríamos','diríais','dirían',
            'iría','irías','iría','iríamos','iríais','irían',
            'querría','querrías','querría','querríamos','querríais','querrían',
            'sabría','sabrías','sabría','sabríamos','sabríais','sabrían',
            # Imperfecto
            'era','eras','era','éramos','erais','eran',
            'estaba','estabas','estaba','estábamos','estabais','estaban',
            'tenía','tenías','tenía','teníamos','teníais','tenían',
            'había','habías','había','habíamos','habíais','habían',
            'hacía','hacías','hacía','hacíamos','hacíais','hacían',
            'podía','podías','podía','podíamos','podíais','podían',
            'decía','decías','decía','decíamos','decíais','decían',
            'iba','ibas','iba','íbamos','ibais','iban',
            'veía','veías','veía','veíamos','veíais','veían',
            'daba','dabas','daba','dábamos','dabais','daban',
            'sabía','sabías','sabía','sabíamos','sabíais','sabían',
            'quería','querías','quería','queríamos','queríais','querían',
            'hablaba','hablabas','hablaba','hablábamos','hablabais','hablaban',
            # Sustantivos comunes
            'casa','trabajo','familia','amigo','amiga','amigos','amigas',
            'persona','personas','vida','muerte','tiempo','día','días',
            'mes','meses','año','años','hoy','mañana','ayer','semana',
            'lugar','lugares','cosa','cosas','mente','cuerpo','alma',
            'espíritu','corazón','amor','odio','felicidad','tristeza',
            'alegría','pena','sueño','sueños','realidad','fantasía',
            'verdad','mentira','belleza','fealdad','fuerza','debilidad',
            'sabiduría','ignorancia','poder','dinero','salud','enfermedad',
            'guerra','paz','libertad','esclavitud','justicia','injusticia',
            'derecho','ley','ciencia','arte','historia','filosofía',
            'literatura','música','pintura','cine','teatro','poesía',
            'novela','cuento','leyenda','mito','religión','dios','demonio',
            'ángel','cielo','infierno','paraíso','abismo','luz','oscuridad',
            'fuego','agua','tierra','aire','viento','sol','luna','estrella',
            'planeta','universo','galaxia','palabra','lenguaje','idioma',
            'cultura','pueblo','nación','ciudad','campo','mar','montaña',
            'valle','río','bosque','hombre','mujer','niño','niña',
            'padre','madre','hijo','hija','hermano','hermana',
            'libro','libros','mesa','silla','puerta','ventana','calle',
            'camino','coche','perro','gato','agua','comida','bebida',
            # Adjetivos
            'bueno','malo','buena','mala','buenos','malos','buenas','malas',
            'grande','pequeño','pequeña','grandes','pequeños','pequeñas',
            'alto','alta','bajo','baja','altos','altas','bajos','bajas',
            'largo','larga','corto','corta','largos','largas','cortos','cortas',
            'nuevo','nueva','viejo','vieja','nuevos','nuevas','viejos','viejas',
            'joven','jóvenes','fuerte','fuertes','débil','débiles',
            'rápido','rápida','lento','lenta','rápidos','rápidas','lentos','lentas',
            'claro','clara','oscuro','oscura','claros','claras','oscuros','oscuras',
            'caliente','frío','fría','calientes','fríos','frías',
            'dulce','salado','salada','amargo','amarga','dulces','salados','saladas',
            'feliz','triste','alegre','enojado','enojada','cansado','cansada',
            'ocupado','ocupada','libre','libres','inteligente','tonto','tonta',
            'sabio','sabia','loco','loca','cuerdo','cuerda','bello','bella',
            'feo','fea','peligroso','peligrosa','seguro','segura',
            'fácil','difícil','simple','complejo','compleja','profundo','profunda',
            'superficial','moderno','moderna','antiguo','antigua','real','falso','falsa',
            # Conectores y adverbios
            'pero','sino','embargo','no','obstante','además','también',
            'asimismo','incluso','entonces','después','luego','mientras',
            'cuando','donde','como','porque','ya','puesto','aunque','bien',
            'tanto','más','menos','muy','poco','poca','mucho','mucha',
            'algo','nada','todo','toda','todos','todas','cada','otro','otra',
            'mismo','misma','propios','propias','solo','sola','solos','solas',
            'aquí','ahí','allí','allá','acá','arriba','abajo','dentro','fuera',
            'cerca','lejos','delante','detrás','antes','ahora','siempre',
            'nunca','jamás','todavía','aún','ya','pronto','tarde','temprano',
            # Formas diacríticas (con tilde)
            'él','tú','sí','mí','té','sé','dé','aún','más','qué','quién',
            'quiénes','cuál','cuáles','cuánto','cuánta','cuántos','cuántas',
            'cómo','cuándo','dónde','por qué',
            # Preposiciones compuestas y locuciones
            'según','durante','mediante','excepto','salvo','barra','versus',
            'además','asimismo','también','inclusive','igualmente',
            'ciertamente','verdaderamente','realmente','efectivamente',
        }
        return base
    
    # --- Reglas de acentuación ---
    def _cargar_reglas_acento(self) -> Dict[str, str]:
        return {
            # -ción / -sión
            'camion': 'camión', 'avion': 'avión', 'corazon': 'corazón',
            'razon': 'razón', 'sazon': 'sazón', 'emocion': 'emoción',
            'decision': 'decisión', 'mision': 'misión', 'vision': 'visión',
            'television': 'televisión', 'educacion': 'educación',
            'informacion': 'información', 'comunicacion': 'comunicación',
            'relacion': 'relación', 'situacion': 'situación',
            'posicion': 'posición', 'condicion': 'condición',
            'operacion': 'operación', 'organizacion': 'organización',
            'nacion': 'nación', 'poblacion': 'población',
            'cancion': 'canción', 'reunion': 'reunión',
            'opinion': 'opinión', 'intencion': 'intención',
            'solucion': 'solución', 'evolucion': 'evolución',
            'revolucion': 'revolución', 'construccion': 'construcción',
            'produccion': 'producción', 'direccion': 'dirección',
            'proteccion': 'protección', 'conexion': 'conexión',
            'reflexion': 'reflexión', 'expresion': 'expresión',
            # Adverbios terminados en -mente
            'jamas': 'jamás', 'tambien': 'también', 'ademas': 'además',
            'facil': 'fácil', 'dificil': 'difícil',
            'arbol': 'árbol', 'lapiz': 'lápiz', 'tunel': 'túnel',
            'boligrafo': 'bolígrafo', 'pajaro': 'pájaro',
            'caracter': 'carácter', 'condor': 'cóndor', 'fenix': 'fénix',
            'ejercito': 'ejército', 'cesped': 'césped', 'angel': 'ángel',
            'increible': 'increíble', 'movil': 'móvil', 'util': 'útil',
            'automovil': 'automóvil', 'satelite': 'satélite',
            'telefono': 'teléfono', 'musica': 'música',
            'medico': 'médico', 'pacifico': 'pacífico', 'publico': 'público',
            'historico': 'histórico', 'numerico': 'numérico',
            'critico': 'crítico', 'sintactico': 'sintáctico',
            'semantico': 'semántico', 'fonetico': 'fonético',
            'estatico': 'estático', 'dinamico': 'dinámico',
            'electrico': 'eléctrico', 'electronico': 'electrónico',
            'mecanico': 'mecánico', 'cientifico': 'científico',
            'algebra': 'álgebra', 'climatico': 'climático',
            'practico': 'práctico', 'teorico': 'teórico',
            'analitico': 'analítico', 'sintetico': 'sintético',
            'poetico': 'poético', 'magico': 'mágico', 'logico': 'lógico',
            'etico': 'ético', 'estetico': 'estético', 'patetico': 'patético',
            'mistico': 'místico', 'ascetico': 'ascético',
            'practica': 'práctica', 'teorica': 'teórica',
            'autobus': 'autobús', 'camion': 'camión',
            # Condicionales
            'podria': 'podría', 'deberia': 'debería', 'estaria': 'estaría',
            'tendria': 'tendría', 'habria': 'habría', 'seria': 'sería',
            'podrias': 'podrías', 'deberias': 'deberías', 'estarias': 'estarías',
            'tendrias': 'tendrías', 'habrias': 'habrías', 'serias': 'serías',
            'querria': 'querría', 'sabria': 'sabría', 'diria': 'diría',
            'iria': 'iría', 'vendria': 'vendría', 'haría': 'haría',
            # Interrogativos/exclamativos (se manejan en diacríticas)
            'que': 'qué', 'quien': 'quién', 'cual': 'cuál',
            'cuanto': 'cuánto', 'donde': 'dónde', 'como': 'cómo',
            'cuando': 'cuándo', 'por que': 'por qué',
            # Errores comunes
            'sobretodo': 'sobre todo', 'siempre': 'siempre',
            'tio': 'tío', 'rio': 'río', 'garcia': 'garcía',
            'perez': 'pérez', 'gomez': 'gómez', 'rodriguez': 'rodríguez',
            'martinez': 'martínez', 'gonzalez': 'gonzález',
            'lopez': 'lópez', 'hernandez': 'hernández',
            'dias': 'días', 'anos': 'años', 'razones': 'razones',
            'corazones': 'corazones', 'canciones': 'canciones',
            'reuniones': 'reuniones', 'decisiones': 'decisiones',
        }
    
    # --- Reglas de errores comunes ---
    def _cargar_reglas_errores(self) -> Dict[str, str]:
        return {
            'impreativo': 'imperativo',
            'fenomenologia': 'fenomenología', 'hermeneutica': 'hermenéutica',
            'ontologia': 'ontología', 'epistemologia': 'epistemología',
            'axiologia': 'axiología', 'estetica': 'estética',
            'etica': 'ética', 'logica': 'lógica', 'poetica': 'poética',
            'retorica': 'retórica', 'dialectica': 'dialéctica',
            'metafisica': 'metafísica', 'psicologia': 'psicología',
            'sociologia': 'sociología', 'antropologia': 'antropología',
            'teologia': 'teología', 'cristologia': 'cristología',
            'eclesiologia': 'eclesiología', 'mariologia': 'marialogía',
            'angelologia': 'angelología', 'demonologia': 'demonología',
            'soteriologia': 'soteriología', 'escatologia': 'escatología',
            'teleologia': 'teleología', 'gnoseologia': 'gnoseología',
            'anatomia': 'anatomía', 'fisiologia': 'fisiología',
            'patologia': 'patología', 'neurologia': 'neurología',
            'psiquiatria': 'psiquiatría', 'psicoterapia': 'psicoterapia',
            'intrinseco': 'intrínseco', 'extrinseco': 'extrínseco',
            'ontico': 'óntico', 'ontologico': 'ontológico',
            'epistemico': 'epistémico', 'gnoseologico': 'gnoseológico',
            'metodologico': 'metodológico', 'teleologico': 'teleológico',
            'escatologico': 'escatológico', 'soterologico': 'soterológico',
            'k': 'que', 'q': 'que', 'xq': 'por qué', 'x': 'por',
            'tb': 'también', 'tmb': 'también', 'pq': 'porque',
            'xk': 'porque', 'mas o menos': 'más o menos',
            'sierto': 'cierto', 'siertos': 'ciertos',
            'hize': 'hice', 'hiciste': 'hiciste', 'valla': 'vaya',
            'aya': 'haya', 'alla': 'allá', 'aca': 'acá',
            'asi': 'así', 'aun': 'aún', 'tio': 'tío', 'tios': 'tíos',
            'salu2': 'saludos', 'besos': 'besos', 'abrazos': 'abrazos',
            'grasias': 'gracias', 'grax': 'gracias', 'dvd': 'de vuelta',
        }
    
    # --- Reglas diacríticas con contexto ---
    def _cargar_reglas_diacriticas(self) -> Dict:
        return {
            'el': {'tilde': 'él', 'funcion': self._es_pronombre_el},
            'tu': {'tilde': 'tú', 'funcion': self._es_pronombre_tu},
            'si': {'tilde': 'sí', 'funcion': self._es_afirmacion_si},
            'mas': {'tilde': 'más', 'funcion': self._es_adverbio_mas},
            'se': {'tilde': 'sé', 'funcion': self._es_verbo_se},
            'te': {'tilde': 'té', 'funcion': self._es_sustantivo_te},
            'mi': {'tilde': 'mí', 'funcion': self._es_pronombre_mi},
            'de': {'tilde': 'dé', 'funcion': self._es_verbo_de},
            'aun': {'tilde': 'aún', 'funcion': self._es_adverbio_aun},
        }
    
    def _cargar_verbos_comunes(self) -> set:
        return {
            # Ser/estar
            'es','era','fue','será','sería','está','estaba','estuvo','estará','estaría',
            'son','eran','fueron','serán','serían','están','estaban','estuvieron','estarán','estarían',
            'soy','eres','somos','sois','estoy','estás','estamos','estáis',
            # Tener/hacer
            'tiene','tenía','tuvo','tendrá','tendría','hace','hacía','hizo','hará','haría',
            'tienen','tenían','tuvieron','tendrán','tendrían','hacen','hacían','hicieron','harán','harían',
            'tengo','tienes','tenemos','tenéis','hago','haces','hacemos','hacéis',
            # Poder/querer/deber
            'puede','podía','pudo','podrá','podría','quiere','quería','quiso','querrá','querría',
            'pueden','podían','pudieron','podrán','podrían','quieren','querían','quisieron','querrán','querrían',
            'puedo','puedes','podemos','podéis','quiero','quieres','queremos','queréis',
            'debe','debía','debió','deberá','debería',
            'deben','debían','debieron','deberán','deberían',
            # Ir/venir
            'va','iba','fue','irá','iría','viene','venía','vino','vendrá','vendría',
            'van','iban','fueron','irán','irían','vienen','venían','vinieron','vendrán','vendrían',
            'voy','vas','vamos','vais','vengo','vienes','venimos','venís',
            # Ver/decir/saber
            've','veía','vio','verá','vería','dice','decía','dijo','dirá','diría',
            'ven','veían','vieron','verán','verían','dicen','decían','dijeron','dirán','dirían',
            'veo','ves','vemos','veis','digo','dices','decimos','decís',
            'sabe','sabía','supo','sabrá','sabría',
            'saben','sabían','supieron','sabrán','sabrían',
            'sé','sabes','sabemos','sabéis',
            # Hablar/pensar/llamar
            'habla','hablaba','habló','hablará','hablaría',
            'hablan','hablaban','hablaron','hablarán','hablarían',
            'piensa','pensaba','pensó','pensará','pensaría',
            'llama','llamaba','llamó','llamará','llamaría',
            # Buscar/encontrar
            'busca','buscaba','buscó','buscará','buscaría',
            'encuentra','encontraba','encontró','encontrará','encontraría',
            # Verbo "hay"
            'hay','había','hubo','habrá','habría',
        }
    
    # === FUNCIONES DE CONTEXTO PARA TILDES DIACRÍTICAS ===
    
    def _limpiar_puntuacion(self, palabra: str) -> str:
        """Quita puntuación de una palabra."""
        return palabra.lower().strip('.,;:!?¿¡()[]{}"\'«»-—')
    
    def _es_pronombre_el(self, idx: int, palabras: List[str]) -> bool:
        """'el' → 'él' si va seguido de verbo o está aislado."""
        if idx + 1 >= len(palabras):
            return False  # Al final suele ser artículo
        siguiente = self._limpiar_puntuacion(palabras[idx + 1])
        # Si la siguiente es verbo común
        if siguiente in self.verbos_comunes:
            return True
        # Si va seguido de pronombre (él me dijo, él te vio)
        if siguiente in {'me','te','le','nos','os','les','lo','la','los','las'}:
            return True
        # Si va seguido de adjetivo que lo describe (él mismo, él solo)
        if siguiente in {'mismo','misma','solo','sola','mismos','mismas'}:
            return True
        return False
    
    def _es_pronombre_tu(self, idx: int, palabras: List[str]) -> bool:
        """'tu' → 'tú' si va seguido de verbo o 'mismo'."""
        if idx + 1 >= len(palabras):
            return False
        siguiente = self._limpiar_puntuacion(palabras[idx + 1])
        if siguiente in self.verbos_comunes:
            return True
        if siguiente in {'mismo','misma','mismos','mismas'}:
            return True
        # "tu que..." (tú, que...)
        if siguiente in {'que','quien'}:
            return True
        return False
    
    def _es_afirmacion_si(self, idx: int, palabras: List[str]) -> bool:
        """'si' → 'sí' si es afirmación o sustantivo 'el sí'."""
        palabra_actual = self._limpiar_puntuacion(palabras[idx])
        
        # Si está al inicio de la oración seguido de coma
        if idx == 0:
            if idx + 1 < len(palabras):
                sig = palabras[idx + 1].strip()
                if sig.startswith(',') or sig.startswith('.'):
                    return True
            return False
        
        # Si va antes de coma o punto (afirmación)
        if idx + 1 < len(palabras):
            siguiente = palabras[idx + 1].strip()
            if siguiente.startswith(',') or siguiente.startswith('.') or siguiente.startswith('!'):
                return True
        
        # "si mismo" → "sí mismo"
        if idx + 1 < len(palabras):
            if self._limpiar_puntuacion(palabras[idx + 1]) in {'mismo','misma'}:
                return True
        
        # "el si" / "un si" → "el sí" / "un sí"
        if idx > 0:
            anterior = self._limpiar_puntuacion(palabras[idx - 1])
            if anterior in {'el','la','un','una','los','las','unos','unas','mi','tu','su'}:
                return True
        
        # "dijo que si" → "dijo que sí"
        if idx > 0:
            anterior = self._limpiar_puntuacion(palabras[idx - 1])
            if anterior == 'que':
                # Verificar si hay verbo antes
                if idx >= 2:
                    ant2 = self._limpiar_puntuacion(palabras[idx - 2])
                    if ant2 in self.verbos_comunes or ant2 in {'dijo','respondió','contestó','afirmó','preguntó'}:
                        return True
        
        # "si" al final de la frase (respuesta)
        if idx == len(palabras) - 1:
            return True
        
        return False
    
    def _es_adverbio_mas(self, idx: int, palabras: List[str]) -> bool:
        """'mas' → 'más' casi siempre (excepto conjunción 'pero')."""
        # Si va seguido de estas palabras, es conjunción (= pero)
        if idx + 1 < len(palabras):
            siguiente = self._limpiar_puntuacion(palabras[idx + 1])
            if siguiente in {'sino','bien','aunque','eso','cuando'}:
                # "mas bien" podría ser "más bien" (adverbio)
                if siguiente == 'bien':
                    return True
                return False
        
        # Por defecto, es "más" (adverbio de cantidad)
        return True
    
    def _es_verbo_se(self, idx: int, palabras: List[str]) -> bool:
        """'se' → 'sé' si es imperativo de saber/ser."""
        if idx + 1 >= len(palabras):
            return False
        siguiente = self._limpiar_puntuacion(palabras[idx + 1])
        
        # "sé que..." (saber)
        if siguiente == 'que':
            return True
        
        # "sé tú mismo", "sé feliz", "sé bueno", etc.
        adjetivos_imperativo = {
            'feliz','bueno','buena','amable','inteligente','amigo','amiga',
            'fuerte','valiente','honesto','honesta','paciente','generoso','generosa',
            'cariñoso','cariñosa','amable','cordial','atento','atenta',
            'mismo','misma','tu','vos','usted',
        }
        if siguiente in adjetivos_imperativo:
            return True
        
        return False
    
    def _es_sustantivo_te(self, idx: int, palabras: List[str]) -> bool:
        """'te' → 'té' si es la bebida."""
        # "el te", "un te", "tomar te", "beber te"
        if idx > 0:
            anterior = self._limpiar_puntuacion(palabras[idx - 1])
            if anterior in {'el','la','un','una','los','las','mi','tu','su'}:
                # Verificar si después viene algo que no sea verbo
                if idx + 1 < len(palabras):
                    siguiente = self._limpiar_puntuacion(palabras[idx + 1])
                    if siguiente not in self.verbos_comunes:
                        return True
                else:
                    return True
        
        # "te verde", "te negro", "te caliente"
        if idx + 1 < len(palabras):
            siguiente = self._limpiar_puntuacion(palabras[idx + 1])
            if siguiente in {'verde','negro','negra','blanco','blanca','caliente','frio','fría','hirviendo'}:
                return True
        
        return False
    
    def _es_pronombre_mi(self, idx: int, palabras: List[str]) -> bool:
        """'mi' → 'mí' si es pronombre personal (después de preposición)."""
        if idx == 0:
            return False
        anterior = self._limpiar_puntuacion(palabras[idx - 1])
        # Después de preposición
        preposiciones = {'para','a','de','por','con','sin','sobre','entre','hacia','hasta','según','tras'}
        if anterior in preposiciones:
            return True
        return False
    
    def _es_verbo_de(self, idx: int, palabras: List[str]) -> bool:
        """'de' → 'dé' si es subjuntivo de dar."""
        # "espero que me dé", "quiero que le dé", "ojalá dé"
        if idx > 0:
            anterior = self._limpiar_puntuacion(palabras[idx - 1])
            # Después de pronombres objeto + que
            if anterior in {'me','te','le','nos','os','les'}:
                # Verificar si hay "que" antes
                if idx >= 2:
                    ant2 = self._limpiar_puntuacion(palabras[idx - 2])
                    if ant2 == 'que':
                        return True
        return False
    
    def _es_adverbio_aun(self, idx: int, palabras: List[str]) -> bool:
        """'aun' → 'aún' si es adverbio de tiempo (= todavía)."""
        # "aún no", "aún sí", "aún cuando", "aún falta"
        if idx + 1 < len(palabras):
            siguiente = self._limpiar_puntuacion(palabras[idx + 1])
            if siguiente in {'no','cuando','falta','queda','quedan','faltan','no','si','está','están','puede','pueden'}:
                return True
        
        # "ni aun" → "ni aún"
        if idx > 0:
            anterior = self._limpiar_puntuacion(palabras[idx - 1])
            if anterior in {'ni','incluso','hasta'}:
                return True
        
        return False
    
    # === ALGORITMO DE LEVENSHTEIN ===
    
    @staticmethod
    def levenshtein(s1: str, s2: str) -> int:
        """Distancia de Levenshtein eficiente."""
        if len(s1) < len(s2):
            return CorrectorOrtografico.levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    # === CORRECCIÓN PRINCIPAL ===
    
    def corregir(self, texto: str) -> Tuple[str, List[str]]:
        if not texto:
            return texto, []
        
        cambios = []
        
        # PASO 1: Corregir tildes diacríticas con contexto
        texto, cambios_diacriticos = self._corregir_diacriticas(texto)
        cambios.extend(cambios_diacriticos)
        
        # PASO 2: Corregir tildes generales y errores
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        for palabra in set(palabras):
            if len(palabra) < 2:
                continue
            if palabra.lower() in self.personal:
                continue
            if palabra.lower() in self.base:
                continue
            
            # Intentar reglas de acento
            corregida = self._aplicar_reglas(palabra.lower())
            if corregida and corregida != palabra.lower():
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
                continue
            
            # Intentar reglas de errores
            corregida = self.reglas_errores.get(palabra.lower())
            if corregida:
                if palabra[0].isupper():
                    corregida = corregida.capitalize()
                texto = texto.replace(palabra, corregida)
                cambios.append(f"{palabra} → {corregida}")
        
        # PASO 3: Capitalización post-punto
        texto = self._capitalizar_oraciones(texto)
        
        return texto, cambios
    
    def _corregir_diacriticas(self, texto: str) -> Tuple[str, List[str]]:
        """Aplica correcciones diacríticas basadas en contexto."""
        cambios = []
        palabras = texto.split()
        resultado = []
        
        for i, palabra in enumerate(palabras):
            limpia = self._limpiar_puntuacion(palabra)
            
            if limpia in self.reglas_diacriticas:
                regla = self.reglas_diacriticas[limpia]
                if regla['funcion'](i, palabras):
                    forma_tildada = regla['tilde']
                    # Conservar mayúscula inicial
                    if palabra[0].isupper():
                        forma_tildada = forma_tildada.capitalize()
                    
                    # Reemplazar manteniendo puntuación
                    palabra_nueva = palabra.replace(limpia, forma_tildada)
                    if palabra_nueva != palabra:
                        cambios.append(f"{palabra} → {palabra_nueva}")
                        palabra = palabra_nueva
            
            resultado.append(palabra)
        
        return ' '.join(resultado), cambios
    
    def _capitalizar_oraciones(self, texto: str) -> str:
        """Pone mayúscula después de . ? !"""
        def reemplazar(match):
            return match.group(1) + match.group(2).upper()
        
        # Después de . ? ! seguido de espacio
        texto = re.sub(r'([.!?]\s+)([a-záéíóúñ])', reemplazar, texto)
        # Primera letra del texto
        if texto and texto[0].islower():
            texto = texto[0].upper() + texto[1:]
        return texto
    
    def _aplicar_reglas(self, palabra: str) -> Optional[str]:
        if palabra in self.cache:
            return self.cache[palabra]
        
        if palabra in self.reglas_acento:
            corr = self.reglas_acento[palabra]
            self.cache[palabra] = corr
            return corr
        
        # Regla: -cion → -ción
        if palabra.endswith('cion') and not palabra.endswith('sion'):
            corr = palabra[:-4] + 'ción'
            self.cache[palabra] = corr
            return corr
        
        # Regla: -sion → -sión
        if palabra.endswith('sion') and not palabra.endswith('sión'):
            corr = palabra[:-4] + 'sión'
            self.cache[palabra] = corr
            return corr
        
        return None
    
    # === DETECCIÓN DE ERRORES ===
    
    def detectar_errores(self, texto: str) -> List[Dict]:
        errores = []
        palabras = re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b', texto)
        for palabra in set(palabras):
            if len(palabra) < 3:
                continue
            if palabra.lower() in self.personal:
                continue
            if palabra.lower() in self.base:
                continue
            # Si está en reglas, no es error
            if palabra.lower() in self.reglas_acento or palabra.lower() in self.reglas_errores:
                continue
            sugerencias = self._sugerir(palabra.lower())
            if sugerencias:
                errores.append({'palabra': palabra, 'sugerencias': sugerencias[:3]})
        return errores
    
    def _sugerir(self, palabra: str) -> List[str]:
        """Sugerencias basadas en Levenshtein real."""
        sugs = []
        
        # Primero reglas conocidas
        if palabra in self.reglas_acento:
            sugs.append(self.reglas_acento[palabra])
        if palabra in self.reglas_errores:
            sugs.append(self.reglas_errores[palabra])
        
        # Distancia de Levenshtein real
        candidatos = []
        palabra_sin_tilde = self._quitar_tildes(palabra)
        
        for b in self.base:
            if len(b) < 3:
                continue
            # Filtrado rápido por longitud
            if abs(len(b) - len(palabra_sin_tilde)) > 2:
                continue
            
            # Comparar sin tildes para mayor robustez
            b_sin_tilde = self._quitar_tildes(b)
            dist = self.levenshtein(palabra_sin_tilde, b_sin_tilde)
            
            # Solo sugerir si la distancia es pequeña relativa al largo
            max_dist = max(1, len(palabra_sin_tilde) // 3)
            if dist <= max_dist and dist > 0:
                candidatos.append((dist, b))
        
        # Ordenar por distancia y tomar las mejores
        candidatos.sort(key=lambda x: x[0])
        for _, palabra_sugerida in candidatos[:3]:
            if palabra_sugerida not in sugs:
                sugs.append(palabra_sugerida)
        
        return sugs
    
    @staticmethod
    def _quitar_tildes(texto: str) -> str:
        """Quita tildes usando Unicode."""
        nfkd = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ============================================================================
# PROCESADOR DE MENSAJES (con regex corregidos)
# ============================================================================
@dataclass
class Mensaje:
    fecha: str
    hora: str
    autor: str
    contenido: str
    es_metadato: bool = False

class Procesador:
    # Regex corregidos: escape de corchetes y .* al final para capturar contenido completo
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\]\s*([^:]+):\s*(.*)'
    PATRON_MOVIL = r'\[(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,\s*(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\]\s*([^:]+):\s*(.*)'
    PATRON_GUION = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'
    PATRON_SIN_HORA = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s-\s*([^:]+):\s*(.*)'
    
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


# ============================================================================
# FUNCIONES DE LA INTERFAZ
# ============================================================================
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


# ============================================================================
# MAIN
# ============================================================================
def main():
    st.markdown("<div style='text-align:center;'><h1>⌨️ Transcripción Bitácora</h1></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#00cc33;font-family:Courier New;font-size:0.9rem;'>[ SISTEMA DE TRANSCRIPCIÓN WHATSAPP → MARKDOWN + CORRECTOR DE TILDES v4.0 ]</p>", unsafe_allow_html=True)
    
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
            
            # --- MODO TEXTO PLANO ---
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
            
            # --- MODO WHATSAPP ---
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
    
    # --- Footer ---
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
    Procesados: {st.session_state.contador} | Historial: {len(st.session_state.historial)} | Diccionario: {len(st.session_state.diccionario_personal)}
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
