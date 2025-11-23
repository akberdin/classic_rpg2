"""
Модуль интеграции - помощники для использования новых классов с существующим кодом.

Этот модуль предоставляет функции для облегчения перехода от старой архитектуры
к новой с минимальными изменениями в существующем коде.
"""

from typing import TYPE_CHECKING, Dict, List, Any

if TYPE_CHECKING:
    from game.engine import Game
    from game.core.npc_manager import NPCManager
    from game.core.ai_context import AIContext
    from game.core.game_context import GameContext


def create_npc_manager_from_game(game: 'Game') -> 'NPCManager':
    """
    Создать NPCManager из существующих списков NPC в Game.

    Используется для миграции от старых списков self.guards, self.merchants и т.д.
    к централизованному NPCManager.

    Args:
        game: Экземпляр Game

    Returns:
        NPCManager: Инициализированный менеджер NPC
    """
    from game.core.npc_manager import NPCManager, NPCType

    manager = NPCManager()

    # Загружаем существующие NPC из атрибутов Game
    npc_mappings = [
        (NPCType.GUARD, 'guards'),
        (NPCType.MERCHANT, 'merchants'),
        (NPCType.MAGE, 'mages'),
        (NPCType.BANDIT, 'bandits'),
        (NPCType.MINER, 'miners'),
        (NPCType.UNDEAD, 'undead'),
        (NPCType.ALCHEMIST, 'alchemists'),
        (NPCType.HUNTER, 'hunters'),
        (NPCType.NECROMANCER, 'necromancers'),
        (NPCType.ANIMAL, 'animals'),
    ]

    for npc_type, attr_name in npc_mappings:
        if hasattr(game, attr_name):
            npcs = getattr(game, attr_name, [])
            if npcs:
                manager.add_npcs(npcs, npc_type)

    return manager


def create_ai_context(game: 'Game') -> 'AIContext':
    """
    Создать AIContext из текущего состояния Game.

    Args:
        game: Экземпляр Game

    Returns:
        AIContext: Контекст для обновления AI
    """
    from game.core.ai_context import AIContext

    # Собираем всех NPC
    all_npcs = (
        getattr(game, 'guards', []) +
        getattr(game, 'merchants', []) +
        getattr(game, 'mages', []) +
        getattr(game, 'bandits', []) +
        getattr(game, 'miners', []) +
        getattr(game, 'undead', []) +
        getattr(game, 'alchemists', []) +
        getattr(game, 'hunters', []) +
        getattr(game, 'necromancers', []) +
        getattr(game, 'animals', [])
    )

    # Получаем текущий час
    current_hour = 12.0
    if hasattr(game, 'game_time') and game.game_time:
        current_hour = game.game_time.game_hour

    return AIContext(
        game_map=game.game_map,
        player=game.player,
        current_hour=current_hour,
        all_npcs=all_npcs,
        performance_optimizer=getattr(game, 'performance_optimizer', None)
    )


def create_game_context(game: 'Game') -> 'GameContext':
    """
    Создать GameContext из Game.

    Args:
        game: Экземпляр Game

    Returns:
        GameContext: Контекст игры
    """
    from game.core.game_context import GameContext
    return GameContext(game)


def get_all_npcs_from_game(game: 'Game') -> List:
    """
    Получить список всех NPC из Game.

    Вспомогательная функция, которая собирает все NPC из отдельных списков.

    Args:
        game: Экземпляр Game

    Returns:
        List: Список всех NPC
    """
    return (
        getattr(game, 'guards', []) +
        getattr(game, 'merchants', []) +
        getattr(game, 'mages', []) +
        getattr(game, 'bandits', []) +
        getattr(game, 'miners', []) +
        getattr(game, 'undead', []) +
        getattr(game, 'alchemists', []) +
        getattr(game, 'hunters', []) +
        getattr(game, 'necromancers', []) +
        getattr(game, 'animals', [])
    )


def update_all_npc_ai_with_context(game: 'Game', context: 'AIContext' = None) -> None:
    """
    Обновить AI всех NPC используя AIContext.

    Это замена для повторяющегося кода в game_time.py.
    Все NPC теперь поддерживают унифицированный вызов update_ai(context).

    Args:
        game: Экземпляр Game
        context: Опциональный AIContext (создаётся автоматически если не указан)
    """
    if context is None:
        context = create_ai_context(game)

    # Унифицированный вызов - все NPC поддерживают AIContext
    npc_groups = [
        'guards', 'merchants', 'mages', 'bandits', 'miners',
        'undead', 'alchemists', 'hunters', 'necromancers', 'animals'
    ]

    for group_name in npc_groups:
        npcs = getattr(game, group_name, [])
        for npc in npcs:
            if context.should_update(npc):
                npc.update_ai(context)
