"""
Классы торговцев: Merchant и MagicMerchant
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_MERCHANT, NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL,
    RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY
)


class Merchant(NPC):
    """Класс Торговца с AI перемещения между городами и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3):
        """
        Инициализация Торговца

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MERCHANT, level=level)

        # Модификация статов для торговца: средние характеристики, низкий дух
        self._adjust_merchant_stats()

        # AI параметры
        self.state = "travel"  # travel, rest, flee
        self.target_location = None  # Целевая локация (город/деревня)
        self.rest_counter = 0
        self.rest_duration = random.randint(5, 8)  # Отдых 5-8 часов в городе
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)
        self.settlements = []  # Список всех населенных пунктов
        self.stuck_counter = 0  # Счетчик для определения застревания
        self.last_position = (x, y)
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз

        # Торговая система
        self._generate_merchant_goods()

    def _adjust_merchant_stats(self):
        """Модификация статов для торговца - не боец, не маг"""
        # Немного повышаем удачу (торговая жилка)
        self.luck = int(self.luck * 1.3)

        # Снижаем боевые характеристики
        self.strength = max(1, int(self.strength * 0.7))
        self.dexterity = max(1, int(self.dexterity * 0.8))

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.8))

        # Обновляем производные статы
        self.update_derived_stats()

    def _generate_merchant_goods(self):
        """Генерация начальных товаров торговца"""
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS

        # Увеличиваем инвентарь торговца
        self.inventory.max_slots = 30
        self.inventory.max_weight = 200.0

        # Даем торговцу стартовое золото
        self.inventory.gold = random.randint(200, 500) + self.level * 50

        # Генерируем зелья (5-10 разных видов)
        potion_types = [
            "minor_health_potion", "health_potion", "greater_health_potion",
            "minor_mana_potion", "mana_potion",
            "minor_stamina_potion", "stamina_potion"
        ]
        for potion_type in random.sample(potion_types, random.randint(4, 6)):
            quantity = random.randint(2, 5)
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], quantity)

        # Всегда добавляем инструменты (кирки и топоры)
        self.inventory.add_item(PREDEFINED_ITEMS["basic_pickaxe"], random.randint(1, 3))
        self.inventory.add_item(PREDEFINED_ITEMS["basic_axe"], random.randint(1, 3))

        # Генерируем оружие (2-4 штуки) с ограничением качества для магазина
        for _ in range(random.randint(2, 4)):
            quality = ItemGenerator.generate_quality_for_shop()
            weapon = ItemGenerator.generate_weapon(self.level, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Генерируем доспехи (3-6 штук) с ограничением качества для магазина
        for _ in range(random.randint(3, 6)):
            quality = ItemGenerator.generate_quality_for_shop()
            armor = ItemGenerator.generate_armor(self.level, quality=quality)
            self.inventory.add_item(armor, 1)

        # Генерируем украшения (1-3 штуки) с ограничением качества для магазина
        for _ in range(random.randint(1, 3)):
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Генерируем ресурсы (2-4 вида)
        resource_types = ["copper_ore", "iron_ore", "silver_ore", "ancient_coin", "artifact_fragment"]
        for resource_type in random.sample(resource_types, random.randint(2, 4)):
            quantity = random.randint(3, 10)
            self.inventory.add_item(PREDEFINED_ITEMS[resource_type], quantity)

    def restock_goods(self):
        """Пополнение товаров торговца (вызывается при отдыхе в городе)"""
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS

        # Добавляем золото
        self.inventory.gold += random.randint(50, 150)

        # Добавляем случайные новые товары
        if random.random() < 0.7:  # 70% шанс добавить зелье
            potion_types = [
                "minor_health_potion", "health_potion",
                "minor_mana_potion", "mana_potion",
                "minor_stamina_potion"
            ]
            potion_type = random.choice(potion_types)
            quantity = random.randint(1, 3)
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], quantity)

        # Пополняем инструменты если их мало (кирки и топоры)
        if random.random() < 0.6:  # 60% шанс пополнить инструменты
            self.inventory.add_item(PREDEFINED_ITEMS["basic_pickaxe"], 1)
            self.inventory.add_item(PREDEFINED_ITEMS["basic_axe"], 1)

        if random.random() < 0.5:  # 50% шанс добавить оружие
            quality = ItemGenerator.generate_quality_for_shop()
            weapon = ItemGenerator.generate_weapon(self.level, quality=quality)
            self.inventory.add_item(weapon, 1)

        if random.random() < 0.5:  # 50% шанс добавить доспех
            quality = ItemGenerator.generate_quality_for_shop()
            armor = ItemGenerator.generate_armor(self.level, quality=quality)
            self.inventory.add_item(armor, 1)

        if random.random() < 0.3:  # 30% шанс добавить украшение
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
            self.inventory.add_item(jewelry, 1)

    def set_settlements(self, settlements):
        """
        Установить список населенных пунктов для посещения

        Args:
            settlements: Список локаций (Location объектов)
        """
        self.settlements = settlements
        if settlements and not self.target_location:
            self._choose_new_destination()

    def update_ai(self, game_map, all_npcs=None):
        """
        Обновление AI торговца за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения угроз
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "travel":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                if not self._travel_step(game_map):
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_threats(self, all_npcs):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшую угрозу
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Если есть угроза, убегаем
        if closest_threat:
            self.threat = closest_threat
            self.state = "flee"
        elif self.state == "flee":
            # Если угрозы больше нет, возвращаемся к путешествию
            self.threat = None
            self.state = "travel"

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к путешествию
        if not self.threat or not self.threat.is_alive:
            self.threat = None
            self.state = "travel"
            return

        # Убегаем в противоположную от угрозы сторону
        dx_away = self.x - self.threat.x
        dy_away = self.y - self.threat.y

        # Нормализуем направление
        if dx_away > 0:
            dx = 1
        elif dx_away < 0:
            dx = -1
        else:
            dx = 0

        if dy_away > 0:
            dy = 1
        elif dy_away < 0:
            dy = -1
        else:
            dy = 0

        # Если оба направления 0, выбираем случайное
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        # Пытаемся двигаться
        if self.consume_stamina():
            new_x = self.x + dx
            new_y = self.y + dy

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
            else:
                # Если не можем идти прямо, пробуем другие направления
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                random.shuffle(directions)
                for alt_dx, alt_dy in directions:
                    new_x = self.x + alt_dx
                    new_y = self.y + alt_dy
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        break

    def _choose_new_destination(self):
        """Выбрать новую цель для путешествия"""
        if not self.settlements:
            return

        # Исключаем текущую позицию из выбора
        available = [s for s in self.settlements
                    if abs(s.x - self.x) > 5 or abs(s.y - self.y) > 5]

        if available:
            self.target_location = random.choice(available)
        elif self.settlements:
            self.target_location = random.choice(self.settlements)

        self.stuck_counter = 0

    def _travel_step(self, game_map):
        """
        Один шаг путешествия к цели

        Returns:
            bool: True если торговец продолжает движение
        """
        if not self.target_location:
            self._choose_new_destination()
            return False

        target_x = self.target_location.x
        target_y = self.target_location.y

        # Проверяем, достигли ли цели (в пределах 2 клеток)
        distance = abs(self.x - target_x) + abs(self.y - target_y)
        if distance <= 2:
            # Достигли города, переходим в режим отдыха/торговли
            self.state = "rest"
            self.rest_counter = 0
            self.rest_duration = random.randint(5, 8)
            return False

        # Используем алгоритм поиска пути для определения следующего шага
        # Торговцы ищут путь на большие расстояния
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=100)

        # Сохраняем текущую позицию для проверки застревания
        old_x, old_y = self.x, self.y

        # Пытаемся двигаться
        moved = False
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy
                moved = True

        # Проверка застревания
        if not moved or (self.x == old_x and self.y == old_y):
            self.stuck_counter += 1
            if self.stuck_counter > 20:
                # Если застряли, выбираем новую цель
                self._choose_new_destination()
                self.stuck_counter = 0
                return False
        else:
            self.stuck_counter = 0

        return True

    def _rest(self):
        """Отдых/торговля в городе"""
        self.rest_counter += 1

        # Пополняем товары каждые 2 часа отдыха
        if self.rest_counter % 2 == 0:
            self.restock_goods()

        if self.rest_counter >= self.rest_duration:
            # Закончили отдых, выбираем новый город
            self.state = "travel"
            self._choose_new_destination()

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли торговец двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class MagicMerchant(Merchant):
    """Класс Торговца магическими книгами для академии магии"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами магии

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Торговец магией не путешествует
        self.state = "rest"
        self.settlements = []
        # Перегенерируем товары для магического торговца
        self._generate_magic_goods()

    def _generate_magic_goods(self):
        """Генерация товаров магического торговца (только книги и магические предметы)"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки (больше для дорогих книг)
        self.inventory.gold = random.randint(2000, 5000) + self.level * 200

        # Книги магических умений (всегда в наличии)
        magic_books = ["book_heal", "book_regeneration"]
        for book_id in magic_books:
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Книги боевых умений (1-2 случайных)
        combat_books = ["book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry"]
        for book_id in random.sample(combat_books, random.randint(1, 2)):
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Книги атакующей магии (очень дорогие, всегда в наличии)
        attack_magic_books = ["book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"]
        for book_id in attack_magic_books:
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Зелья маны (много)
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(5, 10))
        self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(3, 6))

        # Магические кристаллы
        self.inventory.add_item(PREDEFINED_ITEMS["magic_crystal"], random.randint(2, 5))

        # Магические украшения (1-3 штуки) с ограничением качества для магазина
        for _ in range(random.randint(1, 3)):
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

    def restock_goods(self):
        """Пополнение товаров магического торговца"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Добавляем золото (больше для скупки дорогих предметов)
        self.inventory.gold += random.randint(500, 1000)

        # 50% шанс добавить книгу обычного умения
        if random.random() < 0.5:
            all_books = ["book_heal", "book_regeneration", "book_power_strike",
                        "book_poison_strike", "book_stun_strike", "book_battle_cry"]
            book_id = random.choice(all_books)
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # 30% шанс добавить книгу атакующей магии (дорогую)
        if random.random() < 0.3:
            attack_books = ["book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"]
            book_id = random.choice(attack_books)
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Всегда добавляем зелья маны
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(2, 4))

        # 40% шанс добавить украшение с ограничением качества для магазина
        if random.random() < 0.4:
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

    def update_ai(self, game_map, all_npcs=None):
        """Магический торговец не перемещается"""
        # Восстанавливаем энергию стоя на месте
        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 2)
