"""
Генераторы квестов для локаций
"""
import random
from game.config.config_loader import get_quest_config
from ..models import Quest, QuestObjective, QuestType, QuestDifficulty
from ..quest_data import (
    CITY_GATHER_QUESTS,
    CITY_KILL_QUESTS,
    VILLAGE_GATHER_QUESTS,
    VILLAGE_KILL_QUESTS,
    HUNTER_GATHER_QUESTS,
    HUNTER_KILL_QUESTS,
    NECROMANCER_GATHER_QUESTS,
    NECROMANCER_KILL_QUESTS,
    ALCHEMIST_GATHER_QUESTS
)
from .utils import get_player_rank, filter_by_rank
from .rewards import calculate_gather_quest_rewards, calculate_kill_quest_rewards


def generate_quests_for_location(location_name, location_id, player_level=1, count=3, location_type=None):
    """
    Сгенерировать несколько квестов для локации

    Args:
        location_name: Название локации
        location_id: ID локации
        player_level: Уровень игрока
        count: Количество квестов
        location_type: Тип локации (для специализированных генераторов)

    Returns:
        list: Список квестов
    """
    from game.constants import LOCATION_CITY, LOCATION_VILLAGE

    # Используем специализированные генераторы если известен тип локации
    if location_type == LOCATION_CITY:
        return generate_city_quests(location_name, location_id, player_level, count)
    elif location_type == LOCATION_VILLAGE:
        return generate_village_quests(location_name, location_id, player_level, count)

    # Fallback на старый метод для других типов локаций
    quests = []
    for _ in range(count):
        # Простой генератор (можно расширить если нужно)
        quest = _generate_simple_quest(location_name, location_id, player_level)
        quests.append(quest)
    return quests


def generate_city_quests(location_name, location_id, player_level=1, count=3):
    """
    Генерация квестов для городов
    Города: серебро, золото, мифрил, бандиты 3-4 рангов, нежить 3-4 рангов, шкуры медведей и оленей
    """
    player_rank = get_player_rank(player_level)

    # Фильтруем доступные ресурсы по рангу игрока
    available_resources = filter_by_rank(CITY_GATHER_QUESTS, player_rank)
    available_enemies = filter_by_rank(CITY_KILL_QUESTS, player_rank)

    # Если нет доступных квестов, возвращаем пустой список
    if not available_resources and not available_enemies:
        return []

    quests = []
    quest_types = ['gather', 'gather', 'kill']  # Больше квестов на сбор
    random.shuffle(quest_types)

    # Отслеживаем уже использованные ресурсы и врагов для избежания дублирования
    used_resources = set()
    used_enemies = set()

    # Гарантируем хотя бы один квест на части животных
    animal_parts = ['bear_hide', 'deer_hide', 'bear_meat', 'deer_meat', 'wolf_hide', 'bear_fang', 'wolf_fang']
    available_animal_parts = [k for k in animal_parts if k in available_resources]
    animal_quest_added = False

    # Определяем диапазон сложности в зависимости от ранга игрока
    if player_rank >= 3:
        difficulty_range = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
    elif player_rank == 2:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
    else:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM]

    for i in range(min(count, len(quest_types))):
        if quest_types[i] == 'gather' and available_resources:
            # Получаем список доступных ресурсов (исключая уже использованные)
            remaining_resources = [k for k in available_resources.keys() if k not in used_resources]
            if not remaining_resources:
                continue

            # Если это первый квест на сбор и мы еще не добавили квест на части животных
            remaining_animal_parts = [k for k in available_animal_parts if k not in used_resources]
            if not animal_quest_added and remaining_animal_parts and random.random() < 0.7:
                resource_key = random.choice(remaining_animal_parts)
                animal_quest_added = True
            else:
                # Выбираем из оставшихся ресурсов
                resource_key = random.choice(remaining_resources)
                if resource_key in animal_parts:
                    animal_quest_added = True

            used_resources.add(resource_key)

            quest = _generate_gather_quest_from_template(
                resource_key, available_resources[resource_key],
                location_name, location_id, player_level,
                difficulty_range=difficulty_range
            )
            quests.append(quest)
        elif available_enemies:
            # Получаем список доступных врагов (исключая уже использованных)
            remaining_enemies = [k for k in available_enemies.keys() if k not in used_enemies]
            if not remaining_enemies:
                continue

            enemy_key = random.choice(remaining_enemies)
            used_enemies.add(enemy_key)

            quest = _generate_kill_quest_from_template(
                enemy_key, available_enemies[enemy_key],
                location_name, location_id, player_level
            )
            quests.append(quest)
    return quests


