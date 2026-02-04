import logging
import time
from vertexai.generative_models import Part
from src.config import Config
from src.core.google_client import google_manager
from src.core.vertex_wrapper import vertex_client
from src.utils.drive_tools import get_id_from_url

logger = logging.getLogger(__name__)

class ChatService:
    """
    Gestiona la sesión de chat con Vertex AI y la ejecución secuencial de prompts.
    """

    def __init__(self):
        self.drive_service = google_manager.get_drive_service()
        self.model = None
        self.chat_session = None

    def _fetch_doc_text(self, url):
        """Descarga el contenido de texto de un Google Doc dado su URL."""
        try:
            file_id = get_id_from_url(url)
            # Exportar a texto plano
            response = self.drive_service.files().export(
                fileId=file_id,
                mimeType="text/plain"
            ).execute()
            # La respuesta viene como bytes, decodificamos
            return response.decode('utf-8')
        except Exception as e:
            logger.error(f"Error leyendo prompt desde {url}: {e}")
            raise

    def initialize_session(self, cache_obj=None):
        """
        Inicia el modelo. Si se pasa un cache_obj, usa ese contexto.
        Si no, inicia un modelo estándar (útil para pruebas o fallbacks).
        """
        try:
            # 1. Obtener Instrucciones del Sistema desde el Doc
            system_instr = self._fetch_doc_text(Config.URL_SYSTEM_INSTRUCTIONS)
            logger.info("Instrucciones del sistema cargadas desde Drive.")

            # 2. Instanciar Modelo
            if cache_obj:
                # Si usamos caché, el system_instruction ya está "quemado" en el caché
                # al momento de crearlo, pero Vertex permite pasarlo de nuevo a veces.
                # Por seguridad, confiamos en el del caché o instanciamos desde él.
                self.model = vertex_client.get_model_from_cache(cache_obj)
                logger.info("Sesión iniciada con Context Caching.")
            else:
                # Fallback sin caché (para pruebas rápidas)
                from vertexai.generative_models import GenerativeModel
                self.model = GenerativeModel(
                    "gemini-2.5-flash",
                    system_instruction=system_instr
                )
                logger.info("Sesión iniciada SIN caché (Modelo estándar).")

            # 3. Iniciar Chat
            self.chat_session = self.model.start_chat()
            
        except Exception as e:
            logger.error(f"Error inicializando sesión de chat: {e}")
            raise

    def execute_grading_flow(self, patient_files_paths):
        """
        Ejecuta la secuencia completa de Grading VAWA.
        
        Args:
            patient_files_paths: Lista de rutas locales a los PDFs del paciente 
                                 (Main links + adicionales).
        Returns:
            final_response_text: El resultado de la auditoría final (Markdown).
            token_counts: Diccionario con uso de tokens {input, output}.
        """
        if not self.chat_session:
            raise ValueError("La sesión de chat no ha sido inicializada.")

        flow_steps = [
            ("Qualifying Relationship", Config.URL_PROMPT_QUALIFYING, True), # True = enviar archivos aquí
            ("Good Faith Character (GFC)", Config.URL_PROMPT_GFM, False),
            ("Joint Residence", Config.URL_PROMPT_JOINT_RESIDENCE, False),
            ("GMC / Permanent Bar", Config.URL_PROMPT_GMC_PB, False),
            ("Presence of Abuse", Config.URL_PROMPT_ABUSE, False),
            ("Auditoria Final", Config.URL_PROMPT_AUDITORIA, False)
        ]

        full_history_log = []

        try:
            for step_name, prompt_url, attach_files in flow_steps:
                logger.info(f"Ejecutando paso: {step_name}...")
                
                # 1. Obtener texto del prompt
                prompt_text = self._fetch_doc_text(prompt_url)
                
                # 2. Preparar mensaje
                message_parts = [prompt_text]
                
                # Si es el primer paso, adjuntamos los PDFs del paciente
                if attach_files and patient_files_paths:
                    logger.info(f"Adjuntando {len(patient_files_paths)} archivos de evidencia al prompt.")
                    for path in patient_files_paths:
                        with open(path, "rb") as f:
                            pdf_data = f.read()
                        message_parts.append(Part.from_data(data=pdf_data, mime_type="application/pdf"))

                # 3. Enviar a Vertex
                # Retries simples por si Vertex tiene un 'hiccup'
                response = self._send_message_with_retry(message_parts)
                
                logger.info(f"Paso {step_name} completado.")
                # Opcional: Podríamos guardar respuestas intermedias si quisieras debuggear
                # full_history_log.append(f"--- {step_name} ---\n{response.text}\n")
                
                # Pequeña pausa para no saturar si es muy rápido
                time.sleep(1)

            # La respuesta del último paso (Auditoria) es la que nos importa para el entregable
            final_text = response.text
            
            # Obtener métricas de uso (aprox)
            usage = response.usage_metadata
            token_counts = {
                "input": usage.prompt_token_count,
                "output": usage.candidates_token_count
            }

            return final_text, token_counts

        except Exception as e:
            logger.error(f"Error crítico en el flujo de grading: {e}")
            raise

    def _send_message_with_retry(self, content, retries=3):
        """Envía mensaje al chat con reintentos exponenciales."""
        for i in range(retries):
            try:
                return self.chat_session.send_message(content)
            except Exception as e:
                if i == retries - 1:
                    raise
                wait = 2 ** i
                logger.warning(f"Error en envío a Vertex: {e}. Reintentando en {wait}s...")
                time.sleep(wait)

# Instancia global
chat_service = ChatService()