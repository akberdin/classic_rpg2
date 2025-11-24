"""
Game Systems модуль.

Содержит игровые системы:
- skills - система умений и статус-эффектов
"""

# Реэкспорт основных классов из skills для удобства
from game.systems.skills import (
    # Эффекты
    StatusEffect,
    PoisonEffect,
    StunEffect,
    RegenerationEffect,
    StaminaRecoveryEffect,
    StrengthBoostEffect,
    ShieldEffect,
    # Базовые классы
    Skill,
    SkillCategory,
    SkillManager,
    # Словарь умений
    AVAILABLE_SKILLS,
)

__all__ = [
    # Эффекты
    'StatusEffect',
    'PoisonEffect',
    'StunEffect',
    'RegenerationEffect',
    'StaminaRecoveryEffect',
    'StrengthBoostEffect',
    'ShieldEffect',
    # Базовые классы
    'Skill',
    'SkillCategory',
    'SkillManager',
    # Словарь
    'AVAILABLE_SKILLS',
]
