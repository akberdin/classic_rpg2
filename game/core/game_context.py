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

    @nearby_npc.setter
    def nearby_npc(self, value):
        """Установить ближайшего NPC."""
        self._game.nearby_npc = value

    @property
    def running(self) -> bool:
        """Проверить, работает ли игра."""
        return getattr(self._game, 'running', True)

    @running.setter
    def running(self, value: bool):
        """Установить флаг работы игры."""
        self._game.running = value

    # === Флаги меню (с сеттерами) ===

    @property
    def inventory_menu_open(self) -> bool:
        return getattr(self._game, 'inventory_menu_open', False)

    @inventory_menu_open.setter
    def inventory_menu_open(self, value: bool):
        self._game.inventory_menu_open = value

    @property
    def trade_menu_open(self) -> bool:
        return getattr(self._game, 'trade_menu_open', False)

    @trade_menu_open.setter
    def trade_menu_open(self, value: bool):
        self._game.trade_menu_open = value

    @property
    def character_menu_open(self) -> bool:
        return getattr(self._game, 'character_menu_open', False)

    @character_menu_open.setter
    def character_menu_open(self, value: bool):
        self._game.character_menu_open = value

    @property
    def skill_book_menu_open(self) -> bool:
        return getattr(self._game, 'skill_book_menu_open', False)

    @skill_book_menu_open.setter
    def skill_book_menu_open(self, value: bool):
        self._game.skill_book_menu_open = value

    @property
    def interaction_menu_open(self) -> bool:
        return getattr(self._game, 'interaction_menu_open', False)

    @interaction_menu_open.setter
    def interaction_menu_open(self, value: bool):
        self._game.interaction_menu_open = value

    @property
    def quest_window_open(self) -> bool:
        return getattr(self._game, 'quest_window_open', False)

    @quest_window_open.setter
    def quest_window_open(self, value: bool):
        self._game.quest_window_open = value

    @property
    def event_window_open(self) -> bool:
        return getattr(self._game, 'event_window_open', False)

    @event_window_open.setter
    def event_window_open(self, value: bool):
        self._game.event_window_open = value

    @property
    def loot_window_open(self) -> bool:
        return getattr(self._game, 'loot_window_open', False)

    @loot_window_open.setter
    def loot_window_open(self, value: bool):
        self._game.loot_window_open = value

    @property
    def resource_collection_window_open(self) -> bool:
        return getattr(self._game, 'resource_collection_window_open', False)

    @resource_collection_window_open.setter
    def resource_collection_window_open(self, value: bool):
        self._game.resource_collection_window_open = value

    @property
    def cheat_menu_open(self) -> bool:
        return getattr(self._game, 'cheat_menu_open', False)

    @cheat_menu_open.setter
    def cheat_menu_open(self, value: bool):
        self._game.cheat_menu_open = value

    @property
    def settlement_menu_open(self) -> bool:
        return getattr(self._game, 'settlement_menu_open', False)

    @settlement_menu_open.setter
    def settlement_menu_open(self, value: bool):
        self._game.settlement_menu_open = value

    @property
    def inquiry_menu_open(self) -> bool:
        return getattr(self._game, 'inquiry_menu_open', False)

    @inquiry_menu_open.setter
    def inquiry_menu_open(self, value: bool):
        self._game.inquiry_menu_open = value

    @property
    def inquiry_response_open(self) -> bool:
        return getattr(self._game, 'inquiry_response_open', False)

    @inquiry_response_open.setter
    def inquiry_response_open(self, value: bool):
        self._game.inquiry_response_open = value

    @property
    def combat_mode_menu_open(self) -> bool:
        return getattr(self._game, 'combat_mode_menu_open', False)

    @combat_mode_menu_open.setter
    def combat_mode_menu_open(self, value: bool):
        self._game.combat_mode_menu_open = value

    @property
    def crafting_window_open(self) -> bool:
        return getattr(self._game, 'crafting_window_open', False)

    @crafting_window_open.setter
    def crafting_window_open(self, value: bool):
        self._game.crafting_window_open = value

    @property
    def companion_window_open(self) -> bool:
        return getattr(self._game, 'companion_window_open', False)

    @companion_window_open.setter
    def companion_window_open(self, value: bool):
        self._game.companion_window_open = value

    # === UI окна ===

    @property
    def inventory_window(self):
        """Получить окно инвентаря."""
        return getattr(self._game, 'inventory_window', None)

    @property
    def trade_window(self):
        """Получить окно торговли."""
        return getattr(self._game, 'trade_window', None)

    @property
    def character_window(self):
        """Получить окно персонажа."""
        return getattr(self._game, 'character_window', None)

    @property
    def skill_book_window(self):
        """Получить окно книги умений."""
        return getattr(self._game, 'skill_book_window', None)

    @property
    def quest_window(self):
        """Получить окно квестов."""
        return getattr(self._game, 'quest_window', None)

    @property
    def help_window(self):
        """Получить окно помощи."""
        return getattr(self._game, 'help_window', None)

    @property
    def cheat_menu_window(self):
        """Получить окно чит-меню."""
        return getattr(self._game, 'cheat_menu_window', None)

    @property
    def random_event_window(self):
        """Получить окно случайных событий."""
        return getattr(self._game, 'random_event_window', None)

    @property
    def loot_window(self):
        """Получить окно лута."""
        return getattr(self._game, 'loot_window', None)

    @property
    def resource_collection_window(self):
        """Получить окно сбора ресурсов."""
        return getattr(self._game, 'resource_collection_window', None)

    @property
    def settlement_menu_window(self):
        """Получить окно меню города/деревни."""
        return getattr(self._game, 'settlement_menu_window', None)

    @property
    def inquiry_menu_window(self):
        """Получить окно расспроса жителей."""
        return getattr(self._game, 'inquiry_menu_window', None)

    @property
    def inquiry_response_window(self):
        """Получить окно ответа на вопрос."""
        return getattr(self._game, 'inquiry_response_window', None)

    @property
    def crafting_window(self):
        """Получить окно крафта."""
        return getattr(self._game, 'crafting_window', None)

    @property
    def companion_window(self):
        """Получить окно спутников."""
        return getattr(self._game, 'companion_window', None)

    # === Дополнительные системы ===

    @property
    def game_time(self):
        """Получить систему времени."""
        return getattr(self._game, 'game_time', None)

    @property
    def weather_system(self):
        """Получить систему погоды."""
        return getattr(self._game, 'weather_system', None)

    @property
    def killstreak_system(self):
        """Получить систему серий убийств."""
        return getattr(self._game, 'killstreak_system', None)

    @property
    def sprite_manager(self):
        """Получить менеджер спрайтов."""
        return getattr(self._game, 'sprite_manager', None)

    @property
    def random_event_system(self):
        """Получить систему случайных событий."""
        return getattr(self._game, 'random_event_system', None)

    @property
    def crafting_system(self):
        """Получить систему крафта."""
        return getattr(self._game, 'crafting_system', None)

    # === Списки NPC (через NPCManager) ===

    @property
    def guards(self):
        """Список стражников."""
        return getattr(self._game, 'guards', [])

    @property
    def merchants(self):
        """Список торговцев."""
        return getattr(self._game, 'merchants', [])

    @property
    def mages(self):
        """Список магов."""
        return getattr(self._game, 'mages', [])

    @property
    def bandits(self):
        """Список бандитов."""
        return getattr(self._game, 'bandits', [])

    @property
    def miners(self):
        """Список шахтёров."""
        return getattr(self._game, 'miners', [])

    @property
    def undead(self):
        """Список нежити."""
        return getattr(self._game, 'undead', [])

    @property
    def alchemists(self):
        """Список алхимиков."""
        return getattr(self._game, 'alchemists', [])

    @property
    def hunters(self):
        """Список охотников."""
        return getattr(self._game, 'hunters', [])

    @property
    def necromancers(self):
        """Список некромантов."""
        return getattr(self._game, 'necromancers', [])

    @property
    def animals(self):
        """Список животных."""
        return getattr(self._game, 'animals', [])

    # === Методы-делегаты ===

    def start_combat(self, npc, tactical=False) -> None:
        """
        Начать бой с NPC.

        Args:
            npc: Враг для боя
            tactical: Использовать тактический режим боя (по умолчанию False)
        """
        if hasattr(self._game, '_start_combat'):
            self._game._start_combat(npc, tactical=tactical)

    def check_npc_nearby(self) -> None:
        """Проверить наличие NPC поблизости."""
        if hasattr(self._game, '_check_npc_nearby'):
            self._game._check_npc_nearby()

    def collect_resources(self) -> None:
        """Собрать ресурсы."""
        if hasattr(self._game, '_collect_resources'):
            self._game._collect_resources()

    def open_quest_window(self, location=None) -> None:
        """Открыть окно квестов."""
        if location and hasattr(self._game, 'open_quest_window'):
            self._game.open_quest_window(location)
        elif hasattr(self._game, 'open_quest_window_anywhere'):
            self._game.open_quest_window_anywhere()

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
