"""
Система умений и способностей с категориями, рангами и прогрессом
"""
import random
from enum import Enum


class SkillCategory(Enum):
    """Категории умений"""
    COMBAT = "combat"  # Боевые умения
    CRAFTING = "crafting"  # Ремесленные умения
    MAGIC = "magic"  # Магические умения


class StatusEffect:
    """Базовый класс для статус-эффектов"""

    def __init__(self, name, duration, description=""):
        """
        Инициализация статус-эффекта

        Args:
            name: Название эффекта
            duration: Длительность в ходах
            description: Описание эффекта
        """
        self.name = name
        self.duration = duration
        self.remaining_duration = duration
        self.description = description

    def apply(self, character):
        """
        Применить эффект к персонажу

        Args:
            character: Персонаж

        Returns:
            str: Сообщение о применении эффекта
        """
        return f"{character.name} получает эффект: {self.name}"

    def tick(self, character):
        """
        Обновить эффект (вызывается каждый ход)

        Args:
            character: Персонаж

        Returns:
            str: Сообщение о действии эффекта
        """
        self.remaining_duration -= 1
        return ""

    def is_expired(self):
        """
        Проверить, истек ли эффект

        Returns:
            bool: True если эффект истек
        """
        return self.remaining_duration <= 0

    def remove(self, character):
        """
        Удалить эффект с персонажа

        Args:
            character: Персонаж

        Returns:
            str: Сообщение об удалении эффекта
        """
        return f"{self.name} снят с {character.name}"


class PoisonEffect(StatusEffect):
    """Эффект отравления - наносит урон каждый ход"""

    def __init__(self, duration=3, damage_per_turn=5):
        """
        Инициализация отравления

        Args:
            duration: Длительность в ходах
            damage_per_turn: Урон за ход
        """
        super().__init__(
            name="Отравление",
            duration=duration,
            description=f"Наносит {damage_per_turn} урона каждый ход"
        )
        self.damage_per_turn = damage_per_turn

    def tick(self, character):
        """Нанести урон от яда"""
        super().tick(character)
        character.take_damage(self.damage_per_turn)
        return f"{character.name} получает {self.damage_per_turn} урона от яда"


class StunEffect(StatusEffect):
    """Эффект оглушения - пропуск хода"""

    def __init__(self, duration=1):
        """
        Инициализация оглушения

        Args:
            duration: Длительность в ходах
        """
        super().__init__(
            name="Оглушение",
            duration=duration,
            description="Пропуск хода"
        )

    def apply(self, character):
        """Применить оглушение"""
        character.stunned = True
        return f"{character.name} оглушен!"

    def remove(self, character):
        """Снять оглушение"""
        character.stunned = False
        return f"{character.name} пришел в себя"


class RegenerationEffect(StatusEffect):
    """Эффект регенерации - восстановление HP каждый ход"""

    def __init__(self, duration=3, heal_per_turn=10):
        """
        Инициализация регенерации

        Args:
            duration: Длительность в ходах
            heal_per_turn: Лечение за ход
        """
        super().__init__(
            name="Регенерация",
            duration=duration,
            description=f"Восстанавливает {heal_per_turn} HP каждый ход"
        )
        self.heal_per_turn = heal_per_turn

    def tick(self, character):
        """Восстановить здоровье"""
        super().tick(character)
        old_health = character.health
        effective_max_health = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        character.health = min(effective_max_health, character.health + self.heal_per_turn)
        actual_heal = character.health - old_health
        return f"{character.name} восстанавливает {actual_heal} HP от регенерации"


