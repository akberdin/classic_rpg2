"""
Модуль для создания и размещения NPC на карте
"""
import random
from game.npc import Guard, Merchant, MagicMerchant, WarriorMerchant, ShadowMerchant, MagePatrol, Bandit, Miner, Undead, ShadowAdept, Alchemist, Hunter, Necromancer, Wolf, Bear, Deer
from game.inventory import ItemGenerator, ItemQuality
from game.item_registry import get_item
from game.constants import (
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_BANDIT_CAMP,
    LOCATION_MINE, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, LOCATION_SECRET_CAMP, BIOME_FOREST
)


class NPCSpawner:
    """Класс для создания и размещения NPC на карте"""

    def __init__(self, game_map):
        """
        Инициализация спавнера NPC

        Args:
            game_map: Игровая карта
        """
        self.game_map = game_map

    def spawn_all_npcs(self):
        """
        Создать всех NPC на карте

        ВРЕМЕННО ОТКЛЮЧЕНЫ:
        - merchants (торговцы)

        Returns:
            dict: Словарь со списками NPC по типам
        """
        npcs = {
            'guards': self.spawn_guards(),  # Система спавна стражи на основе конфигурации guards
            'merchants': [],  # Временно отключено
            'bandits': self.spawn_bandits(),
            'miners': self.spawn_miners(),
            'undead': self.spawn_undead(),
            'alchemists': self.spawn_alchemists(),
            'necromancers': self.spawn_necromancers(),
            'animals': self.spawn_animals()
        }

        # УСТАРЕВШИЕ методы spawn_mages(), spawn_shadow_adepts(), spawn_hunters() удалены
        # Эти типы NPC (warrior, mage, shadow_adept, hunter) теперь создаются
        # только через систему guards из конфигурации map1_config.json

        # Временно отключаем всех торговцев
        # magic_merchant = self.spawn_magic_merchant()
        # if magic_merchant:
        #     npcs['merchants'].append(magic_merchant)

        # warrior_merchant = self.spawn_warrior_merchant()
        # if warrior_merchant:
        #     npcs['merchants'].append(warrior_merchant)

        # shadow_merchant = self.spawn_shadow_merchant()
        # if shadow_merchant:
        #     npcs['merchants'].append(shadow_merchant)

        print("ВНИМАНИЕ: Спавн торговцев временно отключен")
        return npcs

    def spawn_guards(self):
        """
        Создание стражников на основе конфигурации locations.

        Для каждой локации с параметром guards создаются NPC разных типов и рангов.
        Параметры guards определяют:
        - type: тип стражи (warrior, mage, shadow_adept, hunter)
        - rank: ранг (1-4), определяет уровень
        - count: количество стражей данного типа
        - patrol_radius: радиус патрулирования
        - respawn_time: время респавна при смерти

        Returns:
            list: Список стражников всех типов
        """
        guards = []

        # Находим все локации с параметром guards
        locations_with_guards = [
            loc for loc in self.game_map.locations
            if hasattr(loc, 'guards') and loc.guards
        ]

        for location in locations_with_guards:
            spawn_radius = getattr(location, 'spawn_radius', 5)
            location_name = getattr(location, 'name', 'Неизвестно')

            # Обрабатываем каждую запись в массиве guards
            for guard_config in location.guards:
                guard_type = guard_config.get('type', 'warrior')
                rank = guard_config.get('rank', 1)
                count = guard_config.get('count', 1)
                patrol_radius = guard_config.get('patrol_radius', 5)
                respawn_time = guard_config.get('respawn_time', 0)

                # Определяем диапазон уровней по рангу
                # Ранг 1: 1-10, Ранг 2: 11-20, Ранг 3: 21-30, Ранг 4: 31-40
                level_min = (rank - 1) * 10 + 1
                level_max = rank * 10

                # Создаем count стражей данного типа и ранга
                for i in range(count):
                    # Находим позицию в радиусе spawn_radius от локации
                    guard_pos = None
                    for attempt in range(30):
                        offset_x = random.randint(-spawn_radius, spawn_radius)
                        offset_y = random.randint(-spawn_radius, spawn_radius)
                        gx = location.x + offset_x
                        gy = location.y + offset_y

                        if self.game_map.is_valid_position(gx, gy):
                            tile = self.game_map.get_tile(gx, gy)
                            if tile.is_passable():
                                # Проверяем, нет ли уже NPC на этой позиции
                                occupied = False
                                for existing_guard in guards:
                                    if existing_guard.x == gx and existing_guard.y == gy:
                                        occupied = True
                                        break

                                if not occupied:
                                    guard_pos = (gx, gy)
                                    break

                    if guard_pos:
                        gx, gy = guard_pos
                        guard_level = random.randint(level_min, level_max)

                        # Создаем стражника в зависимости от типа
                        guard = self._create_guard_by_type(
                            guard_type, location_name, gx, gy, guard_level,
                            location.x, location.y, patrol_radius, respawn_time
                        )

                        if guard:
                            guards.append(guard)

        if guards:
            print(f"Создано стражей: {len(guards)} на основе конфигурации")

        return guards

    def _create_guard_by_type(self, guard_type, location_name, x, y, level, home_x, home_y, patrol_radius, respawn_time):
        """
        Создать стражника заданного типа

        Args:
            guard_type: тип стражи (warrior, mage, shadow_adept, hunter)
            location_name: название локации
            x, y: координаты спавна
            level: уровень стражи
            home_x, home_y: координаты домашней точки (центр локации)
            patrol_radius: радиус патрулирования
            respawn_time: время респавна

        Returns:
            NPC объект стражи или None
        """
        guard_names = {
            'warrior': ['Стражник', 'Воин', 'Защитник', 'Страж'],
            'mage': ['Маг', 'Чародей', 'Волшебник', 'Адепт'],
            'shadow_adept': ['Адепт Тени', 'Теневой Страж', 'Ночной Дозор'],
            'hunter': ['Охотник', 'Следопыт', 'Рейнджер', 'Ловчий']
        }

        # Выбираем имя
        name_prefix = random.choice(guard_names.get(guard_type, ['Стражник']))
        guard_name = f"{name_prefix} {location_name}"

        guard = None

        if guard_type == 'warrior':
            # Используем класс Guard для воинов
            guard = Guard(guard_name, x, y, level)
            # Устанавливаем маршрут патрулирования
            patrol_route = self._create_patrol_route(x, y, radius=patrol_radius)
            guard.set_patrol_route(patrol_route)

        elif guard_type == 'mage':
            # Используем класс MagePatrol для магов
            guard = MagePatrol(guard_name, x, y, level, home_x, home_y)
            # У магов свой встроенный механизм патрулирования на основе academy_x/y
            guard.max_distance_from_academy = patrol_radius

        elif guard_type == 'shadow_adept':
            # Используем класс ShadowAdept для адептов тени
            guard = ShadowAdept(guard_name, x, y, level, home_x, home_y)
            # У адептов тени свой встроенный механизм патрулирования
            if hasattr(guard, 'max_distance_from_camp'):
                guard.max_distance_from_camp = patrol_radius

        elif guard_type == 'hunter':
            # Используем класс Hunter для охотников
            guard = Hunter(guard_name, x, y, level, home_x, home_y)
            # У охотников свой встроенный механизм патрулирования
            if hasattr(guard, 'max_distance_from_home'):
                guard.max_distance_from_home = patrol_radius

        # Сохраняем параметры респавна для всех типов стражей
        if guard:
            guard.respawn_time = respawn_time
            guard.spawn_location_x = home_x
            guard.spawn_location_y = home_y
            guard.spawn_radius = patrol_radius

        return guard

    def spawn_merchants(self):
        """
        Создание торговцев, курсирующих между населенными пунктами
        Распределение по рангам: 15-1 ранга, 10-2 ранга, 5-3 ранга, 3-4 ранга

        Returns:
            list: Список торговцев
        """
        merchants = []
        # Находим все города и деревни на карте
        settlements = [loc for loc in self.game_map.locations
                      if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        if len(settlements) < 2:
            # Нужно как минимум 2 населенных пункта для торговцев
            return merchants

        # Имена торговцев с приставками по рангу
        merchant_names_rank1 = [
            "Торговец Иван", "Купец Петр", "Торговка Мария",
            "Торговец Николай", "Купчиха Анна", "Странствующий торговец"
        ]
        merchant_names_rank2 = [
            "Купец Василий", "Торговка Елена", "Купчиха Ольга",
            "Опытный торговец", "Купец Дмитрий", "Торговец Сергей"
        ]
        merchant_names_rank3 = [
            "Богатый купец Михаил", "Именитая купчиха Екатерина",
            "Зажиточный торговец", "Купец Александр", "Торговка Наталья"
        ]
        merchant_names_rank4 = [
            "Главный купец", "Торговый магнат", "Знатный купец Борис"
        ]

        # Создаем торговцев по рангам
        # Ранг 1: 15 торговцев (уровень 1-10)
        for i in range(15):
            start_settlement = random.choice(settlements)
            merchant_pos = self._find_npc_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                merchant_level = random.randint(1, 10)
                merchant_name = random.choice(merchant_names_rank1)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)
                merchants.append(merchant)

        # Ранг 2: 10 торговцев (уровень 11-20)
        for i in range(10):
            start_settlement = random.choice(settlements)
            merchant_pos = self._find_npc_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                merchant_level = random.randint(11, 20)
                merchant_name = random.choice(merchant_names_rank2)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)
                merchants.append(merchant)

        # Ранг 3: 5 торговцев (уровень 21-30)
        for i in range(5):
            start_settlement = random.choice(settlements)
            merchant_pos = self._find_npc_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                merchant_level = random.randint(21, 30)
                merchant_name = random.choice(merchant_names_rank3)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)
                merchants.append(merchant)

        # Ранг 4: 3 торговца (уровень 31-40)
        for i in range(3):
            start_settlement = random.choice(settlements)
            merchant_pos = self._find_npc_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                merchant_level = random.randint(31, 40)
                merchant_name = random.choice(merchant_names_rank4)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)
                merchants.append(merchant)

        print(f"Создано торговцев: {len(merchants)} (15 ранга 1, 10 ранга 2, 5 ранга 3, 3 ранга 4)")
        return merchants

    def spawn_magic_merchant(self):
        """
        Создание магического торговца в академии магии

        Returns:
            MagicMerchant or None: Магический торговец или None
        """
        # Находим академию магии
        magic_school = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_MAGIC_SCHOOL:
                magic_school = loc
                break

        if not magic_school:
            return None

        # Находим позицию рядом с академией
        merchant_pos = self._find_npc_position(magic_school.x, magic_school.y)

        if merchant_pos:
            mx, my = merchant_pos
            merchant_names = [
                "Архимаг Мерлин", "Чародей Гендальф", "Волшебница Моргана",
                "Мудрец Альбус", "Маг Радагаст", "Колдунья Цирцея"
            ]
            merchant_name = random.choice(merchant_names)

            magic_merchant = MagicMerchant(merchant_name, mx, my, level=8)
            print(f"Создан магический торговец '{merchant_name}' в академии магии")
            return magic_merchant

        return None

    def spawn_warrior_merchant(self):
        """
        Создание военного торговца в военной академии

        Returns:
            WarriorMerchant or None: Военный торговец или None
        """
        # Находим военную академию
        warrior_academy = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_WARRIOR_ACADEMY:
                warrior_academy = loc
                break

        if not warrior_academy:
            return None

        # Находим позицию рядом с академией
        merchant_pos = self._find_npc_position(warrior_academy.x, warrior_academy.y)

        if merchant_pos:
            mx, my = merchant_pos
            merchant_names = [
                "Мастер Оружия Артур", "Командир Леонидас", "Наставник Спартак",
                "Генерал Македон", "Воевода Ярослав", "Маршал Дмитрий"
            ]
            merchant_name = random.choice(merchant_names)

            warrior_merchant = WarriorMerchant(merchant_name, mx, my, level=8)
            print(f"Создан военный торговец '{merchant_name}' в военной академии")
            return warrior_merchant

        return None

    def spawn_shadow_merchant(self):
        """
        Создание теневого торговца в Тайном лагере

        Returns:
            ShadowMerchant or None: Теневой торговец или None
        """
        # Находим Тайный лагерь
        secret_camp = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_SECRET_CAMP:
                secret_camp = loc
                break

        if not secret_camp:
            return None

        # Находим позицию рядом с Тайным лагерем
        merchant_pos = self._find_npc_position(secret_camp.x, secret_camp.y)

        if merchant_pos:
            mx, my = merchant_pos
            merchant_names = [
                "Теневой Торговец", "Мастер Клинков", "Торговец Ядами",
                "Посредник Теней", "Темный Коммерсант", "Скрытый Купец"
            ]
            merchant_name = random.choice(merchant_names)

            shadow_merchant = ShadowMerchant(merchant_name, mx, my, level=10)
            print(f"Создан теневой торговец '{merchant_name}' в Тайном лагере")
            return shadow_merchant

        return None



    def spawn_bandits(self):
        """
        Создание бандитов в лагерях с динамическими уровнями

        Returns:
            list: Список бандитов
        """
        bandits = []
        # Находим все бандитские лагеря на карте
        bandit_camps = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_BANDIT_CAMP]

        bandit_names = [
            "Бандит", "Разбойник", "Головорез", "Грабитель",
            "Налетчик", "Лихой человек", "Бандюган", "Воришка"
        ]

        elite_names = [
            "Главарь банды", "Атаман разбойников", "Вожак головорезов"
        ]

        for camp in bandit_camps:
            # Создаем 10-15 бандитов возле каждого лагеря с разными уровнями
            num_bandits = random.randint(10, 15)

            for i in range(num_bandits):
                # Находим позицию в радиусе 10 клеток от лагеря (радиус спавна)
                bandit_pos = None
                for attempt in range(30):  # Увеличиваем попытки для гарантии спавна
                    offset_x = random.randint(-10, 10)  # spawn_radius = 10
                    offset_y = random.randint(-10, 10)
                    bx = camp.x + offset_x
                    by = camp.y + offset_y

                    if self.game_map.is_valid_position(bx, by):
                        tile = self.game_map.get_tile(bx, by)
                        if tile.is_passable():
                            # Проверяем, нет ли уже бандита на этой позиции
                            occupied = False
                            for existing_bandit in bandits:
                                if existing_bandit.x == bx and existing_bandit.y == by:
                                    occupied = True
                                    break

                            if not occupied:
                                bandit_pos = (bx, by)
                                break

                if bandit_pos:
                    bx, by = bandit_pos
                    # Уровни бандитов распределены по рангам:
                    # 40% новички (1-10), 30% обычные (11-20), 20% опытные (21-30), 10% эксперты (31-40)
                    roll = random.random()
                    if roll < 0.4:
                        bandit_level = random.randint(1, 10)  # Новичок
                    elif roll < 0.7:
                        bandit_level = random.randint(11, 20)  # Обычный
                    elif roll < 0.9:
                        bandit_level = random.randint(21, 30)  # Опытный
                    else:
                        bandit_level = random.randint(31, 40)  # Эксперт

                    # Выбираем имя в зависимости от уровня
                    if bandit_level >= 30:
                        bandit_name = f"{random.choice(elite_names)} {camp.name}"
                    else:
                        bandit_name = f"{random.choice(bandit_names)} {camp.name}"

                    # Создаем бандита с привязкой к лагерю
                    bandit = Bandit(bandit_name, bx, by, bandit_level, camp.x, camp.y)

                    bandits.append(bandit)

        return bandits

    def spawn_miners(self):
        """
        Создание шахтеров в шахтах на основе конфигурации

        Параметры для каждой шахты берутся из map1_config.json:
        - miners_count: количество шахтеров
        - rank: ранг шахты (определяет уровень шахтеров)
        - spawn_radius: радиус спавна шахтеров
        - connections: координаты города/деревни для отдыха

        Returns:
            list: Список шахтеров
        """
        miners = []
        # Находим все шахты на карте
        mines = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_MINE]

        miner_names = [
            "Шахтер", "Рудокоп", "Горняк", "Копатель"
        ]

        for mine in mines:
            # Получаем параметры из конфигурации шахты
            # ВАЖНО: если miners_count = 0 в конфиге, то не создаем шахтеров
            num_miners = mine.miners_count if hasattr(mine, 'miners_count') else random.randint(5, 8)
            mine_rank = mine.rank if hasattr(mine, 'rank') else 1
            spawn_radius = mine.spawn_radius if hasattr(mine, 'spawn_radius') else 3

            # Находим город/деревню для отдыха из connections шахты
            rest_location = None
            rest_x = None
            rest_y = None
            rest_location_name = None

            if hasattr(mine, 'connections') and mine.connections:
                # Берем первое подключение из списка connections
                connection_coords = mine.connections[0]
                rest_x, rest_y = connection_coords[0], connection_coords[1]

                # Находим локацию по координатам
                for loc in self.game_map.locations:
                    if loc.x == rest_x and loc.y == rest_y:
                        if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                            rest_location = loc
                            rest_location_name = loc.name
                            break

            # Если не нашли через connections, используем ближайшую деревню/город
            if not rest_location:
                rest_location = self._find_nearest_settlement(mine.x, mine.y)
                if rest_location:
                    rest_x = rest_location.x
                    rest_y = rest_location.y
                    rest_location_name = rest_location.name

            # Определяем уровень шахтеров на основе ранга шахты
            # Ранг 1: уровень 1-10, Ранг 2: 11-20, Ранг 3: 21-30, Ранг 4: 31-40, Ранг 5: 41-50
            level_min = (mine_rank - 1) * 10 + 1
            level_max = mine_rank * 10

            for i in range(num_miners):
                # Находим позицию в радиусе spawn_radius от шахты
                miner_pos = None
                for attempt in range(30):
                    offset_x = random.randint(-spawn_radius, spawn_radius)
                    offset_y = random.randint(-spawn_radius, spawn_radius)
                    mx = mine.x + offset_x
                    my = mine.y + offset_y

                    if self.game_map.is_valid_position(mx, my):
                        tile = self.game_map.get_tile(mx, my)
                        if tile.is_passable():
                            # Проверяем, нет ли уже шахтера на этой позиции
                            occupied = False
                            for existing_miner in miners:
                                if existing_miner.x == mx and existing_miner.y == my:
                                    occupied = True
                                    break

                            if not occupied:
                                miner_pos = (mx, my)
                                break

                if miner_pos:
                    mx, my = miner_pos
                    # Уровень шахтера зависит от ранга шахты
                    miner_level = random.randint(level_min, level_max)
                    miner_name = f"{random.choice(miner_names)} {mine.name}"

                    # Создаем шахтера с новой логикой на основе ходов
                    miner = Miner(
                        name=miner_name,
                        x=mx,
                        y=my,
                        level=miner_level,
                        mine_x=mine.x,
                        mine_y=mine.y,
                        mine_name=mine.name,
                        rest_x=rest_x,
                        rest_y=rest_y,
                        rest_location_name=rest_location_name,
                        spawn_radius=spawn_radius
                    )

                    miners.append(miner)

            print(f"Создано {len([m for m in miners if m.mine_x == mine.x and m.mine_y == mine.y])} шахтеров для {mine.name} (Ранг {mine_rank}, Уровни {level_min}-{level_max}, Отдых: {rest_location_name})")

        return miners

    def spawn_undead(self):
        """
        Создание нежити в руинах с динамическими уровнями

        Returns:
            list: Список нежити
        """
        undead_list = []
        # Находим все руины на карте
        ruins = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_RUINS]

        undead_names = [
            "Зомби", "Скелет", "Мертвец", "Призрак",
            "Нежить", "Упырь", "Костяк", "Тень"
        ]

        elite_names = [
            "Древний лич", "Повелитель мёртвых", "Призрачный страж"
        ]

        for ruin in ruins:
            # Создаем 8-12 нежити возле каждых руин с разными уровнями
            num_undead = random.randint(8, 12)

            for i in range(num_undead):
                # Находим позицию в радиусе 10 клеток от руин (радиус спавна)
                undead_pos = None
                for attempt in range(30):  # Увеличиваем попытки для гарантии спавна
                    offset_x = random.randint(-10, 10)  # spawn_radius = 10
                    offset_y = random.randint(-10, 10)
                    ux = ruin.x + offset_x
                    uy = ruin.y + offset_y

                    if self.game_map.is_valid_position(ux, uy):
                        tile = self.game_map.get_tile(ux, uy)
                        if tile.is_passable():
                            # Проверяем, нет ли уже нежити на этой позиции
                            occupied = False
                            for existing_undead in undead_list:
                                if existing_undead.x == ux and existing_undead.y == uy:
                                    occupied = True
                                    break

                            if not occupied:
                                undead_pos = (ux, uy)
                                break

                if undead_pos:
                    ux, uy = undead_pos
                    # Уровни нежити распределены по рангам:
                    # 40% новички (1-10), 30% обычные (11-20), 20% опытные (21-30), 10% эксперты (31-40)
                    roll = random.random()
                    if roll < 0.4:
                        undead_level = random.randint(1, 10)  # Новичок
                    elif roll < 0.7:
                        undead_level = random.randint(11, 20)  # Обычный
                    elif roll < 0.9:
                        undead_level = random.randint(21, 30)  # Опытный
                    else:
                        undead_level = random.randint(31, 40)  # Эксперт

                    # Выбираем имя в зависимости от уровня
                    if undead_level >= 30:
                        undead_name = f"{random.choice(elite_names)} {ruin.name}"
                    else:
                        undead_name = f"{random.choice(undead_names)} {ruin.name}"

                    # Создаем нежить с привязкой к руинам
                    undead = Undead(undead_name, ux, uy, undead_level, ruin.x, ruin.y)

                    undead_list.append(undead)

        return undead_list

    def spawn_alchemists(self):
        """
        Создание алхимиков в городах и деревнях

        Returns:
            list: Список алхимиков
        """
        alchemists = []
        # Находим все города и крупные деревни
        settlements = [loc for loc in self.game_map.locations
                      if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        alchemist_names = [
            "Алхимик Гермес", "Мудрец Парацельс", "Алхимик Фламель",
            "Знахарь Авиценна", "Зельевар Магнус", "Алхимик Альберт"
        ]

        # Создаем 1-2 алхимика на каждый город
        cities = [loc for loc in settlements if loc.location_type == LOCATION_CITY]
        for city in cities:
            num_alchemists = random.randint(1, 2)
            for i in range(num_alchemists):
                alchemist_pos = self._find_npc_position(city.x, city.y)
                if alchemist_pos:
                    ax, ay = alchemist_pos
                    alchemist_level = random.randint(8, 15)
                    alchemist_name = random.choice(alchemist_names)

                    alchemist = Alchemist(alchemist_name, ax, ay, alchemist_level)
                    alchemists.append(alchemist)
                    print(f"Создан алхимик '{alchemist_name}' в {city.name}")

        return alchemists


    def spawn_necromancers(self):
        """
        Создание некромантов в руинах

        Returns:
            list: Список некромантов
        """
        necromancers = []
        # Находим все руины
        ruins = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_RUINS]

        necromancer_names = [
            "Некромант Мордред", "Темный Маг Лич", "Некромант Кощей",
            "Владыка Нежити", "Мастер Теней", "Черный Колдун"
        ]

        # Создаем 1 некроманта в некоторых руинах (30% шанс)
        for ruin in ruins:
            if random.random() < 0.3:  # 30% шанс
                necro_pos = None
                for attempt in range(20):
                    offset_x = random.randint(-5, 5)
                    offset_y = random.randint(-5, 5)
                    nx = ruin.x + offset_x
                    ny = ruin.y + offset_y

                    if self.game_map.is_valid_position(nx, ny):
                        tile = self.game_map.get_tile(nx, ny)
                        if tile.is_passable():
                            necro_pos = (nx, ny)
                            break

                if necro_pos:
                    nx, ny = necro_pos
                    # Некроманты высокого уровня
                    necro_level = random.randint(20, 35)
                    necro_name = f"{random.choice(necromancer_names)} {ruin.name}"

                    necromancer = Necromancer(necro_name, nx, ny, necro_level, ruin.x, ruin.y)
                    necromancers.append(necromancer)
                    print(f"Создан некромант '{necro_name}' в руинах {ruin.name}")

        return necromancers

    def _find_nearest_settlement(self, x, y):
        """
        Найти ближайший населенный пункт (город или деревню) к заданным координатам

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            Location или None: Ближайший населенный пункт
        """
        settlements = [loc for loc in self.game_map.locations
                      if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

        if not settlements:
            return None

        nearest = None
        nearest_distance = float('inf')

        for settlement in settlements:
            distance = abs(settlement.x - x) + abs(settlement.y - y)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = settlement

        return nearest

    def _find_npc_position(self, center_x, center_y, existing_npcs=None):
        """
        Найти позицию для NPC рядом с центром

        Args:
            center_x: X координата центра
            center_y: Y координата центра
            existing_npcs: Список уже существующих NPC для проверки коллизий

        Returns:
            tuple or None: (x, y) позиция или None
        """
        if existing_npcs is None:
            existing_npcs = []

        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy

                    if self.game_map.is_valid_position(x, y):
                        tile = self.game_map.get_tile(x, y)
                        if tile.is_passable() and not tile.has_location():
                            # Проверяем, нет ли NPC на этой позиции
                            occupied = False
                            for npc in existing_npcs:
                                if npc.x == x and npc.y == y:
                                    occupied = True
                                    break

                            if not occupied:
                                return (x, y)
        return None

    def _create_patrol_route(self, center_x, center_y, radius=5):
        """
        Создать разнообразный маршрут патрулирования вокруг точки
        Каждый маршрут уникален для избежания столпотворения стражников

        Args:
            center_x: X координата центра
            center_y: Y координата центра
            radius: Радиус патрулирования

        Returns:
            list: Список точек маршрута
        """
        # Добавляем рандомизацию для создания уникальных маршрутов
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)

        # Варьируем радиус для каждого стражника
        actual_radius = radius + random.randint(-1, 2)

        # Выбираем тип маршрута случайно
        route_type = random.choice(['square', 'diagonal', 'cross', 'wide'])

        if route_type == 'square':
            # Классический квадратный маршрут с рандомным смещением
            route = [
                (center_x + actual_radius + offset_x, center_y + offset_y),
                (center_x + actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y + offset_y),
                (center_x - actual_radius + offset_x, center_y - actual_radius + offset_y),
                (center_x + offset_x, center_y - actual_radius + offset_y),
                (center_x + actual_radius + offset_x, center_y - actual_radius + offset_y),
            ]
        elif route_type == 'diagonal':
            # Диагональный маршрут
            route = [
                (center_x + actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y - actual_radius + offset_y),
                (center_x + actual_radius + offset_x, center_y - actual_radius + offset_y),
            ]
        elif route_type == 'cross':
            # Крестообразный маршрут
            route = [
                (center_x + actual_radius + offset_x, center_y + offset_y),
                (center_x + offset_x, center_y + offset_y),
                (center_x + offset_x, center_y + actual_radius + offset_y),
                (center_x + offset_x, center_y + offset_y),
                (center_x - actual_radius + offset_x, center_y + offset_y),
                (center_x + offset_x, center_y + offset_y),
                (center_x + offset_x, center_y - actual_radius + offset_y),
                (center_x + offset_x, center_y + offset_y),
            ]
        else:  # 'wide'
            # Широкий маршрут с дополнительными точками
            route = [
                (center_x + actual_radius + offset_x, center_y + offset_y),
                (center_x + actual_radius + offset_x, center_y + actual_radius//2 + offset_y),
                (center_x + actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x + actual_radius//2 + offset_x, center_y + actual_radius + offset_y),
                (center_x + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius//2 + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y + actual_radius + offset_y),
                (center_x - actual_radius + offset_x, center_y + actual_radius//2 + offset_y),
                (center_x - actual_radius + offset_x, center_y + offset_y),
                (center_x - actual_radius + offset_x, center_y - actual_radius//2 + offset_y),
                (center_x - actual_radius + offset_x, center_y - actual_radius + offset_y),
                (center_x - actual_radius//2 + offset_x, center_y - actual_radius + offset_y),
                (center_x + offset_x, center_y - actual_radius + offset_y),
                (center_x + actual_radius//2 + offset_x, center_y - actual_radius + offset_y),
                (center_x + actual_radius + offset_x, center_y - actual_radius + offset_y),
                (center_x + actual_radius + offset_x, center_y - actual_radius//2 + offset_y),
            ]

        return route

    def spawn_animals(self):
        """
        Создание животных NPC на основе конфигурации точек спавна.
        Животные спавнятся только около соответствующих точек спавна:
        - spawn_wolf -> волки
        - spawn_bear -> медведи
        - spawn_deer -> олени

        Параметры из конфигурации:
        - animal_count: количество животных (если 0, то не спавнить)
        - spawn_radius: радиус зоны спавна и патрулирования
        - player_attitude: отношение к игроку (влияет на агрессивность)
        - respawn_time: время респавна животных

        Returns:
            list: Список всех животных (волки, медведи, олени)
        """
        animals = []

        # Распределение по режимам поведения
        PATROL_PERCENT = 100  # 100% патрулируют вокруг точки спавна (не путешествуют)

        # Уровни животных
        level_min, level_max = 1, 15

        # Собираем точки спавна по типам с параметрами из конфигурации
        spawn_points = {
            'wolf': [],
            'bear': [],
            'deer': []
        }

        for loc in self.game_map.locations:
            loc_type = getattr(loc, 'location_type', None) or getattr(loc, 'type', None)

            # Проверяем, что это точка спавна животных
            if loc_type not in ['spawn_wolf', 'spawn_bear', 'spawn_deer']:
                continue

            # Получаем параметры из конфигурации
            animal_count = getattr(loc, 'animal_count', 0)
            spawn_radius = getattr(loc, 'spawn_radius', 8)
            player_attitude = getattr(loc, 'player_attitude', 0)
            respawn_time = getattr(loc, 'respawn_time', 50)
            spawn_id = getattr(loc, 'id', None)

            # Если animal_count = 0, пропускаем эту точку
            if animal_count == 0:
                print(f"Пропуск точки спавна {loc.name} ({loc_type}): animal_count=0")
                continue

            # Определяем тип животного
            if loc_type == 'spawn_wolf':
                animal_type = 'wolf'
            elif loc_type == 'spawn_bear':
                animal_type = 'bear'
            elif loc_type == 'spawn_deer':
                animal_type = 'deer'
            else:
                continue

            # Сохраняем параметры точки спавна
            spawn_points[animal_type].append({
                'x': loc.x,
                'y': loc.y,
                'name': loc.name,
                'animal_count': animal_count,
                'spawn_radius': spawn_radius,
                'player_attitude': player_attitude,
                'respawn_time': respawn_time,
                'spawn_id': spawn_id
            })

        print(f"Найдено активных точек спавна: волки={len(spawn_points['wolf'])}, "
              f"медведи={len(spawn_points['bear'])}, олени={len(spawn_points['deer'])}")

        # Если нет точек спавна, выходим
        total_spawn_points = sum(len(pts) for pts in spawn_points.values())
        if total_spawn_points == 0:
            print("Активные точки спавна животных не найдены на карте!")
            return animals

        # Спавним животных около каждой точки
        for animal_type, spawn_configs in spawn_points.items():
            for spawn_config in spawn_configs:
                spawn_center_x = spawn_config['x']
                spawn_center_y = spawn_config['y']
                spawn_name = spawn_config['name']
                animal_count = spawn_config['animal_count']
                spawn_radius = spawn_config['spawn_radius']
                player_attitude = spawn_config['player_attitude']
                respawn_time = spawn_config['respawn_time']
                spawn_id = spawn_config['spawn_id']

                spawned_at_point = 0
                attempts = 0
                max_attempts = 100

                while spawned_at_point < animal_count and attempts < max_attempts:
                    attempts += 1

                    # Случайная позиция в радиусе от точки спавна
                    offset_x = random.randint(-spawn_radius, spawn_radius)
                    offset_y = random.randint(-spawn_radius, spawn_radius)
                    spawn_x = spawn_center_x + offset_x
                    spawn_y = spawn_center_y + offset_y

                    # Проверяем границы карты
                    if spawn_x < 5 or spawn_x >= self.game_map.width - 5:
                        continue
                    if spawn_y < 5 or spawn_y >= self.game_map.height - 5:
                        continue

                    # Проверяем, что тайл проходим
                    if not self.game_map.is_valid_position(spawn_x, spawn_y):
                        continue

                    tile = self.game_map.get_tile(spawn_x, spawn_y)
                    if not tile or not tile.is_passable():
                        continue

                    # Находим свободную позицию рядом
                    pos = self._find_npc_position(spawn_x, spawn_y, animals)
                    if not pos:
                        continue

                    ax, ay = pos
                    level = random.randint(level_min, level_max)
                    behavior_mode = 'patrol' if random.randint(1, 100) <= PATROL_PERCENT else 'wander'

                    # Создаем животное нужного типа
                    if animal_type == 'wolf':
                        animal = Wolf("Волк", ax, ay, level, spawn_center_x, spawn_center_y, behavior_mode)
                    elif animal_type == 'bear':
                        animal = Bear("Медведь", ax, ay, level, spawn_center_x, spawn_center_y, behavior_mode)
                    else:  # deer
                        animal = Deer("Олень", ax, ay, level, spawn_center_x, spawn_center_y, behavior_mode)

                    # Сохраняем параметры точки спавна для респавна и AI
                    animal.spawn_point_id = spawn_id
                    animal.spawn_point_name = spawn_name
                    animal.spawn_point_respawn_time = respawn_time

                    # Устанавливаем отношение к игроку (это также установит self.relationship)
                    animal.set_spawn_point_attitude(player_attitude)

                    # Устанавливаем patrol_radius и max_distance_from_spawn на основе spawn_radius
                    animal.patrol_radius = spawn_radius
                    animal.max_distance_from_spawn = spawn_radius  # Строго ограничиваем зону

                    animals.append(animal)
                    spawned_at_point += 1

                print(f"  {spawn_name}: создано {spawned_at_point}/{animal_count} животных")

        # Подсчитываем статистику
        wolves = sum(1 for a in animals if isinstance(a, Wolf))
        bears = sum(1 for a in animals if isinstance(a, Bear))
        deers = sum(1 for a in animals if isinstance(a, Deer))
        patrol_animals = sum(1 for a in animals if a.behavior_mode == 'patrol')
        wander_animals = sum(1 for a in animals if a.behavior_mode == 'wander')

        print(f"Создано животных: {len(animals)}")
        print(f"  - Волки: {wolves}, Медведи: {bears}, Олени: {deers}")
        print(f"  - Патрулирование: {patrol_animals}, Путешествие: {wander_animals}")

        return animals


def give_starting_items(player):
    """
    Дать игроку стартовые предметы

    Args:
        player: Игрок
    """
    from game.inventory import ArmorType, EquipmentSlot, WeaponType, WeaponItem

    # Начальное золото
    player.inventory.add_gold(50)

    # Стартовые зелья
    player.inventory.add_item(get_item("minor_health_potion"), 2)
    player.inventory.add_item(get_item("minor_stamina_potion"), 1)

    # Стартовое оружие - только топор плохого качества
    # Генерируем бонусы из конфига для топора плохого качества
    stats_bonus, param_bonus, skill_bonus, base_damage = ItemGenerator.generate_bonuses_from_config(
        "weapon", ItemQuality.POOR, WeaponType.AXE
    )

    # Генерируем название для топора
    weapon_name = ItemGenerator.generate_item_name(
        WeaponType.AXE.rus_name, WeaponType.AXE.rus_name, ItemQuality.POOR
    )

    # Рассчитываем стоимость
    weapon_value = ItemGenerator.calculate_item_value(
        "weapon", ItemQuality.POOR, base_damage, stats_bonus, param_bonus, skill_bonus
    )

    # Создаем топор напрямую
    starter_weapon = WeaponItem(
        weapon_name, WeaponType.AXE, base_damage, weapon_value,
        ItemQuality.POOR, stats_bonus, param_bonus, skill_bonus
    )

    player.inventory.add_item(starter_weapon, 1)
    player.inventory.equip_item(starter_weapon)

    # Легкая плохая нагрудная броня
    starter_chest = ItemGenerator.generate_armor(
        level=1,
        slot=EquipmentSlot.CHEST,
        armor_type=ArmorType.LIGHT,
        quality=ItemQuality.POOR
    )
    player.inventory.add_item(starter_chest, 1)
    player.inventory.equip_item(starter_chest)

    # Легкая плохая обувь
    starter_feet = ItemGenerator.generate_armor(
        level=1,
        slot=EquipmentSlot.FEET,
        armor_type=ArmorType.LIGHT,
        quality=ItemQuality.POOR
    )
    player.inventory.add_item(starter_feet, 1)
    player.inventory.equip_item(starter_feet)

    # Обновляем производные характеристики после экипировки
    player.update_derived_stats()
