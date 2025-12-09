"""
Система генерации и обработки лута.

Извлечено из engine.py для уменьшения сложности.
"""
import json
import os
import random
from game.inventory import ItemGenerator, PREDEFINED_ITEMS
from game.item_registry import get_item, has_item


class LootSystem:
    """Система генерации лута с врагов"""

    # Кэш конфигурации лута
    _config_cache = None

    @classmethod
    def _load_config(cls):
        """Загрузить конфигурацию лута (ленивая загрузка)."""
        if cls._config_cache is not None:
            return cls._config_cache

        config_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'loot_config.json'
        )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._config_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[LootSystem] Ошибка загрузки конфига: {e}")
            cls._config_cache = {}

        return cls._config_cache

    def __init__(self, player, quest_manager=None, killstreak_system=None):
        """
        Инициализация системы лута.

        Args:
            player: Объект игрока
            quest_manager: Менеджер квестов (опционально)
            killstreak_system: Система серий убийств (опционально)
        """
        self.player = player
        self.quest_manager = quest_manager
        self.killstreak_system = killstreak_system
        self.config = self._load_config()

    def _get_item_safe(self, item_id):
        """
        Безопасно получить предмет по ID с fallback на PREDEFINED_ITEMS.

        Args:
            item_id: Идентификатор предмета

        Returns:
            Item: Объект предмета или None
        """
        # Сначала пробуем ItemRegistry
        item = get_item(item_id)
        if item:
            return item
        # Fallback на PREDEFINED_ITEMS
        return PREDEFINED_ITEMS.get(item_id)

    def _get_quality_weights(self, enemy_level):
        """Получить веса качества для уровня врага из конфига."""
        from game.inventory import ItemQuality

        quality_config = self.config.get('quality_by_level', {})

        # Определяем ранг по уровню
        for rank_key in ['rank_1', 'rank_2', 'rank_3', 'rank_4']:
            rank_data = quality_config.get(rank_key, {})
            max_level = rank_data.get('max_level', 999)
            if enemy_level <= max_level:
                weights_str = rank_data.get('weights', {})
                # Преобразуем строковые ключи в ItemQuality
                quality_map = {
                    'POOR': ItemQuality.POOR,
                    'COMMON': ItemQuality.COMMON,
                    'UNCOMMON': ItemQuality.UNCOMMON,
                    'RARE': ItemQuality.RARE,
                    'EPIC': ItemQuality.EPIC,
                    'LEGENDARY': ItemQuality.LEGENDARY,
                }
                return {quality_map[k]: v for k, v in weights_str.items() if k in quality_map}

        # Fallback - обычное качество
        return {ItemQuality.COMMON: 1.0}

    def _get_potion_choices(self, enemy_level):
        """Получить список зелий для уровня врага из конфига."""
        potions_config = self.config.get('potions', {})
        choices = list(potions_config.get('base', [
            'minor_health_potion', 'minor_stamina_potion', 'minor_mana_potion'
        ]))
        if enemy_level >= 10:
            choices.extend(potions_config.get('level_10', [
                'health_potion', 'stamina_potion', 'mana_potion'
            ]))
        return choices

    def _get_book_pool(self, enemy_level):
        """Получить взвешенный пул книг умений для уровня врага."""
        books_config = self.config.get('skill_books', {})
        book_pool = []

        for tier in ['common', 'uncommon', 'rare']:
            tier_config = books_config.get(tier, {})
            min_level = tier_config.get('min_level', 1)
            weight = tier_config.get('weight', 10)
            books = tier_config.get('books', [])

            if enemy_level >= min_level:
                for book in books:
                    book_pool.extend([book] * weight)

        return book_pool

    def _get_available_recipes(self, enemy_level):
        """Получить список доступных рецептов для уровня врага."""
        recipes_config = self.config.get('recipes', {})
        tiers = recipes_config.get('tiers', [])
        available = []

        for tier in tiers:
            min_level = tier.get('min_level', 1)
            if enemy_level >= min_level:
                available.extend(tier.get('recipes', []))

        return available

    def generate_loot(self, enemy):
        """
        Генерировать лут с поверженного врага.

        Args:
            enemy: Поверженный враг

        Returns:
            tuple: (список предметов [(item, quantity)], количество золота)
        """
        loot_items = []
        loot_gold = 0

        # Животные дают специфичный лут без золота
        if enemy.npc_type in ["wolf", "bear", "deer"]:
            animal_loot = ItemGenerator.generate_animal_loot(enemy.npc_type, enemy.level)
            for item in animal_loot:
                loot_items.append((item, 1))
            return loot_items, 0

        # Золото зависит от уровня врага (из конфига)
        gold_config = self.config.get('gold', {})
        base_gold = enemy.level * gold_config.get('base_per_level', 5)
        loot_gold = random.randint(base_gold, int(base_gold * gold_config.get('multiplier_max', 2.0)))

        # Шанс выпадения предметов (из конфига)
        drop_config = self.config.get('drop_chance', {})
        drop_chance = min(
            drop_config.get('base', 0.3) + enemy.level * drop_config.get('per_level', 0.02),
            drop_config.get('max', 0.8)
        )

        # Количество предметов
        num_items = random.randint(
            drop_config.get('items_min', 1),
            drop_config.get('items_max', 3)
        )

        for _ in range(num_items):
            if random.random() < drop_chance:
                item_type = random.choice(['equipment', 'potion', 'equipment', 'potion'])

                if item_type == 'equipment':
                    item_level = max(1, enemy.level + random.randint(-2, 2))

                    # Качество из конфига
                    quality_weights = self._get_quality_weights(enemy.level)
                    quality = ItemGenerator.generate_quality(quality_weights)

                    # Типы экипировки из конфига
                    equip_config = self.config.get('equipment_types', {})
                    equipment_roll = random.random()

                    jewelry_threshold = equip_config.get('jewelry_chance', 0.15)
                    weapon_threshold = jewelry_threshold + equip_config.get('weapon_chance', 0.425)

                    if equipment_roll < jewelry_threshold:
                        item = ItemGenerator.generate_jewelry(item_level, quality=quality)
                    elif equipment_roll < weapon_threshold:
                        item = ItemGenerator.generate_weapon(item_level, quality)
                    else:
                        item = ItemGenerator.generate_armor(item_level, quality=quality)

                    loot_items.append((item, 1))

                elif item_type == 'potion':
                    potion_choices = self._get_potion_choices(enemy.level)
                    potion_name = random.choice(potion_choices)

                    potion = self._get_item_safe(potion_name)
                    if potion:
                        potions_config = self.config.get('potions', {})
                        quantity = random.randint(
                            potions_config.get('quantity_min', 1),
                            potions_config.get('quantity_max', 2)
                        )
                        loot_items.append((potion, quantity))

        # Книги умений (из конфига)
        books_config = self.config.get('skill_books', {})
        book_drop_chance = min(
            books_config.get('drop_chance_base', 0.05) + enemy.level * books_config.get('drop_chance_per_level', 0.005),
            books_config.get('drop_chance_max', 0.20)
        )

        if random.random() < book_drop_chance:
            book_pool = self._get_book_pool(enemy.level)
            if book_pool:
                book_id = random.choice(book_pool)
                book = self._get_item_safe(book_id)
                if book:
                    loot_items.append((book, 1))

        # Рецепты крафта (из конфига)
        recipes_config = self.config.get('recipes', {})
        recipe_drop_chance = min(
            recipes_config.get('drop_chance_base', 0.03) + enemy.level * recipes_config.get('drop_chance_per_level', 0.003),
            recipes_config.get('drop_chance_max', 0.15)
        )

        if random.random() < recipe_drop_chance:
            available_recipes = self._get_available_recipes(enemy.level)
            if available_recipes:
                recipe_id = random.choice(available_recipes)
                recipe = self._get_item_safe(recipe_id)
                if recipe:
                    loot_items.append((recipe, 1))

        # Специальный лут по типам врагов (из конфига)
        special_loot = self.config.get('special_loot', {})

        if enemy.npc_type in special_loot:
            for item_id, drop_data in special_loot[enemy.npc_type].items():
                drop_chance = min(
                    drop_data.get('base_chance', 0.3) + enemy.level * drop_data.get('per_level', 0.01),
                    drop_data.get('max_chance', 0.6)
                )
                if random.random() < drop_chance:
                    quantity = random.randint(
                        drop_data.get('quantity_min', 1),
                        drop_data.get('quantity_max', 3)
                    )
                    special_item = self._get_item_safe(item_id)
                    if special_item:
                        loot_items.append((special_item, quantity))

        return loot_items, loot_gold

    def process_victory(self, enemy):
        """
        Обработать победу над врагом.

        Args:
            enemy: Поверженный враг

        Returns:
            dict: Результат победы {loot_items, loot_gold, streak_message}
        """
        result = {
            'loot_items': [],
            'loot_gold': 0,
            'streak_message': None
        }

        if enemy is None:
            return result

        # Генерируем лут
        loot_items, loot_gold = self.generate_loot(enemy)

        # Применяем бонус серии убийств
        if self.killstreak_system:
            streak_info = self.killstreak_system.register_kill()
            loot_gold = int(loot_gold * streak_info['multiplier'])
            result['streak_message'] = streak_info.get('message')

        result['loot_items'] = loot_items
        result['loot_gold'] = loot_gold

        # Добавляем лут в инвентарь
        self.player.inventory.add_gold(loot_gold)
        for item, quantity in loot_items:
            self.player.inventory.add_item(item, quantity)

            # Обновляем прогресс квестов на сбор для частей животных
            if self.quest_manager and hasattr(item, 'name'):
                item_key = self._get_item_key_by_name(item.name)
                if item_key:
                    self.quest_manager.update_gather_progress(item_key, quantity, self.player)

        # Обновляем статистику игрока
        self._update_kill_stats(enemy)

        # Обновляем квесты
        if self.quest_manager and hasattr(enemy, 'npc_type'):
            self._update_quest_progress(enemy.npc_type)

        return result

    def _update_kill_stats(self, enemy):
        """Обновить статистику убийств игрока."""
        if not hasattr(enemy, 'npc_type'):
            return

        if not hasattr(self.player, 'enemies_killed'):
            self.player.enemies_killed = 0
        self.player.enemies_killed += 1

        enemy_type = enemy.npc_type

        # Отслеживание убийств животных
        stat_map = {
            'wolf': 'wolves_killed',
            'bear': 'bears_killed',
            'deer': 'deer_killed'
        }

        if enemy_type in stat_map:
            stat_name = stat_map[enemy_type]
            if not hasattr(self.player, stat_name):
                setattr(self.player, stat_name, 0)
            setattr(self.player, stat_name, getattr(self.player, stat_name) + 1)

    def _get_item_key_by_name(self, item_name):
        """
        Получить ключ предмета по его имени для квестов.

        Args:
            item_name: Название предмета

        Returns:
            str: Ключ предмета или None
        """
        # Маппинг из конфига
        item_name_to_key = self.config.get('item_name_to_key', {})
        return item_name_to_key.get(item_name)

    def _update_quest_progress(self, enemy_type):
        """Обновить прогресс квестов на убийство."""
        if not self.quest_manager:
            return

        # Типы врагов, которые отслеживаются квестами
        quest_enemy_types = ['bandit', 'undead', 'wolf', 'bear', 'deer', 'necromancer']

        if enemy_type in quest_enemy_types:
            messages = self.quest_manager.update_kill_progress(enemy_type)
            for msg in messages:
                print(f"  {msg}")
