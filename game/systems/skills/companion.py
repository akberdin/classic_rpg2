"""
Умения для спутников игрока.

Содержит умения для различных типов спутников:
- WolfBite - Укус волка
- WolfHowl - Вой волка
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import StrengthBoostEffect, DexterityBoostEffect


class WolfBite(Skill):
    """Укус волка - физический урон в ближнем бою"""

    def __init__(self, companion_rank=0):
        """
        Инициализация умения Укус

        Args:
            companion_rank: Ранг спутника (0-3)
        """
        super().__init__(
            name="Укус",
            description="Волк кусает врага. Урон зависит от ранга спутника",
            category=SkillCategory.GENERAL,
            stamina_cost=5,
            cooldown=0,
            tactical_range=1  # Радиус 1 клетка (8 соседних клеток)
        )
        self.companion_rank = companion_rank

    def get_tactical_range(self):
        """Получить радиус действия для тактического боя"""
        return 1  # Укус работает на расстоянии 1 клетки (ближний бой)

    def set_companion_rank(self, rank):
        """Обновить ранг спутника"""
        self.companion_rank = rank

    def get_damage_multiplier(self):
        """Получить множитель урона в зависимости от ранга спутника"""
        # Ранг 0: x1.0, Ранг 1: x1.3, Ранг 2: x1.6, Ранг 3: x2.0
        return 1.0 + self.companion_rank * 0.3

    def use(self, user, target=None):
        """Использовать укус"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Вычисляем урон с учетом ранга спутника
            base_damage = user.get_total_damage()
            rank_multiplier = self.get_damage_multiplier()
            total_damage = int(base_damage * rank_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # Учитываем защиту цели (броню)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_critical

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} вгрызается в {target.name}! Урон: {actual_damage}"
            else:
                result['message'] = f"{user.name} кусает {target.name}! Урон: {actual_damage}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class WolfHowl(Skill):
    """Вой волка - увеличивает силу и ловкость союзников"""

    def __init__(self, companion_rank=0):
        """
        Инициализация умения Вой

        Args:
            companion_rank: Ранг спутника (0-3)
        """
        super().__init__(
            name="Вой",
            description="Вой волка вдохновляет союзников, увеличивая их силу и ловкость",
            category=SkillCategory.GENERAL,
            stamina_cost=15,
            cooldown=3,
            tactical_range=20  # Действует на всех союзников на поле боя
        )
        self.companion_rank = companion_rank

    def get_tactical_range(self):
        """Получить радиус действия для тактического боя"""
        return 20  # Большой радиус - действует на всех союзников

    def set_companion_rank(self, rank):
        """Обновить ранг спутника"""
        self.companion_rank = rank

    def get_boost_percentage(self):
        """
        Получить процент усиления в зависимости от ранга спутника

        Доступно со 2 ранга (ранг 1+):
        - Ранг 1: 10%
        - Ранг 2: 20%
        - Ранг 3: 30%
        """
        if self.companion_rank < 1:
            return 0  # Недоступно на ранге 0

        return (self.companion_rank) * 10  # 10%, 20%, 30%

    def get_duration(self):
        """Получить длительность эффекта в ходах"""
        # Длительность 3 хода + 1 за каждый ранг
        return 3 + self.companion_rank

    def can_use(self, user, target=None):
        """Проверить, можно ли использовать умение"""
        # Умение доступно только со 2 ранга спутника (companion_rank >= 1)
        if self.companion_rank < 1:
            return False, "Вой доступен со 2 ранга спутника"

        return super().can_use(user)

    def use(self, user, target=None):
        """
        Использовать вой

        Args:
            user: Спутник, использующий умение
            target: Цель (игнорируется, так как баф применяется на всех союзников)
        """
        result = super().use(user, target)

        boost_percentage = self.get_boost_percentage()
        duration = self.get_duration()

        if boost_percentage > 0:
            # В тактическом бою умение применяется на всех союзников
            # Это будет обрабатываться в TacticalCombatSystem
            result['buff_type'] = 'howl'
            result['boost_percentage'] = boost_percentage
            result['duration'] = duration
            result['message'] = f"{user.name} воет! Сила и ловкость союзников увеличены на {boost_percentage}% на {duration} ход(а)!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} пытается выть, но слишком молод для этого умения!"

        return result


