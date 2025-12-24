"""
Модуль экспорта и импорта умений
Конвертация между форматами Skills Crafter и игры
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import (
    SkillData, CostData, RequirementData, TargetingData,
    DamageData, HealingData, StatusEffectData, ScalingData,
    RankProgressionData, VisualData
)


class SkillExporter:
    """Экспортер умений в различные форматы"""

    @staticmethod
    def to_game_config(skills: List[SkillData]) -> Dict[str, Any]:
        """
        Экспорт списка умений в формат skills_config.json

        Args:
            skills: Список умений

        Returns:
            Словарь в формате игровой конфигурации
        """
        output = {
            "_description": "Конфигурация умений (экспорт из Skills Crafter)",
            "_version": "2.0.0",
        }

        # Группировка по категориям
        category_sections = {
            "combat": "combat_skills",
            "general": "combat_skills",
            "warrior": "combat_skills",
            "shadow": "combat_skills",
            "hunter": "combat_skills",
            "magic": "magic_skills",
            "crafting": "crafting_skills",
            "exploration": "exploration_skills",
        }

        weapon_skills: Dict[str, Dict[str, Any]] = {}

        for skill in skills:
            game_data = skill.to_game_config_format()

            # Оружейные умения группируем отдельно
            if skill.requirements.required_weapon != "any":
                weapon_type = f"{skill.requirements.required_weapon}_skills"
                if weapon_type not in weapon_skills:
                    weapon_skills[weapon_type] = {
                        "_description": f"Умения для {skill.requirements.required_weapon}"
                    }
                weapon_skills[weapon_type][skill.skill_id] = game_data
            else:
                # Обычные умения
                section = category_sections.get(skill.category, "combat_skills")
                if section not in output:
                    output[section] = {}
                output[section][skill.skill_id] = game_data

        if weapon_skills:
            output["weapon_skills"] = weapon_skills

        return output

    @staticmethod
    def to_python_class(skill: SkillData) -> str:
        """
        Генерация Python класса умения

        Args:
            skill: Данные умения

        Returns:
            Строка с кодом класса
        """
        class_name = "".join(word.title() for word in skill.skill_id.split("_"))

        lines = [
            f'class {class_name}(Skill):',
            f'    """',
            f'    {skill.name}',
            f'    {skill.description}',
            f'    """',
            f'',
            f'    def __init__(self):',
            f'        super().__init__()',
            f'        self.name = "{skill.name}"',
            f'        self.description = "{skill.description}"',
            f'        self.category = SkillCategory.{skill.category.upper()}',
            f'        self.mana_cost = {skill.costs.mana_cost}',
            f'        self.stamina_cost = {skill.costs.stamina_cost}',
            f'        self.cooldown = {skill.costs.cooldown}',
            f'        self.tactical_range = {skill.targeting.tactical_range}',
        ]

        if skill.requirements.required_weapon != "any":
            lines.append(f'        self.required_weapon = "{skill.requirements.required_weapon}"')

        lines.extend([
            f'',
            f'    def use(self, user, target) -> dict:',
            f'        """Применение умения"""',
            f'        if not self.can_use(user):',
            f'            return {{"success": False, "message": "Недостаточно ресурсов"}}',
            f'',
            f'        self._consume_resources(user)',
            f'        result = {{"success": True, "damage": 0, "message": ""}}',
        ])

        # Добавление логики урона
        if skill.damage:
            lines.extend([
                f'',
                f'        # Расчет урона',
                f'        base_damage = {skill.damage.base_damage}',
                f'        multiplier = {skill.damage.damage_multiplier} + {skill.damage.damage_multiplier_per_rank} * (self.rank - 1)',
                f'        damage = base_damage + user.get_total_damage() * multiplier',
            ])

            for scaling in skill.damage.scaling:
                lines.append(
                    f'        damage += user.{scaling.attribute} * {scaling.multiplier}'
                )

            lines.extend([
                f'',
                f'        target.take_damage(int(damage))',
                f'        result["damage"] = int(damage)',
                f'        result["message"] = f"{{self.name}} наносит {{int(damage)}} урона"',
            ])

        # Добавление статус-эффектов
        if skill.status_effects:
            lines.append(f'')
            lines.append(f'        # Статус-эффекты')
            for effect in skill.status_effects:
                lines.extend([
                    f'        if random.random() < {effect.chance_base}:',
                    f'            effect = {effect.effect_type.title()}Effect(',
                    f'                duration={effect.duration_base} + {effect.duration_per_rank} * (self.rank - 1),',
                    f'                value={effect.value_base} + {effect.value_per_rank} * (self.rank - 1)',
                    f'            )',
                    f'            target.apply_effect(effect)',
                ])

        lines.extend([
            f'',
            f'        self._record_use()',
            f'        return result',
        ])

        return "\n".join(lines)

    @staticmethod
    def save_to_file(skills: List[SkillData], filepath: str, format: str = "crafter"):
        """
        Сохранение умений в файл

        Args:
            skills: Список умений
            filepath: Путь к файлу
            format: Формат ('crafter' или 'game')
        """
        if format == "game":
            data = SkillExporter.to_game_config(skills)
        else:
            data = [skill.to_dict() for skill in skills]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class SkillImporter:
    """Импортер умений из различных форматов"""

    @staticmethod
    def from_game_config(filepath: str) -> List[SkillData]:
        """
        Импорт умений из skills_config.json

        Args:
            filepath: Путь к файлу конфигурации

        Returns:
            Список импортированных умений
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        skills = []

        # Категории для импорта
        categories = [
            ("combat_skills", "combat"),
            ("magic_skills", "magic"),
            ("healing_skills", "magic"),
            ("crafting_skills", "crafting"),
            ("exploration_skills", "exploration"),
        ]

        for section_key, category in categories:
            if section_key in data:
                for skill_id, skill_data in data[section_key].items():
                    if skill_id.startswith("_"):
                        continue
                    skill = SkillImporter._parse_game_skill(skill_id, skill_data, category)
                    skills.append(skill)

        # Оружейные умения
        if "weapon_skills" in data:
            for weapon_type, weapon_skills in data["weapon_skills"].items():
                if weapon_type.startswith("_"):
                    continue
                for skill_id, skill_data in weapon_skills.items():
                    if skill_id.startswith("_"):
                        continue
                    skill = SkillImporter._parse_game_skill(skill_id, skill_data, "combat")
                    skill.requirements.required_weapon = weapon_type.replace("_skills", "")
                    skills.append(skill)

        return skills

    @staticmethod
    def from_crafter_file(filepath: str) -> List[SkillData]:
        """
        Импорт из файла Skills Crafter

        Args:
            filepath: Путь к файлу

        Returns:
            Список умений
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return [SkillData.from_dict(item) for item in data]
        elif isinstance(data, dict):
            skills = []
            for skill_id, skill_data in data.items():
                if not skill_id.startswith("_"):
                    skill_data["skill_id"] = skill_id
                    skills.append(SkillData.from_dict(skill_data))
            return skills

        return []

    @staticmethod
    def _parse_game_skill(skill_id: str, data: Dict[str, Any], category: str) -> SkillData:
        """Парсинг умения из игрового формата"""
        skill = SkillData()
        skill.skill_id = skill_id
        skill.name = data.get("name", skill_id)
        skill.description = data.get("description", "")
        skill.category = data.get("category", category)
        skill.skill_type = "passive" if data.get("passive", False) else "active"

        # Затраты
        skill.costs = CostData(
            mana_cost=data.get("mana_cost", 0),
            mana_cost_per_rank=data.get("mana_cost_per_rank", 0),
            stamina_cost=data.get("stamina_cost", 0),
            cooldown=data.get("cooldown", 0),
        )

        # Требования
        skill.requirements = RequirementData(
            required_weapon=data.get("required_weapon", "any"),
        )

        # Нацеливание
        skill.targeting = TargetingData(
            tactical_range=data.get("tactical_range", 1),
            min_range=data.get("min_range", 0),
            aoe_radius=data.get("aoe_range", 0),
        )

        # Урон
        if any(k in data for k in ["base_damage", "base_damage_multiplier", "damage_multiplier_per_rank"]):
            scaling = []
            for attr in ["intelligence", "strength", "dexterity", "spirit"]:
                mult = data.get(f"{attr}_multiplier")
                if mult:
                    scaling.append(ScalingData(attribute=attr, multiplier=mult))

            skill.damage = DamageData(
                base_damage=data.get("base_damage", 0),
                damage_multiplier=data.get("base_damage_multiplier", 1.0),
                damage_multiplier_per_rank=data.get("damage_multiplier_per_rank", 0),
                scaling=scaling,
                ignores_armor=data.get("ignores_armor", False),
                armor_penetration_base=data.get("base_armor_penetration", 0),
                armor_penetration_per_rank=data.get("armor_penetration_per_rank", 0),
                crit_chance_bonus=data.get("base_crit_chance", 0),
                crit_chance_per_rank=data.get("crit_chance_per_rank", 0),
                hit_count_base=data.get("base_hits", 1) or data.get("base_shots", 1),
                hit_count_per_rank=data.get("hits_per_rank", 0) or data.get("shots_per_rank", 0),
            )

        # Лечение
        if any(k in data for k in ["base_heal_percent", "base_heal_per_turn"]):
            skill.healing = HealingData(
                heal_percent_max_hp=data.get("base_heal_percent", 0),
                heal_percent_per_rank=data.get("heal_percent_per_rank", 0),
                heal_over_time=bool(data.get("base_heal_per_turn")),
                heal_per_turn_base=data.get("base_heal_per_turn", 0),
                heal_per_turn_per_rank=data.get("heal_per_turn_per_rank", 0),
                duration_base=data.get("base_duration", 0),
                duration_per_rank=data.get("duration_per_rank", 0),
            )

        # Статус-эффекты
        effect_types = ["poison", "stun", "bleed", "burn", "slow"]
        for eff_type in effect_types:
            if any(k.startswith(eff_type) for k in data.keys()):
                effect = StatusEffectData(
                    effect_type=eff_type,
                    chance_base=data.get(f"base_{eff_type}_chance", 1.0),
                    chance_per_rank=data.get(f"{eff_type}_chance_per_rank", 0),
                    duration_base=data.get(f"{eff_type}_base_duration", 3),
                    duration_per_rank=data.get(f"{eff_type}_duration_per_rank", 0),
                    value_base=data.get(f"{eff_type}_base_damage", 0) or data.get(f"base_{eff_type}_amount", 0),
                    value_per_rank=data.get(f"{eff_type}_damage_per_rank", 0) or data.get(f"{eff_type}_per_rank", 0),
                )
                skill.status_effects.append(effect)

        # Описания по рангам
        if "description_per_rank" in data:
            skill.rank_progression.descriptions_per_rank = data["description_per_rank"]

        return skill


