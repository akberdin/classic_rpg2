"""
Базовый класс вкладки редактора
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Callable, Any
from abc import ABC, abstractmethod


class BaseEditorTab(ttk.Frame, ABC):
    """Базовый класс для вкладок редактора предметов"""

    def __init__(self, parent, project, on_modified: Callable):
        super().__init__(parent)
        self.project = project
        self.on_modified = on_modified
        self._current_item = None
        self._is_loading = False

        self._create_layout()
        self._create_list_panel()
        self._create_editor_panel()
        self.refresh_list()

    def _create_layout(self):
        """Создать основную раскладку"""
        # Левая панель - список
        self.list_frame = ttk.Frame(self, width=250)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.list_frame.pack_propagate(False)

        # Правая панель - редактор
        self.editor_frame = ttk.Frame(self)
        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_list_panel(self):
        """Создать панель со списком"""
        from ..widgets import ItemListPanel

        self.list_panel = ItemListPanel(
            self.list_frame,
            on_select=self._on_item_select,
            on_add=self._on_add_item,
            on_delete=self._on_delete_item,
            on_duplicate=self._on_duplicate_item
        )
        self.list_panel.pack(fill=tk.BOTH, expand=True)

    @abstractmethod
    def _create_editor_panel(self):
        """Создать панель редактора - переопределяется в подклассах"""
        pass

    @abstractmethod
    def get_items_list(self) -> List[Any]:
        """Получить список предметов из проекта"""
        pass

    @abstractmethod
    def get_item_display_info(self, item) -> tuple:
        """Получить (id, display_name) для предмета"""
        pass

    @abstractmethod
    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        """Найти предмет по ID"""
        pass

    @abstractmethod
    def create_new_item(self) -> Any:
        """Создать новый предмет"""
        pass

    @abstractmethod
    def add_item_to_project(self, item):
        """Добавить предмет в проект"""
        pass

    @abstractmethod
    def remove_item_from_project(self, item_id: str):
        """Удалить предмет из проекта"""
        pass

    @abstractmethod
    def load_item_to_editor(self, item):
        """Загрузить предмет в редактор"""
        pass

    @abstractmethod
    def save_item_from_editor(self):
        """Сохранить предмет из редактора"""
        pass

    def refresh_list(self):
        """Обновить список предметов"""
        items = self.get_items_list()
        display_items = [self.get_item_display_info(item) for item in items]
        self.list_panel.set_items(display_items)

    def _on_item_select(self, item_id: str):
        """Обработчик выбора предмета"""
        # Сохраняем текущий
        if self._current_item:
            self.save_item_from_editor()

        # Загружаем выбранный
        item = self.find_item_by_id(item_id)
        if item:
            self._current_item = item
            self._is_loading = True
            self.load_item_to_editor(item)
            self._is_loading = False

    def _on_add_item(self):
        """Обработчик добавления предмета"""
        # Сохраняем текущий
        if self._current_item:
            self.save_item_from_editor()

        # Создаём новый
        new_item = self.create_new_item()
        self.add_item_to_project(new_item)
        self.refresh_list()
        self.on_modified()

        # Выбираем новый
        item_id, _ = self.get_item_display_info(new_item)
        self.list_panel.select_item(item_id)
        self._current_item = new_item
        self._is_loading = True
        self.load_item_to_editor(new_item)
        self._is_loading = False

    def _on_delete_item(self, item_id: str):
        """Обработчик удаления предмета"""
        self.remove_item_from_project(item_id)
        self._current_item = None
        self.refresh_list()
        self.on_modified()

    def _on_duplicate_item(self, item_id: str):
        """Обработчик дублирования предмета"""
        import copy
        item = self.find_item_by_id(item_id)
        if item:
            new_item = copy.deepcopy(item)
            # Генерируем новый ID
            base_id = item_id
            counter = 1
            new_id = f"{base_id}_copy{counter}"
            while self.find_item_by_id(new_id):
                counter += 1
                new_id = f"{base_id}_copy{counter}"

            new_item.item_id = new_id
            new_item.name = f"{item.name} (копия)"

            self.add_item_to_project(new_item)
            self.refresh_list()
            self.on_modified()

            self.list_panel.select_item(new_id)

    def _mark_modified(self):
        """Отметить проект как изменённый"""
        if not self._is_loading:
            self.on_modified()

    def _generate_id(self, name: str) -> str:
        """Генерация ID из названия"""
        import re
        # Транслитерация русских букв
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }

        result = name.lower()
        for rus, eng in translit.items():
            result = result.replace(rus, eng)

        # Заменяем пробелы и специальные символы на подчёркивания
        result = re.sub(r'[^a-z0-9]+', '_', result)
        result = result.strip('_')

        return result or "new_item"
