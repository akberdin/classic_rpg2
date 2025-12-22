"""
Классы торговцев: Merchant и MagicMerchant
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_MERCHANT, NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL,
    RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY
)
from game.item_registry import get_item


class Merchant(NPC):
    """Класс Торговца с AI перемещения по waypoints и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3, merchant_config=None):
        """
        Инициализация Торговца

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
            merchant_config: Конфигурация торговца из map config (опционально)
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MERCHANT, level=level)

        # Модификация статов для торговца: средние характеристики, низкий дух
        self._adjust_merchant_stats()

        # AI параметры
        self.state = "travel"  # travel, rest, flee
        self.stuck_counter = 0  # Счетчик для определения застревания
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз

        # Состояние по умолчанию для расписания
        self.default_state = "travel"

        # Параметры из конфигурации (новая система waypoints)
        self.merchant_id = None  # Уникальный ID торговца
        self.waypoints = []  # Маршрут: [{"x": int, "y": int, "duration": int}, ...]
        self.current_waypoint_index = 0  # Текущая точка маршрута
        self.is_loop = True  # Зациклен ли маршрут
        self.color = (255, 165, 0)  # Цвет отображения (по умолчанию оранжевый)

        # Специализации торговца (категории товаров с качеством 0-N)
        # 0 = не торгует данной категорией
        self.specializations = {
            "jewelry": 1,
            "books": 1,
            "resources": 1,
            "armor": 1,
            "weapons": 1,
            "potions": 1,
            "recipes": 1
        }

        # Параметры респавна и обновления
        self.respawn_time = 48  # Время респавна в глобальных ходах
        self.assortment_update = 120  # Ходов до обновления ассортимента
        self.assortment_update_counter = 0  # Счётчик ходов для обновления
        self.wealth = 1000  # Стартовый капитал торговца

        # Счётчик отдыха в текущей точке (в глобальных ходах)
        self.rest_counter = 0
        self.current_waypoint_duration = 0  # Длительность остановки в текущей точке

        # Система для торговцев без waypoints (используется respawn_manager)
        self.settlements = []
        self.target_location = None
        self.rest_duration = 0

        # Применяем конфигурацию если есть
        if merchant_config:
            self._apply_config(merchant_config)

        # Торговая система - генерируем товары с учётом специализаций
        self._generate_merchant_goods()

    def _apply_config(self, config):
        """
        Применить конфигурацию торговца из map config

        Args:
            config: Словарь с параметрами торговца
        """
        self.merchant_id = config.get('id')
        self.name = config.get('name', self.name)

        # Ранг торговца определяет качество товаров
        rank = config.get('rank', 1)
        # Устанавливаем уровень на основе ранга (ранг 1: 1-10, ранг 2: 11-20, и т.д.)
        self.level = (rank - 1) * 10 + random.randint(1, 10)

        # Waypoints маршрут
        self.waypoints = config.get('waypoints', [])
        if self.waypoints:
            # Начинаем с первой точки
            self.current_waypoint_index = 0
            first_waypoint = self.waypoints[0]
            self.x = first_waypoint.get('x', self.x)
            self.y = first_waypoint.get('y', self.y)
            self.current_waypoint_duration = first_waypoint.get('duration', 20)

        self.is_loop = config.get('is_loop', True)

        # Цвет
        color = config.get('color', [255, 165, 0])
        if isinstance(color, list) and len(color) >= 3:
            self.color = tuple(color[:3])

        # Специализации
        specs = config.get('specializations', {})
        for category, value in specs.items():
            if category in self.specializations:
                self.specializations[category] = value

        # Параметры респавна и обновления
        self.respawn_time = config.get('respawn_time', 48)
        self.assortment_update = config.get('assortment_update', 120)
        self.wealth = config.get('wealth', 1000)

    def set_waypoints(self, waypoints, is_loop=True):
        """
        Установить маршрут движения торговца

        Args:
            waypoints: Список точек [{"x": int, "y": int, "duration": int}, ...]
            is_loop: Зациклить маршрут
        """
        self.waypoints = waypoints
        self.is_loop = is_loop
        self.current_waypoint_index = 0
        if waypoints:
            first_wp = waypoints[0]
            self.current_waypoint_duration = first_wp.get('duration', 20)

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
        from game.inventory import ItemQuality
        from game.item_registry import ItemRegistry
        from game.crafting_system import CraftingSystem

        # Получаем список базовых рецептов (которые даются при открытии крафта)
        crafting_system = CraftingSystem()
        basic_recipe_ids = set(crafting_system.get_basic_recipes())

        # Группируем все рецепты по качеству предмета, который они создают
        all_recipe_ids = ItemRegistry.get_instance().get_items_by_type('recipes')

        rank_recipes = []
        for recipe_id in all_recipe_ids:
            recipe_item = get_item(recipe_id)
            recipe_quality = recipe_item.quality

            # Пропускаем базовые рецепты - они не продаются
            # Получаем ID рецепта из предмета рецепта
            if hasattr(recipe_item, 'recipe_id') and recipe_item.recipe_id in basic_recipe_ids:
                continue

            # Определяем ранг рецепта по качеству
            if rank == 1:
                # Ранг 1: рецепты для POOR и COMMON качества
                if recipe_quality in [ItemQuality.POOR, ItemQuality.COMMON]:
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
        from game.inventory import ItemQuality

        # Только боевые книги (не магические)
        combat_books = [
            "book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry",
            "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
            "book_backstab", "book_bleeding_cut", "book_shadow_step",
            "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance"
        ]

        allowed_books = []
        for book_id in combat_books:
            book = get_item(book_id)
            if book:
                book_quality = book.quality

                # Фильтруем по качеству в зависимости от ранга
                if rank == 1:
                    # Ранг 1: НЕТ книг
                    pass
                elif rank == 2:
                    # Ранг 2: до необычного качества включительно
                    if book_quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON]:
                        allowed_books.append(book_id)
                elif rank == 3:
                    # Ранг 3: ТОЛЬКО редкого качества
                    if book_quality == ItemQuality.RARE:
                        allowed_books.append(book_id)
                elif rank == 4:
                    # Ранг 4: ТОЛЬКО эпического качества
                    if book_quality == ItemQuality.EPIC:
                        allowed_books.append(book_id)

        return allowed_books

    def _generate_merchant_goods(self):
        """Генерация товаров торговца с учетом ранга и специализаций"""
        from game.inventory import ItemGenerator, EquipmentSlot

        # Очищаем старый ассортимент перед генерацией нового
        self.inventory.items.clear()

        # Получаем ранг торговца
        rank = self.get_merchant_rank()

        # Увеличиваем инвентарь торговца в зависимости от ранга
        self.inventory.max_slots = 40 + (rank * 10)
        self.inventory.max_weight = 200.0 + (rank * 50)

        # Используем wealth из конфига или вычисляем по старой формуле
        if self.wealth > 0:
            self.inventory.gold = self.wealth
        else:
            base_gold = 200 + self.level * 50
            self.inventory.gold = int(base_gold * (1 + rank * 0.5) * 3)

        # Генерируем зелья (если специализация > 0)
        if self.can_trade_category("potions"):
            spec_quality = self.get_category_quality("potions")
            if rank == 1:
                self.inventory.add_item(get_item("minor_health_potion"), random.randint(2, 4) * spec_quality)
                self.inventory.add_item(get_item("minor_stamina_potion"), random.randint(1, 3) * spec_quality)
            elif rank == 2:
                self.inventory.add_item(get_item("minor_health_potion"), random.randint(2, 4))
                self.inventory.add_item(get_item("health_potion"), random.randint(2, 4))
                self.inventory.add_item(get_item("minor_mana_potion"), random.randint(2, 3))
                self.inventory.add_item(get_item("mana_potion"), random.randint(1, 2))
                self.inventory.add_item(get_item("minor_stamina_potion"), random.randint(2, 3))
                self.inventory.add_item(get_item("stamina_potion"), random.randint(1, 2))
            elif rank in [3, 4]:
                self.inventory.add_item(get_item("health_potion"), random.randint(2, 4))
                self.inventory.add_item(get_item("mana_potion"), random.randint(2, 3))
                self.inventory.add_item(get_item("stamina_potion"), random.randint(2, 3))

        # Генерируем оружие (если специализация > 0)
        if self.can_trade_category("weapons"):
            spec_quality = self.get_category_quality("weapons")
            allowed_weapon_types = self._get_allowed_weapon_types(rank)
            if rank == 1:
                num_weapons = random.randint(2, 4) * spec_quality
            else:
                num_weapons = min(random.randint(5, 10), 10)

            for _ in range(num_weapons):
                quality = ItemGenerator.generate_quality_for_shop(rank)
                weapon_type = random.choice(allowed_weapon_types)
                weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
                self.inventory.add_item(weapon, 1)

        # Генерируем броню (если специализация > 0)
        if self.can_trade_category("armor"):
            spec_quality = self.get_category_quality("armor")
            allowed_armor_types = self._get_allowed_armor_types(rank)
            if rank == 1:
                num_armors = random.randint(3, 5) * spec_quality
            else:
                num_armors = min(random.randint(6, 10), 10)

            for _ in range(num_armors):
                quality = ItemGenerator.generate_quality_for_shop(rank)
                armor_type = random.choice(allowed_armor_types)
                slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
                armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=armor_type, quality=quality)
                self.inventory.add_item(armor, 1)

            # Пояса и рюкзаки как часть категории armor
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

        # Генерируем украшения (если специализация > 0)
        if self.can_trade_category("jewelry"):
            spec_quality = self.get_category_quality("jewelry")
            if rank == 1:
                num_jewelry = random.randint(1, 3) * spec_quality
            elif rank in [2, 3, 4]:
                num_jewelry = random.randint(2, 5) * spec_quality

            for _ in range(min(num_jewelry, 10)):
                quality = ItemGenerator.generate_quality_for_shop(rank)
                jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
                self.inventory.add_item(jewelry, 1)

        # Генерируем ресурсы (если специализация > 0)
        if self.can_trade_category("resources"):
            spec_quality = self.get_category_quality("resources")
            resources = self._get_resources_for_rank(rank)
            for resource_id, (min_qty, max_qty) in resources.items():
                if get_item(resource_id):
                    quantity = random.randint(min_qty, max_qty) * spec_quality
                    self.inventory.add_item(get_item(resource_id), quantity)

        # Генерируем книги умений (если специализация > 0)
        if self.can_trade_category("books"):
            spec_quality = self.get_category_quality("books")
            allowed_books = self._get_books_for_rank(rank)
            if allowed_books:
                if rank == 1:
                    num_books = 0  # НЕТ книг для ранга 1
                elif rank == 2:
                    num_books = random.randint(1, 3) * spec_quality
                elif rank == 3:
                    num_books = random.randint(1, 2) * spec_quality
                elif rank == 4:
                    num_books = random.randint(1, 3) * spec_quality
                else:
                    num_books = 0

                if num_books > 0:
                    selected_books = random.sample(allowed_books, min(num_books, len(allowed_books)))
                    for book_id in selected_books:
                        self.inventory.add_item(get_item(book_id), 1)

        # Генерируем рецепты (если специализация > 0)
        if self.can_trade_category("recipes"):
            spec_quality = self.get_category_quality("recipes")
            allowed_recipes = self._get_recipes_for_rank(rank)
            if allowed_recipes:
                if rank == 1:
                    num_recipes = random.randint(5, 8) * spec_quality
                elif rank == 2:
                    num_recipes = random.randint(5, 8) * spec_quality
                elif rank == 3:
                    num_recipes = random.randint(10, 15)
                elif rank == 4:
                    num_recipes = random.randint(10, 15)
                else:
                    num_recipes = 0

                if num_recipes > 0:
                    selected_recipes = random.sample(allowed_recipes, min(num_recipes, len(allowed_recipes)))
                    for recipe_id in selected_recipes:
                        self.inventory.add_item(get_item(recipe_id), 1)


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
        """
        Обновление AI торговца за 1 глобальный ход

        Args:
            context_or_map: AIContext или карта игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (0-23)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость (для торговца всегда активный отдых,
        # чтобы не застревать из-за истощения)
        self.recover_stamina(is_active_rest=True)

        # Проверяем обновление ассортимента
        self._check_assortment_update()

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "travel":
            # Делаем 1 шаг за 1 ход (торговец всегда может двигаться)
            self._travel_step(game_map)
        elif self.state == "rest":
            self._rest_at_waypoint()

    def _check_assortment_update(self):
        """Проверить необходимость обновления ассортимента"""
        self.assortment_update_counter += 1
        if self.assortment_update_counter >= self.assortment_update:
            self.assortment_update_counter = 0
            self._generate_merchant_goods()
            print(f"[Торговец] {self.name}: ассортимент обновлён")

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

        # Пытаемся двигаться (торговец всегда может двигаться при побеге)
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
        """Выбрать новую цель для путешествия (для совместимости со старой системой)"""
        # Если есть waypoints, используем новую систему
        if self.waypoints:
            self._advance_to_next_waypoint()
            return

        # Старая система через settlements
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

    def _get_current_waypoint(self):
        """Получить текущую целевую точку маршрута"""
        if not self.waypoints:
            return None
        if self.current_waypoint_index >= len(self.waypoints):
            if self.is_loop:
                self.current_waypoint_index = 0
            else:
                return None
        return self.waypoints[self.current_waypoint_index]

    def _advance_to_next_waypoint(self):
        """Перейти к следующей точке маршрута"""
        if not self.waypoints:
            return

        # Пропускаем waypoints, на которых торговец уже находится
        # (например, если последняя точка совпадает с первой в цикле)
        attempts = 0
        max_attempts = len(self.waypoints)

        while attempts < max_attempts:
            self.current_waypoint_index += 1
            if self.current_waypoint_index >= len(self.waypoints):
                if self.is_loop:
                    self.current_waypoint_index = 0
                else:
                    # Маршрут завершён
                    self.state = "rest"
                    return

            current_wp = self._get_current_waypoint()
            if current_wp:
                target_x = current_wp.get('x', self.x)
                target_y = current_wp.get('y', self.y)

                # Если торговец уже на этой точке, пропускаем её
                if self.x == target_x and self.y == target_y:
                    attempts += 1
                    continue

                # Нашли точку, куда нужно идти
                self.current_waypoint_duration = current_wp.get('duration', 20)
                break

            attempts += 1

        self.rest_counter = 0
        self.stuck_counter = 0

    def _travel_step(self, game_map):
        """
        Один шаг путешествия к текущей точке waypoint

        Returns:
            bool: True если торговец продолжает движение
        """
        # Новая система waypoints
        if self.waypoints:
            current_wp = self._get_current_waypoint()
            if not current_wp:
                return False

            target_x = current_wp.get('x', self.x)
            target_y = current_wp.get('y', self.y)
        else:
            # Старая система через target_location
            if not self.target_location:
                self._choose_new_destination()
                return False

            target_x = self.target_location.x
            target_y = self.target_location.y

        # Проверяем, достигли ли цели (точные координаты waypoint)
        if self.x == target_x and self.y == target_y:
            # Достигли точки, переходим в режим отдыха
            self.state = "rest"
            self.rest_counter = 0
            if self.waypoints:
                current_wp = self._get_current_waypoint()
                self.current_waypoint_duration = current_wp.get('duration', 20) if current_wp else 20
            else:
                self.rest_duration = random.randint(5, 8)
            return False

        # Проверяем, проходима ли целевая точка
        if not game_map.is_valid_position(target_x, target_y):
            # Целевая точка невалидна, пропускаем
            if self.waypoints:
                self._advance_to_next_waypoint()
            return False

        target_tile = game_map.get_tile(target_x, target_y)
        if not target_tile.is_passable():
            # Целевая точка непроходима, пропускаем
            if self.waypoints:
                self._advance_to_next_waypoint()
            return False

        # Используем алгоритм поиска пути для определения следующего шага
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

        # Если BFS не нашёл путь, пробуем двигаться напрямую к цели
        if not moved:
            # Вычисляем прямое направление к цели
            direct_dx = 0
            direct_dy = 0
            if target_x > self.x:
                direct_dx = 1
            elif target_x < self.x:
                direct_dx = -1
            if target_y > self.y:
                direct_dy = 1
            elif target_y < self.y:
                direct_dy = -1

            # Пробуем разные комбинации направлений
            directions_to_try = [
                (direct_dx, direct_dy),  # Диагональ к цели
                (direct_dx, 0),          # Горизонтально к цели
                (0, direct_dy),          # Вертикально к цели
            ]

            for try_dx, try_dy in directions_to_try:
                if try_dx == 0 and try_dy == 0:
                    continue
                if self._can_move(self.x + try_dx, self.y + try_dy, game_map):
                    self.x += try_dx
                    self.y += try_dy
                    moved = True
                    break

        # Проверка застревания
        if not moved or (self.x == old_x and self.y == old_y):
            self.stuck_counter += 1
            if self.stuck_counter > 10:
                # Если застряли надолго, переходим к следующей точке
                if self.waypoints:
                    self._advance_to_next_waypoint()
                else:
                    self._choose_new_destination()
                self.stuck_counter = 0
                return False
        else:
            self.stuck_counter = 0

        return True

    def _rest_at_waypoint(self):
        """Отдых/торговля в текущей точке waypoint"""
        self.rest_counter += 1

        # Используем duration из текущей точки waypoint
        if self.waypoints:
            if self.rest_counter >= self.current_waypoint_duration:
                # Закончили отдых, переходим к следующей точке
                self.state = "travel"
                self.rest_counter = 0
                self._advance_to_next_waypoint()
        else:
            # Система для торговцев без waypoints
            if self.rest_counter >= self.rest_duration:
                self.state = "travel"
                self.rest_counter = 0
                self._choose_new_destination()

    def can_trade_category(self, category):
        """
        Проверить, торгует ли торговец данной категорией товаров

        Args:
            category: Категория (jewelry, books, resources, armor, weapons, potions, recipes)

        Returns:
            bool: True если торговец торгует этой категорией
        """
        return self.specializations.get(category, 0) > 0

    def get_category_quality(self, category):
        """
        Получить качество товаров для категории (влияет на генерацию)

        Args:
            category: Категория товаров

        Returns:
            int: Уровень качества (0 = не торгует, 1+ = качество)
        """
        return self.specializations.get(category, 0)


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
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для магического торговца
        self._generate_magic_goods()

    def _generate_magic_goods(self):
        """Генерация товаров магического торговца Академии магов"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки (больше для дорогих книг)
        self.inventory.gold = (random.randint(2000, 5000) + self.level * 200) * 3

        # Оружие: только жезлы и посохи (необычного и редкого качества), не более 10
        magic_weapon_types = [WeaponType.STAFF, WeaponType.WAND]
        num_weapons = random.randint(5, 10)
        for _ in range(num_weapons):
            # Генерируем качество только UNCOMMON и RARE
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(magic_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Броня: только легкая броня, пояса и рюкзаки (необычного и редкого качества), не более 10
        # Легкая броня (4-8 штук)
        num_light_armors = random.randint(4, 8)
        for _ in range(num_light_armors):
            # Генерируем качество только UNCOMMON и RARE
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=ArmorType.LIGHT, quality=quality)
            self.inventory.add_item(armor, 1)

        # Пояса и рюкзаки (1-2 штуки каждого, качество UNCOMMON и RARE)
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            belt = ItemGenerator.generate_belt(self.level, quality=quality)
            self.inventory.add_item(belt, 1)

        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            backpack = ItemGenerator.generate_backpack(self.level, quality=quality)
            self.inventory.add_item(backpack, 1)

        # Украшения: не более 5 позиций (необычного и редкого качества)
        num_jewelry = random.randint(2, 5)
        for _ in range(num_jewelry):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Ресурсы: магические кристаллы, осколки артефактов, древние монеты
        self.inventory.add_item(get_item("magic_crystal"), random.randint(3, 6))
        self.inventory.add_item(get_item("artifact_fragment"), random.randint(2, 4))
        self.inventory.add_item(get_item("ancient_coin"), random.randint(3, 6))

        # Зелья: Большие зелье здоровья, маны и выносливости
        self.inventory.add_item(get_item("greater_health_potion"), random.randint(3, 6))
        self.inventory.add_item(get_item("mana_potion"), random.randint(4, 8))
        self.inventory.add_item(get_item("stamina_potion"), random.randint(3, 6))

        # Книги: только магические умения всех видов, не менее 5
        magic_books = [
            # Магические умения поддержки
            "book_heal", "book_regeneration", "book_mage_shield", "book_stamina_recovery",
            # Магические умения атаки
            "book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning", "book_fire_arrow"
        ]

        # Добавляем все доступные магические книги (гарантируем минимум 5)
        books_added = 0
        for book_id in magic_books:
            book = get_item(book_id)
            if book:
                if book.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE, ItemQuality.EPIC]:
                    self.inventory.add_item(book, 1)
                    books_added += 1

        # Если меньше 5 книг, добавляем дубликаты
        if books_added < 5:
            available_books = [bid for bid in magic_books if get_item(bid)]
            while books_added < 5 and available_books:
                book_id = random.choice(available_books)
                self.inventory.add_item(get_item(book_id), 1)
                books_added += 1

        # Рецепты: все ранги (POOR, COMMON, UNCOMMON, RARE), не менее 10
        from game.item_registry import ItemRegistry
        all_recipe_ids = ItemRegistry.get_instance().get_items_by_type('recipes')
        all_rank_recipes = []
        for recipe_id in all_recipe_ids:
            recipe_item = get_item(recipe_id)
            # Рецепты всех рангов (POOR, COMMON, UNCOMMON, RARE)
            if recipe_item.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE]:
                all_rank_recipes.append(recipe_id)

        # Добавляем 10-15 рецептов всех рангов
        if all_rank_recipes:
            num_recipes = random.randint(10, min(15, len(all_rank_recipes)))
            for recipe_id in random.sample(all_rank_recipes, num_recipes):
                self.inventory.add_item(get_item(recipe_id), 1)


    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)


class WarriorMerchant(Merchant):
    """Класс Торговца воинскими книгами для военной академии"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами воинского искусства

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для военного торговца
        self._generate_warrior_goods()

    def _generate_warrior_goods(self):
        """Генерация товаров военного торговца Военной академии"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки (больше для дорогих книг)
        self.inventory.gold = (random.randint(2000, 5000) + self.level * 200) * 3

        # Оружие: ближний и дальний бой (необычного и редкого качества), не более 10
        warrior_weapon_types = [
            WeaponType.SWORD, WeaponType.AXE, WeaponType.SPEAR,
            WeaponType.BOW, WeaponType.CLUB, WeaponType.KNIFE
        ]
        num_weapons = random.randint(5, 10)
        for _ in range(num_weapons):
            # Генерируем качество только UNCOMMON и RARE
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(warrior_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Броня: средняя и тяжелая броня (необычного и редкого качества), не более 10
        warrior_armor_types = [ArmorType.MEDIUM, ArmorType.HEAVY]
        num_armors = random.randint(4, 8)
        for _ in range(num_armors):
            # Генерируем качество только UNCOMMON и RARE
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            armor_type = random.choice(warrior_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=armor_type, quality=quality)
            self.inventory.add_item(armor, 1)

        # Пояса и рюкзаки (1-2 штуки каждого, качество UNCOMMON и RARE)
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            belt = ItemGenerator.generate_belt(self.level, quality=quality)
            self.inventory.add_item(belt, 1)

        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            backpack = ItemGenerator.generate_backpack(self.level, quality=quality)
            self.inventory.add_item(backpack, 1)

        # Украшения: не более 5 позиций (необычного и редкого качества)
        num_jewelry = random.randint(2, 5)
        for _ in range(num_jewelry):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Ресурсы: металлы для ковки
        self.inventory.add_item(get_item("iron_ingot"), random.randint(5, 10))
        self.inventory.add_item(get_item("silver_ingot"), random.randint(3, 6))
        self.inventory.add_item(get_item("gold_ingot"), random.randint(2, 4))

        # Зелья: Зелья здоровья и выносливости (не маны)
        self.inventory.add_item(get_item("greater_health_potion"), random.randint(3, 6))
        self.inventory.add_item(get_item("stamina_potion"), random.randint(4, 8))

        # Книги: только воинские умения всех видов, не менее 5
        warrior_books = [
            # Воинские умения ближнего боя
            "book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry",
            "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance",
            # Воинские умения дальнего боя
            "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
            # Воинские умения скрытности
            "book_backstab", "book_bleeding_cut", "book_shadow_step"
        ]

        # Добавляем все доступные воинские книги (гарантируем минимум 5)
        books_added = 0
        for book_id in warrior_books:
            book = get_item(book_id)
            if book:
                if book.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE, ItemQuality.EPIC]:
                    self.inventory.add_item(book, 1)
                    books_added += 1

        # Если меньше 5 книг, добавляем дубликаты
        if books_added < 5:
            available_books = [bid for bid in warrior_books if get_item(bid)]
            while books_added < 5 and available_books:
                book_id = random.choice(available_books)
                self.inventory.add_item(get_item(book_id), 1)
                books_added += 1

        # Рецепты: все ранги (POOR, COMMON, UNCOMMON, RARE), не менее 10
        from game.item_registry import ItemRegistry
        all_recipe_ids = ItemRegistry.get_instance().get_items_by_type('recipes')
        all_rank_recipes = []
        for recipe_id in all_recipe_ids:
            recipe_item = get_item(recipe_id)
            # Рецепты всех рангов (POOR, COMMON, UNCOMMON, RARE)
            if recipe_item.quality in [ItemQuality.POOR, ItemQuality.COMMON, ItemQuality.UNCOMMON, ItemQuality.RARE]:
                all_rank_recipes.append(recipe_id)

        # Добавляем 10-15 рецептов всех рангов
        if all_rank_recipes:
            num_recipes = random.randint(10, min(15, len(all_rank_recipes)))
            for recipe_id in random.sample(all_rank_recipes, num_recipes):
                self.inventory.add_item(get_item(recipe_id), 1)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)


class ShadowMerchant(Merchant):
    """Класс Торговца книгами Тени для Тайного лагеря"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами Тени

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для теневого торговца
        self._generate_shadow_goods()

    def _generate_shadow_goods(self):
        """Генерация товаров теневого торговца Тайного лагеря"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки
        self.inventory.gold = (random.randint(1500, 4000) + self.level * 150) * 3

        # Оружие: ножи, кинжалы (средняя и легкая броня подходит для убийц)
        shadow_weapon_types = [WeaponType.KNIFE, WeaponType.SWORD, WeaponType.BOW]
        num_weapons = random.randint(5, 10)
        for _ in range(num_weapons):
            # Генерируем качество только UNCOMMON и RARE
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(shadow_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Броня: легкая и средняя броня (необычного и редкого качества)
        shadow_armor_types = [ArmorType.LIGHT, ArmorType.MEDIUM]
        num_armors = random.randint(4, 8)
        for _ in range(num_armors):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            armor_type = random.choice(shadow_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(self.level, slot=slot, armor_type=armor_type, quality=quality)
            self.inventory.add_item(armor, 1)

        # Пояса и рюкзаки (1-2 штуки каждого, качество UNCOMMON и RARE)
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            belt = ItemGenerator.generate_belt(self.level, quality=quality)
            self.inventory.add_item(belt, 1)

        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            backpack = ItemGenerator.generate_backpack(self.level, quality=quality)
            self.inventory.add_item(backpack, 1)

        # Украшения: не более 5 позиций (необычного и редкого качества)
        num_jewelry = random.randint(2, 5)
        for _ in range(num_jewelry):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

        # Зелья: Зелья здоровья и выносливости
        self.inventory.add_item(get_item("health_potion"), random.randint(3, 6))
        self.inventory.add_item(get_item("greater_health_potion"), random.randint(2, 4))
        self.inventory.add_item(get_item("stamina_potion"), random.randint(3, 6))

        # Книги: ВСЕ книги вкладки "Тень" (backstab, bleeding_cut, shadow_step)
        shadow_books = [
            "book_backstab",      # Удар в спину
            "book_bleeding_cut",  # Кровоточащий порез
            "book_shadow_step"    # Шаг тени
        ]

        # Добавляем все теневые книги
        for book_id in shadow_books:
            book = get_item(book_id)
            if book:
                self.inventory.add_item(book, 1)

        # Рецепты: не продаёт рецепты (Тайный лагерь специализируется на книгах)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)