class StaminaRecoveryEffect(StatusEffect):
    """Эффект восстановления выносливости - восстановление выносливости каждый ход"""

    def __init__(self, duration=3, stamina_per_turn=10):
        """
        Инициализация восстановления выносливости

        Args:
            duration: Длительность в ходах
            stamina_per_turn: Восстановление выносливости за ход
        """
        super().__init__(
            name="Восстановление выносливости",
            duration=duration,
            description=f"Восстанавливает {stamina_per_turn} выносливости каждый ход"
        )
        self.stamina_per_turn = stamina_per_turn

    def tick(self, character):
        """Восстановить выносливость"""
        super().tick(character)
        if hasattr(character, 'stamina'):
            old_stamina = character.stamina
            effective_max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina
            character.stamina = min(effective_max_stamina, character.stamina + self.stamina_per_turn)
            actual_recovery = character.stamina - old_stamina
            return f"{character.name} восстанавливает {actual_recovery} выносливости"
        return ""


class StrengthBoostEffect(StatusEffect):
    """Эффект усиления силы"""

    def __init__(self, duration=3, boost_amount=5):
        """
        Инициализация усиления

        Args:
            duration: Длительность в ходах
            boost_amount: Бонус к силе
        """
        super().__init__(
            name="Усиление",
            duration=duration,
            description=f"+{boost_amount} к силе"
        )
        self.boost_amount = boost_amount

    def apply(self, character):
        """Применить усиление"""
        character.temp_strength_boost = self.boost_amount
        return f"{character.name} получает +{self.boost_amount} к силе!"

    def remove(self, character):
        """Снять усиление"""
        character.temp_strength_boost = 0
        return f"Усиление спадает с {character.name}"


class ShieldEffect(StatusEffect):
    """Эффект магического щита"""

    def __init__(self, duration=3, defense_bonus=0):
        super().__init__(
            name="Магический щит",
            duration=duration,
            description=f"+{defense_bonus}% защита"
        )
        self.defense_bonus = defense_bonus

    def apply(self, character):
        return f"Магический щит защищает {character.name}! (+{self.defense_bonus}% защита)"

    def tick(self, character):
        super().tick(character)
        return None

    def remove(self, character):
        return f"Магический щит исчез с {character.name}"


