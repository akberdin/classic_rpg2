"""
Типы клеток для подземелий и шахт
"""
from enum import Enum


class DungeonDepthType(Enum):
    """Типы глубины подземелий (руины)"""
    BASEMENT = "basement"              # Подвал
    DARK_BASEMENT = "dark_basement"    # Темный подвал
    GLOOMY_BASEMENT = "gloomy_basement"  # Мрачный подвал
    ABYSS = "abyss"                    # Преисподня


class MineDepthType(Enum):
    """Типы глубины шахт"""
    MINE = "mine"                # Шахта
    DARK_MINE = "dark_mine"      # Темная шахта
    GLOOMY_MINE = "gloomy_mine"  # Мрачная шахта
    ABYSS = "abyss"              # Преисподня


def get_dungeon_depth_type(depth: int) -> DungeonDepthType:
    """
    Определить тип подземелья по глубине (fallback если нет конфига)

    Args:
        depth: Текущая глубина (1-based)

    Returns:
        DungeonDepthType: Тип подземелья
    """
    if depth <= 2:
        return DungeonDepthType.BASEMENT
    elif depth <= 4:
        return DungeonDepthType.DARK_BASEMENT
    elif depth <= 6:
        return DungeonDepthType.GLOOMY_BASEMENT
    else:
        return DungeonDepthType.ABYSS


def get_mine_depth_type(depth: int) -> MineDepthType:
    """
    Определить тип шахты по глубине (fallback если нет конфига)

    Args:
        depth: Текущая глубина (1-based)

    Returns:
        MineDepthType: Тип шахты
    """
    if depth <= 2:
        return MineDepthType.MINE
    elif depth <= 4:
        return MineDepthType.DARK_MINE
    elif depth <= 6:
        return MineDepthType.GLOOMY_MINE
    else:
        return MineDepthType.ABYSS


def get_depth_type_from_string(floor_type: str, is_mine: bool = False):
    """
    Получить тип глубины из строки конфига

    Args:
        floor_type: Строка типа этажа из конфига (basement, dark_basement и т.д.)
        is_mine: True если это шахта

    Returns:
        DungeonDepthType или MineDepthType
    """
    if is_mine:
        mapping = {
            "mine": MineDepthType.MINE,
            "dark_mine": MineDepthType.DARK_MINE,
            "gloomy_mine": MineDepthType.GLOOMY_MINE,
            "abyss": MineDepthType.ABYSS,
        }
        return mapping.get(floor_type, MineDepthType.MINE)
    else:
        mapping = {
            "basement": DungeonDepthType.BASEMENT,
            "dark_basement": DungeonDepthType.DARK_BASEMENT,
            "gloomy_basement": DungeonDepthType.GLOOMY_BASEMENT,
            "abyss": DungeonDepthType.ABYSS,
        }
        return mapping.get(floor_type, DungeonDepthType.BASEMENT)


# Названия типов глубины для отображения
DUNGEON_DEPTH_NAMES = {
    DungeonDepthType.BASEMENT: "Подвал",
    DungeonDepthType.DARK_BASEMENT: "Темный подвал",
    DungeonDepthType.GLOOMY_BASEMENT: "Мрачный подвал",
    DungeonDepthType.ABYSS: "Преисподня",
}

MINE_DEPTH_NAMES = {
    MineDepthType.MINE: "Шахта",
    MineDepthType.DARK_MINE: "Темная шахта",
    MineDepthType.GLOOMY_MINE: "Мрачная шахта",
    MineDepthType.ABYSS: "Преисподня",
}


def get_depth_type_name(depth_type) -> str:
    """
    Получить название типа глубины

    Args:
        depth_type: DungeonDepthType или MineDepthType

    Returns:
        str: Локализованное название
    """
    if isinstance(depth_type, DungeonDepthType):
        return DUNGEON_DEPTH_NAMES.get(depth_type, "Подвал")
    elif isinstance(depth_type, MineDepthType):
        return MINE_DEPTH_NAMES.get(depth_type, "Шахта")
    return "Неизвестно"


class DungeonTileType(Enum):
    """Типы клеток подземелья"""
    # Базовые типы
    WALL = "wall"              # Стена (непроходима)
    FLOOR = "floor"            # Пол (проходим)
    CORRIDOR = "corridor"      # Коридор (проходим)

    # Специальные типы
    ENTRANCE = "entrance"      # Точка входа
    EXIT = "exit"              # Точка выхода
    STAIRS_DOWN = "stairs_down"  # Лестница на следующий уровень
    STAIRS_UP = "stairs_up"    # Лестница на предыдущий уровень

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

    # Останки врагов
    REMAINS = "remains"        # Останки врага (проходимы, можно обыскать)
    REMAINS_LOOTED = "remains_looted"  # Обысканные останки


# Цвета для временного отображения (градиент серого)
DUNGEON_TILE_COLORS = {
    # Базовые
    DungeonTileType.WALL: (20, 20, 20),            # Почти черный
    DungeonTileType.FLOOR: (80, 80, 80),           # Темно-серый
    DungeonTileType.CORRIDOR: (70, 70, 70),        # Чуть темнее пола

    # Специальные
    DungeonTileType.ENTRANCE: (100, 150, 100),     # Зеленоватый
    DungeonTileType.EXIT: (150, 100, 100),         # Красноватый (выход)
    DungeonTileType.STAIRS_DOWN: (100, 100, 150),  # Синеватый (вниз)
    DungeonTileType.STAIRS_UP: (150, 150, 100),    # Желтоватый (вверх)

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

    # Останки врагов
    DungeonTileType.REMAINS: (120, 80, 80),        # Красноватый (кровь)
    DungeonTileType.REMAINS_LOOTED: (80, 60, 60),  # Темнее (обысканы)
}

# Проходимость клеток
PASSABLE_DUNGEON_TILES = [
    DungeonTileType.FLOOR,
    DungeonTileType.CORRIDOR,
    DungeonTileType.ENTRANCE,
    DungeonTileType.EXIT,
    DungeonTileType.STAIRS_DOWN,
    DungeonTileType.STAIRS_UP,
    DungeonTileType.TRAP,
    DungeonTileType.TRAP_TRIGGERED,
    DungeonTileType.STASH,
    DungeonTileType.STASH_LOOTED,
    DungeonTileType.BONES,
    DungeonTileType.ALTAR,
    DungeonTileType.ORE_VEIN,
    DungeonTileType.REMAINS,
    DungeonTileType.REMAINS_LOOTED,
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
        self.remains_data = None  # Данные останков (если это останки врага)

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

    def is_stairs_down(self) -> bool:
        """Это лестница вниз?"""
        return self.tile_type == DungeonTileType.STAIRS_DOWN

    def is_stairs_up(self) -> bool:
        """Это лестница вверх?"""
        return self.tile_type == DungeonTileType.STAIRS_UP

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
