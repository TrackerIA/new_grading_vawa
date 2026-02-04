import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from src.config import Config

logger = logging.getLogger(__name__)

class GoogleClientManager:
    """
    Singleton para manejar las conexiones autenticadas a Google.
    Usa Service Account Credentials definidas en Config.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleClientManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._creds = None
        self._drive_service = None
        self._sheets_client = None
        self._initialized = True

    def _get_creds(self):
        """Carga las credenciales de la Service Account."""
        if not self._creds:
            try:
                logger.info(f"Cargando credenciales desde: {Config.CREDENTIALS_FILE}")
                
                # Verificamos que el archivo exista
                if not os.path.exists(Config.CREDENTIALS_FILE):
                    raise FileNotFoundError(f"No se encontró el archivo de credenciales: {Config.CREDENTIALS_FILE}")

                self._creds = Credentials.from_service_account_file(
                    Config.CREDENTIALS_FILE, 
                    scopes=Config.SCOPES
                )
            except Exception as e:
                logger.error(f"Error cargando credenciales: {e}")
                raise
        return self._creds

    def get_drive_service(self):
        """Retorna el servicio de Google Drive API v3."""
        if not self._drive_service:
            creds = self._get_creds()
            self._drive_service = build('drive', 'v3', credentials=creds)
        return self._drive_service

    def get_sheets_client(self):
        """Retorna el cliente de gspread para Sheets."""
        if not self._sheets_client:
            creds = self._get_creds()
            self._sheets_client = gspread.authorize(creds)
        return self._sheets_client
        
    def upload_file(self, file_path, file_metadata, mime_type='text/markdown'):
        """
        Helper para subir archivos. Si el método 'create' no está disponible
        directamente en el servicio, usamos este helper.
        """
        from googleapiclient.http import MediaFileUpload
        service = self.get_drive_service()
        
        media_body = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media_body,
            fields='id, webViewLink'
        ).execute()
        
        return file

# Instancia global
google_manager = GoogleClientManager()