#!/usr/bin/env python3
"""
Скрипт запуска тестовой арены Skills Crafter

Использование:
    python run_test_arena.py
"""

import sys
import os

# Устанавливаем рабочую директорию
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем
from utils.skills_crafter.test_arena.launcher import main

if __name__ == "__main__":
    main()
