import logging
import datetime
from src.core.google_client import google_manager
from src.config import Config

logger = logging.getLogger(__name__)

class SheetsService:
    """
    Servicio para interactuar con la Google Sheet 'VAWA NEW GRADING'.
    Maneja lectura de pendientes, actualizaciones de estado y escritura de métricas.
    """
    
    # Mapeo de Columnas (1-based index para gspread)
    COL_STATUS = 3          # Columna C
    COL_CARATULA = 4        # Columna D
    COL_TRANSCRIPT = 5      # Columna E (MAIN)
    COL_EVIDENCIAS = 6      # Columna F
    COL_DAIR = 7            # Columna G
    COL_FAIR = 8            # Columna H
    COL_RAPSHEET = 9        # Columna I
    COL_SUMMARY = 10        # Columna J (MAIN)
    
    COL_GRADING_LINK = 11   # Columna K (Output final)
    
    COL_TOKENS_IN = 13      # Columna M
    COL_TOKENS_OUT = 14     # Columna N
    COL_APP_VERSION = 15    # Columna O
    COL_START_TIME = 16     # Columna P
    COL_END_TIME = 17       # Columna Q
    COL_DURATION = 18       # Columna R

    def __init__(self):
        self.client = google_manager.get_sheets_client()
        self.spreadsheet_id = Config.SPREADSHEET_ID
        self.sheet_name = Config.SHEET_NAME
        self._sheet = None

    @property
    def sheet(self):
        """Lazy load de la hoja para no conectar hasta que sea necesario."""
        if not self._sheet:
            try:
                # Abrir spreadsheet por ID y seleccionar la hoja por nombre
                sh = self.client.open_by_key(self.spreadsheet_id)
                self._sheet = sh.worksheet(self.sheet_name)
            except Exception as e:
                logger.error(f"Error conectando a Sheet {self.sheet_name}: {e}")
                raise
        return self._sheet

    def get_pending_rows(self):
        """
        Busca todas las filas con status 'PENDING PROCESSING'.
        Retorna una lista de diccionarios con la info necesaria y el número de fila.
        """
        rows_data = []
        try:
            # Obtener todos los valores (es más eficiente que iterar celdas)
            all_values = self.sheet.get_all_values()
            
            # Iterar saltando encabezados (asumimos fila 1 headers)
            for i, row in enumerate(all_values):
                row_idx = i + 1  # 1-based index
                if row_idx == 1: continue 

                # Asegurar que la fila tenga suficientes columnas para leer el status
                if len(row) >= self.COL_STATUS:
                    status = row[self.COL_STATUS - 1].strip() # -1 porque lista es 0-based
                    
                    if status == 'PENDING PROCESSING':
                        # Validar Links Principales (E y J)
                        # Nota: row index access es 0-based, por eso restamos 1 a las constantes
                        link_transcript = row[self.COL_TRANSCRIPT - 1] if len(row) >= self.COL_TRANSCRIPT else ""
                        link_summary = row[self.COL_SUMMARY - 1] if len(row) >= self.COL_SUMMARY else ""

                        if not link_transcript or not link_summary:
                            logger.warning(f"Fila {row_idx}: Falta link principal (E o J). Marcando error.")
                            self.update_status(row_idx, "ERROR: MAIN LINK MISSING")
                            continue

                        # Si pasa la validación, agregamos a la lista de trabajo
                        row_data = {
                            'row_idx': row_idx,
                            'client_id': row[0],
                            'client_name': row[1],
                            'links': {
                                'caratula': row[self.COL_CARATULA - 1] if len(row) >= self.COL_CARATULA else "",
                                'transcript': link_transcript,
                                'evidencias': row[self.COL_EVIDENCIAS - 1] if len(row) >= self.COL_EVIDENCIAS else "",
                                'dair': row[self.COL_DAIR - 1] if len(row) >= self.COL_DAIR else "",
                                'fair': row[self.COL_FAIR - 1] if len(row) >= self.COL_FAIR else "",
                                'rapsheet': row[self.COL_RAPSHEET - 1] if len(row) >= self.COL_RAPSHEET else "",
                                'summary': link_summary
                            }
                        }
                        rows_data.append(row_data)
            
            return rows_data

        except Exception as e:
            logger.error(f"Error leyendo filas pendientes: {e}")
            raise

    def update_status(self, row_idx, status):
        """Actualiza la columna C (Status)."""
        try:
            self.sheet.update_cell(row_idx, self.COL_STATUS, status)
            logger.info(f"Fila {row_idx} status actualizado a: {status}")
        except Exception as e:
            logger.error(f"Error actualizando status fila {row_idx}: {e}")

    def mark_processing_start(self, row_idx):
        """Marca inicio: Status PROCESSING y Fecha de Inicio."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates = [
            {'range': f'C{row_idx}', 'values': [['PROCESSING']]},
            {'range': f'P{row_idx}', 'values': [[now]]} # Columna Start Time
        ]
        try:
            self.sheet.batch_update(updates)
        except Exception as e:
            logger.error(f"Error marcando inicio fila {row_idx}: {e}")

    def write_grading_results(self, row_idx, result_data):
        """
        Escribe los resultados finales en las columnas K, M, N, O, Q, R.
        result_data debe ser un dict con:
        - grading_url
        - tokens_in
        - tokens_out
        - start_time (datetime obj)
        """
        try:
            end_time = datetime.datetime.now()
            start_time = result_data.get('start_time', end_time)
            duration_minutes = round((end_time - start_time).total_seconds() / 60, 2)
            
            # Preparar valores
            values = [
                [
                    result_data.get('grading_url', ''), # K - Grading Link
                    '', # L - (Empty/Future)
                    result_data.get('tokens_in', 0),    # M
                    result_data.get('tokens_out', 0),   # N
                    Config.APP_VERSION,                 # O
                    start_time.strftime("%Y-%m-%d %H:%M:%S"), # P (Re-confirmamos por si acaso)
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),   # Q
                    duration_minutes                    # R
                ]
            ]
            
            # Rango desde K hasta R
            range_name = f'K{row_idx}:R{row_idx}'
            self.sheet.update(range_name=range_name, values=values)
            
            # Actualizar status a COMPLETED
            self.update_status(row_idx, 'COMPLETED')
            logger.info(f"Fila {row_idx} completada exitosamente.")

        except Exception as e:
            logger.error(f"Error escribiendo resultados fila {row_idx}: {e}")
            self.update_status(row_idx, "ERROR SAVING RESULTS")

# Instancia global
sheets_service = SheetsService()