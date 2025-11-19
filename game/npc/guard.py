"""
Класс Стражника с AI патрулирования и боевым поведением
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_GUARD, NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE
)


class Guard(NPC):
    """Класс Стражника с AI патрулирования и боевым поведением"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Стражника

        Args:
            name: Имя стражника
            x: Позиция X
            y: Позиция Y
            level: Уровень стражника
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_GUARD, level=level)

        # Модификация статов для стражника: высокие сила и телосложение, низкий дух
        self._adjust_guard_stats()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.patrol_points = []  # Точки патрулирования
        self.current_patrol_index = 0
        self.rest_counter = 0
        self.rest_duration = 3  # Длительность отдыха в часах
        self.patrol_home_x = x  # Домашняя точка патруля
        self.patrol_home_y = y
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range = 10  # Дальность обнаружения врагов
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 8  # Максимальное количество ходов преследования

    def _adjust_guard_stats(self):
        """Модификация статов для стражника - воин, не маг"""
        # Увеличиваем боевые характеристики
        self.strength = int(self.strength * 1.3)
        self.constitution = int(self.constitution * 1.2)
        self.dexterity = int(self.dexterity * 1.1)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.6))

        # Обновляем производные статы
        self.update_derived_stats()

    def set_patrol_route(self, points):
        """
        Установить маршрут патрулирования

        Args:
            points: Список точек (x, y) для патрулирования
        """
        self.patrol_points = points
        self.current_patrol_index = 0

    def update_ai(self, game_map, all_npcs=None):
        """
        Обновление AI стражника за 1 час игрового времени
        Стражник делает несколько шагов за час

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости
        if all_npcs:
            self._check_for_enemies(all_npcs)

        if self.state == "combat":
            self._combat_step(game_map)
        elif self.state == "patrol":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                self._patrol_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_enemies(self, all_npcs):
        """
        Проверить наличие врагов поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship == RELATIONSHIP_HOSTILE:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_enemy = npc
                    closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
            self.pursuit_counter = 0  # Сбрасываем счетчик преследования
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения с ограничением преследования

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования (8 ходов)
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            attack_result = self.attack(self.target_enemy)

            if attack_result['dodged']:
                print(f"{self.target_enemy.name} увернулся от атаки {self.name}!")
            elif attack_result['hit']:
                crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""
                print(f"{self.name} атакует {self.target_enemy.name} и наносит {attack_result['damage']} урона!{crit_msg}")
                if not self.target_enemy.is_alive:
                    print(f"{self.target_enemy.name} повержен!")
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
                    self.pursuit_counter += 1  # Увеличиваем счетчик преследования

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

        # Используем алгоритм поиска пути для определения следующего шага
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=30)

        # Если нашли направление и можем двигаться
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
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
