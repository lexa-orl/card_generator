import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QSpinBox, QMessageBox, QGroupBox, 
                           QFormLayout, QRadioButton, QComboBox, QGridLayout)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

class AnchorPositionEditor(QWidget):
    """
    Новый интуитивный редактор позиций с использованием якорных точек.
    Позволяет четко видеть, какой точкой инфографика будет привязана к заданным координатам.
    """
    position_updated = pyqtSignal(str, str, str, str)  # (id, x_formula, y_formula, anchor)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_anchor = "top-left"  # Якорь по умолчанию
        self.initUI()
    
    def initUI(self):
        # Главный лейаут
        main_layout = QVBoxLayout()
        
        # Панель выбора существующих позиций
        position_selector = QGroupBox("Выберите или создайте позицию")
        position_layout = QVBoxLayout()
        
        # Комбобокс для выбора позиций
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Существующие позиции:"))
        self.positions_combo = QComboBox()
        self.positions_combo.setMinimumWidth(250)
        self.refresh_positions_list()
        selector_layout.addWidget(self.positions_combo)
        
        load_button = QPushButton("Загрузить")
        load_button.clicked.connect(self.load_selected_position)
        selector_layout.addWidget(load_button)
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.delete_selected_position)
        selector_layout.addWidget(delete_button)
        
        position_layout.addLayout(selector_layout)
        
        # Поле для ID позиции
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Название позиции:"))
        self.position_id_input = QLineEdit()
        self.position_id_input.setPlaceholderText("Введите уникальное название для позиции")
        id_layout.addWidget(self.position_id_input)
        position_layout.addLayout(id_layout)
        
        position_selector.setLayout(position_layout)
        main_layout.addWidget(position_selector)
        
        # Создаем горизонтальный лейаут для редактора и превью
        editor_preview_layout = QHBoxLayout()
        
        # ====== Левая часть: редактор координат ======
        editor_panel = QGroupBox("Настройка координат и якорной точки")
        editor_layout = QVBoxLayout()
        
        # Координаты X и Y
        coord_layout = QFormLayout()
        
        # X-координата
        x_layout = QHBoxLayout()
        self.x_coord_spinbox = QSpinBox()
        self.x_coord_spinbox.setRange(0, 2000)
        self.x_coord_spinbox.setValue(30)
        self.x_coord_spinbox.valueChanged.connect(self.update_preview)
        
        self.x_formula_combo = QComboBox()
        self.x_formula_combo.addItems([
            "Абсолютное значение",
            "Отступ слева (MARGIN)",
            "Центр холста",
            "Правый край с отступом (MARGIN)"
        ])
        self.x_formula_combo.currentIndexChanged.connect(self.update_preview)
        
        x_layout.addWidget(self.x_coord_spinbox)
        x_layout.addWidget(self.x_formula_combo)
        coord_layout.addRow("X:", x_layout)
        
        # Y-координата
        y_layout = QHBoxLayout()
        self.y_coord_spinbox = QSpinBox()
        self.y_coord_spinbox.setRange(0, 2000)
        self.y_coord_spinbox.setValue(30)
        self.y_coord_spinbox.valueChanged.connect(self.update_preview)
        
        self.y_formula_combo = QComboBox()
        self.y_formula_combo.addItems([
            "Абсолютное значение",
            "Отступ сверху (MARGIN)",
            "Центр холста",
            "Нижний край с отступом (MARGIN)"
        ])
        self.y_formula_combo.currentIndexChanged.connect(self.update_preview)
        
        y_layout.addWidget(self.y_coord_spinbox)
        y_layout.addWidget(self.y_formula_combo)
        coord_layout.addRow("Y:", y_layout)
        
        editor_layout.addLayout(coord_layout)
        
        # Выбор якорной точки (якорной точки инфографики)
        anchor_group = QGroupBox("Якорная точка инфографики")
        anchor_layout = QGridLayout()
        
        # Создаем радиокнопки в виде 3х3 сетки для выбора точки привязки
        self.anchor_top_left = QRadioButton("▲◄")
        self.anchor_top_center = QRadioButton("▲")
        self.anchor_top_right = QRadioButton("▲►")
        
        self.anchor_middle_left = QRadioButton("◄")
        self.anchor_center = QRadioButton("⬤")
        self.anchor_middle_right = QRadioButton("►")
        
        self.anchor_bottom_left = QRadioButton("▼◄")
        self.anchor_bottom_center = QRadioButton("▼")
        self.anchor_bottom_right = QRadioButton("▼►")
        
        # Добавляем их в сетку
        anchor_layout.addWidget(self.anchor_top_left, 0, 0)
        anchor_layout.addWidget(self.anchor_top_center, 0, 1)
        anchor_layout.addWidget(self.anchor_top_right, 0, 2)
        
        anchor_layout.addWidget(self.anchor_middle_left, 1, 0)
        anchor_layout.addWidget(self.anchor_center, 1, 1)
        anchor_layout.addWidget(self.anchor_middle_right, 1, 2)
        
        anchor_layout.addWidget(self.anchor_bottom_left, 2, 0)
        anchor_layout.addWidget(self.anchor_bottom_center, 2, 1)
        anchor_layout.addWidget(self.anchor_bottom_right, 2, 2)
        
        anchor_group.setLayout(anchor_layout)
        editor_layout.addWidget(anchor_group)
        
        # Описание редактора
        description = QLabel(
            "Выберите, какой точкой инфографика должна привязываться к указанным координатам. "
            "Например, выбрав верхний левый угол (▲◄), инфографика будет размещаться правее и ниже указанной точки. "
            "Выбрав центральную точку (⬤), инфографика будет центрироваться относительно указанных координат."
        )
        description.setWordWrap(True)
        editor_layout.addWidget(description)
        
        # Кнопка сохранения
        save_button = QPushButton("Сохранить позицию")
        save_button.clicked.connect(self.save_position)
        editor_layout.addWidget(save_button)
        
        editor_panel.setLayout(editor_layout)
        editor_preview_layout.addWidget(editor_panel)
        
        # ====== Правая часть: предпросмотр ======
        preview_panel = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        
        self.preview_canvas = QWidget()
        self.preview_canvas.setMinimumSize(350, 500)
        self.preview_canvas.setStyleSheet("background-color: white;")
        
        preview_layout.addWidget(self.preview_canvas)
        
        # Формулы позиции
        self.formula_label = QLabel("Формулы:")
        self.formula_label.setWordWrap(True)
        preview_layout.addWidget(self.formula_label)
        
        preview_panel.setLayout(preview_layout)
        editor_preview_layout.addWidget(preview_panel)
        
        main_layout.addLayout(editor_preview_layout)
        
        # Устанавливаем основной лейаут
        self.setLayout(main_layout)
        
        # Соединяем радиокнопки якорей с функцией обновления
        anchor_buttons = [
            (self.anchor_top_left, "top-left"),
            (self.anchor_top_center, "top-center"), 
            (self.anchor_top_right, "top-right"),
            (self.anchor_middle_left, "middle-left"), 
            (self.anchor_center, "center"), 
            (self.anchor_middle_right, "middle-right"),
            (self.anchor_bottom_left, "bottom-left"), 
            (self.anchor_bottom_center, "bottom-center"), 
            (self.anchor_bottom_right, "bottom-right")
        ]
        
        for button, anchor_name in anchor_buttons:
            button.clicked.connect(lambda checked, a=anchor_name: self.set_anchor(a))
        
        # По умолчанию выбираем верхний левый угол
        self.anchor_top_left.setChecked(True)
        
        # Инициализируем первичное отображение
        QTimer.singleShot(100, self.update_preview)
    
    def set_anchor(self, anchor):
        """Устанавливает текущий якорь и обновляет предпросмотр."""
        self.current_anchor = anchor
        self.update_preview()
    
    def get_formula_from_combo(self, value, combo_index, canvas_size, item_size, is_x=True):
        """Получает формулу координаты в зависимости от выбранного типа и значения."""
        if combo_index == 0:  # Абсолютное значение
            return str(value)
        elif combo_index == 1:  # Отступ (MARGIN)
            if value == self.config_manager.get_settings().get("margin", 30):
                return "MARGIN"
            else:
                return f"MARGIN + {value - self.config_manager.get_settings().get('margin', 30)}"
        elif combo_index == 2:  # Центр холста
            size_var = "canvas_width" if is_x else "canvas_height"
            if value == canvas_size // 2:
                return f"{size_var} // 2"
            else:
                offset = value - (canvas_size // 2)
                sign = "+" if offset >= 0 else "-"
                return f"({size_var} // 2) {sign} {abs(offset)}"
        elif combo_index == 3:  # Край с отступом
            size_var = "canvas_width" if is_x else "canvas_height"
            margin = self.config_manager.get_settings().get("margin", 30)
            if value == canvas_size - margin:
                return f"{size_var} - MARGIN"
            else:
                offset = canvas_size - margin - value
                sign = "+" if offset < 0 else "-"
                return f"{size_var} - MARGIN {sign} {abs(offset)}"
        return str(value)
    
    def refresh_positions_list(self):
        """Обновить список доступных позиций."""
        self.positions_combo.clear()
        positions = self.config_manager.get_positions()
        for pos_id in positions.keys():
            self.positions_combo.addItem(pos_id)
    
    def update_preview(self):
        """Обновить предпросмотр позиции."""
        if not hasattr(self, 'preview_canvas') or not self.preview_canvas:
            return
        
        # Получаем настройки
        settings = self.config_manager.get_settings()
        canvas_width = settings.get("canvas_width", 900)
        canvas_height = settings.get("canvas_height", 1200)
        margin = settings.get("margin", 30)
        
        # Получаем текущие значения
        x_value = self.x_coord_spinbox.value()
        y_value = self.y_coord_spinbox.value()
        x_formula_index = self.x_formula_combo.currentIndex()
        y_formula_index = self.y_formula_combo.currentIndex()
        
        # Генерируем формулы
        x_formula = self.get_formula_from_combo(x_value, x_formula_index, canvas_width, 300, True)
        y_formula = self.get_formula_from_combo(y_value, y_formula_index, canvas_height, 300, False)
        
        # Обновляем метку с формулами
        self.formula_label.setText(f"X: {x_formula}\nY: {y_formula}\nЯкорь: {self.current_anchor}")
        
        # Создаем пиксмап для рисования
        pixmap = QPixmap(self.preview_canvas.width(), self.preview_canvas.height())
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Размер примера инфографики
        sample_width = 300
        sample_height = 300
        
        # Масштабируем для отображения
        scale_factor = min(self.preview_canvas.width() / canvas_width, 
                          self.preview_canvas.height() / canvas_height) * 0.9
        display_width = int(canvas_width * scale_factor)
        display_height = int(canvas_height * scale_factor)
        
        # Центрируем отображение
        offset_x = (self.preview_canvas.width() - display_width) // 2
        offset_y = (self.preview_canvas.height() - display_height) // 2
        
        # Рисуем фон холста
        painter.fillRect(offset_x, offset_y, display_width, display_height, QColor(211, 211, 211))
        
        # Рисуем границы отступов
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        margin_scaled = int(margin * scale_factor)
        painter.drawRect(offset_x + margin_scaled, offset_y + margin_scaled, 
                       display_width - 2 * margin_scaled, display_height - 2 * margin_scaled)
        
        # Рисуем центральные линии
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
        center_x = offset_x + display_width // 2
        center_y = offset_y + display_height // 2
        painter.drawLine(center_x, offset_y, center_x, offset_y + display_height)
        painter.drawLine(offset_x, center_y, offset_x + display_width, center_y)
        
        try:
            # Вычисляем позицию на основе формул
            context = {
                "canvas_width": canvas_width,
                "canvas_height": canvas_height,
                "infografika_width": sample_width,
                "infografika_height": sample_height,
                "MARGIN": margin
            }
            
            x_pos = eval(x_formula, {"__builtins__": {}}, context)
            y_pos = eval(y_formula, {"__builtins__": {}}, context)
            
            # Получаем смещение для якорной точки
            anchor_x_offset, anchor_y_offset = self.config_manager.get_anchor_offset(
                self.current_anchor, sample_width, sample_height
            )
            
            # Вычисляем координаты левого верхнего угла инфографики с учетом якоря
            infographic_x = x_pos - anchor_x_offset
            infographic_y = y_pos - anchor_y_offset
            
            # Масштабируем координаты для отображения
            x_scaled = int(x_pos * scale_factor) + offset_x
            y_scaled = int(y_pos * scale_factor) + offset_y
            infographic_x_scaled = int(infographic_x * scale_factor) + offset_x
            infographic_y_scaled = int(infographic_y * scale_factor) + offset_y
            sample_width_scaled = int(sample_width * scale_factor)
            sample_height_scaled = int(sample_height * scale_factor)
            
            # Рисуем контур инфографики
            painter.setPen(QPen(Qt.blue, 1))
            painter.setBrush(QBrush(QColor(0, 0, 255, 50)))  # Полупрозрачный синий
            painter.drawRect(infographic_x_scaled, infographic_y_scaled, 
                             sample_width_scaled, sample_height_scaled)
            
            # Рисуем якорную точку
            marker_size = 6
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(QBrush(Qt.red))
            painter.drawEllipse(x_scaled - marker_size/2, y_scaled - marker_size/2, marker_size, marker_size)
            
            # Рисуем линию от якоря к углу инфографики, чтобы показать связь
            painter.setPen(QPen(Qt.red, 1, Qt.DashLine))
            painter.drawLine(x_scaled, y_scaled, infographic_x_scaled, infographic_y_scaled)
            
            # Добавляем координаты якорной точки
            painter.setPen(QPen(Qt.black, 1))
            position_desc = f"Якорь на ({x_pos}, {y_pos})"
            painter.drawText(offset_x + 10, offset_y + display_height - 10, position_desc)
            
        except Exception as e:
            painter.setPen(QPen(Qt.red, 1))
            painter.drawText(offset_x + 10, offset_y + 20, f"Ошибка: {str(e)}")
        
        painter.end()
        
        # Отображаем результат на канвасе
        if hasattr(self, '_preview_label'):
            self._preview_label.setPixmap(pixmap)
        else:
            self._preview_label = QLabel(self.preview_canvas)
            self._preview_label.setGeometry(0, 0, self.preview_canvas.width(), self.preview_canvas.height())
            self._preview_label.setPixmap(pixmap)
            self._preview_label.show()
            
    def load_selected_position(self):
        """Загрузить выбранную позицию для редактирования."""
        pos_id = self.positions_combo.currentText()
        if not pos_id:
            QMessageBox.warning(self, "Ошибка", "Выберите позицию из списка")
            return
        
        positions = self.config_manager.get_positions()
        if pos_id not in positions:
            QMessageBox.warning(self, "Ошибка", f"Позиция {pos_id} не найдена")
            return
        
        # Загружаем позицию
        position = positions[pos_id]
        x_formula = position["x"]
        y_formula = position["y"]
        anchor = position.get("anchor", "top-left")
        
        # Устанавливаем ID позиции
        self.position_id_input.setText(pos_id)
        
        # Устанавливаем якорь
        anchor_map = {
            "top-left": self.anchor_top_left,
            "top-center": self.anchor_top_center,
            "top-right": self.anchor_top_right,
            "middle-left": self.anchor_middle_left,
            "center": self.anchor_center,
            "middle-right": self.anchor_middle_right,
            "bottom-left": self.anchor_bottom_left,
            "bottom-center": self.anchor_bottom_center,
            "bottom-right": self.anchor_bottom_right
        }
        
        if anchor in anchor_map:
            anchor_map[anchor].setChecked(True)
            self.current_anchor = anchor
        
        # Пытаемся определить тип формулы и установить комбобоксы
        # Это упрощенный подход, который работает только для формул из наших шаблонов
        settings = self.config_manager.get_settings()
        canvas_width = settings.get("canvas_width", 900)
        canvas_height = settings.get("canvas_height", 1200)
        margin = settings.get("margin", 30)
        
        # Устанавливаем наиболее подходящие варианты для X
        if "MARGIN" in x_formula and "canvas_width" not in x_formula:
            self.x_formula_combo.setCurrentIndex(1)  # Отступ слева
            if x_formula == "MARGIN":
                self.x_coord_spinbox.setValue(margin)
            else:
                # Пытаемся извлечь смещение
                try:
                    context = {"MARGIN": margin}
                    x_value = eval(x_formula, {"__builtins__": {}}, context)
                    self.x_coord_spinbox.setValue(x_value)
                except:
                    self.x_coord_spinbox.setValue(margin)
        elif "canvas_width // 2" in x_formula:
            self.x_formula_combo.setCurrentIndex(2)  # Центр холста
            try:
                context = {"canvas_width": canvas_width}
                x_value = eval(x_formula, {"__builtins__": {}}, context)
                self.x_coord_spinbox.setValue(x_value)
            except:
                self.x_coord_spinbox.setValue(canvas_width // 2)
        elif "canvas_width - " in x_formula:
            self.x_formula_combo.setCurrentIndex(3)  # Правый край
            try:
                context = {"canvas_width": canvas_width, "MARGIN": margin}
                x_value = eval(x_formula, {"__builtins__": {}}, context)
                self.x_coord_spinbox.setValue(x_value)
            except:
                self.x_coord_spinbox.setValue(canvas_width - margin)
        else:
            self.x_formula_combo.setCurrentIndex(0)  # Абсолютное значение
            try:
                x_value = int(x_formula)
                self.x_coord_spinbox.setValue(x_value)
            except:
                self.x_coord_spinbox.setValue(30)
        
        # Устанавливаем наиболее подходящие варианты для Y
        if "MARGIN" in y_formula and "canvas_height" not in y_formula:
            self.y_formula_combo.setCurrentIndex(1)  # Отступ сверху
            if y_formula == "MARGIN":
                self.y_coord_spinbox.setValue(margin)
            else:
                # Пытаемся извлечь смещение
                try:
                    context = {"MARGIN": margin}
                    y_value = eval(y_formula, {"__builtins__": {}}, context)
                    self.y_coord_spinbox.setValue(y_value)
                except:
                    self.y_coord_spinbox.setValue(margin)
        elif "canvas_height // 2" in y_formula:
            self.y_formula_combo.setCurrentIndex(2)  # Центр холста
            try:
                context = {"canvas_height": canvas_height}
                y_value = eval(y_formula, {"__builtins__": {}}, context)
                self.y_coord_spinbox.setValue(y_value)
            except:
                self.y_coord_spinbox.setValue(canvas_height // 2)
        elif "canvas_height - " in y_formula:
            self.y_formula_combo.setCurrentIndex(3)  # Нижний край
            try:
                context = {"canvas_height": canvas_height, "MARGIN": margin}
                y_value = eval(y_formula, {"__builtins__": {}}, context)
                self.y_coord_spinbox.setValue(y_value)
            except:
                self.y_coord_spinbox.setValue(canvas_height - margin)
        else:
            self.y_formula_combo.setCurrentIndex(0)  # Абсолютное значение
            try:
                y_value = int(y_formula)
                self.y_coord_spinbox.setValue(y_value)
            except:
                self.y_coord_spinbox.setValue(30)
        
        # Обновляем предпросмотр
        self.update_preview()
        
        QMessageBox.information(self, "Позиция загружена", 
                              f"Позиция {pos_id} загружена. Вы можете изменить параметры и сохранить.")
    
    def delete_selected_position(self):
        """Удалить выбранную позицию."""
        pos_id = self.positions_combo.currentText()
        if not pos_id:
            QMessageBox.warning(self, "Ошибка", "Выберите позицию из списка")
            return
        
        positions = self.config_manager.get_positions()
        if pos_id not in positions:
            QMessageBox.warning(self, "Ошибка", f"Позиция {pos_id} не найдена")
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(self, "Подтверждение удаления", 
                                    f"Вы действительно хотите удалить позицию {pos_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Сохраняем ID для обновления позиции перед удалением
            deleted_pos_id = pos_id
            
            # Удаляем позицию
            self.config_manager.delete_position(pos_id)
            QMessageBox.information(self, "Успех", f"Позиция {pos_id} удалена")
            
            # Очищаем поле ввода ID позиции
            self.position_id_input.clear()
            
            # Обновить список позиций
            self.refresh_positions_list()
            
            # Передаем сигнал о том, что позиция удалена с указанием ID
            # Пустые строки для формул означают удаление
            self.position_updated.emit(deleted_pos_id, "", "", "")
    
    def save_position(self):
        """Сохранить текущую позицию."""
        pos_id = self.position_id_input.text().strip()
        if not pos_id:
            QMessageBox.warning(self, "Ошибка", "Введите название позиции")
            return
        
        # Получаем настройки
        settings = self.config_manager.get_settings()
        canvas_width = settings.get("canvas_width", 900)
        canvas_height = settings.get("canvas_height", 1200)
        
        # Получаем текущие значения
        x_value = self.x_coord_spinbox.value()
        y_value = self.y_coord_spinbox.value()
        x_formula_index = self.x_formula_combo.currentIndex()
        y_formula_index = self.y_formula_combo.currentIndex()
        
        # Генерируем формулы
        x_formula = self.get_formula_from_combo(x_value, x_formula_index, canvas_width, 300, True)
        y_formula = self.get_formula_from_combo(y_value, y_formula_index, canvas_height, 300, False)
        
        # Передаем сигнал об обновлении позиции
        self.position_updated.emit(pos_id, x_formula, y_formula, self.current_anchor)
        
        # Обновляем список позиций после сохранения
        self.refresh_positions_list()