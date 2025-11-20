"""
Враждебные NPC: Bandit и Undead
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD, NPC_RELATIONSHIPS,
    RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, BANDIT_CAMP_RADIUS
)


class Bandit(NPC):
    """Класс Бандита с AI патрулирования территории лагеря"""

    def __init__(self, name, x=0, y=0, level=4, camp_x=None, camp_y=None):
        """
        Инициализация Бандита

        Args:
            name: Имя бандита
            x: Позиция X
            y: Позиция Y
            level: Уровень бандита
            camp_x: Координата X лагеря
            camp_y: Координата Y лагеря
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_BANDIT, level=level)

        # Модификация статов для бандита: боец с низким духом
        self._adjust_bandit_stats()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat, return_to_camp
        self.camp_x = camp_x if camp_x is not None else x  # Позиция лагеря
        self.camp_y = camp_y if camp_y is not None else y

        # Радиусы зоны контроля бандитов
        self.spawn_radius = 10  # Радиус спавна от лагеря
        self.patrol_radius = 20  # Радиус патрулирования
        self.max_distance_from_camp = self.patrol_radius  # Максимальная дистанция для патруля

        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)  # Отдых 2-4 часа
        self.steps_per_hour = 1  # Шагов за час
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range_player = 10  # Дальность обнаружения игрока
        self.detection_range_npc = 5  # Дальность обнаружения других NPC
        self.wander_target = None  # Целевая точка для блуждания
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 8  # Максимальное количество ходов преследования

    def _adjust_bandit_stats(self):
        """Модификация статов для бандита - агрессивный боец"""
        # Повышаем боевые характеристики
        self.strength = int(self.strength * 1.2)
        self.dexterity = int(self.dexterity * 1.15)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.35))
        self.intelligence = max(1, int(self.intelligence * 0.5))

        # Обновляем производные статы
        self.update_derived_stats()

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI бандита за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока (бандиты агрессивны к игроку)
        """
        if not self.is_alive:
            return

        # Сохраняем ссылки для проверки коллизий
        self._temp_all_npcs = all_npcs
        self._temp_player = player
        self._temp_game_map = game_map

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости (включая игрока)
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

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

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости (включая игрока)

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        # Проверяем игрока (бандиты ВСЕГДА агрессивны к игроку)
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range_player:
                closest_enemy = player
                closest_distance = distance

        # Проверяем других NPC (с меньшей дистанцией обнаружения)
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Пропускаем самого себя
                if npc is self:
                    continue

                # Бандиты не атакуют других бандитов
                if npc.npc_type == NPC_TYPE_BANDIT:
                    continue

                # Проверяем отношение к этому NPC
                relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

                if relationship == RELATIONSHIP_HOSTILE:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                    # Если враг в зоне обнаружения (используем меньшую дистанцию для NPC)
                    if distance <= self.detection_range_npc and distance < closest_distance:
                        closest_enemy = npc
                        closest_distance = distance

        # Если нашли врага, проверяем лимит преследователей
        if closest_enemy:
            # Считаем сколько NPC уже преследуют эту цель
            pursuers_count = 0
            if all_npcs:
                for npc in all_npcs:
                    if (npc.is_alive and npc is not self and
                        hasattr(npc, 'target_enemy') and npc.target_enemy is closest_enemy and
                        hasattr(npc, 'state') and npc.state == "combat"):
                        pursuers_count += 1

            # Ограничиваем до 2 преследующих
            if pursuers_count < 2:
                self.target_enemy = closest_enemy
                self.state = "combat"
                self.pursuit_counter = 0  # Сбрасываем счетчик преследования
            # Если уже есть 2 преследователя, остаемся на патруле
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

        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря, возвращаемся
        if distance_to_camp > self.max_distance_from_camp:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Если цель - игрок, устанавливаем флаг для открытия интерфейса боя вместо прямой атаки
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self
                # Не атакуем игрока напрямую, ждем открытия интерфейса боя
                return

            # Атакуем только NPC (упрощенный бой за один ход)
            enemy_killed = self._simplified_npc_combat(self.target_enemy)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не выходим ли за пределы территории
                distance_to_camp_new = abs(new_x - self.camp_x) + abs(new_y - self.camp_y)
                if distance_to_camp_new <= self.max_distance_from_camp:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории"""
        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря, возвращаемся
        if distance_to_camp > self.max_distance_from_camp:
            # Идем в сторону лагеря
            dx, dy = self._find_next_step(self.camp_x, self.camp_y, game_map, max_search_distance=50)
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
        if random.random() < 0.05:  # 5% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для блуждания в пределах радиуса патрулирования"""
        # Выбираем случайную точку в пределах радиуса патрулирования от лагеря
        max_offset = self.patrol_radius

        target_x = self.camp_x + random.randint(-max_offset, max_offset)
        target_y = self.camp_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0


