"""
Система тумана войны (Fog of War)
Оптимизировано для больших карт (500x500+)
"""
from game.constants import VISION_RADIUS
from game.config.config_loader import get_world_config


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
        # Кэш эффективного радиуса для текущего биома
        self._cache_effective_radius = VISION_RADIUS
        # Флаг для инвалидации кэша миникарты
        self._minimap_dirty = True
        # Счётчик новых исследованных тайлов
        self._newly_explored_count = 0

    def get_effective_vision_radius(self, player_x, player_y):
        """
        Получить эффективный радиус обзора с учётом биома

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y

        Returns:
            int: Эффективный радиус обзора (минимум 1)
        """
        if not self.game_map.is_valid_position(player_x, player_y):
            return self.vision_radius

        tile = self.game_map.get_tile(player_x, player_y)
        if not tile:
            return self.vision_radius

        world_config = get_world_config()
        vision_bonus = world_config.get_vision_bonus(tile.biome, default=0)

        # Применяем бонус к базовому радиусу, минимум 1
        effective_radius = max(1, self.vision_radius + vision_bonus)
        return effective_radius

    def update_vision(self, player_x, player_y):
        """
        Обновить видимость тайлов вокруг игрока

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
        """
        # Получаем эффективный радиус обзора с учётом биома
        effective_radius = self.get_effective_vision_radius(player_x, player_y)
        effective_radius_sq = effective_radius * effective_radius

        # Обновляем кэш видимости (включаем радиус в проверку для инвалидации)
        new_pos = (player_x, player_y)
        if self._cache_player_pos != new_pos or self._cache_effective_radius != effective_radius:
            self._visible_cache.clear()
            self._cache_player_pos = new_pos
            self._cache_effective_radius = effective_radius

            # Проходим по всем тайлам в радиусе видимости
            # Используем квадрат расстояния для оптимизации (без sqrt)
            for dy in range(-effective_radius, effective_radius + 1):
                for dx in range(-effective_radius, effective_radius + 1):
                    # Проверяем квадрат расстояния (без sqrt)
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= effective_radius_sq:
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
        # Получаем эффективный радиус обзора с учётом биома
        effective_radius = self.get_effective_vision_radius(player_x, player_y)

        # Если кэш актуален, используем его
        if self._cache_player_pos == (player_x, player_y) and self._cache_effective_radius == effective_radius:
            return (x, y) in self._visible_cache

        # Иначе вычисляем напрямую (без sqrt)
        dx = x - player_x
        dy = y - player_y
        effective_radius_sq = effective_radius * effective_radius
        return (dx * dx + dy * dy) <= effective_radius_sq

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
