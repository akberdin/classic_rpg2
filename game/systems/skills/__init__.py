"""
Skills модуль - система умений.

Содержит:
- effects - статус-эффекты (StatusEffect, PoisonEffect и др.)
- base - базовые классы (Skill, SkillCategory, SkillManager)
- combat - боевые умения (BasicAttack, BattleCry)
- crafting - ремесленные умения
- weapon - оружейные умения (BasicShot)
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

# Боевые умения (общие)
from game.systems.skills.combat import (
    BasicAttack,
    BattleCry,
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

# Оружейные умения (базовые)
from game.systems.skills.weapon import (
    WeaponSkill,
    BasicShot,
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
    # Словарь умений
    'AVAILABLE_SKILLS',
]


# Словарь всех доступных умений для SkillManager
AVAILABLE_SKILLS = {
    # Боевые (общие)
    'basic_attack': BasicAttack,
    'battle_cry': BattleCry,
    # Общие умения
    'basic_shot': BasicShot,
    # Ремесленные
    'mining': Mining,
    'lumberjacking': Lumberjacking,
    'craftsmanship': Craftsmanship,
    'alchemy': Alchemy,
    'enchanting': Enchanting,
    'herbalism': Herbalism,
}
