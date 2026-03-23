from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Table, TableStyle, PageBreak, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, portrait, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from datetime import date
import tempfile
import pandas as pd
import re
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle


def truncar(texto, max_chars=12):
    texto = str(texto)
    return texto[:max_chars] + '...' if len(texto) > max_chars else texto

def procesar_marcacion(texto):
    if pd.isna(texto) or texto == "":
        return ""
    texto = str(texto).strip()

    # Si es una fecha con hora (última marca, antigüedad) → fecha corta
    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', texto):
        return formatear_fecha_corta(texto)

    # Si es solo fecha
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
    # Intentar parsear fecha
    from datetime import datetime
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']:
        try:
            dt = datetime.strptime(texto[:19], fmt[:len(texto[:19])])
            return dt.strftime('%d/%m/%y')
        except:
            continue
    # Si tiene formato con / o - solo tomar primeros 10 chars
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
        from datetime import datetime
        try:
            dt = datetime.strptime(texto[:10], '%Y-%m-%d')
            return f"{DIAS_SEMANA[dt.weekday()]}{dt.day:02d}"
        except:
            pass
    return encabezado

def abreviar_encabezado(texto, max_chars=10):
    texto_str = str(texto)
    # Si es fecha de día → Lu01, Ma02...
    if es_columna_fecha(texto_str):
        return formatear_encabezado_dia(texto_str)
    clave = texto_str.lower().strip()
    if clave in ABREVIACIONES:
        return ABREVIACIONES[clave]
    return texto_str[:max_chars] + '...' if len(texto_str) > max_chars else texto_str

