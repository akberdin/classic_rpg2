"""
Боевые умения.

Содержит базовые боевые умения:
- BasicAttack - базовая атака
- BattleCry - боевой клич
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import StrengthBoostEffect
from game.config.config_loader import get_skills_config


class BasicAttack(Skill):
    """Базовая атака - доступна с самого начала"""

    def __init__(self):
        super().__init__(
            name="Базовая атака",
            description="Простой удар оружием. Урон увеличивается с рангом",
            category=SkillCategory.GENERAL,
            stamina_cost=5,
            cooldown=0
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Множитель урона x1.0",
            "Ранг 2: Множитель урона x1.2",
            "Ранг 3: Множитель урона x1.4",
            "Ранг 4: Множитель урона x1.6",
            "Ранг 5: Множитель урона x1.8"
        ]

    def use(self, user, target=None):
        """Использовать базовую атаку"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Вычисляем урон с учетом ранга - параметры из конфига
            config = get_skills_config()
            base_multiplier = config.get_combat_skill('basic_attack', 'base_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_combat_skill('basic_attack', 'rank_multiplier_per_rank', default=0.2)

            base_damage = user.get_total_damage()
            rank_multiplier = base_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * rank_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # Учитываем защиту цели
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} наносит мощнейшую базовую атаку {target.name} на {actual_damage} урона!"
            else:
                result['message'] = f"{user.name} наносит базовую атаку {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class BattleCry(Skill):
    """Боевой клич - усиливает силу на несколько ходов"""

    def __init__(self):
        super().__init__(
            name="Боевой клич",
            description="Увеличивает силу. Бонус и длительность растут с рангом",
            category=SkillCategory.GENERAL,
            stamina_cost=15,
            cooldown=6
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +9 Сила на 4 хода",
            "Ранг 2: +13 Сила на 5 ходов",
            "Ранг 3: +17 Сила на 6 ходов",
            "Ранг 4: +21 Сила на 7 ходов",
            "Ранг 5: +25 Сила на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать боевой клич"""
        result = super().use(user, target)

        # Параметры из конфига
        config = get_skills_config()
        base_strength_boost = config.get_combat_skill('battle_cry', 'base_strength_boost', default=5)
        strength_boost_per_rank = config.get_combat_skill('battle_cry', 'strength_boost_per_rank', default=4)
        base_duration = config.get_combat_skill('battle_cry', 'base_duration', default=3)
        duration_per_rank = config.get_combat_skill('battle_cry', 'duration_per_rank', default=1)

        # Бонус силы от ранга
        boost_amount = base_strength_boost + self.rank * strength_boost_per_rank
        boost_duration = base_duration + self.rank * duration_per_rank

        # Накладываем усиление на себя
        boost = StrengthBoostEffect(duration=boost_duration, boost_amount=boost_amount)

        # Добавляем эффект в правильное место
        if hasattr(user, 'skill_manager'):
            # Для игрока - в skill_manager
            user.skill_manager.status_effects.append(boost)
        else:
            # Для NPC без skill_manager - в status_effects
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(boost)

        boost.apply(user)  # Применяем эффект

        result['strength_boost'] = boost_amount
        result['duration'] = boost_duration
        result['message'] = f"{user.name} издает боевой клич! Сила +{boost_amount} на {boost_duration} ходов!"

        return result
