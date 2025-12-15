"""
Враждебные NPC: Bandit, Undead и ShadowAdept
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD, NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_MAGE, NPC_TYPE_NECROMANCER, NPC_RELATIONSHIPS,
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
        self.detection_range_player = 15  # Увеличена дальность обнаружения игрока
        self.detection_range_npc = 8  # Увеличена дальность обнаружения других NPC
        self.wander_target = None  # Целевая точка для блуждания
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 20  # Увеличено до 20 ходов преследования
        self.idle_timer = random.randint(0, 5)  # Рандомная задержка для десинхронизации

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

    def _adjust_bandit_stats(self):
        """Модификация статов для бандита - агрессивный боец"""
        # Повышаем боевые характеристики (макс +5% для баланса)
        self.strength = int(self.strength * 1.05)
        self.dexterity = int(self.dexterity * 1.04)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.35))
        self.intelligence = max(1, int(self.intelligence * 0.5))

        # Обновляем производные статы
        self.update_derived_stats()

    def update_ai(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        """
        Обновление AI бандита за 1 час игрового времени

        Args:
            context_or_map: AIContext или объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока (бандиты агрессивны к игроку)
            current_hour: Текущий час суток (0-23)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            player = context.player
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
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

        # Проверяем дискомфорт от коллизии с другими NPC
        if self._check_and_handle_npc_collision(all_npcs):
            # Пытаемся разойтись
            if self._try_move_away_from_collision(game_map, all_npcs):
                return  # Успешно разошлись, завершаем ход

        # ВСЕГДА проверяем наличие врагов поблизости (включая игрока)
        self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            # В боевом режиме делаем 1 шаг за час (избегаем телепортации)
            if self.consume_stamina():
                self._combat_step(game_map, context)
                # Проверяем врагов после шага
                self._check_for_enemies(all_npcs, player)
        elif self.state == "patrol":
            # Делаем 1 шаг за 1 час (избегаем телепортации)
            if self.consume_stamina():
                self._patrol_step(game_map)
        elif self.state == "rest":
            self._rest()

    def _is_near_settlement(self, game_map, x, y, safe_distance=2):
        """
        Проверить, находится ли позиция рядом с городом или деревней

        Args:
            game_map: Карта игры
            x: Координата X
            y: Координата Y
            safe_distance: Безопасное расстояние от поселения

        Returns:
            bool: True если позиция слишком близко к поселению
        """
        from game.constants import LOCATION_CITY, LOCATION_VILLAGE
        if not hasattr(game_map, 'locations'):
            return False

        for location in game_map.locations:
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                distance = abs(x - location.x) + abs(y - location.y)
                if distance <= safe_distance:
                    return True
        return False

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

    def _combat_step(self, game_map, context=None):
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

        # Проверяем, не находится ли цель слишком близко к городу/деревне
        if hasattr(self.target_enemy, 'x') and hasattr(self.target_enemy, 'y'):
            if self._is_near_settlement(game_map, self.target_enemy.x, self.target_enemy.y, safe_distance=2):
                # Цель в безопасной зоне, прекращаем преследование
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
                return

        # Проверяем лимит преследования
        if self.pursuit_counter >= self.max_pursuit_steps:
            # Не сбрасываем цель сразу, пытаемся найти её снова
            self.pursuit_counter = 0
            # Остаемся в боевом режиме, проверка врагов произойдет в update_ai
            return

        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря (с запасом), возвращаемся
        if distance_to_camp > self.max_distance_from_camp + 5:
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
                # Сбрасываем счетчик, чтобы продолжать стоять рядом
                self.pursuit_counter = 0
                return

            # Атакуем только NPC (упрощенный бой за один ход)
            enemy_killed = self._simplified_npc_combat(self.target_enemy, context)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
            else:
                # Продолжаем атаковать, сбрасываем счетчик
                self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=50)
            if (dx != 0 or dy != 0):
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не приближаемся ли мы к городу/деревне
                if self._is_near_settlement(game_map, new_x, new_y, safe_distance=2):
                    # Не можем идти туда - слишком близко к поселению
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0
                    return

                # Проверяем, не выходим ли за пределы территории (с запасом)
                distance_to_camp_new = abs(new_x - self.camp_x) + abs(new_y - self.camp_y)
                if distance_to_camp_new <= self.max_distance_from_camp + 5:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                    else:
                        # Не можем двигаться, но не сбрасываем преследование
                        self.pursuit_counter += 1
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
        self.steps_per_hour = 1  # 1 шаг за час (избегаем телепортации)
        self.target_enemy = None  # Текущая цель для атаки
        self.detection_range_player = 18  # Увеличена дальность обнаружения игрока - нежить очень чуткая
        self.detection_range_npc = 10  # Увеличена дальность обнаружения других NPC
        self.wander_target = None  # Целевая точка для патруля
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 25  # Увеличено до 25 - нежить упорно преследует
        self.idle_timer = random.randint(0, 5)  # Рандомная задержка для десинхронизации

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

    def _is_near_settlement(self, game_map, x, y, safe_distance=2):
        """
        Проверить, находится ли позиция рядом с городом или деревней

        Args:
            game_map: Карта игры
            x: Координата X
            y: Координата Y
            safe_distance: Безопасное расстояние от поселения

        Returns:
            bool: True если позиция слишком близко к поселению
        """
        from game.constants import LOCATION_CITY, LOCATION_VILLAGE
        if not hasattr(game_map, 'locations'):
            return False

        for location in game_map.locations:
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                distance = abs(x - location.x) + abs(y - location.y)
                if distance <= safe_distance:
                    return True
        return False

    def update_ai(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        """
        Обновление AI нежити за 1 час игрового времени
        АКТИВИРОВАНА система патруля и агрессии

        Args:
            context_or_map: AIContext или объект карты игры
            all_npcs: Список всех NPC для обнаружения врагов
            player: Объект игрока (нежить также агрессивна к игроку)
            current_hour: Текущий час суток (0-23)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            player = context.player
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
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

        # Проверяем дискомфорт от коллизии с другими NPC
        if self._check_and_handle_npc_collision(all_npcs):
            # Пытаемся разойтись
            if self._try_move_away_from_collision(game_map, all_npcs):
                return  # Успешно разошлись, завершаем ход

        # ВСЕГДА проверяем наличие врагов поблизости (включая игрока)
        self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            # В боевом режиме делаем 1 шаг за час (избегаем телепортации)
            if self.consume_stamina():
                self._combat_step(game_map, context)
                # Проверяем врагов после шага
                self._check_for_enemies(all_npcs, player)
        elif self.state == "patrol":
            # Делаем 1 шаг за 1 час (избегаем телепортации)
            if self.consume_stamina():
                self._patrol_step(game_map)
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

    def _combat_step(self, game_map, context=None):
        """
        Один шаг боевого поведения нежити с ограничением преследования

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, не находится ли цель слишком близко к городу/деревне
        if hasattr(self.target_enemy, 'x') and hasattr(self.target_enemy, 'y'):
            if self._is_near_settlement(game_map, self.target_enemy.x, self.target_enemy.y, safe_distance=2):
                # Цель в безопасной зоне, прекращаем преследование
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
                return

        # Проверяем лимит преследования
        if self.pursuit_counter >= self.max_pursuit_steps:
            # Не сбрасываем цель сразу, пытаемся найти её снова
            self.pursuit_counter = 0
            # Остаемся в боевом режиме, проверка врагов произойдет в update_ai
            return

        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин (с запасом для нежити), возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins + 8:
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
                # Сбрасываем счетчик, чтобы продолжать стоять рядом
                self.pursuit_counter = 0
                return

            # Атакуем только NPC (упрощенный бой за один ход)
            enemy_killed = self._simplified_npc_combat(self.target_enemy, context)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
            else:
                # Продолжаем атаковать, сбрасываем счетчик
                self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=60)
            if (dx != 0 or dy != 0):
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не приближаемся ли мы к городу/деревне
                if self._is_near_settlement(game_map, new_x, new_y, safe_distance=2):
                    # Не можем идти туда - слишком близко к поселению
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0
                    return

                # Проверяем, не выходим ли за пределы территории (с запасом)
                distance_to_ruins_new = abs(new_x - self.ruins_x) + abs(new_y - self.ruins_y)
                if distance_to_ruins_new <= self.max_distance_from_ruins + 8:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                    else:
                        # Не можем двигаться, но не сбрасываем преследование
                        self.pursuit_counter += 1
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


