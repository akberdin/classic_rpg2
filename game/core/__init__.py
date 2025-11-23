"""
Core модуль - ядро игры.

Содержит основные классы для управления игрой:
- GameContext - контекст для передачи зависимостей
- AIContext - контекст для обновления AI NPC
- NPCManager - централизованное управление NPC
- NPCType - enum типов NPC

Функции интеграции:
- create_npc_manager_from_game - создать NPCManager из Game
- create_ai_context - создать AIContext
- create_game_context - создать GameContext
- get_all_npcs_from_game - получить всех NPC из Game
- update_all_npc_ai_with_context - обновить AI всех NPC
"""

from game.core.game_context import GameContext
from game.core.ai_context import AIContext
from game.core.npc_manager import NPCManager, NPCType
from game.core.integration import (
    create_npc_manager_from_game,
    create_ai_context,
    create_game_context,
    get_all_npcs_from_game,
    update_all_npc_ai_with_context,
)

__all__ = [
    'GameContext',
    'AIContext',
    'NPCManager',
    'NPCType',
    'create_npc_manager_from_game',
    'create_ai_context',
    'create_game_context',
    'get_all_npcs_from_game',
    'update_all_npc_ai_with_context',
]
