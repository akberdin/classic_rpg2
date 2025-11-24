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
from game.ui.windows.loot import LootWindow
from game.ui.windows.quest import QuestWindow
from game.ui.windows.random_event import RandomEventWindow
from game.ui.windows.cheat_menu import CheatMenuWindow

__all__ = [
    'BaseWindow',
    'HelpWindow',
    'InventoryWindow',
    'TradeWindow',
    'CharacterWindow',
    'SkillBookWindow',
    'LootWindow',
    'QuestWindow',
    'RandomEventWindow',
    'CheatMenuWindow',
]