class ShadowAdept(NPC):
    """
    Класс Адепта Тени - наемные убийцы и шпионы

    Характеристики:
    - Приоритет экипировки: средняя броня
    - Основные характеристики: ловкость и удача
    - Агрессивны к: магам, нежити, бандитам и некромантам
    """

    def __init__(self, name, x=0, y=0, level=5, camp_x=None, camp_y=None):
        """
        Инициализация Адепта Тени

        Args:
            name: Имя адепта
            x: Позиция X
            y: Позиция Y
            level: Уровень адепта
            camp_x: Координата X Тайного лагеря
            camp_y: Координата Y Тайного лагеря
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_SHADOW_ADEPT, level=level)

        # Модификация статов для адепта тени: ловкость и удача
        self._adjust_shadow_adept_stats()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.camp_x = camp_x if camp_x is not None else x
        self.camp_y = camp_y if camp_y is not None else y

        # Радиусы зоны контроля
        self.spawn_radius = 10
        self.patrol_radius = 25  # Широкий радиус патрулирования
        self.max_distance_from_camp = self.patrol_radius

        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)
        self.steps_per_hour = 1
        self.target_enemy = None
        self.detection_range_player = 16  # Высокая дальность обнаружения
        self.detection_range_npc = 12
        self.wander_target = None
        self.pursuit_counter = 0
        self.max_pursuit_steps = 22
        self.idle_timer = random.randint(0, 5)

        # Враждебные типы NPC
        self.hostile_types = [NPC_TYPE_MAGE, NPC_TYPE_UNDEAD, NPC_TYPE_BANDIT, NPC_TYPE_NECROMANCER]

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

    def _adjust_shadow_adept_stats(self):
        """Модификация статов для адепта тени - высокая ловкость и удача"""
        # Повышаем ловкость и удачу (приоритетные характеристики)
        self.dexterity = int(self.dexterity * 1.25)  # +25% ловкости
        self.luck = int(self.luck * 1.20)  # +20% удачи

        # Средняя сила
        self.strength = int(self.strength * 1.0)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.5))
        self.intelligence = max(1, int(self.intelligence * 0.6))

        # Обновляем производные статы
        self.update_derived_stats()

    def _is_near_settlement(self, game_map, x, y, safe_distance=2):
        """Проверить, находится ли позиция рядом с городом или деревней"""
        from game.constants import LOCATION_CITY, LOCATION_VILLAGE
        if not hasattr(game_map, 'locations'):
            return False

        for location in game_map.locations:
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                distance = abs(x - location.x) + abs(y - location.y)
                if distance <= safe_distance:
                    return True
        return False

    def update_ai(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        """Обновление AI адепта тени за 1 час игрового времени"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            player = context.player
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        self.recover_stamina()

        if self.is_resting:
            return

        if self.idle_timer > 0:
            self.idle_timer -= 1
            return

        if self._check_and_handle_npc_collision(all_npcs):
            if self._try_move_away_from_collision(game_map, all_npcs):
                return

        # Проверяем врагов (адепты тени НЕ агрессивны к игроку!)
        self._check_for_enemies(all_npcs, player=None)

        if self.state == "combat":
            if self.consume_stamina():
                self._combat_step(game_map, context)
                self._check_for_enemies(all_npcs, player=None)
        elif self.state == "patrol":
            if self.consume_stamina():
                self._patrol_step(game_map)
        elif self.state == "rest":
            self._rest_shadow()

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости
        Адепты тени агрессивны к магам, нежити, бандитам и некромантам, но НЕ к игроку
        """
        closest_enemy = None
        closest_distance = float('inf')

        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                if npc is self:
                    continue

                if npc.npc_type == NPC_TYPE_SHADOW_ADEPT:
                    continue

                if npc.npc_type in self.hostile_types:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                    if distance <= self.detection_range_npc and distance < closest_distance:
                        closest_enemy = npc
                        closest_distance = distance

        if closest_enemy:
            pursuers_count = 0
            if all_npcs:
                for npc in all_npcs:
                    if (npc.is_alive and npc is not self and
                        hasattr(npc, 'target_enemy') and npc.target_enemy is closest_enemy and
                        hasattr(npc, 'state') and npc.state == "combat"):
                        pursuers_count += 1

            if pursuers_count < 2:
                self.target_enemy = closest_enemy
                self.state = "combat"
                self.pursuit_counter = 0
        elif self.state == "combat":
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map, context=None):
        """Один шаг боевого поведения"""
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        if hasattr(self.target_enemy, 'x') and hasattr(self.target_enemy, 'y'):
            if self._is_near_settlement(game_map, self.target_enemy.x, self.target_enemy.y, safe_distance=2):
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
                return

        if self.pursuit_counter >= self.max_pursuit_steps:
            self.pursuit_counter = 0
            return

        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)
        if distance_to_camp > self.max_distance_from_camp + 5:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        if self.can_attack(self.target_enemy):
            enemy_killed = self._simplified_npc_combat(self.target_enemy, context)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
            else:
                self.pursuit_counter = 0
        else:
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=50)
            if (dx != 0 or dy != 0):
                new_x = self.x + dx
                new_y = self.y + dy

                if self._is_near_settlement(game_map, new_x, new_y, safe_distance=2):
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0
                    return

                distance_to_camp_new = abs(new_x - self.camp_x) + abs(new_y - self.camp_y)
                if distance_to_camp_new <= self.max_distance_from_camp + 5:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1
                    else:
                        self.pursuit_counter += 1
                else:
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории"""
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        if distance_to_camp > self.max_distance_from_camp:
            dx, dy = self._find_next_step(self.camp_x, self.camp_y, game_map, max_search_distance=50)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_wander_target()

        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=30)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        if random.random() < 0.05:
            self.state = "rest"
            self.rest_counter = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для патруля"""
        max_offset = self.patrol_radius

        target_x = self.camp_x + random.randint(-max_offset, max_offset)
        target_y = self.camp_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest_shadow(self):
        """Отдых адепта тени"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0