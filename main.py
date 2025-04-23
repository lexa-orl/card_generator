#!/usr/bin/env python3
import os
import sys

# Добавляем текущую директорию в путь Python для поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Теперь импортируем main из main_app
from attached_assets.main_app import main

if __name__ == "__main__":
    main()