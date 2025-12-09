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
from game.ui.windows import (
    InteractionWindow,
    ExitConfirmationWindow,
    SettlementMenuWindow,
    InquiryMenuWindow,
    InquiryResponseWindow,
    LootWindow,
    SkillBookWindow,
    CombatModeSelectionWindow,
    CraftingWindow,
    NPCSelectionWindow,
)
from game.optimization import PerformanceOptimizer, RenderCache
from game.quest_system import (
    QuestManager, AchievementManager,
    create_unique_quests, get_unique_quest_for_location,
    auto_assign_starter_quests
)
from game.constants import (
    FPS, TILE_SIZE, COLORS,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY
)

# Импорт новых модулей
from game.npc_spawner import NPCSpawner, give_starting_items
from game.input_handler import InputHandler
from game.world_renderer import WorldRenderer
from game.game_time import GameTime
from game.camera import Camera
from game.respawn_manager import RespawnManager
from game.events import create_game_systems, TimeOfDayBonuses
from game.loot_system import LootSystem
from game.hud_renderer import HUDRenderer
from game.resource_system import ResourceSystem
from game.quest_ui_controller import QuestUIController
from game.crafting_system import CraftingSystem
from game.item_registry import get_item


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

        # Тактический бой
        self.combat_mode_menu_open = False
        self.is_npc_aggression = False  # Флаг агрессии NPC (не дает уйти)
        self.tactical_combat_system = None
        self.tactical_combat_renderer = None
        self.tactical_combat_handler = None
        self.in_tactical_combat = False

        # UI компоненты (с передачей scaler для адаптивности)
        self.help_window = HelpWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.inventory_window = InventoryWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.trade_window = TradeWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.character_window = CharacterWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        from game.ui import SkillBookWindow, LootWindow
        from game.ui.windows import ResourceCollectionWindow
        self.skill_book_window = SkillBookWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.loot_window = LootWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.resource_collection_window = ResourceCollectionWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Состояния окон
        self.inventory_menu_open = False
        self.trade_menu_open = False
        self.character_menu_open = False
        self.skill_book_menu_open = False
        self.loot_window_open = False
        self.resource_collection_window_open = False
        self.quest_window_open = False

        # Окно квестов
        self.quest_window = QuestWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Окно случайных событий
        self.random_event_window = RandomEventWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.event_window_open = False

        # Окно крафта
        self.crafting_window = CraftingWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.crafting_window_open = False

        # Окно чит меню
        self.cheat_menu_window = CheatMenuWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.cheat_menu_open = False

        # Окно взаимодействия с NPC
        self.interaction_window = InteractionWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Окно выбора NPC (если в клетке несколько NPC)
        self.npc_selection_window = NPCSelectionWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.npc_selection_menu_open = False

        # Окно выбора режима боя
        self.combat_mode_window = CombatModeSelectionWindow(self.screen, self.font, self.info_font, self.ui_scaler)

        # Окна города/деревни
        self.settlement_menu_window = SettlementMenuWindow(self.screen, self.font, self.info_font, self.ui_scaler, self.game_map)
        self.inquiry_menu_window = InquiryMenuWindow(self.screen, self.font, self.info_font, self.ui_scaler, self.game_map)
        self.inquiry_response_window = InquiryResponseWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.settlement_menu_open = False
        self.inquiry_menu_open = False
        self.inquiry_response_open = False

        # Окно подтверждения выхода
        self.exit_confirmation_window = ExitConfirmationWindow(self.screen, self.font, self.info_font, self.ui_scaler)
        self.exit_confirmation_open = False

        # Менеджер спрайтов
        from game.sprite_manager import SpriteManager
        self.sprite_manager = SpriteManager(tile_size=TILE_SIZE)
        print(f"Менеджер спрайтов инициализирован")

        # Передаём sprite_manager в окно книги умений для отображения иконок
        self.skill_book_window.sprite_manager = self.sprite_manager

        # Создание NPC с помощью спавнера и NPCManager
        from game.core.npc_manager import NPCManager
        npc_spawner = NPCSpawner(self.game_map)
        npcs = npc_spawner.spawn_all_npcs()

        # Инициализируем централизованный менеджер NPC
        self.npc_manager = NPCManager()
        self.npc_manager.load_from_dict(npcs)

        print(f"Игрок создан на позиции ({self.player.x}, {self.player.y})")
        counts = self.npc_manager.get_counts()
        print(f"Создано {counts.get('guards', 0)} стражников")
        print(f"Создано {counts.get('merchants', 0)} торговцев")
        print(f"Создано {counts.get('mages', 0)} магов-патрульных")
        print(f"Создано {counts.get('bandits', 0)} бандитов")
        print(f"Создано {counts.get('miners', 0)} шахтеров")
        print(f"Создано {counts.get('undead', 0)} нежити")
        print(f"Создано {counts.get('alchemists', 0)} алхимиков")
        print(f"Создано {counts.get('hunters', 0)} охотников")
        print(f"Создано {counts.get('necromancers', 0)} некромантов")
        print(f"Создано {counts.get('animals', 0)} животных")

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

        # Инициализация системы лута
        self.loot_system = LootSystem(self.player, self.quest_manager, self.killstreak_system)

        # Инициализация системы крафта
        self.crafting_system = CraftingSystem()

        # Даем игроку стартовые умения
        self.player.skill_manager.learn_skill('basic_attack')  # Базовая атака
        self.player.skill_manager.learn_skill('basic_shot')  # Базовый выстрел (для луков)
        self.player.skill_manager.learn_skill('mining')  # Рудокоп ранг 1
        self.player.skill_manager.learn_skill('lumberjacking')  # Лесоруб ранг 1

        # Назначаем умения в слоты
        self.player.skill_manager.assign_to_slot('basic_attack', 0)  # Слот 1
        self.player.skill_manager.assign_to_slot('basic_shot', 1)  # Слот 2
        self.player.skill_manager.assign_to_slot('mining', 2)  # Слот 3
        self.player.skill_manager.assign_to_slot('lumberjacking', 3)  # Слот 4

        # Перестраиваем spatial grid для NPC
        self.performance_optimizer.rebuild_spatial_grid(self.npc_manager.get_all_npcs())

        # Инициализация обработчика ввода
        self.input_handler = InputHandler(self)

        # Инициализация рендерера мира
        self.world_renderer = WorldRenderer(self)

        # Инициализация рендерера HUD
        self.hud_renderer = HUDRenderer(self)

        # Инициализация системы ресурсов
        self.resource_system = ResourceSystem(
            self.player, self.game_map, self.quest_manager,
            self.game_time, self._start_combat, self._show_resource_collection_window
        )

        # Инициализация контроллера квестов
        self.quest_ui_controller = QuestUIController(
            self.player, self.quest_manager, self.quest_window,
            self.input_handler._refresh_quest_window
        )

        print("Игра готова к запуску!")

    # === Свойства обратной совместимости для доступа к NPC ===
    # Эти свойства делегируют к npc_manager для совместимости со старым кодом

    @property
    def guards(self):
        """Список стражников (через NPCManager)."""
        return self.npc_manager.guards

    @property
    def merchants(self):
        """Список торговцев (через NPCManager)."""
        return self.npc_manager.merchants

    @property
    def mages(self):
        """Список магов (через NPCManager)."""
        return self.npc_manager.mages

    @property
    def bandits(self):
        """Список бандитов (через NPCManager)."""
        return self.npc_manager.bandits

    @property
    def miners(self):
        """Список шахтёров (через NPCManager)."""
        return self.npc_manager.miners

    @property
    def undead(self):
        """Список нежити (через NPCManager)."""
        return self.npc_manager.undead

    @property
    def alchemists(self):
        """Список алхимиков (через NPCManager)."""
        return self.npc_manager.alchemists

    @property
    def hunters(self):
        """Список охотников (через NPCManager)."""
        return self.npc_manager.hunters

    @property
    def necromancers(self):
        """Список некромантов (через NPCManager)."""
        return self.npc_manager.necromancers

    @property
    def animals(self):
        """Список животных (через NPCManager)."""
        return self.npc_manager.animals

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
                # Открываем окно подтверждения выхода вместо немедленного выхода
                if not self.exit_confirmation_open:
                    self.exit_confirmation_open = True
                    continue

            # Если открыто окно подтверждения выхода, обрабатываем его события
            if self.exit_confirmation_open:
                result = self.exit_confirmation_window.handle_input(event)
                if result == 'yes':
                    self.running = False
                elif result == 'no':
                    self.exit_confirmation_open = False
                continue

            # Если идет тактический бой, передаем управление системе тактического боя
            if self.in_tactical_combat and self.tactical_combat_handler:
                result = self.tactical_combat_handler.handle_input(event)
                if result == "victory":
                    # Обрабатываем победу через LootSystem
                    defeated_enemy = self.tactical_combat_system.enemy
                    if defeated_enemy is None:
                        self.in_tactical_combat = False
                        self.tactical_combat_system = None
                        self.tactical_combat_renderer = None
                        self.tactical_combat_handler = None
                        continue

                    # LootSystem обрабатывает: генерацию лута, бонусы killstreak,
                    # добавление в инвентарь, статистику убийств и квесты
                    victory_result = self.loot_system.process_victory(defeated_enemy)

                    # Выводим сообщение о серии убийств
                    if victory_result['streak_message']:
                        print(victory_result['streak_message'])

                    # Показываем окно лута
                    self.loot_window.set_loot(
                        victory_result['loot_items'],
                        victory_result['loot_gold'],
                        defeated_enemy.name
                    )
                    self.loot_window_open = True

                    self.in_tactical_combat = False
                    self.tactical_combat_system = None
                    self.tactical_combat_renderer = None
                    self.tactical_combat_handler = None
                    print("Победа в тактическом бою!")
                elif result == "defeat":
                    self.in_tactical_combat = False
                    self.tactical_combat_system = None
                    self.tactical_combat_renderer = None
                    self.tactical_combat_handler = None
                    print("Поражение в тактическом бою! Игра окончена.")
                    self.running = False
                elif result == "fled":
                    self.in_tactical_combat = False
                    self.tactical_combat_system = None
                    self.tactical_combat_renderer = None
                    self.tactical_combat_handler = None
                continue

            # Если открыто меню выбора NPC, обрабатываем его
            if self.npc_selection_menu_open:
                result = self.npc_selection_window.handle_input(event)
                if result == "select":
                    # Игрок выбрал NPC - открываем меню взаимодействия
                    selected_npc = self.npc_selection_window.get_selected_npc()
                    if selected_npc:
                        self.nearby_npc = selected_npc
                        self.interaction_menu_open = True
                        self.npc_selection_menu_open = False
                        print(f"Вы выбрали: {selected_npc.name}")
                elif result == "cancel":
                    # Игрок отменил выбор
                    self.npc_selection_menu_open = False
                    print("Выбор отменён.")
                continue

            # Если открыто меню выбора режима боя, обрабатываем его
            if self.combat_mode_menu_open:
                self.input_handler.handle_combat_mode_choice(event)
                continue

            # Если идет бой, передаем управление боевой системе
            if self.in_combat and self.combat_system:
                result = self.combat_system.handle_input(event)
                if result == "victory":
                    # Обрабатываем победу через LootSystem
                    defeated_enemy = self.combat_system.enemy
                    if defeated_enemy is None:
                        self.in_combat = False
                        self.combat_system = None
                        continue

                    # LootSystem обрабатывает: генерацию лута, бонусы killstreak,
                    # добавление в инвентарь, статистику убийств и квесты
                    victory_result = self.loot_system.process_victory(defeated_enemy)

                    # Выводим сообщение о серии убийств
                    if victory_result['streak_message']:
                        print(victory_result['streak_message'])

                    # Показываем окно лута
                    self.loot_window.set_loot(
                        victory_result['loot_items'],
                        victory_result['loot_gold'],
                        defeated_enemy.name
                    )
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

            # Маршрутизация событий меню через InputHandler
            if self.input_handler.route_menu_event(event, self._handle_quest_action):
                continue

            # Обработка кликов мыши на основном экране (если ни одно меню не открыто)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # ПКМ
                    # Проверяем клик по слотам зелий на HUD
                    if self._handle_potion_slot_click(event.pos):
                        continue

            # Обработка нажатий клавиш (если ни одно меню не открыто)
            if event.type == pygame.KEYDOWN:
                self.input_handler.handle_key_press(event.key)

    def _check_npc_nearby(self):
        """Проверить наличие NPC рядом с игроком и открыть меню взаимодействия"""
        # Сначала проверяем, находимся ли мы в городе, деревне или школе магов
        tile = self.game_map.get_tile(self.player.x, self.player.y)
        if tile.has_location():
            location = tile.location
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY]:
                # Открываем меню города/деревни/академии магов/военной академии
                # Создаем постоянного торговца для этой локации если его нет
                if not hasattr(location, 'merchant_npc'):
                    if location.location_type == LOCATION_CITY:
                        merchant_level = 15  # Ранг 2: 11-20 уровень
                    elif location.location_type == LOCATION_MAGIC_SCHOOL:
                        merchant_level = 20  # Ранг 2: магическая академия
                    elif location.location_type == LOCATION_WARRIOR_ACADEMY:
                        merchant_level = 20  # Ранг 2: военная академия
                    else:
                        merchant_level = 5  # Ранг 1: деревни
                    location.merchant_npc = Merchant(f"Торговец {location.name}", self.player.x, self.player.y, merchant_level)

                # Открываем окно меню локации
                self.settlement_menu_window.set_location(location)
                self.settlement_menu_open = True
                print(f"Добро пожаловать в {location.name}!")
                return

        # Собираем всех NPC через менеджер
        all_npcs = self.npc_manager.get_all_npcs()

        # Ищем NPC рядом с игроком (в соседних клетках)
        nearby_npcs = []
        for npc in all_npcs:
            if not npc.is_alive:
                continue

            distance = abs(self.player.x - npc.x) + abs(self.player.y - npc.y)
            if distance <= 1:  # Соседняя клетка
                nearby_npcs.append(npc)

        # Если нет NPC рядом
        if not nearby_npcs:
            print("Рядом нет NPC для взаимодействия и вы не находитесь в городе/деревне!")
            return

        # Если только один NPC - сразу открываем меню взаимодействия
        if len(nearby_npcs) == 1:
            self.nearby_npc = nearby_npcs[0]
            self.interaction_menu_open = True
            print(f"Вы встретили: {self.nearby_npc.name}")
            return

        # Если несколько NPC - открываем меню выбора
        self.npc_selection_window.set_npcs(nearby_npcs)
        self.npc_selection_menu_open = True
        print(f"Рядом находится {len(nearby_npcs)} NPC. Выберите с кем взаимодействовать.")

    def open_quest_window(self, location):
        """Делегирование к QuestUIController."""
        self.quest_ui_controller.open_for_location(location)
        self.quest_window_open = self.quest_ui_controller.is_open

    def open_quest_window_anywhere(self):
        """Делегирование к QuestUIController."""
        self.quest_ui_controller.open_anywhere()
        self.quest_window_open = self.quest_ui_controller.is_open

    def _handle_quest_action(self, action):
        """Делегирование к QuestUIController."""
        self.quest_ui_controller.handle_action(action)

    def _handle_potion_slot_click(self, mouse_pos):
        """
        Обработка клика ПКМ по слоту зелья на HUD.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            bool: True если клик был обработан
        """
        if not hasattr(self.hud_renderer, 'potion_slot_rects'):
            return False

        mouse_x, mouse_y = mouse_pos

        for slot_index, (rect, slot, potion) in self.hud_renderer.potion_slot_rects.items():
            if rect.collidepoint(mouse_x, mouse_y):
                if potion:
                    # Используем зелье
                    result = potion.use(self.player)
                    print(result)
                    # Удаляем зелье из инвентаря
                    self.player.inventory.remove_item(potion, 1)
                    # Снимаем зелье из слота если его больше нет
                    if self.player.inventory.get_item_count(potion) == 0:
                        self.player.inventory.unequip_item(slot)
                    return True
                else:
                    print("Слот зелья пуст")
                    return True

        return False

    def _collect_resources(self):
        """Делегирование к ResourceSystem."""
        self.resource_system.collect_resources()

    def _start_combat(self, enemy, tactical=False):
        """
        Начать бой с NPC

        Args:
            enemy: Враг для боя
            tactical: Использовать тактический режим боя (по умолчанию False)
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

        if tactical:
            # Тактический бой
            from game.tactical_combat import TacticalCombatSystem, TacticalCombatRenderer, TacticalCombatUIHandler
            from game.tactical_combat.entourage_generator import EntourageGenerator

            # Генерируем свиту для врага
            entourage_generator = EntourageGenerator()
            entourage = entourage_generator.generate_entourage(enemy)

            if entourage:
                print(f"  Противник привел свиту: {len(entourage)} союзников!")

            self.tactical_combat_system = TacticalCombatSystem(
                self.player, enemy, self.screen, self.font, self.ui_scaler,
                self.game_map, self.respawn_manager, self.sprite_manager, self,
                entourage=entourage
            )
            self.tactical_combat_renderer = TacticalCombatRenderer(
                self.tactical_combat_system, self.screen, self.font, self.ui_scaler
            )
            self.tactical_combat_handler = TacticalCombatUIHandler(
                self.tactical_combat_system, self.tactical_combat_renderer
            )
            # Сохраняем ссылку на ui_handler в combat_system для доступа из renderer
            self.tactical_combat_system._ui_handler = self.tactical_combat_handler
            self.in_tactical_combat = True
            self.nearby_npc = None
        else:
            # Быстрый бой (обычная система)
            self.combat_system = CombatSystem(self.player, enemy, self.screen, self.font, self.ui_scaler, self.game_map, self.respawn_manager, self.sprite_manager, self)
            self.in_combat = True
            self.nearby_npc = None

    def _show_resource_collection_window(self, collected_items, collected_gold, location_name, location_type_display, event_message):
        """
        Показать окно сбора ресурсов

        Args:
            collected_items: Список собранных предметов [(item, quantity), ...]
            collected_gold: Количество собранного золота
            location_name: Название локации
            location_type_display: Отображаемый тип локации
            event_message: Сообщение о событии (опционально)
        """
        self.resource_collection_window.set_resources(
            collected_items,
            collected_gold,
            location_name,
            location_type_display,
            event_message
        )
        self.resource_collection_window_open = True

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
        self.hud_renderer.render()

        # Отрисовка мини-карты
        self.world_renderer.render_minimap()

        # Если идет бой, отрисовываем окно боя
        if self.in_combat and self.combat_system:
            self.combat_system.render()

        # Если идет тактический бой, отрисовываем его
        if self.in_tactical_combat and self.tactical_combat_renderer:
            self.tactical_combat_renderer.render()
            # Обновляем экран сразу для тактического боя
            pygame.display.flip()
            return  # Не отрисовываем остальное во время тактического боя

        # Если открыто меню выбора режима боя, отрисовываем его
        if self.combat_mode_menu_open and self.nearby_npc:
            self.combat_mode_window.render(self.nearby_npc.name, self.is_npc_aggression)

        # Если открыто меню выбора NPC, отрисовываем его
        if self.npc_selection_menu_open:
            self.npc_selection_window.render()

        # Если открыто меню взаимодействия, отрисовываем его
        if self.interaction_menu_open and self.nearby_npc:
            self.interaction_window.render(self.nearby_npc)

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

        # Если открыто окно крафта, отрисовываем его
        if self.crafting_window_open:
            mouse_pos = pygame.mouse.get_pos()
            self.crafting_window.render(self.crafting_system, self.player, mouse_pos)

        # Если открыто окно лута, отрисовываем его
        if self.loot_window_open:
            self.loot_window.render()

        # Если открыто окно сбора ресурсов, отрисовываем его
        if self.resource_collection_window_open:
            self.resource_collection_window.render()

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

        # Если открыто окно подтверждения выхода, отрисовываем его
        if self.exit_confirmation_open:
            self.exit_confirmation_window.render()

        # Если открыто меню города/деревни, отрисовываем его
        if self.settlement_menu_open:
            self.settlement_menu_window.render()

        # Если открыто меню расспроса, отрисовываем его
        if self.inquiry_menu_open:
            self.inquiry_menu_window.render()

        # Если открыто окно ответа на вопрос, отрисовываем его
        if self.inquiry_response_open:
            self.inquiry_response_window.render()

        # Отрисовка окна помощи (поверх всего)
        self.help_window.render()

        # Обновление дисплея
        pygame.display.flip()


