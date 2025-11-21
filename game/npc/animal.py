"""
Животные NPC: Wolf, Bear, Deer
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER,
    NPC_TYPE_HUNTER, NPC_RELATIONSHIPS,
    RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY
)


class Animal(NPC):
    """Базовый класс для животных NPC"""

    def __init__(self, name, x=0, y=0, npc_type=NPC_TYPE_WOLF, level=1, spawn_x=None, spawn_y=None, behavior_mode="patrol"):
        """
        Инициализация животного

        Args:
            name: Имя животного
            x: Позиция X
            y: Позиция Y
            npc_type: Тип животного (wolf, bear, deer)
            level: Уровень животного
            spawn_x: Координата X точки спавна
            spawn_y: Координата Y точки спавна
            behavior_mode: Режим поведения ("patrol" - патрулирование вокруг точки спавна,
                          "wander" - свободное путешествие по всей карте)
        """
        super().__init__(name, x, y, npc_type=npc_type, level=level)

        # AI параметры
        self.behavior_mode = behavior_mode  # patrol или wander
        self.state = behavior_mode  # patrol, wander, rest, combat, flee
        self.spawn_x = spawn_x if spawn_x is not None else x
        self.spawn_y = spawn_y if spawn_y is not None else y

        # Радиусы зоны (для режима patrol)
        self.patrol_radius = 20
        self.max_distance_from_spawn = 30

        # Параметры для режима wander (свободное путешествие)
        self.wander_direction_timer = 0  # Таймер смены направления
        self.wander_direction_duration = random.randint(5, 15)  # Как долго идти в одном направлении
        self.wander_dx = 0  # Текущее направление X
        self.wander_dy = 0  # Текущее направление Y

        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)
        self.steps_per_hour = 1
        self.target_enemy = None
        self.detection_range = 10
        self.wander_target = None
        self.pursuit_counter = 0
        self.max_pursuit_steps = 10
        self.idle_timer = random.randint(0, 5)
        self.flee_on_low_health = False
        self.provoked = False  # Флаг провокации (атаки игроком)

        # Состояние по умолчанию для расписания
        self.default_state = behavior_mode

    def _generate_initial_equipment(self):
        """Переопределяем метод - животные не имеют экипировки"""
        pass

    def update_ai(self, game_map, all_npcs=None, player=None, current_hour=12):
        """
        Обновление AI животного за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт, не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Рандомная задержка для десинхронизации
        if self.idle_timer > 0:
            self.idle_timer -= 1
            return

        # Проверяем наличие врагов (охотников или провокаторов)
        self._check_for_threats(all_npcs, player)

        if self.state == "flee":
            # Убегаем от угрозы
            if self.consume_stamina():
                self._flee_step(game_map)
        elif self.state == "combat":
            # В боевом режиме
            if self.consume_stamina():
                self._combat_step(game_map)
                self._check_for_threats(all_npcs, player)
        elif self.state == "patrol":
            # Патрулирование вокруг точки спавна
            if self.consume_stamina():
                self._patrol_step(game_map)
        elif self.state == "wander":
            # Свободное путешествие по карте
            if self.consume_stamina():
                self._wander_step(game_map)
        elif self.state == "rest":
            self._rest()

    def _check_for_threats(self, all_npcs, player=None):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        closest_threat = None
        closest_distance = float('inf')

        # Проверяем игрока (если был провоцирован атакой)
        if player and player.is_alive and self.provoked:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range:
                closest_threat = player
                closest_distance = distance

        # Проверяем охотников (всегда враждебны)
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive or npc is self:
                    continue

                # Охотники враждебны к животным
                if npc.npc_type == NPC_TYPE_HUNTER:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                    if distance <= self.detection_range and distance < closest_distance:
                        closest_threat = npc
                        closest_distance = distance

        # Реакция на угрозу
        if closest_threat:
            if self.flee_on_low_health or (self.health / self.max_health) < 0.3:
                # Убегаем если пугливы или мало здоровья
                self.state = "flee"
                self.target_enemy = closest_threat
            else:
                # Сражаемся
                self.state = "combat"
                self.target_enemy = closest_threat
                self.pursuit_counter = 0
        elif self.state in ["combat", "flee"]:
            # Возвращаемся к базовому режиму (patrol или wander)
            self.state = self.behavior_mode
            self.target_enemy = None
            self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Делает один шаг патрулирования"""
        # Проверяем, не слишком ли далеко от точки спавна
        distance_from_spawn = abs(self.x - self.spawn_x) + abs(self.y - self.spawn_y)

        if distance_from_spawn > self.max_distance_from_spawn:
            # Возвращаемся к точке спавна
            dx = 1 if self.spawn_x > self.x else -1 if self.spawn_x < self.x else 0
            dy = 1 if self.spawn_y > self.y else -1 if self.spawn_y < self.y else 0
        else:
            # Случайное блуждание
            if not self.wander_target or (self.x, self.y) == self.wander_target:
                # Выбираем новую цель в пределах радиуса патрулирования
                angle = random.uniform(0, 2 * 3.14159)
                radius = random.randint(5, self.patrol_radius)
                target_x = self.spawn_x + int(radius * random.choice([-1, 1]))
                target_y = self.spawn_y + int(radius * random.choice([-1, 1]))
                self.wander_target = (target_x, target_y)

            # Двигаемся к цели
            dx = 1 if self.wander_target[0] > self.x else -1 if self.wander_target[0] < self.x else 0
            dy = 1 if self.wander_target[1] > self.y else -1 if self.wander_target[1] < self.y else 0

        # Пытаемся двигаться
        new_x, new_y = self.x + dx, self.y + dy
        if self._can_move(new_x, new_y, game_map):
            self.x, self.y = new_x, new_y

    def _wander_step(self, game_map):
        """Делает один шаг свободного путешествия по карте"""
        # Обновляем таймер направления
        self.wander_direction_timer += 1

        # Если пришло время сменить направление или столкнулись с препятствием
        if self.wander_direction_timer >= self.wander_direction_duration:
            self._choose_new_wander_direction(game_map)

        # Пытаемся двигаться в текущем направлении
        new_x = self.x + self.wander_dx
        new_y = self.y + self.wander_dy

        # Проверяем границы карты (отступ от края)
        map_margin = 10
        if new_x < map_margin or new_x >= game_map.width - map_margin:
            self._choose_new_wander_direction(game_map)
            new_x = self.x + self.wander_dx
        if new_y < map_margin or new_y >= game_map.height - map_margin:
            self._choose_new_wander_direction(game_map)
            new_y = self.y + self.wander_dy

        # Проверяем проходимость и двигаемся
        if self._can_move(new_x, new_y, game_map):
            self.x, self.y = new_x, new_y
        else:
            # Столкнулись с препятствием - меняем направление
            self._choose_new_wander_direction(game_map)
            new_x = self.x + self.wander_dx
            new_y = self.y + self.wander_dy
            if self._can_move(new_x, new_y, game_map):
                self.x, self.y = new_x, new_y

        # С небольшой вероятностью отдыхаем
        if random.random() < 0.05:
            self.state = "rest"

    def _choose_new_wander_direction(self, game_map):
        """Выбирает новое случайное направление для путешествия"""
        self.wander_direction_timer = 0
        self.wander_direction_duration = random.randint(5, 15)

        # Выбираем случайное направление (включая диагонали)
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),  # Кардинальные
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # Диагональные
        ]

        # Отдаем предпочтение направлениям, ведущим к центру карты
        center_x = game_map.width // 2
        center_y = game_map.height // 2

        # Если далеко от центра, с большей вероятностью двигаемся к центру
        if abs(self.x - center_x) > game_map.width // 3 or abs(self.y - center_y) > game_map.height // 3:
            if random.random() < 0.6:  # 60% шанс двигаться к центру
                dx = 1 if center_x > self.x else -1 if center_x < self.x else 0
                dy = 1 if center_y > self.y else -1 if center_y < self.y else 0
                self.wander_dx, self.wander_dy = dx, dy
                return

        # Иначе случайное направление
        self.wander_dx, self.wander_dy = random.choice(directions)

    def _combat_step(self, game_map):
        """Делает один шаг в боевом режиме"""
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.state = self.behavior_mode
            self.target_enemy = None
            return

        # Проверяем расстояние до врага
        distance = abs(self.x - self.target_enemy.x) + abs(self.y - self.target_enemy.y)

        if distance > self.detection_range * 2:
            # Враг слишком далеко, прекращаем преследование
            self.pursuit_counter = 0
            self.state = self.behavior_mode
            self.target_enemy = None
            return

        # Преследуем врага
        self.pursuit_counter += 1
        if self.pursuit_counter > self.max_pursuit_steps:
            # Прекращаем преследование после N шагов
            self.pursuit_counter = 0
            self.state = self.behavior_mode
            self.target_enemy = None
            return

        # Двигаемся к врагу
        dx = 1 if self.target_enemy.x > self.x else -1 if self.target_enemy.x < self.x else 0
        dy = 1 if self.target_enemy.y > self.y else -1 if self.target_enemy.y < self.y else 0

        new_x, new_y = self.x + dx, self.y + dy
        if self._can_move(new_x, new_y, game_map):
            self.x, self.y = new_x, new_y

    def _flee_step(self, game_map):
        """Делает один шаг при побеге"""
        if not self.target_enemy:
            self.state = self.behavior_mode
            return

        # Убегаем в противоположную сторону от угрозы
        dx = -1 if self.target_enemy.x > self.x else 1 if self.target_enemy.x < self.x else 0
        dy = -1 if self.target_enemy.y > self.y else 1 if self.target_enemy.y < self.y else 0

        # Добавляем случайность для более естественного движения
        if random.random() < 0.3:
            dx = random.choice([-1, 0, 1])
        if random.random() < 0.3:
            dy = random.choice([-1, 0, 1])

        new_x, new_y = self.x + dx, self.y + dy
        if self._can_move(new_x, new_y, game_map):
            self.x, self.y = new_x, new_y

        # Проверяем расстояние до угрозы
        distance = abs(self.x - self.target_enemy.x) + abs(self.y - self.target_enemy.y)
        if distance > self.detection_range * 2:
            # Убежали достаточно далеко
            self.state = self.behavior_mode
            self.target_enemy = None

    def _rest(self):
        """Отдых"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.rest_counter = 0
            self.rest_duration = random.randint(2, 4)
            self.state = self.behavior_mode

    def mark_as_provoked(self):
        """Пометить животное как провоцированное (атакованное игроком)"""
        self.provoked = True


