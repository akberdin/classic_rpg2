"""
Модуль подземелий и шахт

Содержит систему генерации и управления подземельями и NPC.
"""

from game.dungeon.tiles import DungeonTileType, DungeonTile
from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.generator import DungeonGenerator
from game.dungeon.manager import DungeonManager

__all__ = [
    'DungeonTileType',
    'DungeonTile',
    'DungeonMap',
    'DungeonGenerator',
    'DungeonManager',
]
