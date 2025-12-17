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
        self.light_radius = 5  # Радиус освещения от игрока

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
            DungeonTileType.REMAINS: "R",
            DungeonTileType.REMAINS_LOOTED: "r",
        }

    def render_dungeon(self, dungeon: DungeonMap, player, camera_x: int, camera_y: int,
                       viewport_width: int, viewport_height: int, selected_target=None,
                       selected_object=None, selected_object_type=None):
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
            selected_object: Выбранный объект (ловушка или тайник)
            selected_object_type: Тип выбранного объекта ('trap' или 'stash')
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

                # Для необнаруженных объектов показываем как обычный пол
                if tile.tile_type == DungeonTileType.TRAP:
                    trap = dungeon.trap_manager.get_trap_at(map_x, map_y)
                    if trap and not trap.is_detected:
                        # Показываем как обычный пол
                        color = DUNGEON_TILE_COLORS.get(DungeonTileType.FLOOR, (80, 80, 80))
                elif tile.tile_type == DungeonTileType.STASH:
                    stash = dungeon.stash_manager.get_stash_at(map_x, map_y)
                    if stash and not stash.is_detected:
                        # Показываем как обычный пол
                        color = DUNGEON_TILE_COLORS.get(DungeonTileType.FLOOR, (80, 80, 80))

                # Если клетка не видна сейчас, затемняем
                if not tile.visible:
                    color = tuple(int(c * self.dim_factor) for c in color)
                else:
                    # Эффект затухания света от игрока
                    dist = ((map_x - player.x) ** 2 + (map_y - player.y) ** 2) ** 0.5
                    if dist > 0:
                        # Коэффициент освещения: 1.0 в центре, уменьшается к краям
                        light_factor = max(0.3, 1.0 - (dist / (self.light_radius + 1)) * 0.7)
                        color = tuple(int(c * light_factor) for c in color)

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
                    # Проверяем, нужно ли отрисовывать символ (для скрытых объектов)
                    should_draw = True

                    # Ловушки видны только если обнаружены
                    if tile.tile_type == DungeonTileType.TRAP:
                        trap = dungeon.trap_manager.get_trap_at(map_x, map_y)
                        if trap and not trap.is_detected:
                            should_draw = False

                    # Сработавшие ловушки всегда видны
                    elif tile.tile_type == DungeonTileType.TRAP_TRIGGERED:
                        should_draw = True

                    # Тайники видны только если обнаружены
                    elif tile.tile_type == DungeonTileType.STASH:
                        stash = dungeon.stash_manager.get_stash_at(map_x, map_y)
                        if stash and not stash.is_detected:
                            should_draw = False

                    if should_draw:
                        symbol = self.tile_symbols[tile.tile_type]
                        symbol_color = self._get_symbol_color(tile.tile_type)
                        symbol_surface = self.font.render(symbol, True, symbol_color)
                        sym_x = pixel_x + (self.tile_size - symbol_surface.get_width()) // 2
                        sym_y = pixel_y + (self.tile_size - symbol_surface.get_height()) // 2
                        self.screen.blit(symbol_surface, (sym_x, sym_y))

        # Отрисовываем выделение объектов подземелья (ловушек и тайников)
        if selected_object and selected_object_type:
            self._render_object_selection(dungeon, selected_object, start_x, start_y)

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
            DungeonTileType.REMAINS: (255, 150, 150),     # Красноватый
            DungeonTileType.REMAINS_LOOTED: (150, 100, 100),  # Тёмно-красный
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

    def _render_object_selection(self, dungeon: DungeonMap, selected_object, start_x: int, start_y: int):
        """
        Отрисовка выделения для выбранного объекта подземелья

        Args:
            dungeon: Карта подземелья
            selected_object: Выбранный объект (ловушка или тайник)
            start_x: Начальная координата X видимой области
            start_y: Начальная координата Y видимой области
        """
        if not selected_object:
            return

        # Проверяем видимость объекта
        tile = dungeon.get_tile(selected_object.x, selected_object.y)
        if not tile or not tile.visible:
            return

        # Вычисляем позицию на экране
        screen_x = selected_object.x - start_x
        screen_y = selected_object.y - start_y
        pixel_x = screen_x * self.tile_size
        pixel_y = screen_y * self.tile_size

        # Используем желтую/золотую рамку для объектов (чтобы отличать от врагов)
        selection_color = (255, 215, 0)  # Золотой
        pygame.draw.rect(self.screen, selection_color,
                        (pixel_x - 2, pixel_y - 2,
                         self.tile_size + 4, self.tile_size + 4), 3)

        # Уголки для красоты (ярко-желтые)
        corner_len = 8
        corner_color = (255, 255, 100)
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

        # Рисуем обнаруженные ловушки
        for trap in dungeon.trap_manager.traps:
            if trap.is_detected:
                trap_px = x + trap.x * pixel_w
                trap_py = y + trap.y * pixel_h

                # Цвет зависит от состояния ловушки
                if trap.is_disarmed:
                    trap_color = (100, 100, 100)  # Серый для обезвреженных
                else:
                    trap_color = (220, 50, 50)  # Красный для активных

                # Рисуем маркер ловушки (маленький квадрат)
                marker_size = max(2, min(pixel_w, pixel_h) // 2)
                marker_x = trap_px + (pixel_w - marker_size) // 2
                marker_y = trap_py + (pixel_h - marker_size) // 2
                pygame.draw.rect(self.screen, trap_color,
                               (marker_x, marker_y, marker_size, marker_size))

        # Рисуем обнаруженные тайники
        for stash in dungeon.stash_manager.stashes:
            if stash.is_detected and not stash.is_looted:
                stash_px = x + stash.x * pixel_w
                stash_py = y + stash.y * pixel_h

                # Золотой цвет для тайников
                stash_color = (255, 215, 0)
                if stash.has_trap and stash.trap and not stash.trap.is_disarmed:
                    # Оранжевый для тайников с ловушками
                    stash_color = (255, 140, 0)

                # Рисуем маркер тайника (ромб/звезда)
                marker_size = max(2, min(pixel_w, pixel_h) // 2)
                center_x = stash_px + pixel_w // 2
                center_y = stash_py + pixel_h // 2

                # Упрощенная звездочка (крест)
                pygame.draw.line(self.screen, stash_color,
                               (center_x - marker_size, center_y),
                               (center_x + marker_size, center_y), 1)
                pygame.draw.line(self.screen, stash_color,
                               (center_x, center_y - marker_size),
                               (center_x, center_y + marker_size), 1)

        # Рисуем игрока
        player_px = x + player.x * pixel_w
        player_py = y + player.y * pixel_h
        pygame.draw.rect(self.screen, (255, 215, 0),
                        (player_px, player_py, max(2, pixel_w), max(2, pixel_h)))

    def render_minimap_legend(self, x: int, y: int, width: int, font):
        """
        Отрисовка легенды миникарты подземелья

        Args:
            x, y: Позиция легенды на экране
            width: Ширина легенды
            font: Шрифт для текста
        """
        legend_items = [
            ("□", (255, 215, 0), "Игрок"),
            ("■", (220, 50, 50), "Ловушка"),
            ("■", (100, 100, 100), "Обезврежена"),
            ("✦", (255, 215, 0), "Тайник"),
            ("✦", (255, 140, 0), "С ловушкой"),
        ]

        item_height = 18
        legend_height = len(legend_items) * item_height + 10

        # Фон легенды
        pygame.draw.rect(self.screen, (20, 20, 25),
                        (x, y, width, legend_height))
        pygame.draw.rect(self.screen, (80, 80, 100),
                        (x, y, width, legend_height), 1)

        # Отрисовка элементов легенды
        current_y = y + 5
        for symbol, color, label in legend_items:
            # Символ
            symbol_surface = font.render(symbol, True, color)
            self.screen.blit(symbol_surface, (x + 5, current_y))

            # Название
            label_surface = font.render(label, True, (180, 180, 180))
            self.screen.blit(label_surface, (x + 25, current_y))

            current_y += item_height

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
        # Миникарта: y=10, h=180, легенда: y=200, h~100
        # Панель NPC должна быть ниже легенды
        panel_width = 200
        panel_height = 180
        panel_x = self.screen.get_width() - panel_width - 10
        panel_y = 310  # Под мини-картой и легендой (10+180+10+100+10=310)

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
        """Отрисовка подсказок управления боем и объектами"""
        hints = [
            "[ПКМ] / [Tab] - Выбор цели/объекта",
            "[E] - Взаимодействие с объектом",
            "[1-8] - Умения (авто-выбор)",
            "[Esc] - Снять выделение"
        ]

        # Размещаем подсказки в правом нижнем углу
        hint_bg_width = 220
        hint_bg_height = len(hints) * 22 + 10
        hint_x = self.screen.get_width() - hint_bg_width - 10
        hint_y = self.screen.get_height() - hint_bg_height - 10

        # Фон для лучшей читаемости
        hint_bg = pygame.Surface((hint_bg_width, hint_bg_height), pygame.SRCALPHA)
        hint_bg.fill((20, 20, 30, 180))
        self.screen.blit(hint_bg, (hint_x - 5, hint_y - 5))

        for hint in hints:
            hint_surface = font.render(hint, True, (180, 180, 150))
            self.screen.blit(hint_surface, (hint_x, hint_y))
            hint_y += 22

    def render_exploration_stats_panel(self, player, dungeon_manager, font):
        """
        Отрисовка панели статистики исследования

        Args:
            player: Объект игрока
            dungeon_manager: Менеджер подземелья
            font: Шрифт для текста
        """
        if not hasattr(player, 'skill_manager') or not player.skill_manager:
            return

        # Получаем навыки EXPLORATION
        keen_eye = player.skill_manager.get_skill("Острый Глаз")
        disarm_trap = player.skill_manager.get_skill("Обезвреживание")
        lockpicking = player.skill_manager.get_skill("Взлом")
        treasure_hunter = player.skill_manager.get_skill("Охотник за Сокровищами")

        # Если ни одного навыка нет, не показываем панель
        if not any([keen_eye, disarm_trap, lockpicking, treasure_hunter]):
            return

        # Размеры и позиция панели (слева, ниже информации о подземелье)
        panel_width = 220
        panel_height = 200
        panel_x = 10
        panel_y = 180  # Под информацией о подземелье

        # Фон панели
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((30, 40, 30, 230))
        self.screen.blit(panel_surface, (panel_x, panel_y))

        # Рамка (золотая для исследования)
        pygame.draw.rect(self.screen, (180, 140, 60),
                        (panel_x, panel_y, panel_width, panel_height), 2)

        # Заголовок - золотая полоса
        pygame.draw.rect(self.screen, (100, 80, 40),
                        (panel_x, panel_y, panel_width, 28))

        current_y = panel_y + 4
        padding_x = panel_x + 8

        # Заголовок
        title = "ИССЛЕДОВАНИЕ"
        title_surface = font.render(title, True, (255, 215, 100))
        title_x = panel_x + (panel_width - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, current_y))
        current_y += 30

        # Отрисовка навыков
        skills_data = [
            ("Keen Eye", keen_eye),
            ("Disarm", disarm_trap),
            ("Lockpick", lockpicking),
            ("Treasure", treasure_hunter)
        ]

        for skill_name, skill in skills_data:
            if not skill:
                continue

            rank = skill.rank
            # Рисуем звездочки для ранга
            stars = "★" * rank + "☆" * (5 - rank)

            # Имя навыка (сокращенное)
            skill_text = f"{skill_name}: {stars}"
            skill_surface = font.render(skill_text, True, (220, 220, 200))
            self.screen.blit(skill_surface, (padding_x, current_y))
            current_y += 20

        current_y += 5

        # Статистика (если есть навыки)
        if keen_eye:
            detected = getattr(keen_eye, 'objects_detected', 0)
            stat_text = f"Обнаружено: {detected}"
            stat_surface = font.render(stat_text, True, (180, 200, 180))
            self.screen.blit(stat_surface, (padding_x, current_y))
            current_y += 18

        if disarm_trap:
            disarmed = getattr(disarm_trap, 'traps_disarmed', 0)
            stat_text = f"Обезврежено: {disarmed}"
            stat_surface = font.render(stat_text, True, (180, 200, 180))
            self.screen.blit(stat_surface, (padding_x, current_y))
            current_y += 18

        if lockpicking:
            lockpicked = getattr(lockpicking, 'stashes_lockpicked', 0)
            stat_text = f"Взломано: {lockpicked}"
            stat_surface = font.render(stat_text, True, (180, 200, 180))
            self.screen.blit(stat_surface, (padding_x, current_y))
            current_y += 18

        # Информация о выбранном объекте
        if dungeon_manager.selected_object:
            obj_info = dungeon_manager.get_object_info()
            if obj_info:
                current_y += 5
                # Разделитель
                pygame.draw.line(self.screen, (180, 140, 60),
                               (panel_x + 5, current_y),
                               (panel_x + panel_width - 5, current_y), 1)
                current_y += 5

                # Тип объекта
                obj_name = obj_info.get('name', 'Объект')
                obj_level = obj_info.get('level_name', '')
                obj_text = f"{obj_name}"
                obj_surface = font.render(obj_text, True, (255, 215, 100))
                self.screen.blit(obj_surface, (padding_x, current_y))
                current_y += 18

                # Уровень
                level_text = f"Ур: {obj_level}"
                level_surface = font.render(level_text, True, (200, 200, 180))
                self.screen.blit(level_surface, (padding_x, current_y))
