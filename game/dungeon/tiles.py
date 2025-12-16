"""
Типы клеток для подземелий и шахт
"""
from enum import Enum


class DungeonTileType(Enum):
    """Типы клеток подземелья"""
    # Базовые типы
    WALL = "wall"              # Стена (непроходима)
    FLOOR = "floor"            # Пол (проходим)
    CORRIDOR = "corridor"      # Коридор (проходим)

    # Специальные типы
    ENTRANCE = "entrance"      # Точка входа
    EXIT = "exit"              # Точка выхода

    # Интерактивные типы
    TRAP = "trap"              # Ловушка (проходима, наносит урон)
    TRAP_TRIGGERED = "trap_triggered"  # Сработавшая ловушка
    STASH = "stash"            # Тайник (проходим, содержит лут)
    STASH_LOOTED = "stash_looted"  # Обысканный тайник

    # Декоративные типы
    RUBBLE = "rubble"          # Завалы (непроходимы)
    WATER = "water"            # Вода (непроходима)
    BONES = "bones"            # Кости (проходимы, декор)
    ALTAR = "altar"            # Алтарь (проходим, особое место)

    # Для шахт
    ORE_VEIN = "ore_vein"      # Рудная жила (проходима, можно добывать)
    MINECART = "minecart"      # Вагонетка (непроходима)
    SUPPORT = "support"        # Опора (непроходима)


# Цвета для временного отображения (градиент серого)
DUNGEON_TILE_COLORS = {
    # Базовые
    DungeonTileType.WALL: (20, 20, 20),            # Почти черный
    DungeonTileType.FLOOR: (80, 80, 80),           # Темно-серый
    DungeonTileType.CORRIDOR: (70, 70, 70),        # Чуть темнее пола

    # Специальные
    DungeonTileType.ENTRANCE: (100, 150, 100),     # Зеленоватый
    DungeonTileType.EXIT: (150, 100, 100),         # Красноватый (выход)

    # Интерактивные
    DungeonTileType.TRAP: (80, 80, 80),            # Как пол (скрытая)
    DungeonTileType.TRAP_TRIGGERED: (120, 80, 80), # Красноватый оттенок
    DungeonTileType.STASH: (100, 100, 60),         # Желтоватый
    DungeonTileType.STASH_LOOTED: (60, 60, 50),    # Тусклый

    # Декоративные
    DungeonTileType.RUBBLE: (40, 40, 40),          # Очень темный
    DungeonTileType.WATER: (30, 40, 60),           # Темно-синий
    DungeonTileType.BONES: (90, 90, 80),           # Светло-серый с желтизной
    DungeonTileType.ALTAR: (80, 60, 100),          # Фиолетовый оттенок

    # Для шахт
    DungeonTileType.ORE_VEIN: (100, 80, 60),       # Коричневатый
    DungeonTileType.MINECART: (50, 50, 50),        # Темный
    DungeonTileType.SUPPORT: (60, 45, 30),         # Деревянный
}

# Проходимость клеток
PASSABLE_DUNGEON_TILES = [
    DungeonTileType.FLOOR,
    DungeonTileType.CORRIDOR,
    DungeonTileType.ENTRANCE,
    DungeonTileType.EXIT,
    DungeonTileType.TRAP,
    DungeonTileType.TRAP_TRIGGERED,
    DungeonTileType.STASH,
    DungeonTileType.STASH_LOOTED,
    DungeonTileType.BONES,
    DungeonTileType.ALTAR,
    DungeonTileType.ORE_VEIN,
]


class DungeonTile:
    """Класс клетки подземелья"""

    def __init__(self, x: int, y: int, tile_type: DungeonTileType = DungeonTileType.WALL):
        """
        Инициализация клетки подземелья

        Args:
            x: Координата X
            y: Координата Y
            tile_type: Тип клетки
        """
        self.x = x
        self.y = y
        self.tile_type = tile_type
        self.explored = False  # Исследована ли клетка
        self.visible = False   # Видима ли сейчас

        # Дополнительные данные для интерактивных клеток
        self.trap_data = None   # Данные ловушки (если это ловушка)
        self.stash_data = None  # Данные тайника (если это тайник)
        self.ore_data = None    # Данные руды (если это рудная жила)

        # NPC на клетке
        self.npc = None

    def is_passable(self) -> bool:
        """Проверить, можно ли пройти через эту клетку"""
        return self.tile_type in PASSABLE_DUNGEON_TILES

    def get_color(self) -> tuple:
        """Получить цвет клетки для рендеринга"""
        return DUNGEON_TILE_COLORS.get(self.tile_type, (50, 50, 50))

    def is_entrance(self) -> bool:
        """Это точка входа?"""
        return self.tile_type == DungeonTileType.ENTRANCE

    def is_exit(self) -> bool:
        """Это точка выхода?"""
        return self.tile_type == DungeonTileType.EXIT

    def is_trap(self) -> bool:
        """Это ловушка?"""
        return self.tile_type == DungeonTileType.TRAP

    def is_stash(self) -> bool:
        """Это тайник?"""
        return self.tile_type == DungeonTileType.STASH

    def trigger_trap(self):
        """Активировать ловушку"""
        if self.tile_type == DungeonTileType.TRAP:
            self.tile_type = DungeonTileType.TRAP_TRIGGERED
            return True
        return False

    def loot_stash(self):
        """Обыскать тайник"""
        if self.tile_type == DungeonTileType.STASH:
            self.tile_type = DungeonTileType.STASH_LOOTED
            return True
        return False

    def __repr__(self):
        return f"DungeonTile({self.x}, {self.y}, {self.tile_type.value})"
