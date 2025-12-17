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
            'shadow_adepts': self.spawn_shadow_adepts(),
            'alchemists': self.spawn_alchemists(),
            'hunters': self.spawn_hunters(),
            'necromancers': self.spawn_necromancers(),
            'animals': self.spawn_animals()
        }

        # Добавляем магического торговца к торговцам
        magic_merchant = self.spawn_magic_merchant()
        if magic_merchant:
            npcs['merchants'].append(magic_merchant)

        # Добавляем воинского торговца к торговцам
        warrior_merchant = self.spawn_warrior_merchant()
        if warrior_merchant:
            npcs['merchants'].append(warrior_merchant)

        # Добавляем теневого торговца к торговцам (Тайный лагерь)
        shadow_merchant = self.spawn_shadow_merchant()
        if shadow_merchant:
            npcs['merchants'].append(shadow_merchant)

        # Добавляем воинов возле Военной академии к стражникам
        warriors = self.spawn_warriors()
        if warriors:
            npcs['guards'].extend(warriors)

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
                guard_pos = self._find_npc_position(city.x, city.y, guards)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников 3-4 ранга (15-40 уровень)
                    guard_level = random.randint(15, 40)
                    guard = Guard(f"Стражник {city.name}", gx, gy, guard_level)

                    # Увеличенный радиус патрулирования для городов
                    patrol_route = self._create_patrol_route(gx, gy, radius=8)
                    guard.set_patrol_route(patrol_route)

                    guards.append(guard)

        # Спавн стражников в деревнях (4 стражника 1-2 ранга)
        for village in villages:
            num_guards = 4

            for i in range(num_guards):
                guard_pos = self._find_npc_position(village.x, village.y, guards)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников 1-2 ранга (1-15 уровень)
                    guard_level = random.randint(1, 15)
                    guard = Guard(f"Стражник {village.name}", gx, gy, guard_level)

                    # Увеличенный радиус патрулирования для деревень
                    patrol_route = self._create_patrol_route(gx, gy, radius=6)
                    guard.set_patrol_route(patrol_route)

                    guards.append(guard)

        return guards

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

    def spawn_shadow_adepts(self):
        """
        Создание Адептов тени в Тайном лагере
        4 ранга: новичок (1-10), обычный (11-20), ветеран (21-30), эксперт (31-40)

        Returns:
            list: Список адептов тени
        """
        shadow_adepts = []

        # Находим Тайный лагерь
        secret_camp = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_SECRET_CAMP:
                secret_camp = loc
                break

        if not secret_camp:
            return shadow_adepts

        # Имена адептов тени по рангам
        adept_names_rank1 = ["Ученик Тени", "Послушник", "Начинающий Убийца"]
        adept_names_rank2 = ["Адепт Тени", "Теневой Агент", "Шпион"]
        adept_names_rank3 = ["Мастер Теней", "Убийца", "Теневой Охотник"]
        adept_names_rank4 = ["Теневой Лорд", "Верховный Убийца", "Владыка Теней"]

        # Ранг 1: 3 адепта (уровень 1-10)
        for i in range(3):
            adept_pos = None
            for attempt in range(30):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                ax = secret_camp.x + offset_x
                ay = secret_camp.y + offset_y

                if self.game_map.is_valid_position(ax, ay):
                    tile = self.game_map.get_tile(ax, ay)
                    if tile.is_passable():
                        occupied = False
                        for existing in shadow_adepts:
                            if existing.x == ax and existing.y == ay:
                                occupied = True
                                break
                        if not occupied:
                            adept_pos = (ax, ay)
                            break

            if adept_pos:
                ax, ay = adept_pos
                adept_level = random.randint(1, 10)
                adept_name = f"{random.choice(adept_names_rank1)} {secret_camp.name}"
                adept = ShadowAdept(adept_name, ax, ay, adept_level, secret_camp.x, secret_camp.y)
                shadow_adepts.append(adept)

        # Ранг 2: 2 адепта (уровень 11-20)
        for i in range(2):
            adept_pos = None
            for attempt in range(30):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                ax = secret_camp.x + offset_x
                ay = secret_camp.y + offset_y

                if self.game_map.is_valid_position(ax, ay):
                    tile = self.game_map.get_tile(ax, ay)
                    if tile.is_passable():
                        occupied = False
                        for existing in shadow_adepts:
                            if existing.x == ax and existing.y == ay:
                                occupied = True
                                break
                        if not occupied:
                            adept_pos = (ax, ay)
                            break

            if adept_pos:
                ax, ay = adept_pos
                adept_level = random.randint(11, 20)
                adept_name = f"{random.choice(adept_names_rank2)} {secret_camp.name}"
                adept = ShadowAdept(adept_name, ax, ay, adept_level, secret_camp.x, secret_camp.y)
                shadow_adepts.append(adept)

        # Ранг 3: 2 адепта (уровень 21-30)
        for i in range(2):
            adept_pos = None
            for attempt in range(30):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                ax = secret_camp.x + offset_x
                ay = secret_camp.y + offset_y

                if self.game_map.is_valid_position(ax, ay):
                    tile = self.game_map.get_tile(ax, ay)
                    if tile.is_passable():
                        occupied = False
                        for existing in shadow_adepts:
                            if existing.x == ax and existing.y == ay:
                                occupied = True
                                break
                        if not occupied:
                            adept_pos = (ax, ay)
                            break

            if adept_pos:
                ax, ay = adept_pos
                adept_level = random.randint(21, 30)
                adept_name = f"{random.choice(adept_names_rank3)} {secret_camp.name}"
                adept = ShadowAdept(adept_name, ax, ay, adept_level, secret_camp.x, secret_camp.y)
                shadow_adepts.append(adept)

        # Ранг 4: 1 адепт (уровень 31-40)
        adept_pos = None
        for attempt in range(30):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            ax = secret_camp.x + offset_x
            ay = secret_camp.y + offset_y

            if self.game_map.is_valid_position(ax, ay):
                tile = self.game_map.get_tile(ax, ay)
                if tile.is_passable():
                    occupied = False
                    for existing in shadow_adepts:
                        if existing.x == ax and existing.y == ay:
                            occupied = True
                            break
                    if not occupied:
                        adept_pos = (ax, ay)
                        break

        if adept_pos:
            ax, ay = adept_pos
            adept_level = random.randint(31, 40)
            adept_name = f"{random.choice(adept_names_rank4)} {secret_camp.name}"
            adept = ShadowAdept(adept_name, ax, ay, adept_level, secret_camp.x, secret_camp.y)
            shadow_adepts.append(adept)

        print(f"Создано Адептов тени: {len(shadow_adepts)} (3 ранга 1, 2 ранга 2, 2 ранга 3, 1 ранга 4)")
        return shadow_adepts

    def spawn_warriors(self):
        """
        Создание воинов возле военной академии
        4 воина 3 ранга (уровень 21-30) и 4 воина 4 ранга (уровень 31-40)

        Returns:
            list: Список воинов
        """
        warriors = []
        # Находим военную академию
        warrior_academy = None
        for loc in self.game_map.locations:
            if loc.location_type == LOCATION_WARRIOR_ACADEMY:
                warrior_academy = loc
                break

        if not warrior_academy:
            return warriors

        warrior_names = [
            "Воин", "Боец", "Ветеран", "Рыцарь",
            "Защитник", "Страж", "Воитель", "Гвардеец"
        ]

        # Создаем 4 воина 3 ранга (уровень 21-30)
        for i in range(4):
            # Находим позицию рядом с академией (в пределах 10 клеток)
            warrior_pos = None
            for attempt in range(20):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                wx = warrior_academy.x + offset_x
                wy = warrior_academy.y + offset_y

                if self.game_map.is_valid_position(wx, wy):
                    tile = self.game_map.get_tile(wx, wy)
                    if tile.is_passable():
                        warrior_pos = (wx, wy)
                        break

            if warrior_pos:
                wx, wy = warrior_pos
                # Уровень воина 3 ранга
                warrior_level = random.randint(21, 30)
                warrior_name = f"{random.choice(warrior_names)} {warrior_academy.name}"

                # Создаем воина (используем класс Guard)
                warrior = Guard(warrior_name, wx, wy, warrior_level)

                # Создаем маршрут патрулирования вокруг академии
                patrol_route = self._create_patrol_route(wx, wy, radius=8)
                warrior.set_patrol_route(patrol_route)

                warriors.append(warrior)

        # Создаем 4 воина 4 ранга (уровень 31-40)
        for i in range(4):
            # Находим позицию рядом с академией (в пределах 10 клеток)
            warrior_pos = None
            for attempt in range(20):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                wx = warrior_academy.x + offset_x
                wy = warrior_academy.y + offset_y

                if self.game_map.is_valid_position(wx, wy):
                    tile = self.game_map.get_tile(wx, wy)
                    if tile.is_passable():
                        warrior_pos = (wx, wy)
                        break

            if warrior_pos:
                wx, wy = warrior_pos
                # Уровень воина 4 ранга
                warrior_level = random.randint(31, 40)
                warrior_name = f"{random.choice(warrior_names)} {warrior_academy.name}"

                # Создаем воина (используем класс Guard)
                warrior = Guard(warrior_name, wx, wy, warrior_level)

                # Создаем маршрут патрулирования вокруг академии
                patrol_route = self._create_patrol_route(wx, wy, radius=8)
                warrior.set_patrol_route(patrol_route)

                warriors.append(warrior)

        return warriors

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
                # Уровень магов от 31 до 40
                mage_level = random.randint(31, 40)
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
        Создание животных NPC только в радиусе 10 клеток от точек спавна.
        Животные спавнятся только около соответствующих точек спавна:
        - spawn_wolf -> волки
        - spawn_bear -> медведи
        - spawn_deer -> олени

        Returns:
            list: Список всех животных (волки, медведи, олени)
        """
        animals = []

        # Количество животных на одну точку спавна
        ANIMALS_PER_SPAWN = 10
        SPAWN_RADIUS = 10

        # Распределение по режимам поведения
        PATROL_PERCENT = 60  # 60% патрулируют вокруг точки спавна

        # Уровни животных
        level_min, level_max = 1, 15

        # Собираем точки спавна по типам
        spawn_points = {
            'wolf': [],
            'bear': [],
            'deer': []
        }

        for loc in self.game_map.locations:
            loc_type = getattr(loc, 'location_type', None) or getattr(loc, 'type', None)
            if loc_type == 'spawn_wolf':
                spawn_points['wolf'].append((loc.x, loc.y))
            elif loc_type == 'spawn_bear':
                spawn_points['bear'].append((loc.x, loc.y))
            elif loc_type == 'spawn_deer':
                spawn_points['deer'].append((loc.x, loc.y))

        print(f"Найдено точек спавна: волки={len(spawn_points['wolf'])}, "
              f"медведи={len(spawn_points['bear'])}, олени={len(spawn_points['deer'])}")

        # Если нет точек спавна, выходим
        total_spawn_points = sum(len(pts) for pts in spawn_points.values())
        if total_spawn_points == 0:
            print("Точки спавна животных не найдены на карте!")
            return animals

        # Спавним животных около каждой точки
        for animal_type, points in spawn_points.items():
            for spawn_center_x, spawn_center_y in points:
                spawned_at_point = 0
                attempts = 0
                max_attempts = 100

                while spawned_at_point < ANIMALS_PER_SPAWN and attempts < max_attempts:
                    attempts += 1

                    # Случайная позиция в радиусе от точки спавна
                    offset_x = random.randint(-SPAWN_RADIUS, SPAWN_RADIUS)
                    offset_y = random.randint(-SPAWN_RADIUS, SPAWN_RADIUS)
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

                    animals.append(animal)
                    spawned_at_point += 1

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
