"""
Модуль подземелий и шахт

Содержит систему генерации и управления подземельями,
ловушками, тайниками и NPC.
"""

from game.dungeon.tiles import DungeonTileType, DungeonTile
from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.generator import DungeonGenerator
from game.dungeon.traps import Trap, TrapType, TrapManager
from game.dungeon.stashes import Stash, StashManager
from game.dungeon.manager import DungeonManager

__all__ = [
    'DungeonTileType',
    'DungeonTile',
    'DungeonMap',
    'DungeonGenerator',
    'Trap',
    'TrapType',
    'TrapManager',
    'Stash',
    'StashManager',
    'DungeonManager',
]
