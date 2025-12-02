"""
Вспомогательные функции для работы с рангами NPC
"""
import random
from game.constants import RANKS


def get_numeric_rank(level):
    """
    Получить численный ранг (0-4) на основе уровня персонажа

    Args:
        level (int): Уровень персонажа

    Returns:
        int: Численный ранг (0=Новичок, 1=Обычный, 2=Опытный, 3=Эксперт, 4=Мастер)
    """
    if level <= 0:
        return 0
    elif level <= 10:
        return 0  # Новичок (1-10)
    elif level <= 20:
        return 1  # Обычный (11-20)
    elif level <= 30:
        return 2  # Опытный (21-30)
    elif level <= 40:
        return 3  # Эксперт (31-40)
    else:
        return 4  # Мастер (40+)


def get_rank_level_range(rank):
    """
    Получить диапазон уровней для заданного ранга

    Args:
        rank (int): Численный ранг (0-4)

    Returns:
        tuple: (min_level, max_level) для данного ранга
    """
    rank_ranges = {
        0: (1, 10),    # Новичок
        1: (11, 20),   # Обычный
        2: (21, 30),   # Опытный
        3: (31, 40),   # Эксперт
        4: (40, 40)    # Мастер (максимальный уровень)
    }

    return rank_ranges.get(rank, (1, 10))


def get_random_level_for_rank(rank):
    """
    Получить случайный уровень для заданного ранга

    Args:
        rank (int): Численный ранг (0-4)

    Returns:
        int: Случайный уровень в пределах данного ранга
    """
    min_level, max_level = get_rank_level_range(rank)
    return random.randint(min_level, max_level)


def get_rank_name(level):
    """
    Получить название ранга на основе уровня

    Args:
        level (int): Уровень персонажа

    Returns:
        str: Название ранга
    """
    for (min_level, max_level), rank_name in RANKS.items():
        if min_level <= level <= max_level:
            return rank_name
    return "Новичок"
