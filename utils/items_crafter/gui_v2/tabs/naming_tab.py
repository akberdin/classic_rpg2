"""
Вкладка редактора словарей нейминга v2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List

from ..widgets import LabeledEntry, LabeledTextarea, ClipboardEntry, ClipboardText
from ...core.config_manager import ConfigManager
from ...core.naming_system import NamingDictionary, NamingConfig


class NamingTab(ttk.Frame):
    """Вкладка редактора словарей нейминга"""

    def __init__(self, parent, config_manager: ConfigManager, on_modified=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.config_manager = config_manager
        self.on_modified = on_modified
        self._is_loading = False

        self._create_layout()
        self._load_data()

    def _mark_modified(self):
        if not self._is_loading:
            self.config_manager.mark_modified()
            if self.on_modified:
                self.on_modified()

    def _create_layout(self):
        # Notebook для разных словарей
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка префиксов качества
        self._create_quality_prefixes_tab()

        # Вкладка материалов
        self._create_materials_tab()

        # Вкладка названий оружия
        self._create_weapon_names_tab()

        # Вкладка названий брони
        self._create_equipment_names_tab()

        # Вкладка суффиксов
        self._create_suffixes_tab()

        # Вкладка ресурсов
        self._create_resource_names_tab()

    def _create_quality_prefixes_tab(self):
        """Вкладка редактирования префиксов качества"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Префиксы качества")

        ttk.Label(frame, text="Префиксы для каждого уровня качества (по одному на строку):").pack(anchor="w", pady=(0, 10))

        self._quality_prefix_widgets = {}
        qualities = ["poor", "common", "uncommon", "rare", "epic", "legendary", "artifact"]
        quality_names = {
            "poor": "Плохое",
            "common": "Обычное",
            "uncommon": "Необычное",
            "rare": "Редкое",
            "epic": "Эпическое",
            "legendary": "Легендарное",
            "artifact": "Артефакт",
        }

        for quality in qualities:
            q_frame = ttk.LabelFrame(frame, text=quality_names[quality], padding=5)
            q_frame.pack(fill=tk.X, pady=2)

            text = ClipboardText(q_frame, height=2, width=50)
            text.pack(fill=tk.X)
            text.bind("<<Modified>>", lambda e, t=text: self._on_text_modified(t))
            self._quality_prefix_widgets[quality] = text

    def _create_materials_tab(self):
        """Вкладка редактирования названий материалов"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Материалы")

        ttk.Label(frame, text="Названия материалов по уровням (tier):").pack(anchor="w", pady=(0, 10))

        # Создаём notebook для тиров
        tier_notebook = ttk.Notebook(frame)
        tier_notebook.pack(fill=tk.BOTH, expand=True)

        self._material_widgets = {}
        categories = ["metal", "wood", "leather", "cloth", "gem"]
        category_names = {
            "metal": "Металл",
            "wood": "Дерево",
            "leather": "Кожа",
            "cloth": "Ткань",
            "gem": "Камень",
        }

        for tier in range(1, 6):
            tier_frame = ttk.Frame(tier_notebook, padding=10)
            tier_notebook.add(tier_frame, text=f"Tier {tier}")

            self._material_widgets[tier] = {}
            for cat in categories:
                row = ttk.Frame(tier_frame)
                row.pack(fill=tk.X, pady=2)

                ttk.Label(row, text=f"{category_names[cat]}:", width=10).pack(side=tk.LEFT)
                entry = ClipboardEntry(row, width=30)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                entry.bind("<KeyRelease>", lambda e: self._mark_modified())
                self._material_widgets[tier][cat] = entry

    def _create_weapon_names_tab(self):
        """Вкладка редактирования названий оружия"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Оружие")

        ttk.Label(frame, text="Названия типов оружия:").pack(anchor="w", pady=(0, 10))

        self._weapon_name_widgets = {}
        weapons = [
            ("dagger", "Кинжал"), ("sword", "Меч"), ("axe", "Топор"), ("mace", "Булава"),
            ("greatsword", "Двуручный меч"), ("greataxe", "Двуручный топор"),
            ("spear", "Копьё"), ("staff_melee", "Боевой посох"),
            ("bow", "Лук"), ("crossbow", "Арбалет"),
            ("wand", "Жезл"), ("staff_magic", "Магический посох"), ("orb", "Сфера"),
        ]

        for weapon_id, default_name in weapons:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{weapon_id}:", width=15).pack(side=tk.LEFT)
            entry = ClipboardEntry(row, width=30)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.insert(0, default_name)
            entry.bind("<KeyRelease>", lambda e: self._mark_modified())
            self._weapon_name_widgets[weapon_id] = entry

    def _create_equipment_names_tab(self):
        """Вкладка редактирования названий экипировки"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Экипировка")

        ttk.Label(frame, text="Названия типов экипировки:").pack(anchor="w", pady=(0, 10))

        self._equipment_name_widgets = {}
        equipment = [
            ("armor_head", "Шлем"), ("armor_chest", "Нагрудник"),
            ("armor_hands", "Перчатки"), ("armor_feet", "Обувь"), ("armor_belt", "Пояс"),
            ("jewelry_ring", "Кольцо"), ("jewelry_amulet", "Амулет"), ("jewelry_bracelet", "Браслет"),
            ("backpack", "Рюкзак"), ("tool", "Инструмент"),
        ]

        for eq_id, default_name in equipment:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{eq_id}:", width=15).pack(side=tk.LEFT)
            entry = ClipboardEntry(row, width=30)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.insert(0, default_name)
            entry.bind("<KeyRelease>", lambda e: self._mark_modified())
            self._equipment_name_widgets[eq_id] = entry

    def _create_suffixes_tab(self):
        """Вкладка редактирования суффиксов характеристик"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Суффиксы")

        ttk.Label(frame, text="Суффиксы для характеристик (по одному на строку):").pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._suffix_widgets = {}
        stats = [
            ("strength", "Сила"), ("dexterity", "Ловкость"), ("constitution", "Телосложение"),
            ("intelligence", "Интеллект"), ("spirit", "Дух"), ("luck", "Удача"),
            ("max_health", "Здоровье"), ("max_mana", "Мана"),
            ("damage", "Урон"), ("defense", "Защита"), ("crit_chance", "Крит"),
        ]

        for stat_id, stat_name in stats:
            stat_frame = ttk.LabelFrame(scroll_frame, text=stat_name, padding=5)
            stat_frame.pack(fill=tk.X, pady=2, padx=5)

            text = ClipboardText(stat_frame, height=2, width=40)
            text.pack(fill=tk.X)
            text.bind("<<Modified>>", lambda e, t=text: self._on_text_modified(t))
            self._suffix_widgets[stat_id] = text

    def _create_resource_names_tab(self):
        """Вкладка редактирования названий ресурсов"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Ресурсы")

        ttk.Label(frame, text="Названия ресурсов по категориям и уровням:").pack(anchor="w", pady=(0, 10))

        # Notebook для категорий
        cat_notebook = ttk.Notebook(frame)
        cat_notebook.pack(fill=tk.BOTH, expand=True)

        self._resource_name_widgets = {}
        categories = ["ore", "ingot", "wood", "leather", "cloth", "herb", "gem", "essence"]
        category_names = {
            "ore": "Руда", "ingot": "Слиток", "wood": "Древесина", "leather": "Кожа",
            "cloth": "Ткань", "herb": "Трава", "gem": "Камень", "essence": "Эссенция",
        }

        for cat in categories:
            cat_frame = ttk.Frame(cat_notebook, padding=10)
            cat_notebook.add(cat_frame, text=category_names[cat])

            self._resource_name_widgets[cat] = {}
            for tier in range(1, 6):
                row = ttk.Frame(cat_frame)
                row.pack(fill=tk.X, pady=2)

                ttk.Label(row, text=f"Tier {tier}:", width=10).pack(side=tk.LEFT)
                entry = ClipboardEntry(row, width=40)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                entry.bind("<KeyRelease>", lambda e: self._mark_modified())
                self._resource_name_widgets[cat][tier] = entry

    def _on_text_modified(self, text_widget):
        if text_widget.edit_modified():
            self._mark_modified()
            text_widget.edit_modified(False)

    def _load_data(self):
        """Загрузить данные из конфигурации"""
        self._is_loading = True

        dictionary = self.config_manager.naming.dictionary

        # Префиксы качества
        for quality, text_widget in self._quality_prefix_widgets.items():
            prefixes = dictionary.quality_prefixes.get(quality, [])
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", "\n".join(prefixes))

        # Материалы
        for tier, cat_widgets in self._material_widgets.items():
            tier_materials = dictionary.materials.get(tier, {})
            for cat, entry in cat_widgets.items():
                entry.delete(0, tk.END)
                entry.insert(0, tier_materials.get(cat, ""))

        # Оружие
        for weapon_id, entry in self._weapon_name_widgets.items():
            entry.delete(0, tk.END)
            entry.insert(0, dictionary.weapon_names.get(weapon_id, ""))

        # Экипировка
        for eq_id, entry in self._equipment_name_widgets.items():
            entry.delete(0, tk.END)
            entry.insert(0, dictionary.equipment_names.get(eq_id, ""))

        # Суффиксы
        for stat_id, text_widget in self._suffix_widgets.items():
            suffixes = dictionary.stat_suffixes.get(stat_id, [])
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", "\n".join(suffixes))

        # Ресурсы
        for cat, tier_widgets in self._resource_name_widgets.items():
            cat_resources = dictionary.resource_names.get(cat, {})
            for tier, entry in tier_widgets.items():
                entry.delete(0, tk.END)
                entry.insert(0, cat_resources.get(tier, ""))

        self._is_loading = False

    def save_data(self):
        """Сохранить данные в конфигурацию"""
        dictionary = self.config_manager.naming.dictionary

        # Префиксы качества
        for quality, text_widget in self._quality_prefix_widgets.items():
            text = text_widget.get("1.0", tk.END).strip()
            prefixes = [p.strip() for p in text.split("\n") if p.strip()]
            dictionary.quality_prefixes[quality] = prefixes

        # Материалы
        for tier, cat_widgets in self._material_widgets.items():
            if tier not in dictionary.materials:
                dictionary.materials[tier] = {}
            for cat, entry in cat_widgets.items():
                dictionary.materials[tier][cat] = entry.get()

        # Оружие
        for weapon_id, entry in self._weapon_name_widgets.items():
            dictionary.weapon_names[weapon_id] = entry.get()

        # Экипировка
        for eq_id, entry in self._equipment_name_widgets.items():
            dictionary.equipment_names[eq_id] = entry.get()

        # Суффиксы
        for stat_id, text_widget in self._suffix_widgets.items():
            text = text_widget.get("1.0", tk.END).strip()
            suffixes = [s.strip() for s in text.split("\n") if s.strip()]
            dictionary.stat_suffixes[stat_id] = suffixes

        # Ресурсы
        for cat, tier_widgets in self._resource_name_widgets.items():
            if cat not in dictionary.resource_names:
                dictionary.resource_names[cat] = {}
            for tier, entry in tier_widgets.items():
                dictionary.resource_names[cat][tier] = entry.get()
