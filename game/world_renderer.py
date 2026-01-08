"""
Модуль для рендеринга игрового мира, карты и NPC
Оптимизировано для больших карт (500x500+)
"""
import pygame
from game.constants import TILE_SIZE, COLORS
from game.core.game_context import GameContext


class WorldRenderer:
    """Класс для рендеринга игрового мира"""

    def __init__(self, game):
        """
        Инициализация рендерера мира

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.ctx = GameContext(game)

        # === Кэширование миникарты ===
        self._minimap_surface = None  # Кэшированная поверхность миникарты
        self._minimap_size = 0  # Текущий размер миникарты
        self._minimap_scale = 0  # Текущий масштаб (pixel_per_tile)
        self._minimap_needs_full_redraw = True  # Нужна полная перерисовка

        # Шрифт для надписей (кэшируем)
        self._label_font = None

    def get_time_of_day_tint(self):
        """
        Получить цветовой оттенок в зависимости от времени суток

        Returns:
            tuple: (r, g, b) - компонент затемнения (0-255)
        """
        hour = self.ctx.game_time.game_hour

        if 0 <= hour < 6 or hour >= 22:
            # Ночь - очень темно (синеватый оттенок)
            return (50, 50, 80)
        elif 6 <= hour < 8:
            # Рассвет - постепенное осветление (оранжевый оттенок)
            progress = (hour - 6) / 2.0  # 0.0 to 1.0
            r = int(50 + progress * 150)
            g = int(50 + progress * 150)
            b = int(80 + progress * 120)
            return (r, g, b)
        elif 8 <= hour < 18:
            # День - полная яркость
            return (255, 255, 255)
        elif 18 <= hour < 22:
            # Закат - постепенное затемнение (красноватый оттенок)
            progress = (hour - 18) / 4.0  # 0.0 to 1.0
            r = int(255 - progress * 155)
            g = int(255 - progress * 155)
            b = int(255 - progress * 125)
            return (r, g, b)

        return (255, 255, 255)  # По умолчанию - день

    def apply_time_of_day_tint(self, color):
        """
        Применить оттенок времени суток к цвету

        Args:
            color: Исходный цвет (r, g, b)

        Returns:
            tuple: Модифицированный цвет
        """
        tint = self.get_time_of_day_tint()
        return (
            int(color[0] * tint[0] / 255),
            int(color[1] * tint[1] / 255),
            int(color[2] * tint[2] / 255)
        )

    def render_map(self):
        """Отрисовка карты с учетом камеры и тумана войны"""
        # Вычисляем видимую область
        tiles_x = self.ctx.window_width // TILE_SIZE + 1
        tiles_y = (self.ctx.window_height - 100) // TILE_SIZE + 1

        camera_x = self.ctx.camera.x
        camera_y = self.ctx.camera.y

        for dy in range(tiles_y):
            for dx in range(tiles_x):
                # Координаты тайла на карте
                map_x = camera_x + dx
                map_y = camera_y + dy

                # Проверяем валидность координат
                if not self.ctx.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.ctx.game_map.get_tile(map_x, map_y)

                # Координаты на экране
                screen_x = dx * TILE_SIZE
                screen_y = dy * TILE_SIZE

                # Проверяем, исследован ли тайл
                if tile.explored:
                    # Определяем цвет тайла - всегда используем цвет биома
                    # Спрайты объектов отрисовываются поверх
                    color = COLORS.get(tile.biome, COLORS['background'])

                    # Если тайл не в текущей видимости, затемняем его
                    # В чит-режиме все тайлы видимы
                    is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(map_x, map_y, self.ctx.player.x, self.ctx.player.y)

                    # Применяем оттенок времени суток ко всем исследованным тайлам
                    color = self.apply_time_of_day_tint(color)

                    # Дополнительно затемняем тайлы в тумане войны
                    if not is_visible:
                        color = tuple(c // 2 for c in color)  # Затемняем цвет для тумана войны

                    # ВСЕГДА рисуем базовый цвет клетки
                    pygame.draw.rect(
                        self.ctx.screen,
                        color,
                        (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    )

                    # Отрисовка спрайта поверх клетки
                    # Пропускаем точки спавна животных - они невидимы на карте
                    if tile.has_location() and not tile.location.location_type.startswith('spawn_'):
                        # Отрисовываем спрайт локации поверх базового цвета
                        # Спрайт отображается даже в тумане войны (но затемненный)
                        self.ctx.sprite_manager.render_location(
                            self.ctx.screen,
                            tile.location.location_type,
                            screen_x,
                            screen_y,
                            lambda: None,  # Пустая функция, так как базовый цвет уже нарисован
                            darken=not is_visible  # Затемняем спрайт в тумане войны
                        )
                else:
                    # Неисследованная область - туман войны
                    pygame.draw.rect(
                        self.ctx.screen,
                        COLORS['fog'],
                        (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    )

        # Отрисовка надписей над локациями
        self._render_location_labels(tiles_x, tiles_y, camera_x, camera_y)

        # Отрисовка NPC
        self._render_all_npcs(tiles_x, tiles_y, camera_x, camera_y)

        # Отрисовка игрока (поверх всего остального)
        self._render_player(camera_x, camera_y)

    def _render_location_labels(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка надписей над локациями"""
        # Используем кэшированный шрифт
        if self._label_font is None:
            self._label_font = pygame.font.Font(None, 16)
        label_font = self._label_font
        for dy in range(tiles_y):
            for dx in range(tiles_x):
                map_x = camera_x + dx
                map_y = camera_y + dy

                if not self.ctx.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.ctx.game_map.get_tile(map_x, map_y)

                # Отрисовываем название локации, если она видима и исследована
                # Пропускаем точки спавна животных - они не должны отображаться на карте
                if tile.explored and tile.has_location():
                    if tile.location.location_type.startswith('spawn_'):
                        continue
                    if self.ctx.fog_of_war.is_visible(map_x, map_y, self.ctx.player.x, self.ctx.player.y):
                        screen_x = dx * TILE_SIZE
                        screen_y = dy * TILE_SIZE

                        # Создаем надпись
                        location_label = label_font.render(
                            tile.location.name,
                            True,
                            (255, 255, 255)
                        )

                        # Фон для надписи
                        label_rect = location_label.get_rect()
                        label_rect.centerx = screen_x + TILE_SIZE // 2
                        label_rect.bottom = screen_y - 2

                        # Полупрозрачный фон
                        background_surface = pygame.Surface((label_rect.width + 4, label_rect.height + 2))
                        background_surface.set_alpha(180)
                        background_surface.fill((0, 0, 0))
                        self.ctx.screen.blit(background_surface, (label_rect.x - 2, label_rect.y - 1))

                        # Отрисовка надписи
                        self.ctx.screen.blit(location_label, label_rect)

    def _render_all_npcs(self, tiles_x, tiles_y, camera_x, camera_y):
        """
        Отрисовка всех NPC.
        Оптимизировано: использует SpatialGrid для получения только NPC в видимой области.
        """
        # Пробуем использовать оптимизированный метод через SpatialGrid
        optimizer = self.ctx.performance_optimizer
        if optimizer and optimizer.npc_grid.grid:
            # Получаем NPC только в видимой области + небольшой запас
            center_x = camera_x + tiles_x // 2
            center_y = camera_y + tiles_y // 2
            # Радиус поиска - половина диагонали видимой области
            search_radius = max(tiles_x, tiles_y)

            visible_npcs = optimizer.get_nearby_npcs(center_x, center_y, search_radius)

            # Рендерим каждый NPC
            for npc in visible_npcs:
                # Проверяем, в зоне видимости камеры
                if not (camera_x <= npc.x < camera_x + tiles_x and
                        camera_y <= npc.y < camera_y + tiles_y):
                    continue

                self._render_single_npc(npc, camera_x, camera_y)
        else:
            # Fallback на старый метод если SpatialGrid не инициализирован
            self._render_guards(tiles_x, tiles_y, camera_x, camera_y)
            self._render_merchants(tiles_x, tiles_y, camera_x, camera_y)
            self._render_bandits(tiles_x, tiles_y, camera_x, camera_y)
            self._render_miners(tiles_x, tiles_y, camera_x, camera_y)
            self._render_undead(tiles_x, tiles_y, camera_x, camera_y)
            self._render_alchemists(tiles_x, tiles_y, camera_x, camera_y)
            self._render_necromancers(tiles_x, tiles_y, camera_x, camera_y)
            self._render_animals(tiles_x, tiles_y, camera_x, camera_y)

    def _render_single_npc(self, npc, camera_x, camera_y):
        """
        Рендеринг одного NPC (универсальный метод).
        Оптимизированный метод для использования с SpatialGrid.
        """
        if not npc.is_alive:
            return

        # Не рендерим скрытых NPC
        if hasattr(npc, 'is_hidden') and npc.is_hidden():
            return

        # Проверяем исследованность и видимость
        tile = self.ctx.game_map.get_tile(npc.x, npc.y)
        is_visible = (self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or
                     self.ctx.fog_of_war.is_visible(npc.x, npc.y, self.ctx.player.x, self.ctx.player.y))

        if not (tile.explored and is_visible):
            return

        screen_x = (npc.x - camera_x) * TILE_SIZE
        screen_y = (npc.y - camera_y) * TILE_SIZE

        # Определяем тип NPC и рендерим соответственно
        npc_type = getattr(npc, 'npc_type', 'unknown')

        # Получаем цвет и стиль отрисовки в зависимости от типа
        color = self._get_npc_color(npc)

        # Функция отрисовки по умолчанию
        def draw_default(screen=self.ctx.screen, c=color, sx=screen_x, sy=screen_y,
                        level=npc.level, ntype=npc_type):
            if ntype in ('wolf', 'bear', 'deer'):
                # Треугольник для животных
                points = [
                    (sx + TILE_SIZE // 2, sy + TILE_SIZE // 4),
                    (sx + TILE_SIZE // 4, sy + 3 * TILE_SIZE // 4),
                    (sx + 3 * TILE_SIZE // 4, sy + 3 * TILE_SIZE // 4)
                ]
                pygame.draw.polygon(screen, c, points)
                if level > 20:
                    pygame.draw.polygon(screen, (255, 215, 0), points, 2)
            elif ntype in ('guard', 'warrior', 'mage', 'shadow_adept', 'hunter'):
                # Круг для стражников
                pygame.draw.circle(screen, c, (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2), TILE_SIZE // 3)
                if level > 30:
                    pygame.draw.circle(screen, (200, 200, 50), (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2),
                                      TILE_SIZE // 3, 2)
            else:
                # Квадрат для остальных
                pygame.draw.rect(screen, c, (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                                            TILE_SIZE // 2, TILE_SIZE // 2))
                if ntype == 'undead' and level > 30:
                    pygame.draw.rect(screen, (255, 0, 255), (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                                                           TILE_SIZE // 2, TILE_SIZE // 2), 2)
                elif ntype == 'necromancer' and level > 25:
                    pygame.draw.rect(screen, (200, 100, 200), (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                                                              TILE_SIZE // 2, TILE_SIZE // 2), 2)

        # Отрисовка через sprite_manager
        self.ctx.sprite_manager.render_npc(self.ctx.screen, npc_type, screen_x, screen_y,
                                          draw_default, npc.level)

    def _get_npc_color(self, npc):
        """Получить цвет NPC в зависимости от типа, уровня и состояния"""
        npc_type = getattr(npc, 'npc_type', 'unknown')
        level = npc.level
        state = getattr(npc, 'state', 'idle')

        # Guards и подобные
        if npc_type in ('guard', 'warrior', 'mage', 'shadow_adept', 'hunter'):
            if level <= 10:
                base = (100, 150, 255)
            elif level <= 20:
                base = (50, 100, 220)
            elif level <= 30:
                base = (30, 70, 180)
            else:
                base = (80, 50, 200)
            if state == "rest":
                return tuple(max(0, c - 40) for c in base)
            elif state == "combat":
                return tuple(min(255, c + 40) for c in base)
            return base

        # Merchants
        elif npc_type == 'merchant':
            if state == "rest":
                return (150, 100, 50)
            elif state == "flee":
                return (255, 200, 100)
            return (200, 150, 50)

        # Bandits
        elif npc_type == 'bandit':
            if state == "rest":
                return (150, 0, 0)
            elif state == "combat":
                return (255, 50, 50)
            return (200, 0, 0)

        # Miners
        elif npc_type == 'miner':
            if state == "fleeing":
                return (200, 150, 100)
            elif state == "going_to_rest":
                return (100, 70, 40)
            return (150, 100, 50)

        # Undead
        elif npc_type == 'undead':
            if level <= 10:
                base = (80, 100, 80)
            elif level <= 20:
                base = (120, 80, 120)
            elif level <= 30:
                base = (100, 0, 100)
            else:
                base = (150, 0, 150)
            if state == "rest":
                return tuple(max(0, c - 30) for c in base)
            elif state == "combat":
                return tuple(min(255, c + 50) for c in base)
            return base

        # Alchemists
        elif npc_type == 'alchemist':
            return (50, 200, 100)

        # Necromancers
        elif npc_type == 'necromancer':
            if state == "combat":
                return (180, 50, 180)
            return (100, 20, 120)

        # Animals
        elif npc_type == 'wolf':
            if level <= 10:
                base = (120, 120, 120)
            elif level <= 20:
                base = (90, 90, 90)
            elif level <= 30:
                base = (60, 60, 70)
            else:
                base = (40, 40, 50)
            if state == "flee":
                return tuple(min(255, c + 30) for c in base)
            elif state == "combat":
                return tuple(min(255, c + 50) for c in base)
            return base

        elif npc_type == 'bear':
            if level <= 10:
                base = (139, 90, 43)
            elif level <= 20:
                base = (101, 67, 33)
            elif level <= 30:
                base = (70, 50, 30)
            else:
                base = (50, 35, 20)
            if state == "flee":
                return tuple(min(255, c + 30) for c in base)
            elif state == "combat":
                return tuple(min(255, c + 50) for c in base)
            return base

        elif npc_type == 'deer':
            if level <= 10:
                base = (210, 180, 140)
            elif level <= 20:
                base = (180, 140, 100)
            elif level <= 30:
                base = (150, 110, 70)
            else:
                base = (120, 90, 60)
            if state == "flee":
                return tuple(min(255, c + 30) for c in base)
            elif state == "combat":
                return tuple(min(255, c + 50) for c in base)
            return base

        # По умолчанию
        return (100, 100, 100)

    def _render_guards(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка стражников"""
        for guard in self.ctx.guards:
            # Проверяем, находится ли стражник в зоне видимости камеры
            if (camera_x <= guard.x < camera_x + tiles_x and
                camera_y <= guard.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл со стражником
                tile = self.ctx.game_map.get_tile(guard.x, guard.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(guard.x, guard.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not guard.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if guard.is_hidden():
                        continue

                    guard_screen_x = (guard.x - camera_x) * TILE_SIZE
                    guard_screen_y = (guard.y - camera_y) * TILE_SIZE

                    # Цвет зависит от уровня стражника (4 варианта)
                    if guard.level <= 10:
                        base_color = (100, 150, 255)  # Новичок - светло-синий
                    elif guard.level <= 20:
                        base_color = (50, 100, 220)  # Обычный - синий
                    elif guard.level <= 30:
                        base_color = (30, 70, 180)  # Опытный - темно-синий
                    else:
                        base_color = (80, 50, 200)  # Эксперт - фиолетово-синий

                    # Модификация цвета в зависимости от состояния
                    if guard.state == "rest":
                        guard_color = tuple(max(0, c - 40) for c in base_color)
                    elif guard.state == "combat":
                        guard_color = tuple(min(255, c + 40) for c in base_color)
                    else:
                        guard_color = base_color

                    # Функция отрисовки по умолчанию (геометрическая фигура)
                    def draw_guard_default(screen=self.ctx.screen, color=guard_color,
                                          sx=guard_screen_x, sy=guard_screen_y, level=guard.level):
                        pygame.draw.circle(
                            screen,
                            color,
                            (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2),
                            TILE_SIZE // 3
                        )
                        # Обводка для эксперт стражников
                        if level > 30:
                            pygame.draw.circle(
                                screen,
                                (200, 200, 50),
                                (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2),
                                TILE_SIZE // 3,
                                2
                            )

                    # Отрисовка стражника (спрайт или геометрическая фигура)
                    # Используем реальный npc_type для правильного отображения спрайтов
                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, guard.npc_type, guard_screen_x, guard_screen_y,
                        draw_guard_default, guard.level
                    )

    def _render_merchants(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка торговцев"""
        for merchant in self.ctx.merchants:
            # Проверяем, находится ли торговец в зоне видимости камеры
            if (camera_x <= merchant.x < camera_x + tiles_x and
                camera_y <= merchant.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с торговцем
                tile = self.ctx.game_map.get_tile(merchant.x, merchant.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(merchant.x, merchant.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not merchant.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if merchant.is_hidden():
                        continue

                    merchant_screen_x = (merchant.x - camera_x) * TILE_SIZE
                    merchant_screen_y = (merchant.y - camera_y) * TILE_SIZE

                    # Цвет зависит от состояния торговца
                    if merchant.state == "rest":
                        merchant_color = (150, 100, 50)  # Коричневый для отдыха/торговли
                    elif merchant.state == "flee":
                        merchant_color = (255, 200, 100)  # Светлый для побега
                    else:
                        merchant_color = (200, 150, 50)  # Оранжево-коричневый для путешествия

                    # Функция отрисовки по умолчанию (геометрическая фигура)
                    def draw_merchant_default(screen=self.ctx.screen, color=merchant_color,
                                             sx=merchant_screen_x, sy=merchant_screen_y):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                    # Отрисовка торговца (спрайт или геометрическая фигура)
                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'merchant', merchant_screen_x, merchant_screen_y,
                        draw_merchant_default, merchant.level
                    )

    def _render_bandits(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка бандитов"""
        for bandit in self.ctx.bandits:
            # Проверяем, находится ли бандит в зоне видимости камеры
            if (camera_x <= bandit.x < camera_x + tiles_x and
                camera_y <= bandit.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с бандитом
                tile = self.ctx.game_map.get_tile(bandit.x, bandit.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(bandit.x, bandit.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not bandit.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if bandit.is_hidden():
                        continue

                    bandit_screen_x = (bandit.x - camera_x) * TILE_SIZE
                    bandit_screen_y = (bandit.y - camera_y) * TILE_SIZE

                    # Цвет зависит от состояния бандита
                    if bandit.state == "rest":
                        bandit_color = (150, 0, 0)  # Темно-красный для отдыха
                    elif bandit.state == "combat":
                        bandit_color = (255, 50, 50)  # Ярко-красный для боя
                    else:
                        bandit_color = (200, 0, 0)  # Красный для патруля

                    # Функция отрисовки по умолчанию (квадрат)
                    def draw_bandit_default(screen=self.ctx.screen, color=bandit_color,
                                           sx=bandit_screen_x, sy=bandit_screen_y):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                    # Отрисовка бандита (спрайт или геометрическая фигура)
                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'bandit', bandit_screen_x, bandit_screen_y,
                        draw_bandit_default, bandit.level
                    )

    def _render_miners(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка шахтеров"""
        for miner in self.ctx.miners:
            # Проверяем, находится ли шахтер в зоне видимости камеры
            if (camera_x <= miner.x < camera_x + tiles_x and
                camera_y <= miner.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с шахтером
                tile = self.ctx.game_map.get_tile(miner.x, miner.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(miner.x, miner.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not miner.is_alive:
                        continue

                    # Не отрисовываем скрытых NPC (работа/отдых в локации)
                    if miner.is_hidden():
                        continue

                    miner_screen_x = (miner.x - camera_x) * TILE_SIZE
                    miner_screen_y = (miner.y - camera_y) * TILE_SIZE

                    # Цвет зависит от состояния шахтера
                    if miner.state == "fleeing":
                        miner_color = (200, 150, 100)  # Светло-коричневый для побега
                    elif miner.state == "going_to_rest":
                        miner_color = (100, 70, 40)  # Коричневый для движения к отдыху
                    elif miner.state == "going_to_mine":
                        miner_color = (150, 100, 50)  # Темно-коричневый для движения к шахте
                    else:
                        miner_color = (150, 100, 50)  # По умолчанию

                    # Функция отрисовки по умолчанию (геометрическая фигура)
                    def draw_miner_default(screen=self.ctx.screen, color=miner_color,
                                          sx=miner_screen_x, sy=miner_screen_y):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                             TILE_SIZE // 2, TILE_SIZE // 2)
                        )

                    # Отрисовка шахтера (спрайт или геометрическая фигура)
                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'miner', miner_screen_x, miner_screen_y,
                        draw_miner_default, miner.level
                    )

    def _render_undead(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка нежити"""
        for undead_npc in self.ctx.undead:
            # Проверяем, находится ли нежить в зоне видимости камеры
            if (camera_x <= undead_npc.x < camera_x + tiles_x and
                camera_y <= undead_npc.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с нежитью
                tile = self.ctx.game_map.get_tile(undead_npc.x, undead_npc.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(undead_npc.x, undead_npc.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not undead_npc.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if undead_npc.is_hidden():
                        continue

                    undead_screen_x = (undead_npc.x - camera_x) * TILE_SIZE
                    undead_screen_y = (undead_npc.y - camera_y) * TILE_SIZE

                    # Цвет зависит от уровня нежити (4 ранга)
                    if undead_npc.level <= 10:
                        base_color = (80, 100, 80)  # Зомби - серо-зеленый
                    elif undead_npc.level <= 20:
                        base_color = (120, 80, 120)  # Скелет - серо-фиолетовый
                    elif undead_npc.level <= 30:
                        base_color = (100, 0, 100)  # Мертвец - темно-фиолетовый
                    else:
                        base_color = (150, 0, 150)  # Призрак - ярко-фиолетовый

                    # Модификация цвета в зависимости от состояния
                    if undead_npc.state == "rest":
                        undead_color = tuple(max(0, c - 30) for c in base_color)
                    elif undead_npc.state == "combat":
                        undead_color = tuple(min(255, c + 50) for c in base_color)
                    else:
                        undead_color = base_color

                    # Функция отрисовки по умолчанию (квадрат)
                    def draw_undead_default(screen=self.ctx.screen, color=undead_color,
                                           sx=undead_screen_x, sy=undead_screen_y, level=undead_npc.level):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                        # Обводка для элитной нежити
                        if level > 30:
                            pygame.draw.rect(
                                screen,
                                (255, 0, 255),
                                (sx + TILE_SIZE // 4,
                                 sy + TILE_SIZE // 4,
                                 TILE_SIZE // 2,
                                 TILE_SIZE // 2),
                                2
                            )

                    # Отрисовка нежити (спрайт или геометрическая фигура)
                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'undead', undead_screen_x, undead_screen_y,
                        draw_undead_default, undead_npc.level
                    )

    def _render_alchemists(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка алхимиков"""
        for alchemist in self.ctx.alchemists:
            if (camera_x <= alchemist.x < camera_x + tiles_x and
                camera_y <= alchemist.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с алхимиком
                tile = self.ctx.game_map.get_tile(alchemist.x, alchemist.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(alchemist.x, alchemist.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not alchemist.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if alchemist.is_hidden():
                        continue

                    screen_x = (alchemist.x - camera_x) * TILE_SIZE
                    screen_y = (alchemist.y - camera_y) * TILE_SIZE

                    # Зеленый цвет для алхимиков
                    alchemist_color = (50, 200, 100)

                    def draw_alchemist_default(screen=self.ctx.screen, color=alchemist_color,
                                              sx=screen_x, sy=screen_y):
                        # Квадрат для алхимика
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'alchemist', screen_x, screen_y,
                        draw_alchemist_default, alchemist.level
                    )

    def _render_necromancers(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка некромантов"""
        for necromancer in self.ctx.necromancers:
            if (camera_x <= necromancer.x < camera_x + tiles_x and
                camera_y <= necromancer.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с некромантом
                tile = self.ctx.game_map.get_tile(necromancer.x, necromancer.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(necromancer.x, necromancer.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not necromancer.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if necromancer.is_hidden():
                        continue

                    screen_x = (necromancer.x - camera_x) * TILE_SIZE
                    screen_y = (necromancer.y - camera_y) * TILE_SIZE

                    # Темно-фиолетовый для некромантов
                    if necromancer.state == "combat":
                        necro_color = (180, 50, 180)  # Яркий при бое
                    else:
                        necro_color = (100, 20, 120)  # Темный

                    def draw_necro_default(screen=self.ctx.screen, color=necro_color,
                                          sx=screen_x, sy=screen_y, level=necromancer.level):
                        # Квадрат для некроманта
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )
                        # Обводка для высокоуровневых
                        if level > 25:
                            pygame.draw.rect(
                                screen,
                                (200, 100, 200),
                                (sx + TILE_SIZE // 4,
                                 sy + TILE_SIZE // 4,
                                 TILE_SIZE // 2,
                                 TILE_SIZE // 2),
                                2
                            )

                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, 'necromancer', screen_x, screen_y,
                        draw_necro_default, necromancer.level
                    )

    def _render_animals(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка животных (волков, медведей, оленей)"""
        for animal in self.ctx.animals:
            if (camera_x <= animal.x < camera_x + tiles_x and
                camera_y <= animal.y < camera_y + tiles_y):

                # Проверяем, исследован ли тайл с животным
                tile = self.ctx.game_map.get_tile(animal.x, animal.y)
                # Проверяем, видим ли NPC (не в тумане войны) или включен чит-режим
                is_visible = self.ctx.cheat_menu_window.cheats['reveal_map']['enabled'] or self.ctx.fog_of_war.is_visible(animal.x, animal.y, self.ctx.player.x, self.ctx.player.y)

                if tile.explored and is_visible:
                    if not animal.is_alive:
                        continue

                    # Не рендерим скрытых NPC (в режиме отдыха/работы)
                    if animal.is_hidden():
                        continue

                    screen_x = (animal.x - camera_x) * TILE_SIZE
                    screen_y = (animal.y - camera_y) * TILE_SIZE

                    # Определяем цвет в зависимости от типа животного и уровня
                    if animal.npc_type == 'wolf':
                        # Волк - серый с градацией по уровню
                        if animal.level <= 10:
                            base_color = (120, 120, 120)  # Новичок - светло-серый
                        elif animal.level <= 20:
                            base_color = (90, 90, 90)  # Обычный - серый
                        elif animal.level <= 30:
                            base_color = (60, 60, 70)  # Опытный - темно-серый
                        else:
                            base_color = (40, 40, 50)  # Эксперт - почти черный
                    elif animal.npc_type == 'bear':
                        # Медведь - коричневый с градацией по уровню
                        if animal.level <= 10:
                            base_color = (139, 90, 43)  # Новичок - светло-коричневый
                        elif animal.level <= 20:
                            base_color = (101, 67, 33)  # Обычный - коричневый
                        elif animal.level <= 30:
                            base_color = (70, 50, 30)  # Опытный - темно-коричневый
                        else:
                            base_color = (50, 35, 20)  # Эксперт - очень темный коричневый
                    elif animal.npc_type == 'deer':
                        # Олень - бежевый с градацией по уровню
                        if animal.level <= 10:
                            base_color = (210, 180, 140)  # Новичок - светло-бежевый
                        elif animal.level <= 20:
                            base_color = (180, 140, 100)  # Обычный - бежевый
                        elif animal.level <= 30:
                            base_color = (150, 110, 70)  # Опытный - темно-бежевый
                        else:
                            base_color = (120, 90, 60)  # Эксперт - темный бежевый
                    else:
                        base_color = (100, 100, 100)  # Неизвестное животное

                    # Модификация цвета в зависимости от состояния
                    if animal.state == "flee":
                        animal_color = tuple(min(255, c + 30) for c in base_color)  # Светлее при побеге
                    elif animal.state == "combat":
                        animal_color = tuple(min(255, c + 50) for c in base_color)  # Ярче при атаке
                    else:
                        animal_color = base_color

                    def draw_animal_default(screen=self.ctx.screen, color=animal_color,
                                          sx=screen_x, sy=screen_y, level=animal.level,
                                          npc_type=animal.npc_type):
                        # Треугольник для животных (символизирует зверя)
                        points = [
                            (sx + TILE_SIZE // 2, sy + TILE_SIZE // 4),  # Верхушка
                            (sx + TILE_SIZE // 4, sy + 3 * TILE_SIZE // 4),  # Левый угол
                            (sx + 3 * TILE_SIZE // 4, sy + 3 * TILE_SIZE // 4)  # Правый угол
                        ]
                        pygame.draw.polygon(screen, color, points)

                        # Обводка для высокоуровневых животных
                        if level > 20:
                            pygame.draw.polygon(screen, (255, 215, 0), points, 2)

                    self.ctx.sprite_manager.render_npc(
                        self.ctx.screen, animal.npc_type, screen_x, screen_y,
                        draw_animal_default, animal.level
                    )

    def _render_player(self, camera_x, camera_y):
        """Отрисовка игрока"""
        player_screen_x = (self.ctx.player.x - camera_x) * TILE_SIZE
        player_screen_y = (self.ctx.player.y - camera_y) * TILE_SIZE

        # Функция отрисовки по умолчанию (геометрическая фигура)
        def draw_player_default():
            pygame.draw.circle(
                self.ctx.screen,
                COLORS['player'],
                (player_screen_x + TILE_SIZE // 2, player_screen_y + TILE_SIZE // 2),
                TILE_SIZE // 3
            )

        # Отрисовка игрока (спрайт или геометрическая фигура)
        self.ctx.sprite_manager.render_npc(
            self.ctx.screen, 'player', player_screen_x, player_screen_y,
            draw_player_default, self.ctx.player.level
        )

    def render_minimap(self):
        """
        Отрисовка мини-карты.
        Оптимизировано: кэширование в отдельную Surface, обновление только при изменениях.
        Для карт 500x500 это даёт ~100x ускорение (250000 итераций -> 1 blit).
        """
        # Размеры мини-карты (масштабируются под разрешение)
        base_size = 150 * 1.4  # 210 пикселей базовый размер
        minimap_size = self.ctx.ui_scaler.scale_value(int(base_size))
        margin = self.ctx.ui_scaler.scale_value(10)
        panel_height = self.ctx.ui_scaler.scale_value(100)

        # Позиция в правом нижнем углу над панелью
        minimap_x = self.ctx.window_width - minimap_size - margin
        minimap_y = self.ctx.window_height - minimap_size - panel_height - margin

        map_width = self.ctx.game_map.width
        map_height = self.ctx.game_map.height
        pixel_per_tile = min(minimap_size / map_width, minimap_size / map_height)

        # Проверяем, нужно ли пересоздать/обновить кэш миникарты
        need_full_redraw = (
            self._minimap_needs_full_redraw or
            self._minimap_surface is None or
            self._minimap_size != minimap_size or
            self._minimap_scale != pixel_per_tile
        )

        # Проверяем dirty flag из fog_of_war
        fog_dirty = self.ctx.fog_of_war.is_minimap_dirty()

        if need_full_redraw or fog_dirty:
            self._rebuild_minimap_cache(minimap_size, pixel_per_tile, map_width, map_height)
            self._minimap_size = minimap_size
            self._minimap_scale = pixel_per_tile
            self._minimap_needs_full_redraw = False
            self.ctx.fog_of_war.clear_minimap_dirty()

        # Рисуем фон миникарты
        pygame.draw.rect(
            self.ctx.screen,
            (20, 20, 25),
            (minimap_x, minimap_y, minimap_size, minimap_size)
        )

        # Копируем кэшированную миникарту на экран
        if self._minimap_surface:
            self.ctx.screen.blit(self._minimap_surface, (minimap_x, minimap_y))

        # Рамка мини-карты
        pygame.draw.rect(
            self.ctx.screen,
            COLORS['text'],
            (minimap_x, minimap_y, minimap_size, minimap_size),
            3
        )

        # Отметка игрока (рисуется каждый кадр, т.к. позиция меняется)
        player_minimap_x = minimap_x + int(self.ctx.player.x * pixel_per_tile)
        player_minimap_y = minimap_y + int(self.ctx.player.y * pixel_per_tile)

        pygame.draw.circle(
            self.ctx.screen,
            COLORS['player'],
            (player_minimap_x, player_minimap_y),
            3
        )

        # Заголовок мини-карты
        minimap_font_size = self.ctx.ui_scaler.scale_font_size(16)
        minimap_font = pygame.font.Font(None, minimap_font_size)
        minimap_title = minimap_font.render("Карта", True, COLORS['text'])
        title_offset = self.ctx.ui_scaler.scale_value(18)
        self.ctx.screen.blit(minimap_title, (minimap_x + 5, minimap_y - title_offset))

    def _rebuild_minimap_cache(self, minimap_size, pixel_per_tile, map_width, map_height):
        """
        Перестроить кэш миникарты.
        Вызывается только когда исследованы новые тайлы или изменился размер.
        """
        # Создаём новую поверхность для миникарты
        self._minimap_surface = pygame.Surface((minimap_size, minimap_size))
        self._minimap_surface.fill((20, 20, 25))  # Фон

        tile_draw_size = max(1, int(pixel_per_tile))

        # Проходим по всем тайлам карты
        for my in range(map_height):
            for mx in range(map_width):
                if not self.ctx.game_map.is_valid_position(mx, my):
                    continue

                tile = self.ctx.game_map.get_tile(mx, my)

                # Отображаем только исследованные тайлы
                if tile.explored:
                    # Позиция на мини-карте
                    px = int(mx * pixel_per_tile)
                    py = int(my * pixel_per_tile)

                    # Определяем цвет
                    if tile.has_location() and not tile.location.location_type.startswith('spawn_'):
                        color = COLORS.get(tile.location.location_type, COLORS['background'])
                    else:
                        color = COLORS.get(tile.biome, COLORS['background'])

                    # Затемняем цвет
                    color = tuple(c // 2 for c in color)

                    # Рисуем на кэшированной поверхности
                    pygame.draw.rect(
                        self._minimap_surface,
                        color,
                        (px, py, tile_draw_size, tile_draw_size)
                    )

    def invalidate_minimap(self):
        """Принудительно инвалидировать кэш миникарты"""
        self._minimap_needs_full_redraw = True
