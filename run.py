#!/usr/bin/env python3
"""
Запускной скрипт для приложения обработки изображений.
Обеспечивает правильную настройку путей и импорт модулей.
"""
import os
import sys

# Добавляем корневую директорию проекта в путь Python 
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# Импортируем функцию main из главного модуля приложения
from attached_assets.main_app import main

if __name__ == "__main__":
    # Запускаем главную функцию приложения
    print("Запуск приложения для обработки изображений...")
    main()