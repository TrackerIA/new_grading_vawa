import logging
import os
import tempfile
import shutil
from src.services.sheets_service import sheets_service
from src.services.drive_service import drive_service
from src.services.chat_service import chat_service
from src.services.cache_service import cache_service
from src.core.google_client import google_manager
from src.utils.drive_tools import get_id_from_url
from src.config import Config

logger = logging.getLogger(__name__)

class GradingProcess:
    def run(self):
        logger.info(">>> INICIANDO PROCESO DE GRADING VAWA <<<")
        
        # 1. Preparar Caché (Fundamentos)
        try:
            logger.info("Cargando Cache de Fundamentos...")
            cache_obj = cache_service.ensure_fundamentos_cache()
            
            # Inicializar el servicio de chat con este caché
            chat_service.initialize_session(cache_obj=cache_obj)
        except Exception as e:
            logger.critical(f"Fallo crítico inicializando caché: {e}")
            return # Detener todo si no hay conocimiento base

        # 2. Obtener trabajo pendiente
        pending_rows = sheets_service.get_pending_rows()
        logger.info(f"Se encontraron {len(pending_rows)} casos pendientes de procesar.")

        for row in pending_rows:
            self.process_single_case(row)

        logger.info(">>> PROCESO FINALIZADO <<<")

    def process_single_case(self, row_data):
        row_idx = row_data['row_idx']
        client_name = row_data['client_name']
        logger.info(f"--- Procesando Fila {row_idx}: {client_name} ---")

        # Crear carpeta temporal para este caso
        temp_dir = tempfile.mkdtemp()
        patient_pdfs = []

        try:
            # A. Marcar inicio en Sheets
            sheets_service.mark_processing_start(row_idx)

            # B. Descargar y Normalizar Documentos del Paciente
            links = row_data['links']
            # Mapeo de nombre legible -> URL
            docs_to_download = [
                ('caratula', links['caratula']),
                ('transcript', links['transcript']), # MAIN
                ('evidencias', links['evidencias']),
                ('dair', links['dair']),
                ('fair', links['fair']),
                ('rapsheet', links['rapsheet']),
                ('summary', links['summary'])        # MAIN
            ]

            logger.info("Descargando documentos del cliente...")
            for doc_type, url in docs_to_download:
                if url and len(url) > 5: # Validación simple de URL
                    try:
                        file_id = get_id_from_url(url)
                        output_path = os.path.join(temp_dir, f"{doc_type}.pdf")
                        
                        # DriveService convierte todo a PDF automágicamente
                        drive_service.download_as_pdf(file_id, output_path)
                        patient_pdfs.append(output_path)
                    except Exception as e:
                        logger.warning(f"No se pudo descargar {doc_type} ({url}): {e}")
                        # No detenemos el proceso, pero el chat tendrá menos contexto

            if not patient_pdfs:
                raise ValueError("No se pudieron descargar documentos válidos para el cliente.")

            # C. Ejecutar Chat de Grading
            logger.info("Iniciando auditoría con IA...")
            final_markdown, tokens = chat_service.execute_grading_flow(patient_pdfs)

            # D. Subir Resultado a Drive (usando OAuth para evitar problemas de cuota)
            output_filename = f"GRADING_{client_name.replace(' ', '_')}_{row_data['client_id']}.md"
            output_path = os.path.join(temp_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)
            
            # Subir a la carpeta de resultados usando OAuth
            file_metadata = {
                'name': output_filename,
                'parents': [Config.DRIVE_OUTPUT_FOLDER_ID]
            }
            uploaded_file = google_manager.upload_file(
                output_path, 
                file_metadata,
                mime_type='text/markdown'
            )
            
            grading_link = uploaded_file.get('webViewLink')

            # E. Guardar Resultados Finales
            result_data = {
                'grading_url': grading_link,
                'tokens_in': tokens['input'],
                'tokens_out': tokens['output'],
                # start_time ya se marcó al inicio, sheets_service calculará la diff con now()
            }
            sheets_service.write_grading_results(row_idx, result_data)

        except Exception as e:
            logger.error(f"Error procesando caso {client_name}: {e}")
            sheets_service.update_status(row_idx, f"ERROR: {str(e)[:50]}") # Mensaje corto en status
        finally:
            # Limpieza
            shutil.rmtree(temp_dir)

# Instancia global
grading_workflow = GradingProcess()