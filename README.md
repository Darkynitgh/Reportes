# PDF Conversion System

Aplicación web para generar PDFs a partir de archivos Excel.
Incluye frontend en Angular y API en FastAPI.

---

## Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/Darkynitgh/Reportes.git
cd Reportes
```

---

## Backend (API - Python)

```bash
cd PDF-CONVERSION-API
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API disponible en:
http://127.0.0.1:8000

---

## Frontend (Angular)

En otra terminal:

```bash
cd PDF-CONVERSION
npm install
ng serve
```

Aplicación disponible en:
http://localhost:4200

---

## Uso

1. Levantar backend
2. Levantar frontend
3. Subir archivo Excel
4. Generar PDF

---

## Requisitos

* Node.js
* Python 3

---

## Notas

* No subir carpeta `venv`
* No subir `node_modules`
* Usar `requirements.txt` para dependencias
