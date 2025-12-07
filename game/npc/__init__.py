"""
Пакет NPC (неигровых персонажей)

Экспортирует все классы NPC для удобного импорта.
"""
from game.npc.base import NPC
from game.npc.guard import Guard
from game.npc.merchant import Merchant, MagicMerchant, WarriorMerchant
from game.npc.mage import MagePatrol
from game.npc.hostile import Bandit, Undead
from game.npc.worker import Miner
from game.npc.unique import Alchemist, Hunter, Necromancer
from game.npc.animal import Wolf, Bear, Deer

__all__ = [
    'NPC',
    'Guard',
    'Merchant',
    'MagicMerchant',
    'WarriorMerchant',
    'MagePatrol',
    'Bandit',
    'Undead',
    'Miner',
    'Alchemist',
    'Hunter',
    'Necromancer',
    'Wolf',
    'Bear',
    'Deer'
]
