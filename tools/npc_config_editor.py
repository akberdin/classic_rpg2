#!/usr/bin/env python3
"""
NPC Config Editor - Утилита для создания и настройки NPC
Позволяет создавать типовые NPC (с вилкой характеристик) и уникальных NPC
Результаты сохраняются в game/maps/map1_npc_config.json и map1_uniq_npc_config.json
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import os
import sys

# Добавляем путь к проекту для импорта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class NPCConfigEditor:
    """Главное окно редактора NPC"""

    # Константы
    NPC_TYPES = [
        ("guard", "Стражник"),
        ("merchant", "Торговец"),
        ("bandit", "Бандит"),
        ("miner", "Шахтёр"),
        ("undead", "Нежить"),
        ("mage", "Маг"),
        ("alchemist", "Алхимик"),
        ("hunter", "Охотник"),
        ("necromancer", "Некромант"),
        ("shadow_adept", "Адепт Тени"),
        ("wolf", "Волк"),
        ("bear", "Медведь"),
        ("deer", "Олень"),
    ]

    RANKS = [1, 2, 3, 4]

    QUALITY_LEVELS = [
        ("poor", "Плохое"),
        ("common", "Обычное"),
        ("uncommon", "Необычное"),
        ("rare", "Редкое"),
        ("epic", "Эпическое"),
        ("legendary", "Легендарное"),
        ("artifact", "Артефакт"),
    ]

    EQUIPMENT_TYPES = [
        ("weapon", "Оружие"),
        ("light_armor", "Лёгкая броня"),
        ("medium_armor", "Средняя броня"),
        ("heavy_armor", "Тяжёлая броня"),
        ("amulet", "Амулет"),
        ("ring", "Кольцо"),
        ("bracelet", "Браслет"),
    ]

    STATS = [
        ("strength", "Сила"),
        ("dexterity", "Ловкость"),
        ("constitution", "Телосложение"),
        ("spirit", "Дух"),
        ("intelligence", "Интеллект"),
        ("luck", "Удача"),
    ]

    SPRITE_FOLDERS = {
        "guard": "soldier",
        "merchant": "trader",
        "bandit": "bandits",
        "miner": "miners",
        "undead": "skeletons",
        "mage": "mage",
        "alchemist": "alchemist",
        "hunter": "hunter",
        "necromancer": "necro",
        "shadow_adept": "mage",
        "wolf": "wolf",
        "bear": "bear",
        "deer": "deer",
    }

    RELATIONSHIPS = [
        ("hostile", "Враждебный"),
        ("unfriendly", "Недружелюбный"),
        ("neutral", "Нейтральный"),
        ("friendly", "Дружелюбный"),
        ("allied", "Союзный"),
    ]

    SKILLS = [
        # Боевые
        ("basic_attack", "Базовая атака"),
        ("power_strike", "Мощный удар"),
        ("poison_strike", "Отравленный удар"),
        ("stun_strike", "Оглушающий удар"),
        ("battle_cry", "Боевой клич"),
        # Магия
        ("fireball", "Огненный шар"),
        ("ice_bolt", "Ледяная стрела"),
        ("lightning", "Молния"),
        ("magic_missile", "Магическая стрела"),
        ("fire_arrow", "Огненная стрела"),
        # Лечение
        ("heal", "Исцеление"),
        ("regeneration", "Регенерация"),
        ("mage_shield", "Щит мага"),
        # Лук
        ("basic_shot", "Выстрел"),
        ("precise_shot", "Точный выстрел"),
        ("rapid_fire", "Быстрая стрельба"),
        ("piercing_arrow", "Пронзающая стрела"),
        # Кинжал
        ("backstab", "Удар в спину"),
        ("bleeding_cut", "Кровоточащий порез"),
        ("shadow_step", "Шаг тени"),
        # Меч
        ("whirlwind_strike", "Вихревой удар"),
        ("shield_breaker", "Разрушитель щита"),
        ("blade_dance", "Танец клинка"),
        # Копьё
        ("lunge_strike", "Пронзающий выпад"),
        ("spear_sweep", "Вихревое вращение"),
        ("armor_breach", "Разрыв брони"),
    ]

    LOOT_ITEMS = [
        # Зелья
        ("minor_health_potion", "Малое зелье здоровья"),
        ("health_potion", "Зелье здоровья"),
        ("minor_mana_potion", "Малое зелье маны"),
        ("mana_potion", "Зелье маны"),
        ("minor_stamina_potion", "Малое зелье выносливости"),
        ("stamina_potion", "Зелье выносливости"),
        # Материалы
        ("copper_ore", "Медная руда"),
        ("iron_ore", "Железная руда"),
        ("silver_ore", "Серебряная руда"),
        ("gold_ore", "Золотая руда"),
        ("magic_crystal", "Магический кристалл"),
        ("ancient_coin", "Древняя монета"),
        ("old_scroll", "Старый свиток"),
        # Камни
        ("raw_amethyst", "Сырой аметист"),
        ("raw_ruby", "Сырой рубин"),
        ("raw_sapphire", "Сырой сапфир"),
        ("raw_emerald", "Сырой изумруд"),
        ("cut_diamond", "Огранённый алмаз"),
        # Животные
        ("wolf_fang", "Клык волка"),
        ("wolf_hide", "Шкура волка"),
        ("bear_fang", "Клык медведя"),
        ("bear_hide", "Шкура медведя"),
        ("bear_meat", "Медвежатина"),
        ("deer_hide", "Шкура оленя"),
        ("deer_meat", "Оленина"),
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("NPC Config Editor")
        self.root.geometry("1200x800")

        # Пути к файлам
        self.assets_path = os.path.join(PROJECT_ROOT, "assets", "actors")
        self.config_path = os.path.join(PROJECT_ROOT, "game", "maps")
        self.npc_config_file = os.path.join(self.config_path, "map1_npc_config.json")
        self.uniq_npc_config_file = os.path.join(self.config_path, "map1_uniq_npc_config.json")

        # Данные
        self.npc_templates = []  # Типовые NPC
        self.unique_npcs = []    # Уникальные NPC
        self.current_sprite_image = None

        # Загружаем существующие конфиги
        self.load_configs()

        # Создаём интерфейс
        self.create_ui()

    def load_configs(self):
        """Загрузка существующих конфигов"""
        # Загружаем типовые NPC
        if os.path.exists(self.npc_config_file):
            try:
                with open(self.npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.npc_templates = data.get('templates', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.npc_config_file}: {e}")

        # Загружаем уникальных NPC
        if os.path.exists(self.uniq_npc_config_file):
            try:
                with open(self.uniq_npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unique_npcs = data.get('unique_npcs', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.uniq_npc_config_file}: {e}")

    def save_configs(self):
        """Сохранение конфигов"""
        # Создаём папку если нет
        os.makedirs(self.config_path, exist_ok=True)

        # Сохраняем типовые NPC
        npc_data = {
            "_description": "Конфигурация типовых NPC для карты",
            "_version": "1.0.0",
            "templates": self.npc_templates
        }
        with open(self.npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(npc_data, f, ensure_ascii=False, indent=2)

        # Сохраняем уникальных NPC
        uniq_data = {
            "_description": "Конфигурация уникальных NPC для карты",
            "_version": "1.0.0",
            "unique_npcs": self.unique_npcs
        }
        with open(self.uniq_npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(uniq_data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Сохранено", f"Конфиги сохранены:\n{self.npc_config_file}\n{self.uniq_npc_config_file}")

    def create_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка типовых NPC
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text="Типовые NPC")
        self.create_template_tab()

        # Вкладка уникальных NPC
        self.unique_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.unique_frame, text="Уникальные NPC")
        self.create_unique_tab()

        # Панель кнопок внизу
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Сохранить всё", command=self.save_configs).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Перезагрузить", command=self.reload_configs).pack(side=tk.RIGHT, padx=5)

    def reload_configs(self):
        """Перезагрузка конфигов"""
        self.load_configs()
        self.refresh_template_list()
        self.refresh_unique_list()
        messagebox.showinfo("Перезагружено", "Конфиги перезагружены")

    # ==================== ТИПОВЫЕ NPC ====================

    def create_template_tab(self):
        """Создание вкладки типовых NPC"""
        # Левая панель - список шаблонов
        left_frame = ttk.Frame(self.template_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        ttk.Label(left_frame, text="Шаблоны NPC:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        # Список шаблонов
        self.template_listbox = tk.Listbox(left_frame, height=20)
        self.template_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)

        # Кнопки управления списком
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Добавить", command=self.add_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Дублировать", command=self.duplicate_template).pack(side=tk.LEFT, padx=2)

        # Правая панель - редактор шаблона
        right_frame = ttk.Frame(self.template_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Создаём canvas со скроллбаром для правой панели
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.template_editor_frame = ttk.Frame(canvas)

        self.template_editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.template_editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязываем скролл мышкой
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.create_template_editor()
        self.refresh_template_list()

    def create_template_editor(self):
        """Создание редактора шаблона NPC"""
        frame = self.template_editor_frame

        # ID шаблона
        row = 0
        ttk.Label(frame, text="ID шаблона:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.template_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.template_id_var, width=30).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Название
        row += 1
        ttk.Label(frame, text="Название:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.template_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.template_name_var, width=30).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Тип NPC
        row += 1
        ttk.Label(frame, text="Тип NPC:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.template_type_var = tk.StringVar()
        type_combo = ttk.Combobox(frame, textvariable=self.template_type_var, width=27, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)
        type_combo.bind('<<ComboboxSelected>>', self.on_template_type_changed)

        # Ранг
        row += 1
        ttk.Label(frame, text="Ранг (1-4):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.template_rank_var = tk.IntVar(value=1)
        rank_combo = ttk.Combobox(frame, textvariable=self.template_rank_var, width=10, state='readonly')
        rank_combo['values'] = self.RANKS
        rank_combo.grid(row=row, column=1, sticky=tk.W, pady=2)

        # Отношение к игроку
        row += 1
        ttk.Label(frame, text="Отношение:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.template_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(frame, textvariable=self.template_relation_var, width=27, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in self.RELATIONSHIPS]
        rel_combo.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Разделитель - Характеристики
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Характеристики (min-max):", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        # Переменные для статов
        self.template_stats_vars = {}
        for stat_id, stat_name in self.STATS:
            row += 1
            ttk.Label(frame, text=f"{stat_name}:").grid(row=row, column=0, sticky=tk.W, pady=2)

            min_var = tk.IntVar(value=5)
            max_var = tk.IntVar(value=15)
            self.template_stats_vars[stat_id] = (min_var, max_var)

            ttk.Spinbox(frame, from_=1, to=100, textvariable=min_var, width=8).grid(row=row, column=1, sticky=tk.W, pady=2)
            ttk.Label(frame, text="-").grid(row=row, column=2, pady=2)
            ttk.Spinbox(frame, from_=1, to=100, textvariable=max_var, width=8).grid(row=row, column=3, sticky=tk.W, pady=2)

        # Разделитель - Экипировка
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Экипировка:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        # Тип экипировки и качество
        self.template_equip_vars = {}
        for equip_id, equip_name in self.EQUIPMENT_TYPES:
            row += 1

            # Чекбокс включения
            enabled_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame, text=equip_name, variable=enabled_var).grid(row=row, column=0, sticky=tk.W, pady=2)

            # Минимальное качество
            min_qual_var = tk.StringVar(value="common")
            min_combo = ttk.Combobox(frame, textvariable=min_qual_var, width=12, state='readonly')
            min_combo['values'] = [q[0] for q in self.QUALITY_LEVELS]
            min_combo.grid(row=row, column=1, sticky=tk.W, pady=2)

            ttk.Label(frame, text="-").grid(row=row, column=2, pady=2)

            # Максимальное качество
            max_qual_var = tk.StringVar(value="rare")
            max_combo = ttk.Combobox(frame, textvariable=max_qual_var, width=12, state='readonly')
            max_combo['values'] = [q[0] for q in self.QUALITY_LEVELS]
            max_combo.grid(row=row, column=3, sticky=tk.W, pady=2)

            self.template_equip_vars[equip_id] = (enabled_var, min_qual_var, max_qual_var)

        # Разделитель - Лут
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Возможный лут:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        loot_frame = ttk.Frame(frame)
        loot_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        # Список лута с чекбоксами и вероятностями
        self.template_loot_vars = {}
        loot_canvas = tk.Canvas(loot_frame, height=150)
        loot_scrollbar = ttk.Scrollbar(loot_frame, orient="vertical", command=loot_canvas.yview)
        loot_inner_frame = ttk.Frame(loot_canvas)

        loot_inner_frame.bind(
            "<Configure>",
            lambda e: loot_canvas.configure(scrollregion=loot_canvas.bbox("all"))
        )

        loot_canvas.create_window((0, 0), window=loot_inner_frame, anchor="nw")
        loot_canvas.configure(yscrollcommand=loot_scrollbar.set)

        loot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        loot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, (loot_id, loot_name) in enumerate(self.LOOT_ITEMS):
            loot_row = i // 2
            loot_col = (i % 2) * 3

            enabled_var = tk.BooleanVar(value=False)
            chance_var = tk.DoubleVar(value=0.1)

            ttk.Checkbutton(loot_inner_frame, text=loot_name[:15], variable=enabled_var).grid(
                row=loot_row, column=loot_col, sticky=tk.W, padx=2)
            ttk.Spinbox(loot_inner_frame, from_=0.01, to=1.0, increment=0.05,
                       textvariable=chance_var, width=6).grid(row=loot_row, column=loot_col+1, padx=2)

            self.template_loot_vars[loot_id] = (enabled_var, chance_var)

        # Разделитель - Умения
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Умения:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        skills_frame = ttk.Frame(frame)
        skills_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        self.template_skills_vars = {}
        skills_canvas = tk.Canvas(skills_frame, height=120)
        skills_scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=skills_canvas.yview)
        skills_inner_frame = ttk.Frame(skills_canvas)

        skills_inner_frame.bind(
            "<Configure>",
            lambda e: skills_canvas.configure(scrollregion=skills_canvas.bbox("all"))
        )

        skills_canvas.create_window((0, 0), window=skills_inner_frame, anchor="nw")
        skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        skills_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        skills_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, (skill_id, skill_name) in enumerate(self.SKILLS):
            skill_row = i // 3
            skill_col = (i % 3) * 2

            enabled_var = tk.BooleanVar(value=False)
            rank_var = tk.IntVar(value=1)

            ttk.Checkbutton(skills_inner_frame, text=skill_name[:12], variable=enabled_var).grid(
                row=skill_row, column=skill_col, sticky=tk.W, padx=2)
            ttk.Spinbox(skills_inner_frame, from_=1, to=5, textvariable=rank_var, width=3).grid(
                row=skill_row, column=skill_col+1, padx=2)

            self.template_skills_vars[skill_id] = (enabled_var, rank_var)

        # Разделитель - Спрайт
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Спрайт:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        sprite_frame = ttk.Frame(frame)
        sprite_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        self.template_sprite_var = tk.StringVar()
        self.template_sprite_combo = ttk.Combobox(sprite_frame, textvariable=self.template_sprite_var, width=30, state='readonly')
        self.template_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.template_sprite_combo.bind('<<ComboboxSelected>>', self.on_template_sprite_changed)

        self.template_sprite_label = ttk.Label(sprite_frame)
        self.template_sprite_label.pack(side=tk.LEFT, padx=10)

        # Кнопка применить изменения
        row += 1
        ttk.Button(frame, text="Применить изменения", command=self.apply_template_changes).grid(
            row=row, column=0, columnspan=4, pady=20)

    def refresh_template_list(self):
        """Обновление списка шаблонов"""
        self.template_listbox.delete(0, tk.END)
        for template in self.npc_templates:
            display_name = f"{template.get('id', 'unknown')} - {template.get('name', 'Без имени')}"
            self.template_listbox.insert(tk.END, display_name)

    def on_template_select(self, event):
        """Обработка выбора шаблона"""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.npc_templates):
            template = self.npc_templates[index]
            self.load_template_to_editor(template)

    def load_template_to_editor(self, template):
        """Загрузка шаблона в редактор"""
        # Основные поля
        self.template_id_var.set(template.get('id', ''))
        self.template_name_var.set(template.get('name', ''))

        # Тип NPC
        npc_type = template.get('type', 'guard')
        for i, (type_id, type_name) in enumerate(self.NPC_TYPES):
            if type_id == npc_type:
                self.template_type_var.set(f"{type_id} - {type_name}")
                break

        self.template_rank_var.set(template.get('rank', 1))

        # Отношение
        relation = template.get('relationship', 'neutral')
        for rel_id, rel_name in self.RELATIONSHIPS:
            if rel_id == relation:
                self.template_relation_var.set(f"{rel_id} - {rel_name}")
                break

        # Статы
        stats = template.get('stats', {})
        for stat_id, (min_var, max_var) in self.template_stats_vars.items():
            stat_range = stats.get(stat_id, {'min': 5, 'max': 15})
            min_var.set(stat_range.get('min', 5))
            max_var.set(stat_range.get('max', 15))

        # Экипировка
        equipment = template.get('equipment', {})
        for equip_id, (enabled_var, min_qual_var, max_qual_var) in self.template_equip_vars.items():
            if equip_id in equipment:
                enabled_var.set(True)
                equip_data = equipment[equip_id]
                min_qual_var.set(equip_data.get('quality_min', 'common'))
                max_qual_var.set(equip_data.get('quality_max', 'rare'))
            else:
                enabled_var.set(False)

        # Лут
        loot = template.get('loot', {})
        for loot_id, (enabled_var, chance_var) in self.template_loot_vars.items():
            if loot_id in loot:
                enabled_var.set(True)
                chance_var.set(loot[loot_id].get('chance', 0.1))
            else:
                enabled_var.set(False)
                chance_var.set(0.1)

        # Умения
        skills = template.get('skills', {})
        for skill_id, (enabled_var, rank_var) in self.template_skills_vars.items():
            if skill_id in skills:
                enabled_var.set(True)
                rank_var.set(skills[skill_id].get('rank', 1))
            else:
                enabled_var.set(False)
                rank_var.set(1)

        # Спрайт
        self.update_sprite_combo_for_type(template.get('type', 'guard'))
        sprite = template.get('sprite', '')
        if sprite:
            self.template_sprite_var.set(sprite)
            self.load_sprite_preview(sprite)

    def on_template_type_changed(self, event):
        """Обработка смены типа NPC"""
        type_str = self.template_type_var.get()
        if ' - ' in type_str:
            npc_type = type_str.split(' - ')[0]
            self.update_sprite_combo_for_type(npc_type)

    def update_sprite_combo_for_type(self, npc_type):
        """Обновление списка спрайтов для типа NPC"""
        folder = self.SPRITE_FOLDERS.get(npc_type, 'soldier')
        sprite_path = os.path.join(self.assets_path, folder)

        sprites = []
        if os.path.exists(sprite_path):
            for file in os.listdir(sprite_path):
                if file.endswith('.png'):
                    sprites.append(f"{folder}/{file}")

        self.template_sprite_combo['values'] = sprites
        if sprites:
            self.template_sprite_var.set(sprites[0])
            self.load_sprite_preview(sprites[0])

    def on_template_sprite_changed(self, event):
        """Обработка смены спрайта"""
        sprite = self.template_sprite_var.get()
        self.load_sprite_preview(sprite)

    def load_sprite_preview(self, sprite_path):
        """Загрузка превью спрайта"""
        full_path = os.path.join(self.assets_path, sprite_path)
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                img = img.resize((64, 64), Image.Resampling.NEAREST)
                self.current_sprite_image = ImageTk.PhotoImage(img)
                self.template_sprite_label.configure(image=self.current_sprite_image)
            except Exception as e:
                print(f"Ошибка загрузки спрайта: {e}")

    def add_template(self):
        """Добавление нового шаблона"""
        new_template = {
            'id': f'template_{len(self.npc_templates) + 1}',
            'name': 'Новый NPC',
            'type': 'guard',
            'rank': 1,
            'relationship': 'neutral',
            'stats': {stat_id: {'min': 5, 'max': 15} for stat_id, _ in self.STATS},
            'equipment': {},
            'loot': {},
            'skills': {},
            'sprite': 'soldier/soldier1.png'
        }
        self.npc_templates.append(new_template)
        self.refresh_template_list()

        # Выбираем новый шаблон
        self.template_listbox.selection_clear(0, tk.END)
        self.template_listbox.selection_set(len(self.npc_templates) - 1)
        self.load_template_to_editor(new_template)

    def delete_template(self):
        """Удаление шаблона"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите шаблон для удаления")
            return

        index = selection[0]
        if messagebox.askyesno("Подтверждение", "Удалить выбранный шаблон?"):
            del self.npc_templates[index]
            self.refresh_template_list()

    def duplicate_template(self):
        """Дублирование шаблона"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите шаблон для дублирования")
            return

        index = selection[0]
        original = self.npc_templates[index]

        # Глубокое копирование
        import copy
        new_template = copy.deepcopy(original)
        new_template['id'] = f"{original['id']}_copy"
        new_template['name'] = f"{original['name']} (копия)"

        self.npc_templates.append(new_template)
        self.refresh_template_list()

    def apply_template_changes(self):
        """Применение изменений к шаблону"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите шаблон для редактирования")
            return

        index = selection[0]
        template = self.npc_templates[index]

        # Основные поля
        template['id'] = self.template_id_var.get()
        template['name'] = self.template_name_var.get()

        # Тип NPC
        type_str = self.template_type_var.get()
        if ' - ' in type_str:
            template['type'] = type_str.split(' - ')[0]

        template['rank'] = self.template_rank_var.get()

        # Отношение
        rel_str = self.template_relation_var.get()
        if ' - ' in rel_str:
            template['relationship'] = rel_str.split(' - ')[0]

        # Статы
        template['stats'] = {}
        for stat_id, (min_var, max_var) in self.template_stats_vars.items():
            template['stats'][stat_id] = {
                'min': min_var.get(),
                'max': max_var.get()
            }

        # Экипировка
        template['equipment'] = {}
        for equip_id, (enabled_var, min_qual_var, max_qual_var) in self.template_equip_vars.items():
            if enabled_var.get():
                template['equipment'][equip_id] = {
                    'quality_min': min_qual_var.get(),
                    'quality_max': max_qual_var.get()
                }

        # Лут
        template['loot'] = {}
        for loot_id, (enabled_var, chance_var) in self.template_loot_vars.items():
            if enabled_var.get():
                template['loot'][loot_id] = {
                    'chance': chance_var.get()
                }

        # Умения
        template['skills'] = {}
        for skill_id, (enabled_var, rank_var) in self.template_skills_vars.items():
            if enabled_var.get():
                template['skills'][skill_id] = {
                    'rank': rank_var.get()
                }

        # Спрайт
        template['sprite'] = self.template_sprite_var.get()

        self.refresh_template_list()
        messagebox.showinfo("Готово", "Изменения применены")

    # ==================== УНИКАЛЬНЫЕ NPC ====================

    def create_unique_tab(self):
        """Создание вкладки уникальных NPC"""
        # Левая панель - список уникальных NPC
        left_frame = ttk.Frame(self.unique_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        ttk.Label(left_frame, text="Уникальные NPC:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        # Список уникальных NPC
        self.unique_listbox = tk.Listbox(left_frame, height=20)
        self.unique_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.unique_listbox.bind('<<ListboxSelect>>', self.on_unique_select)

        # Кнопки управления
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Добавить", command=self.add_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Дублировать", command=self.duplicate_unique).pack(side=tk.LEFT, padx=2)

        # Правая панель - редактор
        right_frame = ttk.Frame(self.unique_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Создаём canvas со скроллбаром
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.unique_editor_frame = ttk.Frame(canvas)

        self.unique_editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.unique_editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_unique_editor()
        self.refresh_unique_list()

    def create_unique_editor(self):
        """Создание редактора уникального NPC"""
        frame = self.unique_editor_frame

        # ID
        row = 0
        ttk.Label(frame, text="ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unique_id_var, width=30).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Имя
        row += 1
        ttk.Label(frame, text="Имя:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unique_name_var, width=30).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Описание
        row += 1
        ttk.Label(frame, text="Описание:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unique_desc_var, width=50).grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=2)

        # Тип NPC
        row += 1
        ttk.Label(frame, text="Тип NPC:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_type_var = tk.StringVar()
        type_combo = ttk.Combobox(frame, textvariable=self.unique_type_var, width=27, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)
        type_combo.bind('<<ComboboxSelected>>', self.on_unique_type_changed)

        # Уровень
        row += 1
        ttk.Label(frame, text="Уровень:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_level_var = tk.IntVar(value=10)
        ttk.Spinbox(frame, from_=1, to=100, textvariable=self.unique_level_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)

        # Отношение к игроку
        row += 1
        ttk.Label(frame, text="Отношение:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(frame, textvariable=self.unique_relation_var, width=27, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in self.RELATIONSHIPS]
        rel_combo.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Позиция на карте
        row += 1
        ttk.Label(frame, text="Позиция X:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.unique_x_var = tk.IntVar(value=100)
        ttk.Spinbox(frame, from_=0, to=500, textvariable=self.unique_x_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)

        ttk.Label(frame, text="Y:").grid(row=row, column=2, sticky=tk.W, pady=2)
        self.unique_y_var = tk.IntVar(value=100)
        ttk.Spinbox(frame, from_=0, to=500, textvariable=self.unique_y_var, width=10).grid(row=row, column=3, sticky=tk.W, pady=2)

        # Разделитель - Характеристики
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Характеристики (фиксированные):", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        # Статы уникального NPC
        self.unique_stats_vars = {}
        for stat_id, stat_name in self.STATS:
            row += 1
            ttk.Label(frame, text=f"{stat_name}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            stat_var = tk.IntVar(value=10)
            self.unique_stats_vars[stat_id] = stat_var
            ttk.Spinbox(frame, from_=1, to=100, textvariable=stat_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)

        # Разделитель - Экипировка
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Экипировка (фиксированная):", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        self.unique_equip_vars = {}
        for equip_id, equip_name in self.EQUIPMENT_TYPES:
            row += 1

            enabled_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame, text=equip_name, variable=enabled_var).grid(row=row, column=0, sticky=tk.W, pady=2)

            quality_var = tk.StringVar(value="rare")
            qual_combo = ttk.Combobox(frame, textvariable=quality_var, width=12, state='readonly')
            qual_combo['values'] = [q[0] for q in self.QUALITY_LEVELS]
            qual_combo.grid(row=row, column=1, sticky=tk.W, pady=2)

            self.unique_equip_vars[equip_id] = (enabled_var, quality_var)

        # Разделитель - Гарантированный лут
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Гарантированный лут:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        loot_frame = ttk.Frame(frame)
        loot_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        self.unique_loot_vars = {}
        loot_canvas = tk.Canvas(loot_frame, height=120)
        loot_scrollbar = ttk.Scrollbar(loot_frame, orient="vertical", command=loot_canvas.yview)
        loot_inner_frame = ttk.Frame(loot_canvas)

        loot_inner_frame.bind(
            "<Configure>",
            lambda e: loot_canvas.configure(scrollregion=loot_canvas.bbox("all"))
        )

        loot_canvas.create_window((0, 0), window=loot_inner_frame, anchor="nw")
        loot_canvas.configure(yscrollcommand=loot_scrollbar.set)

        loot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        loot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, (loot_id, loot_name) in enumerate(self.LOOT_ITEMS):
            loot_row = i // 2
            loot_col = (i % 2) * 3

            enabled_var = tk.BooleanVar(value=False)
            count_var = tk.IntVar(value=1)

            ttk.Checkbutton(loot_inner_frame, text=loot_name[:15], variable=enabled_var).grid(
                row=loot_row, column=loot_col, sticky=tk.W, padx=2)
            ttk.Spinbox(loot_inner_frame, from_=1, to=99, textvariable=count_var, width=4).grid(
                row=loot_row, column=loot_col+1, padx=2)

            self.unique_loot_vars[loot_id] = (enabled_var, count_var)

        # Разделитель - Умения
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Умения:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        skills_frame = ttk.Frame(frame)
        skills_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        self.unique_skills_vars = {}
        skills_canvas = tk.Canvas(skills_frame, height=120)
        skills_scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=skills_canvas.yview)
        skills_inner_frame = ttk.Frame(skills_canvas)

        skills_inner_frame.bind(
            "<Configure>",
            lambda e: skills_canvas.configure(scrollregion=skills_canvas.bbox("all"))
        )

        skills_canvas.create_window((0, 0), window=skills_inner_frame, anchor="nw")
        skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        skills_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        skills_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, (skill_id, skill_name) in enumerate(self.SKILLS):
            skill_row = i // 3
            skill_col = (i % 3) * 2

            enabled_var = tk.BooleanVar(value=False)
            rank_var = tk.IntVar(value=1)

            ttk.Checkbutton(skills_inner_frame, text=skill_name[:12], variable=enabled_var).grid(
                row=skill_row, column=skill_col, sticky=tk.W, padx=2)
            ttk.Spinbox(skills_inner_frame, from_=1, to=5, textvariable=rank_var, width=3).grid(
                row=skill_row, column=skill_col+1, padx=2)

            self.unique_skills_vars[skill_id] = (enabled_var, rank_var)

        # Разделитель - Спрайт
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Спрайт:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)

        row += 1
        sprite_frame = ttk.Frame(frame)
        sprite_frame.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=5)

        self.unique_sprite_var = tk.StringVar()
        self.unique_sprite_combo = ttk.Combobox(sprite_frame, textvariable=self.unique_sprite_var, width=30, state='readonly')
        self.unique_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.unique_sprite_combo.bind('<<ComboboxSelected>>', self.on_unique_sprite_changed)

        self.unique_sprite_label = ttk.Label(sprite_frame)
        self.unique_sprite_label.pack(side=tk.LEFT, padx=10)

        # Диалоги
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        ttk.Label(frame, text="Диалог (ID):", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.unique_dialog_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unique_dialog_var, width=30).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)

        # Кнопка применить
        row += 1
        ttk.Button(frame, text="Применить изменения", command=self.apply_unique_changes).grid(
            row=row, column=0, columnspan=4, pady=20)

    def refresh_unique_list(self):
        """Обновление списка уникальных NPC"""
        self.unique_listbox.delete(0, tk.END)
        for npc in self.unique_npcs:
            display_name = f"{npc.get('id', 'unknown')} - {npc.get('name', 'Без имени')}"
            self.unique_listbox.insert(tk.END, display_name)

    def on_unique_select(self, event):
        """Обработка выбора уникального NPC"""
        selection = self.unique_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.unique_npcs):
            npc = self.unique_npcs[index]
            self.load_unique_to_editor(npc)

    def load_unique_to_editor(self, npc):
        """Загрузка уникального NPC в редактор"""
        self.unique_id_var.set(npc.get('id', ''))
        self.unique_name_var.set(npc.get('name', ''))
        self.unique_desc_var.set(npc.get('description', ''))

        # Тип
        npc_type = npc.get('type', 'guard')
        for type_id, type_name in self.NPC_TYPES:
            if type_id == npc_type:
                self.unique_type_var.set(f"{type_id} - {type_name}")
                break

        self.unique_level_var.set(npc.get('level', 10))

        # Отношение
        relation = npc.get('relationship', 'neutral')
        for rel_id, rel_name in self.RELATIONSHIPS:
            if rel_id == relation:
                self.unique_relation_var.set(f"{rel_id} - {rel_name}")
                break

        # Позиция
        pos = npc.get('position', {'x': 100, 'y': 100})
        self.unique_x_var.set(pos.get('x', 100))
        self.unique_y_var.set(pos.get('y', 100))

        # Статы
        stats = npc.get('stats', {})
        for stat_id, stat_var in self.unique_stats_vars.items():
            stat_var.set(stats.get(stat_id, 10))

        # Экипировка
        equipment = npc.get('equipment', {})
        for equip_id, (enabled_var, quality_var) in self.unique_equip_vars.items():
            if equip_id in equipment:
                enabled_var.set(True)
                quality_var.set(equipment[equip_id].get('quality', 'rare'))
            else:
                enabled_var.set(False)

        # Лут
        loot = npc.get('loot', {})
        for loot_id, (enabled_var, count_var) in self.unique_loot_vars.items():
            if loot_id in loot:
                enabled_var.set(True)
                count_var.set(loot[loot_id].get('count', 1))
            else:
                enabled_var.set(False)
                count_var.set(1)

        # Умения
        skills = npc.get('skills', {})
        for skill_id, (enabled_var, rank_var) in self.unique_skills_vars.items():
            if skill_id in skills:
                enabled_var.set(True)
                rank_var.set(skills[skill_id].get('rank', 1))
            else:
                enabled_var.set(False)
                rank_var.set(1)

        # Спрайт
        self.update_unique_sprite_combo(npc.get('type', 'guard'))
        sprite = npc.get('sprite', '')
        if sprite:
            self.unique_sprite_var.set(sprite)
            self.load_unique_sprite_preview(sprite)

        # Диалог
        self.unique_dialog_var.set(npc.get('dialog_id', ''))

    def on_unique_type_changed(self, event):
        """Обработка смены типа уникального NPC"""
        type_str = self.unique_type_var.get()
        if ' - ' in type_str:
            npc_type = type_str.split(' - ')[0]
            self.update_unique_sprite_combo(npc_type)

    def update_unique_sprite_combo(self, npc_type):
        """Обновление списка спрайтов для уникального NPC"""
        folder = self.SPRITE_FOLDERS.get(npc_type, 'soldier')
        sprite_path = os.path.join(self.assets_path, folder)

        sprites = []
        if os.path.exists(sprite_path):
            for file in os.listdir(sprite_path):
                if file.endswith('.png'):
                    sprites.append(f"{folder}/{file}")

        self.unique_sprite_combo['values'] = sprites
        if sprites:
            self.unique_sprite_var.set(sprites[0])
            self.load_unique_sprite_preview(sprites[0])

    def on_unique_sprite_changed(self, event):
        """Обработка смены спрайта уникального NPC"""
        sprite = self.unique_sprite_var.get()
        self.load_unique_sprite_preview(sprite)

    def load_unique_sprite_preview(self, sprite_path):
        """Загрузка превью спрайта уникального NPC"""
        full_path = os.path.join(self.assets_path, sprite_path)
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                img = img.resize((64, 64), Image.Resampling.NEAREST)
                self.unique_sprite_image = ImageTk.PhotoImage(img)
                self.unique_sprite_label.configure(image=self.unique_sprite_image)
            except Exception as e:
                print(f"Ошибка загрузки спрайта: {e}")

    def add_unique(self):
        """Добавление нового уникального NPC"""
        new_npc = {
            'id': f'unique_{len(self.unique_npcs) + 1}',
            'name': 'Новый уникальный NPC',
            'description': 'Описание NPC',
            'type': 'guard',
            'level': 10,
            'relationship': 'neutral',
            'position': {'x': 100, 'y': 100},
            'stats': {stat_id: 10 for stat_id, _ in self.STATS},
            'equipment': {},
            'loot': {},
            'skills': {},
            'sprite': 'soldier/soldier1.png',
            'dialog_id': ''
        }
        self.unique_npcs.append(new_npc)
        self.refresh_unique_list()

        self.unique_listbox.selection_clear(0, tk.END)
        self.unique_listbox.selection_set(len(self.unique_npcs) - 1)
        self.load_unique_to_editor(new_npc)

    def delete_unique(self):
        """Удаление уникального NPC"""
        selection = self.unique_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите NPC для удаления")
            return

        index = selection[0]
        if messagebox.askyesno("Подтверждение", "Удалить выбранного NPC?"):
            del self.unique_npcs[index]
            self.refresh_unique_list()

    def duplicate_unique(self):
        """Дублирование уникального NPC"""
        selection = self.unique_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите NPC для дублирования")
            return

        index = selection[0]
        original = self.unique_npcs[index]

        import copy
        new_npc = copy.deepcopy(original)
        new_npc['id'] = f"{original['id']}_copy"
        new_npc['name'] = f"{original['name']} (копия)"

        self.unique_npcs.append(new_npc)
        self.refresh_unique_list()

    def apply_unique_changes(self):
        """Применение изменений к уникальному NPC"""
        selection = self.unique_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите NPC для редактирования")
            return

        index = selection[0]
        npc = self.unique_npcs[index]

        # Основные поля
        npc['id'] = self.unique_id_var.get()
        npc['name'] = self.unique_name_var.get()
        npc['description'] = self.unique_desc_var.get()

        # Тип
        type_str = self.unique_type_var.get()
        if ' - ' in type_str:
            npc['type'] = type_str.split(' - ')[0]

        npc['level'] = self.unique_level_var.get()

        # Отношение
        rel_str = self.unique_relation_var.get()
        if ' - ' in rel_str:
            npc['relationship'] = rel_str.split(' - ')[0]

        # Позиция
        npc['position'] = {
            'x': self.unique_x_var.get(),
            'y': self.unique_y_var.get()
        }

        # Статы
        npc['stats'] = {}
        for stat_id, stat_var in self.unique_stats_vars.items():
            npc['stats'][stat_id] = stat_var.get()

        # Экипировка
        npc['equipment'] = {}
        for equip_id, (enabled_var, quality_var) in self.unique_equip_vars.items():
            if enabled_var.get():
                npc['equipment'][equip_id] = {
                    'quality': quality_var.get()
                }

        # Лут
        npc['loot'] = {}
        for loot_id, (enabled_var, count_var) in self.unique_loot_vars.items():
            if enabled_var.get():
                npc['loot'][loot_id] = {
                    'count': count_var.get()
                }

        # Умения
        npc['skills'] = {}
        for skill_id, (enabled_var, rank_var) in self.unique_skills_vars.items():
            if enabled_var.get():
                npc['skills'][skill_id] = {
                    'rank': rank_var.get()
                }

        # Спрайт
        npc['sprite'] = self.unique_sprite_var.get()

        # Диалог
        npc['dialog_id'] = self.unique_dialog_var.get()

        self.refresh_unique_list()
        messagebox.showinfo("Готово", "Изменения применены")


def main():
    """Главная функция"""
    root = tk.Tk()

    # Устанавливаем стиль
    style = ttk.Style()
    style.theme_use('clam')

    app = NPCConfigEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
