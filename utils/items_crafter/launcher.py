#!/usr/bin/env python3
"""
Items Crafter Launcher v2.0
Точка входа для утилиты создания и редактирования предметов
"""

import sys
import os
import argparse

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import messagebox


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Items Crafter v2.0 - редактор предметов и рецептов")
    parser.add_argument("--version", "-v", action="store_true", help="Показать версию")
    args = parser.parse_args()

    if args.version:
        print("Items Crafter v2.0")
        return 0

    try:
        from utils.items_crafter.gui_v2.main_window import ItemsCrafterAppV2
        root = tk.Tk()
        app = ItemsCrafterAppV2(root)
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
