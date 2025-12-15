"""
Генератор цепочек квестов (крафтовые квесты)
"""
import random
from ..models import Quest, QuestObjective, QuestType, QuestDifficulty
from ..quest_data import (
    BLACKSMITH_CRAFT_QUESTS,
    ALCHEMIST_CRAFT_QUESTS,
    LEATHERWORKER_CRAFT_QUESTS,
    HUNTER_CRAFT_QUESTS,
    MAGE_CRAFT_QUESTS,
    CRAFT_ITEM_KEY_TO_NAME
)
from .utils import get_player_rank


def get_available_chain_quests(quest_manager, player_level, location_type, count=1):
    """
    Получить доступные квесты из цепочек для локации

    Args:
        quest_manager: Менеджер квестов (для проверки завершенных квестов)
        player_level: Уровень игрока
        location_type: Тип локации ('village', 'city', 'magic_school')
        count: Количество квестов для генерации

    Returns:
        list: Список доступных квестов из цепочек
    """
    player_rank = get_player_rank(player_level)
    completed_quest_ids = quest_manager.get_completed_quest_ids()

    # Выбираем пулы квестов в зависимости от типа локации
    quest_pools = _get_quest_pools_for_location(location_type)

    available_quests = []

    for pool in quest_pools:
        chain_quests = _get_available_from_pool(pool, completed_quest_ids, player_rank)
        available_quests.extend(chain_quests)

    # Перемешиваем и возвращаем нужное количество
    random.shuffle(available_quests)
    return available_quests[:count]


def _get_quest_pools_for_location(location_type):
    """
    Получить пулы квестов для типа локации

    Args:
        location_type: Тип локации

    Returns:
        list: Список словарей с шаблонами квестов
    """
    from game.constants import LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL

    if location_type == LOCATION_VILLAGE:
        return [
            BLACKSMITH_CRAFT_QUESTS,
            ALCHEMIST_CRAFT_QUESTS,
            LEATHERWORKER_CRAFT_QUESTS,
            HUNTER_CRAFT_QUESTS
        ]
    elif location_type == LOCATION_CITY:
        return [
            BLACKSMITH_CRAFT_QUESTS,
            ALCHEMIST_CRAFT_QUESTS,
            LEATHERWORKER_CRAFT_QUESTS,
            HUNTER_CRAFT_QUESTS,
            MAGE_CRAFT_QUESTS
        ]
    elif location_type == LOCATION_MAGIC_SCHOOL:
        return [
            MAGE_CRAFT_QUESTS,
            ALCHEMIST_CRAFT_QUESTS
        ]

    return []


def _get_available_from_pool(quest_pool, completed_quest_ids, player_rank):
    """
    Получить доступные квесты из пула

    Args:
        quest_pool: Словарь шаблонов квестов
        completed_quest_ids: Множество ID завершенных квестов
        player_rank: Ранг игрока

    Returns:
        list: Список доступных квестов
    """
    available = []

    for quest_key, quest_data in quest_pool.items():
        # Проверяем ранг
        min_rank = quest_data.get('min_rank', 1)
        if player_rank < min_rank:
            continue

        # Проверяем, не завершен ли уже этот квест
        if quest_key in completed_quest_ids:
            continue

        # Проверяем предыдущий квест в цепочке
        requires_quest = quest_data.get('requires_quest')
        if requires_quest and requires_quest not in completed_quest_ids:
            continue

        # Создаем объект квеста
        quest = _create_chain_quest(quest_key, quest_data)
        if quest:
            available.append(quest)

    return available


def _create_chain_quest(quest_key, quest_data):
    """
    Создать квест из шаблона цепочки

    Args:
        quest_key: Ключ квеста
        quest_data: Данные шаблона квеста

    Returns:
        Quest: Объект квеста или None
    """
    craft_item = quest_data.get('craft_item')
    quantity = quest_data.get('quantity', 1)

    # Получаем название предмета для крафта
    item_display_name = CRAFT_ITEM_KEY_TO_NAME.get(craft_item, craft_item)

    # Создаем цель квеста
    objective = QuestObjective(
        f"Создать {item_display_name} x{quantity}",
        required_count=quantity
    )

    # Определяем сложность по шагу цепочки
    chain_step = quest_data.get('chain_step', 1)
    if chain_step <= 2:
        difficulty = QuestDifficulty.EASY
    elif chain_step <= 3:
        difficulty = QuestDifficulty.MEDIUM
    else:
        difficulty = QuestDifficulty.HARD

    # Рассчитываем награды
    base_exp = 50 + (chain_step * 30)
    base_gold = 20 + (chain_step * 15)
    rewards = {
        'exp': int(base_exp * difficulty.reward_multiplier),
        'gold': int(base_gold * difficulty.reward_multiplier)
    }

    # Выбираем случайное название и описание
    quest_name = random.choice(quest_data['quest_names'])
    description = random.choice(quest_data['descriptions'])

    quest = Quest(
        quest_id=quest_key,
        name=f"[Цепочка] {quest_name}",
        description=description,
        objectives=[objective],
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,  # Крафтовые квесты - тип сбора
        difficulty=difficulty,
        giver_location="Мастер",
        min_rank=quest_data.get('min_rank', 1),
        chain_id=quest_data.get('chain_id'),
        chain_step=chain_step,
        requires_quest=quest_data.get('requires_quest')
    )

    # Устанавливаем целевой предмет для отслеживания крафта
    quest.target_item = craft_item
    quest.is_craft_quest = True

    return quest


def get_next_chain_quest(quest_manager, completed_quest_id):
    """
    Получить следующий квест в цепочке после завершения текущего

    Args:
        quest_manager: Менеджер квестов
        completed_quest_id: ID завершенного квеста

    Returns:
        Quest или None: Следующий квест в цепочке
    """
    # Ищем квест, который требует завершенный квест
    all_pools = [
        BLACKSMITH_CRAFT_QUESTS,
        ALCHEMIST_CRAFT_QUESTS,
        LEATHERWORKER_CRAFT_QUESTS,
        HUNTER_CRAFT_QUESTS,
        MAGE_CRAFT_QUESTS
    ]

    for pool in all_pools:
        for quest_key, quest_data in pool.items():
            if quest_data.get('requires_quest') == completed_quest_id:
                # Проверяем, не завершен ли уже этот квест
                if quest_key not in quest_manager.completed_quest_ids:
                    return _create_chain_quest(quest_key, quest_data)

    return None
