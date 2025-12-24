#!/usr/bin/env python3
"""
NPC Config Editor v3.0 - Модульный редактор NPC
Главное окно приложения
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys

# Добавляем путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from .template_editor import TemplateEditor
from .unique_editor import UniqueEditor


class NPCConfigEditor:
    """Главное окно редактора NPC"""

    VERSION = "3.0.0"

    def __init__(self, root):
        self.root = root
        self.root.title(f"NPC Config Editor v{self.VERSION}")

        # Развёрнутое окно
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)

        self.root.minsize(1400, 800)

        # Пути к файлам
        self.assets_path = os.path.join(PROJECT_ROOT, "assets", "actors")
        self.config_path = os.path.join(PROJECT_ROOT, "game", "maps")
        self.npc_config_file = os.path.join(self.config_path, "map1_npc_config.json")
        self.uniq_npc_config_file = os.path.join(self.config_path, "map1_uniq_npc_config.json")

        # Данные
        self.npc_templates = []
        self.unique_npcs = []
        self.has_changes = False

        # Загружаем конфиги
        self.load_configs()

        # Создаём интерфейс
        self._create_ui()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def load_configs(self):
        """Загрузка конфигов"""
        if os.path.exists(self.npc_config_file):
            try:
                with open(self.npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.npc_templates = data.get('templates', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.npc_config_file}: {e}")

        if os.path.exists(self.uniq_npc_config_file):
            try:
                with open(self.uniq_npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unique_npcs = data.get('unique_npcs', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.uniq_npc_config_file}: {e}")

    def save_configs(self):
        """Сохранение конфигов"""
        errors = self._validate_all()
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return False

        os.makedirs(self.config_path, exist_ok=True)

        # Сохранение шаблонов
        npc_data = {
            "_description": "Конфигурация типовых NPC для карты",
            "_version": self.VERSION,
            "templates": self.npc_templates
        }
        with open(self.npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(npc_data, f, ensure_ascii=False, indent=2)

        # Сохранение уникальных NPC
        uniq_data = {
            "_description": "Конфигурация уникальных NPC для карты",
            "_version": self.VERSION,
            "unique_npcs": self.unique_npcs
        }
        with open(self.uniq_npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(uniq_data, f, ensure_ascii=False, indent=2)

        self.has_changes = False
        self._update_title()
        messagebox.showinfo("Сохранено", f"Конфиги сохранены:\n{self.npc_config_file}\n{self.uniq_npc_config_file}")
        return True

    def _validate_all(self):
        """Валидация всех данных"""
        errors = []

        # Проверка дубликатов ID шаблонов
        template_ids = [t.get('id', '') for t in self.npc_templates]
        duplicates = set([x for x in template_ids if template_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID шаблонов: {', '.join(duplicates)}")

        # Проверка дубликатов ID уникальных NPC
        unique_ids = [n.get('id', '') for n in self.unique_npcs]
        duplicates = set([x for x in unique_ids if unique_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID уникальных NPC: {', '.join(duplicates)}")

        # Проверка суммы статов в шаблонах
        for template in self.npc_templates:
            stat_dist = template.get('stat_distribution', {})
            if stat_dist:
                total = sum(stat_dist.values())
                if abs(total - 100) > 0.1:
                    errors.append(f"Шаблон '{template.get('id')}': сумма статов = {total}% (должно быть 100%)")

        return errors

    def _create_ui(self):
        """Создание интерфейса"""
        # Верхняя панель
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Заголовок
        title_label = ttk.Label(top_frame, text=f"NPC Config Editor v{self.VERSION}",
                                font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)

        # Кнопки управления
        ttk.Button(top_frame, text="Выход", command=self._on_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Сохранить", command=self.save_configs).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Перезагрузить", command=self._reload_configs).pack(side=tk.RIGHT, padx=5)

        # Статистика
        self.stats_label = ttk.Label(top_frame, text="", font=('Arial', 10))
        self.stats_label.pack(side=tk.RIGHT, padx=20)
        self._update_stats()

        # Разделитель
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=10)

        # Главный notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Вкладка типовых NPC
        self.template_editor = TemplateEditor(
            self.notebook,
            self.assets_path,
            self.npc_templates,
            on_change_callback=self._on_data_changed
        )
        self.notebook.add(self.template_editor, text="  Типовые NPC  ")

        # Вкладка уникальных NPC
        self.unique_editor = UniqueEditor(
            self.notebook,
            self.assets_path,
            self.unique_npcs,
            on_change_callback=self._on_data_changed
        )
        self.notebook.add(self.unique_editor, text="  Уникальные NPC  ")

        # Статусная строка
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 9)).pack(side=tk.LEFT)

    def _update_stats(self):
        """Обновление статистики"""
        self.stats_label.configure(
            text=f"Шаблонов: {len(self.npc_templates)} | Уникальных: {len(self.unique_npcs)}"
        )

    def _update_title(self):
        """Обновление заголовка окна"""
        title = f"NPC Config Editor v{self.VERSION}"
        if self.has_changes:
            title += " *"
        self.root.title(title)

    def _on_data_changed(self):
        """Обработка изменения данных"""
        self.has_changes = True
        self._update_title()
        self._update_stats()

    def _reload_configs(self):
        """Перезагрузка конфигов"""
        if self.has_changes:
            if not messagebox.askyesno("Подтверждение",
                                        "Есть несохранённые изменения. Перезагрузить?"):
                return

        self.load_configs()
        self.template_editor.templates = self.npc_templates
        self.template_editor.refresh_list()
        self.unique_editor.unique_npcs = self.unique_npcs
        self.unique_editor.refresh_list()

        self.has_changes = False
        self._update_title()
        self._update_stats()
        self.status_var.set("Конфиги перезагружены")

    def _on_close(self):
        """Обработка закрытия окна"""
        if self.has_changes:
            result = messagebox.askyesnocancel(
                "Сохранить изменения?",
                "Есть несохранённые изменения. Сохранить перед выходом?"
            )
            if result is None:  # Cancel
                return
            if result:  # Yes
                if not self.save_configs():
                    return

        self.root.quit()


def main():
    """Главная функция"""
    root = tk.Tk()

    # Настройка стилей
    style = ttk.Style()

    # Выбор темы в зависимости от платформы
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'vista' in available_themes:
        style.theme_use('vista')

    # Настройка шрифтов
    style.configure('TLabel', font=('Arial', 10))
    style.configure('TButton', font=('Arial', 10))
    style.configure('TCheckbutton', font=('Arial', 10))
    style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'))

    # Настройка Notebook
    style.configure('TNotebook.Tab', padding=[12, 4], font=('Arial', 10))

    app = NPCConfigEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
