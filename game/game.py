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
from game.ui import HelpWindow, InventoryWindow, TradeWindow, UIHelper, CharacterWindow
from game.optimization import PerformanceOptimizer, RenderCache
from game.quests import QuestManager, AchievementManager, create_starter_quests
from game.save_system import SaveSystem
from game.skills import PowerStrike, Heal
from game.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE, COLORS,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_BANDIT_CAMP,
    LOCATION_MINE, LOCATION_RUINS
)


class Game:
    """Главный класс игры"""

    def __init__(self):
        """Инициализация игры"""
        # Окно игры в полноэкранном режиме
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
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

        # Система боя
        self.combat_system = None
        self.in_combat = False

        # Система взаимодействия с NPC
        self.interaction_menu_open = False
        self.nearby_npc = None

        # UI компоненты
        self.help_window = HelpWindow(self.screen, self.font, self.info_font)
        self.inventory_window = InventoryWindow(self.screen, self.font, self.info_font)
        self.trade_window = TradeWindow(self.screen, self.font, self.info_font)
        self.character_window = CharacterWindow(self.screen, self.font, self.info_font)

        # Состояния окон
        self.inventory_menu_open = False
        self.trade_menu_open = False
        self.character_menu_open = False

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

        # Даем игроку стартовые навыки
        self.player.skill_manager.learn_skill(PowerStrike)
        self.player.skill_manager.learn_skill(Heal)

        # Перестраиваем spatial grid для NPC
        all_npcs = self.guards + self.merchants + self.bandits + self.miners + self.undead
        self.performance_optimizer.rebuild_spatial_grid(all_npcs)

        print("Игра готова к запуску!")

    def _give_starting_items(self):
        """Дать игроку стартовые предметы"""
        from game.inventory import ItemGenerator, ItemQuality

        # Начальное золото
        self.player.inventory.add_gold(50)

        # Стартовые зелья
        self.player.inventory.add_item(PREDEFINED_ITEMS["minor_health_potion"], 2)
        self.player.inventory.add_item(PREDEFINED_ITEMS["minor_stamina_potion"], 1)

        # Стартовое снаряжение низкого качества (уровень 1)
        # Генерируем простое оружие
        starter_weapon = ItemGenerator.generate_weapon(level=1, quality=ItemQuality.COMMON)
        self.player.inventory.add_item(starter_weapon, 1)
        self.player.inventory.equip_item(starter_weapon.name)

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

    def _spawn_bandits(self):
        """Создание бандитов в лагерях"""
        # Находим все бандитские лагеря на карте
        bandit_camps = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_BANDIT_CAMP]

        for camp in bandit_camps:
            # Создаем 3-5 бандитов возле каждого лагеря
            num_bandits = random.randint(3, 5)

            for i in range(num_bandits):
                # Находим позицию рядом с лагерем
                bandit_pos = self._find_guard_position(camp.x, camp.y)
                if bandit_pos:
                    bx, by = bandit_pos
                    bandit_level = random.randint(4, 12)
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
            # Создаем 2-3 шахтера возле каждой шахты
            num_miners = random.randint(2, 3)

            for i in range(num_miners):
                # Находим позицию рядом с шахтой
                miner_pos = self._find_guard_position(mine.x, mine.y)
                if miner_pos:
                    mx, my = miner_pos
                    miner_level = random.randint(3, 10)
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
            # Создаем 2-4 нежити возле каждых руин
            num_undead = random.randint(2, 4)

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
                continue

            # Если открыто меню торговли, обрабатываем его
            if self.trade_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_trade_input(event.key)
                continue

            # Если открыто окно характеристик, обрабатываем его
            if self.character_menu_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_character_input(event.key)
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
        elif key == pygame.K_t:
            # Работа - сбор ресурсов или получение золота, занимает 1 час
            self.player.work(self.game_map)
            self.advance_time(1)
            print(f"Вы поработали. {self.get_time_string()}")
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
        # Собираем всех NPC
        all_npcs = self.guards + self.merchants + self.bandits

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

        print("Рядом нет NPC для взаимодействия!")

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

        # Получаем лут с локации
        loot = get_random_loot_from_location(location.location_type)

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
            # Снять экипированный предмет (заглушка - нужно добавить выбор слота)
            print("Функция снятия предметов будет доступна в следующей версии")

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

    def _start_combat(self, enemy):
        """
        Начать бой с NPC

        Args:
            enemy: Враг для боя
        """
        print(f"Бой начался с {enemy.name}!")
        self.combat_system = CombatSystem(self.player, enemy, self.screen, self.font)
        self.in_combat = True
        self.nearby_npc = None

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
            self.inventory_window.render(self.player)

        # Если открыто меню торговли, отрисовываем его
        if self.trade_menu_open and self.nearby_npc:
            self.trade_window.render(self.player, self.nearby_npc)

        # Если открыто окно характеристик, отрисовываем его
        if self.character_menu_open:
            self.character_window.render(self.player)

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
                    else:
                        # Применяем оттенок времени суток только к видимым тайлам
                        color = self._apply_time_of_day_tint(color)

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
                    if not guard.is_alive:
                        continue

                    guard_screen_x = (guard.x - self.camera_x) * TILE_SIZE
                    guard_screen_y = (guard.y - self.camera_y) * TILE_SIZE

                    # Цвет зависит от состояния стражника
                    if guard.state == "rest":
                        guard_color = (100, 100, 200)  # Синий оттенок для отдыха
                    elif guard.state == "combat":
                        guard_color = (50, 150, 255)   # Ярко-синий для боя
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

                    # Цвет зависит от состояния нежити
                    if undead_npc.state == "rest":
                        undead_color = (80, 0, 80)  # Темно-фиолетовый для отдыха
                    elif undead_npc.state == "combat":
                        undead_color = (150, 0, 150)  # Ярко-фиолетовый для боя
                    else:
                        undead_color = (100, 0, 100)  # Фиолетовый для патруля

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
        self.screen.blit(time_gold_text, (WINDOW_WIDTH - 350, info_y + 5))

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
            "F1 - Справка | C - Характеристики | I - Инвентарь",
            True,
            (180, 180, 180)
        )
        self.screen.blit(help_hint, (info_x + 900, info_y + 55))

    def _render_minimap(self):
        """Отрисовка мини-карты"""
        # Размеры мини-карты
        minimap_size = 150
        minimap_x = WINDOW_WIDTH - minimap_size - 10
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

    def _render_interaction_menu(self):
        """Отрисовка меню взаимодействия с NPC"""
        # Затемняем фон
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры меню
        menu_width = 500
        menu_height = 300
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (WINDOW_HEIGHT - menu_height) // 2

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
            "[1] Торговля (скоро)",
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

