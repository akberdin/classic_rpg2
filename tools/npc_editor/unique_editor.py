"""
Редактор уникальных NPC с вкладками: Общая, Лут, Умения
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy

from .config import (
    NPC_TYPES, RELATIONSHIPS, STATS, QUALITY_LEVELS,
    EQUIPMENT_SLOTS, SKILL_CATEGORIES, SKILLS
)
from .widgets import (
    SpriteSelector, StatsFixedWidget, EquipmentWidget,
    SkillsWidget, NPCListWidget, ScrollableFrame
)


class UniqueEditor(ttk.Frame):
    """Редактор уникальных NPC"""

    def __init__(self, parent, assets_path, unique_npcs, on_change_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.assets_path = assets_path
        self.unique_npcs = unique_npcs
        self.on_change_callback = on_change_callback

        self._create_ui()
        self.refresh_list()

    def _create_ui(self):
        """Создание интерфейса"""
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - список NPC
        self.list_widget = NPCListWidget(main_paned, "Уникальные NPC", self._on_select)
        main_paned.add(self.list_widget, weight=1)

        self.list_widget.add_btn.configure(command=self.add_unique)
        self.list_widget.delete_btn.configure(command=self.delete_unique)
        self.list_widget.copy_btn.configure(command=self.duplicate_unique)

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

    def _create_general_tab(self):
        """Вкладка Общая: основная информация, характеристики, экипировка"""
        scroll_frame = ScrollableFrame(self.editor_notebook)
        self.editor_notebook.add(scroll_frame, text="  Общая  ")

        parent = scroll_frame.get_frame()

        # === Основная информация ===
        info_frame = ttk.LabelFrame(parent, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Строка 1: ID и Имя
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="ID:", width=8).pack(side=tk.LEFT)
        self.id_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.id_var, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Имя:", width=6).pack(side=tk.LEFT, padx=(20, 0))
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var, width=25).pack(side=tk.LEFT, padx=5)

        # Строка 2: Описание
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=3)

        ttk.Label(row2, text="Описание:", width=10).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.desc_var, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Строка 3: Тип, Уровень, Отношение
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=3)

        ttk.Label(row3, text="Тип:", width=8).pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(row3, textvariable=self.type_var, width=18, state='readonly')
        type_combo['values'] = [f"{t[0]} - {t[1]}" for t in NPC_TYPES]
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)

        ttk.Label(row3, text="Уровень:", width=8).pack(side=tk.LEFT, padx=(20, 0))
        self.level_var = tk.IntVar(value=10)
        ttk.Spinbox(row3, from_=1, to=100, textvariable=self.level_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(row3, text="Отношение:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.relation_var = tk.StringVar(value="neutral")
        rel_combo = ttk.Combobox(row3, textvariable=self.relation_var, width=18, state='readonly')
        rel_combo['values'] = [f"{r[0]} - {r[1]}" for r in RELATIONSHIPS]
        rel_combo.pack(side=tk.LEFT, padx=5)

        # Строка 4: Позиция и диалог
        row4 = ttk.Frame(info_frame)
        row4.pack(fill=tk.X, pady=3)

        ttk.Label(row4, text="Позиция X:", width=10).pack(side=tk.LEFT)
        self.x_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=10000, textvariable=self.x_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(row4, text="Y:", width=2).pack(side=tk.LEFT, padx=(5, 0))
        self.y_var = tk.IntVar(value=100)
        ttk.Spinbox(row4, from_=0, to=10000, textvariable=self.y_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(row4, text="ID диалога:", width=10).pack(side=tk.LEFT, padx=(30, 0))
        self.dialog_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.dialog_var, width=25).pack(side=tk.LEFT, padx=5)

        # Строка 5: Спрайт
        row5 = ttk.Frame(info_frame)
        row5.pack(fill=tk.X, pady=3)

        ttk.Label(row5, text="Спрайт:", width=8).pack(side=tk.LEFT)
        self.sprite_selector = SpriteSelector(row5, self.assets_path)
        self.sprite_selector.pack(side=tk.LEFT, padx=5)

        # === Характеристики ===
        self.stats_widget = StatsFixedWidget(parent)
        self.stats_widget.pack(fill=tk.X, padx=5, pady=5)

        # === Экипировка ===
        self.equipment_widget = EquipmentWidget(parent, is_template=False)
        self.equipment_widget.pack(fill=tk.X, padx=5, pady=5)

    def _create_loot_tab(self):
        """Вкладка Лут: золото и гарантированные предметы"""
        scroll_frame = ScrollableFrame(self.editor_notebook)
        self.editor_notebook.add(scroll_frame, text="  Лут  ")

        parent = scroll_frame.get_frame()

        # === Золото ===
        gold_frame = ttk.LabelFrame(parent, text="Гарантированное золото", padding=10)
        gold_frame.pack(fill=tk.X, padx=5, pady=5)

        gold_row = ttk.Frame(gold_frame)
        gold_row.pack(fill=tk.X, pady=3)

        ttk.Label(gold_row, text="Количество золота:").pack(side=tk.LEFT)
        self.gold_var = tk.IntVar(value=100)
        ttk.Spinbox(gold_row, from_=0, to=1000000, textvariable=self.gold_var, width=10).pack(side=tk.LEFT, padx=5)

        # === Гарантированные предметы ===
        items_frame = ttk.LabelFrame(parent, text="Гарантированные предметы", padding=10)
        items_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(items_frame, text="Уникальные NPC могут иметь гарантированные предметы, настраиваемые вручную.",
                  font=('Arial', 9, 'italic'), foreground='gray').pack(anchor=tk.W)

        # Список предметов
        self.items_listbox = tk.Listbox(items_frame, height=5, font=('Arial', 10))
        self.items_listbox.pack(fill=tk.X, pady=5)

        items_btn_frame = ttk.Frame(items_frame)
        items_btn_frame.pack(fill=tk.X)

        ttk.Button(items_btn_frame, text="Добавить предмет", command=self._add_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(items_btn_frame, text="Удалить предмет", command=self._remove_item).pack(side=tk.LEFT, padx=2)

        self.guaranteed_items = []

    def _add_item(self):
        """Добавление гарантированного предмета"""
        dialog = ItemDialog(self.winfo_toplevel())
        if dialog.result:
            self.guaranteed_items.append(dialog.result)
            self._refresh_items_list()

    def _remove_item(self):
        """Удаление гарантированного предмета"""
        selection = self.items_listbox.curselection()
        if selection:
            del self.guaranteed_items[selection[0]]
            self._refresh_items_list()

    def _refresh_items_list(self):
        """Обновление списка предметов"""
        self.items_listbox.delete(0, tk.END)
        for item in self.guaranteed_items:
            self.items_listbox.insert(tk.END, f"{item.get('name', 'Предмет')} [{item.get('quality', 'common')}]")

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

    def refresh_list(self):
        """Обновление списка NPC"""
        def format_item(npc):
            npc_type = npc.get('type', 'unknown')
            type_name = dict(NPC_TYPES).get(npc_type, npc_type)
            level = npc.get('level', 1)
            return f"[Lv{level}] {npc.get('name', 'Без имени')} ({type_name})"

        self.list_widget.refresh(self.unique_npcs, format_item)

    def _on_select(self, index):
        """Обработка выбора NPC"""
        if 0 <= index < len(self.unique_npcs):
            self._load_unique(self.unique_npcs[index])

    def _load_unique(self, npc):
        """Загрузка NPC в редактор"""
        self.id_var.set(npc.get('id', ''))
        self.name_var.set(npc.get('name', ''))
        self.desc_var.set(npc.get('description', ''))

        # Тип
        npc_type = npc.get('type', 'guard')
        for type_id, type_name in NPC_TYPES:
            if type_id == npc_type:
                self.type_var.set(f"{type_id} - {type_name}")
                break

        self.level_var.set(npc.get('level', 10))

        # Отношение
        relation = npc.get('relationship', 'neutral')
        for rel_id, rel_name in RELATIONSHIPS:
            if rel_id == relation:
                self.relation_var.set(f"{rel_id} - {rel_name}")
                break

        # Позиция
        pos = npc.get('position', {'x': 100, 'y': 100})
        self.x_var.set(pos.get('x', 100))
        self.y_var.set(pos.get('y', 100))

        self.dialog_var.set(npc.get('dialog_id', ''))

        # Спрайт
        self.sprite_selector.update_for_type(npc_type)
        sprite = npc.get('sprite', '')
        if sprite:
            self.sprite_selector.set(sprite)

        # Золото
        self.gold_var.set(npc.get('gold', 100))

        # Статы
        self.stats_widget.set(npc.get('stats', {}))

        # Экипировка
        self.equipment_widget.set(npc.get('equipment', {}))

        # Умения
        self.skills_widget.set(npc.get('skills', {}))

        # Гарантированные предметы
        self.guaranteed_items = npc.get('guaranteed_items', []).copy()
        self._refresh_items_list()

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
            'stats': {stat_id: 10 for stat_id, _, _ in STATS},
            'gold': 100,
            'equipment': {},
            'skills': {},
            'guaranteed_items': [],
            'sprite': 'soldier/soldier1.png',
            'dialog_id': ''
        }

        self.unique_npcs.append(new_npc)
        self.refresh_list()
        self.list_widget.select(len(self.unique_npcs) - 1)
        self._load_unique(new_npc)

        if self.on_change_callback:
            self.on_change_callback()

    def delete_unique(self):
        """Удаление NPC"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите NPC для удаления")
            return

        npc_name = self.unique_npcs[index].get('name', 'Без имени')
        if messagebox.askyesno("Подтверждение", f"Удалить NPC '{npc_name}'?"):
            del self.unique_npcs[index]
            self.refresh_list()

            if self.on_change_callback:
                self.on_change_callback()

    def duplicate_unique(self):
        """Дублирование NPC"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите NPC для копирования")
            return

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
        self.refresh_list()

        if self.on_change_callback:
            self.on_change_callback()

    def apply_changes(self):
        """Применение изменений"""
        index = self.list_widget.get_selection()
        if index is None:
            messagebox.showwarning("Внимание", "Выберите NPC для редактирования")
            return

        new_id = self.id_var.get().strip()
        if not new_id:
            messagebox.showerror("Ошибка", "ID не может быть пустым")
            return

        # Проверка уникальности ID
        for i, n in enumerate(self.unique_npcs):
            if i != index and n.get('id') == new_id:
                messagebox.showerror("Ошибка", f"ID '{new_id}' уже существует")
                return

        npc = self.unique_npcs[index]

        # Основная информация
        npc['id'] = new_id
        npc['name'] = self.name_var.get()
        npc['description'] = self.desc_var.get()

        type_str = self.type_var.get()
        if ' - ' in type_str:
            npc['type'] = type_str.split(' - ')[0]

        npc['level'] = self.level_var.get()

        rel_str = self.relation_var.get()
        if ' - ' in rel_str:
            npc['relationship'] = rel_str.split(' - ')[0]

        npc['position'] = {
            'x': self.x_var.get(),
            'y': self.y_var.get()
        }

        npc['dialog_id'] = self.dialog_var.get()
        npc['sprite'] = self.sprite_selector.get()

        # Золото
        npc['gold'] = self.gold_var.get()

        # Статы
        npc['stats'] = self.stats_widget.get()

        # Экипировка
        npc['equipment'] = self.equipment_widget.get()

        # Умения
        npc['skills'] = self.skills_widget.get()

        # Гарантированные предметы
        npc['guaranteed_items'] = self.guaranteed_items.copy()

        self.refresh_list()
        messagebox.showinfo("Готово", "Изменения применены")

        if self.on_change_callback:
            self.on_change_callback()


class ItemDialog(tk.Toplevel):
    """Диалог добавления предмета"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Добавить предмет")
        self.geometry("350x200")
        self.resizable(False, False)
        self.result = None

        self.transient(parent)
        self.grab_set()

        self._create_ui()

        self.wait_window(self)

    def _create_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Название предмета
        ttk.Label(frame, text="Название:").pack(anchor=tk.W)
        self.name_var = tk.StringVar(value="Предмет")
        ttk.Entry(frame, textvariable=self.name_var, width=40).pack(fill=tk.X, pady=5)

        # Качество
        ttk.Label(frame, text="Качество:").pack(anchor=tk.W)
        self.quality_var = tk.StringVar(value="rare")
        qual_combo = ttk.Combobox(frame, textvariable=self.quality_var, width=37, state='readonly')
        qual_combo['values'] = [f"{q[0]} - {q[1]}" for q in QUALITY_LEVELS]
        qual_combo.pack(fill=tk.X, pady=5)

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=15)

        ttk.Button(btn_frame, text="Добавить", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self._on_cancel).pack(side=tk.RIGHT)

    def _on_ok(self):
        qual_str = self.quality_var.get()
        quality = qual_str.split(' - ')[0] if ' - ' in qual_str else qual_str

        self.result = {
            'name': self.name_var.get(),
            'quality': quality
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
