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

        # Настройка стандартных клавиш для текстовых полей (Windows-style)
        self._setup_text_bindings()

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

        # Редактирование
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактирование", menu=edit_menu)

        edit_menu.add_command(
            label="Вырезать",
            command=self._cut,
            accelerator="Ctrl+X"
        )
        edit_menu.add_command(
            label="Копировать",
            command=self._copy,
            accelerator="Ctrl+C"
        )
        edit_menu.add_command(
            label="Вставить",
            command=self._paste,
            accelerator="Ctrl+V"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Выделить всё",
            command=self._select_all,
            accelerator="Ctrl+A"
        )

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)

        help_menu.add_command(label="О программе", command=self._show_about)

    def _create_ui(self):
        """Создание интерфейса"""
        # Основной контейнер
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Notebook с вкладками
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладка реестра предметов
        self.items_data_tab = ItemsDataTab(
            self.notebook,
            self.items_data_manager,
            crafting_manager=self.crafting_config_manager,
            on_change=self._on_data_change,
            on_navigate_to_recipe=self._navigate_to_recipe
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
            on_change=self._on_data_change,
            on_create_item=self._create_item_from_recipe
        )
        self.notebook.add(self.crafting_config_tab, text="Крафт (crafting_config)")

        # Статусная строка
        self.status_frame = ttk.Frame(self.main_frame)
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

    def _setup_text_bindings(self):
        """Настройка горячих клавиш для текстовых полей"""
        # Привязка Ctrl+A для выделения всего текста
        self.root.bind_class("Entry", "<Control-a>", self._select_all_in_widget)
        self.root.bind_class("TEntry", "<Control-a>", self._select_all_in_widget)
        self.root.bind_class("Text", "<Control-a>", self._select_all_in_widget)
        self.root.bind_class("TSpinbox", "<Control-a>", self._select_all_in_widget)

    def _select_all_in_widget(self, event):
        """Выделить весь текст в виджете"""
        widget = event.widget
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Spinbox)):
            widget.select_range(0, tk.END)
            widget.icursor(tk.END)
        elif isinstance(widget, tk.Text):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, tk.END)
        return "break"

    def _cut(self):
        """Вырезать в буфер обмена"""
        widget = self.root.focus_get()
        if widget:
            try:
                widget.event_generate("<<Cut>>")
            except tk.TclError:
                pass

    def _copy(self):
        """Копировать в буфер обмена"""
        widget = self.root.focus_get()
        if widget:
            try:
                widget.event_generate("<<Copy>>")
            except tk.TclError:
                pass

    def _paste(self):
        """Вставить из буфера обмена"""
        widget = self.root.focus_get()
        if widget:
            try:
                widget.event_generate("<<Paste>>")
            except tk.TclError:
                pass

    def _select_all(self):
        """Выделить всё в текущем виджете"""
        widget = self.root.focus_get()
        if widget:
            self._select_all_in_widget(type('Event', (), {'widget': widget})())

    def _navigate_to_recipe(self, recipe_id: str):
        """Перейти к рецепту по ID"""
        # Переключаемся на вкладку крафта (индекс 2)
        self.notebook.select(2)
        # Выбираем рецепт в списке
        self.crafting_config_tab.select_recipe_by_id(recipe_id)

    def _create_item_from_recipe(self, item_id: str, category: str, name: str, quality: str):
        """Создать новый предмет из рецепта"""
        # Создаём базовые данные для предмета
        item_data = {
            "name": name if name else item_id
        }
        if quality:
            item_data["quality"] = quality

        # Добавляем предмет
        if self.items_data_manager.add_item(category, item_id, item_data):
            self._on_data_change()
            # Обновляем кэш рецептов в реестре предметов
            self.items_data_tab.refresh_recipe_cache()
            messagebox.showinfo(
                "Предмет создан",
                f"Предмет '{item_id}' добавлен в категорию '{category}'.\n\n"
                "Вы можете отредактировать его параметры во вкладке 'Реестр предметов'."
            )
        else:
            messagebox.showerror("Ошибка", f"Не удалось создать предмет '{item_id}'")

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
            # Пересоздаём интерфейс полностью
            self.main_frame.destroy()
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
            "Items Config Editor v1.1.0\n\n"
            "Утилита для редактирования конфигурации\n"
            "системы предметов игры.\n\n"
            "Файлы:\n"
            f"- {os.path.basename(self.items_data_path)}\n"
            f"- {os.path.basename(self.items_config_path)}\n"
            f"- {os.path.basename(self.crafting_config_path)}\n\n"
            "Горячие клавиши:\n"
            "Ctrl+S - Сохранить всё\n"
            "Ctrl+R - Перезагрузить\n"
            "Ctrl+C - Копировать\n"
            "Ctrl+X - Вырезать\n"
            "Ctrl+V - Вставить\n"
            "Ctrl+A - Выделить всё"
        )