# Специальные эффекты для баффов волка
class WolfHowlStrengthEffect(StrengthBoostEffect):
    """Эффект усиления силы от воя волка"""

    def __init__(self, duration, boost_percentage):
        super().__init__(duration, boost_amount=0)
        self.boost_percentage = boost_percentage
        self.name = "Вой волка (Сила)"

    def apply(self, character):
        """Применить эффект усиления силы"""
        self.boost_amount = int(character.strength * (self.boost_percentage / 100))
        super().apply(character)


class WolfHowlDexterityEffect(DexterityBoostEffect):
    """Эффект усиления ловкости от воя волка"""

    def __init__(self, duration, boost_percentage):
        super().__init__(duration, boost_amount=0)
        self.boost_percentage = boost_percentage
        self.name = "Вой волка (Ловкость)"

    def apply(self, character):
        """Применить эффект усиления ловкости"""
        self.boost_amount = int(character.dexterity * (self.boost_percentage / 100))
        super().apply(character)


class WolfDevour(Skill):
    """Пожирание - волк наносит мощный укус и восстанавливает здоровье"""

    def __init__(self, companion_rank=0):
        """
        Инициализация умения Пожирание

        Args:
            companion_rank: Ранг спутника (0-3)
        """
        super().__init__(
            name="Пожирание",
            description="Волк яростно вгрызается во врага, нанося огромный урон и восстанавливая здоровье. Доступно с 3 ранга",
            category=SkillCategory.GENERAL,
            stamina_cost=15,
            cooldown=3,
            tactical_range=1  # Радиус 1 клетка (ближний бой)
        )
        self.companion_rank = companion_rank

    def get_tactical_range(self):
        """Получить радиус действия для тактического боя"""
        return 1  # Пожирание работает на расстоянии 1 клетки (ближний бой)

    def set_companion_rank(self, rank):
        """Обновить ранг спутника"""
        self.companion_rank = rank

    def get_damage_multiplier(self):
        """
        Получить множитель урона в зависимости от ранга спутника
        Доступно с 3 ранга (companion_rank >= 2):
        - Ранг 2 (3-й ранг): x1.8
        - Ранг 3 (4-й ранг): x2.2
        """
        if self.companion_rank < 2:
            return 0  # Недоступно до 3 ранга

        # Базовый множитель 1.8 для ранга 2, +0.4 за каждый следующий ранг
        return 1.8 + (self.companion_rank - 2) * 0.4

    def get_heal_percentage(self):
        """
        Получить процент восстановления здоровья от нанесенного урона
        - Ранг 2: 30%
        - Ранг 3: 40%
        """
        if self.companion_rank < 2:
            return 0

        # 30% для ранга 2, +10% за каждый следующий ранг
        return 30 + (self.companion_rank - 2) * 10

    def can_use(self, user, target=None):
        """Проверить, можно ли использовать умение"""
        # Умение доступно только с 3 ранга спутника (companion_rank >= 2)
        if self.companion_rank < 2:
            return False, "Пожирание доступно с 3 ранга спутника (Волк)"

        return super().can_use(user)

    def use(self, user, target=None):
        """Использовать пожирание"""
        result = super().use(user, target)

        if target:
            # Проверка критического удара
            crit_chance = user.calculate_crit_chance()
            crit_roll = random.uniform(0, 100)
            is_critical = crit_roll < crit_chance

            # Вычисляем урон с учетом ранга спутника (весомый урон)
            base_damage = user.get_total_damage()
            rank_multiplier = self.get_damage_multiplier()
            total_damage = int(base_damage * rank_multiplier)

            # Удваиваем урон при крите
            if is_critical:
                total_damage *= 2

            # Учитываем защиту цели (броню)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            # === ВОССТАНОВЛЕНИЕ ЗДОРОВЬЯ ===
            heal_percentage = self.get_heal_percentage()
            heal_amount = int(actual_damage * (heal_percentage / 100))

            # Восстанавливаем здоровье волку
            user_max_health = user.get_effective_max_health() if hasattr(user, 'get_effective_max_health') else user.max_health
            old_health = user.health
            user.health = min(user_max_health, user.health + heal_amount)
            actual_heal = user.health - old_health

            result['damage'] = actual_damage
            result['critical'] = is_critical
            result['heal'] = actual_heal

            if is_critical:
                result['message'] = f"КРИТИЧЕСКИЙ УДАР! {user.name} яростно пожирает {target.name}! Урон: {actual_damage}, восстановлено {actual_heal} HP"
            else:
                result['message'] = f"{user.name} пожирает {target.name}! Урон: {actual_damage}, восстановлено {actual_heal} HP"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result
