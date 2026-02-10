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

### Configuración de Google Cloud Project (Vertex AI)
PROJECT_ID=ID_PROJECT<br/>
LOCATION=us-west1 <br/>

### Credenciales
GOOGLE_APPLICATION_CREDENTIALS=credentials.json <br/>

### Configuración de Google Sheets
SPREADSHEET_ID=ID_SPREADSHEET <br/>
SHEET_NAME=NAME_SHEET <br/>

### Configuración de Google Drive
DRIVE_OUTPUT_FOLDER_ID=ID_FOLDER <br/>

