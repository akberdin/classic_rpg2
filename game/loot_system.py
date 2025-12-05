"""
Система генерации и обработки лута.

Извлечено из engine.py для уменьшения сложности.
"""
import random
from game.inventory import ItemGenerator, PREDEFINED_ITEMS


class LootSystem:
    """Система генерации лута с врагов"""

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

        # Золото зависит от уровня врага
        base_gold = enemy.level * 5
        loot_gold = random.randint(base_gold, base_gold * 2)

        # Шанс выпадения предметов зависит от уровня врага
        drop_chance = min(0.3 + enemy.level * 0.02, 0.8)

        # Количество предметов (1-3)
        num_items = random.randint(1, 3)

        for _ in range(num_items):
            if random.random() < drop_chance:
                item_type = random.choice(['equipment', 'potion', 'equipment', 'potion'])

                if item_type == 'equipment':
                    item_level = max(1, enemy.level + random.randint(-2, 2))
                    quality = ItemGenerator.generate_quality()

                    # Выбираем тип экипировки: оружие, броня или ювелирка
                    # Ювелирка встречается реже (15% шанс)
                    equipment_roll = random.random()
                    if equipment_roll < 0.15:
                        # Генерируем ювелирное изделие
                        item = ItemGenerator.generate_jewelry(item_level, quality=quality)
                    elif equipment_roll < 0.575:
                        # Генерируем оружие (42.5%)
                        item = ItemGenerator.generate_weapon(item_level, quality)
                    else:
                        # Генерируем броню (42.5%)
                        item = ItemGenerator.generate_armor(item_level, quality=quality)

                    loot_items.append((item, 1))

                elif item_type == 'potion':
                    potion_choices = ['minor_health_potion', 'minor_stamina_potion', 'minor_mana_potion']
                    if enemy.level >= 10:
                        potion_choices.extend(['health_potion', 'stamina_potion', 'mana_potion'])

                    potion_name = random.choice(potion_choices)
                    if potion_name in PREDEFINED_ITEMS:
                        potion = PREDEFINED_ITEMS[potion_name]
                        quantity = random.randint(1, 2)
                        loot_items.append((potion, quantity))

        # Шанс выпадения книг умений (зависит от уровня врага)
        # Чем выше уровень врага, тем больше шанс
        book_drop_chance = min(0.05 + enemy.level * 0.005, 0.20)  # от 5% до 20%

        if random.random() < book_drop_chance:
            # Книги умений разделены по редкости (вес = шанс выбора)
            # ОБЫЧНЫЕ (вес 50) - базовые умения
            common_books = [
                # Общие боевые умения
                "book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry",
                # Базовые умения лука
                "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
                # Базовые умения кинжала
                "book_backstab", "book_bleeding_cut", "book_shadow_step",
                # Базовые умения меча
                "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance",
                # Базовые магические умения
                "book_heal", "book_regeneration", "book_stamina_recovery",
                "book_magic_missile", "book_mage_shield",
            ]

            # РЕДКИЕ (вес 30) - продвинутые умения
            uncommon_books = [
                # Продвинутые умения SHADOW
                "book_deadly_poison", "book_stealth", "book_shadow_agility",
                # Продвинутые умения WARRIOR
                "book_iron_stance", "book_intimidate", "book_counterattack",
                # Продвинутые умения HUNTER
                "book_hunters_mark", "book_stamina_boost", "book_eagle_eye",
                "book_long_range_shot",
                # Продвинутые умения для копья
                "book_lunge_strike", "book_spear_sweep", "book_armor_breach",
                # Продвинутая магия
                "book_fireball", "book_ice_bolt", "book_lightning",
            ]

            # ЭПИЧЕСКИЕ (вес 10) - мощные умения
            rare_books = [
                # Эпические умения SHADOW
                "book_critical_strike",
                # Эпические умения WARRIOR
                "book_steel_skin", "book_berserker",
                # Эпические умения HUNTER
                "book_explosive_arrow", "book_trap",
            ]

            # Создаем взвешенный список для выбора
            book_pool = []

            # Обычные книги (вес 50 каждая)
            for book in common_books:
                book_pool.extend([book] * 50)

            # Редкие книги (вес 30 каждая, но только если уровень врага >= 5)
            if enemy.level >= 5:
                for book in uncommon_books:
                    book_pool.extend([book] * 30)

            # Эпические книги (вес 10 каждая, но только если уровень врага >= 10)
            if enemy.level >= 10:
                for book in rare_books:
                    book_pool.extend([book] * 10)

            # Выбираем случайную книгу из пула
            if book_pool:
                book_id = random.choice(book_pool)
                if book_id in PREDEFINED_ITEMS:
                    loot_items.append((PREDEFINED_ITEMS[book_id], 1))

        # Шанс выпадения рецептов крафта (зависит от уровня врага)
        # Чем выше уровень врага, тем больше шанс
        recipe_drop_chance = min(0.03 + enemy.level * 0.003, 0.15)  # от 3% до 15%

        if random.random() < recipe_drop_chance:
            # Рецепты разделены по редкости в зависимости от уровня врага
            recipes = []

            # Базовые рецепты (всегда доступны)
            recipes.extend(["recipe_copper_ingot", "recipe_iron_ingot"])

            # Средние рецепты (уровень >= 10)
            if enemy.level >= 10:
                recipes.append("recipe_silver_ingot")

            # Редкие рецепты (уровень >= 15)
            if enemy.level >= 15:
                recipes.append("recipe_gold_ingot")

            # Эпические рецепты (уровень >= 20)
            if enemy.level >= 20:
                recipes.append("recipe_mithril_ingot")

            # Выбираем случайный рецепт из доступных
            if recipes:
                recipe_id = random.choice(recipes)
                if recipe_id in PREDEFINED_ITEMS:
                    loot_items.append((PREDEFINED_ITEMS[recipe_id], 1))

        # Специальный лут для бандитов - древние монеты
        if enemy.npc_type == "bandit":
            coin_drop_chance = min(0.30 + enemy.level * 0.01, 0.60)  # от 30% до 60%
            if random.random() < coin_drop_chance:
                quantity = random.randint(1, 3)
                loot_items.append((PREDEFINED_ITEMS["ancient_coin"], quantity))

        # Специальный лут для нежити - магические кристаллы и древние свитки
        if enemy.npc_type == "undead":
            # Магические кристаллы (40-70% шанс)
            crystal_drop_chance = min(0.40 + enemy.level * 0.01, 0.70)
            if random.random() < crystal_drop_chance:
                quantity = random.randint(1, 2)
                loot_items.append((PREDEFINED_ITEMS["magic_crystal"], quantity))

            # Древние свитки (35-65% шанс)
            scroll_drop_chance = min(0.35 + enemy.level * 0.01, 0.65)
            if random.random() < scroll_drop_chance:
                quantity = random.randint(1, 3)
                loot_items.append((PREDEFINED_ITEMS["old_scroll"], quantity))

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
