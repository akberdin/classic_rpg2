"""
Рендерер для подземелий и шахт
"""
import pygame
from typing import Optional

from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.tiles import DungeonTileType, DUNGEON_TILE_COLORS


class DungeonRenderer:
    """Рендерер для отображения подземелий"""

    def __init__(self, screen, tile_size: int, ui_scaler, sprite_manager=None):
        """
        Инициализация рендерера

        Args:
            screen: Экран pygame
            tile_size: Размер тайла в пикселях
            ui_scaler: Масштабировщик UI
            sprite_manager: Менеджер спрайтов (опционально)
        """
        self.screen = screen
        self.tile_size = tile_size
        self.ui_scaler = ui_scaler
        self.sprite_manager = sprite_manager

        # Шрифты
        font_size = max(12, tile_size // 3)
        self.font = pygame.font.Font(None, font_size)
        self.small_font = pygame.font.Font(None, max(10, font_size - 4))

        # Цвета
        self.fog_color = (10, 10, 15)  # Неисследованные клетки
        self.dim_factor = 0.5  # Затемнение исследованных, но невидимых клеток

        # Спецсимволы для отображения
        self.tile_symbols = {
            DungeonTileType.ENTRANCE: "E",
            DungeonTileType.EXIT: "X",
            DungeonTileType.TRAP: "^",
            DungeonTileType.TRAP_TRIGGERED: "v",
            DungeonTileType.STASH: "$",
            DungeonTileType.STASH_LOOTED: "_",
            DungeonTileType.ALTAR: "A",
            DungeonTileType.BONES: "b",
            DungeonTileType.ORE_VEIN: "o",
        }

    def render_dungeon(self, dungeon: DungeonMap, player, camera_x: int, camera_y: int,
                       viewport_width: int, viewport_height: int, selected_target=None):
        """
        Отрисовка подземелья

        Args:
            dungeon: Карта подземелья
            player: Объект игрока
            camera_x: Смещение камеры по X (в тайлах)
            camera_y: Смещение камеры по Y (в тайлах)
            viewport_width: Ширина области отрисовки (в пикселях)
            viewport_height: Высота области отрисовки (в пикселях)
            selected_target: Выбранная цель (NPC) для отображения выделения
        """
        # Вычисляем количество видимых тайлов
        tiles_x = viewport_width // self.tile_size + 2
        tiles_y = viewport_height // self.tile_size + 2

        # Центрируем камеру на игроке
        start_x = player.x - tiles_x // 2
        start_y = player.y - tiles_y // 2

        # Отрисовываем тайлы
        for screen_y in range(tiles_y):
            for screen_x in range(tiles_x):
                map_x = start_x + screen_x
                map_y = start_y + screen_y

                tile = dungeon.get_tile(map_x, map_y)

                # Позиция на экране
                pixel_x = screen_x * self.tile_size
                pixel_y = screen_y * self.tile_size

                if tile is None:
                    # За пределами карты - черный
                    pygame.draw.rect(self.screen, (0, 0, 0),
                                    (pixel_x, pixel_y, self.tile_size, self.tile_size))
                    continue

                if not tile.explored:
                    # Неисследованная клетка
                    pygame.draw.rect(self.screen, self.fog_color,
                                    (pixel_x, pixel_y, self.tile_size, self.tile_size))
                    continue

                # Получаем цвет клетки
                color = tile.get_color()

                # Если клетка не видна сейчас, затемняем
                if not tile.visible:
                    color = tuple(int(c * self.dim_factor) for c in color)

                # Рисуем клетку
                pygame.draw.rect(self.screen, color,
                                (pixel_x, pixel_y, self.tile_size, self.tile_size))

                # Добавляем сетку для видимых клеток
                if tile.visible:
                    grid_color = tuple(min(255, c + 20) for c in color)
                    pygame.draw.rect(self.screen, grid_color,
                                    (pixel_x, pixel_y, self.tile_size, self.tile_size), 1)

                # Рисуем специальные символы
                if tile.visible and tile.tile_type in self.tile_symbols:
                    symbol = self.tile_symbols[tile.tile_type]
                    symbol_color = self._get_symbol_color(tile.tile_type)
                    symbol_surface = self.font.render(symbol, True, symbol_color)
                    sym_x = pixel_x + (self.tile_size - symbol_surface.get_width()) // 2
                    sym_y = pixel_y + (self.tile_size - symbol_surface.get_height()) // 2
                    self.screen.blit(symbol_surface, (sym_x, sym_y))

        # Отрисовываем NPC
        self._render_npcs(dungeon, player, start_x, start_y, tiles_x, tiles_y, selected_target)

        # Отрисовываем игрока
        self._render_player(player, start_x, start_y)

    def _get_symbol_color(self, tile_type: DungeonTileType) -> tuple:
        """Получить цвет символа для типа клетки"""
        colors = {
            DungeonTileType.ENTRANCE: (100, 255, 100),    # Зеленый
            DungeonTileType.EXIT: (255, 100, 100),        # Красный
            DungeonTileType.TRAP: (255, 200, 100),        # Оранжевый
            DungeonTileType.TRAP_TRIGGERED: (150, 100, 100),
            DungeonTileType.STASH: (255, 255, 100),       # Желтый
            DungeonTileType.STASH_LOOTED: (150, 150, 100),
            DungeonTileType.ALTAR: (200, 100, 255),       # Фиолетовый
            DungeonTileType.BONES: (220, 220, 200),
            DungeonTileType.ORE_VEIN: (200, 150, 100),
        }
        return colors.get(tile_type, (255, 255, 255))

    def _render_npcs(self, dungeon: DungeonMap, player, start_x: int, start_y: int,
                     tiles_x: int, tiles_y: int, selected_target=None):
        """Отрисовка NPC в подземелье"""
        for npc in dungeon.npcs:
            if not npc.is_alive:
                continue

            # Проверяем, в пределах ли экрана
            screen_x = npc.x - start_x
            screen_y = npc.y - start_y

            if not (0 <= screen_x < tiles_x and 0 <= screen_y < tiles_y):
                continue

            # Проверяем видимость
            tile = dungeon.get_tile(npc.x, npc.y)
            if tile is None or not tile.visible:
                continue

            # Позиция на экране
            pixel_x = screen_x * self.tile_size
            pixel_y = screen_y * self.tile_size

            # Проверяем, выделен ли NPC
            is_selected = (selected_target is not None and selected_target == npc)

            # Рисуем индикатор выделения (перед спрайтом)
            if is_selected:
                self._render_selection_indicator(pixel_x, pixel_y)

            # Функция отрисовки по умолчанию
            def draw_npc_default():
                center_x = pixel_x + self.tile_size // 2
                center_y = pixel_y + self.tile_size // 2
                radius = self.tile_size // 3

                # Цвет зависит от типа NPC
                npc_color = (128, 128, 160)  # Серо-синий для нежити
                if hasattr(npc, 'npc_type'):
                    if npc.npc_type == "undead":
                        npc_color = (100, 100, 130)

                pygame.draw.circle(self.screen, npc_color, (center_x, center_y), radius)
                pygame.draw.circle(self.screen, (200, 200, 220), (center_x, center_y), radius, 2)

            # Используем спрайт если доступен
            npc_type = getattr(npc, 'npc_type', 'undead')
            npc_level = getattr(npc, 'level', 1)

            if self.sprite_manager:
                self.sprite_manager.render_npc(
                    self.screen, npc_type, pixel_x, pixel_y,
                    draw_npc_default, npc_level
                )
            else:
                draw_npc_default()

            # Рисуем шкалу здоровья над NPC
            self._render_npc_health_bar(npc, pixel_x, pixel_y)

    def _render_selection_indicator(self, pixel_x: int, pixel_y: int):
        """Рисуем индикатор выделения вокруг клетки"""
        # Красная рамка вокруг выделенного врага
        pygame.draw.rect(self.screen, (255, 80, 80),
                        (pixel_x - 2, pixel_y - 2,
                         self.tile_size + 4, self.tile_size + 4), 3)

        # Уголки для красоты
        corner_len = 8
        corner_color = (255, 200, 100)
        # Верхний левый
        pygame.draw.line(self.screen, corner_color, (pixel_x, pixel_y), (pixel_x + corner_len, pixel_y), 2)
        pygame.draw.line(self.screen, corner_color, (pixel_x, pixel_y), (pixel_x, pixel_y + corner_len), 2)
        # Верхний правый
        pygame.draw.line(self.screen, corner_color, (pixel_x + self.tile_size, pixel_y),
                        (pixel_x + self.tile_size - corner_len, pixel_y), 2)
        pygame.draw.line(self.screen, corner_color, (pixel_x + self.tile_size, pixel_y),
                        (pixel_x + self.tile_size, pixel_y + corner_len), 2)
        # Нижний левый
        pygame.draw.line(self.screen, corner_color, (pixel_x, pixel_y + self.tile_size),
                        (pixel_x + corner_len, pixel_y + self.tile_size), 2)
        pygame.draw.line(self.screen, corner_color, (pixel_x, pixel_y + self.tile_size),
                        (pixel_x, pixel_y + self.tile_size - corner_len), 2)
        # Нижний правый
        pygame.draw.line(self.screen, corner_color, (pixel_x + self.tile_size, pixel_y + self.tile_size),
                        (pixel_x + self.tile_size - corner_len, pixel_y + self.tile_size), 2)
        pygame.draw.line(self.screen, corner_color, (pixel_x + self.tile_size, pixel_y + self.tile_size),
                        (pixel_x + self.tile_size, pixel_y + self.tile_size - corner_len), 2)

    def _render_npc_health_bar(self, npc, pixel_x: int, pixel_y: int):
        """Рисуем шкалу здоровья над NPC"""
        hp = getattr(npc, 'health', 0)  # Используем health вместо hp
        max_hp = getattr(npc, 'max_health', 1)  # Используем max_health вместо max_hp
        if max_hp <= 0:
            max_hp = 1

        # Размеры шкалы
        bar_width = self.tile_size - 4
        bar_height = 5
        bar_x = pixel_x + 2
        bar_y = pixel_y - bar_height - 3

        # Фон шкалы
        pygame.draw.rect(self.screen, (40, 40, 40),
                        (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))

        # Заполнение шкалы
        fill_width = int(bar_width * (hp / max_hp))

        # Цвет зависит от процента HP
        hp_percent = hp / max_hp
        if hp_percent > 0.6:
            bar_color = (80, 200, 80)  # Зеленый
        elif hp_percent > 0.3:
            bar_color = (220, 180, 50)  # Желтый
        else:
            bar_color = (200, 60, 60)  # Красный

        if fill_width > 0:
            pygame.draw.rect(self.screen, bar_color,
                            (bar_x, bar_y, fill_width, bar_height))

        # Рамка
        pygame.draw.rect(self.screen, (100, 100, 100),
                        (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 1)

        # Уровень под шкалой HP
        level = getattr(npc, 'level', 1)
        level_text = f"Lv{level}"
        level_surface = self.small_font.render(level_text, True, (200, 200, 200))
        level_x = pixel_x + (self.tile_size - level_surface.get_width()) // 2
        level_y = pixel_y + self.tile_size + 1
        self.screen.blit(level_surface, (level_x, level_y))

    def _render_player(self, player, start_x: int, start_y: int):
        """Отрисовка игрока"""
        screen_x = player.x - start_x
        screen_y = player.y - start_y

        pixel_x = screen_x * self.tile_size
        pixel_y = screen_y * self.tile_size

        # Функция отрисовки по умолчанию (геометрическая фигура)
        def draw_player_default():
            center_x = pixel_x + self.tile_size // 2
            center_y = pixel_y + self.tile_size // 2
            radius = self.tile_size // 3
            pygame.draw.circle(self.screen, (255, 215, 0), (center_x, center_y), radius)
            pygame.draw.circle(self.screen, (255, 255, 200), (center_x, center_y), radius, 2)

        # Используем спрайт если доступен
        if self.sprite_manager:
            self.sprite_manager.render_npc(
                self.screen, 'player', pixel_x, pixel_y,
                draw_player_default, player.level
            )
        else:
            draw_player_default()

    def render_minimap(self, dungeon: DungeonMap, player, x: int, y: int,
                       width: int, height: int):
        """
        Отрисовка мини-карты подземелья

        Args:
            dungeon: Карта подземелья
            player: Объект игрока
            x, y: Позиция мини-карты на экране
            width, height: Размеры мини-карты
        """
        # Размер одного пикселя мини-карты
        pixel_w = max(1, width // dungeon.width)
        pixel_h = max(1, height // dungeon.height)

        # Фон мини-карты
        pygame.draw.rect(self.screen, (20, 20, 25), (x, y, width, height))
        pygame.draw.rect(self.screen, (80, 80, 100), (x, y, width, height), 1)

        # Рисуем тайлы
        for ty in range(dungeon.height):
            for tx in range(dungeon.width):
                tile = dungeon.get_tile(tx, ty)

                if tile is None or not tile.explored:
                    continue

                px = x + tx * pixel_w
                py = y + ty * pixel_h

                # Упрощенные цвета для мини-карты
                if tile.tile_type == DungeonTileType.WALL:
                    color = (40, 40, 45)
                elif tile.tile_type in [DungeonTileType.ENTRANCE, DungeonTileType.EXIT]:
                    color = (100, 200, 100) if tile.tile_type == DungeonTileType.ENTRANCE else (200, 100, 100)
                else:
                    color = (80, 80, 90)

                if not tile.visible:
                    color = tuple(int(c * 0.6) for c in color)

                pygame.draw.rect(self.screen, color, (px, py, pixel_w, pixel_h))

        # Рисуем игрока
        player_px = x + player.x * pixel_w
        player_py = y + player.y * pixel_h
        pygame.draw.rect(self.screen, (255, 215, 0),
                        (player_px, player_py, max(2, pixel_w), max(2, pixel_h)))

    def render_hud(self, dungeon: DungeonMap, player, font):
        """
        Отрисовка HUD для подземелья

        Args:
            dungeon: Карта подземелья
            player: Объект игрока
            font: Шрифт для текста
        """
        # Информация о подземелье в верхнем левом углу
        padding = 10
        line_height = 25

        # Фон панели
        panel_width = 300
        panel_height = 100
        pygame.draw.rect(self.screen, (30, 30, 40, 200),
                        (padding, padding, panel_width, panel_height))
        pygame.draw.rect(self.screen, (80, 80, 100),
                        (padding, padding, panel_width, panel_height), 1)

        current_y = padding + 10

        # Название подземелья
        name_surface = font.render(dungeon.name, True, (255, 200, 100))
        self.screen.blit(name_surface, (padding + 10, current_y))
        current_y += line_height

        # Уровень
        level_text = f"Уровень: {dungeon.dungeon_level}"
        level_surface = font.render(level_text, True, (200, 200, 200))
        self.screen.blit(level_surface, (padding + 10, current_y))
        current_y += line_height

        # Позиция игрока
        pos_text = f"Позиция: ({player.x}, {player.y})"
        pos_surface = font.render(pos_text, True, (180, 180, 180))
        self.screen.blit(pos_surface, (padding + 10, current_y))

        # Подсказка о выходе
        tile = dungeon.get_tile(player.x, player.y)
        if tile and tile.is_exit():
            hint_text = "[E] Покинуть подземелье"
            hint_surface = font.render(hint_text, True, (100, 255, 100))
            hint_x = (self.screen.get_width() - hint_surface.get_width()) // 2
            hint_y = self.screen.get_height() - 50
            self.screen.blit(hint_surface, (hint_x, hint_y))

    def render_target_info_panel(self, target_info: dict, font):
        """
        Отрисовка панели информации о выбранном враге

        Args:
            target_info: Словарь с информацией о цели
            font: Шрифт для текста
        """
        if target_info is None:
            return

        # Размеры и позиция панели (справа)
        panel_width = 200
        panel_height = 180
        panel_x = self.screen.get_width() - panel_width - 10
        panel_y = 130  # Под мини-картой

        # Фон панели
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((30, 30, 50, 230))
        self.screen.blit(panel_surface, (panel_x, panel_y))

        # Рамка
        pygame.draw.rect(self.screen, (100, 80, 80),
                        (panel_x, panel_y, panel_width, panel_height), 2)

        # Заголовок - красная полоса
        pygame.draw.rect(self.screen, (120, 50, 50),
                        (panel_x, panel_y, panel_width, 30))

        current_y = panel_y + 5
        padding_x = panel_x + 10

        # Имя врага
        name = target_info.get('name', 'Враг')
        name_surface = font.render(name, True, (255, 200, 200))
        self.screen.blit(name_surface, (padding_x, current_y))
        current_y += 30

        # Уровень
        level = target_info.get('level', 1)
        level_text = f"Уровень: {level}"
        level_surface = font.render(level_text, True, (200, 200, 200))
        self.screen.blit(level_surface, (padding_x, current_y))
        current_y += 25

        # Шкала HP
        hp = target_info.get('hp', 0)
        max_hp = target_info.get('max_hp', 1)
        if max_hp <= 0:
            max_hp = 1

        hp_text = f"HP: {hp}/{max_hp}"
        hp_text_surface = font.render(hp_text, True, (200, 200, 200))
        self.screen.blit(hp_text_surface, (padding_x, current_y))
        current_y += 22

        # Шкала HP графическая
        bar_width = panel_width - 20
        bar_height = 12
        bar_x = padding_x
        bar_y = current_y

        # Фон шкалы
        pygame.draw.rect(self.screen, (40, 40, 40),
                        (bar_x, bar_y, bar_width, bar_height))

        # Заполнение
        fill_width = int(bar_width * (hp / max_hp))
        hp_percent = hp / max_hp
        if hp_percent > 0.6:
            bar_color = (80, 200, 80)
        elif hp_percent > 0.3:
            bar_color = (220, 180, 50)
        else:
            bar_color = (200, 60, 60)

        if fill_width > 0:
            pygame.draw.rect(self.screen, bar_color,
                            (bar_x, bar_y, fill_width, bar_height))

        pygame.draw.rect(self.screen, (100, 100, 100),
                        (bar_x, bar_y, bar_width, bar_height), 1)
        current_y += 20

        # Атака и защита
        attack = target_info.get('attack', 5)
        defense = target_info.get('defense', 0)

        stats_text = f"Атака: {attack}  Защита: {defense}"
        stats_surface = font.render(stats_text, True, (180, 180, 180))
        self.screen.blit(stats_surface, (padding_x, current_y))
        current_y += 25

        # Тип NPC
        npc_type = target_info.get('npc_type', 'unknown')
        type_names = {
            'undead': 'Нежить',
            'skeleton': 'Скелет',
            'zombie': 'Зомби',
            'ghost': 'Призрак',
            'golem': 'Голем',
        }
        type_display = type_names.get(npc_type, npc_type.capitalize())
        type_text = f"Тип: {type_display}"
        type_surface = font.render(type_text, True, (150, 150, 180))
        self.screen.blit(type_surface, (padding_x, current_y))

    def render_combat_hints(self, font):
        """Отрисовка подсказок управления боем"""
        hints = [
            "[ПКМ] / [Tab] - Выбор цели",
            "[1-8] - Умения (авто-выбор)",
            "[Esc] - Снять выделение"
        ]

        # Размещаем подсказки выше центральных элементов интерфейса
        hint_y = self.screen.get_height() - 120
        hint_x = 10

        # Фон для лучшей читаемости
        hint_bg_width = 220
        hint_bg_height = len(hints) * 22 + 10
        hint_bg = pygame.Surface((hint_bg_width, hint_bg_height), pygame.SRCALPHA)
        hint_bg.fill((20, 20, 30, 180))
        self.screen.blit(hint_bg, (hint_x - 5, hint_y - 5))

        for hint in hints:
            hint_surface = font.render(hint, True, (180, 180, 150))
            self.screen.blit(hint_surface, (hint_x, hint_y))
            hint_y += 22
