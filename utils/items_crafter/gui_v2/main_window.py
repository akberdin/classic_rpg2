"""
Главное окно Items Crafter v2.0
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from ..core.config_manager import ConfigManager, CrafterConfig, ensure_configs_dir
from ..core.item_templates import TemplatesConfig
from ..core.naming_system import NamingConfig

from .tabs import (
    ResourcesTab, EquipmentTab, ConsumablesTab,
    RecipesTab, TemplatesTab, NamingTab
)


class ItemsCrafterAppV2:
    """Главное приложение Items Crafter v2.0"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Items Crafter v2.0 - Редактор предметов и рецептов")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # Менеджер конфигов
        self.config_manager = ConfigManager()

        # Создаём интерфейс
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_statusbar()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Горячие клавиши
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())

        self._update_title()
        self._update_stats()

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
        file_menu.add_command(label="Экспорт в JSON...", command=self._export_all)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close, accelerator="Alt+F4")

        # Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Вырезать", accelerator="Ctrl+X")
        edit_menu.add_command(label="Копировать", accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Проверить проект", command=self._validate_project)

        # Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Сбросить шаблоны", command=self._reset_templates)
        tools_menu.add_command(label="Сбросить словари нейминга", command=self._reset_naming)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

    def _create_toolbar(self):
        """Создать панель инструментов"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="Новый", command=self._new_project, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Открыть", command=self._open_project, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Сохранить", command=self._save_project, width=10).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="Экспорт", command=self._export_all, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Проверить", command=self._validate_project, width=10).pack(side=tk.LEFT, padx=2)

    def _create_main_content(self):
        """Создать основное содержимое"""
        # Notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладки редактирования предметов
        self.resources_tab = ResourcesTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.resources_tab, text="Ресурсы")

        self.equipment_tab = EquipmentTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.equipment_tab, text="Экипировка")

        self.consumables_tab = ConsumablesTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.consumables_tab, text="Расходники")

        self.recipes_tab = RecipesTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.recipes_tab, text="Рецепты")

        # Вкладки конфигурации
        self.templates_tab = TemplatesTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.templates_tab, text="Шаблоны")

        self.naming_tab = NamingTab(self.notebook, self.config_manager, self._on_modified)
        self.notebook.add(self.naming_tab, text="Нейминг")

    def _create_statusbar(self):
        """Создать строку состояния"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.statusbar, text="Готово")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.stats_label = ttk.Label(self.statusbar, text="")
        self.stats_label.pack(side=tk.RIGHT, padx=5)

    def _on_modified(self):
        """Обработчик изменения данных"""
        self._update_title()
        self._update_stats()

    def _update_title(self):
        """Обновить заголовок окна"""
        title = "Items Crafter v2.0 - Редактор предметов и рецептов"
        if self.config_manager.current_file:
            title += f" - {os.path.basename(str(self.config_manager.current_file))}"
        if self.config_manager.is_modified:
            title += " *"
        self.root.title(title)

    def _update_stats(self):
        """Обновить статистику"""
        # Проверяем что statusbar уже создан
        if not hasattr(self, 'stats_label'):
            return
        project = self.config_manager.project
        stats = (
            f"Ресурсов: {len(project.resources)} | "
            f"Оружия: {len(project.weapons)} | "
            f"Брони: {len(project.armor)} | "
            f"Украшений: {len(project.jewelry)} | "
            f"Расходников: {len(project.consumables)} | "
            f"Рецептов: {len(project.recipes)} | "
            f"Шаблонов: {len(self.config_manager.templates.templates)}"
        )
        self.stats_label.config(text=stats)

    def _refresh_all_tabs(self):
        """Обновить все вкладки"""
        self.resources_tab.refresh_list()
        self.equipment_tab.refresh_list()
        self.consumables_tab.refresh_list()
        self.recipes_tab.refresh_list()
        self.templates_tab.refresh_list()
        self.naming_tab._load_data()
        self._update_stats()

    def _new_project(self):
        """Создать новый проект"""
        if self.config_manager.is_modified:
            if not messagebox.askyesno("Подтверждение",
                                       "Есть несохранённые изменения. Создать новый проект?"):
                return

        self.config_manager.new()
        self._refresh_all_tabs()
        self._update_title()
        self.status_label.config(text="Создан новый проект")

    def _open_project(self):
        """Открыть проект"""
        if self.config_manager.is_modified:
            if not messagebox.askyesno("Подтверждение",
                                       "Есть несохранённые изменения. Открыть другой проект?"):
                return

        configs_dir = ensure_configs_dir()
        filepath = filedialog.askopenfilename(
            title="Открыть проект",
            initialdir=str(configs_dir),
            filetypes=[("Items Crafter Project", "*.json"), ("Все файлы", "*.*")]
        )

        if filepath:
            if self.config_manager.load(filepath):
                self._refresh_all_tabs()
                self._update_title()
                self.status_label.config(text=f"Открыт проект: {filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить проект")

    def _save_project(self):
        """Сохранить проект"""
        # Сохраняем данные нейминга
        self.naming_tab.save_data()

        if not self.config_manager.current_file:
            self._save_project_as()
            return

        if self.config_manager.save():
            self._update_title()
            self.status_label.config(text=f"Проект сохранён: {self.config_manager.current_file}")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить проект")

    def _save_project_as(self):
        """Сохранить проект как..."""
        configs_dir = ensure_configs_dir()
        filepath = filedialog.asksaveasfilename(
            title="Сохранить проект",
            initialdir=str(configs_dir),
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )

        if filepath:
            # Сохраняем данные нейминга
            self.naming_tab.save_data()

            if self.config_manager.save(filepath):
                self._update_title()
                self.status_label.config(text=f"Проект сохранён: {filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить проект")

    def _export_all(self):
        """Экспортировать все конфиги"""
        output_dir = filedialog.askdirectory(title="Выберите папку для экспорта")

        if output_dir:
            # Сохраняем данные нейминга
            self.naming_tab.save_data()

            results = self.config_manager.export_all(output_dir)
            success_count = sum(1 for v in results.values() if v)

            if all(results.values()):
                messagebox.showinfo("Успех", f"Экспортировано {success_count} файлов в: {output_dir}")
            else:
                failed = [k for k, v in results.items() if not v]
                messagebox.showwarning("Частичный успех",
                                       f"Экспортировано {success_count} файлов.\n"
                                       f"Не удалось экспортировать: {', '.join(failed)}")

            self.status_label.config(text=f"Экспортировано в: {output_dir}")

    def _validate_project(self):
        """Проверить проект на ошибки"""
        errors = self.config_manager.validate()

        if errors:
            error_text = "\n".join(errors[:20])
            if len(errors) > 20:
                error_text += f"\n\n...и ещё {len(errors) - 20} ошибок"

            messagebox.showwarning("Найдены ошибки",
                                   f"Обнаружено {len(errors)} ошибок:\n\n{error_text}")
        else:
            messagebox.showinfo("Проверка пройдена", "Ошибок не обнаружено!")
            self.status_label.config(text="Проверка пройдена успешно")

    def _reset_templates(self):
        """Сбросить шаблоны на значения по умолчанию"""
        if messagebox.askyesno("Подтверждение",
                               "Сбросить все шаблоны на значения по умолчанию?"):
            self.config_manager.config.templates = TemplatesConfig.create_default()
            self.templates_tab.refresh_list()
            self.config_manager.mark_modified()
            self._update_title()
            self.status_label.config(text="Шаблоны сброшены")

    def _reset_naming(self):
        """Сбросить словари нейминга на значения по умолчанию"""
        if messagebox.askyesno("Подтверждение",
                               "Сбросить все словари нейминга на значения по умолчанию?"):
            self.config_manager.config.naming = NamingConfig.create_default()
            self.naming_tab._load_data()
            self.config_manager.mark_modified()
            self._update_title()
            self.status_label.config(text="Словари нейминга сброшены")

    def _show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "О программе",
            "Items Crafter v2.0\n\n"
            "Утилита для создания и редактирования\n"
            "предметов и рецептов для Classic RPG.\n\n"
            "Новые возможности v2.0:\n"
            "• Связь предмет-рецепт\n"
            "• Система шаблонов экипировки\n"
            "• Система нейминга через словари\n"
            "• Буфер обмена (Ctrl+C/X/V)\n"
            "• Изолированные конфиги\n\n"
            "Вкладки:\n"
            "• Ресурсы - материалы для крафта\n"
            "• Экипировка - оружие, броня, украшения\n"
            "• Расходники - зелья, еда\n"
            "• Рецепты - крафт со связью\n"
            "• Шаблоны - параметры по качествам\n"
            "• Нейминг - словари имён"
        )

    def _on_close(self):
        """Обработка закрытия окна"""
        if self.config_manager.is_modified:
            result = messagebox.askyesnocancel(
                "Сохранение",
                "Есть несохранённые изменения. Сохранить перед выходом?"
            )
            if result is None:  # Cancel
                return
            if result:  # Yes
                self._save_project()

        self.root.destroy()


def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = ItemsCrafterAppV2(root)
    root.mainloop()


if __name__ == "__main__":
    main()
