"""
Базовый класс редактора вкладки v2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Tuple, Any
from abc import ABC, abstractmethod

from ..core.config_manager import ConfigManager, clipboard
from ..core.item_models import BaseItem


class BaseEditorTab(ttk.Frame, ABC):
    """
    Базовый класс для вкладок редактора
    Реализует общую логику работы со списком и редактором
    """

    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        on_modified: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.config_manager = config_manager
        self.on_modified = on_modified
        self._current_item_id: Optional[str] = None
        self._is_loading = False

        self._create_layout()

    def _create_layout(self):
        """Создать базовую раскладку: список слева, редактор справа"""
        # Разделитель
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Левая панель - список
        self.left_frame = ttk.Frame(self.paned, width=300)
        self.paned.add(self.left_frame, weight=1)

        # Правая панель - редактор
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=3)

        # Создаём панель списка
        from .widgets import ItemListPanel
        self.list_panel = ItemListPanel(
            self.left_frame,
            on_select=self._on_item_selected,
            on_add=self._on_add_item,
            on_delete=self._on_delete_item,
            on_duplicate=self._on_duplicate_item,
        )
        self.list_panel.pack(fill=tk.BOTH, expand=True)

        # Редактор создаётся в наследниках
        self._create_editor(self.right_frame)

        # Горячие клавиши для буфера обмена на уровне вкладки
        self.bind_all('<Control-c>', self._on_copy_item)
        self.bind_all('<Control-x>', self._on_cut_item)
        self.bind_all('<Control-v>', self._on_paste_item)

    @abstractmethod
    def _create_editor(self, parent: ttk.Frame):
        """Создать форму редактора. Реализуется в наследниках."""
        pass

    @abstractmethod
    def get_items_list(self) -> List[Tuple[str, str]]:
        """Получить список элементов [(id, display_name), ...]"""
        pass

    @abstractmethod
    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        """Найти элемент по ID"""
        pass

    @abstractmethod
    def create_new_item(self) -> Any:
        """Создать новый элемент"""
        pass

    @abstractmethod
    def add_item_to_project(self, item: Any):
        """Добавить элемент в проект"""
        pass

    @abstractmethod
    def remove_item_from_project(self, item_id: str):
        """Удалить элемент из проекта"""
        pass

    @abstractmethod
    def load_item_to_editor(self, item: Any):
        """Загрузить элемент в форму редактора"""
        pass

    @abstractmethod
    def save_item_from_editor(self) -> bool:
        """Сохранить элемент из формы редактора. Возвращает успех."""
        pass

    @abstractmethod
    def get_item_type_name(self) -> str:
        """Получить название типа элемента для буфера обмена"""
        pass

    def refresh_list(self):
        """Обновить список элементов"""
        items = self.get_items_list()
        self.list_panel.set_items(items)

    def _mark_modified(self):
        """Отметить проект как изменённый"""
        if not self._is_loading:
            self.config_manager.mark_modified()
            if self.on_modified:
                self.on_modified()

    def _on_item_selected(self, item_id: str):
        """Обработчик выбора элемента в списке"""
        # Сохраняем текущий элемент
        if self._current_item_id:
            self.save_item_from_editor()

        # Загружаем новый
        item = self.find_item_by_id(item_id)
        if item:
            self._current_item_id = item_id
            self._is_loading = True
            self.load_item_to_editor(item)
            self._is_loading = False

    def _on_add_item(self):
        """Обработчик добавления элемента"""
        # Сохраняем текущий
        if self._current_item_id:
            self.save_item_from_editor()

        # Создаём новый
        new_item = self.create_new_item()
        self.add_item_to_project(new_item)
        self._mark_modified()

        # Обновляем список и выбираем новый элемент
        self.refresh_list()
        self._current_item_id = new_item.item_id if hasattr(new_item, 'item_id') else getattr(new_item, 'recipe_id', '')
        self.list_panel.select_item(self._current_item_id)

        self._is_loading = True
        self.load_item_to_editor(new_item)
        self._is_loading = False

    def _on_delete_item(self, item_id: str):
        """Обработчик удаления элемента"""
        if not messagebox.askyesno("Подтверждение", f"Удалить элемент '{item_id}'?"):
            return

        self.remove_item_from_project(item_id)
        self._mark_modified()

        if self._current_item_id == item_id:
            self._current_item_id = None

        self.refresh_list()

    def _on_duplicate_item(self, item_id: str):
        """Обработчик копирования элемента"""
        item = self.find_item_by_id(item_id)
        if not item:
            return

        # Создаём копию
        if hasattr(item, 'copy'):
            new_item = item.copy()
        else:
            new_item = self.create_new_item()

        # Генерируем новый ID
        base_id = item_id
        counter = 1
        new_id = f"{base_id}_copy"
        while self.find_item_by_id(new_id):
            counter += 1
            new_id = f"{base_id}_copy{counter}"

        if hasattr(new_item, 'item_id'):
            new_item.item_id = new_id
        elif hasattr(new_item, 'recipe_id'):
            new_item.recipe_id = new_id

        self.add_item_to_project(new_item)
        self._mark_modified()

        self.refresh_list()
        self.list_panel.select_item(new_id)

    def _on_copy_item(self, event=None):
        """Копировать текущий элемент в буфер"""
        # Проверяем что фокус на нашей вкладке
        if not self._is_our_focus():
            return

        if self._current_item_id:
            item = self.find_item_by_id(self._current_item_id)
            if item:
                clipboard.copy(item, self.get_item_type_name())

    def _on_cut_item(self, event=None):
        """Вырезать текущий элемент"""
        if not self._is_our_focus():
            return

        if self._current_item_id:
            item = self.find_item_by_id(self._current_item_id)
            if item:
                clipboard.cut(item, self.get_item_type_name())
                self.remove_item_from_project(self._current_item_id)
                self._current_item_id = None
                self._mark_modified()
                self.refresh_list()

    def _on_paste_item(self, event=None):
        """Вставить элемент из буфера"""
        if not self._is_our_focus():
            return

        if not clipboard.has_content:
            return

        if clipboard.content_type != self.get_item_type_name():
            messagebox.showwarning("Ошибка", f"Буфер содержит элемент другого типа: {clipboard.content_type}")
            return

        data = clipboard.paste()
        if data:
            # Создаём элемент из данных
            new_item = self._create_item_from_dict(data)
            if new_item:
                # Генерируем уникальный ID
                base_id = data.get('id', data.get('recipe_id', 'pasted'))
                new_id = self._generate_unique_id(base_id)

                if hasattr(new_item, 'item_id'):
                    new_item.item_id = new_id
                elif hasattr(new_item, 'recipe_id'):
                    new_item.recipe_id = new_id

                self.add_item_to_project(new_item)
                self._mark_modified()
                self.refresh_list()
                self.list_panel.select_item(new_id)

    def _is_our_focus(self) -> bool:
        """Проверить что фокус на нашей вкладке и не в текстовом поле"""
        try:
            focused = self.focus_get()
            if not focused:
                return False
            # Не перехватываем если фокус на текстовом виджете
            if isinstance(focused, (tk.Entry, tk.Text, ttk.Entry, ttk.Spinbox, ttk.Combobox)):
                return False
            widget_class = focused.winfo_class()
            if widget_class in ('Entry', 'Text', 'TEntry', 'TSpinbox', 'TCombobox'):
                return False
            return focused == self or str(focused).startswith(str(self))
        except:
            return False

    def _generate_unique_id(self, base_id: str) -> str:
        """Генерировать уникальный ID"""
        if not self.find_item_by_id(base_id):
            return base_id

        counter = 1
        while True:
            new_id = f"{base_id}_{counter}"
            if not self.find_item_by_id(new_id):
                return new_id
            counter += 1

    @abstractmethod
    def _create_item_from_dict(self, data: dict) -> Optional[Any]:
        """Создать элемент из словаря (для вставки из буфера)"""
        pass
