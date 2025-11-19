"""
Основной класс игры
"""
import pygame
import random
import ctypes
import platform
from game.map import GameMap
from game.character import Player
from game.npc import Merchant
from game.fog_of_war import FogOfWar
from game.combat import CombatSystem
from game.inventory import get_random_loot_from_location, PREDEFINED_ITEMS
from game.ui import HelpWindow, InventoryWindow, TradeWindow, UIHelper, CharacterWindow, UIScaler
from game.optimization import PerformanceOptimizer, RenderCache
from game.quests import QuestManager, AchievementManager, create_starter_quests
from game.save_system import SaveSystem
from game.constants import (
    FPS, TILE_SIZE, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT,
    LOCATION_CITY, LOCATION_VILLAGE
)

# Импорт новых модулей
from game.npc_spawner import NPCSpawner, give_starting_items
from game.input_handler import InputHandler
from game.world_renderer import WorldRenderer
from game.game_time import GameTime
from game.camera import Camera
from game.respawn_manager import RespawnManager


class Game:
    """Главный класс игры"""

    def __init__(self):
        """Инициализация игры"""
        # Для Windows: сообщаем системе, что процесс умеет работать с DPI
        if platform.system() == 'Windows':
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass  # Игнорируем ошибки на не-Windows системах

        # Создаем полноэкранное окно с нативным разрешением рабочего стола
        # Передаем (0, 0) чтобы pygame использовал текущее разрешение без смены видеорежима
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # Получаем фактические размеры созданного окна
        self.window_width = self.screen.get_width()
        self.window_height = self.screen.get_height()

        # Ограничиваем максимальными значениями из констант (на случай очень больших мониторов)
        if self.window_width > WINDOW_WIDTH or self.window_height > WINDOW_HEIGHT:
            self.window_width = min(self.window_width, WINDOW_WIDTH)
            self.window_height = min(self.window_height, WINDOW_HEIGHT)
            # Пересоздаём окно с ограниченным разрешением
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.FULLSCREEN
            )

        pygame.display.set_caption("Classic RPG")

        # Создаем масштабировщик UI для адаптивности
        self.ui_scaler = UIScaler(self.window_width, self.window_height)

        print(f"Инициализация игры с разрешением: {self.window_width}x{self.window_height}")

        # Часы для контроля FPS
        self.clock = pygame.time.Clock()
        self.running = True

        # Генерация карты
        print("Генерация карты...")
        self.game_map = GameMap()

        # Создание игрока
        spawn_x, spawn_y = self.game_map.find_spawn_point()
        self.player = Player("Герой", spawn_x, spawn_y)

        # Система тумана войны
        self.fog_of_war = FogOfWar(self.game_map)
        self.fog_of_war.update_vision(self.player.x, self.player.y)

        # Инициализация игрового времени
        self.game_time = GameTime(self)

        # Инициализация камеры
        self.camera = Camera(self)
        self.camera.update()

        # Шрифт для текста (адаптивные размеры)
        font_size = self.ui_scaler.scale_font_size(24)
        info_font_size = self.ui_scaler.scale_font_size(20)
        self.font = pygame.font.Font(None, font_size)
        self.info_font = pygame.font.Font(None, info_font_size)

        # Система боя
        self.combat_system = None
        self.in_combat = False

        # Система взаимодействия с NPC
        self.interaction_menu_open = False
        self.nearby_npc = None

        # UI компоненты (с передачей scaler для адаптивности)
        self.help_window = HelpWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.inventory_window = InventoryWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.trade_window = TradeWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.character_window = CharacterWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        from game.ui import SkillBookWindow, LootWindow
        self.skill_book_window = SkillBookWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.loot_window = LootWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Состояния окон
        self.inventory_menu_open = False
        self.trade_menu_open = False
        self.character_menu_open = False
        self.skill_book_menu_open = False
        self.loot_window_open = False

        # Менеджер спрайтов
        from game.sprite_manager import SpriteManager
        self.sprite_manager = SpriteManager(tile_size=TILE_SIZE)
        print(f"Менеджер спрайтов инициализирован")

        # Создание NPC с помощью спавнера
        npc_spawner = NPCSpawner(self.game_map)
        npcs = npc_spawner.spawn_all_npcs()

        self.guards = npcs['guards']
        self.merchants = npcs['merchants']
        self.mages = npcs['mages']
        self.bandits = npcs['bandits']
        self.miners = npcs['miners']
        self.undead = npcs['undead']

        print(f"Игрок создан на позиции ({self.player.x}, {self.player.y})")
        print(f"Создано {len(self.guards)} стражников")
        print(f"Создано {len(self.merchants)} торговцев")
        print(f"Создано {len(self.mages)} магов-патрульных")
        print(f"Создано {len(self.bandits)} бандитов")
        print(f"Создано {len(self.miners)} шахтеров")
        print(f"Создано {len(self.undead)} нежити")

        # Инициализация менеджера респавна
        self.respawn_manager = RespawnManager(self.game_map)

        # Даем игроку стартовые предметы
        give_starting_items(self.player)

        # Инициализация оптимизатора производительности
        self.performance_optimizer = PerformanceOptimizer()
        self.render_cache = RenderCache()

        # Инициализация менеджера квестов
        self.quest_manager = QuestManager()
        for quest in create_starter_quests():
            self.quest_manager.add_available_quest(quest)

        # Инициализация менеджера достижений
        self.achievement_manager = AchievementManager()

        # Даем игроку стартовые умения
        self.player.skill_manager.learn_skill('basic_attack')  # Базовая атака
        self.player.skill_manager.learn_skill('mining')  # Рудокоп ранг 1
        self.player.skill_manager.learn_skill('lumberjacking')  # Лесоруб ранг 1
        self.player.skill_manager.learn_skill('heal')  # Лечение (магия)

        # Назначаем умения в слоты
        self.player.skill_manager.assign_to_slot('basic_attack', 0)  # Слот 1
        self.player.skill_manager.assign_to_slot('mining', 1)  # Слот 2
        self.player.skill_manager.assign_to_slot('lumberjacking', 2)  # Слот 3
        self.player.skill_manager.assign_to_slot('heal', 3)  # Слот 4

        # Перестраиваем spatial grid для NPC
        all_npcs = self.guards + self.merchants + self.mages + self.bandits + self.miners + self.undead
        self.performance_optimizer.rebuild_spatial_grid(all_npcs)

        # Чит-режим (отключен по умолчанию)
        self.cheat_mode_active = False
        self.cheat_gold_given = False  # Флаг для выдачи золота один раз

        # Инициализация обработчика ввода
        self.input_handler = InputHandler(self)

        # Инициализация рендерера мира
        self.world_renderer = WorldRenderer(self)

        print("Игра готова к запуску!")

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

            # Если идет бой, передаем управление боевой системе
            if self.in_combat and self.combat_system:
                result = self.combat_system.handle_input(event)
                if result == "victory":
                    # Генерируем лут
                    defeated_enemy = self.combat_system.enemy
                    loot_items, loot_gold = self._generate_loot(defeated_enemy)

                    # Добавляем лут в инвентарь игрока
                    self.player.inventory.add_gold(loot_gold)
                    for item, quantity in loot_items:
                        self.player.inventory.add_item(item, quantity)

                    # Показываем окно лута
                    self.loot_window.set_loot(loot_items, loot_gold, defeated_enemy.name)
                    self.loot_window_open = True

                    self.in_combat = False
                    self.combat_system = None
                    print("Победа в бою!")
                elif result == "defeat":
                    self.in_combat = False
                    self.combat_system = None
                    print("Поражение в бою! Игра окончена.")
                    self.running = False
                elif result == "fled":
                    self.in_combat = False
                    self.combat_system = None
                    print("Вы сбежали из боя!")
                continue

            # Если открыто меню взаимодействия, обрабатываем выбор
            if self.interaction_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_interaction_choice(event.key)
                continue

            # Если открыто меню инвентаря, обрабатываем его
            if self.inventory_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_inventory_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # ПКМ
                        self.input_handler.handle_inventory_right_click(event.pos)
                continue

            # Если открыто меню торговли, обрабатываем его
            if self.trade_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_trade_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # ПКМ
                        self.input_handler.handle_trade_right_click(event.pos)
                continue

            # Если открыто окно характеристик, обрабатываем его
            if self.character_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_character_input(event.key)
                continue

            # Если открыто окно книги умений, обрабатываем его
            if self.skill_book_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_skill_book_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Обработка событий мыши в книге умений
                    self.skill_book_window.handle_mouse_event(event, self.player)
                continue

            # Если открыто окно лута, обрабатываем его
            if self.loot_window_open:
                if event.type == pygame.KEYDOWN:
                    self.loot_window_open = False
                continue

            # Обработка нажатий клавиш
            if event.type == pygame.KEYDOWN:
                self.input_handler.handle_key_press(event.key)

    def _check_npc_nearby(self):
        """Проверить наличие NPC рядом с игроком и открыть меню взаимодействия"""
        # Сначала проверяем, находимся ли мы в городе или деревне
        tile = self.game_map.get_tile(self.player.x, self.player.y)
        if tile.has_location():
            location = tile.location
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                # Открываем торговое окно для города/деревни
                # Создаем временного торговца для этой локации
                if not hasattr(location, 'merchant_npc'):
                    # Создаем постоянного торговца для этой локации
                    merchant_level = 10 if location.location_type == LOCATION_CITY else 5
                    location.merchant_npc = Merchant(f"Торговец {location.name}", self.player.x, self.player.y, merchant_level)
                    # Пополняем товары
                    location.merchant_npc.restock_goods()

                self.nearby_npc = location.merchant_npc
                self.trade_menu_open = True
                self.trade_window.mode = "buy"
                self.trade_window.selected_merchant_index = 0
                self.trade_window.selected_player_index = 0
                print(f"Добро пожаловать в {location.name}! Вы можете торговать здесь.")
                return

        # Собираем всех NPC (включая miners и undead)
        all_npcs = self.guards + self.merchants + self.bandits + self.miners + self.undead

        # Ищем NPC рядом с игроком (в соседних клетках)
        for npc in all_npcs:
            if not npc.is_alive:
                continue

            distance = abs(self.player.x - npc.x) + abs(self.player.y - npc.y)
            if distance <= 1:  # Соседняя клетка
                self.nearby_npc = npc
                self.interaction_menu_open = True
                print(f"Вы встретили: {npc.name}")
                return

        print("Рядом нет NPC для взаимодействия и вы не находитесь в городе/деревне!")

    def _collect_resources(self):
        """Собрать ресурсы с текущей локации"""
        tile = self.game_map.get_tile(self.player.x, self.player.y)

        if not tile.has_location():
            print("Здесь нечего собирать!")
            return

        location = tile.location

        if not location.can_collect_loot:
            print(f"{location.name} не содержит ресурсов для сбора.")
            return

        if location.loot_collected:
            print(f"Вы уже собрали ресурсы с {location.name}.")
            return

        # Получаем лут с локации (передаем уровень игрока для более интересного лута)
        loot = get_random_loot_from_location(location.location_type, self.player.level)

        if not loot:
            print("Ничего не найдено!")
            return

        # Добавляем лут в инвентарь
        for item, quantity in loot:
            if self.player.inventory.add_item(item, quantity):
                print(f"Найдено: {item.name} x{quantity}")
            else:
                print(f"Инвентарь полон! Не удалось подобрать {item.name}")

        # Помечаем локацию как обыскованную
        location.loot_collected = True

        # Обновляем прогресс квеста "Охотник за сокровищами"
        self.player.resources_collected += 1
        self.quest_manager.update_quest_progress("treasure_hunter", 0, 1)

        # Добавляем тип локации в посещенные
        self.player.visited_location_types.add(location.location_type)

        # Продвигаем время на 1 час
        self.game_time.advance_time(1)
        print(f"Время: {self.game_time.get_time_string()}")

    def _start_combat(self, enemy):
        """
        Начать бой с NPC

        Args:
            enemy: Враг для боя
        """
        print(f"Бой начался с {enemy.name}!")
        self.combat_system = CombatSystem(self.player, enemy, self.screen, self.font, self.ui_scaler, self.game_map, self.respawn_manager)
        self.in_combat = True
        self.nearby_npc = None

    def _update(self):
        """Обновление состояния игры"""
        # AI стражников обновляется в методе advance_time

        # Чит-мод: восстанавливаем здоровье, ману и выносливость (с учетом бонусов от экипировки)
        if self.cheat_mode_active:
            self.player.health = self.player.get_effective_max_health()
            self.player.stamina = self.player.get_effective_max_stamina()
            self.player.mana = self.player.get_effective_max_mana()
            self.player.is_resting = False

    def _render(self):
        """Отрисовка игры"""
        # Очистка экрана
        self.screen.fill(COLORS['background'])

        # Отрисовка карты
        self.world_renderer.render_map()

        # Отрисовка UI
        self._render_ui()

        # Отрисовка мини-карты
        self.world_renderer.render_minimap()

        # Если идет бой, отрисовываем окно боя
        if self.in_combat and self.combat_system:
            self.combat_system.render()

        # Если открыто меню взаимодействия, отрисовываем его
        if self.interaction_menu_open and self.nearby_npc:
            self._render_interaction_menu()

        # Если открыто меню инвентаря, отрисовываем его
        if self.inventory_menu_open:
            mouse_pos = pygame.mouse.get_pos()
            self.inventory_window.render(self.player, mouse_pos)

        # Если открыто меню торговли, отрисовываем его
        if self.trade_menu_open and self.nearby_npc:
            trade_mouse_pos = pygame.mouse.get_pos()
            self.trade_window.render(self.player, self.nearby_npc, trade_mouse_pos)

        # Если открыто окно характеристик, отрисовываем его
        if self.character_menu_open:
            self.character_window.render(self.player)

        # Если открыто окно книги умений, отрисовываем его
        if self.skill_book_menu_open:
            self.skill_book_window.render(self.player)

        # Если открыто окно лута, отрисовываем его
        if self.loot_window_open:
            self.loot_window.render()

        # Отрисовка окна помощи (поверх всего)
        self.help_window.render()

        # Обновление дисплея
        pygame.display.flip()

    def _render_ui(self):
        """Отрисовка пользовательского интерфейса"""
        # Панель внизу экрана (масштабируется под разрешение)
        ui_height = self.ui_scaler.scale_height(100)
        ui_y = self.window_height - ui_height

        # Фон панели
        pygame.draw.rect(
            self.screen,
            (32, 32, 32),
            (0, ui_y, self.window_width, ui_height)
        )

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (0, ui_y),
            (self.window_width, ui_y),
            2
        )

        # Информация об игроке
        info_x = 20
        info_y = ui_y + 10

        # Имя и уровень
        player_rank = self.player.get_rank()
        name_text = self.font.render(
            f"{self.player.name} | Ур: {self.player.level} ({player_rank})",
            True,
            COLORS['text']
        )
        self.screen.blit(name_text, (info_x, info_y))

        # Игровое время и золото
        time_gold_text = self.info_font.render(
            f"{self.game_time.get_time_string()} | Золото: {self.player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        time_gold_x = self.window_width - self.ui_scaler.scale_width(350)
        self.screen.blit(time_gold_text, (time_gold_x, info_y + 5))

        # Прогресс-бары
        bar_y = info_y + 35
        # Масштабируем размеры и позиции под ширину экрана
        bar_width = self.ui_scaler.scale_width(350)
        bar_height = 18
        bar_spacing = self.ui_scaler.scale_width(30)  # Расстояние между полосами

        # Получаем эффективные максимумы с учетом экипировки
        effective_max_health = self.player.get_effective_max_health()
        effective_max_mana = self.player.get_effective_max_mana()
        effective_max_stamina = self.player.get_effective_max_stamina()

        # Вычисляем проценты
        health_percent = int((self.player.health / effective_max_health * 100) if effective_max_health > 0 else 0)
        mana_percent = int((self.player.mana / effective_max_mana * 100) if effective_max_mana > 0 else 0)
        stamina_percent = int((self.player.stamina / effective_max_stamina * 100) if effective_max_stamina > 0 else 0)

        # Полоса здоровья (красная)
        UIHelper.draw_progress_bar(
            self.screen,
            info_x, bar_y, bar_width, bar_height,
            self.player.health, effective_max_health,
            bg_color=(60, 20, 20),
            fill_color=(200, 50, 50),
            border_color=(255, 100, 100),
            text=f"HP: {self.player.health}/{effective_max_health} ({health_percent}%)",
            font=self.info_font
        )

        # Полоса маны (синяя)
        mana_x = info_x + bar_width + bar_spacing
        UIHelper.draw_progress_bar(
            self.screen,
            mana_x, bar_y, bar_width, bar_height,
            self.player.mana, effective_max_mana,
            bg_color=(20, 20, 60),
            fill_color=(50, 100, 200),
            border_color=(100, 150, 255),
            text=f"MP: {self.player.mana}/{effective_max_mana} ({mana_percent}%)",
            font=self.info_font
        )

        # Полоса выносливости (оранжевая)
        stamina_x = mana_x + bar_width + bar_spacing
        stamina_color = (200, 120, 50) if not self.player.is_resting else (150, 70, 30)
        stamina_status = " [ОТДЫХ]" if self.player.is_resting else ""
        UIHelper.draw_progress_bar(
            self.screen,
            stamina_x, bar_y, bar_width, bar_height,
            self.player.stamina, effective_max_stamina,
            bg_color=(60, 40, 20),
            fill_color=stamina_color,
            border_color=(255, 165, 0),
            text=f"Stamina: {self.player.stamina}/{effective_max_stamina} ({stamina_percent}%){stamina_status}",
            font=self.info_font
        )

        # Опыт и информация о статах (компактно)
        exp_text = self.info_font.render(
            f"Опыт: {self.player.experience}/{self.player.experience_to_next_level}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(exp_text, (info_x, bar_y + 30))

        # Нераспределенные очки характеристик (если есть)
        if self.player.stat_points > 0:
            stat_points_text = self.info_font.render(
                f"Свободных очков: {self.player.stat_points} [Нажми C]",
                True,
                (100, 255, 100)
            )
            stat_points_x = self.ui_scaler.scale_width(320)
            self.screen.blit(stat_points_text, (stat_points_x, bar_y + 30))

        # Подсказка о помощи
        help_hint = self.info_font.render(
            "F1 - Справка | C - Характеристики | I - Инвентарь | K - Книга умений",
            True,
            (180, 180, 180)
        )
        help_hint_x = self.ui_scaler.scale_width(800)
        self.screen.blit(help_hint, (help_hint_x, info_y + 55))

        # Панель умений (8 слотов)
        self._render_skill_panel()

    def _render_skill_panel(self):
        """Отрисовка панели умений над панелью параметров"""
        # Размеры и позиция (масштабируются под разрешение)
        slot_size = self.ui_scaler.scale_value(48)
        slot_spacing = self.ui_scaler.scale_value(8)
        panel_x = (self.window_width - (slot_size + slot_spacing) * 8) // 2
        # Поднимаем над панелью параметров
        ui_height = self.ui_scaler.scale_height(100)
        ui_y = self.window_height - ui_height
        panel_offset = self.ui_scaler.scale_value(15)
        panel_y = ui_y - slot_size - panel_offset

        # Отрисовываем 8 слотов
        for i in range(8):
            slot_x = panel_x + i * (slot_size + slot_spacing)
            skill = self.player.skill_manager.get_slot_skill(i)

            # Проверяем, доступно ли умение для использования
            is_usable = False
            if skill:
                can_use, reason = skill.can_use(self.player)
                is_usable = can_use

            # Фон слота
            if skill:
                # Цвет фона зависит от категории умения и доступности
                if is_usable:
                    # Яркие цвета для доступных умений
                    if skill.category.value == 'combat':
                        bg_color = (80, 50, 50)
                    elif skill.category.value == 'magic':
                        bg_color = (50, 50, 80)
                    elif skill.category.value == 'crafting':
                        bg_color = (70, 70, 50)
                    else:
                        bg_color = (60, 60, 60)
                else:
                    # Темные цвета для недоступных умений
                    if skill.category.value == 'combat':
                        bg_color = (40, 25, 25)
                    elif skill.category.value == 'magic':
                        bg_color = (25, 25, 40)
                    elif skill.category.value == 'crafting':
                        bg_color = (35, 35, 25)
                    else:
                        bg_color = (30, 30, 30)
            else:
                bg_color = (30, 30, 30)

            pygame.draw.rect(
                self.screen,
                bg_color,
                (slot_x, panel_y, slot_size, slot_size)
            )

            # Рамка слота (ярче для доступных умений)
            if skill and is_usable:
                border_color = (200, 200, 100)  # Яркая желтая рамка для доступных
            elif skill:
                border_color = (80, 80, 80)  # Темная рамка для недоступных
            else:
                border_color = (100, 100, 100)  # Обычная рамка для пустых

            pygame.draw.rect(
                self.screen,
                border_color,
                (slot_x, panel_y, slot_size, slot_size),
                2
            )

            # Номер слота (клавиша)
            key_text = self.info_font.render(
                str(i + 1),
                True,
                (200, 200, 200)
            )
            self.screen.blit(key_text, (slot_x + 4, panel_y + 4))

            # Если есть умение, показываем его информацию
            if skill:
                # Иконка умения (первая буква названия)
                icon_font = pygame.font.Font(None, 32)
                icon_text = icon_font.render(
                    skill.name[0],
                    True,
                    (255, 255, 255)
                )
                icon_rect = icon_text.get_rect()
                icon_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2 + 4)
                self.screen.blit(icon_text, icon_rect)

                # Ранг умения (маленькими цифрами в углу)
                rank_text = self.info_font.render(
                    f"R{skill.rank}",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(rank_text, (slot_x + slot_size - 22, panel_y + slot_size - 18))

                # Перезарядка (если есть)
                if skill.current_cooldown > 0:
                    cooldown_text = self.info_font.render(
                        str(skill.current_cooldown),
                        True,
                        (255, 100, 100)
                    )
                    cooldown_rect = cooldown_text.get_rect()
                    cooldown_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2)
                    self.screen.blit(cooldown_text, cooldown_rect)

    def _generate_loot(self, enemy):
        """
        Генерировать лут с поверженного врага

        Args:
            enemy: Поверженный враг

        Returns:
            tuple: (список предметов [(item, quantity)], количество золота)
        """
        from game.inventory import ItemGenerator, ItemQuality, PREDEFINED_ITEMS

        loot_items = []
        loot_gold = 0

        # Золото зависит от уровня врага
        base_gold = enemy.level * 5
        loot_gold = random.randint(base_gold, base_gold * 2)

        # Шанс выпадения предметов зависит от уровня врага
        drop_chance = min(0.3 + enemy.level * 0.02, 0.8)  # От 30% до 80%

        # Количество предметов (1-3)
        num_items = random.randint(1, 3)

        for _ in range(num_items):
            if random.random() < drop_chance:
                # Определяем тип предмета
                item_type = random.choice(['equipment', 'potion', 'equipment', 'potion'])

                if item_type == 'equipment':
                    # Генерируем экипировку
                    item_level = max(1, enemy.level + random.randint(-2, 2))
                    quality = ItemGenerator.generate_quality()

                    if random.random() < 0.5:
                        item = ItemGenerator.generate_weapon(item_level, quality)
                    else:
                        item = ItemGenerator.generate_armor(item_level, quality=quality)

                    loot_items.append((item, 1))

                elif item_type == 'potion':
                    # Зелья
                    potion_choices = ['minor_health_potion', 'minor_stamina_potion', 'minor_mana_potion']
                    if enemy.level >= 10:
                        potion_choices.extend(['health_potion', 'stamina_potion', 'mana_potion'])

                    potion_name = random.choice(potion_choices)
                    if potion_name in PREDEFINED_ITEMS:
                        potion = PREDEFINED_ITEMS[potion_name]
                        quantity = random.randint(1, 2)
                        loot_items.append((potion, quantity))

        return loot_items, loot_gold

    def _render_interaction_menu(self):
        """Отрисовка меню взаимодействия с NPC"""
        # Затемняем фон
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры меню
        menu_width = 500
        menu_height = 300
        menu_x = (self.window_width - menu_width) // 2
        menu_y = (self.window_height - menu_height) // 2

        # Фон меню
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (menu_x, menu_y, menu_width, menu_height)
        )

        # Рамка меню
        pygame.draw.rect(
            self.screen,
            COLORS['text'],
            (menu_x, menu_y, menu_width, menu_height),
            3
        )

        # Заголовок
        title_text = self.font.render(
            f"Взаимодействие: {self.nearby_npc.name}",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = menu_x + menu_width // 2
        title_rect.y = menu_y + 20
        self.screen.blit(title_text, title_rect)

        # Информация о NPC
        npc_info = [
            f"Уровень: {self.nearby_npc.level}",
            f"Здоровье: {self.nearby_npc.health}/{self.nearby_npc.max_health}",
            f"Тип: {self.nearby_npc.npc_type}"
        ]

        info_y = menu_y + 70
        for i, info in enumerate(npc_info):
            info_text = self.info_font.render(info, True, (200, 200, 200))
            info_rect = info_text.get_rect()
            info_rect.centerx = menu_x + menu_width // 2
            info_rect.y = info_y + i * 25
            self.screen.blit(info_text, info_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (menu_x + 20, menu_y + 160),
            (menu_x + menu_width - 20, menu_y + 160),
            2
        )

        # Варианты действий
        actions_y = menu_y + 180
        actions_title = self.font.render("Выберите действие:", True, COLORS['text'])
        actions_title_rect = actions_title.get_rect()
        actions_title_rect.centerx = menu_x + menu_width // 2
        actions_title_rect.y = actions_y
        self.screen.blit(actions_title, actions_title_rect)

        # Кнопки действий (зависят от типа NPC)
        if self.nearby_npc.npc_type == "mage":
            training_cost = 50 * self.nearby_npc.level
            actions = [
                "[1] Купить заклинания",
                f"[2] Обучение ({training_cost} зол.)",
                "[3] Агрессия",
                "[4] Уйти"
            ]
        elif self.nearby_npc.npc_type == "merchant":
            actions = [
                "[1] Торговля",
                "[2] Агрессия",
                "[3] Уйти"
            ]
        else:
            actions = [
                "[1] Торговля",
                "[2] Агрессия",
                "[3] Уйти"
            ]

        buttons_y = actions_y + 40
        for i, action in enumerate(actions):
            action_text = self.info_font.render(action, True, (150, 255, 150))
            action_rect = action_text.get_rect()
            action_rect.centerx = menu_x + menu_width // 2
            action_rect.y = buttons_y + i * 30
            self.screen.blit(action_text, action_rect)