class SkillValidator:
    """Валидатор умений"""

    @staticmethod
    def validate(skill: SkillData) -> List[str]:
        """
        Полная валидация умения

        Args:
            skill: Данные умения

        Returns:
            Список ошибок (пустой если валидация успешна)
        """
        errors = []

        # Базовая валидация
        errors.extend(skill.validate())

        # Дополнительные проверки
        if skill.costs.mana_cost < 0:
            errors.append("Стоимость маны не может быть отрицательной")

        if skill.costs.stamina_cost < 0:
            errors.append("Стоимость выносливости не может быть отрицательной")

        if skill.costs.cooldown < 0:
            errors.append("Кулдаун не может быть отрицательным")

        # Проверка масштабирования урона
        if skill.damage:
            for scaling in skill.damage.scaling:
                if scaling.multiplier < 0:
                    errors.append(f"Множитель {scaling.attribute} не может быть отрицательным")

        # Проверка эффектов
        for i, effect in enumerate(skill.status_effects):
            if effect.chance_base < 0 or effect.chance_base > 1:
                errors.append(f"Эффект {i+1}: шанс должен быть от 0 до 1")
            if effect.duration_base <= 0:
                errors.append(f"Эффект {i+1}: длительность должна быть положительной")

        # Проверка прогрессии
        if skill.rank_progression.max_rank < 1:
            errors.append("Максимальный ранг должен быть минимум 1")

        if skill.rank_progression.max_rank > 10:
            errors.append("Максимальный ранг не должен превышать 10")

        return errors

    @staticmethod
    def validate_batch(skills: List[SkillData]) -> Dict[str, List[str]]:
        """
        Валидация списка умений

        Args:
            skills: Список умений

        Returns:
            Словарь {skill_id: [ошибки]}
        """
        results = {}

        # Проверка на дубликаты ID
        skill_ids = [s.skill_id for s in skills]
        duplicates = set(x for x in skill_ids if skill_ids.count(x) > 1)

        for skill in skills:
            errors = SkillValidator.validate(skill)

            if skill.skill_id in duplicates:
                errors.append(f"Дублирующийся ID: {skill.skill_id}")

            if errors:
                results[skill.skill_id] = errors

        return results
