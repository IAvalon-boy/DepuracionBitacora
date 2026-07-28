class ProcesadorMensajes:
    """Procesador con soporte mejorado para múltiples formatos (Web y Móvil)"""

    # --- FORMATOS SOPORTADOS ---

    # 1. WhatsApp Web (con corchetes, con o sin AM/PM, con o sin espacios)
    # Ej: [5:24 p. m., 27/7/2026] Daniel Diaz: Mensaje
    #     [17:24, 27/7/2026] Daniel Diaz: Mensaje
    PATRON_WEB = r'\[(\d{1,2}:\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\s*,\s*(\d{1,2}/\d{1,2}/\d{2,4})\]\s*([^:]+):\s*(.*)'

    # 2. WhatsApp Web sin AM/PM (24h) - ya incluido en el anterior

    # 3. WhatsApp Móvil (sin corchetes, con guión)
    # Ej: 27/7/2026 17:24 - Daniel Diaz: Mensaje
    #     27/07/2026, 17:24 - Daniel Diaz: Mensaje
    #     27/07/2026 5:24 p. m. - Daniel Diaz: Mensaje (raro)
    PATRON_MOVIL = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*,?\s*(\d{1,2}:\d{2}\s*(?:a\.?\s*m\.?|p\.?\s*m\.?)?)\s*-\s*([^:]+):\s*(.*)'

    # 4. Formato alternativo: solo fecha y autor (sin hora)
    # Ej: 27/7/2026 - Daniel Diaz: Mensaje
    PATRON_ALT = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*([^:]+):\s*(.*)'

    # 5. Formato con guión largo o diferente
    # Ej: 27/7/2026 – Daniel Diaz: Mensaje  (con guión largo)
    PATRON_ALT2 = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*[–—-]\s*([^:]+):\s*(.*)'

    PATRON_MULTIMEDIA = r'<Multimedia omitido>|IMG[_-]\d+|VIDEO[_-]\d+|\.(jpg|png|gif|mp4|pdf|docx?)'
    PATRON_ADJUNTO = r'Documento omitido|Audio omitido|Archivo omitido|Archivo adjunto'
    PATRON_ENLACE = r'https?://[^\s]+'

    def __init__(self):
        self.corrector = CorrectorOrtografico()
        self._cache_fechas = {}

    def procesar(self, texto: str) -> Tuple[List[Mensaje], List[str]]:
        """Procesa texto y retorna (mensajes, lineas_no_parseadas)"""
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
        # Intentar formato Web (con corchetes)
        match = re.match(self.PATRON_WEB, linea)
        if match:
            return self._crear_desde_web(match)

        # Intentar formato Móvil (con guión)
        match = re.match(self.PATRON_MOVIL, linea)
        if match:
            return self._crear_desde_movil(match)

        # Intentar formato alternativo (solo fecha y autor)
        match = re.match(self.PATRON_ALT, linea)
        if match:
            return self._crear_desde_alt(match)

        # Intentar formato con guión largo
        match = re.match(self.PATRON_ALT2, linea)
        if match:
            return self._crear_desde_alt(match)

        return None

    def _crear_desde_web(self, match) -> Mensaje:
        hora = match.group(1)
        ampm = match.group(2) or ''
        fecha_str = match.group(3)
        autor = match.group(4).strip()
        contenido = match.group(5).strip()

        hora_24 = self._convertir_hora(hora, ampm)
        fecha = self._formatear_fecha(fecha_str)

        return self._crear_mensaje(fecha, hora_24, autor, contenido)

    def _crear_desde_movil(self, match) -> Mensaje:
        fecha_str = match.group(1)
        hora_ampm = match.group(2).strip()
        autor = match.group(3).strip()
        contenido = match.group(4).strip()

        # Extraer hora y posible AM/PM
        # Si la hora contiene AM/PM, separar
        ampm = ''
        hora = hora_ampm
        if re.search(r'a\.?\s*m\.?|p\.?\s*m\.?', hora_ampm, re.IGNORECASE):
            # Dividir en hora y ampm
            partes = re.split(r'\s+(?=a\.?\s*m\.?|p\.?\s*m\.?)', hora_ampm, flags=re.IGNORECASE)
            if len(partes) == 2:
                hora = partes[0]
                ampm = partes[1]

        hora_24 = self._convertir_hora(hora, ampm)
        fecha = self._formatear_fecha(fecha_str)

        return self._crear_mensaje(fecha, hora_24, autor, contenido)

    def _crear_desde_alt(self, match) -> Mensaje:
        fecha_str = match.group(1)
        autor = match.group(2).strip()
        contenido = match.group(3).strip()

        fecha = self._formatear_fecha(fecha_str)
        return self._crear_mensaje(fecha, "00:00", autor, contenido)

    def _crear_mensaje(self, fecha: str, hora: str, autor: str, contenido: str) -> Mensaje:
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
        if not ampm:
            return hora
        try:
            h, m = map(int, hora.split(':'))
            ampm_clean = ampm.lower().replace(' ', '').replace('.', '')
            if 'pm' in ampm_clean and h < 12:
                h += 12
            elif 'am' in ampm_clean and h == 12:
                h = 0
            return f"{h:02d}:{m:02d}"
        except:
            return hora

    def _formatear_fecha(self, fecha_str: str) -> str:
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
        contenido = msg.contenido
        if eliminar_enlaces:
            contenido = re.sub(self.PATRON_ENLACE, '', contenido)
        if eliminar_adjuntos:
            contenido = re.sub(self.PATRON_MULTIMEDIA, '', contenido, flags=re.IGNORECASE)
            contenido = re.sub(self.PATRON_ADJUNTO, '', contenido, flags=re.IGNORECASE)
        contenido = re.sub(r'\d{1,2}:\d{2}', '', contenido)
        return contenido.strip()

    def generar_markdown(self, mensajes: List[Mensaje], opciones: Dict) -> str:
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
