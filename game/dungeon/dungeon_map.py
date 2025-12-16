"""
Класс карты подземелья
"""
import random
from typing import List, Tuple, Optional

from game.dungeon.tiles import DungeonTile, DungeonTileType, PASSABLE_DUNGEON_TILES
from game.dungeon.traps import TrapManager
from game.dungeon.stashes import StashManager


class DungeonMap:
    """Класс карты подземелья"""

    def __init__(self, width: int, height: int, dungeon_type: str = "dungeon",
                 dungeon_level: int = 1, name: str = "Подземелье"):
        """
        Инициализация карты подземелья

        Args:
            width: Ширина карты
            height: Высота карты
            dungeon_type: Тип ("dungeon" или "mine")
            dungeon_level: Уровень подземелья (влияет на сложность)
            name: Название подземелья
        """
        self.width = width
        self.height = height
        self.dungeon_type = dungeon_type
        self.dungeon_level = dungeon_level
        self.name = name

        # Создаем карту, заполненную стенами
        self.tiles: List[List[DungeonTile]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(DungeonTile(x, y, DungeonTileType.WALL))
            self.tiles.append(row)

        # Менеджеры интерактивных объектов
        self.trap_manager = TrapManager()
        self.stash_manager = StashManager()

        # Точки входа и выхода
        self.entrance: Optional[Tuple[int, int]] = None
        self.exits: List[Tuple[int, int]] = []

        # NPC в подземелье
        self.npcs: List = []

        # Комнаты (для отладки и генерации)
        self.rooms: List[Tuple[int, int, int, int]] = []  # (x, y, width, height)

        # Координаты возврата (позиция на основной карте)
        self.return_x: int = 0
        self.return_y: int = 0

    def get_tile(self, x: int, y: int) -> Optional[DungeonTile]:
        """
        Получить клетку по координатам

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            DungeonTile или None если координаты вне карты
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def set_tile_type(self, x: int, y: int, tile_type: DungeonTileType):
        """
        Установить тип клетки

        Args:
            x: Координата X
            y: Координата Y
            tile_type: Новый тип клетки
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x].tile_type = tile_type

    def is_passable(self, x: int, y: int) -> bool:
        """
        Проверить, можно ли пройти через клетку

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если клетка проходима
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        return tile.is_passable()

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Проверить, валидны ли координаты

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если координаты в пределах карты
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def set_entrance(self, x: int, y: int):
        """
        Установить точку входа

        Args:
            x: Координата X
            y: Координата Y
        """
        self.entrance = (x, y)
        self.set_tile_type(x, y, DungeonTileType.ENTRANCE)

    def add_exit(self, x: int, y: int):
        """
        Добавить точку выхода

        Args:
            x: Координата X
            y: Координата Y
        """
        self.exits.append((x, y))
        self.set_tile_type(x, y, DungeonTileType.EXIT)

    def get_random_floor_tile(self, exclude_special: bool = True) -> Optional[Tuple[int, int]]:
        """
        Получить случайную проходимую клетку

        Args:
            exclude_special: Исключить специальные клетки (вход, выход, ловушки, тайники)

        Returns:
            Tuple[int, int] или None
        """
        floor_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile.tile_type in [DungeonTileType.FLOOR, DungeonTileType.CORRIDOR]:
                    if exclude_special:
                        # Проверяем, не занята ли клетка
                        if self.trap_manager.get_trap_at(x, y) is None:
                            if self.stash_manager.get_stash_at(x, y) is None:
                                floor_tiles.append((x, y))
                    else:
                        floor_tiles.append((x, y))

        if floor_tiles:
            return random.choice(floor_tiles)
        return None

    def get_all_floor_tiles(self) -> List[Tuple[int, int]]:
        """Получить все проходимые клетки"""
        floor_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile.is_passable():
                    floor_tiles.append((x, y))

        return floor_tiles

    def update_visibility(self, player_x: int, player_y: int, vision_radius: int = 5):
        """
        Обновить видимость клеток

        Args:
            player_x: Координата X игрока
            player_y: Координата Y игрока
            vision_radius: Радиус видимости
        """
        # Сначала скрываем все клетки
        for row in self.tiles:
            for tile in row:
                tile.visible = False

        # Показываем клетки в радиусе видимости
        for dy in range(-vision_radius, vision_radius + 1):
            for dx in range(-vision_radius, vision_radius + 1):
                # Проверяем расстояние (круглый радиус)
                if dx * dx + dy * dy <= vision_radius * vision_radius:
                    x = player_x + dx
                    y = player_y + dy

                    tile = self.get_tile(x, y)
                    if tile:
                        # Проверяем линию видимости (упрощенно)
                        if self._has_line_of_sight(player_x, player_y, x, y):
                            tile.visible = True
                            tile.explored = True

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        Проверить линию видимости между двумя точками (алгоритм Брезенхема)

        Args:
            x1, y1: Начальная точка
            x2, y2: Конечная точка

        Returns:
            bool: True если есть прямая видимость
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1

        while True:
            # Проверяем текущую клетку (кроме начальной и конечной)
            if (x, y) != (x1, y1) and (x, y) != (x2, y2):
                tile = self.get_tile(x, y)
                if tile and tile.tile_type == DungeonTileType.WALL:
                    return False

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return True

    def add_npc(self, npc):
        """
        Добавить NPC в подземелье

        Args:
            npc: Объект NPC
        """
        self.npcs.append(npc)

    def remove_npc(self, npc):
        """
        Удалить NPC из подземелья

        Args:
            npc: Объект NPC
        """
        if npc in self.npcs:
            self.npcs.remove(npc)

    def get_npc_at(self, x: int, y: int):
        """
        Получить NPC по координатам

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            NPC или None
        """
        for npc in self.npcs:
            if npc.x == x and npc.y == y and npc.is_alive:
                return npc
        return None

    def get_nearby_npcs(self, x: int, y: int, radius: int = 1) -> List:
        """
        Получить NPC поблизости

        Args:
            x: Координата X
            y: Координата Y
            radius: Радиус поиска

        Returns:
            List: Список NPC
        """
        nearby = []
        for npc in self.npcs:
            if not npc.is_alive:
                continue
            distance = abs(npc.x - x) + abs(npc.y - y)
            if distance <= radius:
                nearby.append(npc)
        return nearby

    def is_exit_tile(self, x: int, y: int) -> bool:
        """
        Проверить, является ли клетка выходом

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если это выход
        """
        return (x, y) in self.exits

    def is_entrance_tile(self, x: int, y: int) -> bool:
        """
        Проверить, является ли клетка входом

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если это вход
        """
        return self.entrance == (x, y)

    def get_statistics(self) -> dict:
        """
        Получить статистику карты

        Returns:
            dict: Статистика
        """
        floor_count = 0
        wall_count = 0
        special_count = 0

        for row in self.tiles:
            for tile in row:
                if tile.tile_type == DungeonTileType.WALL:
                    wall_count += 1
                elif tile.tile_type in [DungeonTileType.FLOOR, DungeonTileType.CORRIDOR]:
                    floor_count += 1
                else:
                    special_count += 1

        return {
            "name": self.name,
            "type": self.dungeon_type,
            "level": self.dungeon_level,
            "size": f"{self.width}x{self.height}",
            "floor_tiles": floor_count,
            "wall_tiles": wall_count,
            "special_tiles": special_count,
            "rooms": len(self.rooms),
            "traps": len(self.trap_manager.traps),
            "stashes": len(self.stash_manager.stashes),
            "npcs": len(self.npcs),
            "exits": len(self.exits),
        }

    def debug_print(self):
        """Вывести карту в консоль (для отладки)"""
        symbols = {
            DungeonTileType.WALL: '#',
            DungeonTileType.FLOOR: '.',
            DungeonTileType.CORRIDOR: '+',
            DungeonTileType.ENTRANCE: 'E',
            DungeonTileType.EXIT: 'X',
            DungeonTileType.TRAP: '^',
            DungeonTileType.TRAP_TRIGGERED: 'v',
            DungeonTileType.STASH: '$',
            DungeonTileType.STASH_LOOTED: '_',
            DungeonTileType.RUBBLE: '%',
            DungeonTileType.WATER: '~',
            DungeonTileType.BONES: 'b',
            DungeonTileType.ALTAR: 'A',
            DungeonTileType.ORE_VEIN: 'o',
            DungeonTileType.MINECART: 'M',
            DungeonTileType.SUPPORT: '|',
        }

        print(f"\n=== {self.name} ({self.dungeon_type}, уровень {self.dungeon_level}) ===")
        for y in range(self.height):
            row_str = ""
            for x in range(self.width):
                tile = self.tiles[y][x]
                row_str += symbols.get(tile.tile_type, '?')
            print(row_str)
        print()
