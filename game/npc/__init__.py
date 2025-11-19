"""
Пакет NPC (неигровых персонажей)

Экспортирует все классы NPC для удобного импорта.
"""
from game.npc.base import NPC
from game.npc.guard import Guard
from game.npc.merchant import Merchant, MagicMerchant
from game.npc.mage import MagePatrol
from game.npc.hostile import Bandit, Undead
from game.npc.worker import Miner

__all__ = [
    'NPC',
    'Guard',
    'Merchant',
    'MagicMerchant',
    'MagePatrol',
    'Bandit',
    'Undead',
    'Miner'
]
