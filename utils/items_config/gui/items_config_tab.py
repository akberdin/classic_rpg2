"""
Вкладка редактирования items_config.json
Конфигурация системы предметов
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, List

from utils.items_config.models import (
    ItemsConfigManager, QUALITY_LEVELS, ITEM_PARAMETER_TYPES, STATS, PARAMS
)
from utils.items_config.gui.widgets import (
    ScrollableFrame, LabeledEntry, LabeledSpinbox,
    LabeledCombobox, ColorPicker, RangeEditor, ListEditor, DictEditor
)


class ItemsConfigTab(ttk.Frame):
    """Вкладка редактирования конфигурации предметов"""

    def __init__(self, parent, manager: ItemsConfigManager, on_change: Callable = None):
        super().__init__(parent)
        self.manager = manager
        self.on_change = on_change

        self._create_ui()

    def _create_ui(self):
        """Создание интерфейса"""
        # Notebook для подразделов
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладки
        self._create_quality_levels_tab()
        self._create_item_parameters_tab()
        self._create_base_prices_tab()
        self._create_quality_weights_tab()
        self._create_slots_tab()
        self._create_luck_modifiers_tab()
        self._create_weapon_filters_tab()

    def _create_quality_levels_tab(self):
        """Вкладка уровней качества"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Уровни качества")

        # Левая панель - список качеств
        left_frame = ttk.Frame(frame)
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(left_frame, text="Качество:").pack(anchor="w")
        self.quality_listbox = tk.Listbox(left_frame, width=15, height=10, exportselection=False)
        self.quality_listbox.pack(fill="y", expand=True)
        self.quality_listbox.bind("<<ListboxSelect>>", self._on_quality_select)

        # Заполняем список
        qualities = [q.lower() for q in QUALITY_LEVELS]
        for q in qualities:
            self.quality_listbox.insert(tk.END, q)

        # Правая панель - редактор
        right_frame = ttk.Frame(frame)
        right_frame.pack(side="left", fill="both", expand=True)

        self.quality_editor_frame = ttk.LabelFrame(right_frame, text="Параметры качества", padding=10)
        self.quality_editor_frame.pack(fill="both", expand=True)

        # Суффиксы
        ttk.Label(self.quality_editor_frame, text="Суффиксы названий:").pack(anchor="w")
        self.suffixes_frame = ttk.Frame(self.quality_editor_frame)
        self.suffixes_frame.pack(fill="x", pady=5)

        self.suffix_entries = []
        for i in range(3):
            entry = ttk.Entry(self.suffixes_frame, width=20)
            entry.pack(side="left", padx=2)
            self.suffix_entries.append(entry)

        # Цвет
        self.quality_color_picker = ColorPicker(self.quality_editor_frame, "Цвет:")
        self.quality_color_picker.pack(fill="x", pady=5)

        # Кнопка сохранения
        ttk.Button(
            self.quality_editor_frame, text="Сохранить",
            command=self._save_quality_level
        ).pack(pady=10)

        self.current_quality = None

    def _on_quality_select(self, event):
        """Выбор качества"""
        selection = self.quality_listbox.curselection()
        if not selection:
            return

        quality = self.quality_listbox.get(selection[0])
        self.current_quality = quality
        self._load_quality_level(quality)

    def _load_quality_level(self, quality: str):
        """Загрузить данные качества"""
        levels = self.manager.get_quality_levels()
        data = levels.get(quality, {})

        # Суффиксы
        suffixes = data.get("suffixes", ["", "", ""])
        for i, entry in enumerate(self.suffix_entries):
            entry.delete(0, tk.END)
            if i < len(suffixes):
                entry.insert(0, suffixes[i])

        # Цвет
        color = data.get("color", [255, 255, 255])
        self.quality_color_picker.set(color)

    def _save_quality_level(self):
        """Сохранить данные качества"""
        if not self.current_quality:
            return

        suffixes = [e.get().strip() for e in self.suffix_entries if e.get().strip()]
        color = self.quality_color_picker.get()

        data = {
            "suffixes": suffixes,
            "color": color
        }

        self.manager.update_quality_level(self.current_quality, data)
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Данные качества сохранены")

    def _create_item_parameters_tab(self):
        """Вкладка параметров предметов"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Параметры предметов")

        # Верхняя панель выбора
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(select_frame, text="Тип предмета:").pack(side="left")
        self.item_type_var = tk.StringVar()
        self.item_type_combo = ttk.Combobox(
            select_frame, textvariable=self.item_type_var,
            values=ITEM_PARAMETER_TYPES, state="readonly", width=15
        )
        self.item_type_combo.pack(side="left", padx=5)
        self.item_type_combo.bind("<<ComboboxSelected>>", self._on_item_type_select)

        ttk.Label(select_frame, text="Качество:").pack(side="left", padx=(20, 0))
        self.param_quality_var = tk.StringVar()
        self.param_quality_combo = ttk.Combobox(
            select_frame, textvariable=self.param_quality_var,
            values=[q.lower() for q in QUALITY_LEVELS], state="readonly", width=12
        )
        self.param_quality_combo.pack(side="left", padx=5)
        self.param_quality_combo.bind("<<ComboboxSelected>>", self._on_param_quality_select)

        # Scroll frame для редактора
        scroll = ScrollableFrame(frame)
        scroll.pack(fill="both", expand=True)
        self.params_editor_frame = scroll.scrollable_frame

        # Редактор параметров
        self._create_params_editor()

    def _create_params_editor(self):
        """Создание редактора параметров"""
        # Диапазон урона/защиты
        self.damage_range = RangeEditor(
            self.params_editor_frame, "Урон/Защита:", to=100
        )
        self.damage_range.pack(fill="x", pady=2)

        # Количество характеристик
        self.stats_count_range = RangeEditor(
            self.params_editor_frame, "Кол-во характ.:", to=10
        )
        self.stats_count_range.pack(fill="x", pady=2)

        # Количество параметров
        self.params_count_range = RangeEditor(
            self.params_editor_frame, "Кол-во парам.:", to=10
        )
        self.params_count_range.pack(fill="x", pady=2)

        # Количество навыков
        self.skills_count_range = RangeEditor(
            self.params_editor_frame, "Кол-во навыков:", to=5
        )
        self.skills_count_range.pack(fill="x", pady=2)

        ttk.Separator(self.params_editor_frame).pack(fill="x", pady=10)

        # Диапазон бонусов характеристик
        self.stat_bonus_range = RangeEditor(
            self.params_editor_frame, "Бонус характ.:", to=30
        )
        self.stat_bonus_range.pack(fill="x", pady=2)

        # Список доступных характеристик
        self.stat_bonus_list = ListEditor(
            self.params_editor_frame, "Доступные характеристики:",
            available_values=STATS
        )
        self.stat_bonus_list.pack(fill="x", pady=5)

        # Диапазон бонусов параметров
        self.param_bonus_range = RangeEditor(
            self.params_editor_frame, "Бонус парам.:", to=50
        )
        self.param_bonus_range.pack(fill="x", pady=2)

        # Список доступных параметров
        self.param_bonus_list = ListEditor(
            self.params_editor_frame, "Доступные параметры:",
            available_values=PARAMS
        )
        self.param_bonus_list.pack(fill="x", pady=5)

        ttk.Separator(self.params_editor_frame).pack(fill="x", pady=10)

        # Множители цены
        ttk.Label(
            self.params_editor_frame, text="Множители цены:",
            font=("TkDefaultFont", 9, "bold")
        ).pack(anchor="w")

        price_frame = ttk.Frame(self.params_editor_frame)
        price_frame.pack(fill="x", pady=5)

        self.price_per_damage = LabeledSpinbox(
            price_frame, "За урон/защиту:", from_=0, to=10, increment=0.1
        )
        self.price_per_damage.pack(fill="x", pady=2)

        self.price_per_stat = LabeledSpinbox(
            price_frame, "За характ.:", from_=0, to=10, increment=0.1
        )
        self.price_per_stat.pack(fill="x", pady=2)

        self.price_per_param = LabeledSpinbox(
            price_frame, "За параметр:", from_=0, to=10, increment=0.1
        )
        self.price_per_param.pack(fill="x", pady=2)

        self.price_per_skill = LabeledSpinbox(
            price_frame, "За навык:", from_=0, to=10, increment=0.1
        )
        self.price_per_skill.pack(fill="x", pady=2)

        # Кнопка сохранения
        ttk.Button(
            self.params_editor_frame, text="Сохранить параметры",
            command=self._save_item_parameters
        ).pack(pady=10)

    def _on_item_type_select(self, event):
        """Выбор типа предмета"""
        self._load_item_parameters()

    def _on_param_quality_select(self, event):
        """Выбор качества для параметров"""
        self._load_item_parameters()

    def _load_item_parameters(self):
        """Загрузить параметры предмета"""
        item_type = self.item_type_var.get()
        quality = self.param_quality_var.get()

        if not item_type or not quality:
            return

        params = self.manager.get_item_type_parameters(item_type)
        data = params.get(quality, {})

        # Заполняем редактор
        # Диапазон урона/защиты
        damage_key = "damage_range" if "weapon" in item_type else "defense_range"
        self.damage_range.set(data.get(damage_key, [0, 0]))

        self.stats_count_range.set(data.get("stats_count_range", [0, 0]))
        self.params_count_range.set(data.get("params_count_range", [0, 0]))
        self.skills_count_range.set(data.get("skills_count_range", [0, 0]))

        stat_range = data.get("stat_bonus_range")
        self.stat_bonus_range.set(stat_range if stat_range else [0, 0])

        self.stat_bonus_list.set(data.get("stat_bonus_list", []))

        param_range = data.get("param_bonus_range")
        self.param_bonus_range.set(param_range if param_range else [0, 0])

        self.param_bonus_list.set(data.get("param_bonus_list", []))

        # Множители цены
        multipliers = data.get("price_multipliers", {})
        self.price_per_damage.set(multipliers.get("per_damage", 0) or multipliers.get("per_defense", 0))
        self.price_per_stat.set(multipliers.get("per_stat", 0))
        self.price_per_param.set(multipliers.get("per_param_percent", 0))
        self.price_per_skill.set(multipliers.get("per_skill", 0))

    def _save_item_parameters(self):
        """Сохранить параметры предмета"""
        item_type = self.item_type_var.get()
        quality = self.param_quality_var.get()

        if not item_type or not quality:
            messagebox.showwarning("Предупреждение", "Выберите тип предмета и качество")
            return

        damage_key = "damage_range" if "weapon" in item_type else "defense_range"

        stat_range = self.stat_bonus_range.get()
        param_range = self.param_bonus_range.get()

        data = {
            damage_key: self.damage_range.get(),
            "stats_count_range": self.stats_count_range.get(),
            "params_count_range": self.params_count_range.get(),
            "skills_count_range": self.skills_count_range.get(),
            "stat_bonus_range": stat_range if stat_range != [0, 0] else None,
            "stat_bonus_list": self.stat_bonus_list.get(),
            "param_bonus_range": param_range if param_range != [0, 0] else None,
            "param_bonus_list": self.param_bonus_list.get(),
            "skill_bonus_range": None,
            "price_multipliers": {
                "per_damage" if "weapon" in item_type else "per_defense": self.price_per_damage.get(),
                "per_stat": self.price_per_stat.get(),
                "per_param_percent": self.price_per_param.get(),
                "per_skill": self.price_per_skill.get()
            }
        }

        self.manager.update_item_type_quality_params(item_type, quality, data)
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Параметры сохранены")

    def _create_base_prices_tab(self):
        """Вкладка базовых цен"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Базовые цены")

        ttk.Label(
            frame, text="Базовые цены предметов по типам",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.base_prices_editor = DictEditor(
            frame, "",
            data=self.manager.get_base_prices(),
            key_label="Тип предмета",
            value_label="Цена",
            available_keys=ITEM_PARAMETER_TYPES + ["belt", "backpack", "talisman"],
            value_type="int"
        )
        self.base_prices_editor.pack(fill="both", expand=True)

        ttk.Button(
            frame, text="Сохранить цены",
            command=self._save_base_prices
        ).pack(pady=10)

    def _save_base_prices(self):
        """Сохранить базовые цены"""
        prices = self.base_prices_editor.get()
        self.manager.data["base_prices"] = prices
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Базовые цены сохранены")

    def _create_quality_weights_tab(self):
        """Вкладка весов качества"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Веса качества")

        ttk.Label(
            frame, text="Веса для генерации качества предметов",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Выбор категории
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", pady=5)

        ttk.Label(select_frame, text="Категория:").pack(side="left")
        self.weights_category_var = tk.StringVar(value="default")
        self.weights_category_combo = ttk.Combobox(
            select_frame, textvariable=self.weights_category_var,
            values=["default", "jewelry"], state="readonly", width=15
        )
        self.weights_category_combo.pack(side="left", padx=5)
        self.weights_category_combo.bind("<<ComboboxSelected>>", self._on_weights_category_select)

        # Редактор весов
        self.weights_editor = DictEditor(
            frame, "",
            key_label="Качество",
            value_label="Вес",
            available_keys=[q.lower() for q in QUALITY_LEVELS],
            value_type="float"
        )
        self.weights_editor.pack(fill="both", expand=True, pady=10)

        ttk.Button(
            frame, text="Сохранить веса",
            command=self._save_quality_weights
        ).pack(pady=10)

        # Загружаем default
        self._load_quality_weights("default")

    def _on_weights_category_select(self, event):
        """Выбор категории весов"""
        category = self.weights_category_var.get()
        self._load_quality_weights(category)

    def _load_quality_weights(self, category: str):
        """Загрузить веса качества"""
        weights = self.manager.get_quality_weights()
        data = weights.get(category, {})
        # Исключаем комментарии
        clean_data = {k: v for k, v in data.items() if not k.startswith("_")}
        self.weights_editor.set(clean_data)

    def _save_quality_weights(self):
        """Сохранить веса качества"""
        category = self.weights_category_var.get()
        weights = self.weights_editor.get()
        self.manager.update_quality_weights(category, weights)
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Веса качества сохранены")

    def _create_slots_tab(self):
        """Вкладка слотов поясов и рюкзаков"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Слоты")

        # Пояса
        belt_frame = ttk.LabelFrame(frame, text="Слоты поясов [зелья, талисманы]", padding=10)
        belt_frame.pack(fill="x", pady=5)

        self.belt_slots_editors = {}
        belt_slots = self.manager.get_belt_slots()
        for i, quality in enumerate([q.lower() for q in QUALITY_LEVELS]):
            row = ttk.Frame(belt_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{quality}:", width=12).pack(side="left")

            slots = belt_slots.get(quality, [0, 0])

            potions_var = tk.IntVar(value=slots[0] if len(slots) > 0 else 0)
            potions_spin = ttk.Spinbox(row, from_=0, to=10, textvariable=potions_var, width=5)
            potions_spin.pack(side="left", padx=2)

            talismans_var = tk.IntVar(value=slots[1] if len(slots) > 1 else 0)
            talismans_spin = ttk.Spinbox(row, from_=0, to=10, textvariable=talismans_var, width=5)
            talismans_spin.pack(side="left", padx=2)

            self.belt_slots_editors[quality] = (potions_var, talismans_var)

        # Рюкзаки
        backpack_frame = ttk.LabelFrame(frame, text="Слоты рюкзаков", padding=10)
        backpack_frame.pack(fill="x", pady=5)

        self.backpack_slots_editors = {}
        backpack_slots = self.manager.get_backpack_slots()
        for quality in [q.lower() for q in QUALITY_LEVELS]:
            row = ttk.Frame(backpack_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{quality}:", width=12).pack(side="left")

            slots = backpack_slots.get(quality, 0)
            slots_var = tk.IntVar(value=slots)
            slots_spin = ttk.Spinbox(row, from_=0, to=50, textvariable=slots_var, width=5)
            slots_spin.pack(side="left", padx=2)

            self.backpack_slots_editors[quality] = slots_var

        ttk.Button(
            frame, text="Сохранить слоты",
            command=self._save_slots
        ).pack(pady=10)

    def _save_slots(self):
        """Сохранить слоты"""
        # Пояса
        for quality, (potions_var, talismans_var) in self.belt_slots_editors.items():
            self.manager.update_belt_slots(quality, [potions_var.get(), talismans_var.get()])

        # Рюкзаки
        for quality, slots_var in self.backpack_slots_editors.items():
            self.manager.update_backpack_slots(quality, slots_var.get())

        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Слоты сохранены")

    def _create_luck_modifiers_tab(self):
        """Вкладка модификаторов удачи"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Удача")

        scroll = ScrollableFrame(frame)
        scroll.pack(fill="both", expand=True)
        content = scroll.scrollable_frame

        luck = self.manager.get_luck_modifiers()

        ttk.Label(
            content, text="Влияние удачи на генерацию предметов",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Основные параметры
        self.luck_bonus_per_point = LabeledSpinbox(
            content, "Бонус за очко:", from_=0, to=1, increment=0.01,
            value=luck.get("bonus_per_point", 0.01)
        )
        self.luck_bonus_per_point.pack(fill="x", pady=2)

        self.luck_max_bonus = LabeledSpinbox(
            content, "Макс. бонус:", from_=0, to=1, increment=0.05,
            value=luck.get("max_bonus", 0.5)
        )
        self.luck_max_bonus.pack(fill="x", pady=2)

        ttk.Separator(content).pack(fill="x", pady=10)

        # Перераспределение качества
        ttk.Label(content, text="Перераспределение качества:").pack(anchor="w")

        redistr = luck.get("quality_redistribution", {})

        self.luck_poor_reduction = LabeledSpinbox(
            content, "Снижение poor:", from_=0, to=1, increment=0.1,
            value=redistr.get("poor_reduction_factor", 0.1)
        )
        self.luck_poor_reduction.pack(fill="x", pady=2)

        self.luck_common_reduction = LabeledSpinbox(
            content, "Снижение common:", from_=0, to=1, increment=0.1,
            value=redistr.get("common_reduction_factor", 0.5)
        )
        self.luck_common_reduction.pack(fill="x", pady=2)

        self.luck_common_min = LabeledSpinbox(
            content, "Мин. вес common:", from_=0, to=1, increment=0.05,
            value=redistr.get("common_min_weight", 0.2)
        )
        self.luck_common_min.pack(fill="x", pady=2)

        self.luck_poor_min = LabeledSpinbox(
            content, "Мин. вес poor:", from_=0, to=1, increment=0.01,
            value=redistr.get("poor_min_weight", 0.01)
        )
        self.luck_poor_min.pack(fill="x", pady=2)

        ttk.Separator(content).pack(fill="x", pady=10)

        # Доли распределения
        ttk.Label(content, text="Доли распределения бонуса:").pack(anchor="w")

        shares_frame = ttk.Frame(content)
        shares_frame.pack(fill="x", pady=5)

        self.luck_shares = {}
        for quality in ["uncommon", "rare", "epic", "legendary", "artifact"]:
            row = ttk.Frame(shares_frame)
            row.pack(fill="x", pady=1)

            ttk.Label(row, text=f"{quality}:", width=12).pack(side="left")
            var = tk.DoubleVar(value=redistr.get(f"{quality}_share", 0))
            spin = ttk.Spinbox(row, from_=0, to=1, increment=0.05, textvariable=var, width=8)
            spin.pack(side="left")
            self.luck_shares[quality] = var

        ttk.Separator(content).pack(fill="x", pady=10)

        # Дополнительный дроп
        ttk.Label(content, text="Шанс дополнительного предмета:").pack(anchor="w")

        extra = luck.get("extra_drop", {})

        self.luck_extra_chance = LabeledSpinbox(
            content, "Шанс за очко:", from_=0, to=10, increment=0.5,
            value=extra.get("chance_per_point", 1)
        )
        self.luck_extra_chance.pack(fill="x", pady=2)

        self.luck_extra_max = LabeledSpinbox(
            content, "Макс. шанс:", from_=0, to=100, increment=5,
            value=extra.get("max_chance", 30)
        )
        self.luck_extra_max.pack(fill="x", pady=2)

        ttk.Button(
            content, text="Сохранить настройки удачи",
            command=self._save_luck_modifiers
        ).pack(pady=10)

    def _save_luck_modifiers(self):
        """Сохранить модификаторы удачи"""
        modifiers = {
            "bonus_per_point": self.luck_bonus_per_point.get(),
            "max_bonus": self.luck_max_bonus.get(),
            "quality_redistribution": {
                "poor_reduction_factor": self.luck_poor_reduction.get(),
                "common_reduction_factor": self.luck_common_reduction.get(),
                "common_min_weight": self.luck_common_min.get(),
                "poor_min_weight": self.luck_poor_min.get(),
            },
            "extra_drop": {
                "chance_per_point": self.luck_extra_chance.get(),
                "max_chance": self.luck_extra_max.get()
            }
        }

        # Добавляем доли
        for quality, var in self.luck_shares.items():
            modifiers["quality_redistribution"][f"{quality}_share"] = var.get()

        self.manager.update_luck_modifiers(modifiers)
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Настройки удачи сохранены")

    def _create_weapon_filters_tab(self):
        """Вкладка фильтров оружия"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Фильтры оружия")

        ttk.Label(
            frame, text="Фильтры характеристик и параметров для оружия",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        scroll = ScrollableFrame(frame)
        scroll.pack(fill="both", expand=True)
        content = scroll.scrollable_frame

        filters = self.manager.get_weapon_filters()
        stat_filters = filters.get("stat_filters", {})
        param_filters = filters.get("param_filters", {})

        weapon_types = ["sword", "axe", "knife", "spear", "bow", "staff", "wand", "club", "pickaxe"]

        self.weapon_stat_filters = {}
        self.weapon_param_filters = {}

        for wtype in weapon_types:
            wframe = ttk.LabelFrame(content, text=wtype.upper(), padding=5)
            wframe.pack(fill="x", pady=5)

            # Фильтр характеристик
            stat_frame = ttk.Frame(wframe)
            stat_frame.pack(fill="x")

            stat_data = stat_filters.get(wtype, {})
            allowed_stats = stat_data.get("allowed", [])
            excluded_stats = stat_data.get("excluded", [])

            ttk.Label(stat_frame, text="Характеристики:").pack(side="left")

            mode_var = tk.StringVar(
                value="allowed" if allowed_stats else ("excluded" if excluded_stats else "all")
            )
            mode_combo = ttk.Combobox(
                stat_frame, textvariable=mode_var,
                values=["all", "allowed", "excluded"], state="readonly", width=10
            )
            mode_combo.pack(side="left", padx=5)

            stats_var = tk.StringVar(
                value=", ".join(allowed_stats if allowed_stats else excluded_stats)
            )
            stats_entry = ttk.Entry(stat_frame, textvariable=stats_var, width=40)
            stats_entry.pack(side="left", padx=5)

            self.weapon_stat_filters[wtype] = (mode_var, stats_var)

            # Фильтр параметров
            param_frame = ttk.Frame(wframe)
            param_frame.pack(fill="x", pady=2)

            param_data = param_filters.get(wtype, {})
            allowed_params = param_data.get("allowed", [])

            ttk.Label(param_frame, text="Параметры:").pack(side="left")

            pmode_var = tk.StringVar(value="allowed" if allowed_params else "all")
            pmode_combo = ttk.Combobox(
                param_frame, textvariable=pmode_var,
                values=["all", "allowed"], state="readonly", width=10
            )
            pmode_combo.pack(side="left", padx=5)

            params_var = tk.StringVar(value=", ".join(allowed_params))
            params_entry = ttk.Entry(param_frame, textvariable=params_var, width=40)
            params_entry.pack(side="left", padx=5)

            self.weapon_param_filters[wtype] = (pmode_var, params_var)

        ttk.Label(
            content, text="Подсказка: характеристики/параметры через запятую",
            font=("TkDefaultFont", 8)
        ).pack(anchor="w", pady=5)

        ttk.Button(
            content, text="Сохранить фильтры",
            command=self._save_weapon_filters
        ).pack(pady=10)

    def _save_weapon_filters(self):
        """Сохранить фильтры оружия"""
        stat_filters = {}
        param_filters = {}

        for wtype, (mode_var, stats_var) in self.weapon_stat_filters.items():
            mode = mode_var.get()
            stats = [s.strip() for s in stats_var.get().split(",") if s.strip()]

            if mode == "allowed" and stats:
                stat_filters[wtype] = {"allowed": stats}
            elif mode == "excluded" and stats:
                stat_filters[wtype] = {"excluded": stats}

        for wtype, (mode_var, params_var) in self.weapon_param_filters.items():
            mode = mode_var.get()
            params = [p.strip() for p in params_var.get().split(",") if p.strip()]

            if mode == "allowed" and params:
                param_filters[wtype] = {"allowed": params}

        filters = {
            "stat_filters": stat_filters,
            "param_filters": param_filters
        }

        self.manager.update_weapon_filters(filters)
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Успех", "Фильтры оружия сохранены")
