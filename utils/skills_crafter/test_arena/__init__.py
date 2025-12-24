"""
Test Arena - Тестовая площадка для проверки умений из Skills Crafter

Изолированная среда для тестирования умений и их анимаций,
не зависящая от основного кода игры.
"""

from .entities import TestCharacter, TestNPC, TestPlayer
from .skill_loader import SkillsCrafterLoader

# Ленивый импорт арены (требует pygame)
def get_test_arena():
    """Получить класс TestArena (требует pygame)"""
    from .arena import TestArena
    return TestArena

__all__ = [
    'TestCharacter',
    'TestNPC',
    'TestPlayer',
    'SkillsCrafterLoader',
    'get_test_arena',
]
