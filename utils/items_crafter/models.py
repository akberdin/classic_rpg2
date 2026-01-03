"""
Модели данных для Items Crafter
Определяет структуры для хранения конфигурации предметов и рецептов
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple


# ==================== ENUMS ====================

class ItemType(Enum):
    """Тип предмета"""
    RESOURCE = "resource"
    WEAPON = "weapon"
    ARMOR = "armor"
    JEWELRY = "jewelry"
    POTION = "potion"
    SKILL_BOOK = "skill_book"
    RECIPE = "recipe"
    MISC = "misc"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.RESOURCE.value: "Ресурс",
            cls.WEAPON.value: "Оружие",
            cls.ARMOR.value: "Броня",
            cls.JEWELRY.value: "Украшение",
            cls.POTION.value: "Зелье",
            cls.SKILL_BOOK.value: "Книга умений",
            cls.RECIPE.value: "Рецепт",
            cls.MISC.value: "Прочее",
        }


class ItemQuality(Enum):
    """Качество предмета"""
    POOR = "poor"
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.POOR.value: "Плохое",
            cls.COMMON.value: "Обычное",
            cls.UNCOMMON.value: "Необычное",
            cls.RARE.value: "Редкое",
            cls.EPIC.value: "Эпическое",
            cls.LEGENDARY.value: "Легендарное",
            cls.ARTIFACT.value: "Артефакт",
        }

    @classmethod
    def get_colors(cls) -> Dict[str, Tuple[int, int, int]]:
        return {
            cls.POOR.value: (128, 128, 128),
            cls.COMMON.value: (255, 255, 255),
            cls.UNCOMMON.value: (30, 255, 0),
            cls.RARE.value: (0, 112, 255),
            cls.EPIC.value: (163, 53, 238),
            cls.LEGENDARY.value: (255, 128, 0),
            cls.ARTIFACT.value: (230, 204, 128),
        }


class WeaponType(Enum):
    """Тип оружия"""
    KNIFE = "knife"
    CLUB = "club"
    SWORD = "sword"
    SPEAR = "spear"
    BOW = "bow"
    STAFF = "staff"
    WAND = "wand"
    AXE = "axe"
    PICKAXE = "pickaxe"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.KNIFE.value: "Нож",
            cls.CLUB.value: "Дубина",
            cls.SWORD.value: "Меч",
            cls.SPEAR.value: "Копьё",
            cls.BOW.value: "Лук",
            cls.STAFF.value: "Посох",
            cls.WAND.value: "Жезл",
            cls.AXE.value: "Топор",
            cls.PICKAXE.value: "Кирка",
        }

    @classmethod
    def get_multipliers(cls) -> Dict[str, float]:
        """Множители урона по типам оружия"""
        return {
            cls.KNIFE.value: 1.0,
            cls.CLUB.value: 1.2,
            cls.SWORD.value: 1.5,
            cls.SPEAR.value: 1.4,
            cls.BOW.value: 1.3,
            cls.STAFF.value: 1.1,
            cls.WAND.value: 1.0,
            cls.AXE.value: 1.4,
            cls.PICKAXE.value: 1.1,
        }

    @classmethod
    def get_tactical_ranges(cls) -> Dict[str, int]:
        """Тактический радиус по типам оружия"""
        return {
            cls.KNIFE.value: 1,
            cls.CLUB.value: 1,
            cls.SWORD.value: 1,
            cls.SPEAR.value: 2,
            cls.BOW.value: 5,
            cls.STAFF.value: 1,
            cls.WAND.value: 1,
            cls.AXE.value: 1,
            cls.PICKAXE.value: 1,
        }


class ArmorType(Enum):
    """Тип брони"""
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.LIGHT.value: "Лёгкая",
            cls.MEDIUM.value: "Средняя",
            cls.HEAVY.value: "Тяжёлая",
        }

    @classmethod
    def get_multipliers(cls) -> Dict[str, float]:
        """Множители защиты по типам брони"""
        return {
            cls.LIGHT.value: 1.0,
            cls.MEDIUM.value: 1.5,
            cls.HEAVY.value: 2.0,
        }


class EquipmentSlot(Enum):
    """Слоты экипировки"""
    WEAPON = "weapon"
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    FEET = "feet"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    RING_3 = "ring_3"
    RING_4 = "ring_4"
    AMULET = "amulet"
    BRACELET_1 = "bracelet_1"
    BRACELET_2 = "bracelet_2"
    BELT = "belt"
    BACKPACK = "backpack"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.WEAPON.value: "Оружие",
            cls.HEAD.value: "Голова",
            cls.CHEST.value: "Грудь",
            cls.HANDS.value: "Руки",
            cls.FEET.value: "Ноги",
            cls.RING_1.value: "Кольцо 1",
            cls.RING_2.value: "Кольцо 2",
            cls.RING_3.value: "Кольцо 3",
            cls.RING_4.value: "Кольцо 4",
            cls.AMULET.value: "Амулет",
            cls.BRACELET_1.value: "Браслет 1",
            cls.BRACELET_2.value: "Браслет 2",
            cls.BELT.value: "Пояс",
            cls.BACKPACK.value: "Рюкзак",
        }


class JewelryType(Enum):
    """Тип украшения"""
    RING = "ring"
    AMULET = "amulet"
    BRACELET = "bracelet"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.RING.value: "Кольцо",
            cls.AMULET.value: "Амулет",
            cls.BRACELET.value: "Браслет",
        }


class ResourceCategory(Enum):
    """Категория ресурса"""
    ORE = "ore"
    INGOT = "ingot"
    WOOD = "wood"
    HERB = "herb"
    HIDE = "hide"
    BONE = "bone"
    GEM = "gem"
    COMPONENT = "component"
    RARE = "rare"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.ORE.value: "Руда",
            cls.INGOT.value: "Слиток",
            cls.WOOD.value: "Древесина",
            cls.HERB.value: "Трава",
            cls.HIDE.value: "Шкура",
            cls.BONE.value: "Кость",
            cls.GEM.value: "Драгоценный камень",
            cls.COMPONENT.value: "Компонент",
            cls.RARE.value: "Редкий материал",
        }


class StatType(Enum):
    """Тип характеристики"""
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    SPIRIT = "spirit"
    LUCK = "luck"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.STRENGTH.value: "Сила",
            cls.DEXTERITY.value: "Ловкость",
            cls.CONSTITUTION.value: "Телосложение",
            cls.INTELLIGENCE.value: "Интеллект",
            cls.SPIRIT.value: "Дух",
            cls.LUCK.value: "Удача",
        }


class ParamType(Enum):
    """Тип параметра"""
    HEALTH = "health"
    MANA = "mana"
    STAMINA = "stamina"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.HEALTH.value: "Здоровье",
            cls.MANA.value: "Мана",
            cls.STAMINA.value: "Выносливость",
        }


class CraftingStation(Enum):
    """Станция крафта"""
    WORKBENCH = "workbench"
    FORGE = "forge"
    ALCHEMY_TABLE = "alchemy_table"
    ENCHANTING_TABLE = "enchanting_table"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.WORKBENCH.value: "Мастерская",
            cls.FORGE.value: "Кузница",
            cls.ALCHEMY_TABLE.value: "Алхимический стол",
            cls.ENCHANTING_TABLE.value: "Стол зачарования",
        }


class RecipeCategory(Enum):
    """Категория рецепта"""
    SMELTING = "smelting"
    WEAPON = "weapon"
    ARMOR = "armor"
    JEWELRY = "jewelry"
    TOOL = "tool"
    ALCHEMY = "alchemy"
    ENCHANTING = "enchanting"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.SMELTING.value: "Переплавка",
            cls.WEAPON.value: "Оружие",
            cls.ARMOR.value: "Броня",
            cls.JEWELRY.value: "Украшения",
            cls.TOOL.value: "Инструменты",
            cls.ALCHEMY.value: "Алхимия",
            cls.ENCHANTING.value: "Зачарование",
        }


class SkillType(Enum):
    """Тип навыка крафта"""
    CRAFTSMANSHIP = "craftsmanship"
    ALCHEMY = "alchemy"
    ENCHANTING = "enchanting"
    HERBALISM = "herbalism"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.CRAFTSMANSHIP.value: "Ремесло",
            cls.ALCHEMY.value: "Алхимия",
            cls.ENCHANTING.value: "Зачарование",
            cls.HERBALISM.value: "Травничество",
        }


# ==================== DATA CLASSES ====================

@dataclass
class RangeValue:
    """Диапазон значений (min-max)"""
    min_value: int = 0
    max_value: int = 0

    def to_list(self) -> List[int]:
        return [self.min_value, self.max_value]

    @classmethod
    def from_list(cls, data: Optional[List[int]]) -> Optional["RangeValue"]:
        if data is None or len(data) != 2:
            return None
        return cls(min_value=data[0], max_value=data[1])

    def __str__(self) -> str:
        return f"{self.min_value}-{self.max_value}"


@dataclass
class PriceMultipliers:
    """Множители цены предмета"""
    per_damage: float = 0.0
    per_defense: float = 0.0
    per_stat: float = 0.0
    per_param_percent: float = 0.0
    per_skill: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "per_damage": self.per_damage,
            "per_defense": self.per_defense,
            "per_stat": self.per_stat,
            "per_param_percent": self.per_param_percent,
            "per_skill": self.per_skill,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceMultipliers":
        return cls(
            per_damage=data.get("per_damage", 0.0),
            per_defense=data.get("per_defense", 0.0),
            per_stat=data.get("per_stat", 0.0),
            per_param_percent=data.get("per_param_percent", 0.0),
            per_skill=data.get("per_skill", 0.0),
        )


@dataclass
class EquipmentParametersData:
    """Параметры экипировки для определённого качества"""
    damage_range: Optional[RangeValue] = None
    defense_range: Optional[RangeValue] = None
    stats_count_range: Optional[RangeValue] = None
    params_count_range: Optional[RangeValue] = None
    skills_count_range: Optional[RangeValue] = None
    stat_bonus_range: Optional[RangeValue] = None
    stat_bonus_list: List[str] = field(default_factory=list)
    param_bonus_range: Optional[RangeValue] = None
    param_bonus_list: List[str] = field(default_factory=list)
    skill_bonus_range: Optional[RangeValue] = None
    price_multipliers: PriceMultipliers = field(default_factory=PriceMultipliers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "damage_range": self.damage_range.to_list() if self.damage_range else None,
            "defense_range": self.defense_range.to_list() if self.defense_range else None,
            "stats_count_range": self.stats_count_range.to_list() if self.stats_count_range else None,
            "params_count_range": self.params_count_range.to_list() if self.params_count_range else None,
            "skills_count_range": self.skills_count_range.to_list() if self.skills_count_range else None,
            "stat_bonus_range": self.stat_bonus_range.to_list() if self.stat_bonus_range else None,
            "stat_bonus_list": self.stat_bonus_list,
            "param_bonus_range": self.param_bonus_range.to_list() if self.param_bonus_range else None,
            "param_bonus_list": self.param_bonus_list,
            "skill_bonus_range": self.skill_bonus_range.to_list() if self.skill_bonus_range else None,
            "price_multipliers": self.price_multipliers.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquipmentParametersData":
        return cls(
            damage_range=RangeValue.from_list(data.get("damage_range")),
            defense_range=RangeValue.from_list(data.get("defense_range")),
            stats_count_range=RangeValue.from_list(data.get("stats_count_range")),
            params_count_range=RangeValue.from_list(data.get("params_count_range")),
            skills_count_range=RangeValue.from_list(data.get("skills_count_range")),
            stat_bonus_range=RangeValue.from_list(data.get("stat_bonus_range")),
            stat_bonus_list=data.get("stat_bonus_list", []),
            param_bonus_range=RangeValue.from_list(data.get("param_bonus_range")),
            param_bonus_list=data.get("param_bonus_list", []),
            skill_bonus_range=RangeValue.from_list(data.get("skill_bonus_range")),
            price_multipliers=PriceMultipliers.from_dict(data.get("price_multipliers", {})),
        )


@dataclass
class BaseItemData:
    """Базовые данные предмета"""
    item_id: str = ""
    name: str = ""
    display_name: str = ""
    description: str = ""
    item_type: str = "resource"
    quality: str = "common"
    stackable: bool = True
    max_stack: int = 99
    base_price: int = 1
    weight: float = 0.1
    sprite: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "type": self.item_type,
            "quality": self.quality,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "base_price": self.base_price,
            "weight": self.weight,
            "sprite": self.sprite,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseItemData":
        return cls(
            item_id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            item_type=data.get("type", "resource"),
            quality=data.get("quality", "common"),
            stackable=data.get("stackable", True),
            max_stack=data.get("max_stack", 99),
            base_price=data.get("base_price", 1),
            weight=data.get("weight", 0.1),
            sprite=data.get("sprite", ""),
        )


@dataclass
class ResourceItemData(BaseItemData):
    """Данные ресурса"""
    category: str = "component"
    tier: int = 1

    def __post_init__(self):
        self.item_type = "resource"
        self.stackable = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["category"] = self.category
        data["tier"] = self.tier
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceItemData":
        base = BaseItemData.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            category=data.get("category", "component"),
            tier=data.get("tier", 1),
        )


@dataclass
class WeaponItemData(BaseItemData):
    """Данные оружия"""
    weapon_type: str = "sword"
    slot: str = "weapon"
    two_handed: bool = False
    tactical_range: int = 1
    # Параметры по качеству задаются в отдельной структуре
    parameters_by_quality: Dict[str, EquipmentParametersData] = field(default_factory=dict)

    def __post_init__(self):
        self.item_type = "weapon"
        self.stackable = False
        self.max_stack = 1

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["weapon_type"] = self.weapon_type
        data["slot"] = self.slot
        data["two_handed"] = self.two_handed
        data["tactical_range"] = self.tactical_range
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeaponItemData":
        base = BaseItemData.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            weapon_type=data.get("weapon_type", "sword"),
            slot=data.get("slot", "weapon"),
            two_handed=data.get("two_handed", False),
            tactical_range=data.get("tactical_range", 1),
        )


@dataclass
class ArmorItemData(BaseItemData):
    """Данные брони"""
    armor_type: str = "light"
    slot: str = "chest"
    # Параметры по качеству
    parameters_by_quality: Dict[str, EquipmentParametersData] = field(default_factory=dict)

    def __post_init__(self):
        self.item_type = "armor"
        self.stackable = False
        self.max_stack = 1

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["armor_type"] = self.armor_type
        data["slot"] = self.slot
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmorItemData":
        base = BaseItemData.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            armor_type=data.get("armor_type", "light"),
            slot=data.get("slot", "chest"),
        )


@dataclass
class JewelryItemData(BaseItemData):
    """Данные украшения"""
    jewelry_type: str = "ring"
    slot: str = "ring_1"
    material: str = "copper"
    gem: Optional[str] = None
    # Параметры по качеству
    parameters_by_quality: Dict[str, EquipmentParametersData] = field(default_factory=dict)

    def __post_init__(self):
        self.item_type = "jewelry"
        self.stackable = False
        self.max_stack = 1

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["jewelry_type"] = self.jewelry_type
        data["slot"] = self.slot
        data["material"] = self.material
        if self.gem:
            data["gem"] = self.gem
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JewelryItemData":
        base = BaseItemData.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            jewelry_type=data.get("jewelry_type", "ring"),
            slot=data.get("slot", "ring_1"),
            material=data.get("material", "copper"),
            gem=data.get("gem"),
        )


@dataclass
class PotionEffect:
    """Эффект зелья"""
    effect_type: str = "heal"  # heal, mana, stamina, buff
    value: int = 0
    duration: int = 0  # В ходах, 0 = мгновенно
    is_percent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "value": self.value,
            "duration": self.duration,
            "is_percent": self.is_percent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PotionEffect":
        return cls(
            effect_type=data.get("effect_type", "heal"),
            value=data.get("value", 0),
            duration=data.get("duration", 0),
            is_percent=data.get("is_percent", False),
        )


@dataclass
class PotionItemData(BaseItemData):
    """Данные зелья"""
    effects: List[PotionEffect] = field(default_factory=list)
    cooldown: int = 0

    def __post_init__(self):
        self.item_type = "potion"
        self.stackable = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["effects"] = [e.to_dict() for e in self.effects]
        data["cooldown"] = self.cooldown
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PotionItemData":
        base = BaseItemData.from_dict(data)
        effects = [PotionEffect.from_dict(e) for e in data.get("effects", [])]
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            effects=effects,
            cooldown=data.get("cooldown", 0),
        )


@dataclass
class RecipeIngredient:
    """Ингредиент рецепта"""
    item_id: str = ""
    quantity: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item": self.item_id,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeIngredient":
        return cls(
            item_id=data.get("item", ""),
            quantity=data.get("quantity", 1),
        )


@dataclass
class RecipeData:
    """Данные рецепта"""
    recipe_id: str = ""
    name: str = ""
    display_name: str = ""
    description: str = ""
    quality: str = "common"
    station: str = "workbench"
    category: str = "tool"
    result_item: str = ""
    result_quantity: int = 1
    ingredients: List[RecipeIngredient] = field(default_factory=list)
    required_level: int = 1
    required_skill: str = "craftsmanship"
    required_skill_rank: int = 1
    base_price: int = 10
    sprite: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.recipe_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "quality": self.quality,
            "station": self.station,
            "category": self.category,
            "result_item": self.result_item,
            "result_quantity": self.result_quantity,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "required_level": self.required_level,
            "required_skill": self.required_skill,
            "required_skill_rank": self.required_skill_rank,
            "base_price": self.base_price,
            "sprite": self.sprite,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeData":
        ingredients = [RecipeIngredient.from_dict(i) for i in data.get("ingredients", [])]
        return cls(
            recipe_id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            quality=data.get("quality", "common"),
            station=data.get("station", "workbench"),
            category=data.get("category", "tool"),
            result_item=data.get("result_item", ""),
            result_quantity=data.get("result_quantity", 1),
            ingredients=ingredients,
            required_level=data.get("required_level", 1),
            required_skill=data.get("required_skill", "craftsmanship"),
            required_skill_rank=data.get("required_skill_rank", 1),
            base_price=data.get("base_price", 10),
            sprite=data.get("sprite"),
        )

    def validate(self) -> List[str]:
        """Валидация данных рецепта"""
        errors = []
        if not self.recipe_id:
            errors.append("ID рецепта обязателен")
        if not self.name:
            errors.append("Название рецепта обязательно")
        if not self.result_item:
            errors.append("Результат рецепта обязателен")
        if not self.ingredients:
            errors.append("Рецепт должен содержать хотя бы один ингредиент")
        if self.result_quantity < 1:
            errors.append("Количество результата должно быть >= 1")
        return errors


@dataclass
class QualityLevel:
    """Уровень качества"""
    quality_id: str = ""
    name: str = ""
    suffixes: List[str] = field(default_factory=list)
    color: Tuple[int, int, int] = (255, 255, 255)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "suffixes": self.suffixes,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, quality_id: str, data: Dict[str, Any]) -> "QualityLevel":
        color_data = data.get("color", [255, 255, 255])
        return cls(
            quality_id=quality_id,
            name=data.get("name", ""),
            suffixes=data.get("suffixes", []),
            color=tuple(color_data) if isinstance(color_data, list) else (255, 255, 255),
        )


@dataclass
class ItemsConfig:
    """Полный конфиг предметов"""
    version: str = "2.0.0"
    quality_levels: Dict[str, QualityLevel] = field(default_factory=dict)
    item_parameters: Dict[str, Dict[str, EquipmentParametersData]] = field(default_factory=dict)
    base_prices: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_description": "Конфигурация предметов - детальные параметры по уровням качества",
            "_version": self.version,
            "quality_levels": {
                k: v.to_dict() for k, v in self.quality_levels.items()
            },
            "item_parameters": {
                item_type: {
                    quality: params.to_dict()
                    for quality, params in qualities.items()
                }
                for item_type, qualities in self.item_parameters.items()
            },
            "base_prices": self.base_prices,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemsConfig":
        quality_levels = {}
        for q_id, q_data in data.get("quality_levels", {}).items():
            if not q_id.startswith("_"):
                quality_levels[q_id] = QualityLevel.from_dict(q_id, q_data)

        item_parameters = {}
        for item_type, qualities in data.get("item_parameters", {}).items():
            if not item_type.startswith("_"):
                item_parameters[item_type] = {}
                for quality, params in qualities.items():
                    item_parameters[item_type][quality] = EquipmentParametersData.from_dict(params)

        return cls(
            version=data.get("_version", "2.0.0"),
            quality_levels=quality_levels,
            item_parameters=item_parameters,
            base_prices=data.get("base_prices", {}),
        )


# ==================== PROJECT DATA ====================

@dataclass
class ItemsCrafterProject:
    """Проект Items Crafter - содержит все данные"""
    name: str = "Новый проект"
    version: str = "1.0.0"

    # Предметы по категориям
    resources: List[ResourceItemData] = field(default_factory=list)
    weapons: List[WeaponItemData] = field(default_factory=list)
    armors: List[ArmorItemData] = field(default_factory=list)
    jewelry: List[JewelryItemData] = field(default_factory=list)
    potions: List[PotionItemData] = field(default_factory=list)

    # Рецепты
    recipes: List[RecipeData] = field(default_factory=list)

    # Конфигурация параметров
    items_config: ItemsConfig = field(default_factory=ItemsConfig)

    def get_all_items(self) -> List[BaseItemData]:
        """Получить все предметы"""
        items: List[BaseItemData] = []
        items.extend(self.resources)
        items.extend(self.weapons)
        items.extend(self.armors)
        items.extend(self.jewelry)
        items.extend(self.potions)
        return items

    def get_item_by_id(self, item_id: str) -> Optional[BaseItemData]:
        """Найти предмет по ID"""
        for item in self.get_all_items():
            if item.item_id == item_id:
                return item
        return None

    def get_recipe_by_id(self, recipe_id: str) -> Optional[RecipeData]:
        """Найти рецепт по ID"""
        for recipe in self.recipes:
            if recipe.recipe_id == recipe_id:
                return recipe
        return None

    def validate(self) -> List[str]:
        """Валидация всего проекта"""
        errors = []

        # Проверка уникальности ID предметов
        item_ids = set()
        for item in self.get_all_items():
            if item.item_id in item_ids:
                errors.append(f"Дублирующийся ID предмета: {item.item_id}")
            item_ids.add(item.item_id)

        # Проверка уникальности ID рецептов
        recipe_ids = set()
        for recipe in self.recipes:
            if recipe.recipe_id in recipe_ids:
                errors.append(f"Дублирующийся ID рецепта: {recipe.recipe_id}")
            recipe_ids.add(recipe.recipe_id)

            # Проверка существования результата
            if recipe.result_item and recipe.result_item not in item_ids:
                errors.append(f"Рецепт '{recipe.name}': результат '{recipe.result_item}' не найден")

            # Проверка существования ингредиентов
            for ing in recipe.ingredients:
                if ing.item_id not in item_ids:
                    errors.append(f"Рецепт '{recipe.name}': ингредиент '{ing.item_id}' не найден")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "resources": [r.to_dict() for r in self.resources],
            "weapons": [w.to_dict() for w in self.weapons],
            "armors": [a.to_dict() for a in self.armors],
            "jewelry": [j.to_dict() for j in self.jewelry],
            "potions": [p.to_dict() for p in self.potions],
            "recipes": [r.to_dict() for r in self.recipes],
            "items_config": self.items_config.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemsCrafterProject":
        return cls(
            name=data.get("name", "Новый проект"),
            version=data.get("version", "1.0.0"),
            resources=[ResourceItemData.from_dict(r) for r in data.get("resources", [])],
            weapons=[WeaponItemData.from_dict(w) for w in data.get("weapons", [])],
            armors=[ArmorItemData.from_dict(a) for a in data.get("armors", [])],
            jewelry=[JewelryItemData.from_dict(j) for j in data.get("jewelry", [])],
            potions=[PotionItemData.from_dict(p) for p in data.get("potions", [])],
            recipes=[RecipeData.from_dict(r) for r in data.get("recipes", [])],
            items_config=ItemsConfig.from_dict(data.get("items_config", {})),
        )
