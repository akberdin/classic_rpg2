"""
Загрузчик умений из формата Skills Crafter
Преобразует данные из моделей skills_crafter для использования в тестовой арене
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class AnimationFrame:
    """Кадр анимации умения"""
    sprite_path: str
    duration_ms: int = 100


@dataclass
class TestSkill:
    """Умение для тестовой арены"""
    skill_id: str
    name: str
    description: str

    # Основные параметры
    skill_type: str = "active"  # active, passive
    category: str = "combat"

    # Стоимость
    mana_cost: int = 0
    stamina_cost: int = 0
    health_cost: int = 0
    cooldown: int = 0
    current_cooldown: int = 0

    # Урон
    base_damage: int = 0
    damage_per_rank: int = 0
    damage_scaling_attribute: str = "strength"
    damage_scaling_factor: float = 0.0
    damage_type: str = "physical"  # physical, magic, fire, ice, poison

    # Лечение
    base_healing: int = 0
    healing_per_rank: int = 0

    # Targeting
    target_type: str = "single_enemy"  # self, single_enemy, single_ally, all_enemies, etc
    tactical_range: int = 1
    area_type: str = "single"  # single, circle, cone, line
    area_radius: int = 0

    # Статус-эффекты
    status_effects: List[Dict[str, Any]] = field(default_factory=list)

    # Визуальные настройки
    animation_type: str = "static"  # static, projectile, impact, on_target, on_caster, beam
    icon_path: str = ""
    animation_frames: List[AnimationFrame] = field(default_factory=list)
    projectile_speed: float = 300.0
    projectile_trajectory: str = "straight"  # straight, arc, wave, homing
    animation_duration: float = 0.5

    # Ранг
    current_rank: int = 1
    max_rank: int = 5

    def get_effect_color(self) -> tuple:
        """Получить цвет эффекта на основе категории/типа урона"""
        # Цвета по типу урона
        damage_colors = {
            "fire": (255, 100, 50),
            "ice": (100, 180, 255),
            "poison": (100, 200, 80),
            "lightning": (255, 255, 100),
            "physical": (200, 200, 200),
            "magic": (180, 100, 255),
        }
        # Цвета по категории
        category_colors = {
            "magic": (150, 100, 255),
            "warrior": (200, 100, 80),
            "shadow": (100, 80, 120),
            "hunter": (100, 180, 100),
        }

        # Сначала проверяем тип урона
        if self.damage_type in damage_colors:
            return damage_colors[self.damage_type]

        # По названию умения (для молнии и т.д.)
        name_lower = self.name.lower()
        if "молни" in name_lower or "lightning" in name_lower:
            return damage_colors["lightning"]
        if "огн" in name_lower or "fire" in name_lower:
            return damage_colors["fire"]
        if "лед" in name_lower or "ice" in name_lower:
            return damage_colors["ice"]
        if "яд" in name_lower or "отрав" in name_lower or "poison" in name_lower:
            return damage_colors["poison"]

        # По категории
        if self.category in category_colors:
            return category_colors[self.category]

        return (200, 180, 100)  # По умолчанию - золотистый

    def get_damage(self, caster) -> int:
        """Вычислить урон умения"""
        base = self.base_damage + (self.current_rank - 1) * self.damage_per_rank

        # Добавляем масштабирование
        scaling_value = 0
        if self.damage_scaling_attribute == "strength":
            scaling_value = caster.strength
        elif self.damage_scaling_attribute == "dexterity":
            scaling_value = caster.dexterity
        elif self.damage_scaling_attribute == "intelligence":
            scaling_value = caster.intelligence

        scaling_bonus = int(scaling_value * self.damage_scaling_factor)
        return base + scaling_bonus

    def get_healing(self, caster) -> int:
        """Вычислить лечение умения"""
        return self.base_healing + (self.current_rank - 1) * self.healing_per_rank

    def can_use(self, caster) -> tuple:
        """Проверить, можно ли использовать умение"""
        if self.current_cooldown > 0:
            return False, f"Умение на перезарядке ({self.current_cooldown} ходов)"

        if caster.mana < self.mana_cost:
            return False, f"Недостаточно маны (нужно {self.mana_cost})"

        if caster.stamina < self.stamina_cost:
            return False, f"Недостаточно выносливости (нужно {self.stamina_cost})"

        if caster.health <= self.health_cost:
            return False, "Недостаточно здоровья"

        return True, ""

    def use(self, caster, target) -> Dict[str, Any]:
        """Использовать умение"""
        can, reason = self.can_use(caster)
        if not can:
            return {"success": False, "message": reason}

        # Тратим ресурсы
        caster.mana -= self.mana_cost
        caster.stamina -= self.stamina_cost
        if self.health_cost > 0:
            caster.health -= self.health_cost

        # Устанавливаем перезарядку
        self.current_cooldown = self.cooldown

        result = {
            "success": True,
            "skill_id": self.skill_id,
            "skill_name": self.name,
            "caster": caster.name,
            "target": target.name if target else None,
            "damage": 0,
            "healing": 0,
            "effects_applied": [],
            "killed": False,
        }

        # Применяем урон
        if self.base_damage > 0 and target:
            damage = self.get_damage(caster)
            actual_damage = target.take_damage(damage)
            result["damage"] = actual_damage

            if not target.is_alive:
                result["killed"] = True

        # Применяем лечение
        if self.base_healing > 0:
            heal_target = target if self.target_type in ["single_ally", "self"] else caster
            healing = self.get_healing(caster)
            actual_healing = heal_target.heal(healing)
            result["healing"] = actual_healing

        # Применяем статус-эффекты
        if self.status_effects and target:
            from .entities import StatusEffect
            import random

            for effect_data in self.status_effects:
                chance = effect_data.get("chance_base", 1.0)
                if random.random() <= chance:
                    effect = StatusEffect(
                        effect_type=effect_data.get("effect_type", "burn"),
                        name=effect_data.get("name", "Эффект"),
                        duration=effect_data.get("duration_base", 3),
                        remaining_duration=effect_data.get("duration_base", 3),
                        value=effect_data.get("value_base", 5),
                        icon_id=effect_data.get("effect_type", "burn"),
                    )
                    target.add_status_effect(effect)
                    result["effects_applied"].append(effect.name)

        # Формируем сообщение
        msg_parts = [f"{caster.name} использует {self.name}"]
        if result["damage"] > 0:
            msg_parts.append(f"наносит {result['damage']} урона")
        if result["healing"] > 0:
            msg_parts.append(f"восстанавливает {result['healing']} здоровья")
        if result["effects_applied"]:
            msg_parts.append(f"накладывает: {', '.join(result['effects_applied'])}")
        if result["killed"]:
            msg_parts.append(f"{target.name} повержен!")

        result["message"] = " - ".join(msg_parts)

        return result

    def tick_cooldown(self):
        """Уменьшить перезарядку"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class SkillsCrafterLoader:
    """Загрузчик умений из формата Skills Crafter"""

    # Путь к папке с сохраненными умениями
    DEFAULT_SKILLS_PATH = "utils/skills_crafter/saved_skills"

    def __init__(self, skills_path: Optional[str] = None):
        self.skills_path = skills_path or self.DEFAULT_SKILLS_PATH
        self.loaded_skills: Dict[str, TestSkill] = {}

    def load_from_json(self, json_path: str) -> Optional[TestSkill]:
        """
        Загрузить умение из JSON файла формата Skills Crafter

        Args:
            json_path: Путь к JSON файлу

        Returns:
            TestSkill или None если ошибка
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._convert_to_test_skill(data)
        except Exception as e:
            print(f"Ошибка загрузки умения из {json_path}: {e}")
            return None

    def load_from_dict(self, data: Dict[str, Any]) -> Optional[TestSkill]:
        """
        Загрузить умение из словаря

        Args:
            data: Данные умения в формате Skills Crafter

        Returns:
            TestSkill
        """
        return self._convert_to_test_skill(data)

    def load_from_test_config(self, config_path: str = None) -> Dict[str, TestSkill]:
        """
        Загрузить умения из test_skills.json (формат Skills Crafter)

        Args:
            config_path: Путь к конфигу (по умолчанию utils/skills_crafter/test_skills.json)

        Returns:
            Словарь загруженных умений
        """
        if config_path is None:
            config_path = "utils/skills_crafter/test_skills.json"

        skills = {}

        if not os.path.exists(config_path):
            print(f"Конфиг {config_path} не найден")
            return skills

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                skills_data = json.load(f)

            if isinstance(skills_data, list):
                for skill_data in skills_data:
                    skill = self._convert_to_test_skill(skill_data)
                    if skill:
                        skills[skill.skill_id] = skill
            elif isinstance(skills_data, dict):
                # Поддержка старого формата {skills: [...]}
                for skill_data in skills_data.get("skills", []):
                    skill = self._convert_to_test_skill(skill_data)
                    if skill:
                        skills[skill.skill_id] = skill

            print(f"Загружено {len(skills)} умений из {config_path}")
        except Exception as e:
            print(f"Ошибка загрузки умений из {config_path}: {e}")

        return skills

    def _convert_to_test_skill(self, data: Dict[str, Any]) -> TestSkill:
        """
        Преобразовать данные Skills Crafter в TestSkill

        Args:
            data: Данные умения из Skills Crafter
        """
        # Извлекаем данные урона
        damage_data = data.get("damage", {})
        healing_data = data.get("healing", {})
        # Поддержка обоих форматов: cost и costs
        cost_data = data.get("costs", data.get("cost", {}))
        targeting_data = data.get("targeting", {})
        # Поддержка обоих форматов: visual и visuals
        visual_data = data.get("visuals", data.get("visual", {}))
        effects_data = data.get("status_effects", [])

        # Преобразуем статус-эффекты
        status_effects = []
        if isinstance(effects_data, list):
            status_effects = effects_data
        elif isinstance(effects_data, dict):
            status_effects = [effects_data]

        # Получаем данные анимации
        animation_frames = []
        animation_type = "static"
        projectile_speed = 300.0
        projectile_trajectory = "straight"
        animation_duration = 0.5

        if visual_data:
            animation_type = visual_data.get("display_type", "static")
            animation_duration = visual_data.get("duration", 0.5)

            # Парсим кадры анимации
            frames_data = visual_data.get("animation_frames", visual_data.get("frames", []))
            if frames_data:
                for frame_data in frames_data:
                    if isinstance(frame_data, dict):
                        frame = AnimationFrame(
                            sprite_path=frame_data.get("sprite_path", ""),
                            duration_ms=frame_data.get("duration_ms", 100)
                        )
                        animation_frames.append(frame)
                    elif isinstance(frame_data, str):
                        animation_frames.append(AnimationFrame(sprite_path=frame_data))

            # Парсим данные снаряда
            projectile_data = visual_data.get("projectile", {})
            if projectile_data:
                projectile_speed = projectile_data.get("speed", 300.0)
                projectile_trajectory = projectile_data.get("trajectory", "straight")

        # Извлекаем данные масштабирования
        scaling_attr = "strength"
        scaling_factor = 0.0
        scaling_list = damage_data.get("scaling", [])
        if scaling_list and isinstance(scaling_list, list) and len(scaling_list) > 0:
            scaling_attr = scaling_list[0].get("attribute", "strength")
            scaling_factor = scaling_list[0].get("factor", 0.0)
        elif damage_data.get("scaling_attribute"):
            scaling_attr = damage_data.get("scaling_attribute")
            scaling_factor = damage_data.get("scaling_factor", 0.0)

        skill = TestSkill(
            # Поддержка обоих форматов: id и skill_id
            skill_id=data.get("skill_id", data.get("id", "unknown_skill")),
            name=data.get("name", "Неизвестное умение"),
            description=data.get("description", ""),

            skill_type=data.get("skill_type", "active"),
            category=data.get("category", "combat"),

            # Стоимость (поддержка обоих форматов: mana/mana_cost)
            mana_cost=cost_data.get("mana_cost", cost_data.get("mana", 0)),
            stamina_cost=cost_data.get("stamina_cost", cost_data.get("stamina", 0)),
            health_cost=cost_data.get("health_cost", cost_data.get("health", 0)),
            cooldown=cost_data.get("cooldown", 0),

            # Урон
            base_damage=int(damage_data.get("base_damage", 0)),
            damage_per_rank=damage_data.get("damage_per_rank", 0),
            damage_scaling_attribute=scaling_attr,
            damage_scaling_factor=scaling_factor,
            damage_type=damage_data.get("damage_type", "physical"),

            # Лечение
            base_healing=healing_data.get("base_healing", 0),
            healing_per_rank=healing_data.get("healing_per_rank", 0),

            # Targeting (поддержка обоих форматов: range/tactical_range)
            target_type=targeting_data.get("target_type", "single_enemy"),
            tactical_range=targeting_data.get("tactical_range", targeting_data.get("range", 1)),
            area_type=targeting_data.get("area_type", "single"),
            area_radius=targeting_data.get("aoe_radius", targeting_data.get("area_radius", 0)),

            # Эффекты
            status_effects=status_effects,

            # Визуальные
            animation_type=animation_type,
            animation_frames=animation_frames,
            projectile_speed=projectile_speed,
            projectile_trajectory=projectile_trajectory,
            animation_duration=animation_duration,
        )

        self.loaded_skills[skill.skill_id] = skill
        return skill

    def load_all_from_directory(self, directory: Optional[str] = None) -> Dict[str, TestSkill]:
        """
        Загрузить все умения из директории

        Args:
            directory: Путь к директории (по умолчанию saved_skills)

        Returns:
            Словарь загруженных умений
        """
        path = directory or self.skills_path
        skills = {}

        if not os.path.exists(path):
            print(f"Директория {path} не найдена")
            return skills

        for filename in os.listdir(path):
            if filename.endswith('.json'):
                filepath = os.path.join(path, filename)
                skill = self.load_from_json(filepath)
                if skill:
                    skills[skill.skill_id] = skill

        print(f"Загружено {len(skills)} умений из {path}")
        return skills

    def create_default_skills(self) -> Dict[str, TestSkill]:
        """
        Создать набор тестовых умений по умолчанию
        для тестирования без загрузки из файлов
        """
        default_skills = {
            "basic_attack": {
                "id": "basic_attack",
                "name": "Базовая атака",
                "description": "Простой удар оружием",
                "skill_type": "active",
                "category": "combat",
                "cost": {"mana": 0, "stamina": 5, "cooldown": 0},
                "damage": {
                    "base_damage": 10,
                    "damage_per_rank": 5,
                    "scaling_attribute": "strength",
                    "scaling_factor": 0.5,
                    "damage_type": "physical"
                },
                "targeting": {"target_type": "single_enemy", "range": 1},
                "visual": {"display_type": "static", "duration": 0.3}
            },
            "fireball": {
                "id": "fireball",
                "name": "Огненный шар",
                "description": "Мощный огненный снаряд",
                "skill_type": "active",
                "category": "magic",
                "cost": {"mana": 15, "stamina": 0, "cooldown": 2},
                "damage": {
                    "base_damage": 25,
                    "damage_per_rank": 10,
                    "scaling_attribute": "intelligence",
                    "scaling_factor": 0.8,
                    "damage_type": "fire"
                },
                "targeting": {"target_type": "single_enemy", "range": 4, "area_type": "circle", "area_radius": 1},
                "status_effects": [{
                    "effect_type": "burn",
                    "name": "Горение",
                    "chance_base": 0.5,
                    "duration_base": 3,
                    "value_base": 5
                }],
                "visual": {
                    "display_type": "projectile",
                    "duration": 0.5,
                    "projectile": {"speed": 300}
                }
            },
            "heal": {
                "id": "heal",
                "name": "Лечение",
                "description": "Восстанавливает здоровье цели",
                "skill_type": "active",
                "category": "magic",
                "cost": {"mana": 20, "stamina": 0, "cooldown": 3},
                "healing": {
                    "base_healing": 30,
                    "healing_per_rank": 15
                },
                "targeting": {"target_type": "single_ally", "range": 3},
                "visual": {"display_type": "on_target", "duration": 0.6}
            },
            "poison_strike": {
                "id": "poison_strike",
                "name": "Отравленный удар",
                "description": "Удар, отравляющий цель",
                "skill_type": "active",
                "category": "shadow",
                "cost": {"mana": 10, "stamina": 10, "cooldown": 3},
                "damage": {
                    "base_damage": 15,
                    "damage_per_rank": 5,
                    "scaling_attribute": "dexterity",
                    "scaling_factor": 0.4,
                    "damage_type": "poison"
                },
                "targeting": {"target_type": "single_enemy", "range": 1},
                "status_effects": [{
                    "effect_type": "poison",
                    "name": "Отравление",
                    "chance_base": 0.8,
                    "duration_base": 4,
                    "value_base": 8
                }],
                "visual": {"display_type": "static", "duration": 0.4}
            },
            "power_strike": {
                "id": "power_strike",
                "name": "Мощный удар",
                "description": "Сильный удар с повышенным уроном",
                "skill_type": "active",
                "category": "warrior",
                "cost": {"mana": 0, "stamina": 20, "cooldown": 2},
                "damage": {
                    "base_damage": 30,
                    "damage_per_rank": 12,
                    "scaling_attribute": "strength",
                    "scaling_factor": 0.7,
                    "damage_type": "physical"
                },
                "targeting": {"target_type": "single_enemy", "range": 1},
                "visual": {"display_type": "static", "duration": 0.4}
            },
            "ice_bolt": {
                "id": "ice_bolt",
                "name": "Ледяная стрела",
                "description": "Магический ледяной снаряд",
                "skill_type": "active",
                "category": "magic",
                "cost": {"mana": 12, "stamina": 0, "cooldown": 1},
                "damage": {
                    "base_damage": 18,
                    "damage_per_rank": 8,
                    "scaling_attribute": "intelligence",
                    "scaling_factor": 0.6,
                    "damage_type": "ice"
                },
                "targeting": {"target_type": "single_enemy", "range": 5},
                "visual": {
                    "display_type": "projectile",
                    "duration": 0.4,
                    "projectile": {"speed": 400}
                }
            },
            "regeneration": {
                "id": "regeneration",
                "name": "Регенерация",
                "description": "Постепенно восстанавливает здоровье",
                "skill_type": "active",
                "category": "magic",
                "cost": {"mana": 25, "stamina": 0, "cooldown": 5},
                "targeting": {"target_type": "self", "range": 0},
                "status_effects": [{
                    "effect_type": "regeneration",
                    "name": "Регенерация",
                    "chance_base": 1.0,
                    "duration_base": 5,
                    "value_base": 10
                }],
                "visual": {"display_type": "on_caster", "duration": 0.5}
            },
            "arrow_shot": {
                "id": "arrow_shot",
                "name": "Выстрел из лука",
                "description": "Дальнобойная атака",
                "skill_type": "active",
                "category": "hunter",
                "cost": {"mana": 0, "stamina": 8, "cooldown": 0},
                "damage": {
                    "base_damage": 12,
                    "damage_per_rank": 6,
                    "scaling_attribute": "dexterity",
                    "scaling_factor": 0.6,
                    "damage_type": "physical"
                },
                "targeting": {"target_type": "single_enemy", "range": 6},
                "visual": {
                    "display_type": "projectile",
                    "duration": 0.3,
                    "projectile": {"speed": 500}
                }
            },
        }

        skills = {}
        for skill_data in default_skills.values():
            skill = self._convert_to_test_skill(skill_data)
            skills[skill.skill_id] = skill

        print(f"Создано {len(skills)} умений по умолчанию")
        return skills

    def get_skill(self, skill_id: str) -> Optional[TestSkill]:
        """Получить загруженное умение по ID"""
        return self.loaded_skills.get(skill_id)

    def get_all_skills(self) -> Dict[str, TestSkill]:
        """Получить все загруженные умения"""
        return self.loaded_skills.copy()
