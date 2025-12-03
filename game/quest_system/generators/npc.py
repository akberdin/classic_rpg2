"""
Генераторы квестов для NPC
"""
import random
from ..models import Quest, QuestObjective, QuestType, QuestDifficulty


def create_alchemist_npc_quests(npc_name):
    """
    Создать квесты для алхимика

    Args:
        npc_name: Имя алхимика (для giver_location)

    Returns:
        list: Список квестов
    """
    quests = []

    # Квест на сбор ингредиентов
    gather_quest = Quest(
        quest_id=f"alchemist_gather_{random.randint(1000, 9999)}",
        name="Сбор ингредиентов",
        description="Алхимику нужны магические кристаллы для зелий.",
        objectives=[
            QuestObjective("Собрать магические кристаллы", 3)
        ],
        rewards={"exp": 150, "gold": 100},
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    )
    gather_quest.target_item = "magic_crystal"
    quests.append(gather_quest)

    # Квест на уничтожение нежити
    kill_quest = Quest(
        quest_id=f"alchemist_undead_{random.randint(1000, 9999)}",
        name="Очищение руин",
        description="Нежить в руинах мешает собирать редкие ингредиенты.",
        objectives=[
            QuestObjective("Уничтожить нежить", 5)
        ],
        rewards={"exp": 200, "gold": 150},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.HARD,
        giver_location=npc_name
    )
    kill_quest.target_enemy = "undead"
    quests.append(kill_quest)

    return quests


def create_hunter_npc_quests(npc_name):
    """
    Создать квесты для охотника

    Args:
        npc_name: Имя охотника (для giver_location)

    Returns:
        list: Список квестов
    """
    quests = []

    # Квест на уничтожение бандитов
    bandit_quest = Quest(
        quest_id=f"hunter_bandits_{random.randint(1000, 9999)}",
        name="Охота на бандитов",
        description="Бандиты угрожают путникам на дорогах. Необходимо их остановить.",
        objectives=[
            QuestObjective("Уничтожить бандитов", 5)
        ],
        rewards={"exp": 180, "gold": 120},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    )
    bandit_quest.target_enemy = "bandit"
    quests.append(bandit_quest)

    # Квест на охоту на волков
    wolf_quest = Quest(
        quest_id=f"hunter_wolves_{random.randint(1000, 9999)}",
        name="Волчья угроза",
        description="Волки нападают на стада. Нужно проредить их популяцию.",
        objectives=[
            QuestObjective("Убить волков", 6)
        ],
        rewards={"exp": 150, "gold": 100},
        quest_type=QuestType.KILL_ANIMALS,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    )
    wolf_quest.target_animal = "wolf"
    quests.append(wolf_quest)

    return quests
