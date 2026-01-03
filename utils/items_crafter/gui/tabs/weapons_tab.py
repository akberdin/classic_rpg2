"""
Вкладка редактирования оружия
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox, LabeledCombobox,
    LabeledCheckbox, QualityParametersEditor
)
from ...models import WeaponItemData, WeaponType, ItemQuality


class WeaponsTab(BaseEditorTab):
    """Вкладка для редактирования оружия"""

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
            scroll_frame, text="Редактор оружия",
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

        # Тип оружия и качество
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=2)

        weapon_types = list(WeaponType.get_display_names().values())
        self.weapon_type_combo = LabeledCombobox(type_frame, "Тип оружия:", weapon_types)
        self.weapon_type_combo.pack(side=tk.LEFT, padx=(0, 20))

        qualities = list(ItemQuality.get_display_names().values())
        self.quality_combo = LabeledCombobox(type_frame, "Качество:", qualities)
        self.quality_combo.pack(side=tk.LEFT)

        # Параметры оружия
        params_frame = ttk.LabelFrame(scroll_frame, text="Параметры оружия")
        params_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.tactical_range_spin = LabeledSpinbox(row1, "Такт. радиус:", from_=1, to=10)
        self.tactical_range_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.price_spin = LabeledSpinbox(row1, "Базовая цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.weight_spin = LabeledFloatSpinbox(row1, "Вес:", from_=0.1, to=50.0, increment=0.1)
        self.weight_spin.pack(side=tk.LEFT)

        row2 = ttk.Frame(params_frame)
        row2.pack(fill=tk.X, padx=5, pady=2)

        self.two_handed_check = LabeledCheckbox(row2, "Двуручное")
        self.two_handed_check.pack(side=tk.LEFT)

        # Спрайт
        sprite_frame = ttk.LabelFrame(scroll_frame, text="Графика")
        sprite_frame.pack(fill=tk.X, pady=5, padx=5)

        self.sprite_entry = LabeledEntry(sprite_frame, "Спрайт:")
        self.sprite_entry.pack(fill=tk.X, padx=5, pady=2)

        # Параметры по качеству
        self.quality_params = QualityParametersEditor(
            scroll_frame, title="Параметры по уровням качества"
        )
        self.quality_params.pack(fill=tk.X, pady=5, padx=5)

        # Привязка изменений
        for widget in [self.id_entry, self.display_name_entry, self.description_entry,
                       self.sprite_entry]:
            widget.bind_change(self._mark_modified)

        for widget in [self.tactical_range_spin, self.price_spin, self.weight_spin]:
            widget.bind_change(self._mark_modified)

        self.weapon_type_combo.bind_change(self._on_weapon_type_change)
        self.quality_combo.bind_change(self._mark_modified)
        self.two_handed_check.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def _on_weapon_type_change(self):
        """При изменении типа оружия обновляем радиус"""
        if self._is_loading:
            return

        type_names = list(WeaponType.get_display_names().values())
        type_keys = list(WeaponType.get_display_names().keys())
        current_name = self.weapon_type_combo.get()

        if current_name in type_names:
            type_key = type_keys[type_names.index(current_name)]
            tactical_range = WeaponType.get_tactical_ranges().get(type_key, 1)
            self.tactical_range_spin.set(tactical_range)

        self._mark_modified()

    def get_items_list(self) -> List[Any]:
        return self.project.weapons

    def get_item_display_info(self, item) -> tuple:
        return (item.item_id, item.name or item.display_name or item.item_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.weapons:
            if item.item_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        # Генерируем уникальный ID
        base_id = "new_weapon"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return WeaponItemData(
            item_id=new_id,
            name="Новое оружие",
            display_name="Новое оружие",
            description="Описание оружия",
            weapon_type="sword",
            quality="common",
            tactical_range=1,
            base_price=50,
            weight=2.0,
            two_handed=False,
        )

    def add_item_to_project(self, item):
        self.project.weapons.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.weapons = [w for w in self.project.weapons if w.item_id != item_id]

    def load_item_to_editor(self, item: WeaponItemData):
        """Загрузить оружие в редактор"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Тип оружия
        type_keys = list(WeaponType.get_display_names().keys())
        type_names = list(WeaponType.get_display_names().values())
        if item.weapon_type in type_keys:
            self.weapon_type_combo.set(type_names[type_keys.index(item.weapon_type)])

        # Качество
        qualities = list(ItemQuality.get_display_names().keys())
        qual_names = list(ItemQuality.get_display_names().values())
        if item.quality in qualities:
            self.quality_combo.set(qual_names[qualities.index(item.quality)])

        self.tactical_range_spin.set(item.tactical_range)
        self.price_spin.set(item.base_price)
        self.weight_spin.set(item.weight)
        self.two_handed_check.set(item.two_handed)
        self.sprite_entry.set(item.sprite or "")

        # Параметры по качеству
        if item.parameters_by_quality:
            params = {
                q: p.to_dict() if hasattr(p, 'to_dict') else p
                for q, p in item.parameters_by_quality.items()
            }
            self.quality_params.set_parameters(params)

    def save_item_from_editor(self):
        """Сохранить оружие из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.item_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Тип оружия
        type_names = list(WeaponType.get_display_names().values())
        type_keys = list(WeaponType.get_display_names().keys())
        type_name = self.weapon_type_combo.get()
        if type_name in type_names:
            item.weapon_type = type_keys[type_names.index(type_name)]

        # Качество
        qual_names = list(ItemQuality.get_display_names().values())
        qualities = list(ItemQuality.get_display_names().keys())
        qual_name = self.quality_combo.get()
        if qual_name in qual_names:
            item.quality = qualities[qual_names.index(qual_name)]

        item.tactical_range = self.tactical_range_spin.get()
        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()
        item.two_handed = self.two_handed_check.get()
        item.sprite = self.sprite_entry.get()

        self.refresh_list()
