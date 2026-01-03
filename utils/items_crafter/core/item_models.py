"""
Модели данных предметов v2.0
Чёткая структура с поддержкой связи предмет-рецепт
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from copy import deepcopy

from .enums import (
    ItemCategory, EquipmentType, WeaponSubtype, ArmorWeight,
    ItemQuality, ResourceCategory, MaterialTier,
    StatType, DerivedStat, CraftingStation, CraftingSkill, EffectType
)


# ==================== ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ====================

@dataclass
class Range:
    """Диапазон значений min-max"""
    min_val: int = 0
    max_val: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {"min": self.min_val, "max": self.max_val}

    def to_list(self) -> List[int]:
        return [self.min_val, self.max_val]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Range":
        if isinstance(data, list):
            return cls(min_val=data[0], max_val=data[1])
        return cls(min_val=data.get("min", 0), max_val=data.get("max", 0))

    def __str__(self) -> str:
        if self.min_val == self.max_val:
            return str(self.min_val)
        return f"{self.min_val}-{self.max_val}"

    def average(self) -> float:
        return (self.min_val + self.max_val) / 2


@dataclass
class StatBonus:
    """Бонус к характеристике"""
    stat: str  # StatType или DerivedStat value
    value: int = 0
    is_percent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stat": self.stat,
            "value": self.value,
            "is_percent": self.is_percent
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatBonus":
        return cls(
            stat=data.get("stat", ""),
            value=data.get("value", 0),
            is_percent=data.get("is_percent", False)
        )

    def __str__(self) -> str:
        sign = "+" if self.value >= 0 else ""
        suffix = "%" if self.is_percent else ""
        return f"{sign}{self.value}{suffix} {self.stat}"


# ==================== БАЗОВЫЙ КЛАСС ПРЕДМЕТА ====================

@dataclass
class BaseItem:
    """
    Базовый класс для всех предметов
    Содержит общие поля для любого предмета
    """
    # Идентификация
    item_id: str = ""
    name: str = ""                      # Внутреннее имя
    display_name: str = ""              # Отображаемое имя (генерируется через naming_system)
    description: str = ""

    # Категория и качество
    category: str = ItemCategory.MISC.value
    quality: str = ItemQuality.COMMON.value

    # Параметры стака
    stackable: bool = True
    max_stack: int = 99

    # Экономика
    base_price: int = 1
    weight: float = 0.1

    # Связь с рецептом (ID рецепта, который создаёт этот предмет)
    recipe_id: Optional[str] = None

    # Визуал
    icon: str = ""
    sprite: str = ""

    # Уровень предмета (для требований)
    level: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "quality": self.quality,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "base_price": self.base_price,
            "weight": self.weight,
            "recipe_id": self.recipe_id,
            "icon": self.icon,
            "sprite": self.sprite,
            "level": self.level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseItem":
        return cls(
            item_id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            category=data.get("category", ItemCategory.MISC.value),
            quality=data.get("quality", ItemQuality.COMMON.value),
            stackable=data.get("stackable", True),
            max_stack=data.get("max_stack", 99),
            base_price=data.get("base_price", 1),
            weight=data.get("weight", 0.1),
            recipe_id=data.get("recipe_id"),
            icon=data.get("icon", ""),
            sprite=data.get("sprite", ""),
            level=data.get("level", 1),
        )

    def copy(self) -> "BaseItem":
        """Создать копию предмета"""
        return deepcopy(self)


# ==================== РЕСУРСЫ ====================

@dataclass
class ResourceItem(BaseItem):
    """
    Ресурс - материал для крафта
    """
    resource_category: str = ResourceCategory.COMPONENT.value
    tier: int = 1  # MaterialTier

    def __post_init__(self):
        self.category = ItemCategory.RESOURCE.value
        self.stackable = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "resource_category": self.resource_category,
            "tier": self.tier,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceItem":
        base = BaseItem.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            resource_category=data.get("resource_category", ResourceCategory.COMPONENT.value),
            tier=data.get("tier", 1),
        )


# ==================== ЭКИПИРОВКА ====================

@dataclass
class EquipmentItem(BaseItem):
    """
    Экипировка - надеваемый предмет
    Содержит параметры, которые определяются шаблоном + качеством
    """
    # Тип экипировки
    equipment_type: str = EquipmentType.WEAPON_MELEE_1H.value

    # Уровень материала (влияет на базовые характеристики)
    material_tier: int = 1

    # Основные боевые характеристики (заполняются из шаблона)
    damage: Optional[Range] = None
    defense: Optional[Range] = None

    # Бонусы к характеристикам
    stat_bonuses: List[StatBonus] = field(default_factory=list)

    # Требования
    required_level: int = 1
    required_stats: Dict[str, int] = field(default_factory=dict)

    # Прочность
    max_durability: int = 100

    def __post_init__(self):
        self.category = ItemCategory.EQUIPMENT.value
        self.stackable = False
        self.max_stack = 1

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "equipment_type": self.equipment_type,
            "material_tier": self.material_tier,
            "damage": self.damage.to_dict() if self.damage else None,
            "defense": self.defense.to_dict() if self.defense else None,
            "stat_bonuses": [b.to_dict() for b in self.stat_bonuses],
            "required_level": self.required_level,
            "required_stats": self.required_stats,
            "max_durability": self.max_durability,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquipmentItem":
        base = BaseItem.from_dict(data)

        damage_data = data.get("damage")
        defense_data = data.get("defense")

        return cls(
            **{k: v for k, v in base.__dict__.items()},
            equipment_type=data.get("equipment_type", EquipmentType.WEAPON_MELEE_1H.value),
            material_tier=data.get("material_tier", 1),
            damage=Range.from_dict(damage_data) if damage_data else None,
            defense=Range.from_dict(defense_data) if defense_data else None,
            stat_bonuses=[StatBonus.from_dict(b) for b in data.get("stat_bonuses", [])],
            required_level=data.get("required_level", 1),
            required_stats=data.get("required_stats", {}),
            max_durability=data.get("max_durability", 100),
        )


@dataclass
class WeaponItem(EquipmentItem):
    """
    Оружие - специализированная экипировка
    """
    weapon_subtype: str = WeaponSubtype.SWORD.value
    tactical_range: int = 1
    attack_speed: float = 1.0  # Скорость атаки (атак в секунду)

    def __post_init__(self):
        super().__post_init__()
        # Автоматически определяем тип экипировки
        try:
            subtype = WeaponSubtype(self.weapon_subtype)
            self.equipment_type = WeaponSubtype.get_equipment_type(subtype).value
            self.tactical_range = WeaponSubtype.get_tactical_range().get(self.weapon_subtype, 1)
        except ValueError:
            pass

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "weapon_subtype": self.weapon_subtype,
            "tactical_range": self.tactical_range,
            "attack_speed": self.attack_speed,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeaponItem":
        base = EquipmentItem.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            weapon_subtype=data.get("weapon_subtype", WeaponSubtype.SWORD.value),
            tactical_range=data.get("tactical_range", 1),
            attack_speed=data.get("attack_speed", 1.0),
        )


@dataclass
class ArmorItem(EquipmentItem):
    """
    Броня - защитная экипировка
    """
    armor_weight: str = ArmorWeight.LIGHT.value

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "armor_weight": self.armor_weight,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmorItem":
        base = EquipmentItem.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            armor_weight=data.get("armor_weight", ArmorWeight.LIGHT.value),
        )


@dataclass
class JewelryItem(EquipmentItem):
    """
    Украшение - аксессуар с бонусами
    """
    gem_socket: bool = False  # Есть ли слот для камня
    socketed_gem: Optional[str] = None  # ID вставленного камня

    def __post_init__(self):
        super().__post_init__()
        # Украшения не имеют урона/защиты
        self.damage = None
        self.defense = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "gem_socket": self.gem_socket,
            "socketed_gem": self.socketed_gem,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JewelryItem":
        base = EquipmentItem.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            gem_socket=data.get("gem_socket", False),
            socketed_gem=data.get("socketed_gem"),
        )


# ==================== РАСХОДНИКИ ====================

@dataclass
class ConsumableEffect:
    """Эффект расходника"""
    effect_type: str = EffectType.HEAL_INSTANT.value
    value: int = 0
    duration: int = 0  # В ходах, 0 = мгновенно
    is_percent: bool = False
    target_stat: Optional[str] = None  # Для BUFF_STAT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "value": self.value,
            "duration": self.duration,
            "is_percent": self.is_percent,
            "target_stat": self.target_stat,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsumableEffect":
        return cls(
            effect_type=data.get("effect_type", EffectType.HEAL_INSTANT.value),
            value=data.get("value", 0),
            duration=data.get("duration", 0),
            is_percent=data.get("is_percent", False),
            target_stat=data.get("target_stat"),
        )


@dataclass
class ConsumableItem(BaseItem):
    """
    Расходник - используемый предмет (зелья, свитки, еда)
    """
    effects: List[ConsumableEffect] = field(default_factory=list)
    cooldown: int = 0  # Время перезарядки в ходах
    charges: int = 1   # Количество использований

    def __post_init__(self):
        self.category = ItemCategory.CONSUMABLE.value
        self.stackable = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "effects": [e.to_dict() for e in self.effects],
            "cooldown": self.cooldown,
            "charges": self.charges,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsumableItem":
        base = BaseItem.from_dict(data)
        return cls(
            **{k: v for k, v in base.__dict__.items()},
            effects=[ConsumableEffect.from_dict(e) for e in data.get("effects", [])],
            cooldown=data.get("cooldown", 0),
            charges=data.get("charges", 1),
        )


# ==================== РЕЦЕПТЫ ====================

@dataclass
class RecipeIngredient:
    """Ингредиент рецепта"""
    item_id: str = ""
    quantity: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeIngredient":
        return cls(
            item_id=data.get("item_id", data.get("item", "")),
            quantity=data.get("quantity", 1),
        )


@dataclass
class Recipe:
    """
    Рецепт крафта
    Связан с предметом-результатом через result_item_id
    """
    recipe_id: str = ""
    name: str = ""
    display_name: str = ""
    description: str = ""

    # Результат
    result_item_id: str = ""  # ID создаваемого предмета
    result_quantity: int = 1
    result_quality: str = ItemQuality.COMMON.value  # Качество результата

    # Ингредиенты
    ingredients: List[RecipeIngredient] = field(default_factory=list)

    # Требования
    station: str = CraftingStation.WORKBENCH.value
    required_skill: str = CraftingSkill.SMITHING.value
    required_skill_level: int = 1
    required_player_level: int = 1

    # Параметры крафта
    craft_time: float = 1.0  # Время крафта в секундах
    experience_gain: int = 10  # Опыт за крафт

    # Метаданные
    is_unlocked_by_default: bool = True
    unlock_item_id: Optional[str] = None  # ID предмета для разблокировки

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.recipe_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "result_item_id": self.result_item_id,
            "result_quantity": self.result_quantity,
            "result_quality": self.result_quality,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "station": self.station,
            "required_skill": self.required_skill,
            "required_skill_level": self.required_skill_level,
            "required_player_level": self.required_player_level,
            "craft_time": self.craft_time,
            "experience_gain": self.experience_gain,
            "is_unlocked_by_default": self.is_unlocked_by_default,
            "unlock_item_id": self.unlock_item_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recipe":
        return cls(
            recipe_id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            result_item_id=data.get("result_item_id", data.get("result_item", "")),
            result_quantity=data.get("result_quantity", 1),
            result_quality=data.get("result_quality", ItemQuality.COMMON.value),
            ingredients=[RecipeIngredient.from_dict(i) for i in data.get("ingredients", [])],
            station=data.get("station", CraftingStation.WORKBENCH.value),
            required_skill=data.get("required_skill", CraftingSkill.SMITHING.value),
            required_skill_level=data.get("required_skill_level", data.get("required_skill_rank", 1)),
            required_player_level=data.get("required_player_level", data.get("required_level", 1)),
            craft_time=data.get("craft_time", 1.0),
            experience_gain=data.get("experience_gain", 10),
            is_unlocked_by_default=data.get("is_unlocked_by_default", True),
            unlock_item_id=data.get("unlock_item_id"),
        )

    def validate(self, all_items: Dict[str, BaseItem]) -> List[str]:
        """Валидация рецепта"""
        errors = []

        if not self.recipe_id:
            errors.append("ID рецепта обязателен")

        if not self.name:
            errors.append("Название рецепта обязательно")

        if not self.result_item_id:
            errors.append("Результат рецепта обязателен")
        elif self.result_item_id not in all_items:
            errors.append(f"Предмет-результат '{self.result_item_id}' не найден")

        if not self.ingredients:
            errors.append("Рецепт должен содержать хотя бы один ингредиент")
        else:
            for ing in self.ingredients:
                if ing.item_id not in all_items:
                    errors.append(f"Ингредиент '{ing.item_id}' не найден")
                if ing.quantity < 1:
                    errors.append(f"Количество ингредиента '{ing.item_id}' должно быть >= 1")

        if self.result_quantity < 1:
            errors.append("Количество результата должно быть >= 1")

        return errors

    def copy(self) -> "Recipe":
        """Создать копию рецепта"""
        return deepcopy(self)


# ==================== ПРОЕКТ ====================

@dataclass
class ItemsProject:
    """
    Проект системы предметов v2.0
    Содержит все предметы и рецепты с двусторонней связью
    """
    name: str = "Новый проект"
    version: str = "2.0.0"

    # Предметы по типам
    resources: List[ResourceItem] = field(default_factory=list)
    weapons: List[WeaponItem] = field(default_factory=list)
    armor: List[ArmorItem] = field(default_factory=list)
    jewelry: List[JewelryItem] = field(default_factory=list)
    consumables: List[ConsumableItem] = field(default_factory=list)

    # Рецепты
    recipes: List[Recipe] = field(default_factory=list)

    def get_all_items(self) -> List[BaseItem]:
        """Получить все предметы"""
        items: List[BaseItem] = []
        items.extend(self.resources)
        items.extend(self.weapons)
        items.extend(self.armor)
        items.extend(self.jewelry)
        items.extend(self.consumables)
        return items

    def get_items_dict(self) -> Dict[str, BaseItem]:
        """Получить словарь предметов по ID"""
        return {item.item_id: item for item in self.get_all_items()}

    def get_item_by_id(self, item_id: str) -> Optional[BaseItem]:
        """Найти предмет по ID"""
        for item in self.get_all_items():
            if item.item_id == item_id:
                return item
        return None

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Recipe]:
        """Найти рецепт по ID"""
        for recipe in self.recipes:
            if recipe.recipe_id == recipe_id:
                return recipe
        return None

    def get_recipe_for_item(self, item_id: str) -> Optional[Recipe]:
        """Найти рецепт, создающий данный предмет"""
        for recipe in self.recipes:
            if recipe.result_item_id == item_id:
                return recipe
        return None

    def get_recipes_using_item(self, item_id: str) -> List[Recipe]:
        """Найти рецепты, использующие данный предмет как ингредиент"""
        result = []
        for recipe in self.recipes:
            for ing in recipe.ingredients:
                if ing.item_id == item_id:
                    result.append(recipe)
                    break
        return result

    def link_item_to_recipe(self, item_id: str, recipe_id: str):
        """Связать предмет с рецептом"""
        item = self.get_item_by_id(item_id)
        if item:
            item.recipe_id = recipe_id

    def validate(self) -> List[str]:
        """Валидация всего проекта"""
        errors = []
        items_dict = self.get_items_dict()

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

            # Валидация рецепта
            errors.extend(recipe.validate(items_dict))

        # Проверка связей предмет-рецепт
        for item in self.get_all_items():
            if item.recipe_id:
                if item.recipe_id not in recipe_ids:
                    errors.append(f"Предмет '{item.item_id}' ссылается на несуществующий рецепт '{item.recipe_id}'")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "resources": [r.to_dict() for r in self.resources],
            "weapons": [w.to_dict() for w in self.weapons],
            "armor": [a.to_dict() for a in self.armor],
            "jewelry": [j.to_dict() for j in self.jewelry],
            "consumables": [c.to_dict() for c in self.consumables],
            "recipes": [r.to_dict() for r in self.recipes],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemsProject":
        return cls(
            name=data.get("name", "Новый проект"),
            version=data.get("version", "2.0.0"),
            resources=[ResourceItem.from_dict(r) for r in data.get("resources", [])],
            weapons=[WeaponItem.from_dict(w) for w in data.get("weapons", [])],
            armor=[ArmorItem.from_dict(a) for a in data.get("armor", [])],
            jewelry=[JewelryItem.from_dict(j) for j in data.get("jewelry", [])],
            consumables=[ConsumableItem.from_dict(c) for c in data.get("consumables", [])],
            recipes=[Recipe.from_dict(r) for r in data.get("recipes", [])],
        )
