#!/usr/bin/env python3
"""
NPC Config Editor v2.1 - Утилита для создания и настройки NPC
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
        ("poor", "Плохое"),
        ("common", "Обычное"),
        ("uncommon", "Необычное"),
        ("rare", "Редкое"),
        ("epic", "Эпическое"),
        ("legendary", "Легендарное"),
        ("artifact", "Артефакт"),
    ]

    LOOT_CATEGORIES = [
        ("weapon", "Оружие"),
        ("armor", "Броня"),
        ("jewelry", "Украшения"),
        ("potion", "Зелья"),
        ("material", "Материалы"),
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

    def __init__(self, root):
        self.root = root
        self.root.title("NPC Config Editor v2.1")

        # Развёрнутое окно (не полноэкранное, с панелью задач)
        # Для разрешения 1920x1200 с учётом панели задач (~40px)
        self.root.state('zoomed')  # Для Windows - развёрнутое окно
        self.root.minsize(1600, 900)

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
        errors = self.validate_all_data()
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return

        os.makedirs(self.config_path, exist_ok=True)

        npc_data = {
            "_description": "Конфигурация типовых NPC для карты",
            "_version": "2.1.0",
            "templates": self.npc_templates
        }
        with open(self.npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(npc_data, f, ensure_ascii=False, indent=2)

        uniq_data = {
            "_description": "Конфигурация уникальных NPC для карты",
            "_version": "2.1.0",
            "unique_npcs": self.unique_npcs
        }
        with open(self.uniq_npc_config_file, 'w', encoding='utf-8') as f:
            json.dump(uniq_data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Сохранено", f"Конфиги сохранены:\n{self.npc_config_file}\n{self.uniq_npc_config_file}")

    def validate_all_data(self):
        """Валидация всех данных"""
        errors = []

        template_ids = [t.get('id', '') for t in self.npc_templates]
        duplicates = set([x for x in template_ids if template_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID шаблонов: {', '.join(duplicates)}")

        unique_ids = [n.get('id', '') for n in self.unique_npcs]
        duplicates = set([x for x in unique_ids if unique_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Дублирующиеся ID уникальных NPC: {', '.join(duplicates)}")

        for template in self.npc_templates:
            stat_dist = template.get('stat_distribution', {})
            total = sum(stat_dist.values())
            if stat_dist and abs(total - 100) > 0.1:
                errors.append(f"Шаблон '{template.get('id')}': сумма статов = {total}% (должно быть 100%)")

        return errors

    def create_ui(self):
        """Создание пользовательского интерфейса"""
        # Верхняя панель
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="NPC Config Editor", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Выход", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Сохранить всё", command=self.save_configs).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Перезагрузить", command=self.reload_configs).pack(side=tk.RIGHT, padx=5)

        # Главный notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Вкладки
        self.template_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.template_frame, text="  Типовые NPC  ")
        self.create_template_tab()

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
        """Создание вкладки типовых NPC"""
        main_paned = ttk.PanedWindow(self.template_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - список шаблонов
        left_frame = ttk.LabelFrame(main_paned, text="Список шаблонов", padding=5)
        main_paned.add(left_frame, weight=1)

        self.template_listbox = tk.Listbox(left_frame, width=35, font=('Arial', 10))
        self.template_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Копировать", command=self.duplicate_template).pack(side=tk.LEFT, padx=2)

        # Правая панель - редактор (с прокруткой)
        right_container = ttk.Frame(main_paned)
        main_paned.add(right_container, weight=4)

        # Canvas для прокрутки
        canvas = tk.Canvas(right_container)
        scrollbar_y = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(right_container, orient="horizontal", command=canvas.xview)

        self.template_editor_frame = ttk.Frame(canvas)

        self.template_editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.template_editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Привязка скролла мыши
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.create_template_editor()
        self.refresh_template_list()

    def create_template_editor(self):
        """Создание редактора шаблона NPC"""
        parent = self.template_editor_frame

        # ===== Блок: Основная информация =====
        info_frame = ttk.LabelFrame(parent, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Строка 1: ID и Название
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="Идентификатор:", width=15).pack(side=tk.LEFT)
        self.template_id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.template_id_var, width=25).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Название:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.template_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.template_name_var, width=30).pack(side=tk.LEFT, padx=5)

        # Строка 2: Тип, Ранг, Отношение
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=3)

        ttk.Label(row2, text="Тип NPC:", width=15).pack(side=tk.LEFT)
        self.template_type_var = tk.StringVar()
        type_combo = ttk.Combobox(row2, textvariable=self.template_type_var, width=22, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_template_type_changed)

        ttk.Label(row2, text="Ранг:", width=8).pack(side=tk.LEFT, padx=(20, 0))
        self.template_rank_var = tk.IntVar(value=1)
        rank_combo = ttk.Combobox(row2, textvariable=self.template_rank_var, width=5, state='readonly')
        rank_combo['values'] = self.RANKS
        rank_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="Отношение к игроку:", width=18).pack(side=tk.LEFT, padx=(20, 0))
        self.template_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row2, textvariable=self.template_relation_var, width=15, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in self.RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        # Строка 3: Спрайт
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=3)

        ttk.Label(row3, text="Спрайт:", width=15).pack(side=tk.LEFT)
        self.template_sprite_var = tk.StringVar()
        self.template_sprite_combo = ttk.Combobox(row3, textvariable=self.template_sprite_var, width=30, state='readonly')
        self.template_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.template_sprite_combo.bind('<<ComboboxSelected>>', self.on_template_sprite_changed)

        self.template_sprite_label = ttk.Label(row3)
        self.template_sprite_label.pack(side=tk.LEFT, padx=20)

        # ===== Блок: Распределение характеристик =====
        stats_frame = ttk.LabelFrame(parent, text="Распределение характеристик (в процентах, сумма должна быть 100%)", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.template_stats_vars = {}
        stats_row = ttk.Frame(stats_frame)
        stats_row.pack(fill=tk.X, pady=5)

        for i, (stat_id, stat_name) in enumerate(self.STATS):
            stat_frame = ttk.Frame(stats_row)
            stat_frame.pack(side=tk.LEFT, padx=15)

            ttk.Label(stat_frame, text=f"{stat_name}:").pack(side=tk.LEFT)
            var = tk.IntVar(value=16)
            self.template_stats_vars[stat_id] = var
            spinbox = ttk.Spinbox(stat_frame, from_=0, to=100, textvariable=var, width=5,
                                  command=self.update_stats_total)
            spinbox.pack(side=tk.LEFT, padx=3)
            spinbox.bind('<KeyRelease>', lambda e: self.update_stats_total())
            ttk.Label(stat_frame, text="%").pack(side=tk.LEFT)

        # Индикатор суммы
        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(fill=tk.X, pady=5)
        self.stats_total_var = tk.StringVar(value="Сумма: 96%")
        self.stats_total_label = ttk.Label(total_frame, textvariable=self.stats_total_var, font=('Arial', 11, 'bold'))
        self.stats_total_label.pack(side=tk.LEFT)

        # ===== Блок: Деньги =====
        gold_frame = ttk.LabelFrame(parent, text="Деньги", padding=10)
        gold_frame.pack(fill=tk.X, padx=5, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X, pady=3)

        ttk.Label(gold_row, text="Шанс выпадения:").pack(side=tk.LEFT)
        self.template_gold_chance_var = tk.IntVar(value=80)
        ttk.Spinbox(gold_row, from_=0, to=100, textvariable=self.template_gold_chance_var, width=5).pack(side=tk.LEFT, padx=3)
        ttk.Label(gold_row, text="%").pack(side=tk.LEFT)

        ttk.Label(gold_row, text="Базовая сумма:").pack(side=tk.LEFT, padx=(30, 0))
        self.template_gold_base_var = tk.IntVar(value=10)
        ttk.Spinbox(gold_row, from_=0, to=10000, textvariable=self.template_gold_base_var, width=8).pack(side=tk.LEFT, padx=3)

        ttk.Label(gold_row, text="Коэффициент от уровня:").pack(side=tk.LEFT, padx=(30, 0))
        self.template_gold_level_mult_var = tk.DoubleVar(value=1.5)
        ttk.Spinbox(gold_row, from_=0.0, to=10.0, increment=0.1, textvariable=self.template_gold_level_mult_var, width=6).pack(side=tk.LEFT, padx=3)

        ttk.Label(gold_row, text="Разброс:").pack(side=tk.LEFT, padx=(30, 0))
        self.template_gold_variance_var = tk.IntVar(value=20)
        ttk.Spinbox(gold_row, from_=0, to=100, textvariable=self.template_gold_variance_var, width=5).pack(side=tk.LEFT, padx=3)
        ttk.Label(gold_row, text="%").pack(side=tk.LEFT)

        # Пояснение формулы
        ttk.Label(gold_frame, text="Формула: (Базовая сумма + Уровень × Коэффициент) ± Разброс%",
                  font=('Arial', 9, 'italic')).pack(anchor=tk.W, pady=3)

        # ===== Блок: Лут =====
        loot_frame = ttk.LabelFrame(parent, text="Выпадение предметов", padding=10)
        loot_frame.pack(fill=tk.X, padx=5, pady=5)

        # Максимальное количество предметов
        max_items_row = ttk.Frame(loot_frame)
        max_items_row.pack(fill=tk.X, pady=5)
        ttk.Label(max_items_row, text="Максимальное количество выпадающих предметов:").pack(side=tk.LEFT)
        self.template_max_loot_var = tk.IntVar(value=3)
        ttk.Spinbox(max_items_row, from_=0, to=10, textvariable=self.template_max_loot_var, width=5).pack(side=tk.LEFT, padx=5)

        # Категории лута
        self.template_loot_vars = {}

        for cat_id, cat_name in self.LOOT_CATEGORIES:
            cat_frame = ttk.LabelFrame(loot_frame, text=cat_name, padding=5)
            cat_frame.pack(fill=tk.X, pady=5)

            self.template_loot_vars[cat_id] = {'qualities': {}}

            # Заголовок категории с чекбоксом
            header_row = ttk.Frame(cat_frame)
            header_row.pack(fill=tk.X, pady=2)

            cat_enabled_var = tk.BooleanVar(value=True)
            self.template_loot_vars[cat_id]['enabled'] = cat_enabled_var
            ttk.Checkbutton(header_row, text=f"Разрешить выпадение категории \"{cat_name}\"",
                           variable=cat_enabled_var).pack(side=tk.LEFT)

            # Качества
            qualities_row = ttk.Frame(cat_frame)
            qualities_row.pack(fill=tk.X, pady=5)

            for qual_id, qual_name in self.QUALITY_LEVELS:
                qual_frame = ttk.Frame(qualities_row)
                qual_frame.pack(side=tk.LEFT, padx=8)

                # Название качества
                ttk.Label(qual_frame, text=qual_name, width=12).pack(side=tk.LEFT)

                # Шанс
                chance_var = tk.IntVar(value=10 if qual_id in ['common', 'uncommon'] else 5)
                ttk.Spinbox(qual_frame, from_=0, to=100, textvariable=chance_var, width=4).pack(side=tk.LEFT, padx=2)
                ttk.Label(qual_frame, text="%").pack(side=tk.LEFT)

                # Чекбокс доступности
                enabled_var = tk.BooleanVar(value=qual_id in ['poor', 'common', 'uncommon'])
                ttk.Checkbutton(qual_frame, variable=enabled_var).pack(side=tk.LEFT, padx=3)

                self.template_loot_vars[cat_id]['qualities'][qual_id] = {
                    'chance': chance_var,
                    'enabled': enabled_var
                }

        # ===== Блок: Умения =====
        skills_frame = ttk.LabelFrame(parent, text="Умения", padding=10)
        skills_frame.pack(fill=tk.X, padx=5, pady=5)

        self.template_skills_vars = {}

        # Группировка по категориям
        skill_categories = {
            'combat': 'Ближний бой',
            'magic': 'Магия',
            'ranged': 'Дальний бой',
            'stealth': 'Скрытность',
            'weapon': 'Оружейные приёмы'
        }

        skills_container = ttk.Frame(skills_frame)
        skills_container.pack(fill=tk.X)

        col = 0
        for cat_id, cat_name in skill_categories.items():
            cat_frame = ttk.LabelFrame(skills_container, text=cat_name, padding=5)
            cat_frame.grid(row=0, column=col, padx=5, pady=5, sticky='nsew')
            col += 1

            cat_skills = [s for s in self.SKILLS if s[2] == cat_id]
            for skill_id, skill_name, _ in cat_skills:
                skill_row = ttk.Frame(cat_frame)
                skill_row.pack(fill=tk.X, pady=2)

                enabled_var = tk.BooleanVar(value=False)
                rank_var = tk.IntVar(value=1)

                ttk.Checkbutton(skill_row, text=skill_name, variable=enabled_var, width=20).pack(side=tk.LEFT)
                ttk.Label(skill_row, text="Ранг:").pack(side=tk.LEFT, padx=5)
                ttk.Spinbox(skill_row, from_=1, to=5, textvariable=rank_var, width=3).pack(side=tk.LEFT)

                self.template_skills_vars[skill_id] = (enabled_var, rank_var)

        # Кнопка применить
        ttk.Button(parent, text="Применить изменения", command=self.apply_template_changes).pack(pady=15)

    def update_stats_total(self, event=None):
        """Обновление суммы распределения статов"""
        total = sum(var.get() for var in self.template_stats_vars.values())
        self.stats_total_var.set(f"Сумма: {total}%")
        if total == 100:
            self.stats_total_label.configure(foreground='green')
        else:
            self.stats_total_label.configure(foreground='red')

    def refresh_template_list(self):
        """Обновление списка шаблонов"""
        self.template_listbox.delete(0, tk.END)
        for template in self.npc_templates:
            npc_type = template.get('type', 'unknown')
            type_name = dict(self.NPC_TYPES).get(npc_type, npc_type)
            rank = template.get('rank', 1)
            display_name = f"[Ранг {rank}] {template.get('name', 'Без имени')} ({type_name})"
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

        relation = template.get('relationship', 'neutral')
        for rel_id, rel_name in self.RELATIONSHIPS:
            if rel_id == relation:
                self.template_relation_var.set(f"{rel_id} - {rel_name}")
                break

        # Статы
        stat_dist = template.get('stat_distribution', {})
        for stat_id, var in self.template_stats_vars.items():
            var.set(stat_dist.get(stat_id, 16))
        self.update_stats_total()

        # Золото
        gold = template.get('gold', {})
        self.template_gold_chance_var.set(gold.get('chance', 80))
        self.template_gold_base_var.set(gold.get('base', 10))
        self.template_gold_level_mult_var.set(gold.get('level_multiplier', 1.5))
        self.template_gold_variance_var.set(gold.get('variance_percent', 20))

        # Лут
        loot = template.get('loot', {})
        self.template_max_loot_var.set(loot.get('max_items', 3))

        for cat_id, cat_vars in self.template_loot_vars.items():
            cat_loot = loot.get('categories', {}).get(cat_id, {})
            cat_vars['enabled'].set(cat_loot.get('enabled', True))

            for qual_id, qual_vars in cat_vars['qualities'].items():
                qual_data = cat_loot.get('qualities', {}).get(qual_id, {})
                qual_vars['chance'].set(qual_data.get('chance', 5))
                qual_vars['enabled'].set(qual_data.get('enabled', qual_id in ['poor', 'common', 'uncommon']))

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
        """Обновление списка спрайтов"""
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
            'stat_distribution': {
                'strength': 17, 'dexterity': 17, 'constitution': 17,
                'spirit': 17, 'intelligence': 16, 'luck': 16
            },
            'gold': {
                'chance': 80,
                'base': 10,
                'level_multiplier': 1.5,
                'variance_percent': 20
            },
            'loot': {
                'max_items': 3,
                'categories': {}
            },
            'skills': {},
            'sprite': 'soldier/soldier1.png'
        }

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
            messagebox.showwarning("Внимание", "Выберите шаблон для копирования")
            return

        index = selection[0]
        original = self.npc_templates[index]

        new_template = copy.deepcopy(original)
        new_template['id'] = f"{original['id']}_copy"
        new_template['name'] = f"{original['name']} (копия)"

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

        stats_total = sum(var.get() for var in self.template_stats_vars.values())
        if stats_total != 100:
            messagebox.showerror("Ошибка", f"Сумма распределения статов должна быть 100%\nТекущая сумма: {stats_total}%")
            return

        index = selection[0]
        template = self.npc_templates[index]

        new_id = self.template_id_var.get().strip()
        if not new_id:
            messagebox.showerror("Ошибка", "Идентификатор не может быть пустым")
            return

        for i, t in enumerate(self.npc_templates):
            if i != index and t.get('id') == new_id:
                messagebox.showerror("Ошибка", f"Идентификатор '{new_id}' уже существует")
                return

        template['id'] = new_id
        template['name'] = self.template_name_var.get()

        type_str = self.template_type_var.get()
        if ' - ' in type_str:
            template['type'] = type_str.split(' - ')[0]

        template['rank'] = self.template_rank_var.get()

        rel_str = self.template_relation_var.get()
        if ' - ' in rel_str:
            template['relationship'] = rel_str.split(' - ')[0]

        # Статы
        template['stat_distribution'] = {}
        for stat_id, var in self.template_stats_vars.items():
            template['stat_distribution'][stat_id] = var.get()

        # Золото
        template['gold'] = {
            'chance': self.template_gold_chance_var.get(),
            'base': self.template_gold_base_var.get(),
            'level_multiplier': self.template_gold_level_mult_var.get(),
            'variance_percent': self.template_gold_variance_var.get()
        }

        # Лут
        template['loot'] = {
            'max_items': self.template_max_loot_var.get(),
            'categories': {}
        }

        for cat_id, cat_vars in self.template_loot_vars.items():
            cat_data = {
                'enabled': cat_vars['enabled'].get(),
                'qualities': {}
            }

            for qual_id, qual_vars in cat_vars['qualities'].items():
                cat_data['qualities'][qual_id] = {
                    'chance': qual_vars['chance'].get(),
                    'enabled': qual_vars['enabled'].get()
                }

            template['loot']['categories'][cat_id] = cat_data

        # Умения
        template['skills'] = {}
        for skill_id, (enabled_var, rank_var) in self.template_skills_vars.items():
            if enabled_var.get():
                template['skills'][skill_id] = {'rank': rank_var.get()}

        template['sprite'] = self.template_sprite_var.get()

        self.refresh_template_list()
        messagebox.showinfo("Готово", "Изменения применены")

    # ==================== УНИКАЛЬНЫЕ NPC ====================

    def create_unique_tab(self):
        """Создание вкладки уникальных NPC"""
        main_paned = ttk.PanedWindow(self.unique_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - список
        left_frame = ttk.LabelFrame(main_paned, text="Список уникальных NPC", padding=5)
        main_paned.add(left_frame, weight=1)

        self.unique_listbox = tk.Listbox(left_frame, width=35, font=('Arial', 10))
        self.unique_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.unique_listbox.bind('<<ListboxSelect>>', self.on_unique_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_unique).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Копировать", command=self.duplicate_unique).pack(side=tk.LEFT, padx=2)

        # Правая панель - редактор
        right_container = ttk.Frame(main_paned)
        main_paned.add(right_container, weight=4)

        canvas = tk.Canvas(right_container)
        scrollbar_y = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)

        self.unique_editor_frame = ttk.Frame(canvas)

        self.unique_editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.unique_editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.create_unique_editor()
        self.refresh_unique_list()

    def create_unique_editor(self):
        """Создание редактора уникального NPC"""
        parent = self.unique_editor_frame

        # ===== Блок: Основная информация =====
        info_frame = ttk.LabelFrame(parent, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="Идентификатор:", width=15).pack(side=tk.LEFT)
        self.unique_id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.unique_id_var, width=25).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Имя:", width=8).pack(side=tk.LEFT, padx=(20, 0))
        self.unique_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.unique_name_var, width=30).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=3)

        ttk.Label(row2, text="Описание:", width=15).pack(side=tk.LEFT)
        self.unique_desc_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.unique_desc_var, width=80).pack(side=tk.LEFT, padx=5)

        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=3)

        ttk.Label(row3, text="Тип NPC:", width=15).pack(side=tk.LEFT)
        self.unique_type_var = tk.StringVar()
        type_combo = ttk.Combobox(row3, textvariable=self.unique_type_var, width=22, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in self.NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_unique_type_changed)

        ttk.Label(row3, text="Уровень:", width=8).pack(side=tk.LEFT, padx=(20, 0))
        self.unique_level_var = tk.IntVar(value=10)
        ttk.Spinbox(row3, from_=1, to=100, textvariable=self.unique_level_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(row3, text="Отношение к игроку:", width=18).pack(side=tk.LEFT, padx=(20, 0))
        self.unique_relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row3, textvariable=self.unique_relation_var, width=18, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in self.RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        row4 = ttk.Frame(info_frame)
        row4.pack(fill=tk.X, pady=3)

        ttk.Label(row4, text="Позиция X:", width=15).pack(side=tk.LEFT)
        self.unique_x_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=1000, textvariable=self.unique_x_var, width=6).pack(side=tk.LEFT, padx=5)

        ttk.Label(row4, text="Y:", width=3).pack(side=tk.LEFT)
        self.unique_y_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=1000, textvariable=self.unique_y_var, width=6).pack(side=tk.LEFT, padx=5)

        ttk.Label(row4, text="Идентификатор диалога:", width=20).pack(side=tk.LEFT, padx=(30, 0))
        self.unique_dialog_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.unique_dialog_var, width=25).pack(side=tk.LEFT, padx=5)

        row5 = ttk.Frame(info_frame)
        row5.pack(fill=tk.X, pady=3)

        ttk.Label(row5, text="Спрайт:", width=15).pack(side=tk.LEFT)
        self.unique_sprite_var = tk.StringVar()
        self.unique_sprite_combo = ttk.Combobox(row5, textvariable=self.unique_sprite_var, width=30, state='readonly')
        self.unique_sprite_combo.pack(side=tk.LEFT, padx=5)
        self.unique_sprite_combo.bind('<<ComboboxSelected>>', self.on_unique_sprite_changed)

        self.unique_sprite_label = ttk.Label(row5)
        self.unique_sprite_label.pack(side=tk.LEFT, padx=20)

        # ===== Блок: Характеристики =====
        stats_frame = ttk.LabelFrame(parent, text="Характеристики (фиксированные значения)", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unique_stats_vars = {}
        stats_row = ttk.Frame(stats_frame)
        stats_row.pack(fill=tk.X, pady=5)

        for stat_id, stat_name in self.STATS:
            stat_frame = ttk.Frame(stats_row)
            stat_frame.pack(side=tk.LEFT, padx=20)

            ttk.Label(stat_frame, text=f"{stat_name}:").pack(side=tk.LEFT)
            var = tk.IntVar(value=10)
            self.unique_stats_vars[stat_id] = var
            ttk.Spinbox(stat_frame, from_=1, to=100, textvariable=var, width=5).pack(side=tk.LEFT, padx=3)

        # ===== Блок: Золото =====
        gold_frame = ttk.LabelFrame(parent, text="Гарантированное золото", padding=10)
        gold_frame.pack(fill=tk.X, padx=5, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X, pady=3)

        ttk.Label(gold_row, text="Количество золота:").pack(side=tk.LEFT)
        self.unique_gold_var = tk.IntVar(value=100)
        ttk.Spinbox(gold_row, from_=0, to=100000, textvariable=self.unique_gold_var, width=10).pack(side=tk.LEFT, padx=5)

        # ===== Блок: Экипировка =====
        equip_frame = ttk.LabelFrame(parent, text="Экипировка", padding=10)
        equip_frame.pack(fill=tk.X, padx=5, pady=5)

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

        equip_row = ttk.Frame(equip_frame)
        equip_row.pack(fill=tk.X, pady=5)

        for equip_id, equip_name in equip_types:
            eq_frame = ttk.Frame(equip_row)
            eq_frame.pack(side=tk.LEFT, padx=10)

            enabled_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(eq_frame, text=equip_name, variable=enabled_var).pack(side=tk.LEFT)

            quality_var = tk.StringVar(value="rare")
            qual_combo = ttk.Combobox(eq_frame, textvariable=quality_var, width=12, state='readonly')
            qual_combo['values'] = [f"{q[0]} - {q[1]}" for q in self.QUALITY_LEVELS]
            qual_combo.pack(side=tk.LEFT, padx=3)

            self.unique_equip_vars[equip_id] = (enabled_var, quality_var)

        # ===== Блок: Умения =====
        skills_frame = ttk.LabelFrame(parent, text="Умения", padding=10)
        skills_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unique_skills_vars = {}

        skill_categories = {
            'combat': 'Ближний бой',
            'magic': 'Магия',
            'ranged': 'Дальний бой',
            'stealth': 'Скрытность',
            'weapon': 'Оружейные приёмы'
        }

        skills_container = ttk.Frame(skills_frame)
        skills_container.pack(fill=tk.X)

        col = 0
        for cat_id, cat_name in skill_categories.items():
            cat_frame = ttk.LabelFrame(skills_container, text=cat_name, padding=5)
            cat_frame.grid(row=0, column=col, padx=5, pady=5, sticky='nsew')
            col += 1

            cat_skills = [s for s in self.SKILLS if s[2] == cat_id]
            for skill_id, skill_name, _ in cat_skills:
                skill_row = ttk.Frame(cat_frame)
                skill_row.pack(fill=tk.X, pady=2)

                enabled_var = tk.BooleanVar(value=False)
                rank_var = tk.IntVar(value=1)

                ttk.Checkbutton(skill_row, text=skill_name, variable=enabled_var, width=20).pack(side=tk.LEFT)
                ttk.Label(skill_row, text="Ранг:").pack(side=tk.LEFT, padx=5)
                ttk.Spinbox(skill_row, from_=1, to=5, textvariable=rank_var, width=3).pack(side=tk.LEFT)

                self.unique_skills_vars[skill_id] = (enabled_var, rank_var)

        # Кнопка применить
        ttk.Button(parent, text="Применить изменения", command=self.apply_unique_changes).pack(pady=15)

    def refresh_unique_list(self):
        """Обновление списка уникальных NPC"""
        self.unique_listbox.delete(0, tk.END)
        for npc in self.unique_npcs:
            level = npc.get('level', 1)
            npc_type = npc.get('type', 'unknown')
            type_name = dict(self.NPC_TYPES).get(npc_type, npc_type)
            display_name = f"[Уровень {level}] {npc.get('name', 'Без имени')} ({type_name})"
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

        relation = npc.get('relationship', 'neutral')
        for rel_id, rel_name in self.RELATIONSHIPS:
            if rel_id == relation:
                self.unique_relation_var.set(f"{rel_id} - {rel_name}")
                break

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
                qual = equipment[equip_id].get('quality', 'rare')
                for q_id, q_name in self.QUALITY_LEVELS:
                    if q_id == qual:
                        quality_var.set(f"{q_id} - {q_name}")
                        break
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
        """Обработка смены типа"""
        type_str = self.unique_type_var.get()
        if ' - ' in type_str:
            npc_type = type_str.split(' - ')[0]
            self.update_unique_sprite_combo(npc_type)

    def update_unique_sprite_combo(self, npc_type):
        """Обновление списка спрайтов"""
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
        """Загрузка превью спрайта"""
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
            'description': 'Описание персонажа',
            'type': 'guard',
            'level': 10,
            'relationship': 'neutral',
            'position': {'x': 100, 'y': 100},
            'stats': {stat_id: 10 for stat_id, _ in self.STATS},
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
            messagebox.showwarning("Внимание", "Выберите NPC для копирования")
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
            messagebox.showerror("Ошибка", "Идентификатор не может быть пустым")
            return

        for i, n in enumerate(self.unique_npcs):
            if i != index and n.get('id') == new_id:
                messagebox.showerror("Ошибка", f"Идентификатор '{new_id}' уже существует")
                return

        npc['id'] = new_id
        npc['name'] = self.unique_name_var.get()
        npc['description'] = self.unique_desc_var.get()

        type_str = self.unique_type_var.get()
        if ' - ' in type_str:
            npc['type'] = type_str.split(' - ')[0]

        npc['level'] = self.unique_level_var.get()

        rel_str = self.unique_relation_var.get()
        if ' - ' in rel_str:
            npc['relationship'] = rel_str.split(' - ')[0]

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
                qual_str = quality_var.get()
                if ' - ' in qual_str:
                    qual = qual_str.split(' - ')[0]
                else:
                    qual = qual_str
                npc['equipment'][equip_id] = {'quality': qual}

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

    style.configure('TLabel', font=('Arial', 10))
    style.configure('TButton', font=('Arial', 10))
    style.configure('TCheckbutton', font=('Arial', 10))
    style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'))

    app = NPCConfigEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
