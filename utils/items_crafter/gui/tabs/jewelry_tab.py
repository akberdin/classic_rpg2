"""
Вкладка редактирования украшений
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Any

from .base_tab import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox, LabeledCombobox,
    QualityParametersEditor
)
from ...models import JewelryItemData, JewelryType, ItemQuality


class JewelryTab(BaseEditorTab):
    """Вкладка для редактирования украшений"""

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
            scroll_frame, text="Редактор украшений",
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

        # Тип украшения
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=2)

        jewelry_types = list(JewelryType.get_display_names().values())
        self.jewelry_type_combo = LabeledCombobox(type_frame, "Тип:", jewelry_types)
        self.jewelry_type_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.jewelry_type_combo.bind_change(self._on_jewelry_type_change)

        qualities = list(ItemQuality.get_display_names().values())
        self.quality_combo = LabeledCombobox(type_frame, "Качество:", qualities)
        self.quality_combo.pack(side=tk.LEFT)

        # Материал и камень
        material_frame = ttk.Frame(main_frame)
        material_frame.pack(fill=tk.X, padx=5, pady=2)

        materials = ["copper", "silver", "gold", "mithril"]
        material_names = ["Медь", "Серебро", "Золото", "Мифрил"]
        self.material_combo = LabeledCombobox(material_frame, "Материал:", material_names)
        self.material_combo.pack(side=tk.LEFT, padx=(0, 20))
        self._materials = dict(zip(material_names, materials))

        gems = ["", "amethyst", "ruby", "sapphire", "emerald", "topaz", "diamond"]
        gem_names = ["Без камня", "Аметист", "Рубин", "Сапфир", "Изумруд", "Топаз", "Алмаз"]
        self.gem_combo = LabeledCombobox(material_frame, "Камень:", gem_names)
        self.gem_combo.pack(side=tk.LEFT)
        self._gems = dict(zip(gem_names, gems))

        # Параметры
        params_frame = ttk.LabelFrame(scroll_frame, text="Параметры")
        params_frame.pack(fill=tk.X, pady=5, padx=5)

        row1 = ttk.Frame(params_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)

        self.price_spin = LabeledSpinbox(row1, "Базовая цена:", from_=1, to=99999)
        self.price_spin.pack(side=tk.LEFT, padx=(0, 20))

        self.weight_spin = LabeledFloatSpinbox(row1, "Вес:", from_=0.01, to=10.0, increment=0.01)
        self.weight_spin.pack(side=tk.LEFT)

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

        for widget in [self.price_spin, self.weight_spin]:
            widget.bind_change(self._mark_modified)

        self.quality_combo.bind_change(self._mark_modified)
        self.material_combo.bind_change(self._mark_modified)
        self.gem_combo.bind_change(self._mark_modified)

    def _on_name_change(self):
        """При изменении названия генерируем ID"""
        if self._is_loading:
            return
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            self.id_entry.set(self._generate_id(name))
        self._mark_modified()

    def _on_jewelry_type_change(self):
        """При изменении типа обновляем слот"""
        self._mark_modified()

    def get_items_list(self) -> List[Any]:
        return self.project.jewelry

    def get_item_display_info(self, item) -> tuple:
        return (item.item_id, item.name or item.display_name or item.item_id)

    def find_item_by_id(self, item_id: str) -> Optional[Any]:
        for item in self.project.jewelry:
            if item.item_id == item_id:
                return item
        return None

    def create_new_item(self) -> Any:
        base_id = "new_jewelry"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return JewelryItemData(
            item_id=new_id,
            name="Новое украшение",
            display_name="Новое украшение",
            description="Описание украшения",
            jewelry_type="ring",
            slot="ring_1",
            material="copper",
            quality="common",
            base_price=80,
            weight=0.1,
        )

    def add_item_to_project(self, item):
        self.project.jewelry.append(item)

    def remove_item_from_project(self, item_id: str):
        self.project.jewelry = [j for j in self.project.jewelry if j.item_id != item_id]

    def load_item_to_editor(self, item: JewelryItemData):
        """Загрузить украшение в редактор"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_entry.set(item.description)

        # Тип украшения
        type_keys = list(JewelryType.get_display_names().keys())
        type_names = list(JewelryType.get_display_names().values())
        if item.jewelry_type in type_keys:
            self.jewelry_type_combo.set(type_names[type_keys.index(item.jewelry_type)])

        # Качество
        qualities = list(ItemQuality.get_display_names().keys())
        qual_names = list(ItemQuality.get_display_names().values())
        if item.quality in qualities:
            self.quality_combo.set(qual_names[qualities.index(item.quality)])

        # Материал
        materials_rev = {v: k for k, v in self._materials.items()}
        if item.material in materials_rev:
            self.material_combo.set(materials_rev[item.material])

        # Камень
        gems_rev = {v: k for k, v in self._gems.items()}
        if item.gem in gems_rev:
            self.gem_combo.set(gems_rev[item.gem])
        else:
            self.gem_combo.set("Без камня")

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
        """Сохранить украшение из редактора"""
        if not self._current_item:
            return

        item = self._current_item
        item.item_id = self.id_entry.get()
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_entry.get()

        # Тип украшения
        type_names = list(JewelryType.get_display_names().values())
        type_keys = list(JewelryType.get_display_names().keys())
        type_name = self.jewelry_type_combo.get()
        if type_name in type_names:
            item.jewelry_type = type_keys[type_names.index(type_name)]

        # Слот (автоматически из типа)
        slot_map = {"ring": "ring_1", "amulet": "amulet", "bracelet": "bracelet_1"}
        item.slot = slot_map.get(item.jewelry_type, "ring_1")

        # Качество
        qual_names = list(ItemQuality.get_display_names().values())
        qualities = list(ItemQuality.get_display_names().keys())
        qual_name = self.quality_combo.get()
        if qual_name in qual_names:
            item.quality = qualities[qual_names.index(qual_name)]

        # Материал
        material_name = self.material_combo.get()
        if material_name in self._materials:
            item.material = self._materials[material_name]

        # Камень
        gem_name = self.gem_combo.get()
        if gem_name in self._gems:
            item.gem = self._gems[gem_name] or None

        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()
        item.sprite = self.sprite_entry.get()

        self.refresh_list()
