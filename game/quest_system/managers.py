"""
Менеджеры для управления квестами и достижениями
"""
from game.config.config_loader import get_quest_config
from .models import QuestStatus, QuestType, QuestObjective, Achievement, AchievementRarity


class QuestManager:
    """Менеджер квестов"""

    def __init__(self):
        """Инициализация менеджера квестов"""
        config = get_quest_config()
        self.MAX_ACTIVE_QUESTS = config.get_quest_limit('max_active_quests', default=5)
        self.QUEST_ROTATION_TURNS = config.get_quest_limit('quest_rotation_turns', default=120)

        self.available_quests = []  # Доступные квесты
        self.active_quests = []     # Активные квесты
        self.completed_quests = []  # Завершенные квесты
        self.location_quests = {}   # Квесты по локациям: {location_id: [quests]}
        self.location_quest_turn = {}  # Ход последнего обновления квестов: {location_id: turn}

    def add_available_quest(self, quest):
        """
        Добавить квест в список доступных

        Args:
            quest: Квест для добавления
        """
        self.available_quests.append(quest)

    def add_location_quest(self, location_id, quest):
        """
        Добавить квест к локации

        Args:
            location_id: ID локации
            quest: Квест для добавления
        """
        if location_id not in self.location_quests:
            self.location_quests[location_id] = []
        self.location_quests[location_id].append(quest)

    def get_location_quests(self, location_id):
        """
        Получить доступные квесты в локации

        Args:
            location_id: ID локации

        Returns:
            list: Список доступных квестов в локации
        """
        return self.location_quests.get(location_id, [])

    def can_accept_quest(self):
        """
        Проверить, можно ли принять новый квест

        Returns:
            bool: True если можно принять квест
        """
        return len(self.active_quests) < self.MAX_ACTIVE_QUESTS

    def accept_quest(self, quest_id, location_id=None, player=None):
        """
        Принять квест

        Args:
            quest_id: ID квеста
            location_id: ID локации (опционально)
            player: Игрок (для проверки текущего прогресса)

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        # Проверяем лимит активных квестов
        if not self.can_accept_quest():
            return False, f"Достигнут лимит активных квестов ({self.MAX_ACTIVE_QUESTS})"

        # Ищем квест среди доступных или в локации
        quest = None

        # Сначала ищем в локации
        if location_id and location_id in self.location_quests:
            for q in self.location_quests[location_id]:
                if q.quest_id == quest_id:
                    quest = q
                    break

        # Затем ищем среди общих доступных
        if not quest:
            for q in self.available_quests:
                if q.quest_id == quest_id:
                    quest = q
                    break

        if not quest:
            return False, "Квест не найден"

        # Принимаем квест
        if quest.start():
            # Удаляем из соответствующего списка
            if location_id and location_id in self.location_quests:
                if quest in self.location_quests[location_id]:
                    self.location_quests[location_id].remove(quest)
            if quest in self.available_quests:
                self.available_quests.remove(quest)

            self.active_quests.append(quest)

            # Если передан игрок и это квест на сбор, сразу проверяем инвентарь
            if player and quest.quest_type == QuestType.GATHER_RESOURCE and quest.target_item:
                current_count = self._get_item_count_in_inventory(player, quest.target_item)
                if quest.objectives:
                    quest.objectives[0].current_count = min(current_count, quest.objectives[0].required_count)
                    quest.objectives[0].completed = quest.objectives[0].current_count >= quest.objectives[0].required_count
                    quest.check_completion()

            return True, f"Принят квест: {quest.name}"

        return False, "Квест уже принят"

    def abandon_quest(self, quest_id):
        """
        Отменить квест

        Args:
            quest_id: ID квеста

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        quest = None
        for q in self.active_quests:
            if q.quest_id == quest_id:
                quest = q
                break

        if not quest:
            return False, "Квест не найден среди активных"

        self.active_quests.remove(quest)
        quest.status = QuestStatus.NOT_STARTED

        # Сбрасываем прогресс целей
        for obj in quest.objectives:
            obj.current_count = 0
            obj.completed = False

        # Возвращаем квест в локацию если он был из локации
        if quest.location_id:
            self.add_location_quest(quest.location_id, quest)
        else:
            self.available_quests.append(quest)

        return True, f"Квест отменён: {quest.name}"

    def get_quests_ready_to_turn_in(self, location_id=None):
        """
        Получить список квестов готовых к сдаче

        Args:
            location_id: ID локации (опционально, для фильтрации)

        Returns:
            list: Список квестов готовых к сдаче
        """
        ready_quests = []
        for quest in self.active_quests:
            # Проверяем завершение квеста перед добавлением
            quest.check_completion()

            if quest.is_ready_to_turn_in():
                # Стартовые квесты можно сдать в любой локации
                if quest.is_starter or quest.giver_location == "Любая локация":
                    ready_quests.append(quest)
                # Квесты без привязки к локации (от NPC) тоже показываем
                elif quest.location_id is None:
                    ready_quests.append(quest)
                # Локационные квесты - только в нужной локации
                elif location_id is None or quest.location_id == location_id:
                    ready_quests.append(quest)
        return ready_quests

    def update_quest_progress(self, quest_id, objective_index, amount=1):
        """
        Обновить прогресс цели квеста

        Args:
            quest_id: ID квеста
            objective_index: Индекс цели
            amount: Количество для добавления

        Returns:
            tuple: (bool, str) - завершена ли цель и сообщение
        """
        # Ищем квест среди активных
        quest = None
        for q in self.active_quests:
            if q.quest_id == quest_id:
                quest = q
                break

        if not quest:
            return False, ""

        # Обновляем цель
        if 0 <= objective_index < len(quest.objectives):
            objective = quest.objectives[objective_index]
            completed = objective.progress(amount)

            # Проверяем общее завершение квеста
            quest.check_completion()

            if completed:
                return True, f"Цель выполнена: {objective.description}"

        return False, ""

    def complete_quest(self, quest_id, player):
        """
        Завершить квест и получить награды

        Args:
            quest_id: ID квеста
            player: Игрок

        Returns:
            tuple: (bool, list) - успех и список сообщений о наградах
        """
        # Ищем квест среди активных
        quest = None
        for q in self.active_quests:
            if q.quest_id == quest_id and (q.is_completed() or q.is_ready_to_turn_in()):
                quest = q
                break

        if not quest:
            return False, []

        # Получаем награды
        messages = quest.claim_rewards(player)

        # Перемещаем квест в завершенные
        self.active_quests.remove(quest)
        self.completed_quests.append(quest)

        return True, messages

    def update_kill_progress(self, enemy_type):
        """
        Обновить прогресс квестов на убийство

        Args:
            enemy_type: Тип убитого врага ('bandit', 'undead', 'necromancer', 'wolf', 'bear', 'deer')

        Returns:
            list: Список сообщений о прогрессе
        """
        messages = []
        # Словарь для поиска врагов по описанию цели
        enemy_keywords = {
            'bandit': ['бандит', 'разбойник'],
            'undead': ['нежить', 'мертв', 'зомби', 'скелет'],
            'necromancer': ['некромант', 'темный маг'],
            'wolf': ['волк', 'волков'],
            'bear': ['медвед', 'медведей'],
            'deer': ['олен', 'оленей']
        }

        # Типы врагов для any_enemy
        humanoid_enemies = ['bandit', 'undead', 'necromancer']

        for quest in self.active_quests:
            if quest.quest_type in [QuestType.KILL_ENEMIES, QuestType.KILL_ANIMALS]:
                # Проверяем основной target_enemy или target_animal
                # any_enemy засчитывает всех гуманоидных врагов
                is_any_enemy_match = quest.target_enemy == "any_enemy" and enemy_type in humanoid_enemies
                if quest.target_enemy == enemy_type or quest.target_animal == enemy_type or is_any_enemy_match:
                    if quest.objectives:
                        completed = quest.objectives[0].progress(1)
                        quest.check_completion()
                        if completed:
                            messages.append(f"Цель выполнена: {quest.objectives[0].description}")
                        elif quest.is_ready_to_turn_in():
                            messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")
                else:
                    # Для квестов с несколькими целями проверяем каждую цель по описанию
                    keywords = enemy_keywords.get(enemy_type, [enemy_type])
                    for i, objective in enumerate(quest.objectives):
                        if objective.completed:
                            continue
                        desc_lower = objective.description.lower()
                        if any(kw in desc_lower for kw in keywords):
                            completed = objective.progress(1)
                            quest.check_completion()
                            if completed:
                                messages.append(f"Цель выполнена: {objective.description}")
                            if quest.is_ready_to_turn_in():
                                messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")
                            break  # Обновляем только одну цель за раз
        return messages

    def update_gather_progress(self, item_name, amount=1, player=None):
        """
        Обновить прогресс квестов на сбор ресурсов

        Args:
            item_name: Название собранного предмета
            amount: Количество (не используется если передан player)
            player: Игрок (для проверки инвентаря)

        Returns:
            list: Список сообщений о прогрессе
        """
        messages = []
        # Словарь для поиска ресурсов по описанию цели
        resource_keywords = {
            'copper_ore': ['медн', 'меди'],
            'iron_ore': ['железн', 'железа'],
            'silver_ore': ['серебр', 'серебра'],
            'gold_ore': ['золот', 'золота'],
            'mithril_ore': ['мифрил'],
            'wood': ['древесин', 'дерево'],
            'magic_crystal': ['магическ', 'кристалл'],
            'artifact_fragment': ['артефакт', 'фрагмент'],
            'ancient_coin': ['древн', 'монет'],
            'old_scroll': ['свиток', 'старый'],
            # Ресурсы животных
            'wolf_fang': ['клык волка', 'зуб волка'],
            'wolf_hide': ['шкура волка', 'шкур волк'],
            'bear_fang': ['клык медведя', 'зуб медвед'],
            'bear_hide': ['шкура медведя', 'шкур медвед'],
            'bear_meat': ['медвежатин', 'мясо медвед'],
            'deer_hide': ['шкура оленя', 'шкур олен'],
            'deer_meat': ['оленин', 'мясо олен'],
            # Общие категории
            'animal_hide': ['шкур', 'hide'],
            'animal_fang': ['зуб', 'клык', 'fang'],
            'animal_meat': ['мясо', 'meat']
        }

        for quest in self.active_quests:
            if quest.quest_type == QuestType.GATHER_RESOURCE:
                # Проверяем основной target_item
                if quest.target_item == item_name:
                    if quest.objectives:
                        if player:
                            current_count = self._get_item_count_in_inventory(player, item_name)
                            quest.objectives[0].current_count = min(current_count, quest.objectives[0].required_count)
                            quest.objectives[0].completed = quest.objectives[0].current_count >= quest.objectives[0].required_count
                        else:
                            quest.objectives[0].progress(amount)

                        quest.check_completion()

                        if quest.objectives[0].is_completed():
                            if quest.is_ready_to_turn_in():
                                messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")
                else:
                    # Для квестов с несколькими целями проверяем каждую цель по описанию
                    keywords = resource_keywords.get(item_name, [item_name])
                    for objective in quest.objectives:
                        if objective.completed:
                            continue
                        desc_lower = objective.description.lower()
                        if any(kw in desc_lower for kw in keywords):
                            if player:
                                current_count = self._get_item_count_in_inventory(player, item_name)
                                objective.current_count = min(current_count, objective.required_count)
                                objective.completed = objective.current_count >= objective.required_count
                            else:
                                objective.progress(amount)

                            quest.check_completion()

                            if objective.is_completed():
                                if quest.is_ready_to_turn_in():
                                    messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")
                            break  # Обновляем только одну цель за раз
        return messages

    def _get_item_count_in_inventory(self, player, item_key):
        """
        Получить количество предмета в инвентаре игрока

        Args:
            player: Игрок
            item_key: Ключ предмета (например 'copper_ore')

        Returns:
            int: Количество предмета
        """
        from .quest_data import ITEM_KEY_TO_NAME

        item_name = ITEM_KEY_TO_NAME.get(item_key)
        if not item_name:
            return 0

        # Проверяем инвентарь игрока
        item_data = player.inventory.get_item(item_name)
        if item_data:
            return item_data[1]  # Возвращаем количество
        return 0

    def check_all_quest_progress(self, player):
        """
        Проверить прогресс всех активных квестов на основе инвентаря

        Args:
            player: Игрок

        Returns:
            list: Список сообщений о прогрессе
        """
        from .quest_data import RESOURCE_KEYWORDS

        messages = []
        for quest in self.active_quests:
            if quest.quest_type == QuestType.GATHER_RESOURCE:
                was_ready = quest.is_ready_to_turn_in()

                # Проверяем основной target_item если он установлен
                if quest.target_item and quest.objectives:
                    current_count = self._get_item_count_in_inventory(player, quest.target_item)
                    quest.objectives[0].current_count = min(current_count, quest.objectives[0].required_count)
                    quest.objectives[0].completed = quest.objectives[0].current_count >= quest.objectives[0].required_count

                # Для квестов с несколькими целями проверяем каждую цель
                # Это важно для уникальных квестов с несколькими типами ресурсов
                if len(quest.objectives) > 1 or not quest.target_item:
                    for objective in quest.objectives:
                        if objective.completed:
                            continue

                        # Пытаемся найти соответствующий ресурс по описанию цели
                        desc_lower = objective.description.lower()
                        for item_key, keywords in RESOURCE_KEYWORDS.items():
                            if any(kw in desc_lower for kw in keywords):
                                current_count = self._get_item_count_in_inventory(player, item_key)
                                objective.current_count = min(current_count, objective.required_count)
                                objective.completed = objective.current_count >= objective.required_count
                                break

                quest.check_completion()

                # Сообщаем если квест стал готов к сдаче
                if quest.is_ready_to_turn_in() and not was_ready:
                    messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")

        return messages

    def get_active_quests(self):
        """
        Получить список активных квестов

        Returns:
            list: Список активных квестов
        """
        return self.active_quests

    def get_available_quests(self):
        """
        Получить список доступных квестов

        Returns:
            list: Список доступных квестов
        """
        return self.available_quests

    def get_completed_quests(self):
        """
        Получить список завершенных квестов

        Returns:
            list: Список завершенных квестов
        """
        return self.completed_quests

    def rotate_location_quests(self, location_id, location_name, location_type, current_turn, player_level=1):
        """
        Обновить квесты в локации если прошло достаточно времени
        Активные квесты не удаляются

        Args:
            location_id: ID локации
            location_name: Название локации
            location_type: Тип локации (для генерации уникальных квестов)
            current_turn: Текущий игровой ход
            player_level: Уровень игрока

        Returns:
            bool: True если квесты были обновлены
        """
        from .generators.location import generate_quests_for_location
        from .factories import get_unique_quest_for_location

        # Проверяем нужно ли обновлять квесты
        last_update_turn = self.location_quest_turn.get(location_id, 0)
        turns_since_update = current_turn - last_update_turn

        if turns_since_update < self.QUEST_ROTATION_TURNS:
            return False

        # Сохраняем ID активных квестов из этой локации
        active_quest_ids = {q.quest_id for q in self.active_quests if q.location_id == location_id}

        # Удаляем старые НЕ активные квесты из локации
        if location_id in self.location_quests:
            # Оставляем только активные квесты
            self.location_quests[location_id] = [
                q for q in self.location_quests[location_id]
                if q.quest_id in active_quest_ids
            ]
        else:
            self.location_quests[location_id] = []

        # Генерируем новые квесты
        # Сначала пытаемся добавить уникальный квест
        unique_quest = get_unique_quest_for_location(location_type, location_name)
        if unique_quest:
            unique_quest.location_id = location_id
            self.location_quests[location_id].append(unique_quest)

        # Затем генерируем обычные квесты
        num_quests = 3 if not unique_quest else 2
        new_quests = generate_quests_for_location(
            location_name, location_id, player_level, count=num_quests, location_type=location_type
        )

        for quest in new_quests:
            self.location_quests[location_id].append(quest)

        # Обновляем ход последнего обновления
        self.location_quest_turn[location_id] = current_turn

        return True

    def check_and_rotate_all_quests(self, game_map, current_turn, player_level=1):
        """
        Проверить и обновить квесты во всех локациях

        Args:
            game_map: Игровая карта
            current_turn: Текущий игровой ход
            player_level: Уровень игрока

        Returns:
            list: Список названий локаций где квесты были обновлены
        """
        from game.constants import LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL

        updated_locations = []

        # Проходим по всем локациям на карте
        for location in game_map.locations:
            # Обновляем квесты только в городах, деревнях и академии магии
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL]:
                location_id = f"{location.x}_{location.y}"

                if self.rotate_location_quests(
                    location_id,
                    location.name,
                    location.location_type,
                    current_turn,
                    player_level
                ):
                    updated_locations.append(location.name)

        return updated_locations


