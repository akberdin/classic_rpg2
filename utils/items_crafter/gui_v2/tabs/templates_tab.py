"""
Вкладка редактора шаблонов экипировки v2.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple

from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox,
    LabeledCombobox, LabeledTextarea, QualityParamsEditor, ItemListPanel
)
from ...core.config_manager import ConfigManager
from ...core.item_templates import EquipmentTemplate, QualityParameters
from ...core.enums import EquipmentType, ItemQuality, StatType, DerivedStat


class TemplatesTab(ttk.Frame):
    """Вкладка редактора шаблонов экипировки"""

    def __init__(self, parent, config_manager: ConfigManager, on_modified=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.config_manager = config_manager
        self.on_modified = on_modified
        self._current_template_id: Optional[str] = None
        self._is_loading = False

        self._create_layout()
        self.refresh_list()

    def _mark_modified(self):
        if not self._is_loading:
            self.config_manager.mark_modified()
            if self.on_modified:
                self.on_modified()

    def _create_layout(self):
        # Разделитель
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Левая панель - список
        left_frame = ttk.Frame(paned, width=300)
        paned.add(left_frame, weight=1)

        self.list_panel = ItemListPanel(
            left_frame,
            on_select=self._on_template_selected,
            on_add=self._on_add_template,
            on_delete=self._on_delete_template,
            on_duplicate=self._on_duplicate_template,
        )
        self.list_panel.pack(fill=tk.BOTH, expand=True)

        # Правая панель - редактор
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        self._create_editor(right_frame)

    def _create_editor(self, parent):
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

        self.id_entry = LabeledEntry(info_frame, "ID шаблона:")
        self.id_entry.pack(fill=tk.X, pady=2)
        self.id_entry.bind_change(self._mark_modified)

        self.name_entry = LabeledEntry(info_frame, "Название:")
        self.name_entry.pack(fill=tk.X, pady=2)
        self.name_entry.bind_change(self._mark_modified)

        equipment_names = EquipmentType.get_display_names()
        self.equipment_type_combo = LabeledCombobox(
            info_frame, "Тип экипировки:",
            values=list(equipment_names.values())
        )
        self.equipment_type_combo.pack(fill=tk.X, pady=2)
        self.equipment_type_combo.bind_change(self._mark_modified)
        self._eq_type_map = {v: k for k, v in equipment_names.items()}
        self._eq_type_map_rev = equipment_names

        # Базовые значения
        base_frame = ttk.LabelFrame(self.editor_frame, text="Базовые значения (Tier 1, Common)", padding=10)
        base_frame.pack(fill=tk.X, padx=5, pady=5)

        self.base_damage_spin = LabeledSpinbox(base_frame, "Базовый урон:", from_=0, to=999)
        self.base_damage_spin.pack(fill=tk.X, pady=2)
        self.base_damage_spin.bind_change(self._mark_modified)

        self.base_defense_spin = LabeledSpinbox(base_frame, "Базовая защита:", from_=0, to=999)
        self.base_defense_spin.pack(fill=tk.X, pady=2)
        self.base_defense_spin.bind_change(self._mark_modified)

        self.base_bonus_spin = LabeledSpinbox(base_frame, "Базовый бонус:", from_=1, to=99)
        self.base_bonus_spin.pack(fill=tk.X, pady=2)
        self.base_bonus_spin.bind_change(self._mark_modified)

        self.base_price_spin = LabeledSpinbox(base_frame, "Базовая цена:", from_=1, to=99999)
        self.base_price_spin.pack(fill=tk.X, pady=2)
        self.base_price_spin.bind_change(self._mark_modified)

        self.base_weight_spin = LabeledFloatSpinbox(base_frame, "Базовый вес:", from_=0.1, to=99.9)
        self.base_weight_spin.pack(fill=tk.X, pady=2)
        self.base_weight_spin.bind_change(self._mark_modified)

        self.base_level_spin = LabeledSpinbox(base_frame, "Базовый уровень:", from_=1, to=100)
        self.base_level_spin.pack(fill=tk.X, pady=2)
        self.base_level_spin.bind_change(self._mark_modified)

        # Допустимые характеристики
        stats_frame = ttk.LabelFrame(self.editor_frame, text="Допустимые характеристики для бонусов", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(stats_frame, text="Основные характеристики:").pack(anchor="w")
        self.primary_stats_frame = ttk.Frame(stats_frame)
        self.primary_stats_frame.pack(fill=tk.X, pady=2)

        self._primary_stat_vars = {}
        for stat in StatType:
            var = tk.BooleanVar(value=False)
            self._primary_stat_vars[stat.value] = var
            cb = ttk.Checkbutton(self.primary_stats_frame, text=StatType.get_display_names()[stat.value],
                                variable=var, command=self._mark_modified)
            cb.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="Производные характеристики:").pack(anchor="w", pady=(10, 0))
        self.secondary_stats_frame = ttk.Frame(stats_frame)
        self.secondary_stats_frame.pack(fill=tk.X, pady=2)

        self._secondary_stat_vars = {}
        row_frame = None
        for i, stat in enumerate(DerivedStat):
            if i % 3 == 0:
                row_frame = ttk.Frame(self.secondary_stats_frame)
                row_frame.pack(fill=tk.X)
            var = tk.BooleanVar(value=False)
            self._secondary_stat_vars[stat.value] = var
            cb = ttk.Checkbutton(row_frame, text=DerivedStat.get_display_names()[stat.value],
                                variable=var, command=self._mark_modified)
            cb.pack(side=tk.LEFT, padx=5)

        # Параметры по качествам
        quality_frame = ttk.LabelFrame(self.editor_frame, text="Параметры по качествам", padding=10)
        quality_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        qualities = []
        for q in ItemQuality:
            color = ItemQuality.get_hex_colors()[q.value]
            qualities.append((q.value, ItemQuality.get_display_names()[q.value], color))

        self.quality_params_editor = QualityParamsEditor(quality_frame, qualities, on_change=self._mark_modified)
        self.quality_params_editor.pack(fill=tk.BOTH, expand=True)

    def refresh_list(self):
        templates = []
        for template_id, template in self.config_manager.templates.templates.items():
            templates.append((template_id, template.name))
        self.list_panel.set_items(templates)

    def _on_template_selected(self, template_id: str):
        if self._current_template_id:
            self._save_template()

        template = self.config_manager.templates.get_template(template_id)
        if template:
            self._current_template_id = template_id
            self._is_loading = True
            self._load_template(template)
            self._is_loading = False

    def _on_add_template(self):
        if self._current_template_id:
            self._save_template()

        base_id = "new_template"
        counter = 1
        new_id = base_id
        while self.config_manager.templates.get_template(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        new_template = EquipmentTemplate(
            template_id=new_id,
            name="Новый шаблон",
            equipment_type=EquipmentType.WEAPON_MELEE_1H.value,
            base_damage=10,
            base_defense=0,
            base_bonus_value=2,
            base_price=20,
            base_weight=1.0,
        )

        self.config_manager.templates.add_template(new_template)
        self._mark_modified()
        self.refresh_list()
        self.list_panel.select_item(new_id)

    def _on_delete_template(self, template_id: str):
        from tkinter import messagebox
        if messagebox.askyesno("Подтверждение", f"Удалить шаблон '{template_id}'?"):
            self.config_manager.templates.remove_template(template_id)
            if self._current_template_id == template_id:
                self._current_template_id = None
            self._mark_modified()
            self.refresh_list()

    def _on_duplicate_template(self, template_id: str):
        template = self.config_manager.templates.get_template(template_id)
        if template:
            new_template = template.copy()
            counter = 1
            new_id = f"{template_id}_copy"
            while self.config_manager.templates.get_template(new_id):
                counter += 1
                new_id = f"{template_id}_copy{counter}"
            new_template.template_id = new_id
            self.config_manager.templates.add_template(new_template)
            self._mark_modified()
            self.refresh_list()

    def _load_template(self, template: EquipmentTemplate):
        self.id_entry.set(template.template_id)
        self.name_entry.set(template.name)

        eq_type_display = self._eq_type_map_rev.get(template.equipment_type, "")
        self.equipment_type_combo.set(eq_type_display)

        self.base_damage_spin.set(template.base_damage)
        self.base_defense_spin.set(template.base_defense)
        self.base_bonus_spin.set(template.base_bonus_value)
        self.base_price_spin.set(template.base_price)
        self.base_weight_spin.set(template.base_weight)
        self.base_level_spin.set(template.base_required_level)

        # Допустимые характеристики
        for stat_value, var in self._primary_stat_vars.items():
            var.set(stat_value in template.allowed_primary_stats)

        for stat_value, var in self._secondary_stat_vars.items():
            var.set(stat_value in template.allowed_secondary_stats)

        # Параметры по качествам
        quality_params = {}
        for q_value, qp in template.quality_params.items():
            quality_params[q_value] = qp.to_dict()
        self.quality_params_editor.set_params(quality_params)

    def _save_template(self):
        if not self._current_template_id:
            return

        template = self.config_manager.templates.get_template(self._current_template_id)
        if not template:
            return

        new_id = self.id_entry.get().strip()
        if not new_id:
            return

        # Если ID изменился
        if new_id != self._current_template_id:
            if self.config_manager.templates.get_template(new_id):
                return  # ID занят
            self.config_manager.templates.remove_template(self._current_template_id)
            template.template_id = new_id
            self.config_manager.templates.add_template(template)
            self._current_template_id = new_id

        template.name = self.name_entry.get()

        eq_type_display = self.equipment_type_combo.get()
        template.equipment_type = self._eq_type_map.get(eq_type_display, EquipmentType.WEAPON_MELEE_1H.value)

        template.base_damage = self.base_damage_spin.get()
        template.base_defense = self.base_defense_spin.get()
        template.base_bonus_value = self.base_bonus_spin.get()
        template.base_price = self.base_price_spin.get()
        template.base_weight = self.base_weight_spin.get()
        template.base_required_level = self.base_level_spin.get()

        # Допустимые характеристики
        template.allowed_primary_stats = [
            stat_value for stat_value, var in self._primary_stat_vars.items() if var.get()
        ]
        template.allowed_secondary_stats = [
            stat_value for stat_value, var in self._secondary_stat_vars.items() if var.get()
        ]

        # Параметры по качествам
        quality_params_data = self.quality_params_editor.get_params()
        for q_value, data in quality_params_data.items():
            template.quality_params[q_value] = QualityParameters.from_dict(data)

        self.refresh_list()