class Skill:
    """Базовый класс для умений с системой рангов и прогресса"""

    def __init__(self, name, description, category, mana_cost=0, stamina_cost=0, cooldown=0, max_rank=5):
        """
        Инициализация умения

        Args:
            name: Название умения
            description: Описание умения
            category: Категория умения (SkillCategory)
            mana_cost: Стоимость в мане
            stamina_cost: Стоимость в выносливости
            cooldown: Перезарядка в ходах
            max_rank: Максимальный ранг умения
        """
        self.name = name
        self.base_description = description
        self.category = category
        self.mana_cost = mana_cost
        self.stamina_cost = stamina_cost
        self.cooldown = cooldown
        self.current_cooldown = 0

        # Система рангов и прогресса
        self.rank = 1
        self.max_rank = max_rank
        self.experience = 0
        self.experience_to_next_rank = 100  # Базовое значение для ранга 2
        self.use_count = 0  # Счётчик использований

    @property
    def description(self):
        """Получить описание с учетом текущего ранга"""
        return f"{self.base_description} [Ранг {self.rank}/{self.max_rank}]"

    def get_required_uses_for_rank(self):
        """Получить требуемое количество использований для следующего ранга"""
        return 20 * self.rank  # 20, 40, 60, 80 для рангов 2, 3, 4, 5

    def get_required_player_level_for_rank(self):
        """Получить минимальный уровень игрока для следующего ранга"""
        return 5 * self.rank  # 5, 10, 15, 20 для рангов 2, 3, 4, 5

    def get_gold_cost_for_rank(self):
        """Получить стоимость в золоте для повышения ранга"""
        return 50 * self.rank * self.rank  # 50, 200, 450, 800 для рангов 2, 3, 4, 5

    def can_rank_up(self, player):
        """
        Проверить, можно ли повысить ранг умения

        Args:
            player: Игрок

        Returns:
            tuple: (bool, str) - можно ли повысить и причина если нет
        """
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        # Проверка опыта
        if self.experience < self.experience_to_next_rank:
            return False, f"Недостаточно опыта умения ({self.experience}/{self.experience_to_next_rank})"

        # Проверка использований
        required_uses = self.get_required_uses_for_rank()
        if self.use_count < required_uses:
            return False, f"Недостаточно использований ({self.use_count}/{required_uses})"

        # Проверка уровня игрока
        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Недостаточный уровень персонажа ({player.level}/{required_level})"

        # Проверка золота
        gold_cost = self.get_gold_cost_for_rank()
        if player.inventory.gold < gold_cost:
            return False, f"Недостаточно золота ({player.inventory.gold}/{gold_cost})"

        return True, ""

    def get_rank_up_requirements(self):
        """Получить строку с требованиями для повышения ранга"""
        if self.rank >= self.max_rank:
            return "Максимальный ранг достигнут"

        return (f"Требования для ранга {self.rank + 1}:\n"
                f"  Опыт: {self.experience}/{self.experience_to_next_rank}\n"
                f"  Использований: {self.use_count}/{self.get_required_uses_for_rank()}\n"
                f"  Уровень персонажа: {self.get_required_player_level_for_rank()}\n"
                f"  Золото: {self.get_gold_cost_for_rank()}")

    def add_experience(self, amount):
        """
        Добавить опыт умению

        Args:
            amount: Количество опыта

        Returns:
            bool: True если достигнуто достаточно опыта (но ранг не повышается автоматически)
        """
        if self.rank >= self.max_rank:
            return False

        self.experience += amount

        # Теперь повышение ранга НЕ происходит автоматически
        # Нужно явно вызвать try_rank_up с проверкой всех условий
        return self.experience >= self.experience_to_next_rank

    def try_rank_up(self, player):
        """
        Попытаться повысить ранг умения с проверкой всех условий

        Args:
            player: Игрок

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        can_up, reason = self.can_rank_up(player)
        if not can_up:
            return False, reason

        # Списываем золото
        gold_cost = self.get_gold_cost_for_rank()
        player.inventory.gold -= gold_cost

        # Повышаем ранг
        self.experience -= self.experience_to_next_rank
        self.rank += 1
        self.use_count = 0  # Сбрасываем счётчик использований

        # Увеличиваем требуемый опыт для следующего ранга
        self.experience_to_next_rank = int(self.experience_to_next_rank * 1.5)

        return True, f"Умение '{self.name}' повышено до ранга {self.rank}! Потрачено {gold_cost} золота."

    def rank_up(self):
        """Устаревший метод - используйте try_rank_up с проверкой условий"""
        if self.rank >= self.max_rank:
            return

        self.experience -= self.experience_to_next_rank
        self.rank += 1
        # Увеличиваем требуемый опыт для следующего ранга
        self.experience_to_next_rank = int(self.experience_to_next_rank * 1.5)

        print(f"Умение '{self.name}' повышено до ранга {self.rank}!")

    def can_use(self, user):
        """
        Проверить, можно ли использовать умение

        Args:
            user: Использующий персонаж

        Returns:
            tuple: (bool, str) - можно ли использовать и причина если нет
        """
        if self.current_cooldown > 0:
            return False, f"{self.name} перезаряжается ({self.current_cooldown} ходов)"

        if hasattr(user, 'mana') and user.mana < self.mana_cost:
            return False, f"Недостаточно маны для {self.name}"

        if hasattr(user, 'stamina') and user.stamina < self.stamina_cost:
            return False, f"Недостаточно выносливости для {self.name}"

        return True, ""

    def use(self, user, target=None):
        """
        Использовать умение

        Args:
            user: Использующий персонаж
            target: Цель умения (если есть)

        Returns:
            dict: Результат использования умения
        """
        # Списываем ресурсы
        if hasattr(user, 'mana'):
            user.mana -= self.mana_cost
        if hasattr(user, 'stamina'):
            user.stamina -= self.stamina_cost

        # Запускаем перезарядку
        self.current_cooldown = self.cooldown

        # Добавляем опыт за использование
        self.add_experience(10)

        # Увеличиваем счётчик использований для системы рангов
        self.use_count += 1

        return {
            'success': True,
            'message': f"{user.name} использует {self.name}!"
        }

    def tick_cooldown(self):
        """Уменьшить перезарядку на 1"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


