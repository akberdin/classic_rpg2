"""
Класс карты игры с улучшенной процедурной генерацией биомов и локаций

Алгоритм генерации использует многослойный шум Перлина:
- Слой высоты (elevation) - определяет рельеф
- Слой влажности (moisture) - определяет тип растительности
- Градиент температуры - север холоднее, юг теплее
"""
import random
import math
from perlin_noise import PerlinNoise
from game.tile import Tile, Location
from game.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST,
    BIOME_MOUNTAIN, BIOME_SWAMP,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, LOCATION_SECRET_CAMP,
    PASSABLE_BIOMES,
    CITY_NAMES, VILLAGE_NAMES, MAGIC_SCHOOL_NAMES, WARRIOR_ACADEMY_NAMES, MINE_NAMES, BANDIT_CAMP_NAMES, RUIN_NAMES, SECRET_CAMP_NAMES
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
        """
        Улучшенная генерация карты с многослойным шумом Перлина

        Использует:
        - Шум высоты (elevation) для рельефа
        - Шум влажности (moisture) для типа растительности
        - Градиент температуры (север холоднее)
        - Постобработка для пляжей и рек
        """
        # Инициализация пустой карты
        self.tiles = [[Tile(x, y) for x in range(self.width)] for y in range(self.height)]

        # Сохраняем seed для воспроизводимости
        self.seed = random.randint(0, 10000)

        # Создаем генераторы шума для разных слоев
        elevation_noise = PerlinNoise(octaves=6, seed=self.seed)
        moisture_noise = PerlinNoise(octaves=4, seed=self.seed + 1000)
        detail_noise = PerlinNoise(octaves=8, seed=self.seed + 2000)  # Для мелких деталей

        # Параметры масштаба
        elevation_scale = 80.0   # Крупные формы рельефа
        moisture_scale = 60.0    # Зоны влажности
        detail_scale = 30.0      # Мелкие детали

        # Храним карты высот и влажности для последующей обработки
        self.elevation_map = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.moisture_map = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

        # Первый проход: генерация базовых значений
        for y in range(self.height):
            for x in range(self.width):
                # Получаем значения шума
                elevation = elevation_noise([x / elevation_scale, y / elevation_scale])
                moisture = moisture_noise([x / moisture_scale, y / moisture_scale])
                detail = detail_noise([x / detail_scale, y / detail_scale])

                # Нормализуем от [-0.5, 0.5] до [0, 1]
                elevation = elevation + 0.5
                moisture = moisture + 0.5
                detail = detail + 0.5

                # Добавляем мелкие детали к высоте (20% влияния)
                elevation = elevation * 0.8 + detail * 0.2

                # Градиент для создания континента (края карты ниже)
                edge_distance = self._get_edge_distance(x, y)
                elevation = elevation * edge_distance

                # Сохраняем значения
                self.elevation_map[y][x] = elevation
                self.moisture_map[y][x] = moisture

        # Второй проход: определение биомов
        for y in range(self.height):
            for x in range(self.width):
                elevation = self.elevation_map[y][x]
                moisture = self.moisture_map[y][x]

                # Градиент температуры (юг теплее)
                temperature = y / self.height  # 0 на севере, 1 на юге

                biome = self._determine_biome_advanced(elevation, moisture, temperature)
                self.tiles[y][x].biome = biome

        # Третий проход: постобработка - создание пляжей
        self._generate_beaches()

        # Четвертый проход: генерация рек
        self._generate_rivers()

        # Генерация локаций
        self._generate_locations()

    def _get_edge_distance(self, x, y):
        """
        Получить коэффициент расстояния от края карты
        Используется для создания острова/континента (края ниже)

        Returns:
            float: Коэффициент от 0 (край) до 1 (центр)
        """
        # Нормализованные координаты от центра
        nx = 2.0 * x / self.width - 1.0
        ny = 2.0 * y / self.height - 1.0

        # Расстояние от центра (квадратная метрика для более квадратного континента)
        d = max(abs(nx), abs(ny))

        # Плавный переход от центра к краям
        # Край начинается на расстоянии 0.7 от центра
        if d < 0.6:
            return 1.0
        elif d < 0.9:
            return 1.0 - (d - 0.6) * 2.0  # Плавное уменьшение
        else:
            return 0.1  # Минимальная высота у краев

    def _determine_biome_advanced(self, elevation, moisture, temperature):
        """
        Определить биом на основе высоты, влажности и температуры

        Логика определения биомов:
        - Очень низко (< 0.25): Вода
        - Низко (0.25-0.35) + высокая влажность: Болото
        - Низко (0.25-0.35) + низкая влажность: Песок/Пляж
        - Средне-низко (0.35-0.5): Равнины или Лес (зависит от влажности)
        - Средне (0.5-0.65): Равнины или Холмы
        - Высоко (0.65-0.8): Холмы или Лес (зависит от влажности)
        - Очень высоко (> 0.8): Горы

        Args:
            elevation: Высота (0..1)
            moisture: Влажность (0..1)
            temperature: Температура (0..1, где 0 - север/холод, 1 - юг/тепло)

        Returns:
            str: Тип биома
        """
        # Вода - очень низкие области
        if elevation < 0.25:
            return BIOME_WATER

        # Горы - очень высокие области
        if elevation > 0.8:
            return BIOME_MOUNTAIN

        # Высокие холмы
        if elevation > 0.65:
            # Лес на влажных высотах
            if moisture > 0.5:
                return BIOME_FOREST
            return BIOME_HILLS

        # Средняя высота - основная область биомов
        if elevation > 0.5:
            if moisture > 0.6:
                return BIOME_FOREST
            elif moisture > 0.35:
                return BIOME_PLAINS
            else:
                return BIOME_HILLS  # Сухие холмы

        # Низкие области
        if elevation > 0.35:
            if moisture > 0.65:
                return BIOME_FOREST  # Влажный лес
            elif moisture > 0.4:
                return BIOME_PLAINS
            else:
                return BIOME_SAND  # Сухие низины

        # Очень низкие области (0.25-0.35) - прибрежная зона
        if moisture > 0.6:
            return BIOME_SWAMP  # Болото в низких влажных местах
        else:
            return BIOME_SAND  # Песок/пляж

    def _generate_beaches(self):
        """
        Постобработка: генерация пляжей вокруг воды
        Песок должен быть на границе воды и суши
        """
        # Находим все клетки воды и создаем песок вокруг них
        water_tiles = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x].biome == BIOME_WATER:
                    water_tiles.add((x, y))

        # Для каждой клетки рядом с водой - возможно сделать песком
        beach_candidates = set()
        for wx, wy in water_tiles:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = wx + dx, wy + dy
                    if self.is_valid_position(nx, ny):
                        tile = self.tiles[ny][nx]
                        if tile.biome not in [BIOME_WATER, BIOME_MOUNTAIN]:
                            beach_candidates.add((nx, ny))

        # Превращаем часть кандидатов в песок (пляж)
        for bx, by in beach_candidates:
            # 70% шанс стать песком у воды
            if random.random() < 0.7:
                self.tiles[by][bx].biome = BIOME_SAND

    def _generate_rivers(self):
        """
        Генерация рек методом "от истока к устью"
        Реки текут из высоких точек в низкие (к воде)
        """
        num_rivers = random.randint(3, 6)

        for _ in range(num_rivers):
            # Находим исток - высокую точку (холмы или горы)
            source = self._find_river_source()
            if source is None:
                continue

            # Прокладываем реку к ближайшей воде или краю карты
            self._carve_river(source[0], source[1])

    def _find_river_source(self):
        """Найти подходящий исток реки (высокая точка)"""
        for _ in range(100):
            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)

            elevation = self.elevation_map[y][x]
            # Исток должен быть в горах или высоких холмах
            if elevation > 0.6 and self.tiles[y][x].biome in [BIOME_MOUNTAIN, BIOME_HILLS]:
                return (x, y)
        return None

    def _carve_river(self, start_x, start_y):
        """
        Прокладывание реки от истока вниз по склону
        Использует алгоритм градиентного спуска с небольшим рандомом
        """
        x, y = start_x, start_y
        river_length = 0
        max_length = 150

        while river_length < max_length:
            # Делаем текущую клетку водой
            if self.is_valid_position(x, y):
                # Не перезаписываем существующую воду или слишком ценные биомы рядом с локациями
                if self.tiles[y][x].biome != BIOME_WATER and not self.tiles[y][x].has_location():
                    self.tiles[y][x].biome = BIOME_WATER

            # Находим соседа с минимальной высотой
            best_neighbor = None
            best_elevation = self.elevation_map[y][x]

            # Проверяем соседей (с небольшим случайным смещением)
            neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            random.shuffle(neighbors)  # Добавляем рандом

            for dx, dy in neighbors:
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    neighbor_elevation = self.elevation_map[ny][nx]
                    # Небольшой шанс выбрать не самого низкого соседа (извилистость)
                    if neighbor_elevation < best_elevation or (random.random() < 0.15 and neighbor_elevation < best_elevation + 0.1):
                        best_elevation = neighbor_elevation
                        best_neighbor = (nx, ny)

            # Если не нашли путь вниз или достигли воды - останавливаемся
            if best_neighbor is None:
                break

            nx, ny = best_neighbor
            if self.tiles[ny][nx].biome == BIOME_WATER:
                # Достигли существующей воды - река влилась
                break

            x, y = nx, ny
            river_length += 1

    def _determine_biome(self, noise_val):
        """
        Устаревший метод определения биома (для обратной совместимости)
        Используйте _determine_biome_advanced для новой логики

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
        """
        Улучшенная генерация локаций с учетом рельефа и биомов

        Логика размещения:
        - Города: на равнинах, предпочтительно рядом с водой (реки)
        - Деревни: на равнинах и в лесах
        - Шахты: ТОЛЬКО в горах или холмах
        - Руины: в труднодоступных местах (холмы, болота)
        - Лагеря бандитов: в лесах
        """
        # Генерация школы магов и деревень рядом с ней
        self._generate_magic_school_cluster()

        # Генерация военной академии
        self._generate_warrior_academy_cluster()

        # Генерация городов (на равнинах, рядом с водой)
        self._generate_cities()

        # Генерация деревень (на равнинах и лесах)
        self._generate_villages()

        # Генерация шахт (в горах и холмах)
        self._generate_mines()

        # Генерация лагерей бандитов (только в лесах)
        self._generate_bandit_camps()

        # Генерация руин (в труднодоступных местах)
        self._generate_ruins()

        # Генерация Тайного лагеря
        self._generate_secret_camp()

        # Поиск и создание стартовой деревни "Тихая" (после генерации всех локаций)
        self._setup_starting_village()

    def _generate_cities(self):
        """
        Генерация городов на равнинах, предпочтительно рядом с водой
        """
        names_copy = CITY_NAMES.copy()
        random.shuffle(names_copy)
        count = 15
        created = 0

        for _ in range(2000):
            if created >= count:
                break

            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)
            tile = self.tiles[y][x]

            # Города должны быть на равнинах
            if tile.biome != BIOME_PLAINS or tile.has_location():
                continue

            # Проверяем расстояние до других локаций
            if not self._check_min_distance_to_all_locations(x, y, 8):
                continue

            # Бонус за близость к воде (реке)
            near_water = self._has_water_nearby(x, y, radius=5)

            # 80% шанс если рядом вода, 40% если нет
            if random.random() < (0.8 if near_water else 0.4):
                name = names_copy[created] if created < len(names_copy) else f"Город #{created+1}"
                location = Location(x, y, LOCATION_CITY, name)
                self.tiles[y][x].set_location(location)
                self.locations.append(location)
                created += 1

    def _generate_villages(self):
        """
        Генерация деревень на равнинах и в лесах
        """
        names_copy = VILLAGE_NAMES.copy()
        random.shuffle(names_copy)
        count = 35
        created = 0

        for _ in range(3000):
            if created >= count:
                break

            x = random.randint(3, self.width - 3)
            y = random.randint(3, self.height - 3)
            tile = self.tiles[y][x]

            # Деревни на равнинах и в лесах
            if tile.biome not in [BIOME_PLAINS, BIOME_FOREST] or tile.has_location():
                continue

            # Проверяем расстояние до других локаций
            if not self._check_min_distance_to_all_locations(x, y, 5):
                continue

            name = names_copy[created] if created < len(names_copy) else f"Деревня #{created+1}"
            location = Location(x, y, LOCATION_VILLAGE, name)
            self.tiles[y][x].set_location(location)
            self.locations.append(location)
            created += 1

    def _generate_mines(self):
        """
        Генерация шахт ТОЛЬКО в горах или холмах
        Это логично - руда добывается в горных районах
        """
        names_copy = MINE_NAMES.copy()
        random.shuffle(names_copy)
        count = 20
        created = 0

        for _ in range(3000):
            if created >= count:
                break

            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)
            tile = self.tiles[y][x]

            # Шахты ТОЛЬКО в горах или холмах - это реалистично!
            if tile.biome not in [BIOME_MOUNTAIN, BIOME_HILLS] or tile.has_location():
                continue

            # Проверяем расстояние до других локаций
            if not self._check_min_distance_to_all_locations(x, y, 6):
                continue

            name = names_copy[created] if created < len(names_copy) else f"Шахта #{created+1}"
            location = Location(x, y, LOCATION_MINE, name)
            self.tiles[y][x].set_location(location)
            self.locations.append(location)
            created += 1

    def _has_water_nearby(self, x, y, radius=5):
        """
        Проверить наличие воды в указанном радиусе

        Args:
            x, y: Центральные координаты
            radius: Радиус поиска

        Returns:
            bool: True если вода найдена
        """
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    if self.tiles[ny][nx].biome == BIOME_WATER:
                        return True
        return False

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

    def _generate_secret_camp(self):
        """
        Генерация Тайного лагеря с требованиями по расстоянию:
        - >= 20 клеток от городов, академии магов и военной академии
        - >= 15 клеток от деревень, лагерей бандитов и руин
        """
        # Получаем локации для проверки расстояний
        major_locations = [loc for loc in self.locations
                          if loc.location_type in [LOCATION_CITY, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY]]
        minor_locations = [loc for loc in self.locations
                          if loc.location_type in [LOCATION_VILLAGE, LOCATION_BANDIT_CAMP, LOCATION_RUINS]]

        names_copy = SECRET_CAMP_NAMES.copy()
        random.shuffle(names_copy)

        max_attempts = 2000

        for attempt in range(max_attempts):
            # Находим случайную позицию в лесу (Тайный лагерь скрыт в лесах)
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]

            # Проверяем, что это лес и там нет локации
            if tile.biome != BIOME_FOREST or tile.has_location() or not tile.is_passable():
                continue

            # Проверяем расстояние до крупных локаций (>= 20 клеток)
            too_close_to_major = False
            for loc in major_locations:
                distance = abs(x - loc.x) + abs(y - loc.y)
                if distance < 20:
                    too_close_to_major = True
                    break

            if too_close_to_major:
                continue

            # Проверяем расстояние до малых локаций (>= 15 клеток)
            too_close_to_minor = False
            for loc in minor_locations:
                distance = abs(x - loc.x) + abs(y - loc.y)
                if distance < 15:
                    too_close_to_minor = True
                    break

            if too_close_to_minor:
                continue

            # Создаем Тайный лагерь
            name = names_copy[0] if names_copy else "Тайный Лагерь"
            location = Location(x, y, LOCATION_SECRET_CAMP, name)
            self.tiles[y][x].set_location(location)
            self.locations.append(location)
            return

        # Если не удалось найти подходящее место, создаем в любом лесу с минимальными требованиями
        for attempt in range(max_attempts):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            tile = self.tiles[y][x]

            if tile.biome == BIOME_FOREST and not tile.has_location() and tile.is_passable():
                if self._check_min_distance_to_all_locations(x, y, 10):
                    name = names_copy[0] if names_copy else "Тайный Лагерь"
                    location = Location(x, y, LOCATION_SECRET_CAMP, name)
                    self.tiles[y][x].set_location(location)
                    self.locations.append(location)
                    return

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
