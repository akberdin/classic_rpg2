"""
Модуль для создания и размещения NPC на карте
"""
import random
from game.npc import Guard, Merchant, MagicMerchant, MagePatrol, Bandit, Miner, Undead, Alchemist, Hunter, Necromancer
from game.inventory import PREDEFINED_ITEMS, ItemGenerator, ItemQuality
from game.constants import (
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_BANDIT_CAMP,
    LOCATION_MINE, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL
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

        Returns:
            dict: Словарь со списками NPC по типам
        """
        npcs = {
            'guards': self.spawn_guards(),
            'merchants': self.spawn_merchants(),
            'mages': self.spawn_mages(),
            'bandits': self.spawn_bandits(),
            'miners': self.spawn_miners(),
            'undead': self.spawn_undead(),
            'alchemists': self.spawn_alchemists(),
            'hunters': self.spawn_hunters(),
            'necromancers': self.spawn_necromancers()
        }

        # Добавляем магического торговца к торговцам
        magic_merchant = self.spawn_magic_merchant()
        if magic_merchant:
            npcs['merchants'].append(magic_merchant)

        return npcs

    def spawn_guards(self):
        """
        Создание стражников в городах и деревнях

        Returns:
            list: Список стражников
        """
        guards = []
        # Находим все города на карте
        cities = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_CITY]
        villages = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_VILLAGE]

        # Спавн стражников в городах (8 стражников 3-4 ранга)
        for city in cities:
            num_guards = 8

            for i in range(num_guards):
                guard_pos = self._find_npc_position(city.x, city.y)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников 3-4 ранга (15-40 уровень)
                    guard_level = random.randint(15, 40)
                    guard = Guard(f"Стражник {city.name}", gx, gy, guard_level)

                    patrol_route = self._create_patrol_route(gx, gy, radius=5)
                    guard.set_patrol_route(patrol_route)

                    guards.append(guard)

        # Спавн стражников в деревнях (4 стражника 1-2 ранга)
        for village in villages:
            num_guards = 4

            for i in range(num_guards):
                guard_pos = self._find_npc_position(village.x, village.y)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников 1-2 ранга (1-15 уровень)
                    guard_level = random.randint(1, 15)
                    guard = Guard(f"Стражник {village.name}", gx, gy, guard_level)

                    patrol_route = self._create_patrol_route(gx, gy, radius=4)
                    guard.set_patrol_route(patrol_route)

                    guards.append(guard)

        return guards

    def spawn_merchants(self):
        """
        Создание торговцев, курсирующих между населенными пунктами

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

        # Создаем 10-15 торговцев
        num_merchants = random.randint(10, 15)

        merchant_names = [
            "Торговец Иван", "Купец Петр", "Торговка Мария",
            "Купец Василий", "Торговец Николай", "Купчиха Анна",
            "Странствующий торговец", "Заезжий купец"
        ]

        for i in range(num_merchants):
            # Выбираем случайный стартовый населенный пункт
            start_settlement = random.choice(settlements)

            # Находим позицию рядом с населенным пунктом
            merchant_pos = self._find_npc_position(start_settlement.x, start_settlement.y)

            if merchant_pos:
                mx, my = merchant_pos
                # Уровень торговцев от 2 до 8
                merchant_level = random.randint(2, 8)
                merchant_name = random.choice(merchant_names)

                merchant = Merchant(merchant_name, mx, my, merchant_level)
                merchant.set_settlements(settlements)

                merchants.append(merchant)

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

    def spawn_mages(self):
        """
        Создание магов-патрульных в академии магии

        Returns:
            list: Список магов
        """
        mages = []
        # Находим академию магии
        magic_school = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_MAGIC_SCHOOL:
                magic_school = loc
                break

        if not magic_school:
            return mages

        # Создаем 3-5 магов-патрульных возле академии
        num_mages = random.randint(3, 5)

        mage_names = [
            "Адепт", "Чародей", "Волшебник", "Маг",
            "Заклинатель", "Колдун", "Ученик мага", "Магистр"
        ]

        for i in range(num_mages):
            # Находим позицию рядом с академией (в пределах 10 клеток)
            mage_pos = None
            for attempt in range(20):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                mx = magic_school.x + offset_x
                my = magic_school.y + offset_y

                if self.game_map.is_valid_position(mx, my):
                    tile = self.game_map.get_tile(mx, my)
                    if tile.is_passable():
                        mage_pos = (mx, my)
                        break

            if mage_pos:
                mx, my = mage_pos
                # Уровень магов от 8 до 20
                mage_level = random.randint(8, 20)
                mage_name = f"{random.choice(mage_names)} {magic_school.name}"

                # Создаем мага с привязкой к академии
                mage = MagePatrol(mage_name, mx, my, mage_level, magic_school.x, magic_school.y)

                mages.append(mage)

        return mages

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
                # Находим позицию рядом с лагерем
                bandit_pos = self._find_npc_position(camp.x, camp.y)
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
        Создание шахтеров в шахтах

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
            # Создаем 5-8 шахтеров возле каждой шахты
            num_miners = random.randint(5, 8)

            for i in range(num_miners):
                # Находим позицию рядом с шахтой
                miner_pos = self._find_npc_position(mine.x, mine.y)
                if miner_pos:
                    mx, my = miner_pos
                    # Уровень шахтеров от 2 до 8
                    miner_level = random.randint(2, 8)
                    miner_name = f"{random.choice(miner_names)} {mine.name}"

                    # Создаем шахтера с привязкой к шахте
                    miner = Miner(miner_name, mx, my, miner_level, mine.x, mine.y)

                    miners.append(miner)

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

    def spawn_hunters(self):
        """
        Создание охотников в лесных и диких областях

        Returns:
            list: Список охотников
        """
        hunters = []

        # Находим деревни как базы для охотников
        villages = [loc for loc in self.game_map.locations
                   if loc.location_type == LOCATION_VILLAGE]

        hunter_names = [
            "Охотник Орион", "Следопыт Артемис", "Рейнджер Робин",
            "Охотник Немрод", "Следопыт Иван", "Ловчий Степан"
        ]

        # Создаем 1-2 охотника возле каждой деревни
        for village in villages:
            if random.random() < 0.5:  # 50% шанс
                num_hunters = random.randint(1, 2)
                for i in range(num_hunters):
                    # Позиция немного дальше от деревни
                    hunter_pos = None
                    for attempt in range(20):
                        offset_x = random.randint(-15, 15)
                        offset_y = random.randint(-15, 15)
                        hx = village.x + offset_x
                        hy = village.y + offset_y

                        if self.game_map.is_valid_position(hx, hy):
                            tile = self.game_map.get_tile(hx, hy)
                            if tile.is_passable():
                                hunter_pos = (hx, hy)
                                break

                    if hunter_pos:
                        hx, hy = hunter_pos
                        hunter_level = random.randint(10, 25)
                        hunter_name = random.choice(hunter_names)

                        hunter = Hunter(hunter_name, hx, hy, hunter_level, village.x, village.y)
                        hunters.append(hunter)
                        print(f"Создан охотник '{hunter_name}' возле {village.name}")

        return hunters

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

    def _find_npc_position(self, center_x, center_y):
        """
        Найти позицию для NPC рядом с центром

        Args:
            center_x: X координата центра
            center_y: Y координата центра

        Returns:
            tuple or None: (x, y) позиция или None
        """
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
        """
        Создать маршрут патрулирования вокруг точки

        Args:
            center_x: X координата центра
            center_y: Y координата центра
            radius: Радиус патрулирования

        Returns:
            list: Список точек маршрута
        """
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


def give_starting_items(player):
    """
    Дать игроку стартовые предметы

    Args:
        player: Игрок
    """
    # Начальное золото
    player.inventory.add_gold(50)

    # Стартовые зелья
    player.inventory.add_item(PREDEFINED_ITEMS["minor_health_potion"], 2)
    player.inventory.add_item(PREDEFINED_ITEMS["minor_stamina_potion"], 1)

    # Стартовое оружие - топор для рубки леса
    starter_axe = PREDEFINED_ITEMS["basic_axe"]
    player.inventory.add_item(starter_axe, 1)
    player.inventory.equip_item(starter_axe.name)

    # Генерируем простой доспех для торса
    starter_chest = ItemGenerator.generate_armor(level=1, quality=ItemQuality.COMMON)
    player.inventory.add_item(starter_chest, 1)
    if starter_chest.slot.value == "chest":
        player.inventory.equip_item(starter_chest.name)

    # Обновляем производные характеристики после экипировки
    player.update_derived_stats()
