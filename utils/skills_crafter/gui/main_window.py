"""
Главное окно Skills Crafter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..models import (
    SkillData, SkillCategory, SkillType, TargetType, AreaType,
    ScalingAttribute, WeaponType, StatusEffectType,
    CostData, RequirementData, TargetingData, DamageData,
    HealingData, StatusEffectData, ScalingData, RankProgressionData,
    VisualData
)
from .widgets import (
    LabeledEntry, LabeledSpinbox, LabeledCombobox, LabeledCheckbox,
    ScrollableFrame, CollapsibleFrame, StatusEffectEditor, ScalingEditor
)


class SkillsCrafterApp:
    """Главное приложение Skills Crafter"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Skills Crafter - Редактор умений")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Текущие данные
        self.current_skill = SkillData()
        self.skills_list: List[SkillData] = []
        self.current_file: Optional[str] = None
        self.modified = False

        # Путь к проекту
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.config_path = self.project_root / "game" / "config"
        self.assets_path = self.project_root / "assets"

        # Настройка стилей
        self._setup_styles()

        # Создание интерфейса
        self._create_menu()
        self._create_main_layout()
        self._create_statusbar()

        # Привязка событий
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        """Настройка стилей ttk"""
        style = ttk.Style()
        style.theme_use('clam')

        # Заголовки секций
        style.configure(
            "Section.TLabel",
            font=("TkDefaultFont", 11, "bold"),
            foreground="#2c3e50"
        )

        # Фреймы вкладок
        style.configure("Tab.TFrame", padding=10)

    def _create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новое умение", command=self._new_skill, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Открыть...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Импорт из skills_config.json", command=self._import_from_game)
        file_menu.add_command(label="Экспорт в skills_config.json", command=self._export_to_game)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close, accelerator="Alt+F4")

        # Редактирование
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактирование", menu=edit_menu)
        edit_menu.add_command(label="Копировать умение", command=self._duplicate_skill)
        edit_menu.add_command(label="Удалить умение", command=self._delete_skill)
        edit_menu.add_separator()
        edit_menu.add_command(label="Генерировать описания рангов", command=self._generate_rank_descriptions)

        # Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Предпросмотр JSON", command=self._preview_json)
        tools_menu.add_command(label="Валидация", command=self._validate_skill)
        tools_menu.add_separator()
        tools_menu.add_command(label="Калькулятор урона", command=self._show_damage_calculator)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

        # Горячие клавиши
        self.root.bind("<Control-n>", lambda e: self._new_skill())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())

    def _create_main_layout(self):
        """Создание основного layout"""
        # Главный контейнер
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - список умений
        left_frame = ttk.Frame(main_paned, width=250)
        main_paned.add(left_frame, weight=1)
        self._create_skills_list(left_frame)

        # Правая панель - редактор
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)
        self._create_editor(right_frame)

    def _create_skills_list(self, parent: ttk.Frame):
        """Создание панели списка умений"""
        # Заголовок
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header, text="Умения", style="Section.TLabel").pack(side=tk.LEFT)

        # Кнопки
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="+", width=3, command=self._new_skill).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="-", width=3, command=self._delete_skill).pack(side=tk.LEFT, padx=1)

        # Поиск
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_skills_list)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X)
        search_entry.insert(0, "Поиск...")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Поиск..." else None)

        # Список
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.skills_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.skills_listbox.yview)
        self.skills_listbox.configure(yscrollcommand=scrollbar.set)

        self.skills_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.skills_listbox.bind("<<ListboxSelect>>", self._on_skill_select)

    def _create_editor(self, parent: ttk.Frame):
        """Создание редактора умения"""
        # Notebook с вкладками
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладки
        self._create_basic_tab()
        self._create_costs_tab()
        self._create_targeting_tab()
        self._create_damage_tab()
        self._create_healing_tab()
        self._create_effects_tab()
        self._create_progression_tab()
        self._create_visuals_tab()

    def _create_basic_tab(self):
        """Вкладка базовой информации"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Основное")
        content = tab.scrollable_frame

        # Идентификация
        id_frame = CollapsibleFrame(content, "Идентификация")
        id_frame.pack(fill=tk.X, pady=5, padx=5)

        self.skill_id_entry = LabeledEntry(
            id_frame.content, "ID умения:", 30, "",
            "Уникальный идентификатор (латиница, snake_case)"
        )
        self.skill_id_entry.pack(fill=tk.X, pady=2)
        self.skill_id_entry.bind_change(self._mark_modified)

        self.skill_name_entry = LabeledEntry(
            id_frame.content, "Название:", 30, "",
            "Отображаемое название умения"
        )
        self.skill_name_entry.pack(fill=tk.X, pady=2)
        self.skill_name_entry.bind_change(self._mark_modified)

        # Описание
        desc_frame = ttk.Frame(id_frame.content)
        desc_frame.pack(fill=tk.X, pady=2)

        ttk.Label(desc_frame, text="Описание:", width=20, anchor="e").pack(side=tk.LEFT, padx=(0, 5))

        self.description_text = tk.Text(desc_frame, height=4, width=40, wrap=tk.WORD)
        self.description_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.description_text.bind("<KeyRelease>", lambda e: self._mark_modified())

        # Тип и категория
        type_frame = CollapsibleFrame(content, "Тип и категория")
        type_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(type_frame.content)
        row1.pack(fill=tk.X, pady=2)

        self.skill_type_combo = LabeledCombobox(
            row1, "Тип умения:",
            values=["active", "passive"],
            display_names={"active": "Активное", "passive": "Пассивное"},
            default="active"
        )
        self.skill_type_combo.pack(side=tk.LEFT, padx=5)
        self.skill_type_combo.bind_change(self._mark_modified)

        self.category_combo = LabeledCombobox(
            row1, "Категория:",
            values=list(SkillCategory.get_display_names().keys()),
            display_names=SkillCategory.get_display_names(),
            default="combat"
        )
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind_change(self._mark_modified)

        # Требования оружия
        weapon_frame = CollapsibleFrame(content, "Требования оружия")
        weapon_frame.pack(fill=tk.X, pady=5, padx=5)

        self.weapon_combo = LabeledCombobox(
            weapon_frame.content, "Требуемое оружие:",
            values=list(WeaponType.get_display_names().keys()),
            display_names=WeaponType.get_display_names(),
            default="any"
        )
        self.weapon_combo.pack(fill=tk.X, pady=2)
        self.weapon_combo.bind_change(self._mark_modified)

    def _create_costs_tab(self):
        """Вкладка затрат и требований"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Затраты")
        content = tab.scrollable_frame

        # Затраты ресурсов
        costs_frame = CollapsibleFrame(content, "Затраты ресурсов")
        costs_frame.pack(fill=tk.X, pady=5, padx=5)

        # Мана
        mana_row = ttk.Frame(costs_frame.content)
        mana_row.pack(fill=tk.X, pady=2)

        self.mana_cost = LabeledSpinbox(
            mana_row, "Мана:", 0, 500, 5, 0,
            tooltip="Базовая стоимость маны"
        )
        self.mana_cost.pack(side=tk.LEFT, padx=5)
        self.mana_cost.bind_change(self._mark_modified)

        self.mana_per_rank = LabeledSpinbox(
            mana_row, "+ за ранг:", -50, 50, 5, 0
        )
        self.mana_per_rank.pack(side=tk.LEFT, padx=5)
        self.mana_per_rank.bind_change(self._mark_modified)

        # Выносливость
        stamina_row = ttk.Frame(costs_frame.content)
        stamina_row.pack(fill=tk.X, pady=2)

        self.stamina_cost = LabeledSpinbox(
            stamina_row, "Выносливость:", 0, 100, 5, 0,
            tooltip="Базовая стоимость выносливости"
        )
        self.stamina_cost.pack(side=tk.LEFT, padx=5)
        self.stamina_cost.bind_change(self._mark_modified)

        self.stamina_per_rank = LabeledSpinbox(
            stamina_row, "+ за ранг:", -20, 20, 1, 0
        )
        self.stamina_per_rank.pack(side=tk.LEFT, padx=5)
        self.stamina_per_rank.bind_change(self._mark_modified)

        # Здоровье
        health_row = ttk.Frame(costs_frame.content)
        health_row.pack(fill=tk.X, pady=2)

        self.health_cost = LabeledSpinbox(
            health_row, "Здоровье:", 0, 100, 5, 0,
            tooltip="Затраты здоровья (для умений жертвования)"
        )
        self.health_cost.pack(side=tk.LEFT, padx=5)
        self.health_cost.bind_change(self._mark_modified)

        self.health_per_rank = LabeledSpinbox(
            health_row, "+ за ранг:", -20, 20, 1, 0
        )
        self.health_per_rank.pack(side=tk.LEFT, padx=5)
        self.health_per_rank.bind_change(self._mark_modified)

        # Кулдаун
        cd_frame = CollapsibleFrame(content, "Перезарядка")
        cd_frame.pack(fill=tk.X, pady=5, padx=5)

        cd_row = ttk.Frame(cd_frame.content)
        cd_row.pack(fill=tk.X, pady=2)

        self.cooldown = LabeledSpinbox(
            cd_row, "Кулдаун (ходов):", 0, 20, 1, 0,
            tooltip="Количество ходов до повторного использования"
        )
        self.cooldown.pack(side=tk.LEFT, padx=5)
        self.cooldown.bind_change(self._mark_modified)

        self.cd_reduction = LabeledSpinbox(
            cd_row, "- за ранг:", 0, 5, 1, 0,
            tooltip="Уменьшение кулдауна за каждый ранг"
        )
        self.cd_reduction.pack(side=tk.LEFT, padx=5)
        self.cd_reduction.bind_change(self._mark_modified)

        # Требования персонажа
        req_frame = CollapsibleFrame(content, "Требования персонажа")
        req_frame.pack(fill=tk.X, pady=5, padx=5)

        self.level_required = LabeledSpinbox(
            req_frame.content, "Мин. уровень:", 1, 100, 1, 1,
            tooltip="Минимальный уровень персонажа"
        )
        self.level_required.pack(fill=tk.X, pady=2)
        self.level_required.bind_change(self._mark_modified)

        # Требования атрибутов
        attr_frame = ttk.Frame(req_frame.content)
        attr_frame.pack(fill=tk.X, pady=5)

        ttk.Label(attr_frame, text="Минимальные атрибуты:", style="Section.TLabel").pack(anchor=tk.W)

        attrs_row1 = ttk.Frame(attr_frame)
        attrs_row1.pack(fill=tk.X, pady=2)

        self.req_strength = LabeledSpinbox(attrs_row1, "Сила:", 0, 100, 1, 0, width=5)
        self.req_strength.pack(side=tk.LEFT, padx=5)

        self.req_dexterity = LabeledSpinbox(attrs_row1, "Ловкость:", 0, 100, 1, 0, width=5)
        self.req_dexterity.pack(side=tk.LEFT, padx=5)

        self.req_constitution = LabeledSpinbox(attrs_row1, "Телосложение:", 0, 100, 1, 0, width=5)
        self.req_constitution.pack(side=tk.LEFT, padx=5)

        attrs_row2 = ttk.Frame(attr_frame)
        attrs_row2.pack(fill=tk.X, pady=2)

        self.req_intelligence = LabeledSpinbox(attrs_row2, "Интеллект:", 0, 100, 1, 0, width=5)
        self.req_intelligence.pack(side=tk.LEFT, padx=5)

        self.req_spirit = LabeledSpinbox(attrs_row2, "Дух:", 0, 100, 1, 0, width=5)
        self.req_spirit.pack(side=tk.LEFT, padx=5)

    def _create_targeting_tab(self):
        """Вкладка нацеливания"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Нацеливание")
        content = tab.scrollable_frame

        # Тип цели
        target_frame = CollapsibleFrame(content, "Тип цели")
        target_frame.pack(fill=tk.X, pady=5, padx=5)

        self.target_type_combo = LabeledCombobox(
            target_frame.content, "Цель:",
            values=list(TargetType.get_display_names().keys()),
            display_names=TargetType.get_display_names(),
            default="single_enemy"
        )
        self.target_type_combo.pack(fill=tk.X, pady=2)
        self.target_type_combo.bind_change(self._mark_modified)

        self.area_type_combo = LabeledCombobox(
            target_frame.content, "Область:",
            values=list(AreaType.get_display_names().keys()),
            display_names=AreaType.get_display_names(),
            default="single"
        )
        self.area_type_combo.pack(fill=tk.X, pady=2)
        self.area_type_combo.bind_change(self._on_area_type_change)

        # Дальность
        range_frame = CollapsibleFrame(content, "Дальность")
        range_frame.pack(fill=tk.X, pady=5, padx=5)

        range_row = ttk.Frame(range_frame.content)
        range_row.pack(fill=tk.X, pady=2)

        self.tactical_range = LabeledSpinbox(
            range_row, "Макс. дальность:", 0, 20, 1, 1,
            tooltip="Максимальная дальность в клетках (0 = на себя)"
        )
        self.tactical_range.pack(side=tk.LEFT, padx=5)
        self.tactical_range.bind_change(self._mark_modified)

        self.min_range = LabeledSpinbox(
            range_row, "Мин. дальность:", 0, 10, 1, 0,
            tooltip="Минимальная дальность (для дальних умений)"
        )
        self.min_range.pack(side=tk.LEFT, padx=5)
        self.min_range.bind_change(self._mark_modified)

        self.range_per_rank = LabeledSpinbox(
            range_row, "+ за ранг:", 0, 5, 1, 0
        )
        self.range_per_rank.pack(side=tk.LEFT, padx=5)
        self.range_per_rank.bind_change(self._mark_modified)

        # AoE параметры
        self.aoe_frame = CollapsibleFrame(content, "Параметры области (AoE)")
        self.aoe_frame.pack(fill=tk.X, pady=5, padx=5)

        aoe_row = ttk.Frame(self.aoe_frame.content)
        aoe_row.pack(fill=tk.X, pady=2)

        self.aoe_radius = LabeledSpinbox(
            aoe_row, "Радиус:", 0, 10, 1, 0,
            tooltip="Радиус области поражения"
        )
        self.aoe_radius.pack(side=tk.LEFT, padx=5)
        self.aoe_radius.bind_change(self._mark_modified)

        self.aoe_radius_per_rank = LabeledSpinbox(
            aoe_row, "+ за ранг:", 0, 3, 1, 0
        )
        self.aoe_radius_per_rank.pack(side=tk.LEFT, padx=5)
        self.aoe_radius_per_rank.bind_change(self._mark_modified)

        # Конус
        cone_row = ttk.Frame(self.aoe_frame.content)
        cone_row.pack(fill=tk.X, pady=2)

        self.cone_angle = LabeledSpinbox(
            cone_row, "Угол конуса (°):", 15, 180, 15, 60,
            tooltip="Угол конуса в градусах"
        )
        self.cone_angle.pack(side=tk.LEFT, padx=5)
        self.cone_angle.bind_change(self._mark_modified)

        # Опции
        options_frame = CollapsibleFrame(content, "Дополнительные опции")
        options_frame.pack(fill=tk.X, pady=5, padx=5)

        self.can_target_self = LabeledCheckbox(
            options_frame.content, "Можно применить на себя", False
        )
        self.can_target_self.pack(fill=tk.X, pady=2)
        self.can_target_self.bind_change(self._mark_modified)

        self.requires_los = LabeledCheckbox(
            options_frame.content, "Требует прямой видимости", True
        )
        self.requires_los.pack(fill=tk.X, pady=2)
        self.requires_los.bind_change(self._mark_modified)

        # Knockback
        kb_frame = ttk.Frame(options_frame.content)
        kb_frame.pack(fill=tk.X, pady=2)

        self.knockback_chance = LabeledSpinbox(
            kb_frame, "Шанс отбрасывания:", 0, 1, 0.1, 0, is_float=True
        )
        self.knockback_chance.pack(side=tk.LEFT, padx=5)
        self.knockback_chance.bind_change(self._mark_modified)

        self.knockback_per_rank = LabeledSpinbox(
            kb_frame, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.knockback_per_rank.pack(side=tk.LEFT, padx=5)
        self.knockback_per_rank.bind_change(self._mark_modified)

        self.knockback_distance = LabeledSpinbox(
            kb_frame, "Дистанция:", 1, 5, 1, 1
        )
        self.knockback_distance.pack(side=tk.LEFT, padx=5)
        self.knockback_distance.bind_change(self._mark_modified)

    def _create_damage_tab(self):
        """Вкладка урона"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Урон")
        content = tab.scrollable_frame

        # Включение урона
        self.has_damage = LabeledCheckbox(content, "Умение наносит урон", False)
        self.has_damage.pack(fill=tk.X, pady=5, padx=5)
        self.has_damage.bind_change(self._toggle_damage_frame)

        # Контейнер для параметров урона
        self.damage_container = ttk.Frame(content)
        self.damage_container.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # Базовый урон
        base_frame = CollapsibleFrame(self.damage_container, "Базовый урон")
        base_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(base_frame.content)
        row1.pack(fill=tk.X, pady=2)

        self.base_damage = LabeledSpinbox(
            row1, "Фиксированный урон:", 0, 500, 5, 0,
            tooltip="Базовый урон, не зависящий от оружия"
        )
        self.base_damage.pack(side=tk.LEFT, padx=5)
        self.base_damage.bind_change(self._mark_modified)

        row2 = ttk.Frame(base_frame.content)
        row2.pack(fill=tk.X, pady=2)

        self.damage_multiplier = LabeledSpinbox(
            row2, "Множитель урона:", 0, 10, 0.1, 1.0, is_float=True,
            tooltip="Множитель урона оружия"
        )
        self.damage_multiplier.pack(side=tk.LEFT, padx=5)
        self.damage_multiplier.bind_change(self._mark_modified)

        self.damage_mult_per_rank = LabeledSpinbox(
            row2, "+ за ранг:", 0, 2, 0.05, 0.2, is_float=True
        )
        self.damage_mult_per_rank.pack(side=tk.LEFT, padx=5)
        self.damage_mult_per_rank.bind_change(self._mark_modified)

        # Броня
        armor_frame = CollapsibleFrame(self.damage_container, "Взаимодействие с броней")
        armor_frame.pack(fill=tk.X, pady=5)

        self.ignores_armor = LabeledCheckbox(
            armor_frame.content, "Игнорирует броню (магический урон)", False
        )
        self.ignores_armor.pack(fill=tk.X, pady=2)
        self.ignores_armor.bind_change(self._mark_modified)

        pen_row = ttk.Frame(armor_frame.content)
        pen_row.pack(fill=tk.X, pady=2)

        self.armor_penetration = LabeledSpinbox(
            pen_row, "Пробитие брони:", 0, 1, 0.1, 0, is_float=True,
            tooltip="Процент игнорируемой брони (0.5 = 50%)"
        )
        self.armor_penetration.pack(side=tk.LEFT, padx=5)
        self.armor_penetration.bind_change(self._mark_modified)

        self.pen_per_rank = LabeledSpinbox(
            pen_row, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.pen_per_rank.pack(side=tk.LEFT, padx=5)
        self.pen_per_rank.bind_change(self._mark_modified)

        # Криты
        crit_frame = CollapsibleFrame(self.damage_container, "Критические удары")
        crit_frame.pack(fill=tk.X, pady=5)

        crit_row = ttk.Frame(crit_frame.content)
        crit_row.pack(fill=tk.X, pady=2)

        self.crit_chance_bonus = LabeledSpinbox(
            crit_row, "Бонус к криту:", 0, 1, 0.05, 0, is_float=True,
            tooltip="Дополнительный шанс крита"
        )
        self.crit_chance_bonus.pack(side=tk.LEFT, padx=5)
        self.crit_chance_bonus.bind_change(self._mark_modified)

        self.crit_per_rank = LabeledSpinbox(
            crit_row, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.crit_per_rank.pack(side=tk.LEFT, padx=5)
        self.crit_per_rank.bind_change(self._mark_modified)

        self.crit_damage_mult = LabeledSpinbox(
            crit_row, "Множитель крита:", 1, 5, 0.5, 2.0, is_float=True
        )
        self.crit_damage_mult.pack(side=tk.LEFT, padx=5)
        self.crit_damage_mult.bind_change(self._mark_modified)

        # Множественные удары
        hits_frame = CollapsibleFrame(self.damage_container, "Множественные удары")
        hits_frame.pack(fill=tk.X, pady=5)

        hits_row = ttk.Frame(hits_frame.content)
        hits_row.pack(fill=tk.X, pady=2)

        self.hit_count = LabeledSpinbox(
            hits_row, "Кол-во ударов:", 1, 10, 1, 1,
            tooltip="Количество ударов за одно применение"
        )
        self.hit_count.pack(side=tk.LEFT, padx=5)
        self.hit_count.bind_change(self._mark_modified)

        self.hits_per_rank = LabeledSpinbox(
            hits_row, "+ за ранг:", 0, 3, 1, 0
        )
        self.hits_per_rank.pack(side=tk.LEFT, padx=5)
        self.hits_per_rank.bind_change(self._mark_modified)

        self.damage_per_hit = LabeledSpinbox(
            hits_row, "Урон за удар:", 0.1, 2, 0.1, 1.0, is_float=True,
            tooltip="Множитель урона для каждого удара"
        )
        self.damage_per_hit.pack(side=tk.LEFT, padx=5)
        self.damage_per_hit.bind_change(self._mark_modified)

        # Масштабирование по атрибутам
        scaling_frame = CollapsibleFrame(self.damage_container, "Масштабирование по атрибутам")
        scaling_frame.pack(fill=tk.X, pady=5)

        self.damage_scaling_container = ttk.Frame(scaling_frame.content)
        self.damage_scaling_container.pack(fill=tk.X)

        self.damage_scaling_editors: List[ScalingEditor] = []

        add_scaling_btn = ttk.Button(
            scaling_frame.content, text="+ Добавить атрибут",
            command=self._add_damage_scaling
        )
        add_scaling_btn.pack(pady=5)

        # Изначально скрыть
        self.damage_container.pack_forget()

    def _create_healing_tab(self):
        """Вкладка лечения"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Лечение")
        content = tab.scrollable_frame

        # Включение лечения
        self.has_healing = LabeledCheckbox(content, "Умение восстанавливает HP", False)
        self.has_healing.pack(fill=tk.X, pady=5, padx=5)
        self.has_healing.bind_change(self._toggle_healing_frame)

        # Контейнер для параметров лечения
        self.healing_container = ttk.Frame(content)
        self.healing_container.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # Мгновенное лечение
        instant_frame = CollapsibleFrame(self.healing_container, "Мгновенное лечение")
        instant_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(instant_frame.content)
        row1.pack(fill=tk.X, pady=2)

        self.base_heal = LabeledSpinbox(
            row1, "Фиксированное лечение:", 0, 500, 5, 0,
            tooltip="Базовое значение лечения"
        )
        self.base_heal.pack(side=tk.LEFT, padx=5)
        self.base_heal.bind_change(self._mark_modified)

        row2 = ttk.Frame(instant_frame.content)
        row2.pack(fill=tk.X, pady=2)

        self.heal_percent = LabeledSpinbox(
            row2, "% от макс. HP:", 0, 1, 0.05, 0, is_float=True,
            tooltip="Лечение как процент от максимального здоровья"
        )
        self.heal_percent.pack(side=tk.LEFT, padx=5)
        self.heal_percent.bind_change(self._mark_modified)

        self.heal_percent_per_rank = LabeledSpinbox(
            row2, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.heal_percent_per_rank.pack(side=tk.LEFT, padx=5)
        self.heal_percent_per_rank.bind_change(self._mark_modified)

        # Лечение по времени
        hot_frame = CollapsibleFrame(self.healing_container, "Лечение по времени (HoT)")
        hot_frame.pack(fill=tk.X, pady=5)

        self.heal_over_time = LabeledCheckbox(
            hot_frame.content, "Лечение за несколько ходов", False
        )
        self.heal_over_time.pack(fill=tk.X, pady=2)
        self.heal_over_time.bind_change(self._mark_modified)

        hot_row1 = ttk.Frame(hot_frame.content)
        hot_row1.pack(fill=tk.X, pady=2)

        self.heal_per_turn = LabeledSpinbox(
            hot_row1, "Лечение за ход:", 0, 100, 5, 0
        )
        self.heal_per_turn.pack(side=tk.LEFT, padx=5)
        self.heal_per_turn.bind_change(self._mark_modified)

        self.heal_per_turn_per_rank = LabeledSpinbox(
            hot_row1, "+ за ранг:", 0, 20, 1, 0
        )
        self.heal_per_turn_per_rank.pack(side=tk.LEFT, padx=5)
        self.heal_per_turn_per_rank.bind_change(self._mark_modified)

        hot_row2 = ttk.Frame(hot_frame.content)
        hot_row2.pack(fill=tk.X, pady=2)

        self.heal_duration = LabeledSpinbox(
            hot_row2, "Длительность (ходов):", 1, 20, 1, 3
        )
        self.heal_duration.pack(side=tk.LEFT, padx=5)
        self.heal_duration.bind_change(self._mark_modified)

        self.heal_duration_per_rank = LabeledSpinbox(
            hot_row2, "+ за ранг:", 0, 5, 1, 0
        )
        self.heal_duration_per_rank.pack(side=tk.LEFT, padx=5)
        self.heal_duration_per_rank.bind_change(self._mark_modified)

        # Масштабирование лечения
        heal_scaling_frame = CollapsibleFrame(self.healing_container, "Масштабирование")
        heal_scaling_frame.pack(fill=tk.X, pady=5)

        self.heal_scaling_container = ttk.Frame(heal_scaling_frame.content)
        self.heal_scaling_container.pack(fill=tk.X)

        self.heal_scaling_editors: List[ScalingEditor] = []

        add_heal_scaling_btn = ttk.Button(
            heal_scaling_frame.content, text="+ Добавить атрибут",
            command=self._add_heal_scaling
        )
        add_heal_scaling_btn.pack(pady=5)

        # Изначально скрыть
        self.healing_container.pack_forget()

    def _create_effects_tab(self):
        """Вкладка статус-эффектов"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Эффекты")
        content = tab.scrollable_frame

        # Заголовок
        header = ttk.Frame(content)
        header.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(
            header, text="Статус-эффекты, накладываемые умением",
            style="Section.TLabel"
        ).pack(side=tk.LEFT)

        ttk.Button(
            header, text="+ Добавить эффект",
            command=self._add_status_effect
        ).pack(side=tk.RIGHT)

        # Контейнер для эффектов
        self.effects_container = ttk.Frame(content)
        self.effects_container.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        self.effect_editors: List[StatusEffectEditor] = []

    def _create_progression_tab(self):
        """Вкладка прогрессии по рангам"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Ранги")
        content = tab.scrollable_frame

        # Параметры рангов
        rank_frame = CollapsibleFrame(content, "Параметры системы рангов")
        rank_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(rank_frame.content)
        row1.pack(fill=tk.X, pady=2)

        self.max_rank = LabeledSpinbox(
            row1, "Макс. ранг:", 1, 10, 1, 5
        )
        self.max_rank.pack(side=tk.LEFT, padx=5)
        self.max_rank.bind_change(self._on_max_rank_change)

        row2 = ttk.Frame(rank_frame.content)
        row2.pack(fill=tk.X, pady=2)

        self.base_exp = LabeledSpinbox(
            row2, "Базовый опыт:", 10, 1000, 10, 100,
            tooltip="Опыт для получения ранга 2"
        )
        self.base_exp.pack(side=tk.LEFT, padx=5)
        self.base_exp.bind_change(self._mark_modified)

        self.exp_multiplier = LabeledSpinbox(
            row2, "Множитель опыта:", 1, 3, 0.1, 1.5, is_float=True,
            tooltip="Множитель опыта для следующих рангов"
        )
        self.exp_multiplier.pack(side=tk.LEFT, padx=5)
        self.exp_multiplier.bind_change(self._mark_modified)

        row3 = ttk.Frame(rank_frame.content)
        row3.pack(fill=tk.X, pady=2)

        self.uses_per_rank = LabeledSpinbox(
            row3, "Использований на ранг:", 5, 100, 5, 20
        )
        self.uses_per_rank.pack(side=tk.LEFT, padx=5)
        self.uses_per_rank.bind_change(self._mark_modified)

        self.level_per_rank = LabeledSpinbox(
            row3, "Уровней на ранг:", 1, 20, 1, 5
        )
        self.level_per_rank.pack(side=tk.LEFT, padx=5)
        self.level_per_rank.bind_change(self._mark_modified)

        # Описания по рангам
        desc_frame = CollapsibleFrame(content, "Описания по рангам")
        desc_frame.pack(fill=tk.X, pady=5, padx=5)

        self.rank_descriptions_container = ttk.Frame(desc_frame.content)
        self.rank_descriptions_container.pack(fill=tk.X)

        self.rank_desc_entries: List[LabeledEntry] = []

        # Кнопка генерации
        gen_btn = ttk.Button(
            desc_frame.content, text="Авто-генерация описаний",
            command=self._generate_rank_descriptions
        )
        gen_btn.pack(pady=5)

        # Создать поля для 5 рангов
        self._create_rank_description_fields(5)

    def _create_visuals_tab(self):
        """Вкладка визуальных настроек"""
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="Визуал")
        content = tab.scrollable_frame

        # Иконка
        icon_frame = CollapsibleFrame(content, "Иконка умения")
        icon_frame.pack(fill=tk.X, pady=5, padx=5)

        icon_row = ttk.Frame(icon_frame.content)
        icon_row.pack(fill=tk.X, pady=5)

        # Превью иконки
        self.icon_preview_frame = ttk.Frame(icon_row, width=64, height=64, relief=tk.SUNKEN)
        self.icon_preview_frame.pack(side=tk.LEFT, padx=10)
        self.icon_preview_frame.pack_propagate(False)

        self.icon_preview_label = ttk.Label(self.icon_preview_frame, text="Нет\nиконки")
        self.icon_preview_label.pack(expand=True)

        self.current_icon_image = None

        # Путь к иконке
        icon_path_frame = ttk.Frame(icon_row)
        icon_path_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.icon_path_entry = LabeledEntry(
            icon_path_frame, "Путь к иконке:", 40, ""
        )
        self.icon_path_entry.pack(fill=tk.X)
        self.icon_path_entry.bind_change(self._mark_modified)

        icon_btn_frame = ttk.Frame(icon_path_frame)
        icon_btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(
            icon_btn_frame, text="Выбрать...",
            command=self._select_icon
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            icon_btn_frame, text="Предпросмотр",
            command=self._preview_icon
        ).pack(side=tk.LEFT, padx=2)

        # Цвета
        colors_frame = CollapsibleFrame(content, "Цвета")
        colors_frame.pack(fill=tk.X, pady=5, padx=5)

        colors_row = ttk.Frame(colors_frame.content)
        colors_row.pack(fill=tk.X, pady=2)

        self.color_primary = LabeledEntry(
            colors_row, "Основной цвет:", 10, "#FFFFFF"
        )
        self.color_primary.pack(side=tk.LEFT, padx=5)
        self.color_primary.bind_change(self._mark_modified)

        self.primary_color_btn = ttk.Button(
            colors_row, text="...", width=3,
            command=lambda: self._pick_color("primary")
        )
        self.primary_color_btn.pack(side=tk.LEFT)

        self.color_secondary = LabeledEntry(
            colors_row, "Вторичный цвет:", 10, "#888888"
        )
        self.color_secondary.pack(side=tk.LEFT, padx=5)
        self.color_secondary.bind_change(self._mark_modified)

        self.secondary_color_btn = ttk.Button(
            colors_row, text="...", width=3,
            command=lambda: self._pick_color("secondary")
        )
        self.secondary_color_btn.pack(side=tk.LEFT)

        # Анимация и эффекты
        fx_frame = CollapsibleFrame(content, "Анимация и эффекты")
        fx_frame.pack(fill=tk.X, pady=5, padx=5)

        self.animation_type = LabeledCombobox(
            fx_frame.content, "Тип анимации:",
            values=["default", "slash", "stab", "projectile", "explosion", "heal", "buff"],
            default="default"
        )
        self.animation_type.pack(fill=tk.X, pady=2)
        self.animation_type.bind_change(self._mark_modified)

        self.particle_effect = LabeledEntry(
            fx_frame.content, "Эффект частиц:", 30, ""
        )
        self.particle_effect.pack(fill=tk.X, pady=2)
        self.particle_effect.bind_change(self._mark_modified)

        # Звуки
        sound_frame = CollapsibleFrame(content, "Звуки")
        sound_frame.pack(fill=tk.X, pady=5, padx=5)

        self.sound_use = LabeledEntry(
            sound_frame.content, "Звук применения:", 30, ""
        )
        self.sound_use.pack(fill=tk.X, pady=2)
        self.sound_use.bind_change(self._mark_modified)

        self.sound_hit = LabeledEntry(
            sound_frame.content, "Звук попадания:", 30, ""
        )
        self.sound_hit.pack(fill=tk.X, pady=2)
        self.sound_hit.bind_change(self._mark_modified)

    def _create_statusbar(self):
        """Создание статус-бара"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.statusbar, text="Готов")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.modified_label = ttk.Label(self.statusbar, text="")
        self.modified_label.pack(side=tk.RIGHT, padx=5)

    # === Вспомогательные методы ===

    def _mark_modified(self):
        """Пометить как измененный"""
        self.modified = True
        self.modified_label.configure(text="● Изменено")

    def _clear_modified(self):
        """Снять пометку изменения"""
        self.modified = False
        self.modified_label.configure(text="")

    def _toggle_damage_frame(self):
        """Показать/скрыть фрейм урона"""
        if self.has_damage.get():
            self.damage_container.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        else:
            self.damage_container.pack_forget()
        self._mark_modified()

    def _toggle_healing_frame(self):
        """Показать/скрыть фрейм лечения"""
        if self.has_healing.get():
            self.healing_container.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        else:
            self.healing_container.pack_forget()
        self._mark_modified()

    def _on_area_type_change(self):
        """Обработка смены типа области"""
        self._mark_modified()

    def _on_max_rank_change(self):
        """Обработка смены макс. ранга"""
        max_rank = int(self.max_rank.get())
        self._create_rank_description_fields(max_rank)
        self._mark_modified()

    def _create_rank_description_fields(self, count: int):
        """Создание полей описаний для рангов"""
        # Удалить существующие
        for entry in self.rank_desc_entries:
            entry.destroy()
        self.rank_desc_entries.clear()

        # Создать новые
        for i in range(count):
            entry = LabeledEntry(
                self.rank_descriptions_container,
                f"Ранг {i+1}:", 60, ""
            )
            entry.pack(fill=tk.X, pady=1)
            entry.bind_change(self._mark_modified)
            self.rank_desc_entries.append(entry)

    def _add_damage_scaling(self):
        """Добавить масштабирование урона"""
        editor = ScalingEditor(
            self.damage_scaling_container,
            ScalingAttribute.get_display_names(),
            on_delete=lambda e: self._remove_scaling(e, self.damage_scaling_editors)
        )
        editor.pack(fill=tk.X, pady=2)
        self.damage_scaling_editors.append(editor)
        self._mark_modified()

    def _add_heal_scaling(self):
        """Добавить масштабирование лечения"""
        editor = ScalingEditor(
            self.heal_scaling_container,
            ScalingAttribute.get_display_names(),
            on_delete=lambda e: self._remove_scaling(e, self.heal_scaling_editors)
        )
        editor.pack(fill=tk.X, pady=2)
        self.heal_scaling_editors.append(editor)
        self._mark_modified()

    def _remove_scaling(self, editor: ScalingEditor, editors_list: List[ScalingEditor]):
        """Удалить масштабирование"""
        if editor in editors_list:
            editors_list.remove(editor)
        self._mark_modified()

    def _add_status_effect(self):
        """Добавить статус-эффект"""
        editor = StatusEffectEditor(
            self.effects_container,
            StatusEffectType.get_display_names(),
            on_delete=lambda e: self._remove_effect(e)
        )
        editor.pack(fill=tk.X, pady=5)
        self.effect_editors.append(editor)
        self._mark_modified()

    def _remove_effect(self, editor: StatusEffectEditor):
        """Удалить статус-эффект"""
        if editor in self.effect_editors:
            self.effect_editors.remove(editor)
        self._mark_modified()

    def _select_icon(self):
        """Выбор иконки"""
        initial_dir = str(self.assets_path / "sprites" / "skills")
        if not os.path.exists(initial_dir):
            initial_dir = str(self.assets_path)

        filepath = filedialog.askopenfilename(
            title="Выберите иконку",
            initialdir=initial_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif"),
                ("Все файлы", "*.*")
            ]
        )

        if filepath:
            # Относительный путь от assets
            try:
                rel_path = os.path.relpath(filepath, self.assets_path)
                self.icon_path_entry.set(rel_path)
            except ValueError:
                self.icon_path_entry.set(filepath)
            self._preview_icon()
            self._mark_modified()

    def _preview_icon(self):
        """Предпросмотр иконки"""
        path = self.icon_path_entry.get()
        if not path:
            return

        full_path = self.assets_path / path
        if not full_path.exists():
            full_path = Path(path)

        try:
            img = Image.open(full_path)
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            self.current_icon_image = ImageTk.PhotoImage(img)
            self.icon_preview_label.configure(image=self.current_icon_image, text="")
        except Exception as e:
            self.icon_preview_label.configure(image="", text=f"Ошибка:\n{e}")

    def _pick_color(self, color_type: str):
        """Выбор цвета"""
        from tkinter import colorchooser

        if color_type == "primary":
            initial = self.color_primary.get()
        else:
            initial = self.color_secondary.get()

        color = colorchooser.askcolor(color=initial, title="Выберите цвет")
        if color[1]:
            if color_type == "primary":
                self.color_primary.set(color[1])
            else:
                self.color_secondary.set(color[1])
            self._mark_modified()

    def _filter_skills_list(self, *args):
        """Фильтрация списка умений"""
        search = self.search_var.get().lower()
        if search == "поиск...":
            search = ""

        self.skills_listbox.delete(0, tk.END)
        for skill in self.skills_list:
            if search in skill.skill_id.lower() or search in skill.name.lower():
                display = f"{skill.name} ({skill.skill_id})"
                self.skills_listbox.insert(tk.END, display)

    def _on_skill_select(self, event):
        """Обработка выбора умения из списка"""
        selection = self.skills_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        # Найти соответствующее умение
        display = self.skills_listbox.get(idx)
        for skill in self.skills_list:
            if f"{skill.name} ({skill.skill_id})" == display:
                self._load_skill_to_editor(skill)
                break

    def _update_skills_listbox(self):
        """Обновление списка умений"""
        self.skills_listbox.delete(0, tk.END)
        for skill in self.skills_list:
            display = f"{skill.name} ({skill.skill_id})"
            self.skills_listbox.insert(tk.END, display)

    # === Методы работы с данными ===

    def _collect_skill_data(self) -> SkillData:
        """Сбор данных из редактора"""
        skill = SkillData()

        # Базовая информация
        skill.skill_id = self.skill_id_entry.get()
        skill.name = self.skill_name_entry.get()
        skill.description = self.description_text.get("1.0", tk.END).strip()
        skill.category = self.category_combo.get()
        skill.skill_type = self.skill_type_combo.get()

        # Затраты
        skill.costs = CostData(
            mana_cost=int(self.mana_cost.get()),
            mana_cost_per_rank=int(self.mana_per_rank.get()),
            stamina_cost=int(self.stamina_cost.get()),
            stamina_cost_per_rank=int(self.stamina_per_rank.get()),
            health_cost=int(self.health_cost.get()),
            health_cost_per_rank=int(self.health_per_rank.get()),
            cooldown=int(self.cooldown.get()),
            cooldown_reduction_per_rank=int(self.cd_reduction.get()),
        )

        # Требования
        skill.requirements = RequirementData(
            level_required=int(self.level_required.get()),
            required_weapon=self.weapon_combo.get(),
            min_strength=int(self.req_strength.get()),
            min_dexterity=int(self.req_dexterity.get()),
            min_constitution=int(self.req_constitution.get()),
            min_intelligence=int(self.req_intelligence.get()),
            min_spirit=int(self.req_spirit.get()),
        )

        # Нацеливание
        skill.targeting = TargetingData(
            target_type=self.target_type_combo.get(),
            area_type=self.area_type_combo.get(),
            tactical_range=int(self.tactical_range.get()),
            min_range=int(self.min_range.get()),
            range_per_rank=int(self.range_per_rank.get()),
            aoe_radius=int(self.aoe_radius.get()),
            aoe_radius_per_rank=int(self.aoe_radius_per_rank.get()),
            cone_angle=int(self.cone_angle.get()),
            can_target_self=self.can_target_self.get(),
            requires_line_of_sight=self.requires_los.get(),
            knockback_chance=float(self.knockback_chance.get()),
            knockback_chance_per_rank=float(self.knockback_per_rank.get()),
            knockback_distance=int(self.knockback_distance.get()),
        )

        # Урон
        if self.has_damage.get():
            scaling = [e.get_data() for e in self.damage_scaling_editors]
            scaling_data = [ScalingData.from_dict(s) for s in scaling]

            skill.damage = DamageData(
                base_damage=float(self.base_damage.get()),
                damage_multiplier=float(self.damage_multiplier.get()),
                damage_multiplier_per_rank=float(self.damage_mult_per_rank.get()),
                scaling=scaling_data,
                ignores_armor=self.ignores_armor.get(),
                armor_penetration_base=float(self.armor_penetration.get()),
                armor_penetration_per_rank=float(self.pen_per_rank.get()),
                crit_chance_bonus=float(self.crit_chance_bonus.get()),
                crit_chance_per_rank=float(self.crit_per_rank.get()),
                crit_damage_multiplier=float(self.crit_damage_mult.get()),
                hit_count_base=int(self.hit_count.get()),
                hit_count_per_rank=int(self.hits_per_rank.get()),
                damage_per_hit_multiplier=float(self.damage_per_hit.get()),
            )

        # Лечение
        if self.has_healing.get():
            scaling = [e.get_data() for e in self.heal_scaling_editors]
            scaling_data = [ScalingData.from_dict(s) for s in scaling]

            skill.healing = HealingData(
                base_heal=float(self.base_heal.get()),
                heal_percent_max_hp=float(self.heal_percent.get()),
                heal_percent_per_rank=float(self.heal_percent_per_rank.get()),
                scaling=scaling_data,
                heal_over_time=self.heal_over_time.get(),
                heal_per_turn_base=float(self.heal_per_turn.get()),
                heal_per_turn_per_rank=float(self.heal_per_turn_per_rank.get()),
                duration_base=int(self.heal_duration.get()),
                duration_per_rank=int(self.heal_duration_per_rank.get()),
            )

        # Эффекты
        skill.status_effects = [
            StatusEffectData.from_dict(e.get_data())
            for e in self.effect_editors
        ]

        # Прогрессия
        skill.rank_progression = RankProgressionData(
            max_rank=int(self.max_rank.get()),
            base_experience=int(self.base_exp.get()),
            experience_multiplier=float(self.exp_multiplier.get()),
            uses_per_rank_multiplier=int(self.uses_per_rank.get()),
            level_per_rank_multiplier=int(self.level_per_rank.get()),
            descriptions_per_rank=[e.get() for e in self.rank_desc_entries],
        )

        # Визуал
        skill.visuals = VisualData(
            icon_path=self.icon_path_entry.get(),
            animation_type=self.animation_type.get(),
            particle_effect=self.particle_effect.get(),
            sound_use=self.sound_use.get(),
            sound_hit=self.sound_hit.get(),
            color_primary=self.color_primary.get(),
            color_secondary=self.color_secondary.get(),
        )

        return skill

    def _load_skill_to_editor(self, skill: SkillData):
        """Загрузка умения в редактор"""
        # Базовая информация
        self.skill_id_entry.set(skill.skill_id)
        self.skill_name_entry.set(skill.name)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", skill.description)
        self.category_combo.set(skill.category)
        self.skill_type_combo.set(skill.skill_type)

        # Затраты
        self.mana_cost.set(skill.costs.mana_cost)
        self.mana_per_rank.set(skill.costs.mana_cost_per_rank)
        self.stamina_cost.set(skill.costs.stamina_cost)
        self.stamina_per_rank.set(skill.costs.stamina_cost_per_rank)
        self.health_cost.set(skill.costs.health_cost)
        self.health_per_rank.set(skill.costs.health_cost_per_rank)
        self.cooldown.set(skill.costs.cooldown)
        self.cd_reduction.set(skill.costs.cooldown_reduction_per_rank)

        # Требования
        self.level_required.set(skill.requirements.level_required)
        self.weapon_combo.set(skill.requirements.required_weapon)
        self.req_strength.set(skill.requirements.min_strength)
        self.req_dexterity.set(skill.requirements.min_dexterity)
        self.req_constitution.set(skill.requirements.min_constitution)
        self.req_intelligence.set(skill.requirements.min_intelligence)
        self.req_spirit.set(skill.requirements.min_spirit)

        # Нацеливание
        self.target_type_combo.set(skill.targeting.target_type)
        self.area_type_combo.set(skill.targeting.area_type)
        self.tactical_range.set(skill.targeting.tactical_range)
        self.min_range.set(skill.targeting.min_range)
        self.range_per_rank.set(skill.targeting.range_per_rank)
        self.aoe_radius.set(skill.targeting.aoe_radius)
        self.aoe_radius_per_rank.set(skill.targeting.aoe_radius_per_rank)
        self.cone_angle.set(skill.targeting.cone_angle)
        self.can_target_self.set(skill.targeting.can_target_self)
        self.requires_los.set(skill.targeting.requires_line_of_sight)
        self.knockback_chance.set(skill.targeting.knockback_chance)
        self.knockback_per_rank.set(skill.targeting.knockback_chance_per_rank)
        self.knockback_distance.set(skill.targeting.knockback_distance)

        # Урон
        self.has_damage.set(skill.damage is not None)
        self._toggle_damage_frame()
        if skill.damage:
            self.base_damage.set(skill.damage.base_damage)
            self.damage_multiplier.set(skill.damage.damage_multiplier)
            self.damage_mult_per_rank.set(skill.damage.damage_multiplier_per_rank)
            self.ignores_armor.set(skill.damage.ignores_armor)
            self.armor_penetration.set(skill.damage.armor_penetration_base)
            self.pen_per_rank.set(skill.damage.armor_penetration_per_rank)
            self.crit_chance_bonus.set(skill.damage.crit_chance_bonus)
            self.crit_per_rank.set(skill.damage.crit_chance_per_rank)
            self.crit_damage_mult.set(skill.damage.crit_damage_multiplier)
            self.hit_count.set(skill.damage.hit_count_base)
            self.hits_per_rank.set(skill.damage.hit_count_per_rank)
            self.damage_per_hit.set(skill.damage.damage_per_hit_multiplier)

            # Очистить и загрузить scaling
            for e in self.damage_scaling_editors:
                e.destroy()
            self.damage_scaling_editors.clear()

            for s in skill.damage.scaling:
                editor = ScalingEditor(
                    self.damage_scaling_container,
                    ScalingAttribute.get_display_names(),
                    on_delete=lambda e: self._remove_scaling(e, self.damage_scaling_editors)
                )
                editor.set_data(s.to_dict())
                editor.pack(fill=tk.X, pady=2)
                self.damage_scaling_editors.append(editor)

        # Лечение
        self.has_healing.set(skill.healing is not None)
        self._toggle_healing_frame()
        if skill.healing:
            self.base_heal.set(skill.healing.base_heal)
            self.heal_percent.set(skill.healing.heal_percent_max_hp)
            self.heal_percent_per_rank.set(skill.healing.heal_percent_per_rank)
            self.heal_over_time.set(skill.healing.heal_over_time)
            self.heal_per_turn.set(skill.healing.heal_per_turn_base)
            self.heal_per_turn_per_rank.set(skill.healing.heal_per_turn_per_rank)
            self.heal_duration.set(skill.healing.duration_base)
            self.heal_duration_per_rank.set(skill.healing.duration_per_rank)

            # Очистить и загрузить scaling
            for e in self.heal_scaling_editors:
                e.destroy()
            self.heal_scaling_editors.clear()

            for s in skill.healing.scaling:
                editor = ScalingEditor(
                    self.heal_scaling_container,
                    ScalingAttribute.get_display_names(),
                    on_delete=lambda e: self._remove_scaling(e, self.heal_scaling_editors)
                )
                editor.set_data(s.to_dict())
                editor.pack(fill=tk.X, pady=2)
                self.heal_scaling_editors.append(editor)

        # Эффекты
        for e in self.effect_editors:
            e.destroy()
        self.effect_editors.clear()

        for effect in skill.status_effects:
            editor = StatusEffectEditor(
                self.effects_container,
                StatusEffectType.get_display_names(),
                on_delete=lambda e: self._remove_effect(e)
            )
            editor.set_data(effect.to_dict())
            editor.pack(fill=tk.X, pady=5)
            self.effect_editors.append(editor)

        # Прогрессия
        self.max_rank.set(skill.rank_progression.max_rank)
        self.base_exp.set(skill.rank_progression.base_experience)
        self.exp_multiplier.set(skill.rank_progression.experience_multiplier)
        self.uses_per_rank.set(skill.rank_progression.uses_per_rank_multiplier)
        self.level_per_rank.set(skill.rank_progression.level_per_rank_multiplier)

        self._create_rank_description_fields(skill.rank_progression.max_rank)
        for i, desc in enumerate(skill.rank_progression.descriptions_per_rank):
            if i < len(self.rank_desc_entries):
                self.rank_desc_entries[i].set(desc)

        # Визуал
        self.icon_path_entry.set(skill.visuals.icon_path)
        self.animation_type.set(skill.visuals.animation_type)
        self.particle_effect.set(skill.visuals.particle_effect)
        self.sound_use.set(skill.visuals.sound_use)
        self.sound_hit.set(skill.visuals.sound_hit)
        self.color_primary.set(skill.visuals.color_primary)
        self.color_secondary.set(skill.visuals.color_secondary)

        if skill.visuals.icon_path:
            self._preview_icon()

        self.current_skill = skill
        self._clear_modified()

    # === Команды меню ===

    def _new_skill(self):
        """Создание нового умения"""
        if self.modified:
            if not messagebox.askyesno("Несохраненные изменения",
                                       "Есть несохраненные изменения. Продолжить?"):
                return

        new_skill = SkillData()
        new_skill.skill_id = f"new_skill_{len(self.skills_list) + 1}"
        new_skill.name = "Новое умение"

        self.skills_list.append(new_skill)
        self._update_skills_listbox()
        self._load_skill_to_editor(new_skill)

        # Выбрать в списке
        self.skills_listbox.selection_clear(0, tk.END)
        self.skills_listbox.selection_set(tk.END)
        self.skills_listbox.see(tk.END)

        self.status_label.configure(text="Создано новое умение")

    def _duplicate_skill(self):
        """Дублирование текущего умения"""
        skill = self._collect_skill_data()
        skill.skill_id = f"{skill.skill_id}_copy"
        skill.name = f"{skill.name} (копия)"

        self.skills_list.append(skill)
        self._update_skills_listbox()
        self._load_skill_to_editor(skill)

        self.skills_listbox.selection_clear(0, tk.END)
        self.skills_listbox.selection_set(tk.END)

        self.status_label.configure(text="Умение скопировано")

    def _delete_skill(self):
        """Удаление умения"""
        selection = self.skills_listbox.curselection()
        if not selection:
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранное умение?"):
            return

        idx = selection[0]
        display = self.skills_listbox.get(idx)

        for i, skill in enumerate(self.skills_list):
            if f"{skill.name} ({skill.skill_id})" == display:
                del self.skills_list[i]
                break

        self._update_skills_listbox()
        if self.skills_list:
            self._load_skill_to_editor(self.skills_list[0])
            self.skills_listbox.selection_set(0)
        else:
            self._new_skill()

        self.status_label.configure(text="Умение удалено")

    def _open_file(self):
        """Открытие файла"""
        filepath = filedialog.askopenfilename(
            title="Открыть файл умений",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.skills_list.clear()

            if isinstance(data, list):
                for item in data:
                    self.skills_list.append(SkillData.from_dict(item))
            elif isinstance(data, dict):
                for skill_id, skill_data in data.items():
                    if not skill_id.startswith("_"):
                        skill_data["skill_id"] = skill_id
                        self.skills_list.append(SkillData.from_dict(skill_data))

            self._update_skills_listbox()
            if self.skills_list:
                self._load_skill_to_editor(self.skills_list[0])
                self.skills_listbox.selection_set(0)

            self.current_file = filepath
            self.status_label.configure(text=f"Открыт: {os.path.basename(filepath)}")
            self._clear_modified()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def _save_file(self):
        """Сохранение файла"""
        # Обновить текущее умение в списке
        current = self._collect_skill_data()
        for i, skill in enumerate(self.skills_list):
            if skill.skill_id == self.current_skill.skill_id:
                self.skills_list[i] = current
                break
        else:
            self.skills_list.append(current)

        if not self.current_file:
            self._save_as()
            return

        try:
            data = [skill.to_dict() for skill in self.skills_list]
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._update_skills_listbox()
            self._clear_modified()
            self.status_label.configure(text=f"Сохранено: {os.path.basename(self.current_file)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def _save_as(self):
        """Сохранение как..."""
        filepath = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )

        if filepath:
            self.current_file = filepath
            self._save_file()

    def _import_from_game(self):
        """Импорт из skills_config.json"""
        config_file = self.config_path / "skills_config.json"

        if not config_file.exists():
            messagebox.showerror("Ошибка", "Файл skills_config.json не найден")
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.skills_list.clear()

            # Импорт из разных категорий
            categories = [
                ("combat_skills", "combat"),
                ("magic_skills", "magic"),
                ("healing_skills", "magic"),
                ("crafting_skills", "crafting"),
                ("exploration_skills", "exploration"),
            ]

            for section_key, category in categories:
                if section_key in data:
                    for skill_id, skill_data in data[section_key].items():
                        if skill_id.startswith("_"):
                            continue
                        skill = self._import_game_skill(skill_id, skill_data, category)
                        self.skills_list.append(skill)

            # Оружейные умения
            if "weapon_skills" in data:
                for weapon_type, skills in data["weapon_skills"].items():
                    if weapon_type.startswith("_"):
                        continue
                    for skill_id, skill_data in skills.items():
                        if skill_id.startswith("_"):
                            continue
                        skill = self._import_game_skill(skill_id, skill_data, "combat")
                        skill.requirements.required_weapon = weapon_type.replace("_skills", "")
                        self.skills_list.append(skill)

            self._update_skills_listbox()
            if self.skills_list:
                self._load_skill_to_editor(self.skills_list[0])
                self.skills_listbox.selection_set(0)

            self.status_label.configure(text=f"Импортировано {len(self.skills_list)} умений")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _import_game_skill(self, skill_id: str, data: Dict[str, Any], category: str) -> SkillData:
        """Импорт одного умения из игрового формата"""
        skill = SkillData()
        skill.skill_id = skill_id
        skill.name = data.get("name", skill_id)
        skill.description = data.get("description", "")
        skill.category = data.get("category", category)
        skill.skill_type = "passive" if data.get("passive", False) else "active"

        skill.costs = CostData(
            mana_cost=data.get("mana_cost", 0),
            stamina_cost=data.get("stamina_cost", 0),
            cooldown=data.get("cooldown", 0),
        )

        skill.requirements = RequirementData(
            required_weapon=data.get("required_weapon", "any"),
        )

        skill.targeting = TargetingData(
            tactical_range=data.get("tactical_range", 1),
            min_range=data.get("min_range", 0),
            aoe_radius=data.get("aoe_range", 0),
        )

        # Проверка на урон
        has_damage = any([
            data.get("base_damage"),
            data.get("base_damage_multiplier"),
            data.get("damage_multiplier_per_rank"),
        ])

        if has_damage:
            skill.damage = DamageData(
                base_damage=data.get("base_damage", 0),
                damage_multiplier=data.get("base_damage_multiplier", 1.0),
                damage_multiplier_per_rank=data.get("damage_multiplier_per_rank", 0),
                ignores_armor=data.get("ignores_armor", False),
                armor_penetration_base=data.get("base_armor_penetration", 0),
                armor_penetration_per_rank=data.get("armor_penetration_per_rank", 0),
                crit_chance_bonus=data.get("base_crit_chance", 0),
                crit_chance_per_rank=data.get("crit_chance_per_rank", 0),
                hit_count_base=data.get("base_hits", 1),
                hit_count_per_rank=data.get("hits_per_rank", 0),
            )

            # Scaling
            for attr in ["intelligence", "strength", "dexterity", "spirit"]:
                mult = data.get(f"{attr}_multiplier")
                if mult:
                    skill.damage.scaling.append(ScalingData(
                        attribute=attr,
                        multiplier=mult
                    ))

        # Проверка на лечение
        has_healing = any([
            data.get("base_heal_percent"),
            data.get("base_heal_per_turn"),
        ])

        if has_healing:
            skill.healing = HealingData(
                heal_percent_max_hp=data.get("base_heal_percent", 0),
                heal_percent_per_rank=data.get("heal_percent_per_rank", 0),
                heal_over_time=bool(data.get("base_heal_per_turn")),
                heal_per_turn_base=data.get("base_heal_per_turn", 0),
                heal_per_turn_per_rank=data.get("heal_per_turn_per_rank", 0),
                duration_base=data.get("base_duration", 0),
                duration_per_rank=data.get("duration_per_rank", 0),
            )

        # Описания по рангам
        if "description_per_rank" in data:
            skill.rank_progression.descriptions_per_rank = data["description_per_rank"]

        return skill

    def _export_to_game(self):
        """Экспорт в формат skills_config.json"""
        # Обновить текущее умение
        current = self._collect_skill_data()
        for i, skill in enumerate(self.skills_list):
            if skill.skill_id == self.current_skill.skill_id:
                self.skills_list[i] = current
                break

        filepath = filedialog.asksaveasfilename(
            title="Экспорт в игровой формат",
            defaultextension=".json",
            initialdir=str(self.config_path),
            filetypes=[("JSON файлы", "*.json")]
        )

        if not filepath:
            return

        try:
            # Группировка по категориям
            output = {
                "_description": "Конфигурация умений (экспорт из Skills Crafter)",
                "_version": "2.0.0",
            }

            category_map = {
                "combat": "combat_skills",
                "magic": "magic_skills",
                "crafting": "crafting_skills",
                "exploration": "exploration_skills",
            }

            weapon_skills = {}

            for skill in self.skills_list:
                game_data = skill.to_game_config_format()

                # Оружейные умения
                if skill.requirements.required_weapon != "any":
                    weapon_type = f"{skill.requirements.required_weapon}_skills"
                    if weapon_type not in weapon_skills:
                        weapon_skills[weapon_type] = {}
                    weapon_skills[weapon_type][skill.skill_id] = game_data
                else:
                    # Обычные умения
                    section = category_map.get(skill.category, "combat_skills")
                    if section not in output:
                        output[section] = {}
                    output[section][skill.skill_id] = game_data

            if weapon_skills:
                output["weapon_skills"] = weapon_skills

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            self.status_label.configure(text=f"Экспортировано в: {os.path.basename(filepath)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта:\n{e}")

    def _generate_rank_descriptions(self):
        """Автогенерация описаний по рангам"""
        skill = self._collect_skill_data()
        descriptions = []

        for rank in range(1, skill.rank_progression.max_rank + 1):
            parts = []

            # Урон
            if skill.damage:
                mult = skill.damage.damage_multiplier + (skill.damage.damage_multiplier_per_rank * (rank - 1))
                parts.append(f"Урон x{mult:.2f}")

                if skill.damage.armor_penetration_base > 0:
                    pen = (skill.damage.armor_penetration_base +
                           skill.damage.armor_penetration_per_rank * (rank - 1)) * 100
                    parts.append(f"пробитие {pen:.0f}%")

                if skill.damage.crit_chance_bonus > 0:
                    crit = (skill.damage.crit_chance_bonus +
                            skill.damage.crit_chance_per_rank * (rank - 1)) * 100
                    parts.append(f"крит {crit:.0f}%")

                if skill.damage.hit_count_base > 1:
                    hits = skill.damage.hit_count_base + skill.damage.hit_count_per_rank * (rank - 1)
                    parts.append(f"{hits} ударов")

            # Лечение
            if skill.healing:
                if skill.healing.heal_percent_max_hp > 0:
                    heal = (skill.healing.heal_percent_max_hp +
                            skill.healing.heal_percent_per_rank * (rank - 1)) * 100
                    parts.append(f"лечение {heal:.0f}% HP")

                if skill.healing.heal_over_time:
                    hpt = skill.healing.heal_per_turn_base + skill.healing.heal_per_turn_per_rank * (rank - 1)
                    dur = skill.healing.duration_base + skill.healing.duration_per_rank * (rank - 1)
                    parts.append(f"{hpt:.0f} HP/ход на {dur} ходов")

            # Эффекты
            for effect in skill.status_effects:
                eff_name = StatusEffectType.get_display_names().get(effect.effect_type, effect.effect_type)
                dur = effect.duration_base + effect.duration_per_rank * (rank - 1)
                val = effect.value_base + effect.value_per_rank * (rank - 1)

                if effect.chance_base < 1.0:
                    chance = (effect.chance_base + effect.chance_per_rank * (rank - 1)) * 100
                    parts.append(f"{eff_name} {val:.0f} ({dur} ход.), шанс {chance:.0f}%")
                else:
                    parts.append(f"{eff_name} {val:.0f} на {dur} ход.")

            desc = f"Ранг {rank}: " + ", ".join(parts) if parts else f"Ранг {rank}"
            descriptions.append(desc)

        # Обновить поля
        for i, desc in enumerate(descriptions):
            if i < len(self.rank_desc_entries):
                self.rank_desc_entries[i].set(desc)

        self._mark_modified()
        self.status_label.configure(text="Описания сгенерированы")

    def _preview_json(self):
        """Предпросмотр JSON"""
        skill = self._collect_skill_data()

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Предпросмотр JSON")
        preview_window.geometry("600x500")

        # Tabs для разных форматов
        notebook = ttk.Notebook(preview_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Полный формат
        full_frame = ttk.Frame(notebook)
        notebook.add(full_frame, text="Полный формат")

        full_text = tk.Text(full_frame, wrap=tk.NONE)
        full_scroll = ttk.Scrollbar(full_frame, orient=tk.VERTICAL, command=full_text.yview)
        full_text.configure(yscrollcommand=full_scroll.set)

        full_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        full_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        full_json = json.dumps(skill.to_dict(), ensure_ascii=False, indent=2)
        full_text.insert("1.0", full_json)

        # Игровой формат
        game_frame = ttk.Frame(notebook)
        notebook.add(game_frame, text="Игровой формат")

        game_text = tk.Text(game_frame, wrap=tk.NONE)
        game_scroll = ttk.Scrollbar(game_frame, orient=tk.VERTICAL, command=game_text.yview)
        game_text.configure(yscrollcommand=game_scroll.set)

        game_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        game_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        game_json = json.dumps(
            {skill.skill_id: skill.to_game_config_format()},
            ensure_ascii=False,
            indent=2
        )
        game_text.insert("1.0", game_json)

    def _validate_skill(self):
        """Валидация текущего умения"""
        skill = self._collect_skill_data()
        errors = skill.validate()

        if errors:
            messagebox.showwarning(
                "Ошибки валидации",
                "Найдены следующие проблемы:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
        else:
            messagebox.showinfo("Валидация", "Умение прошло валидацию успешно!")

    def _show_damage_calculator(self):
        """Калькулятор урона"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Калькулятор урона")
        calc_window.geometry("400x300")

        skill = self._collect_skill_data()

        # Входные данные
        input_frame = ttk.LabelFrame(calc_window, text="Параметры персонажа")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        level_spin = LabeledSpinbox(input_frame, "Уровень:", 1, 100, 1, 10)
        level_spin.pack(fill=tk.X, pady=2)

        str_spin = LabeledSpinbox(input_frame, "Сила:", 1, 100, 1, 15)
        str_spin.pack(fill=tk.X, pady=2)

        dex_spin = LabeledSpinbox(input_frame, "Ловкость:", 1, 100, 1, 15)
        dex_spin.pack(fill=tk.X, pady=2)

        int_spin = LabeledSpinbox(input_frame, "Интеллект:", 1, 100, 1, 15)
        int_spin.pack(fill=tk.X, pady=2)

        weapon_spin = LabeledSpinbox(input_frame, "Урон оружия:", 1, 500, 10, 50)
        weapon_spin.pack(fill=tk.X, pady=2)

        rank_spin = LabeledSpinbox(input_frame, "Ранг умения:", 1, 5, 1, 1)
        rank_spin.pack(fill=tk.X, pady=2)

        # Результат
        result_frame = ttk.LabelFrame(calc_window, text="Расчетный урон")
        result_frame.pack(fill=tk.X, padx=10, pady=5)

        result_label = ttk.Label(result_frame, text="—", font=("TkDefaultFont", 14))
        result_label.pack(pady=10)

        def calculate():
            if not skill.damage:
                result_label.configure(text="Умение не наносит урона")
                return

            rank = int(rank_spin.get())
            weapon_dmg = int(weapon_spin.get())
            strength = int(str_spin.get())
            dexterity = int(dex_spin.get())
            intelligence = int(int_spin.get())

            # Базовый урон
            base = skill.damage.base_damage

            # Множитель
            mult = skill.damage.damage_multiplier + skill.damage.damage_multiplier_per_rank * (rank - 1)
            damage = base + weapon_dmg * mult

            # Скейлинг
            for s in skill.damage.scaling:
                stat_value = {
                    "strength": strength,
                    "dexterity": dexterity,
                    "intelligence": intelligence,
                }.get(s.attribute, 0)

                stat_mult = s.multiplier + s.multiplier_per_rank * (rank - 1)
                damage += stat_value * stat_mult

            # Множественные удары
            hits = skill.damage.hit_count_base + skill.damage.hit_count_per_rank * (rank - 1)
            total = damage * hits * skill.damage.damage_per_hit_multiplier

            result_label.configure(text=f"{total:.0f} урона ({hits} x {damage:.0f})")

        ttk.Button(calc_window, text="Рассчитать", command=calculate).pack(pady=10)

    def _show_about(self):
        """О программе"""
        messagebox.showinfo(
            "О программе",
            "Skills Crafter v1.0.0\n\n"
            "Утилита для создания и редактирования умений\n"
            "для Classic RPG\n\n"
            "Возможности:\n"
            "• Создание умений через визуальный интерфейс\n"
            "• Импорт/экспорт в игровой формат\n"
            "• Предпросмотр спрайтов\n"
            "• Калькулятор урона\n"
            "• Автогенерация описаний"
        )

    def _on_close(self):
        """Обработка закрытия"""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Несохраненные изменения",
                "Сохранить изменения перед выходом?"
            )
            if result is None:
                return
            if result:
                self._save_file()

        self.root.destroy()


def main():
    """Точка входа"""
    root = tk.Tk()
    app = SkillsCrafterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
