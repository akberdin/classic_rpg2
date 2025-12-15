"""
Модули для генерации квестов

Включает:
- rewards: Расчет наград за квесты
- utils: Вспомогательные функции для генератора квестов
- chains: Генератор цепочек квестов (крафтовые квесты)
"""

from .rewards import (
    calculate_gather_quest_rewards,
    calculate_kill_quest_rewards
)

from .utils import (
    get_player_rank,
    filter_by_rank
)

from .chains import (
    get_available_chain_quests,
    get_next_chain_quest
)

__all__ = [
    'calculate_gather_quest_rewards',
    'calculate_kill_quest_rewards',
    'get_player_rank',
    'filter_by_rank',
    'get_available_chain_quests',
    'get_next_chain_quest'
]
