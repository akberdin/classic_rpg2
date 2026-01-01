"""
Окна пользовательского интерфейса.

Все окна извлечены из ui_legacy.py в отдельные модули.
"""

from game.ui.windows.base import BaseWindow
from game.ui.windows.help import HelpWindow
from game.ui.windows.inventory import InventoryWindow
from game.ui.windows.trade import TradeWindow
from game.ui.windows.character import CharacterWindow
from game.ui.windows.skill_book import SkillBookWindow
from game.ui.windows.loot import LootWindow, DungeonLootWindow
from game.ui.windows.resource_collection import ResourceCollectionWindow
from game.ui.windows.quest import QuestWindow
from game.ui.windows.random_event import RandomEventWindow
from game.ui.windows.cheat_menu import CheatMenuWindow
from game.ui.windows.interaction import InteractionWindow
from game.ui.windows.exit_confirmation import ExitConfirmationWindow
from game.ui.windows.settlement_menu import (
    SettlementMenuWindow,
    InquiryMenuWindow,
    InquiryResponseWindow
)
from game.ui.windows.combat_mode_selection import CombatModeSelectionWindow
from game.ui.windows.crafting import CraftingWindow
from game.ui.windows.npc_selection import NPCSelectionWindow
from game.ui.windows.dungeon_entry import DungeonEntryWindow, DungeonExitWindow, StairsMenuWindow

__all__ = [
    'BaseWindow',
    'HelpWindow',
    'InventoryWindow',
    'TradeWindow',
    'CharacterWindow',
    'SkillBookWindow',
    'LootWindow',
    'DungeonLootWindow',
    'ResourceCollectionWindow',
    'QuestWindow',
    'RandomEventWindow',
    'CheatMenuWindow',
    'InteractionWindow',
    'ExitConfirmationWindow',
    'SettlementMenuWindow',
    'InquiryMenuWindow',
    'InquiryResponseWindow',
    'CombatModeSelectionWindow',
    'CraftingWindow',
    'NPCSelectionWindow',
    'DungeonEntryWindow',
    'DungeonExitWindow',
    'StairsMenuWindow',
]
