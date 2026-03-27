import os
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Table, TableStyle, PageBreak, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, portrait, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import date, datetime, timedelta
import tempfile
import pandas as pd
import re
from reportlab.lib.colors import HexColor, white, black

def color_texto_contraste(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    luminancia = (0.299*r + 0.587*g + 0.114*b)
    return black if luminancia > 186 else white

def truncar(texto, max_chars=12):
    texto = str(texto)
    return texto[:max_chars] + '...' if len(texto) > max_chars else texto

def procesar_marcacion(texto):
    if pd.isna(texto) or texto == "":
        return ""
    texto = str(texto).strip()
    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', texto):
        return formatear_fecha_corta(texto)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', texto):
        return formatear_fecha_corta(texto)
    partes = texto.split("|")
    nomenclatura = partes[0].strip()
    marcas = re.findall(r'\d{2}:\d{2}|\?|!', texto)
    if marcas.count("?") >= 2:
        return nomenclatura
    if len(marcas) == 0:
        return nomenclatura
    elif len(marcas) == 1:
        return marcas[0]
    else:
        return "\n".join(marcas[:2])

ABREVIACIONES = {
    'nombre del colaborador': 'Nombre',
    'email del colaborador': 'Email',
    'identificador': 'Clave',
    'contrato': 'Contrato',
    'area/departamento': 'Depto',
    'posición': 'Puesto',
    'ultima marca (zona horaria contrato)': 'Últ. Marca',
    'última marca (zona horaria contrato)': 'Últ. Marca',
    'zona horaria contrato': 'Zona',
}

DIAS_SEMANA = {0: 'Lu', 1: 'Ma', 2: 'Mi', 3: 'Ju', 4: 'Vi', 5: 'Sa', 6: 'Do'}

def formatear_fecha_corta(valor):
    if not valor or str(valor).strip() in ['', 'nan', 'NaT']:
        return ''
    texto = str(valor).strip()
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']:
        try:
            dt = datetime.strptime(texto[:19], fmt[:len(texto[:19])])
            return dt.strftime('%d/%m/%y')
        except:
            continue
    if re.match(r'\d{4}-\d{2}-\d{2}', texto):
        try:
            dt = datetime.strptime(texto[:10], '%Y-%m-%d')
            return dt.strftime('%d/%m/%y')
        except:
            pass
    return texto[:10]

def es_columna_fecha(encabezado):
    return bool(re.match(r'\d{4}-\d{2}-\d{2}', str(encabezado).strip()))

def formatear_encabezado_dia(encabezado):
    texto = str(encabezado).strip()
    if re.match(r'\d{4}-\d{2}-\d{2}', texto):
        try:
            dt = datetime.strptime(texto[:10], '%Y-%m-%d')
            return f"{DIAS_SEMANA[dt.weekday()]} {dt.day:02d}" 
        except:
            pass
    return encabezado

def abreviar_encabezado(texto, max_chars=10):
    texto_str = str(texto)
    if es_columna_fecha(texto_str):
        return formatear_encabezado_dia(texto_str)
    clave = texto_str.lower().strip()
    if clave in ABREVIACIONES:
        return ABREVIACIONES[clave]
    return texto_str[:max_chars] + '...' if len(texto_str) > max_chars else texto_str

# Nueva firma — elimina columna_agrupacion, columna_agrupacion2, filtro_agrupacion
def generar_personalizado(df_raw, fila_inicio, orientacion, columnas,
    agrupaciones, nomenclatura, incluir_comentarios=False,
    nombre_empresa='REPORTE DE ASISTENCIA', tamano_letra=0,
    tipo_periodo='ninguno', logo_path=None, posicion_logo='izquierda',
    color_titulo='#4f46e5', color_encabezado='#4f46e5'):

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp.name
    tmp.close()

    if fila_inicio < 1 or fila_inicio > len(df_raw):
        raise ValueError(
            f"fila_inicio={fila_inicio} está fuera de rango. "
            f"El archivo tiene {len(df_raw)} filas."
        )
    # EXTRAER DATOS
    encabezados_raw = df_raw.iloc[fila_inicio - 1].tolist()
    datos_raw = df_raw.iloc[fila_inicio:].values.tolist()

    
    encabezados_raw = [str(v) if pd.notna(v) and str(v) != 'nan' else f'Col{i}'
                       for i, v in enumerate(encabezados_raw)]

    # DETECTAR FECHAS EN ENCABEZADOS Y FILTRAR POR PERIODO
    cols_fechas = []
    for i, enc in enumerate(encabezados_raw):
        if re.match(r'\d{2}/\d{2}/\d{4}', str(enc)) or re.match(r'\d{4}-\d{2}-\d{2}', str(enc)):
            try:
                if '/' in str(enc):
                    dt = datetime.strptime(str(enc)[:10], '%d/%m/%Y')
                else:
                    dt = datetime.strptime(str(enc)[:10], '%Y-%m-%d')
                cols_fechas.append((i, dt))
            except:
                pass

        if tipo_periodo != 'ninguno' and cols_fechas:
            fecha_min = min(cols_fechas, key=lambda x: x[1])[1]

            if tipo_periodo == 'semana':
                fecha_inicio = fecha_min
                fecha_fin = fecha_min + timedelta(days=6)
                periodo_label = f"SEMANA: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"

            elif tipo_periodo == 'quincena':
                fecha_inicio = fecha_min
                fecha_fin = fecha_min + timedelta(days=14)
                periodo_label = f"QUINCENA: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"

            elif tipo_periodo == 'quincena_1':
                fecha_inicio = fecha_min
                fecha_fin = fecha_min + timedelta(days=6)
                periodo_label = f"1ª SEMANA: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"

            elif tipo_periodo == 'quincena_2':
                fecha_inicio = fecha_min + timedelta(days=7)
                fecha_fin = fecha_min + timedelta(days=14)
                periodo_label = f"2ª SEMANA: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"

            
            cols_a_excluir = {
                i for i, dt in cols_fechas
                if dt < fecha_inicio or dt > fecha_fin
            }

            columnas = [c for c in columnas if c not in cols_a_excluir]
    else:
        if cols_fechas:
            fecha_min = min(cols_fechas, key=lambda x: x[1])[1]
            fecha_max = max(cols_fechas, key=lambda x: x[1])[1]
            periodo_label = f"{fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}"
        else:
            periodo_label = ""

    # FILTRAR COLUMNAS
    encabezados = [encabezados_raw[i] if i < len(encabezados_raw) else f'Col{i}' for i in columnas]
    datos = []
    for fila in datos_raw:
        fila_filtrada = [procesar_marcacion(fila[i]) if i < len(fila) else '' for i in columnas]
        datos.append(fila_filtrada)

    # CONFIGURACION PAGINA
    pagesize = landscape(letter) if orientacion == 'landscape' else portrait(letter)
    page_width, page_height = pagesize
    margen = 0.5 * inch
    available_width = page_width - (margen * 2)

    # TAMAÑO DE LETRA
    if tamano_letra and tamano_letra > 0:
        font_size = tamano_letra
    else:
        num_cols = len(columnas)
        if num_cols <= 5:
            font_size = 9
        elif num_cols <= 8:
            font_size = 8
        elif num_cols <= 12:
            font_size = 7
        elif num_cols <= 16:
            font_size = 6
        else:
            font_size = 5

    estilo_celda = ParagraphStyle(
        'celda',
        fontSize=font_size,
        leading=font_size + 2,
        wordWrap='CJK',
        alignment=TA_CENTER
    )

    estilo_sin_wrap = ParagraphStyle(
        'sin_wrap',
        fontSize=font_size,
        leading=font_size + 2,
        alignment=TA_CENTER,
        wordWrap=None
    )

    # ANCHOS DE COLUMNAS
    col_comentarios_ancho = 50 if incluir_comentarios else 0
    espacio_disponible = available_width - col_comentarios_ancho

    def calcular_ancho_col(encabezado, datos_col, fs):
        ancho_enc = stringWidth(str(encabezado), 'Helvetica-Bold', fs) + 6
        muestra = datos_col[:20]
        ancho_datos = max(
            [stringWidth(str(v)[:30], 'Helvetica', fs) + 8 for v in muestra if v]
            or [20]
        )
        return max(ancho_enc, ancho_datos, 30)

    anchos_naturales = []
    for j, enc in enumerate(encabezados):
        enc_abrev = abreviar_encabezado(enc)
        datos_col = [fila[j] if j < len(fila) else '' for fila in datos[:20]]
        ancho = calcular_ancho_col(enc_abrev, datos_col, font_size)
        if "Nombre" in str(enc).lower():
            ancho = ancho * 1.9
        anchos_naturales.append(ancho)
        

    total_natural = sum(anchos_naturales)
    if total_natural > espacio_disponible:
        factor = espacio_disponible / total_natural
        col_widths = [max(a * factor, 15) for a in anchos_naturales]
    else:
        col_widths = anchos_naturales

    if incluir_comentarios:
        col_widths.append(col_comentarios_ancho)

    # NOMENCLATURA
    if nomenclatura:
        items_nomenc = []
        for item in nomenclatura:
            if isinstance(item, dict):
                items_nomenc.append(f"({item['abrev']}) {item['nombre'].upper()}")
            else:
                items_nomenc.append(str(item))

        total = len(items_nomenc)
        if total <= 7:
            cols_simb = total
            filas_simb = [items_nomenc]
        elif total <= 14:
            cols_simb = 7
            mitad = (total + 1) // 2
            fila1 = items_nomenc[:mitad]
            fila2 = items_nomenc[mitad:]
            while len(fila2) < len(fila1):
                fila2.append('')
            filas_simb = [fila1, fila2]
        else:
            cols_simb = 7
            tercios = (total + 2) // 3
            fila1 = items_nomenc[:tercios]
            fila2 = items_nomenc[tercios:tercios*2]
            fila3 = items_nomenc[tercios*2:]
            while len(fila2) < len(fila1): fila2.append('')
            while len(fila3) < len(fila1): fila3.append('')
            filas_simb = [fila1, fila2, fila3]

        if total <= 7:
            font_simb = 6
        elif total <= 14:
            font_simb = 5
        else:
            font_simb = 4

        tabla_simbologia = Table(
            filas_simb,
            colWidths=[available_width / cols_simb] * cols_simb
        )
        tabla_simbologia.setStyle(TableStyle([
            ('FONTSIZE',      (0,0), (-1,-1), font_simb),
            ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME',      (0,0), (-1,-1), 'Helvetica'),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
    else:
        tabla_simbologia = None

    fecha_hoy = date.today()

    # ENCABEZADO
    def dibujar_header(canvas, doc):
        canvas.saveState()
        y_base = page_height - margen - 5

        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(HexColor(color_titulo))
        titulo = f"REPORTE DE ASISTENCIA: {nombre_empresa.upper()}" if nombre_empresa else "REPORTE DE ASISTENCIA"
        canvas.drawCentredString(page_width / 2, y_base - 15, titulo)
        canvas.setFillColor(black)
        canvas.drawCentredString(page_width / 2, y_base - 15, titulo)

        canvas.setFont("Helvetica", 9)

        if logo_path and os.path.exists(logo_path):
            from reportlab.lib.utils import ImageReader
            try:
                img = ImageReader(logo_path)
                img_w, img_h = img.getSize()
                alto_logo = 40
                ancho_logo = (img_w / img_h) * alto_logo
                if posicion_logo == 'izquierda':
                    x_logo = margen
                else:
                    x_logo = page_width - margen - ancho_logo
                y_logo = y_base - alto_logo
                canvas.drawImage(logo_path, x_logo, y_logo,
                                width=ancho_logo, height=alto_logo,
                                preserveAspectRatio=True, mask='auto')
            except:
                pass

        if periodo_label:
            canvas.drawCentredString(page_width / 2, y_base - 27, f"PERIODO: {periodo_label}")

        if tabla_simbologia:
            w, h = tabla_simbologia.wrap(available_width, 0)
            x = (page_width - w) / 2
            tabla_simbologia.drawOn(canvas, x, y_base - 42 - h)

        y_firma = margen + 20
        centro = page_width / 2
        largo = 150

        canvas.line(centro - 180 - largo/2, y_firma, centro - 180 + largo/2, y_firma)
        canvas.line(centro + 180 - largo/2, y_firma, centro + 180 + largo/2, y_firma)

        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(centro - 180, y_firma - 10, "JEFE DEPARTAMENTAL")
        canvas.drawCentredString(centro + 180, y_firma - 10, "GERENTE DE AREA")

        canvas.drawString(margen, y_firma - 22,
            "OBS: Por ser un documento Auditable por favor traer las firmas de Autorización. No usar Corrector y llenarlo en su totalidad")
        canvas.drawRightString(page_width - doc.rightMargin, y_firma - 25,
            f"Página {doc.page}   Fecha Impresión: {fecha_hoy.strftime('%d/%m/%Y')}")
        canvas.restoreState()

    # CREAR PDF
    doc = BaseDocTemplate(
        pdf_path,
        pagesize=pagesize,
        leftMargin=margen,
        rightMargin=margen,
        topMargin=margen,
        bottomMargin=margen
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 0.8 * inch,
        doc.width,
        doc.height - 1.8 * inch,
        id='normal'
    )
    template = PageTemplate(id='header', frames=[frame], onPage=dibujar_header)
    doc.addPageTemplates([template])

    # Reemplaza todo el bloque "AGRUPAR Y GENERAR" por esto:

    df_final = pd.DataFrame(datos, columns=encabezados)
    df_final = df_final.reset_index(drop=True)

    # Construir lista de columnas de agrupacion con sus filtros
    niveles = []
    for agrup in agrupaciones:
        col_idx = agrup.get('columna', 0)
        filtro = agrup.get('filtro', [])
        try:
            idx_en_encabezados = columnas.index(col_idx)
            nombre_col = encabezados[idx_en_encabezados]
            niveles.append({
                'col': nombre_col,
                'filtro': [str(f).strip() for f in filtro] if filtro else []
            })
        except ValueError as e:
            continue

    # Normalizar columnas de agrupacion
    for nivel in niveles:
        col = nivel['col']
        df_final[col] = df_final[col].apply(lambda x: str(x).strip())
        df_final[col] = df_final[col].replace({'nan': 'Sin grupo', '': 'Sin grupo'})

    # Aplicar filtros de cada nivel
    for nivel in niveles:
        if nivel['filtro']:
            df_final = df_final[df_final[nivel['col']].isin(nivel['filtro'])]

    df_final = df_final.reset_index(drop=True)

        # Funcion recursiva para agrupar y generar tablas
    def generar_tablas(df, niveles_restantes, profundidad=0, ruta_actual=None):
        if ruta_actual is None:     
            ruta_actual = [] 
        if df.empty:
            return

        if not niveles_restantes:

            if ruta_actual and elementos:
                elementos.append(PageBreak())
            if ruta_actual:
                etiqueta = ' | '.join(f"{col}: {val}" for col, val in ruta_actual)
                estilo_etiqueta = ParagraphStyle(
                    'etiqueta_grupo',
                    fontSize=font_size + 2,
                    fontName='Helvetica-Bold',
                    leading=font_size + 5,
                    spaceAfter=2
                )
                elementos.append(Paragraph(etiqueta, estilo_etiqueta))

            encabezados_tabla = [abreviar_encabezado(e) for e in encabezados]
            if incluir_comentarios:
                encabezados_tabla.append('Comentarios')

            filas_tabla = []
            for fila in df.values.tolist():
                fila_datos = []
                for k, v in enumerate(fila):
                    if v:
                        estilo = estilo_sin_wrap if k == 0 else estilo_celda
                        fila_datos.append(Paragraph(str(v), estilo))
                    else:
                        fila_datos.append('')
                if incluir_comentarios:
                    fila_datos.append('')
                filas_tabla.append(fila_datos)

            data_tabla = [encabezados_tabla] + filas_tabla
            tabla = Table(data_tabla, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
            color_fondo = HexColor(color_encabezado)
            color_texto_enc = color_texto_contraste(color_encabezado)
            tabla.setStyle(TableStyle([
                ('FONTSIZE',      (0,0), (-1,-1), font_size),
                ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME',      (0,0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND',    (0,0), (-1, 0), color_fondo),
                ('TEXTCOLOR',     (0,0), (-1, 0), color_texto_enc),
                ('LEADING',       (0,0), (-1,-1), font_size + 1),
                ('TOPPADDING',    (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING',   (0,0), (-1,-1), 1),
                ('RIGHTPADDING',  (0,0), (-1,-1), 1),
                ('GRID',          (0,0), (-1,-1), 0.7, colors.black)
            ]))
            elementos.append(tabla)
            return

        nivel_actual = niveles_restantes[0]
        resto = niveles_restantes[1:]

        # Respetar orden del filtro
        if nivel_actual['filtro']:
            orden_grupos = [g for g in nivel_actual['filtro'] if g in df[nivel_actual['col']].values]
        else:
            orden_grupos = df[nivel_actual['col']].unique().tolist()

        for idx, grupo_val in enumerate(orden_grupos):
            filas_grupo = df[df[nivel_actual['col']] == grupo_val]

            if filas_grupo.empty:
                continue

            # if profundidad == 0 and idx > 0:
            #     elementos.append(PageBreak())
            # elif profundidad > 0 and idx > 0:
            #     elementos.append(Spacer(1, 6))
                
            generar_tablas(
                                filas_grupo,
                                resto,
                                profundidad + 1,
                                ruta_actual + [(nivel_actual['col'], grupo_val)]
                            )

    elementos = []
    generar_tablas(df_final, niveles, profundidad=0)
    doc.build(elementos) 

    return pdf_path