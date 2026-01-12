"""
Типы квестов и связанные константы.
"""

from enum import Enum
from game.constants import (
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL,
    LOCATION_WARRIOR_ACADEMY, LOCATION_SECRET_CAMP
)


class QuestType(str, Enum):
    """Типы квестов."""
    GATHER_RESOURCE = "gather_resource"  # Добыча ресурса
    HUNT_ANIMALS = "hunt_animals"        # Охота на животных
    DELIVER_MESSAGE = "deliver_message"  # Доставка послания
    CLEAR_LOCATION = "clear_location"    # Зачистка локации
    COLLECT_ITEMS = "collect_items"      # Сбор предметов


# Локации, которые могут выдавать квесты
QUEST_SOURCE_LOCATIONS = [
    LOCATION_CITY,
    "capital",  # Столица
    LOCATION_VILLAGE,
    LOCATION_WARRIOR_ACADEMY,
    LOCATION_MAGIC_SCHOOL,
    LOCATION_SECRET_CAMP,
]


# Допустимые типы ресурсов для gather_resource
RESOURCE_TYPES = {
    "wood": "Древесина",
    "iron_ore": "Железная руда",
    "copper_ore": "Медная руда",
    "gold_ore": "Золотая руда",
    "silver_ore": "Серебряная руда",
    "mithril_ore": "Мифриловая руда",
}

# Допустимые типы животных для hunt_animals
ANIMAL_TYPES = {
    "wolf": "Волк",
    "bear": "Медведь",
    "deer": "Олень",
}

# Допустимые типы локаций для deliver_message
DELIVERY_LOCATION_TYPES = [
    "city",
    "capital",
    "village",
    "warrior_academy",
    "magic_school",
    "secret_camp",
]

# Допустимые типы локаций для clear_location
CLEAR_LOCATION_TYPES = [
    "mine",
    "ruins",
]

# Уровни сложности
DIFFICULTY_NAMES = {
    1: "Легкий",
    2: "Нормальный",
    3: "Сложный",
    4: "Очень сложный",
    5: "Экстремальный",
}
