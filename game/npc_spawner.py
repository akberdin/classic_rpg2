"""
Модуль для создания и размещения NPC на карте
"""
import random
from game.character import Guard, Merchant, MagicMerchant, MagePatrol, Bandit, Miner, Undead
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
            'undead': self.spawn_undead()
        }

        # Добавляем магического торговца к торговцам
        magic_merchant = self.spawn_magic_merchant()
        if magic_merchant:
            npcs['merchants'].append(magic_merchant)

        return npcs

    def spawn_guards(self):
        """
        Создание стражников в городах

        Returns:
            list: Список стражников
        """
        guards = []
        # Находим все города на карте
        cities = [loc for loc in self.game_map.locations if loc.location_type == LOCATION_CITY]

        for city in cities:
            # Создаем 6-10 стражников возле каждого города
            num_guards = random.randint(6, 10)

            for i in range(num_guards):
                # Находим позицию рядом с городом
                guard_pos = self._find_npc_position(city.x, city.y)
                if guard_pos:
                    gx, gy = guard_pos
                    # Уровень стражников от 5 до 20
                    guard_level = random.randint(5, 20)
                    guard = Guard(f"Стражник {city.name}", gx, gy, guard_level)

                    # Создаем маршрут патрулирования вокруг города
                    patrol_route = self._create_patrol_route(gx, gy, radius=5)
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
        Создание бандитов в лагерях

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

        for camp in bandit_camps:
            # Создаем 7-12 бандитов возле каждого лагеря
            num_bandits = random.randint(7, 12)

            for i in range(num_bandits):
                # Находим позицию рядом с лагерем
                bandit_pos = self._find_npc_position(camp.x, camp.y)
                if bandit_pos:
                    bx, by = bandit_pos
                    # Уровень бандитов от 3 до 15
                    bandit_level = random.randint(3, 15)
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
        Создание нежити в руинах

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

        for ruin in ruins:
            # Создаем 5-10 нежити возле каждых руин
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
                    undead_name = f"{random.choice(undead_names)} {ruin.name}"

                    # Создаем нежить с привязкой к руинам
                    undead = Undead(undead_name, ux, uy, undead_level, ruin.x, ruin.y)

                    undead_list.append(undead)

        return undead_list

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
