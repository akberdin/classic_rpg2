"""
Генератор цепочек квестов (крафтовые квесты).

Цепочки привязаны к конкретным NPC-мастерам:
- Кузнец: кузнечное дело (города, деревни)
- Алхимик: зельеварение (города, деревни, школы магии)
- Скорняк: обработка шкур (деревни)
- Мастер охоты: охотничье снаряжение (деревни, города)
- Архимаг: магические предметы (школы магии)
"""
import json
import random
from pathlib import Path
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


# Карта пулов квестов по имени
CHAIN_POOLS = {
    'BLACKSMITH_CRAFT_QUESTS': BLACKSMITH_CRAFT_QUESTS,
    'ALCHEMIST_CRAFT_QUESTS': ALCHEMIST_CRAFT_QUESTS,
    'LEATHERWORKER_CRAFT_QUESTS': LEATHERWORKER_CRAFT_QUESTS,
    'HUNTER_CRAFT_QUESTS': HUNTER_CRAFT_QUESTS,
    'MAGE_CRAFT_QUESTS': MAGE_CRAFT_QUESTS
}


def _load_chain_config():
    """Загрузить конфигурацию цепочек квестов"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'quest_config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('quest_chains', {})
    except Exception:
        return {}


def get_chain_masters_for_location(location_type):
    """
    Получить список мастеров цепочек для типа локации.

    Args:
        location_type: Тип локации (строка: 'city', 'village', 'magic_school')

    Returns:
        list: Список словарей с информацией о мастерах
              [{'id': 'blacksmith', 'npc_name': 'Кузнец', 'description': '...'}]
    """
    chain_config = _load_chain_config()
    masters = []

    for chain_id, chain_data in chain_config.items():
        locations = chain_data.get('locations', [])
        if location_type in locations:
            masters.append({
                'id': chain_id,
                'npc_name': chain_data.get('npc_name', 'Мастер'),
                'npc_type': chain_data.get('npc_type', 'neutral'),
                'description': chain_data.get('description', ''),
                'unlock_condition': chain_data.get('unlock_condition', 'player_level >= 1')
            })

    return masters


def get_chain_quests_for_master(quest_manager, player_level, master_id):
    """
    Получить доступные квесты цепочки для конкретного мастера.

    Args:
        quest_manager: Менеджер квестов
        player_level: Уровень игрока
        master_id: ID мастера (например 'blacksmith', 'alchemist')

    Returns:
        list: Список доступных квестов от этого мастера
    """
    chain_config = _load_chain_config()
    master_data = chain_config.get(master_id)

    if not master_data:
        return []

    player_rank = get_player_rank(player_level)
    completed_quest_ids = quest_manager.get_completed_quest_ids()

    # Получаем пулы квестов для этого мастера
    chain_pools = master_data.get('chain_pools', [])
    npc_name = master_data.get('npc_name', 'Мастер')

    available_quests = []

    for pool_name in chain_pools:
        pool = CHAIN_POOLS.get(pool_name, {})
        quests = _get_available_from_pool(pool, completed_quest_ids, player_rank, npc_name)
        available_quests.extend(quests)

    return available_quests


def get_chain_progress(quest_manager, master_id):
    """
    Получить прогресс цепочки квестов для мастера.

    Args:
        quest_manager: Менеджер квестов
        master_id: ID мастера

    Returns:
        dict: {'completed': int, 'total': int, 'current_step': int, 'chain_name': str}
    """
    chain_config = _load_chain_config()
    master_data = chain_config.get(master_id)

    if not master_data:
        return {'completed': 0, 'total': 0, 'current_step': 0, 'chain_name': ''}

    completed_quest_ids = quest_manager.get_completed_quest_ids()
    chain_pools = master_data.get('chain_pools', [])

    completed = 0
    total = 0
    current_step = 1

    for pool_name in chain_pools:
        pool = CHAIN_POOLS.get(pool_name, {})
        for quest_key, quest_data in pool.items():
            total += 1
            if quest_key in completed_quest_ids:
                completed += 1
                step = quest_data.get('chain_step', 1)
                if step >= current_step:
                    current_step = step + 1

    return {
        'completed': completed,
        'total': total,
        'current_step': current_step,
        'chain_name': master_data.get('description', '')
    }


def get_available_chain_quests(quest_manager, player_level, location_type, count=1):
    """
    Получить доступные квесты из цепочек для локации.

    Возвращает квесты от всех мастеров, доступных в этой локации.

    Args:
        quest_manager: Менеджер квестов (для проверки завершенных квестов)
        player_level: Уровень игрока
        location_type: Тип локации ('village', 'city', 'magic_school')
        count: Количество квестов для генерации

    Returns:
        list: Список доступных квестов из цепочек
    """
    # Конвертируем константу локации в строку
    location_str = _convert_location_type(location_type)

    masters = get_chain_masters_for_location(location_str)
    available_quests = []

    for master in masters:
        # Проверяем условие разблокировки
        if not _check_unlock_condition(master.get('unlock_condition'), player_level):
            continue

        quests = get_chain_quests_for_master(quest_manager, player_level, master['id'])
        available_quests.extend(quests)

    # Перемешиваем и возвращаем нужное количество
    random.shuffle(available_quests)
    return available_quests[:count]


def _convert_location_type(location_type):
    """Преобразовать константу типа локации в строку"""
    from game.constants import (
        LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL,
        LOCATION_MINE, LOCATION_RUINS, LOCATION_BANDIT_CAMP
    )

    mapping = {
        LOCATION_CITY: 'city',
        LOCATION_VILLAGE: 'village',
        LOCATION_MAGIC_SCHOOL: 'magic_school',
        LOCATION_MINE: 'mine',
        LOCATION_RUINS: 'ruins',
        LOCATION_BANDIT_CAMP: 'bandit_camp'
    }

    return mapping.get(location_type, location_type)


def _check_unlock_condition(condition, player_level):
    """
    Проверить условие разблокировки цепочки.

    Args:
        condition: Строка условия (например 'player_level >= 5')
        player_level: Уровень игрока

    Returns:
        bool: True если условие выполнено
    """
    if not condition:
        return True

    try:
        # Безопасное вычисление простых условий
        return eval(condition, {'player_level': player_level})
    except Exception:
        return True


def _get_available_from_pool(quest_pool, completed_quest_ids, player_rank, npc_name):
    """
    Получить доступные квесты из пула.

    Args:
        quest_pool: Словарь шаблонов квестов
        completed_quest_ids: Множество ID завершенных квестов
        player_rank: Ранг игрока
        npc_name: Имя NPC-квестодателя

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
        quest = _create_chain_quest(quest_key, quest_data, npc_name)
        if quest:
            available.append(quest)

    return available


