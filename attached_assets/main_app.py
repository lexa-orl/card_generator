import sys
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, 
                            QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, 
                            QProgressBar, QComboBox, QGroupBox, QFormLayout, QDialogButtonBox,
                            QRadioButton, QSlider)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QImage
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QThread, QTimer

from attached_assets.config_manager import ConfigManager
from attached_assets.image_processor import ImageProcessor
from attached_assets.anchor_position_editor import AnchorPositionEditor
from PIL import Image

# Класс SimplePositionSelector удален, вместо него используется AnchorPositionEditor

class PositionEditorTab(QWidget):
    """
    Tab for editing position configurations.
    """
    position_updated = pyqtSignal()  # Signal to notify when positions are updated
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.initUI()
        
    def initUI(self):
        # Вертикальный лейаут для всего редактора
        layout = QVBoxLayout()
        
        # Вкладки для режимов редактирования и визуализации
        position_tabs = QTabWidget()
        
        # 1. Вкладка "Интуитивный редактор"
        self.anchor_editor = AnchorPositionEditor(self.config_manager)
        self.anchor_editor.position_updated.connect(self.on_position_from_anchor_editor)
        position_tabs.addTab(self.anchor_editor, "Интуитивный редактор")
        
        # 2. Вкладка "Визуализация"
        visualization_widget = QWidget()
        visual_layout = QVBoxLayout()
        
        # Создаем визуализатор позиций
        self.canvas = PositionVisualizer(self.config_manager)
        self.canvas.setMinimumSize(400, 600)  # Увеличиваем размер для лучшей видимости
        visual_layout.addWidget(self.canvas)
        
        # Добавляем кнопку обновления
        self.refresh_visual_button = QPushButton("Обновить визуализацию")
        self.refresh_visual_button.clicked.connect(self.canvas.update)
        visual_layout.addWidget(self.refresh_visual_button)
        
        visualization_widget.setLayout(visual_layout)
        position_tabs.addTab(visualization_widget, "Визуализация")
        
        # 3. Вкладка "Расширенный режим"
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout()
        
        # Поля ввода для позиции
        edit_group = QGroupBox("Редактировать/Добавить позицию")
        edit_layout = QFormLayout()
        
        self.pos_id_input = QLineEdit()
        self.x_formula_input = QLineEdit()
        self.y_formula_input = QLineEdit()
        
        edit_layout.addRow("ID позиции:", self.pos_id_input)
        edit_layout.addRow("Формула X:", self.x_formula_input)
        edit_layout.addRow("Формула Y:", self.y_formula_input)
        
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_position)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_position)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        
        edit_layout.addRow(button_layout)
        edit_group.setLayout(edit_layout)
        advanced_layout.addWidget(edit_group)
        
        # Справочный текст
        help_label = QLabel("""
Доступные переменные для формул:
- canvas_width: Ширина холста
- canvas_height: Высота холста
- infografika_width: Ширина инфографики
- infografika_height: Высота инфографики
- MARGIN: Значение отступа из настроек

Примеры:
- Верхний левый угол: MARGIN, MARGIN
- По центру: (canvas_width - infografika_width) // 2, (canvas_height - infografika_height) // 2
- Нижний правый угол: canvas_width - infografika_width - MARGIN, canvas_height - infografika_height - MARGIN
        """)
        advanced_layout.addWidget(help_label)
        
        advanced_widget.setLayout(advanced_layout)
        position_tabs.addTab(advanced_widget, "Расширенный режим")
        
        # Добавляем вкладки в основной лейаут
        layout.addWidget(position_tabs)
        
        # Таблица сохраненных позиций
        table_group = QGroupBox("Сохраненные позиции")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID позиции", "Формула X", "Формула Y"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # Выделять всю строку
        table_layout.addWidget(self.table)
        
        # Обновляем таблицу
        self.refresh_table()
        
        # Подключаем выбор элементов таблицы к редактору
        self.table.itemSelectionChanged.connect(self.on_position_selected)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        self.setLayout(layout)
    
    def on_position_from_anchor_editor(self, pos_id, x_formula, y_formula, anchor):
        """Обработать позицию из интуитивного редактора с якорными точками."""
        # Проверяем случай удаления позиции (пустые формулы означают удаление)
        if x_formula == "" and y_formula == "":
            # Это сигнал об удалении позиции
            # Убедимся, что позиция была удалена
            positions = self.config_manager.get_positions()
            if pos_id not in positions:
                # Позиция была успешно удалена, просто обновляем UI
                self.refresh_table()
                self.canvas.update()
                self.position_updated.emit()
                return
            else:
                # Что-то пошло не так, повторно пытаемся удалить
                self.config_manager.delete_position(pos_id)
                QMessageBox.information(self, "Успех", f"Позиция {pos_id} удалена.")
        else:
            # Обычное обновление или добавление позиции с якорем
            positions = self.config_manager.get_positions()
            if pos_id in positions:
                self.config_manager.update_position(pos_id, x_formula, y_formula, anchor)
                QMessageBox.information(self, "Успех", f"Позиция {pos_id} обновлена.")
            else:
                self.config_manager.add_position(pos_id, x_formula, y_formula, anchor)
                QMessageBox.information(self, "Успех", f"Добавлена новая позиция {pos_id}.")
        
        # Refresh UI
        self.refresh_table()
        self.canvas.update()
        self.position_updated.emit()
        
        # Обновить список позиций в редакторе
        self.anchor_editor.refresh_positions_list()
    
    def refresh_table(self):
        """Refresh the positions table with the latest data."""
        positions = self.config_manager.get_positions()
        self.table.setRowCount(len(positions))
        
        for i, (pos_id, pos_config) in enumerate(positions.items()):
            self.table.setItem(i, 0, QTableWidgetItem(pos_id))
            self.table.setItem(i, 1, QTableWidgetItem(pos_config["x"]))
            self.table.setItem(i, 2, QTableWidgetItem(pos_config["y"]))
        
        self.table.resizeColumnsToContents()
    
    def on_position_selected(self):
        """Load the selected position into the editor."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        pos_id = self.table.item(row, 0).text()
        x_formula = self.table.item(row, 1).text()
        y_formula = self.table.item(row, 2).text()
        
        self.pos_id_input.setText(pos_id)
        self.x_formula_input.setText(x_formula)
        self.y_formula_input.setText(y_formula)
    
    def save_position(self):
        """Save or update a position."""
        pos_id = self.pos_id_input.text().strip()
        x_formula = self.x_formula_input.text().strip()
        y_formula = self.y_formula_input.text().strip()
        
        if not pos_id or not x_formula or not y_formula:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return
        
        # Validate formulas
        try:
            context = {
                "canvas_width": 900,
                "canvas_height": 1200,
                "infografika_width": 300,
                "infografika_height": 300,
                "MARGIN": 30
            }
            eval(x_formula, {"__builtins__": {}}, context)
            eval(y_formula, {"__builtins__": {}}, context)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректная формула: {str(e)}")
            return
        
        # Save position
        positions = self.config_manager.get_positions()
        if pos_id in positions:
            self.config_manager.update_position(pos_id, x_formula, y_formula)
            QMessageBox.information(self, "Успех", f"Позиция {pos_id} обновлена.")
        else:
            self.config_manager.add_position(pos_id, x_formula, y_formula)
            QMessageBox.information(self, "Успех", f"Добавлена новая позиция {pos_id}.")
        
        # Refresh UI
        self.refresh_table()
        self.canvas.update()
        self.position_updated.emit()
        
        # Clear inputs
        self.pos_id_input.clear()
        self.x_formula_input.clear()
        self.y_formula_input.clear()
    
    def delete_position(self):
        """Delete a position."""
        pos_id = self.pos_id_input.text().strip()
        if not pos_id:
            QMessageBox.warning(self, "Ошибка", "Выберите позицию для удаления.")
            return
        
        positions = self.config_manager.get_positions()
        if pos_id not in positions:
            QMessageBox.warning(self, "Ошибка", f"Позиция {pos_id} не найдена.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Вы уверены, что хотите удалить позицию {pos_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config_manager.delete_position(pos_id)
            QMessageBox.information(self, "Успех", f"Позиция {pos_id} удалена.")
            
            # Refresh UI
            self.refresh_table()
            self.canvas.update()
            self.position_updated.emit()
            
            # Обновить список позиций в редакторе
            self.anchor_editor.refresh_positions_list()
            
            # Clear inputs
            self.pos_id_input.clear()
            self.x_formula_input.clear()
            self.y_formula_input.clear()

class PositionVisualizer(QWidget):
    """
    Widget to visualize position configurations on a canvas.
    """
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setMinimumSize(300, 400)
        
    def paintEvent(self, event):
        """Paint the canvas with positions."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get settings
        settings = self.config_manager.get_settings()
        canvas_width = settings.get("canvas_width", 900)
        canvas_height = settings.get("canvas_height", 1200)
        margin = settings.get("margin", 30)
        
        # Scale down for display
        scale_factor = min(self.width() / canvas_width, self.height() / canvas_height) * 0.9
        display_width = int(canvas_width * scale_factor)
        display_height = int(canvas_height * scale_factor)
        
        # Center the display
        offset_x = (self.width() - display_width) // 2
        offset_y = (self.height() - display_height) // 2
        
        # Draw canvas background
        painter.fillRect(offset_x, offset_y, display_width, display_height, QColor(211, 211, 211))
        
        # Draw margin guidelines
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        margin_scaled = int(margin * scale_factor)
        painter.drawRect(offset_x + margin_scaled, offset_y + margin_scaled, 
                         display_width - 2 * margin_scaled, display_height - 2 * margin_scaled)
        
        # Draw center lines
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
        center_x = offset_x + display_width // 2
        center_y = offset_y + display_height // 2
        painter.drawLine(center_x, offset_y, center_x, offset_y + display_height)
        painter.drawLine(offset_x, center_y, offset_x + display_width, center_y)
        
        # Sample infographic size
        sample_width = 300
        sample_height = 300
        sample_width_scaled = int(sample_width * scale_factor)
        sample_height_scaled = int(sample_height * scale_factor)
        
        # Draw positions
        positions = self.config_manager.get_positions()
        for pos_id, pos_config in positions.items():
            try:
                # Calculate actual position
                x, y = self.config_manager.calculate_position(
                    pos_id, canvas_width, canvas_height, sample_width, sample_height, margin
                )
                
                # Scale position for display
                x_scaled = int(x * scale_factor) + offset_x
                y_scaled = int(y * scale_factor) + offset_y
                
                # Draw position marker
                marker_size = 5
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(Qt.red))
                painter.drawRect(x_scaled - marker_size, y_scaled - marker_size, 
                                 marker_size * 2, marker_size * 2)
                
                # Draw sample infographic outline
                painter.setPen(QPen(Qt.blue, 1))
                painter.setBrush(QBrush(Qt.transparent))
                painter.drawRect(x_scaled, y_scaled, sample_width_scaled, sample_height_scaled)
                
                # Draw position ID
                painter.setPen(QPen(Qt.white, 1))
                painter.drawText(x_scaled + 5, y_scaled + 15, pos_id)
            except Exception as e:
                print(f"Ошибка отображения позиции {pos_id}: {e}")
                continue

