"""
Главное окно Items Config Editor
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

from utils.items_config.models import (
    ItemsDataManager, ItemsConfigManager, CraftingConfigManager, get_config_paths
)
from utils.items_config.gui.items_data_tab import ItemsDataTab
from utils.items_config.gui.items_config_tab import ItemsConfigTab
from utils.items_config.gui.crafting_config_tab import CraftingConfigTab


class ItemsConfigApp:
    """Главное приложение Items Config Editor"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Items Config Editor")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        # Пути к файлам
        self.items_data_path, self.items_config_path, self.crafting_config_path = get_config_paths()

        # Менеджеры данных
        self.items_data_manager = ItemsDataManager(self.items_data_path)
        self.items_config_manager = ItemsConfigManager(self.items_config_path)
        self.crafting_config_manager = CraftingConfigManager(self.crafting_config_path)

        # Загрузка данных
        if not self._load_data():
            return

        # Флаг изменений
        self.has_unsaved_changes = False

        # Создание интерфейса
        self._create_menu()
        self._create_ui()
        self._update_title()

        # Обработка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Горячие клавиши
        self.root.bind("<Control-s>", lambda e: self._save_all())
        self.root.bind("<Control-r>", lambda e: self._reload_data())

    def _load_data(self) -> bool:
        """Загрузить данные из файлов"""
        if not os.path.exists(self.items_data_path):
            messagebox.showerror(
                "Ошибка",
                f"Файл не найден:\n{self.items_data_path}"
            )
            return False

        if not os.path.exists(self.items_config_path):
            messagebox.showerror(
                "Ошибка",
                f"Файл не найден:\n{self.items_config_path}"
            )
            return False

        if not os.path.exists(self.crafting_config_path):
            messagebox.showerror(
                "Ошибка",
                f"Файл не найден:\n{self.crafting_config_path}"
            )
            return False

        if not self.items_data_manager.load():
            messagebox.showerror("Ошибка", "Не удалось загрузить items_data.json")
            return False

        if not self.items_config_manager.load():
            messagebox.showerror("Ошибка", "Не удалось загрузить items_config.json")
            return False

        if not self.crafting_config_manager.load():
            messagebox.showerror("Ошибка", "Не удалось загрузить crafting_config.json")
            return False

        return True

    def _create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)

        file_menu.add_command(
            label="Сохранить всё",
            command=self._save_all,
            accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label="Перезагрузить",
            command=self._reload_data,
            accelerator="Ctrl+R"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)

        help_menu.add_command(label="О программе", command=self._show_about)

    def _create_ui(self):
        """Создание интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # Notebook с вкладками
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладка реестра предметов
        self.items_data_tab = ItemsDataTab(
            self.notebook,
            self.items_data_manager,
            on_change=self._on_data_change
        )
        self.notebook.add(self.items_data_tab, text="Реестр предметов (items_data)")

        # Вкладка конфигурации
        self.items_config_tab = ItemsConfigTab(
            self.notebook,
            self.items_config_manager,
            on_change=self._on_data_change
        )
        self.notebook.add(self.items_config_tab, text="Конфигурация (items_config)")

        # Вкладка крафта
        self.crafting_config_tab = CraftingConfigTab(
            self.notebook,
            self.crafting_config_manager,
            self.items_data_manager,
            on_change=self._on_data_change
        )
        self.notebook.add(self.crafting_config_tab, text="Крафт (crafting_config)")

        # Статусная строка
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(
            self.status_frame,
            text="Готово",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=5, pady=2)

        # Кнопки справа
        btn_frame = ttk.Frame(self.status_frame)
        btn_frame.pack(side="right", padx=5, pady=2)

        ttk.Button(
            btn_frame, text="Сохранить всё",
            command=self._save_all
        ).pack(side="left", padx=2)

        ttk.Button(
            btn_frame, text="Перезагрузить",
            command=self._reload_data
        ).pack(side="left", padx=2)

    def _on_data_change(self):
        """Обработка изменения данных"""
        self.has_unsaved_changes = True
        self._update_title()
        self._update_status("Есть несохранённые изменения")

    def _update_title(self):
        """Обновить заголовок окна"""
        title = "Items Config Editor"
        if self.has_unsaved_changes:
            title += " *"
        self.root.title(title)

    def _update_status(self, text: str):
        """Обновить статусную строку"""
        self.status_label.config(text=text)

    def _save_all(self):
        """Сохранить все изменения"""
        errors = []

        if not self.items_data_manager.save():
            errors.append("items_data.json")

        if not self.items_config_manager.save():
            errors.append("items_config.json")

        if not self.crafting_config_manager.save():
            errors.append("crafting_config.json")

        if errors:
            messagebox.showerror(
                "Ошибка сохранения",
                f"Не удалось сохранить:\n" + "\n".join(errors)
            )
        else:
            self.has_unsaved_changes = False
            self._update_title()
            self._update_status("Все изменения сохранены")
            messagebox.showinfo("Успех", "Все изменения сохранены")

    def _reload_data(self):
        """Перезагрузить данные из файлов"""
        if self.has_unsaved_changes:
            if not messagebox.askyesno(
                "Подтверждение",
                "Есть несохранённые изменения. Перезагрузить?"
            ):
                return

        if self._load_data():
            # Пересоздаём вкладки
            self.notebook.destroy()
            self._create_ui()
            self.has_unsaved_changes = False
            self._update_title()
            self._update_status("Данные перезагружены")

    def _on_close(self):
        """Обработка закрытия окна"""
        if self.has_unsaved_changes:
            result = messagebox.askyesnocancel(
                "Сохранить изменения?",
                "Есть несохранённые изменения. Сохранить перед выходом?"
            )

            if result is None:  # Cancel
                return
            elif result:  # Yes
                self._save_all()

        self.root.destroy()

    def _show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "О программе",
            "Items Config Editor v1.0.0\n\n"
            "Утилита для редактирования конфигурации\n"
            "системы предметов игры.\n\n"
            "Файлы:\n"
            f"- {os.path.basename(self.items_data_path)}\n"
            f"- {os.path.basename(self.items_config_path)}\n"
            f"- {os.path.basename(self.crafting_config_path)}\n\n"
            "Горячие клавиши:\n"
            "Ctrl+S - Сохранить всё\n"
            "Ctrl+R - Перезагрузить"
        )
