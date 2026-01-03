"""
Система шаблонов экипировки v2.0

ПОЛИТИКА ШАБЛОНОВ:
1. Каждый тип экипировки имеет свой шаблон
2. Шаблон определяет ДИАПАЗОНЫ параметров для каждого уровня качества
3. Шаблон определяет ДОПУСТИМЫЕ характеристики для данного типа экипировки
4. При создании предмета параметры генерируются на основе шаблона + качества + уровня материала

ФОРМУЛА РАСЧЁТА:
    базовое_значение = template.base_value * quality_multiplier * tier_multiplier
    финальное_значение = random(базовое_значение * variance_min, базовое_значение * variance_max)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from copy import deepcopy

from .enums import (
    EquipmentType, WeaponSubtype, ArmorWeight, ItemQuality,
    StatType, DerivedStat, MaterialTier
)
from .item_models import Range, StatBonus


# ==================== ПАРАМЕТРЫ КАЧЕСТВА ====================

@dataclass
class QualityParameters:
    """
    Параметры для конкретного уровня качества
    Определяет диапазоны значений и количество бонусов
    """
    # Множитель основных параметров (урон/защита)
    main_stat_multiplier: float = 1.0

    # Диапазон основного параметра (как множитель от базового)
    main_stat_variance: Range = field(default_factory=lambda: Range(90, 110))

    # Количество дополнительных бонусов
    bonus_count: Range = field(default_factory=lambda: Range(0, 0))

    # Диапазон значений бонусов (как множитель от базового бонуса)
    bonus_value_multiplier: float = 1.0
    bonus_value_variance: Range = field(default_factory=lambda: Range(90, 110))

    # Множитель цены
    price_multiplier: float = 1.0

    # Множитель требований
    requirement_multiplier: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_stat_multiplier": self.main_stat_multiplier,
            "main_stat_variance": self.main_stat_variance.to_list(),
            "bonus_count": self.bonus_count.to_list(),
            "bonus_value_multiplier": self.bonus_value_multiplier,
            "bonus_value_variance": self.bonus_value_variance.to_list(),
            "price_multiplier": self.price_multiplier,
            "requirement_multiplier": self.requirement_multiplier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityParameters":
        return cls(
            main_stat_multiplier=data.get("main_stat_multiplier", 1.0),
            main_stat_variance=Range.from_dict(data.get("main_stat_variance", [90, 110])),
            bonus_count=Range.from_dict(data.get("bonus_count", [0, 0])),
            bonus_value_multiplier=data.get("bonus_value_multiplier", 1.0),
            bonus_value_variance=Range.from_dict(data.get("bonus_value_variance", [90, 110])),
            price_multiplier=data.get("price_multiplier", 1.0),
            requirement_multiplier=data.get("requirement_multiplier", 1.0),
        )


# ==================== ШАБЛОН ЭКИПИРОВКИ ====================

@dataclass
class EquipmentTemplate:
    """
    Шаблон для типа экипировки
    Определяет базовые параметры и правила генерации для всех качеств
    """
    # Идентификация
    template_id: str = ""
    name: str = ""
    equipment_type: str = EquipmentType.WEAPON_MELEE_1H.value

    # Базовые значения (для Tier 1, Quality Common)
    base_damage: int = 0          # Для оружия
    base_defense: int = 0         # Для брони
    base_bonus_value: int = 1     # Базовое значение бонуса к статам

    # Базовая цена и вес
    base_price: int = 10
    base_weight: float = 1.0

    # Базовые требования
    base_required_level: int = 1

    # Допустимые характеристики для бонусов
    allowed_primary_stats: List[str] = field(default_factory=list)   # StatType values
    allowed_secondary_stats: List[str] = field(default_factory=list) # DerivedStat values

    # Параметры по качествам
    quality_params: Dict[str, QualityParameters] = field(default_factory=dict)

    def __post_init__(self):
        # Инициализируем параметры качества по умолчанию, если не заданы
        if not self.quality_params:
            self.quality_params = self._get_default_quality_params()

    def _get_default_quality_params(self) -> Dict[str, QualityParameters]:
        """Параметры по умолчанию для каждого качества"""
        return {
            ItemQuality.POOR.value: QualityParameters(
                main_stat_multiplier=0.7,
                main_stat_variance=Range(85, 95),
                bonus_count=Range(0, 0),
                bonus_value_multiplier=0.0,
                price_multiplier=0.5,
                requirement_multiplier=0.8,
            ),
            ItemQuality.COMMON.value: QualityParameters(
                main_stat_multiplier=1.0,
                main_stat_variance=Range(90, 110),
                bonus_count=Range(0, 1),
                bonus_value_multiplier=1.0,
                bonus_value_variance=Range(90, 110),
                price_multiplier=1.0,
                requirement_multiplier=1.0,
            ),
            ItemQuality.UNCOMMON.value: QualityParameters(
                main_stat_multiplier=1.15,
                main_stat_variance=Range(95, 115),
                bonus_count=Range(1, 2),
                bonus_value_multiplier=1.2,
                bonus_value_variance=Range(90, 115),
                price_multiplier=2.0,
                requirement_multiplier=1.0,
            ),
            ItemQuality.RARE.value: QualityParameters(
                main_stat_multiplier=1.3,
                main_stat_variance=Range(100, 120),
                bonus_count=Range(2, 3),
                bonus_value_multiplier=1.5,
                bonus_value_variance=Range(95, 120),
                price_multiplier=5.0,
                requirement_multiplier=1.1,
            ),
            ItemQuality.EPIC.value: QualityParameters(
                main_stat_multiplier=1.5,
                main_stat_variance=Range(105, 125),
                bonus_count=Range(3, 4),
                bonus_value_multiplier=1.8,
                bonus_value_variance=Range(100, 130),
                price_multiplier=15.0,
                requirement_multiplier=1.2,
            ),
            ItemQuality.LEGENDARY.value: QualityParameters(
                main_stat_multiplier=1.8,
                main_stat_variance=Range(110, 130),
                bonus_count=Range(4, 5),
                bonus_value_multiplier=2.2,
                bonus_value_variance=Range(110, 140),
                price_multiplier=50.0,
                requirement_multiplier=1.3,
            ),
            ItemQuality.ARTIFACT.value: QualityParameters(
                main_stat_multiplier=2.2,
                main_stat_variance=Range(120, 140),
                bonus_count=Range(5, 6),
                bonus_value_multiplier=2.5,
                bonus_value_variance=Range(120, 150),
                price_multiplier=200.0,
                requirement_multiplier=1.5,
            ),
        }

    def get_quality_params(self, quality: str) -> QualityParameters:
        """Получить параметры для качества"""
        return self.quality_params.get(quality, self.quality_params.get(ItemQuality.COMMON.value))

    def calculate_main_stat(self, quality: str, tier: int) -> Range:
        """
        Рассчитать диапазон основного параметра (урон/защита)

        Формула:
            base = base_damage или base_defense
            tier_mult = MaterialTier.get_stat_multiplier()[tier]
            quality_mult = quality_params.main_stat_multiplier
            variance = quality_params.main_stat_variance

            min = base * tier_mult * quality_mult * (variance.min / 100)
            max = base * tier_mult * quality_mult * (variance.max / 100)
        """
        base = self.base_damage if self.base_damage > 0 else self.base_defense
        if base == 0:
            return Range(0, 0)

        tier_mult = MaterialTier.get_stat_multiplier().get(tier, 1.0)
        qp = self.get_quality_params(quality)

        base_value = base * tier_mult * qp.main_stat_multiplier
        min_val = int(base_value * qp.main_stat_variance.min_val / 100)
        max_val = int(base_value * qp.main_stat_variance.max_val / 100)

        return Range(min_val, max_val)

    def calculate_bonus_count(self, quality: str) -> Range:
        """Получить диапазон количества бонусов для качества"""
        qp = self.get_quality_params(quality)
        return qp.bonus_count

    def calculate_bonus_value(self, quality: str, tier: int) -> Range:
        """
        Рассчитать диапазон значения бонуса

        Формула:
            base = base_bonus_value
            tier_mult = MaterialTier.get_stat_multiplier()[tier]
            quality_mult = quality_params.bonus_value_multiplier
            variance = quality_params.bonus_value_variance

            min = base * tier_mult * quality_mult * (variance.min / 100)
            max = base * tier_mult * quality_mult * (variance.max / 100)
        """
        tier_mult = MaterialTier.get_stat_multiplier().get(tier, 1.0)
        qp = self.get_quality_params(quality)

        if qp.bonus_value_multiplier == 0:
            return Range(0, 0)

        base_value = self.base_bonus_value * tier_mult * qp.bonus_value_multiplier
        min_val = max(1, int(base_value * qp.bonus_value_variance.min_val / 100))
        max_val = max(1, int(base_value * qp.bonus_value_variance.max_val / 100))

        return Range(min_val, max_val)

    def calculate_price(self, quality: str, tier: int) -> int:
        """Рассчитать цену"""
        tier_mult = MaterialTier.get_stat_multiplier().get(tier, 1.0)
        qp = self.get_quality_params(quality)
        return int(self.base_price * tier_mult * qp.price_multiplier)

    def calculate_required_level(self, quality: str, tier: int) -> int:
        """Рассчитать требуемый уровень"""
        # Уровень зависит от tier и немного от качества
        tier_level = (tier - 1) * 10 + 1  # Tier 1 = 1, Tier 2 = 11, etc.
        qp = self.get_quality_params(quality)
        return max(1, int(tier_level * qp.requirement_multiplier))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "equipment_type": self.equipment_type,
            "base_damage": self.base_damage,
            "base_defense": self.base_defense,
            "base_bonus_value": self.base_bonus_value,
            "base_price": self.base_price,
            "base_weight": self.base_weight,
            "base_required_level": self.base_required_level,
            "allowed_primary_stats": self.allowed_primary_stats,
            "allowed_secondary_stats": self.allowed_secondary_stats,
            "quality_params": {k: v.to_dict() for k, v in self.quality_params.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquipmentTemplate":
        quality_params = {}
        for k, v in data.get("quality_params", {}).items():
            quality_params[k] = QualityParameters.from_dict(v)

        template = cls(
            template_id=data.get("template_id", ""),
            name=data.get("name", ""),
            equipment_type=data.get("equipment_type", EquipmentType.WEAPON_MELEE_1H.value),
            base_damage=data.get("base_damage", 0),
            base_defense=data.get("base_defense", 0),
            base_bonus_value=data.get("base_bonus_value", 1),
            base_price=data.get("base_price", 10),
            base_weight=data.get("base_weight", 1.0),
            base_required_level=data.get("base_required_level", 1),
            allowed_primary_stats=data.get("allowed_primary_stats", []),
            allowed_secondary_stats=data.get("allowed_secondary_stats", []),
        )
        if quality_params:
            template.quality_params = quality_params
        return template

    def copy(self) -> "EquipmentTemplate":
        return deepcopy(self)


# ==================== ФАБРИКА ШАБЛОНОВ ====================

class TemplateFactory:
    """
    Фабрика для создания стандартных шаблонов экипировки
    """

    @staticmethod
    def create_weapon_template(
        weapon_subtype: WeaponSubtype,
        base_damage: int = 10,
        base_price: int = 20,
    ) -> EquipmentTemplate:
        """Создать шаблон оружия"""
        # Определяем допустимые статы для оружия
        melee_stats = [StatType.STRENGTH.value, StatType.DEXTERITY.value]
        ranged_stats = [StatType.DEXTERITY.value, StatType.LUCK.value]
        magic_stats = [StatType.INTELLIGENCE.value, StatType.SPIRIT.value]

        equipment_type = WeaponSubtype.get_equipment_type(weapon_subtype)

        if equipment_type == EquipmentType.WEAPON_MAGIC:
            allowed_primary = magic_stats
        elif equipment_type == EquipmentType.WEAPON_RANGED:
            allowed_primary = ranged_stats
        else:
            allowed_primary = melee_stats

        # Вторичные статы
        allowed_secondary = [
            DerivedStat.CRIT_CHANCE.value,
            DerivedStat.CRIT_DAMAGE.value,
            DerivedStat.DAMAGE.value,
        ]

        # Множитель урона из подтипа
        damage_mult = WeaponSubtype.get_base_damage_multiplier().get(weapon_subtype.value, 1.0)
        adjusted_damage = int(base_damage * damage_mult)

        return EquipmentTemplate(
            template_id=f"template_{weapon_subtype.value}",
            name=WeaponSubtype.get_display_names().get(weapon_subtype.value, weapon_subtype.value),
            equipment_type=equipment_type.value,
            base_damage=adjusted_damage,
            base_defense=0,
            base_bonus_value=2,
            base_price=base_price,
            base_weight=2.0 if equipment_type in [EquipmentType.WEAPON_MELEE_2H] else 1.0,
            allowed_primary_stats=allowed_primary,
            allowed_secondary_stats=allowed_secondary,
        )

    @staticmethod
    def create_armor_template(
        equipment_type: EquipmentType,
        armor_weight: ArmorWeight,
        base_defense: int = 5,
        base_price: int = 15,
    ) -> EquipmentTemplate:
        """Создать шаблон брони"""
        # Множитель защиты от веса брони
        defense_mult = ArmorWeight.get_defense_multiplier().get(armor_weight.value, 1.0)
        adjusted_defense = int(base_defense * defense_mult)

        # Допустимые статы зависят от типа брони
        if armor_weight == ArmorWeight.CLOTH:
            allowed_primary = [StatType.INTELLIGENCE.value, StatType.SPIRIT.value]
        elif armor_weight == ArmorWeight.LIGHT:
            allowed_primary = [StatType.DEXTERITY.value, StatType.LUCK.value]
        elif armor_weight == ArmorWeight.MEDIUM:
            allowed_primary = [StatType.STRENGTH.value, StatType.DEXTERITY.value, StatType.CONSTITUTION.value]
        else:  # HEAVY
            allowed_primary = [StatType.STRENGTH.value, StatType.CONSTITUTION.value]

        allowed_secondary = [
            DerivedStat.MAX_HEALTH.value,
            DerivedStat.DEFENSE.value,
            DerivedStat.DODGE_CHANCE.value,
            DerivedStat.BLOCK_CHANCE.value,
        ]

        # Базовый вес зависит от слота и веса брони
        slot_weight = {
            EquipmentType.ARMOR_HEAD: 1.0,
            EquipmentType.ARMOR_CHEST: 3.0,
            EquipmentType.ARMOR_HANDS: 0.5,
            EquipmentType.ARMOR_FEET: 1.0,
            EquipmentType.ARMOR_BELT: 0.5,
        }
        weight_mult = ArmorWeight.get_defense_multiplier().get(armor_weight.value, 1.0)
        base_weight = slot_weight.get(equipment_type, 1.0) * weight_mult

        return EquipmentTemplate(
            template_id=f"template_{equipment_type.value}_{armor_weight.value}",
            name=f"{ArmorWeight.get_display_names()[armor_weight.value]} {EquipmentType.get_display_names()[equipment_type.value]}",
            equipment_type=equipment_type.value,
            base_damage=0,
            base_defense=adjusted_defense,
            base_bonus_value=2,
            base_price=base_price,
            base_weight=base_weight,
            allowed_primary_stats=allowed_primary,
            allowed_secondary_stats=allowed_secondary,
        )

    @staticmethod
    def create_jewelry_template(
        equipment_type: EquipmentType,
        base_price: int = 25,
    ) -> EquipmentTemplate:
        """Создать шаблон украшения"""
        # Украшения могут давать любые статы
        allowed_primary = [s.value for s in StatType]
        allowed_secondary = [
            DerivedStat.MAX_HEALTH.value,
            DerivedStat.MAX_MANA.value,
            DerivedStat.MAX_STAMINA.value,
            DerivedStat.CRIT_CHANCE.value,
            DerivedStat.DODGE_CHANCE.value,
        ]

        return EquipmentTemplate(
            template_id=f"template_{equipment_type.value}",
            name=EquipmentType.get_display_names().get(equipment_type.value, "Украшение"),
            equipment_type=equipment_type.value,
            base_damage=0,
            base_defense=0,
            base_bonus_value=3,  # Украшения дают больше бонусов к статам
            base_price=base_price,
            base_weight=0.1,
            allowed_primary_stats=allowed_primary,
            allowed_secondary_stats=allowed_secondary,
        )


# ==================== ХРАНИЛИЩЕ ШАБЛОНОВ ====================

@dataclass
class TemplatesConfig:
    """
    Конфигурация всех шаблонов экипировки
    """
    version: str = "2.0.0"
    templates: Dict[str, EquipmentTemplate] = field(default_factory=dict)

    def get_template(self, template_id: str) -> Optional[EquipmentTemplate]:
        """Получить шаблон по ID"""
        return self.templates.get(template_id)

    def get_templates_by_type(self, equipment_type: str) -> List[EquipmentTemplate]:
        """Получить все шаблоны для типа экипировки"""
        return [t for t in self.templates.values() if t.equipment_type == equipment_type]

    def add_template(self, template: EquipmentTemplate):
        """Добавить шаблон"""
        self.templates[template.template_id] = template

    def remove_template(self, template_id: str):
        """Удалить шаблон"""
        if template_id in self.templates:
            del self.templates[template_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "templates": {k: v.to_dict() for k, v in self.templates.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplatesConfig":
        templates = {}
        for k, v in data.get("templates", {}).items():
            templates[k] = EquipmentTemplate.from_dict(v)
        return cls(
            version=data.get("version", "2.0.0"),
            templates=templates,
        )

    @classmethod
    def create_default(cls) -> "TemplatesConfig":
        """Создать конфигурацию с шаблонами по умолчанию"""
        config = cls()

        # Создаём шаблоны оружия
        for weapon_subtype in WeaponSubtype:
            template = TemplateFactory.create_weapon_template(weapon_subtype)
            config.add_template(template)

        # Создаём шаблоны брони
        armor_types = [
            EquipmentType.ARMOR_HEAD,
            EquipmentType.ARMOR_CHEST,
            EquipmentType.ARMOR_HANDS,
            EquipmentType.ARMOR_FEET,
            EquipmentType.ARMOR_BELT,
        ]
        for armor_type in armor_types:
            for armor_weight in ArmorWeight:
                template = TemplateFactory.create_armor_template(armor_type, armor_weight)
                config.add_template(template)

        # Создаём шаблоны украшений
        jewelry_types = [
            EquipmentType.JEWELRY_RING,
            EquipmentType.JEWELRY_AMULET,
            EquipmentType.JEWELRY_BRACELET,
        ]
        for jewelry_type in jewelry_types:
            template = TemplateFactory.create_jewelry_template(jewelry_type)
            config.add_template(template)

        return config
