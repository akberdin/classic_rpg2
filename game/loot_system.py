"""
Система генерации и обработки лута.

Извлечено из engine.py для уменьшения сложности.
"""
import json
import os
import random
from game.inventory import ItemGenerator
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

    def __init__(self, player, killstreak_system=None):
        """
        Инициализация системы лута.

        Args:
            player: Объект игрока
            killstreak_system: Система серий убийств (опционально)
        """
        self.player = player
        self.killstreak_system = killstreak_system
        self.config = self._load_config()

    def _get_item_safe(self, item_id):
        """
        Безопасно получить предмет по ID.

        Args:
            item_id: Идентификатор предмета

        Returns:
            Item: Объект предмета или None
        """
        return get_item(item_id)

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

        # Обновляем статистику игрока
        self._update_kill_stats(enemy)

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

        # Уведомляем систему квестов об убийстве животного
        if enemy_type in ('wolf', 'bear', 'deer'):
            if hasattr(self.player, 'quest_manager'):
                self.player.quest_manager.update_quest_progress(
                    'animal_killed',
                    {'animal_type': enemy_type}
                )

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

