#!/usr/bin/env python3
"""
Launcher для тестовой арены Skills Crafter

Запуск:
    python -m utils.skills_crafter.test_arena.launcher
    или
    python utils/skills_crafter/test_arena/launcher.py
"""

import sys
import os

# Добавляем корневую директорию проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def check_pygame():
    """Проверка наличия pygame"""
    try:
        import pygame
        return True
    except ImportError:
        print("=" * 50)
        print("ОШИБКА: pygame не установлен!")
        print("=" * 50)
        print()
        print("Для запуска тестовой арены необходим pygame.")
        print("Установите его командой:")
        print()
        print("    pip install pygame")
        print()
        return False


def run_test_arena():
    """Запустить тестовую арену"""
    print("=" * 50)
    print("Skills Crafter - Test Arena")
    print("=" * 50)
    print()

    if not check_pygame():
        return 1

    print("Загрузка тестовой арены...")
    print()

    try:
        from utils.skills_crafter.test_arena.arena import TestArena

        arena = TestArena()
        arena.setup_default_arena()

        print("Управление:")
        print("  1-8     - Выбор умения")
        print("  ЛКМ     - Применить умение / Выбрать цель")
        print("  ПКМ     - Отменить выбор")
        print("  R       - Сбросить арену")
        print("  Space   - Следующий ход (обработка эффектов)")
        print("  Esc     - Выход")
        print()
        print("Запуск...")

        arena.run()
        return 0

    except Exception as e:
        print(f"Ошибка запуска арены: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Главная функция"""
    sys.exit(run_test_arena())


if __name__ == "__main__":
    main()