class Undead(NPC):
    """Класс Нежити с агрессивным AI и привязкой к руинам"""

    def __init__(self, name, x=0, y=0, level=1, ruins_x=None, ruins_y=None):
        """
        Инициализация Нежити

        Args:
            name: Имя нежити
            x: Позиция X
            y: Позиция Y
            level: Уровень нежити (определяет ранг)
            ruins_x: Координата X руин
            ruins_y: Координата Y руин
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_UNDEAD, level=level)

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat, return_to_ruins
        self.ruins_x = ruins_x if ruins_x is not None else x  # Центр руин
        self.ruins_y = ruins_y if ruins_y is not None else y

        # Радиусы зоны контроля нежити
        self.spawn_radius = 10  # Радиус спавна от руин
        self.patrol_radius = 20  # Радиус патрулирования
        self.max_distance_from_ruins = self.patrol_radius  # Максимальная дистанция для патруля

        self.rest_counter = 0
        self.rest_duration = random.randint(2, 3)  # Отдых 2-3 часа
        self.steps_per_hour = 2  # Увеличено с 1 до 2 - нежить быстрее передвигается
        self.target_enemy = None  # Текущая цель для атаки
        self.detection_range_player = 15  # Дальность обнаружения игрока - лучше видят врагов
        self.detection_range_npc = 5  # Дальность обнаружения других NPC
        self.wander_target = None  # Целевая точка для патруля
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 10  # Увеличено с 8 до 10 - дольше преследуют

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI нежити за 1 час игрового времени
        АКТИВИРОВАНА система патруля и агрессии

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения врагов
            player: Объект игрока (нежита также агрессивна к игроку)
        """
        if not self.is_alive:
            return

        # Сохраняем ссылки для проверки коллизий
        self._temp_all_npcs = all_npcs
        self._temp_player = player
        self._temp_game_map = game_map

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости (включая игрока)
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

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

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости
        Нежита агрессивна ко ВСЕМ!

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        # Проверяем игрока (нежита ВСЕГДА агрессивна к игроку)
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range_player:
                closest_enemy = player
                closest_distance = distance

        # Проверяем других NPC (нежита агрессивна ко всем, кроме другой нежити!)
        # Используем меньшую дистанцию обнаружения для NPC
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Нежита не атакует другую нежить
                if npc.npc_type == NPC_TYPE_UNDEAD:
                    continue

                # Нежита враждебна ко всем живым существам
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения (используем меньшую дистанцию для NPC)
                if distance <= self.detection_range_npc and distance < closest_distance:
                    closest_enemy = npc
                    closest_distance = distance

        # Если нашли врага, проверяем лимит преследователей
        if closest_enemy:
            # Считаем сколько NPC уже преследуют эту цель
            pursuers_count = 0
            if all_npcs:
                for npc in all_npcs:
                    if (npc.is_alive and npc is not self and
                        hasattr(npc, 'target_enemy') and npc.target_enemy is closest_enemy and
                        hasattr(npc, 'state') and npc.state == "combat"):
                        pursuers_count += 1

            # Ограничиваем до 2 преследующих
            if pursuers_count < 2:
                self.target_enemy = closest_enemy
                self.state = "combat"
                self.pursuit_counter = 0  # Сбрасываем счетчик преследования
            # Если уже есть 2 преследователя, остаемся на патруле
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

        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин, возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Если цель - игрок, устанавливаем флаг для открытия интерфейса боя вместо прямой атаки
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self
                # Не атакуем игрока напрямую, ждем открытия интерфейса боя
                return

            # Атакуем только NPC (упрощенный бой за один ход)
            enemy_killed = self._simplified_npc_combat(self.target_enemy)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не выходим ли за пределы территории
                distance_to_ruins_new = abs(new_x - self.ruins_x) + abs(new_y - self.ruins_y)
                if distance_to_ruins_new <= self.max_distance_from_ruins:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории руин"""
        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин, возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins:
            # Идем в сторону руин
            dx, dy = self._find_next_step(self.ruins_x, self.ruins_y, game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Если достигли цели патруля или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_patrol_target()

        # Идем к цели патруля
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        # Случайный отдых
        if random.random() < 0.1:  # 10% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_patrol_target(self):
        """Выбрать случайную точку для патруля в пределах радиуса патрулирования руин"""
        # Выбираем случайную точку в пределах радиуса патрулирования от руин
        max_offset = self.patrol_radius

        target_x = self.ruins_x + random.randint(-max_offset, max_offset)
        target_y = self.ruins_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0