def generar_personalizado(df_raw, fila_inicio, orientacion, columnas, columna_agrupacion, nomenclatura, incluir_comentarios=False, nombre_empresa='REPORTE DE ASISTENCIA', tamano_letra=0):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp.name
    tmp.close()

    # DETECTAR PERIODO
    fecha_inicio = None
    fecha_fin = None
    for idx, row in df_raw.iterrows():
        celda = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        fechas = re.findall(r"\d{4}-\d{2}-\d{2}", celda)
        if len(fechas) >= 2:
            from datetime import datetime
            fecha_inicio = datetime.strptime(fechas[0], "%Y-%m-%d")
            fecha_fin    = datetime.strptime(fechas[1], "%Y-%m-%d")
            break

    # EXTRAER DATOS
    # fila_inicio es 1-based, entonces encabezados están en fila_inicio - 1 (0-based)
    # y datos desde fila_inicio (0-based)
    encabezados_raw = df_raw.iloc[fila_inicio - 1].tolist()
    datos_raw = df_raw.iloc[fila_inicio:].values.tolist()

    # Limpiar encabezados nan
    encabezados_raw = [str(v) if pd.notna(v) and str(v) != 'nan' else f'Col{i}' 
                    for i, v in enumerate(encabezados_raw)]
    # FILTRAR COLUMNAS
    encabezados = [encabezados_raw[i] if i < len(encabezados_raw) else f'Col{i}' for i in columnas]
    datos = []
    for fila in datos_raw:
        fila_filtrada = [procesar_marcacion(fila[i]) if i < len(fila) else '' for i in columnas]
        datos.append(fila_filtrada)

    # INDICE DE COLUMNA AGRUPACION dentro de columnas filtradas
    try:
        idx_agrupacion = columnas.index(columna_agrupacion)
    except ValueError:
        idx_agrupacion = 0

    # CONFIGURACION PAGINA
    pagesize = landscape(letter) if orientacion == 'landscape' else portrait(letter)
    page_width, page_height = pagesize
    margen = 0.5 * inch
    available_width = page_width - (margen * 2)

    if tamano_letra and tamano_letra > 0:
        font_size = tamano_letra
    else:
            # CALCULAR TAMAÑO DE LETRA AUTOMATICO
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

        # Estilo para wrap en celdas
    from reportlab.lib.enums import TA_CENTER

    estilo_celda = ParagraphStyle(
        'celda',
        fontSize=font_size,
        leading=font_size + 2,
        wordWrap='CJK',
        alignment=TA_CENTER
    )

   # ANCHOS DE COLUMNAS DINAMICOS BASADOS EN CONTENIDO
    col_comentarios_ancho = 50 if incluir_comentarios else 0
    espacio_disponible = available_width - col_comentarios_ancho

    # Calcular ancho mínimo por columna basado en contenido
    from reportlab.pdfbase.pdfmetrics import stringWidth

    def calcular_ancho_col(encabezado, datos_col, font_size):
        # Ancho del encabezado
        ancho_enc = stringWidth(str(encabezado), 'Helvetica-Bold', font_size) + 6
        # Ancho del contenido más largo (primeras 20 filas)
        muestra = datos_col[:20]
        ancho_datos = max(
            [stringWidth(str(v)[:15], 'Helvetica', font_size) + 6 for v in muestra if v]
            or [20]
        )
        return max(ancho_enc, ancho_datos, 20)  # mínimo 20 puntos

    # Calcular anchos naturales por columna
    anchos_naturales = []
    for j, enc in enumerate(encabezados):
        enc_abrev = abreviar_encabezado(enc)
        datos_col = [fila[j] if j < len(fila) else '' for fila in datos[:20]]
        ancho = calcular_ancho_col(enc_abrev, datos_col, font_size)
        anchos_naturales.append(ancho)

    # Escalar para que quepan en el espacio disponible
    total_natural = sum(anchos_naturales)
    if total_natural > espacio_disponible:
        factor = espacio_disponible / total_natural
        col_widths = [max(a * factor, 15) for a in anchos_naturales]
    else:
        col_widths = anchos_naturales

    if incluir_comentarios:
        col_widths.append(col_comentarios_ancho)
   # NOMENCLATURA DESDE FRONTEND
    if nomenclatura:
        items_nomenc = []
        for item in nomenclatura:
            if isinstance(item, dict):
                items_nomenc.append(f"({item['abrev']}) {item['nombre'].upper()}")
            else:
                items_nomenc.append(str(item))

        # Distribuir en filas según cantidad
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

        # Fuente automática según cantidad aqui se modifica el tamaño de Nomenclatura
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
            ('FONTSIZE', (0,0), (-1,-1), font_simb),
            ('ALIGN',    (0,0), (-1,-1), 'LEFT'),
            ('VALIGN',   (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('TOPPADDING',    (0,0), (-1,-1), 0),  
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),  
        ]))
    else:
        tabla_simbologia = None

    fecha_hoy = date.today()

    # ENCABEZADO
    def dibujar_header(canvas, doc):
        canvas.saveState()
        y_base = page_height - margen

        canvas.setFont("Helvetica-Bold", 10)
        titulo = f"REPORTE DE ASISTENCIA: {nombre_empresa.upper()}" if nombre_empresa else "REPORTE DE ASISTENCIA"
        canvas.drawCentredString(page_width / 2, y_base - 15, titulo)

        if fecha_inicio and fecha_fin:
            canvas.setFont("Helvetica", 9)
            canvas.drawCentredString(page_width / 2, y_base - 27,
                f"PERIODO: {fecha_inicio.strftime('%d/%m/%Y')} ==> {fecha_fin.strftime('%d/%m/%Y')}")

        if tabla_simbologia:
            w, h = tabla_simbologia.wrap(available_width, 0)
            x = (page_width - w) / 2
            tabla_simbologia.drawOn(canvas, x, y_base - 42 - h)

       # FIRMAS CENTRADAS
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
        canvas.drawString(margen, y_firma - 32,
            "")
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
    #Se modifica el Margen entre lineas de la Nomenclatura y la Tabla
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 0.8 * inch,
        doc.width,
        doc.height - 1.8 * inch,
        id='normal'
    )
    template = PageTemplate(id='header', frames=[frame], onPage=dibujar_header)
    doc.addPageTemplates([template])


    # AGRUPAR Y GENERAR
    df_final = pd.DataFrame(datos, columns=encabezados)
    df_final = df_final.reset_index(drop=True)

    # Limpiar columna de agrupacion
    col_grupo = encabezados[idx_agrupacion]
    df_final[col_grupo] = df_final[col_grupo].astype(str).fillna('Sin grupo')
    df_final[col_grupo] = df_final[col_grupo].replace('nan', 'Sin grupo')
    df_final[col_grupo] = df_final[col_grupo].replace('', 'Sin grupo')

    # Filtrar filas vacías sin boolean mask
    indices_validos = [i for i, val in enumerate(df_final[col_grupo]) 
                    if str(val).strip() not in ['', 'nan', 'Sin grupo']]
    df_final = df_final.iloc[indices_validos].reset_index(drop=True)

    
    grupos = list(df_final.groupby(col_grupo, sort=True))
    elementos = []
    styles = getSampleStyleSheet()

    for i, (grupo, filas_grupo) in enumerate(grupos):
        encabezados_tabla = [abreviar_encabezado(e) for e in encabezados]
        if incluir_comentarios:
            encabezados_tabla.append('Comentarios')

        filas_tabla = []  # ← AGREGA ESTA LÍNEA
        for fila in filas_grupo.values.tolist():
            fila_datos = []
            for j, v in enumerate(fila):
                if v:
                    # Primera columna (nombre) sin wrap
                    if j == 0:
                        estilo_sin_wrap = ParagraphStyle(
                            'sin_wrap',
                            fontSize=font_size,
                            leading=font_size + 2,
                            alignment=TA_CENTER,
                            wordWrap=None
                        )
                        fila_datos.append(Paragraph(str(v), estilo_sin_wrap))
                    else:
                        fila_datos.append(Paragraph(str(v), estilo_celda))
                else:
                    fila_datos.append('')
            if incluir_comentarios:
                fila_datos.append('')
            filas_tabla.append(fila_datos)
            

        data_grupo = [encabezados_tabla] + filas_tabla
        tabla = Table(data_grupo, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
        tabla.setStyle(TableStyle([
            ('FONTSIZE',      (0,0), (-1,-1),  font_size),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME',      (0,0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND',    (0,0), (-1, 0), colors.HexColor("#ffffff")),
            ('TEXTCOLOR',     (0,0), (-1, 0), colors.black),
            ('LEADING',       (0,0), (-1,-1),  font_size + 1),
            ('TOPPADDING',    (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING',   (0,0), (-1,-1), 1),
            ('RIGHTPADDING',  (0,0), (-1,-1), 1),
            ('GRID',          (0,0), (-1,-1), 0.7, colors.black)
        ]))

        elementos.append(tabla)
        if i < len(grupos) - 1:
            elementos.append(PageBreak())

    doc.build(elementos)
    return pdf_path