def generate_village_quests(location_name, location_id, player_level=1, count=3):
    """
    Генерация квестов для деревень
    Деревни: шкуры волков, зубы и мясо животных, волки, медведи, железо, медь, бандиты 1-2, нежить 1-2
    """
    player_rank = get_player_rank(player_level)

    # Фильтруем доступные ресурсы по рангу игрока
    available_resources = filter_by_rank(VILLAGE_GATHER_QUESTS, player_rank)
    available_enemies = filter_by_rank(VILLAGE_KILL_QUESTS, player_rank)

    # Если нет доступных квестов, возвращаем пустой список
    if not available_resources and not available_enemies:
        return []

    quests = []
    quest_types = ['gather', 'kill', 'gather']  # Смешанные квесты
    random.shuffle(quest_types)

    # Отслеживаем уже использованные ресурсы и врагов для избежания дублирования
    used_resources = set()
    used_enemies = set()

    # Гарантируем хотя бы один квест на части животных
    animal_parts = ['wolf_hide', 'wolf_fang', 'bear_meat', 'deer_meat', 'deer_hide', 'bear_hide', 'bear_fang']
    available_animal_parts = [k for k in animal_parts if k in available_resources]
    animal_quest_added = False

    # Определяем диапазон сложности в зависимости от ранга игрока
    if player_rank >= 2:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
    else:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM]

    for i in range(min(count, len(quest_types))):
        if quest_types[i] == 'gather' and available_resources:
            # Получаем список доступных ресурсов (исключая уже использованные)
            remaining_resources = [k for k in available_resources.keys() if k not in used_resources]
            if not remaining_resources:
                continue

            # Если это первый квест на сбор и мы еще не добавили квест на части животных
            remaining_animal_parts = [k for k in available_animal_parts if k not in used_resources]
            if not animal_quest_added and remaining_animal_parts and random.random() < 0.7:
                resource_key = random.choice(remaining_animal_parts)
                animal_quest_added = True
            else:
                # Выбираем из оставшихся ресурсов
                resource_key = random.choice(remaining_resources)
                if resource_key in animal_parts:
                    animal_quest_added = True

            used_resources.add(resource_key)

            quest = _generate_gather_quest_from_template(
                resource_key, available_resources[resource_key],
                location_name, location_id, player_level,
                difficulty_range=difficulty_range
            )
            quests.append(quest)
        elif available_enemies:
            # Получаем список доступных врагов (исключая уже использованных)
            remaining_enemies = [k for k in available_enemies.keys() if k not in used_enemies]
            if not remaining_enemies:
                continue

            enemy_key = random.choice(remaining_enemies)
            used_enemies.add(enemy_key)

            quest = _generate_kill_quest_from_template(
                enemy_key, available_enemies[enemy_key],
                location_name, location_id, player_level
            )
            quests.append(quest)
    return quests


def generate_hunter_quests(location_name, location_id, player_level=1, count=3):
    """
    Генерация квестов для охотников
    Охотники: шкуры, зубы и мясо всех животных, убийство всех животных
    """
    player_rank = get_player_rank(player_level)

    # Фильтруем доступные ресурсы по рангу игрока
    available_resources = filter_by_rank(HUNTER_GATHER_QUESTS, player_rank)
    available_enemies = filter_by_rank(HUNTER_KILL_QUESTS, player_rank)

    # Если нет доступных квестов, возвращаем пустой список
    if not available_resources and not available_enemies:
        return []

    quests = []
    quest_types = ['gather', 'kill', 'gather']
    random.shuffle(quest_types)

    # Отслеживаем уже использованные ресурсы и врагов для избежания дублирования
    used_resources = set()
    used_enemies = set()

    # Определяем диапазон сложности в зависимости от ранга игрока
    if player_rank >= 3:
        difficulty_range = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
    elif player_rank >= 2:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
    else:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM]

    for i in range(min(count, len(quest_types))):
        if quest_types[i] == 'gather' and available_resources:
            # Получаем список доступных ресурсов (исключая уже использованные)
            remaining_resources = [k for k in available_resources.keys() if k not in used_resources]
            if not remaining_resources:
                continue

            resource_key = random.choice(remaining_resources)
            used_resources.add(resource_key)

            quest = _generate_gather_quest_from_template(
                resource_key, available_resources[resource_key],
                location_name, location_id, player_level,
                difficulty_range=difficulty_range
            )
            quests.append(quest)
        elif available_enemies:
            # Получаем список доступных врагов (исключая уже использованных)
            remaining_enemies = [k for k in available_enemies.keys() if k not in used_enemies]
            if not remaining_enemies:
                continue

            enemy_key = random.choice(remaining_enemies)
            used_enemies.add(enemy_key)

            quest = _generate_kill_quest_from_template(
                enemy_key, available_enemies[enemy_key],
                location_name, location_id, player_level,
                is_animal=enemy_key in ['wolf', 'bear', 'deer']
            )
            quests.append(quest)
    return quests


