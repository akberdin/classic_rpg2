"""
Основной класс игры
"""
import pygame
import random
from game.map import GameMap
from game.character import Player, Guard, Merchant
from game.fog_of_war import FogOfWar
from game.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE, COLORS, LOCATION_CITY, LOCATION_VILLAGE
)


class Game:
    """Главный класс игры"""

    def __init__(self):
        """Инициализация игры"""
        # Окно игры
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Classic RPG")

        # Часы для контроля FPS
        self.clock = pygame.time.Clock()
        self.running = True

        # Игровое время (часы и дни)
        self.game_hour = 6  # Начало игры в 6 утра
        self.game_day = 1

        # Генерация карты
        print("Генерация карты...")
        self.game_map = GameMap()

        # Создание игрока
        spawn_x, spawn_y = self.game_map.find_spawn_point()
        self.player = Player("Герой", spawn_x, spawn_y)

        # Система тумана войны
        self.fog_of_war = FogOfWar(self.game_map)
        self.fog_of_war.update_vision(self.player.x, self.player.y)

        # Камера (смещение для отображения карты)
        self.camera_x = 0
        self.camera_y = 0
        self._update_camera()

        # Шрифт для текста
        self.font = pygame.font.Font(None, 24)
        self.info_font = pygame.font.Font(None, 20)

        # Создание стражников в городах
        self.guards = []
        self._spawn_guards()

        # Создание торговцев
        self.merchants = []
        self._spawn_merchants()

        print(f"Игрок создан на позиции ({self.player.x}, {self.player.y})")
        print(f"Создано {len(self.guards)} стражников")
        print(f"Создано {len(self.merchants)} торговцев")
        print("Игра готова к запуску!")

    def _spawn_guards(self):
        """Создание стражников в городах"""
        # Находим все города на карте
        cities = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_CITY]

        for city in cities:
            # Создаем 2-3 стражников возле каждого города
            num_guards = random.randint(2, 3)

            for i in range(num_guards):
                # Находим позицию рядом с городом
                guard_pos = self._find_guard_position(city.x, city.y)
                if guard_pos:
                    gx, gy = guard_pos
                    guard_level = random.randint(5, 15)
                    guard = Guard(f"Стражник {city.name}", gx, gy, guard_level)

                    # Создаем маршрут патрулирования вокруг города
                    patrol_route = self._create_patrol_route(gx, gy, radius=5)
                    guard.set_patrol_route(patrol_route)

                    self.guards.append(guard)

    def _find_guard_position(self, center_x, center_y):
        """Найти позицию для стражника рядом с городом"""
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy

                    if self.game_map.is_valid_position(x, y):
                        tile = self.game_map.get_tile(x, y)
                        if tile.is_passable() and not tile.has_location():
                            return (x, y)
        return None

    def _create_patrol_route(self, center_x, center_y, radius=5):
        """Создать маршрут патрулирования вокруг точки"""
        route = [
            (center_x + radius, center_y),
            (center_x + radius, center_y + radius),
            (center_x, center_y + radius),
            (center_x - radius, center_y + radius),
            (center_x - radius, center_y),
            (center_x - radius, center_y - radius),
            (center_x, center_y - radius),
            (center_x + radius, center_y - radius),
        ]
        return route

    def _spawn_merchants(self):
        """Создание торговцев, курсирующих между населенными пунктами"""
        # Находим все города и деревни на карте
        settlements = [loc for loc in self.game_map.locations
                      if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        if len(settlements) < 2:
            # Нужно как минимум 2 населенных пункта для торговцев
            return

        # Создаем 3-5 торговцев
        num_merchants = random.randint(3, 5)

        for i in range(num_merchants):
            # Выбираем случайный стартовый населенный пункт
            start_settlement = random.choice(settlements)

            # Находим позицию рядом с населенным пунктом
            merchant_pos = self._find_guard_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                merchant_level = random.randint(3, 8)
                merchant_names = [
                    "Торговец Иван", "Купец Петр", "Торговка Мария",
                    "Купец Василий", "Торговец Николай", "Купчиха Анна",
                    "Странствующий торговец", "Заезжий купец"
                ]
                merchant_name = random.choice(merchant_names)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)

                self.merchants.append(merchant)

    def advance_time(self, hours=1):
        """
        Продвинуть игровое время на указанное количество часов

        Args:
            hours: Количество часов для продвижения
        """
        self.game_hour += hours

        # Если прошло 24 часа, начинается новый день
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1

        # Обновляем AI всех NPC при изменении времени
        for _ in range(hours):
            for guard in self.guards:
                guard.update_ai(self.game_map)
            for merchant in self.merchants:
                merchant.update_ai(self.game_map)

    def get_time_string(self):
        """
        Получить строковое представление времени

        Returns:
            str: Время в формате "День X, ЧЧ:00"
        """
        return f"День {self.game_day}, {self.game_hour:02d}:00"

    def run(self):
        """Главный игровой цикл"""
        while self.running:
            # Обработка событий
            self._handle_events()

            # Обновление состояния игры
            self._update()

            # Отрисовка
            self._render()

            # Ограничение FPS
            self.clock.tick(FPS)

    def _handle_events(self):
        """Обработка событий ввода"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Обработка нажатий клавиш
            if event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)

    def _handle_key_press(self, key):
        """
        Обработка нажатия клавиш

        Args:
            key: Код нажатой клавиши
        """
        # Движение игрока (стрелки или WASD)
        moved = False
        new_x, new_y = self.player.x, self.player.y

        if key == pygame.K_UP or key == pygame.K_w:
            new_y -= 1
            moved = True
        elif key == pygame.K_DOWN or key == pygame.K_s:
            new_y += 1
            moved = True
        elif key == pygame.K_LEFT or key == pygame.K_a:
            new_x -= 1
            moved = True
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            new_x += 1
            moved = True
        elif key == pygame.K_r:
            # Отдых - восстанавливает здоровье и ману, занимает 1 час
            self.player.rest()
            self.advance_time(1)
            print(f"Вы отдохнули. {self.get_time_string()}")
            return
        elif key == pygame.K_t:
            # Работа - получение опыта и золота, занимает 1 час
            self.player.work()
            self.advance_time(1)
            print(f"Вы поработали. {self.get_time_string()}")
            return
        elif key == pygame.K_ESCAPE:
            self.running = False

        # Попытка переместить игрока
        if moved:
            if self.player.move_to(new_x, new_y, self.game_map):
                # Продвигаем время на 1 час за перемещение
                self.advance_time(1)

                # Обновляем туман войны
                self.fog_of_war.update_vision(self.player.x, self.player.y)
                # Обновляем камеру
                self._update_camera()

                # Проверяем, есть ли локация на новой позиции
                tile = self.game_map.get_tile(self.player.x, self.player.y)
                if tile.has_location():
                    print(f"Вы прибыли в: {tile.location.name}")
                    print(f"  {tile.location.get_description()}")
                    print(f"Время: {self.get_time_string()}")

    def _update(self):
        """Обновление состояния игры"""
        # AI стражников обновляется в методе advance_time
        pass

    def _update_camera(self):
        """Обновление позиции камеры, чтобы следить за игроком"""
        # Вычисляем размер видимой области в тайлах
        tiles_x = WINDOW_WIDTH // TILE_SIZE
        tiles_y = (WINDOW_HEIGHT - 100) // TILE_SIZE  # -100 для UI панели

        # Центрируем камеру на игроке
        self.camera_x = self.player.x - tiles_x // 2
        self.camera_y = self.player.y - tiles_y // 2

        # Ограничиваем камеру границами карты
        self.camera_x = max(0, min(self.camera_x, self.game_map.width - tiles_x))
        self.camera_y = max(0, min(self.camera_y, self.game_map.height - tiles_y))

    def _render(self):
        """Отрисовка игры"""
        # Очистка экрана
        self.screen.fill(COLORS['background'])

        # Отрисовка карты
        self._render_map()

        # Отрисовка UI
        self._render_ui()

        # Обновление дисплея
        pygame.display.flip()

    def _render_map(self):
        """Отрисовка карты с учетом камеры и тумана войны"""
        # Вычисляем видимую область
        tiles_x = WINDOW_WIDTH // TILE_SIZE + 1
        tiles_y = (WINDOW_HEIGHT - 100) // TILE_SIZE + 1

        for dy in range(tiles_y):
            for dx in range(tiles_x):
                # Координаты тайла на карте
                map_x = self.camera_x + dx
                map_y = self.camera_y + dy

                # Проверяем валидность координат
                if not self.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game_map.get_tile(map_x, map_y)

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
                    if not self.fog_of_war.is_visible(map_x, map_y, self.player.x, self.player.y):
                        color = tuple(c // 2 for c in color)  # Затемняем цвет

                    # Отрисовка тайла
                    pygame.draw.rect(
                        self.screen,
                        color,
                        (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    )
                else:
                    # Неисследованная область - туман войны
                    pygame.draw.rect(
                        self.screen,
                        COLORS['fog'],
                        (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    )

        # Отрисовка надписей над локациями
        label_font = pygame.font.Font(None, 16)
        for dy in range(tiles_y):
            for dx in range(tiles_x):
                map_x = self.camera_x + dx
                map_y = self.camera_y + dy

                if not self.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game_map.get_tile(map_x, map_y)

                # Отрисовываем название локации, если она видима и исследована
                if tile.explored and tile.has_location():
                    if self.fog_of_war.is_visible(map_x, map_y, self.player.x, self.player.y):
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
                        self.screen.blit(background_surface, (label_rect.x - 2, label_rect.y - 1))

                        # Отрисовка надписи
                        self.screen.blit(location_label, label_rect)

        # Отрисовка стражников
        for guard in self.guards:
            # Проверяем, находится ли стражник в зоне видимости камеры
            if (self.camera_x <= guard.x < self.camera_x + tiles_x and
                self.camera_y <= guard.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы стражника (туман войны)
                tile = self.game_map.get_tile(guard.x, guard.y)
                if tile.explored and self.fog_of_war.is_visible(guard.x, guard.y, self.player.x, self.player.y):
                    guard_screen_x = (guard.x - self.camera_x) * TILE_SIZE
                    guard_screen_y = (guard.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния стражника
                    if guard.state == "rest":
                        guard_color = (100, 100, 200)  # Синий оттенок для отдыха
                    else:
                        guard_color = (0, 100, 200)    # Темно-синий для патруля

                    # Отрисовка стражника
                    pygame.draw.circle(
                        self.screen,
                        guard_color,
                        (guard_screen_x + TILE_SIZE // 2, guard_screen_y + TILE_SIZE // 2),
                        TILE_SIZE // 3
                    )

        # Отрисовка торговцев
        for merchant in self.merchants:
            # Проверяем, находится ли торговец в зоне видимости камеры
            if (self.camera_x <= merchant.x < self.camera_x + tiles_x and
                self.camera_y <= merchant.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы торговца (туман войны)
                tile = self.game_map.get_tile(merchant.x, merchant.y)
                if tile.explored and self.fog_of_war.is_visible(merchant.x, merchant.y, self.player.x, self.player.y):
                    merchant_screen_x = (merchant.x - self.camera_x) * TILE_SIZE
                    merchant_screen_y = (merchant.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния торговца
                    if merchant.state == "rest":
                        merchant_color = (150, 100, 50)  # Коричневый для отдыха/торговли
                    else:
                        merchant_color = (200, 150, 50)  # Оранжево-коричневый для путешествия

                    # Отрисовка торговца (квадрат для отличия от стражников)
                    pygame.draw.rect(
                        self.screen,
                        merchant_color,
                        (merchant_screen_x + TILE_SIZE // 4,
                         merchant_screen_y + TILE_SIZE // 4,
                         TILE_SIZE // 2,
                         TILE_SIZE // 2)
                    )

        # Отрисовка игрока (поверх всего остального)
        player_screen_x = (self.player.x - self.camera_x) * TILE_SIZE
        player_screen_y = (self.player.y - self.camera_y) * TILE_SIZE

        pygame.draw.circle(
            self.screen,
            COLORS['player'],
            (player_screen_x + TILE_SIZE // 2, player_screen_y + TILE_SIZE // 2),
            TILE_SIZE // 3
        )

    def _render_ui(self):
        """Отрисовка пользовательского интерфейса"""
        # Панель внизу экрана
        ui_height = 100
        ui_y = WINDOW_HEIGHT - ui_height

        # Фон панели
        pygame.draw.rect(
            self.screen,
            (32, 32, 32),
            (0, ui_y, WINDOW_WIDTH, ui_height)
        )

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (0, ui_y),
            (WINDOW_WIDTH, ui_y),
            2
        )

        # Информация об игроке
        info_x = 20
        info_y = ui_y + 10

        # Имя и позиция
        name_text = self.font.render(f"{self.player.name}", True, COLORS['text'])
        self.screen.blit(name_text, (info_x, info_y))

        pos_text = self.info_font.render(
            f"Позиция: ({self.player.x}, {self.player.y})",
            True,
            COLORS['text']
        )
        self.screen.blit(pos_text, (info_x, info_y + 30))

        # Уровень, ранг и опыт
        player_rank = self.player.get_rank()
        level_text = self.info_font.render(
            f"Уровень: {self.player.level} ({player_rank}) | Опыт: {self.player.experience}/{self.player.experience_to_next_level}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(level_text, (info_x, info_y + 55))

        # Здоровье и мана
        health_text = self.info_font.render(
            f"Здоровье: {self.player.health}/{self.player.max_health}",
            True,
            (255, 100, 100)
        )
        self.screen.blit(health_text, (info_x + 400, info_y + 55))

        mana_text = self.info_font.render(
            f"Мана: {self.player.mana}/{self.player.max_mana}",
            True,
            (100, 150, 255)
        )
        self.screen.blit(mana_text, (info_x + 650, info_y + 55))

        # Характеристики
        stats = self.player.get_stats()
        stats_x = 300
        stats_text = [
            f"Сила: {stats['strength']}",
            f"Ловкость: {stats['dexterity']}",
            f"Телосложение: {stats['constitution']}",
            f"Дух: {stats['spirit']}",
            f"Интеллект: {stats['intelligence']}",
            f"Удача: {stats['luck']}"
        ]

        for i, text in enumerate(stats_text):
            stat_surface = self.info_font.render(text, True, COLORS['text'])
            self.screen.blit(stat_surface, (stats_x + (i % 3) * 150, info_y + (i // 3) * 25))

        # Информация о локации (перенесена вниз)
        tile = self.game_map.get_tile(self.player.x, self.player.y)
        if tile.has_location():
            location_text = self.info_font.render(
                f"Локация: {tile.location.name}",
                True,
                (255, 255, 0)
            )
            self.screen.blit(location_text, (info_x, info_y + 75))

        # Игровое время
        time_text = self.font.render(
            self.get_time_string(),
            True,
            (255, 215, 0)
        )
        self.screen.blit(time_text, (info_x + 900, info_y))

        # Управление
        controls_text = self.info_font.render(
            "WASD - движение | R - отдых | T - работа | ESC - выход",
            True,
            (180, 180, 180)
        )
        self.screen.blit(controls_text, (WINDOW_WIDTH - 500, info_y + 70))
