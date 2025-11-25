"""
Базовый класс NPC (неигровых персонажей)
"""
import random
from collections import deque
from game.character import Character
from game.inventory import Inventory
from game.constants import (
    RELATIONSHIP_NEUTRAL, NPC_RELATIONSHIPS, RELATIONSHIP_HOSTILE
)


# Импорт расписаний будет выполнен позже, чтобы избежать циклических зависимостей
_schedule_module = None


def get_schedule_module():
    """Ленивый импорт модуля расписаний"""
    global _schedule_module
    if _schedule_module is None:
        from game import npc_schedule
        _schedule_module = npc_schedule
    return _schedule_module


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

        # Генерируем характеристики на основе уровня
        self.generate_random_stats(level=self.level)

        # Инвентарь для NPC
        self.inventory = Inventory(max_slots=10, max_weight=50.0)

        # Генерируем и экипируем начальную экипировку
        self._generate_initial_equipment()

        # Система расписаний (инициализируется позже)
        self.schedule = None
        self._init_schedule()

        # Механизм дискомфорта от совместного нахождения с другими NPC
        self.collision_tracker = {}  # {npc_id: turns_count}

    def _init_schedule(self):
        """Инициализация расписания для NPC"""
        schedule_module = get_schedule_module()
        if schedule_module:
            self.schedule = schedule_module.create_schedule_for_npc(self)

    def _generate_initial_equipment(self):
        """Генерация и автоматическая экипировка начального снаряжения"""
        from game.inventory import ItemGenerator

        # Используем rank-based генерацию для лучшего масштабирования
        equipment_items = ItemGenerator.generate_npc_equipment_by_rank(self.npc_type, self.level)

        for item in equipment_items:
            # Добавляем в инвентарь
            if self.inventory.add_item(item, 1):
                # Пытаемся сразу экипировать
                self.inventory.equip_item(item.name)

        # Обновляем характеристики после экипировки
        self.update_derived_stats()

    def is_hidden(self):
        """
        Проверить, скрыт ли NPC (находится в локации)

        Returns:
            bool: True если NPC скрыт
        """
        return self.schedule and self.schedule.is_hidden

    def update_schedule(self, current_hour, game_map):
        """
        Обновить расписание NPC

        Args:
            current_hour: Текущий час суток (0-23)
            game_map: Карта игры
        """
        if self.schedule:
            self.schedule.update(current_hour, game_map)

    def update_ai(self, context):
        """
        Обновить AI NPC.

        Базовый метод - ничего не делает. Переопределяется в подклассах.

        Args:
            context: AIContext с данными для принятия решений
                     или старые параметры для обратной совместимости
        """
        pass

    def _parse_ai_context(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        """
        Разобрать параметры вызова update_ai.

        Поддерживает два способа вызова:
        1. С AIContext (новый способ)
        2. С отдельными параметрами (старый способ)

        Returns:
            tuple: (game_map, all_npcs, player, current_hour)
        """
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            ctx = context_or_map
            return (ctx.game_map, ctx.all_npcs, ctx.player, ctx.current_hour)
        return (context_or_map, all_npcs, player, current_hour)

    def _pre_update_ai(self, current_hour, game_map):
        """
        Общие проверки перед обновлением AI.

        Выполняет: is_alive, расписание, is_hidden, recover_stamina, is_resting.

        Returns:
            bool: True если можно продолжать update_ai
        """
        if not self.is_alive:
            return False

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return False

        self.recover_stamina()

        if self.is_resting:
            return False

        return True

    def _find_next_step(self, target_x, target_y, game_map, max_search_distance=50):
        """
        Найти следующий шаг к цели используя BFS (поиск в ширину)

        Args:
            target_x: Целевая X координата
            target_y: Целевая Y координата
            game_map: Объект карты игры
            max_search_distance: Максимальная дистанция поиска в клетках

        Returns:
            tuple: (dx, dy) - направление следующего шага, или (0, 0) если путь не найден
        """
        # Если уже на месте
        if self.x == target_x and self.y == target_y:
            return (0, 0)

        # BFS для поиска кратчайшего пути
        queue = deque([(self.x, self.y, None)])  # (x, y, first_step)
        visited = {(self.x, self.y)}

        # 8 направлений движения
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        while queue:
            x, y, first_step = queue.popleft()

            # Проверяем все 8 направлений
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                # Достигли цели
                if nx == target_x and ny == target_y:
                    # Возвращаем первый шаг из найденного пути
                    if first_step:
                        return first_step
                    else:
                        return (dx, dy)

                # Проверяем валидность и проходимость
                if (nx, ny) not in visited:
                    if game_map.is_valid_position(nx, ny):
                        tile = game_map.get_tile(nx, ny)
                        if tile.is_passable():
                            # Ограничиваем дистанцию поиска
                            distance = abs(nx - self.x) + abs(ny - self.y)
                            if distance <= max_search_distance:
                                visited.add((nx, ny))
                                # Сохраняем первый шаг (если это первый шаг из начальной позиции)
                                next_first_step = first_step if first_step else (dx, dy)
                                queue.append((nx, ny, next_first_step))

        # Путь не найден - возвращаем (0, 0)
        return (0, 0)

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли NPC двигаться на клетку
        Проверяет только валидность позиции и проходимость тайла

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

    def _check_and_handle_npc_collision(self, all_npcs):
        """
        Проверить наличие других NPC на той же клетке и обработать дискомфорт.
        Если NPC находится с другим NPC более 3 ходов, попытаться разойтись.

        Args:
            all_npcs: Список всех NPC

        Returns:
            bool: True если нужно попытаться разойтись
        """
        if not all_npcs:
            return False

        # Находим всех NPC на той же клетке
        npcs_on_same_tile = []
        for npc in all_npcs:
            if npc is self or not npc.is_alive:
                continue
            if npc.x == self.x and npc.y == self.y:
                npcs_on_same_tile.append(npc)

        # Обновляем трекер коллизий
        current_npc_ids = {id(npc) for npc in npcs_on_same_tile}

        # Увеличиваем счетчик для NPC, которые все еще на той же клетке
        for npc in npcs_on_same_tile:
            npc_id = id(npc)
            if npc_id in self.collision_tracker:
                self.collision_tracker[npc_id] += 1
            else:
                self.collision_tracker[npc_id] = 1

        # Удаляем из трекера NPC, которые больше не на той же клетке
        self.collision_tracker = {
            npc_id: count
            for npc_id, count in self.collision_tracker.items()
            if npc_id in current_npc_ids
        }

        # Проверяем, есть ли NPC с которым мы находимся более 3 ходов
        max_collision_turns = max(self.collision_tracker.values()) if self.collision_tracker else 0

        return max_collision_turns > 3

    def _try_move_away_from_collision(self, game_map, all_npcs):
        """
        Попытаться уйти с клетки при дискомфорте от коллизии с другим NPC.

        Args:
            game_map: Объект карты
            all_npcs: Список всех NPC

        Returns:
            bool: True если удалось сдвинуться
        """
        # Все возможные направления (включая диагонали)
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        # Перемешиваем для случайности
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = self.x + dx
            new_y = self.y + dy

            # Проверяем проходимость
            if not self._can_move(new_x, new_y, game_map):
                continue

            # Проверяем, нет ли других NPC на новой клетке
            has_npc = False
            if all_npcs:
                for npc in all_npcs:
                    if npc is self or not npc.is_alive:
                        continue
                    if npc.x == new_x and npc.y == new_y:
                        has_npc = True
                        break

            # Если клетка свободна, перемещаемся
            if not has_npc:
                self.x = new_x
                self.y = new_y
                # Сбрасываем трекер коллизий после успешного расхождения
                self.collision_tracker.clear()
                return True

        return False

    def _simplified_npc_combat(self, enemy, context=None):
        """
        Упрощенный бой между NPC - моментальный расчет победителя
        Рассчитывает исход боя мгновенно на основе характеристик

        Args:
            enemy: Враг для боя
            context: AIContext (опционально) для регистрации смертей

        Returns:
            bool: True если враг повержен
        """
        # Моментальный расчет боя на основе характеристик
        # Рассчитываем "силу" каждого бойца
        self_power = (self.get_total_damage() * 0.4 +
                     self.get_total_defense() * 0.2 +
                     self.health * 0.3 +
                     self.dexterity * 0.1)

        enemy_power = (enemy.get_total_damage() * 0.4 +
                      enemy.get_total_defense() * 0.2 +
                      enemy.health * 0.3 +
                      enemy.dexterity * 0.1)

        # Добавляем случайность (±20%)
        self_power *= random.uniform(0.8, 1.2)
        enemy_power *= random.uniform(0.8, 1.2)

        # Определяем победителя и наносим урон
        if self_power > enemy_power:
            # Этот NPC побеждает
            power_ratio = self_power / enemy_power
            damage = int(self.get_total_damage() * power_ratio * random.uniform(0.8, 1.5))
            enemy.take_damage(damage)

            # Этот NPC тоже получает урон, но меньше
            counter_damage = int(enemy.get_total_damage() * random.uniform(0.3, 0.7))
            self.take_damage(counter_damage)

            # Регистрируем смерть врага для респавна
            enemy_killed = not enemy.is_alive
            if enemy_killed and context and context.respawn_manager and context.game:
                context.respawn_manager.register_death(enemy, context.game)

            return enemy_killed
        else:
            # Враг побеждает
            power_ratio = enemy_power / self_power
            damage = int(enemy.get_total_damage() * power_ratio * random.uniform(0.8, 1.5))
            self.take_damage(damage)

            # Враг тоже получает урон, но меньше
            counter_damage = int(self.get_total_damage() * random.uniform(0.3, 0.7))
            enemy.take_damage(counter_damage)

            # Регистрируем смерть этого NPC для респавна
            self_killed = not self.is_alive
            if self_killed and context and context.respawn_manager and context.game:
                context.respawn_manager.register_death(self, context.game)

            return False
