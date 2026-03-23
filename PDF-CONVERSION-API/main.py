from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import tempfile
import os
import json
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
    tamano_letra: int = Form(None)
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
        pdf_path = generar_personalizado(
            df,
            fila_inicio_val,
            orientacion,
            cols,
            columna_agrupacion or 0,
            nomenc,
            comentarios,
            nombre_empresa or 'REPORTE DE ASISTENCIA',
            tamano_letra or 0
        )
    else:
        return {"error": "Formato no válido"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{archivo.filename}_{formato}.pdf"
    )