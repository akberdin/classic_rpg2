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
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import RegenerationEffect, StaminaRecoveryEffect, ShieldEffect


class Heal(Skill):
    """Лечение - восстанавливает здоровье"""

    def __init__(self):
        super().__init__(
            name="Лечение",
            description="Восстанавливает HP. Эффективность растет с рангом",
            category=SkillCategory.MAGIC,
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

        # Базовое лечение зависит от интеллекта и духа
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

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
            category=SkillCategory.MAGIC,
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать регенерацию - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Регенерация ВСЕГДА применяется к себе (user), не к target
        regen_target = user

        # Получаем характеристики заклинателя
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

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
            category=SkillCategory.MAGIC,
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать восстановление выносливости - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Восстановление выносливости ВСЕГДА применяется к себе (user), не к target
        recovery_target = user

        # Получаем характеристики заклинателя
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

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
        if not hasattr(recovery_target, 'status_effects'):
            recovery_target.status_effects = []
        recovery_target.status_effects.append(stamina_effect)

        result['stamina_per_turn'] = stamina_per_turn
        result['duration'] = recovery_duration
        result['message'] = f"{user.name} накладывает восстановление выносливости на себя! (+{stamina_per_turn} выносливости/ход на {recovery_duration} ходов)"

        return result


# ==================== АТАКУЮЩИЕ МАГИЧЕСКИЕ УМЕНИЯ ====================

class Fireball(Skill):
    """Огненный шар - мощная магическая атака огнем"""

    def __init__(self):
        super().__init__(
            name="Огненный шар",
            description="Мощная огненная атака. Игнорирует броню, но снижается магической защитой. Урон растет с рангом",
            category=SkillCategory.MAGIC,
            mana_cost=35,
            cooldown=3
        )

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Множитель урона x1.0 (20 + Интеллект*4)",
            "Ранг 2: Множитель урона x1.35",
            "Ранг 3: Множитель урона x1.7",
            "Ранг 4: Множитель урона x2.05",
            "Ранг 5: Множитель урона x2.4"
        ]

    def use(self, user, target=None):
        """Использовать огненный шар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Базовый урон зависит от интеллекта (значительно увеличено)
            intelligence = getattr(user, 'intelligence', 1)
            spirit = getattr(user, 'spirit', 1)

            # Урон: 20 + интеллект*4 + дух*0.3 (интеллект значительно важнее)
            base_damage = 20 + intelligence * 4 + spirit * 0.3
            # Улучшенный множитель от ранга (+35% за ранг)
            damage_multiplier = 1.0 + (self.rank - 1) * 0.35  # 1.0x -> 2.4x на 5 ранге
            total_damage = int(base_damage * damage_multiplier)

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)
            result['message'] = f"{user.name} запускает огненный шар в {target.name} и наносит {actual_damage} магического урона!"

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
            category=SkillCategory.MAGIC,
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
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Урон немного меньше чем у огненного шара, но меньше кулдаун и есть замедление
            intelligence = getattr(user, 'intelligence', 1)
            spirit = getattr(user, 'spirit', 1)

            # Урон: 15 + интеллект*3 + дух*0.3 (увеличено)
            base_damage = 15 + intelligence * 3 + spirit * 0.3
            damage_multiplier = 1.0 + (self.rank - 1) * 0.3  # +30% за ранг
            total_damage = int(base_damage * damage_multiplier)

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            # Улучшенный шанс и длительность замедления
            slow_chance = 0.4 + (self.rank - 1) * 0.1  # 40% -> 80% на 5 ранге
            slow_duration = 1 + (self.rank - 1) // 2  # 1-3 хода
            slowed = False
            if random.random() < slow_chance:
                slow = StunEffect(duration=slow_duration)
                slow.name = "Обморожение"
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(slow)
                slowed = True

            result['damage'] = actual_damage
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)
            result['slowed'] = slowed
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
            category=SkillCategory.MAGIC,
            mana_cost=50,
            cooldown=4
        )

    def use(self, user, target=None):
        """Использовать молнию"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Самый высокий урон среди магических атак
            intelligence = getattr(user, 'intelligence', 1)
            spirit = getattr(user, 'spirit', 1)

            # Урон: 30 + интеллект*5 + дух*0.3 (максимальный урон, интеллект критичен)
            base_damage = 30 + intelligence * 5 + spirit * 0.3
            damage_multiplier = 1.0 + (self.rank - 1) * 0.4  # +40% за ранг
            total_damage = int(base_damage * damage_multiplier)

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)
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
            category=SkillCategory.MAGIC,
            mana_cost=15,
            cooldown=1
        )

    def use(self, user, target=None):
        """Использовать магическую стрелу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Базовая магическая атака с низкой стоимостью
            intelligence = getattr(user, 'intelligence', 1)
            spirit = getattr(user, 'spirit', 1)

            # Урон: 12 + интеллект*2.5 + дух*0.2 (увеличено)
            base_damage = 12 + intelligence * 2.5 + spirit * 0.2
            damage_multiplier = 1.0 + (self.rank - 1) * 0.25  # +25% за ранг
            total_damage = int(base_damage * damage_multiplier)

            # ИГНОРИРУЕМ БРОНЮ, но учитываем магическую защиту
            magic_defense = target.get_magic_defense() if hasattr(target, 'get_magic_defense') else 0
            actual_damage = max(1, total_damage - magic_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['ignored_armor'] = True
            result['magic_blocked'] = max(0, total_damage - actual_damage)
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
            category=SkillCategory.MAGIC,
            mana_cost=25,
            cooldown=3
        )

    def use(self, user, target=None):
        """Использовать щит мага - ВСЕГДА накладывает на себя (user)"""
        result = super().use(user, target)

        # Щит мага ВСЕГДА применяется к себе (user), не к target
        shield_target = user

        # Расчет бонуса защиты: базовые 50% + интеллект/2 + ранг*10%
        intelligence = getattr(user, 'intelligence', 1)
        defense_bonus = int(50 + intelligence / 2 + (self.rank - 1) * 10)

        # Длительность: 3 хода + ранг
        duration = 3 + self.rank

        # Создаем и применяем эффект щита на себя
        shield_effect = ShieldEffect(duration=duration, defense_bonus=defense_bonus)
        if not hasattr(shield_target, 'status_effects'):
            shield_target.status_effects = []

        # Проверяем, нет ли уже щита (чтобы избежать многократного наложения)
        has_shield = any(isinstance(effect, ShieldEffect) for effect in shield_target.status_effects)
        if has_shield:
            result['message'] = f"{user.name} уже защищен магическим щитом!"
        else:
            shield_target.status_effects.append(shield_effect)
            result['shield'] = defense_bonus
            result['duration'] = duration
            result['message'] = f"{user.name} создает магический щит на себя! (+{defense_bonus}% защита на {duration} ходов)"

        return result


# ==================== РЕМЕСЛЕННЫЕ УМЕНИЯ ====================

