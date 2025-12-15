"""
Класс карты игры с генерацией биомов и локаций
"""
import random
from perlin_noise import PerlinNoise
from game.tile import Tile, Location
from game.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY,
    PASSABLE_BIOMES,
    CITY_NAMES, VILLAGE_NAMES, MAGIC_SCHOOL_NAMES, WARRIOR_ACADEMY_NAMES, MINE_NAMES, BANDIT_CAMP_NAMES, RUIN_NAMES
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
        self.starting_village = None  # Стартовая деревня "Тихая"

        # Генерация карты с проверкой на успешность размещения стартовой деревни
        self._generate_map_with_starting_village()

    def _generate_map_with_starting_village(self, max_attempts=10):
        """
        Генерация карты с гарантированным размещением стартовой деревни "Тихая"

        При невозможности найти подходящее место для деревни - перегенерирует карту

        Args:
            max_attempts: Максимальное количество попыток перегенерации карты
        """
        for attempt in range(max_attempts):
            # Сбрасываем данные для новой генерации
            self.tiles = []
            self.locations = []
            self.starting_village = None

            # Генерируем карту
            self._generate_map()

            # Проверяем, создана ли стартовая деревня
            if self.starting_village is not None:
                return  # Успешная генерация

            # Если не создана, пробуем снова
            if attempt < max_attempts - 1:
                print(f"Попытка {attempt + 1}: не удалось найти место для деревни 'Тихая', перегенерация карты...")

        # Если после всех попыток не удалось - создаём деревню в случайном безопасном месте
        print("Предупреждение: не удалось найти идеальное место для деревни 'Тихая', создаём в ближайшем подходящем месте")
        self._create_fallback_starting_village()

    def _create_fallback_starting_village(self):
        """Создание стартовой деревни в запасном месте (если не удалось найти идеальное)"""
        # Ищем любое место подальше от опасных локаций
        for _ in range(1000):
            x, y = self._find_random_passable_position()
            if x is None:
                continue

            # Проверяем расстояние до опасных локаций (хотя бы 15 клеток)
            safe = True
            for loc in self.locations:
                if loc.location_type in [LOCATION_BANDIT_CAMP, LOCATION_RUINS]:
                    distance = abs(x - loc.x) + abs(y - loc.y)
                    if distance < 15:
                        safe = False
                        break

            if safe and self._check_min_distance_to_all_locations(x, y, 3):
                village = Location(x, y, LOCATION_VILLAGE, "Тихая")
                self.tiles[y][x].set_location(village)
                self.locations.append(village)
                self.starting_village = village
                return

    def _generate_map(self):
        """Генерация карты с биомами"""
        # Инициализация пустой карты
        self.tiles = [[Tile(x, y) for x in range(self.width)] for y in range(self.height)]

        # Параметры для шума Перлина
        scale = 100.0
        octaves = 6
        self.seed = random.randint(0, 10000)  # Сохраняем seed для воспроизводимости

        # Создаем генератор шума Перлина
        noise_generator = PerlinNoise(octaves=octaves, seed=self.seed)

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

        # Генерация военной академии
        self._generate_warrior_academy_cluster()

        # Генерация компактных кластеров городов (увеличено с 10 до 15)
        self._generate_compact_locations(LOCATION_CITY, 15, CITY_NAMES, min_distance=5, max_distance=15)

        # Генерация компактных кластеров деревень (увеличено с 25 до 35)
        self._generate_compact_locations(LOCATION_VILLAGE, 35, VILLAGE_NAMES, min_distance=5, max_distance=15)

        # Генерация компактных кластеров шахт (увеличено с 15 до 20)
        self._generate_compact_locations(LOCATION_MINE, 20, MINE_NAMES, min_distance=5, max_distance=15)

        # Генерация лагерей бандитов (только в лесах, на расстоянии >= 50 от городов)
        self._generate_bandit_camps()

        # Генерация руин (увеличено до 40, на расстоянии >= 15 от городов и деревень)
        self._generate_ruins()

        # Поиск и создание стартовой деревни "Тихая" (после генерации всех локаций)
        self._setup_starting_village()

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

    def _generate_warrior_academy_cluster(self):
        """Генерация военной академии на расстоянии >= 20 клеток от руин и лагерей бандитов"""
        max_attempts = 1000

        for attempt in range(max_attempts):
            # Находим случайную позицию
            academy_x, academy_y = self._find_random_passable_position()
            if academy_x is None:
                continue

            # Проверяем расстояние до руин и лагерей бандитов
            min_distance_to_dangerous = float('inf')
            for loc in self.locations:
                if loc.location_type in [LOCATION_RUINS, LOCATION_BANDIT_CAMP]:
                    distance = abs(academy_x - loc.x) + abs(academy_y - loc.y)
                    min_distance_to_dangerous = min(min_distance_to_dangerous, distance)

            # Если слишком близко к опасной зоне, пробуем другую позицию
            if min_distance_to_dangerous < 20:
                continue

            # Создаем военную академию
            academy_name = random.choice(WARRIOR_ACADEMY_NAMES)
            academy = Location(academy_x, academy_y, LOCATION_WARRIOR_ACADEMY, academy_name)
            self.tiles[academy_y][academy_x].set_location(academy)
            self.locations.append(academy)
            return

        # Если не удалось найти подходящее место, создаем в случайном месте
        academy_x, academy_y = self._find_random_passable_position()
        if academy_x is not None:
            academy_name = random.choice(WARRIOR_ACADEMY_NAMES)
            academy = Location(academy_x, academy_y, LOCATION_WARRIOR_ACADEMY, academy_name)
            self.tiles[academy_y][academy_x].set_location(academy)
            self.locations.append(academy)

    def _generate_compact_locations(self, location_type, count, name_list, min_distance=5, max_distance=15):
        """
        Генерация локаций с равномерным распределением по карте

        Args:
            location_type: Тип локации
            count: Количество локаций
            name_list: Список имен
            min_distance: Минимальное расстояние между локациями одного типа
            max_distance: Максимальное расстояние при поиске позиции рядом с якорем
        """
        names_copy = name_list.copy()
        random.shuffle(names_copy)

        # Минимальное расстояние до любой другой локации
        min_distance_to_any = max(3, min_distance // 2)

        for i in range(count):
            x, y = None, None

            # Пробуем несколько стратегий размещения
            for attempt in range(50):
                if attempt < 25:
                    # Первые попытки - случайное размещение по всей карте
                    candidate_x, candidate_y = self._find_random_passable_position()
                else:
                    # Если не получается - пробуем рядом с существующими локациями того же типа
                    same_type_locations = [loc for loc in self.locations if loc.location_type == location_type]
                    if same_type_locations:
                        anchor = random.choice(same_type_locations)
                        pos = self._find_nearby_position(anchor.x, anchor.y, min_distance, max_distance, check_all_locations=False)
                        if pos:
                            candidate_x, candidate_y = pos
                        else:
                            continue
                    else:
                        continue

                if candidate_x is None:
                    continue

                # Проверяем минимальное расстояние до всех существующих локаций
                if self._check_min_distance_to_all_locations(candidate_x, candidate_y, min_distance_to_any):
                    x, y = candidate_x, candidate_y
                    break

            if x is not None:
                # Выбираем имя из списка или генерируем если список закончился
                name = names_copy[i] if i < len(names_copy) else f"{location_type} #{i+1}"
                location = Location(x, y, location_type, name)
                self.tiles[y][x].set_location(location)
                self.locations.append(location)

    def _check_min_distance_to_all_locations(self, x, y, min_distance):
        """
        Проверить, что позиция находится на минимальном расстоянии от всех существующих локаций

        Args:
            x: Координата X
            y: Координата Y
            min_distance: Минимальное расстояние

        Returns:
            bool: True если расстояние достаточное
        """
        for loc in self.locations:
            distance = abs(x - loc.x) + abs(y - loc.y)
            if distance < min_distance:
                return False
        return True

    def _generate_bandit_camps(self):
        """
        Генерация лагерей бандитов только в лесах и на расстоянии >= 15 клеток от городов и деревень
        """
        # Получаем список всех городов и деревень для проверки расстояния
        settlements = [loc for loc in self.locations if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        names_copy = BANDIT_CAMP_NAMES.copy()
        random.shuffle(names_copy)

        count = 15  # Количество лагерей бандитов (увеличено с 10 до 15)
        created = 0
        max_attempts = 5000  # Увеличиваем количество попыток для размещения большего количества лагерей

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

            # Проверяем расстояние до всех городов и деревень (должно быть >= 15)
            min_distance_to_settlement = float('inf')
            for settlement in settlements:
                distance = abs(x - settlement.x) + abs(y - settlement.y)
                min_distance_to_settlement = min(min_distance_to_settlement, distance)

            # Если слишком близко к городу или деревне, пропускаем
            if min_distance_to_settlement < 15:
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

    def _generate_ruins(self):
        """
        Генерация руин на расстоянии >= 15 клеток от городов и деревень
        """
        # Получаем список всех городов и деревень для проверки расстояния
        settlements = [loc for loc in self.locations if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        names_copy = RUIN_NAMES.copy()
        random.shuffle(names_copy)

        count = 40  # Количество руин
        created = 0
        max_attempts = 5000

        for attempt in range(max_attempts):
            if created >= count:
                break

            # Находим случайную проходимую позицию
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]

            # Проверяем, что там нет локации и клетка проходима
            if tile.has_location() or not tile.is_passable():
                continue

            # Проверяем расстояние до всех городов и деревень (должно быть >= 15)
            min_distance_to_settlement = float('inf')
            for settlement in settlements:
                distance = abs(x - settlement.x) + abs(y - settlement.y)
                min_distance_to_settlement = min(min_distance_to_settlement, distance)

            # Если слишком близко к городу или деревне, пропускаем
            if min_distance_to_settlement < 15:
                continue

            # Проверяем расстояние до других руин (минимум 10 клеток)
            too_close_to_other_ruin = False
            for loc in self.locations:
                if loc.location_type == LOCATION_RUINS:
                    distance = abs(x - loc.x) + abs(y - loc.y)
                    if distance < 10:
                        too_close_to_other_ruin = True
                        break

            if too_close_to_other_ruin:
                continue

            # Создаем руины
            name = names_copy[created] if created < len(names_copy) else f"Руины #{created+1}"
            location = Location(x, y, LOCATION_RUINS, name)
            self.tiles[y][x].set_location(location)
            self.locations.append(location)
            created += 1

    def _setup_starting_village(self):
        """
        Поиск и создание стартовой деревни "Тихая" после генерации всех локаций

        Условия размещения:
        - Рядом (3-5 клеток) должен быть лес (биом)
        - Рядом (3-5 клеток) должна быть шахта (локация)
        - В радиусе 20 клеток не должно быть лагерей бандитов и руин
        """
        position = self._find_tikhaya_village_position()
        if position:
            x, y = position
            village = Location(x, y, LOCATION_VILLAGE, "Тихая")
            self.tiles[y][x].set_location(village)
            self.locations.append(village)
            self.starting_village = village

    def _find_tikhaya_village_position(self):
        """
        Найти подходящее место для деревни "Тихая"

        Условия:
        - Рядом (3-5 клеток) есть лес (биом BIOME_FOREST)
        - Рядом (3-5 клеток) есть шахта (LOCATION_MINE)
        - В радиусе 20 клеток нет лагерей бандитов и руин
        - Минимальное расстояние до других локаций (3 клетки)

        Returns:
            tuple: (x, y) или None если не найдено
        """
        # Получаем все шахты для проверки близости
        mines = [loc for loc in self.locations if loc.location_type == LOCATION_MINE]
        if not mines:
            return None

        # Получаем опасные локации для проверки расстояния
        dangerous_locations = [loc for loc in self.locations
                               if loc.location_type in [LOCATION_BANDIT_CAMP, LOCATION_RUINS]]

        max_attempts = 2000
        for _ in range(max_attempts):
            # Находим случайную проходимую позицию
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]

            # Проверяем, что тайл проходим и свободен
            if not tile.is_passable() or tile.has_location():
                continue

            # Проверяем минимальное расстояние до других локаций
            if not self._check_min_distance_to_all_locations(x, y, 3):
                continue

            # Проверяем наличие леса рядом (3-5 клеток)
            has_forest_nearby = self._check_biome_nearby(x, y, BIOME_FOREST, min_dist=3, max_dist=5)
            if not has_forest_nearby:
                continue

            # Проверяем наличие шахты рядом (3-5 клеток)
            has_mine_nearby = self._check_location_nearby(x, y, mines, min_dist=3, max_dist=5)
            if not has_mine_nearby:
                continue

            # Проверяем расстояние до опасных локаций (>= 20 клеток)
            safe_from_danger = True
            for loc in dangerous_locations:
                distance = abs(x - loc.x) + abs(y - loc.y)
                if distance < 20:
                    safe_from_danger = False
                    break

            if not safe_from_danger:
                continue

            # Все условия выполнены - возвращаем позицию
            return (x, y)

        return None

    def _check_biome_nearby(self, x, y, biome_type, min_dist, max_dist):
        """
        Проверить наличие указанного биома в заданном радиусе

        Args:
            x, y: Центральные координаты
            biome_type: Тип биома для поиска
            min_dist: Минимальное расстояние
            max_dist: Максимальное расстояние

        Returns:
            bool: True если биом найден в заданном радиусе
        """
        for dx in range(-max_dist, max_dist + 1):
            for dy in range(-max_dist, max_dist + 1):
                check_x = x + dx
                check_y = y + dy

                if not self.is_valid_position(check_x, check_y):
                    continue

                # Вычисляем евклидово расстояние
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if min_dist <= distance <= max_dist:
                    if self.tiles[check_y][check_x].biome == biome_type:
                        return True
        return False

    def _check_location_nearby(self, x, y, locations, min_dist, max_dist):
        """
        Проверить наличие локации из списка в заданном радиусе

        Args:
            x, y: Центральные координаты
            locations: Список локаций для проверки
            min_dist: Минимальное расстояние
            max_dist: Максимальное расстояние

        Returns:
            bool: True если локация найдена в заданном радиусе
        """
        for loc in locations:
            # Используем евклидово расстояние
            distance = ((x - loc.x) ** 2 + (y - loc.y) ** 2) ** 0.5
            if min_dist <= distance <= max_dist:
                return True
        return False

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

    def _find_nearby_position(self, center_x, center_y, min_distance, max_distance, check_all_locations=True):
        """
        Найти позицию рядом с указанной точкой

        Args:
            center_x: Центральная координата X
            center_y: Центральная координата Y
            min_distance: Минимальное расстояние от центра
            max_distance: Максимальное расстояние от центра
            check_all_locations: Проверять ли расстояние до всех существующих локаций

        Returns:
            tuple: (x, y) или None
        """
        max_attempts = 100
        min_distance_to_any = 3  # Минимальное расстояние до любой локации

        for _ in range(max_attempts):
            # Генерируем случайное смещение
            distance = random.randint(min_distance, max_distance)

            # Вычисляем новые координаты
            angle = random.random() * 2 * 3.14159  # Случайный угол
            x = int(center_x + distance * (random.random() * 2 - 1))
            y = int(center_y + distance * (random.random() * 2 - 1))

            # Проверяем валидность
            if self.is_valid_position(x, y):
                tile = self.tiles[y][x]
                if tile.is_passable() and not tile.has_location():
                    # Проверяем расстояние от центра
                    actual_distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    if min_distance <= actual_distance <= max_distance:
                        # Проверяем расстояние до всех локаций, если требуется
                        if check_all_locations:
                            if self._check_min_distance_to_all_locations(x, y, min_distance_to_any):
                                return x, y
                        else:
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
        Найти подходящую точку спавна игрока в стартовой деревне "Тихая"

        Returns:
            tuple: (x, y) координаты точки спавна
        """
        # Приоритет - стартовая деревня "Тихая"
        if self.starting_village is not None:
            settlement = self.starting_village
        else:
            # Запасной вариант - ищем все города и деревни
            settlements = [loc for loc in self.locations
                          if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

            if not settlements:
                # Если нет поселений, спавним в центре карты
                center_x = self.width // 2
                center_y = self.height // 2
                return (center_x, center_y)

            # Выбираем случайное поселение
            settlement = random.choice(settlements)

        # Ищем проходимое место рядом с поселением (в радиусе 3-7 клеток)
        search_radius = 7
        for radius in range(3, search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = settlement.x + dx
                    y = settlement.y + dy

                    if self.is_valid_position(x, y):
                        tile = self.get_tile(x, y)
                        if tile.is_passable() and not tile.has_location():
                            return (x, y)

        # Если не нашли рядом с поселением, возвращаем координаты поселения
        return (settlement.x, settlement.y)
