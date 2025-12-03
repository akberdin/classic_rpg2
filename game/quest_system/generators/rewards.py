"""
Модуль для расчета наград за квесты
"""
from game.config.config_loader import get_quest_config


def calculate_gather_quest_rewards(player_level, difficulty, required_amount):
    """
    Рассчитать награды за квест на сбор ресурсов

    Args:
        player_level: Уровень игрока
        difficulty: Сложность квеста (QuestDifficulty)
        required_amount: Требуемое количество ресурсов

    Returns:
        dict: Словарь с наградами {'exp': int, 'gold': int}
    """
    config = get_quest_config()

    # Получаем базовые значения из конфига
    base_exp = config.get_reward_param('gather_quests', 'base_exp', default=50)
    exp_per_level = config.get_reward_param('gather_quests', 'exp_per_level', default=10)
    base_gold = config.get_reward_param('gather_quests', 'base_gold', default=30)
    gold_per_level = config.get_reward_param('gather_quests', 'gold_per_level', default=5)
    amount_divisor = config.get_reward_param('gather_quests', 'amount_divisor', default=5)

    # Рассчитываем награды
    exp_reward = int(
        (base_exp + player_level * exp_per_level) *
        difficulty.reward_multiplier *
        (required_amount / amount_divisor)
    )
    gold_reward = int(
        (base_gold + player_level * gold_per_level) *
        difficulty.reward_multiplier *
        (required_amount / amount_divisor)
    )

    return {
        'exp': exp_reward,
        'gold': gold_reward
    }


def calculate_kill_quest_rewards(player_level, difficulty, required_amount):
    """
    Рассчитать награды за квест на убийство врагов

    Args:
        player_level: Уровень игрока
        difficulty: Сложность квеста (QuestDifficulty)
        required_amount: Требуемое количество убийств

    Returns:
        dict: Словарь с наградами {'exp': int, 'gold': int}
    """
    config = get_quest_config()

    # Получаем базовые значения из конфига
    base_exp = config.get_reward_param('kill_quests', 'base_exp', default=80)
    exp_per_level = config.get_reward_param('kill_quests', 'exp_per_level', default=15)
    base_gold = config.get_reward_param('kill_quests', 'base_gold', default=50)
    gold_per_level = config.get_reward_param('kill_quests', 'gold_per_level', default=8)
    amount_divisor = config.get_reward_param('kill_quests', 'amount_divisor', default=4)

    # Рассчитываем награды (больше за убийства)
    exp_reward = int(
        (base_exp + player_level * exp_per_level) *
        difficulty.reward_multiplier *
        (required_amount / amount_divisor)
    )
    gold_reward = int(
        (base_gold + player_level * gold_per_level) *
        difficulty.reward_multiplier *
        (required_amount / amount_divisor)
    )

    return {
        'exp': exp_reward,
        'gold': gold_reward
    }
