"""
Система сбора ресурсов.

Извлечено из engine.py для уменьшения сложности.
"""
import random


# Словарь соответствий имен предметов и ключей для квестов
ITEM_KEY_MAPPING = {
    'Медная руда': 'copper_ore',
    'Железная руда': 'iron_ore',
    'Серебряная руда': 'silver_ore',
    'Золотая руда': 'gold_ore',
    'Мифриловая руда': 'mithril_ore',
    'Древесина': 'wood',
    'Древняя монета': 'ancient_coin',
    'Фрагмент артефакта': 'artifact_fragment',
    'Магический кристалл': 'magic_crystal',
    'Старый свиток': 'old_scroll',
    # Части животных
    'Клык волка': 'wolf_fang',
    'Клык медведя': 'bear_fang',
    'Шкура волка': 'wolf_hide',
    'Шкура медведя': 'bear_hide',
    'Шкура оленя': 'deer_hide',
    'Медвежатина': 'bear_meat',
    'Оленина': 'deer_meat',
}


class ResourceSystem:
    """Система сбора ресурсов с локаций"""

    def __init__(self, player, game_map, quest_manager, game_time, start_combat_callback=None, resource_window_callback=None):
        """
        Инициализация системы ресурсов.

        Args:
            player: Объект игрока
            game_map: Карта игры
            quest_manager: Менеджер квестов
            game_time: Система игрового времени
            start_combat_callback: Функция для начала боя
            resource_window_callback: Функция для показа окна сбора ресурсов
        """
        self.player = player
        self.game_map = game_map
        self.quest_manager = quest_manager
        self.game_time = game_time
        self.start_combat_callback = start_combat_callback
        self.resource_window_callback = resource_window_callback

    def collect_resources(self):
        """
        Собрать ресурсы с текущей локации.

        Returns:
            bool: True если сбор успешен
        """
        from game.inventory import get_random_loot_from_location
        from game.constants import LOCATION_MINE, LOCATION_RUINS, LOCATION_BANDIT_CAMP

        tile = self.game_map.get_tile(self.player.x, self.player.y)

        if not tile.has_location():
            print("Здесь нечего собирать!")
            return False

        location = tile.location

        if not location.can_collect_loot:
            print(f"{location.name} не содержит ресурсов для сбора.")
            return False

        if location.loot_collected:
            print(f"Вы уже собрали ресурсы с {location.name}.")
            return False

        # Проверяем случайное событие при сборе лута
        event_result, event_message = self._process_loot_event()
        if event_result == "combat_started":
            location.loot_collected = True
            return False

        # Получаем лут с локации с учётом удачи игрока
        loot = get_random_loot_from_location(
            location.location_type,
            self.player.level,
            self.player.luck
        )

        if not loot:
            print("Ничего не найдено!")
            return False

        # Бонусный лут от события
        if event_result == "bonus_loot":
            bonus_loot = get_random_loot_from_location(
                location.location_type,
                self.player.level,
                self.player.luck
            )
            loot.extend(bonus_loot)

        # Добавляем лут в инвентарь и собираем информацию
        collected_items, collected_gold = self._add_loot_to_inventory(loot)

        # Помечаем локацию как обыскованную
        location.loot_collected = True

        # Обновляем прогресс квеста "Охотник за сокровищами"
        self.player.resources_collected += 1
        self.quest_manager.update_quest_progress("treasure_hunter", 0, 1)

        # Добавляем тип локации в посещенные и обновляем квест "Исследователь"
        if location.location_type not in self.player.visited_location_types:
            self.player.visited_location_types.add(location.location_type)
            self.quest_manager.update_quest_progress("explorer_start", 0, 1)

        # Продвигаем время на 20 минут (1/3 часа)
        self.game_time.advance_time(1/3)

        # Определяем отображаемый тип локации
        location_type_display = {
            LOCATION_MINE: "Шахта",
            LOCATION_RUINS: "Руины",
            LOCATION_BANDIT_CAMP: "Лагерь бандитов"
        }.get(location.location_type, "Локация")

        # Показываем окно с собранными ресурсами
        if self.resource_window_callback:
            self.resource_window_callback(
                collected_items,
                collected_gold,
                location.name,
                location_type_display,
                event_message
            )

        return True

    def _add_loot_to_inventory(self, loot):
        """
        Добавить лут в инвентарь игрока.

        Args:
            loot: Список предметов [(item, quantity), ...]

        Returns:
            tuple: (collected_items, collected_gold) - списки собранных предметов и золота
        """
        collected_items = []
        collected_gold = 0

        for item, quantity in loot:
            if item == 'gold':
                self.player.inventory.add_gold(quantity)
                collected_gold += quantity
            elif self.player.inventory.add_item(item, quantity):
                collected_items.append((item, quantity))

                # Обновляем прогресс квестов на сбор ресурсов
                item_key = self.get_item_key(item.name)
                if item_key:
                    self.quest_manager.update_gather_progress(
                        item_key, quantity, self.player
                    )

        return collected_items, collected_gold

    def _process_loot_event(self):
        """
        Обработать случайное событие при сборе лута.

        Returns:
            tuple: (event_type, event_message) - тип события и сообщение для отображения
        """
        from game.npc import Bandit

        # Шанс события - 30%
        if random.randint(1, 100) > 30:
            return "nothing", None

        # Выбираем тип события
        event_type = random.choice(["trap", "enemy", "bonus", "nothing"])

        if event_type == "trap":
            return self._trigger_trap()

        elif event_type == "enemy":
            return self._spawn_enemy()

        elif event_type == "bonus":
            return "bonus_loot", "Удача! Вы нашли дополнительный тайник!"

        return "nothing", None

    def _trigger_trap(self):
        """
        Обработать попадание в ловушку.

        Returns:
            tuple: (event_type, event_message)
        """
        effective_max_health = self.player.get_effective_max_health()
        trap_damage = int(effective_max_health * 0.10)
        self.player.health -= trap_damage
        self.player.health = max(1, self.player.health)
        message = f"Вы попали в ловушку! Получено {trap_damage} урона."
        print(message)
        return "trap_triggered", message

    def _spawn_enemy(self):
        """
        Создать врага для боя.

        Returns:
            tuple: (event_type, event_message)
        """
        from game.npc import Bandit

        # Спавн врага на 2-5 уровней выше игрока
        enemy_level = self.player.level + random.randint(2, 5)
        enemy_level = min(enemy_level, 40)

        # Создаём бандита-защитника
        enemy_names = ["Страж сокровищ", "Охранник", "Засадник", "Грабитель"]
        enemy = Bandit(
            random.choice(enemy_names),
            self.player.x,
            self.player.y,
            enemy_level,
            self.player.x,
            self.player.y
        )

        message = f"На вас напал {enemy.name} {enemy_level} уровня!"
        print(message)

        if self.start_combat_callback:
            self.start_combat_callback(enemy)
            return "combat_started", None

        return "nothing", None

    @staticmethod
    def get_item_key(item_name):
        """
        Получить ключ предмета для системы квестов.

        Args:
            item_name: Отображаемое имя предмета

        Returns:
            str: Ключ предмета или None
        """
        return ITEM_KEY_MAPPING.get(item_name)
