"""
Вкладка редактора экипировки v2.0
Универсальная вкладка для оружия, брони и украшений
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple, Any, Union

from ..base_editor import BaseEditorTab
from ..widgets import (
    LabeledEntry, LabeledSpinbox, LabeledFloatSpinbox,
    LabeledCombobox, LabeledCheckbox, LabeledTextarea,
    RangeEditor, StatBonusEditor
)
from ...core.config_manager import ConfigManager
from ...core.item_models import WeaponItem, ArmorItem, JewelryItem, EquipmentItem, StatBonus, Range
from ...core.enums import (
    EquipmentType, WeaponSubtype, ArmorWeight,
    ItemQuality, MaterialTier, StatType, DerivedStat
)

EquipmentItemType = Union[WeaponItem, ArmorItem, JewelryItem]


class EquipmentTab(BaseEditorTab):
    """Вкладка редактора экипировки"""

    def get_item_type_name(self) -> str:
        return "equipment"

    def get_items_list(self) -> List[Tuple[str, str]]:
        items = []
        # Оружие
        for weapon in self.config_manager.project.weapons:
            items.append((weapon.item_id, f"[Оружие] {weapon.display_name or weapon.name}"))
        # Броня
        for armor in self.config_manager.project.armor:
            items.append((armor.item_id, f"[Броня] {armor.display_name or armor.name}"))
        # Украшения
        for jewelry in self.config_manager.project.jewelry:
            items.append((jewelry.item_id, f"[Украшение] {jewelry.display_name or jewelry.name}"))
        return items

    def find_item_by_id(self, item_id: str) -> Optional[EquipmentItemType]:
        for weapon in self.config_manager.project.weapons:
            if weapon.item_id == item_id:
                return weapon
        for armor in self.config_manager.project.armor:
            if armor.item_id == item_id:
                return armor
        for jewelry in self.config_manager.project.jewelry:
            if jewelry.item_id == item_id:
                return jewelry
        return None

    def create_new_item(self) -> EquipmentItemType:
        # По умолчанию создаём оружие
        base_id = "new_weapon"
        counter = 1
        new_id = base_id
        while self.find_item_by_id(new_id):
            new_id = f"{base_id}_{counter}"
            counter += 1

        return WeaponItem(
            item_id=new_id,
            name="Новое оружие",
            display_name="Новое оружие",
            description="",
            quality=ItemQuality.COMMON.value,
            equipment_type=EquipmentType.WEAPON_MELEE_1H.value,
            weapon_subtype=WeaponSubtype.SWORD.value,
            material_tier=1,
            damage=Range(5, 10),
            required_level=1,
            base_price=10,
            weight=1.0,
        )

    def add_item_to_project(self, item: EquipmentItemType):
        if isinstance(item, WeaponItem):
            self.config_manager.project.weapons.append(item)
        elif isinstance(item, ArmorItem):
            self.config_manager.project.armor.append(item)
        elif isinstance(item, JewelryItem):
            self.config_manager.project.jewelry.append(item)

    def remove_item_from_project(self, item_id: str):
        self.config_manager.project.weapons = [
            w for w in self.config_manager.project.weapons if w.item_id != item_id
        ]
        self.config_manager.project.armor = [
            a for a in self.config_manager.project.armor if a.item_id != item_id
        ]
        self.config_manager.project.jewelry = [
            j for j in self.config_manager.project.jewelry if j.item_id != item_id
        ]

    def _create_item_from_dict(self, data: dict) -> Optional[EquipmentItemType]:
        try:
            eq_type = data.get("equipment_type", "")
            if "weapon" in eq_type.lower():
                return WeaponItem.from_dict(data)
            elif "armor" in eq_type.lower():
                return ArmorItem.from_dict(data)
            elif "jewelry" in eq_type.lower():
                return JewelryItem.from_dict(data)
            else:
                return WeaponItem.from_dict(data)
        except:
            return None

    def _create_editor(self, parent: ttk.Frame):
        """Создать форму редактора экипировки"""
        # Прокручиваемая область
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.editor_frame = ttk.Frame(canvas)

        self.editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # === Основная информация ===
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

        # === Тип экипировки ===
        type_frame = ttk.LabelFrame(self.editor_frame, text="Тип экипировки", padding=10)
        type_frame.pack(fill=tk.X, padx=5, pady=5)

        # Категория: Оружие/Броня/Украшение
        self.category_var = tk.StringVar(value="weapon")
        cat_row = ttk.Frame(type_frame)
        cat_row.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(cat_row, text="Оружие", variable=self.category_var, value="weapon",
                       command=self._on_category_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(cat_row, text="Броня", variable=self.category_var, value="armor",
                       command=self._on_category_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(cat_row, text="Украшение", variable=self.category_var, value="jewelry",
                       command=self._on_category_change).pack(side=tk.LEFT, padx=5)

        # Подтип (зависит от категории)
        self.subtype_combo = LabeledCombobox(type_frame, "Подтип:", values=[])
        self.subtype_combo.pack(fill=tk.X, pady=2)
        self.subtype_combo.bind_change(self._on_subtype_change)

        # Дополнительные параметры для брони
        self.armor_weight_combo = LabeledCombobox(
            type_frame, "Класс брони:",
            values=list(ArmorWeight.get_display_names().values())
        )
        self.armor_weight_combo.pack(fill=tk.X, pady=2)
        self.armor_weight_combo.bind_change(self._mark_modified)
        self._armor_weight_map = {v: k for k, v in ArmorWeight.get_display_names().items()}

        # === Качество и материал ===
        quality_frame = ttk.LabelFrame(self.editor_frame, text="Качество и материал", padding=10)
        quality_frame.pack(fill=tk.X, padx=5, pady=5)

        quality_names = ItemQuality.get_display_names()
        self.quality_combo = LabeledCombobox(quality_frame, "Качество:", values=list(quality_names.values()))
        self.quality_combo.pack(fill=tk.X, pady=2)
        self.quality_combo.bind_change(self._mark_modified)
        self._quality_map = {v: k for k, v in quality_names.items()}
        self._quality_map_rev = quality_names

        tier_names = MaterialTier.get_display_names()
        self.tier_combo = LabeledCombobox(
            quality_frame, "Уровень материала:",
            values=[f"{k} - {v}" for k, v in tier_names.items()]
        )
        self.tier_combo.pack(fill=tk.X, pady=2)
        self.tier_combo.bind_change(self._mark_modified)

        # === Боевые параметры ===
        combat_frame = ttk.LabelFrame(self.editor_frame, text="Боевые параметры", padding=10)
        combat_frame.pack(fill=tk.X, padx=5, pady=5)

        self.damage_range = RangeEditor(combat_frame, "Урон:", from_=0, to=9999)
        self.damage_range.pack(fill=tk.X, pady=2)
        self.damage_range.bind_change(self._mark_modified)

        self.defense_range = RangeEditor(combat_frame, "Защита:", from_=0, to=9999)
        self.defense_range.pack(fill=tk.X, pady=2)
        self.defense_range.bind_change(self._mark_modified)

        self.tactical_range_spin = LabeledSpinbox(combat_frame, "Тактический радиус:", from_=1, to=10)
        self.tactical_range_spin.pack(fill=tk.X, pady=2)
        self.tactical_range_spin.bind_change(self._mark_modified)

        self.attack_speed_spin = LabeledFloatSpinbox(combat_frame, "Скорость атаки:", from_=0.1, to=5.0)
        self.attack_speed_spin.pack(fill=tk.X, pady=2)
        self.attack_speed_spin.bind_change(self._mark_modified)

        # === Бонусы ===
        bonuses_frame = ttk.LabelFrame(self.editor_frame, text="Бонусы к характеристикам", padding=10)
        bonuses_frame.pack(fill=tk.X, padx=5, pady=5)

        # Собираем все возможные статы
        stat_options = []
        for stat in StatType:
            stat_options.append((stat.value, StatType.get_display_names()[stat.value]))
        for stat in DerivedStat:
            stat_options.append((stat.value, DerivedStat.get_display_names()[stat.value]))

        self.stat_bonuses_editor = StatBonusEditor(
            bonuses_frame,
            stat_options=stat_options,
            on_change=self._mark_modified
        )
        self.stat_bonuses_editor.pack(fill=tk.BOTH, expand=True)

        # === Требования ===
        req_frame = ttk.LabelFrame(self.editor_frame, text="Требования", padding=10)
        req_frame.pack(fill=tk.X, padx=5, pady=5)

        self.required_level_spin = LabeledSpinbox(req_frame, "Уровень:", from_=1, to=100)
        self.required_level_spin.pack(fill=tk.X, pady=2)
        self.required_level_spin.bind_change(self._mark_modified)

        self.durability_spin = LabeledSpinbox(req_frame, "Прочность:", from_=1, to=9999)
        self.durability_spin.pack(fill=tk.X, pady=2)
        self.durability_spin.bind_change(self._mark_modified)

        # === Экономика ===
        economy_frame = ttk.LabelFrame(self.editor_frame, text="Экономика", padding=10)
        economy_frame.pack(fill=tk.X, padx=5, pady=5)

        self.price_spin = LabeledSpinbox(economy_frame, "Базовая цена:", from_=0, to=999999)
        self.price_spin.pack(fill=tk.X, pady=2)
        self.price_spin.bind_change(self._mark_modified)

        self.weight_spin = LabeledFloatSpinbox(economy_frame, "Вес:", from_=0.0, to=999.9)
        self.weight_spin.pack(fill=tk.X, pady=2)
        self.weight_spin.bind_change(self._mark_modified)

        # === Связанный рецепт (управляется во вкладке Рецепты) ===
        recipe_frame = ttk.LabelFrame(self.editor_frame, text="Связанный рецепт", padding=10)
        recipe_frame.pack(fill=tk.X, padx=5, pady=5)

        self.recipe_label = ttk.Label(recipe_frame, text="Рецепт: (не задан)")
        self.recipe_label.pack(fill=tk.X, pady=2)

        ttk.Label(recipe_frame, text="(Связь создаётся во вкладке Рецепты)",
                 foreground="gray").pack(anchor="w")

        ttk.Button(recipe_frame, text="Очистить связь", command=self._clear_recipe).pack(anchor="w", pady=2)

        # === Визуал ===
        visual_frame = ttk.LabelFrame(self.editor_frame, text="Визуал", padding=10)
        visual_frame.pack(fill=tk.X, padx=5, pady=5)

        self.icon_entry = LabeledEntry(visual_frame, "Иконка:")
        self.icon_entry.pack(fill=tk.X, pady=2)
        self.icon_entry.bind_change(self._mark_modified)

        self.sprite_entry = LabeledEntry(visual_frame, "Спрайт:")
        self.sprite_entry.pack(fill=tk.X, pady=2)
        self.sprite_entry.bind_change(self._mark_modified)

        # Инициализация UI для категории по умолчанию
        self._on_category_change()

    def _on_name_change(self):
        """Автозаполнение ID при изменении имени"""
        name = self.name_entry.get()
        if name and not self.id_entry.get():
            item_id = name.lower().replace(" ", "_")
            self.id_entry.set(item_id)
        if name and not self.display_name_entry.get():
            self.display_name_entry.set(name)
        self._mark_modified()

    def _on_category_change(self):
        """Обработка смены категории экипировки"""
        category = self.category_var.get()

        if category == "weapon":
            # Показать подтипы оружия
            weapon_names = WeaponSubtype.get_display_names()
            self.subtype_combo.set_values(list(weapon_names.values()))
            self._subtype_map = {v: k for k, v in weapon_names.items()}

            # Показать урон, скрыть защиту
            self.damage_range.pack(fill=tk.X, pady=2)
            self.defense_range.pack_forget()
            self.tactical_range_spin.pack(fill=tk.X, pady=2)
            self.attack_speed_spin.pack(fill=tk.X, pady=2)
            self.armor_weight_combo.pack_forget()

        elif category == "armor":
            # Показать подтипы брони (слоты)
            armor_slots = {
                EquipmentType.ARMOR_HEAD.value: "Шлем",
                EquipmentType.ARMOR_CHEST.value: "Нагрудник",
                EquipmentType.ARMOR_HANDS.value: "Перчатки",
                EquipmentType.ARMOR_FEET.value: "Обувь",
                EquipmentType.ARMOR_BELT.value: "Пояс",
            }
            self.subtype_combo.set_values(list(armor_slots.values()))
            self._subtype_map = {v: k for k, v in armor_slots.items()}

            # Показать защиту, скрыть урон
            self.damage_range.pack_forget()
            self.defense_range.pack(fill=tk.X, pady=2)
            self.tactical_range_spin.pack_forget()
            self.attack_speed_spin.pack_forget()
            self.armor_weight_combo.pack(fill=tk.X, pady=2)

        elif category == "jewelry":
            # Показать типы украшений
            jewelry_types = {
                EquipmentType.JEWELRY_RING.value: "Кольцо",
                EquipmentType.JEWELRY_AMULET.value: "Амулет",
                EquipmentType.JEWELRY_BRACELET.value: "Браслет",
            }
            self.subtype_combo.set_values(list(jewelry_types.values()))
            self._subtype_map = {v: k for k, v in jewelry_types.items()}

            # Скрыть урон и защиту
            self.damage_range.pack_forget()
            self.defense_range.pack_forget()
            self.tactical_range_spin.pack_forget()
            self.attack_speed_spin.pack_forget()
            self.armor_weight_combo.pack_forget()

        self._mark_modified()

    def _on_subtype_change(self):
        """Обработка смены подтипа"""
        category = self.category_var.get()
        subtype_display = self.subtype_combo.get()
        subtype = self._subtype_map.get(subtype_display, "")

        if category == "weapon":
            # Автообновление тактического радиуса
            try:
                weapon_subtype = WeaponSubtype(subtype)
                tactical_range = WeaponSubtype.get_tactical_range().get(subtype, 1)
                self.tactical_range_spin.set(tactical_range)
            except:
                pass

        self._mark_modified()

    def _clear_recipe(self):
        if self._current_item_id:
            item = self.find_item_by_id(self._current_item_id)
            if item:
                item.recipe_id = None
                self.recipe_label.config(text="Рецепт: (не задан)")
                self._mark_modified()

    def load_item_to_editor(self, item: EquipmentItemType):
        """Загрузить экипировку в форму"""
        self.id_entry.set(item.item_id)
        self.name_entry.set(item.name)
        self.display_name_entry.set(item.display_name)
        self.description_text.set(item.description)

        # Определяем категорию
        if isinstance(item, WeaponItem):
            self.category_var.set("weapon")
            self._on_category_change()

            # Подтип оружия
            weapon_names = WeaponSubtype.get_display_names()
            subtype_display = weapon_names.get(item.weapon_subtype, "")
            self.subtype_combo.set(subtype_display)

            # Урон
            if item.damage:
                self.damage_range.set(item.damage.min_val, item.damage.max_val)
            else:
                self.damage_range.set(0, 0)

            self.tactical_range_spin.set(item.tactical_range)
            self.attack_speed_spin.set(item.attack_speed)

        elif isinstance(item, ArmorItem):
            self.category_var.set("armor")
            self._on_category_change()

            # Подтип (слот)
            armor_slots = {
                EquipmentType.ARMOR_HEAD.value: "Шлем",
                EquipmentType.ARMOR_CHEST.value: "Нагрудник",
                EquipmentType.ARMOR_HANDS.value: "Перчатки",
                EquipmentType.ARMOR_FEET.value: "Обувь",
                EquipmentType.ARMOR_BELT.value: "Пояс",
            }
            slot_display = armor_slots.get(item.equipment_type, "")
            self.subtype_combo.set(slot_display)

            # Защита
            if item.defense:
                self.defense_range.set(item.defense.min_val, item.defense.max_val)
            else:
                self.defense_range.set(0, 0)

            # Класс брони
            armor_weight_display = ArmorWeight.get_display_names().get(item.armor_weight, "")
            self.armor_weight_combo.set(armor_weight_display)

        elif isinstance(item, JewelryItem):
            self.category_var.set("jewelry")
            self._on_category_change()

            # Тип украшения
            jewelry_types = {
                EquipmentType.JEWELRY_RING.value: "Кольцо",
                EquipmentType.JEWELRY_AMULET.value: "Амулет",
                EquipmentType.JEWELRY_BRACELET.value: "Браслет",
            }
            type_display = jewelry_types.get(item.equipment_type, "")
            self.subtype_combo.set(type_display)

        # Качество
        quality_display = self._quality_map_rev.get(item.quality, "")
        self.quality_combo.set(quality_display)

        # Tier
        tier_names = MaterialTier.get_display_names()
        tier_display = f"{item.material_tier} - {tier_names.get(item.material_tier, '')}"
        self.tier_combo.set(tier_display)

        # Бонусы
        bonuses = [b.to_dict() for b in item.stat_bonuses]
        self.stat_bonuses_editor.set_bonuses(bonuses)

        # Требования
        self.required_level_spin.set(item.required_level)
        self.durability_spin.set(item.max_durability)

        # Экономика
        self.price_spin.set(item.base_price)
        self.weight_spin.set(item.weight)

        # Рецепт
        if item.recipe_id:
            recipe = self.config_manager.project.get_recipe_by_id(item.recipe_id)
            if recipe:
                self.recipe_label.config(text=f"Рецепт: {recipe.display_name} [{recipe.recipe_id}]")
            else:
                self.recipe_label.config(text=f"Рецепт: {item.recipe_id} (не найден)")
        else:
            self.recipe_label.config(text="Рецепт: (не задан)")

        # Визуал
        self.icon_entry.set(item.icon)
        self.sprite_entry.set(item.sprite)

    def save_item_from_editor(self) -> bool:
        """Сохранить экипировку из формы"""
        if not self._current_item_id:
            return False

        item = self.find_item_by_id(self._current_item_id)
        if not item:
            return False

        new_id = self.id_entry.get().strip()
        if not new_id:
            return False

        # Проверяем уникальность ID
        if new_id != self._current_item_id:
            existing = self.find_item_by_id(new_id)
            if existing:
                return False

        # Определяем нужно ли создавать новый объект другого типа
        category = self.category_var.get()
        need_new_type = False

        if category == "weapon" and not isinstance(item, WeaponItem):
            need_new_type = True
        elif category == "armor" and not isinstance(item, ArmorItem):
            need_new_type = True
        elif category == "jewelry" and not isinstance(item, JewelryItem):
            need_new_type = True

        if need_new_type:
            # Удаляем старый объект и создаём новый нужного типа
            self.remove_item_from_project(self._current_item_id)

            if category == "weapon":
                new_item = WeaponItem(item_id=new_id)
            elif category == "armor":
                new_item = ArmorItem(item_id=new_id)
            else:
                new_item = JewelryItem(item_id=new_id)

            self.add_item_to_project(new_item)
            item = new_item

        # Обновляем общие поля
        item.item_id = new_id
        item.name = self.name_entry.get()
        item.display_name = self.display_name_entry.get()
        item.description = self.description_text.get()

        # Качество
        quality_display = self.quality_combo.get()
        item.quality = self._quality_map.get(quality_display, ItemQuality.COMMON.value)

        # Tier
        tier_str = self.tier_combo.get()
        try:
            item.material_tier = int(tier_str.split(" - ")[0])
        except:
            item.material_tier = 1

        # Тип-специфичные поля
        subtype_display = self.subtype_combo.get()
        subtype = self._subtype_map.get(subtype_display, "")

        if isinstance(item, WeaponItem):
            item.weapon_subtype = subtype
            item.equipment_type = WeaponSubtype.get_equipment_type(WeaponSubtype(subtype)).value
            damage = self.damage_range.get()
            item.damage = Range(damage[0], damage[1])
            item.tactical_range = self.tactical_range_spin.get()
            item.attack_speed = self.attack_speed_spin.get()

        elif isinstance(item, ArmorItem):
            item.equipment_type = subtype
            defense = self.defense_range.get()
            item.defense = Range(defense[0], defense[1])
            armor_weight_display = self.armor_weight_combo.get()
            item.armor_weight = self._armor_weight_map.get(armor_weight_display, ArmorWeight.LIGHT.value)

        elif isinstance(item, JewelryItem):
            item.equipment_type = subtype

        # Бонусы
        bonuses_data = self.stat_bonuses_editor.get_bonuses()
        item.stat_bonuses = [StatBonus.from_dict(b) for b in bonuses_data]

        # Требования
        item.required_level = self.required_level_spin.get()
        item.max_durability = self.durability_spin.get()

        # Экономика
        item.base_price = self.price_spin.get()
        item.weight = self.weight_spin.get()

        # Визуал
        item.icon = self.icon_entry.get()
        item.sprite = self.sprite_entry.get()

        # Обновляем ID если изменился
        if new_id != self._current_item_id:
            self._current_item_id = new_id
            self.refresh_list()
            self.list_panel.select_item(new_id)

        return True
