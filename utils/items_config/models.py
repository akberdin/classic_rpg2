"""
Модели данных для Items Config Editor
Загрузка и сохранение конфигурационных файлов
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


# Пути к файлам конфигурации
def get_config_paths() -> tuple:
    """Получить пути к файлам конфигурации"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    items_data_path = os.path.join(base_path, "game", "config", "items_data.json")
    items_config_path = os.path.join(base_path, "game", "config", "items_config.json")
    crafting_config_path = os.path.join(base_path, "game", "config", "crafting_config.json")
    return items_data_path, items_config_path, crafting_config_path


# Категории предметов в items_data.json
ITEM_CATEGORIES = {
    "resources": "Ресурсы",
    "potions": "Зелья",
    "weapons": "Оружие",
    "armor": "Броня",
    "jewelry": "Украшения"
}

# Типы оружия
WEAPON_TYPES = [
    "SWORD", "AXE", "KNIFE", "SPEAR", "BOW", "STAFF", "PICKAXE", "CLUB", "WAND"
]

# Типы брони
ARMOR_TYPES = ["LIGHT", "MEDIUM", "HEAVY"]

# Слоты экипировки
EQUIPMENT_SLOTS = [
    "HEAD", "CHEST", "HANDS", "FEET", "BELT", "BACKPACK",
    "RING_1", "RING_2", "AMULET", "BRACELET_1", "BRACELET_2"
]

# Уровни качества
QUALITY_LEVELS = [
    "POOR", "COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "ARTIFACT"
]

# Типы эффектов зелий
POTION_EFFECTS = ["health", "mana", "stamina"]

# Характеристики
STATS = ["strength", "dexterity", "constitution", "spirit", "intelligence", "luck"]

# Параметры
PARAMS = ["health", "mana", "stamina"]

# Типы предметов для item_parameters
ITEM_PARAMETER_TYPES = [
    "weapon", "light_armor", "medium_armor", "heavy_armor",
    "amulet", "ring", "bracelet"
]


