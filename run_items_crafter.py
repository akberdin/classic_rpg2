#!/usr/bin/env python3
"""
Скрипт запуска Items Crafter
Утилита для создания и редактирования предметов и рецептов
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.items_crafter.launcher import main

if __name__ == "__main__":
    sys.exit(main())
