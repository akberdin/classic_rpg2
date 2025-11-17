"""
Классы персонажей (игрок и NPC)
"""
import random
from game.constants import MAX_LEVEL, RANKS, RELATIONSHIP_NEUTRAL


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

    def get_rank(self):
        """
        Получить ранг персонажа на основе уровня

        Returns:
            str: Название ранга
        """
        level = getattr(self, 'level', 1)
        for (min_level, max_level), rank_name in RANKS.items():
            if min_level <= level <= max_level:
                return rank_name
        return "Новичок"


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
        # Проверяем, не достигнут ли максимальный уровень
        if self.level >= MAX_LEVEL:
            print(f"Вы достигли максимального уровня {MAX_LEVEL}!")
            self.experience = 0
            return

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

        # Получаем ранг
        rank = self.get_rank()
        print(f"Поздравляем! Вы достигли {self.level} уровня! Ранг: {rank}")

    def rest(self):
        """
        Отдых - восстанавливает здоровье и ману
        Занимает 1 час игрового времени
        """
        # Восстанавливаем 30% от максимального здоровья
        health_restored = int(self.max_health * 0.3)
        self.health = min(self.max_health, self.health + health_restored)

        # Восстанавливаем 50% от максимальной маны
        mana_restored = int(self.max_mana * 0.5)
        self.mana = min(self.max_mana, self.mana + mana_restored)

        print(f"Здоровье восстановлено: +{health_restored} ({self.health}/{self.max_health})")
        print(f"Мана восстановлена: +{mana_restored} ({self.mana}/{self.max_mana})")

    def work(self):
        """
        Работа - получение опыта и золота
        Занимает 1 час игрового времени
        """
        # Получаем опыт в зависимости от уровня
        exp_gained = 10 + self.level * 2
        self.add_experience(exp_gained)
        print(f"Вы поработали и получили {exp_gained} опыта")


class NPC(Character):
    """Класс NPC (неигровых персонажей)"""

    def __init__(self, name, x=0, y=0, npc_type="neutral", level=1):
        """
        Инициализация NPC

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            npc_type: Тип NPC (neutral, enemy, friendly)
            level: Уровень NPC
        """
        super().__init__(name, x, y)
        self.npc_type = npc_type
        self.level = level
        self.relationship = RELATIONSHIP_NEUTRAL  # Отношение к игроку по умолчанию
        self.generate_random_stats()


