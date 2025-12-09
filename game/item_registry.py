"""
Единый реестр предметов игры.

Централизует доступ к предметам, заменяя PREDEFINED_ITEMS и ITEM_ID_TO_NAME.
Загружает данные из items_data.json и кэширует созданные объекты.
"""
import json
import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from game.inventory import (
        Item, ResourceItem, PotionItem, SkillBookItem, RecipeItem,
        WeaponItem, ArmorItem, WeaponType, ArmorType, EquipmentSlot,
        ItemQuality
    )


class ItemRegistry:
    """
    Единый реестр всех предметов игры.

    Использование:
        registry = ItemRegistry.get_instance()
        item = registry.get_item("iron_sword")
        name = registry.get_item_name("iron_sword")
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if ItemRegistry._initialized:
            return

        self._data: Dict[str, Dict] = {}
        self._item_cache: Dict[str, Any] = {}  # Item objects
        self._name_cache: Dict[str, str] = {}
        self._type_index: Dict[str, List[str]] = {}
        self._quality_index: Dict[str, List[str]] = {}

        self._load_data()
        ItemRegistry._initialized = True

    @classmethod
    def get_instance(cls) -> 'ItemRegistry':
        """Получить единственный экземпляр реестра (singleton)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Сбросить кэш (для тестов)."""
        cls._instance = None
        cls._initialized = False

    def _load_data(self):
        """Загрузить данные из items_data.json."""
        config_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'items_data.json'
        )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            print(f"[ItemRegistry] Файл не найден: {config_path}")
            return
        except json.JSONDecodeError as e:
            print(f"[ItemRegistry] Ошибка парсинга JSON: {e}")
            return

        # Обработка каждой категории
        categories = ['resources', 'potions', 'weapons', 'armor', 'skill_books', 'recipes']

        for category in categories:
            if category not in raw_data:
                continue

            for item_id, item_data in raw_data[category].items():
                if item_id.startswith('_'):  # Пропуск комментариев
                    continue

                # Добавляем категорию в данные для последующего создания
                item_data['_category'] = category
                self._data[item_id] = item_data

                # Кэшируем название
                if 'name' in item_data:
                    self._name_cache[item_id] = item_data['name']

                # Индекс по типу
                if category not in self._type_index:
                    self._type_index[category] = []
                self._type_index[category].append(item_id)

                # Индекс по качеству
                quality = item_data.get('quality', 'COMMON')
                if quality not in self._quality_index:
                    self._quality_index[quality] = []
                self._quality_index[quality].append(item_id)

    def get_item(self, item_id: str):
        """
        Получить предмет по ID.

        Args:
            item_id: Идентификатор предмета

        Returns:
            Объект предмета или None если не найден
        """
        # Проверяем кэш
        if item_id in self._item_cache:
            return self._item_cache[item_id]

        # Проверяем данные
        if item_id not in self._data:
            return None

        # Создаем предмет
        item = self._create_item(item_id, self._data[item_id])

        if item:
            self._item_cache[item_id] = item

        return item

    def get_item_name(self, item_id: str) -> Optional[str]:
        """
        Получить название предмета по ID.

        Заменяет ITEM_ID_TO_NAME из crafting_system.py.

        Args:
            item_id: Идентификатор предмета

        Returns:
            Название предмета или None если не найден
        """
        return self._name_cache.get(item_id)

    def get_items(self, item_ids: List[str]):
        """
        Получить несколько предметов одним вызовом (batch).

        Args:
            item_ids: Список идентификаторов предметов

        Returns:
            Список кортежей (item_id, item)
        """
        return [(item_id, self.get_item(item_id)) for item_id in item_ids]

    def get_items_dict(self, item_ids: List[str]):
        """
        Получить несколько предметов как словарь (batch).

        Args:
            item_ids: Список идентификаторов предметов

        Returns:
            Словарь {item_id: item}
        """
        return {item_id: self.get_item(item_id) for item_id in item_ids}

    def has_items(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Проверить существование нескольких предметов (batch).

        Args:
            item_ids: Список идентификаторов предметов

        Returns:
            Словарь {item_id: exists}
        """
        return {item_id: item_id in self._data for item_id in item_ids}

    def preload(self, item_ids: List[str] = None):
        """
        Предзагрузить предметы в кэш для ускорения последующего доступа.

        Args:
            item_ids: Список ID для предзагрузки (None = все предметы)
        """
        if item_ids is None:
            item_ids = list(self._data.keys())

        for item_id in item_ids:
            if item_id not in self._item_cache:
                self.get_item(item_id)

    def preload_common(self):
        """Предзагрузить часто используемые предметы (зелья, базовые ресурсы)."""
        common_items = [
            # Зелья
            'minor_health_potion', 'health_potion', 'greater_health_potion',
            'minor_mana_potion', 'mana_potion',
            'minor_stamina_potion', 'stamina_potion',
            # Базовые ресурсы
            'copper_ore', 'iron_ore', 'wood', 'charcoal',
            'copper_ingot', 'iron_ingot',
        ]
        self.preload(common_items)

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Получить статистику кэша.

        Returns:
            Словарь со статистикой {total_items, cached_items, cache_hit_rate}
        """
        total = len(self._data)
        cached = len(self._item_cache)
        return {
            'total_items': total,
            'cached_items': cached,
            'uncached_items': total - cached,
        }

    def clear_cache(self):
        """Очистить кэш предметов (для тестов или освобождения памяти)."""
        self._item_cache.clear()

    def get_items_by_type(self, item_type: str) -> List[str]:
        """
        Получить список ID предметов определенного типа.

        Args:
            item_type: Тип предметов (resources, potions, weapons, armor, skill_books, recipes)

        Returns:
            Список ID предметов
        """
        return self._type_index.get(item_type, [])

    def get_items_by_quality(self, quality: str) -> List[str]:
        """
        Получить список ID предметов определенного качества.

        Args:
            quality: Качество (POOR, COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, ARTIFACT)

        Returns:
            Список ID предметов
        """
        return self._quality_index.get(quality, [])

    def get_all_item_ids(self) -> List[str]:
        """Получить все ID предметов."""
        return list(self._data.keys())

    def has_item(self, item_id: str) -> bool:
        """Проверить, существует ли предмет с данным ID."""
        return item_id in self._data

    def get_item_data(self, item_id: str) -> Optional[Dict]:
        """Получить сырые данные предмета (для отладки)."""
        return self._data.get(item_id)

    def _get_quality(self, quality_str: str):
        """Преобразовать строку качества в enum."""
        from game.inventory import ItemQuality
        quality_map = {
            'POOR': ItemQuality.POOR,
            'COMMON': ItemQuality.COMMON,
            'UNCOMMON': ItemQuality.UNCOMMON,
            'RARE': ItemQuality.RARE,
            'EPIC': ItemQuality.EPIC,
            'LEGENDARY': ItemQuality.LEGENDARY,
            'ARTIFACT': ItemQuality.ARTIFACT,
        }
        return quality_map.get(quality_str, ItemQuality.COMMON)

    def _get_weapon_type(self, type_str: str):
        """Преобразовать строку типа оружия в enum."""
        from game.inventory import WeaponType
        type_map = {
            'KNIFE': WeaponType.KNIFE,
            'CLUB': WeaponType.CLUB,
            'SWORD': WeaponType.SWORD,
            'SPEAR': WeaponType.SPEAR,
            'BOW': WeaponType.BOW,
            'STAFF': WeaponType.STAFF,
            'WAND': WeaponType.WAND,
            'AXE': WeaponType.AXE,
            'PICKAXE': WeaponType.PICKAXE,
        }
        return type_map.get(type_str, WeaponType.SWORD)

    def _get_armor_type(self, type_str: str):
        """Преобразовать строку типа брони в enum."""
        from game.inventory import ArmorType
        type_map = {
            'LIGHT': ArmorType.LIGHT,
            'MEDIUM': ArmorType.MEDIUM,
            'HEAVY': ArmorType.HEAVY,
        }
        return type_map.get(type_str, ArmorType.LIGHT)

    def _get_equipment_slot(self, slot_str: str):
        """Преобразовать строку слота в enum."""
        from game.inventory import EquipmentSlot
        slot_map = {
            'WEAPON': EquipmentSlot.WEAPON,
            'HEAD': EquipmentSlot.HEAD,
            'CHEST': EquipmentSlot.CHEST,
            'HANDS': EquipmentSlot.HANDS,
            'FEET': EquipmentSlot.FEET,
            'RING_1': EquipmentSlot.RING_1,
            'RING_2': EquipmentSlot.RING_2,
            'RING_3': EquipmentSlot.RING_3,
            'RING_4': EquipmentSlot.RING_4,
            'AMULET': EquipmentSlot.AMULET,
            'BRACELET_1': EquipmentSlot.BRACELET_1,
            'BRACELET_2': EquipmentSlot.BRACELET_2,
            'BELT': EquipmentSlot.BELT,
            'BACKPACK': EquipmentSlot.BACKPACK,
        }
        return slot_map.get(slot_str, EquipmentSlot.CHEST)

    def _create_item(self, item_id: str, data: Dict):
        """
        Создать объект предмета из данных JSON.

        Args:
            item_id: Идентификатор предмета
            data: Данные предмета из JSON

        Returns:
            Объект предмета соответствующего типа
        """
        from game.inventory import (
            Item, ResourceItem, PotionItem, SkillBookItem, RecipeItem,
            WeaponItem, ArmorItem
        )
        category = data.get('_category', '')
        name = data.get('name', item_id)
        value = data.get('value', 0)
        weight = data.get('weight', 0.5)
        quality = self._get_quality(data.get('quality', 'COMMON'))

        try:
            item = None

            if category == 'resources':
                item = ResourceItem(name, value, weight, quality)

            elif category == 'potions':
                effect_type = data.get('effect_type', 'health')
                effect_value = data.get('effect_value', 50)
                item = PotionItem(name, effect_type, effect_value, value, weight, quality)

            elif category == 'weapons':
                weapon_type = self._get_weapon_type(data.get('weapon_type', 'SWORD'))
                damage = data.get('damage', 10)
                stats_bonus = data.get('stats_bonus', {})
                param_bonus = data.get('param_bonus', {})
                skill_bonus = data.get('skill_bonus', {})

                item = WeaponItem(
                    name, weapon_type, damage,
                    value=value,
                    quality=quality,
                    stats_bonus=stats_bonus,
                    param_bonus=param_bonus,
                    skill_bonus=skill_bonus
                )

            elif category == 'armor':
                slot = self._get_equipment_slot(data.get('slot', 'CHEST'))
                armor_type = self._get_armor_type(data.get('armor_type', 'LIGHT'))
                defense = data.get('defense', 1)
                stats_bonus = data.get('stats_bonus', {})
                param_bonus = data.get('param_bonus', {})
                skill_bonus = data.get('skill_bonus', {})

                item = ArmorItem(
                    name, slot, armor_type, defense,
                    value=value,
                    quality=quality,
                    stats_bonus=stats_bonus,
                    param_bonus=param_bonus,
                    skill_bonus=skill_bonus
                )

            elif category == 'skill_books':
                skill_id = data.get('skill_id', '')
                item = SkillBookItem(name, skill_id, value, 0.5, quality)

            elif category == 'recipes':
                recipe_id = data.get('recipe_id', '')
                description = data.get('description', '')
                item = RecipeItem(name, recipe_id, value, 0.1, quality, description)

            else:
                # Базовый предмет
                item = Item(name, 'misc', value, weight, quality)

            # Устанавливаем item_id для всех предметов
            if item:
                item.item_id = item_id
            return item

        except Exception as e:
            print(f"[ItemRegistry] Ошибка создания предмета {item_id}: {e}")
            return None


# Глобальные функции для удобства использования

def get_item(item_id: str):
    """Получить предмет по ID (shortcut для ItemRegistry.get_instance().get_item())."""
    return ItemRegistry.get_instance().get_item(item_id)


def get_item_name(item_id: str) -> Optional[str]:
    """Получить название предмета по ID (заменяет ITEM_ID_TO_NAME)."""
    return ItemRegistry.get_instance().get_item_name(item_id)


def get_items_by_type(item_type: str) -> List[str]:
    """Получить список ID предметов по типу."""
    return ItemRegistry.get_instance().get_items_by_type(item_type)


def has_item(item_id: str) -> bool:
    """Проверить существование предмета."""
    return ItemRegistry.get_instance().has_item(item_id)
