"""
Система умений и способностей.

Этот файл сохранён для обратной совместимости.
Все классы перенесены в game/systems/skills/.

Использование:
    from game.skills import Skill, SkillManager, BasicAttack
    # или напрямую:
    from game.systems.skills import Skill, SkillManager, BasicAttack
"""

# Реэкспорт всех классов из нового модуля
from game.systems.skills import (
    # Эффекты
    StatusEffect,
    PoisonEffect,
    StunEffect,
    RegenerationEffect,
    StaminaRecoveryEffect,
    StrengthBoostEffect,
    ShieldEffect,
    SlowEffect,
    ArmorBreakEffect,
    # Базовые классы
    Skill,
    SkillCategory,
    SkillManager,
    # Боевые умения (общие)
    BasicAttack,
    BattleCry,
    # Ремесленные умения
    Mining,
    Lumberjacking,
    Craftsmanship,
    Alchemy,
    Enchanting,
    Herbalism,
    # Оружейные умения (базовые)
    WeaponSkill,
    BasicShot,
    # Словарь умений
    AVAILABLE_SKILLS,
)

__all__ = [
    # Эффекты
    'StatusEffect', 'PoisonEffect', 'StunEffect', 'RegenerationEffect',
    'StaminaRecoveryEffect', 'StrengthBoostEffect', 'ShieldEffect', 'SlowEffect', 'ArmorBreakEffect',
    # Базовые
    'Skill', 'SkillCategory', 'SkillManager',
    # Боевые (общие)
    'BasicAttack', 'BattleCry',
    # Ремесленные
    'Mining', 'Lumberjacking', 'Craftsmanship', 'Alchemy', 'Enchanting', 'Herbalism',
    # Оружейные (базовые)
    'WeaponSkill', 'BasicShot',
    # Словарь
    'AVAILABLE_SKILLS',
]