def generate_necromancer_quests(location_name, location_id, player_level=1, count=2):
    """
    Генерация квестов для некроманта
    Некромант: артефакты, древние монеты, нежить 1-4 рангов
    """
    player_rank = get_player_rank(player_level)

    # Фильтруем доступные ресурсы по рангу игрока
    available_resources = filter_by_rank(NECROMANCER_GATHER_QUESTS, player_rank)
    available_enemies = filter_by_rank(NECROMANCER_KILL_QUESTS, player_rank)

    # Если нет доступных квестов, возвращаем пустой список
    if not available_resources and not available_enemies:
        return []

    quests = []
    quest_types = ['gather', 'kill']
    random.shuffle(quest_types)

    # Отслеживаем уже использованные ресурсы и врагов для избежания дублирования
    used_resources = set()
    used_enemies = set()

    # Определяем диапазон сложности в зависимости от ранга игрока
    # Некромант - высокоуровневый контент, но адаптируем под ранг
    if player_rank >= 4:
        difficulty_range = [QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
    elif player_rank >= 3:
        difficulty_range = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
    else:
        difficulty_range = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD]

    for i in range(min(count, len(quest_types))):
        if quest_types[i] == 'gather' and available_resources:
            # Получаем список доступных ресурсов (исключая уже использованные)
            remaining_resources = [k for k in available_resources.keys() if k not in used_resources]
            if not remaining_resources:
                continue

            resource_key = random.choice(remaining_resources)
            used_resources.add(resource_key)

            quest = _generate_gather_quest_from_template(
                resource_key, available_resources[resource_key],
                location_name, location_id, player_level,
                difficulty_range=difficulty_range
            )
            quests.append(quest)
        elif available_enemies:
            # Получаем список доступных врагов (исключая уже использованных)
            remaining_enemies = [k for k in available_enemies.keys() if k not in used_enemies]
            if not remaining_enemies:
                continue

            enemy_key = random.choice(remaining_enemies)
            used_enemies.add(enemy_key)

            quest = _generate_kill_quest_from_template(
                enemy_key, available_enemies[enemy_key],
                location_name, location_id, player_level
            )
            quests.append(quest)
    return quests


def generate_alchemist_quests(location_name, location_id, player_level=1, count=2):
    """
    Генерация квестов для алхимика
    Алхимик: зубы животных, древние свитки, магические кристаллы
    """
    player_rank = get_player_rank(player_level)

    # Фильтруем доступные ресурсы по рангу игрока
    available_resources = filter_by_rank(ALCHEMIST_GATHER_QUESTS, player_rank)

    # Если нет доступных квестов, возвращаем пустой список
    if not available_resources:
        return []

    quests = []

    # Отслеживаем уже использованные ресурсы для избежания дублирования
    used_resources = set()

    # Определяем диапазон сложности в зависимости от ранга игрока
    if player_rank >= 3:
        difficulty_range = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
    elif player_rank >= 2:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
    else:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM]

    for _ in range(count):
        # Получаем список доступных ресурсов (исключая уже использованные)
        remaining_resources = [k for k in available_resources.keys() if k not in used_resources]
        if not remaining_resources:
            break

        resource_key = random.choice(remaining_resources)
        used_resources.add(resource_key)

        quest = _generate_gather_quest_from_template(
            resource_key, available_resources[resource_key],
            location_name, location_id, player_level,
            difficulty_range=difficulty_range
        )
        quests.append(quest)
    return quests


