"""
Система тумана войны (Fog of War)
Оптимизировано для больших карт (500x500+)
"""
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
        # Кэш квадрата радиуса для оптимизации (избегаем sqrt)
        self._vision_radius_sq = VISION_RADIUS * VISION_RADIUS
        # Кэш текущей видимости (позиция игрока -> set видимых тайлов)
        self._visible_cache = set()
        self._cache_player_pos = None
        # Флаг для инвалидации кэша миникарты
        self._minimap_dirty = True
        # Счётчик новых исследованных тайлов
        self._newly_explored_count = 0

    def update_vision(self, player_x, player_y):
        """
        Обновить видимость тайлов вокруг игрока

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
        """
        # Обновляем кэш видимости
        new_pos = (player_x, player_y)
        if self._cache_player_pos != new_pos:
            self._visible_cache.clear()
            self._cache_player_pos = new_pos

            # Проходим по всем тайлам в радиусе видимости
            # Используем квадрат расстояния для оптимизации (без sqrt)
            radius_sq = self._vision_radius_sq
            for dy in range(-self.vision_radius, self.vision_radius + 1):
                for dx in range(-self.vision_radius, self.vision_radius + 1):
                    # Проверяем квадрат расстояния (без sqrt)
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= radius_sq:
                        tile_x = player_x + dx
                        tile_y = player_y + dy

                        # Добавляем в кэш видимости
                        self._visible_cache.add((tile_x, tile_y))

                        # Проверяем, что координаты валидны и помечаем как исследованные
                        if self.game_map.is_valid_position(tile_x, tile_y):
                            tile = self.game_map.get_tile(tile_x, tile_y)
                            if not tile.explored:
                                tile.explored = True
                                self._newly_explored_count += 1
                                self._minimap_dirty = True

    def is_visible(self, x, y, player_x, player_y):
        """
        Проверить, виден ли тайл игроку в данный момент
        Оптимизировано: использует квадрат расстояния вместо sqrt

        Args:
            x: Координата тайла X
            y: Координата тайла Y
            player_x: Позиция игрока X
            player_y: Позиция игрока Y

        Returns:
            bool: True если тайл виден
        """
        # Если кэш актуален, используем его
        if self._cache_player_pos == (player_x, player_y):
            return (x, y) in self._visible_cache

        # Иначе вычисляем напрямую (без sqrt)
        dx = x - player_x
        dy = y - player_y
        return (dx * dx + dy * dy) <= self._vision_radius_sq

    def is_minimap_dirty(self):
        """Проверить, нужно ли перерисовать миникарту"""
        return self._minimap_dirty

    def clear_minimap_dirty(self):
        """Сбросить флаг обновления миникарты"""
        self._minimap_dirty = False
        self._newly_explored_count = 0

    def mark_minimap_dirty(self):
        """Принудительно пометить миникарту для перерисовки (для читов и т.д.)"""
        self._minimap_dirty = True

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
