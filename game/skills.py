"""
Система навыков и способностей
"""
import random


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
        character.health = min(character.max_health, character.health + self.heal_per_turn)
        actual_heal = character.health - old_health
        return f"{character.name} восстанавливает {actual_heal} HP от регенерации"


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


class Skill:
    """Базовый класс для навыков"""

    def __init__(self, name, description, mana_cost=0, stamina_cost=0, cooldown=0):
        """
        Инициализация навыка

        Args:
            name: Название навыка
            description: Описание навыка
            mana_cost: Стоимость в мане
            stamina_cost: Стоимость в выносливости
            cooldown: Перезарядка в ходах
        """
        self.name = name
        self.description = description
        self.mana_cost = mana_cost
        self.stamina_cost = stamina_cost
        self.cooldown = cooldown
        self.current_cooldown = 0

    def can_use(self, user):
        """
        Проверить, можно ли использовать навык

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
        Использовать навык

        Args:
            user: Использующий персонаж
            target: Цель навыка (если есть)

        Returns:
            dict: Результат использования навыка
        """
        # Списываем ресурсы
        if hasattr(user, 'mana'):
            user.mana -= self.mana_cost
        if hasattr(user, 'stamina'):
            user.stamina -= self.stamina_cost

        # Запускаем перезарядку
        self.current_cooldown = self.cooldown

        return {
            'success': True,
            'message': f"{user.name} использует {self.name}!"
        }

    def tick_cooldown(self):
        """Уменьшить перезарядку на 1"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class PowerStrike(Skill):
    """Мощный удар - наносит увеличенный урон"""

    def __init__(self):
        super().__init__(
            name="Мощный удар",
            description="Наносит урон с коэффициентом 1.5x",
            stamina_cost=10,
            cooldown=2
        )

    def use(self, user, target=None):
        """Использовать мощный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Вычисляем урон с учетом бонуса
            base_damage = user.get_total_damage()
            bonus_damage = int(base_damage * 0.5)
            total_damage = base_damage + bonus_damage

            # Учитываем защиту цели
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
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
            description="Наносит урон и накладывает отравление на 3 хода",
            stamina_cost=15,
            cooldown=4
        )

    def use(self, user, target=None):
        """Использовать отравленный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим обычный урон
            base_damage = user.get_total_damage()
            target_defense = target.get_total_defense()
            actual_damage = max(1, base_damage - target_defense)

            target.take_damage(actual_damage)

            # Накладываем отравление
            poison = PoisonEffect(duration=3, damage_per_turn=5)
            if not hasattr(target, 'status_effects'):
                target.status_effects = []
            target.status_effects.append(poison)

            result['damage'] = actual_damage
            result['poison_applied'] = True
            result['message'] = f"{user.name} наносит отравленный удар {target.name} на {actual_damage} урона и накладывает яд!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class StunStrike(Skill):
    """Оглушающий удар - наносит урон и оглушает"""

    def __init__(self):
        super().__init__(
            name="Оглушающий удар",
            description="Наносит урон и оглушает на 1 ход (50% шанс)",
            stamina_cost=20,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать оглушающий удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим урон
            base_damage = user.get_total_damage()
            target_defense = target.get_total_defense()
            actual_damage = max(1, base_damage - target_defense)

            target.take_damage(actual_damage)

            # Шанс оглушения 50%
            stunned = False
            if random.random() < 0.5:
                stun = StunEffect(duration=1)
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(stun)
                stunned = True

            result['damage'] = actual_damage
            result['stunned'] = stunned
            result['message'] = f"{user.name} наносит оглушающий удар {target.name} на {actual_damage} урона!"

            if stunned:
                result['message'] += f" {target.name} оглушен!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class Heal(Skill):
    """Лечение - восстанавливает здоровье"""

    def __init__(self):
        super().__init__(
            name="Лечение",
            description="Восстанавливает 40% от максимального HP",
            mana_cost=20,
            cooldown=3
        )

    def use(self, user, target=None):
        """Использовать лечение"""
        result = super().use(user, target)

        # Если цель не указана, лечим себя
        if target is None:
            target = user

        # Восстанавливаем здоровье
        heal_amount = int(target.max_health * 0.4)
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
            description="Восстанавливает 10 HP каждый ход в течение 3 ходов",
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать регенерацию"""
        result = super().use(user, target)

        # Если цель не указана, накладываем на себя
        if target is None:
            target = user

        # Накладываем эффект регенерации
        regen = RegenerationEffect(duration=3, heal_per_turn=10)
        if not hasattr(target, 'status_effects'):
            target.status_effects = []
        target.status_effects.append(regen)

        result['message'] = f"{user.name} накладывает регенерацию на {target.name}!"

        return result


class BattleCry(Skill):
    """Боевой клич - усиливает силу на несколько ходов"""

    def __init__(self):
        super().__init__(
            name="Боевой клич",
            description="Увеличивает силу на 5 на 3 хода",
            stamina_cost=15,
            cooldown=6
        )

    def use(self, user, target=None):
        """Использовать боевой клич"""
        result = super().use(user, target)

        # Накладываем усиление на себя
        boost = StrengthBoostEffect(duration=3, boost_amount=5)
        if not hasattr(user, 'status_effects'):
            user.status_effects = []
        user.status_effects.append(boost)

        result['message'] = f"{user.name} издает боевой клич! Сила увеличена на 5!"

        return result


# Список всех доступных навыков
AVAILABLE_SKILLS = {
    'power_strike': PowerStrike,
    'poison_strike': PoisonStrike,
    'stun_strike': StunStrike,
    'heal': Heal,
    'regeneration': Regeneration,
    'battle_cry': BattleCry,
}


class SkillManager:
    """Менеджер навыков персонажа"""

    def __init__(self, character):
        """
        Инициализация менеджера навыков

        Args:
            character: Персонаж-владелец навыков
        """
        self.character = character
        self.learned_skills = []  # Список изученных навыков
        self.status_effects = []  # Активные статус-эффекты

    def learn_skill(self, skill_class):
        """
        Изучить новый навык

        Args:
            skill_class: Класс навыка для изучения

        Returns:
            bool: True если навык успешно изучен
        """
        skill = skill_class()

        # Проверяем, не изучен ли уже этот навык
        for learned in self.learned_skills:
            if learned.name == skill.name:
                return False

        self.learned_skills.append(skill)
        return True

    def use_skill(self, skill_name, target=None):
        """
        Использовать навык

        Args:
            skill_name: Название навыка
            target: Цель навыка

        Returns:
            dict: Результат использования
        """
        # Ищем навык
        skill = None
        for s in self.learned_skills:
            if s.name == skill_name:
                skill = s
                break

        if not skill:
            return {
                'success': False,
                'message': f"Навык {skill_name} не изучен"
            }

        # Проверяем возможность использования
        can_use, reason = skill.can_use(self.character)
        if not can_use:
            return {
                'success': False,
                'message': reason
            }

        # Используем навык
        return skill.use(self.character, target)

    def tick_cooldowns(self):
        """Уменьшить перезарядки всех навыков"""
        for skill in self.learned_skills:
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

    def get_skill_list(self):
        """
        Получить список изученных навыков с информацией о перезарядке

        Returns:
            list: Список навыков
        """
        return self.learned_skills
