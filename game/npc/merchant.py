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

        # Состояние по умолчанию для расписания
        self.default_state = "travel"

        # Торговая система
        self._generate_merchant_goods()

    def _adjust_merchant_stats(self):
        """Модификация статов для торговца - не боец, не маг"""
        # Немного повышаем удачу (торговая жилка, макс +5%)
        self.luck = int(self.luck * 1.05)

        # Снижаем боевые характеристики, но компенсируем силу бонусом +10
        self.strength = max(1, int(self.strength * 0.7)) + 10  # Бонус +10 к силе для переноски товаров
        self.dexterity = max(1, int(self.dexterity * 0.8))

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.8))

        # Обновляем производные статы
        self.update_derived_stats()

    def get_merchant_rank(self):
        """
        Получить ранг торговца на основе уровня

        Returns:
            int: Ранг от 1 до 4
        """
        if self.level <= 10:
            return 1
        elif self.level <= 20:
            return 2
        elif self.level <= 30:
            return 3
        else:
            return 4

    def _get_allowed_weapon_types(self, rank):
        """Получить разрешенные типы оружия для данного ранга"""
        from game.inventory import WeaponType
        if rank == 1:
            # Ранг 1: только кирки, топоры, луки, копья, ножи, дубины
            return [WeaponType.PICKAXE, WeaponType.AXE, WeaponType.BOW, WeaponType.SPEAR, WeaponType.KNIFE, WeaponType.CLUB]
        else:
            # Остальные ранги: любое оружие
            return list(WeaponType)

    def _get_allowed_armor_types(self, rank):
        """Получить разрешенные типы брони для данного ранга"""
        from game.inventory import ArmorType
        if rank == 1:
            # Ранг 1: только легкая и средняя броня
            return [ArmorType.LIGHT, ArmorType.MEDIUM]
        else:
            # Остальные ранги: любая броня
            return list(ArmorType)

    def _get_resources_for_rank(self, rank):
        """Получить список ресурсов для данного ранга"""
        if rank == 1:
            # Ранг 1: дерево, древесный уголь, медная руда, железная руда, части и мясо животных
            return {
                "wood": (3, 8),
                "charcoal": (3, 8),
                "copper_ore": (3, 8),
                "iron_ore": (3, 8),
                "wolf_fang": (1, 3),
                "wolf_hide": (1, 3),
                "bear_fang": (1, 3),
                "bear_hide": (1, 3),
                "bear_meat": (2, 4),
                "deer_hide": (1, 3),
                "deer_meat": (2, 4),
                "poor_fabric": (2, 5),
            }
        elif rank == 2:
            # Ранг 2: медная, железная, серебряная и золотая руды, древесный уголь
            return {
                "copper_ore": (3, 8),
                "iron_ore": (3, 8),
                "silver_ore": (2, 5),
                "gold_ore": (1, 3),
                "charcoal": (3, 8),
                "fabric": (2, 5),
            }
        elif rank in [3, 4]:
            # Ранги 3-4: медные, железные, серебряные и золотые слитки
            return {
                "copper_ingot": (2, 5),
                "iron_ingot": (2, 5),
                "silver_ingot": (1, 3),
                "gold_ingot": (1, 2),
                "fine_fabric": (1, 3),
            }
        return {}

    def _get_recipes_for_rank(self, rank):
        """Получить рецепты для данного ранга с механизмом автоматического определения ранга"""
        from game.inventory import PREDEFINED_ITEMS, ItemQuality

        # Группируем все рецепты по качеству предмета, который они создают
        all_recipe_ids = [key for key in PREDEFINED_ITEMS.keys() if key.startswith("recipe_")]

        rank_recipes = []
        for recipe_id in all_recipe_ids:
            recipe_item = PREDEFINED_ITEMS[recipe_id]
            recipe_quality = recipe_item.quality

            # Определяем ранг рецепта по качеству
            if rank == 1:
                # Ранг 1: только рецепты для POOR качества
                if recipe_quality == ItemQuality.POOR:
                    rank_recipes.append(recipe_id)
            elif rank == 2:
                # Ранг 2: рецепты для POOR и COMMON качества
                if recipe_quality in [ItemQuality.POOR, ItemQuality.COMMON]:
                    rank_recipes.append(recipe_id)
            elif rank == 3:
                # Ранг 3: рецепты для COMMON и UNCOMMON качества
                if recipe_quality in [ItemQuality.COMMON, ItemQuality.UNCOMMON]:
                    rank_recipes.append(recipe_id)
            elif rank == 4:
                # Ранг 4: рецепты для UNCOMMON и RARE качества
                if recipe_quality in [ItemQuality.UNCOMMON, ItemQuality.RARE]:
                    rank_recipes.append(recipe_id)

        return rank_recipes

    def _get_books_for_rank(self, rank):
        """Получить книги умений для данного ранга (только не магические)"""
        from game.inventory import PREDEFINED_ITEMS, ItemQuality

        # Только боевые книги (не магические)
        combat_books = [
            "book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry",
            "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
            "book_backstab", "book_bleeding_cut", "book_shadow_step",
            "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance"
        ]

        allowed_books = []
        for book_id in combat_books:
            if book_id in PREDEFINED_ITEMS:
                book = PREDEFINED_ITEMS[book_id]
                book_quality = book.quality

                # Фильтруем по качеству в зависимости от ранга
                if rank == 1:
                    # Ранг 1: не продают книги
                    pass
                elif rank == 2:
                    # Ранг 2: до необычного качества
                    if book_quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON]:
                        allowed_books.append(book_id)
                elif rank == 3:
                    # Ранг 3: до редкого качества
                    if book_quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE]:
                        allowed_books.append(book_id)
                elif rank == 4:
                    # Ранг 4: до эпического качества
                    if book_quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE, ItemQuality.EPIC]:
                        allowed_books.append(book_id)

        return allowed_books

    def _generate_merchant_goods(self):
        """Генерация начальных товаров торговца с учетом ранга"""
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS, EquipmentSlot

        # Получаем ранг торговца
        rank = self.get_merchant_rank()

        # Увеличиваем инвентарь и золото торговца в зависимости от ранга
        self.inventory.max_slots = 40 + (rank * 10)
        self.inventory.max_weight = 200.0 + (rank * 50)

        # Даем торговцу стартовое золото
        base_gold = 200 + self.level * 50
        self.inventory.gold = int(base_gold * (1 + rank * 0.5) * 3)

        # Генерируем зелья
        if rank == 1:
            # Ранг 1: малые зелья здоровья и выносливости
            self.inventory.add_item(PREDEFINED_ITEMS["minor_health_potion"], random.randint(2, 4))
            self.inventory.add_item(PREDEFINED_ITEMS["minor_stamina_potion"], random.randint(1, 3))
        elif rank == 2:
            # Ранг 2: зелье здоровья, маны, выносливости (не большие)
            self.inventory.add_item(PREDEFINED_ITEMS["minor_health_potion"], random.randint(2, 4))
            self.inventory.add_item(PREDEFINED_ITEMS["health_potion"], random.randint(2, 4))
            self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(2, 3))
            self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(1, 2))
            self.inventory.add_item(PREDEFINED_ITEMS["minor_stamina_potion"], random.randint(2, 3))
            self.inventory.add_item(PREDEFINED_ITEMS["stamina_potion"], random.randint(1, 2))
        elif rank in [3, 4]:
            # Ранги 3-4: зелье здоровья, маны, выносливости (не большие)
            self.inventory.add_item(PREDEFINED_ITEMS["health_potion"], random.randint(2, 4))
            self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(2, 3))
            self.inventory.add_item(PREDEFINED_ITEMS["stamina_potion"], random.randint(2, 3))

        # Генерируем оружие (с ограничениями по типам для ранга 1)
        allowed_weapon_types = self._get_allowed_weapon_types(rank)
        if rank == 1:
            num_weapons = random.randint(2, 4)  # Минимальный объем
        else:
            num_weapons = min(random.randint(5, 8), 10)  # Не более 10

        for _ in range(num_weapons):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            weapon_type = random.choice(allowed_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Генерируем броню (с ограничениями по типам для ранга 1)
        allowed_armor_types = self._get_allowed_armor_types(rank)
        if rank == 1:
            num_armors = random.randint(3, 5)  # Минимальный объем
        else:
            num_armors = min(random.randint(6, 8), 10)  # Не более 10

        for _ in range(num_armors):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            armor_type = random.choice(allowed_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=armor_type, quality=quality)
            self.inventory.add_item(armor, 1)

        # Генерируем пояса и рюкзаки (для ранга 1 - плохого качества, минимальный объем)
        if rank == 1:
            num_belts = random.randint(1, 2)
            num_backpacks = random.randint(1, 2)
        else:
            num_belts = random.randint(1, 2)
            num_backpacks = random.randint(1, 2)

        for _ in range(num_belts):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            belt = ItemGenerator.generate_belt(self.level, quality=quality)
            self.inventory.add_item(belt, 1)

        for _ in range(num_backpacks):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            backpack = ItemGenerator.generate_backpack(self.level, quality=quality)
            self.inventory.add_item(backpack, 1)

        # Генерируем украшения
        if rank == 1:
            num_jewelry = random.randint(1, 3)  # Не более 3
        elif rank in [2, 3, 4]:
            num_jewelry = random.randint(2, 5)  # Не более 5

        for _ in range(num_jewelry):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Генерируем ресурсы
        resources = self._get_resources_for_rank(rank)
        for resource_id, (min_qty, max_qty) in resources.items():
            if resource_id in PREDEFINED_ITEMS:
                quantity = random.randint(min_qty, max_qty)
                self.inventory.add_item(PREDEFINED_ITEMS[resource_id], quantity)

        # Генерируем книги умений (только не магические)
        allowed_books = self._get_books_for_rank(rank)
        if allowed_books:
            if rank == 2:
                num_books = random.randint(0, 1)  # 0-1 книга
            elif rank == 3:
                num_books = random.randint(1, 2)  # 1-2 книги
            elif rank == 4:
                num_books = random.randint(1, 3)  # 1-3 книги
            else:
                num_books = 0

            if num_books > 0:
                selected_books = random.sample(allowed_books, min(num_books, len(allowed_books)))
                for book_id in selected_books:
                    self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Генерируем рецепты
        allowed_recipes = self._get_recipes_for_rank(rank)
        if allowed_recipes:
            if rank == 1:
                num_recipes = random.randint(1, 3)
            elif rank == 2:
                num_recipes = random.randint(2, 4)
            elif rank == 3:
                num_recipes = random.randint(2, 4)
            elif rank == 4:
                num_recipes = random.randint(3, 5)
            else:
                num_recipes = 0

            if num_recipes > 0:
                selected_recipes = random.sample(allowed_recipes, min(num_recipes, len(allowed_recipes)))
                for recipe_id in selected_recipes:
                    self.inventory.add_item(PREDEFINED_ITEMS[recipe_id], 1)

    def restock_goods(self):
        """
        Пополнение товаров торговца с учетом ранга.
        Вызывается при отдыхе в городе (каждые 2 часа).
        Полная ротация товаров происходит раз в 5 дней (120 часов игрового времени).
        """
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS, EquipmentSlot

        # Получаем ранг торговца
        rank = self.get_merchant_rank()

        # Инициализируем счетчик ротации, если его нет
        if not hasattr(self, 'restock_hours'):
            self.restock_hours = 0

        # Увеличиваем счетчик (каждый вызов = 2 часа)
        self.restock_hours += 2

        # Проверяем, нужна ли полная ротация товаров (раз в 5 дней = 120 часов)
        if self.restock_hours >= 120:
            # Полная ротация: очищаем весь инвентарь и генерируем заново
            self.inventory.items.clear()
            self._generate_merchant_goods()
            self.restock_hours = 0
            return

        # Частичное пополнение товаров (между полными ротациями)
        # Добавляем золото
        base_gold = random.randint(50, 150)
        self.inventory.gold += int(base_gold * (1 + rank * 0.3) * 3)

        # Случайно добавляем зелья (с учетом ранга)
        potion_chance = 0.5
        if random.random() < potion_chance:
            if rank == 1:
                potion_types = ["minor_health_potion", "minor_stamina_potion"]
            elif rank == 2:
                potion_types = ["minor_health_potion", "health_potion", "minor_mana_potion", "mana_potion", "minor_stamina_potion", "stamina_potion"]
            else:
                potion_types = ["health_potion", "mana_potion", "stamina_potion"]

            potion_type = random.choice(potion_types)
            quantity = random.randint(1, 2)
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], quantity)

        # Случайно добавляем оружие (с учетом разрешенных типов)
        weapon_chance = 0.3
        if random.random() < weapon_chance:
            allowed_weapon_types = self._get_allowed_weapon_types(rank)
            quality = ItemGenerator.generate_quality_for_shop(rank)
            weapon_type = random.choice(allowed_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Случайно добавляем броню (с учетом разрешенных типов)
        armor_chance = 0.3
        if random.random() < armor_chance:
            allowed_armor_types = self._get_allowed_armor_types(rank)
            quality = ItemGenerator.generate_quality_for_shop(rank)
            armor_type = random.choice(allowed_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=armor_type, quality=quality)
            self.inventory.add_item(armor, 1)

        # Случайно добавляем ресурсы
        resource_chance = 0.4
        if random.random() < resource_chance:
            resources = self._get_resources_for_rank(rank)
            if resources:
                resource_id = random.choice(list(resources.keys()))
                min_qty, max_qty = resources[resource_id]
                quantity = random.randint(min_qty, max_qty)
                self.inventory.add_item(PREDEFINED_ITEMS[resource_id], quantity)

        # Случайно добавляем рецепт
        recipe_chance = 0.2
        if random.random() < recipe_chance:
            allowed_recipes = self._get_recipes_for_rank(rank)
            if allowed_recipes:
                recipe_id = random.choice(allowed_recipes)
                self.inventory.add_item(PREDEFINED_ITEMS[recipe_id], 1)

        # Случайно добавляем книгу (если доступны для ранга)
        book_chance = 0.15
        if random.random() < book_chance:
            allowed_books = self._get_books_for_rank(rank)
            if allowed_books:
                book_id = random.choice(allowed_books)
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

    def set_settlements(self, settlements):
        """
        Установить список населенных пунктов для посещения

        Args:
            settlements: Список локаций (Location объектов)
        """
        self.settlements = settlements
        if settlements and not self.target_location:
            self._choose_new_destination()

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map
        """
        Обновление AI торговца за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
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
            # Делаем 1 шаг за 1 час (избегаем телепортации)
            if self.consume_stamina():
                self._travel_step(game_map)
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
        """Генерация товаров магического торговца Академии магов"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки (больше для дорогих книг)
        self.inventory.gold = (random.randint(2000, 5000) + self.level * 200) * 3

        # Оружие: только жезлы и посохи (до редкого качества), не более 10
        magic_weapon_types = [WeaponType.STAFF, WeaponType.WAND]
        num_weapons = random.randint(5, 10)
        for _ in range(num_weapons):
            # Генерируем качество до RARE включительно
            quality = ItemGenerator.generate_quality_for_shop(merchant_rank=4)
            weapon_type = random.choice(magic_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Броня: только легкая, пояса и рюкзаки (до редкого качества), не более 10
        num_armors = random.randint(4, 8)
        for _ in range(num_armors):
            quality = ItemGenerator.generate_quality_for_shop(merchant_rank=4)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=ArmorType.LIGHT, quality=quality)
            self.inventory.add_item(armor, 1)

        # Пояса и рюкзаки
        for _ in range(random.randint(1, 2)):
            quality = ItemGenerator.generate_quality_for_shop(merchant_rank=4)
            belt = ItemGenerator.generate_belt(self.level, quality=quality)
            self.inventory.add_item(belt, 1)

        for _ in range(random.randint(1, 2)):
            quality = ItemGenerator.generate_quality_for_shop(merchant_rank=4)
            backpack = ItemGenerator.generate_backpack(self.level, quality=quality)
            self.inventory.add_item(backpack, 1)

        # Украшения: не более 5 позиций (до редкого качества)
        num_jewelry = random.randint(2, 5)
        for _ in range(num_jewelry):
            quality = ItemGenerator.generate_quality_for_shop(merchant_rank=4)
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Ресурсы: магические кристаллы, осколки артефактов, древние монеты
        self.inventory.add_item(PREDEFINED_ITEMS["magic_crystal"], random.randint(3, 6))
        self.inventory.add_item(PREDEFINED_ITEMS["artifact_fragment"], random.randint(2, 4))
        self.inventory.add_item(PREDEFINED_ITEMS["ancient_coin"], random.randint(3, 6))

        # Зелья: Большие зелье здоровья, маны и выносливости
        self.inventory.add_item(PREDEFINED_ITEMS["greater_health_potion"], random.randint(3, 6))
        self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(4, 8))
        self.inventory.add_item(PREDEFINED_ITEMS["stamina_potion"], random.randint(3, 6))

        # Книги: только магические умения до эпического качества
        magic_books = [
            # Магические умения поддержки
            "book_heal", "book_regeneration", "book_mage_shield", "book_stamina_recovery",
            # Магические умения атаки
            "book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"
        ]

        # Фильтруем книги по качеству (до RARE включительно, без EPIC)
        for book_id in magic_books:
            if book_id in PREDEFINED_ITEMS:
                book = PREDEFINED_ITEMS[book_id]
                if book.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE]:
                    self.inventory.add_item(book, 1)

        # Рецепты: только рецепты для 4 ранга (UNCOMMON и RARE качества)
        all_recipe_ids = [key for key in PREDEFINED_ITEMS.keys() if key.startswith("recipe_")]
        rank4_recipes = []
        for recipe_id in all_recipe_ids:
            recipe_item = PREDEFINED_ITEMS[recipe_id]
            if recipe_item.quality in [ItemQuality.UNCOMMON, ItemQuality.RARE]:
                rank4_recipes.append(recipe_id)

        # Добавляем 2-4 рецепта 4 ранга
        if rank4_recipes:
            num_recipes = random.randint(2, min(4, len(rank4_recipes)))
            for recipe_id in random.sample(rank4_recipes, num_recipes):
                self.inventory.add_item(PREDEFINED_ITEMS[recipe_id], 1)

    def restock_goods(self):
        """
        Пополнение товаров магического торговца.
        Полная ротация происходит раз в 5 дней (120 часов).
        """
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator, WeaponType, ItemQuality

        # Инициализируем счетчик ротации, если его нет
        if not hasattr(self, 'restock_hours'):
            self.restock_hours = 0

        # Увеличиваем счетчик (каждый вызов = 2 часа)
        self.restock_hours += 2

        # Проверяем, нужна ли полная ротация товаров (раз в 5 дней = 120 часов)
        if self.restock_hours >= 120:
            # Полная ротация: очищаем весь инвентарь и генерируем заново
            self._generate_magic_goods()
            self.restock_hours = 0
            return

        # Частичное пополнение товаров между полными ротациями
        # Добавляем золото
        self.inventory.gold += random.randint(500, 1000) * 3

        # Случайно добавляем магическую книгу
        if random.random() < 0.3:
            magic_books = [
                "book_heal", "book_regeneration", "book_mage_shield", "book_stamina_recovery",
                "book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"
            ]
            # Фильтруем по качеству (до EPIC)
            allowed_books = []
            for book_id in magic_books:
                if book_id in PREDEFINED_ITEMS:
                    book = PREDEFINED_ITEMS[book_id]
                    if book.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE, ItemQuality.EPIC]:
                        allowed_books.append(book_id)

            if allowed_books:
                book_id = random.choice(allowed_books)
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Случайно добавляем зелья
        if random.random() < 0.5:
            potion_type = random.choice(["greater_health_potion", "mana_potion", "stamina_potion"])
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], random.randint(1, 3))

        # Случайно добавляем ресурсы
        if random.random() < 0.3:
            resource_type = random.choice(["magic_crystal", "artifact_fragment", "ancient_coin"])
            self.inventory.add_item(PREDEFINED_ITEMS[resource_type], random.randint(1, 2))

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map
        """Магический торговец не перемещается"""
        # Обновляем расписание
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем энергию стоя на месте
        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 2)
