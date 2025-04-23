import os
import pandas as pd
from PIL import Image, ImageOps
import time
import shutil

class ImageProcessor:
    """
    Handles image processing tasks, including resizing, cropping,
    and overlaying infographics.
    """
    
    def __init__(self, config_manager):
        """Initialize with a config manager."""
        self.config_manager = config_manager
    
    def process_and_center_image(self, photo_path, canvas_width, canvas_height):
        """
        Processes an image: removes Exif, resizes, centers, and crops excess.
        Returns a new canvas with the processed image.
        """
        try:
            with Image.open(photo_path) as img:
                img = ImageOps.exif_transpose(img)
                
                # Scale to fill canvas
                scale = max(canvas_width / img.width, canvas_height / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)))
                
                # Center crop
                left = (img.width - canvas_width) // 2
                top = (img.height - canvas_height) // 2
                img = img.crop((left, top, left + canvas_width, top + canvas_height))
                
                # Create canvas
                canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
                canvas.paste(img, (0, 0))
                
                return canvas
        except Exception as e:
            raise Exception(f"Ошибка обработки изображения {photo_path}: {e}")
    
    def overlay_infografika(self, canvas, infografika_path, position):
        """
        Overlays an infographic onto the canvas at the specified position.
        Returns the modified canvas.
        """
        try:
            with Image.open(infografika_path) as infografika:
                if infografika.mode != 'RGBA':
                    infografika = infografika.convert('RGBA')
                
                # Get canvas dimensions
                canvas_width, canvas_height = canvas.size
                
                # Get settings
                settings = self.config_manager.get_settings()
                margin = settings.get("margin", 30)
                
                # Calculate position
                x_offset, y_offset = self.config_manager.calculate_position(
                    position, 
                    canvas_width, 
                    canvas_height, 
                    infografika.width, 
                    infografika.height,
                    margin
                )
                
                # Paste infographic onto canvas
                canvas.paste(infografika, (x_offset, y_offset), infografika)
                return canvas
        except Exception as e:
            raise Exception(f"Ошибка наложения инфографики {infografika_path}: {e}")
    
    def get_next_output_dir(self, base_output_dir):
        """
        Creates a uniquely indexed output directory.
        If output dir exists, creates output_1, output_2, etc.
        """
        if not os.path.exists(base_output_dir):
            os.makedirs(base_output_dir)
            return base_output_dir
        
        counter = 1
        while True:
            indexed_dir = f"{base_output_dir}_{counter}"
            if not os.path.exists(indexed_dir):
                os.makedirs(indexed_dir)
                return indexed_dir
            counter += 1
    
    def generate_cards(self, excel_file, photos_dir, infografika_dir, output_dir, 
                       canvas_width, canvas_height, margin, progress_callback=None):
        """
        Processes all photos based on data from all sheets in Excel file.
        Each sheet is processed separately but with the same logic.
        """
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        
        # Создаем новую выходную директорию с индексом, если она уже существует
        original_output_dir = output_dir
        output_dir_index = 1
        while os.path.exists(output_dir):
            output_dir = f"{original_output_dir}_{output_dir_index}"
            output_dir_index += 1
        
        # Создаем выходную директорию
        os.makedirs(output_dir, exist_ok=True)
        print(f"Создана директория для результатов: {output_dir}")
        
        # Читаем все листы из Excel файла
        try:
            xl = pd.ExcelFile(excel_file)
            sheet_names = xl.sheet_names
            print(f"Найдено {len(sheet_names)} листов в файле: {', '.join(sheet_names)}")
        except Exception as e:
            raise Exception(f"Ошибка чтения Excel файла: {str(e)}")
        
        # Получаем список директорий артикулов
        all_articles = [d for d in os.listdir(photos_dir) if os.path.isdir(os.path.join(photos_dir, d))]
        if not all_articles:
            raise Exception(f"Не найдены директории артикулов в {photos_dir}")
        
        total_processed = 0
        
        # Для каждого артикула
        for article_idx, article in enumerate(all_articles):
            article_dir = os.path.join(photos_dir, article)
            
            # Получаем список файлов изображений в директории артикула
            image_files = [f for f in os.listdir(article_dir) 
                          if os.path.isfile(os.path.join(article_dir, f)) and 
                          f.lower().endswith(tuple(allowed_extensions))]
            
            # Сортируем файлы по имени для обеспечения последовательности
            image_files.sort()
            
            # Создаем директорию для вывода для этого артикула
            article_output_dir = os.path.join(output_dir, article)
            os.makedirs(article_output_dir, exist_ok=True)
            
            # Обрабатываем каждое изображение
            for img_idx, img_file in enumerate(image_files):
                photo_path = os.path.join(article_dir, img_file)
                output_path = os.path.join(article_output_dir, os.path.splitext(img_file)[0] + ".png")
                
                # Создаем canvas для изображения
                try:
                    canvas = self.process_and_center_image(photo_path, canvas_width, canvas_height)
                except Exception as e:
                    print(f"Ошибка обработки изображения {photo_path}: {e}")
                    continue
                
                # Для каждого листа Excel проверяем, нужно ли добавить инфографику
                added_infografika = False
                
                for sheet_name in sheet_names:
                    try:
                        # Читаем данные текущего листа
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str).fillna('')
                        data = df.values.tolist()
                        
                        # Создаем словарь артикул -> данные
                        articles_in_excel = {row[0]: row[1:] for row in data if row[0]}
                        
                        # Проверяем, есть ли этот артикул в данных листа
                        if article in articles_in_excel:
                            slides_data = articles_in_excel[article]
                            
                            # Проверяем, есть ли данные для этого изображения
                            if img_idx < len(slides_data) // 2:
                                infografika_name = slides_data[2 * img_idx]
                                position_str = slides_data[2 * img_idx + 1]
                                
                                if infografika_name and position_str:
                                    # Путь к файлу инфографики
                                    infografika_path = os.path.join(infografika_dir, infografika_name + ".png")
                                    position = int(position_str)
                                    
                                    # Если файл существует, добавляем инфографику на изображение
                                    if os.path.exists(infografika_path):
                                        canvas = self.overlay_infografika(canvas, infografika_path, position)
                                        added_infografika = True
                                        print(f"Добавлена инфографика {infografika_name} на позицию {position} из листа {sheet_name} для изображения {img_file} артикула {article}")
                    
                    except Exception as e:
                        print(f"Ошибка при обработке листа {sheet_name} для артикула {article}, изображения {img_file}: {e}")
                
                # Сохраняем результат
                try:
                    canvas.save(output_path)
                    total_processed += 1
                    
                    # Обновляем прогресс (общий прогресс по всем артикулам и изображениям)
                    if progress_callback:
                        total_items = sum(
                            len([f for f in os.listdir(os.path.join(photos_dir, a)) 
                                if os.path.isfile(os.path.join(photos_dir, a, f)) and 
                                f.lower().endswith(tuple(allowed_extensions))])
                            for a in all_articles
                        )
                        current_item = sum(
                            len([f for f in os.listdir(os.path.join(photos_dir, a)) 
                                if os.path.isfile(os.path.join(photos_dir, a, f)) and 
                                f.lower().endswith(tuple(allowed_extensions))])
                            for a in all_articles[:article_idx]
                        ) + img_idx + 1
                        
                        progress_callback(current_item, total_items)
                    
                except Exception as e:
                    print(f"Ошибка сохранения результата {output_path}: {e}")
        
        return total_processed, output_dir  # Возвращаем также путь к выходной директории