def _generate_gather_quest_from_template(resource_key, resource_data, location_name, location_id,
                                         player_level, difficulty_range=None):
    """
    Генерация квеста на сбор с заданными параметрами

    Args:
        resource_key: Ключ ресурса
        resource_data: Данные о ресурсе из шаблонов
        location_name: Название локации
        location_id: ID локации
        player_level: Уровень игрока
        difficulty_range: Диапазон сложностей

    Returns:
        Quest: Сгенерированный квест
    """
    if difficulty_range is None:
        difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]

    difficulty = random.choice(difficulty_range)
    config = get_quest_config()

    # Получаем диапазон количества из конфига
    difficulty_name = difficulty.name.lower()
    amounts = config.get_quest_amount('gather', difficulty_name, default=[3, 5])
    min_amount, max_amount = amounts
    required_amount = random.randint(min_amount, max_amount)

    # Рассчитываем награды
    rewards = calculate_gather_quest_rewards(player_level, difficulty, required_amount)

    quest_name = random.choice(resource_data['quest_names'])
    description = random.choice(resource_data['descriptions'])
    quest_id = f"gather_{resource_key}_{location_id}_{random.randint(1000, 9999)}"

    objective = QuestObjective(
        f"Добыть {resource_data['display_name']} x{required_amount}",
        required_count=required_amount
    )

    # Получаем минимальный ранг из данных ресурса
    min_rank = resource_data.get('min_rank', 1)

    quest = Quest(
        quest_id=quest_id,
        name=quest_name,
        description=description,
        objectives=[objective],
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=difficulty,
        location_id=location_id,
        giver_location=location_name,
        min_rank=min_rank
    )
    quest.target_item = resource_key
    return quest


def _generate_kill_quest_from_template(enemy_key, enemy_data, location_name, location_id,
                                       player_level, is_animal=False):
    """
    Генерация квеста на убийство с заданными параметрами

    Args:
        enemy_key: Ключ врага
        enemy_data: Данные о враге из шаблонов
        location_name: Название локации
        location_id: ID локации
        player_level: Уровень игрока
        is_animal: Является ли врагом животное

    Returns:
        Quest: Сгенерированный квест
    """
    min_level = enemy_data.get('min_level', 1)
    target = enemy_data.get('target', enemy_key)

    # Сложность зависит от уровня врага
    if min_level >= 15:
        difficulty = random.choice([QuestDifficulty.HARD, QuestDifficulty.VERY_HARD])
    elif min_level >= 10:
        difficulty = random.choice([QuestDifficulty.MEDIUM, QuestDifficulty.HARD])
    elif min_level >= 5:
        difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])
    else:
        difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])

    config = get_quest_config()

    # Получаем диапазон количества из конфига
    difficulty_name = difficulty.name.lower()
    amounts = config.get_quest_amount('kill', difficulty_name, default=[2, 4])
    min_amount, max_amount = amounts
    required_amount = random.randint(min_amount, max_amount)

    # Рассчитываем награды
    rewards = calculate_kill_quest_rewards(player_level, difficulty, required_amount)

    quest_name = random.choice(enemy_data['quest_names'])
    description = random.choice(enemy_data['descriptions'])
    quest_id = f"kill_{enemy_key}_{location_id}_{random.randint(1000, 9999)}"

    objective = QuestObjective(
        f"Убить {enemy_data['display_name']} x{required_amount}",
        required_count=required_amount
    )

    quest_type = QuestType.KILL_ANIMALS if is_animal else QuestType.KILL_ENEMIES

    # Получаем минимальный ранг из данных врага
    min_rank = enemy_data.get('min_rank', 1)

    quest = Quest(
        quest_id=quest_id,
        name=quest_name,
        description=description,
        objectives=[objective],
        rewards=rewards,
        quest_type=quest_type,
        difficulty=difficulty,
        location_id=location_id,
        giver_location=location_name,
        min_rank=min_rank
    )

    if is_animal:
        quest.target_animal = target
    else:
        quest.target_enemy = target

    return quest


def _generate_simple_quest(location_name, location_id, player_level):
    """
    Простой генератор квестов для неизвестных типов локаций

    Args:
        location_name: Название локации
        location_id: ID локации
        player_level: Уровень игрока

    Returns:
        Quest: Сгенерированный квест
    """
    # Простой квест на убийство врагов
    difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])
    config = get_quest_config()

    difficulty_name = difficulty.name.lower()
    amounts = config.get_quest_amount('kill', difficulty_name, default=[2, 4])
    min_amount, max_amount = amounts
    required_amount = random.randint(min_amount, max_amount)

    rewards = calculate_kill_quest_rewards(player_level, difficulty, required_amount)

    quest_id = f"simple_{location_id}_{random.randint(1000, 9999)}"

    objective = QuestObjective(
        f"Убить врагов x{required_amount}",
        required_count=required_amount
    )

    quest = Quest(
        quest_id=quest_id,
        name="Защита окрестностей",
        description="Очистите окрестности от врагов.",
        objectives=[objective],
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=difficulty,
        location_id=location_id,
        giver_location=location_name
    )
    quest.target_enemy = "any_enemy"
    return quest
