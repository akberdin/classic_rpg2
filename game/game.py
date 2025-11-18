"""
Основной класс игры
"""
import pygame
import random
from game.map import GameMap
from game.character import Player, Guard, Merchant, Bandit, Miner, Undead
from game.fog_of_war import FogOfWar
from game.combat import CombatSystem
from game.inventory import get_random_loot_from_location, PREDEFINED_ITEMS, EquipmentItem
from game.ui import HelpWindow, InventoryWindow, TradeWindow, UIHelper, CharacterWindow, UIScaler
from game.optimization import PerformanceOptimizer, RenderCache
from game.quests import QuestManager, AchievementManager, create_starter_quests
from game.save_system import SaveSystem
from game.skills import PowerStrike, Heal
from game.constants import (
    FPS, TILE_SIZE, COLORS,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_BANDIT_CAMP,
    LOCATION_MINE, LOCATION_RUINS
)


class Game:
    """Главный класс игры"""

    def __init__(self):
        """Инициализация игры"""
        # Получаем информацию о дисплее
        display_info = pygame.display.Info()
        self.window_width = display_info.current_w
        self.window_height = display_info.current_h

        # Окно игры в полноэкранном режиме с реальным разрешением
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Classic RPG")

        # Создаем масштабировщик UI для адаптивности
        self.ui_scaler = UIScaler(self.window_width, self.window_height)

        print(f"Инициализация игры с разрешением: {self.window_width}x{self.window_height}")

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

        # Создание стражников в городах
        self.guards = []
        self._spawn_guards()

        # Создание торговцев
        self.merchants = []
        self._spawn_merchants()

        # Создание бандитов в лагерях
        self.bandits = []
        self._spawn_bandits()

        # Создание шахтеров в шахтах
        self.miners = []
        self._spawn_miners()

        # Создание нежити в руинах
        self.undead = []
        self._spawn_undead()

        print(f"Игрок создан на позиции ({self.player.x}, {self.player.y})")
        print(f"Создано {len(self.guards)} стражников")
        print(f"Создано {len(self.merchants)} торговцев")
        print(f"Создано {len(self.bandits)} бандитов")
        print(f"Создано {len(self.miners)} шахтеров")
        print(f"Создано {len(self.undead)} нежити")

        # Даем игроку стартовые предметы
        self._give_starting_items()

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
        from game.skills import BasicAttack, Mining, Lumberjacking
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
        all_npcs = self.guards + self.merchants + self.bandits + self.miners + self.undead
        self.performance_optimizer.rebuild_spatial_grid(all_npcs)

        # Чит-режим (отключен по умолчанию)
        self.cheat_mode_active = False
        self.cheat_gold_given = False  # Флаг для выдачи золота один раз

        print("Игра готова к запуску!")

    def _give_starting_items(self):
        """Дать игроку стартовые предметы"""
        from game.inventory import ItemGenerator, ItemQuality

        # Начальное золото
        self.player.inventory.add_gold(50)

        # Стартовые зелья
        self.player.inventory.add_item(PREDEFINED_ITEMS["minor_health_potion"], 2)
        self.player.inventory.add_item(PREDEFINED_ITEMS["minor_stamina_potion"], 1)

        # Стартовое оружие - топор для рубки леса
        starter_axe = PREDEFINED_ITEMS["basic_axe"]
        self.player.inventory.add_item(starter_axe, 1)
        self.player.inventory.equip_item(starter_axe.name)

        # Генерируем простой доспех для торса
        starter_chest = ItemGenerator.generate_armor(level=1, quality=ItemQuality.COMMON)
        self.player.inventory.add_item(starter_chest, 1)
        if starter_chest.slot.value == "chest":
            self.player.inventory.equip_item(starter_chest.name)

        # Обновляем производные характеристики после экипировки
        self.player.update_derived_stats()

    def _spawn_guards(self):
        """Создание стражников в городах"""
        # Находим все города на карте
        cities = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_CITY]

        for city in cities:
            # Создаем 6-10 стражников возле каждого города (увеличено с 3-5)
            num_guards = random.randint(6, 10)

            for i in range(num_guards):
                # Находим позицию рядом с городом
                guard_pos = self._find_guard_position(city.x, city.y)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников от 5 до 20
                    guard_level = random.randint(5, 20)
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

        # Создаем 10-15 торговцев (увеличено с 5-8)
        num_merchants = random.randint(10, 15)

        for i in range(num_merchants):
            # Выбираем случайный стартовый населенный пункт
            start_settlement = random.choice(settlements)

            # Находим позицию рядом с населенным пунктом
            merchant_pos = self._find_guard_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                # Уровень торговцев от 2 до 8
                merchant_level = random.randint(2, 8)
                merchant_names = [
                    "Торговец Иван", "Купец Петр", "Торговка Мария",
                    "Купец Василий", "Торговец Николай", "Купчиха Анна",
                    "Странствующий торговец", "Заезжий купец"
                ]
                merchant_name = random.choice(merchant_names)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)

                self.merchants.append(merchant)

    def _spawn_bandits(self):
        """Создание бандитов в лагерях"""
        # Находим все бандитские лагеря на карте
        bandit_camps = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_BANDIT_CAMP]

        for camp in bandit_camps:
            # Создаем 7-12 бандитов возле каждого лагеря (увеличено с 4-7)
            num_bandits = random.randint(7, 12)

            for i in range(num_bandits):
                # Находим позицию рядом с лагерем
                bandit_pos = self._find_guard_position(camp.x, camp.y)
                if bandit_pos:
                    bx, by = bandit_pos
                    # Уровень бандитов от 3 до 15
                    bandit_level = random.randint(3, 15)
                    bandit_names = [
                        "Бандит", "Разбойник", "Головорез", "Грабитель",
                        "Налетчик", "Лихой человек", "Бандюган", "Воришка"
                    ]
                    bandit_name = f"{random.choice(bandit_names)} {camp.name}"

                    # Создаем бандита с привязкой к лагерю
                    bandit = Bandit(bandit_name, bx, by, bandit_level, camp.x, camp.y)

                    self.bandits.append(bandit)

    def _spawn_miners(self):
        """Создание шахтеров в шахтах"""
        # Находим все шахты на карте
        mines = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_MINE]

        for mine in mines:
            # Создаем 5-8 шахтеров возле каждой шахты (увеличено с 3-5)
            num_miners = random.randint(5, 8)

            for i in range(num_miners):
                # Находим позицию рядом с шахтой
                miner_pos = self._find_guard_position(mine.x, mine.y)
                if miner_pos:
                    mx, my = miner_pos
                    # Уровень шахтеров от 2 до 8
                    miner_level = random.randint(2, 8)
                    miner_names = [
                        "Шахтер", "Рудокоп", "Горняк", "Копатель"
                    ]
                    miner_name = f"{random.choice(miner_names)} {mine.name}"

                    # Создаем шахтера с привязкой к шахте
                    miner = Miner(miner_name, mx, my, miner_level, mine.x, mine.y)

                    self.miners.append(miner)

    def _spawn_undead(self):
        """Создание нежити в руинах"""
        # Находим все руины на карте
        ruins = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_RUINS]

        for ruin in ruins:
            # Создаем 5-10 нежити возле каждых руин (увеличено с 3-6)
            num_undead = random.randint(5, 10)

            for i in range(num_undead):
                # Находим позицию рядом с руинами (в пределах 7 клеток)
                undead_pos = None
                for attempt in range(20):
                    offset_x = random.randint(-7, 7)
                    offset_y = random.randint(-7, 7)
                    ux = ruin.x + offset_x
                    uy = ruin.y + offset_y

                    if self.game_map.is_valid_position(ux, uy):
                        tile = self.game_map.get_tile(ux, uy)
                        if tile.is_passable():
                            undead_pos = (ux, uy)
                            break

                if undead_pos:
                    ux, uy = undead_pos
                    # 4 ранга нежити (уровни распределяем от 1 до 40)
                    undead_level = random.randint(1, 40)
                    undead_names = [
                        "Зомби", "Скелет", "Мертвец", "Призрак",
                        "Нежить", "Упырь", "Костяк", "Тень"
                    ]
                    undead_name = f"{random.choice(undead_names)} {ruin.name}"

                    # Создаем нежить с привязкой к руинам
                    undead = Undead(undead_name, ux, uy, undead_level, ruin.x, ruin.y)

                    self.undead.append(undead)

    def advance_time(self, hours=1, skip_player_recovery=False):
        """
        Продвинуть игровое время на указанное количество часов

        Args:
            hours: Количество часов для продвижения
            skip_player_recovery: Не восстанавливать выносливость игрока (используется при отдыхе)
        """
        self.game_hour += hours

        # Если прошло 24 часа, начинается новый день
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1

        # Обновляем AI всех NPC при изменении времени
        for _ in range(hours):
            # Восстанавливаем выносливость игрока (если не пропускаем)
            if not skip_player_recovery:
                self.player.recover_stamina()

            # Обновляем перезарядки навыков и статус-эффекты игрока
            self.player.skill_manager.tick_cooldowns()
            effect_messages = self.player.skill_manager.tick_status_effects()
            for msg in effect_messages:
                print(msg)

            # Перестраиваем spatial grid для оптимизации
            all_npcs = self.guards + self.merchants + self.bandits + self.miners + self.undead
            self.performance_optimizer.rebuild_spatial_grid(all_npcs)

            # Увеличиваем счетчик для оптимизации AI
            self.performance_optimizer.increment_counter()

            # Обновляем AI только тех NPC, которых нужно обновлять в этом кадре
            for guard in self.guards:
                if self.performance_optimizer.should_update_ai(guard, self.player.x, self.player.y):
                    guard.update_ai(self.game_map, all_npcs)

            for merchant in self.merchants:
                if self.performance_optimizer.should_update_ai(merchant, self.player.x, self.player.y):
                    merchant.update_ai(self.game_map, all_npcs)

            for bandit in self.bandits:
                if self.performance_optimizer.should_update_ai(bandit, self.player.x, self.player.y):
                    bandit.update_ai(self.game_map, all_npcs, self.player)

            for miner in self.miners:
                if self.performance_optimizer.should_update_ai(miner, self.player.x, self.player.y):
                    miner.update_ai(self.game_map, all_npcs)

            for undead_npc in self.undead:
                if self.performance_optimizer.should_update_ai(undead_npc, self.player.x, self.player.y):
                    undead_npc.update_ai(self.game_map, all_npcs, self.player)

        # Проверяем, атаковал ли кто-то игрока (принудительное открытие окна боя)
        if self.player.attacked_by_npc and not self.in_combat:
            attacker = self.player.attacked_by_npc
            self.player.attacked_by_npc = None  # Сбрасываем флаг
            if attacker.is_alive:  # Проверяем что атакующий еще жив
                self._start_combat(attacker)
                print(f"{attacker.name} напал на вас!")

        # Проверяем достижения
        unlocked = self.achievement_manager.check_achievements(self.player)
        for achievement in unlocked:
            print(f"🏆 Достижение разблокировано: {achievement.name}!")
            print(f"   {achievement.description}")

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
                    self._handle_interaction_choice(event.key)
                continue

            # Если открыто меню инвентаря, обрабатываем его
            if self.inventory_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_inventory_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # ПКМ
                        self._handle_inventory_right_click(event.pos)
                continue

            # Если открыто меню торговли, обрабатываем его
            if self.trade_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_trade_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # ПКМ
                        self._handle_trade_right_click(event.pos)
                continue

            # Если открыто окно характеристик, обрабатываем его
            if self.character_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_character_input(event.key)
                continue

            # Если открыто окно книги умений, обрабатываем его
            if self.skill_book_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_skill_book_input(event.key)
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
            self.advance_time(1, skip_player_recovery=True)
            print(f"Вы отдохнули. {self.get_time_string()}")
            return
        elif key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_e:
            # Взаимодействие с NPC
            self._check_npc_nearby()
            return
        elif key == pygame.K_f:
            # Сбор ресурсов с локации
            self._collect_resources()
            return
        elif key == pygame.K_F5:
            # Быстрое сохранение
            SaveSystem.save_game(self, "autosave")
            print("Игра сохранена!")
            return
        elif key == pygame.K_F9:
            # Быстрая загрузка (не реализована в этой версии - требует рестарта)
            print("Для загрузки используйте параметр при запуске игры")
            return
        elif key == pygame.K_k:
            # Открыть/закрыть книгу умений
            self.skill_book_menu_open = not getattr(self, 'skill_book_menu_open', False)
            return
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                     pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
            # Использовать умение из слота (клавиши 1-8)
            slot_index = key - pygame.K_1  # Преобразуем код клавиши в индекс слота (0-7)
            skill = self.player.skill_manager.get_slot_skill(slot_index)
            if skill:
                # Используем умение вне боя (применяется только к ремесленным умениям)
                if skill.category.value == 'crafting':
                    result = self.player.skill_manager.use_skill_from_slot(slot_index)
                    print(result['message'])
                else:
                    print(f"{skill.name} можно использовать только в бою!")
            else:
                print(f"Слот {slot_index + 1} пуст!")
            return
        elif key == pygame.K_i:
            # Открыть/закрыть инвентарь
            self.inventory_menu_open = not self.inventory_menu_open
            return
        elif key == pygame.K_c:
            # Открыть/закрыть окно характеристик
            self.character_menu_open = not self.character_menu_open
            return
        elif key == pygame.K_F1:
            # Открыть/закрыть окно помощи
            self.help_window.toggle()
            return
        elif key == pygame.K_F2:
            # Включить/выключить чит-мод
            self.cheat_mode_active = not self.cheat_mode_active
            self.player.godmode = self.cheat_mode_active  # Устанавливаем режим бессмертия
            if self.cheat_mode_active:
                print("ЧИТ-МОД АКТИВИРОВАН:")
                print("- Бесконечное здоровье и выносливость")
                print("- Вся карта открыта")
                print("- Туман войны отключен")

                # Выдаем золото один раз при активации
                if not self.cheat_gold_given:
                    self.player.inventory.add_gold(5000)
                    print("- Получено 5000 золота")
                    self.cheat_gold_given = True

                # Открываем всю карту (устанавливаем explored для всех тайлов)
                for x in range(self.game_map.width):
                    for y in range(self.game_map.height):
                        tile = self.game_map.get_tile(x, y)
                        if tile:
                            tile.explored = True
            else:
                print("ЧИТ-МОД ОТКЛЮЧЕН")
            return

        # Попытка переместить игрока
        if moved:
            # Проверяем выносливость перед движением
            if self.player.is_resting:
                print("Вы слишком устали и должны отдохнуть!")
                return

            if not self.player.consume_stamina():
                print("У вас недостаточно выносливости! Нажмите R для отдыха.")
                return

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
        self.advance_time(1)
        print(f"Время: {self.get_time_string()}")

    def _handle_inventory_input(self, key):
        """
        Обработка ввода в меню инвентаря

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_i:
            self.inventory_menu_open = False
            return

        all_items = self.player.inventory.get_all_items()

        if key == pygame.K_UP or key == pygame.K_w:
            if all_items:
                self.inventory_window.selected_inventory_index = max(0, self.inventory_window.selected_inventory_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if all_items:
                self.inventory_window.selected_inventory_index = min(len(all_items) - 1, self.inventory_window.selected_inventory_index + 1)
        elif key == pygame.K_RETURN or key == pygame.K_u:
            # Использовать выбранный предмет
            if all_items and 0 <= self.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.inventory_window.selected_inventory_index]
                result = self.player.use_item(item.name)
                print(result)
                # Если предметов больше нет, корректируем индекс
                if self.player.inventory.get_item(item.name) is None:
                    all_items = self.player.inventory.get_all_items()
                    self.inventory_window.selected_inventory_index = min(self.inventory_window.selected_inventory_index, len(all_items) - 1)
                    if self.inventory_window.selected_inventory_index < 0:
                        self.inventory_window.selected_inventory_index = 0
        elif key == pygame.K_e:
            # Экипировать выбранный предмет
            if all_items and 0 <= self.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.inventory_window.selected_inventory_index]
                if isinstance(item, EquipmentItem):
                    success, message = self.player.inventory.equip_item(item.name)
                    print(message)
                    # Обновляем производные характеристики после экипировки
                    if success:
                        self.player.update_derived_stats()
                else:
                    print("Этот предмет нельзя экипировать")
        elif key == pygame.K_q:
            # Снять экипированный предмет через выбранный слот
            if self.inventory_window.selected_equipment_slot:
                slot = self.inventory_window.selected_equipment_slot
                item = self.player.inventory.get_equipped_item(slot)
                if item:
                    success, message = self.player.inventory.unequip_item(slot)
                    print(message)
                    if success:
                        self.player.update_derived_stats()
                else:
                    print("В этом слоте нет предмета")
            else:
                print("Выберите слот экипировки для снятия предмета")

    def _handle_inventory_right_click(self, mouse_pos):
        """
        Обработка правого клика мыши в инвентаре

        Args:
            mouse_pos: Позиция мыши (x, y)
        """
        from game.inventory import EquipmentItem

        mouse_x, mouse_y = mouse_pos

        # Проверяем клик по предмету в инвентаре
        item = self.inventory_window.get_item_at_mouse(self.player, mouse_x, mouse_y)
        if item:
            # Клик по предмету в инвентаре - экипировать его
            if isinstance(item, EquipmentItem):
                success, message = self.player.inventory.equip_item(item.name)
                print(message)
                if success:
                    self.player.update_derived_stats()
            else:
                print("Этот предмет нельзя экипировать")
            return

        # Проверяем клик по экипированному предмету
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Размеры окна (адаптивные)
        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(900)
            window_height = self.ui_scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Левая панель - экипировка
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        equipment_panel_x = window_x + margin
        equipment_panel_y = window_y + panel_y_offset
        equipment_panel_width = int(400 * (window_width / 900))

        # Проверяем, находится ли курсор в области экипировки
        if equipment_panel_x <= mouse_x <= equipment_panel_x + equipment_panel_width:
            # Вычисляем на какой слот кликнули
            from game.inventory import EquipmentSlot

            slot_y_start = equipment_panel_y + int(40 * (window_height / 650))
            slot_height = max(22, int(28 * (window_height / 650)))

            # Группировка слотов (такая же как в ui.py)
            slot_groups = [
                ("Оружие", [EquipmentSlot.WEAPON]),
                ("Доспехи", [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]),
                ("Кольца", [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]),
                ("Украшения", [EquipmentSlot.AMULET, EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]),
            ]

            current_y = slot_y_start
            for group_name, slots in slot_groups:
                # Пропускаем заголовок группы
                current_y += max(20, int(25 * (window_height / 650)))

                for slot in slots:
                    # Проверяем клик по этому слоту
                    if current_y <= mouse_y <= current_y + slot_height:
                        item = self.player.inventory.get_equipped_item(slot)
                        if item:
                            success, message = self.player.inventory.unequip_item(slot)
                            print(message)
                            if success:
                                self.player.update_derived_stats()
                        else:
                            print(f"Слот {group_name} пуст")
                        return

                    current_y += slot_height

                # Пропускаем отступ между группами
                current_y += max(8, int(10 * (window_height / 650)))

    def _handle_interaction_choice(self, key):
        """
        Обработка выбора в меню взаимодействия

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_1:
            # Торговля
            if self.nearby_npc and self.nearby_npc.npc_type == "merchant":
                self.trade_menu_open = True
                self.trade_window.mode = "buy"
                self.trade_window.selected_merchant_index = 0
                self.trade_window.selected_player_index = 0
                print(f"Торговля с {self.nearby_npc.name}")
            else:
                print(f"{self.nearby_npc.name} не торгует")
            self.interaction_menu_open = False
        elif key == pygame.K_2:
            # Агрессия - начать бой
            self._start_combat(self.nearby_npc)
            self.interaction_menu_open = False
        elif key == pygame.K_3:
            # Уйти
            print("Вы ушли от разговора.")
            self.interaction_menu_open = False
            self.nearby_npc = None
        elif key == pygame.K_ESCAPE:
            # Также можно закрыть меню через ESC
            self.interaction_menu_open = False
            self.nearby_npc = None

    def _handle_trade_input(self, key):
        """
        Обработка ввода в меню торговли

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE:
            self.trade_menu_open = False
            self.nearby_npc = None
            return
        elif key == pygame.K_TAB:
            # Переключение между покупкой и продажей
            if self.trade_window.mode == "buy":
                self.trade_window.mode = "sell"
            else:
                self.trade_window.mode = "buy"
            return

        if self.trade_window.mode == "buy":
            # Режим покупки
            if not hasattr(self.nearby_npc, 'inventory'):
                return

            merchant_items = self.nearby_npc.inventory.get_all_items()
            if not merchant_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.trade_window.selected_merchant_index = max(0, self.trade_window.selected_merchant_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.trade_window.selected_merchant_index = min(len(merchant_items) - 1, self.trade_window.selected_merchant_index + 1)
            elif key == pygame.K_RETURN:
                # Купить выбранный предмет
                if 0 <= self.trade_window.selected_merchant_index < len(merchant_items):
                    item, quantity = merchant_items[self.trade_window.selected_merchant_index]
                    buy_price = int(item.value * 1.5)  # Торговец продает с наценкой 50%

                    if self.player.inventory.gold >= buy_price:
                        if self.nearby_npc.inventory.remove_item(item.name, 1):
                            if self.player.inventory.add_item(item, 1):
                                self.player.inventory.remove_gold(buy_price)
                                self.nearby_npc.inventory.add_gold(buy_price)
                                print(f"Вы купили {item.name} за {buy_price} золота")
                            else:
                                # Возвращаем предмет торговцу если не поместился в инвентарь
                                self.nearby_npc.inventory.add_item(item, 1)
                                print("Ваш инвентарь переполнен!")
                    else:
                        print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.player.inventory.gold}")
        else:
            # Режим продажи
            player_items = self.player.inventory.get_all_items()
            if not player_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.trade_window.selected_player_index = max(0, self.trade_window.selected_player_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.trade_window.selected_player_index = min(len(player_items) - 1, self.trade_window.selected_player_index + 1)
            elif key == pygame.K_RETURN:
                # Продать выбранный предмет
                if 0 <= self.trade_window.selected_player_index < len(player_items):
                    item, quantity = player_items[self.trade_window.selected_player_index]
                    sell_price = int(item.value * 0.7)  # Торговец покупает за 70% от стоимости

                    if self.nearby_npc.inventory.gold >= sell_price:
                        if self.player.inventory.remove_item(item.name, 1):
                            if self.nearby_npc.inventory.add_item(item, 1):
                                self.player.inventory.add_gold(sell_price)
                                self.nearby_npc.inventory.remove_gold(sell_price)
                                print(f"Вы продали {item.name} за {sell_price} золота")

                                # Обновляем прогресс квеста "Начинающий торговец"
                                self.player.items_sold += 1
                                self.quest_manager.update_quest_progress("merchant", 0, 1)
                            else:
                                # Возвращаем предмет игроку если не поместился в инвентарь торговца
                                self.player.inventory.add_item(item, 1)
                                print("У торговца нет места для этого предмета!")
                    else:
                        print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.nearby_npc.inventory.gold}")

    def _handle_trade_right_click(self, pos):
        """
        Обработка правого клика мыши в окне торговли

        Args:
            pos: Позиция клика (x, y)
        """
        mouse_x, mouse_y = pos

        # Получаем индекс предмета под курсором
        item_index = self.trade_window.get_item_index_at_mouse(mouse_x, mouse_y)

        if item_index is None:
            return

        if self.trade_window.mode == "buy":
            # Режим покупки
            if not hasattr(self.nearby_npc, 'inventory'):
                return

            merchant_items = self.nearby_npc.inventory.get_all_items()
            if not merchant_items or item_index >= len(merchant_items):
                return

            # Выбираем предмет и покупаем
            self.trade_window.selected_merchant_index = item_index
            item, quantity = merchant_items[item_index]
            buy_price = int(item.value * 1.5)

            if self.player.inventory.gold >= buy_price:
                if self.nearby_npc.inventory.remove_item(item.name, 1):
                    if self.player.inventory.add_item(item, 1):
                        self.player.inventory.remove_gold(buy_price)
                        self.nearby_npc.inventory.add_gold(buy_price)
                        print(f"Вы купили {item.name} за {buy_price} золота")
                    else:
                        self.nearby_npc.inventory.add_item(item, 1)
                        print("Ваш инвентарь переполнен!")
            else:
                print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.player.inventory.gold}")
        else:
            # Режим продажи
            player_items = self.player.inventory.get_all_items()
            if not player_items or item_index >= len(player_items):
                return

            # Выбираем предмет и продаем
            self.trade_window.selected_player_index = item_index
            item, quantity = player_items[item_index]
            sell_price = int(item.value * 0.7)

            if self.nearby_npc.inventory.gold >= sell_price:
                if self.player.inventory.remove_item(item.name, 1):
                    if self.nearby_npc.inventory.add_item(item, 1):
                        self.player.inventory.add_gold(sell_price)
                        self.nearby_npc.inventory.remove_gold(sell_price)
                        print(f"Вы продали {item.name} за {sell_price} золота")

                        # Обновляем прогресс квеста "Начинающий торговец"
                        self.player.items_sold += 1
                        self.quest_manager.update_quest_progress("merchant", 0, 1)
                    else:
                        self.player.inventory.add_item(item, 1)
                        print("У торговца нет места для этого предмета!")
            else:
                print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.nearby_npc.inventory.gold}")

    def _handle_character_input(self, key):
        """
        Обработка ввода в окне характеристик

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_c:
            self.character_menu_open = False
            return

        # Навигация по характеристикам
        if key == pygame.K_UP or key == pygame.K_w:
            self.character_window.selected_stat_index = max(0, self.character_window.selected_stat_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.character_window.selected_stat_index = min(5, self.character_window.selected_stat_index + 1)
        elif key == pygame.K_RETURN:
            # Добавить очко к выбранной характеристике
            if self.player.stat_points > 0:
                stat_key, stat_name = self.character_window.stats_list[self.character_window.selected_stat_index]
                if self.player.add_stat_point(stat_key):
                    print(f"{stat_name} увеличена! Осталось очков: {self.player.stat_points}")

    def _handle_skill_book_input(self, key):
        """
        Обработка ввода в окне книги умений

        Args:
            key: Нажатая клавиша
        """
        from game.skills import SkillCategory

        if key == pygame.K_ESCAPE or key == pygame.K_k:
            self.skill_book_menu_open = False
            return

        # Переключение между вкладками (TAB)
        if key == pygame.K_TAB:
            self.skill_book_window.selected_tab = (self.skill_book_window.selected_tab + 1) % 3
            self.skill_book_window.selected_skill_index = 0
            return

        # Навигация по умениям (W/S)
        if key == pygame.K_UP or key == pygame.K_w:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.skill_book_window.selected_tab]
            skills_dict = self.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.skill_book_window.selected_skill_index = max(0, self.skill_book_window.selected_skill_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.skill_book_window.selected_tab]
            skills_dict = self.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.skill_book_window.selected_skill_index = min(len(skills) - 1, self.skill_book_window.selected_skill_index + 1)

        # Навигация по слотам (A/D)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self.skill_book_window.selected_slot_index = max(0, self.skill_book_window.selected_slot_index - 1)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.skill_book_window.selected_slot_index = min(7, self.skill_book_window.selected_slot_index + 1)

        # Назначить умение в слот (Enter)
        elif key == pygame.K_RETURN:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.skill_book_window.selected_tab]
            skills_dict = self.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]

            if skills and self.skill_book_window.selected_skill_index < len(skills):
                # Найдем ID умения
                selected_skill = skills[self.skill_book_window.selected_skill_index]
                skill_id = None
                for sid, skill in skills_dict.items():
                    if skill == selected_skill:
                        skill_id = sid
                        break

                if skill_id:
                    success = self.player.skill_manager.assign_to_slot(
                        skill_id,
                        self.skill_book_window.selected_slot_index
                    )
                    if success:
                        print(f"{selected_skill.name} назначено в слот {self.skill_book_window.selected_slot_index + 1}")
                    else:
                        print("Не удалось назначить умение в слот")

        # Убрать умение из слота (Delete)
        elif key == pygame.K_DELETE:
            self.player.skill_manager.unassign_from_slot(self.skill_book_window.selected_slot_index)
            print(f"Слот {self.skill_book_window.selected_slot_index + 1} очищен")

    def _start_combat(self, enemy):
        """
        Начать бой с NPC

        Args:
            enemy: Враг для боя
        """
        print(f"Бой начался с {enemy.name}!")
        self.combat_system = CombatSystem(self.player, enemy, self.screen, self.font, self.ui_scaler)
        self.in_combat = True
        self.nearby_npc = None

    def _update(self):
        """Обновление состояния игры"""
        # AI стражников обновляется в методе advance_time

        # Чит-мод: восстанавливаем здоровье и выносливость
        if self.cheat_mode_active:
            self.player.health = self.player.max_health
            self.player.stamina = self.player.max_stamina
            self.player.is_resting = False

    def _update_camera(self):
        """Обновление позиции камеры, чтобы следить за игроком"""
        # Вычисляем размер видимой области в тайлах
        tiles_x = self.window_width // TILE_SIZE
        tiles_y = (self.window_height - 100) // TILE_SIZE  # -100 для UI панели

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

        # Отрисовка мини-карты
        self._render_minimap()

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

    def _get_time_of_day_tint(self):
        """
        Получить цветовой оттенок в зависимости от времени суток

        Returns:
            tuple: (r, g, b) - компонент затемнения (0-255)
        """
        # Ночь: 0-5 часов и 22-23 часа
        # Рассвет: 6-7 часов
        # День: 8-17 часов
        # Закат: 18-21 часов

        hour = self.game_hour

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

    def _apply_time_of_day_tint(self, color):
        """
        Применить оттенок времени суток к цвету

        Args:
            color: Исходный цвет (r, g, b)

        Returns:
            tuple: Модифицированный цвет
        """
        tint = self._get_time_of_day_tint()
        return (
            int(color[0] * tint[0] / 255),
            int(color[1] * tint[1] / 255),
            int(color[2] * tint[2] / 255)
        )

    def _render_map(self):
        """Отрисовка карты с учетом камеры и тумана войны"""
        # Вычисляем видимую область
        tiles_x = self.window_width // TILE_SIZE + 1
        tiles_y = (self.window_height - 100) // TILE_SIZE + 1

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
                    # В чит-режиме все тайлы видимы
                    is_visible = self.cheat_mode_active or self.fog_of_war.is_visible(map_x, map_y, self.player.x, self.player.y)
                    if not is_visible:
                        color = tuple(c // 2 for c in color)  # Затемняем цвет
                    else:
                        # Применяем оттенок времени суток только к видимым тайлам
                        color = self._apply_time_of_day_tint(color)

                    # Отрисовка тайла
                    if tile.has_location() and is_visible:
                        # Используем спрайт для видимой локации
                        def draw_default():
                            pygame.draw.rect(
                                self.screen,
                                color,
                                (screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                            )
                        self.sprite_manager.render_location(
                            self.screen,
                            tile.location.location_type,
                            screen_x,
                            screen_y,
                            draw_default
                        )
                    else:
                        # Обычная отрисовка для биомов и невидимых локаций
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
                    if not guard.is_alive:
                        continue

                    guard_screen_x = (guard.x - self.camera_x) * TILE_SIZE
                    guard_screen_y = (guard.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от уровня стражника (4 варианта)
                    if guard.level <= 7:
                        # Новичок - светло-синий
                        base_color = (100, 150, 255)
                    elif guard.level <= 12:
                        # Опытный - синий
                        base_color = (50, 100, 220)
                    elif guard.level <= 17:
                        # Ветеран - темно-синий
                        base_color = (30, 70, 180)
                    else:
                        # Элита - фиолетово-синий
                        base_color = (80, 50, 200)

                    # Модификация цвета в зависимости от состояния
                    if guard.state == "rest":
                        guard_color = tuple(max(0, c - 40) for c in base_color)
                    elif guard.state == "combat":
                        guard_color = tuple(min(255, c + 40) for c in base_color)
                    else:
                        guard_color = base_color

                    # Отрисовка стражника (круг с обводкой для элиты)
                    pygame.draw.circle(
                        self.screen,
                        guard_color,
                        (guard_screen_x + TILE_SIZE // 2, guard_screen_y + TILE_SIZE // 2),
                        TILE_SIZE // 3
                    )

                    # Обводка для элитных стражников
                    if guard.level > 17:
                        pygame.draw.circle(
                            self.screen,
                            (200, 200, 50),
                            (guard_screen_x + TILE_SIZE // 2, guard_screen_y + TILE_SIZE // 2),
                            TILE_SIZE // 3,
                            2
                        )

        # Отрисовка торговцев
        for merchant in self.merchants:
            # Проверяем, находится ли торговец в зоне видимости камеры
            if (self.camera_x <= merchant.x < self.camera_x + tiles_x and
                self.camera_y <= merchant.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы торговца (туман войны)
                tile = self.game_map.get_tile(merchant.x, merchant.y)
                if tile.explored and self.fog_of_war.is_visible(merchant.x, merchant.y, self.player.x, self.player.y):
                    if not merchant.is_alive:
                        continue

                    merchant_screen_x = (merchant.x - self.camera_x) * TILE_SIZE
                    merchant_screen_y = (merchant.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния торговца
                    if merchant.state == "rest":
                        merchant_color = (150, 100, 50)  # Коричневый для отдыха/торговли
                    elif merchant.state == "flee":
                        merchant_color = (255, 200, 100)  # Светлый для побега
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

        # Отрисовка бандитов
        for bandit in self.bandits:
            # Проверяем, находится ли бандит в зоне видимости камеры
            if (self.camera_x <= bandit.x < self.camera_x + tiles_x and
                self.camera_y <= bandit.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы бандита (туман войны)
                tile = self.game_map.get_tile(bandit.x, bandit.y)
                if tile.explored and self.fog_of_war.is_visible(bandit.x, bandit.y, self.player.x, self.player.y):
                    if not bandit.is_alive:
                        continue

                    bandit_screen_x = (bandit.x - self.camera_x) * TILE_SIZE
                    bandit_screen_y = (bandit.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния бандита
                    if bandit.state == "rest":
                        bandit_color = (150, 0, 0)  # Темно-красный для отдыха
                    elif bandit.state == "combat":
                        bandit_color = (255, 50, 50)  # Ярко-красный для боя
                    else:
                        bandit_color = (200, 0, 0)  # Красный для патруля

                    # Отрисовка бандита (треугольник для отличия от других)
                    center_x = bandit_screen_x + TILE_SIZE // 2
                    center_y = bandit_screen_y + TILE_SIZE // 2
                    size = TILE_SIZE // 3

                    points = [
                        (center_x, center_y - size),  # Верх
                        (center_x - size, center_y + size),  # Левый низ
                        (center_x + size, center_y + size)   # Правый низ
                    ]

                    pygame.draw.polygon(
                        self.screen,
                        bandit_color,
                        points
                    )

        # Отрисовка шахтеров
        for miner in self.miners:
            # Проверяем, находится ли шахтер в зоне видимости камеры
            if (self.camera_x <= miner.x < self.camera_x + tiles_x and
                self.camera_y <= miner.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы шахтера (туман войны)
                tile = self.game_map.get_tile(miner.x, miner.y)
                if tile.explored and self.fog_of_war.is_visible(miner.x, miner.y, self.player.x, self.player.y):
                    if not miner.is_alive:
                        continue

                    miner_screen_x = (miner.x - self.camera_x) * TILE_SIZE
                    miner_screen_y = (miner.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния шахтера
                    if miner.state == "rest":
                        miner_color = (100, 70, 40)  # Коричневый для отдыха
                    elif miner.state == "flee":
                        miner_color = (200, 150, 100)  # Светло-коричневый для побега
                    else:
                        miner_color = (150, 100, 50)  # Темно-коричневый для работы

                    # Отрисовка шахтера (квадрат)
                    pygame.draw.rect(
                        self.screen,
                        miner_color,
                        (miner_screen_x + TILE_SIZE // 4, miner_screen_y + TILE_SIZE // 4,
                         TILE_SIZE // 2, TILE_SIZE // 2)
                    )

        # Отрисовка нежити
        for undead_npc in self.undead:
            # Проверяем, находится ли нежить в зоне видимости камеры
            if (self.camera_x <= undead_npc.x < self.camera_x + tiles_x and
                self.camera_y <= undead_npc.y < self.camera_y + tiles_y):

                # Проверяем, видим ли мы нежить (туман войны)
                tile = self.game_map.get_tile(undead_npc.x, undead_npc.y)
                if tile.explored and self.fog_of_war.is_visible(undead_npc.x, undead_npc.y, self.player.x, self.player.y):
                    if not undead_npc.is_alive:
                        continue

                    undead_screen_x = (undead_npc.x - self.camera_x) * TILE_SIZE
                    undead_screen_y = (undead_npc.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от уровня нежити (4 ранга)
                    if undead_npc.level <= 10:
                        # Зомби - серо-зеленый
                        base_color = (80, 100, 80)
                    elif undead_npc.level <= 20:
                        # Скелет - серо-фиолетовый
                        base_color = (120, 80, 120)
                    elif undead_npc.level <= 30:
                        # Мертвец - темно-фиолетовый
                        base_color = (100, 0, 100)
                    else:
                        # Призрак - ярко-фиолетовый
                        base_color = (150, 0, 150)

                    # Модификация цвета в зависимости от состояния
                    if undead_npc.state == "rest":
                        undead_color = tuple(max(0, c - 30) for c in base_color)
                    elif undead_npc.state == "combat":
                        undead_color = tuple(min(255, c + 50) for c in base_color)
                    else:
                        undead_color = base_color

                    # Отрисовка нежити (ромб)
                    center_x = undead_screen_x + TILE_SIZE // 2
                    center_y = undead_screen_y + TILE_SIZE // 2
                    size = TILE_SIZE // 3

                    points = [
                        (center_x, center_y - size),  # Верх
                        (center_x + size, center_y),  # Право
                        (center_x, center_y + size),  # Низ
                        (center_x - size, center_y)   # Лево
                    ]

                    pygame.draw.polygon(
                        self.screen,
                        undead_color,
                        points
                    )

                    # Обводка для элитной нежити
                    if undead_npc.level > 30:
                        pygame.draw.polygon(
                            self.screen,
                            (255, 0, 255),
                            points,
                            2
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
            f"{self.get_time_string()} | Золото: {self.player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(time_gold_text, (self.window_width - 350, info_y + 5))

        # Прогресс-бары
        bar_y = info_y + 35
        bar_width = 350
        bar_height = 18

        # Полоса здоровья (красная)
        UIHelper.draw_progress_bar(
            self.screen,
            info_x, bar_y, bar_width, bar_height,
            self.player.health, self.player.max_health,
            bg_color=(60, 20, 20),
            fill_color=(200, 50, 50),
            border_color=(255, 100, 100),
            text=f"HP: {self.player.health}/{self.player.max_health}",
            font=self.info_font
        )

        # Полоса маны (синяя)
        UIHelper.draw_progress_bar(
            self.screen,
            info_x + 380, bar_y, bar_width, bar_height,
            self.player.mana, self.player.max_mana,
            bg_color=(20, 20, 60),
            fill_color=(50, 100, 200),
            border_color=(100, 150, 255),
            text=f"MP: {self.player.mana}/{self.player.max_mana}",
            font=self.info_font
        )

        # Полоса выносливости (оранжевая)
        stamina_color = (200, 120, 50) if not self.player.is_resting else (150, 70, 30)
        stamina_status = " [ОТДЫХ]" if self.player.is_resting else ""
        UIHelper.draw_progress_bar(
            self.screen,
            info_x + 760, bar_y, bar_width, bar_height,
            self.player.stamina, self.player.max_stamina,
            bg_color=(60, 40, 20),
            fill_color=stamina_color,
            border_color=(255, 165, 0),
            text=f"Stamina: {self.player.stamina}/{self.player.max_stamina}{stamina_status}",
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
            self.screen.blit(stat_points_text, (info_x + 300, bar_y + 30))

        # Подсказка о помощи
        help_hint = self.info_font.render(
            "F1 - Справка | C - Характеристики | I - Инвентарь | K - Книга умений",
            True,
            (180, 180, 180)
        )
        self.screen.blit(help_hint, (info_x + 800, info_y + 55))

        # Панель умений (8 слотов)
        self._render_skill_panel()

    def _render_skill_panel(self):
        """Отрисовка панели умений над панелью параметров"""
        # Размеры и позиция
        slot_size = 48
        slot_spacing = 8
        panel_x = (self.window_width - (slot_size + slot_spacing) * 8) // 2
        # Поднимаем над панелью параметров (ui_height = 100)
        ui_height = 100
        ui_y = self.window_height - ui_height
        panel_y = ui_y - slot_size - 15

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

    def _render_minimap(self):
        """Отрисовка мини-карты"""
        # Размеры мини-карты
        minimap_size = 150
        minimap_x = self.window_width - minimap_size - 10
        minimap_y = 10
        pixel_per_tile = 1.5  # Размер одного тайла на мини-карте

        # Фон мини-карты
        pygame.draw.rect(
            self.screen,
            (20, 20, 25),
            (minimap_x, minimap_y, minimap_size, minimap_size)
        )

        # Рамка мини-карты
        pygame.draw.rect(
            self.screen,
            COLORS['text'],
            (minimap_x, minimap_y, minimap_size, minimap_size),
            2
        )

        # Вычисляем область карты для отображения (вокруг игрока)
        map_view_radius = int(minimap_size / pixel_per_tile / 2)

        for dy in range(-map_view_radius, map_view_radius):
            for dx in range(-map_view_radius, map_view_radius):
                map_x = self.player.x + dx
                map_y = self.player.y + dy

                if not self.game_map.is_valid_position(map_x, map_y):
                    continue

                tile = self.game_map.get_tile(map_x, map_y)

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
                        self.screen,
                        color,
                        (minimap_px, minimap_py, int(pixel_per_tile), int(pixel_per_tile))
                    )

        # Отметка игрока на мини-карте (в центре)
        player_minimap_x = minimap_x + minimap_size // 2
        player_minimap_y = minimap_y + minimap_size // 2

        pygame.draw.circle(
            self.screen,
            COLORS['player'],
            (player_minimap_x, player_minimap_y),
            3
        )

        # Заголовок мини-карты
        minimap_font = pygame.font.Font(None, 16)
        minimap_title = minimap_font.render("Карта", True, COLORS['text'])
        self.screen.blit(minimap_title, (minimap_x + 5, minimap_y - 18))

    def _generate_loot(self, enemy):
        """
        Генерировать лут с поверженного врага

        Args:
            enemy: Поверженный враг

        Returns:
            tuple: (список предметов [(item, quantity)], количество золота)
        """
        from game.inventory import ItemGenerator, ItemQuality, PREDEFINED_ITEMS
        import random

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
                        item = ItemGenerator.generate_armor(item_level, quality)

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

        # Кнопки действий
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

