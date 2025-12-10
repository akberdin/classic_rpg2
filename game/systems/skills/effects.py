"""
Модуль статус-эффектов.

Содержит базовый класс StatusEffect и конкретные реализации эффектов:
- PoisonEffect - отравление
- StunEffect - оглушение
- RegenerationEffect - регенерация здоровья
- StaminaRecoveryEffect - восстановление выносливости
- StrengthBoostEffect - усиление силы
- ShieldEffect - магический щит
- BurnEffect - горение (урон от огня)
"""


class StatusEffect:
    """Базовый класс для статус-эффектов"""

    def __init__(self, name, duration, description="", icon_id=None):
        """
        Инициализация статус-эффекта

        Args:
            name: Название эффекта
            duration: Длительность в ходах
            description: Описание эффекта
            icon_id: ID иконки эффекта из конфига assets (например, 'burn', 'poison')
        """
        self.name = name
        self.duration = duration
        self.remaining_duration = duration
        self.description = description
        self.icon_id = icon_id  # ID для поиска спрайта в assets_config.json

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
            description=f"Наносит {damage_per_turn} урона каждый ход",
            icon_id="poison"
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
            description="Пропуск хода",
            icon_id="stun"
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
            description=f"Восстанавливает {heal_per_turn} HP каждый ход",
            icon_id="regeneration"
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
            description=f"+{boost_amount} к силе",
            icon_id="strength_boost"
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
            description=f"+{defense_bonus}% защита",
            icon_id="shield"
        )
        self.defense_bonus = defense_bonus

    def apply(self, character):
        return f"Магический щит защищает {character.name}! (+{self.defense_bonus}% защита)"

    def tick(self, character):
        super().tick(character)
        return None

    def remove(self, character):
        return f"Магический щит исчез с {character.name}"


class SlowEffect(StatusEffect):
    """Эффект замедления"""

    def __init__(self, duration=2):
        super().__init__(
            name="Замедление",
            duration=duration,
            description="Замедлен",
            icon_id="slow"
        )

    def apply(self, character):
        return f"{character.name} замедлен!"

    def tick(self, character):
        super().tick(character)
        return None

    def remove(self, character):
        return f"Замедление спадает с {character.name}"


class ArmorBreakEffect(StatusEffect):
    """Эффект снижения защиты"""

    def __init__(self, duration=3, defense_reduction=5):
        super().__init__(
            name="Сломленная броня",
            duration=duration,
            description=f"-{defense_reduction} защиты",
            icon_id="armor_break"
        )
        self.defense_reduction = defense_reduction

    def apply(self, character):
        # Временно сохраняем снижение защиты на персонаже
        if not hasattr(character, 'temp_defense_penalty'):
            character.temp_defense_penalty = 0
        character.temp_defense_penalty += self.defense_reduction
        return f"Броня {character.name} пробита! (-{self.defense_reduction} защиты)"

    def tick(self, character):
        super().tick(character)
        return None

    def remove(self, character):
        # Убираем снижение защиты
        if hasattr(character, 'temp_defense_penalty'):
            character.temp_defense_penalty = max(0, character.temp_defense_penalty - self.defense_reduction)
        return f"Броня {character.name} восстановлена"


class BurnEffect(StatusEffect):
    """Эффект горения - наносит урон от огня каждый ход"""

    def __init__(self, duration=2, damage_per_turn=5):
        """
        Инициализация эффекта горения

        Args:
            duration: Длительность в ходах (1-3)
            damage_per_turn: Урон за ход
        """
        super().__init__(
            name="Горение",
            duration=duration,
            description=f"Наносит {damage_per_turn} урона от огня каждый ход",
            icon_id="burn"
        )
        self.damage_per_turn = damage_per_turn

    def apply(self, character):
        """Применить эффект горения"""
        return f"{character.name} охвачен пламенем! ({self.damage_per_turn} урона/ход на {self.duration} ходов)"

    def tick(self, character):
        """Нанести урон от огня"""
        super().tick(character)
        character.take_damage(self.damage_per_turn)
        return f"{character.name} получает {self.damage_per_turn} урона от огня"

    def remove(self, character):
        """Снять эффект горения"""
        return f"Пламя на {character.name} погасло"
