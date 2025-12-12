"""
Боевые умения.

Содержит базовые боевые умения:
- BasicAttack - базовая атака
- PowerStrike - мощный удар
- PoisonStrike - ядовитый удар
- StunStrike - оглушающий удар
- BattleCry - боевой клич
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import PoisonEffect, StunEffect, StrengthBoostEffect


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

            # Вычисляем урон с учетом ранга (20% за ранг - улучшено)
            base_damage = user.get_total_damage()
            rank_multiplier = 1.0 + (self.rank - 1) * 0.2  # 1.0x -> 1.8x на 5 ранге
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


class PowerStrike(Skill):
    """Мощный удар - наносит увеличенный урон"""

    def __init__(self):
        super().__init__(
            name="Мощный удар",
            description="Наносит урон с увеличенным коэффициентом. Сила растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=10,
            cooldown=2
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.8, пробитие брони 0%",
            "Ранг 2: Урон x2.15, пробитие брони 10%",
            "Ранг 3: Урон x2.5, пробитие брони 20%",
            "Ранг 4: Урон x2.85, пробитие брони 30%",
            "Ранг 5: Урон x3.2, пробитие брони 40%"
        ]

    def use(self, user, target=None):
        """Использовать мощный удар"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Коэффициент урона растет с рангом (1.8x + 0.35x за ранг - улучшено)
            damage_multiplier = 1.8 + (self.rank - 1) * 0.35  # 1.8x -> 3.2x на 5 ранге

            base_damage = user.get_total_damage()
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # Бонус пробития брони на высоких рангах (игнорируем часть защиты)
            armor_penetration = (self.rank - 1) * 0.1  # 0% -> 40% на 5 ранге

            # Учитываем защиту цели с пробитием
            target_defense = target.get_total_defense()
            effective_defense = int(target_defense * (1 - armor_penetration))
            actual_damage = max(1, total_damage - effective_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['armor_penetration'] = int(armor_penetration * 100)

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} наносит разрушительный мощный удар {target.name} на {actual_damage} урона!"
            else:
                result['message'] = f"{user.name} наносит мощный удар {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class PoisonStrike(Skill):
    """Отравленный удар - наносит урон и накладывает яд"""

    def __init__(self):
        super().__init__(
            name="Отравленный удар",
            description="Наносит урон и накладывает отравление. Длительность растет с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=15,
            cooldown=4
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Яд 5 урона/ход на 3 хода",
            "Ранг 2: Яд 9 урона/ход на 4 хода",
            "Ранг 3: Яд 13 урона/ход на 5 ходов",
            "Ранг 4: Яд 17 урона/ход на 6 ходов",
            "Ранг 5: Яд 21 урона/ход на 7 ходов"
        ]

    def use(self, user, target=None):
        """Использовать отравленный удар"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Наносим урон с множителем от ранга (улучшено)
            base_damage = user.get_total_damage()
            damage_multiplier = 1.0 + (self.rank - 1) * 0.15  # 1.0x -> 1.6x на 5 ранге
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Значительно улучшенный яд с рангом
            poison_duration = 3 + (self.rank - 1)  # 3-7 ходов
            poison_damage = 5 + (self.rank - 1) * 4  # 5-21 урона/ход

            # На высоких рангах яд также снижает защиту цели
            defense_reduction = (self.rank - 1) * 2  # 0-8 снижения защиты

            # Накладываем отравление
            poison = PoisonEffect(duration=poison_duration, damage_per_turn=poison_damage)

            # Добавляем эффект в правильное место
            if hasattr(target, 'skill_manager'):
                # Для игрока - в skill_manager
                target.skill_manager.status_effects.append(poison)
            else:
                # Для NPC без skill_manager - в status_effects
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(poison)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['poison_applied'] = True
            result['poison_damage'] = poison_damage
            result['poison_duration'] = poison_duration

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} наносит смертоносный отравленный удар {target.name} на {actual_damage} урона и накладывает сильный яд ({poison_damage} урона/ход на {poison_duration} ходов)!"
            else:
                result['message'] = f"{user.name} наносит отравленный удар {target.name} на {actual_damage} урона и накладывает яд ({poison_damage} урона/ход на {poison_duration} ходов)!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class StunStrike(Skill):
    """Оглушающий удар - наносит урон и оглушает"""

    def __init__(self):
        super().__init__(
            name="Оглушающий удар",
            description="Наносит урон и оглушает. Шанс оглушения растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=20,
            cooldown=5
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.5, шанс оглушения 50%, 1 ход",
            "Ранг 2: Урон x1.7, шанс оглушения 60%, 1 ход",
            "Ранг 3: Урон x1.9, шанс оглушения 70%, 2 хода",
            "Ранг 4: Урон x2.1, шанс оглушения 80%, 2 хода",
            "Ранг 5: Урон x2.3, шанс оглушения 90%, 3 хода"
        ]

    def use(self, user, target=None):
        """Использовать оглушающий удар"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Наносим урон с множителем (1.5x + 0.2x за ранг - улучшено)
            damage_multiplier = 1.5 + (self.rank - 1) * 0.2  # 1.5x -> 2.3x на 5 ранге
            base_damage = user.get_total_damage()
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Шанс оглушения растет с рангом (50% + 10% за ранг, max 90%)
            stun_chance = min(0.90, 0.5 + (self.rank - 1) * 0.1)
            # Длительность оглушения также растет с рангом
            stun_duration = 1 + (self.rank - 1) // 2  # 1-3 хода

            stunned = False
            if random.random() < stun_chance:
                stun = StunEffect(duration=stun_duration)

                # Добавляем эффект в правильное место
                if hasattr(target, 'skill_manager'):
                    # Для игрока - в skill_manager
                    target.skill_manager.status_effects.append(stun)
                else:
                    # Для NPC без skill_manager - в status_effects
                    if not hasattr(target, 'status_effects'):
                        target.status_effects = []
                    target.status_effects.append(stun)

                stun.apply(target)  # Применяем эффект оглушения
                stunned = True

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['stunned'] = stunned
            result['stun_chance'] = int(stun_chance * 100)

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} наносит сокрушительный оглушающий удар {target.name} на {actual_damage} урона!"
            else:
                result['message'] = f"{user.name} наносит оглушающий удар {target.name} на {actual_damage} урона!"

            if stunned:
                result['message'] += f" {target.name} оглушен на {stun_duration} ход(а)!"

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

        # Значительно улучшенный бонус силы от ранга
        boost_amount = 5 + self.rank * 4  # 9 -> 25 на 5 ранге (было 5-13)
        boost_duration = 3 + self.rank  # 4-8 ходов (было 3-7)

        # На высоких рангах также даёт бонус к шансу крита
        crit_bonus = (self.rank - 1) * 3  # 0-12% к криту

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


# ==================== МАГИЧЕСКИЕ УМЕНИЯ ====================