@dataclass
class ItemData:
    """Данные предмета"""
    item_id: str
    category: str
    name: str
    value: int = 0
    weight: float = 0.0
    quality: Optional[str] = None
    sprite: Optional[str] = None  # Путь к спрайту
    # Для оружия
    weapon_type: Optional[str] = None
    damage: Optional[int] = None
    # Для брони
    slot: Optional[str] = None
    armor_type: Optional[str] = None
    defense: Optional[int] = None
    # Для зелий
    effect_type: Optional[str] = None
    effect_value: Optional[int] = None
    # Бонусы
    stats_bonus: Dict[str, int] = field(default_factory=dict)
    param_bonus: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для JSON"""
        result = {"name": self.name}

        if self.value > 0:
            result["value"] = self.value
        if self.weight > 0:
            result["weight"] = self.weight
        if self.quality:
            result["quality"] = self.quality
        if self.sprite:
            result["sprite"] = self.sprite

        # Оружие
        if self.weapon_type:
            result["weapon_type"] = self.weapon_type
        if self.damage is not None:
            result["damage"] = self.damage

        # Броня
        if self.slot:
            result["slot"] = self.slot
        if self.armor_type:
            result["armor_type"] = self.armor_type
        if self.defense is not None:
            result["defense"] = self.defense

        # Зелья
        if self.effect_type:
            result["effect_type"] = self.effect_type
        if self.effect_value is not None:
            result["effect_value"] = self.effect_value

        # Бонусы
        if self.stats_bonus:
            result["stats_bonus"] = self.stats_bonus
        if self.param_bonus:
            result["param_bonus"] = self.param_bonus

        return result

    @classmethod
    def from_dict(cls, item_id: str, category: str, data: Dict[str, Any]) -> "ItemData":
        """Создать из словаря"""
        return cls(
            item_id=item_id,
            category=category,
            name=data.get("name", item_id),
            value=data.get("value", 0),
            weight=data.get("weight", 0.0),
            quality=data.get("quality"),
            sprite=data.get("sprite"),
            weapon_type=data.get("weapon_type"),
            damage=data.get("damage"),
            slot=data.get("slot"),
            armor_type=data.get("armor_type"),
            defense=data.get("defense"),
            effect_type=data.get("effect_type"),
            effect_value=data.get("effect_value"),
            stats_bonus=data.get("stats_bonus", {}),
            param_bonus=data.get("param_bonus", {})
        )


class ItemsDataManager:
    """Менеджер данных предметов (items_data.json)"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}

    def load(self) -> bool:
        """Загрузить данные из файла"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка загрузки {self.file_path}: {e}")
            return False

    def save(self) -> bool:
        """Сохранить данные в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка сохранения {self.file_path}: {e}")
            return False

    def has_changes(self) -> bool:
        """Проверить наличие несохранённых изменений"""
        return self.data != self._original_data

    def get_categories(self) -> List[str]:
        """Получить список категорий"""
        return [k for k in self.data.keys() if not k.startswith("_")]

    def get_items_in_category(self, category: str) -> List[ItemData]:
        """Получить список предметов в категории"""
        items = []
        if category in self.data:
            for item_id, item_data in self.data[category].items():
                if not item_id.startswith("_"):
                    items.append(ItemData.from_dict(item_id, category, item_data))
        return items

    def get_item(self, category: str, item_id: str) -> Optional[ItemData]:
        """Получить предмет по ID"""
        if category in self.data and item_id in self.data[category]:
            return ItemData.from_dict(item_id, category, self.data[category][item_id])
        return None

    def add_item(self, category: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Добавить предмет"""
        if category not in self.data:
            return False
        if item_id in self.data[category]:
            return False
        self.data[category][item_id] = item_data
        return True

    def update_item(self, category: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Обновить предмет"""
        if category not in self.data or item_id not in self.data[category]:
            return False
        self.data[category][item_id] = item_data
        return True

    def delete_item(self, category: str, item_id: str) -> bool:
        """Удалить предмет"""
        if category not in self.data or item_id not in self.data[category]:
            return False
        del self.data[category][item_id]
        return True

    def rename_item(self, category: str, old_id: str, new_id: str) -> bool:
        """Переименовать ID предмета"""
        if category not in self.data:
            return False
        if old_id not in self.data[category]:
            return False
        if new_id in self.data[category]:
            return False

        self.data[category][new_id] = self.data[category][old_id]
        del self.data[category][old_id]
        return True


class ItemsConfigManager:
    """Менеджер конфигурации предметов (items_config.json)"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}

    def load(self) -> bool:
        """Загрузить данные из файла"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка загрузки {self.file_path}: {e}")
            return False

    def save(self) -> bool:
        """Сохранить данные в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка сохранения {self.file_path}: {e}")
            return False

    def has_changes(self) -> bool:
        """Проверить наличие несохранённых изменений"""
        return self.data != self._original_data

    # Quality Levels
    def get_quality_levels(self) -> Dict[str, Any]:
        """Получить уровни качества"""
        return self.data.get("quality_levels", {})

    def update_quality_level(self, quality: str, data: Dict[str, Any]) -> bool:
        """Обновить уровень качества"""
        if "quality_levels" not in self.data:
            self.data["quality_levels"] = {}
        self.data["quality_levels"][quality] = data
        return True

    # Item Parameters
    def get_item_parameters(self) -> Dict[str, Any]:
        """Получить параметры предметов"""
        return self.data.get("item_parameters", {})

    def get_item_type_parameters(self, item_type: str) -> Dict[str, Any]:
        """Получить параметры для типа предмета"""
        return self.data.get("item_parameters", {}).get(item_type, {})

    def update_item_type_quality_params(
        self, item_type: str, quality: str, params: Dict[str, Any]
    ) -> bool:
        """Обновить параметры качества для типа предмета"""
        if "item_parameters" not in self.data:
            self.data["item_parameters"] = {}
        if item_type not in self.data["item_parameters"]:
            self.data["item_parameters"][item_type] = {}
        self.data["item_parameters"][item_type][quality] = params
        return True

    # Base Prices
    def get_base_prices(self) -> Dict[str, int]:
        """Получить базовые цены"""
        return self.data.get("base_prices", {})

    def update_base_price(self, item_type: str, price: int) -> bool:
        """Обновить базовую цену"""
        if "base_prices" not in self.data:
            self.data["base_prices"] = {}
        self.data["base_prices"][item_type] = price
        return True

    # Quality Weights
    def get_quality_weights(self) -> Dict[str, Any]:
        """Получить веса качества"""
        return self.data.get("quality_weights", {})

    def update_quality_weights(self, category: str, weights: Dict[str, float]) -> bool:
        """Обновить веса качества для категории"""
        if "quality_weights" not in self.data:
            self.data["quality_weights"] = {}
        self.data["quality_weights"][category] = weights
        return True

    # Belt/Backpack Slots
    def get_belt_slots(self) -> Dict[str, List[int]]:
        """Получить слоты поясов"""
        return self.data.get("belt_slots", {})

    def update_belt_slots(self, quality: str, slots: List[int]) -> bool:
        """Обновить слоты пояса"""
        if "belt_slots" not in self.data:
            self.data["belt_slots"] = {}
        self.data["belt_slots"][quality] = slots
        return True

    def get_backpack_slots(self) -> Dict[str, int]:
        """Получить слоты рюкзаков"""
        return self.data.get("backpack_slots", {})

    def update_backpack_slots(self, quality: str, slots: int) -> bool:
        """Обновить слоты рюкзака"""
        if "backpack_slots" not in self.data:
            self.data["backpack_slots"] = {}
        self.data["backpack_slots"][quality] = slots
        return True

    # Luck Modifiers
    def get_luck_modifiers(self) -> Dict[str, Any]:
        """Получить модификаторы удачи"""
        return self.data.get("luck_modifiers", {})

    def update_luck_modifiers(self, modifiers: Dict[str, Any]) -> bool:
        """Обновить модификаторы удачи"""
        self.data["luck_modifiers"] = modifiers
        return True

    # Weapon Filters
    def get_weapon_filters(self) -> Dict[str, Any]:
        """Получить фильтры оружия"""
        return self.data.get("weapon_filters", {})

    def update_weapon_filters(self, filters: Dict[str, Any]) -> bool:
        """Обновить фильтры оружия"""
        self.data["weapon_filters"] = filters
        return True

    # Belt Parameters
    def get_belt_parameters(self) -> Dict[str, Any]:
        """Получить параметры поясов"""
        return self.data.get("belt_parameters", {})

    def update_belt_parameters(self, params: Dict[str, Any]) -> bool:
        """Обновить параметры поясов"""
        self.data["belt_parameters"] = params
        return True

    # Talisman Parameters
    def get_talisman_parameters(self) -> Dict[str, Any]:
        """Получить параметры талисманов"""
        return self.data.get("talisman_parameters", {})

    def update_talisman_parameters(self, params: Dict[str, Any]) -> bool:
        """Обновить параметры талисманов"""
        self.data["talisman_parameters"] = params
        return True

    # Skill Bonus Config
    def get_skill_bonus_config(self) -> Dict[str, Any]:
        """Получить конфигурацию бонусов умений"""
        return self.data.get("skill_bonus_config", {})

    def update_skill_bonus_config(self, config: Dict[str, Any]) -> bool:
        """Обновить конфигурацию бонусов умений"""
        self.data["skill_bonus_config"] = config
        return True


# Станции крафта
CRAFTING_STATIONS = ["workbench", "forge", "alchemy_table", "enchanting_table"]

# Категории рецептов
RECIPE_CATEGORIES = [
    "smelting", "tool", "weapon", "armor", "jewelry", "potion", "food"
]

# Навыки крафта
CRAFTING_SKILLS = ["craftsmanship", "alchemy", "enchanting"]


@dataclass
class Recipe:
    """Рецепт крафта"""
    id: str
    name: str
    display_name: str = ""
    quality: str = "common"
    description: str = ""
    station: str = "workbench"
    result_item: str = ""
    result_quantity: int = 1
    required_level: int = 1
    required_skill: str = "craftsmanship"
    required_skill_rank: int = 1
    ingredients: List[Dict[str, Any]] = field(default_factory=list)
    category: str = "tool"
    base_price: int = 0
    sprite: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для JSON"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "quality": self.quality,
            "description": self.description,
            "station": self.station,
            "result_item": self.result_item,
            "result_quantity": self.result_quantity,
            "required_level": self.required_level,
            "required_skill": self.required_skill,
            "required_skill_rank": self.required_skill_rank,
            "ingredients": self.ingredients,
            "category": self.category,
            "base_price": self.base_price,
            "sprite": self.sprite
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recipe":
        """Создать из словаря"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            quality=data.get("quality", "common"),
            description=data.get("description", ""),
            station=data.get("station", "workbench"),
            result_item=data.get("result_item", ""),
            result_quantity=data.get("result_quantity", 1),
            required_level=data.get("required_level", 1),
            required_skill=data.get("required_skill", "craftsmanship"),
            required_skill_rank=data.get("required_skill_rank", 1),
            ingredients=data.get("ingredients", []),
            category=data.get("category", "tool"),
            base_price=data.get("base_price", 0),
            sprite=data.get("sprite")
        )


