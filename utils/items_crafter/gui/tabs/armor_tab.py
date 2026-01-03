"""
Вкладка редактирования брони
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox, LabeledCombobox,
    QualityParametersEditor, SpriteSelector
)
from ...models import ArmorItemData, ArmorType, EquipmentSlot


class ArmorTab(BaseEditorTab):
    """Вкладка для редактирования брони"""

    def _create_editor_panel(self):
        """Создать панель редактора"""
        # Создаём прокручиваемую область
        canvas = tk.Canvas(self.editor_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.editor_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Заголовок
        ttk.Label(
            scroll_frame, text="Редактор брони",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Основные поля
        main_frame = ttk.LabelFrame(scroll_frame, text="Основные параметры")
        main_frame.pack(fill=tk.X, pady=5, padx=5)

        self.id_entry = LabeledEntry(main_frame, "ID:")
        self.id_entry.pack(fill=tk.X, padx=5, pady=2)

        self.name_entry = LabeledEntry(main_frame, "Название:")
        self.name_entry.pack(fill=tk.X, padx=5, pady=2)
        self.name_entry.bind_change(self._on_name_change)

        self.display_name_entry = LabeledEntry(main_frame, "Отобр. имя:")
        self.display_name_entry.pack(fill=tk.X, padx=5, pady=2)

        self.description_entry = LabeledEntry(main_frame, "Описание:", width=50)
        self.description_entry.pack(fill=tk.X, padx=5, pady=2)

        # Тип брони и слот
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=2)

        armor_types = list(ArmorType.get_display_names().values())
        self.armor_type_combo = LabeledCombobox(type_frame, "Тип брони:", armor_types)
        self.armor_type_combo.pack(side=tk.LEFT, padx=(0, 20))

        # Слоты для брони
        armor_slots = {
            "head": "Голова",
            "chest": "Грудь",
            "hands": "Руки",
            "feet": "Ноги",
            "belt": "Пояс",
            "backpack": "Рюкзак",
        }
        slot_names = list(armor_slots.values())
        self.slot_combo = LabeledCombobox(type_frame, "Слот:", slot_names)
        self.slot_combo.pack(side=tk.LEFT)
        self._armor_slots = armor_slots

        # Параметры брони
        params_frame = ttk.LabelFrame(scroll_frame, text="Параметры брони")
        params_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.price_spin = LabeledSpinbox(row1, "Базовая цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.weight_spin = LabeledFloatSpinbox(row1, "Вес:", from_=0.1, to=50.0, increment=0.1)
        self.weight_spin.pack(side=tk.LEFT)

        # Спрайт
        sprite_frame = ttk.LabelFrame(scroll_frame, text="Графика")
        sprite_frame.pack(fill=tk.X, pady=5, padx=5)

        self.sprite_entry = SpriteSelector(sprite_frame)
        self.sprite_entry.pack(fill=tk.X, padx=5, pady=2)

        # Параметры по качеству
        self.quality_params = QualityParametersEditor(
            scroll_frame, title="Параметры защиты по уровням качества"
        )
        self.quality_params.pack(fill=tk.X, pady=5, padx=5)

        # Привязка изменений
        for widget in [self.id_entry, self.display_name_entry, self.description_entry,
                       self.sprite_entry]:
            widget.bind_change(self._mark_modified)

        for widget in [self.price_spin, self.weight_spin]:
            widget.bind_change(self._mark_modified)

        self.armor_type_combo.bind_change(self._mark_modified)
        self.slot_combo.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def get_items_list(self) -> List[Any]:
        return self.project.armors

    def get_item_display_info(self, item) -> tuple:
        return (item.item_id, item.name or item.display_name or item.item_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.armors:
            if item.item_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        base_id = "new_armor"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return ArmorItemData(
            item_id=new_id,
            name="Новая броня",
            display_name="Новая броня",
            description="Описание брони",
            armor_type="light",
            slot="chest",
            base_price=60,
            weight=3.0,
        )

    def add_item_to_project(self, item):
        self.project.armors.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.armors = [a for a in self.project.armors if a.item_id != item_id]

    def load_item_to_editor(self, item: ArmorItemData):
        """Загрузить броню в редактор"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Тип брони
        type_keys = list(ArmorType.get_display_names().keys())
        type_names = list(ArmorType.get_display_names().values())
        if item.armor_type in type_keys:
            self.armor_type_combo.set(type_names[type_keys.index(item.armor_type)])

        # Слот
        slot_keys = list(self._armor_slots.keys())
        slot_names = list(self._armor_slots.values())
        if item.slot in slot_keys:
            self.slot_combo.set(slot_names[slot_keys.index(item.slot)])

        self.price_spin.set(item.base_price)
        self.weight_spin.set(item.weight)
        self.sprite_entry.set(item.sprite or "")

        # Параметры по качеству
        if item.parameters_by_quality:
            params = {
                q: p.to_dict() if hasattr(p, 'to_dict') else p
                for q, p in item.parameters_by_quality.items()
            }
            self.quality_params.set_parameters(params)

    def save_item_from_editor(self):
        """Сохранить броню из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.item_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Тип брони
        type_names = list(ArmorType.get_display_names().values())
        type_keys = list(ArmorType.get_display_names().keys())
        type_name = self.armor_type_combo.get()
        if type_name in type_names:
            item.armor_type = type_keys[type_names.index(type_name)]

        # Слот
        slot_names = list(self._armor_slots.values())
        slot_keys = list(self._armor_slots.keys())
        slot_name = self.slot_combo.get()
        if slot_name in slot_names:
            item.slot = slot_keys[slot_names.index(slot_name)]

        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()
        item.sprite = self.sprite_entry.get()

        self.refresh_list()
