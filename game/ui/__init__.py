"""
UI модуль - пользовательский интерфейс игры.

Содержит:
- Базовые компоненты (UIScaler, UIHelper)
- Окна интерфейса (InventoryWindow, TradeWindow и др.)

Все классы доступны через этот модуль для обратной совместимости.
"""

# Базовые компоненты
from game.ui.base import UIScaler, UIHelper

# Окна - импортируем из новых модулей
from game.ui.windows import (
    HelpWindow,
    InventoryWindow,
    TradeWindow,
    CharacterWindow,
    SkillBookWindow,
    LootWindow,
    DungeonLootWindow,
    QuestWindow,
    RandomEventWindow,
    CheatMenuWindow,
)

__all__ = [
    # Базовые компоненты
    'UIScaler',
    'UIHelper',
    # Окна
    'HelpWindow',
    'InventoryWindow',
    'TradeWindow',
    'CharacterWindow',
    'SkillBookWindow',
    'LootWindow',
    'DungeonLootWindow',
    'QuestWindow',
    'RandomEventWindow',
    'CheatMenuWindow',
]
