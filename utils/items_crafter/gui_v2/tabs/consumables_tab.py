"""
Вкладка редактора расходников (зелья, еда, свитки) v2.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple, Any

from ..base_editor import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox,
    LabeledCombobox, LabeledCheckbox, LabeledTextarea
)
from ...core.config_manager import ConfigManager
from ...core.item_models import ConsumableItem, ConsumableEffect
from ...core.enums import ItemQuality, EffectType, StatType


class EffectsEditor(ttk.Frame):
    """Редактор эффектов расходника"""

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_change = on_change
        self._effects: List[dict] = []
        self._create_widgets()

    def _create_widgets(self):
        # Таблица эффектов
        columns = ("type", "value", "duration", "percent")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=4)
        self.tree.heading("type", text="Тип эффекта")
        self.tree.heading("value", text="Значение")
        self.tree.heading("duration", text="Длительность")
        self.tree.heading("percent", text="%")
        self.tree.column("type", width=150)
        self.tree.column("value", width=80)
        self.tree.column("duration", width=80)
        self.tree.column("percent", width=40)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self._add_effect, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self._edit_effect, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._remove_effect, width=10).pack(side=tk.LEFT, padx=2)

    def get_effects(self) -> List[dict]:
        return self._effects.copy()

    def set_effects(self, effects: List[dict]):
        self._effects = effects.copy()
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        effect_names = EffectType.get_display_names()
        for effect in self._effects:
            effect_type = effect.get("effect_type", "")
            value = effect.get("value", 0)
            duration = effect.get("duration", 0)
            is_percent = "Да" if effect.get("is_percent", False) else ""
            type_name = effect_names.get(effect_type, effect_type)
            self.tree.insert("", tk.END, values=(type_name, value, duration, is_percent))

    def _add_effect(self):
        dialog = EffectDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self._effects.append(dialog.result)
            self._refresh_tree()
            if self.on_change:
                self.on_change()

    def _edit_effect(self):
        selection = self.tree.selection()
        if not selection:
            return
        idx = self.tree.index(selection[0])
        if idx < len(self._effects):
            dialog = EffectDialog(self, self._effects[idx])
            self.wait_window(dialog)
            if dialog.result:
                self._effects[idx] = dialog.result
                self._refresh_tree()
                if self.on_change:
                    self.on_change()

    def _remove_effect(self):
        selection = self.tree.selection()
        if not selection:
            return
        idx = self.tree.index(selection[0])
        if idx < len(self._effects):
            del self._effects[idx]
            self._refresh_tree()
            if self.on_change:
                self.on_change()


class EffectDialog(tk.Toplevel):
    """Диалог добавления/редактирования эффекта"""

    def __init__(self, parent, initial=None):
        super().__init__(parent)
        self.title("Эффект")
        self.resizable(False, False)
        self.result = None
        self._create_widgets(initial)
        self.transient(parent)
        self.grab_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def _create_widgets(self, initial):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Тип эффекта
        ttk.Label(frame, text="Тип эффекта:").grid(row=0, column=0, sticky="e", pady=5)
        self.type_var = tk.StringVar()
        effect_names = list(EffectType.get_display_names().values())
        self.type_combo = ttk.Combobox(frame, textvariable=self.type_var, values=effect_names, state="readonly", width=25)
        self.type_combo.grid(row=0, column=1, pady=5, padx=(5, 0))
        self._effect_map = {v: k for k, v in EffectType.get_display_names().items()}

        # Значение
        ttk.Label(frame, text="Значение:").grid(row=1, column=0, sticky="e", pady=5)
        self.value_var = tk.IntVar(value=10)
        self.value_spin = ttk.Spinbox(frame, from_=0, to=9999, textvariable=self.value_var, width=10)
        self.value_spin.grid(row=1, column=1, sticky="w", pady=5, padx=(5, 0))

        # Длительность
        ttk.Label(frame, text="Длительность (ходы):").grid(row=2, column=0, sticky="e", pady=5)
        self.duration_var = tk.IntVar(value=0)
        self.duration_spin = ttk.Spinbox(frame, from_=0, to=999, textvariable=self.duration_var, width=10)
        self.duration_spin.grid(row=2, column=1, sticky="w", pady=5, padx=(5, 0))

        # Процент
        self.percent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Процентное значение", variable=self.percent_var).grid(row=3, column=0, columnspan=2, pady=5)

        # Целевая характеристика (для BUFF_STAT)
        ttk.Label(frame, text="Целевая характеристика:").grid(row=4, column=0, sticky="e", pady=5)
        self.target_var = tk.StringVar()
        stat_names = list(StatType.get_display_names().values())
        self.target_combo = ttk.Combobox(frame, textvariable=self.target_var, values=stat_names, state="readonly", width=20)
        self.target_combo.grid(row=4, column=1, pady=5, padx=(5, 0))
        self._stat_map = {v: k for k, v in StatType.get_display_names().items()}

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="OK", command=self._on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # Начальные значения
        if initial:
            effect_type = initial.get("effect_type", "")
            type_name = EffectType.get_display_names().get(effect_type, "")
            if type_name:
                self.type_combo.set(type_name)
            self.value_var.set(initial.get("value", 10))
            self.duration_var.set(initial.get("duration", 0))
            self.percent_var.set(initial.get("is_percent", False))
            target_stat = initial.get("target_stat", "")
            if target_stat:
                target_name = StatType.get_display_names().get(target_stat, "")
                if target_name:
                    self.target_combo.set(target_name)
        elif effect_names:
            self.type_combo.current(0)

    def _on_ok(self):
        type_name = self.type_var.get()
        effect_type = self._effect_map.get(type_name, "")

        target_name = self.target_var.get()
        target_stat = self._stat_map.get(target_name)

        self.result = {
            "effect_type": effect_type,
            "value": self.value_var.get(),
            "duration": self.duration_var.get(),
            "is_percent": self.percent_var.get(),
            "target_stat": target_stat,
        }
        self.destroy()


class ConsumablesTab(BaseEditorTab):
    """Вкладка редактора расходников"""

    def get_item_type_name(self) -> str:
        return "consumable"

    def get_items_list(self) -> List[Tuple[str, str]]:
        items = []
        for consumable in self.config_manager.project.consumables:
            items.append((consumable.item_id, consumable.display_name or consumable.name))
        return items

    def find_item_by_id(self, item_id: str) -> Optional[ConsumableItem]:
        for consumable in self.config_manager.project.consumables:
            if consumable.item_id == item_id:
                return consumable
        return None

    def create_new_item(self) -> ConsumableItem:
        base_id = "new_consumable"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return ConsumableItem(
            item_id=new_id,
            name="Новый расходник",
            display_name="Новый расходник",
            description="",
            quality=ItemQuality.COMMON.value,
            effects=[],
            cooldown=0,
            charges=1,
            base_price=5,
            max_stack=20,
        )

    def add_item_to_project(self, item: ConsumableItem):
        self.config_manager.project.consumables.append(item)

    def remove_item_from_project(self, item_id: str):
        self.config_manager.project.consumables = [
            c for c in self.config_manager.project.consumables if c.item_id != item_id
        ]

    def _create_item_from_dict(self, data: dict) -> Optional[ConsumableItem]:
        try:
            return ConsumableItem.from_dict(data)
        except:
            return None

    def _create_editor(self, parent: ttk.Frame):
        """Создать форму редактора расходника"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.editor_frame = ttk.Frame(canvas)

        self.editor_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Основная информация
        info_frame = ttk.LabelFrame(self.editor_frame, text="Основная информация", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.id_entry = LabeledEntry(info_frame, "ID:")
        self.id_entry.pack(fill=tk.X, pady=2)
        self.id_entry.bind_change(self._mark_modified)

        self.name_entry = LabeledEntry(info_frame, "Имя:")
        self.name_entry.pack(fill=tk.X, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(info_frame, "Отображаемое имя:")
        self.display_name_entry.pack(fill=tk.X, pady=2)
        self.display_name_entry.bind_change(self._mark_modified)

        self.description_text = LabeledTextarea(info_frame, "Описание:", height=3)
        self.description_text.pack(fill=tk.X, pady=2)
        self.description_text.bind_change(self._mark_modified)

        # Качество
        quality_frame = ttk.LabelFrame(self.editor_frame, text="Качество", padding=10)
        quality_frame.pack(fill=tk.X, padx=5, pady=5)

        quality_names = ItemQuality.get_display_names()
        self.quality_combo = LabeledCombobox(quality_frame, "Качество:", values=list(quality_names.values()))
        self.quality_combo.pack(fill=tk.X, pady=2)
        self.quality_combo.bind_change(self._mark_modified)
        self._quality_map = {v: k for k, v in quality_names.items()}
        self._quality_map_rev = quality_names

        # Эффекты
        effects_frame = ttk.LabelFrame(self.editor_frame, text="Эффекты", padding=10)
        effects_frame.pack(fill=tk.X, padx=5, pady=5)

        self.effects_editor = EffectsEditor(effects_frame, on_change=self._mark_modified)
        self.effects_editor.pack(fill=tk.BOTH, expand=True)

        # Параметры использования
        usage_frame = ttk.LabelFrame(self.editor_frame, text="Параметры использования", padding=10)
        usage_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cooldown_spin = LabeledSpinbox(usage_frame, "Перезарядка (ходы):", from_=0, to=999)
        self.cooldown_spin.pack(fill=tk.X, pady=2)
        self.cooldown_spin.bind_change(self._mark_modified)

        self.charges_spin = LabeledSpinbox(usage_frame, "Заряды:", from_=1, to=99)
        self.charges_spin.pack(fill=tk.X, pady=2)
        self.charges_spin.bind_change(self._mark_modified)

        # Экономика
        economy_frame = ttk.LabelFrame(self.editor_frame, text="Экономика", padding=10)
        economy_frame.pack(fill=tk.X, padx=5, pady=5)

        self.price_spin = LabeledSpinbox(economy_frame, "Базовая цена:", from_=0, to=99999)
        self.price_spin.pack(fill=tk.X, pady=2)
        self.price_spin.bind_change(self._mark_modified)

        self.weight_spin = LabeledFloatSpinbox(economy_frame, "Вес:", from_=0.0, to=999.9)
        self.weight_spin.pack(fill=tk.X, pady=2)
        self.weight_spin.bind_change(self._mark_modified)

        self.max_stack_spin = LabeledSpinbox(economy_frame, "Макс. стак:", from_=1, to=9999)
        self.max_stack_spin.pack(fill=tk.X, pady=2)
        self.max_stack_spin.bind_change(self._mark_modified)

        # Связанный рецепт (управляется во вкладке Рецепты)
        recipe_frame = ttk.LabelFrame(self.editor_frame, text="Связанный рецепт", padding=10)
        recipe_frame.pack(fill=tk.X, padx=5, pady=5)

        self.recipe_label = ttk.Label(recipe_frame, text="Рецепт: (не задан)")
        self.recipe_label.pack(fill=tk.X, pady=2)

        ttk.Label(recipe_frame, text="(Связь создаётся во вкладке Рецепты)",
                 foreground="gray").pack(anchor="w")

        # Визуал
        visual_frame = ttk.LabelFrame(self.editor_frame, text="Визуал", padding=10)
        visual_frame.pack(fill=tk.X, padx=5, pady=5)

        self.icon_entry = LabeledEntry(visual_frame, "Иконка:")
        self.icon_entry.pack(fill=tk.X, pady=2)
        self.icon_entry.bind_change(self._mark_modified)

        self.sprite_entry = LabeledEntry(visual_frame, "Спрайт:")
        self.sprite_entry.pack(fill=tk.X, pady=2)
        self.sprite_entry.bind_change(self._mark_modified)

    def _on_name_change(self):
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(name.lower().replace(" ", "_"))
        if name and not self.display_name_entry.get():
            self.display_name_entry.set(name)
        self._mark_modified()

    def load_item_to_editor(self, item: ConsumableItem):
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_text.set(item.description)

        quality_display = self._quality_map_rev.get(item.quality, "")
        self.quality_combo.set(quality_display)

        effects = [e.to_dict() for e in item.effects]
        self.effects_editor.set_effects(effects)

        self.cooldown_spin.set(item.cooldown)
        self.charges_spin.set(item.charges)

        self.price_spin.set(item.base_price)
        self.weight_spin.set(item.weight)
        self.max_stack_spin.set(item.max_stack)

        if item.recipe_id:
            recipe = self.config_manager.project.get_recipe_by_id(item.recipe_id)
            if recipe:
                self.recipe_label.config(text=f"Рецепт: {recipe.display_name} [{recipe.recipe_id}]")
            else:
                self.recipe_label.config(text=f"Рецепт: {item.recipe_id} (не найден)")
        else:
            self.recipe_label.config(text="Рецепт: (не задан)")

        self.icon_entry.set(item.icon)
        self.sprite_entry.set(item.sprite)

    def save_item_from_editor(self) -> bool:
        if not self._current_item_id:
            return False

        item = self.find_item_by_id(self._current_item_id)
        if not item:
            return False

        new_id = self.id_entry.get().strip()
        if not new_id:
            return False

        if new_id != self._current_item_id:
            existing = self.find_item_by_id(new_id)
            if existing:
                return False

        item.item_id = new_id
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_text.get()

        quality_display = self.quality_combo.get()
        item.quality = self._quality_map.get(quality_display, ItemQuality.COMMON.value)

        effects_data = self.effects_editor.get_effects()
        item.effects = [ConsumableEffect.from_dict(e) for e in effects_data]

        item.cooldown = self.cooldown_spin.get()
        item.charges = self.charges_spin.get()

        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()
        item.max_stack = self.max_stack_spin.get()

        item.icon = self.icon_entry.get()
        item.sprite = self.sprite_entry.get()

        if new_id != self._current_item_id:
            self._current_item_id = new_id
            self.refresh_list()
            self.list_panel.select_item(new_id)

        return True
