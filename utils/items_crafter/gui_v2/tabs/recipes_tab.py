"""
Вкладка редактора рецептов v2.0
Поддерживает связь рецепт-предмет
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple, Any

from ..base_editor import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox,
    LabeledCombobox, LabeledCheckbox, LabeledTextarea,
    IngredientEditor
)
from ...core.config_manager import ConfigManager
from ...core.item_models import Recipe, RecipeIngredient
from ...core.enums import ItemQuality, CraftingStation, CraftingSkill


class RecipesTab(BaseEditorTab):
    """Вкладка редактора рецептов"""

    def get_item_type_name(self) -> str:
        return "recipe"

    def get_items_list(self) -> List[Tuple[str, str]]:
        items = []
        for recipe in self.config_manager.project.recipes:
            items.append((recipe.recipe_id, recipe.display_name or recipe.name))
        return items

    def find_item_by_id(self, item_id: str) -> Optional[Recipe]:
        for recipe in self.config_manager.project.recipes:
            if recipe.recipe_id == item_id:
                return recipe
        return None

    def create_new_item(self) -> Recipe:
        base_id = "new_recipe"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return Recipe(
            recipe_id=new_id,
            name="Новый рецепт",
            display_name="Новый рецепт",
            description="",
            result_item_id="",
            result_quantity=1,
            result_quality=ItemQuality.COMMON.value,
            ingredients=[],
            station=CraftingStation.WORKBENCH.value,
            required_skill=CraftingSkill.SMITHING.value,
            required_skill_level=1,
            required_player_level=1,
        )

    def add_item_to_project(self, item: Recipe):
        self.config_manager.project.recipes.append(item)

    def remove_item_from_project(self, item_id: str):
        # Очищаем связи с предметами
        for item in self.config_manager.project.get_all_items():
            if item.recipe_id == item_id:
                item.recipe_id = None

        self.config_manager.project.recipes = [
            r for r in self.config_manager.project.recipes if r.recipe_id != item_id
        ]

    def _create_item_from_dict(self, data: dict) -> Optional[Recipe]:
        try:
            return Recipe.from_dict(data)
        except:
            return None

    def _get_all_items(self) -> List[Tuple[str, str]]:
        """Получить все предметы для выбора в ингредиентах"""
        items = []
        for item in self.config_manager.project.get_all_items():
            items.append((item.item_id, item.display_name or item.name))
        return items

    def _create_editor(self, parent: ttk.Frame):
        """Создать форму редактора рецепта"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.editor_frame = ttk.Frame(canvas)

        self.editor_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # === Основная информация ===
        info_frame = ttk.LabelFrame(self.editor_frame, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.id_entry = LabeledEntry(info_frame, "ID рецепта:")
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

        # === Результат ===
        result_frame = ttk.LabelFrame(self.editor_frame, text="Результат крафта", padding=10)
        result_frame.pack(fill=tk.X, padx=5, pady=5)

        # Выбор предмета-результата
        result_row = ttk.Frame(result_frame)
        result_row.pack(fill=tk.X, pady=2)

        ttk.Label(result_row, text="Предмет:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.result_item_var = tk.StringVar()
        self.result_item_combo = ttk.Combobox(result_row, textvariable=self.result_item_var, state="readonly", width=30)
        self.result_item_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.result_item_combo.bind("<<ComboboxSelected>>", lambda e: self._on_result_item_change())

        ttk.Button(result_row, text="Обновить", command=self._refresh_items_list, width=10).pack(side=tk.LEFT, padx=5)

        self.result_quantity_spin = LabeledSpinbox(result_frame, "Количество:", from_=1, to=999)
        self.result_quantity_spin.pack(fill=tk.X, pady=2)
        self.result_quantity_spin.bind_change(self._mark_modified)

        quality_names = ItemQuality.get_display_names()
        self.result_quality_combo = LabeledCombobox(result_frame, "Качество:", values=list(quality_names.values()))
        self.result_quality_combo.pack(fill=tk.X, pady=2)
        self.result_quality_combo.bind_change(self._mark_modified)
        self._quality_map = {v: k for k, v in quality_names.items()}
        self._quality_map_rev = quality_names

        # Связь с предметом
        link_row = ttk.Frame(result_frame)
        link_row.pack(fill=tk.X, pady=5)

        self.link_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(link_row, text="Связать рецепт с предметом-результатом", variable=self.link_var).pack(side=tk.LEFT)

        # === Ингредиенты ===
        ingredients_frame = ttk.LabelFrame(self.editor_frame, text="Ингредиенты", padding=10)
        ingredients_frame.pack(fill=tk.X, padx=5, pady=5)

        self.ingredients_editor = IngredientEditor(
            ingredients_frame,
            get_items_callback=self._get_all_items,
            on_change=self._mark_modified
        )
        self.ingredients_editor.pack(fill=tk.BOTH, expand=True)

        # === Станция и навык ===
        craft_frame = ttk.LabelFrame(self.editor_frame, text="Параметры крафта", padding=10)
        craft_frame.pack(fill=tk.X, padx=5, pady=5)

        station_names = CraftingStation.get_display_names()
        self.station_combo = LabeledCombobox(craft_frame, "Станция:", values=list(station_names.values()))
        self.station_combo.pack(fill=tk.X, pady=2)
        self.station_combo.bind_change(self._mark_modified)
        self._station_map = {v: k for k, v in station_names.items()}
        self._station_map_rev = station_names

        skill_names = CraftingSkill.get_display_names()
        self.skill_combo = LabeledCombobox(craft_frame, "Навык:", values=list(skill_names.values()))
        self.skill_combo.pack(fill=tk.X, pady=2)
        self.skill_combo.bind_change(self._mark_modified)
        self._skill_map = {v: k for k, v in skill_names.items()}
        self._skill_map_rev = skill_names

        self.skill_level_spin = LabeledSpinbox(craft_frame, "Уровень навыка:", from_=1, to=100)
        self.skill_level_spin.pack(fill=tk.X, pady=2)
        self.skill_level_spin.bind_change(self._mark_modified)

        self.player_level_spin = LabeledSpinbox(craft_frame, "Уровень персонажа:", from_=1, to=100)
        self.player_level_spin.pack(fill=tk.X, pady=2)
        self.player_level_spin.bind_change(self._mark_modified)

        self.craft_time_spin = LabeledFloatSpinbox(craft_frame, "Время крафта (сек):", from_=0.1, to=60.0)
        self.craft_time_spin.pack(fill=tk.X, pady=2)
        self.craft_time_spin.bind_change(self._mark_modified)

        self.experience_spin = LabeledSpinbox(craft_frame, "Опыт за крафт:", from_=0, to=9999)
        self.experience_spin.pack(fill=tk.X, pady=2)
        self.experience_spin.bind_change(self._mark_modified)

        # === Разблокировка ===
        unlock_frame = ttk.LabelFrame(self.editor_frame, text="Разблокировка", padding=10)
        unlock_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unlocked_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(unlock_frame, text="Доступен по умолчанию", variable=self.unlocked_var,
                       command=self._mark_modified).pack(anchor="w", pady=2)

        self.unlock_item_entry = LabeledEntry(unlock_frame, "Предмет разблокировки:")
        self.unlock_item_entry.pack(fill=tk.X, pady=2)
        self.unlock_item_entry.bind_change(self._mark_modified)

        # Инициализация списка предметов
        self._refresh_items_list()

    def _on_name_change(self):
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set("recipe_" + name.lower().replace(" ", "_"))
        if name and not self.display_name_entry.get():
            self.display_name_entry.set(name)
        self._mark_modified()

    def _refresh_items_list(self):
        """Обновить список предметов для выбора результата"""
        items = self._get_all_items()
        item_displays = [f"{name} [{id_}]" for id_, name in items]
        self.result_item_combo["values"] = item_displays
        self._items_list = items

    def _on_result_item_change(self):
        """Обработка выбора предмета-результата"""
        self._mark_modified()

    def load_item_to_editor(self, item: Recipe):
        self.id_entry.set(item.recipe_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_text.set(item.description)

        # Обновляем список предметов
        self._refresh_items_list()

        # Результат
        result_id = item.result_item_id
        for i, (id_, name) in enumerate(self._items_list):
            if id_ == result_id:
                self.result_item_combo.current(i)
                break

        self.result_quantity_spin.set(item.result_quantity)

        quality_display = self._quality_map_rev.get(item.result_quality, "")
        self.result_quality_combo.set(quality_display)

        # Проверяем связь
        result_item = self.config_manager.project.get_item_by_id(result_id)
        if result_item and result_item.recipe_id == item.recipe_id:
            self.link_var.set(True)
        else:
            self.link_var.set(False)

        # Ингредиенты
        ingredients = [{"item_id": ing.item_id, "quantity": ing.quantity} for ing in item.ingredients]
        self.ingredients_editor.set_ingredients(ingredients)

        # Станция и навык
        station_display = self._station_map_rev.get(item.station, "")
        self.station_combo.set(station_display)

        skill_display = self._skill_map_rev.get(item.required_skill, "")
        self.skill_combo.set(skill_display)

        self.skill_level_spin.set(item.required_skill_level)
        self.player_level_spin.set(item.required_player_level)
        self.craft_time_spin.set(item.craft_time)
        self.experience_spin.set(item.experience_gain)

        # Разблокировка
        self.unlocked_var.set(item.is_unlocked_by_default)
        self.unlock_item_entry.set(item.unlock_item_id or "")

    def save_item_from_editor(self) -> bool:
        if not self._current_item_id:
            return False

        item = self.find_item_by_id(self._current_item_id)
        if not item:
            return False

        new_id = self.id_entry.get().strip()
        if not new_id:
            return False

        if new_id != self._current_item_id:
            existing = self.find_item_by_id(new_id)
            if existing:
                return False

        old_id = item.recipe_id
        item.recipe_id = new_id
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_text.get()

        # Результат
        idx = self.result_item_combo.current()
        if idx >= 0 and idx < len(self._items_list):
            item.result_item_id = self._items_list[idx][0]
        else:
            item.result_item_id = ""

        item.result_quantity = self.result_quantity_spin.get()

        quality_display = self.result_quality_combo.get()
        item.result_quality = self._quality_map.get(quality_display, ItemQuality.COMMON.value)

        # Управление связью с предметом
        if self.link_var.get() and item.result_item_id:
            result_item = self.config_manager.project.get_item_by_id(item.result_item_id)
            if result_item:
                result_item.recipe_id = new_id

        # Ингредиенты
        ingredients_data = self.ingredients_editor.get_ingredients()
        item.ingredients = [RecipeIngredient(item_id=ing["item_id"], quantity=ing["quantity"]) for ing in ingredients_data]

        # Станция и навык
        station_display = self.station_combo.get()
        item.station = self._station_map.get(station_display, CraftingStation.WORKBENCH.value)

        skill_display = self.skill_combo.get()
        item.required_skill = self._skill_map.get(skill_display, CraftingSkill.SMITHING.value)

        item.required_skill_level = self.skill_level_spin.get()
        item.required_player_level = self.player_level_spin.get()
        item.craft_time = self.craft_time_spin.get()
        item.experience_gain = self.experience_spin.get()

        # Разблокировка
        item.is_unlocked_by_default = self.unlocked_var.get()
        unlock_item = self.unlock_item_entry.get().strip()
        item.unlock_item_id = unlock_item if unlock_item else None

        # Обновляем связи если ID изменился
        if new_id != old_id:
            for proj_item in self.config_manager.project.get_all_items():
                if proj_item.recipe_id == old_id:
                    proj_item.recipe_id = new_id

            self._current_item_id = new_id
            self.refresh_list()
            self.list_panel.select_item(new_id)

        return True
