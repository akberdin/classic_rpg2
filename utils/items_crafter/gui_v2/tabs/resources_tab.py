"""
Вкладка редактора ресурсов v2.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple, Any

from ..base_editor import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox,
    LabeledCombobox, LabeledCheckbox, LabeledTextarea
)
from ...core.config_manager import ConfigManager
from ...core.item_models import ResourceItem
from ...core.enums import ResourceCategory, ItemQuality, MaterialTier


class ResourcesTab(BaseEditorTab):
    """Вкладка редактора ресурсов"""

    def get_item_type_name(self) -> str:
        return "resource"

    def get_items_list(self) -> List[Tuple[str, str]]:
        items = []
        for resource in self.config_manager.project.resources:
            items.append((resource.item_id, resource.display_name or resource.name))
        return items

    def find_item_by_id(self, item_id: str) -> Optional[ResourceItem]:
        for resource in self.config_manager.project.resources:
            if resource.item_id == item_id:
                return resource
        return None

    def create_new_item(self) -> ResourceItem:
        # Генерируем уникальный ID
        base_id = "new_resource"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return ResourceItem(
            item_id=new_id,
            name="Новый ресурс",
            display_name="Новый ресурс",
            description="",
            quality=ItemQuality.COMMON.value,
            resource_category=ResourceCategory.COMPONENT.value,
            tier=1,
            base_price=1,
            weight=0.1,
            max_stack=99,
        )

    def add_item_to_project(self, item: ResourceItem):
        self.config_manager.project.resources.append(item)

    def remove_item_from_project(self, item_id: str):
        self.config_manager.project.resources = [
            r for r in self.config_manager.project.resources
            if r.item_id != item_id
        ]

    def _create_item_from_dict(self, data: dict) -> Optional[ResourceItem]:
        try:
            return ResourceItem.from_dict(data)
        except:
            return None

    def _create_editor(self, parent: ttk.Frame):
        """Создать форму редактора ресурса"""
        # Прокручиваемая область
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.editor_frame = ttk.Frame(canvas)

        self.editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Основная информация
        info_frame = ttk.LabelFrame(self.editor_frame, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.id_entry = LabeledEntry(info_frame, "ID:")
        self.id_entry.pack(fill=tk.X, pady=2)
        self.id_entry.bind_change(self._mark_modified)

        self.name_entry = LabeledEntry(info_frame, "Имя:")
        self.name_entry.pack(fill=tk.X, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(info_frame, "Отображаемое имя:")
        self.display_name_entry.pack(fill=tk.X, pady=2)
        self.display_name_entry.bind_change(self._mark_modified)

        self.description_text = LabeledTextarea(info_frame, "Описание:", height=3)
        self.description_text.pack(fill=tk.X, pady=2)
        self.description_text.bind_change(self._mark_modified)

        # Категория и качество
        cat_frame = ttk.LabelFrame(self.editor_frame, text="Категория и качество", padding=10)
        cat_frame.pack(fill=tk.X, padx=5, pady=5)

        category_names = ResourceCategory.get_display_names()
        self.category_combo = LabeledCombobox(
            cat_frame, "Категория:",
            values=list(category_names.values())
        )
        self.category_combo.pack(fill=tk.X, pady=2)
        self.category_combo.bind_change(self._mark_modified)
        self._category_map = {v: k for k, v in category_names.items()}
        self._category_map_rev = category_names

        quality_names = ItemQuality.get_display_names()
        self.quality_combo = LabeledCombobox(
            cat_frame, "Качество:",
            values=list(quality_names.values())
        )
        self.quality_combo.pack(fill=tk.X, pady=2)
        self.quality_combo.bind_change(self._mark_modified)
        self._quality_map = {v: k for k, v in quality_names.items()}
        self._quality_map_rev = quality_names

        tier_names = MaterialTier.get_display_names()
        self.tier_combo = LabeledCombobox(
            cat_frame, "Уровень материала:",
            values=[f"{k} - {v}" for k, v in tier_names.items()]
        )
        self.tier_combo.pack(fill=tk.X, pady=2)
        self.tier_combo.bind_change(self._mark_modified)

        # Параметры
        params_frame = ttk.LabelFrame(self.editor_frame, text="Параметры", padding=10)
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        self.price_spin = LabeledSpinbox(params_frame, "Базовая цена:", from_=0, to=99999)
        self.price_spin.pack(fill=tk.X, pady=2)
        self.price_spin.bind_change(self._mark_modified)

        self.weight_spin = LabeledFloatSpinbox(params_frame, "Вес:", from_=0.0, to=999.9)
        self.weight_spin.pack(fill=tk.X, pady=2)
        self.weight_spin.bind_change(self._mark_modified)

        self.max_stack_spin = LabeledSpinbox(params_frame, "Макс. стак:", from_=1, to=9999)
        self.max_stack_spin.pack(fill=tk.X, pady=2)
        self.max_stack_spin.bind_change(self._mark_modified)

        # Связанный рецепт (управляется во вкладке Рецепты)
        recipe_frame = ttk.LabelFrame(self.editor_frame, text="Связанный рецепт", padding=10)
        recipe_frame.pack(fill=tk.X, padx=5, pady=5)

        self.recipe_label = ttk.Label(recipe_frame, text="Рецепт: (не задан)")
        self.recipe_label.pack(fill=tk.X, pady=2)

        ttk.Label(recipe_frame, text="(Связь создаётся во вкладке Рецепты)",
                 foreground="gray").pack(anchor="w")

        ttk.Button(recipe_frame, text="Очистить связь", command=self._clear_recipe).pack(anchor="w", pady=2)

        # Визуал
        visual_frame = ttk.LabelFrame(self.editor_frame, text="Визуал", padding=10)
        visual_frame.pack(fill=tk.X, padx=5, pady=5)

        self.icon_entry = LabeledEntry(visual_frame, "Иконка:")
        self.icon_entry.pack(fill=tk.X, pady=2)
        self.icon_entry.bind_change(self._mark_modified)

        self.sprite_entry = LabeledEntry(visual_frame, "Спрайт:")
        self.sprite_entry.pack(fill=tk.X, pady=2)
        self.sprite_entry.bind_change(self._mark_modified)

    def _on_name_change(self):
        """Автозаполнение ID и display_name при изменении имени"""
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            item_id = name.lower().replace(" ", "_")
            self.id_entry.set(item_id)
        if name and not self.display_name_entry.get():
            self.display_name_entry.set(name)
        self._mark_modified()

    def _clear_recipe(self):
        """Очистить связь с рецептом"""
        if self._current_item_id:
            item = self.find_item_by_id(self._current_item_id)
            if item:
                item.recipe_id = None
                self.recipe_label.config(text="Рецепт: (не задан)")
                self._mark_modified()

    def load_item_to_editor(self, item: ResourceItem):
        """Загрузить ресурс в форму"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_text.set(item.description)

        # Категория
        cat_display = self._category_map_rev.get(item.resource_category, "")
        self.category_combo.set(cat_display)

        # Качество
        quality_display = self._quality_map_rev.get(item.quality, "")
        self.quality_combo.set(quality_display)

        # Tier
        tier_names = MaterialTier.get_display_names()
        tier_display = f"{item.tier} - {tier_names.get(item.tier, '')}"
        self.tier_combo.set(tier_display)

        self.price_spin.set(item.base_price)
        self.weight_spin.set(item.weight)
        self.max_stack_spin.set(item.max_stack)

        # Рецепт
        if item.recipe_id:
            recipe = self.config_manager.project.get_recipe_by_id(item.recipe_id)
            if recipe:
                self.recipe_label.config(text=f"Рецепт: {recipe.display_name} [{recipe.recipe_id}]")
            else:
                self.recipe_label.config(text=f"Рецепт: {item.recipe_id} (не найден)")
        else:
            self.recipe_label.config(text="Рецепт: (не задан)")

        self.icon_entry.set(item.icon)
        self.sprite_entry.set(item.sprite)

    def save_item_from_editor(self) -> bool:
        """Сохранить ресурс из формы"""
        if not self._current_item_id:
            return False

        item = self.find_item_by_id(self._current_item_id)
        if not item:
            return False

        # Получаем новый ID
        new_id = self.id_entry.get().strip()
        if not new_id:
            return False

        # Проверяем уникальность ID если он изменился
        if new_id != self._current_item_id:
            existing = self.find_item_by_id(new_id)
            if existing:
                return False  # ID занят

        item.item_id = new_id
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_text.get()

        # Категория
        cat_display = self.category_combo.get()
        item.resource_category = self._category_map.get(cat_display, ResourceCategory.COMPONENT.value)

        # Качество
        quality_display = self.quality_combo.get()
        item.quality = self._quality_map.get(quality_display, ItemQuality.COMMON.value)

        # Tier
        tier_str = self.tier_combo.get()
        try:
            item.tier = int(tier_str.split(" - ")[0])
        except:
            item.tier = 1

        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()
        item.max_stack = self.max_stack_spin.get()

        item.icon = self.icon_entry.get()
        item.sprite = self.sprite_entry.get()

        # Обновляем текущий ID если он изменился
        if new_id != self._current_item_id:
            self._current_item_id = new_id
            self.refresh_list()
            self.list_panel.select_item(new_id)

        return True
