from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile

def generar_simple(df, nombre_archivo):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp.name
    tmp.close()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=portrait(letter),
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    headers = df.columns.tolist()
    filas = df.values.tolist()
    data = [headers] + [[str(c) for c in fila] for fila in filas]

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('FONTSIZE',     (0,0), (-1,-1), 7),
        ('FONTNAME',     (0,0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND',   (0,0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR',    (0,0), (-1, 0), colors.white),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f3ff')]),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    doc.build([tabla])
    return pdf_path