#!/usr/bin/env python3
"""
Items Crafter Launcher v2.0
Точка входа для утилиты создания и редактирования предметов

Запускает новую версию v2.0 с:
- Новой системой предметов и рецептов
- Связью предмет-рецепт
- Шаблонами экипировки
- Системой нейминга через словари
- Буфером обмена
"""

import sys
import os
import argparse

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import messagebox


def check_dependencies():
    """Проверка зависимостей"""
    missing = []

    try:
        import json
    except ImportError:
        missing.append("json (встроен в Python)")

    return missing


def run_v1():
    """Запуск старой версии v1.0"""
    from utils.items_crafter.gui.main_window import ItemsCrafterApp
    root = tk.Tk()
    app = ItemsCrafterApp(root)
    root.mainloop()


def run_v2():
    """Запуск новой версии v2.0"""
    from utils.items_crafter.gui_v2.main_window import ItemsCrafterAppV2
    root = tk.Tk()
    app = ItemsCrafterAppV2(root)
    root.mainloop()


def main():
    """Главная функция"""
    # Парсинг аргументов
    parser = argparse.ArgumentParser(description="Items Crafter - редактор предметов и рецептов")
    parser.add_argument("--legacy", "-l", action="store_true",
                       help="Запустить старую версию v1.0")
    parser.add_argument("--version", "-v", action="store_true",
                       help="Показать версию")
    args = parser.parse_args()

    if args.version:
        print("Items Crafter v2.0")
        return 0

    # Проверка зависимостей
    missing = check_dependencies()
    if missing:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Отсутствуют зависимости",
            "Для работы Items Crafter необходимо установить:\n\n" +
            "\n".join(f"• {dep}" for dep in missing)
        )
        return 1

    # Запуск
    try:
        # Настройка иконки (если есть)
        if args.legacy:
            run_v1()
        else:
            run_v2()

        return 0

    except Exception as e:
        import traceback
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка запуска",
            f"Не удалось запустить Items Crafter:\n\n{e}\n\n{traceback.format_exc()}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
