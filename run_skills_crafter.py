#!/usr/bin/env python3
"""
Запуск Skills Crafter из корня проекта
"""

import sys
import os

# Убеждаемся, что мы в правильной директории
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Добавляем в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.skills_crafter.launcher import main

if __name__ == "__main__":
    sys.exit(main())
