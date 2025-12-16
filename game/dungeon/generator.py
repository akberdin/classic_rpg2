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
            "min_rooms": 5,
            "max_rooms": 12,
            "min_room_size": 4,
            "max_room_size": 10,
            "corridor_width": 1,
            "trap_chance": 0.08,     # 8% шанс ловушки на проходимой клетке
            "stash_chance": 0.05,    # 5% шанс тайника
            "decorations": True,
        }

        # Параметры генерации шахт
        self.mine_params = {
            "min_rooms": 3,
            "max_rooms": 8,
            "min_room_size": 3,
            "max_room_size": 8,
            "corridor_width": 2,     # Шахты шире
            "trap_chance": 0.05,     # Меньше ловушек
            "stash_chance": 0.10,    # Больше руды
            "decorations": True,
        }

    def generate(self, dungeon_type: str = "dungeon", dungeon_level: int = 1,
                 width: int = 50, height: int = 40, name: str = None) -> DungeonMap:
        """
        Генерация подземелья

        Args:
            dungeon_type: "dungeon" или "mine"
            dungeon_level: Уровень подземелья (1-10)
            width: Ширина карты
            height: Высота карты
            name: Название (если None - генерируется)

        Returns:
            DungeonMap: Сгенерированная карта
        """
        # Выбираем параметры в зависимости от типа
        params = self.mine_params if dungeon_type == "mine" else self.dungeon_params

        # Генерируем название если не указано
        if name is None:
            name = self._generate_name(dungeon_type, dungeon_level)

        # Создаем карту
        dungeon = DungeonMap(width, height, dungeon_type, dungeon_level, name)

        # Генерируем комнаты
        num_rooms = random.randint(params["min_rooms"], params["max_rooms"])
        self._generate_rooms(dungeon, num_rooms, params)

        # Соединяем комнаты коридорами
        self._connect_rooms(dungeon, params["corridor_width"])

        # Размещаем вход и выходы
        self._place_entrance_and_exits(dungeon)

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
        Генерация комнат методом BSP (Binary Space Partitioning)

        Args:
            dungeon: Карта подземелья
            num_rooms: Количество комнат
            params: Параметры генерации
        """
        min_size = params["min_room_size"]
        max_size = params["max_room_size"]

        rooms_created = 0
        attempts = 0
        max_attempts = num_rooms * 10

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
                # Создаем комнату
                self._carve_room(dungeon, room_x, room_y, room_w, room_h)
                dungeon.rooms.append((room_x, room_y, room_w, room_h))
                rooms_created += 1

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

    def _place_entrance_and_exits(self, dungeon: DungeonMap):
        """Разместить вход и выходы"""
        if not dungeon.rooms:
            return

        # Вход в первой комнате
        first_room = dungeon.rooms[0]
        entrance_x = first_room[0] + first_room[2] // 2
        entrance_y = first_room[1] + first_room[3] // 2
        dungeon.set_entrance(entrance_x, entrance_y)

        # Выход в последней комнате
        last_room = dungeon.rooms[-1]
        exit_x = last_room[0] + last_room[2] // 2
        exit_y = last_room[1] + last_room[3] // 2
        dungeon.add_exit(exit_x, exit_y)

        # Дополнительный выход в случайной комнате (если достаточно комнат)
        if len(dungeon.rooms) >= 5:
            # Выбираем комнату в середине, но не первую и не последнюю
            mid_idx = len(dungeon.rooms) // 2
            mid_room = dungeon.rooms[mid_idx]
            alt_exit_x = mid_room[0] + mid_room[2] // 2
            alt_exit_y = mid_room[1] + mid_room[3] // 2

            # Убеждаемся, что это не совпадает с входом
            if (alt_exit_x, alt_exit_y) != (entrance_x, entrance_y):
                dungeon.add_exit(alt_exit_x, alt_exit_y)

    def _place_traps(self, dungeon: DungeonMap, trap_chance: float):
        """Разместить ловушки"""
        floor_tiles = dungeon.get_all_floor_tiles()

        for x, y in floor_tiles:
            # Не ставим ловушки на входе/выходе
            if dungeon.is_entrance_tile(x, y) or dungeon.is_exit_tile(x, y):
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
            # Не ставим тайники на входе/выходе или на ловушках
            if dungeon.is_entrance_tile(x, y) or dungeon.is_exit_tile(x, y):
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
        """Добавить декоративные элементы"""
        floor_tiles = dungeon.get_all_floor_tiles()

        for x, y in floor_tiles:
            # Пропускаем специальные клетки
            tile = dungeon.get_tile(x, y)
            if tile.tile_type not in [DungeonTileType.FLOOR, DungeonTileType.CORRIDOR]:
                continue

            # Случайные декорации
            roll = random.random()

            if dungeon_type == "mine":
                # Для шахт
                if roll < 0.01:
                    dungeon.set_tile_type(x, y, DungeonTileType.MINECART)
                elif roll < 0.03:
                    dungeon.set_tile_type(x, y, DungeonTileType.SUPPORT)
                elif roll < 0.05:
                    dungeon.set_tile_type(x, y, DungeonTileType.RUBBLE)
            else:
                # Для подземелий
                if roll < 0.02:
                    dungeon.set_tile_type(x, y, DungeonTileType.BONES)
                elif roll < 0.03:
                    dungeon.set_tile_type(x, y, DungeonTileType.RUBBLE)
                elif roll < 0.005:
                    dungeon.set_tile_type(x, y, DungeonTileType.ALTAR)
                elif roll < 0.01:
                    dungeon.set_tile_type(x, y, DungeonTileType.WATER)

    def generate_dungeon_for_location(self, location_type: str, location_name: str,
                                       location_x: int, location_y: int) -> DungeonMap:
        """
        Генерация подземелья для конкретной локации

        Args:
            location_type: Тип локации ("ruins" или "mine")
            location_name: Название локации
            location_x: X координата локации на основной карте
            location_y: Y координата локации на основной карте

        Returns:
            DungeonMap: Сгенерированная карта
        """
        # Определяем параметры на основе типа локации
        if location_type == "mine":
            dungeon_type = "mine"
            # Уровень шахты зависит от расстояния от центра карты
            distance = abs(location_x - 100) + abs(location_y - 100)
            dungeon_level = max(1, min(10, 1 + distance // 30))
            width = random.randint(40, 60)
            height = random.randint(30, 50)
        else:  # ruins / dungeon
            dungeon_type = "dungeon"
            # Уровень подземелья зависит от расстояния от центра
            distance = abs(location_x - 100) + abs(location_y - 100)
            dungeon_level = max(1, min(10, 1 + distance // 25))
            width = random.randint(45, 65)
            height = random.randint(35, 55)

        # Генерируем название
        name = f"Подземелье под {location_name}" if dungeon_type == "dungeon" else f"Шахта {location_name}"

        # Генерируем подземелье
        dungeon = self.generate(dungeon_type, dungeon_level, width, height, name)

        # Сохраняем координаты возврата
        dungeon.return_x = location_x
        dungeon.return_y = location_y

        return dungeon
