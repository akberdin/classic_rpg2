"""
Система нейминга предметов через словари v2.0

Генерирует отображаемые имена предметов по шаблонам:
- Материал + Тип: "Железный меч"
- Качество + Материал + Тип: "Превосходный железный меч"
- Материал + Тип + Суффикс: "Железный меч силы"
- Полная форма: "Превосходный железный меч силы"

Словари загружаются из JSON и могут редактироваться.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import random


# ==================== СЛОВАРИ ====================

@dataclass
class NamingDictionary:
    """
    Словарь для генерации имён
    """
    # Префиксы качества
    quality_prefixes: Dict[str, List[str]] = field(default_factory=dict)

    # Названия материалов по tier
    materials: Dict[int, Dict[str, str]] = field(default_factory=dict)  # tier -> {category: name}

    # Базовые названия типов экипировки
    equipment_names: Dict[str, str] = field(default_factory=dict)

    # Названия подтипов оружия
    weapon_names: Dict[str, str] = field(default_factory=dict)

    # Суффиксы по статам
    stat_suffixes: Dict[str, List[str]] = field(default_factory=dict)

    # Названия ресурсов по категориям и tier
    resource_names: Dict[str, Dict[int, str]] = field(default_factory=dict)  # category -> {tier: name}

    # Названия расходников
    consumable_names: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_prefixes": self.quality_prefixes,
            "materials": {str(k): v for k, v in self.materials.items()},
            "equipment_names": self.equipment_names,
            "weapon_names": self.weapon_names,
            "stat_suffixes": self.stat_suffixes,
            "resource_names": self.resource_names,
            "consumable_names": self.consumable_names,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NamingDictionary":
        materials = {}
        for k, v in data.get("materials", {}).items():
            materials[int(k)] = v

        return cls(
            quality_prefixes=data.get("quality_prefixes", {}),
            materials=materials,
            equipment_names=data.get("equipment_names", {}),
            weapon_names=data.get("weapon_names", {}),
            stat_suffixes=data.get("stat_suffixes", {}),
            resource_names=data.get("resource_names", {}),
            consumable_names=data.get("consumable_names", {}),
        )

    @classmethod
    def create_default(cls) -> "NamingDictionary":
        """Создать словарь по умолчанию"""
        return cls(
            quality_prefixes={
                "poor": ["Ржавый", "Сломанный", "Потрёпанный", "Изношенный"],
                "common": [],  # Обычные предметы без префикса
                "uncommon": ["Добротный", "Крепкий", "Надёжный"],
                "rare": ["Отличный", "Превосходный", "Искусный"],
                "epic": ["Великолепный", "Изумительный", "Мастерский"],
                "legendary": ["Легендарный", "Древний", "Мифический"],
                "artifact": ["Божественный", "Священный", "Первородный"],
            },

            materials={
                1: {
                    "metal": "Медный",
                    "wood": "Берёзовый",
                    "leather": "Кожаный",
                    "cloth": "Льняной",
                    "gem": "Кварцевый",
                },
                2: {
                    "metal": "Железный",
                    "wood": "Дубовый",
                    "leather": "Плотный кожаный",
                    "cloth": "Шёлковый",
                    "gem": "Аметистовый",
                },
                3: {
                    "metal": "Стальной",
                    "wood": "Ясеневый",
                    "leather": "Укреплённый кожаный",
                    "cloth": "Бархатный",
                    "gem": "Рубиновый",
                },
                4: {
                    "metal": "Мифриловый",
                    "wood": "Эбеновый",
                    "leather": "Драконий",
                    "cloth": "Звёздный",
                    "gem": "Изумрудный",
                },
                5: {
                    "metal": "Адамантиевый",
                    "wood": "Древесины Иггдрасиля",
                    "leather": "Небесный",
                    "cloth": "Эфирный",
                    "gem": "Алмазный",
                },
            },

            equipment_names={
                # Броня
                "armor_head": "шлем",
                "armor_chest": "нагрудник",
                "armor_hands": "перчатки",
                "armor_feet": "сапоги",
                "armor_belt": "пояс",
                # Украшения
                "jewelry_ring": "кольцо",
                "jewelry_amulet": "амулет",
                "jewelry_bracelet": "браслет",
                # Прочее
                "backpack": "рюкзак",
                "tool": "инструмент",
            },

            weapon_names={
                "dagger": "кинжал",
                "sword": "меч",
                "axe": "топор",
                "mace": "булава",
                "greatsword": "двуручный меч",
                "greataxe": "двуручный топор",
                "spear": "копьё",
                "staff_melee": "боевой посох",
                "bow": "лук",
                "crossbow": "арбалет",
                "wand": "жезл",
                "staff_magic": "посох",
                "orb": "сфера",
            },

            stat_suffixes={
                "strength": ["силы", "мощи", "титана"],
                "dexterity": ["ловкости", "проворства", "вора"],
                "constitution": ["стойкости", "выносливости", "камня"],
                "intelligence": ["разума", "мудрости", "учёного"],
                "spirit": ["духа", "воли", "провидца"],
                "luck": ["удачи", "фортуны", "игрока"],
                "max_health": ["жизни", "здоровья", "витальности"],
                "max_mana": ["маны", "магии", "чародея"],
                "damage": ["урона", "ярости", "берсерка"],
                "defense": ["защиты", "крепости", "стража"],
                "crit_chance": ["критических ударов", "меткости", "снайпера"],
            },

            resource_names={
                "ore": {
                    1: "Медная руда",
                    2: "Железная руда",
                    3: "Стальная руда",
                    4: "Мифриловая руда",
                    5: "Адамантиевая руда",
                },
                "ingot": {
                    1: "Медный слиток",
                    2: "Железный слиток",
                    3: "Стальной слиток",
                    4: "Мифриловый слиток",
                    5: "Адамантиевый слиток",
                },
                "wood": {
                    1: "Берёзовая древесина",
                    2: "Дубовая древесина",
                    3: "Ясеневая древесина",
                    4: "Эбеновая древесина",
                    5: "Древесина Иггдрасиля",
                },
                "leather": {
                    1: "Мягкая кожа",
                    2: "Обычная кожа",
                    3: "Плотная кожа",
                    4: "Драконья кожа",
                    5: "Небесная кожа",
                },
                "cloth": {
                    1: "Льняная ткань",
                    2: "Шёлковая ткань",
                    3: "Бархат",
                    4: "Звёздная ткань",
                    5: "Эфирная ткань",
                },
                "herb": {
                    1: "Лечебная трава",
                    2: "Целебный корень",
                    3: "Магический цветок",
                    4: "Редкое растение",
                    5: "Божественный лотос",
                },
                "gem": {
                    1: "Кварц",
                    2: "Аметист",
                    3: "Рубин",
                    4: "Изумруд",
                    5: "Алмаз",
                },
                "essence": {
                    1: "Слабая эссенция",
                    2: "Эссенция магии",
                    3: "Сильная эссенция",
                    4: "Чистая эссенция",
                    5: "Первородная эссенция",
                },
            },

            consumable_names={
                "heal_instant": "Зелье лечения",
                "heal_over_time": "Зелье регенерации",
                "mana_instant": "Зелье маны",
                "mana_over_time": "Зелье восстановления маны",
                "stamina_instant": "Зелье выносливости",
                "buff_stat": "Эликсир",
                "buff_damage": "Зелье силы",
                "buff_defense": "Зелье защиты",
            },
        )


# ==================== ГЕНЕРАТОР ИМЁН ====================

class NameGenerator:
    """
    Генератор отображаемых имён для предметов
    """

    def __init__(self, dictionary: Optional[NamingDictionary] = None):
        self.dictionary = dictionary or NamingDictionary.create_default()

    def generate_weapon_name(
        self,
        weapon_subtype: str,
        tier: int = 1,
        quality: str = "common",
        main_stat: Optional[str] = None,
        include_quality_prefix: bool = True,
        include_stat_suffix: bool = True,
    ) -> str:
        """
        Генерировать имя оружия

        Формат: [Качество] [Материал] [Тип] [суффикс]
        Пример: "Превосходный стальной меч силы"
        """
        parts = []

        # Префикс качества
        if include_quality_prefix and quality in self.dictionary.quality_prefixes:
            prefixes = self.dictionary.quality_prefixes[quality]
            if prefixes:
                parts.append(random.choice(prefixes))

        # Название материала
        material_category = self._get_weapon_material_category(weapon_subtype)
        if tier in self.dictionary.materials:
            material_name = self.dictionary.materials[tier].get(material_category, "")
            if material_name:
                parts.append(material_name)

        # Название оружия
        weapon_name = self.dictionary.weapon_names.get(weapon_subtype, weapon_subtype)
        parts.append(weapon_name)

        # Суффикс стата
        if include_stat_suffix and main_stat and main_stat in self.dictionary.stat_suffixes:
            suffixes = self.dictionary.stat_suffixes[main_stat]
            if suffixes:
                parts.append(random.choice(suffixes))

        return " ".join(parts).strip().capitalize()

    def generate_armor_name(
        self,
        equipment_type: str,
        armor_weight: str,
        tier: int = 1,
        quality: str = "common",
        main_stat: Optional[str] = None,
        include_quality_prefix: bool = True,
        include_stat_suffix: bool = True,
    ) -> str:
        """
        Генерировать имя брони

        Формат: [Качество] [Материал] [Тип] [суффикс]
        Пример: "Превосходный стальной нагрудник защиты"
        """
        parts = []

        # Префикс качества
        if include_quality_prefix and quality in self.dictionary.quality_prefixes:
            prefixes = self.dictionary.quality_prefixes[quality]
            if prefixes:
                parts.append(random.choice(prefixes))

        # Название материала
        material_category = self._get_armor_material_category(armor_weight)
        if tier in self.dictionary.materials:
            material_name = self.dictionary.materials[tier].get(material_category, "")
            if material_name:
                parts.append(material_name)

        # Название брони
        armor_name = self.dictionary.equipment_names.get(equipment_type, equipment_type)
        parts.append(armor_name)

        # Суффикс стата
        if include_stat_suffix and main_stat and main_stat in self.dictionary.stat_suffixes:
            suffixes = self.dictionary.stat_suffixes[main_stat]
            if suffixes:
                parts.append(random.choice(suffixes))

        return " ".join(parts).strip().capitalize()

    def generate_jewelry_name(
        self,
        equipment_type: str,
        tier: int = 1,
        quality: str = "common",
        main_stat: Optional[str] = None,
        include_quality_prefix: bool = True,
        include_stat_suffix: bool = True,
    ) -> str:
        """
        Генерировать имя украшения

        Формат: [Качество] [Материал] [Тип] [суффикс]
        Пример: "Легендарное алмазное кольцо мудрости"
        """
        parts = []

        # Префикс качества
        if include_quality_prefix and quality in self.dictionary.quality_prefixes:
            prefixes = self.dictionary.quality_prefixes[quality]
            if prefixes:
                parts.append(random.choice(prefixes))

        # Материал для украшений - камень
        if tier in self.dictionary.materials:
            material_name = self.dictionary.materials[tier].get("gem", "")
            if material_name:
                parts.append(material_name)

        # Название украшения
        jewelry_name = self.dictionary.equipment_names.get(equipment_type, equipment_type)
        parts.append(jewelry_name)

        # Суффикс стата
        if include_stat_suffix and main_stat and main_stat in self.dictionary.stat_suffixes:
            suffixes = self.dictionary.stat_suffixes[main_stat]
            if suffixes:
                parts.append(random.choice(suffixes))

        return " ".join(parts).strip().capitalize()

    def generate_resource_name(
        self,
        category: str,
        tier: int = 1,
    ) -> str:
        """
        Генерировать имя ресурса

        Пример: "Железная руда", "Стальной слиток"
        """
        if category in self.dictionary.resource_names:
            tier_names = self.dictionary.resource_names[category]
            if tier in tier_names:
                return tier_names[tier]

        return f"{category}_{tier}"

    def generate_consumable_name(
        self,
        effect_type: str,
        tier: int = 1,
        quality: str = "common",
    ) -> str:
        """
        Генерировать имя расходника

        Пример: "Малое зелье лечения", "Большое зелье маны"
        """
        base_name = self.dictionary.consumable_names.get(effect_type, "Зелье")

        # Префикс размера по tier
        size_prefixes = {
            1: "Малое",
            2: "Среднее",
            3: "Большое",
            4: "Мощное",
            5: "Великое",
        }

        prefix = size_prefixes.get(tier, "")
        if prefix:
            return f"{prefix} {base_name.lower()}"
        return base_name

    def _get_weapon_material_category(self, weapon_subtype: str) -> str:
        """Определить категорию материала для оружия"""
        wood_weapons = ["bow", "crossbow", "staff_melee", "staff_magic", "spear"]
        if weapon_subtype in wood_weapons:
            return "wood"
        return "metal"

    def _get_armor_material_category(self, armor_weight: str) -> str:
        """Определить категорию материала для брони"""
        material_map = {
            "cloth": "cloth",
            "light": "leather",
            "medium": "leather",
            "heavy": "metal",
        }
        return material_map.get(armor_weight, "metal")

    def generate_id_from_name(self, name: str) -> str:
        """
        Генерировать ID из имени

        "Железный меч силы" -> "iron_sword_of_power"
        """
        # Простая транслитерация и преобразование
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
            'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }

        result = []
        for char in name.lower():
            if char in translit_map:
                result.append(translit_map[char])
            elif char.isalnum():
                result.append(char)
            elif char == ' ':
                result.append('_')

        # Убираем дублирующиеся подчёркивания
        id_str = ''.join(result)
        while '__' in id_str:
            id_str = id_str.replace('__', '_')

        return id_str.strip('_')


# ==================== КОНФИГУРАЦИЯ НЕЙМИНГА ====================

@dataclass
class NamingConfig:
    """
    Полная конфигурация системы нейминга
    """
    version: str = "2.0.0"
    dictionary: NamingDictionary = field(default_factory=NamingDictionary.create_default)

    # Настройки генерации
    include_quality_prefix: bool = True
    include_stat_suffix: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "dictionary": self.dictionary.to_dict(),
            "include_quality_prefix": self.include_quality_prefix,
            "include_stat_suffix": self.include_stat_suffix,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NamingConfig":
        dictionary = NamingDictionary.from_dict(data.get("dictionary", {}))
        return cls(
            version=data.get("version", "2.0.0"),
            dictionary=dictionary,
            include_quality_prefix=data.get("include_quality_prefix", True),
            include_stat_suffix=data.get("include_stat_suffix", True),
        )

    @classmethod
    def create_default(cls) -> "NamingConfig":
        return cls(
            dictionary=NamingDictionary.create_default(),
        )
