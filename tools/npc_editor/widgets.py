"""
Переиспользуемые UI компоненты для NPC Editor
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

from .config import (
    STATS, QUALITY_LEVELS, EQUIPMENT_SLOTS, SKILL_CATEGORIES, SKILLS,
    LOOT_CATEGORIES, NPC_TYPES, RELATIONSHIPS, SPRITE_FOLDERS
)


class SpriteSelector(ttk.Frame):
    """Виджет выбора спрайта с превью"""

    def __init__(self, parent, assets_path, **kwargs):
        super().__init__(parent, **kwargs)
        self.assets_path = assets_path
        self.current_image = None

        self.sprite_var = tk.StringVar()
        self.sprite_combo = ttk.Combobox(self, textvariable=self.sprite_var, width=28, state='readonly')
        self.sprite_combo.pack(side=tk.LEFT, padx=5)
        self.sprite_combo.bind('<<ComboboxSelected>>', self._on_sprite_changed)

        self.preview_label = ttk.Label(self)
        self.preview_label.pack(side=tk.LEFT, padx=10)

    def update_for_type(self, npc_type):
        """Обновить список спрайтов для типа NPC"""
        folder = SPRITE_FOLDERS.get(npc_type, 'soldier')
        sprite_path = os.path.join(self.assets_path, folder)

        sprites = []
        if os.path.exists(sprite_path):
            for file in sorted(os.listdir(sprite_path)):
                if file.endswith('.png'):
                    sprites.append(f"{folder}/{file}")

        self.sprite_combo['values'] = sprites
        if sprites:
            self.sprite_var.set(sprites[0])
            self._load_preview(sprites[0])

    def _on_sprite_changed(self, event=None):
        """Обработка смены спрайта"""
        self._load_preview(self.sprite_var.get())

    def _load_preview(self, sprite_path):
        """Загрузка превью"""
        full_path = os.path.join(self.assets_path, sprite_path)
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                img = img.resize((48, 48), Image.Resampling.NEAREST)
                self.current_image = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.current_image)
            except Exception:
                pass

    def get(self):
        return self.sprite_var.get()

    def set(self, value):
        self.sprite_var.set(value)
        self._load_preview(value)


class StatsDistributionWidget(ttk.LabelFrame):
    """Виджет распределения характеристик (в процентах)"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Распределение характеристик", padding=10, **kwargs)

        self.stats_vars = {}

        # Строка статов
        stats_row = ttk.Frame(self)
        stats_row.pack(fill=tk.X, pady=5)

        for stat_id, stat_name, abbr in STATS:
            stat_frame = ttk.Frame(stats_row)
            stat_frame.pack(side=tk.LEFT, padx=10)

            ttk.Label(stat_frame, text=f"{abbr}:", width=4).pack(side=tk.LEFT)
            var = tk.IntVar(value=16)
            self.stats_vars[stat_id] = var

            spinbox = ttk.Spinbox(stat_frame, from_=0, to=100, textvariable=var, width=4,
                                  command=self._update_total)
            spinbox.pack(side=tk.LEFT, padx=2)
            spinbox.bind('<KeyRelease>', lambda e: self._update_total())
            ttk.Label(stat_frame, text="%").pack(side=tk.LEFT)

        # Индикатор суммы
        total_frame = ttk.Frame(self)
        total_frame.pack(fill=tk.X, pady=5)

        self.total_var = tk.StringVar(value="Сумма: 96%")
        self.total_label = ttk.Label(total_frame, textvariable=self.total_var, font=('Arial', 10, 'bold'))
        self.total_label.pack(side=tk.LEFT)

        # Кнопка баланса
        ttk.Button(total_frame, text="Выровнять", command=self._balance_stats, width=10).pack(side=tk.RIGHT)

    def _update_total(self, event=None):
        """Обновление суммы"""
        total = sum(var.get() for var in self.stats_vars.values())
        self.total_var.set(f"Сумма: {total}%")
        if total == 100:
            self.total_label.configure(foreground='green')
        elif total > 100:
            self.total_label.configure(foreground='red')
        else:
            self.total_label.configure(foreground='orange')

    def _balance_stats(self):
        """Выровнять статы до 100%"""
        total = sum(var.get() for var in self.stats_vars.values())
        if total == 0:
            for var in self.stats_vars.values():
                var.set(16)
            list(self.stats_vars.values())[0].set(20)  # Первый стат чуть больше
        else:
            diff = 100 - total
            if diff != 0:
                # Добавляем/убираем разницу к первому стату
                first_stat = list(self.stats_vars.values())[0]
                first_stat.set(max(0, min(100, first_stat.get() + diff)))
        self._update_total()

    def get(self):
        """Получить распределение"""
        return {stat_id: var.get() for stat_id, var in self.stats_vars.items()}

    def set(self, distribution):
        """Установить распределение"""
        for stat_id, var in self.stats_vars.items():
            var.set(distribution.get(stat_id, 16))
        self._update_total()

    def is_valid(self):
        """Проверка корректности"""
        return sum(var.get() for var in self.stats_vars.values()) == 100


