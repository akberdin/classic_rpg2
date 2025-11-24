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
            animal_loot = ItemGenerator.generate_animal_loot(enemy.npc_type)
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

                    if random.random() < 0.5:
                        item = ItemGenerator.generate_weapon(item_level, quality)
                    else:
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
