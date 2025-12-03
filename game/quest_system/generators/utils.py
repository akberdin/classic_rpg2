"""
Вспомогательные функции для генератора квестов
"""
from game.config.config_loader import get_quest_config


def get_player_rank(player_level):
    """
    Определить ранг игрока по уровню

    Args:
        player_level: Уровень игрока

    Returns:
        int: Ранг игрока (1-4)
    """
    config = get_quest_config()

    # Получаем пороги рангов из конфига
    rank_1_max = config.get_rank_threshold('rank_1_max_level', default=10)
    rank_2_max = config.get_rank_threshold('rank_2_max_level', default=20)
    rank_3_max = config.get_rank_threshold('rank_3_max_level', default=30)

    if player_level <= rank_1_max:
        return 1
    elif player_level <= rank_2_max:
        return 2
    elif player_level <= rank_3_max:
        return 3
    else:
        return 4


def filter_by_rank(items_dict, player_rank):
    """
    Фильтровать словарь предметов/врагов по рангу игрока

    Args:
        items_dict: Словарь с данными предметов/врагов
        player_rank: Ранг игрока

    Returns:
        dict: Отфильтрованный словарь, содержащий только доступные предметы
    """
    return {
        key: value
        for key, value in items_dict.items()
        if value.get('min_rank', 1) <= player_rank
    }
