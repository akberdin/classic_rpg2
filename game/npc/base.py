"""
Базовый класс NPC (неигровых персонажей)
"""
from collections import deque
from game.character import Character
from game.inventory import Inventory
from game.constants import (
    RELATIONSHIP_NEUTRAL, NPC_RELATIONSHIPS, RELATIONSHIP_HOSTILE,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE, LOCATION_MAGIC_SCHOOL
)


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

        # Временные переменные для проверки коллизий (устанавливаются в update_ai)
        self._temp_all_npcs = None
        self._temp_player = None
        self._temp_game_map = None

        # Рандомная задержка для десинхронизации поведения NPC
        import random
        self.action_delay = random.uniform(0.5, 2.0)  # Случайная задержка между действиями
        self.decision_variance = random.uniform(0.8, 1.2)  # Вариативность принятия решений

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

    def _allows_collisions(self, x, y, game_map):
        """
        Проверить, разрешены ли коллизии на данной клетке
        Коллизии разрешены в городах, деревнях, шахтах и школах магии

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если коллизии разрешены на этой клетке
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        if tile.has_location():
            location_type = tile.location.location_type
            # Коллизии разрешены в городах, деревнях, шахтах и школе магии
            return location_type in [LOCATION_CITY, LOCATION_VILLAGE,
                                    LOCATION_MINE, LOCATION_MAGIC_SCHOOL]

        return False

    def _is_position_occupied(self, x, y, all_npcs, player):
        """
        Проверить, занята ли клетка другим NPC или игроком

        Args:
            x: Координата X
            y: Координата Y
            all_npcs: Список всех NPC
            player: Объект игрока

        Returns:
            bool: True если клетка занята
        """
        # Проверяем игрока
        if player and hasattr(player, 'x') and hasattr(player, 'y'):
            if player.x == x and player.y == y:
                return True

        # Проверяем всех NPC
        if all_npcs:
            for npc in all_npcs:
                # Пропускаем самого себя
                if npc is self:
                    continue
                # Проверяем живых NPC на этой позиции
                if npc.is_alive and npc.x == x and npc.y == y:
                    return True

        return False

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли NPC двигаться на клетку (базовый метод)
        Учитывает коллизии с другими NPC и игроком

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
        if not tile.is_passable():
            return False

        # Если коллизии разрешены на этой клетке (города, деревни и т.д.),
        # то можно двигаться
        if self._allows_collisions(x, y, game_map):
            return True

        # Иначе проверяем, не занята ли клетка другим NPC/игроком
        # Используем временные переменные, установленные в update_ai
        all_npcs = self._temp_all_npcs if hasattr(self, '_temp_all_npcs') else None
        player = self._temp_player if hasattr(self, '_temp_player') else None

        if self._is_position_occupied(x, y, all_npcs, player):
            return False

        return True

    def _simplified_npc_combat(self, enemy):
        """
        Упрощенный бой между NPC - моментальный расчет победителя
        Рассчитывает исход боя мгновенно на основе характеристик

        Args:
            enemy: Враг для боя

        Returns:
            bool: True если враг повержен
        """
        import random

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

            return not enemy.is_alive
        else:
            # Враг побеждает
            power_ratio = enemy_power / self_power
            damage = int(enemy.get_total_damage() * power_ratio * random.uniform(0.8, 1.5))
            self.take_damage(damage)

            # Враг тоже получает урон, но меньше
            counter_damage = int(self.get_total_damage() * random.uniform(0.3, 0.7))
            enemy.take_damage(counter_damage)

            return False
