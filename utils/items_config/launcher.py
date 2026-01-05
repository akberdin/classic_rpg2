#!/usr/bin/env python3
"""
Items Config Editor Launcher
Точка входа для утилиты редактирования конфигурации предметов
"""

import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import messagebox


def main():
    """Главная функция"""
    try:
        from utils.items_config.gui.main_window import ItemsConfigApp

        root = tk.Tk()

        # Настройка иконки (если есть)
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "assets", "icons", "items_config.png"
            )
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
        except Exception:
            pass

        app = ItemsConfigApp(root)
        root.mainloop()
        return 0

    except Exception as e:
        import traceback
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка запуска",
            f"Не удалось запустить Items Config Editor:\n\n{e}\n\n{traceback.format_exc()}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
