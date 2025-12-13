"""
Магические умения.

Содержит:
- Heal - лечение
- Regeneration - регенерация
- StaminaRecovery - восстановление выносливости
- Fireball - огненный шар
- IceBolt - ледяная стрела
- Lightning - молния
- MagicMissile - магическая стрела
- MageShield - магический щит
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import RegenerationEffect, StaminaRecoveryEffect, ShieldEffect, StunEffect, BurnEffect
from game.config.config_loader import get_skills_config


class Heal(Skill):
    """Лечение - восстанавливает здоровье"""

    def __init__(self):
        super().__init__(
            name="Лечение",
            description="Восстанавливает HP. Эффективность растет с рангом",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=20,
            cooldown=3
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Восстановление 35% макс. HP",
            "Ранг 2: Восстановление 47% макс. HP",
            "Ранг 3: Восстановление 59% макс. HP",
            "Ранг 4: Восстановление 71% макс. HP",
            "Ранг 5: Восстановление 83% макс. HP"
        ]

    def use(self, user, target=None):
        """Использовать лечение - ВСЕГДА лечит себя (user)"""
        result = super().use(user, target)

        # Лечение ВСЕГДА применяется к себе (user), не к target
        heal_target = user

        # Базовое лечение зависит от интеллекта и духа (с учетом экипировки)
        intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
        spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

        # Лечение: процент от макс. здоровья + бонус от интеллекта и духа
        # Улучшено: 35% + 12% за ранг, плюс бонус от статов
        heal_percent = 0.35 + (self.rank - 1) * 0.12  # 35% -> 83% на 5 ранге
        max_health = heal_target.get_effective_max_health() if hasattr(heal_target, 'get_effective_max_health') else heal_target.max_health
        base_heal = int(max_health * heal_percent)
        stat_bonus = int(intelligence * 2 + spirit * 1.5) * self.rank  # Бонус от статов
        heal_amount = base_heal + stat_bonus

        old_health = heal_target.health
        heal_target.health = min(max_health, heal_target.health + heal_amount)
        actual_heal = heal_target.health - old_health

        result['heal'] = actual_heal
        result['message'] = f"{user.name} восстанавливает {actual_heal} HP!"

        return result


class Regeneration(Skill):
    """Регенерация - накладывает эффект восстановления HP"""

    def __init__(self):
        super().__init__(
            name="Регенерация",
            description="Восстанавливает HP каждый ход. Эффективность растет с рангом",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать регенерацию - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Регенерация ВСЕГДА применяется к себе (user), не к target
        regen_target = user

        # Получаем характеристики заклинателя (с учетом экипировки)
        intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
        spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

        # Значительно улучшенная регенерация с рангом
        base_heal = 15 + self.rank * 6  # 21 -> 45 на 5 ранге
        # Процент от макс. здоровья
        max_health = regen_target.get_effective_max_health() if hasattr(regen_target, 'get_effective_max_health') else getattr(regen_target, 'max_health', 100)
        percent_heal = int(max_health * (0.04 + self.rank * 0.02))  # 6% -> 14% за ход
        # Бонус от статов
        stat_bonus = int((intelligence + spirit) * 0.5 * self.rank)
        heal_per_turn = base_heal + percent_heal + stat_bonus

        regen_duration = 4 + self.rank  # 5-9 ходов

        # Накладываем эффект регенерации на себя
        regen = RegenerationEffect(duration=regen_duration, heal_per_turn=heal_per_turn)

        # Добавляем эффект в правильное место
        if hasattr(regen_target, 'skill_manager'):
            # Для игрока - в skill_manager
            regen_target.skill_manager.status_effects.append(regen)
        else:
            # Для NPC без skill_manager - в status_effects
            if not hasattr(regen_target, 'status_effects'):
                regen_target.status_effects = []
            regen_target.status_effects.append(regen)

        result['heal_per_turn'] = heal_per_turn
        result['duration'] = regen_duration
        result['message'] = f"{user.name} накладывает регенерацию на себя! (+{heal_per_turn} HP/ход на {regen_duration} ходов)"

        return result


class StaminaRecovery(Skill):
    """Восстановление выносливости - накладывает эффект восстановления выносливости"""

    def __init__(self):
        super().__init__(
            name="Восстановление выносливости",
            description="Восстанавливает выносливость каждый ход. Эффективность растет с рангом",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать восстановление выносливости - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Восстановление выносливости ВСЕГДА применяется к себе (user), не к target
        recovery_target = user

        # Получаем характеристики заклинателя (с учетом экипировки)
        intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
        spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

        # Восстановление выносливости с рангом
        base_recovery = 15 + self.rank * 5  # 20 -> 40 на 5 ранге
        # Процент от макс. выносливости
        max_stamina = recovery_target.get_effective_max_stamina() if hasattr(recovery_target, 'get_effective_max_stamina') else getattr(recovery_target, 'max_stamina', 100)
        percent_recovery = int(max_stamina * (0.05 + self.rank * 0.02))  # 7% -> 15% за ход
        # Бонус от статов
        stat_bonus = int((intelligence + spirit) * 0.4 * self.rank)
        stamina_per_turn = base_recovery + percent_recovery + stat_bonus

        recovery_duration = 4 + self.rank  # 5-9 ходов

        # Накладываем эффект восстановления выносливости на себя
        stamina_effect = StaminaRecoveryEffect(duration=recovery_duration, stamina_per_turn=stamina_per_turn)

        # Добавляем эффект в правильное место
        if hasattr(recovery_target, 'skill_manager'):
            # Для игрока - в skill_manager
            recovery_target.skill_manager.status_effects.append(stamina_effect)
        else:
            # Для NPC без skill_manager - в status_effects
            if not hasattr(recovery_target, 'status_effects'):
                recovery_target.status_effects = []
            recovery_target.status_effects.append(stamina_effect)

        result['stamina_per_turn'] = stamina_per_turn
        result['duration'] = recovery_duration
        result['message'] = f"{user.name} накладывает восстановление выносливости на себя! (+{stamina_per_turn} выносливости/ход на {recovery_duration} ходов)"

        return result


# ==================== АТАКУЮЩИЕ МАГИЧЕСКИЕ УМЕНИЯ ====================

class Fireball(Skill):
    """Огненный шар - мощная магическая атака огнем с эффектом поджога"""

    def __init__(self):
        super().__init__(
            name="Огненный шар",
            description="Мощная огненная атака. Поджигает цель (1-3 хода, 10% урона). Огонь может перекинуться на соседей (20% шанс). Игнорирует броню",
            category=SkillCategory.MAGE, tactical_range=6,
            mana_cost=35,
            cooldown=3
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.0, горение 10% урона, шанс поджога соседей 20%",
            "Ранг 2: Урон x1.35, горение 15% урона, шанс поджога соседей 25%",
            "Ранг 3: Урон x1.7, горение 20% урона, шанс поджога соседей 30%",
            "Ранг 4: Урон x2.05, горение 25% урона, шанс поджога соседей 35%",
            "Ранг 5: Урон x2.4, горение 30% урона, шанс поджога соседей 40%"
        ]

    def use(self, user, target=None):
        """Использовать огненный шар"""
        import random
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Параметры из конфига
            config = get_skills_config()
            base_damage_value = config.get_magic_skill('fireball', 'base_damage', default=20)
            intelligence_multiplier = config.get_magic_skill('fireball', 'intelligence_multiplier', default=4.0)
            spirit_multiplier = config.get_magic_skill('fireball', 'spirit_multiplier', default=0.3)
            base_rank_multiplier = config.get_magic_skill('fireball', 'base_rank_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_magic_skill('fireball', 'rank_multiplier_per_rank', default=0.35)
            burn_damage_percent_base = config.get_magic_skill('fireball', 'burn_damage_percent_base', default=0.10)
            burn_damage_percent_per_rank = config.get_magic_skill('fireball', 'burn_damage_percent_per_rank', default=0.05)
            burn_duration_min = config.get_magic_skill('fireball', 'burn_duration_min', default=1)
            burn_duration_max = config.get_magic_skill('fireball', 'burn_duration_max', default=3)
            burn_spread_chance_base = config.get_magic_skill('fireball', 'burn_spread_chance_base', default=0.20)
            burn_spread_chance_per_rank = config.get_magic_skill('fireball', 'burn_spread_chance_per_rank', default=0.05)

            # Базовый урон зависит от интеллекта (с учетом экипировки)
            intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
            spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

            # Урон: base + интеллект*multiplier + дух*multiplier
            base_damage = base_damage_value + intelligence * intelligence_multiplier + spirit * spirit_multiplier
            # Множитель от ранга
            damage_multiplier = base_rank_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)

            # === МЕХАНИКА ПОДЖОГА ЦЕЛИ ===
            # Урон от горения
            burn_damage_percent = burn_damage_percent_base + (self.rank - 1) * burn_damage_percent_per_rank
            burn_damage_per_turn = max(1, int(actual_damage * burn_damage_percent))

            # Длительность горения (случайно)
            burn_duration = random.randint(burn_duration_min, burn_duration_max)

            # Применяем эффект горения на цель
            burn_effect = BurnEffect(duration=burn_duration, damage_per_turn=burn_damage_per_turn)

            # Добавляем эффект в правильное место
            if hasattr(target, 'skill_manager') and target.skill_manager:
                target.skill_manager.status_effects.append(burn_effect)
            else:
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(burn_effect)

            result['burn_applied'] = True
            result['burn_damage'] = burn_damage_per_turn
            result['burn_duration'] = burn_duration

            # === МЕХАНИКА РАСПРОСТРАНЕНИЯ ОГНЯ НА СОСЕДЕЙ ===
            # Шанс поджога соседей
            spread_chance = burn_spread_chance_base + (self.rank - 1) * burn_spread_chance_per_rank

            # Передаем информацию для обработки в тактическом бою
            result['burn_spread'] = {
                'chance': spread_chance,
                'damage_per_turn': burn_damage_per_turn,
                'duration_range': (1, 3)  # Случайная длительность 1-3 хода
            }

            # Формируем сообщение
            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} запускает мощнейший огненный шар в {target.name} и наносит {actual_damage} магического урона!"
            else:
                result['message'] = f"{user.name} запускает огненный шар в {target.name} и наносит {actual_damage} магического урона!"

            result['message'] += f" {target.name} загорается! ({burn_damage_per_turn} урона/ход на {burn_duration} ход(а))"

            if magic_defense > 0:
                result['message'] += f" (магическая защита поглотила {result['magic_blocked']} урона)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class IceBolt(Skill):
    """Ледяная стрела - магическая атака льдом с замедлением"""

    def __init__(self):
        super().__init__(
            name="Ледяная стрела",
            description="Ледяная атака с шансом замедления. Игнорирует броню, снижается магической защитой",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=25,
            cooldown=2
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.0, шанс замедления 30%",
            "Ранг 2: Урон x1.3, шанс замедления 40%",
            "Ранг 3: Урон x1.6, шанс замедления 50%",
            "Ранг 4: Урон x1.9, шанс замедления 60%",
            "Ранг 5: Урон x2.2, шанс замедления 70%"
        ]

    def use(self, user, target=None):
        """Использовать ледяную стрелу"""
        import random
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Параметры из конфига
            config = get_skills_config()
            base_damage_value = config.get_magic_skill('ice_bolt', 'base_damage', default=15)
            intelligence_multiplier = config.get_magic_skill('ice_bolt', 'intelligence_multiplier', default=3.0)
            spirit_multiplier = config.get_magic_skill('ice_bolt', 'spirit_multiplier', default=0.3)
            base_rank_multiplier = config.get_magic_skill('ice_bolt', 'base_rank_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_magic_skill('ice_bolt', 'rank_multiplier_per_rank', default=0.3)
            base_slow_chance = config.get_magic_skill('ice_bolt', 'base_slow_chance', default=0.4)
            slow_chance_per_rank = config.get_magic_skill('ice_bolt', 'slow_chance_per_rank', default=0.1)
            base_slow_duration = config.get_magic_skill('ice_bolt', 'base_slow_duration', default=1)
            slow_duration_rank_divisor = config.get_magic_skill('ice_bolt', 'slow_duration_rank_divisor', default=2)

            # Урон немного меньше чем у огненного шара, но меньше кулдаун и есть замедление (с учетом экипировки)
            intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
            spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

            # Урон: base + интеллект*multiplier + дух*multiplier
            base_damage = base_damage_value + intelligence * intelligence_multiplier + spirit * spirit_multiplier
            damage_multiplier = base_rank_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            # Шанс и длительность замедления
            slow_chance = base_slow_chance + (self.rank - 1) * slow_chance_per_rank
            slow_duration = base_slow_duration + (self.rank - 1) // slow_duration_rank_divisor
            slowed = False
            if random.random() < slow_chance:
                slow = StunEffect(duration=slow_duration)
                slow.name = "Обморожение"

                # Добавляем эффект в правильное место
                if hasattr(target, 'skill_manager'):
                    # Для игрока - в skill_manager
                    target.skill_manager.status_effects.append(slow)
                else:
                    # Для NPC без skill_manager - в status_effects
                    if not hasattr(target, 'status_effects'):
                        target.status_effects = []
                    target.status_effects.append(slow)

                slow.apply(target)  # Применяем эффект замедления
                slowed = True

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)
            result['slowed'] = slowed

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} запускает смертоносную ледяную стрелу в {target.name} и наносит {actual_damage} магического урона!"
            else:
                result['message'] = f"{user.name} запускает ледяную стрелу в {target.name} и наносит {actual_damage} магического урона!"

            if slowed:
                result['message'] += f" {target.name} заморожен на {slow_duration} ход(а)!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class Lightning(Skill):
    """Молния - быстрая магическая атака с высоким уроном"""

    def __init__(self):
        super().__init__(
            name="Молния",
            description="Мощнейшая атака молнией. Высокий урон, игнорирует броню, снижается магической защитой",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=50,
            cooldown=4
        )

    def use(self, user, target=None):
        """Использовать молнию"""
        import random
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Параметры из конфига
            config = get_skills_config()
            base_damage_value = config.get_magic_skill('lightning', 'base_damage', default=30)
            intelligence_multiplier = config.get_magic_skill('lightning', 'intelligence_multiplier', default=5.0)
            spirit_multiplier = config.get_magic_skill('lightning', 'spirit_multiplier', default=0.3)
            base_rank_multiplier = config.get_magic_skill('lightning', 'base_rank_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_magic_skill('lightning', 'rank_multiplier_per_rank', default=0.4)

            # Самый высокий урон среди магических атак (с учетом экипировки)
            intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
            spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

            # Урон: base + интеллект*multiplier + дух*multiplier
            base_damage = base_damage_value + intelligence * intelligence_multiplier + spirit * spirit_multiplier
            damage_multiplier = base_rank_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} поражает {target.name} разрушительной молнией и наносит {actual_damage} магического урона!"
            else:
                result['message'] = f"{user.name} поражает {target.name} молнией и наносит {actual_damage} магического урона!"

            if magic_defense > 0:
                result['message'] += f" (магическая защита поглотила {result['magic_blocked']} урона)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class MagicMissile(Skill):
    """Магическая стрела - базовая магическая атака"""

    def __init__(self):
        super().__init__(
            name="Магическая стрела",
            description="Базовая магическая атака. Низкая стоимость, игнорирует броню, снижается магической защитой",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=4,
            cooldown=1
        )

    def use(self, user, target=None):
        """Использовать магическую стрелу"""
        import random
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Параметры из конфига
            config = get_skills_config()
            base_damage_value = config.get_magic_skill('magic_missile', 'base_damage', default=12)
            intelligence_multiplier = config.get_magic_skill('magic_missile', 'intelligence_multiplier', default=2.5)
            spirit_multiplier = config.get_magic_skill('magic_missile', 'spirit_multiplier', default=0.2)
            base_rank_multiplier = config.get_magic_skill('magic_missile', 'base_rank_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_magic_skill('magic_missile', 'rank_multiplier_per_rank', default=0.25)

            # Базовая магическая атака с низкой стоимостью (с учетом экипировки)
            intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
            spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

            # Урон: base + интеллект*multiplier + дух*multiplier
            base_damage = base_damage_value + intelligence * intelligence_multiplier + spirit * spirit_multiplier
            damage_multiplier = base_rank_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} запускает усиленную магическую стрелу в {target.name} и наносит {actual_damage} магического урона!"
            else:
                result['message'] = f"{user.name} запускает магическую стрелу в {target.name} и наносит {actual_damage} магического урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class MageShield(Skill):
    """Магический щит - защитная магия"""

    def __init__(self):
        super().__init__(
            name="Щит мага",
            description="Создает магический щит, повышающий физическую защиту в бою. Эффект зависит от интеллекта и уровня умения",
            category=SkillCategory.MAGE,tactical_range=6,
            mana_cost=25,
            cooldown=3
        )

    def use(self, user, target=None):
        """Использовать щит мага - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Щит мага ВСЕГДА применяется к себе (user), не к target
        shield_target = user

        # Расчет бонуса защиты: базовые 50% + интеллект/2 + ранг*10% (с учетом экипировки)
        intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
        defense_bonus = int(50 + intelligence / 2 + (self.rank - 1) * 10)

        # Длительность: 3 хода + ранг
        duration = 3 + self.rank

        # Создаем и применяем эффект щита на себя
        shield_effect = ShieldEffect(duration=duration, defense_bonus=defense_bonus)

        # Получаем список эффектов
        if hasattr(shield_target, 'skill_manager'):
            effects_list = shield_target.skill_manager.status_effects
        else:
            if not hasattr(shield_target, 'status_effects'):
                shield_target.status_effects = []
            effects_list = shield_target.status_effects

        # Проверяем, нет ли уже щита (чтобы избежать многократного наложения)
        has_shield = any(isinstance(effect, ShieldEffect) for effect in effects_list)
        if has_shield:
            result['message'] = f"{user.name} уже защищен магическим щитом!"
        else:
            effects_list.append(shield_effect)
            result['shield'] = defense_bonus
            result['duration'] = duration
            result['message'] = f"{user.name} создает магический щит на себя! (+{defense_bonus}% защита на {duration} ходов)"

        return result