# ==================== БОЕВЫЕ УМЕНИЯ ====================

class BasicAttack(Skill):
    """Базовая атака - доступна с самого начала"""

    def __init__(self):
        super().__init__(
            name="Базовая атака",
            description="Простой удар оружием. Урон увеличивается с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=5,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать базовую атаку"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Вычисляем урон с учетом ранга (20% за ранг - улучшено)
            base_damage = user.get_total_damage()
            rank_multiplier = 1.0 + (self.rank - 1) * 0.2  # 1.0x -> 1.8x на 5 ранге
            total_damage = int(base_damage * rank_multiplier)

            # Учитываем защиту цели
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
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
            category=SkillCategory.COMBAT,
            stamina_cost=10,
            cooldown=2
        )

    def use(self, user, target=None):
        """Использовать мощный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Коэффициент урона растет с рангом (1.8x + 0.35x за ранг - улучшено)
            damage_multiplier = 1.8 + (self.rank - 1) * 0.35  # 1.8x -> 3.2x на 5 ранге

            base_damage = user.get_total_damage()
            total_damage = int(base_damage * damage_multiplier)

            # Бонус пробития брони на высоких рангах (игнорируем часть защиты)
            armor_penetration = (self.rank - 1) * 0.1  # 0% -> 40% на 5 ранге

            # Учитываем защиту цели с пробитием
            target_defense = target.get_total_defense()
            effective_defense = int(target_defense * (1 - armor_penetration))
            actual_damage = max(1, total_damage - effective_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['armor_penetration'] = int(armor_penetration * 100)
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
            category=SkillCategory.COMBAT,
            stamina_cost=15,
            cooldown=4
        )

    def use(self, user, target=None):
        """Использовать отравленный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим урон с множителем от ранга (улучшено)
            base_damage = user.get_total_damage()
            damage_multiplier = 1.0 + (self.rank - 1) * 0.15  # 1.0x -> 1.6x на 5 ранге
            total_damage = int(base_damage * damage_multiplier)

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
            if not hasattr(target, 'status_effects'):
                target.status_effects = []
            target.status_effects.append(poison)

            result['damage'] = actual_damage
            result['poison_applied'] = True
            result['poison_damage'] = poison_damage
            result['poison_duration'] = poison_duration
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
            category=SkillCategory.COMBAT,
            stamina_cost=20,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать оглушающий удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим урон с множителем (1.5x + 0.2x за ранг - улучшено)
            damage_multiplier = 1.5 + (self.rank - 1) * 0.2  # 1.5x -> 2.3x на 5 ранге
            base_damage = user.get_total_damage()
            total_damage = int(base_damage * damage_multiplier)

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
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(stun)
                stunned = True

            result['damage'] = actual_damage
            result['stunned'] = stunned
            result['stun_chance'] = int(stun_chance * 100)
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
            category=SkillCategory.COMBAT,
            stamina_cost=15,
            cooldown=6
        )

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
        if not hasattr(user, 'status_effects'):
            user.status_effects = []
        user.status_effects.append(boost)

        result['strength_boost'] = boost_amount
        result['duration'] = boost_duration
        result['message'] = f"{user.name} издает боевой клич! Сила +{boost_amount} на {boost_duration} ходов!"

        return result


