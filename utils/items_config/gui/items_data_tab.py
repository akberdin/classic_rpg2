"""
Вкладка редактирования items_data.json
Реестр всех предметов игры
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Optional, Callable
import os

from utils.items_config.models import (
    ItemsDataManager, ItemData, ITEM_CATEGORIES,
    WEAPON_TYPES, ARMOR_TYPES, EQUIPMENT_SLOTS,
    QUALITY_LEVELS, POTION_EFFECTS, STATS, PARAMS
)
from utils.items_config.gui.widgets import (
    ScrollableFrame, LabeledEntry, LabeledSpinbox,
    LabeledCombobox, DictEditor, SearchableListbox
)


class ItemsDataTab(ttk.Frame):
    """Вкладка редактирования данных предметов"""

    def __init__(self, parent, manager: ItemsDataManager,
                 crafting_manager=None, on_change: Callable = None,
                 on_navigate_to_recipe: Callable = None):
        super().__init__(parent)
        self.manager = manager
        self.crafting_manager = crafting_manager
        self.on_change = on_change
        self.on_navigate_to_recipe = on_navigate_to_recipe
        self.current_category = None
        self.current_item_id = None
        self.sort_column = None
        self.sort_reverse = False
        self._recipe_cache = {}  # Кэш рецептов для быстрого поиска

        self._build_recipe_cache()
        self._create_ui()
        self._load_categories()

    def _build_recipe_cache(self):
        """Построить кэш рецептов для быстрого поиска по result_item"""
        self._recipe_cache = {}
        if self.crafting_manager:
            recipes = self.crafting_manager.get_recipes()
            for recipe in recipes:
                result_item = recipe.get("result_item")
                if result_item:
                    self._recipe_cache[result_item] = recipe

    def refresh_recipe_cache(self):
        """Обновить кэш рецептов (публичный метод)"""
        self._build_recipe_cache()
        if self.current_category:
            self._load_items()

    def _create_ui(self):
        """Создание интерфейса"""
        # Основной PanedWindow для разделения на 3 части
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Левая панель - категории
        self._create_categories_panel()

        # Средняя панель - список предметов
        self._create_items_panel()

        # Правая панель - редактор предмета
        self._create_editor_panel()

    def _create_categories_panel(self):
        """Панель категорий"""
        categories_frame = ttk.LabelFrame(self.paned, text="Категории", padding=5)
        self.paned.add(categories_frame, weight=1)

        self.categories_listbox = tk.Listbox(categories_frame, exportselection=False)
        self.categories_listbox.pack(fill="both", expand=True)
        self.categories_listbox.bind("<<ListboxSelect>>", self._on_category_select)

    def _create_items_panel(self):
        """Панель списка предметов"""
        items_frame = ttk.LabelFrame(self.paned, text="Предметы", padding=5)
        self.paned.add(items_frame, weight=2)

        # Поиск
        search_frame = ttk.Frame(items_frame)
        search_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(search_frame, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_var.trace_add("write", lambda *args: self._filter_items())

        # Список предметов
        list_frame = ttk.Frame(items_frame)
        list_frame.pack(fill="both", expand=True)

        columns = ("id", "name", "quality", "recipe")
        self.items_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        # Заголовки с сортировкой
        column_config = [
            ("id", "ID", 120),
            ("name", "Название", 140),
            ("quality", "Качество", 70),
            ("recipe", "Рецепт", 60)
        ]
        for col, text, width in column_config:
            self.items_tree.heading(
                col, text=text,
                command=lambda c=col: self._sort_by_column(c)
            )
            self.items_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)

        self.items_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.items_tree.bind("<<TreeviewSelect>>", self._on_item_select)

        # Кнопки управления
        btn_frame = ttk.Frame(items_frame)
        btn_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self._add_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Дублировать", command=self._duplicate_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_item).pack(side="left", padx=2)

    def _create_editor_panel(self):
        """Панель редактора предмета"""
        editor_outer = ttk.LabelFrame(self.paned, text="Редактор", padding=5)
        self.paned.add(editor_outer, weight=3)

        # Scroll frame
        scroll = ScrollableFrame(editor_outer)
        scroll.pack(fill="both", expand=True)
        self.editor_frame = scroll.scrollable_frame

        # ID предмета
        self.id_entry = LabeledEntry(self.editor_frame, "ID предмета:", width=25)
        self.id_entry.pack(fill="x", pady=2)

        # Название
        self.name_entry = LabeledEntry(self.editor_frame, "Название:", width=25)
        self.name_entry.pack(fill="x", pady=2)

        # Цена
        self.value_spinbox = LabeledSpinbox(
            self.editor_frame, "Цена:", from_=0, to=999999, increment=1
        )
        self.value_spinbox.pack(fill="x", pady=2)

        # Вес
        self.weight_spinbox = LabeledSpinbox(
            self.editor_frame, "Вес:", from_=0, to=100, increment=0.1
        )
        self.weight_spinbox.pack(fill="x", pady=2)

        # Качество
        self.quality_combo = LabeledCombobox(
            self.editor_frame, "Качество:",
            values=[""] + QUALITY_LEVELS
        )
        self.quality_combo.pack(fill="x", pady=2)

        # Спрайт
        sprite_frame = ttk.Frame(self.editor_frame)
        sprite_frame.pack(fill="x", pady=2)

        ttk.Label(sprite_frame, text="Спрайт:", width=15, anchor="e").pack(side="left", padx=(0, 5))
        self.sprite_var = tk.StringVar()
        self.sprite_entry = ttk.Entry(sprite_frame, textvariable=self.sprite_var)
        self.sprite_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(
            sprite_frame, text="...", width=3,
            command=self._browse_sprite
        ).pack(side="left", padx=(2, 0))

        # Разделитель
        ttk.Separator(self.editor_frame, orient="horizontal").pack(fill="x", pady=10)

        # === Секция для оружия ===
        self.weapon_frame = ttk.LabelFrame(self.editor_frame, text="Параметры оружия", padding=5)

        self.weapon_type_combo = LabeledCombobox(
            self.weapon_frame, "Тип оружия:",
            values=[""] + WEAPON_TYPES
        )
        self.weapon_type_combo.pack(fill="x", pady=2)

        self.damage_spinbox = LabeledSpinbox(
            self.weapon_frame, "Урон:", from_=0, to=999, increment=1
        )
        self.damage_spinbox.pack(fill="x", pady=2)

        # === Секция для брони ===
        self.armor_frame = ttk.LabelFrame(self.editor_frame, text="Параметры брони", padding=5)

        self.slot_combo = LabeledCombobox(
            self.armor_frame, "Слот:",
            values=[""] + EQUIPMENT_SLOTS
        )
        self.slot_combo.pack(fill="x", pady=2)

        self.armor_type_combo = LabeledCombobox(
            self.armor_frame, "Тип брони:",
            values=[""] + ARMOR_TYPES
        )
        self.armor_type_combo.pack(fill="x", pady=2)

        self.defense_spinbox = LabeledSpinbox(
            self.armor_frame, "Защита:", from_=0, to=999, increment=1
        )
        self.defense_spinbox.pack(fill="x", pady=2)

        # === Секция для зелий ===
        self.potion_frame = ttk.LabelFrame(self.editor_frame, text="Параметры зелья", padding=5)

        self.effect_type_combo = LabeledCombobox(
            self.potion_frame, "Тип эффекта:",
            values=[""] + POTION_EFFECTS
        )
        self.effect_type_combo.pack(fill="x", pady=2)

        self.effect_value_spinbox = LabeledSpinbox(
            self.potion_frame, "Сила эффекта:", from_=0, to=9999, increment=10
        )
        self.effect_value_spinbox.pack(fill="x", pady=2)

        # === Бонусы характеристик ===
        self.stats_frame = ttk.LabelFrame(self.editor_frame, text="Бонусы характеристик", padding=5)

        self.stats_editor = DictEditor(
            self.stats_frame, "",
            available_keys=STATS,
            value_type="int"
        )
        self.stats_editor.pack(fill="x")

        # === Бонусы параметров ===
        self.params_frame = ttk.LabelFrame(self.editor_frame, text="Бонусы параметров", padding=5)

        self.params_editor = DictEditor(
            self.params_frame, "",
            available_keys=PARAMS,
            value_type="int"
        )
        self.params_editor.pack(fill="x")

        # === Секция рецепта ===
        self.recipe_frame = ttk.LabelFrame(self.editor_frame, text="Рецепт крафта", padding=5)

        self.recipe_info_frame = ttk.Frame(self.recipe_frame)
        self.recipe_info_frame.pack(fill="x")

        self.recipe_status_label = ttk.Label(
            self.recipe_info_frame,
            text="Нет рецепта",
            foreground="gray"
        )
        self.recipe_status_label.pack(side="left", fill="x", expand=True)

        self.recipe_btn = ttk.Button(
            self.recipe_info_frame,
            text="Перейти к рецепту",
            command=self._navigate_to_recipe,
            state="disabled"
        )
        self.recipe_btn.pack(side="right")

        # Информация о рецепте
        self.recipe_details_frame = ttk.Frame(self.recipe_frame)
        self.recipe_details_frame.pack(fill="x", pady=(5, 0))

        self.recipe_name_label = ttk.Label(self.recipe_details_frame, text="")
        self.recipe_name_label.pack(anchor="w")

        self.recipe_station_label = ttk.Label(self.recipe_details_frame, text="")
        self.recipe_station_label.pack(anchor="w")

        self.recipe_ingredients_label = ttk.Label(self.recipe_details_frame, text="")
        self.recipe_ingredients_label.pack(anchor="w")

        # Кнопка сохранения
        self.save_btn = ttk.Button(
            self.editor_frame, text="Сохранить изменения",
            command=self._save_current_item
        )
        self.save_btn.pack(fill="x", pady=10)

        # Изначально скрываем специфичные секции
        self._hide_all_sections()

    def _hide_all_sections(self):
        """Скрыть все специфичные секции"""
        self.weapon_frame.pack_forget()
        self.armor_frame.pack_forget()
        self.potion_frame.pack_forget()
        self.stats_frame.pack_forget()
        self.params_frame.pack_forget()
        self.recipe_frame.pack_forget()

    def _show_sections_for_category(self, category: str):
        """Показать секции для категории"""
        self._hide_all_sections()

        if category == "weapons":
            self.weapon_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.stats_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.params_frame.pack(fill="x", pady=5, before=self.save_btn)
        elif category == "armor":
            self.armor_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.stats_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.params_frame.pack(fill="x", pady=5, before=self.save_btn)
        elif category == "jewelry":
            self.armor_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.stats_frame.pack(fill="x", pady=5, before=self.save_btn)
            self.params_frame.pack(fill="x", pady=5, before=self.save_btn)
        elif category == "potions":
            self.potion_frame.pack(fill="x", pady=5, before=self.save_btn)

        # Секция рецепта показывается всегда (для всех категорий)
        self.recipe_frame.pack(fill="x", pady=5, before=self.save_btn)

    def _load_categories(self):
        """Загрузить категории"""
        self.categories_listbox.delete(0, tk.END)
        for cat_id, cat_name in ITEM_CATEGORIES.items():
            self.categories_listbox.insert(tk.END, f"{cat_name} ({cat_id})")

    def _on_category_select(self, event):
        """Обработка выбора категории"""
        selection = self.categories_listbox.curselection()
        if not selection:
            return

        # Извлекаем ID категории из строки
        text = self.categories_listbox.get(selection[0])
        # Формат: "Название (id)"
        cat_id = text.split("(")[-1].rstrip(")")

        self.current_category = cat_id
        self._load_items()
        self._show_sections_for_category(cat_id)
        self._clear_editor()

    def _load_items(self):
        """Загрузить предметы текущей категории"""
        self.items_tree.delete(*self.items_tree.get_children())

        if not self.current_category:
            return

        items = self.manager.get_items_in_category(self.current_category)
        for item in items:
            quality = item.quality or ""
            has_recipe = "Да" if item.item_id in self._recipe_cache else ""
            self.items_tree.insert("", tk.END, iid=item.item_id,
                                   values=(item.item_id, item.name, quality, has_recipe))

    def _sort_by_column(self, column: str):
        """Сортировка по столбцу"""
        # Переключаем направление, если тот же столбец
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Получаем все элементы
        items = [(self.items_tree.set(child, column), child)
                 for child in self.items_tree.get_children("")]

        # Сортируем
        items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        # Переставляем элементы
        for index, (_, child) in enumerate(items):
            self.items_tree.move(child, "", index)

        # Обновляем заголовок с индикатором сортировки
        column_names = {"id": "ID", "name": "Название", "quality": "Качество", "recipe": "Рецепт"}
        for col in column_names:
            text = column_names[col]
            if col == column:
                arrow = " ▼" if self.sort_reverse else " ▲"
                text += arrow
            self.items_tree.heading(col, text=text)

    def _filter_items(self):
        """Фильтрация предметов по поиску"""
        search = self.search_var.get().lower()
        self.items_tree.delete(*self.items_tree.get_children())

        if not self.current_category:
            return

        items = self.manager.get_items_in_category(self.current_category)
        for item in items:
            if search in item.item_id.lower() or search in item.name.lower():
                quality = item.quality or ""
                has_recipe = "Да" if item.item_id in self._recipe_cache else ""
                self.items_tree.insert("", tk.END, iid=item.item_id,
                                       values=(item.item_id, item.name, quality, has_recipe))

    def _on_item_select(self, event):
        """Обработка выбора предмета"""
        selection = self.items_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        self.current_item_id = item_id
        self._load_item_to_editor(item_id)

    def _load_item_to_editor(self, item_id: str):
        """Загрузить предмет в редактор"""
        item = self.manager.get_item(self.current_category, item_id)
        if not item:
            return

        # Базовые поля
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.value_spinbox.set(item.value)
        self.weight_spinbox.set(item.weight)
        self.quality_combo.set(item.quality or "")
        self.sprite_var.set(item.sprite or "")

        # Оружие
        self.weapon_type_combo.set(item.weapon_type or "")
        self.damage_spinbox.set(item.damage or 0)

        # Броня
        self.slot_combo.set(item.slot or "")
        self.armor_type_combo.set(item.armor_type or "")
        self.defense_spinbox.set(item.defense or 0)

        # Зелья
        self.effect_type_combo.set(item.effect_type or "")
        self.effect_value_spinbox.set(item.effect_value or 0)

        # Бонусы
        self.stats_editor.set(item.stats_bonus)
        self.params_editor.set(item.param_bonus)

        # Информация о рецепте
        self._update_recipe_info(item_id)

    def _clear_editor(self):
        """Очистить редактор"""
        self.current_item_id = None
        self.id_entry.set("")
        self.name_entry.set("")
        self.value_spinbox.set(0)
        self.weight_spinbox.set(0)
        self.quality_combo.set("")
        self.sprite_var.set("")
        self.weapon_type_combo.set("")
        self.damage_spinbox.set(0)
        self.slot_combo.set("")
        self.armor_type_combo.set("")
        self.defense_spinbox.set(0)
        self.effect_type_combo.set("")
        self.effect_value_spinbox.set(0)
        self.stats_editor.set({})
        self.params_editor.set({})
        self._clear_recipe_info()

    def _save_current_item(self):
        """Сохранить текущий предмет"""
        if not self.current_category:
            messagebox.showwarning("Предупреждение", "Выберите категорию")
            return

        new_id = self.id_entry.get().strip()
        if not new_id:
            messagebox.showwarning("Предупреждение", "Введите ID предмета")
            return

        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название предмета")
            return

        # Формируем данные предмета
        item_data = {"name": name}

        value = self.value_spinbox.get_int()
        if value > 0:
            item_data["value"] = value

        weight = self.weight_spinbox.get()
        if weight > 0:
            item_data["weight"] = weight

        quality = self.quality_combo.get()
        if quality:
            item_data["quality"] = quality

        sprite = self.sprite_var.get().strip()
        if sprite:
            item_data["sprite"] = sprite

        # Оружие
        if self.current_category == "weapons":
            weapon_type = self.weapon_type_combo.get()
            if weapon_type:
                item_data["weapon_type"] = weapon_type
            damage = self.damage_spinbox.get_int()
            if damage > 0:
                item_data["damage"] = damage

        # Броня / Украшения
        if self.current_category in ("armor", "jewelry"):
            slot = self.slot_combo.get()
            if slot:
                item_data["slot"] = slot
            armor_type = self.armor_type_combo.get()
            if armor_type:
                item_data["armor_type"] = armor_type
            defense = self.defense_spinbox.get_int()
            if defense > 0:
                item_data["defense"] = defense

        # Зелья
        if self.current_category == "potions":
            effect_type = self.effect_type_combo.get()
            if effect_type:
                item_data["effect_type"] = effect_type
            effect_value = self.effect_value_spinbox.get_int()
            if effect_value > 0:
                item_data["effect_value"] = effect_value

        # Бонусы (для оружия, брони, украшений)
        if self.current_category in ("weapons", "armor", "jewelry"):
            stats = self.stats_editor.get()
            if stats:
                item_data["stats_bonus"] = stats
            params = self.params_editor.get()
            if params:
                item_data["param_bonus"] = params

        # Проверяем, это обновление или создание
        if self.current_item_id:
            # Если ID изменился - переименовываем
            if new_id != self.current_item_id:
                if not self.manager.rename_item(self.current_category, self.current_item_id, new_id):
                    messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                    return

            self.manager.update_item(self.current_category, new_id, item_data)
        else:
            # Новый предмет
            if not self.manager.add_item(self.current_category, new_id, item_data):
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                return

        self.current_item_id = new_id
        self._load_items()

        # Выбираем сохранённый предмет
        self.items_tree.selection_set(new_id)
        self.items_tree.see(new_id)

        if self.on_change:
            self.on_change()

    def _add_item(self):
        """Добавить новый предмет"""
        if not self.current_category:
            messagebox.showwarning("Предупреждение", "Выберите категорию")
            return

        self._clear_editor()
        self.id_entry.entry.focus_set()

    def _duplicate_item(self):
        """Дублировать выбранный предмет"""
        if not self.current_item_id:
            messagebox.showwarning("Предупреждение", "Выберите предмет для дублирования")
            return

        new_id = simpledialog.askstring(
            "Дублирование",
            "Введите ID для нового предмета:",
            initialvalue=f"{self.current_item_id}_copy"
        )

        if not new_id:
            return

        item = self.manager.get_item(self.current_category, self.current_item_id)
        if item:
            if self.manager.add_item(self.current_category, new_id, item.to_dict()):
                self._load_items()
                self.items_tree.selection_set(new_id)
                self.items_tree.see(new_id)
                self.current_item_id = new_id
                self._load_item_to_editor(new_id)
                if self.on_change:
                    self.on_change()
            else:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")

    def _delete_item(self):
        """Удалить выбранный предмет"""
        if not self.current_item_id:
            messagebox.showwarning("Предупреждение", "Выберите предмет для удаления")
            return

        if messagebox.askyesno("Подтверждение",
                               f"Удалить предмет '{self.current_item_id}'?"):
            self.manager.delete_item(self.current_category, self.current_item_id)
            self._load_items()
            self._clear_editor()
            if self.on_change:
                self.on_change()

    def _browse_sprite(self):
        """Выбрать файл спрайта"""
        # Определяем начальную директорию (assets/sprites если существует)
        initial_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        ))))
        sprites_dir = os.path.join(initial_dir, "assets", "sprites")
        if not os.path.exists(sprites_dir):
            sprites_dir = os.path.join(initial_dir, "assets")
        if not os.path.exists(sprites_dir):
            sprites_dir = initial_dir

        filepath = filedialog.askopenfilename(
            title="Выберите спрайт",
            initialdir=sprites_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG", "*.png"),
                ("Все файлы", "*.*")
            ]
        )

        if filepath:
            # Преобразуем в относительный путь от корня проекта
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)
                ))))
                rel_path = os.path.relpath(filepath, project_root)
                # Используем прямые слэши для совместимости
                rel_path = rel_path.replace("\\", "/")
                self.sprite_var.set(rel_path)
            except ValueError:
                # Если не удалось сделать относительный путь, используем абсолютный
                self.sprite_var.set(filepath)

    def _find_recipe_for_item(self, item_id: str):
        """Найти рецепт для предмета (использует кэш)"""
        return self._recipe_cache.get(item_id)

    def _update_recipe_info(self, item_id: str):
        """Обновить информацию о рецепте"""
        self.current_recipe = self._find_recipe_for_item(item_id)

        if self.current_recipe:
            self.recipe_status_label.config(
                text="Рецепт найден",
                foreground="green"
            )
            self.recipe_btn.config(state="normal")

            # Показываем детали
            self.recipe_name_label.config(
                text=f"Название: {self.current_recipe.get('name', 'N/A')}"
            )
            station = self.current_recipe.get('station', 'N/A')
            station_name = {
                'workbench': 'Мастерская',
                'forge': 'Кузница',
                'alchemy_table': 'Алхимический стол',
                'enchanting_table': 'Стол зачарования'
            }.get(station, station)
            self.recipe_station_label.config(text=f"Станция: {station_name}")

            # Ингредиенты
            ingredients = self.current_recipe.get('ingredients', [])
            if ingredients:
                ing_text = "Ингредиенты: " + ", ".join(
                    f"{ing.get('item', '?')} x{ing.get('quantity', 1)}"
                    for ing in ingredients
                )
            else:
                ing_text = "Ингредиенты: нет"
            self.recipe_ingredients_label.config(text=ing_text)

            self.recipe_details_frame.pack(fill="x", pady=(5, 0))
        else:
            self.recipe_status_label.config(
                text="Нет рецепта для этого предмета",
                foreground="gray"
            )
            self.recipe_btn.config(state="disabled")
            self.recipe_name_label.config(text="")
            self.recipe_station_label.config(text="")
            self.recipe_ingredients_label.config(text="")
            self.recipe_details_frame.pack_forget()

    def _clear_recipe_info(self):
        """Очистить информацию о рецепте"""
        self.current_recipe = None
        self.recipe_status_label.config(
            text="Нет рецепта",
            foreground="gray"
        )
        self.recipe_btn.config(state="disabled")
        self.recipe_name_label.config(text="")
        self.recipe_station_label.config(text="")
        self.recipe_ingredients_label.config(text="")
        self.recipe_details_frame.pack_forget()

    def _navigate_to_recipe(self):
        """Перейти к рецепту"""
        if self.current_recipe and self.on_navigate_to_recipe:
            self.on_navigate_to_recipe(self.current_recipe.get('id'))
