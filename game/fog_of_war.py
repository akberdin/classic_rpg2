"""
Система тумана войны (Fog of War)
Оптимизировано для больших карт (500x500+)
"""
from game.constants import VISION_RADIUS
from game.config.config_loader import get_world_config


class FogOfWar:
    """Класс управления туманом войны"""

    # Биомы с возвышенностью (хороший обзор в лес)
    ELEVATED_BIOMES = {'hills', 'mountain'}
    # Биом леса
    FOREST_BIOME = 'forest'
    # Часы ночи (с 21:00 до 6:00)
    NIGHT_START_HOUR = 21
    NIGHT_END_HOUR = 6

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
        # Кэш биома игрока для проверки видимости в лес
        self._cache_player_biome = None
        # Кэш времени суток для инвалидации
        self._cache_is_night = False
        # Текущий час для расчёта ночи
        self._current_hour = 6
        # Флаг для инвалидации кэша миникарты
        self._minimap_dirty = True
        # Счётчик новых исследованных тайлов
        self._newly_explored_count = 0

    def set_current_hour(self, hour):
        """
        Установить текущий час для расчёта ночного режима

        Args:
            hour: Текущий час (0-23, может быть float)
        """
        self._current_hour = int(hour) % 24

    def is_night(self):
        """
        Проверить, ночь ли сейчас

        Returns:
            bool: True если ночь (21:00 - 6:00)
        """
        return self._current_hour >= self.NIGHT_START_HOUR or self._current_hour < self.NIGHT_END_HOUR

    def get_effective_vision_radius(self, player_x, player_y):
        """
        Получить эффективный радиус обзора с учётом биома и времени суток

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y

        Returns:
            int: Эффективный радиус обзора (минимум 1)
        """
        if not self.game_map.is_valid_position(player_x, player_y):
            base_radius = self.vision_radius
        else:
            tile = self.game_map.get_tile(player_x, player_y)
            if not tile:
                base_radius = self.vision_radius
            else:
                world_config = get_world_config()
                vision_bonus = world_config.get_vision_bonus(tile.biome, default=0)
                base_radius = self.vision_radius + vision_bonus

        # Ночью радиус уменьшается в 2 раза
        if self.is_night():
            base_radius = base_radius // 2

        # Минимум 1 клетка
        return max(1, base_radius)

    def _is_tile_visible_with_forest_check(self, tile_x, tile_y, player_x, player_y,
                                            player_biome, effective_radius_sq):
        """
        Проверить видимость клетки с учётом ограничения видимости в лес

        Args:
            tile_x, tile_y: Координаты проверяемой клетки
            player_x, player_y: Координаты игрока
            player_biome: Биом клетки игрока
            effective_radius_sq: Квадрат эффективного радиуса обзора

        Returns:
            bool: True если клетка видна
        """
        dx = tile_x - player_x
        dy = tile_y - player_y
        dist_sq = dx * dx + dy * dy
        # Расстояние Чебышёва для проверки "квадратного" радиуса (включает диагонали)
        chebyshev_dist = max(abs(dx), abs(dy))

        # Специальная обработка для игрока в лесу - используем расстояние Чебышёва
        # чтобы видеть все 8 соседних клеток, а не только 4 (крест)
        if player_biome == self.FOREST_BIOME:
            # В лесу радиус 1 означает все 8 соседних клеток
            if chebyshev_dist > 1:
                return False
            return True

        # Для остальных биомов - стандартная проверка Евклидова расстояния
        if dist_sq > effective_radius_sq:
            return False

        # Получаем биом целевой клетки
        target_tile = self.game_map.get_tile(tile_x, tile_y)
        if not target_tile:
            return False

        target_biome = target_tile.biome

        # Если целевая клетка - лес
        if target_biome == self.FOREST_BIOME:
            # Если игрок на возвышенности - видит лес нормально
            if player_biome in self.ELEVATED_BIOMES:
                return True

            # Иначе - видимость в лес ограничена 1 клеткой
            return chebyshev_dist <= 1

        # Для не-лесных клеток - стандартная проверка
        return True

    def update_vision(self, player_x, player_y):
        """
        Обновить видимость тайлов вокруг игрока

        Args:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
        """
        # Получаем биом позиции игрока
        player_tile = self.game_map.get_tile(player_x, player_y)
        player_biome = player_tile.biome if player_tile else 'plains'

        # Получаем эффективный радиус обзора с учётом биома и времени суток
        effective_radius = self.get_effective_vision_radius(player_x, player_y)
        effective_radius_sq = effective_radius * effective_radius
        current_is_night = self.is_night()

        # Обновляем кэш видимости (включаем радиус, биом и ночь в проверку для инвалидации)
        new_pos = (player_x, player_y)
        if (self._cache_player_pos != new_pos or
            self._cache_effective_radius != effective_radius or
            self._cache_player_biome != player_biome or
            self._cache_is_night != current_is_night):

            self._visible_cache.clear()
            self._cache_player_pos = new_pos
            self._cache_effective_radius = effective_radius
            self._cache_player_biome = player_biome
            self._cache_is_night = current_is_night

            # Проходим по всем тайлам в радиусе видимости
            for dy in range(-effective_radius, effective_radius + 1):
                for dx in range(-effective_radius, effective_radius + 1):
                    tile_x = player_x + dx
                    tile_y = player_y + dy

                    # Проверяем видимость с учётом леса
                    if self._is_tile_visible_with_forest_check(
                        tile_x, tile_y, player_x, player_y,
                        player_biome, effective_radius_sq
                    ):
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

        Args:
            x: Координата тайла X
            y: Координата тайла Y
            player_x: Позиция игрока X
            player_y: Позиция игрока Y

        Returns:
            bool: True если тайл виден
        """
        # Получаем данные для проверки
        player_tile = self.game_map.get_tile(player_x, player_y)
        player_biome = player_tile.biome if player_tile else 'plains'
        effective_radius = self.get_effective_vision_radius(player_x, player_y)
        current_is_night = self.is_night()

        # Если кэш актуален, используем его
        if (self._cache_player_pos == (player_x, player_y) and
            self._cache_effective_radius == effective_radius and
            self._cache_player_biome == player_biome and
            self._cache_is_night == current_is_night):
            return (x, y) in self._visible_cache

        # Иначе вычисляем напрямую
        effective_radius_sq = effective_radius * effective_radius
        return self._is_tile_visible_with_forest_check(
            x, y, player_x, player_y, player_biome, effective_radius_sq
        )

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