# ==================== МАГИЧЕСКИЕ УМЕНИЯ ====================

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

    def use(self, user, target=None):
        """Использовать лечение"""
        result = super().use(user, target)

        # Если цель не указана, лечим себя
        if target is None:
            target = user

        # Базовое лечение зависит от интеллекта и духа
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

        # Лечение: процент от макс. здоровья + бонус от интеллекта и духа
        # Улучшено: 35% + 12% за ранг, плюс бонус от статов
        heal_percent = 0.35 + (self.rank - 1) * 0.12  # 35% -> 83% на 5 ранге
        base_heal = int(target.max_health * heal_percent)
        stat_bonus = int(intelligence * 2 + spirit * 1.5) * self.rank  # Бонус от статов
        heal_amount = base_heal + stat_bonus

        old_health = target.health
        target.health = min(target.max_health, target.health + heal_amount)
        actual_heal = target.health - old_health

        result['heal'] = actual_heal
        result['message'] = f"{user.name} восстанавливает {actual_heal} HP для {target.name}!"

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
        """Использовать регенерацию"""
        result = super().use(user, target)

        # Если цель не указана, накладываем на себя
        if target is None:
            target = user

        # Получаем характеристики заклинателя
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

        # Значительно улучшенная регенерация с рангом
        base_heal = 15 + self.rank * 6  # 21 -> 45 на 5 ранге
        # Процент от макс. здоровья
        max_health = getattr(target, 'max_health', 100)
        percent_heal = int(max_health * (0.04 + self.rank * 0.02))  # 6% -> 14% за ход
        # Бонус от статов
        stat_bonus = int((intelligence + spirit) * 0.5 * self.rank)
        heal_per_turn = base_heal + percent_heal + stat_bonus

        regen_duration = 4 + self.rank  # 5-9 ходов

        # Накладываем эффект регенерации
        regen = RegenerationEffect(duration=regen_duration, heal_per_turn=heal_per_turn)
        if not hasattr(target, 'status_effects'):
            target.status_effects = []
        target.status_effects.append(regen)

        result['heal_per_turn'] = heal_per_turn
        result['duration'] = regen_duration
        result['message'] = f"{user.name} накладывает регенерацию на {target.name}! (+{heal_per_turn} HP/ход на {regen_duration} ходов)"

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
        """Использовать восстановление выносливости"""
        result = super().use(user, target)

        # Если цель не указана, накладываем на себя
        if target is None:
            target = user

        # Получаем характеристики заклинателя
        intelligence = getattr(user, 'intelligence', 1)
        spirit = getattr(user, 'spirit', 1)

        # Восстановление выносливости с рангом
        base_recovery = 15 + self.rank * 5  # 20 -> 40 на 5 ранге
        # Процент от макс. выносливости
        max_stamina = getattr(target, 'max_stamina', 100)
        percent_recovery = int(max_stamina * (0.05 + self.rank * 0.02))  # 7% -> 15% за ход
        # Бонус от статов
        stat_bonus = int((intelligence + spirit) * 0.4 * self.rank)
        stamina_per_turn = base_recovery + percent_recovery + stat_bonus

        recovery_duration = 4 + self.rank  # 5-9 ходов

        # Накладываем эффект восстановления выносливости
        stamina_effect = StaminaRecoveryEffect(duration=recovery_duration, stamina_per_turn=stamina_per_turn)
        if not hasattr(target, 'status_effects'):
            target.status_effects = []
        target.status_effects.append(stamina_effect)

        result['stamina_per_turn'] = stamina_per_turn
        result['duration'] = recovery_duration
        result['message'] = f"{user.name} накладывает восстановление выносливости на {target.name}! (+{stamina_per_turn} выносливости/ход на {recovery_duration} ходов)"

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
        """Использовать щит мага"""
        result = super().use(user, target)

        if target is None:
            target = user

        # Расчет бонуса защиты: базовые 50% + интеллект/2 + ранг*10%
        intelligence = getattr(user, 'intelligence', 1)
        defense_bonus = int(50 + intelligence / 2 + (self.rank - 1) * 10)

        # Длительность: 3 хода + ранг
        duration = 3 + self.rank

        # Создаем и применяем эффект щита
        shield_effect = ShieldEffect(duration=duration, defense_bonus=defense_bonus)
        if not hasattr(target, 'status_effects'):
            target.status_effects = []

        # Проверяем, нет ли уже щита (чтобы избежать многократного наложения)
        has_shield = any(isinstance(effect, ShieldEffect) for effect in target.status_effects)
        if has_shield:
            result['message'] = f"{target.name} уже защищен магическим щитом!"
        else:
            target.status_effects.append(shield_effect)
            result['shield'] = defense_bonus
            result['duration'] = duration
            result['message'] = f"{user.name} создает магический щит на {target.name}! (+{defense_bonus}% защита на {duration} ходов)"

        return result


