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
    SlowEffect,
    ArmorBreakEffect,
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
    BasicShot,
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
    'WeaponSkill', 'BasicShot', 'PreciseShot', 'RapidFire', 'PiercingArrow', 'Backstab',
    'BleedingCut', 'ShadowStep', 'WhirlwindStrike', 'ShieldBreaker', 'BladeDance',
    'LungeStrike', 'SpearSweep', 'ArmorBreach',
    # Словарь умений
    'AVAILABLE_SKILLS',
]


# Словарь всех доступных умений для SkillManager
AVAILABLE_SKILLS = {
    # Боевые (общие)
    'basic_attack': BasicAttack,
    'power_strike': PowerStrike,
    'poison_strike': PoisonStrike,
    'stun_strike': StunStrike,
    'battle_cry': BattleCry,
    # Общие умения
    'basic_shot': BasicShot,
    # Боевые (лук)
    'precise_shot': PreciseShot,
    'rapid_fire': RapidFire,
    'piercing_arrow': PiercingArrow,
    # Боевые (кинжал)
    'backstab': Backstab,
    'bleeding_cut': BleedingCut,
    'shadow_step': ShadowStep,
    # Боевые (меч)
    'whirlwind_strike': WhirlwindStrike,
    'shield_breaker': ShieldBreaker,
    'blade_dance': BladeDance,
    # Боевые (копье)
    'lunge_strike': LungeStrike,
    'spear_sweep': SpearSweep,
    'armor_breach': ArmorBreach,
    # Магические (поддерживающие)
    'heal': Heal,
    'regeneration': Regeneration,
    'stamina_recovery': StaminaRecovery,
    'mage_shield': MageShield,
    # Магические (атакующие)
    'fireball': Fireball,
    'ice_bolt': IceBolt,
    'lightning': Lightning,
    'magic_missile': MagicMissile,
    # Ремесленные
    'mining': Mining,
    'lumberjacking': Lumberjacking,
}
