import streamlit as st
import re
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="Bitácora", layout="centered")

st.markdown("""
<style>
    .stApp { background: #0a0a0a; }
    .stTextArea textarea { 
        background: #1a1a1a; 
        color: #00ff41; 
        border: 1px solid #00ff41; 
        font-family: monospace;
    }
    .stButton button {
        background: #1a1a1a;
        color: #00ff41;
        border: 1px solid #00ff41;
        font-weight: bold;
    }
    .stButton button:hover {
        background: #00ff41;
        color: #0a0a0a;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Bitácora Lite")

texto_input = st.text_area(
    "Pega aquí los mensajes de WhatsApp (Web o Móvil):",
    height=200,
    placeholder="[5:24 p. m., 27/7/2026] Daniel Diaz: Mensaje\n27/7/2026 17:24 - Daniel Diaz: Mensaje"
)

if st.button("Generar"):
    if not texto_input.strip():
        st.warning("Pega algunos mensajes primero.")
    else:
        # --- Parser simple ---
        mensajes_por_dia = defaultdict(list)
        lineas_no_parseadas = []

        patron_web = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}/\d{2,4})\]\s*([^:]+):\s*(.*)'
        patron_movil = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'
        patron_alt = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*([^:]+):\s*(.*)'

        for linea in texto_input.strip().split('\n'):
            if not linea.strip():
                continue

            match = re.match(patron_web, linea)
            if match:
                fecha_str = match.group(3)
                autor = match.group(4).strip()
                contenido = match.group(5).strip()
            else:
                match = re.match(patron_movil, linea)
                if match:
                    fecha_str = match.group(1)
                    autor = match.group(3).strip()
                    contenido = match.group(4).strip()
                else:
                    match = re.match(patron_alt, linea)
                    if match:
                        fecha_str = match.group(1)
                        autor = match.group(2).strip()
                        contenido = match.group(3).strip()
                    else:
                        lineas_no_parseadas.append(linea.strip())
                        continue

            # Formatear fecha
            try:
                fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                fecha = fecha_dt.strftime('%d-%m')
            except:
                fecha = fecha_str

            # Limpiar contenido básico
            contenido = re.sub(r'https?://[^\s]+', '', contenido)
            contenido = re.sub(r'<Multimedia omitido>|IMG[_-]\d+|VIDEO[_-]\d+', '', contenido, flags=re.IGNORECASE)
            contenido = contenido.strip()

            if contenido:
                mensajes_por_dia[fecha].append(contenido)

        if not mensajes_por_dia:
            st.error("No se encontraron mensajes válidos.")
            if lineas_no_parseadas:
                with st.expander("🔍 Líneas no reconocidas (primeras 10)"):
                    for ln in lineas_no_parseadas[:10]:
                        st.code(ln)
        else:
            # Generar Markdown
            lineas = []
            mes_actual = datetime.now().month
            meses_romanos = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
                             7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'}
            titulo = f"# {meses_romanos.get(mes_actual, '')}: {datetime.now().strftime('%B')}"
            lineas.append(titulo)
            lineas.append("")

            for fecha, contenidos in sorted(mensajes_por_dia.items()):
                lineas.append(f"## {fecha}")
                for c in contenidos:
                    lineas.append(c)
                lineas.append("")

            resultado = '\n'.join(lineas)

            st.code(resultado, language="markdown")

            st.download_button(
                label="📥 Descargar .md",
                data=resultado,
                file_name=f"bitacora_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )

            st.success(f"✅ {sum(len(v) for v in mensajes_por_dia.values())} mensajes procesados, {len(mensajes_por_dia)} días.")