def _create_chain_quest(quest_key, quest_data, npc_name="Мастер"):
    """
    Создать квест из шаблона цепочки.

    Args:
        quest_key: Ключ квеста
        quest_data: Данные шаблона квеста
        npc_name: Имя NPC-квестодателя

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
    chain_id = quest_data.get('chain_id', 'unknown')

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

    # Формируем название с указанием шага цепочки
    formatted_name = f"[{npc_name} {chain_step}/5] {quest_name}"

    quest = Quest(
        quest_id=quest_key,
        name=formatted_name,
        description=f"{description}\n\n[Цепочка: {npc_name}, шаг {chain_step}]",
        objectives=[objective],
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,  # Крафтовые квесты - тип сбора
        difficulty=difficulty,
        giver_location=npc_name,
        min_rank=quest_data.get('min_rank', 1),
        chain_id=chain_id,
        chain_step=chain_step,
        requires_quest=quest_data.get('requires_quest')
    )

    # Устанавливаем целевой предмет для отслеживания крафта
    quest.target_item = craft_item
    quest.is_craft_quest = True
    quest.chain_master = npc_name  # Запоминаем кто выдал квест

    return quest


def get_next_chain_quest(quest_manager, completed_quest_id):
    """
    Получить следующий квест в цепочке после завершения текущего.

    Args:
        quest_manager: Менеджер квестов
        completed_quest_id: ID завершенного квеста

    Returns:
        Quest или None: Следующий квест в цепочке
    """
    # Ищем квест, который требует завершенный квест
    for pool_name, pool in CHAIN_POOLS.items():
        for quest_key, quest_data in pool.items():
            if quest_data.get('requires_quest') == completed_quest_id:
                # Проверяем, не завершен ли уже этот квест
                if quest_key not in quest_manager.completed_quest_ids:
                    # Определяем NPC-мастера
                    npc_name = _get_npc_name_for_pool(pool_name)
                    return _create_chain_quest(quest_key, quest_data, npc_name)

    return None


def _get_npc_name_for_pool(pool_name):
    """Получить имя NPC для пула квестов"""
    pool_to_npc = {
        'BLACKSMITH_CRAFT_QUESTS': 'Кузнец',
        'ALCHEMIST_CRAFT_QUESTS': 'Алхимик',
        'LEATHERWORKER_CRAFT_QUESTS': 'Скорняк',
        'HUNTER_CRAFT_QUESTS': 'Мастер охоты',
        'MAGE_CRAFT_QUESTS': 'Архимаг'
    }
    return pool_to_npc.get(pool_name, 'Мастер')
