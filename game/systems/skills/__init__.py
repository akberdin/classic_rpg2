"""
Skills модуль - система умений.

Содержит:
- effects - статус-эффекты (StatusEffect, PoisonEffect и др.)
- base - базовые классы (Skill, SkillCategory, SkillManager)
- combat - боевые умения
- magic - магические умения
- crafting - ремесленные умения
- weapon - оружейные умения
"""

# Эффекты
from game.systems.skills.effects import (
    StatusEffect,
    PoisonEffect,
    StunEffect,
    RegenerationEffect,
    StaminaRecoveryEffect,
    StrengthBoostEffect,
    ShieldEffect,
)

# Базовые классы
from game.systems.skills.base import (
    Skill,
    SkillCategory,
    SkillManager,
)

# Боевые умения
from game.systems.skills.combat import (
    BasicAttack,
    PowerStrike,
    PoisonStrike,
    StunStrike,
    BattleCry,
)

# Магические умения
from game.systems.skills.magic import (
    Heal,
    Regeneration,
    StaminaRecovery,
    Fireball,
    IceBolt,
    Lightning,
    MagicMissile,
    MageShield,
)

# Ремесленные умения
from game.systems.skills.crafting import (
    Mining,
    Lumberjacking,
)

# Оружейные умения
from game.systems.skills.weapon import (
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
)

__all__ = [
    # Эффекты
    'StatusEffect', 'PoisonEffect', 'StunEffect', 'RegenerationEffect',
    'StaminaRecoveryEffect', 'StrengthBoostEffect', 'ShieldEffect',
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
]
