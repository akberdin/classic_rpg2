"""
Класс карты игры с генерацией биомов и локаций
"""
import random
from perlin_noise import PerlinNoise
from game.tile import Tile, Location
from game.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_BANDIT_CAMP, LOCATION_RUINS,
    PASSABLE_BIOMES
)


class GameMap:
    """Класс игровой карты"""

    def __init__(self, width=MAP_WIDTH, height=MAP_HEIGHT):
        """
        Инициализация карты

        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
        """
        self.width = width
        self.height = height
        self.tiles = []
        self.locations = []

        # Генерация карты
        self._generate_map()

    def _generate_map(self):
        """Генерация карты с биомами"""
        # Инициализация пустой карты
        self.tiles = [[Tile(x, y) for x in range(self.width)] for y in range(self.height)]

        # Параметры для шума Перлина
        scale = 100.0
        octaves = 6
        seed = random.randint(0, 10000)

        # Создаем генератор шума Перлина
        noise_generator = PerlinNoise(octaves=octaves, seed=seed)

        # Генерация биомов с помощью шума Перлина
        for y in range(self.height):
            for x in range(self.width):
                # Получаем значение шума для данной точки
                noise_val = noise_generator([x / scale, y / scale])

                # Нормализуем значение от -0.5..0.5 до 0..1
                noise_val = noise_val + 0.5

                # Определяем биом на основе значения шума
                biome = self._determine_biome(noise_val)
                self.tiles[y][x].biome = biome

        # Генерация локаций
        self._generate_locations()

    def _determine_biome(self, noise_val):
        """
        Определить биом на основе значения шума

        Args:
            noise_val: Значение шума (0..1)

        Returns:
            str: Тип биома
        """
        if noise_val < 0.3:
            return BIOME_WATER
        elif noise_val < 0.4:
            return BIOME_SAND
        elif noise_val < 0.6:
            return BIOME_PLAINS
        elif noise_val < 0.75:
            return BIOME_HILLS
        else:
            return BIOME_FOREST

    def _generate_locations(self):
        """Генерация локаций на карте"""
        location_types = [
            (LOCATION_CITY, 3, "Города"),          # 3 города
            (LOCATION_VILLAGE, 10, "Деревни"),     # 10 деревень
            (LOCATION_MINE, 8, "Шахты"),           # 8 шахт
            (LOCATION_BANDIT_CAMP, 6, "Лагеря"),   # 6 лагерей бандитов
            (LOCATION_RUINS, 12, "Руины")          # 12 руин
        ]

        for location_type, count, prefix in location_types:
            for i in range(count):
                # Ищем подходящее место для локации
                placed = False
                attempts = 0
                max_attempts = 1000

                while not placed and attempts < max_attempts:
                    x = random.randint(0, self.width - 1)
                    y = random.randint(0, self.height - 1)

                    tile = self.tiles[y][x]

                    # Проверяем, что тайл проходим и на нем нет другой локации
                    if tile.is_passable() and not tile.has_location():
                        # Создаем локацию с уникальным именем
                        name = f"{prefix} #{i + 1}"
                        location = Location(x, y, location_type, name)
                        tile.set_location(location)
                        self.locations.append(location)
                        placed = True

                    attempts += 1

    def get_tile(self, x, y):
        """
        Получить тайл по координатам

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            Tile или None
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_valid_position(self, x, y):
        """
        Проверить, находятся ли координаты в пределах карты

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если координаты валидны
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def find_spawn_point(self):
        """
        Найти подходящую точку спавна игрока

        Returns:
            tuple: (x, y) координаты точки спавна
        """
        # Ищем проходимый тайл без локаций в центре карты
        center_x = self.width // 2
        center_y = self.height // 2
        search_radius = 20

        for radius in range(0, search_radius):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy

                    if self.is_valid_position(x, y):
                        tile = self.get_tile(x, y)
                        if tile.is_passable() and not tile.has_location():
                            return (x, y)

        # Если не нашли, возвращаем центр карты
        return (center_x, center_y)