class CraftingConfigManager:
    """Менеджер конфигурации крафта (crafting_config.json)"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}

    def load(self) -> bool:
        """Загрузить данные из файла"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка загрузки {self.file_path}: {e}")
            return False

    def save(self) -> bool:
        """Сохранить данные в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self._original_data = json.loads(json.dumps(self.data))
            return True
        except Exception as e:
            print(f"Ошибка сохранения {self.file_path}: {e}")
            return False

    def has_changes(self) -> bool:
        """Проверить наличие несохранённых изменений"""
        return self.data != self._original_data

    # Станции крафта
    def get_stations(self) -> Dict[str, Any]:
        """Получить станции крафта"""
        return self.data.get("crafting_stations", {})

    def update_station(self, station_id: str, data: Dict[str, Any]) -> bool:
        """Обновить станцию крафта"""
        if "crafting_stations" not in self.data:
            self.data["crafting_stations"] = {}
        self.data["crafting_stations"][station_id] = data
        return True

    # Рецепты
    def get_recipes(self) -> List[Dict[str, Any]]:
        """Получить все рецепты"""
        return self.data.get("recipes", [])

    def get_recipes_by_station(self, station: str) -> List[Recipe]:
        """Получить рецепты по станции"""
        recipes = []
        for r in self.data.get("recipes", []):
            if r.get("station") == station:
                recipes.append(Recipe.from_dict(r))
        return recipes

    def get_recipes_by_category(self, category: str) -> List[Recipe]:
        """Получить рецепты по категории"""
        recipes = []
        for r in self.data.get("recipes", []):
            if r.get("category") == category:
                recipes.append(Recipe.from_dict(r))
        return recipes

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Recipe]:
        """Получить рецепт по ID"""
        for r in self.data.get("recipes", []):
            if r.get("id") == recipe_id:
                return Recipe.from_dict(r)
        return None

    def add_recipe(self, recipe: Recipe) -> bool:
        """Добавить рецепт"""
        if "recipes" not in self.data:
            self.data["recipes"] = []

        # Проверяем, что ID уникален
        for r in self.data["recipes"]:
            if r.get("id") == recipe.id:
                return False

        self.data["recipes"].append(recipe.to_dict())
        return True

    def update_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> bool:
        """Обновить рецепт"""
        for i, r in enumerate(self.data.get("recipes", [])):
            if r.get("id") == recipe_id:
                self.data["recipes"][i] = recipe_data
                return True
        return False

    def delete_recipe(self, recipe_id: str) -> bool:
        """Удалить рецепт"""
        recipes = self.data.get("recipes", [])
        for i, r in enumerate(recipes):
            if r.get("id") == recipe_id:
                del recipes[i]
                return True
        return False

    def get_all_recipe_ids(self) -> List[str]:
        """Получить все ID рецептов"""
        return [r.get("id", "") for r in self.data.get("recipes", [])]
