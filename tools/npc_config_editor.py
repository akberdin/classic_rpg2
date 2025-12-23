#!/usr/bin/env python3
"""
NPC Config Editor - Утилита для создания и настройки NPC
Позволяет создавать типовые NPC (с вилкой характеристик) и уникальных NPC
Результаты сохраняются в game/maps/map1_npc_config.json и map1_uniq_npc_config.json
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import json
import os
import sys
import copy

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
        ("poor", "Плохое", "#808080"),
        ("common", "Обычное", "#FFFFFF"),
        ("uncommon", "Необычное", "#1EFF00"),
        ("rare", "Редкое", "#0070FF"),
        ("epic", "Эпическое", "#A335EE"),
        ("legendary", "Легендарное", "#FF8000"),
        ("artifact", "Артефакт", "#E6CC80"),
    ]

    LOOT_TYPES = [
        ("weapon", "Оружие"),
        ("armor", "Броня"),
        ("jewelry", "Украшения"),
        ("potion", "Зелья"),
        ("material", "Материалы"),
    ]

    STATS = [
        ("strength", "Сила", "STR"),
        ("dexterity", "Ловкость", "DEX"),
        ("constitution", "Телосложение", "CON"),
        ("spirit", "Дух", "SPI"),
        ("intelligence", "Интеллект", "INT"),
        ("luck", "Удача", "LCK"),
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
        ("basic_attack", "Базовая атака", "combat"),
        ("power_strike", "Мощный удар", "combat"),
        ("poison_strike", "Отравленный удар", "combat"),
        ("stun_strike", "Оглушающий удар", "combat"),
        ("battle_cry", "Боевой клич", "combat"),
        ("fireball", "Огненный шар", "magic"),
        ("ice_bolt", "Ледяная стрела", "magic"),
        ("lightning", "Молния", "magic"),
        ("magic_missile", "Магическая стрела", "magic"),
        ("heal", "Исцеление", "magic"),
        ("regeneration", "Регенерация", "magic"),
        ("mage_shield", "Щит мага", "magic"),
        ("basic_shot", "Выстрел", "ranged"),
        ("precise_shot", "Точный выстрел", "ranged"),
        ("rapid_fire", "Быстрая стрельба", "ranged"),
        ("piercing_arrow", "Пронзающая стрела", "ranged"),
        ("backstab", "Удар в спину", "stealth"),
        ("bleeding_cut", "Кровоточащий порез", "stealth"),
        ("shadow_step", "Шаг тени", "stealth"),
        ("whirlwind_strike", "Вихревой удар", "weapon"),
        ("shield_breaker", "Разрушитель щита", "weapon"),
        ("blade_dance", "Танец клинка", "weapon"),
    ]

    # Очков характеристик за уровень
    STAT_POINTS_PER_LEVEL = 3

    def __init__(self, root):
        self.root = root
        self.root.title("NPC Config Editor")

        # Полноэкранный режим
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())

        # Пути к файлам
        self.assets_path = os.path.join(PROJECT_ROOT, "assets", "actors")
        self.config_path = os.path.join(PROJECT_ROOT, "game", "maps")
        self.npc_config_file = os.path.join(self.config_path, "map1_npc_config.json")
        self.uniq_npc_config_file = os.path.join(self.config_path, "map1_uniq_npc_config.json")

        # Данные
        self.npc_templates = []
        self.unique_npcs = []
        self.current_sprite_image = None
        self.unique_sprite_image = None

        # Загружаем существующие конфиги
        self.load_configs()

        # Создаём интерфейс
        self.create_ui()

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)

    def load_configs(self):
        """Загрузка существующих конфигов"""
        if os.path.exists(self.npc_config_file):
            try:
                with open(self.npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.npc_templates = data.get('templates', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.npc_config_file}: {e}")

        if os.path.exists(self.uniq_npc_config_file):
            try:
                with open(self.uniq_npc_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unique_npcs = data.get('unique_npcs', [])
            except Exception as e:
                print(f"Ошибка загрузки {self.uniq_npc_config_file}: {e}")

    def save_configs(self):
        """Сохранение конфигов с валидацией"""
        # Валидация
        errors = self.validate_all_data()
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return

        os.makedirs(self.config_path, exist_ok=True)

        npc_data = {
            "_description": "Конфигурация типовых NPC для карты",
            "_version": "2.0.0",
            "templates": self.npc_templates
        }
        with open(self.npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(npc_data, f, ensure_ascii=False, indent=2)

        uniq_data = {
            "_description": "Конфигурация уникальных NPC для карты",
            "_version": "2.0.0",
            "unique_npcs": self.unique_npcs
        }
        with open(self.uniq_npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(uniq_data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Сохранено", f"Конфиги сохранены:\n{self.npc_config_file}\n{self.uniq_npc_config_file}")

    def validate_all_data(self):
        """Валидация всех данных"""
        errors = []

        # Проверка уникальности ID шаблонов
        template_ids = [t.get('id', '') for t in self.npc_templates]
        duplicates = set([x for x in template_ids if template_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID шаблонов: {', '.join(duplicates)}")

        # Проверка уникальности ID уникальных NPC
        unique_ids = [n.get('id', '') for n in self.unique_npcs]
        duplicates = set([x for x in unique_ids if unique_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID уникальных NPC: {', '.join(duplicates)}")

        # Проверка что распределение статов = 100%
        for template in self.npc_templates:
            stat_dist = template.get('stat_distribution', {})
            total = sum(stat_dist.values())
            if stat_dist and abs(total - 100) > 0.1:
                errors.append(f"Шаблон '{template.get('id')}': сумма распределения статов = {total}% (должно быть 100%)")

        return errors

    def create_ui(self):
        """Создание пользовательского интерфейса"""
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="NPC Config Editor", font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Выход (Esc)", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Сохранить всё", command=self.save_configs).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Перезагрузить", command=self.reload_configs).pack(side=tk.RIGHT, padx=5)

        # Главный notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Вкладка типовых NPC
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text="  Типовые NPC  ")
        self.create_template_tab()

        # Вкладка уникальных NPC
        self.unique_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.unique_frame, text="  Уникальные NPC  ")
        self.create_unique_tab()

    def reload_configs(self):
        """Перезагрузка конфигов"""
        self.load_configs()
        self.refresh_template_list()
        self.refresh_unique_list()
        messagebox.showinfo("Перезагружено", "Конфиги перезагружены")

    # ==================== ТИПОВЫЕ NPC ====================

    def create_template_tab(self):
        """Создание вкладки типовых NPC с оптимизированным layout"""
        # Главный контейнер с тремя колонками
        main_container = ttk.Frame(self.template_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая колонка - список шаблонов (узкая)
        left_frame = ttk.LabelFrame(main_container, text="Шаблоны", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.template_listbox = tk.Listbox(left_frame, width=30, height=25, font=('Arial', 10))
        self.template_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Копия", command=self.duplicate_template).pack(side=tk.LEFT, padx=2)

        # Центральная колонка - основные настройки
        center_frame = ttk.LabelFrame(main_container, text="Основные настройки", padding=5)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.create_template_basic_settings(center_frame)

        # Правая колонка - лут и умения
        right_frame = ttk.LabelFrame(main_container, text="Лут и Умения", padding=5)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.create_template_loot_skills(right_frame)

        self.refresh_template_list()

    def create_template_basic_settings(self, parent):
        """Создание основных настроек шаблона"""
        # Верхняя часть - ID, имя, тип
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=5)

        # Ряд 1: ID и Имя
        row1 = ttk.Frame(top_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="ID:", width=12).pack(side=tk.LEFT)
        self.template_id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.template_id_var, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Название:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.template_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.template_name_var, width=25).pack(side=tk.LEFT, padx=5)

        # Ряд 2: Тип, Ранг, Отношение
        row2 = ttk.Frame(top_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="Тип NPC:", width=12).pack(side=tk.LEFT)
        self.template_type_var = tk.StringVar()
        type_combo = ttk.Combobox(row2, textvariable=self.template_type_var, width=18, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_template_type_changed)

        ttk.Label(row2, text="Ранг:", width=6).pack(side=tk.LEFT, padx=(20, 0))
        self.template_rank_var = tk.IntVar(value=1)
        rank_combo = ttk.Combobox(row2, textvariable=self.template_rank_var, width=5, state='readonly')
        rank_combo['values'] = self.RANKS
        rank_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="Отношение:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.template_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row2, textvariable=self.template_relation_var, width=15, state='readonly')
        rel_combo['values'] = [f"{r[0]}" for r in self.RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        # Спрайт с превью
        sprite_frame = ttk.LabelFrame(parent, text="Спрайт", padding=5)
        sprite_frame.pack(fill=tk.X, pady=5)

        sprite_inner = ttk.Frame(sprite_frame)
        sprite_inner.pack(fill=tk.X)

        self.template_sprite_var = tk.StringVar()
        self.template_sprite_combo = ttk.Combobox(sprite_inner, textvariable=self.template_sprite_var, width=25, state='readonly')
        self.template_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.template_sprite_combo.bind('<<ComboboxSelected>>', self.on_template_sprite_changed)

        self.template_sprite_label = ttk.Label(sprite_inner, text="[превью]")
        self.template_sprite_label.pack(side=tk.LEFT, padx=20)

        # Распределение характеристик
        stats_frame = ttk.LabelFrame(parent, text="Распределение характеристик (%, сумма = 100%)", padding=5)
        stats_frame.pack(fill=tk.X, pady=5)

        self.template_stats_vars = {}
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)

        # Два ряда по 3 стата
        for i, (stat_id, stat_name, stat_short) in enumerate(self.STATS):
            row_idx = i // 3
            col_idx = i % 3

            if col_idx == 0:
                stat_row = ttk.Frame(stats_container)
                stat_row.pack(fill=tk.X, pady=2)

            stat_frame = ttk.Frame(stat_row)
            stat_frame.pack(side=tk.LEFT, padx=10, expand=True)

            ttk.Label(stat_frame, text=f"{stat_short}:", width=5).pack(side=tk.LEFT)
            var = tk.IntVar(value=16)  # По умолчанию равномерно ~16.67%
            self.template_stats_vars[stat_id] = var

            spinbox = ttk.Spinbox(stat_frame, from_=0, to=100, textvariable=var, width=5,
                                  command=lambda: self.update_stats_total())
            spinbox.pack(side=tk.LEFT, padx=2)
            ttk.Label(stat_frame, text="%").pack(side=tk.LEFT)

        # Показатель суммы
        self.stats_total_var = tk.StringVar(value="Сумма: 96%")
        ttk.Label(stats_frame, textvariable=self.stats_total_var, font=('Arial', 10, 'bold')).pack(pady=5)

        # Золото
        gold_frame = ttk.LabelFrame(parent, text="Золото", padding=5)
        gold_frame.pack(fill=tk.X, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X)

        ttk.Label(gold_row, text="Базовое количество:").pack(side=tk.LEFT)
        self.template_gold_base_var = tk.IntVar(value=10)
        ttk.Spinbox(gold_row, from_=0, to=10000, textvariable=self.template_gold_base_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(gold_row, text="Разброс ±%:").pack(side=tk.LEFT, padx=(20, 0))
        self.template_gold_variance_var = tk.IntVar(value=20)
        ttk.Spinbox(gold_row, from_=0, to=100, textvariable=self.template_gold_variance_var, width=5).pack(side=tk.LEFT, padx=5)

        # Кнопка применить
        ttk.Button(parent, text="✓ Применить изменения", command=self.apply_template_changes).pack(pady=10)

    def create_template_loot_skills(self, parent):
        """Создание настроек лута и умений"""
        # Notebook для лута и умений
        loot_notebook = ttk.Notebook(parent)
        loot_notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка лута
        loot_frame = ttk.Frame(loot_notebook, padding=5)
        loot_notebook.add(loot_frame, text="Лут по качеству")

        self.template_loot_vars = {}

        for loot_type_id, loot_type_name in self.LOOT_TYPES:
            type_frame = ttk.LabelFrame(loot_frame, text=loot_type_name, padding=3)
            type_frame.pack(fill=tk.X, pady=3)

            self.template_loot_vars[loot_type_id] = {}

            # Общий шанс выпадения типа
            chance_row = ttk.Frame(type_frame)
            chance_row.pack(fill=tk.X)

            ttk.Label(chance_row, text="Шанс выпадения:").pack(side=tk.LEFT)
            type_chance_var = tk.IntVar(value=30)
            self.template_loot_vars[loot_type_id]['_chance'] = type_chance_var
            ttk.Spinbox(chance_row, from_=0, to=100, textvariable=type_chance_var, width=5).pack(side=tk.LEFT, padx=5)
            ttk.Label(chance_row, text="%").pack(side=tk.LEFT)

            # Качества с чекбоксами
            quality_frame = ttk.Frame(type_frame)
            quality_frame.pack(fill=tk.X, pady=2)

            for qual_id, qual_name, qual_color in self.QUALITY_LEVELS:
                qual_frame = ttk.Frame(quality_frame)
                qual_frame.pack(side=tk.LEFT, padx=3)

                enabled_var = tk.BooleanVar(value=True if qual_id in ['common', 'uncommon'] else False)
                weight_var = tk.IntVar(value=50 if qual_id == 'common' else 30 if qual_id == 'uncommon' else 10)

                cb = ttk.Checkbutton(qual_frame, text=qual_name[:3], variable=enabled_var)
                cb.pack(side=tk.LEFT)

                spinbox = ttk.Spinbox(qual_frame, from_=0, to=100, textvariable=weight_var, width=3)
                spinbox.pack(side=tk.LEFT)

                self.template_loot_vars[loot_type_id][qual_id] = (enabled_var, weight_var)

        # Вкладка умений
        skills_frame = ttk.Frame(loot_notebook, padding=5)
        loot_notebook.add(skills_frame, text="Умения")

        # Создаём canvas со скроллом для умений
        skills_canvas = tk.Canvas(skills_frame, height=300)
        skills_scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=skills_canvas.yview)
        skills_inner = ttk.Frame(skills_canvas)

        skills_inner.bind("<Configure>", lambda e: skills_canvas.configure(scrollregion=skills_canvas.bbox("all")))
        skills_canvas.create_window((0, 0), window=skills_inner, anchor="nw")
        skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        skills_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        skills_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязка скролла мыши только к этому canvas
        def on_mousewheel(event):
            skills_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        skills_canvas.bind("<MouseWheel>", on_mousewheel)
        skills_canvas.bind("<Enter>", lambda e: skills_canvas.bind_all("<MouseWheel>", on_mousewheel))
        skills_canvas.bind("<Leave>", lambda e: skills_canvas.unbind_all("<MouseWheel>"))

        self.template_skills_vars = {}

        # Группировка по категориям
        categories = {
            'combat': 'Ближний бой',
            'magic': 'Магия',
            'ranged': 'Дальний бой',
            'stealth': 'Скрытность',
            'weapon': 'Оружейные'
        }

        for cat_id, cat_name in categories.items():
            cat_frame = ttk.LabelFrame(skills_inner, text=cat_name, padding=3)
            cat_frame.pack(fill=tk.X, pady=2, padx=5)

            cat_skills = [s for s in self.SKILLS if s[2] == cat_id]
            for skill_id, skill_name, _ in cat_skills:
                skill_row = ttk.Frame(cat_frame)
                skill_row.pack(fill=tk.X, pady=1)

                enabled_var = tk.BooleanVar(value=False)
                rank_var = tk.IntVar(value=1)

                ttk.Checkbutton(skill_row, text=skill_name, variable=enabled_var, width=20).pack(side=tk.LEFT)
                ttk.Label(skill_row, text="Ранг:").pack(side=tk.LEFT, padx=(10, 2))
                ttk.Spinbox(skill_row, from_=1, to=5, textvariable=rank_var, width=3).pack(side=tk.LEFT)

                self.template_skills_vars[skill_id] = (enabled_var, rank_var)

    def update_stats_total(self):
        """Обновление суммы распределения статов"""
        total = sum(var.get() for var in self.template_stats_vars.values())
        color = "green" if total == 100 else "red"
        self.stats_total_var.set(f"Сумма: {total}%")

    def refresh_template_list(self):
        """Обновление списка шаблонов"""
        self.template_listbox.delete(0, tk.END)
        for template in self.npc_templates:
            npc_type = template.get('type', 'unknown')
            type_name = dict(self.NPC_TYPES).get(npc_type, npc_type)
            rank = template.get('rank', 1)
            display_name = f"[R{rank}] {template.get('name', 'Без имени')} ({type_name})"
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
        self.template_id_var.set(template.get('id', ''))
        self.template_name_var.set(template.get('name', ''))

        npc_type = template.get('type', 'guard')
        for type_id, type_name in self.NPC_TYPES:
            if type_id == npc_type:
                self.template_type_var.set(f"{type_id} - {type_name}")
                break

        self.template_rank_var.set(template.get('rank', 1))
        self.template_relation_var.set(template.get('relationship', 'neutral'))

        # Распределение статов
        stat_dist = template.get('stat_distribution', {})
        for stat_id, var in self.template_stats_vars.items():
            var.set(stat_dist.get(stat_id, 16))
        self.update_stats_total()

        # Золото
        gold = template.get('gold', {})
        self.template_gold_base_var.set(gold.get('base', 10))
        self.template_gold_variance_var.set(gold.get('variance_percent', 20))

        # Лут
        loot = template.get('loot', {})
        for loot_type_id, quality_vars in self.template_loot_vars.items():
            type_loot = loot.get(loot_type_id, {})

            if '_chance' in quality_vars:
                quality_vars['_chance'].set(type_loot.get('chance', 30))

            for qual_id in [q[0] for q in self.QUALITY_LEVELS]:
                if qual_id in quality_vars:
                    enabled_var, weight_var = quality_vars[qual_id]
                    qual_data = type_loot.get('qualities', {}).get(qual_id, {})
                    enabled_var.set(qual_data.get('enabled', False))
                    weight_var.set(qual_data.get('weight', 10))

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
        self.update_sprite_combo_for_type(npc_type)
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
            for file in sorted(os.listdir(sprite_path)):
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
                img = img.resize((48, 48), Image.Resampling.NEAREST)
                self.current_sprite_image = ImageTk.PhotoImage(img)
                self.template_sprite_label.configure(image=self.current_sprite_image)
            except Exception as e:
                print(f"Ошибка загрузки спрайта: {e}")

    def add_template(self):
        """Добавление нового шаблона"""
        new_id = f'template_{len(self.npc_templates) + 1}'

        # Проверка уникальности ID
        existing_ids = [t.get('id', '') for t in self.npc_templates]
        counter = 1
        while new_id in existing_ids:
            counter += 1
            new_id = f'template_{len(self.npc_templates) + counter}'

        new_template = {
            'id': new_id,
            'name': 'Новый NPC',
            'type': 'guard',
            'rank': 1,
            'relationship': 'neutral',
            'stat_distribution': {stat_id: 16 for stat_id, _, _ in self.STATS},
            'gold': {'base': 10, 'variance_percent': 20},
            'loot': {},
            'skills': {},
            'sprite': 'soldier/soldier1.png'
        }

        # Корректируем сумму до 100
        new_template['stat_distribution']['luck'] = 20

        self.npc_templates.append(new_template)
        self.refresh_template_list()

        self.template_listbox.selection_clear(0, tk.END)
        self.template_listbox.selection_set(len(self.npc_templates) - 1)
        self.template_listbox.see(len(self.npc_templates) - 1)
        self.load_template_to_editor(new_template)

    def delete_template(self):
        """Удаление шаблона"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите шаблон для удаления")
            return

        index = selection[0]
        template_name = self.npc_templates[index].get('name', 'Без имени')
        if messagebox.askyesno("Подтверждение", f"Удалить шаблон '{template_name}'?"):
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

        new_template = copy.deepcopy(original)
        new_template['id'] = f"{original['id']}_copy"
        new_template['name'] = f"{original['name']} (копия)"

        # Проверка уникальности ID
        existing_ids = [t.get('id', '') for t in self.npc_templates]
        counter = 1
        while new_template['id'] in existing_ids:
            counter += 1
            new_template['id'] = f"{original['id']}_copy{counter}"

        self.npc_templates.append(new_template)
        self.refresh_template_list()

    def apply_template_changes(self):
        """Применение изменений к шаблону"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите шаблон для редактирования")
            return

        # Валидация суммы статов
        stats_total = sum(var.get() for var in self.template_stats_vars.values())
        if stats_total != 100:
            messagebox.showerror("Ошибка", f"Сумма распределения статов должна быть 100%\nТекущая сумма: {stats_total}%")
            return

        index = selection[0]
        template = self.npc_templates[index]

        # Основные поля
        new_id = self.template_id_var.get().strip()
        if not new_id:
            messagebox.showerror("Ошибка", "ID не может быть пустым")
            return

        # Проверка уникальности ID (исключая текущий шаблон)
        for i, t in enumerate(self.npc_templates):
            if i != index and t.get('id') == new_id:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                return

        template['id'] = new_id
        template['name'] = self.template_name_var.get()

        type_str = self.template_type_var.get()
        if ' - ' in type_str:
            template['type'] = type_str.split(' - ')[0]

        template['rank'] = self.template_rank_var.get()
        template['relationship'] = self.template_relation_var.get()

        # Распределение статов
        template['stat_distribution'] = {}
        for stat_id, var in self.template_stats_vars.items():
            template['stat_distribution'][stat_id] = var.get()

        # Золото
        template['gold'] = {
            'base': self.template_gold_base_var.get(),
            'variance_percent': self.template_gold_variance_var.get()
        }

        # Лут
        template['loot'] = {}
        for loot_type_id, quality_vars in self.template_loot_vars.items():
            type_loot = {'qualities': {}}

            if '_chance' in quality_vars:
                type_loot['chance'] = quality_vars['_chance'].get()

            for qual_id in [q[0] for q in self.QUALITY_LEVELS]:
                if qual_id in quality_vars:
                    enabled_var, weight_var = quality_vars[qual_id]
                    if enabled_var.get():
                        type_loot['qualities'][qual_id] = {
                            'enabled': True,
                            'weight': weight_var.get()
                        }

            if type_loot['qualities']:
                template['loot'][loot_type_id] = type_loot

        # Умения
        template['skills'] = {}
        for skill_id, (enabled_var, rank_var) in self.template_skills_vars.items():
            if enabled_var.get():
                template['skills'][skill_id] = {'rank': rank_var.get()}

        # Спрайт
        template['sprite'] = self.template_sprite_var.get()

        self.refresh_template_list()
        messagebox.showinfo("Готово", "Изменения применены")

    # ==================== УНИКАЛЬНЫЕ NPC ====================

    def create_unique_tab(self):
        """Создание вкладки уникальных NPC с оптимизированным layout"""
        main_container = ttk.Frame(self.unique_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая колонка - список
        left_frame = ttk.LabelFrame(main_container, text="Уникальные NPC", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.unique_listbox = tk.Listbox(left_frame, width=35, height=25, font=('Arial', 10))
        self.unique_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.unique_listbox.bind('<<ListboxSelect>>', self.on_unique_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Копия", command=self.duplicate_unique).pack(side=tk.LEFT, padx=2)

        # Центральная колонка - основные настройки
        center_frame = ttk.LabelFrame(main_container, text="Основные настройки", padding=5)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.create_unique_basic_settings(center_frame)

        # Правая колонка - лут и умения
        right_frame = ttk.LabelFrame(main_container, text="Экипировка и Умения", padding=5)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.create_unique_loot_skills(right_frame)

        self.refresh_unique_list()

    def create_unique_basic_settings(self, parent):
        """Создание основных настроек уникального NPC"""
        # ID, Имя, Описание
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="ID:", width=10).pack(side=tk.LEFT)
        self.unique_id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.unique_id_var, width=25).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Имя:", width=6).pack(side=tk.LEFT, padx=(10, 0))
        self.unique_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.unique_name_var, width=25).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="Описание:").pack(side=tk.LEFT)
        self.unique_desc_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.unique_desc_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Тип, Уровень, Отношение
        row3 = ttk.Frame(parent)
        row3.pack(fill=tk.X, pady=2)

        ttk.Label(row3, text="Тип NPC:", width=10).pack(side=tk.LEFT)
        self.unique_type_var = tk.StringVar()
        type_combo = ttk.Combobox(row3, textvariable=self.unique_type_var, width=18, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_unique_type_changed)

        ttk.Label(row3, text="Уровень:", width=8).pack(side=tk.LEFT, padx=(10, 0))
        self.unique_level_var = tk.IntVar(value=10)
        ttk.Spinbox(row3, from_=1, to=100, textvariable=self.unique_level_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(row3, text="Отношение:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.unique_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row3, textvariable=self.unique_relation_var, width=12, state='readonly')
        rel_combo['values'] = [r[0] for r in self.RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        # Позиция и Диалог
        row4 = ttk.Frame(parent)
        row4.pack(fill=tk.X, pady=2)

        ttk.Label(row4, text="Позиция X:").pack(side=tk.LEFT)
        self.unique_x_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=500, textvariable=self.unique_x_var, width=6).pack(side=tk.LEFT, padx=5)

        ttk.Label(row4, text="Y:").pack(side=tk.LEFT)
        self.unique_y_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=500, textvariable=self.unique_y_var, width=6).pack(side=tk.LEFT, padx=5)

        ttk.Label(row4, text="ID Диалога:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.unique_dialog_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.unique_dialog_var, width=20).pack(side=tk.LEFT, padx=5)

        # Спрайт
        sprite_frame = ttk.LabelFrame(parent, text="Спрайт", padding=5)
        sprite_frame.pack(fill=tk.X, pady=5)

        sprite_inner = ttk.Frame(sprite_frame)
        sprite_inner.pack(fill=tk.X)

        self.unique_sprite_var = tk.StringVar()
        self.unique_sprite_combo = ttk.Combobox(sprite_inner, textvariable=self.unique_sprite_var, width=25, state='readonly')
        self.unique_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.unique_sprite_combo.bind('<<ComboboxSelected>>', self.on_unique_sprite_changed)

        self.unique_sprite_label = ttk.Label(sprite_inner, text="[превью]")
        self.unique_sprite_label.pack(side=tk.LEFT, padx=20)

        # Характеристики (фиксированные значения)
        stats_frame = ttk.LabelFrame(parent, text="Характеристики (фиксированные)", padding=5)
        stats_frame.pack(fill=tk.X, pady=5)

        self.unique_stats_vars = {}
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)

        for i, (stat_id, stat_name, stat_short) in enumerate(self.STATS):
            row_idx = i // 3
            col_idx = i % 3

            if col_idx == 0:
                stat_row = ttk.Frame(stats_container)
                stat_row.pack(fill=tk.X, pady=2)

            stat_frame = ttk.Frame(stat_row)
            stat_frame.pack(side=tk.LEFT, padx=15, expand=True)

            ttk.Label(stat_frame, text=f"{stat_name}:", width=12).pack(side=tk.LEFT)
            var = tk.IntVar(value=10)
            self.unique_stats_vars[stat_id] = var
            ttk.Spinbox(stat_frame, from_=1, to=100, textvariable=var, width=5).pack(side=tk.LEFT, padx=2)

        # Золото
        gold_frame = ttk.LabelFrame(parent, text="Гарантированное золото", padding=5)
        gold_frame.pack(fill=tk.X, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X)

        ttk.Label(gold_row, text="Количество:").pack(side=tk.LEFT)
        self.unique_gold_var = tk.IntVar(value=100)
        ttk.Spinbox(gold_row, from_=0, to=100000, textvariable=self.unique_gold_var, width=10).pack(side=tk.LEFT, padx=5)

        # Кнопка применить
        ttk.Button(parent, text="✓ Применить изменения", command=self.apply_unique_changes).pack(pady=10)

    def create_unique_loot_skills(self, parent):
        """Создание настроек экипировки и умений для уникального NPC"""
        loot_notebook = ttk.Notebook(parent)
        loot_notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка экипировки
        equip_frame = ttk.Frame(loot_notebook, padding=5)
        loot_notebook.add(equip_frame, text="Экипировка")

        self.unique_equip_vars = {}

        equip_types = [
            ("weapon", "Оружие"),
            ("light_armor", "Лёгкая броня"),
            ("medium_armor", "Средняя броня"),
            ("heavy_armor", "Тяжёлая броня"),
            ("amulet", "Амулет"),
            ("ring", "Кольцо"),
            ("bracelet", "Браслет"),
        ]

        for equip_id, equip_name in equip_types:
            row = ttk.Frame(equip_frame)
            row.pack(fill=tk.X, pady=3)

            enabled_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(row, text=equip_name, variable=enabled_var, width=15).pack(side=tk.LEFT)

            ttk.Label(row, text="Качество:").pack(side=tk.LEFT, padx=(10, 5))
            quality_var = tk.StringVar(value="rare")
            qual_combo = ttk.Combobox(row, textvariable=quality_var, width=12, state='readonly')
            qual_combo['values'] = [q[0] for q in self.QUALITY_LEVELS]
            qual_combo.pack(side=tk.LEFT)

            self.unique_equip_vars[equip_id] = (enabled_var, quality_var)

        # Вкладка умений
        skills_frame = ttk.Frame(loot_notebook, padding=5)
        loot_notebook.add(skills_frame, text="Умения")

        skills_canvas = tk.Canvas(skills_frame, height=250)
        skills_scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=skills_canvas.yview)
        skills_inner = ttk.Frame(skills_canvas)

        skills_inner.bind("<Configure>", lambda e: skills_canvas.configure(scrollregion=skills_canvas.bbox("all")))
        skills_canvas.create_window((0, 0), window=skills_inner, anchor="nw")
        skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        skills_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        skills_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def on_mousewheel(event):
            skills_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        skills_canvas.bind("<Enter>", lambda e: skills_canvas.bind_all("<MouseWheel>", on_mousewheel))
        skills_canvas.bind("<Leave>", lambda e: skills_canvas.unbind_all("<MouseWheel>"))

        self.unique_skills_vars = {}

        categories = {
            'combat': 'Ближний бой',
            'magic': 'Магия',
            'ranged': 'Дальний бой',
            'stealth': 'Скрытность',
            'weapon': 'Оружейные'
        }

        for cat_id, cat_name in categories.items():
            cat_frame = ttk.LabelFrame(skills_inner, text=cat_name, padding=3)
            cat_frame.pack(fill=tk.X, pady=2, padx=5)

            cat_skills = [s for s in self.SKILLS if s[2] == cat_id]
            for skill_id, skill_name, _ in cat_skills:
                skill_row = ttk.Frame(cat_frame)
                skill_row.pack(fill=tk.X, pady=1)

                enabled_var = tk.BooleanVar(value=False)
                rank_var = tk.IntVar(value=1)

                ttk.Checkbutton(skill_row, text=skill_name, variable=enabled_var, width=20).pack(side=tk.LEFT)
                ttk.Label(skill_row, text="Ранг:").pack(side=tk.LEFT, padx=(10, 2))
                ttk.Spinbox(skill_row, from_=1, to=5, textvariable=rank_var, width=3).pack(side=tk.LEFT)

                self.unique_skills_vars[skill_id] = (enabled_var, rank_var)

    def refresh_unique_list(self):
        """Обновление списка уникальных NPC"""
        self.unique_listbox.delete(0, tk.END)
        for npc in self.unique_npcs:
            level = npc.get('level', 1)
            npc_type = npc.get('type', 'unknown')
            type_name = dict(self.NPC_TYPES).get(npc_type, npc_type)
            display_name = f"[Lv{level}] {npc.get('name', 'Без имени')} ({type_name})"
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

        npc_type = npc.get('type', 'guard')
        for type_id, type_name in self.NPC_TYPES:
            if type_id == npc_type:
                self.unique_type_var.set(f"{type_id} - {type_name}")
                break

        self.unique_level_var.set(npc.get('level', 10))
        self.unique_relation_var.set(npc.get('relationship', 'neutral'))

        pos = npc.get('position', {'x': 100, 'y': 100})
        self.unique_x_var.set(pos.get('x', 100))
        self.unique_y_var.set(pos.get('y', 100))

        self.unique_dialog_var.set(npc.get('dialog_id', ''))
        self.unique_gold_var.set(npc.get('gold', 100))

        # Статы
        stats = npc.get('stats', {})
        for stat_id, var in self.unique_stats_vars.items():
            var.set(stats.get(stat_id, 10))

        # Экипировка
        equipment = npc.get('equipment', {})
        for equip_id, (enabled_var, quality_var) in self.unique_equip_vars.items():
            if equip_id in equipment:
                enabled_var.set(True)
                quality_var.set(equipment[equip_id].get('quality', 'rare'))
            else:
                enabled_var.set(False)

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
        self.update_unique_sprite_combo(npc_type)
        sprite = npc.get('sprite', '')
        if sprite:
            self.unique_sprite_var.set(sprite)
            self.load_unique_sprite_preview(sprite)

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
            for file in sorted(os.listdir(sprite_path)):
                if file.endswith('.png'):
                    sprites.append(f"{folder}/{file}")

        self.unique_sprite_combo['values'] = sprites
        if sprites:
            self.unique_sprite_var.set(sprites[0])
            self.load_unique_sprite_preview(sprites[0])

    def on_unique_sprite_changed(self, event):
        """Обработка смены спрайта"""
        sprite = self.unique_sprite_var.get()
        self.load_unique_sprite_preview(sprite)

    def load_unique_sprite_preview(self, sprite_path):
        """Загрузка превью спрайта уникального NPC"""
        full_path = os.path.join(self.assets_path, sprite_path)
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                img = img.resize((48, 48), Image.Resampling.NEAREST)
                self.unique_sprite_image = ImageTk.PhotoImage(img)
                self.unique_sprite_label.configure(image=self.unique_sprite_image)
            except Exception as e:
                print(f"Ошибка загрузки спрайта: {e}")

    def add_unique(self):
        """Добавление нового уникального NPC"""
        new_id = f'unique_{len(self.unique_npcs) + 1}'

        existing_ids = [n.get('id', '') for n in self.unique_npcs]
        counter = 1
        while new_id in existing_ids:
            counter += 1
            new_id = f'unique_{len(self.unique_npcs) + counter}'

        new_npc = {
            'id': new_id,
            'name': 'Новый уникальный NPC',
            'description': 'Описание NPC',
            'type': 'guard',
            'level': 10,
            'relationship': 'neutral',
            'position': {'x': 100, 'y': 100},
            'stats': {stat_id: 10 for stat_id, _, _ in self.STATS},
            'gold': 100,
            'equipment': {},
            'skills': {},
            'sprite': 'soldier/soldier1.png',
            'dialog_id': ''
        }
        self.unique_npcs.append(new_npc)
        self.refresh_unique_list()

        self.unique_listbox.selection_clear(0, tk.END)
        self.unique_listbox.selection_set(len(self.unique_npcs) - 1)
        self.unique_listbox.see(len(self.unique_npcs) - 1)
        self.load_unique_to_editor(new_npc)

    def delete_unique(self):
        """Удаление уникального NPC"""
        selection = self.unique_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите NPC для удаления")
            return

        index = selection[0]
        npc_name = self.unique_npcs[index].get('name', 'Без имени')
        if messagebox.askyesno("Подтверждение", f"Удалить NPC '{npc_name}'?"):
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

        new_npc = copy.deepcopy(original)
        new_npc['id'] = f"{original['id']}_copy"
        new_npc['name'] = f"{original['name']} (копия)"

        existing_ids = [n.get('id', '') for n in self.unique_npcs]
        counter = 1
        while new_npc['id'] in existing_ids:
            counter += 1
            new_npc['id'] = f"{original['id']}_copy{counter}"

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

        new_id = self.unique_id_var.get().strip()
        if not new_id:
            messagebox.showerror("Ошибка", "ID не может быть пустым")
            return

        for i, n in enumerate(self.unique_npcs):
            if i != index and n.get('id') == new_id:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                return

        npc['id'] = new_id
        npc['name'] = self.unique_name_var.get()
        npc['description'] = self.unique_desc_var.get()

        type_str = self.unique_type_var.get()
        if ' - ' in type_str:
            npc['type'] = type_str.split(' - ')[0]

        npc['level'] = self.unique_level_var.get()
        npc['relationship'] = self.unique_relation_var.get()

        npc['position'] = {
            'x': self.unique_x_var.get(),
            'y': self.unique_y_var.get()
        }

        npc['dialog_id'] = self.unique_dialog_var.get()
        npc['gold'] = self.unique_gold_var.get()

        # Статы
        npc['stats'] = {}
        for stat_id, var in self.unique_stats_vars.items():
            npc['stats'][stat_id] = var.get()

        # Экипировка
        npc['equipment'] = {}
        for equip_id, (enabled_var, quality_var) in self.unique_equip_vars.items():
            if enabled_var.get():
                npc['equipment'][equip_id] = {'quality': quality_var.get()}

        # Умения
        npc['skills'] = {}
        for skill_id, (enabled_var, rank_var) in self.unique_skills_vars.items():
            if enabled_var.get():
                npc['skills'][skill_id] = {'rank': rank_var.get()}

        npc['sprite'] = self.unique_sprite_var.get()

        self.refresh_unique_list()
        messagebox.showinfo("Готово", "Изменения применены")


def main():
    """Главная функция"""
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use('clam')

    # Настройка шрифтов
    style.configure('TLabel', font=('Arial', 10))
    style.configure('TButton', font=('Arial', 10))
    style.configure('TCheckbutton', font=('Arial', 9))

    app = NPCConfigEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
