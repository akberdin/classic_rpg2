"""
Классы для тайлов и локаций на карте
"""
from game.constants import (
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL,
    PASSABLE_BIOMES
)


class Tile:
    """Класс для одного тайла на карте"""

    def __init__(self, x, y, biome=BIOME_PLAINS):
        """
        Инициализация тайла

        Args:
            x: Координата X
            y: Координата Y
            biome: Тип биома
        """
        self.x = x
        self.y = y
        self.biome = biome
        self.location = None  # Объект на этом тайле (город, деревня и т.д.)
        self.explored = False  # Был ли тайл исследован (для тумана войны)

    def is_passable(self):
        """
        Проверить, можно ли пройти через этот тайл

        Returns:
            bool: True если тайл проходим
        """
        return self.biome in PASSABLE_BIOMES

    def set_location(self, location):
        """
        Установить локацию на этом тайле

        Args:
            location: Объект Location
        """
        self.location = location

    def has_location(self):
        """Проверить, есть ли локация на этом тайле"""
        return self.location is not None


class Location:
    """Класс для локаций (города, деревни, шахты и т.д.)"""

    def __init__(self, x, y, location_type, name=None):
        """
        Инициализация локации

        Args:
            x: Координата X
            y: Координата Y
            location_type: Тип локации
            name: Название локации
        """
        self.x = x
        self.y = y
        self.location_type = location_type
        self.name = name or self._generate_default_name()

    def _generate_default_name(self):
        """Генерация названия по умолчанию"""
        names = {
            LOCATION_CITY: "Город",
            LOCATION_VILLAGE: "Деревня",
            LOCATION_MINE: "Шахта",
            LOCATION_BANDIT_CAMP: "Лагерь бандитов",
            LOCATION_RUINS: "Руины",
            LOCATION_MAGIC_SCHOOL: "Школа магов"
        }
        return names.get(self.location_type, "Неизвестное место")

    def get_description(self):
        """Получить описание локации"""
        descriptions = {
            LOCATION_CITY: "Большой процветающий город с множеством торговцев и жителей",
            LOCATION_VILLAGE: "Небольшая деревня с простыми домами",
            LOCATION_MINE: "Заброшенная шахта, говорят там водятся монстры",
            LOCATION_BANDIT_CAMP: "Лагерь опасных бандитов",
            LOCATION_RUINS: "Древние руины, полные тайн и сокровищ",
            LOCATION_MAGIC_SCHOOL: "Школа магов, где обучают искусству волшебства"
        }
        return descriptions.get(self.location_type, "Неизвестное место")
