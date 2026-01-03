"""
Вкладка редактирования ресурсов
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox, LabeledCombobox
from ...models import ResourceItemData, ResourceCategory, ItemQuality


class ResourcesTab(BaseEditorTab):
    """Вкладка для редактирования ресурсов"""

    def _create_editor_panel(self):
        """Создать панель редактора"""
        # Заголовок
        ttk.Label(
            self.editor_frame, text="Редактор ресурсов",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Основные поля
        main_frame = ttk.LabelFrame(self.editor_frame, text="Основные параметры")
        main_frame.pack(fill=tk.X, pady=5)

        self.id_entry = LabeledEntry(main_frame, "ID:")
        self.id_entry.pack(fill=tk.X, padx=5, pady=2)

        self.name_entry = LabeledEntry(main_frame, "Название:")
        self.name_entry.pack(fill=tk.X, padx=5, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(main_frame, "Отобр. имя:")
        self.display_name_entry.pack(fill=tk.X, padx=5, pady=2)

        self.description_entry = LabeledEntry(main_frame, "Описание:", width=50)
        self.description_entry.pack(fill=tk.X, padx=5, pady=2)

        # Категория и качество
        cat_frame = ttk.Frame(main_frame)
        cat_frame.pack(fill=tk.X, padx=5, pady=2)

        categories = list(ResourceCategory.get_display_names().values())
        self.category_combo = LabeledCombobox(cat_frame, "Категория:", categories)
        self.category_combo.pack(side=tk.LEFT, padx=(0, 20))

        qualities = list(ItemQuality.get_display_names().values())
        self.quality_combo = LabeledCombobox(cat_frame, "Качество:", qualities)
        self.quality_combo.pack(side=tk.LEFT)

        # Параметры
        params_frame = ttk.LabelFrame(self.editor_frame, text="Параметры")
        params_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.tier_spin = LabeledSpinbox(row1, "Уровень:", from_=1, to=10)
        self.tier_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.price_spin = LabeledSpinbox(row1, "Цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.max_stack_spin = LabeledSpinbox(row1, "Макс. стак:", from_=1, to=999)
        self.max_stack_spin.pack(side=tk.LEFT)

        row2 = ttk.Frame(params_frame)
        row2.pack(fill=tk.X, padx=5, pady=2)

        self.weight_spin = LabeledFloatSpinbox(row2, "Вес:", from_=0.01, to=100.0, increment=0.1)
        self.weight_spin.pack(side=tk.LEFT)

        # Спрайт
        sprite_frame = ttk.LabelFrame(self.editor_frame, text="Графика")
        sprite_frame.pack(fill=tk.X, pady=5)

        self.sprite_entry = LabeledEntry(sprite_frame, "Спрайт:")
        self.sprite_entry.pack(fill=tk.X, padx=5, pady=2)

        # Привязка изменений
        for widget in [self.id_entry, self.display_name_entry, self.description_entry,
                       self.sprite_entry]:
            widget.bind_change(self._mark_modified)

        for widget in [self.tier_spin, self.price_spin, self.max_stack_spin, self.weight_spin]:
            widget.bind_change(self._mark_modified)

        self.category_combo.bind_change(self._mark_modified)
        self.quality_combo.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def get_items_list(self) -> List[Any]:
        return self.project.resources

    def get_item_display_info(self, item) -> tuple:
        return (item.item_id, item.name or item.display_name or item.item_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.resources:
            if item.item_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        # Генерируем уникальный ID
        base_id = "new_resource"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return ResourceItemData(
            item_id=new_id,
            name="Новый ресурс",
            display_name="Новый ресурс",
            description="Описание ресурса",
            category="component",
            quality="common",
            tier=1,
            base_price=10,
            max_stack=99,
            weight=0.1,
        )

    def add_item_to_project(self, item):
        self.project.resources.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.resources = [r for r in self.project.resources if r.item_id != item_id]

    def load_item_to_editor(self, item: ResourceItemData):
        """Загрузить ресурс в редактор"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Категория
        categories = list(ResourceCategory.get_display_names().keys())
        cat_names = list(ResourceCategory.get_display_names().values())
        if item.category in categories:
            self.category_combo.set(cat_names[categories.index(item.category)])

        # Качество
        qualities = list(ItemQuality.get_display_names().keys())
        qual_names = list(ItemQuality.get_display_names().values())
        if item.quality in qualities:
            self.quality_combo.set(qual_names[qualities.index(item.quality)])

        self.tier_spin.set(item.tier)
        self.price_spin.set(item.base_price)
        self.max_stack_spin.set(item.max_stack)
        self.weight_spin.set(item.weight)
        self.sprite_entry.set(item.sprite or "")

    def save_item_from_editor(self):
        """Сохранить ресурс из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.item_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Категория
        cat_names = list(ResourceCategory.get_display_names().values())
        categories = list(ResourceCategory.get_display_names().keys())
        cat_name = self.category_combo.get()
        if cat_name in cat_names:
            item.category = categories[cat_names.index(cat_name)]

        # Качество
        qual_names = list(ItemQuality.get_display_names().values())
        qualities = list(ItemQuality.get_display_names().keys())
        qual_name = self.quality_combo.get()
        if qual_name in qual_names:
            item.quality = qualities[qual_names.index(qual_name)]

        item.tier = self.tier_spin.get()
        item.base_price = self.price_spin.get()
        item.max_stack = self.max_stack_spin.get()
        item.weight = self.weight_spin.get()
        item.sprite = self.sprite_entry.get()

        self.refresh_list()
