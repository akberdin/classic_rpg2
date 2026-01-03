#!/usr/bin/env python3
"""
Items Crafter Launcher
Точка входа для утилиты создания и редактирования предметов
"""

import sys
import os

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


def main():
    """Главная функция"""
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

    # Импорт и запуск
    try:
        from utils.items_crafter.gui.main_window import ItemsCrafterApp

        root = tk.Tk()

        # Настройка иконки (если есть)
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "assets", "icons", "items_crafter.png"
            )
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
        except Exception:
            pass

        app = ItemsCrafterApp(root)
        root.mainloop()
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
