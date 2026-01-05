"""
Вкладка редактирования crafting_config.json
Рецепты и станции крафта
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Dict, Any, List, Optional

from utils.items_config.models import (
    CraftingConfigManager, Recipe,
    CRAFTING_STATIONS, RECIPE_CATEGORIES, CRAFTING_SKILLS, QUALITY_LEVELS
)
from utils.items_config.gui.widgets import (
    ScrollableFrame, LabeledEntry, LabeledSpinbox, LabeledCombobox
)


class CraftingConfigTab(ttk.Frame):
    """Вкладка редактирования конфигурации крафта"""

    def __init__(self, parent, manager: CraftingConfigManager, items_data_manager=None, on_change: Callable = None):
        super().__init__(parent)
        self.manager = manager
        self.items_data_manager = items_data_manager
        self.on_change = on_change
        self.current_recipe_id = None
        self.sort_column = None
        self.sort_reverse = False

        self._create_ui()

    def _create_ui(self):
        """Создание интерфейса"""
        # Notebook для станций и рецептов
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладка станций
        self._create_stations_tab()

        # Вкладка рецептов
        self._create_recipes_tab()

    def _create_stations_tab(self):
        """Вкладка станций крафта"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Станции крафта")

        ttk.Label(
            frame,
            text="Станции крафта определяют, где можно создавать предметы",
            foreground="gray"
        ).pack(anchor="w", pady=(0, 10))

        # Список станций
        self.stations_frame = ttk.Frame(frame)
        self.stations_frame.pack(fill="both", expand=True)

        self.station_entries = {}
        stations = self.manager.get_stations()

        for station_id in CRAFTING_STATIONS:
            station_data = stations.get(station_id, {"name": station_id, "description": ""})

            station_frame = ttk.LabelFrame(self.stations_frame, text=station_id, padding=10)
            station_frame.pack(fill="x", pady=5)

            # Название
            name_frame = ttk.Frame(station_frame)
            name_frame.pack(fill="x")
            ttk.Label(name_frame, text="Название:", width=12).pack(side="left")
            name_var = tk.StringVar(value=station_data.get("name", ""))
            name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
            name_entry.pack(side="left", fill="x", expand=True)

            # Описание
            desc_frame = ttk.Frame(station_frame)
            desc_frame.pack(fill="x", pady=2)
            ttk.Label(desc_frame, text="Описание:", width=12).pack(side="left")
            desc_var = tk.StringVar(value=station_data.get("description", ""))
            desc_entry = ttk.Entry(desc_frame, textvariable=desc_var, width=50)
            desc_entry.pack(side="left", fill="x", expand=True)

            self.station_entries[station_id] = (name_var, desc_var)

        ttk.Button(
            frame, text="Сохранить станции",
            command=self._save_stations
        ).pack(pady=10)

    def _save_stations(self):
        """Сохранить станции"""
        for station_id, (name_var, desc_var) in self.station_entries.items():
            self.manager.update_station(station_id, {
                "name": name_var.get(),
                "description": desc_var.get()
            })

        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Станции сохранены")

    def _create_recipes_tab(self):
        """Вкладка рецептов"""
        frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(frame, text="Рецепты")

        # PanedWindow
        paned = ttk.PanedWindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Левая часть - список рецептов
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Фильтры
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(filter_frame, text="Станция:").pack(side="left")
        self.filter_station_var = tk.StringVar(value="все")
        self.filter_station_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_station_var,
            values=["все"] + CRAFTING_STATIONS, state="readonly", width=15
        )
        self.filter_station_combo.pack(side="left", padx=5)
        self.filter_station_combo.bind("<<ComboboxSelected>>", lambda e: self._load_recipes())

        ttk.Label(filter_frame, text="Категория:").pack(side="left", padx=(10, 0))
        self.filter_category_var = tk.StringVar(value="все")
        self.filter_category_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_category_var,
            values=["все"] + RECIPE_CATEGORIES, state="readonly", width=12
        )
        self.filter_category_combo.pack(side="left", padx=5)
        self.filter_category_combo.bind("<<ComboboxSelected>>", lambda e: self._load_recipes())

        # Поиск
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(search_frame, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_var.trace_add("write", lambda *args: self._load_recipes())

        # Treeview
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True)

        columns = ("id", "name", "station", "category", "level")
        self.recipes_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        for col, text, width in [
            ("id", "ID", 100),
            ("name", "Название", 150),
            ("station", "Станция", 80),
            ("category", "Категория", 80),
            ("level", "Уровень", 60)
        ]:
            self.recipes_tree.heading(col, text=text, command=lambda c=col: self._sort_recipes(c))
            self.recipes_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.recipes_tree.yview)
        self.recipes_tree.configure(yscrollcommand=scrollbar.set)

        self.recipes_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.recipes_tree.bind("<<TreeviewSelect>>", self._on_recipe_select)

        # Кнопки
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self._add_recipe).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Дублировать", command=self._duplicate_recipe).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_recipe).pack(side="left", padx=2)

        # Правая часть - редактор рецепта
        right_frame = ttk.LabelFrame(paned, text="Редактор рецепта", padding=5)
        paned.add(right_frame, weight=1)

        scroll = ScrollableFrame(right_frame)
        scroll.pack(fill="both", expand=True)
        self.editor_frame = scroll.scrollable_frame

        self._create_recipe_editor()
        self._load_recipes()

    def _create_recipe_editor(self):
        """Создание редактора рецепта"""
        # ID
        self.recipe_id_entry = LabeledEntry(self.editor_frame, "ID рецепта:", width=25)
        self.recipe_id_entry.pack(fill="x", pady=2)

        # Название
        self.recipe_name_entry = LabeledEntry(self.editor_frame, "Название:", width=25)
        self.recipe_name_entry.pack(fill="x", pady=2)

        # Отображаемое название
        self.recipe_display_entry = LabeledEntry(self.editor_frame, "Отображение:", width=25)
        self.recipe_display_entry.pack(fill="x", pady=2)

        # Описание
        desc_frame = ttk.Frame(self.editor_frame)
        desc_frame.pack(fill="x", pady=2)
        ttk.Label(desc_frame, text="Описание:", width=15).pack(side="left")
        self.recipe_desc_text = tk.Text(desc_frame, height=3, width=30)
        self.recipe_desc_text.pack(side="left", fill="x", expand=True)

        ttk.Separator(self.editor_frame).pack(fill="x", pady=10)

        # Станция
        self.recipe_station_combo = LabeledCombobox(
            self.editor_frame, "Станция:",
            values=CRAFTING_STATIONS
        )
        self.recipe_station_combo.pack(fill="x", pady=2)

        # Категория
        self.recipe_category_combo = LabeledCombobox(
            self.editor_frame, "Категория:",
            values=RECIPE_CATEGORIES
        )
        self.recipe_category_combo.pack(fill="x", pady=2)

        # Качество
        self.recipe_quality_combo = LabeledCombobox(
            self.editor_frame, "Качество:",
            values=[q.lower() for q in QUALITY_LEVELS]
        )
        self.recipe_quality_combo.pack(fill="x", pady=2)

        ttk.Separator(self.editor_frame).pack(fill="x", pady=10)

        # Результат
        ttk.Label(self.editor_frame, text="Результат:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        self.recipe_result_item = LabeledEntry(self.editor_frame, "ID предмета:", width=20)
        self.recipe_result_item.pack(fill="x", pady=2)

        self.recipe_result_qty = LabeledSpinbox(
            self.editor_frame, "Количество:", from_=1, to=100, increment=1, value=1
        )
        self.recipe_result_qty.pack(fill="x", pady=2)

        ttk.Separator(self.editor_frame).pack(fill="x", pady=10)

        # Требования
        ttk.Label(self.editor_frame, text="Требования:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        self.recipe_req_level = LabeledSpinbox(
            self.editor_frame, "Уровень:", from_=1, to=100, increment=1, value=1
        )
        self.recipe_req_level.pack(fill="x", pady=2)

        self.recipe_req_skill = LabeledCombobox(
            self.editor_frame, "Навык:",
            values=CRAFTING_SKILLS
        )
        self.recipe_req_skill.pack(fill="x", pady=2)

        self.recipe_req_rank = LabeledSpinbox(
            self.editor_frame, "Ранг навыка:", from_=1, to=10, increment=1, value=1
        )
        self.recipe_req_rank.pack(fill="x", pady=2)

        ttk.Separator(self.editor_frame).pack(fill="x", pady=10)

        # Ингредиенты
        ttk.Label(self.editor_frame, text="Ингредиенты:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        self.ingredients_frame = ttk.Frame(self.editor_frame)
        self.ingredients_frame.pack(fill="x", pady=5)

        # Treeview для ингредиентов
        ing_columns = ("item", "quantity")
        self.ingredients_tree = ttk.Treeview(
            self.ingredients_frame, columns=ing_columns, show="headings", height=5
        )
        self.ingredients_tree.heading("item", text="Предмет")
        self.ingredients_tree.heading("quantity", text="Кол-во")
        self.ingredients_tree.column("item", width=150)
        self.ingredients_tree.column("quantity", width=60)
        self.ingredients_tree.pack(fill="x")

        # Добавление ингредиента
        ing_add_frame = ttk.Frame(self.editor_frame)
        ing_add_frame.pack(fill="x", pady=2)

        self.ing_item_var = tk.StringVar()
        ttk.Entry(ing_add_frame, textvariable=self.ing_item_var, width=20).pack(side="left", padx=2)

        self.ing_qty_var = tk.IntVar(value=1)
        ttk.Spinbox(ing_add_frame, from_=1, to=100, textvariable=self.ing_qty_var, width=5).pack(side="left", padx=2)

        ttk.Button(ing_add_frame, text="+", width=3, command=self._add_ingredient).pack(side="left", padx=2)
        ttk.Button(ing_add_frame, text="-", width=3, command=self._remove_ingredient).pack(side="left", padx=2)

        ttk.Separator(self.editor_frame).pack(fill="x", pady=10)

        # Базовая цена
        self.recipe_price = LabeledSpinbox(
            self.editor_frame, "Базовая цена:", from_=0, to=10000, increment=10, value=0
        )
        self.recipe_price.pack(fill="x", pady=2)

        # Кнопка сохранения
        ttk.Button(
            self.editor_frame, text="Сохранить рецепт",
            command=self._save_recipe
        ).pack(fill="x", pady=10)

    def _load_recipes(self):
        """Загрузить рецепты"""
        self.recipes_tree.delete(*self.recipes_tree.get_children())

        recipes = self.manager.get_recipes()
        station_filter = self.filter_station_var.get()
        category_filter = self.filter_category_var.get()
        search = self.search_var.get().lower()

        for r in recipes:
            # Фильтрация
            if station_filter != "все" and r.get("station") != station_filter:
                continue
            if category_filter != "все" and r.get("category") != category_filter:
                continue
            if search and search not in r.get("id", "").lower() and search not in r.get("name", "").lower():
                continue

            self.recipes_tree.insert("", tk.END, iid=r.get("id"),
                                     values=(r.get("id"), r.get("name"),
                                             r.get("station"), r.get("category"),
                                             r.get("required_level", 1)))

    def _sort_recipes(self, column: str):
        """Сортировка рецептов"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        items = [(self.recipes_tree.set(child, column), child)
                 for child in self.recipes_tree.get_children("")]

        # Для уровня - числовая сортировка
        if column == "level":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=self.sort_reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        for index, (_, child) in enumerate(items):
            self.recipes_tree.move(child, "", index)

    def _on_recipe_select(self, event):
        """Выбор рецепта"""
        selection = self.recipes_tree.selection()
        if not selection:
            return

        recipe_id = selection[0]
        self.current_recipe_id = recipe_id
        self._load_recipe_to_editor(recipe_id)

    def _load_recipe_to_editor(self, recipe_id: str):
        """Загрузить рецепт в редактор"""
        recipe = self.manager.get_recipe_by_id(recipe_id)
        if not recipe:
            return

        self.recipe_id_entry.set(recipe.id)
        self.recipe_name_entry.set(recipe.name)
        self.recipe_display_entry.set(recipe.display_name)

        self.recipe_desc_text.delete("1.0", tk.END)
        self.recipe_desc_text.insert("1.0", recipe.description)

        self.recipe_station_combo.set(recipe.station)
        self.recipe_category_combo.set(recipe.category)
        self.recipe_quality_combo.set(recipe.quality)

        self.recipe_result_item.set(recipe.result_item)
        self.recipe_result_qty.set(recipe.result_quantity)

        self.recipe_req_level.set(recipe.required_level)
        self.recipe_req_skill.set(recipe.required_skill)
        self.recipe_req_rank.set(recipe.required_skill_rank)

        self.recipe_price.set(recipe.base_price)

        # Ингредиенты
        self.ingredients_tree.delete(*self.ingredients_tree.get_children())
        for ing in recipe.ingredients:
            self.ingredients_tree.insert("", tk.END, values=(ing.get("item"), ing.get("quantity")))

    def _clear_editor(self):
        """Очистить редактор"""
        self.current_recipe_id = None
        self.recipe_id_entry.set("")
        self.recipe_name_entry.set("")
        self.recipe_display_entry.set("")
        self.recipe_desc_text.delete("1.0", tk.END)
        self.recipe_station_combo.set("workbench")
        self.recipe_category_combo.set("tool")
        self.recipe_quality_combo.set("common")
        self.recipe_result_item.set("")
        self.recipe_result_qty.set(1)
        self.recipe_req_level.set(1)
        self.recipe_req_skill.set("craftsmanship")
        self.recipe_req_rank.set(1)
        self.recipe_price.set(0)
        self.ingredients_tree.delete(*self.ingredients_tree.get_children())

    def _add_ingredient(self):
        """Добавить ингредиент"""
        item = self.ing_item_var.get().strip()
        qty = self.ing_qty_var.get()
        if item:
            self.ingredients_tree.insert("", tk.END, values=(item, qty))
            self.ing_item_var.set("")
            self.ing_qty_var.set(1)

    def _remove_ingredient(self):
        """Удалить ингредиент"""
        selection = self.ingredients_tree.selection()
        if selection:
            self.ingredients_tree.delete(selection[0])

    def _get_ingredients_from_editor(self) -> List[Dict[str, Any]]:
        """Получить ингредиенты из редактора"""
        ingredients = []
        for item in self.ingredients_tree.get_children():
            values = self.ingredients_tree.item(item)["values"]
            ingredients.append({
                "item": values[0],
                "quantity": int(values[1])
            })
        return ingredients

    def _save_recipe(self):
        """Сохранить рецепт"""
        recipe_id = self.recipe_id_entry.get().strip()
        if not recipe_id:
            messagebox.showwarning("Предупреждение", "Введите ID рецепта")
            return

        name = self.recipe_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название рецепта")
            return

        recipe_data = {
            "id": recipe_id,
            "name": name,
            "display_name": self.recipe_display_entry.get().strip(),
            "quality": self.recipe_quality_combo.get(),
            "description": self.recipe_desc_text.get("1.0", tk.END).strip(),
            "station": self.recipe_station_combo.get(),
            "result_item": self.recipe_result_item.get().strip(),
            "result_quantity": self.recipe_result_qty.get_int(),
            "required_level": self.recipe_req_level.get_int(),
            "required_skill": self.recipe_req_skill.get(),
            "required_skill_rank": self.recipe_req_rank.get_int(),
            "ingredients": self._get_ingredients_from_editor(),
            "category": self.recipe_category_combo.get(),
            "base_price": self.recipe_price.get_int(),
            "sprite": None
        }

        if self.current_recipe_id:
            # Обновление существующего
            if recipe_id != self.current_recipe_id:
                # ID изменился - удаляем старый, добавляем новый
                self.manager.delete_recipe(self.current_recipe_id)
                if not self.manager.add_recipe(Recipe.from_dict(recipe_data)):
                    messagebox.showerror("Ошибка", f"ID '{recipe_id}' уже существует")
                    return
            else:
                self.manager.update_recipe(recipe_id, recipe_data)
        else:
            # Новый рецепт
            if not self.manager.add_recipe(Recipe.from_dict(recipe_data)):
                messagebox.showerror("Ошибка", f"ID '{recipe_id}' уже существует")
                return

        self.current_recipe_id = recipe_id
        self._load_recipes()

        # Выбираем сохранённый рецепт
        if recipe_id in self.recipes_tree.get_children():
            self.recipes_tree.selection_set(recipe_id)
            self.recipes_tree.see(recipe_id)

        if self.on_change:
            self.on_change()

    def _add_recipe(self):
        """Добавить новый рецепт"""
        self._clear_editor()
        self.recipe_id_entry.entry.focus_set()

    def _duplicate_recipe(self):
        """Дублировать рецепт"""
        if not self.current_recipe_id:
            messagebox.showwarning("Предупреждение", "Выберите рецепт для дублирования")
            return

        new_id = simpledialog.askstring(
            "Дублирование",
            "Введите ID для нового рецепта:",
            initialvalue=f"{self.current_recipe_id}_copy"
        )

        if not new_id:
            return

        recipe = self.manager.get_recipe_by_id(self.current_recipe_id)
        if recipe:
            new_recipe = Recipe.from_dict(recipe.to_dict())
            new_recipe.id = new_id
            new_recipe.name = f"{recipe.name} (копия)"

            if self.manager.add_recipe(new_recipe):
                self._load_recipes()
                self.recipes_tree.selection_set(new_id)
                self.recipes_tree.see(new_id)
                self.current_recipe_id = new_id
                self._load_recipe_to_editor(new_id)
                if self.on_change:
                    self.on_change()
            else:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")

    def _delete_recipe(self):
        """Удалить рецепт"""
        if not self.current_recipe_id:
            messagebox.showwarning("Предупреждение", "Выберите рецепт для удаления")
            return

        if messagebox.askyesno("Подтверждение",
                               f"Удалить рецепт '{self.current_recipe_id}'?"):
            self.manager.delete_recipe(self.current_recipe_id)
            self._load_recipes()
            self._clear_editor()
            if self.on_change:
                self.on_change()
