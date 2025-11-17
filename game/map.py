"""
Класс карты игры с генерацией биомов и локаций
"""
import random
from perlin_noise import PerlinNoise
from game.tile import Tile, Location
from game.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL,
    PASSABLE_BIOMES,
    CITY_NAMES, VILLAGE_NAMES, MAGIC_SCHOOL_NAMES, MINE_NAMES, BANDIT_CAMP_NAMES, RUIN_NAMES
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
        """Генерация локаций на карте с компактным размещением"""
        # Генерация школы магов и деревень рядом с ней
        self._generate_magic_school_cluster()

        # Генерация компактных кластеров городов
        self._generate_compact_locations(LOCATION_CITY, 3, CITY_NAMES, min_distance=5, max_distance=15)

        # Генерация компактных кластеров деревень
        self._generate_compact_locations(LOCATION_VILLAGE, 8, VILLAGE_NAMES, min_distance=5, max_distance=15)

        # Генерация компактных кластеров шахт
        self._generate_compact_locations(LOCATION_MINE, 8, MINE_NAMES, min_distance=5, max_distance=15)

        # Генерация лагерей бандитов (только в лесах, на расстоянии >= 50 от городов)
        self._generate_bandit_camps()

        # Генерация руин
        self._generate_compact_locations(LOCATION_RUINS, 12, RUIN_NAMES, min_distance=5, max_distance=15)

    def _generate_magic_school_cluster(self):
        """Генерация школы магов с двумя деревнями рядом"""
        # Находим место для школы магов
        school_x, school_y = self._find_random_passable_position()
        if school_x is None:
            return

        # Создаем школу магов
        school_name = random.choice(MAGIC_SCHOOL_NAMES)
        school = Location(school_x, school_y, LOCATION_MAGIC_SCHOOL, school_name)
        self.tiles[school_y][school_x].set_location(school)
        self.locations.append(school)

        # Генерируем две деревни рядом (5-10 клеток)
        village_names_copy = VILLAGE_NAMES.copy()
        random.shuffle(village_names_copy)

        for i in range(2):
            village_pos = self._find_nearby_position(school_x, school_y, min_distance=5, max_distance=10)
            if village_pos:
                vx, vy = village_pos
                village_name = village_names_copy[i] if i < len(village_names_copy) else f"Деревня #{i+1}"
                village = Location(vx, vy, LOCATION_VILLAGE, village_name)
                self.tiles[vy][vx].set_location(village)
                self.locations.append(village)

    def _generate_compact_locations(self, location_type, count, name_list, min_distance=5, max_distance=15):
        """
        Генерация компактных кластеров локаций

        Args:
            location_type: Тип локации
            count: Количество локаций
            name_list: Список имен
            min_distance: Минимальное расстояние между локациями
            max_distance: Максимальное расстояние между локациями
        """
        names_copy = name_list.copy()
        random.shuffle(names_copy)

        for i in range(count):
            if i == 0 or len(self.locations) == 0:
                # Первая локация или если нет других локаций - размещаем случайно
                x, y = self._find_random_passable_position()
            else:
                # Последующие локации размещаем рядом с уже размещенными
                # Выбираем случайную локацию того же типа как якорь
                same_type_locations = [loc for loc in self.locations if loc.location_type == location_type]
                if same_type_locations:
                    anchor = random.choice(same_type_locations)
                    pos = self._find_nearby_position(anchor.x, anchor.y, min_distance, max_distance)
                    if pos:
                        x, y = pos
                    else:
                        x, y = self._find_random_passable_position()
                else:
                    x, y = self._find_random_passable_position()

            if x is not None:
                # Выбираем имя из списка или генерируем если список закончился
                name = names_copy[i] if i < len(names_copy) else f"{location_type} #{i+1}"
                location = Location(x, y, location_type, name)
                self.tiles[y][x].set_location(location)
                self.locations.append(location)

    def _generate_bandit_camps(self):
        """
        Генерация лагерей бандитов только в лесах и на расстоянии >= 50 клеток от городов
        """
        # Получаем список всех городов для проверки расстояния
        cities = [loc for loc in self.locations if loc.location_type == LOCATION_CITY]

        names_copy = BANDIT_CAMP_NAMES.copy()
        random.shuffle(names_copy)

        count = 6  # Количество лагерей бандитов
        created = 0
        max_attempts = 2000  # Увеличиваем количество попыток

        for attempt in range(max_attempts):
            if created >= count:
                break

            # Находим случайную позицию в лесу
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]

            # Проверяем, что это лес и там нет локации
            if tile.biome != BIOME_FOREST or tile.has_location() or not tile.is_passable():
                continue

            # Проверяем расстояние до всех городов (должно быть >= 50)
            min_distance_to_city = float('inf')
            for city in cities:
                distance = abs(x - city.x) + abs(y - city.y)
                min_distance_to_city = min(min_distance_to_city, distance)

            # Если слишком близко к городу, пропускаем
            if min_distance_to_city < 50:
                continue

            # Проверяем расстояние до других лагерей бандитов (минимум 10 клеток)
            too_close_to_other_camp = False
            for loc in self.locations:
                if loc.location_type == LOCATION_BANDIT_CAMP:
                    distance = abs(x - loc.x) + abs(y - loc.y)
                    if distance < 10:
                        too_close_to_other_camp = True
                        break

            if too_close_to_other_camp:
                continue

            # Создаем лагерь бандитов
            name = names_copy[created] if created < len(names_copy) else f"Лагерь бандитов #{created+1}"
            location = Location(x, y, LOCATION_BANDIT_CAMP, name)
            self.tiles[y][x].set_location(location)
            self.locations.append(location)
            created += 1

    def _find_random_passable_position(self):
        """Найти случайную проходимую позицию на карте"""
        max_attempts = 1000
        for _ in range(max_attempts):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]
            if tile.is_passable() and not tile.has_location():
                return x, y
        return None, None

    def _find_nearby_position(self, center_x, center_y, min_distance, max_distance):
        """
        Найти позицию рядом с указанной точкой

        Args:
            center_x: Центральная координата X
            center_y: Центральная координата Y
            min_distance: Минимальное расстояние
            max_distance: Максимальное расстояние

        Returns:
            tuple: (x, y) или None
        """
        max_attempts = 100
        for _ in range(max_attempts):
            # Генерируем случайное смещение
            distance = random.randint(min_distance, max_distance)
            angle = random.uniform(0, 2 * 3.14159)

            # Вычисляем новые координаты
            x = int(center_x + distance * random.choice([-1, 1]) * abs(random.random()))
            y = int(center_y + distance * random.choice([-1, 1]) * abs(random.random()))

            # Проверяем валидность
            if self.is_valid_position(x, y):
                tile = self.tiles[y][x]
                if tile.is_passable() and not tile.has_location():
                    # Проверяем расстояние
                    actual_distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if min_distance <= actual_distance <= max_distance:
                        return x, y
        return None

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