# ==================== РЕМЕСЛЕННЫЕ УМЕНИЯ ====================

class Mining(Skill):
    """Рудокоп - добыча руды"""

    def __init__(self):
        super().__init__(
            name="Рудокоп",
            description="Позволяет добывать руду в шахтах. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение рудокопа"""
        # Получаем профессию рудокопа
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        mining_profession = user.profession_manager.get_profession('mining')
        if not mining_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Рудокоп не найдена"
            return result

        # Проверяем, можно ли использовать профессию
        # Получаем текущую локацию
        location = None
        if hasattr(user, 'x') and hasattr(user, 'y'):
            # Пытаемся получить локацию из текущей позиции игрока
            # Это требует доступа к карте, который мы получим из контекста
            pass

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = mining_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Добыто: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} добыл ресурсы!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

        return result


class Lumberjacking(Skill):
    """Лесоруб - рубка деревьев"""

    def __init__(self):
        super().__init__(
            name="Лесоруб",
            description="Позволяет рубить деревья. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение лесоруба"""
        # Получаем профессию лесоруба
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        lumberjacking_profession = user.profession_manager.get_profession('lumberjacking')
        if not lumberjacking_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Лесоруб не найдена"
            return result

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = lumberjacking_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Срублено: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} срубил деревья!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

        return result


# Список всех доступных умений
AVAILABLE_SKILLS = {
    # Боевые
    'basic_attack': BasicAttack,
    'power_strike': PowerStrike,
    'poison_strike': PoisonStrike,
    'stun_strike': StunStrike,
    'battle_cry': BattleCry,
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
}