class Guard(NPC):
    """Класс Стражника с AI патрулирования"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Стражника

        Args:
            name: Имя стражника
            x: Позиция X
            y: Позиция Y
            level: Уровень стражника
        """
        super().__init__(name, x, y, npc_type="guard", level=level)

        # AI параметры
        self.state = "patrol"  # patrol, rest, alert
        self.patrol_points = []  # Точки патрулирования
        self.current_patrol_index = 0
        self.rest_counter = 0
        self.rest_duration = 3  # Длительность отдыха в часах
        self.patrol_home_x = x  # Домашняя точка патруля
        self.patrol_home_y = y
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)

    def set_patrol_route(self, points):
        """
        Установить маршрут патрулирования

        Args:
            points: Список точек (x, y) для патрулирования
        """
        self.patrol_points = points
        self.current_patrol_index = 0

    def update_ai(self, game_map):
        """
        Обновление AI стражника за 1 час игрового времени
        Стражник делает несколько шагов за час

        Args:
            game_map: Объект карты игры
        """
        if self.state == "patrol":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                self._patrol_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _patrol_step(self, game_map):
        """Один шаг патрулирования"""
        if not self.patrol_points:
            # Если нет маршрута, стоим на месте
            # Периодически переходим в режим отдыха
            if random.random() < 0.1:  # 10% шанс каждый шаг
                self.state = "rest"
                self.rest_counter = 0
            return

        # Получаем целевую точку
        target_x, target_y = self.patrol_points[self.current_patrol_index]

        # Вычисляем направление движения (8 направлений)
        dx = 0
        dy = 0

        if self.x < target_x:
            dx = 1
        elif self.x > target_x:
            dx = -1

        if self.y < target_y:
            dy = 1
        elif self.y > target_y:
            dy = -1

        # Пытаемся двигаться по диагонали, если это возможно
        if dx != 0 and dy != 0:
            # Диагональное движение
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy
            # Если по диагонали нельзя, пробуем по оси X
            elif self._can_move(self.x + dx, self.y, game_map):
                self.x += dx
            # Если по X нельзя, пробуем по оси Y
            elif self._can_move(self.x, self.y + dy, game_map):
                self.y += dy
        # Движение только по одной оси
        elif dx != 0:
            if self._can_move(self.x + dx, self.y, game_map):
                self.x += dx
        elif dy != 0:
            if self._can_move(self.x, self.y + dy, game_map):
                self.y += dy

        # Проверяем, достигли ли цели
        if self.x == target_x and self.y == target_y:
            # Переходим к следующей точке
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

            # Случайный отдых в точке патруля
            if random.random() < 0.3:  # 30% шанс отдохнуть
                self.state = "rest"
                self.rest_counter = 0

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли стражник двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Merchant(NPC):
    """Класс Торговца с AI перемещения между городами"""

    def __init__(self, name, x=0, y=0, level=3):
        """
        Инициализация Торговца

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, npc_type="merchant", level=level)

        # AI параметры
        self.state = "travel"  # travel, rest, trade
        self.target_location = None  # Целевая локация (город/деревня)
        self.rest_counter = 0
        self.rest_duration = random.randint(5, 8)  # Отдых 5-8 часов в городе
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)
        self.settlements = []  # Список всех населенных пунктов
        self.stuck_counter = 0  # Счетчик для определения застревания
        self.last_position = (x, y)

    def set_settlements(self, settlements):
        """
        Установить список населенных пунктов для посещения

        Args:
            settlements: Список локаций (Location объектов)
        """
        self.settlements = settlements
        if settlements and not self.target_location:
            self._choose_new_destination()

    def update_ai(self, game_map):
        """
        Обновление AI торговца за 1 час игрового времени

        Args:
            game_map: Объект карты игры
        """
        if self.state == "travel":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self._travel_step(game_map):
                    break
        elif self.state == "rest":
            self._rest()

    def _choose_new_destination(self):
        """Выбрать новую цель для путешествия"""
        if not self.settlements:
            return

        # Исключаем текущую позицию из выбора
        available = [s for s in self.settlements
                    if abs(s.x - self.x) > 5 or abs(s.y - self.y) > 5]

        if available:
            self.target_location = random.choice(available)
        elif self.settlements:
            self.target_location = random.choice(self.settlements)

        self.stuck_counter = 0

    def _travel_step(self, game_map):
        """
        Один шаг путешествия к цели

        Returns:
            bool: True если торговец продолжает движение
        """
        if not self.target_location:
            self._choose_new_destination()
            return False

        target_x = self.target_location.x
        target_y = self.target_location.y

        # Проверяем, достигли ли цели (в пределах 2 клеток)
        distance = abs(self.x - target_x) + abs(self.y - target_y)
        if distance <= 2:
            # Достигли города, переходим в режим отдыха/торговли
            self.state = "rest"
            self.rest_counter = 0
            self.rest_duration = random.randint(5, 8)
            return False

        # Определяем направление движения (8 направлений)
        dx = 0
        dy = 0

        if self.x < target_x:
            dx = 1
        elif self.x > target_x:
            dx = -1

        if self.y < target_y:
            dy = 1
        elif self.y > target_y:
            dy = -1

        # Сохраняем текущую позицию для проверки застревания
        old_x, old_y = self.x, self.y

        # Пытаемся двигаться
        moved = False

        # Приоритет 1: Диагональное движение
        if dx != 0 and dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy
                moved = True
            # Приоритет 2: Движение по оси X
            elif self._can_move(self.x + dx, self.y, game_map):
                self.x += dx
                moved = True
            # Приоритет 3: Движение по оси Y
            elif self._can_move(self.x, self.y + dy, game_map):
                self.y += dy
                moved = True
        # Движение только по одной оси
        elif dx != 0:
            if self._can_move(self.x + dx, self.y, game_map):
                self.x += dx
                moved = True
            # Попытка обойти препятствие
            elif self._can_move(self.x + dx, self.y + 1, game_map):
                self.x += dx
                self.y += 1
                moved = True
            elif self._can_move(self.x + dx, self.y - 1, game_map):
                self.x += dx
                self.y -= 1
                moved = True
        elif dy != 0:
            if self._can_move(self.x, self.y + dy, game_map):
                self.y += dy
                moved = True
            # Попытка обойти препятствие
            elif self._can_move(self.x + 1, self.y + dy, game_map):
                self.x += 1
                self.y += dy
                moved = True
            elif self._can_move(self.x - 1, self.y + dy, game_map):
                self.x -= 1
                self.y += dy
                moved = True

        # Проверка застревания
        if not moved or (self.x == old_x and self.y == old_y):
            self.stuck_counter += 1
            if self.stuck_counter > 20:
                # Если застряли, выбираем новую цель
                self._choose_new_destination()
                self.stuck_counter = 0
                return False
        else:
            self.stuck_counter = 0

        return True

    def _rest(self):
        """Отдых/торговля в городе"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            # Закончили отдых, выбираем новый город
            self.state = "travel"
            self._choose_new_destination()

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли торговец двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()
