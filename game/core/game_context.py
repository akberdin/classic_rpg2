"""
GameContext - контекст игры для передачи зависимостей между модулями.

Этот класс обеспечивает единую точку доступа к игровым данным,
уменьшая связанность между модулями и количество передаваемых параметров.
"""

from typing import TYPE_CHECKING, Tuple, Optional, Any

if TYPE_CHECKING:
    from game.engine import Game
    from game.character import Player
    from game.map import GameMap


class GameContext:
    """
    Контекст игры для передачи зависимостей.

    Предоставляет единый интерфейс для доступа к игровым данным,
    скрывая детали реализации Game класса.
    """

    def __init__(self, game: 'Game'):
        """
        Инициализация контекста.

        Args:
            game: Экземпляр главного класса Game
        """
        self._game = game

    # === Основные свойства ===

    @property
    def player(self) -> 'Player':
        """Получить игрока."""
        return self._game.player

    @property
    def game_map(self) -> 'GameMap':
        """Получить игровую карту."""
        return self._game.game_map

    @property
    def current_hour(self) -> float:
        """Получить текущий игровой час."""
        if hasattr(self._game, 'game_time') and self._game.game_time:
            return self._game.game_time.game_hour
        return 12.0  # Значение по умолчанию

    @property
    def current_day(self) -> int:
        """Получить текущий игровой день."""
        if hasattr(self._game, 'game_time') and self._game.game_time:
            return self._game.game_time.game_day
        return 1

    # === Экран и камера ===

    @property
    def screen(self):
        """Получить pygame экран."""
        return self._game.screen

    @property
    def screen_size(self) -> Tuple[int, int]:
        """Получить размер экрана (ширина, высота)."""
        return (self._game.window_width, self._game.window_height)

    @property
    def window_width(self) -> int:
        """Получить ширину окна."""
        return self._game.window_width

    @property
    def window_height(self) -> int:
        """Получить высоту окна."""
        return self._game.window_height

    @property
    def camera_position(self) -> Tuple[int, int]:
        """Получить позицию камеры."""
        if hasattr(self._game, 'camera') and self._game.camera:
            return (self._game.camera.x, self._game.camera.y)
        return (0, 0)

    @property
    def camera(self):
        """Получить объект камеры."""
        return self._game.camera

    # === UI элементы ===

    @property
    def ui_scaler(self):
        """Получить масштабировщик UI."""
        return self._game.ui_scaler

    @property
    def font(self):
        """Получить основной шрифт."""
        return self._game.font

    @property
    def info_font(self):
        """Получить информационный шрифт."""
        return getattr(self._game, 'info_font', self._game.font)

    # === Игровые системы ===

    @property
    def fog_of_war(self):
        """Получить систему тумана войны."""
        return self._game.fog_of_war

    @property
    def respawn_manager(self):
        """Получить менеджер респавна."""
        return getattr(self._game, 'respawn_manager', None)

    @property
    def quest_manager(self):
        """Получить менеджер квестов."""
        return getattr(self._game, 'quest_manager', None)

    @property
    def achievement_manager(self):
        """Получить менеджер достижений."""
        return getattr(self._game, 'achievement_manager', None)

    @property
    def performance_optimizer(self):
        """Получить оптимизатор производительности."""
        return getattr(self._game, 'performance_optimizer', None)

    # === Читы и отладка ===

    def is_cheat_enabled(self, cheat_name: str) -> bool:
        """
        Проверить, включён ли чит.

        Args:
            cheat_name: Имя чита (godmode, reveal_map и т.д.)

        Returns:
            True если чит включён, иначе False
        """
        if not hasattr(self._game, 'cheat_menu_window'):
            return False
        cheats = getattr(self._game.cheat_menu_window, 'cheats', {})
        cheat_data = cheats.get(cheat_name, {})
        return cheat_data.get('enabled', False)

    def is_godmode_enabled(self) -> bool:
        """Проверить, включён ли режим бога."""
        return self.is_cheat_enabled('godmode')

    def is_map_revealed(self) -> bool:
        """Проверить, раскрыта ли вся карта."""
        return self.is_cheat_enabled('reveal_map')

    # === Состояние игры ===

    @property
    def in_combat(self) -> bool:
        """Проверить, идёт ли бой."""
        return getattr(self._game, 'in_combat', False)

    @property
    def combat_system(self):
        """Получить систему боя."""
        return getattr(self._game, 'combat_system', None)

    @property
    def nearby_npc(self):
        """Получить ближайшего NPC."""
        return getattr(self._game, 'nearby_npc', None)

    # === Вспомогательные методы ===

    def get_player_position(self) -> Tuple[int, int]:
        """Получить позицию игрока."""
        return (self.player.x, self.player.y)

    def get_tile_at_player(self):
        """Получить тайл под игроком."""
        return self.game_map.get_tile(self.player.x, self.player.y)

    def is_position_visible(self, x: int, y: int) -> bool:
        """
        Проверить, видна ли позиция.

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            True если позиция видна
        """
        if self.is_map_revealed():
            return True
        if self.fog_of_war:
            return self.fog_of_war.is_visible(x, y, self.player.x, self.player.y)
        return True

    def is_position_explored(self, x: int, y: int) -> bool:
        """
        Проверить, исследована ли позиция.

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            True если позиция исследована
        """
        if self.is_map_revealed():
            return True
        if self.fog_of_war:
            return self.fog_of_war.is_explored(x, y)
        return True
