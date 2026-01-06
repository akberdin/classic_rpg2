"""
Система профессиональных умений (добыча ресурсов)
"""
import random
from game.inventory import WeaponType, EquipmentSlot
from game.constants import BIOME_FOREST, BIOME_PLAINS, LOCATION_MINE
from game.item_registry import get_item


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
    """
    Профессия Рудокоп

    ВАЖНО: Устаревшая механика добычи руды по шансам удалена.
    Теперь добыча руды происходит через взаимодействие с объектами руды в шахтах.
    Используйте умение "Рудокоп" для добычи руды из выбранных объектов.

    Профессия теперь используется только для отслеживания прогресса
    и предоставления бонусов к добыче.
    """

    def __init__(self):
        super().__init__("Рудокоп", max_rank=10)

    def can_use(self, player, location):
        """
        Проверить, можно ли использовать умение добычи

        Args:
            player: Игрок
            location: Локация (для проверки на мировой карте)

        Returns:
            tuple: (bool, str) - можно ли использовать и сообщение
        """
        # Проверяем, что игрок в шахте
        if not location or location.location_type != LOCATION_MINE:
            return False, "Вы должны находиться в шахте!"

        # Проверяем, есть ли кирка
        weapon = player.inventory.get_equipped_item(EquipmentSlot.WEAPON)
        if not weapon or weapon.weapon_type != WeaponType.PICKAXE:
            return False, "Вам нужна экипированная кирка для добычи руды!"

        return True, ""

    def get_quantity_bonus(self):
        """
        Получить бонус к количеству добытой руды

        Returns:
            int: Бонус к количеству руды (0-5 на основе ранга профессии)
        """
        # За каждые 2 ранга профессии +1 к максимальному количеству руды
        return self.rank // 2


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
        if biome != BIOME_FOREST:
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

        # Добавляем 1 опыт персонажу за каждое использование навыка
        if hasattr(player, 'add_experience'):
            player.add_experience(1)

        # Шанс с учетом ранга
        chance = min(95, self.base_chance + success_bonus)

        if random.random() * 100 < chance:
            # Количество зависит от ранга (1-4 на низких рангах, до 8 на высоких)
            quantity = random.randint(2, min(8, 2 + self.rank))
            resources.append((get_item("wood"), quantity))

            # Даем опыт только при успешной добыче (улучшенная формула)
            exp_gained = 15 + quantity * 3 + self.rank * 2
            leveled_up = self.add_experience(exp_gained)

            if leveled_up:
                print(f"Профессия {self.name} повышена до ранга {self.rank}!")

        # Случайные события при рубке (10% шанс)
        event_roll = random.randint(1, 100)
        if event_roll <= 10:
            events = [
                ("Полено отскочило и ударило вас по ноге!", -12, None),
                ("Вы нашли дупло с монетами внутри дерева!", 0, 40),
                ("Дерево упало не в ту сторону! Вы получили травмы.", -18, None),
                ("Вы нашли особо качественное дерево!", 0, "extra_wood"),
            ]
            event = random.choice(events)
            print(event[0])

            # Применяем эффект события
            if event[1] < 0:  # Урон
                player.take_damage(abs(event[1]))
            elif event[2] == "extra_wood":  # Дополнительная древесина
                resources.append((get_item("wood"), random.randint(3, 6)))
            elif event[2] is not None:  # Золото
                player.inventory.add_gold(event[2])

        return resources


class HerbalismProfession(Profession):
    """Профессия Травник"""

    def __init__(self):
        super().__init__("Травник", max_rank=10)
        # Шансы сбора трав (базовые значения)
        self.herb_chances = {
            "chamomile": 55,
            "mint": 50,
            "sage": 35,
            "ginseng": 25,
            "mandrake": 12
        }

    def can_use(self, player, biome):
        """
        Проверить, можно ли использовать умение

        Args:
            player: Игрок
            biome: Биом

        Returns:
            tuple: (bool, str) - можно ли использовать и сообщение
        """
        # Проверяем, что игрок на равнине или в лесу
        if biome not in [BIOME_PLAINS, BIOME_FOREST]:
            return False, "Травы можно собирать только на равнинах или в лесу!"

        return True, ""

    def gather(self, player):
        """
        Собрать травы

        Args:
            player: Игрок

        Returns:
            list: Список собранных ресурсов [(item, quantity), ...]
        """
        resources = []
        success_bonus = self.get_success_bonus()

        # Добавляем 1 опыт персонажу за каждое использование навыка
        if hasattr(player, 'add_experience'):
            player.add_experience(1)

        # Определяем доступные типы трав на основе ранга
        available_herbs = {}
        if self.rank >= 1:
            available_herbs["chamomile"] = self.herb_chances["chamomile"]
        if self.rank >= 2:
            available_herbs["mint"] = self.herb_chances["mint"]
        if self.rank >= 3:
            available_herbs["sage"] = self.herb_chances["sage"]
        if self.rank >= 4:
            available_herbs["ginseng"] = self.herb_chances["ginseng"]
        if self.rank >= 5:
            available_herbs["mandrake"] = self.herb_chances["mandrake"]

        # Пробуем собрать каждый доступный тип травы
        for herb_type, base_chance in available_herbs.items():
            # Шанс с учетом ранга
            chance = min(95, base_chance + success_bonus)

            if random.random() * 100 < chance:
                # Количество зависит от ранга (1-2 на низких рангах, до 4 на высоких)
                quantity = random.randint(1, min(4, 1 + self.rank // 3))
                resources.append((get_item(herb_type), quantity))

        # Случайные события при сборе трав (10% шанс)
        event_roll = random.randint(1, 100)
        if event_roll <= 10:
            events = [
                ("Вы наткнулись на ядовитый плющ и получили раздражение!", -8, None),
                ("Вы нашли скрытый тайник травника с монетами!", 0, 35),
                ("Вас ужалила пчела! Больно!", -10, None),
                ("Удача! Вы нашли редкий пучок трав!", 0, "extra_herbs"),
            ]
            event = random.choice(events)
            print(event[0])

            # Применяем эффект события
            if event[1] < 0:  # Урон
                player.take_damage(abs(event[1]))
            elif event[2] == "extra_herbs":  # Дополнительные травы
                bonus_herb = random.choice(list(self.herb_chances.keys()))
                resources.append((get_item(bonus_herb), random.randint(1, 2)))
            elif event[2] is not None:  # Золото
                player.inventory.add_gold(event[2])

        # Даем опыт только при успешном сборе (улучшенная формула)
        if resources:
            # Базовый опыт + бонус за количество + бонус за ранг
            exp_gained = 12 + len(resources) * 8 + self.rank * 2
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
            'lumberjacking': Lumberjacking(),
            'herbalism': HerbalismProfession()
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
