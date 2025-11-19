"""
Базовый класс NPC (неигровых персонажей)
"""
from collections import deque
from game.character import Character
from game.inventory import Inventory
from game.constants import (
    RELATIONSHIP_NEUTRAL, NPC_RELATIONSHIPS, RELATIONSHIP_HOSTILE
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

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли NPC двигаться на клетку (базовый метод)

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