class Wolf(Animal):
    """Класс Волка - быстрый и агрессивный хищник"""

    def __init__(self, name, x=0, y=0, level=1, spawn_x=None, spawn_y=None, behavior_mode="patrol"):
        super().__init__(name, x, y, npc_type=NPC_TYPE_WOLF, level=level, spawn_x=spawn_x, spawn_y=spawn_y, behavior_mode=behavior_mode)
        self._adjust_wolf_stats()
        self.detection_range = 12
        self.max_pursuit_steps = 15
        self.flee_on_low_health = False

    def _adjust_wolf_stats(self):
        """Модификация статов для волка - быстрый хищник"""
        self.dexterity = int(self.dexterity * 1.05)  # Слегка повышенная ловкость (макс +5%)
        self.strength = int(self.strength * 1.03)  # Слегка повышенная сила
        self.constitution = int(self.constitution * 0.9)  # Низкая выносливость
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.4))
        self.update_derived_stats()


class Bear(Animal):
    """Класс Медведя - сильный и территориальный"""

    def __init__(self, name, x=0, y=0, level=1, spawn_x=None, spawn_y=None, behavior_mode="patrol"):
        super().__init__(name, x, y, npc_type=NPC_TYPE_BEAR, level=level, spawn_x=spawn_x, spawn_y=spawn_y, behavior_mode=behavior_mode)
        self._adjust_bear_stats()
        self.detection_range = 8
        self.max_pursuit_steps = 10
        self.patrol_radius = 15
        self.flee_on_low_health = False

    def _adjust_bear_stats(self):
        """Модификация статов для медведя - сильный и живучий"""
        self.strength = int(self.strength * 1.05)  # Повышенная сила (макс +5%)
        self.constitution = int(self.constitution * 1.05)  # Повышенная выносливость
        self.dexterity = int(self.dexterity * 0.8)  # Низкая ловкость
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.4))
        self.update_derived_stats()