class StatsFixedWidget(ttk.LabelFrame):
    """Виджет фиксированных характеристик (для уникальных NPC)"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Характеристики", padding=10, **kwargs)

        self.stats_vars = {}
        stats_row = ttk.Frame(self)
        stats_row.pack(fill=tk.X, pady=5)

        for stat_id, stat_name, abbr in STATS:
            stat_frame = ttk.Frame(stats_row)
            stat_frame.pack(side=tk.LEFT, padx=15)

            ttk.Label(stat_frame, text=f"{stat_name}:").pack(side=tk.LEFT)
            var = tk.IntVar(value=10)
            self.stats_vars[stat_id] = var
            ttk.Spinbox(stat_frame, from_=1, to=100, textvariable=var, width=5).pack(side=tk.LEFT, padx=3)

    def get(self):
        return {stat_id: var.get() for stat_id, var in self.stats_vars.items()}

    def set(self, stats):
        for stat_id, var in self.stats_vars.items():
            var.set(stats.get(stat_id, 10))


class EquipmentWidget(ttk.LabelFrame):
    """Виджет экипировки"""

    def __init__(self, parent, is_template=True, **kwargs):
        super().__init__(parent, text="Экипировка", padding=10, **kwargs)
        self.is_template = is_template
        self.equip_vars = {}

        # Основные слоты в две строки
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=3)
        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=3)

        slots_row1 = EQUIPMENT_SLOTS[:4]  # weapon, offhand, head, body
        slots_row2 = EQUIPMENT_SLOTS[4:]  # hands, feet, amulet, ring

        for slot_id, slot_name in slots_row1:
            self._create_slot(row1, slot_id, slot_name)

        for slot_id, slot_name in slots_row2:
            self._create_slot(row2, slot_id, slot_name)

    def _create_slot(self, parent, slot_id, slot_name):
        """Создание слота экипировки"""
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=8, pady=2)

        enabled_var = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(frame, text=slot_name, variable=enabled_var, width=10)
        cb.pack(side=tk.LEFT)

        quality_var = tk.StringVar(value="common")
        qual_combo = ttk.Combobox(frame, textvariable=quality_var, width=10, state='readonly')
        qual_combo['values'] = [q[0] for q in QUALITY_LEVELS]
        qual_combo.pack(side=tk.LEFT, padx=2)

        self.equip_vars[slot_id] = {'enabled': enabled_var, 'quality': quality_var}

    def get(self):
        """Получить данные экипировки"""
        result = {}
        for slot_id, vars_dict in self.equip_vars.items():
            if vars_dict['enabled'].get():
                result[slot_id] = {'quality': vars_dict['quality'].get()}
        return result

    def set(self, equipment):
        """Установить экипировку"""
        for slot_id, vars_dict in self.equip_vars.items():
            if slot_id in equipment:
                vars_dict['enabled'].set(True)
                vars_dict['quality'].set(equipment[slot_id].get('quality', 'common'))
            else:
                vars_dict['enabled'].set(False)
                vars_dict['quality'].set('common')

    def apply_preset(self, preset):
        """Применить пресет экипировки"""
        self.set(preset)


class LootWidget(ttk.LabelFrame):
    """Компактный виджет настройки лута (объединённый с деньгами)"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Добыча", padding=10, **kwargs)

        # === Секция денег ===
        gold_frame = ttk.LabelFrame(self, text="Золото", padding=5)
        gold_frame.pack(fill=tk.X, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X, pady=2)

        ttk.Label(gold_row, text="Шанс:").pack(side=tk.LEFT)
        self.gold_chance_var = tk.IntVar(value=80)
        ttk.Spinbox(gold_row, from_=0, to=100, textvariable=self.gold_chance_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(gold_row, text="%").pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(gold_row, text="База:").pack(side=tk.LEFT)
        self.gold_base_var = tk.IntVar(value=10)
        ttk.Spinbox(gold_row, from_=0, to=10000, textvariable=self.gold_base_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(gold_row, text="× Уровень:").pack(side=tk.LEFT, padx=(15, 0))
        self.gold_mult_var = tk.DoubleVar(value=1.5)
        ttk.Spinbox(gold_row, from_=0.0, to=10.0, increment=0.1, textvariable=self.gold_mult_var, width=5).pack(side=tk.LEFT, padx=2)

        ttk.Label(gold_row, text="± Разброс:").pack(side=tk.LEFT, padx=(15, 0))
        self.gold_variance_var = tk.IntVar(value=20)
        ttk.Spinbox(gold_row, from_=0, to=100, textvariable=self.gold_variance_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(gold_row, text="%").pack(side=tk.LEFT)

        # === Секция предметов ===
        items_frame = ttk.LabelFrame(self, text="Предметы", padding=5)
        items_frame.pack(fill=tk.X, pady=5)

        # Максимальное количество
        max_row = ttk.Frame(items_frame)
        max_row.pack(fill=tk.X, pady=2)
        ttk.Label(max_row, text="Макс. предметов:").pack(side=tk.LEFT)
        self.max_items_var = tk.IntVar(value=3)
        ttk.Spinbox(max_row, from_=0, to=10, textvariable=self.max_items_var, width=4).pack(side=tk.LEFT, padx=5)

        # Категории лута - компактная таблица
        self.category_vars = {}

        # Заголовок таблицы
        header_row = ttk.Frame(items_frame)
        header_row.pack(fill=tk.X, pady=(10, 2))

        ttk.Label(header_row, text="Категория", width=14, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header_row, text="Базовый %", width=10, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)

        # Качества - компактно
        for qual_id, qual_name, _ in QUALITY_LEVELS[:5]:  # Только первые 5
            ttk.Label(header_row, text=qual_name[:3], width=5, font=('Arial', 8)).pack(side=tk.LEFT, padx=1)

        # Строки категорий
        for cat_id, cat_name, icon in LOOT_CATEGORIES:
            cat_row = ttk.Frame(items_frame)
            cat_row.pack(fill=tk.X, pady=1)

            enabled_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(cat_row, text=f"{cat_name}", variable=enabled_var, width=12).pack(side=tk.LEFT)

            base_chance_var = tk.IntVar(value=15)
            ttk.Spinbox(cat_row, from_=0, to=100, textvariable=base_chance_var, width=4).pack(side=tk.LEFT, padx=5)
            ttk.Label(cat_row, text="%").pack(side=tk.LEFT)

            # Качества для категории
            quality_vars = {}
            for qual_id, qual_name, _ in QUALITY_LEVELS[:5]:
                qvar = tk.BooleanVar(value=qual_id in ['poor', 'common', 'uncommon'])
                ttk.Checkbutton(cat_row, variable=qvar, width=3).pack(side=tk.LEFT, padx=1)
                quality_vars[qual_id] = qvar

            self.category_vars[cat_id] = {
                'enabled': enabled_var,
                'base_chance': base_chance_var,
                'qualities': quality_vars
            }

    def get_gold(self):
        """Получить настройки золота"""
        return {
            'chance': self.gold_chance_var.get(),
            'base': self.gold_base_var.get(),
            'level_multiplier': self.gold_mult_var.get(),
            'variance_percent': self.gold_variance_var.get()
        }

    def set_gold(self, gold):
        """Установить настройки золота"""
        self.gold_chance_var.set(gold.get('chance', 80))
        self.gold_base_var.set(gold.get('base', 10))
        self.gold_mult_var.set(gold.get('level_multiplier', 1.5))
        self.gold_variance_var.set(gold.get('variance_percent', 20))

    def get_loot(self):
        """Получить настройки лута"""
        return {
            'max_items': self.max_items_var.get(),
            'categories': {
                cat_id: {
                    'enabled': vars_dict['enabled'].get(),
                    'base_chance': vars_dict['base_chance'].get(),
                    'qualities': {
                        qual_id: qvar.get()
                        for qual_id, qvar in vars_dict['qualities'].items()
                    }
                }
                for cat_id, vars_dict in self.category_vars.items()
            }
        }

    def set_loot(self, loot):
        """Установить настройки лута"""
        self.max_items_var.set(loot.get('max_items', 3))
        categories = loot.get('categories', {})

        for cat_id, vars_dict in self.category_vars.items():
            cat_data = categories.get(cat_id, {})
            vars_dict['enabled'].set(cat_data.get('enabled', True))
            vars_dict['base_chance'].set(cat_data.get('base_chance', 15))

            qualities = cat_data.get('qualities', {})
            for qual_id, qvar in vars_dict['qualities'].items():
                qvar.set(qualities.get(qual_id, qual_id in ['poor', 'common', 'uncommon']))


class SkillsWidget(ttk.LabelFrame):
    """Виджет умений"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Умения", padding=10, **kwargs)

        self.skills_vars = {}
        skills_container = ttk.Frame(self)
        skills_container.pack(fill=tk.BOTH, expand=True)

        col = 0
        for cat_id, cat_name in SKILL_CATEGORIES.items():
            cat_frame = ttk.LabelFrame(skills_container, text=cat_name, padding=5)
            cat_frame.grid(row=0, column=col, padx=5, pady=5, sticky='nsew')
            col += 1

            cat_skills = [s for s in SKILLS if s[2] == cat_id]
            for skill_id, skill_name, _, desc in cat_skills:
                skill_row = ttk.Frame(cat_frame)
                skill_row.pack(fill=tk.X, pady=2)

                enabled_var = tk.BooleanVar(value=False)
                rank_var = tk.IntVar(value=1)

                cb = ttk.Checkbutton(skill_row, text=skill_name, variable=enabled_var, width=18)
                cb.pack(side=tk.LEFT)

                ttk.Label(skill_row, text="Ур:").pack(side=tk.LEFT, padx=2)
                ttk.Spinbox(skill_row, from_=1, to=5, textvariable=rank_var, width=3).pack(side=tk.LEFT)

                self.skills_vars[skill_id] = (enabled_var, rank_var)

    def get(self):
        """Получить умения"""
        result = {}
        for skill_id, (enabled_var, rank_var) in self.skills_vars.items():
            if enabled_var.get():
                result[skill_id] = {'rank': rank_var.get()}
        return result

    def set(self, skills):
        """Установить умения"""
        for skill_id, (enabled_var, rank_var) in self.skills_vars.items():
            if skill_id in skills:
                enabled_var.set(True)
                rank_var.set(skills[skill_id].get('rank', 1))
            else:
                enabled_var.set(False)
                rank_var.set(1)

    def apply_preset(self, skill_list):
        """Применить пресет умений"""
        for skill_id, (enabled_var, rank_var) in self.skills_vars.items():
            enabled_var.set(skill_id in skill_list)
            rank_var.set(1)


class NPCListWidget(ttk.LabelFrame):
    """Виджет списка NPC с кнопками управления"""

    def __init__(self, parent, title, on_select_callback, **kwargs):
        super().__init__(parent, text=title, padding=5, **kwargs)

        self.on_select_callback = on_select_callback

        self.listbox = tk.Listbox(self, width=35, font=('Arial', 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)

        self.add_btn = ttk.Button(btn_frame, text="Добавить", width=10)
        self.add_btn.pack(side=tk.LEFT, padx=2)

        self.delete_btn = ttk.Button(btn_frame, text="Удалить", width=10)
        self.delete_btn.pack(side=tk.LEFT, padx=2)

        self.copy_btn = ttk.Button(btn_frame, text="Копировать", width=10)
        self.copy_btn.pack(side=tk.LEFT, padx=2)

    def _on_select(self, event):
        selection = self.listbox.curselection()
        if selection and self.on_select_callback:
            self.on_select_callback(selection[0])

    def refresh(self, items, format_func):
        """Обновить список"""
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, format_func(item))

    def get_selection(self):
        """Получить индекс выбранного элемента"""
        selection = self.listbox.curselection()
        return selection[0] if selection else None

    def select(self, index):
        """Выбрать элемент по индексу"""
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)


class ScrollableFrame(ttk.Frame):
    """Фрейм с прокруткой"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(self)
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)

        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Привязка скролла мыши
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def get_frame(self):
        """Получить фрейм для добавления содержимого"""
        return self.scrollable_frame
