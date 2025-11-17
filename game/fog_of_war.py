"""
Система тумана войны (Fog of War)
"""
import math
from game.constants import VISION_RADIUS


class FogOfWar:
    """Класс управления туманом войны"""

    def __init__(self, game_map):
        """
        Инициализация системы тумана войны

        Args:
            game_map: Объект игровой карты
        """
        self.game_map = game_map
        self.vision_radius = VISION_RADIUS

    def update_vision(self, player_x, player_y):
        """
        Обновить видимость тайлов вокруг игрока

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
        """
        # Проходим по всем тайлам в радиусе видимости
        for dy in range(-self.vision_radius, self.vision_radius + 1):
            for dx in range(-self.vision_radius, self.vision_radius + 1):
                # Вычисляем координаты тайла
                tile_x = player_x + dx
                tile_y = player_y + dy

                # Проверяем, находится ли тайл в радиусе видимости (круговая область)
                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= self.vision_radius:
                    # Проверяем, что координаты валидны
                    if self.game_map.is_valid_position(tile_x, tile_y):
                        tile = self.game_map.get_tile(tile_x, tile_y)
                        tile.explored = True

    def is_visible(self, x, y, player_x, player_y):
        """
        Проверить, виден ли тайл игроку в данный момент

        Args:
            x: Координата тайла X
            y: Координата тайла Y
            player_x: Позиция игрока X
            player_y: Позиция игрока Y

        Returns:
            bool: True если тайл виден
        """
        dx = x - player_x
        dy = y - player_y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= self.vision_radius

    def is_explored(self, x, y):
        """
        Проверить, был ли тайл исследован

        Args:
            x: Координата тайла X
            y: Координата тайла Y

        Returns:
            bool: True если тайл был исследован
        """
        if self.game_map.is_valid_position(x, y):
            tile = self.game_map.get_tile(x, y)
            return tile.explored
        return False
