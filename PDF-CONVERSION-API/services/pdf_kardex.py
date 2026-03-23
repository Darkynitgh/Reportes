from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import date
import tempfile
import pandas as pd
import re
from datetime import datetime, timedelta

def procesar_marcacion(texto):
    if pd.isna(texto) or texto == "":
        return ""
    texto = str(texto).strip()
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

def generar_kardex(df, nombre_archivo):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp.name
    tmp.close()

    # BUSCAR PERIODO
    fecha_inicio = None
    fecha_fin = None
    texto_periodo = ""

    for celda in df.iloc[:, 0]:
        if pd.notna(celda):
            texto = str(celda)
            fechas = re.findall(r"\d{4}-\d{2}-\d{2}", texto)
            if len(fechas) >= 2:
                texto_periodo = texto
                fecha_inicio = datetime.strptime(fechas[0], "%Y-%m-%d")
                fecha_fin = datetime.strptime(fechas[1], "%Y-%m-%d")
                break

    if not fecha_inicio:
        raise Exception("No se encontraron fechas en el Excel")

    # LIMPIAR FECHA ULTIMA MARCA
    df.iloc[:, 6] = df.iloc[:, 6].astype(str).str[:10]

    # GENERAR COLUMNAS DINAMICAS
    dias_semana = {0:"LU", 1:"MA", 2:"MI", 3:"JU", 4:"VI", 5:"SA", 6:"DO"}
    total_dias = (fecha_fin - fecha_inicio).days + 1
    columnas_base = [0, 1, 2, 3, 4, 5]
    columnas_dias = []

    for i in range(total_dias):
        fecha = fecha_inicio + timedelta(days=i)
        dia = dias_semana[fecha.weekday()]
        encabezado = f"{dia}{fecha.day:02d}"
        col = 8 + i
        columnas_dias.append(col)
        df.iloc[:, col] = df.iloc[:, col].apply(procesar_marcacion)
        df.rename(columns={df.columns[col]: encabezado}, inplace=True)

    columnas_finales = columnas_base + columnas_dias
    df_asistencia = df.iloc[2:, columnas_finales]
    df_asistencia = df_asistencia.sort_values(by=df_asistencia.columns[2])

    # SIMBOLOGIA
    marcas = [
        ["(D) DESCANSO", "(DL) DESCANSO LABORADO", "(F) FALTA POR NO MARCAR", "(FL) FERIADO LABORADO", "($) HORAS EXTRAS", "(I) INCAPACIDAD", "(MF) MARCA FALTANTE"],
        ["(C) PERMISO CON GOCE", "(P) PERMISO SIN GOCE", "(PD) PRIMA DOMINICAL", "(S) SUSPENSION", "(X) TURNO LABORADO", "(V) VACACIONES", ""]
    ]

    page_width, page_height = landscape(letter)
    margen = 0.5 * inch
    available_width = page_width - (margen * 2)

    # ANCHOS DE COLUMNAS
    anchos_fijos = {0: 35, 1: 140, 2: 90, 3: 140, 4: 53}
    num_cols = len(df_asistencia.columns)
    espacio_usado = sum(anchos_fijos.values())
    dias_cols = num_cols - len(anchos_fijos) - 1
    espacio_restante = available_width - espacio_usado - 40
    ancho_dia = espacio_restante / dias_cols if dias_cols > 0 else 20

    col_widths = []
    for i in range(num_cols):
        if i in anchos_fijos:
            col_widths.append(anchos_fijos[i])
        elif i == num_cols - 1:
            col_widths.append(40)
        else:
            col_widths.append(ancho_dia)

    # TABLA SIMBOLOGIA
    tabla_simbologia = Table(marcas, colWidths=[available_width / 7] * 7)
    tabla_simbologia.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))

    fecha_hoy = date.today()

    # ENCABEZADO
    def dibujar_header(canvas, doc):
        canvas.saveState()
        w, h = tabla_simbologia.wrap(available_width, 0)
        x = (page_width - w) / 2
        y = page_height - h - margen

        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(page_width / 2, y + h + 20, nombre_archivo.upper())
        canvas.drawCentredString(page_width / 2, y + h + 8,
            f"PERIODO: {fecha_inicio.strftime('%d/%m/%Y')} ===> {fecha_fin.strftime('%d/%m/%Y')}")

        tabla_simbologia.drawOn(canvas, x, y - 15)

        # FIRMAS
        y_firma = margen + 20
        centro = page_width / 2
        sep = 120
        largo = 200

        canvas.line(centro - sep - largo / 2, y_firma, centro - sep + largo / 2, y_firma)
        canvas.line(centro + sep - largo / 2, y_firma, centro + sep + largo / 2, y_firma)

        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(centro - sep, y_firma - 10, "JEFE DEPARTAMENTAL")
        canvas.drawCentredString(centro + sep, y_firma - 10, "GERENTE DE AREA")
        canvas.drawString(doc.leftMargin, y_firma - 25,
            "OBS: Documento auditable. No usar corrector y llenar completamente.")
        canvas.drawRightString(page_width - doc.rightMargin, y_firma - 25,
            f"Página {doc.page}   Fecha Impresión: {fecha_hoy.strftime('%d/%m/%Y')}")

        canvas.restoreState()

    # CREAR PDF
    doc = BaseDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=margen,
        rightMargin=margen,
        topMargin=margen,
        bottomMargin=margen
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 0.8 * inch,
        doc.width,
        doc.height - 1.4 * inch,
        id='normal'
    )

    template = PageTemplate(id='header', frames=[frame], onPage=dibujar_header)
    doc.addPageTemplates([template])

    # GENERAR POR DEPARTAMENTO
    elementos = []
    grupos = list(df_asistencia.groupby(df_asistencia.columns[2]))

    for i, (depto, grupo) in enumerate(grupos):
        data_grupo = [df_asistencia.columns.tolist()] + grupo.values.tolist()

        tabla = Table(data_grupo, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LEADING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black)
        ]))

        elementos.append(tabla)
        if i < len(grupos) - 1:
            elementos.append(PageBreak())

    doc.build(elementos)
    return pdf_path