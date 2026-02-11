<div align="center">
  <h1 align="center">GRADING VAWA (CCC)</h1>
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Google_Cloud-Vertex_AI-orange.svg" alt="GCP Vertex AI">
</div>


# Introducción

El proyecto presentado a continuación tiene como objetivo categorizar los casos haciendo uso de modelos LLM, 
Como apoyo para los colaboradores del área de CCC, esta categorización está centrada en analizar los criterios de elegibilidad del cliente y los abusos que ha sufrido.

# Diagrama de flujo

<img width="3105" height="1479" alt="GRADINGVAWAWORKFLOW drawio (1)" src="https://github.com/user-attachments/assets/ffa7d4d5-c476-4609-9204-2ab350d417fd" />

El diagrama de flujo representado arriba muestra el proceso para analizar casos una vez están en una spreadsheet especfica.

# Estructura de datos
Existen algunas condiciones que se deben de cumplir de manera obligatoria para poder generar un grading de un caso VAWA, a continuación se mencionan todas estas condiciones:


<div align="center">

| Ubicación | Descripción | OBLIGATORIO |
| :--- | :--- | :---: |
| **Columna A** | ID cliente | SI |
| **Columna B** | Nombre del cliente | SI |
| **Columna E** | Transcripción de entrevista | SI |
| **Columna F** | Categoría asignada por IA (VAWA, Visa U/T) | SI |
| **Columna J** | Resumen IA | SI |

</div>

# Ejemplo de archivo '.env'
```bash
### Configuración de Google Cloud Project (Vertex AI)
PROJECT_ID=ID_PROJECT
LOCATION=us-west1 

### Credenciales
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

### Configuración de Google Sheets
SPREADSHEET_ID=ID_SPREADSHEET
SHEET_NAME=NAME_SHEET

### Configuración de Google Drive
DRIVE_OUTPUT_FOLDER_ID=ID_FOLDER
```
# Quick Start

Sigue estos pasos para configurar y ejecutar el analizador en tu ordenador.

### 1. Clonar el Repositorio
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DE_TU_CARPETA>
```
### 2. Preparar el Entorno Virtual (Recomendado)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
.\venv\Scripts\activate

# Activar entorno (Mac/Linux)
source venv/bin/activate
```
### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Credenciales y Entorno
Este es el paso más importante para que el sistema tenga acceso a tus herramientas de Google Cloud.

Archivo de Identidad: Coloca tu archivo credentials.json (Service Account) directamente en la carpeta raíz del proyecto.

Variables de Control: Crea un archivo llamado .env basándote en la sección de ejemplo de este README y completa los IDs de tu Spreadsheet y Drive.

Permisos de Acceso: Abre tu archivo credentials.json, busca el campo "client_email" y copia esa dirección de correo.

> [!IMPORTANT]
> **Acceso Compartido:** Debes entrar a tu Google Sheet y a tu carpeta de Google Drive, hacer clic en "Compartir" y agregar el correo de la Service Account con el rol de Editor. Sin esto, la IA no podrá leer las transcripciones ni escribir los resultados.


