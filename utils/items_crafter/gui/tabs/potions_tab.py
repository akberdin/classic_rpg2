"""
Вкладка редактирования зелий
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox, LabeledCombobox, LabeledCheckbox, SpriteSelector
from ...models import PotionItemData, PotionEffect, ItemQuality


class PotionsTab(BaseEditorTab):
    """Вкладка для редактирования зелий"""

    def _create_editor_panel(self):
        """Создать панель редактора"""
        # Заголовок
        ttk.Label(
            self.editor_frame, text="Редактор зелий",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Основные поля
        main_frame = ttk.LabelFrame(self.editor_frame, text="Основные параметры")
        main_frame.pack(fill=tk.X, pady=5)

        self.id_entry = LabeledEntry(main_frame, "ID:")
        self.id_entry.pack(fill=tk.X, padx=5, pady=2)

        self.name_entry = LabeledEntry(main_frame, "Название:")
        self.name_entry.pack(fill=tk.X, padx=5, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(main_frame, "Отобр. имя:")
        self.display_name_entry.pack(fill=tk.X, padx=5, pady=2)

        self.description_entry = LabeledEntry(main_frame, "Описание:", width=50)
        self.description_entry.pack(fill=tk.X, padx=5, pady=2)

        # Качество
        qual_frame = ttk.Frame(main_frame)
        qual_frame.pack(fill=tk.X, padx=5, pady=2)

        qualities = list(ItemQuality.get_display_names().values())
        self.quality_combo = LabeledCombobox(qual_frame, "Качество:", qualities)
        self.quality_combo.pack(side=tk.LEFT)

        # Параметры
        params_frame = ttk.LabelFrame(self.editor_frame, text="Параметры")
        params_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.price_spin = LabeledSpinbox(row1, "Цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.max_stack_spin = LabeledSpinbox(row1, "Макс. стак:", from_=1, to=99)
        self.max_stack_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.cooldown_spin = LabeledSpinbox(row1, "Кулдаун:", from_=0, to=100)
        self.cooldown_spin.pack(side=tk.LEFT)

        row2 = ttk.Frame(params_frame)
        row2.pack(fill=tk.X, padx=5, pady=2)

        self.weight_spin = LabeledFloatSpinbox(row2, "Вес:", from_=0.01, to=10.0, increment=0.01)
        self.weight_spin.pack(side=tk.LEFT)

        # Спрайт
        sprite_frame = ttk.LabelFrame(self.editor_frame, text="Графика")
        sprite_frame.pack(fill=tk.X, pady=5)

        self.sprite_entry = SpriteSelector(sprite_frame)
        self.sprite_entry.pack(fill=tk.X, padx=5, pady=2)

        # Эффекты
        effects_frame = ttk.LabelFrame(self.editor_frame, text="Эффекты зелья")
        effects_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Список эффектов
        list_frame = ttk.Frame(effects_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.effects_tree = ttk.Treeview(
            list_frame, columns=("type", "value", "duration"),
            show="headings", height=4,
            yscrollcommand=scrollbar.set
        )
        self.effects_tree.heading("type", text="Тип эффекта")
        self.effects_tree.heading("value", text="Значение")
        self.effects_tree.heading("duration", text="Длительность")
        self.effects_tree.column("type", width=120)
        self.effects_tree.column("value", width=80)
        self.effects_tree.column("duration", width=80)
        self.effects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.effects_tree.yview)

        # Кнопки управления эффектами
        effect_btn_frame = ttk.Frame(effects_frame)
        effect_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(effect_btn_frame, text="Добавить", command=self._add_effect).pack(side=tk.LEFT, padx=2)
        ttk.Button(effect_btn_frame, text="Удалить", command=self._remove_effect).pack(side=tk.LEFT, padx=2)
        ttk.Button(effect_btn_frame, text="Изменить", command=self._edit_effect).pack(side=tk.LEFT, padx=2)

        self._effects: List[PotionEffect] = []

        # Привязка изменений
        for widget in [self.id_entry, self.display_name_entry, self.description_entry,
                       self.sprite_entry]:
            widget.bind_change(self._mark_modified)

        for widget in [self.price_spin, self.max_stack_spin, self.cooldown_spin, self.weight_spin]:
            widget.bind_change(self._mark_modified)

        self.quality_combo.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def _refresh_effects_tree(self):
        """Обновить дерево эффектов"""
        self.effects_tree.delete(*self.effects_tree.get_children())
        effect_names = {
            "heal": "Лечение",
            "mana": "Мана",
            "stamina": "Выносливость",
            "buff": "Усиление",
        }
        for effect in self._effects:
            type_name = effect_names.get(effect.effect_type, effect.effect_type)
            value_str = f"{effect.value}{'%' if effect.is_percent else ''}"
            duration_str = f"{effect.duration} ход." if effect.duration > 0 else "Мгновенно"
            self.effects_tree.insert("", tk.END, values=(type_name, value_str, duration_str))

    def _add_effect(self):
        """Добавить эффект"""
        dialog = EffectDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self._effects.append(dialog.result)
            self._refresh_effects_tree()
            self._mark_modified()

    def _remove_effect(self):
        """Удалить эффект"""
        selection = self.effects_tree.selection()
        if selection:
            index = self.effects_tree.index(selection[0])
            if 0 <= index < len(self._effects):
                del self._effects[index]
                self._refresh_effects_tree()
                self._mark_modified()

    def _edit_effect(self):
        """Редактировать эффект"""
        selection = self.effects_tree.selection()
        if selection:
            index = self.effects_tree.index(selection[0])
            if 0 <= index < len(self._effects):
                current = self._effects[index]
                dialog = EffectDialog(self, current)
                self.wait_window(dialog)
                if dialog.result:
                    self._effects[index] = dialog.result
                    self._refresh_effects_tree()
                    self._mark_modified()

    def get_items_list(self) -> List[Any]:
        return self.project.potions

    def get_item_display_info(self, item) -> tuple:
        return (item.item_id, item.name or item.display_name or item.item_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.potions:
            if item.item_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        base_id = "new_potion"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return PotionItemData(
            item_id=new_id,
            name="Новое зелье",
            display_name="Новое зелье",
            description="Описание зелья",
            quality="common",
            base_price=20,
            max_stack=10,
            weight=0.2,
            cooldown=0,
            effects=[PotionEffect(effect_type="heal", value=25)],
        )

    def add_item_to_project(self, item):
        self.project.potions.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.potions = [p for p in self.project.potions if p.item_id != item_id]

    def load_item_to_editor(self, item: PotionItemData):
        """Загрузить зелье в редактор"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Качество
        qualities = list(ItemQuality.get_display_names().keys())
        qual_names = list(ItemQuality.get_display_names().values())
        if item.quality in qualities:
            self.quality_combo.set(qual_names[qualities.index(item.quality)])

        self.price_spin.set(item.base_price)
        self.max_stack_spin.set(item.max_stack)
        self.cooldown_spin.set(item.cooldown)
        self.weight_spin.set(item.weight)
        self.sprite_entry.set(item.sprite or "")

        # Эффекты
        self._effects = item.effects.copy() if item.effects else []
        self._refresh_effects_tree()

    def save_item_from_editor(self):
        """Сохранить зелье из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.item_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Качество
        qual_names = list(ItemQuality.get_display_names().values())
        qualities = list(ItemQuality.get_display_names().keys())
        qual_name = self.quality_combo.get()
        if qual_name in qual_names:
            item.quality = qualities[qual_names.index(qual_name)]

        item.base_price = self.price_spin.get()
        item.max_stack = self.max_stack_spin.get()
        item.cooldown = self.cooldown_spin.get()
        item.weight = self.weight_spin.get()
        item.sprite = self.sprite_entry.get()
        item.effects = self._effects.copy()

        self.refresh_list()


class EffectDialog(tk.Toplevel):
    """Диалог добавления/редактирования эффекта зелья"""

    def __init__(self, parent, current_effect: Optional[PotionEffect] = None):
        super().__init__(parent)
        self.title("Эффект зелья")
        self.geometry("350x200")
        self.transient(parent)
        self.grab_set()

        self.result: Optional[PotionEffect] = None

        # Тип эффекта
        ttk.Label(self, text="Тип эффекта:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.type_var = tk.StringVar()
        effect_types = ["Лечение", "Мана", "Выносливость", "Усиление"]
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, values=effect_types, state="readonly")
        self.type_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        self.type_combo.current(0)
        self._type_map = {"Лечение": "heal", "Мана": "mana", "Выносливость": "stamina", "Усиление": "buff"}
        self._type_map_rev = {v: k for k, v in self._type_map.items()}

        # Значение
        ttk.Label(self, text="Значение:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.value_var = tk.IntVar(value=25)
        self.value_spin = ttk.Spinbox(self, textvariable=self.value_var, from_=1, to=9999, width=10)
        self.value_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Проценты
        self.is_percent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="В процентах", variable=self.is_percent_var).grid(
            row=1, column=2, padx=10, pady=10
        )

        # Длительность
        ttk.Label(self, text="Длительность (ходы):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.duration_var = tk.IntVar(value=0)
        self.duration_spin = ttk.Spinbox(self, textvariable=self.duration_var, from_=0, to=100, width=10)
        self.duration_spin.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        ttk.Label(self, text="(0 = мгновенно)").grid(row=2, column=2, padx=10, pady=10)

        # Заполняем текущими значениями
        if current_effect:
            if current_effect.effect_type in self._type_map_rev:
                self.type_combo.set(self._type_map_rev[current_effect.effect_type])
            self.value_var.set(current_effect.value)
            self.is_percent_var.set(current_effect.is_percent)
            self.duration_var.set(current_effect.duration)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _ok(self):
        type_name = self.type_var.get()
        self.result = PotionEffect(
            effect_type=self._type_map.get(type_name, "heal"),
            value=self.value_var.get(),
            duration=self.duration_var.get(),
            is_percent=self.is_percent_var.get(),
        )
        self.destroy()
