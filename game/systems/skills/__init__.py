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
    Craftsmanship,
    Alchemy,
    Enchanting,
    Herbalism,
)

# Оружейные умения
from game.systems.skills.weapon import (
    WeaponSkill,
    BasicShot,
    PreciseShot,
    RapidFire,
    PiercingArrow,
    LongRangeShot,
    Backstab,
    BleedingCut,
    ShadowStep,
    WhirlwindStrike,
    ShieldBreaker,
    BladeDance,
    LungeStrike,
    SpearSweep,
    ArmorBreach,
    # Новые умения для SHADOW
    DeadlyPoison,
    Stealth,
    CriticalStrike,
    ShadowAgility,
    # Новые умения для WARRIOR
    IronStance,
    Intimidate,
    SteelSkin,
    Counterattack,
    Berserker,
    # Новые умения для HUNTER
    HuntersMark,
    StaminaBoost,
    EagleEye,
    ExplosiveArrow,
    Trap,
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
    'Mining', 'Lumberjacking', 'Craftsmanship', 'Alchemy', 'Enchanting', 'Herbalism',
    # Оружейные
    'WeaponSkill', 'BasicShot', 'PreciseShot', 'RapidFire', 'PiercingArrow', 'LongRangeShot',
    'Backstab', 'BleedingCut', 'ShadowStep', 'WhirlwindStrike', 'ShieldBreaker', 'BladeDance',
    'LungeStrike', 'SpearSweep', 'ArmorBreach',
    # Новые умения SHADOW
    'DeadlyPoison', 'Stealth', 'CriticalStrike', 'ShadowAgility',
    # Новые умения WARRIOR
    'IronStance', 'Intimidate', 'SteelSkin', 'Counterattack', 'Berserker',
    # Новые умения HUNTER
    'HuntersMark', 'StaminaBoost', 'EagleEye', 'ExplosiveArrow', 'Trap',
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
    'long_range_shot': LongRangeShot,
    # Боевые (кинжал) - SHADOW
    'backstab': Backstab,
    'bleeding_cut': BleedingCut,
    'shadow_step': ShadowStep,
    'deadly_poison': DeadlyPoison,
    'stealth': Stealth,
    'critical_strike': CriticalStrike,
    'shadow_agility': ShadowAgility,
    # Боевые (меч) - WARRIOR
    'whirlwind_strike': WhirlwindStrike,
    'shield_breaker': ShieldBreaker,
    'blade_dance': BladeDance,
    'iron_stance': IronStance,
    'intimidate': Intimidate,
    'steel_skin': SteelSkin,
    'counterattack': Counterattack,
    'berserker': Berserker,
    # Боевые (лук/копье) - HUNTER
    'lunge_strike': LungeStrike,
    'spear_sweep': SpearSweep,
    'armor_breach': ArmorBreach,
    'hunters_mark': HuntersMark,
    'stamina_boost': StaminaBoost,
    'eagle_eye': EagleEye,
    'explosive_arrow': ExplosiveArrow,
    'trap': Trap,
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
    'craftsmanship': Craftsmanship,
    'alchemy': Alchemy,
    'enchanting': Enchanting,
    'herbalism': Herbalism,
}
