import os
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal

class ProcessImagesThread(QThread):
    """
    Thread for processing images in the background.
    """
    progress_updated = pyqtSignal(int, int)  # (current, total)
    processing_complete = pyqtSignal(int, str)  # number of processed images, output directory
    processing_error = pyqtSignal(str)  # error message
    
    def __init__(self, config_manager, image_processor):
        super().__init__()
        self.config_manager = config_manager
        self.image_processor = image_processor
        
    def run(self):
        try:
            # Get settings
            settings = self.config_manager.get_settings()
            photos_dir = settings.get("photos_dir", "photos")
            infografika_dir = settings.get("infografika_dir", "infografika")
            excel_file = settings.get("excel_file", "data.xlsx")
            output_dir = settings.get("output_dir", "output")
            canvas_width = settings.get("canvas_width", 900)
            canvas_height = settings.get("canvas_height", 1200)
            margin = settings.get("margin", 30)
            
            # Verify required paths
            if not os.path.exists(photos_dir):
                self.processing_error.emit(f"Директория фото не найдена: {photos_dir}")
                return
            
            if not os.path.exists(infografika_dir):
                self.processing_error.emit(f"Директория инфографики не найдена: {infografika_dir}")
                return
            
            if not os.path.exists(excel_file):
                self.processing_error.emit(f"Excel файл не найден: {excel_file}")
                return
            
            # Process images from all Excel sheets
            try:
                # Проверяем Excel файл на наличие листов
                xl = pd.ExcelFile(excel_file)
                sheet_names = xl.sheet_names
                
                if not sheet_names:
                    self.processing_error.emit("Excel файл не содержит листов")
                    return
                
                # Обрабатываем изображения и получаем результаты
                processed_count, final_output_dir = self.image_processor.generate_cards(
                    excel_file, photos_dir, infografika_dir, output_dir,
                    canvas_width, canvas_height, margin,
                    progress_callback=self.progress_updated.emit
                )
                
                self.processing_complete.emit(processed_count, final_output_dir)
                
            except Exception as e:
                self.processing_error.emit(f"Ошибка обработки изображений: {str(e)}")
            
        except Exception as e:
            self.processing_error.emit(f"Ошибка в потоке обработки: {str(e)}")