"""
Модуль для рендеринга игрового мира, карты и NPC
"""
import pygame
from game.constants import TILE_SIZE, COLORS


class WorldRenderer:
    """Класс для рендеринга игрового мира"""

    def __init__(self, game):
        """
        Инициализация рендерера мира

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game

    def get_time_of_day_tint(self):
        """
        Получить цветовой оттенок в зависимости от времени суток

        Returns:
            tuple: (r, g, b) - компонент затемнения (0-255)
        """
        hour = self.game.game_time.game_hour

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
        tiles_x = self.game.window_width // TILE_SIZE + 1
        tiles_y = (self.game.window_height - 100) // TILE_SIZE + 1

        camera_x = self.game.camera.x
        camera_y = self.game.camera.y

        for dy in range(tiles_y):
            for dx in range(tiles_x):
                # Координаты тайла на карте
                map_x = camera_x + dx
                map_y = camera_y + dy

                # Проверяем валидность координат
                if not self.game.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game.game_map.get_tile(map_x, map_y)

                # Координаты на экране
                screen_x = dx * TILE_SIZE
                screen_y = dy * TILE_SIZE

                # Проверяем, исследован ли тайл
                if tile.explored:
                    # Определяем цвет тайла
                    if tile.has_location():
                        color = COLORS.get(tile.location.location_type, COLORS['background'])
                    else:
                        color = COLORS.get(tile.biome, COLORS['background'])

                    # Если тайл не в текущей видимости, затемняем его
                    # В чит-режиме все тайлы видимы
                    is_visible = self.game.cheat_mode_active or self.game.fog_of_war.is_visible(map_x, map_y, self.game.player.x, self.game.player.y)
                    if not is_visible:
                        color = tuple(c // 2 for c in color)  # Затемняем цвет
                        # Под туманом войны НЕ отображаем спрайты локаций, только цвет
                        pygame.draw.rect(
                            self.game.screen,
                            color,
                            (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                        )
                    else:
                        # Применяем оттенок времени суток только к видимым тайлам
                        color = self.apply_time_of_day_tint(color)

                        # Отрисовка тайла
                        if tile.has_location():
                            # Используем спрайт для видимой локации
                            def draw_default():
                                pygame.draw.rect(
                                    self.game.screen,
                                    color,
                                    (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                                )
                            self.game.sprite_manager.render_location(
                                self.game.screen,
                                tile.location.location_type,
                                screen_x,
                                screen_y,
                                draw_default
                            )
                        else:
                            # Обычная отрисовка для биомов
                            pygame.draw.rect(
                                self.game.screen,
                                color,
                                (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                            )
                else:
                    # Неисследованная область - туман войны
                    pygame.draw.rect(
                        self.game.screen,
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
        label_font = pygame.font.Font(None, 16)
        for dy in range(tiles_y):
            for dx in range(tiles_x):
                map_x = camera_x + dx
                map_y = camera_y + dy

                if not self.game.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game.game_map.get_tile(map_x, map_y)

                # Отрисовываем название локации, если она видима и исследована
                if tile.explored and tile.has_location():
                    if self.game.fog_of_war.is_visible(map_x, map_y, self.game.player.x, self.game.player.y):
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
                        self.game.screen.blit(background_surface, (label_rect.x - 2, label_rect.y - 1))

                        # Отрисовка надписи
                        self.game.screen.blit(location_label, label_rect)

    def _render_all_npcs(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка всех NPC"""
        self._render_guards(tiles_x, tiles_y, camera_x, camera_y)
        self._render_merchants(tiles_x, tiles_y, camera_x, camera_y)
        self._render_bandits(tiles_x, tiles_y, camera_x, camera_y)
        self._render_miners(tiles_x, tiles_y, camera_x, camera_y)
        self._render_undead(tiles_x, tiles_y, camera_x, camera_y)
        self._render_mages(tiles_x, tiles_y, camera_x, camera_y)
        self._render_alchemists(tiles_x, tiles_y, camera_x, camera_y)
        self._render_hunters(tiles_x, tiles_y, camera_x, camera_y)
        self._render_necromancers(tiles_x, tiles_y, camera_x, camera_y)

    def _render_guards(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка стражников"""
        for guard in self.game.guards:
            # Проверяем, находится ли стражник в зоне видимости камеры
            if (camera_x <= guard.x < camera_x + tiles_x and
                camera_y <= guard.y < camera_y + tiles_y):

                # Проверяем, видим ли мы стражника (туман войны)
                tile = self.game.game_map.get_tile(guard.x, guard.y)
                if tile.explored and self.game.fog_of_war.is_visible(guard.x, guard.y, self.game.player.x, self.game.player.y):
                    if not guard.is_alive:
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
                    def draw_guard_default(screen=self.game.screen, color=guard_color,
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
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'guard', guard_screen_x, guard_screen_y,
                        draw_guard_default, guard.level
                    )

    def _render_merchants(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка торговцев"""
        for merchant in self.game.merchants:
            # Проверяем, находится ли торговец в зоне видимости камеры
            if (camera_x <= merchant.x < camera_x + tiles_x and
                camera_y <= merchant.y < camera_y + tiles_y):

                # Проверяем, видим ли мы торговца (туман войны)
                tile = self.game.game_map.get_tile(merchant.x, merchant.y)
                if tile.explored and self.game.fog_of_war.is_visible(merchant.x, merchant.y, self.game.player.x, self.game.player.y):
                    if not merchant.is_alive:
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
                    def draw_merchant_default(screen=self.game.screen, color=merchant_color,
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
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'merchant', merchant_screen_x, merchant_screen_y,
                        draw_merchant_default, merchant.level
                    )

    def _render_bandits(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка бандитов"""
        for bandit in self.game.bandits:
            # Проверяем, находится ли бандит в зоне видимости камеры
            if (camera_x <= bandit.x < camera_x + tiles_x and
                camera_y <= bandit.y < camera_y + tiles_y):

                # Проверяем, видим ли мы бандита (туман войны)
                tile = self.game.game_map.get_tile(bandit.x, bandit.y)
                if tile.explored and self.game.fog_of_war.is_visible(bandit.x, bandit.y, self.game.player.x, self.game.player.y):
                    if not bandit.is_alive:
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
                    def draw_bandit_default(screen=self.game.screen, color=bandit_color,
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
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'bandit', bandit_screen_x, bandit_screen_y,
                        draw_bandit_default, bandit.level
                    )

    def _render_miners(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка шахтеров"""
        for miner in self.game.miners:
            # Проверяем, находится ли шахтер в зоне видимости камеры
            if (camera_x <= miner.x < camera_x + tiles_x and
                camera_y <= miner.y < camera_y + tiles_y):

                # Проверяем, видим ли мы шахтера (туман войны)
                tile = self.game.game_map.get_tile(miner.x, miner.y)
                if tile.explored and self.game.fog_of_war.is_visible(miner.x, miner.y, self.game.player.x, self.game.player.y):
                    if not miner.is_alive:
                        continue

                    miner_screen_x = (miner.x - camera_x) * TILE_SIZE
                    miner_screen_y = (miner.y - camera_y) * TILE_SIZE

                    # Цвет зависит от состояния шахтера
                    if miner.state == "rest":
                        miner_color = (100, 70, 40)  # Коричневый для отдыха
                    elif miner.state == "flee":
                        miner_color = (200, 150, 100)  # Светло-коричневый для побега
                    else:
                        miner_color = (150, 100, 50)  # Темно-коричневый для работы

                    # Функция отрисовки по умолчанию (геометрическая фигура)
                    def draw_miner_default(screen=self.game.screen, color=miner_color,
                                          sx=miner_screen_x, sy=miner_screen_y):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                             TILE_SIZE // 2, TILE_SIZE // 2)
                        )

                    # Отрисовка шахтера (спрайт или геометрическая фигура)
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'miner', miner_screen_x, miner_screen_y,
                        draw_miner_default, miner.level
                    )

    def _render_undead(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка нежити"""
        for undead_npc in self.game.undead:
            # Проверяем, находится ли нежить в зоне видимости камеры
            if (camera_x <= undead_npc.x < camera_x + tiles_x and
                camera_y <= undead_npc.y < camera_y + tiles_y):

                # Проверяем, видим ли мы нежить (туман войны)
                tile = self.game.game_map.get_tile(undead_npc.x, undead_npc.y)
                if tile.explored and self.game.fog_of_war.is_visible(undead_npc.x, undead_npc.y, self.game.player.x, self.game.player.y):
                    if not undead_npc.is_alive:
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
                    def draw_undead_default(screen=self.game.screen, color=undead_color,
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
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'undead', undead_screen_x, undead_screen_y,
                        draw_undead_default, undead_npc.level
                    )

    def _render_mages(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка магов"""
        for mage in self.game.mages:
            # Проверяем, находится ли маг в зоне видимости камеры
            if (camera_x <= mage.x < camera_x + tiles_x and
                camera_y <= mage.y < camera_y + tiles_y):

                # Проверяем, видим ли мы мага (туман войны)
                tile = self.game.game_map.get_tile(mage.x, mage.y)
                if tile.explored and self.game.fog_of_war.is_visible(mage.x, mage.y, self.game.player.x, self.game.player.y):
                    if not mage.is_alive:
                        continue

                    mage_screen_x = (mage.x - camera_x) * TILE_SIZE
                    mage_screen_y = (mage.y - camera_y) * TILE_SIZE

                    # Цвет зависит от уровня мага
                    if mage.level <= 10:
                        base_color = (100, 100, 200)  # Светло-синий для адептов
                    elif mage.level <= 15:
                        base_color = (80, 80, 220)  # Синий для чародеев
                    else:
                        base_color = (138, 43, 226)  # Фиолетовый для магистров

                    # Модификация цвета в зависимости от состояния
                    if mage.state == "rest":
                        mage_color = tuple(max(0, c - 30) for c in base_color)
                    elif mage.state == "combat":
                        mage_color = tuple(min(255, c + 50) for c in base_color)
                    else:
                        mage_color = base_color

                    # Функция отрисовки по умолчанию (квадрат для мага)
                    def draw_mage_default(screen=self.game.screen, color=mage_color,
                                         sx=mage_screen_x, sy=mage_screen_y, level=mage.level):
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                        # Обводка для высокоуровневых магов
                        if level > 15:
                            pygame.draw.rect(
                                screen,
                                (200, 150, 255),
                                (sx + TILE_SIZE // 4,
                                 sy + TILE_SIZE // 4,
                                 TILE_SIZE // 2,
                                 TILE_SIZE // 2),
                                2
                            )

                    # Отрисовка мага (спрайт или геометрическая фигура)
                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'mage', mage_screen_x, mage_screen_y,
                        draw_mage_default, mage.level
                    )

    def _render_alchemists(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка алхимиков"""
        for alchemist in self.game.alchemists:
            if (camera_x <= alchemist.x < camera_x + tiles_x and
                camera_y <= alchemist.y < camera_y + tiles_y):

                tile = self.game.game_map.get_tile(alchemist.x, alchemist.y)
                if tile.explored and self.game.fog_of_war.is_visible(alchemist.x, alchemist.y, self.game.player.x, self.game.player.y):
                    if not alchemist.is_alive:
                        continue

                    screen_x = (alchemist.x - camera_x) * TILE_SIZE
                    screen_y = (alchemist.y - camera_y) * TILE_SIZE

                    # Зеленый цвет для алхимиков
                    alchemist_color = (50, 200, 100)

                    def draw_alchemist_default(screen=self.game.screen, color=alchemist_color,
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

                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'alchemist', screen_x, screen_y,
                        draw_alchemist_default, alchemist.level
                    )

    def _render_hunters(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка охотников"""
        for hunter in self.game.hunters:
            if (camera_x <= hunter.x < camera_x + tiles_x and
                camera_y <= hunter.y < camera_y + tiles_y):

                tile = self.game.game_map.get_tile(hunter.x, hunter.y)
                if tile.explored and self.game.fog_of_war.is_visible(hunter.x, hunter.y, self.game.player.x, self.game.player.y):
                    if not hunter.is_alive:
                        continue

                    screen_x = (hunter.x - camera_x) * TILE_SIZE
                    screen_y = (hunter.y - camera_y) * TILE_SIZE

                    # Коричнево-зеленый для охотников
                    if hunter.state == "hunt":
                        hunter_color = (200, 150, 50)  # Оранжевый при охоте
                    elif hunter.state == "rest":
                        hunter_color = (100, 80, 50)  # Темный при отдыхе
                    else:
                        hunter_color = (139, 120, 85)  # Коричневый

                    def draw_hunter_default(screen=self.game.screen, color=hunter_color,
                                           sx=screen_x, sy=screen_y):
                        # Квадрат для охотника
                        pygame.draw.rect(
                            screen,
                            color,
                            (sx + TILE_SIZE // 4,
                             sy + TILE_SIZE // 4,
                             TILE_SIZE // 2,
                             TILE_SIZE // 2)
                        )

                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'hunter', screen_x, screen_y,
                        draw_hunter_default, hunter.level
                    )

    def _render_necromancers(self, tiles_x, tiles_y, camera_x, camera_y):
        """Отрисовка некромантов"""
        for necromancer in self.game.necromancers:
            if (camera_x <= necromancer.x < camera_x + tiles_x and
                camera_y <= necromancer.y < camera_y + tiles_y):

                tile = self.game.game_map.get_tile(necromancer.x, necromancer.y)
                if tile.explored and self.game.fog_of_war.is_visible(necromancer.x, necromancer.y, self.game.player.x, self.game.player.y):
                    if not necromancer.is_alive:
                        continue

                    screen_x = (necromancer.x - camera_x) * TILE_SIZE
                    screen_y = (necromancer.y - camera_y) * TILE_SIZE

                    # Темно-фиолетовый для некромантов
                    if necromancer.state == "combat":
                        necro_color = (180, 50, 180)  # Яркий при бое
                    else:
                        necro_color = (100, 20, 120)  # Темный

                    def draw_necro_default(screen=self.game.screen, color=necro_color,
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

                    self.game.sprite_manager.render_npc(
                        self.game.screen, 'necromancer', screen_x, screen_y,
                        draw_necro_default, necromancer.level
                    )

    def _render_player(self, camera_x, camera_y):
        """Отрисовка игрока"""
        player_screen_x = (self.game.player.x - camera_x) * TILE_SIZE
        player_screen_y = (self.game.player.y - camera_y) * TILE_SIZE

        # Функция отрисовки по умолчанию (геометрическая фигура)
        def draw_player_default():
            pygame.draw.circle(
                self.game.screen,
                COLORS['player'],
                (player_screen_x + TILE_SIZE // 2, player_screen_y + TILE_SIZE // 2),
                TILE_SIZE // 3
            )

        # Отрисовка игрока (спрайт или геометрическая фигура)
        self.game.sprite_manager.render_npc(
            self.game.screen, 'player', player_screen_x, player_screen_y,
            draw_player_default, self.game.player.level
        )

    def render_minimap(self):
        """Отрисовка мини-карты"""
        # Размеры мини-карты (масштабируются под разрешение)
        minimap_size = self.game.ui_scaler.scale_value(150)
        margin = self.game.ui_scaler.scale_value(10)
        minimap_x = self.game.window_width - minimap_size - margin
        minimap_y = margin
        pixel_per_tile = minimap_size / 100  # Адаптивный размер тайла

        # Фон мини-карты
        pygame.draw.rect(
            self.game.screen,
            (20, 20, 25),
            (minimap_x, minimap_y, minimap_size, minimap_size)
        )

        # Рамка мини-карты
        pygame.draw.rect(
            self.game.screen,
            COLORS['text'],
            (minimap_x, minimap_y, minimap_size, minimap_size),
            2
        )

        # Вычисляем область карты для отображения (вокруг игрока)
        map_view_radius = int(minimap_size / pixel_per_tile / 2)

        for dy in range(-map_view_radius, map_view_radius):
            for dx in range(-map_view_radius, map_view_radius):
                map_x = self.game.player.x + dx
                map_y = self.game.player.y + dy

                if not self.game.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game.game_map.get_tile(map_x, map_y)

                # Отображаем только исследованные тайлы
                if tile.explored:
                    # Позиция на мини-карте
                    minimap_px = minimap_x + int((dx + map_view_radius) * pixel_per_tile)
                    minimap_py = minimap_y + int((dy + map_view_radius) * pixel_per_tile)

                    # Определяем цвет
                    if tile.has_location():
                        color = COLORS.get(tile.location.location_type, COLORS['background'])
                    else:
                        color = COLORS.get(tile.biome, COLORS['background'])

                    # Затемняем цвет для мини-карты
                    color = tuple(c // 2 for c in color)

                    # Отрисовка пикселя тайла
                    pygame.draw.rect(
                        self.game.screen,
                        color,
                        (minimap_px, minimap_py, int(pixel_per_tile), int(pixel_per_tile))
                    )

        # Отметка игрока на мини-карте (в центре)
        player_minimap_x = minimap_x + minimap_size // 2
        player_minimap_y = minimap_y + minimap_size // 2

        pygame.draw.circle(
            self.game.screen,
            COLORS['player'],
            (player_minimap_x, player_minimap_y),
            3
        )

        # Заголовок мини-карты
        minimap_font_size = self.game.ui_scaler.scale_font_size(16)
        minimap_font = pygame.font.Font(None, minimap_font_size)
        minimap_title = minimap_font.render("Карта", True, COLORS['text'])
        title_offset = self.game.ui_scaler.scale_value(18)
        self.game.screen.blit(minimap_title, (minimap_x + 5, minimap_y - title_offset))