class SkillManager:
    """Менеджер умений персонажа"""

    def __init__(self, character):
        """
        Инициализация менеджера умений

        Args:
            character: Персонаж-владелец умений
        """
        self.character = character
        self.learned_skills = {}  # Словарь {skill_id: skill_instance}
        self.status_effects = []  # Активные статус-эффекты
        self.skill_slots = [None] * 8  # 8 слотов для быстрого доступа к умениям

    def learn_skill(self, skill_class_or_id):
        """
        Изучить новый навык

        Args:
            skill_class_or_id: Класс навыка или его ID

        Returns:
            bool: True если навык успешно изучен
        """
        # Если передан строковый ID, получаем класс
        if isinstance(skill_class_or_id, str):
            skill_id = skill_class_or_id
            if skill_id not in AVAILABLE_SKILLS:
                return False
            skill_class = AVAILABLE_SKILLS[skill_id]
        else:
            skill_class = skill_class_or_id
            # Ищем ID по классу
            skill_id = None
            for sid, sclass in AVAILABLE_SKILLS.items():
                if sclass == skill_class:
                    skill_id = sid
                    break
            if not skill_id:
                return False

        # Проверяем, не изучен ли уже этот навык
        if skill_id in self.learned_skills:
            return False

        skill = skill_class()
        self.learned_skills[skill_id] = skill

        print(f"Изучено умение: {skill.name} ({skill.category.value})")
        return True

    def assign_to_slot(self, skill_id, slot_index):
        """
        Назначить умение в слот быстрого доступа

        Args:
            skill_id: ID умения
            slot_index: Индекс слота (0-7)

        Returns:
            bool: True если успешно назначено
        """
        if slot_index < 0 or slot_index >= 8:
            return False

        if skill_id not in self.learned_skills:
            return False

        self.skill_slots[slot_index] = skill_id
        return True

    def unassign_from_slot(self, slot_index):
        """
        Убрать умение из слота

        Args:
            slot_index: Индекс слота (0-7)
        """
        if 0 <= slot_index < 8:
            self.skill_slots[slot_index] = None

    def get_slot_skill(self, slot_index):
        """
        Получить умение из слота

        Args:
            slot_index: Индекс слота (0-7)

        Returns:
            Skill or None: Умение в слоте или None
        """
        if slot_index < 0 or slot_index >= 8:
            return None

        skill_id = self.skill_slots[slot_index]
        if not skill_id:
            return None

        return self.learned_skills.get(skill_id)

    def use_skill_from_slot(self, slot_index, target=None):
        """
        Использовать умение из слота

        Args:
            slot_index: Индекс слота (0-7)
            target: Цель умения

        Returns:
            dict: Результат использования
        """
        skill = self.get_slot_skill(slot_index)
        if not skill:
            return {
                'success': False,
                'message': f"Слот {slot_index + 1} пуст"
            }

        return self.use_skill(skill, target)

    def use_skill(self, skill_or_name, target=None):
        """
        Использовать умение

        Args:
            skill_or_name: Объект умения или его название/ID
            target: Цель умения

        Returns:
            dict: Результат использования
        """
        # Ищем умение
        skill = None
        if isinstance(skill_or_name, str):
            # Ищем по ID
            if skill_or_name in self.learned_skills:
                skill = self.learned_skills[skill_or_name]
            else:
                # Ищем по имени
                for s in self.learned_skills.values():
                    if s.name == skill_or_name:
                        skill = s
                        break
        else:
            skill = skill_or_name

        if not skill:
            return {
                'success': False,
                'message': f"Умение не найдено"
            }

        # Проверяем возможность использования
        can_use, reason = skill.can_use(self.character)
        if not can_use:
            return {
                'success': False,
                'message': reason
            }

        # Используем умение
        return skill.use(self.character, target)

    def tick_cooldowns(self):
        """Уменьшить перезарядки всех умений"""
        for skill in self.learned_skills.values():
            skill.tick_cooldown()

    def tick_status_effects(self):
        """
        Обновить все статус-эффекты

        Returns:
            list: Список сообщений от эффектов
        """
        messages = []

        # Обновляем эффекты
        for effect in self.status_effects[:]:  # Копия списка для безопасного удаления
            message = effect.tick(self.character)
            if message:
                messages.append(message)

            # Удаляем истекшие эффекты
            if effect.is_expired():
                remove_message = effect.remove(self.character)
                if remove_message:
                    messages.append(remove_message)
                self.status_effects.remove(effect)

        return messages

    def add_status_effect(self, effect):
        """
        Добавить статус-эффект

        Args:
            effect: Эффект для добавления
        """
        # Применяем эффект
        message = effect.apply(self.character)
        self.status_effects.append(effect)
        return message

    def has_effect(self, effect_name):
        """
        Проверить наличие эффекта

        Args:
            effect_name: Название эффекта

        Returns:
            bool: True если эффект активен
        """
        for effect in self.status_effects:
            if effect.name == effect_name:
                return True
        return False

    def get_skills_by_category(self, category):
        """
        Получить все изученные умения определенной категории

        Args:
            category: Категория умений (SkillCategory)

        Returns:
            list: Список умений
        """
        return [skill for skill in self.learned_skills.values() if skill.category == category]

    def get_all_skills(self):
        """
        Получить все изученные умения

        Returns:
            dict: Словарь {skill_id: skill}
        """
        return self.learned_skills

    def try_rank_up_skill(self, skill_id, player):
        """
        Попытаться повысить ранг умения

        Args:
            skill_id: ID умения
            player: Игрок

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        if skill_id not in self.learned_skills:
            return False, "Умение не найдено"

        skill = self.learned_skills[skill_id]
        return skill.try_rank_up(player)