class Deer(Animal):
    """Класс Оленя - быстрый и пугливый"""

    def __init__(self, name, x=0, y=0, level=1, spawn_x=None, spawn_y=None, behavior_mode="patrol"):
        super().__init__(name, x, y, npc_type=NPC_TYPE_DEER, level=level, spawn_x=spawn_x, spawn_y=spawn_y, behavior_mode=behavior_mode)
        self._adjust_deer_stats()
        self.detection_range = 10
        self.max_pursuit_steps = 5
        self.flee_on_low_health = True  # Олени всегда убегают

    def _adjust_deer_stats(self):
        """Модификация статов для оленя - быстрый и слабый"""
        self.dexterity = int(self.dexterity * 1.05)  # Слегка повышенная ловкость (макс +5%)
        self.strength = int(self.strength * 0.7)  # Низкая сила
        self.constitution = int(self.constitution * 0.8)  # Низкая выносливость
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.4))
        self.update_derived_stats()

    def _check_for_threats(self, all_npcs, player=None):
        """Олени боятся всех - переопределяем метод"""
        closest_threat = None
        closest_distance = float('inf')

        # Проверяем игрока (олени боятся всех, не только провокаторов)
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range:
                closest_threat = player
                closest_distance = distance

        # Проверяем всех NPC
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive or npc is self or npc.npc_type == NPC_TYPE_DEER:
                    continue

                distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Олени всегда убегают от угрозы
        if closest_threat:
            self.state = "flee"
            self.target_enemy = closest_threat
        elif self.state == "flee":
            self.state = self.behavior_mode
            self.target_enemy = None
