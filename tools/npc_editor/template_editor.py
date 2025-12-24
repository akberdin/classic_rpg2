"""
Редактор типовых NPC с вкладками: Общая, Лут, Умения
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy

from .config import (
    NPC_TYPES, RANKS, RELATIONSHIPS, STATS_PRESETS,
    EQUIPMENT_PRESETS, LOOT_PRESETS, SKILLS_PRESETS
)
from .widgets import (
    SpriteSelector, StatsDistributionWidget, EquipmentWidget,
    LootWidget, SkillsWidget, NPCListWidget, ScrollableFrame
)


class TemplateEditor(ttk.Frame):
    """Редактор типовых NPC"""

    def __init__(self, parent, assets_path, templates, on_change_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.assets_path = assets_path
        self.templates = templates
        self.on_change_callback = on_change_callback

        self._create_ui()
        self.refresh_list()

    def _create_ui(self):
        """Создание интерфейса"""
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - список шаблонов
        self.list_widget = NPCListWidget(main_paned, "Шаблоны NPC", self._on_select)
        main_paned.add(self.list_widget, weight=1)

        self.list_widget.add_btn.configure(command=self.add_template)
        self.list_widget.delete_btn.configure(command=self.delete_template)
        self.list_widget.copy_btn.configure(command=self.duplicate_template)

        # Правая панель - редактор с вкладками
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)

        # Notebook для вкладок редактора
        self.editor_notebook = ttk.Notebook(right_frame)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка "Общая"
        self._create_general_tab()

        # Вкладка "Лут"
        self._create_loot_tab()

        # Вкладка "Умения"
        self._create_skills_tab()

        # Кнопка применить
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Применить изменения", command=self.apply_changes).pack(side=tk.RIGHT, padx=10)
        ttk.Button(btn_frame, text="Применить пресет типа", command=self._apply_type_preset).pack(side=tk.RIGHT, padx=5)

    def _create_general_tab(self):
        """Вкладка Общая: основная информация, характеристики, экипировка"""
        scroll_frame = ScrollableFrame(self.editor_notebook)
        self.editor_notebook.add(scroll_frame, text="  Общая  ")

        parent = scroll_frame.get_frame()

        # === Основная информация ===
        info_frame = ttk.LabelFrame(parent, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Строка 1: ID и Название
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="ID:", width=8).pack(side=tk.LEFT)
        self.id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.id_var, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Название:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var, width=25).pack(side=tk.LEFT, padx=5)

        # Строка 2: Тип, Ранг, Отношение
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=3)

        ttk.Label(row2, text="Тип:", width=8).pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(row2, textvariable=self.type_var, width=18, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)

        ttk.Label(row2, text="Ранг:", width=6).pack(side=tk.LEFT, padx=(20, 0))
        self.rank_var = tk.IntVar(value=1)
        rank_combo = ttk.Combobox(row2, textvariable=self.rank_var, width=4, state='readonly')
        rank_combo['values'] = RANKS
        rank_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="Отношение:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row2, textvariable=self.relation_var, width=18, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        # Строка 3: Спрайт
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=3)

        ttk.Label(row3, text="Спрайт:", width=8).pack(side=tk.LEFT)
        self.sprite_selector = SpriteSelector(row3, self.assets_path)
        self.sprite_selector.pack(side=tk.LEFT, padx=5)

        # === Распределение характеристик ===
        self.stats_widget = StatsDistributionWidget(parent)
        self.stats_widget.pack(fill=tk.X, padx=5, pady=5)

        # === Экипировка ===
        self.equipment_widget = EquipmentWidget(parent, is_template=True)
        self.equipment_widget.pack(fill=tk.X, padx=5, pady=5)

    def _create_loot_tab(self):
        """Вкладка Лут: золото и предметы"""
        scroll_frame = ScrollableFrame(self.editor_notebook)
        self.editor_notebook.add(scroll_frame, text="  Лут  ")

        parent = scroll_frame.get_frame()

        # Виджет лута (объединённый с золотом)
        self.loot_widget = LootWidget(parent)
        self.loot_widget.pack(fill=tk.X, padx=5, pady=5)

        # Подсказка
        hint_frame = ttk.Frame(parent)
        hint_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Label(hint_frame, text="Формула золота: (База + Уровень × Множитель) ± Разброс%",
                  font=('Arial', 9, 'italic'), foreground='gray').pack(anchor=tk.W)
        ttk.Label(hint_frame, text="Шанс предмета = Базовый% × Множитель качества",
                  font=('Arial', 9, 'italic'), foreground='gray').pack(anchor=tk.W)

    def _create_skills_tab(self):
        """Вкладка Умения"""
        scroll_frame = ScrollableFrame(self.editor_notebook)
        self.editor_notebook.add(scroll_frame, text="  Умения  ")

        parent = scroll_frame.get_frame()

        # Виджет умений
        self.skills_widget = SkillsWidget(parent)
        self.skills_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _on_type_changed(self, event=None):
        """Обработка смены типа NPC"""
        type_str = self.type_var.get()
        if ' - ' in type_str:
            npc_type = type_str.split(' - ')[0]
            self.sprite_selector.update_for_type(npc_type)

    def _apply_type_preset(self):
        """Применить пресет на основе типа NPC"""
        type_str = self.type_var.get()
        if not type_str or ' - ' not in type_str:
            messagebox.showwarning("Внимание", "Сначала выберите тип NPC")
            return

        npc_type = type_str.split(' - ')[0]

        # Применить пресет статов
        if npc_type in STATS_PRESETS:
            self.stats_widget.set(STATS_PRESETS[npc_type])

        # Применить пресет экипировки
        if npc_type in EQUIPMENT_PRESETS:
            self.equipment_widget.set(EQUIPMENT_PRESETS[npc_type])

        # Применить пресет лута
        if npc_type in LOOT_PRESETS:
            preset = LOOT_PRESETS[npc_type]
            self.loot_widget.set_gold(preset.get('gold', {}))
            loot_data = {
                'max_items': 3,
                'categories': {
                    cat_id: {
                        'enabled': cat_data.get('enabled', False),
                        'base_chance': cat_data.get('base_chance', 10),
                        'qualities': {'poor': True, 'common': True, 'uncommon': True, 'rare': False, 'epic': False}
                    }
                    for cat_id, cat_data in preset.get('categories', {}).items()
                }
            }
            self.loot_widget.set_loot(loot_data)

        # Применить пресет умений
        if npc_type in SKILLS_PRESETS:
            self.skills_widget.apply_preset(SKILLS_PRESETS[npc_type])

        messagebox.showinfo("Пресет применён", f"Применён пресет для типа '{npc_type}'")

    def refresh_list(self):
        """Обновление списка шаблонов"""
        def format_item(template):
            npc_type = template.get('type', 'unknown')
            type_name = dict(NPC_TYPES).get(npc_type, npc_type)
            rank = template.get('rank', 1)
            return f"[R{rank}] {template.get('name', 'Без имени')} ({type_name})"

        self.list_widget.refresh(self.templates, format_item)

    def _on_select(self, index):
        """Обработка выбора шаблона"""
        if 0 <= index < len(self.templates):
            self._load_template(self.templates[index])

    def _load_template(self, template):
        """Загрузка шаблона в редактор"""
        self.id_var.set(template.get('id', ''))
        self.name_var.set(template.get('name', ''))

        # Тип
        npc_type = template.get('type', 'guard')
        for type_id, type_name in NPC_TYPES:
            if type_id == npc_type:
                self.type_var.set(f"{type_id} - {type_name}")
                break

        self.rank_var.set(template.get('rank', 1))

        # Отношение
        relation = template.get('relationship', 'neutral')
        for rel_id, rel_name in RELATIONSHIPS:
            if rel_id == relation:
                self.relation_var.set(f"{rel_id} - {rel_name}")
                break

        # Спрайт
        self.sprite_selector.update_for_type(npc_type)
        sprite = template.get('sprite', '')
        if sprite:
            self.sprite_selector.set(sprite)

        # Статы
        self.stats_widget.set(template.get('stat_distribution', {}))

        # Экипировка
        self.equipment_widget.set(template.get('equipment', {}))

        # Золото и лут
        self.loot_widget.set_gold(template.get('gold', {}))
        self.loot_widget.set_loot(template.get('loot', {}))

        # Умения
        self.skills_widget.set(template.get('skills', {}))

    def add_template(self):
        """Добавление нового шаблона"""
        new_id = f'template_{len(self.templates) + 1}'
        existing_ids = [t.get('id', '') for t in self.templates]

        counter = 1
        while new_id in existing_ids:
            counter += 1
            new_id = f'template_{len(self.templates) + counter}'

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
            'equipment': {},
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

        self.templates.append(new_template)
        self.refresh_list()
        self.list_widget.select(len(self.templates) - 1)
        self._load_template(new_template)

        if self.on_change_callback:
            self.on_change_callback()

    def delete_template(self):
        """Удаление шаблона"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите шаблон для удаления")
            return

        template_name = self.templates[index].get('name', 'Без имени')
        if messagebox.askyesno("Подтверждение", f"Удалить шаблон '{template_name}'?"):
            del self.templates[index]
            self.refresh_list()

            if self.on_change_callback:
                self.on_change_callback()

    def duplicate_template(self):
        """Дублирование шаблона"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите шаблон для копирования")
            return

        original = self.templates[index]
        new_template = copy.deepcopy(original)
        new_template['id'] = f"{original['id']}_copy"
        new_template['name'] = f"{original['name']} (копия)"

        existing_ids = [t.get('id', '') for t in self.templates]
        counter = 1
        while new_template['id'] in existing_ids:
            counter += 1
            new_template['id'] = f"{original['id']}_copy{counter}"

        self.templates.append(new_template)
        self.refresh_list()

        if self.on_change_callback:
            self.on_change_callback()

    def apply_changes(self):
        """Применение изменений"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите шаблон для редактирования")
            return

        # Валидация статов
        if not self.stats_widget.is_valid():
            total = sum(self.stats_widget.stats_vars[k].get() for k in self.stats_widget.stats_vars)
            messagebox.showerror("Ошибка", f"Сумма статов должна быть 100%\nТекущая сумма: {total}%")
            return

        new_id = self.id_var.get().strip()
        if not new_id:
            messagebox.showerror("Ошибка", "ID не может быть пустым")
            return

        # Проверка уникальности ID
        for i, t in enumerate(self.templates):
            if i != index and t.get('id') == new_id:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                return

        template = self.templates[index]

        # Основная информация
        template['id'] = new_id
        template['name'] = self.name_var.get()

        type_str = self.type_var.get()
        if ' - ' in type_str:
            template['type'] = type_str.split(' - ')[0]

        template['rank'] = self.rank_var.get()

        rel_str = self.relation_var.get()
        if ' - ' in rel_str:
            template['relationship'] = rel_str.split(' - ')[0]

        template['sprite'] = self.sprite_selector.get()

        # Статы
        template['stat_distribution'] = self.stats_widget.get()

        # Экипировка
        template['equipment'] = self.equipment_widget.get()

        # Золото и лут
        template['gold'] = self.loot_widget.get_gold()
        template['loot'] = self.loot_widget.get_loot()

        # Умения
        template['skills'] = self.skills_widget.get()

        self.refresh_list()
        messagebox.showinfo("Готово", "Изменения применены")

        if self.on_change_callback:
            self.on_change_callback()
