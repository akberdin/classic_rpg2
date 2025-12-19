"""
Класс Шахтера с новой AI логикой на основе ходов
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_MINER, NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL,
    RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY
)


class Miner(NPC):
    """
    Класс Шахтера с циклической логикой работы на основе ходов:
    1. После спавна идёт к шахте
    2. Скрывается на 35-40 ходов (работает в шахте)
    3. Появляется и идёт в город/деревню для отдыха
    4. Скрывается на 35-40 ходов (отдыхает)
    5. Появляется и идёт к шахте - цикл повторяется
    6. При появлении агрессивных NPC убегает
    """

    def __init__(self, name, x=0, y=0, level=3, mine_x=None, mine_y=None, mine_name=None,
                 rest_x=None, rest_y=None, rest_location_name=None, spawn_radius=3):
        """
        Инициализация Шахтера

        Args:
            name: Имя шахтера
            x: Позиция X спавна
            y: Позиция Y спавна
            level: Уровень шахтера
            mine_x: Координата X шахты
            mine_y: Координата Y шахты
            mine_name: Название шахты
            rest_x: Координата X места отдыха (город/деревня)
            rest_y: Координата Y места отдыха
            rest_location_name: Название места отдыха
            spawn_radius: Радиус спавна от шахты
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MINER, level=level)

        # Модификация статов для шахтера: больше силы и телосложения
        self._adjust_miner_stats()

        # Координаты рабочего места (шахта)
        self.mine_x = mine_x if mine_x is not None else x
        self.mine_y = mine_y if mine_y is not None else y
        self.mine_name = mine_name or "Шахта"

        # Координаты места отдыха (город/деревня)
        self.rest_x = rest_x if rest_x is not None else x
        self.rest_y = rest_y if rest_y is not None else y
        self.rest_location_name = rest_location_name or "Город"

        # Параметры для работы/отдыха
        self.work_turns = random.randint(35, 40)  # Длительность работы в шахте
        self.rest_turns = random.randint(35, 40)  # Длительность отдыха

        # Состояния цикла работы
        # going_to_mine -> working -> going_to_rest -> resting -> going_to_mine ...
        # fleeing - особое состояние при угрозе
        self.state = "going_to_mine"

        # Параметры обнаружения угроз
        self.threat = None  # Текущая угроза
        self.detection_range = 8  # Дальность обнаружения угроз
        self.previous_state = None  # Состояние до бегства

        # Радиус спавна (для совместимости)
        self.spawn_radius = spawn_radius

        # Состояние по умолчанию (не используется в новой логике)
        self.default_state = "going_to_mine"

    def _adjust_miner_stats(self):
        """
        Модификация статов для шахтера - физический труженик.
        Фокус на силе и телосложении.
        """
        # Значительно повышаем физические характеристики
        self.strength = int(self.strength * 1.25)  # +25% к силе
        self.constitution = int(self.constitution * 1.25)  # +25% к телосложению

        # Сильно снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.3))
        self.intelligence = max(1, int(self.intelligence * 0.5))

        # Немного снижаем ловкость
        self.dexterity = max(1, int(self.dexterity * 0.85))

        # Обновляем производные статы
        self.update_derived_stats()

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """
        Обновление AI шахтера каждый ход

        Args:
            context_or_map: AIContext или карта игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (не используется в новой логике)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        # Если NPC скрыт, не обновляем AI
        # (update_hidden_state уже вызван в npc_manager перед этим методом)
        if self.is_hidden():
            return

        # Проверяем только что ли появился (по состоянию working/resting)
        if self.state in ["working", "resting"]:
            self._handle_appearance()
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        # Обрабатываем состояния
        if self.state == "fleeing":
            self._flee_step(game_map)
        elif self.state == "going_to_mine":
            self._go_to_mine(game_map)
        elif self.state == "going_to_rest":
            self._go_to_rest(game_map)
        # working и resting обрабатываются через механизм скрытия

    def _handle_appearance(self):
        """
        Обработка появления NPC на карте после скрытия.
        Определяет следующий этап цикла.
        """
        if self.state == "working":
            # Закончили работать - идём отдыхать
            self.state = "going_to_rest"
        elif self.state == "resting":
            # Закончили отдыхать - идём работать
            self.state = "going_to_mine"

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
            if not npc.is_alive or npc == self:
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
            if self.state != "fleeing":
                self.previous_state = self.state
                self.state = "fleeing"
            self.threat = closest_threat
        elif self.state == "fleeing":
            # Если угрозы больше нет, возвращаемся к предыдущей деятельности
            self.state = self.previous_state if self.previous_state else "going_to_mine"
            self.threat = None
            self.previous_state = None

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к работе
        if not self.threat or not self.threat.is_alive:
            self.state = self.previous_state if self.previous_state else "going_to_mine"
            self.threat = None
            self.previous_state = None
            return

        # Проверяем выносливость
        if not self.consume_stamina():
            return  # Нет выносливости - стоим на месте

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

    def _go_to_mine(self, game_map):
        """
        Идти к шахте. При достижении - скрываемся для работы.

        Args:
            game_map: Объект карты игры
        """
        # Проверяем, достигли ли шахты
        if self.x == self.mine_x and self.y == self.mine_y:
            # Достигли шахты - начинаем работать
            self.state = "working"
            work_duration = random.randint(35, 40)
            self.hide_from_map(work_duration, f"{self.mine_name} (работа)")
            return

        # Проверяем выносливость
        if not self.consume_stamina():
            return  # Нет выносливости

        # Делаем шаг к шахте
        dx, dy = self._find_next_step(self.mine_x, self.mine_y, game_map, max_search_distance=100)
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy

    def _go_to_rest(self, game_map):
        """
        Идти к месту отдыха (город/деревня). При достижении - скрываемся для отдыха.

        Args:
            game_map: Объект карты игры
        """
        # Проверяем, достигли ли места отдыха (точное попадание на клетку)
        if self.x == self.rest_x and self.y == self.rest_y:
            # Достигли места отдыха - начинаем отдыхать
            self.state = "resting"
            rest_duration = random.randint(35, 40)
            self.hide_from_map(rest_duration, f"{self.rest_location_name} (отдых)")
            return

        # Проверяем выносливость
        if not self.consume_stamina():
            return  # Нет выносливости

        # Делаем шаг к месту отдыха
        dx, dy = self._find_next_step(self.rest_x, self.rest_y, game_map, max_search_distance=100)
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy
