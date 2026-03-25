from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import tempfile
import os
import json
from pypdf import PdfWriter, PdfReader 
from services.pdf_kardex import generar_kardex
from services.pdf_personalizado import generar_personalizado

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generar-pdf")
async def generar_pdf(
    archivo: UploadFile = File(...),
    formato: str = Form(...),
    fila_inicio: int = Form(None),
    orientacion: str = Form(None),
    columnas: str = Form(None),
    columna_agrupacion: int = Form(None),
    nomenclatura: str = Form(None),
    incluir_comentarios: str = Form(None),
    nombre_empresa: str = Form(None),
    tamano_letra: int = Form(None),
    tipo_periodo: str = Form(None),
    columna_agrupacion2: int = Form(None),
    filtro_agrupacion: str = Form(None),
    logo: UploadFile = File(None),
    posicion_logo: str = Form(None),
    color_titulo: str = Form('#4f46e5'),
    color_encabezado: str = Form('#4f46e5'),
):
    
    contenido = await archivo.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(contenido)
        tmp_path = tmp.name

    df = pd.read_excel(tmp_path, header=None)
    os.unlink(tmp_path)

    if formato == "kardex":
        df_normal = df.copy()
        df_normal.columns = df_normal.iloc[0]
        df_normal = df_normal.iloc[1:]
        pdf_path = generar_kardex(df_normal, archivo.filename)

    elif formato == "personalizado":
        cols = json.loads(columnas)
        nomenc = json.loads(nomenclatura) if nomenclatura else []
        comentarios = incluir_comentarios == 'true'
        fila_inicio_val = fila_inicio if fila_inicio else 23
        filtro_agrup = json.loads(filtro_agrupacion) if filtro_agrupacion else []
        pdf_path = generar_personalizado(
            df,
            fila_inicio_val,
            orientacion,
            cols,
            columna_agrupacion or 0,
            nomenc,
            comentarios,
            nombre_empresa or 'REPORTE DE ASISTENCIA',
            tamano_letra or 0,
            tipo_periodo or 'ninguno',
            columna_agrupacion2 if columna_agrupacion2 is not None else -1,
            filtro_agrup,
            color_titulo,
            color_encabezado
            
        )
        logo_path = None
    if logo:
        contenido_logo = await logo.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
            tmp_logo.write(contenido_logo)
            logo_path = tmp_logo.name

    pdf_path = generar_personalizado(
        df, fila_inicio_val, orientacion, cols,
        columna_agrupacion or 0, nomenc, comentarios,
        nombre_empresa or 'REPORTE DE ASISTENCIA',
        tamano_letra or 0, tipo_periodo or 'ninguno',
        columna_agrupacion2 if columna_agrupacion2 is not None else -1,
        filtro_agrup,
        logo_path,
        posicion_logo or 'izquierda',
        color_titulo='#4f46e5',
        color_encabezado='#4f46e5'
    )

    if logo_path and os.path.exists(logo_path):
        os.unlink(logo_path)
    else:
        return {"error": "Formato no válido"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{archivo.filename}_{formato}.pdf"
    )

@app.post("/combinar-pdfs")
async def combinar_pdfs(archivos: list[UploadFile] = File(...)):
    writer = PdfWriter()

    for archivo in archivos:
        contenido = await archivo.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contenido)
            tmp_path = tmp.name
        reader = PdfReader(tmp_path)
        for page in reader.pages:
            writer.add_page(page)
        os.unlink(tmp_path)

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_out.close()
    with open(tmp_out.name, "wb") as f:
        writer.write(f)

    return FileResponse(tmp_out.name, media_type="application/pdf", filename="reporte_completo.pdf")