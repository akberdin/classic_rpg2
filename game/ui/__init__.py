"""
UI модуль - пользовательский интерфейс игры.

Содержит:
- Базовые компоненты (UIScaler, UIHelper)
- Окна интерфейса (InventoryWindow, TradeWindow и др.)

Для обратной совместимости все классы реэкспортируются из оригинального ui.py.
Новые модули доступны в game.ui.base и game.ui.windows.
"""

# Базовые компоненты из нового модуля
from game.ui.base import UIScaler, UIHelper

# Для обратной совместимости импортируем все окна из старого ui.py
# По мере рефакторинга окна будут перемещаться в game.ui.windows
from game.ui_legacy import (
    HelpWindow,
    InventoryWindow,
    TradeWindow,
    CharacterWindow,
    SkillBookWindow,
    LootWindow,
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
    'QuestWindow',
    'RandomEventWindow',
    'CheatMenuWindow',
]
