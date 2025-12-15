"""
Модули для генерации квестов

Включает:
- rewards: Расчет наград за квесты
- utils: Вспомогательные функции для генератора квестов
- chains: Генератор цепочек квестов (крафтовые квесты)
- template_generator: Универсальный шаблонный генератор на основе конфигурации
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
    get_next_chain_quest,
    get_chain_masters_for_location,
    get_chain_quests_for_master,
    get_chain_progress
)

from .template_generator import (
    TemplateQuestGenerator,
    generate_quests_from_template,
    get_template_generator,
    get_quest_config
)

__all__ = [
    'calculate_gather_quest_rewards',
    'calculate_kill_quest_rewards',
    'get_player_rank',
    'filter_by_rank',
    'get_available_chain_quests',
    'get_next_chain_quest',
    'get_chain_masters_for_location',
    'get_chain_quests_for_master',
    'get_chain_progress',
    'TemplateQuestGenerator',
    'generate_quests_from_template',
    'get_template_generator',
    'get_quest_config'
]
