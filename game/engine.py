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
from game.ui import HelpWindow, InventoryWindow, TradeWindow, UIHelper, CharacterWindow, UIScaler, QuestWindow, RandomEventWindow, CheatMenuWindow
from game.optimization import PerformanceOptimizer, RenderCache
from game.quests import (QuestManager, AchievementManager, create_starter_quests,
                        QuestGenerator, create_unique_quests, get_unique_quest_for_location,
                        auto_assign_starter_quests, AchievementRarity)
from game.save_system import SaveSystem
from game.constants import (
    FPS, TILE_SIZE, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL
)

# Импорт новых модулей
from game.npc_spawner import NPCSpawner, give_starting_items
from game.input_handler import InputHandler
from game.world_renderer import WorldRenderer
from game.game_time import GameTime
from game.camera import Camera
from game.respawn_manager import RespawnManager
from game.events import create_game_systems, TimeOfDayBonuses


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

        # Используем нативное разрешение экрана без ограничений

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
        self.quest_window_open = False

        # Окно квестов
        self.quest_window = QuestWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Окно случайных событий
        self.random_event_window = RandomEventWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.event_window_open = False

        # Окно чит меню
        self.cheat_menu_window = CheatMenuWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.cheat_menu_open = False

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
        self.alchemists = npcs['alchemists']
        self.hunters = npcs['hunters']
        self.necromancers = npcs['necromancers']
        self.animals = npcs['animals']

        print(f"Игрок создан на позиции ({self.player.x}, {self.player.y})")
        print(f"Создано {len(self.guards)} стражников")
        print(f"Создано {len(self.merchants)} торговцев")
        print(f"Создано {len(self.mages)} магов-патрульных")
        print(f"Создано {len(self.bandits)} бандитов")
        print(f"Создано {len(self.miners)} шахтеров")
        print(f"Создано {len(self.undead)} нежити")
        print(f"Создано {len(self.alchemists)} алхимиков")
        print(f"Создано {len(self.hunters)} охотников")
        print(f"Создано {len(self.necromancers)} некромантов")
        print(f"Создано {len(self.animals)} животных")

        # Инициализация менеджера респавна
        self.respawn_manager = RespawnManager(self.game_map)

        # Даем игроку стартовые предметы
        give_starting_items(self.player)

        # Инициализация оптимизатора производительности
        self.performance_optimizer = PerformanceOptimizer()
        self.render_cache = RenderCache()

        # Инициализация менеджера квестов
        self.quest_manager = QuestManager()
        # Автоматически назначаем стартовые квесты игроку
        auto_assign_starter_quests(self.quest_manager)
        # Добавляем уникальные квесты с хорошими наградами в доступные
        for quest in create_unique_quests():
            self.quest_manager.add_available_quest(quest)

        # Инициализация менеджера достижений с наградами
        self.achievement_manager = AchievementManager()

        # Инициализация систем событий, погоды и серий убийств
        self.weather_system, self.random_event_system, self.killstreak_system = create_game_systems()

        # Даем игроку стартовые умения
        self.player.skill_manager.learn_skill('basic_attack')  # Базовая атака
        self.player.skill_manager.learn_skill('mining')  # Рудокоп ранг 1
        self.player.skill_manager.learn_skill('lumberjacking')  # Лесоруб ранг 1

        # Назначаем умения в слоты
        self.player.skill_manager.assign_to_slot('basic_attack', 0)  # Слот 1
        self.player.skill_manager.assign_to_slot('mining', 1)  # Слот 2
        self.player.skill_manager.assign_to_slot('lumberjacking', 2)  # Слот 3

        # Создаём централизованный менеджер NPC
        from game.core import create_npc_manager_from_game, get_all_npcs_from_game
        self.npc_manager = create_npc_manager_from_game(self)

        # Перестраиваем spatial grid для NPC
        all_npcs = get_all_npcs_from_game(self)
        self.performance_optimizer.rebuild_spatial_grid(all_npcs)

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
                    # Генерируем лут (проверка на None)
                    defeated_enemy = self.combat_system.enemy
                    if defeated_enemy is None:
                        self.in_combat = False
                        self.combat_system = None
                        continue
                    loot_items, loot_gold = self._generate_loot(defeated_enemy)

                    # Применяем бонус серии убийств
                    if hasattr(self, 'killstreak_system'):
                        streak_info = self.killstreak_system.register_kill()
                        multiplier = streak_info['multiplier']
                        loot_gold = int(loot_gold * multiplier)
                        if streak_info['message']:
                            print(streak_info['message'])

                    # Добавляем лут в инвентарь игрока
                    self.player.inventory.add_gold(loot_gold)
                    for item, quantity in loot_items:
                        self.player.inventory.add_item(item, quantity)

                    # Показываем окно лута
                    self.loot_window.set_loot(loot_items, loot_gold, defeated_enemy.name)
                    self.loot_window_open = True

                    # Обновляем прогресс квестов на убийство
                    if hasattr(defeated_enemy, 'npc_type'):
                        enemy_type = defeated_enemy.npc_type
                        # Обновляем статистику игрока
                        if not hasattr(self.player, 'enemies_killed'):
                            self.player.enemies_killed = 0
                        self.player.enemies_killed += 1

                        # Отслеживание убийств животных
                        if enemy_type == 'wolf':
                            if not hasattr(self.player, 'wolves_killed'):
                                self.player.wolves_killed = 0
                            self.player.wolves_killed += 1
                        elif enemy_type == 'bear':
                            if not hasattr(self.player, 'bears_killed'):
                                self.player.bears_killed = 0
                            self.player.bears_killed += 1
                        elif enemy_type == 'deer':
                            if not hasattr(self.player, 'deer_killed'):
                                self.player.deer_killed = 0
                            self.player.deer_killed += 1

                        # Обновляем прогресс квестов для всех типов врагов
                        if enemy_type in ['bandit', 'undead', 'wolf', 'bear', 'deer', 'necromancer']:
                            self.update_kill_quest_progress(enemy_type)

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
                    elif event.button == 4:  # Колесо вверх
                        all_items = self.player.inventory.get_all_items()
                        if all_items:
                            self.inventory_window.selected_inventory_index = max(0, self.inventory_window.selected_inventory_index - 1)
                    elif event.button == 5:  # Колесо вниз
                        all_items = self.player.inventory.get_all_items()
                        if all_items:
                            self.inventory_window.selected_inventory_index = min(len(all_items) - 1, self.inventory_window.selected_inventory_index + 1)
                elif event.type == pygame.MOUSEWHEEL:
                    all_items = self.player.inventory.get_all_items()
                    if all_items:
                        if event.y > 0:  # Колесо вверх
                            self.inventory_window.selected_inventory_index = max(0, self.inventory_window.selected_inventory_index - 1)
                        elif event.y < 0:  # Колесо вниз
                            self.inventory_window.selected_inventory_index = min(len(all_items) - 1, self.inventory_window.selected_inventory_index + 1)
                continue

            # Если открыто меню торговли, обрабатываем его
            if self.trade_menu_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_trade_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # ЛКМ - фильтры и сортировка
                        self.input_handler.handle_trade_left_click(event.pos)
                    elif event.button == 3:  # ПКМ
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

            # Если открыто окно квестов, обрабатываем его
            if self.quest_window_open:
                if event.type == pygame.KEYDOWN:
                    self.input_handler.handle_quest_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Обработка событий мыши в окне квестов
                    action = self.quest_window.handle_mouse_event(event, self)
                    if action:
                        self._handle_quest_action(action)
                continue

            # Если открыто окно случайных событий, обрабатываем его
            if self.event_window_open:
                if self.random_event_window.handle_input(event):
                    self.event_window_open = False
                    self.random_event_system.clear_last_event()
                continue

            # Если открыто чит меню, обрабатываем его
            if self.cheat_menu_open:
                if self.cheat_menu_window.handle_input(event, self):
                    self.cheat_menu_open = False
                continue

            # Обработка нажатий клавиш
            if event.type == pygame.KEYDOWN:
                self.input_handler.handle_key_press(event.key)

    def _check_npc_nearby(self):
        """Проверить наличие NPC рядом с игроком и открыть меню взаимодействия"""
        # Сначала проверяем, находимся ли мы в городе, деревне или школе магов
        tile = self.game_map.get_tile(self.player.x, self.player.y)
        if tile.has_location():
            location = tile.location
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL]:
                # Открываем торговое окно для города/деревни/школы магов
                # Создаем временного торговца для этой локации
                if not hasattr(location, 'merchant_npc'):
                    # Создаем постоянного торговца для этой локации
                    if location.location_type == LOCATION_MAGIC_SCHOOL:
                        merchant_level = 15
                    elif location.location_type == LOCATION_CITY:
                        merchant_level = 10
                    else:
                        merchant_level = 5
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

        # Собираем всех NPC (включая mages, alchemists, hunters, necromancers, animals)
        all_npcs = self.guards + self.merchants + self.bandits + self.miners + self.undead + self.mages + self.alchemists + self.hunters + self.necromancers + self.animals

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

    def open_quest_window(self, location):
        """
        Открыть окно квестов для локации

        Args:
            location: Объект локации
        """
        location_id = f"{location.x}_{location.y}"

        # Генерируем квесты для локации, если их еще нет
        if location_id not in self.quest_manager.location_quests:
            quests = QuestGenerator.generate_quests_for_location(
                location.name, location_id, self.player.level, count=3
            )
            for quest in quests:
                self.quest_manager.add_location_quest(location_id, quest)

            # Пробуем добавить уникальный квест для городов, деревень и школы магов
            unique_quest = get_unique_quest_for_location(location.location_type, location.name)
            if unique_quest:
                unique_quest.location_id = location_id
                self.quest_manager.add_location_quest(location_id, unique_quest)

        # Проверяем прогресс всех квестов на сбор ресурсов
        self.quest_manager.check_all_quest_progress(self.player)

        # Получаем доступные квесты для этой локации
        available_quests = self.quest_manager.get_location_quests(location_id)

        # Получаем активные квесты
        active_quests = self.quest_manager.get_active_quests()

        # Получаем квесты готовые к сдаче в этой локации
        turn_in_quests = self.quest_manager.get_quests_ready_to_turn_in(location_id)

        # Устанавливаем данные в окно квестов
        self.quest_window.set_data(
            location.name,
            location_id,
            available_quests,
            active_quests,
            turn_in_quests
        )

        # Открываем окно
        self.quest_window_open = True

    def open_quest_window_anywhere(self):
        """
        Открыть окно квестов из любого места (только активные квесты)
        """
        # Проверяем прогресс всех квестов на сбор ресурсов
        self.quest_manager.check_all_quest_progress(self.player)

        # Получаем активные квесты
        active_quests = self.quest_manager.get_active_quests()

        # Устанавливаем данные в окно квестов (без доступных и готовых к сдаче)
        self.quest_window.set_data(
            "Журнал квестов",  # Общее название
            None,  # Нет локации
            [],  # Нет доступных квестов
            active_quests,
            []  # Нет квестов к сдаче
        )

        # Автоматически переключаем на вкладку активных квестов
        self.quest_window.mode = "active"

        # Открываем окно
        self.quest_window_open = True

    def _handle_quest_action(self, action):
        """
        Обработка действий с квестами из окна квестов

        Args:
            action: Тип действия ('accept', 'turn_in', 'abandon')
        """
        quest = self.quest_window.get_selected_quest()
        if not quest:
            return

        if action == 'accept':
            # Принять квест
            success, message = self.quest_manager.accept_quest(
                quest.quest_id,
                self.quest_window.location_id,
                self.player
            )
            print(message)
            if success:
                self.input_handler._refresh_quest_window()

        elif action == 'turn_in':
            # Сдать квест
            success, messages = self.quest_manager.complete_quest(
                quest.quest_id,
                self.player
            )
            if success:
                print(f"Квест '{quest.name}' завершён!")
                for msg in messages:
                    print(f"  {msg}")
                self.input_handler._refresh_quest_window()
            else:
                print("Не удалось сдать квест")

        elif action == 'abandon':
            # Отменить квест
            success, message = self.quest_manager.abandon_quest(quest.quest_id)
            print(message)
            if success:
                self.input_handler._refresh_quest_window()

    def _collect_resources(self):
        """Собрать ресурсы с текущей локации с учётом случайных событий"""
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

        # Проверяем случайное событие при сборе лута
        event_result = self._process_loot_event()
        if event_result == "combat_started":
            # Бой начался, лут будет собран после победы
            location.loot_collected = True
            return
        elif event_result == "trap_triggered":
            # Ловушка сработала, но лут всё равно можно собрать
            pass

        # Получаем лут с локации с учётом удачи игрока
        loot = get_random_loot_from_location(location.location_type, self.player.level, self.player.luck)

        if not loot:
            print("Ничего не найдено!")
            return

        # Бонусный лут от события
        if event_result == "bonus_loot":
            print("Удача! Вы нашли дополнительный тайник!")
            bonus_loot = get_random_loot_from_location(location.location_type, self.player.level, self.player.luck)
            loot.extend(bonus_loot)

        # Добавляем лут в инвентарь
        for item, quantity in loot:
            if item == 'gold':
                self.player.inventory.add_gold(quantity)
                print(f"Найдено: {quantity} золота")
            elif self.player.inventory.add_item(item, quantity):
                print(f"Найдено: {item.name} x{quantity}")

                # Обновляем прогресс квестов на сбор ресурсов
                item_key = self._get_item_key(item.name)
                if item_key:
                    messages = self.quest_manager.update_gather_progress(item_key, quantity, self.player)
                    for msg in messages:
                        print(f"  {msg}")
            else:
                print(f"Инвентарь полон! Не удалось подобрать {item.name}")

        # Помечаем локацию как обыскованную
        location.loot_collected = True

        # Обновляем прогресс квеста "Охотник за сокровищами"
        self.player.resources_collected += 1
        self.quest_manager.update_quest_progress("treasure_hunter", 0, 1)

        # Добавляем тип локации в посещенные
        self.player.visited_location_types.add(location.location_type)

        # Продвигаем время на 20 минут (1/3 часа)
        self.game_time.advance_time(1/3)
        print(f"Время: {self.game_time.get_time_string()}")

    def _process_loot_event(self):
        """
        Обработать случайное событие при сборе лута

        Returns:
            str: тип события ('nothing', 'trap_triggered', 'combat_started', 'bonus_loot')
        """
        import random
        from game.npc import Bandit

        # Шанс события - 30%
        if random.randint(1, 100) > 30:
            return "nothing"

        # Выбираем тип события
        event_type = random.choice(["trap", "enemy", "bonus", "nothing"])

        if event_type == "trap":
            # Ловушка наносит урон (10% от макс здоровья)
            effective_max_health = self.player.get_effective_max_health()
            trap_damage = int(effective_max_health * 0.10)
            self.player.health -= trap_damage
            self.player.health = max(1, self.player.health)
            print(f"Вы попали в ловушку! Получено {trap_damage} урона.")
            return "trap_triggered"

        elif event_type == "enemy":
            # Спавн врага на 2-5 уровней выше игрока
            enemy_level = self.player.level + random.randint(2, 5)
            enemy_level = min(enemy_level, 40)  # Макс 40 уровень

            # Создаём бандита-защитника
            enemy_names = ["Страж сокровищ", "Охранник", "Засадник", "Грабитель"]
            enemy = Bandit(
                random.choice(enemy_names),
                self.player.x,
                self.player.y,
                enemy_level,
                self.player.x,
                self.player.y
            )

            print(f"На вас напал {enemy.name} {enemy_level} уровня!")
            self._start_combat(enemy)
            return "combat_started"

        elif event_type == "bonus":
            # Бонусный лут
            return "bonus_loot"

        return "nothing"

    def _get_item_key(self, item_name):
        """
        Получить ключ предмета для системы квестов

        Args:
            item_name: Отображаемое имя предмета

        Returns:
            str: Ключ предмета или None
        """
        # Словарь соответствий отображаемых имен и ключей
        item_mapping = {
            'Медная руда': 'copper_ore',
            'Железная руда': 'iron_ore',
            'Серебряная руда': 'silver_ore',
            'Золотая руда': 'gold_ore',
            'Мифриловая руда': 'mithril_ore',
            'Древесина': 'wood',
            'Древняя монета': 'ancient_coin',
            'Фрагмент артефакта': 'artifact_fragment',
            'Магический кристалл': 'magic_crystal',
            'Старый свиток': 'old_scroll',
        }
        return item_mapping.get(item_name)

    def update_kill_quest_progress(self, enemy_type):
        """
        Обновить прогресс квестов на убийство

        Args:
            enemy_type: Тип убитого врага ('bandit', 'undead')
        """
        messages = self.quest_manager.update_kill_progress(enemy_type)
        for msg in messages:
            print(f"  {msg}")

    def _start_combat(self, enemy):
        """
        Начать бой с NPC

        Args:
            enemy: Враг для боя
        """
        print(f"Бой начался с {enemy.name}!")

        # Закрываем окно случайного события, если оно открыто
        if hasattr(self, 'event_window_open') and self.event_window_open:
            self.event_window_open = False
            if hasattr(self, 'random_event_system'):
                self.random_event_system.clear_last_event()

        # Показываем бонусы погоды и времени суток
        if hasattr(self, 'weather_system'):
            weather_mods = self.weather_system.get_combat_modifier()
            if weather_mods['accuracy'] != 1.0 or weather_mods['evasion'] != 1.0:
                effects = []
                if weather_mods['accuracy'] < 1.0:
                    effects.append(f"точность {int(weather_mods['accuracy']*100)}%")
                if weather_mods['evasion'] > 1.0:
                    effects.append(f"уклонение +{int((weather_mods['evasion']-1)*100)}%")
                if effects:
                    print(f"  Погода ({self.weather_system.current_weather.display_name}): {', '.join(effects)}")

        time_bonuses = TimeOfDayBonuses.get_bonuses(self.game_time.hour)
        if time_bonuses['description']:
            print(f"  {time_bonuses['description']}")

        self.combat_system = CombatSystem(self.player, enemy, self.screen, self.font, self.ui_scaler, self.game_map, self.respawn_manager)
        self.in_combat = True
        self.nearby_npc = None

    def _update(self):
        """Обновление состояния игры"""
        # AI стражников обновляется в методе advance_time

        # Режим бессмертия: восстанавливаем здоровье, ману и выносливость (с учетом бонусов от экипировки)
        if self.cheat_menu_window.cheats['godmode']['enabled']:
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

        # Если открыто окно квестов, отрисовываем его
        if self.quest_window_open:
            self.quest_window.render(self.player)

        # Если открыто окно случайных событий, отрисовываем его
        if self.event_window_open:
            event_result = self.random_event_system.get_last_event()
            if event_result:
                self.random_event_window.render(event_result)

        # Если открыто чит меню, отрисовываем его
        if self.cheat_menu_open:
            self.cheat_menu_window.render()

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

        # Игровое время, погода и золото
        weather_str = ""
        if hasattr(self, 'weather_system'):
            weather_str = f" | {self.weather_system.current_weather.display_name}"

        time_gold_text = self.info_font.render(
            f"{self.game_time.get_time_string()}{weather_str} | Золото: {self.player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        time_gold_x = self.window_width - self.ui_scaler.scale_width(450)
        self.screen.blit(time_gold_text, (time_gold_x, info_y + 5))

        # Серия убийств (если активна)
        if hasattr(self, 'killstreak_system') and self.killstreak_system.current_streak >= 3:
            streak_text = self.info_font.render(
                f"Серия: x{self.killstreak_system.current_streak}",
                True,
                (255, 100, 100)
            )
            self.screen.blit(streak_text, (time_gold_x, info_y + 22))

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

        # Животные дают специфичный лут без золота
        if enemy.npc_type in ["wolf", "bear", "deer"]:
            animal_loot = ItemGenerator.generate_animal_loot(enemy.npc_type)
            for item in animal_loot:
                loot_items.append((item, 1))
            return loot_items, 0  # Животные не дают золото

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
        elif self.nearby_npc.npc_type == "alchemist":
            actions = [
                "[1] Торговля зельями",
                "[2] Взять квест",
                "[3] Сдать квест",
                "[4] Уйти"
            ]
        elif self.nearby_npc.npc_type == "hunter":
            actions = [
                "[1] Торговля",
                "[2] Взять квест",
                "[3] Сдать квест",
                "[4] Уйти"
            ]
        elif self.nearby_npc.npc_type == "merchant":
            actions = [
                "[1] Торговля",
                "[2] Агрессия",
                "[3] Уйти"
            ]
        elif self.nearby_npc.npc_type in ["wolf", "bear", "deer"]:
            # Животные - только агрессия или уйти
            actions = [
                "[1] Агрессия",
                "[2] Уйти"
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
