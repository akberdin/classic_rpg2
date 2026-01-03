"""
Вкладка редактирования рецептов
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import LabeledEntry, LabeledSpinbox, LabeledCombobox, IngredientEditor
from ...models import RecipeData, RecipeIngredient, CraftingStation, RecipeCategory, SkillType, ItemQuality


class RecipesTab(BaseEditorTab):
    """Вкладка для редактирования рецептов"""

    def _create_editor_panel(self):
        """Создать панель редактора"""
        # Создаём прокручиваемую область
        canvas = tk.Canvas(self.editor_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.editor_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Заголовок
        ttk.Label(
            scroll_frame, text="Редактор рецептов",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Основные поля
        main_frame = ttk.LabelFrame(scroll_frame, text="Основные параметры")
        main_frame.pack(fill=tk.X, pady=5, padx=5)

        self.id_entry = LabeledEntry(main_frame, "ID:")
        self.id_entry.pack(fill=tk.X, padx=5, pady=2)

        self.name_entry = LabeledEntry(main_frame, "Название:")
        self.name_entry.pack(fill=tk.X, padx=5, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(main_frame, "Отобр. имя:")
        self.display_name_entry.pack(fill=tk.X, padx=5, pady=2)

        self.description_entry = LabeledEntry(main_frame, "Описание:", width=50)
        self.description_entry.pack(fill=tk.X, padx=5, pady=2)

        # Станция и категория
        station_frame = ttk.Frame(main_frame)
        station_frame.pack(fill=tk.X, padx=5, pady=2)

        stations = list(CraftingStation.get_display_names().values())
        self.station_combo = LabeledCombobox(station_frame, "Станция:", stations)
        self.station_combo.pack(side=tk.LEFT, padx=(0, 20))

        categories = list(RecipeCategory.get_display_names().values())
        self.category_combo = LabeledCombobox(station_frame, "Категория:", categories)
        self.category_combo.pack(side=tk.LEFT)

        # Качество
        qual_frame = ttk.Frame(main_frame)
        qual_frame.pack(fill=tk.X, padx=5, pady=2)

        qualities = list(ItemQuality.get_display_names().values())
        self.quality_combo = LabeledCombobox(qual_frame, "Качество:", qualities)
        self.quality_combo.pack(side=tk.LEFT)

        # Результат
        result_frame = ttk.LabelFrame(scroll_frame, text="Результат крафта")
        result_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(result_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.result_item_entry = LabeledEntry(row1, "ID предмета:", width=25)
        self.result_item_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(row1, text="Выбрать...", command=self._select_result_item).pack(side=tk.LEFT)

        row2 = ttk.Frame(result_frame)
        row2.pack(fill=tk.X, padx=5, pady=2)

        self.result_quantity_spin = LabeledSpinbox(row2, "Количество:", from_=1, to=99)
        self.result_quantity_spin.pack(side=tk.LEFT)

        # Требования
        req_frame = ttk.LabelFrame(scroll_frame, text="Требования")
        req_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(req_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.level_spin = LabeledSpinbox(row1, "Уровень:", from_=1, to=50)
        self.level_spin.pack(side=tk.LEFT, padx=(0, 20))

        skills = list(SkillType.get_display_names().values())
        self.skill_combo = LabeledCombobox(row1, "Навык:", skills)
        self.skill_combo.pack(side=tk.LEFT, padx=(0, 20))

        self.skill_rank_spin = LabeledSpinbox(row1, "Ранг навыка:", from_=1, to=5)
        self.skill_rank_spin.pack(side=tk.LEFT)

        # Цена и спрайт
        price_frame = ttk.Frame(scroll_frame)
        price_frame.pack(fill=tk.X, pady=5, padx=5)

        self.price_spin = LabeledSpinbox(price_frame, "Базовая цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.sprite_entry = LabeledEntry(price_frame, "Спрайт:", width=25)
        self.sprite_entry.pack(side=tk.LEFT)

        # Ингредиенты
        self.ingredients_editor = IngredientEditor(scroll_frame, available_items=[])
        self.ingredients_editor.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # Привязка изменений
        for widget in [self.id_entry, self.display_name_entry, self.description_entry,
                       self.result_item_entry, self.sprite_entry]:
            widget.bind_change(self._mark_modified)

        for widget in [self.result_quantity_spin, self.level_spin, self.skill_rank_spin, self.price_spin]:
            widget.bind_change(self._mark_modified)

        self.station_combo.bind_change(self._mark_modified)
        self.category_combo.bind_change(self._mark_modified)
        self.quality_combo.bind_change(self._mark_modified)
        self.skill_combo.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def _select_result_item(self):
        """Выбор результата из списка предметов"""
        dialog = ItemSelectorDialog(self, self.project)
        self.wait_window(dialog)
        if dialog.result:
            self.result_item_entry.set(dialog.result)
            self._mark_modified()

    def _update_available_items(self):
        """Обновить список доступных предметов для ингредиентов"""
        items = []
        for item in self.project.get_all_items():
            items.append((item.item_id, item.name or item.display_name or item.item_id))
        self.ingredients_editor.set_available_items(items)

    def get_items_list(self) -> List[Any]:
        return self.project.recipes

    def get_item_display_info(self, item) -> tuple:
        return (item.recipe_id, item.name or item.display_name or item.recipe_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.recipes:
            if item.recipe_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        base_id = "new_recipe"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return RecipeData(
            recipe_id=new_id,
            name="Новый рецепт",
            display_name="Рецепт: Новый рецепт",
            description="Описание рецепта",
            quality="common",
            station="workbench",
            category="tool",
            result_item="",
            result_quantity=1,
            required_level=1,
            required_skill="craftsmanship",
            required_skill_rank=1,
            base_price=10,
        )

    def add_item_to_project(self, item):
        self.project.recipes.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.recipes = [r for r in self.project.recipes if r.recipe_id != item_id]

    def load_item_to_editor(self, item: RecipeData):
        """Загрузить рецепт в редактор"""
        # Обновляем список доступных предметов
        self._update_available_items()

        self.id_entry.set(item.recipe_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Станция
        station_keys = list(CraftingStation.get_display_names().keys())
        station_names = list(CraftingStation.get_display_names().values())
        if item.station in station_keys:
            self.station_combo.set(station_names[station_keys.index(item.station)])

        # Категория
        cat_keys = list(RecipeCategory.get_display_names().keys())
        cat_names = list(RecipeCategory.get_display_names().values())
        if item.category in cat_keys:
            self.category_combo.set(cat_names[cat_keys.index(item.category)])

        # Качество
        qual_keys = list(ItemQuality.get_display_names().keys())
        qual_names = list(ItemQuality.get_display_names().values())
        if item.quality in qual_keys:
            self.quality_combo.set(qual_names[qual_keys.index(item.quality)])

        # Навык
        skill_keys = list(SkillType.get_display_names().keys())
        skill_names = list(SkillType.get_display_names().values())
        if item.required_skill in skill_keys:
            self.skill_combo.set(skill_names[skill_keys.index(item.required_skill)])

        self.result_item_entry.set(item.result_item)
        self.result_quantity_spin.set(item.result_quantity)
        self.level_spin.set(item.required_level)
        self.skill_rank_spin.set(item.required_skill_rank)
        self.price_spin.set(item.base_price)
        self.sprite_entry.set(item.sprite or "")

        # Ингредиенты
        ingredients = [{"item": ing.item_id, "quantity": ing.quantity} for ing in item.ingredients]
        self.ingredients_editor.set_ingredients(ingredients)

    def save_item_from_editor(self):
        """Сохранить рецепт из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.recipe_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Станция
        station_names = list(CraftingStation.get_display_names().values())
        station_keys = list(CraftingStation.get_display_names().keys())
        station_name = self.station_combo.get()
        if station_name in station_names:
            item.station = station_keys[station_names.index(station_name)]

        # Категория
        cat_names = list(RecipeCategory.get_display_names().values())
        cat_keys = list(RecipeCategory.get_display_names().keys())
        cat_name = self.category_combo.get()
        if cat_name in cat_names:
            item.category = cat_keys[cat_names.index(cat_name)]

        # Качество
        qual_names = list(ItemQuality.get_display_names().values())
        qual_keys = list(ItemQuality.get_display_names().keys())
        qual_name = self.quality_combo.get()
        if qual_name in qual_names:
            item.quality = qual_keys[qual_names.index(qual_name)]

        # Навык
        skill_names = list(SkillType.get_display_names().values())
        skill_keys = list(SkillType.get_display_names().keys())
        skill_name = self.skill_combo.get()
        if skill_name in skill_names:
            item.required_skill = skill_keys[skill_names.index(skill_name)]

        item.result_item = self.result_item_entry.get()
        item.result_quantity = self.result_quantity_spin.get()
        item.required_level = self.level_spin.get()
        item.required_skill_rank = self.skill_rank_spin.get()
        item.base_price = self.price_spin.get()
        item.sprite = self.sprite_entry.get() or None

        # Ингредиенты
        ingredients_data = self.ingredients_editor.get_ingredients()
        item.ingredients = [
            RecipeIngredient(item_id=ing["item"], quantity=ing["quantity"])
            for ing in ingredients_data
        ]

        self.refresh_list()


class ItemSelectorDialog(tk.Toplevel):
    """Диалог выбора предмета"""

    def __init__(self, parent, project):
        super().__init__(parent)
        self.title("Выбор предмета")
        self.geometry("400x500")
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.project = project

        # Поиск
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_list())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Список
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-1>", lambda e: self._ok())

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Выбрать", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Заполняем список
        self._items = [(item.item_id, item.name or item.display_name or item.item_id)
                       for item in project.get_all_items()]
        self._filtered_items = self._items.copy()
        self._filter_list()

    def _filter_list(self):
        query = self.search_var.get().lower()
        if query:
            self._filtered_items = [
                (id_, name) for id_, name in self._items
                if query in name.lower() or query in id_.lower()
            ]
        else:
            self._filtered_items = self._items.copy()

        self.listbox.delete(0, tk.END)
        for item_id, name in self._filtered_items:
            self.listbox.insert(tk.END, f"{name} [{item_id}]")

    def _ok(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self._filtered_items):
                self.result = self._filtered_items[index][0]
        self.destroy()
