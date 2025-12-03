"""
Модули для генерации квестов

Включает:
- rewards: Расчет наград за квесты
- utils: Вспомогательные функции для генератора квестов
"""

from .rewards import (
    calculate_gather_quest_rewards,
    calculate_kill_quest_rewards
)

from .utils import (
    get_player_rank,
    filter_by_rank
)

__all__ = [
    'calculate_gather_quest_rewards',
    'calculate_kill_quest_rewards',
    'get_player_rank',
    'filter_by_rank'
]
