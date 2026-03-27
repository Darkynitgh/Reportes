from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import tempfile
import os
import json
from pypdf import PdfWriter, PdfReader 
from services.pdf_kardex import generar_kardex
from services.pdf_personalizado import generar_personalizado
from database import engine
from sqlalchemy import text
from fastapi.security import OAuth2PasswordRequestForm
from auth import hashear_password, verificar_password, crear_token, get_usuario_actual
from database import get_db
from sqlalchemy.orm import Session



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    nomenclatura: str = Form(None),
    agrupaciones: str = Form(None),
    incluir_comentarios: str = Form(None),
    nombre_empresa: str = Form(None),
    tamano_letra: int = Form(None),
    tipo_periodo: str = Form(None),
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

    # Procesar logo si viene
    logo_path = None
    if logo:
        contenido_logo = await logo.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
            tmp_logo.write(contenido_logo)
            logo_path = tmp_logo.name

    if formato == "kardex":
        df_normal = df.copy()
        df_normal.columns = df_normal.iloc[0]
        df_normal = df_normal.iloc[1:]
        pdf_path = generar_kardex(df_normal, archivo.filename)

    elif formato == "personalizado":
        cols = json.loads(columnas)
        nomenc = json.loads(nomenclatura) if nomenclatura else []
        comentarios = incluir_comentarios == 'true'
        fila_inicio_val = fila_inicio if fila_inicio else 1
        agrupaciones_list = json.loads(agrupaciones) if agrupaciones else []

        
        pdf_path = generar_personalizado(
            df,
            fila_inicio_val,
            orientacion,
            cols,
            agrupaciones_list,      
            nomenc,
            comentarios,
            nombre_empresa or 'REPORTE DE ASISTENCIA',
            tamano_letra or 0,
            tipo_periodo or 'ninguno',
            logo_path,
            posicion_logo or 'izquierda',
            color_titulo or '#4f46e5',
            color_encabezado or '#4f46e5'
        )
    else:
        return {"error": "Formato no válido"}

    # Limpiar logo temporal
    if logo_path and os.path.exists(logo_path):
        os.unlink(logo_path)

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

@app.get("/test-db")
def test_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        return {"db": "conectada "}
    
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    resultado = db.execute(
        text("SELECT * FROM usuarios WHERE username = :username"),
        {"username": form_data.username}
    ).fetchone()
    
    if not resultado or not verificar_password(form_data.password, resultado.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    token = crear_token({"sub": resultado.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def me(usuario: str = Depends(get_usuario_actual)):
    return {"usuario": usuario}