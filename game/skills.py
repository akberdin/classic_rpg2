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
    # Боевые умения
    BasicAttack,
    PowerStrike,
    PoisonStrike,
    StunStrike,
    BattleCry,
    # Магические умения
    Heal,
    Regeneration,
    StaminaRecovery,
    Fireball,
    IceBolt,
    Lightning,
    MagicMissile,
    MageShield,
    # Ремесленные умения
    Mining,
    Lumberjacking,
    # Оружейные умения
    WeaponSkill,
    PreciseShot,
    RapidFire,
    PiercingArrow,
    Backstab,
    BleedingCut,
    ShadowStep,
    WhirlwindStrike,
    ShieldBreaker,
    BladeDance,
    LungeStrike,
    SpearSweep,
    ArmorBreach,
    # Словарь умений
    AVAILABLE_SKILLS,
)

__all__ = [
    # Эффекты
    'StatusEffect', 'PoisonEffect', 'StunEffect', 'RegenerationEffect',
    'StaminaRecoveryEffect', 'StrengthBoostEffect', 'ShieldEffect', 'SlowEffect', 'ArmorBreakEffect',
    # Базовые
    'Skill', 'SkillCategory', 'SkillManager',
    # Боевые
    'BasicAttack', 'PowerStrike', 'PoisonStrike', 'StunStrike', 'BattleCry',
    # Магические
    'Heal', 'Regeneration', 'StaminaRecovery', 'Fireball', 'IceBolt',
    'Lightning', 'MagicMissile', 'MageShield',
    # Ремесленные
    'Mining', 'Lumberjacking',
    # Оружейные
    'WeaponSkill', 'PreciseShot', 'RapidFire', 'PiercingArrow', 'Backstab',
    'BleedingCut', 'ShadowStep', 'WhirlwindStrike', 'ShieldBreaker', 'BladeDance',
    'LungeStrike', 'SpearSweep', 'ArmorBreach',
    # Словарь
    'AVAILABLE_SKILLS',
]
