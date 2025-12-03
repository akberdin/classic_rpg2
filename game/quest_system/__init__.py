"""
Модульная система квестов для RPG игры

Включает:
- models: Базовые модели данных (Quest, QuestObjective, Achievement и т.д.)
- quest_data: Константы и шаблоны квестов
- generators: Модули для генерации квестов и расчета наград
- managers: Менеджеры квестов и достижений
- factories: Фабрики для создания специальных квестов
"""

from .models import (
    QuestStatus,
    QuestType,
    QuestDifficulty,
    QuestObjective,
    Quest,
    AchievementRarity,
    Achievement
)

from .quest_data import (
    ENEMY_KEYWORDS,
    RESOURCE_KEYWORDS,
    ITEM_KEY_TO_NAME,
    CITY_GATHER_QUESTS,
    VILLAGE_GATHER_QUESTS,
    HUNTER_GATHER_QUESTS,
    NECROMANCER_GATHER_QUESTS,
    ALCHEMIST_GATHER_QUESTS,
    CITY_KILL_QUESTS,
    VILLAGE_KILL_QUESTS,
    HUNTER_KILL_QUESTS,
    NECROMANCER_KILL_QUESTS
)

from .managers import (
    QuestManager,
    AchievementManager
)

from .factories import (
    create_starter_quests,
    auto_assign_starter_quests,
    create_unique_quests,
    get_unique_quest_for_location
)

from .generators.location import (
    generate_quests_for_location,
    generate_city_quests,
    generate_village_quests,
    generate_hunter_quests,
    generate_necromancer_quests,
    generate_alchemist_quests
)

from .generators.npc import (
    create_alchemist_npc_quests,
    create_hunter_npc_quests
)

__all__ = [
    # Models
    'QuestStatus',
    'QuestType',
    'QuestDifficulty',
    'QuestObjective',
    'Quest',
    'AchievementRarity',
    'Achievement',
    # Quest Data
    'ENEMY_KEYWORDS',
    'RESOURCE_KEYWORDS',
    'ITEM_KEY_TO_NAME',
    'CITY_GATHER_QUESTS',
    'VILLAGE_GATHER_QUESTS',
    'HUNTER_GATHER_QUESTS',
    'NECROMANCER_GATHER_QUESTS',
    'ALCHEMIST_GATHER_QUESTS',
    'CITY_KILL_QUESTS',
    'VILLAGE_KILL_QUESTS',
    'HUNTER_KILL_QUESTS',
    'NECROMANCER_KILL_QUESTS',
    # Managers
    'QuestManager',
    'AchievementManager',
    # Factories
    'create_starter_quests',
    'auto_assign_starter_quests',
    'create_unique_quests',
    'get_unique_quest_for_location',
    # Location Generators
    'generate_quests_for_location',
    'generate_city_quests',
    'generate_village_quests',
    'generate_hunter_quests',
    'generate_necromancer_quests',
    'generate_alchemist_quests',
    # NPC Generators
    'create_alchemist_npc_quests',
    'create_hunter_npc_quests'
]
