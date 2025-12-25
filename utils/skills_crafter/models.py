"""
Модели данных для Skills Crafter
Определяет структуры для хранения конфигурации умений
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class SkillType(Enum):
    """Тип умения"""
    ACTIVE = "active"
    PASSIVE = "passive"


class SkillCategory(Enum):
    """Категория умения"""
    GENERAL = "general"
    COMBAT = "combat"
    WARRIOR = "warrior"
    SHADOW = "shadow"
    HUNTER = "hunter"
    MAGE = "magic"
    CRAFTING = "crafting"
    EXPLORATION = "exploration"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.GENERAL.value: "Общее",
            cls.COMBAT.value: "Боевое",
            cls.WARRIOR.value: "Воин",
            cls.SHADOW.value: "Тень",
            cls.HUNTER.value: "Охотник",
            cls.MAGE.value: "Маг",
            cls.CRAFTING.value: "Ремесло",
            cls.EXPLORATION.value: "Исследование",
        }


class TargetType(Enum):
    """Тип цели умения"""
    SELF = "self"
    SINGLE_ENEMY = "single_enemy"
    SINGLE_ALLY = "single_ally"
    ALL_ENEMIES = "all_enemies"
    ALL_ALLIES = "all_allies"
    POINT = "point"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.SELF.value: "На себя",
            cls.SINGLE_ENEMY.value: "Один враг",
            cls.SINGLE_ALLY.value: "Один союзник",
            cls.ALL_ENEMIES.value: "Все враги",
            cls.ALL_ALLIES.value: "Все союзники",
            cls.POINT.value: "Точка на поле",
        }


class AreaType(Enum):
    """Тип области воздействия"""
    SINGLE = "single"
    CIRCLE = "circle"
    CONE = "cone"
    LINE = "line"
    CROSS = "cross"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.SINGLE.value: "Одиночная цель",
            cls.CIRCLE.value: "Круг (AoE)",
            cls.CONE.value: "Конус",
            cls.LINE.value: "Линия",
            cls.CROSS.value: "Крест",
        }


class ScalingAttribute(Enum):
    """Атрибуты для масштабирования урона/эффекта"""
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    SPIRIT = "spirit"
    LUCK = "luck"
    WEAPON_DAMAGE = "weapon_damage"
    MAX_HP = "max_hp"
    MAX_MANA = "max_mana"
    MAX_STAMINA = "max_stamina"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.STRENGTH.value: "Сила",
            cls.DEXTERITY.value: "Ловкость",
            cls.CONSTITUTION.value: "Телосложение",
            cls.INTELLIGENCE.value: "Интеллект",
            cls.SPIRIT.value: "Дух",
            cls.LUCK.value: "Удача",
            cls.WEAPON_DAMAGE.value: "Урон оружия",
            cls.MAX_HP.value: "Макс. HP",
            cls.MAX_MANA.value: "Макс. Мана",
            cls.MAX_STAMINA.value: "Макс. Выносливость",
        }


class WeaponType(Enum):
    """Типы оружия"""
    ANY = "any"
    SWORD = "sword"
    KNIFE = "knife"
    BOW = "bow"
    SPEAR = "spear"
    STAFF = "staff"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.ANY.value: "Любое",
            cls.SWORD.value: "Меч",
            cls.KNIFE.value: "Кинжал",
            cls.BOW.value: "Лук",
            cls.SPEAR.value: "Копье",
            cls.STAFF.value: "Посох",
        }


class StatusEffectType(Enum):
    """Типы статус-эффектов"""
    POISON = "poison"
    BURN = "burn"
    BLEED = "bleed"
    STUN = "stun"
    SLOW = "slow"
    REGENERATION = "regeneration"
    STAMINA_RECOVERY = "stamina_recovery"
    STRENGTH_BOOST = "strength_boost"
    DEFENSE_BOOST = "shield"
    ARMOR_BREAK = "armor_break"
    DODGE_BOOST = "shadow"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.POISON.value: "Отравление",
            cls.BURN.value: "Горение",
            cls.BLEED.value: "Кровотечение",
            cls.STUN.value: "Оглушение",
            cls.SLOW.value: "Замедление",
            cls.REGENERATION.value: "Регенерация",
            cls.STAMINA_RECOVERY.value: "Восст. выносливости",
            cls.STRENGTH_BOOST.value: "Усиление силы",
            cls.DEFENSE_BOOST.value: "Щит",
            cls.ARMOR_BREAK.value: "Пробой брони",
            cls.DODGE_BOOST.value: "Уклонение",
        }


@dataclass
class StatusEffectData:
    """Данные о статус-эффекте, накладываемом умением"""
    effect_type: str = "poison"
    chance_base: float = 1.0  # Базовый шанс (1.0 = 100%)
    chance_per_rank: float = 0.0  # Прирост шанса за ранг
    duration_base: int = 3  # Базовая длительность
    duration_per_rank: int = 0  # Прирост длительности за ранг
    value_base: float = 5.0  # Базовое значение (урон/лечение/бонус)
    value_per_rank: float = 2.0  # Прирост значения за ранг
    # Для сложных эффектов
    spread_chance: float = 0.0  # Шанс распространения (для burn)
    spread_chance_per_rank: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "chance_base": self.chance_base,
            "chance_per_rank": self.chance_per_rank,
            "duration_base": self.duration_base,
            "duration_per_rank": self.duration_per_rank,
            "value_base": self.value_base,
            "value_per_rank": self.value_per_rank,
            "spread_chance": self.spread_chance,
            "spread_chance_per_rank": self.spread_chance_per_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusEffectData":
        return cls(
            effect_type=data.get("effect_type", "poison"),
            chance_base=data.get("chance_base", 1.0),
            chance_per_rank=data.get("chance_per_rank", 0.0),
            duration_base=data.get("duration_base", 3),
            duration_per_rank=data.get("duration_per_rank", 0),
            value_base=data.get("value_base", 5.0),
            value_per_rank=data.get("value_per_rank", 2.0),
            spread_chance=data.get("spread_chance", 0.0),
            spread_chance_per_rank=data.get("spread_chance_per_rank", 0.0),
        )


@dataclass
class ScalingData:
    """Данные о масштабировании по атрибуту"""
    attribute: str = "strength"
    multiplier: float = 1.0
    multiplier_per_rank: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "multiplier": self.multiplier,
            "multiplier_per_rank": self.multiplier_per_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScalingData":
        return cls(
            attribute=data.get("attribute", "strength"),
            multiplier=data.get("multiplier", 1.0),
            multiplier_per_rank=data.get("multiplier_per_rank", 0.0),
        )


@dataclass
class DamageData:
    """Данные об уроне умения"""
    base_damage: float = 0.0
    damage_multiplier: float = 1.0  # Множитель урона оружия
    damage_multiplier_per_rank: float = 0.2
    # Масштабирование по атрибутам
    scaling: List[ScalingData] = field(default_factory=list)
    # Свойства урона
    ignores_armor: bool = False
    armor_penetration_base: float = 0.0
    armor_penetration_per_rank: float = 0.0
    # Криты
    crit_chance_bonus: float = 0.0
    crit_chance_per_rank: float = 0.0
    crit_damage_multiplier: float = 2.0
    # Множественные удары
    hit_count_base: int = 1
    hit_count_per_rank: int = 0
    damage_per_hit_multiplier: float = 1.0  # Множитель урона за удар (для multi-hit)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_damage": self.base_damage,
            "damage_multiplier": self.damage_multiplier,
            "damage_multiplier_per_rank": self.damage_multiplier_per_rank,
            "scaling": [s.to_dict() for s in self.scaling],
            "ignores_armor": self.ignores_armor,
            "armor_penetration_base": self.armor_penetration_base,
            "armor_penetration_per_rank": self.armor_penetration_per_rank,
            "crit_chance_bonus": self.crit_chance_bonus,
            "crit_chance_per_rank": self.crit_chance_per_rank,
            "crit_damage_multiplier": self.crit_damage_multiplier,
            "hit_count_base": self.hit_count_base,
            "hit_count_per_rank": self.hit_count_per_rank,
            "damage_per_hit_multiplier": self.damage_per_hit_multiplier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DamageData":
        scaling = [ScalingData.from_dict(s) for s in data.get("scaling", [])]
        return cls(
            base_damage=data.get("base_damage", 0.0),
            damage_multiplier=data.get("damage_multiplier", 1.0),
            damage_multiplier_per_rank=data.get("damage_multiplier_per_rank", 0.2),
            scaling=scaling,
            ignores_armor=data.get("ignores_armor", False),
            armor_penetration_base=data.get("armor_penetration_base", 0.0),
            armor_penetration_per_rank=data.get("armor_penetration_per_rank", 0.0),
            crit_chance_bonus=data.get("crit_chance_bonus", 0.0),
            crit_chance_per_rank=data.get("crit_chance_per_rank", 0.0),
            crit_damage_multiplier=data.get("crit_damage_multiplier", 2.0),
            hit_count_base=data.get("hit_count_base", 1),
            hit_count_per_rank=data.get("hit_count_per_rank", 0),
            damage_per_hit_multiplier=data.get("damage_per_hit_multiplier", 1.0),
        )


@dataclass
class HealingData:
    """Данные о лечении умения"""
    base_heal: float = 0.0
    heal_percent_max_hp: float = 0.0  # Лечение как % от макс. HP
    heal_percent_per_rank: float = 0.0
    # Масштабирование
    scaling: List[ScalingData] = field(default_factory=list)
    # Лечение по времени (для регенерации)
    heal_over_time: bool = False
    heal_per_turn_base: float = 0.0
    heal_per_turn_per_rank: float = 0.0
    duration_base: int = 0
    duration_per_rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_heal": self.base_heal,
            "heal_percent_max_hp": self.heal_percent_max_hp,
            "heal_percent_per_rank": self.heal_percent_per_rank,
            "scaling": [s.to_dict() for s in self.scaling],
            "heal_over_time": self.heal_over_time,
            "heal_per_turn_base": self.heal_per_turn_base,
            "heal_per_turn_per_rank": self.heal_per_turn_per_rank,
            "duration_base": self.duration_base,
            "duration_per_rank": self.duration_per_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealingData":
        scaling = [ScalingData.from_dict(s) for s in data.get("scaling", [])]
        return cls(
            base_heal=data.get("base_heal", 0.0),
            heal_percent_max_hp=data.get("heal_percent_max_hp", 0.0),
            heal_percent_per_rank=data.get("heal_percent_per_rank", 0.0),
            scaling=scaling,
            heal_over_time=data.get("heal_over_time", False),
            heal_per_turn_base=data.get("heal_per_turn_base", 0.0),
            heal_per_turn_per_rank=data.get("heal_per_turn_per_rank", 0.0),
            duration_base=data.get("duration_base", 0),
            duration_per_rank=data.get("duration_per_rank", 0),
        )


@dataclass
class CostData:
    """Затраты на использование умения"""
    mana_cost: int = 0
    mana_cost_per_rank: int = 0
    stamina_cost: int = 0
    stamina_cost_per_rank: int = 0
    health_cost: int = 0
    health_cost_per_rank: int = 0
    # Кулдаун
    cooldown: int = 0
    cooldown_reduction_per_rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mana_cost": self.mana_cost,
            "mana_cost_per_rank": self.mana_cost_per_rank,
            "stamina_cost": self.stamina_cost,
            "stamina_cost_per_rank": self.stamina_cost_per_rank,
            "health_cost": self.health_cost,
            "health_cost_per_rank": self.health_cost_per_rank,
            "cooldown": self.cooldown,
            "cooldown_reduction_per_rank": self.cooldown_reduction_per_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostData":
        return cls(
            mana_cost=data.get("mana_cost", 0),
            mana_cost_per_rank=data.get("mana_cost_per_rank", 0),
            stamina_cost=data.get("stamina_cost", 0),
            stamina_cost_per_rank=data.get("stamina_cost_per_rank", 0),
            health_cost=data.get("health_cost", 0),
            health_cost_per_rank=data.get("health_cost_per_rank", 0),
            cooldown=data.get("cooldown", 0),
            cooldown_reduction_per_rank=data.get("cooldown_reduction_per_rank", 0),
        )


@dataclass
class RequirementData:
    """Требования для изучения/использования умения"""
    level_required: int = 1
    required_weapon: str = "any"  # Тип оружия
    required_skills: List[str] = field(default_factory=list)  # ID умений-пререквизитов
    required_skill_ranks: Dict[str, int] = field(default_factory=dict)  # skill_id: min_rank
    # Требования атрибутов
    min_strength: int = 0
    min_dexterity: int = 0
    min_constitution: int = 0
    min_intelligence: int = 0
    min_spirit: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_required": self.level_required,
            "required_weapon": self.required_weapon,
            "required_skills": self.required_skills,
            "required_skill_ranks": self.required_skill_ranks,
            "min_strength": self.min_strength,
            "min_dexterity": self.min_dexterity,
            "min_constitution": self.min_constitution,
            "min_intelligence": self.min_intelligence,
            "min_spirit": self.min_spirit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementData":
        return cls(
            level_required=data.get("level_required", 1),
            required_weapon=data.get("required_weapon", "any"),
            required_skills=data.get("required_skills", []),
            required_skill_ranks=data.get("required_skill_ranks", {}),
            min_strength=data.get("min_strength", 0),
            min_dexterity=data.get("min_dexterity", 0),
            min_constitution=data.get("min_constitution", 0),
            min_intelligence=data.get("min_intelligence", 0),
            min_spirit=data.get("min_spirit", 0),
        )


@dataclass
class TargetingData:
    """Данные о нацеливании умения"""
    target_type: str = "single_enemy"
    area_type: str = "single"
    # Дальность
    tactical_range: int = 1  # Максимальная дальность
    min_range: int = 0  # Минимальная дальность
    range_per_rank: int = 0  # Прирост дальности за ранг
    # Для AoE
    aoe_radius: int = 0
    aoe_radius_per_rank: int = 0
    # Для конуса
    cone_angle: int = 60  # Угол конуса в градусах
    # Для линии
    line_width: int = 1
    # Особые свойства
    can_target_self: bool = False
    requires_line_of_sight: bool = True
    knockback_chance: float = 0.0
    knockback_chance_per_rank: float = 0.0
    knockback_distance: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_type": self.target_type,
            "area_type": self.area_type,
            "tactical_range": self.tactical_range,
            "min_range": self.min_range,
            "range_per_rank": self.range_per_rank,
            "aoe_radius": self.aoe_radius,
            "aoe_radius_per_rank": self.aoe_radius_per_rank,
            "cone_angle": self.cone_angle,
            "line_width": self.line_width,
            "can_target_self": self.can_target_self,
            "requires_line_of_sight": self.requires_line_of_sight,
            "knockback_chance": self.knockback_chance,
            "knockback_chance_per_rank": self.knockback_chance_per_rank,
            "knockback_distance": self.knockback_distance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetingData":
        return cls(
            target_type=data.get("target_type", "single_enemy"),
            area_type=data.get("area_type", "single"),
            tactical_range=data.get("tactical_range", 1),
            min_range=data.get("min_range", 0),
            range_per_rank=data.get("range_per_rank", 0),
            aoe_radius=data.get("aoe_radius", 0),
            aoe_radius_per_rank=data.get("aoe_radius_per_rank", 0),
            cone_angle=data.get("cone_angle", 60),
            line_width=data.get("line_width", 1),
            can_target_self=data.get("can_target_self", False),
            requires_line_of_sight=data.get("requires_line_of_sight", True),
            knockback_chance=data.get("knockback_chance", 0.0),
            knockback_chance_per_rank=data.get("knockback_chance_per_rank", 0.0),
            knockback_distance=data.get("knockback_distance", 1),
        )


@dataclass
class RankProgressionData:
    """Данные о прогрессии умения по рангам"""
    max_rank: int = 5
    # Опыт для повышения ранга
    base_experience: int = 100
    experience_multiplier: float = 1.5
    # Требования использований
    uses_per_rank_multiplier: int = 20
    # Требования уровня
    level_per_rank_multiplier: int = 5
    # Стоимость повышения
    gold_base_cost: int = 50
    gold_multiplier: float = 1.0  # rank * rank
    # Описания для каждого ранга
    descriptions_per_rank: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_rank": self.max_rank,
            "base_experience": self.base_experience,
            "experience_multiplier": self.experience_multiplier,
            "uses_per_rank_multiplier": self.uses_per_rank_multiplier,
            "level_per_rank_multiplier": self.level_per_rank_multiplier,
            "gold_base_cost": self.gold_base_cost,
            "gold_multiplier": self.gold_multiplier,
            "descriptions_per_rank": self.descriptions_per_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RankProgressionData":
        return cls(
            max_rank=data.get("max_rank", 5),
            base_experience=data.get("base_experience", 100),
            experience_multiplier=data.get("experience_multiplier", 1.5),
            uses_per_rank_multiplier=data.get("uses_per_rank_multiplier", 20),
            level_per_rank_multiplier=data.get("level_per_rank_multiplier", 5),
            gold_base_cost=data.get("gold_base_cost", 50),
            gold_multiplier=data.get("gold_multiplier", 1.0),
            descriptions_per_rank=data.get("descriptions_per_rank", []),
        )


class AnimationLoopMode(Enum):
    """Режим воспроизведения анимации"""
    ONCE = "once"              # Один раз
    LOOP = "loop"              # Зацикленно
    PING_PONG = "ping_pong"    # Туда-обратно

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.ONCE.value: "Один раз",
            cls.LOOP.value: "Зацикленно",
            cls.PING_PONG.value: "Туда-обратно",
        }


class AnimationDisplayType(Enum):
    """Тип отображения анимации на поле боя"""
    STATIC = "static"          # Статическая анимация в одном месте
    PROJECTILE = "projectile"  # Снаряд летит от кастера к цели (стрела, фаербол)
    BEAM = "beam"              # Луч/линия от кастера к цели (молния, лазер)
    SPRITE_BEAM = "sprite_beam"  # Спрайтовый луч от кастера к цели (молния со спрайтами)
    IMPACT = "impact"          # Появляется в точке попадания (взрыв, удар)
    AREA = "area"              # Покрывает область (AoE эффекты)
    ON_CASTER = "on_caster"    # Отображается на кастере (баффы, ауры)
    ON_TARGET = "on_target"    # Отображается на цели (дебаффы)
    CHAIN = "chain"            # Цепная анимация между несколькими целями

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.STATIC.value: "Статическая",
            cls.PROJECTILE.value: "Снаряд (летит к цели)",
            cls.BEAM.value: "Луч (линия к цели)",
            cls.SPRITE_BEAM.value: "Спрайтовый луч (от кастера к цели)",
            cls.IMPACT.value: "Удар (в точке попадания)",
            cls.AREA.value: "Область (AoE)",
            cls.ON_CASTER.value: "На кастере",
            cls.ON_TARGET.value: "На цели",
            cls.CHAIN.value: "Цепная (между целями)",
        }


class ProjectileTrajectory(Enum):
    """Траектория снаряда"""
    STRAIGHT = "straight"      # Прямая линия
    ARC = "arc"                # Дуга (парабола)
    HOMING = "homing"          # Самонаводящийся
    WAVE = "wave"              # Волнообразная

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.STRAIGHT.value: "Прямая",
            cls.ARC.value: "Дуга",
            cls.HOMING.value: "Самонаведение",
            cls.WAVE.value: "Волна",
        }


class AnimationAnchor(Enum):
    """Точка привязки анимации относительно юнита"""
    CENTER = "center"          # Центр
    TOP = "top"                # Сверху
    BOTTOM = "bottom"          # Снизу (у ног)
    WEAPON = "weapon"          # У оружия/руки
    HEAD = "head"              # У головы

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.CENTER.value: "Центр",
            cls.TOP.value: "Сверху",
            cls.BOTTOM.value: "Снизу (у ног)",
            cls.WEAPON.value: "У оружия",
            cls.HEAD.value: "Над головой",
        }


@dataclass
class ProjectileData:
    """Настройки снаряда для projectile-анимаций"""
    speed: float = 300.0              # Скорость в пикселях/сек
    trajectory: str = "straight"       # Тип траектории
    arc_height: float = 50.0          # Высота дуги (для arc траектории)
    auto_rotate: bool = True          # Авто-поворот к цели
    rotation_offset: float = 0.0      # Смещение угла в градусах
    # Эффект при попадании
    impact_animation: str = ""        # ID анимации при попадании
    impact_scale: float = 1.0         # Масштаб анимации попадания
    # Эффект следа
    trail_enabled: bool = False       # Включить след
    trail_color: str = "#FFFFFF"      # Цвет следа
    trail_length: int = 5             # Длина следа в кадрах

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speed": self.speed,
            "trajectory": self.trajectory,
            "arc_height": self.arc_height,
            "auto_rotate": self.auto_rotate,
            "rotation_offset": self.rotation_offset,
            "impact_animation": self.impact_animation,
            "impact_scale": self.impact_scale,
            "trail_enabled": self.trail_enabled,
            "trail_color": self.trail_color,
            "trail_length": self.trail_length,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectileData":
        return cls(
            speed=data.get("speed", 300.0),
            trajectory=data.get("trajectory", "straight"),
            arc_height=data.get("arc_height", 50.0),
            auto_rotate=data.get("auto_rotate", True),
            rotation_offset=data.get("rotation_offset", 0.0),
            impact_animation=data.get("impact_animation", ""),
            impact_scale=data.get("impact_scale", 1.0),
            trail_enabled=data.get("trail_enabled", False),
            trail_color=data.get("trail_color", "#FFFFFF"),
            trail_length=data.get("trail_length", 5),
        )


@dataclass
class BeamData:
    """Настройки луча для beam-анимаций"""
    width: int = 8                    # Ширина луча в пикселях
    segments: int = 10                # Количество сегментов (для волнистости)
    wave_amplitude: float = 0.0       # Амплитуда волны (0 = прямой луч)
    wave_frequency: float = 1.0       # Частота волны
    duration_ms: int = 500            # Длительность отображения
    fade_in_ms: int = 50              # Время появления
    fade_out_ms: int = 100            # Время исчезновения
    color_start: str = "#FFFFFF"      # Цвет у кастера
    color_end: str = "#FFFFFF"        # Цвет у цели
    glow_enabled: bool = True         # Эффект свечения
    glow_radius: int = 4              # Радиус свечения

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "segments": self.segments,
            "wave_amplitude": self.wave_amplitude,
            "wave_frequency": self.wave_frequency,
            "duration_ms": self.duration_ms,
            "fade_in_ms": self.fade_in_ms,
            "fade_out_ms": self.fade_out_ms,
            "color_start": self.color_start,
            "color_end": self.color_end,
            "glow_enabled": self.glow_enabled,
            "glow_radius": self.glow_radius,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeamData":
        return cls(
            width=data.get("width", 8),
            segments=data.get("segments", 10),
            wave_amplitude=data.get("wave_amplitude", 0.0),
            wave_frequency=data.get("wave_frequency", 1.0),
            duration_ms=data.get("duration_ms", 500),
            fade_in_ms=data.get("fade_in_ms", 50),
            fade_out_ms=data.get("fade_out_ms", 100),
            color_start=data.get("color_start", "#FFFFFF"),
            color_end=data.get("color_end", "#FFFFFF"),
            glow_enabled=data.get("glow_enabled", True),
            glow_radius=data.get("glow_radius", 4),
        )


@dataclass
class AreaEffectData:
    """Настройки для area-анимаций"""
    radius_cells: int = 1              # Радиус в клетках поля боя
    shape: str = "circle"              # circle, square, cone, line
    fill_alpha: float = 0.3            # Прозрачность заливки
    border_width: int = 2              # Толщина границы
    border_color: str = "#FFFFFF"      # Цвет границы
    fill_color: str = "#FF0000"        # Цвет заливки
    pulse_enabled: bool = False        # Пульсация
    pulse_speed: float = 1.0           # Скорость пульсации

    def to_dict(self) -> Dict[str, Any]:
        return {
            "radius_cells": self.radius_cells,
            "shape": self.shape,
            "fill_alpha": self.fill_alpha,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "fill_color": self.fill_color,
            "pulse_enabled": self.pulse_enabled,
            "pulse_speed": self.pulse_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AreaEffectData":
        return cls(
            radius_cells=data.get("radius_cells", 1),
            shape=data.get("shape", "circle"),
            fill_alpha=data.get("fill_alpha", 0.3),
            border_width=data.get("border_width", 2),
            border_color=data.get("border_color", "#FFFFFF"),
            fill_color=data.get("fill_color", "#FF0000"),
            pulse_enabled=data.get("pulse_enabled", False),
            pulse_speed=data.get("pulse_speed", 1.0),
        )


@dataclass
class AnimationTimingData:
    """Тайминги анимации относительно применения эффекта"""
    # Когда применяется урон/эффект
    damage_apply_at: str = "on_hit"    # on_cast, on_hit, on_end
    damage_delay_ms: int = 0           # Задержка применения урона после события
    # Для нескольких ударов
    multi_hit_delay_ms: int = 200      # Задержка между ударами
    # Синхронизация со звуком
    sound_delay_ms: int = 0            # Задержка звука относительно анимации

    def to_dict(self) -> Dict[str, Any]:
        return {
            "damage_apply_at": self.damage_apply_at,
            "damage_delay_ms": self.damage_delay_ms,
            "multi_hit_delay_ms": self.multi_hit_delay_ms,
            "sound_delay_ms": self.sound_delay_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationTimingData":
        return cls(
            damage_apply_at=data.get("damage_apply_at", "on_hit"),
            damage_delay_ms=data.get("damage_delay_ms", 0),
            multi_hit_delay_ms=data.get("multi_hit_delay_ms", 200),
            sound_delay_ms=data.get("sound_delay_ms", 0),
        )


@dataclass
class AnimationFrameData:
    """Данные кадра анимации"""
    sprite_path: str = ""
    duration_ms: int = 100  # Длительность кадра в мс (можно переопределить)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprite_path": self.sprite_path,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationFrameData":
        if isinstance(data, str):
            # Обратная совместимость - если просто строка пути
            return cls(sprite_path=data)
        return cls(
            sprite_path=data.get("sprite_path", ""),
            duration_ms=data.get("duration_ms", 100),
        )


@dataclass
class VisualData:
    """Визуальные данные умения"""
    icon_path: str = ""
    animation_type: str = "default"
    particle_effect: str = ""
    sound_use: str = ""
    sound_hit: str = ""
    color_primary: str = "#FFFFFF"
    color_secondary: str = "#888888"
    # Анимация из спрайтов (1-8 кадров)
    animation_frames: List[AnimationFrameData] = field(default_factory=list)
    animation_fps: int = 10  # Кадров в секунду (по умолчанию)
    animation_loop_mode: str = "once"  # once, loop, ping_pong
    animation_scale: float = 1.0  # Масштаб анимации
    animation_vertical_offset: float = 0.0  # Вертикальное смещение анимации в пикселях

    # Настройки отображения анимации на поле боя
    display_type: str = "on_target"    # Тип отображения (static, projectile, beam, etc.)
    anchor_point: str = "center"        # Точка привязки (center, top, bottom, weapon, head)

    # Настройки снаряда (для display_type = projectile)
    projectile: Optional[ProjectileData] = None
    # Настройки луча (для display_type = beam)
    beam: Optional[BeamData] = None
    # Настройки области (для display_type = area)
    area_effect: Optional[AreaEffectData] = None
    # Тайминги анимации
    timing: AnimationTimingData = field(default_factory=AnimationTimingData)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "icon_path": self.icon_path,
            "animation_type": self.animation_type,
            "particle_effect": self.particle_effect,
            "sound_use": self.sound_use,
            "sound_hit": self.sound_hit,
            "color_primary": self.color_primary,
            "color_secondary": self.color_secondary,
            "animation_frames": [f.to_dict() for f in self.animation_frames],
            "animation_fps": self.animation_fps,
            "animation_loop_mode": self.animation_loop_mode,
            "animation_scale": self.animation_scale,
            "animation_vertical_offset": self.animation_vertical_offset,
            "display_type": self.display_type,
            "anchor_point": self.anchor_point,
            "timing": self.timing.to_dict(),
        }
        if self.projectile:
            result["projectile"] = self.projectile.to_dict()
        if self.beam:
            result["beam"] = self.beam.to_dict()
        if self.area_effect:
            result["area_effect"] = self.area_effect.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualData":
        frames = []
        for f in data.get("animation_frames", []):
            frames.append(AnimationFrameData.from_dict(f))

        projectile = None
        if "projectile" in data:
            projectile = ProjectileData.from_dict(data["projectile"])

        beam = None
        if "beam" in data:
            beam = BeamData.from_dict(data["beam"])

        area_effect = None
        if "area_effect" in data:
            area_effect = AreaEffectData.from_dict(data["area_effect"])

        return cls(
            icon_path=data.get("icon_path", ""),
            animation_type=data.get("animation_type", "default"),
            particle_effect=data.get("particle_effect", ""),
            sound_use=data.get("sound_use", ""),
            sound_hit=data.get("sound_hit", ""),
            color_primary=data.get("color_primary", "#FFFFFF"),
            color_secondary=data.get("color_secondary", "#888888"),
            animation_frames=frames,
            animation_fps=data.get("animation_fps", 10),
            animation_loop_mode=data.get("animation_loop_mode", "once"),
            animation_scale=data.get("animation_scale", 1.0),
            animation_vertical_offset=data.get("animation_vertical_offset", 0.0),
            display_type=data.get("display_type", "on_target"),
            anchor_point=data.get("anchor_point", "center"),
            projectile=projectile,
            beam=beam,
            area_effect=area_effect,
            timing=AnimationTimingData.from_dict(data.get("timing", {})),
        )


@dataclass
class SkillData:
    """Основные данные умения"""
    # Идентификация
    skill_id: str = ""
    name: str = ""
    description: str = ""
    category: str = "combat"
    skill_type: str = "active"

    # Компоненты
    costs: CostData = field(default_factory=CostData)
    requirements: RequirementData = field(default_factory=RequirementData)
    targeting: TargetingData = field(default_factory=TargetingData)
    damage: Optional[DamageData] = None
    healing: Optional[HealingData] = None
    status_effects: List[StatusEffectData] = field(default_factory=list)
    rank_progression: RankProgressionData = field(default_factory=RankProgressionData)
    visuals: VisualData = field(default_factory=VisualData)

    # Дополнительные параметры
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для экспорта"""
        data = {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "skill_type": self.skill_type,
            "costs": self.costs.to_dict(),
            "requirements": self.requirements.to_dict(),
            "targeting": self.targeting.to_dict(),
            "status_effects": [se.to_dict() for se in self.status_effects],
            "rank_progression": self.rank_progression.to_dict(),
            "visuals": self.visuals.to_dict(),
        }

        if self.damage:
            data["damage"] = self.damage.to_dict()
        if self.healing:
            data["healing"] = self.healing.to_dict()
        if self.custom_params:
            data["custom_params"] = self.custom_params

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillData":
        """Создание из словаря"""
        damage = None
        if "damage" in data:
            damage = DamageData.from_dict(data["damage"])

        healing = None
        if "healing" in data:
            healing = HealingData.from_dict(data["healing"])

        status_effects = [
            StatusEffectData.from_dict(se)
            for se in data.get("status_effects", [])
        ]

        return cls(
            skill_id=data.get("skill_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", "combat"),
            skill_type=data.get("skill_type", "active"),
            costs=CostData.from_dict(data.get("costs", {})),
            requirements=RequirementData.from_dict(data.get("requirements", {})),
            targeting=TargetingData.from_dict(data.get("targeting", {})),
            damage=damage,
            healing=healing,
            status_effects=status_effects,
            rank_progression=RankProgressionData.from_dict(data.get("rank_progression", {})),
            visuals=VisualData.from_dict(data.get("visuals", {})),
            custom_params=data.get("custom_params", {}),
        )

    def to_game_config_format(self) -> Dict[str, Any]:
        """
        Преобразование в формат, совместимый с skills_config.json
        """
        config = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "mana_cost": self.costs.mana_cost,
            "stamina_cost": self.costs.stamina_cost,
            "cooldown": self.costs.cooldown,
            "tactical_range": self.targeting.tactical_range,
        }

        # Пассивное умение
        if self.skill_type == "passive":
            config["passive"] = True

        # Требования оружия
        if self.requirements.required_weapon != "any":
            config["required_weapon"] = self.requirements.required_weapon

        # Урон
        if self.damage:
            if self.damage.base_damage > 0:
                config["base_damage"] = self.damage.base_damage
            if self.damage.damage_multiplier != 1.0:
                config["base_damage_multiplier"] = self.damage.damage_multiplier
            if self.damage.damage_multiplier_per_rank != 0:
                config["damage_multiplier_per_rank"] = self.damage.damage_multiplier_per_rank
            if self.damage.ignores_armor:
                config["ignores_armor"] = True
            if self.damage.armor_penetration_base > 0:
                config["base_armor_penetration"] = self.damage.armor_penetration_base
                config["armor_penetration_per_rank"] = self.damage.armor_penetration_per_rank
            if self.damage.crit_chance_bonus > 0:
                config["base_crit_chance"] = self.damage.crit_chance_bonus
                config["crit_chance_per_rank"] = self.damage.crit_chance_per_rank
            if self.damage.hit_count_base > 1:
                config["base_hits"] = self.damage.hit_count_base
                config["hits_per_rank"] = self.damage.hit_count_per_rank

            # Скейлинг по атрибутам
            for scale in self.damage.scaling:
                config[f"{scale.attribute}_multiplier"] = scale.multiplier

        # Лечение
        if self.healing:
            if self.healing.heal_percent_max_hp > 0:
                config["base_heal_percent"] = self.healing.heal_percent_max_hp
                config["heal_percent_per_rank"] = self.healing.heal_percent_per_rank
            if self.healing.heal_over_time:
                config["base_heal_per_turn"] = self.healing.heal_per_turn_base
                config["heal_per_turn_per_rank"] = self.healing.heal_per_turn_per_rank
                config["base_duration"] = self.healing.duration_base
                config["duration_per_rank"] = self.healing.duration_per_rank

            for scale in self.healing.scaling:
                config[f"{scale.attribute}_multiplier"] = scale.multiplier

        # Статус-эффекты
        for effect in self.status_effects:
            prefix = effect.effect_type
            if effect.chance_base < 1.0:
                config[f"base_{prefix}_chance"] = effect.chance_base
                config[f"{prefix}_chance_per_rank"] = effect.chance_per_rank
            config[f"{prefix}_base_damage" if prefix in ["poison", "burn", "bleed"]
                   else f"base_{prefix}_amount"] = effect.value_base
            config[f"{prefix}_damage_per_rank" if prefix in ["poison", "burn", "bleed"]
                   else f"{prefix}_per_rank"] = effect.value_per_rank
            config[f"{prefix}_base_duration"] = effect.duration_base
            config[f"{prefix}_duration_per_rank"] = effect.duration_per_rank

        # Дальность
        if self.targeting.min_range > 0:
            config["min_range"] = self.targeting.min_range
        if self.targeting.range_per_rank > 0:
            config["range_per_rank"] = self.targeting.range_per_rank

        # AoE
        if self.targeting.aoe_radius > 0:
            config["aoe_range"] = self.targeting.aoe_radius

        # Knockback
        if self.targeting.knockback_chance > 0:
            config["base_knockback_chance"] = self.targeting.knockback_chance
            config["knockback_chance_per_rank"] = self.targeting.knockback_chance_per_rank

        # Описания по рангам
        if self.rank_progression.descriptions_per_rank:
            config["description_per_rank"] = self.rank_progression.descriptions_per_rank

        return config

    def validate(self) -> List[str]:
        """Валидация данных умения, возвращает список ошибок"""
        errors = []

        if not self.skill_id:
            errors.append("ID умения обязателен")
        elif not self.skill_id.replace("_", "").isalnum():
            errors.append("ID должен содержать только буквы, цифры и подчеркивания")

        if not self.name:
            errors.append("Название умения обязательно")

        if self.targeting.tactical_range < 0:
            errors.append("Дальность не может быть отрицательной")

        if self.targeting.min_range > self.targeting.tactical_range:
            errors.append("Минимальная дальность не может превышать максимальную")

        if self.costs.cooldown < 0:
            errors.append("Кулдаун не может быть отрицательным")

        return errors
