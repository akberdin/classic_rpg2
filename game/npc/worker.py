"""
Класс Шахтера с AI работы и побега от опасности
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_MINER, NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL,
    RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY
)


class Miner(NPC):
    """Класс Шахтера с AI работы и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3, mine_x=None, mine_y=None):
        """
        Инициализация Шахтера

        Args:
            name: Имя шахтера
            x: Позиция X
            y: Позиция Y
            level: Уровень шахтера
            mine_x: Координата X шахты (центр территории)
            mine_y: Координата Y шахты (центр территории)
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MINER, level=level)

        # Модификация статов для шахтера: физический труд, низкий дух
        self._adjust_miner_stats()

        # AI параметры
        self.state = "work"  # work, rest, flee
        self.mine_x = mine_x if mine_x is not None else x  # Центр шахты
        self.mine_y = mine_y if mine_y is not None else y
        self.max_distance_from_mine = 20  # Максимальная дистанция от шахты
        self.rest_counter = 0
        self.rest_duration = random.randint(3, 5)  # Отдых 3-5 часов
        self.steps_per_hour = 1  # Шагов за час
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз
        self.wander_target = None  # Целевая точка для блуждания

        # Состояние по умолчанию для расписания
        self.default_state = "work"

    def _adjust_miner_stats(self):
        """Модификация статов для шахтера - физический труженик"""
        # Повышаем физические характеристики (макс +5% для баланса)
        self.strength = int(self.strength * 1.05)
        self.constitution = int(self.constitution * 1.05)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.35))
        self.intelligence = max(1, int(self.intelligence * 0.6))

        # Немного снижаем ловкость
        self.dexterity = max(1, int(self.dexterity * 0.9))

        # Обновляем производные статы
        self.update_derived_stats()

    def update_ai(self, game_map, all_npcs=None, current_hour=12):
        """
        Обновление AI шахтера за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности и посещение локаций)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "work":
            # Делаем 1 шаг за 1 час (избегаем телепортации)
            if self.consume_stamina():
                self._work_step(game_map)
        elif self.state == "rest":
            self._rest()

    def _check_for_threats(self, all_npcs):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшую угрозу
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Если есть угроза, убегаем
        if closest_threat:
            self.threat = closest_threat
            self.state = "flee"
        elif self.state == "flee":
            # Если угрозы больше нет, возвращаемся к работе
            self.threat = None
            self.state = "work"

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к работе
        if not self.threat or not self.threat.is_alive:
            self.threat = None
            self.state = "work"
            return

        # Убегаем в противоположную от угрозы сторону
        dx_away = self.x - self.threat.x
        dy_away = self.y - self.threat.y

        # Нормализуем направление
        if dx_away > 0:
            dx = 1
        elif dx_away < 0:
            dx = -1
        else:
            dx = 0

        if dy_away > 0:
            dy = 1
        elif dy_away < 0:
            dy = -1
        else:
            dy = 0

        # Если оба направления 0, выбираем случайное
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        # Пытаемся двигаться
        if self.consume_stamina():
            new_x = self.x + dx
            new_y = self.y + dy

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
            else:
                # Если не можем идти прямо, пробуем другие направления
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                random.shuffle(directions)
                for alt_dx, alt_dy in directions:
                    new_x = self.x + alt_dx
                    new_y = self.y + alt_dy
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        break

    def _work_step(self, game_map):
        """Один шаг работы - патрулирование территории шахты"""
        # Проверяем расстояние до шахты
        distance_to_mine = abs(self.x - self.mine_x) + abs(self.y - self.mine_y)

        # Если слишком далеко от шахты, возвращаемся
        if distance_to_mine > self.max_distance_from_mine:
            # Идем в сторону шахты
            dx, dy = self._find_next_step(self.mine_x, self.mine_y, game_map, max_search_distance=50)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Если достигли цели блуждания или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_wander_target()

        # Идем к цели блуждания
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=30)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        # Случайный отдых
        if random.random() < 0.08:  # 8% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для блуждания в пределах территории шахты"""
        # Выбираем случайную точку в пределах радиуса от шахты
        max_offset = min(self.max_distance_from_mine, 15)  # Ограничиваем для производительности

        target_x = self.mine_x + random.randint(-max_offset, max_offset)
        target_y = self.mine_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "work"
            self.rest_counter = 0
