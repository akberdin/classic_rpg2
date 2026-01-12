"""
Модуль системы квестов.

Содержит классы для управления квестами:
- QuestType: Перечисление типов квестов
- QuestInstance: Экземпляр активного квеста у игрока
- QuestManager: Менеджер квестов игрока
"""

from game.quests.quest_types import QuestType, QUEST_SOURCE_LOCATIONS
from game.quests.quest_instance import QuestInstance
from game.quests.quest_manager import QuestManager

__all__ = [
    'QuestType',
    'QUEST_SOURCE_LOCATIONS',
    'QuestInstance',
    'QuestManager',
]
