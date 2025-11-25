"""
AIContext - контекст для обновления AI NPC.

Этот класс инкапсулирует все данные, необходимые для обновления AI,
уменьшая количество параметров, передаваемых в метод update_ai().
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from game.map import GameMap
    from game.character import Player
    from game.npc.base import NPC
    from game.optimization import PerformanceOptimizer


class AIContext:
    """
    Контекст для обновления AI NPC.

    Содержит все данные, необходимые NPC для принятия решений:
    - Карта мира
    - Информация о игроке
    - Список всех NPC
    - Текущее время
    - Оптимизатор производительности
    """

    def __init__(
        self,
        game_map: 'GameMap',
        player: 'Player',
        current_hour: float,
        all_npcs: List['NPC'],
        performance_optimizer: Optional['PerformanceOptimizer'] = None,
        respawn_manager=None,
        game=None
    ):
        """
        Инициализация контекста AI.

        Args:
            game_map: Игровая карта
            player: Игрок
            current_hour: Текущий игровой час (0-24)
            all_npcs: Список всех NPC в игре
            performance_optimizer: Оптимизатор для определения необходимости обновления
            respawn_manager: Менеджер респавна NPC (для регистрации смертей в быстрых боях)
            game: Объект игры (для удаления мертвых NPC из списков)
        """
        self.game_map = game_map
        self.player = player
        self.current_hour = current_hour
        self.all_npcs = all_npcs
        self.optimizer = performance_optimizer
        self.respawn_manager = respawn_manager
        self.game = game

    # === Информация о игроке ===

    @property
    def player_x(self) -> int:
        """X координата игрока."""
        return self.player.x

    @property
    def player_y(self) -> int:
        """Y координата игрока."""
        return self.player.y

    @property
    def player_position(self) -> Tuple[int, int]:
        """Позиция игрока как кортеж (x, y)."""
        return (self.player.x, self.player.y)

    @property
    def player_level(self) -> int:
        """Уровень игрока."""
        return self.player.level

    # === Информация о времени ===

    def is_night(self) -> bool:
        """Проверить, ночь ли сейчас (22:00 - 06:00)."""
        return self.current_hour < 6 or self.current_hour >= 22

    def is_day(self) -> bool:
        """Проверить, день ли сейчас (06:00 - 22:00)."""
        return 6 <= self.current_hour < 22

    def is_morning(self) -> bool:
        """Проверить, утро ли (06:00 - 12:00)."""
        return 6 <= self.current_hour < 12

    def is_evening(self) -> bool:
        """Проверить, вечер ли (18:00 - 22:00)."""
        return 18 <= self.current_hour < 22

    # === Оптимизация ===

    def should_update(self, npc: 'NPC') -> bool:
        """
        Проверить, нужно ли обновлять AI данного NPC.

        Учитывает расстояние до игрока и настройки оптимизации.

        Args:
            npc: NPC для проверки

        Returns:
            True если AI нужно обновить
        """
        if self.optimizer is None:
            return True
        return self.optimizer.should_update_ai(npc, self.player_x, self.player_y)

    # === Поиск ===

    def get_nearby_npcs(self, x: int, y: int, radius: int) -> List['NPC']:
        """
        Получить NPC в радиусе от точки.

        Args:
            x: X координата центра
            y: Y координата центра
            radius: Радиус поиска

        Returns:
            Список NPC в радиусе
        """
        nearby = []
        for npc in self.all_npcs:
            if npc.x is None or npc.y is None:
                continue
            distance = abs(npc.x - x) + abs(npc.y - y)  # Manhattan distance
            if distance <= radius:
                nearby.append(npc)
        return nearby

    def get_hostile_npcs_nearby(self, x: int, y: int, radius: int) -> List['NPC']:
        """
        Получить враждебных NPC в радиусе.

        Args:
            x: X координата центра
            y: Y координата центра
            radius: Радиус поиска

        Returns:
            Список враждебных NPC в радиусе
        """
        from game.constants import RELATIONSHIP_HOSTILE
        return [
            npc for npc in self.get_nearby_npcs(x, y, radius)
            if getattr(npc, 'relationship', 0) <= RELATIONSHIP_HOSTILE
        ]

    def get_friendly_npcs_nearby(self, x: int, y: int, radius: int) -> List['NPC']:
        """
        Получить дружественных NPC в радиусе.

        Args:
            x: X координата центра
            y: Y координата центра
            radius: Радиус поиска

        Returns:
            Список дружественных NPC в радиусе
        """
        from game.constants import RELATIONSHIP_NEUTRAL
        return [
            npc for npc in self.get_nearby_npcs(x, y, radius)
            if getattr(npc, 'relationship', 0) >= RELATIONSHIP_NEUTRAL
        ]

    # === Карта ===

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Проверить, валидна ли позиция на карте.

        Args:
            x: X координата
            y: Y координата

        Returns:
            True если позиция валидна и проходима
        """
        return self.game_map.is_valid_position(x, y)

    def get_tile(self, x: int, y: int):
        """
        Получить тайл по координатам.

        Args:
            x: X координата
            y: Y координата

        Returns:
            Объект Tile или None
        """
        return self.game_map.get_tile(x, y)

    def distance_to_player(self, x: int, y: int) -> int:
        """
        Рассчитать Manhattan расстояние до игрока.

        Args:
            x: X координата точки
            y: Y координата точки

        Returns:
            Расстояние до игрока
        """
        return abs(x - self.player_x) + abs(y - self.player_y)

    def is_player_nearby(self, x: int, y: int, radius: int) -> bool:
        """
        Проверить, находится ли игрок в радиусе.

        Args:
            x: X координата центра
            y: Y координата центра
            radius: Радиус проверки

        Returns:
            True если игрок в радиусе
        """
        return self.distance_to_player(x, y) <= radius
