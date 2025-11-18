"""
Система профессиональных умений (добыча ресурсов)
"""
import random
from game.inventory import PREDEFINED_ITEMS, WeaponType, EquipmentSlot


class Profession:
    """Базовый класс для профессии"""

    def __init__(self, name, max_rank=10):
        """
        Инициализация профессии

        Args:
            name: Название профессии
            max_rank: Максимальный ранг
        """
        self.name = name
        self.rank = 1
        self.experience = 0
        self.max_rank = max_rank
        self.experience_to_next_rank = 100  # Опыт для следующего ранга

    def add_experience(self, amount):
        """
        Добавить опыт к профессии

        Args:
            amount: Количество опыта

        Returns:
            bool: True если повысился ранг
        """
        self.experience += amount
        leveled_up = False

        while self.experience >= self.experience_to_next_rank and self.rank < self.max_rank:
            self.experience -= self.experience_to_next_rank
            self.rank += 1
            leveled_up = True
            # Увеличиваем требуемый опыт для следующего ранга
            self.experience_to_next_rank = int(self.experience_to_next_rank * 1.3)

        return leveled_up

    def get_success_bonus(self):
        """
        Получить бонус к шансу успеха на основе ранга

        Returns:
            float: Бонус к шансу в процентах (0-50)
        """
        # За каждый ранг +5% к шансу успеха (максимум 50% на 10 ранге)
        return (self.rank - 1) * 5


class Mining(Profession):
    """Профессия Рудокоп"""

    def __init__(self):
        super().__init__("Рудокоп", max_rank=10)
        # Шансы добычи руды (базовые значения)
        self.ore_chances = {
            "copper_ore": 50,
            "iron_ore": 45,
            "silver_ore": 30,
            "gold_ore": 20,
            "mithril_ore": 10
        }

    def can_use(self, player, location):
        """
        Проверить, можно ли использовать умение

        Args:
            player: Игрок
            location: Локация

        Returns:
            tuple: (bool, str) - можно ли использовать и сообщение
        """
        # Проверяем, что игрок в шахте
        if not location or location.location_type != 'mine':
            return False, "Вы должны находиться в шахте!"

        # Проверяем, есть ли кирка
        weapon = player.inventory.get_equipped_item(EquipmentSlot.WEAPON)
        if not weapon or weapon.weapon_type != WeaponType.PICKAXE:
            return False, "Вам нужна экипированная кирка для добычи руды!"

        return True, ""

    def gather(self, player):
        """
        Добыть ресурсы

        Args:
            player: Игрок

        Returns:
            list: Список добытых ресурсов [(item, quantity), ...]
        """
        resources = []
        success_bonus = self.get_success_bonus()

        # Пробуем добыть каждый тип руды
        for ore_type, base_chance in self.ore_chances.items():
            # Шанс с учетом ранга
            chance = min(95, base_chance + success_bonus)

            if random.random() * 100 < chance:
                # Количество зависит от ранга (1-3 на низких рангах, до 5 на высоких)
                quantity = random.randint(1, min(5, 1 + self.rank // 2))
                resources.append((PREDEFINED_ITEMS[ore_type], quantity))

        # Даем опыт за попытку добычи
        exp_gained = 10 + len(resources) * 5
        leveled_up = self.add_experience(exp_gained)

        if leveled_up:
            print(f"Профессия {self.name} повышена до ранга {self.rank}!")

        return resources


class Lumberjacking(Profession):
    """Профессия Лесоруб"""

    def __init__(self):
        super().__init__("Лесоруб", max_rank=10)
        # Базовый шанс добычи древесины
        self.base_chance = 60

    def can_use(self, player, biome):
        """
        Проверить, можно ли использовать умение

        Args:
            player: Игрок
            biome: Биом

        Returns:
            tuple: (bool, str) - можно ли использовать и сообщение
        """
        # Проверяем, что игрок в лесу
        if biome != 'forest':
            return False, "Вы должны находиться в лесу!"

        # Проверяем, есть ли топор
        weapon = player.inventory.get_equipped_item(EquipmentSlot.WEAPON)
        if not weapon or weapon.weapon_type != WeaponType.AXE:
            return False, "Вам нужен экипированный топор для рубки деревьев!"

        return True, ""

    def gather(self, player):
        """
        Добыть древесину

        Args:
            player: Игрок

        Returns:
            list: Список добытых ресурсов [(item, quantity), ...]
        """
        resources = []
        success_bonus = self.get_success_bonus()

        # Шанс с учетом ранга
        chance = min(95, self.base_chance + success_bonus)

        if random.random() * 100 < chance:
            # Количество зависит от ранга (1-4 на низких рангах, до 8 на высоких)
            quantity = random.randint(2, min(8, 2 + self.rank))
            resources.append((PREDEFINED_ITEMS["wood"], quantity))

        # Даем опыт за попытку
        exp_gained = 10 if resources else 5
        leveled_up = self.add_experience(exp_gained)

        if leveled_up:
            print(f"Профессия {self.name} повышена до ранга {self.rank}!")

        return resources


class ProfessionManager:
    """Менеджер профессий игрока"""

    def __init__(self):
        """Инициализация менеджера профессий"""
        self.professions = {
            'mining': Mining(),
            'lumberjacking': Lumberjacking()
        }

    def get_profession(self, name):
        """
        Получить профессию по названию

        Args:
            name: Название профессии

        Returns:
            Profession: Объект профессии или None
        """
        return self.professions.get(name)

    def get_all_professions(self):
        """
        Получить все профессии

        Returns:
            dict: Словарь профессий
        """
        return self.professions
