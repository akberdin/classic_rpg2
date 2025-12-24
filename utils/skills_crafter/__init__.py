"""
Skills Crafter Utility
Утилита для создания и настройки умений в Classic RPG

Возможности:
- Создание умений через визуальный интерфейс (Tkinter)
- Настройка всех параметров умения
- Предпросмотр спрайтов
- Экспорт в формат JSON совместимый с игрой
- Тестирование умений в игровой среде (Pygame)
"""

__version__ = "1.0.0"
__author__ = "Classic RPG Team"

from .models import (
    SkillData,
    SkillType,
    SkillCategory,
    TargetType,
    AreaType,
    ScalingAttribute,
    StatusEffectData,
    RankProgressionData,
    DamageData,
    CostData,
    RequirementData,
    VisualData,
    AnimationFrameData,
    AnimationLoopMode,
)