class FireArrow(Skill):
    """Огненная стрела - дистанционная огненная атака с шансом поджога"""

    def __init__(self):
        super().__init__(
            name="Огненная стрела",
            description="Дистанционная огненная атака. Игнорирует физическую броню, может поджечь цель",
            category=SkillCategory.MAGE,
            tactical_range=4,
            mana_cost=5,
            cooldown=1
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.0 (10 + Интеллект*2.0), дальность 5, мана 5, шанс поджога 20%",
            "Ранг 2: Урон x1.2 (10 + Интеллект*2.0), дальность 6, мана 10, шанс поджога 30%",
            "Ранг 3: Урон x1.4 (10 + Интеллект*2.0), дальность 7, мана 15, шанс поджога 40%",
            "Ранг 4: Урон x1.6 (10 + Интеллект*2.0), дальность 8, мана 20, шанс поджога 50%",
            "Ранг 5: Урон x1.8 (10 + Интеллект*2.0), дальность 9, мана 25, шанс поджога 60%"
        ]

    def get_tactical_range(self):
        """Дальность увеличивается с рангом: 4 + ранг"""
        return 4 + self.rank

    def get_mana_cost(self):
        """Стоимость маны увеличивается с рангом: 5 * ранг"""
        return 5 * self.rank

    def use(self, user, target=None):
        """Использовать огненную стрелу"""
        import random
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Параметры из конфига
            config = get_skills_config()
            base_damage_value = config.get_magic_skill('fire_arrow', 'base_damage', default=10)
            intelligence_multiplier = config.get_magic_skill('fire_arrow', 'intelligence_multiplier', default=2.0)
            spirit_multiplier = config.get_magic_skill('fire_arrow', 'spirit_multiplier', default=0.2)
            base_rank_multiplier = config.get_magic_skill('fire_arrow', 'base_rank_multiplier', default=1.0)
            rank_multiplier_per_rank = config.get_magic_skill('fire_arrow', 'rank_multiplier_per_rank', default=0.2)

            # Базовый урон зависит от интеллекта и духа (с учетом экипировки)
            intelligence = user.get_effective_intelligence() if hasattr(user, 'get_effective_intelligence') else getattr(user, 'intelligence', 1)
            spirit = user.get_effective_spirit() if hasattr(user, 'get_effective_spirit') else getattr(user, 'spirit', 1)

            # Урон: base + интеллект*multiplier + дух*multiplier
            base_damage = base_damage_value + intelligence * intelligence_multiplier + spirit * spirit_multiplier
            # Множитель от ранга
            damage_multiplier = base_rank_multiplier + (self.rank - 1) * rank_multiplier_per_rank
            total_damage = int(base_damage * damage_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # ИГНОРИРУЕМ ФИЗИЧЕСКУЮ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)

            # === МЕХАНИКА ПОДЖОГА ===
            # Параметры поджога из конфига
            burn_base_chance = config.get_magic_skill('fire_arrow', 'burn_base_chance', default=0.20)
            burn_chance_per_rank = config.get_magic_skill('fire_arrow', 'burn_chance_per_rank', default=0.10)
            burn_duration = config.get_magic_skill('fire_arrow', 'burn_duration', default=3)
            burn_damage_percent = config.get_magic_skill('fire_arrow', 'burn_damage_percent', default=0.50)

            # Шанс поджога: базовый + бонус за ранг
            burn_chance = burn_base_chance + (self.rank - 1) * burn_chance_per_rank

            burn_applied = False
            if random.random() < burn_chance:
                # Урон от горения: процент от нанесенного урона
                burn_damage_per_turn = max(1, int(actual_damage * burn_damage_percent))

                # Применяем эффект горения на цель
                burn_effect = BurnEffect(duration=burn_duration, damage_per_turn=burn_damage_per_turn)

                # Добавляем эффект в правильное место
                if hasattr(target, 'skill_manager') and target.skill_manager:
                    target.skill_manager.status_effects.append(burn_effect)
                else:
                    if not hasattr(target, 'status_effects'):
                        target.status_effects = []
                    target.status_effects.append(burn_effect)

                burn_applied = True
                result['burn_applied'] = True
                result['burn_damage'] = burn_damage_per_turn
                result['burn_duration'] = burn_duration

            # Формируем сообщение
            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} запускает мощнейшую огненную стрелу в {target.name} и наносит {actual_damage} магического урона!"
            else:
                result['message'] = f"{user.name} запускает огненную стрелу в {target.name} и наносит {actual_damage} магического урона!"

            if burn_applied:
                result['message'] += f" {target.name} загорается! ({burn_damage_per_turn} урона/ход на {burn_duration} ход(а))"

            if magic_defense > 0:
                result['message'] += f" (магическая защита поглотила {result['magic_blocked']} урона)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


# ==================== РЕМЕСЛЕННЫЕ УМЕНИЯ ====================

