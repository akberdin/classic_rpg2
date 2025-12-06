"""
Система профессиональных умений (добыча ресурсов)
"""
import random
from game.inventory import PREDEFINED_ITEMS, WeaponType, EquipmentSlot
from game.constants import BIOME_FOREST, BIOME_PLAINS, LOCATION_MINE


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
        if not location or location.location_type != LOCATION_MINE:
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

        # Добавляем 1 опыт персонажу за каждое использование навыка
        if hasattr(player, 'add_experience'):
            player.add_experience(1)

        # Определяем доступные типы руды на основе ранга
        available_ores = {}
        if self.rank >= 1:
            available_ores["copper_ore"] = self.ore_chances["copper_ore"]
        if self.rank >= 2:
            available_ores["iron_ore"] = self.ore_chances["iron_ore"]
        if self.rank >= 3:
            available_ores["silver_ore"] = self.ore_chances["silver_ore"]
        if self.rank >= 4:
            available_ores["gold_ore"] = self.ore_chances["gold_ore"]
        if self.rank >= 5:
            available_ores["mithril_ore"] = self.ore_chances["mithril_ore"]

        # Пробуем добыть каждый доступный тип руды
        for ore_type, base_chance in available_ores.items():
            # Шанс с учетом ранга
            chance = min(95, base_chance + success_bonus)

            if random.random() * 100 < chance:
                # Количество зависит от ранга (1-3 на низких рангах, до 5 на высоких)
                quantity = random.randint(1, min(5, 1 + self.rank // 2))
                resources.append((PREDEFINED_ITEMS[ore_type], quantity))

        # Случайные события при добыче (10% шанс)
        event_roll = random.randint(1, 100)
        if event_roll <= 10:
            events = [
                ("Камень упал с потолка и ударил вас по голове!", -10, None),
                ("Вы нашли тайник со старыми монетами!", 0, 50),
                ("Обвал! Вы получили травмы.", -15, None),
                ("Вы нашли дополнительную руду в расщелине!", 0, "extra_ore"),
            ]
            event = random.choice(events)
            print(event[0])

            # Применяем эффект события
            if event[1] < 0:  # Урон
                player.take_damage(abs(event[1]))
            elif event[2] == "extra_ore":  # Дополнительная руда
                bonus_ore = random.choice(list(self.ore_chances.keys()))
                resources.append((PREDEFINED_ITEMS[bonus_ore], random.randint(1, 3)))
            elif event[2] is not None:  # Золото
                player.inventory.add_gold(event[2])

        # Даем опыт только при успешной добыче (улучшенная формула)
        if resources:
            # Базовый опыт + бонус за количество + бонус за ранг
            exp_gained = 15 + len(resources) * 10 + self.rank * 2
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
            resources.append((PREDEFINED_ITEMS["wood"], quantity))

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
                resources.append((PREDEFINED_ITEMS["wood"], random.randint(3, 6)))
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
                resources.append((PREDEFINED_ITEMS[herb_type], quantity))

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
                resources.append((PREDEFINED_ITEMS[bonus_herb], random.randint(1, 2)))
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