class AchievementManager:
    """Менеджер достижений с визуальным отображением и наградами"""

    def __init__(self):
        """Инициализация менеджера достижений"""
        self.achievements = []
        self.pending_rewards = []  # Невостребованные награды
        self._setup_achievements()

    def _setup_achievements(self):
        """Настроить список достижений с наградами"""

        # ===== БОЕВЫЕ ДОСТИЖЕНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="first_blood",
            name="Первая кровь",
            description="Убейте первого врага",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 1,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 50, 'gold': 25},
            icon="⚔"
        ))

        self.achievements.append(Achievement(
            achievement_id="slayer_10",
            name="Убийца",
            description="Убейте 10 врагов",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 10,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 100, 'gold': 50},
            icon="⚔"
        ))

        self.achievements.append(Achievement(
            achievement_id="slayer_50",
            name="Воин",
            description="Убейте 50 врагов",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 50,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 300, 'gold': 150},
            icon="⚔"
        ))

        self.achievements.append(Achievement(
            achievement_id="slayer_100",
            name="Ветеран боёв",
            description="Убейте 100 врагов",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 100,
            rarity=AchievementRarity.RARE,
            rewards={'exp': 500, 'gold': 300},
            icon="⚔"
        ))

        self.achievements.append(Achievement(
            achievement_id="slayer_500",
            name="Легенда поля боя",
            description="Убейте 500 врагов",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 500,
            rarity=AchievementRarity.LEGENDARY,
            rewards={'exp': 2000, 'gold': 1000},
            icon="⚔"
        ))

        # ===== ОХОТНИЧЬИ ДОСТИЖЕНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="wolf_hunter",
            name="Охотник на волков",
            description="Убейте 10 волков",
            condition_func=lambda p: hasattr(p, 'wolves_killed') and p.wolves_killed >= 10,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 100, 'gold': 75},
            icon="🐺"
        ))

        self.achievements.append(Achievement(
            achievement_id="bear_hunter",
            name="Охотник на медведей",
            description="Убейте 5 медведей",
            condition_func=lambda p: hasattr(p, 'bears_killed') and p.bears_killed >= 5,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 200, 'gold': 150},
            icon="🐻"
        ))

        self.achievements.append(Achievement(
            achievement_id="master_hunter",
            name="Мастер охоты",
            description="Убейте 25 волков и 15 медведей",
            condition_func=lambda p: (hasattr(p, 'wolves_killed') and p.wolves_killed >= 25 and
                                     hasattr(p, 'bears_killed') and p.bears_killed >= 15),
            rarity=AchievementRarity.EPIC,
            rewards={'exp': 800, 'gold': 500},
            icon="🏹"
        ))

        # ===== ДОСТИЖЕНИЯ УРОВНЯ =====

        self.achievements.append(Achievement(
            achievement_id="level_10",
            name="Начинающий герой",
            description="Достигните 10 уровня",
            condition_func=lambda p: p.level >= 10,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 150, 'gold': 100},
            icon="📈"
        ))

        self.achievements.append(Achievement(
            achievement_id="level_20",
            name="Ветеран",
            description="Достигните 20 уровня",
            condition_func=lambda p: p.level >= 20,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 400, 'gold': 250},
            icon="📈"
        ))

        self.achievements.append(Achievement(
            achievement_id="level_30",
            name="Эксперт",
            description="Достигните 30 уровня",
            condition_func=lambda p: p.level >= 30,
            rarity=AchievementRarity.RARE,
            rewards={'exp': 800, 'gold': 500},
            icon="📈"
        ))

        self.achievements.append(Achievement(
            achievement_id="level_50",
            name="Легенда",
            description="Достигните 50 уровня",
            condition_func=lambda p: p.level >= 50,
            rarity=AchievementRarity.LEGENDARY,
            rewards={'exp': 2000, 'gold': 1500},
            icon="👑"
        ))

        # ===== ЭКОНОМИЧЕСКИЕ ДОСТИЖЕНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="rich_100",
            name="Торговец",
            description="Накопите 100 золота",
            condition_func=lambda p: p.inventory.gold >= 100,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 50, 'gold': 25},
            icon="💰"
        ))

        self.achievements.append(Achievement(
            achievement_id="rich_500",
            name="Предприниматель",
            description="Накопите 500 золота",
            condition_func=lambda p: p.inventory.gold >= 500,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 150, 'gold': 75},
            icon="💰"
        ))

        self.achievements.append(Achievement(
            achievement_id="rich_1000",
            name="Богач",
            description="Накопите 1000 золота",
            condition_func=lambda p: p.inventory.gold >= 1000,
            rarity=AchievementRarity.RARE,
            rewards={'exp': 300, 'gold': 150},
            icon="💰"
        ))

        self.achievements.append(Achievement(
            achievement_id="rich_5000",
            name="Магнат",
            description="Накопите 5000 золота",
            condition_func=lambda p: p.inventory.gold >= 5000,
            rarity=AchievementRarity.EPIC,
            rewards={'exp': 600, 'gold': 300},
            icon="💎"
        ))

        # ===== КОЛЛЕКЦИОННЫЕ ДОСТИЖЕНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="collector_10",
            name="Собиратель",
            description="Соберите 10 различных предметов",
            condition_func=lambda p: len(p.inventory.get_all_items()) >= 10,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 75, 'gold': 50},
            icon="📦"
        ))

        self.achievements.append(Achievement(
            achievement_id="collector_50",
            name="Коллекционер",
            description="Соберите 50 различных предметов",
            condition_func=lambda p: len(p.inventory.get_all_items()) >= 50,
            rarity=AchievementRarity.RARE,
            rewards={'exp': 400, 'gold': 250},
            icon="📦",
            hidden=True
        ))

        # ===== ДОСТИЖЕНИЯ ИССЛЕДОВАНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="explorer_3",
            name="Путешественник",
            description="Посетите 3 разных типа локаций",
            condition_func=lambda p: hasattr(p, 'visited_location_types') and
                                    len(p.visited_location_types) >= 3,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 100, 'gold': 50},
            icon="🗺"
        ))

        self.achievements.append(Achievement(
            achievement_id="explorer_5",
            name="Исследователь",
            description="Посетите 5 разных типов локаций",
            condition_func=lambda p: hasattr(p, 'visited_location_types') and
                                    len(p.visited_location_types) >= 5,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 250, 'gold': 150},
            icon="🗺"
        ))

        # ===== КВЕСТОВЫЕ ДОСТИЖЕНИЯ =====

        self.achievements.append(Achievement(
            achievement_id="quest_1",
            name="Помощник",
            description="Выполните первый квест",
            condition_func=lambda p: hasattr(p, 'quests_completed') and p.quests_completed >= 1,
            rarity=AchievementRarity.COMMON,
            rewards={'exp': 50, 'gold': 30},
            icon="📜"
        ))

        self.achievements.append(Achievement(
            achievement_id="quest_10",
            name="Доброволец",
            description="Выполните 10 квестов",
            condition_func=lambda p: hasattr(p, 'quests_completed') and p.quests_completed >= 10,
            rarity=AchievementRarity.UNCOMMON,
            rewards={'exp': 200, 'gold': 150},
            icon="📜"
        ))

        self.achievements.append(Achievement(
            achievement_id="quest_50",
            name="Герой королевства",
            description="Выполните 50 квестов",
            condition_func=lambda p: hasattr(p, 'quests_completed') and p.quests_completed >= 50,
            rarity=AchievementRarity.EPIC,
            rewards={'exp': 1000, 'gold': 750},
            icon="🎖"
        ))

    def check_achievements(self, player):
        """
        Проверить все достижения для игрока

        Args:
            player: Игрок для проверки

        Returns:
            list: Список новых разблокированных достижений
        """
        unlocked = []
        for achievement in self.achievements:
            if achievement.check(player):
                unlocked.append(achievement)
                self.pending_rewards.append(achievement)

        return unlocked

    def claim_all_rewards(self, player):
        """
        Получить награды за все невостребованные достижения

        Args:
            player: Игрок

        Returns:
            list: Список сообщений о полученных наградах
        """
        all_messages = []
        for achievement in self.pending_rewards[:]:
            messages = achievement.claim_rewards(player)
            if messages:
                all_messages.append(f"[{achievement.name}]: " + ", ".join(messages))
                self.pending_rewards.remove(achievement)
        return all_messages

    def get_unclaimed_rewards_count(self):
        """Получить количество невостребованных наград"""
        return len([a for a in self.achievements if a.unlocked and not a.reward_claimed])

    def get_unlocked_achievements(self):
        """
        Получить список разблокированных достижений

        Returns:
            list: Список разблокированных достижений
        """
        return [a for a in self.achievements if a.unlocked]

    def get_locked_achievements(self):
        """
        Получить список заблокированных достижений

        Returns:
            list: Список заблокированных (не скрытых) достижений
        """
        return [a for a in self.achievements if not a.unlocked and not a.hidden]

    def get_progress_percentage(self):
        """
        Получить процент прогресса достижений

        Returns:
            float: Процент прогресса (0-100)
        """
        total = len(self.achievements)
        unlocked = len(self.get_unlocked_achievements())
        return (unlocked / total * 100) if total > 0 else 0

    def get_achievements_by_rarity(self, rarity):
        """Получить достижения по редкости"""
        return [a for a in self.achievements if a.rarity == rarity]

    def get_display_data(self):
        """
        Получить данные для отображения в UI

        Returns:
            dict: Данные для отображения
        """
        return {
            'unlocked': [a.get_display_info() for a in self.get_unlocked_achievements()],
            'locked': [a.get_display_info() for a in self.get_locked_achievements()],
            'progress': self.get_progress_percentage(),
            'total': len(self.achievements),
            'completed': len(self.get_unlocked_achievements()),
            'unclaimed_rewards': self.get_unclaimed_rewards_count()
        }
