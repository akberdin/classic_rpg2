"""
Процедурный генератор подземелий и шахт
"""
import random
from typing import List, Tuple, Optional

from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.tiles import DungeonTileType
from game.dungeon.traps import Trap, TrapType
from game.dungeon.stashes import Stash, StashType


class DungeonGenerator:
    """Процедурный генератор подземелий"""

    def __init__(self):
        """Инициализация генератора"""
        # Параметры генерации подземелий
        self.dungeon_params = {
            "min_rooms": 8,
            "max_rooms": 18,
            "min_room_size": 5,
            "max_room_size": 14,
            "corridor_width": 2,
            "trap_chance": 0.08,     # 8% шанс ловушки на проходимой клетке
            "stash_chance": 0.015,   # 1.5% шанс тайника (уменьшено для баланса)
            "decorations": True,
        }

        # Параметры генерации шахт
        self.mine_params = {
            "min_rooms": 6,
            "max_rooms": 14,
            "min_room_size": 4,
            "max_room_size": 12,
            "corridor_width": 3,     # Шахты шире
            "trap_chance": 0.025,    # Меньше ловушек (2.5% вместо 5%)
            "stash_chance": 0.03,    # 3% руды (уменьшено с 10% для баланса)
            "decorations": True,
        }

    def generate(self, dungeon_type: str = "dungeon", dungeon_level: int = 1,
                 width: int = 50, height: int = 40, name: str = None,
                 current_depth: int = 1, max_depth: int = 5,
                 floor_type: str = None) -> DungeonMap:
        """
        Генерация подземелья

        Args:
            dungeon_type: "dungeon" или "mine"
            dungeon_level: Уровень подземелья (влияет на сложность врагов)
            width: Ширина карты
            height: Высота карты
            name: Название (если None - генерируется)
            current_depth: Текущая глубина (уровень подземелья, 1-based)
            max_depth: Максимальная глубина подземелья
            floor_type: Тип этажа из конфига (basement, dark_basement, etc.)

        Returns:
            DungeonMap: Сгенерированная карта
        """
        # Выбираем параметры в зависимости от типа
        params = self.mine_params if dungeon_type == "mine" else self.dungeon_params

        # Генерируем название если не указано
        if name is None:
            name = self._generate_name(dungeon_type, dungeon_level)

        # Создаем карту с учетом текущей глубины и типа этажа
        dungeon = DungeonMap(width, height, dungeon_type, dungeon_level, name,
                             current_depth, floor_type)

        # Генерируем комнаты
        num_rooms = random.randint(params["min_rooms"], params["max_rooms"])
        self._generate_rooms(dungeon, num_rooms, params)

        # Соединяем комнаты коридорами
        self._connect_rooms(dungeon, params["corridor_width"])

        # Размещаем вход и выходы/лестницы
        self._place_entrance_and_exits(dungeon, current_depth, max_depth)

        # Добавляем ловушки
        self._place_traps(dungeon, params["trap_chance"])

        # Добавляем тайники
        self._place_stashes(dungeon, params["stash_chance"])

        # Добавляем декорации
        if params["decorations"]:
            self._place_decorations(dungeon, dungeon_type)

        return dungeon

    def _generate_name(self, dungeon_type: str, level: int) -> str:
        """Генерация названия подземелья"""
        if dungeon_type == "mine":
            prefixes = ["Заброшенная", "Древняя", "Глубокая", "Темная", "Проклятая"]
            names = ["Шахта", "Копь", "Выработка", "Каменоломня"]
            suffixes = ["", " Забытых", " Теней", " Мёртвых", " Гномов"]
        else:
            prefixes = ["Забытые", "Древние", "Проклятые", "Тёмные", "Гнилые"]
            names = ["Катакомбы", "Подземелье", "Крипта", "Руины", "Склеп"]
            suffixes = ["", " Ужаса", " Теней", " Королей", " Демонов"]

        prefix = random.choice(prefixes) if random.random() < 0.6 else ""
        name = random.choice(names)
        suffix = random.choice(suffixes) if random.random() < 0.4 else ""

        full_name = f"{prefix} {name}{suffix}".strip()
        return f"{full_name} (Ур. {level})"

    def _generate_rooms(self, dungeon: DungeonMap, num_rooms: int, params: dict):
        """
        Улучшенная генерация комнат с различными формами

        Типы комнат:
        - Прямоугольные (стандартные)
        - L-образные (угловые)
        - Крестообразные
        - Круглые (приблизительно)
        - Специальные комнаты (сокровищница, комната босса)

        Args:
            dungeon: Карта подземелья
            num_rooms: Количество комнат
            params: Параметры генерации
        """
        min_size = params["min_room_size"]
        max_size = params["max_room_size"]

        rooms_created = 0
        attempts = 0
        max_attempts = num_rooms * 15  # Увеличено для большего разнообразия

        # Отмечаем, созданы ли специальные комнаты
        treasure_room_created = False
        boss_room_created = False

        while rooms_created < num_rooms and attempts < max_attempts:
            attempts += 1

            # Генерируем размеры комнаты
            room_w = random.randint(min_size, max_size)
            room_h = random.randint(min_size, max_size)

            # Генерируем позицию (с отступом от краев)
            room_x = random.randint(2, dungeon.width - room_w - 2)
            room_y = random.randint(2, dungeon.height - room_h - 2)

            # Проверяем, не пересекается ли с другими комнатами
            if not self._room_overlaps(dungeon, room_x, room_y, room_w, room_h):
                # Выбираем тип комнаты
                room_type = self._choose_room_type(
                    rooms_created, num_rooms,
                    treasure_room_created, boss_room_created
                )

                # Создаем комнату выбранного типа
                if room_type == "rectangular":
                    self._carve_room(dungeon, room_x, room_y, room_w, room_h)
                elif room_type == "l_shaped":
                    self._carve_l_shaped_room(dungeon, room_x, room_y, room_w, room_h)
                elif room_type == "cross":
                    self._carve_cross_room(dungeon, room_x, room_y, room_w, room_h)
                elif room_type == "circular":
                    self._carve_circular_room(dungeon, room_x, room_y, min(room_w, room_h) // 2)
                elif room_type == "treasure":
                    self._carve_room(dungeon, room_x, room_y, room_w, room_h)
                    treasure_room_created = True
                elif room_type == "boss":
                    # Комната босса больше обычной
                    boss_w = min(room_w + 4, max_size + 4)
                    boss_h = min(room_h + 4, max_size + 4)
                    self._carve_room(dungeon, room_x, room_y, boss_w, boss_h)
                    boss_room_created = True
                else:
                    self._carve_room(dungeon, room_x, room_y, room_w, room_h)

                dungeon.rooms.append((room_x, room_y, room_w, room_h))
                rooms_created += 1

    def _choose_room_type(self, current_room: int, total_rooms: int,
                          treasure_created: bool, boss_created: bool) -> str:
        """
        Выбрать тип комнаты на основе текущего прогресса генерации

        Returns:
            str: Тип комнаты
        """
        # Последняя комната - комната босса (если еще не создана)
        if current_room == total_rooms - 1 and not boss_created:
            return "boss"

        # Предпоследняя комната - сокровищница (если еще не создана)
        if current_room == total_rooms - 2 and not treasure_created:
            return "treasure"

        # Для остальных комнат - случайный выбор формы
        roll = random.random()
        if roll < 0.55:
            return "rectangular"  # 55% - обычные прямоугольные
        elif roll < 0.70:
            return "l_shaped"     # 15% - L-образные
        elif roll < 0.85:
            return "cross"        # 15% - крестообразные
        else:
            return "circular"     # 15% - круглые

    def _carve_l_shaped_room(self, dungeon: DungeonMap, x: int, y: int, w: int, h: int):
        """
        Вырезать L-образную комнату

        Args:
            dungeon: Карта подземелья
            x, y, w, h: Параметры ограничивающего прямоугольника
        """
        # L-образная комната состоит из двух прямоугольников
        # Вертикальная часть
        vert_w = w // 2
        for dy in range(h):
            for dx in range(vert_w):
                dungeon.set_tile_type(x + dx, y + dy, DungeonTileType.FLOOR)

        # Горизонтальная часть (нижняя)
        horiz_h = h // 2
        for dy in range(horiz_h):
            for dx in range(w):
                dungeon.set_tile_type(x + dx, y + h - horiz_h + dy, DungeonTileType.FLOOR)

    def _carve_cross_room(self, dungeon: DungeonMap, x: int, y: int, w: int, h: int):
        """
        Вырезать крестообразную комнату

        Args:
            dungeon: Карта подземелья
            x, y, w, h: Параметры ограничивающего прямоугольника
        """
        # Центральная вертикальная часть
        vert_w = max(3, w // 3)
        vert_start = (w - vert_w) // 2
        for dy in range(h):
            for dx in range(vert_w):
                dungeon.set_tile_type(x + vert_start + dx, y + dy, DungeonTileType.FLOOR)

        # Центральная горизонтальная часть
        horiz_h = max(3, h // 3)
        horiz_start = (h - horiz_h) // 2
        for dy in range(horiz_h):
            for dx in range(w):
                dungeon.set_tile_type(x + dx, y + horiz_start + dy, DungeonTileType.FLOOR)

    def _carve_circular_room(self, dungeon: DungeonMap, cx: int, cy: int, radius: int):
        """
        Вырезать круглую комнату

        Args:
            dungeon: Карта подземелья
            cx, cy: Координаты центра
            radius: Радиус комнаты
        """
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                # Проверяем, находится ли точка внутри круга
                if dx * dx + dy * dy <= radius * radius:
                    px, py = cx + dx, cy + dy
                    if dungeon.is_valid_position(px, py):
                        dungeon.set_tile_type(px, py, DungeonTileType.FLOOR)

    def _room_overlaps(self, dungeon: DungeonMap, x: int, y: int, w: int, h: int,
                       padding: int = 2) -> bool:
        """
        Проверка пересечения комнаты с существующими

        Args:
            dungeon: Карта подземелья
            x, y, w, h: Параметры новой комнаты
            padding: Минимальное расстояние между комнатами

        Returns:
            bool: True если пересекается
        """
        for rx, ry, rw, rh in dungeon.rooms:
            # Проверяем пересечение с учетом отступа
            if (x - padding < rx + rw and x + w + padding > rx and
                y - padding < ry + rh and y + h + padding > ry):
                return True
        return False

    def _carve_room(self, dungeon: DungeonMap, x: int, y: int, w: int, h: int):
        """
        Вырезать комнату в карте

        Args:
            dungeon: Карта подземелья
            x, y, w, h: Параметры комнаты
        """
        for dy in range(h):
            for dx in range(w):
                dungeon.set_tile_type(x + dx, y + dy, DungeonTileType.FLOOR)

    def _connect_rooms(self, dungeon: DungeonMap, corridor_width: int = 1):
        """
        Соединить все комнаты коридорами

        Args:
            dungeon: Карта подземелья
            corridor_width: Ширина коридора
        """
        if len(dungeon.rooms) < 2:
            return

        # Соединяем каждую комнату со следующей
        for i in range(len(dungeon.rooms) - 1):
            room1 = dungeon.rooms[i]
            room2 = dungeon.rooms[i + 1]

            # Центры комнат
            x1 = room1[0] + room1[2] // 2
            y1 = room1[1] + room1[3] // 2
            x2 = room2[0] + room2[2] // 2
            y2 = room2[1] + room2[3] // 2

            # Создаем L-образный коридор
            if random.random() < 0.5:
                # Сначала горизонтально, потом вертикально
                self._carve_corridor_h(dungeon, x1, x2, y1, corridor_width)
                self._carve_corridor_v(dungeon, y1, y2, x2, corridor_width)
            else:
                # Сначала вертикально, потом горизонтально
                self._carve_corridor_v(dungeon, y1, y2, x1, corridor_width)
                self._carve_corridor_h(dungeon, x1, x2, y2, corridor_width)

        # Добавляем несколько дополнительных связей для интересности
        if len(dungeon.rooms) > 3:
            extra_connections = random.randint(1, len(dungeon.rooms) // 3)
            for _ in range(extra_connections):
                room1 = random.choice(dungeon.rooms)
                room2 = random.choice(dungeon.rooms)
                if room1 != room2:
                    x1 = room1[0] + room1[2] // 2
                    y1 = room1[1] + room1[3] // 2
                    x2 = room2[0] + room2[2] // 2
                    y2 = room2[1] + room2[3] // 2

                    self._carve_corridor_h(dungeon, x1, x2, y1, corridor_width)
                    self._carve_corridor_v(dungeon, y1, y2, x2, corridor_width)

    def _carve_corridor_h(self, dungeon: DungeonMap, x1: int, x2: int, y: int, width: int):
        """Вырезать горизонтальный коридор"""
        start_x = min(x1, x2)
        end_x = max(x1, x2)

        for x in range(start_x, end_x + 1):
            for w in range(width):
                tile_y = y + w - width // 2
                if dungeon.is_valid_position(x, tile_y):
                    tile = dungeon.get_tile(x, tile_y)
                    if tile and tile.tile_type == DungeonTileType.WALL:
                        dungeon.set_tile_type(x, tile_y, DungeonTileType.CORRIDOR)

    def _carve_corridor_v(self, dungeon: DungeonMap, y1: int, y2: int, x: int, width: int):
        """Вырезать вертикальный коридор"""
        start_y = min(y1, y2)
        end_y = max(y1, y2)

        for y in range(start_y, end_y + 1):
            for w in range(width):
                tile_x = x + w - width // 2
                if dungeon.is_valid_position(tile_x, y):
                    tile = dungeon.get_tile(tile_x, y)
                    if tile and tile.tile_type == DungeonTileType.WALL:
                        dungeon.set_tile_type(tile_x, y, DungeonTileType.CORRIDOR)

    def _find_nearby_floor(self, dungeon: DungeonMap, center_x: int, center_y: int) -> Optional[Tuple[int, int]]:
        """
        Найти ближайший тайл пола вокруг указанной позиции

        Args:
            dungeon: Карта подземелья
            center_x: Центральная X координата
            center_y: Центральная Y координата

        Returns:
            Кортеж (x, y) с координатами найденного пола, или None если не найден
        """
        # Проверяем сначала центральную клетку
        if 0 < center_x < dungeon.width - 1 and 0 < center_y < dungeon.height - 1:
            tile = dungeon.get_tile(center_x, center_y)
            if tile and tile.tile_type == DungeonTileType.FLOOR:
                return (center_x, center_y)

        # Проверяем клетки вокруг в порядке близости
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            test_x = center_x + dx
            test_y = center_y + dy

            if 0 < test_x < dungeon.width - 1 and 0 < test_y < dungeon.height - 1:
                tile = dungeon.get_tile(test_x, test_y)
                if tile and tile.tile_type == DungeonTileType.FLOOR:
                    return (test_x, test_y)

        return None

    def _place_entrance_and_exits(self, dungeon: DungeonMap, current_depth: int = 1, max_depth: int = 5):
        """
        Разместить вход, выходы и лестницы

        Args:
            dungeon: Карта подземелья
            current_depth: Текущая глубина (1-based)
            max_depth: Максимальная глубина подземелья
        """
        if not dungeon.rooms:
            return

        # Вход в первой комнате
        first_room = dungeon.rooms[0]
        entrance_x = first_room[0] + first_room[2] // 2
        entrance_y = first_room[1] + first_room[3] // 2

        # Устанавливаем вход СНАЧАЛА
        dungeon.set_entrance(entrance_x, entrance_y)

        # Если это НЕ первый уровень - ставим лестницу вверх рядом с входом
        if current_depth > 1:
            # Ищем ближайший пол ВОКРУГ входа (не сам вход!)
            stairs_up_x, stairs_up_y = None, None

            # Проверяем клетки вокруг входа (не включая сам вход)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                test_x = entrance_x + dx
                test_y = entrance_y + dy

                if 0 < test_x < dungeon.width - 1 and 0 < test_y < dungeon.height - 1:
                    tile = dungeon.get_tile(test_x, test_y)
                    if tile and tile.tile_type == DungeonTileType.FLOOR:
                        stairs_up_x = test_x
                        stairs_up_y = test_y
                        break

            # Если нашли подходящую клетку - устанавливаем лестницу
            if stairs_up_x is not None:
                dungeon.set_tile_type(stairs_up_x, stairs_up_y, DungeonTileType.STAIRS_UP)
                dungeon.stairs_up = (stairs_up_x, stairs_up_y)

        # В последней комнате размещаем либо выход, либо лестницу вниз
        last_room = dungeon.rooms[-1]
        exit_x = last_room[0] + last_room[2] // 2
        exit_y = last_room[1] + last_room[3] // 2

        if current_depth < max_depth:
            # Не последний уровень - ставим лестницу вниз
            stairs_down_pos = self._find_nearby_floor(dungeon, exit_x, exit_y)
            if stairs_down_pos:
                stairs_down_x, stairs_down_y = stairs_down_pos
                dungeon.set_tile_type(stairs_down_x, stairs_down_y, DungeonTileType.STAIRS_DOWN)
                dungeon.stairs_down = (stairs_down_x, stairs_down_y)
        else:
            # Последний уровень - ставим выход
            exit_pos = self._find_nearby_floor(dungeon, exit_x, exit_y)
            if exit_pos:
                dungeon.add_exit(exit_pos[0], exit_pos[1])

        # Дополнительный выход в случайной комнате (только на последнем уровне)
        if current_depth == max_depth and len(dungeon.rooms) >= 5:
            # Выбираем комнату в середине, но не первую и не последнюю
            mid_idx = len(dungeon.rooms) // 2
            mid_room = dungeon.rooms[mid_idx]
            alt_exit_x = mid_room[0] + mid_room[2] // 2
            alt_exit_y = mid_room[1] + mid_room[3] // 2

            # Убеждаемся, что это не совпадает с входом
            if (alt_exit_x, alt_exit_y) != (entrance_x, entrance_y):
                alt_exit_pos = self._find_nearby_floor(dungeon, alt_exit_x, alt_exit_y)
                if alt_exit_pos:
                    dungeon.add_exit(alt_exit_pos[0], alt_exit_pos[1])

    def _place_traps(self, dungeon: DungeonMap, trap_chance: float):
        """Разместить ловушки"""
        floor_tiles = dungeon.get_all_floor_tiles()

        for x, y in floor_tiles:
            tile = dungeon.get_tile(x, y)
            if not tile:
                continue

            # Не ставим ловушки на входе/выходе/лестницах
            if dungeon.is_entrance_tile(x, y) or dungeon.is_exit_tile(x, y):
                continue
            if tile.tile_type in (DungeonTileType.STAIRS_UP, DungeonTileType.STAIRS_DOWN):
                continue

            if random.random() < trap_chance:
                trap = dungeon.trap_manager.generate_random_trap(x, y, dungeon.dungeon_level)
                dungeon.trap_manager.add_trap(trap)
                # Помечаем клетку как ловушку
                dungeon.set_tile_type(x, y, DungeonTileType.TRAP)

    def _place_stashes(self, dungeon: DungeonMap, stash_chance: float):
        """Разместить тайники"""
        floor_tiles = dungeon.get_all_floor_tiles()
        is_mine = dungeon.dungeon_type == "mine"

        for x, y in floor_tiles:
            tile = dungeon.get_tile(x, y)
            if not tile:
                continue

            # Не ставим тайники на входе/выходе/лестницах или на ловушках
            if dungeon.is_entrance_tile(x, y) or dungeon.is_exit_tile(x, y):
                continue
            if tile.tile_type in (DungeonTileType.STAIRS_UP, DungeonTileType.STAIRS_DOWN):
                continue
            if dungeon.trap_manager.get_trap_at(x, y) is not None:
                continue

            if random.random() < stash_chance:
                stash = dungeon.stash_manager.generate_random_stash(
                    x, y, dungeon.dungeon_level, is_mine
                )
                dungeon.stash_manager.add_stash(stash)

                # Помечаем клетку как тайник (если видимый)
                if stash.is_detected:
                    dungeon.set_tile_type(x, y, DungeonTileType.STASH)

    def _place_decorations(self, dungeon: DungeonMap, dungeon_type: str):
        """
        Добавить декоративные элементы в подземелье

        ИСПРАВЛЕНА ОШИБКА: ранее условия проверялись в неправильном порядке,
        из-за чего алтари и лужи воды никогда не генерировались.
        Теперь используются правильные диапазоны.
        """
        floor_tiles = dungeon.get_all_floor_tiles()

        for x, y in floor_tiles:
            # Пропускаем специальные клетки
            tile = dungeon.get_tile(x, y)
            if tile.tile_type not in [DungeonTileType.FLOOR, DungeonTileType.CORRIDOR]:
                continue

            # Случайные декорации с ПРАВИЛЬНЫМИ диапазонами
            roll = random.random()

            if dungeon_type == "mine":
                # Для шахт:
                # 0-1%: вагонетки
                # 1-3%: опоры
                # 3-6%: обломки
                if roll < 0.01:
                    dungeon.set_tile_type(x, y, DungeonTileType.MINECART)
                elif roll < 0.03:
                    dungeon.set_tile_type(x, y, DungeonTileType.SUPPORT)
                elif roll < 0.06:
                    dungeon.set_tile_type(x, y, DungeonTileType.RUBBLE)
            else:
                # Для подземелий (ИСПРАВЛЕННЫЙ порядок):
                # 0-0.3%: алтари (редкие!)
                # 0.3-1%: лужи воды
                # 1-3%: кости
                # 3-5%: обломки
                if roll < 0.003:
                    dungeon.set_tile_type(x, y, DungeonTileType.ALTAR)
                elif roll < 0.01:
                    dungeon.set_tile_type(x, y, DungeonTileType.WATER)
                elif roll < 0.03:
                    dungeon.set_tile_type(x, y, DungeonTileType.BONES)
                elif roll < 0.05:
                    dungeon.set_tile_type(x, y, DungeonTileType.RUBBLE)

    def generate_dungeon_for_location(self, location_type: str, location_name: str,
                                       location_x: int, location_y: int,
                                       current_depth: int = 1, max_depth: int = 5,
                                       floor_type: str = None, floor_size: int = None) -> DungeonMap:
        """
        Генерация подземелья для конкретной локации

        Args:
            location_type: Тип локации ("ruins" или "mine")
            location_name: Название локации
            location_x: X координата локации на основной карте
            location_y: Y координата локации на основной карте
            current_depth: Текущая глубина (уровень подземелья)
            max_depth: Максимальная глубина подземелья
            floor_type: Тип этажа из конфига (basement, dark_basement, mine, etc.)
            floor_size: Размер этажа из конфига (1-10, влияет на размер карты)

        Returns:
            DungeonMap: Сгенерированная карта
        """
        # Определяем параметры на основе типа локации
        if location_type == "mine":
            dungeon_type = "mine"
            # Уровень шахты зависит от расстояния от центра карты
            distance = abs(location_x - 100) + abs(location_y - 100)
            dungeon_level = max(1, min(10, 1 + distance // 30))
            # Размер зависит от floor_size из конфига или от уровня
            if floor_size is not None:
                # floor_size от 1 до 10, где 1 = маленький, 10 = огромный
                base_width, base_height = 40, 35
                size_bonus = floor_size * 8
                width = base_width + size_bonus + random.randint(0, 15)
                height = base_height + size_bonus + random.randint(0, 10)
            else:
                # Fallback: размер зависит от уровня
                base_width, base_height = 50, 40
                level_bonus = dungeon_level * 5
                width = base_width + level_bonus + random.randint(0, 20)
                height = base_height + level_bonus + random.randint(0, 15)
        else:  # ruins / dungeon
            dungeon_type = "dungeon"
            # Уровень подземелья зависит от расстояния от центра
            distance = abs(location_x - 100) + abs(location_y - 100)
            dungeon_level = max(1, min(10, 1 + distance // 25))
            # Размер зависит от floor_size из конфига или от уровня
            if floor_size is not None:
                # floor_size от 1 до 10, где 1 = маленький, 10 = огромный
                base_width, base_height = 45, 40
                size_bonus = floor_size * 10
                width = base_width + size_bonus + random.randint(0, 20)
                height = base_height + size_bonus + random.randint(0, 15)
            else:
                # Fallback: размер зависит от уровня
                base_width, base_height = 55, 45
                level_bonus = dungeon_level * 6
                width = base_width + level_bonus + random.randint(0, 25)
                height = base_height + level_bonus + random.randint(0, 20)

        # Генерируем название с указанием глубины
        if current_depth > 1:
            depth_suffix = f" (Уровень {current_depth})"
        else:
            depth_suffix = ""

        name = f"Подземелье под {location_name}{depth_suffix}" if dungeon_type == "dungeon" else f"Шахта {location_name}{depth_suffix}"

        # Генерируем подземелье с учётом глубины и типа этажа
        dungeon = self.generate(dungeon_type, dungeon_level, width, height, name,
                                current_depth, max_depth, floor_type)

        # Сохраняем координаты возврата
        dungeon.return_x = location_x
        dungeon.return_y = location_y

        return dungeon