class PreviewTab(QWidget):
    """
    Tab for previewing infographic positions on images.
    """
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.image_processor = ImageProcessor(config_manager)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Selector area
        selector_layout = QHBoxLayout()
        
        # Article selection
        article_group = QGroupBox("Выбор артикула и изображения")
        article_layout = QVBoxLayout()
        
        self.article_combo = QComboBox()
        article_layout.addWidget(QLabel("Артикул:"))
        article_layout.addWidget(self.article_combo)
        
        self.image_combo = QComboBox()
        article_layout.addWidget(QLabel("Изображение:"))
        article_layout.addWidget(self.image_combo)
        
        self.refresh_articles_button = QPushButton("Обновить список")
        self.refresh_articles_button.clicked.connect(self.refresh_articles)
        article_layout.addWidget(self.refresh_articles_button)
        
        article_group.setLayout(article_layout)
        selector_layout.addWidget(article_group)
        
        # Infographic selection
        infographic_group = QGroupBox("Выбор инфографики и позиции")
        infographic_layout = QVBoxLayout()
        
        self.infographic_combo = QComboBox()
        infographic_layout.addWidget(QLabel("Инфографика:"))
        infographic_layout.addWidget(self.infographic_combo)
        
        self.position_combo = QComboBox()
        infographic_layout.addWidget(QLabel("Позиция:"))
        infographic_layout.addWidget(self.position_combo)
        
        self.refresh_infographics_button = QPushButton("Обновить список")
        self.refresh_infographics_button.clicked.connect(self.refresh_infographics)
        infographic_layout.addWidget(self.refresh_infographics_button)
        
        infographic_group.setLayout(infographic_layout)
        selector_layout.addWidget(infographic_group)
        
        layout.addLayout(selector_layout)
        
        # Preview button
        self.preview_button = QPushButton("Сгенерировать предпросмотр")
        self.preview_button.clicked.connect(self.generate_preview)
        layout.addWidget(self.preview_button)
        
        # Preview image
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.preview_label)
        
        # Connect article selection to image listing
        self.article_combo.currentIndexChanged.connect(self.refresh_images)
        
        # Connect combos to position listing
        self.refresh_positions()
        
        # Initial data population
        self.refresh_articles()
        self.refresh_infographics()
        
        self.setLayout(layout)
    
    def refresh_articles(self):
        """Refresh the list of articles from the photos directory."""
        try:
            self.article_combo.clear()
            
            photos_dir = self.config_manager.get_settings().get("photos_dir", "photos")
            if not os.path.exists(photos_dir):
                QMessageBox.warning(self, "Ошибка", f"Директория фото не найдена: {photos_dir}")
                return
            
            articles = [d for d in os.listdir(photos_dir) if os.path.isdir(os.path.join(photos_dir, d))]
            
            if not articles:
                QMessageBox.information(self, "Информация", "Артикулы не найдены.")
                return
            
            for article in articles:
                self.article_combo.addItem(article)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список артикулов: {str(e)}")
    
    def refresh_images(self):
        """Refresh the list of images for the selected article."""
        try:
            self.image_combo.clear()
            
            article = self.article_combo.currentText()
            if not article:
                return
            
            photos_dir = self.config_manager.get_settings().get("photos_dir", "photos")
            article_dir = os.path.join(photos_dir, article)
            
            if not os.path.exists(article_dir):
                QMessageBox.warning(self, "Ошибка", f"Директория артикула не найдена: {article_dir}")
                return
            
            allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
            images = [f for f in os.listdir(article_dir) 
                     if os.path.isfile(os.path.join(article_dir, f)) and 
                     f.lower().endswith(tuple(allowed_extensions))]
            
            if not images:
                QMessageBox.information(self, "Информация", "Изображения не найдены.")
                return
            
            for image in images:
                self.image_combo.addItem(image)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список изображений: {str(e)}")
    
    def refresh_infographics(self):
        """Refresh the list of infographics."""
        try:
            self.infographic_combo.clear()
            
            # Add "None" option first
            self.infographic_combo.addItem("Нет")
            
            infografika_dir = self.config_manager.get_settings().get("infografika_dir", "infografika")
            if not os.path.exists(infografika_dir):
                QMessageBox.warning(self, "Ошибка", f"Директория инфографики не найдена: {infografika_dir}")
                return
            
            infographics = [os.path.splitext(f)[0] for f in os.listdir(infografika_dir) 
                           if f.lower().endswith('.png')]
            
            if not infographics:
                QMessageBox.information(self, "Информация", "Инфографика не найдена.")
                return
            
            for infographic in infographics:
                self.infographic_combo.addItem(infographic)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список инфографики: {str(e)}")
    
    def refresh_positions(self):
        """Refresh the list of positions."""
        try:
            self.position_combo.clear()
            
            positions = self.config_manager.get_positions()
            if not positions:
                QMessageBox.warning(self, "Ошибка", "Позиции не найдены.")
                return
            
            for pos_id in positions.keys():
                self.position_combo.addItem(pos_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список позиций: {str(e)}")
    
    def generate_preview(self):
        """Generate a preview of the selected image with infographic."""
        try:
            # Get selected values
            article = self.article_combo.currentText()
            image = self.image_combo.currentText()
            infographic = self.infographic_combo.currentText()
            position = self.position_combo.currentText()
            
            if not article or not image:
                QMessageBox.warning(self, "Ошибка", "Выберите артикул и изображение.")
                return
            
            # Get paths
            photos_dir = self.config_manager.get_settings().get("photos_dir", "photos")
            infografika_dir = self.config_manager.get_settings().get("infografika_dir", "infografika")
            photo_path = os.path.join(photos_dir, article, image)
            
            # Get settings
            settings = self.config_manager.get_settings()
            canvas_width = settings.get("canvas_width", 900)
            canvas_height = settings.get("canvas_height", 1200)
            
            # Process image
            canvas = self.image_processor.process_and_center_image(photo_path, canvas_width, canvas_height)
            
            # Add infographic if selected
            if infographic != "Нет":
                infographic_path = os.path.join(infografika_dir, infographic + ".png")
                if os.path.exists(infographic_path):
                    position_id = position
                    canvas = self.image_processor.overlay_infografika(canvas, infographic_path, position_id)
            
            # Convert PIL image to QPixmap for display
            img_data = canvas.convert("RGBA").tobytes("raw", "RGBA")
            qimage = QImage(img_data, canvas.width, canvas.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale if necessary to fit the label
            if pixmap.width() > self.preview_label.width() or pixmap.height() > self.preview_label.height():
                pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Display the preview
            self.preview_label.setPixmap(pixmap)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать предпросмотр: {str(e)}")

class ProcessImagesThread(QThread):
    """
    Thread for processing images in the background.
    """
    progress_updated = pyqtSignal(int, int)  # (current, total)
    processing_complete = pyqtSignal(int, str)  # number of processed images, output directory
    error_occurred = pyqtSignal(str)  # error message
    
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
                self.error_occurred.emit(f"Директория фото не найдена: {photos_dir}")
                return
            
            if not os.path.exists(infografika_dir):
                self.error_occurred.emit(f"Директория инфографики не найдена: {infografika_dir}")
                return
            
            if not os.path.exists(excel_file):
                self.error_occurred.emit(f"Excel файл не найден: {excel_file}")
                return
            
            # Process images from all Excel sheets
            try:
                # Проверяем Excel файл на наличие листов
                xl = pd.ExcelFile(excel_file)
                sheet_names = xl.sheet_names
                
                if not sheet_names:
                    self.error_occurred.emit("Excel файл не содержит листов")
                    return
                
                # Обрабатываем изображения и получаем результаты
                processed_count, final_output_dir = self.image_processor.generate_cards(
                    excel_file, photos_dir, infografika_dir, output_dir,
                    canvas_width, canvas_height, margin,
                    progress_callback=self.progress_updated.emit
                )
                
                self.processing_complete.emit(processed_count, final_output_dir)
                
            except Exception as e:
                self.error_occurred.emit(f"Ошибка обработки изображений: {str(e)}")
            
        except Exception as e:
            self.error_occurred.emit(f"Ошибка в потоке обработки: {str(e)}")

class ProcessTab(QWidget):
    """
    Tab for processing all images according to Excel data.
    """
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.image_processor = ImageProcessor(config_manager)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Canvas size settings
        canvas_group = QGroupBox("Размеры холста")
        canvas_layout = QVBoxLayout()
        
        # Resolution presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Предустановки:"))
        
        # 2000x3000
        preset_2000x3000 = QPushButton("2000 x 3000")
        preset_2000x3000.clicked.connect(lambda: self.set_resolution(2000, 3000))
        presets_layout.addWidget(preset_2000x3000)
        
        # 1000x1500
        preset_1000x1500 = QPushButton("1000 x 1500")
        preset_1000x1500.clicked.connect(lambda: self.set_resolution(1000, 1500))
        presets_layout.addWidget(preset_1000x1500)
        
        # 900x1200
        preset_900x1200 = QPushButton("900 x 1200")
        preset_900x1200.clicked.connect(lambda: self.set_resolution(900, 1200))
        presets_layout.addWidget(preset_900x1200)
        
        canvas_layout.addLayout(presets_layout)
        
        # Custom resolution
        custom_layout = QFormLayout()
        
        settings = self.config_manager.get_settings()
        
        self.width_input = QSpinBox()
        self.width_input.setRange(100, 5000)
        self.width_input.setValue(settings.get("canvas_width", 900))
        self.width_input.setSingleStep(10)
        
        self.height_input = QSpinBox()
        self.height_input.setRange(100, 5000)
        self.height_input.setValue(settings.get("canvas_height", 1200))
        self.height_input.setSingleStep(10)
        
        self.margin_input = QSpinBox()
        self.margin_input.setRange(0, 500)
        self.margin_input.setValue(settings.get("margin", 30))
        
        custom_layout.addRow("Ширина (px):", self.width_input)
        custom_layout.addRow("Высота (px):", self.height_input)
        custom_layout.addRow("Отступ (px):", self.margin_input)
        
        update_button = QPushButton("Обновить настройки")
        update_button.clicked.connect(self.update_settings)
        
        canvas_layout.addLayout(custom_layout)
        canvas_layout.addWidget(update_button)
        
        canvas_group.setLayout(canvas_layout)
        layout.addWidget(canvas_group)
        
        # Status section
        status_group = QGroupBox("Статус")
        status_layout = QVBoxLayout()
        
        photos_dir = settings.get("photos_dir", "photos")
        infografika_dir = settings.get("infografika_dir", "infografika")
        excel_file = settings.get("excel_file", "data.xlsx")
        
        self.status_label = QLabel()
        self.update_status_label(photos_dir, infografika_dir, excel_file)
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Process button and progress bar
        process_group = QGroupBox("Обработка")
        process_layout = QVBoxLayout()
        
        self.process_button = QPushButton("Начать обработку")
        self.process_button.clicked.connect(self.process_images)
        process_layout.addWidget(self.process_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        process_layout.addWidget(self.progress_bar)
        
        self.result_label = QLabel()
        process_layout.addWidget(self.result_label)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
        self.setLayout(layout)
    
    def set_resolution(self, width, height):
        """Установить предустановленное разрешение."""
        self.width_input.setValue(width)
        self.height_input.setValue(height)
        self.update_settings()
    
    def update_settings(self):
        """Обновить настройки размеров холста."""
        width = self.width_input.value()
        height = self.height_input.value()
        margin = self.margin_input.value()
        
        self.config_manager.update_settings(
            canvas_width=width,
            canvas_height=height,
            margin=margin
        )
        
        QMessageBox.information(self, "Настройки обновлены", 
                               f"Новые размеры: {width}x{height}, отступ: {margin}px")
    
    def update_status_label(self, photos_dir, infografika_dir, excel_file):
        """Update the status label with path checks."""
        status_text = "<b>Статус путей:</b><br>"
        
        if not os.path.exists(photos_dir):
            status_text += f"❌ Директория фото: {photos_dir} (не найдена)<br>"
        else:
            status_text += f"✓ Директория фото: {photos_dir}<br>"
        
        if not os.path.exists(infografika_dir):
            status_text += f"❌ Директория инфографики: {infografika_dir} (не найдена)<br>"
        else:
            status_text += f"✓ Директория инфографики: {infografika_dir}<br>"
        
        if not os.path.exists(excel_file):
            status_text += f"❌ Excel файл: {excel_file} (не найден)<br>"
        else:
            status_text += f"✓ Excel файл: {excel_file}<br>"
        
        self.status_label.setText(status_text)
    
    def process_images(self):
        """Process all images according to Excel data."""
        # Get settings
        settings = self.config_manager.get_settings()
        photos_dir = settings.get("photos_dir", "photos")
        infografika_dir = settings.get("infografika_dir", "infografika")
        excel_file = settings.get("excel_file", "data.xlsx")
        
        # Update status label
        self.update_status_label(photos_dir, infografika_dir, excel_file)
        
        # Check paths
        if not os.path.exists(photos_dir) or not os.path.exists(infografika_dir) or not os.path.exists(excel_file):
            QMessageBox.warning(self, "Ошибка", "Некоторые пути не существуют. Проверьте настройки.")
            return
        
        # Start processing thread
        self.process_thread = ProcessImagesThread(self.config_manager, self.image_processor)
        self.process_thread.progress_updated.connect(self.update_progress)
        self.process_thread.processing_complete.connect(self.processing_complete)
        self.process_thread.error_occurred.connect(self.processing_error)
        
        # Disable process button while processing
        self.process_button.setEnabled(False)
        self.process_button.setText("Обработка...")
        
        # Start thread
        self.process_thread.start()
    
    def update_progress(self, current, total):
        """Update progress bar."""
        progress = int(100 * current / total) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.result_label.setText(f"Обработано: {current} из {total}")
    
    def processing_complete(self, processed_count, output_dir):
        """Handle processing completion."""
        self.process_button.setEnabled(True)
        self.process_button.setText("Начать обработку")
        self.progress_bar.setValue(100)
        self.result_label.setText(f"Обработка завершена. Обработано изображений: {processed_count}")
        QMessageBox.information(self, "Обработка завершена", 
                               f"Обработка изображений завершена.\nОбработано: {processed_count} изображений.\nРезультаты сохранены в: {output_dir}")
    
    def processing_error(self, error_message):
        """Handle processing error."""
        self.process_button.setEnabled(True)
        self.process_button.setText("Начать обработку")
        self.result_label.setText(f"Ошибка: {error_message}")
        QMessageBox.critical(self, "Ошибка обработки", error_message)

class SettingsDialog(QWidget):
    """
    Dialog for editing application settings.
    """
    settings_updated = pyqtSignal()  # Signal when settings are updated
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Form for settings
        form_layout = QFormLayout()
        
        # Get current settings
        settings = self.config_manager.get_settings()
        
        # Directory settings
        self.photos_dir_input = QLineEdit(settings.get("photos_dir", "photos"))
        photos_dir_layout = QHBoxLayout()
        photos_dir_layout.addWidget(self.photos_dir_input)
        photos_dir_button = QPushButton("Обзор...")
        photos_dir_button.clicked.connect(lambda: self.browse_directory(self.photos_dir_input))
        photos_dir_layout.addWidget(photos_dir_button)
        form_layout.addRow("Директория фото:", photos_dir_layout)
        
        self.infografika_dir_input = QLineEdit(settings.get("infografika_dir", "infografika"))
        infografika_dir_layout = QHBoxLayout()
        infografika_dir_layout.addWidget(self.infografika_dir_input)
        infografika_dir_button = QPushButton("Обзор...")
        infografika_dir_button.clicked.connect(lambda: self.browse_directory(self.infografika_dir_input))
        infografika_dir_layout.addWidget(infografika_dir_button)
        form_layout.addRow("Директория инфографики:", infografika_dir_layout)
        
        self.output_dir_input = QLineEdit(settings.get("output_dir", "output"))
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_button = QPushButton("Обзор...")
        output_dir_button.clicked.connect(lambda: self.browse_directory(self.output_dir_input))
        output_dir_layout.addWidget(output_dir_button)
        form_layout.addRow("Директория вывода:", output_dir_layout)
        
        # Excel file setting
        self.excel_file_input = QLineEdit(settings.get("excel_file", "data.xlsx"))
        excel_file_layout = QHBoxLayout()
        excel_file_layout.addWidget(self.excel_file_input)
        excel_file_button = QPushButton("Обзор...")
        excel_file_button.clicked.connect(lambda: self.browse_file(self.excel_file_input, "Excel files (*.xlsx *.xls)"))
        excel_file_layout.addWidget(excel_file_button)
        form_layout.addRow("Excel файл:", excel_file_layout)
        
        # Dimension settings
        self.canvas_width_input = QSpinBox()
        self.canvas_width_input.setRange(100, 5000)
        self.canvas_width_input.setValue(settings.get("canvas_width", 900))
        form_layout.addRow("Ширина холста (px):", self.canvas_width_input)
        
        self.canvas_height_input = QSpinBox()
        self.canvas_height_input.setRange(100, 5000)
        self.canvas_height_input.setValue(settings.get("canvas_height", 1200))
        form_layout.addRow("Высота холста (px):", self.canvas_height_input)
        
        self.margin_input = QSpinBox()
        self.margin_input.setRange(0, 500)
        self.margin_input.setValue(settings.get("margin", 30))
        form_layout.addRow("Отступ (px):", self.margin_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_directory(self, line_edit):
        """Open a dialog to browse for a directory."""
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию")
        if directory:
            line_edit.setText(directory)
    
    def browse_file(self, line_edit, file_filter):
        """Open a dialog to browse for a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", file_filter)
        if file_path:
            line_edit.setText(file_path)
    
    def save_settings(self):
        """Save the settings and close the dialog."""
        # Update settings
        self.config_manager.update_settings(
            photos_dir=self.photos_dir_input.text(),
            infografika_dir=self.infografika_dir_input.text(),
            output_dir=self.output_dir_input.text(),
            excel_file=self.excel_file_input.text(),
            canvas_width=self.canvas_width_input.value(),
            canvas_height=self.canvas_height_input.value(),
            margin=self.margin_input.value()
        )
        
        # Signal that settings have been updated
        self.settings_updated.emit()
        
        # Close dialog
        self.close()

class MainWindow(QMainWindow):
    """
    Main application window.
    """
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Редактор позиций и обработка изображений")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        
        # Settings action
        settings_action = file_menu.addAction("Настройки")
        settings_action.triggered.connect(self.open_settings)
        
        # Exit action
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menu_bar.addMenu("Помощь")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_about)
        
        # Create central widget and tab layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # Position editor tab
        self.position_editor_tab = PositionEditorTab(self.config_manager)
        self.position_editor_tab.position_updated.connect(lambda: tabs.widget(1).refresh_positions())
        tabs.addTab(self.position_editor_tab, "Редактор позиций")
        
        # Preview tab
        self.preview_tab = PreviewTab(self.config_manager)
        tabs.addTab(self.preview_tab, "Предпросмотр")
        
        # Process tab
        self.process_tab = ProcessTab(self.config_manager)
        tabs.addTab(self.process_tab, "Обработка")
        
        layout.addWidget(tabs)
        
        central_widget.setLayout(layout)
    
    def open_settings(self):
        """Open the settings dialog."""
        self.settings_dialog = SettingsDialog(self.config_manager)
        self.settings_dialog.settings_updated.connect(self.on_settings_updated)
        self.settings_dialog.show()
    
    def on_settings_updated(self):
        """Handle settings updates."""
        # Update process tab status label
        settings = self.config_manager.get_settings()
        photos_dir = settings.get("photos_dir", "photos")
        infografika_dir = settings.get("infografika_dir", "infografika")
        excel_file = settings.get("excel_file", "data.xlsx")
        
        self.process_tab.update_status_label(photos_dir, infografika_dir, excel_file)
        
        # Update preview tab combos
        self.preview_tab.refresh_articles()
        self.preview_tab.refresh_infographics()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "О программе", 
                        """<b>Редактор позиций и обработка изображений</b>
                        <p>Версия 1.0.0</p>
                        <p>Программа для удобного создания и редактирования 
                        позиций инфографики, а также для автоматизированной 
                        обработки фотографий согласно данным из Excel файла.</p>
                        """)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()