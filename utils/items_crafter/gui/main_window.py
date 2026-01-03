"""
Главное окно Items Crafter
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from ..models import ItemsCrafterProject
from ..exporter import ItemsExporter, ItemsImporter, save_project, load_project
from .tabs import ResourcesTab, WeaponsTab, ArmorTab, JewelryTab, PotionsTab, RecipesTab


class ItemsCrafterApp:
    """Главное приложение Items Crafter"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Items Crafter - Редактор предметов и рецептов")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Проект
        self.project = ItemsCrafterProject()
        self.project_file: Optional[str] = None
        self._is_modified = False

        # Путь к конфигам игры
        self._game_config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "game", "config"
        )

        # Создаём интерфейс
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_statusbar()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Попытка импорта из игровых конфигов
        self._try_import_from_game()

    def _create_menu(self):
        """Создать главное меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый проект", command=self._new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть проект...", command=self._open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить проект", command=self._save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self._save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Импорт из игры...", command=self._import_from_game)
        file_menu.add_command(label="Экспорт в игру", command=self._export_to_game)
        file_menu.add_command(label="Экспорт в отдельные файлы...", command=self._export_separate)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close, accelerator="Alt+F4")

        # Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Проверить проект", command=self._validate_project)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

        # Горячие клавиши
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())

    def _create_toolbar(self):
        """Создать панель инструментов"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="Новый", command=self._new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Открыть", command=self._open_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Сохранить", command=self._save_project).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="Импорт из игры", command=self._import_from_game).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Экспорт в игру", command=self._export_to_game).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="Проверить", command=self._validate_project).pack(side=tk.LEFT, padx=2)

    def _create_main_content(self):
        """Создать основное содержимое"""
        # Notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладки
        self.resources_tab = ResourcesTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.resources_tab, text="Ресурсы")

        self.weapons_tab = WeaponsTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.weapons_tab, text="Оружие")

        self.armor_tab = ArmorTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.armor_tab, text="Броня")

        self.jewelry_tab = JewelryTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.jewelry_tab, text="Украшения")

        self.potions_tab = PotionsTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.potions_tab, text="Зелья")

        self.recipes_tab = RecipesTab(self.notebook, self.project, self._mark_modified)
        self.notebook.add(self.recipes_tab, text="Рецепты")

    def _create_statusbar(self):
        """Создать строку состояния"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.statusbar, text="Готово")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.stats_label = ttk.Label(self.statusbar, text="")
        self.stats_label.pack(side=tk.RIGHT, padx=5)

        self._update_stats()

    def _update_stats(self):
        """Обновить статистику"""
        stats = (
            f"Ресурсов: {len(self.project.resources)} | "
            f"Оружия: {len(self.project.weapons)} | "
            f"Брони: {len(self.project.armors)} | "
            f"Украшений: {len(self.project.jewelry)} | "
            f"Зелий: {len(self.project.potions)} | "
            f"Рецептов: {len(self.project.recipes)}"
        )
        self.stats_label.config(text=stats)

    def _update_title(self):
        """Обновить заголовок окна"""
        title = "Items Crafter - Редактор предметов и рецептов"
        if self.project_file:
            title += f" - {os.path.basename(self.project_file)}"
        if self._is_modified:
            title += " *"
        self.root.title(title)

    def _mark_modified(self):
        """Отметить проект как изменённый"""
        self._is_modified = True
        self._update_title()
        self._update_stats()

    def _refresh_all_tabs(self):
        """Обновить все вкладки"""
        self.resources_tab.project = self.project
        self.resources_tab.refresh_list()

        self.weapons_tab.project = self.project
        self.weapons_tab.refresh_list()

        self.armor_tab.project = self.project
        self.armor_tab.refresh_list()

        self.jewelry_tab.project = self.project
        self.jewelry_tab.refresh_list()

        self.potions_tab.project = self.project
        self.potions_tab.refresh_list()

        self.recipes_tab.project = self.project
        self.recipes_tab.refresh_list()

        self._update_stats()

    def _new_project(self):
        """Создать новый проект"""
        if self._is_modified:
            if not messagebox.askyesno("Подтверждение",
                                       "Есть несохранённые изменения. Создать новый проект?"):
                return

        self.project = ItemsCrafterProject()
        self.project_file = None
        self._is_modified = False
        self._refresh_all_tabs()
        self._update_title()
        self.status_label.config(text="Создан новый проект")

    def _open_project(self):
        """Открыть проект"""
        if self._is_modified:
            if not messagebox.askyesno("Подтверждение",
                                       "Есть несохранённые изменения. Открыть другой проект?"):
                return

        filepath = filedialog.askopenfilename(
            title="Открыть проект",
            filetypes=[("Items Crafter Project", "*.icp"), ("JSON", "*.json"), ("Все файлы", "*.*")]
        )

        if filepath:
            project = load_project(filepath)
            if project:
                self.project = project
                self.project_file = filepath
                self._is_modified = False
                self._refresh_all_tabs()
                self._update_title()
                self.status_label.config(text=f"Открыт проект: {filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить проект")

    def _save_project(self):
        """Сохранить проект"""
        if not self.project_file:
            self._save_project_as()
            return

        if save_project(self.project, self.project_file):
            self._is_modified = False
            self._update_title()
            self.status_label.config(text=f"Проект сохранён: {self.project_file}")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить проект")

    def _save_project_as(self):
        """Сохранить проект как..."""
        filepath = filedialog.asksaveasfilename(
            title="Сохранить проект",
            defaultextension=".icp",
            filetypes=[("Items Crafter Project", "*.icp"), ("JSON", "*.json")]
        )

        if filepath:
            self.project_file = filepath
            self._save_project()

    def _try_import_from_game(self):
        """Попытаться автоматически импортировать из игровых конфигов"""
        if os.path.exists(self._game_config_dir):
            items_data = os.path.join(self._game_config_dir, "items_data.json")
            if os.path.exists(items_data):
                if messagebox.askyesno("Импорт",
                                       "Найдены конфиги игры. Импортировать предметы и рецепты?"):
                    self._import_from_game()

    def _import_from_game(self):
        """Импортировать из игровых конфигов"""
        config_dir = filedialog.askdirectory(
            title="Выберите папку с конфигами игры (game/config)",
            initialdir=self._game_config_dir if os.path.exists(self._game_config_dir) else None
        )

        if config_dir:
            project = ItemsImporter.import_from_game(config_dir)
            if project:
                self.project = project
                self._is_modified = True
                self._refresh_all_tabs()
                self._update_title()

                total = (len(project.resources) + len(project.weapons) +
                         len(project.armors) + len(project.jewelry) +
                         len(project.potions))
                self.status_label.config(
                    text=f"Импортировано: {total} предметов, {len(project.recipes)} рецептов"
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось импортировать данные")

    def _export_to_game(self):
        """Экспортировать в игровые конфиги"""
        # Валидация
        errors = self.project.validate()
        if errors:
            if not messagebox.askyesno("Предупреждение",
                                       f"Найдены ошибки:\n" + "\n".join(errors[:5]) +
                                       ("\n..." if len(errors) > 5 else "") +
                                       "\n\nПродолжить экспорт?"):
                return

        config_dir = filedialog.askdirectory(
            title="Выберите папку для экспорта (game/config)",
            initialdir=self._game_config_dir if os.path.exists(self._game_config_dir) else None
        )

        if config_dir:
            exporter = ItemsExporter(self.project)
            results = exporter.export_to_game(config_dir)

            success = all(results.values())
            if success:
                self.status_label.config(text=f"Экспортировано в: {config_dir}")
                messagebox.showinfo("Успех", "Данные успешно экспортированы в игру")
            else:
                failed = [k for k, v in results.items() if not v]
                messagebox.showwarning("Частичный успех",
                                       f"Некоторые файлы не были экспортированы:\n" +
                                       "\n".join(failed))

    def _export_separate(self):
        """Экспортировать в отдельные файлы"""
        output_dir = filedialog.askdirectory(
            title="Выберите папку для экспорта"
        )

        if output_dir:
            exporter = ItemsExporter(self.project)
            results = exporter.export_separate_configs(output_dir)

            success_count = sum(1 for v in results.values() if v)
            self.status_label.config(text=f"Экспортировано {success_count} файлов в: {output_dir}")

            if all(results.values()):
                messagebox.showinfo("Успех", "Все файлы успешно экспортированы")
            else:
                failed = [k for k, v in results.items() if not v]
                messagebox.showwarning("Частичный успех",
                                       f"Некоторые файлы не были экспортированы:\n" +
                                       "\n".join(failed))

    def _validate_project(self):
        """Проверить проект на ошибки"""
        errors = self.project.validate()

        if errors:
            error_text = "\n".join(errors[:20])
            if len(errors) > 20:
                error_text += f"\n\n...и ещё {len(errors) - 20} ошибок"

            messagebox.showwarning("Найдены ошибки",
                                   f"Обнаружено {len(errors)} ошибок:\n\n{error_text}")
        else:
            messagebox.showinfo("Проверка пройдена",
                               "Ошибок не обнаружено!")
            self.status_label.config(text="Проверка пройдена успешно")

    def _show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "О программе",
            "Items Crafter v1.0.0\n\n"
            "Утилита для создания и редактирования\n"
            "предметов и рецептов для Classic RPG.\n\n"
            "Функции:\n"
            "• Редактирование ресурсов\n"
            "• Редактирование оружия с диапазонами параметров\n"
            "• Редактирование брони с диапазонами параметров\n"
            "• Редактирование украшений\n"
            "• Редактирование зелий\n"
            "• Редактирование рецептов крафта\n"
            "• Импорт/экспорт конфигов игры"
        )

    def _on_close(self):
        """Обработка закрытия окна"""
        if self._is_modified:
            result = messagebox.askyesnocancel(
                "Сохранение",
                "Есть несохранённые изменения. Сохранить перед выходом?"
            )
            if result is None:  # Cancel
                return
            if result:  # Yes
                self._save_project()

        self.root.destroy()
