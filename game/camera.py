"""
Модуль для управления камерой
"""
from game.constants import TILE_SIZE


class Camera:
    """Класс для управления камерой"""

    def __init__(self, game):
        """
        Инициализация камеры

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.x = 0
        self.y = 0

    def update(self):
        """Обновление позиции камеры, чтобы следить за игроком"""
        # Вычисляем размер видимой области в тайлах
        tiles_x = self.game.window_width // TILE_SIZE
        tiles_y = (self.game.window_height - 100) // TILE_SIZE  # -100 для UI панели

        # Центрируем камеру на игроке
        self.x = self.game.player.x - tiles_x // 2
        self.y = self.game.player.y - tiles_y // 2

        # Ограничиваем камеру границами карты
        self.x = max(0, min(self.x, self.game.game_map.width - tiles_x))
        self.y = max(0, min(self.y, self.game.game_map.height - tiles_y))

    def get_visible_tiles(self):
        """
        Получить количество видимых тайлов

        Returns:
            tuple: (tiles_x, tiles_y)
        """
        tiles_x = self.game.window_width // TILE_SIZE + 1
        tiles_y = (self.game.window_height - 100) // TILE_SIZE + 1
        return tiles_x, tiles_y
