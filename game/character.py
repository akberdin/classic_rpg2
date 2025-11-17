"""
Классы персонажей (игрок и NPC)
"""
import random


class Character:
    """Базовый класс для всех персонажей (игрок и NPC)"""

    def __init__(self, name, x=0, y=0):
        """
        Инициализация персонажа

        Args:
            name: Имя персонажа
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        self.name = name
        self.x = x
        self.y = y

        # Характеристики
        self.strength = 0      # Сила
        self.dexterity = 0     # Ловкость
        self.constitution = 0  # Телосложение
        self.spirit = 0        # Дух
        self.intelligence = 0  # Интеллект
        self.luck = 0          # Удача

    def generate_random_stats(self, min_val=5, max_val=15):
        """
        Генерация случайных характеристик

        Args:
            min_val: Минимальное значение характеристики
            max_val: Максимальное значение характеристики
        """
        self.strength = random.randint(min_val, max_val)
        self.dexterity = random.randint(min_val, max_val)
        self.constitution = random.randint(min_val, max_val)
        self.spirit = random.randint(min_val, max_val)
        self.intelligence = random.randint(min_val, max_val)
        self.luck = random.randint(min_val, max_val)

    def get_stats(self):
        """Получить все характеристики в виде словаря"""
        return {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'spirit': self.spirit,
            'intelligence': self.intelligence,
            'luck': self.luck
        }

    def move(self, dx, dy):
        """
        Переместить персонажа

        Args:
            dx: Смещение по X
            dy: Смещение по Y
        """
        self.x += dx
        self.y += dy


class Player(Character):
    """Класс игрока"""

    def __init__(self, name="Hero", x=0, y=0):
        """
        Инициализация игрока

        Args:
            name: Имя игрока
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        super().__init__(name, x, y)

        # Устанавливаем базовые характеристики игрока
        self.strength = 1
        self.dexterity = 1
        self.constitution = 1
        self.spirit = 1
        self.intelligence = 1
        self.luck = 1

        # Дополнительные параметры игрока
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100  # Опыт для следующего уровня

        # Параметр маг (по умолчанию - нет)
        self.is_mage = False

        # Здоровье зависит от телосложения (1 телосложение = 20 здоровья)
        self.max_health = self.constitution * 20
        self.health = self.max_health

        # Мана зависит от духа (1 дух = 10 маны)
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

    def can_move_to(self, x, y, game_map):
        """
        Проверить, может ли игрок переместиться на данную клетку

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если можно переместиться
        """
        # Проверка границ карты
        if x < 0 or x >= game_map.width or y < 0 or y >= game_map.height:
            return False

        # Проверка проходимости тайла
        tile = game_map.get_tile(x, y)
        return tile.is_passable()

    def move_to(self, x, y, game_map):
        """
        Переместить игрока на указанную позицию с проверкой

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если перемещение успешно
        """
        if self.can_move_to(x, y, game_map):
            self.x = x
            self.y = y
            return True
        return False

    def add_experience(self, amount):
        """
        Добавить опыт игроку

        Args:
            amount: Количество опыта

        Returns:
            bool: True если произошло повышение уровня
        """
        self.experience += amount
        leveled_up = False

        # Проверяем, достаточно ли опыта для повышения уровня
        while self.experience >= self.experience_to_next_level:
            leveled_up = True
            self.level_up()

        return leveled_up

    def level_up(self):
        """Повысить уровень игрока"""
        self.experience -= self.experience_to_next_level
        self.level += 1

        # Увеличиваем требуемый опыт для следующего уровня
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)

        # Повышаем характеристики
        self.strength += 1
        self.dexterity += 1
        self.constitution += 1
        self.spirit += 1
        self.intelligence += 1
        self.luck += 1

        # Обновляем максимальное здоровье и ману
        self.max_health = self.constitution * 20
        self.health = self.max_health
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

        print(f"Поздравляем! Вы достигли {self.level} уровня!")


class NPC(Character):
    """Класс NPC (неигровых персонажей)"""

    def __init__(self, name, x=0, y=0, npc_type="neutral"):
        """
        Инициализация NPC

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            npc_type: Тип NPC (neutral, enemy, friendly)
        """
        super().__init__(name, x, y)
        self.npc_type = npc_type
        self.generate_random_stats()
