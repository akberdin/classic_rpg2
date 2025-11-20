"""
Система квестов и достижений
"""
from enum import Enum
import random


class QuestStatus(Enum):
    """Статусы квеста"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    READY_TO_TURN_IN = "ready_to_turn_in"


class QuestType(Enum):
    """Типы квестов"""
    GATHER_RESOURCE = "gather_resource"  # Собрать ресурсы
    KILL_ENEMIES = "kill_enemies"  # Убить врагов
    STORY = "story"  # Сюжетные квесты


class QuestDifficulty(Enum):
    """Сложность квеста"""
    EASY = ("easy", "Легкий", 1.0)
    MEDIUM = ("medium", "Средний", 1.5)
    HARD = ("hard", "Сложный", 2.0)
    VERY_HARD = ("very_hard", "Очень сложный", 3.0)

    def __init__(self, value, display_name, reward_multiplier):
        self._value_ = value
        self.display_name = display_name
        self.reward_multiplier = reward_multiplier


class QuestObjective:
    """Цель квеста"""

    def __init__(self, description, required_count=1):
        """
        Инициализация цели квеста

        Args:
            description: Описание цели
            required_count: Требуемое количество
        """
        self.description = description
        self.required_count = required_count
        self.current_count = 0
        self.completed = False

    def progress(self, amount=1):
        """
        Продвинуть прогресс цели

        Args:
            amount: Количество для добавления

        Returns:
            bool: True если цель завершена
        """
        if self.completed:
            return True

        self.current_count += amount
        if self.current_count >= self.required_count:
            self.current_count = self.required_count
            self.completed = True

        return self.completed

    def is_completed(self):
        """
        Проверить, завершена ли цель

        Returns:
            bool: True если завершена
        """
        return self.completed

    def get_progress_string(self):
        """
        Получить строку прогресса

        Returns:
            str: Строка вида "описание (текущее/требуемое)"
        """
        status = "[✓]" if self.completed else "[ ]"
        return f"{status} {self.description} ({self.current_count}/{self.required_count})"


class Quest:
    """Базовый класс квеста"""

    def __init__(self, quest_id, name, description, objectives, rewards,
                 quest_type=QuestType.STORY, difficulty=QuestDifficulty.EASY,
                 location_id=None, giver_location=None):
        """
        Инициализация квеста

        Args:
            quest_id: Уникальный ID квеста
            name: Название квеста
            description: Описание квеста
            objectives: Список целей квеста (QuestObjective)
            rewards: Словарь наград {'exp': int, 'gold': int, 'items': []}
            quest_type: Тип квеста (QuestType)
            difficulty: Сложность квеста (QuestDifficulty)
            location_id: ID локации для сдачи квеста
            giver_location: Название локации, где был получен квест
        """
        self.quest_id = quest_id
        self.name = name
        self.description = description
        self.objectives = objectives
        self.rewards = rewards
        self.quest_type = quest_type
        self.difficulty = difficulty
        self.location_id = location_id
        self.giver_location = giver_location
        self.status = QuestStatus.NOT_STARTED

        # Данные для отслеживания прогресса
        self.target_item = None  # Для квестов на сбор ресурсов
        self.target_enemy = None  # Для квестов на убийство

    def start(self):
        """Начать квест"""
        if self.status == QuestStatus.NOT_STARTED:
            self.status = QuestStatus.IN_PROGRESS
            return True
        return False

    def check_completion(self):
        """
        Проверить, завершены ли все цели

        Returns:
            bool: True если квест готов к сдаче
        """
        if self.status != QuestStatus.IN_PROGRESS:
            return False

        # Проверяем все цели
        all_completed = all(obj.is_completed() for obj in self.objectives)

        if all_completed:
            self.status = QuestStatus.READY_TO_TURN_IN

        return all_completed

    def is_ready_to_turn_in(self):
        """
        Проверить, готов ли квест к сдаче

        Returns:
            bool: True если готов к сдаче
        """
        return self.status == QuestStatus.READY_TO_TURN_IN

    def is_completed(self):
        """
        Проверить, завершен ли квест

        Returns:
            bool: True если завершен
        """
        return self.status == QuestStatus.COMPLETED

    def is_in_progress(self):
        """
        Проверить, в процессе ли квест

        Returns:
            bool: True если в процессе
        """
        return self.status == QuestStatus.IN_PROGRESS

    def get_progress_string(self):
        """
        Получить строку прогресса квеста

        Returns:
            str: Многострочная строка с прогрессом всех целей
        """
        difficulty_str = f" [{self.difficulty.display_name}]" if hasattr(self.difficulty, 'display_name') else ""
        lines = [f"Квест: {self.name}{difficulty_str}", f"  {self.description}", "  Цели:"]
        for obj in self.objectives:
            lines.append(f"    {obj.get_progress_string()}")

        # Показать награды
        rewards_str = []
        if 'exp' in self.rewards and self.rewards['exp'] > 0:
            rewards_str.append(f"{self.rewards['exp']} опыта")
        if 'gold' in self.rewards and self.rewards['gold'] > 0:
            rewards_str.append(f"{self.rewards['gold']} золота")
        if rewards_str:
            lines.append(f"  Награда: {', '.join(rewards_str)}")

        # Место сдачи
        if self.giver_location:
            lines.append(f"  Сдать в: {self.giver_location}")

        return "\n".join(lines)

    def claim_rewards(self, player):
        """
        Получить награды за квест

        Args:
            player: Игрок, получающий награды

        Returns:
            list: Список сообщений о полученных наградах
        """
        if not self.is_ready_to_turn_in() and not self.is_completed():
            return []

        messages = []

        # Опыт
        if 'exp' in self.rewards and self.rewards['exp'] > 0:
            player.add_experience(self.rewards['exp'])
            messages.append(f"Получено {self.rewards['exp']} опыта")

        # Золото
        if 'gold' in self.rewards and self.rewards['gold'] > 0:
            player.inventory.add_gold(self.rewards['gold'])
            messages.append(f"Получено {self.rewards['gold']} золота")

        # Предметы
        if 'items' in self.rewards:
            for item, quantity in self.rewards['items']:
                if player.inventory.add_item(item, quantity):
                    messages.append(f"Получено: {item.name} x{quantity}")
                else:
                    messages.append(f"Инвентарь полон! Не удалось получить {item.name}")

        # Устанавливаем статус завершённого квеста
        self.status = QuestStatus.COMPLETED

        return messages


class Achievement:
    """Достижение"""

    def __init__(self, achievement_id, name, description, condition_func, hidden=False):
        """
        Инициализация достижения

        Args:
            achievement_id: Уникальный ID достижения
            name: Название достижения
            description: Описание достижения
            condition_func: Функция проверки условия получения
            hidden: Скрытое ли достижение
        """
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.condition_func = condition_func
        self.hidden = hidden
        self.unlocked = False
        self.unlock_time = None

    def check(self, player):
        """
        Проверить условие получения достижения

        Args:
            player: Игрок для проверки

        Returns:
            bool: True если достижение разблокировано
        """
        if self.unlocked:
            return False

        if self.condition_func(player):
            self.unlocked = True
            import time
            self.unlock_time = time.time()
            return True

        return False


class QuestManager:
    """Менеджер квестов"""

    MAX_ACTIVE_QUESTS = 5  # Максимум активных квестов
    QUEST_ROTATION_DAYS = 5  # Квесты обновляются раз в 5 дней

    def __init__(self):
        """Инициализация менеджера квестов"""
        self.available_quests = []  # Доступные квесты
        self.active_quests = []     # Активные квесты
        self.completed_quests = []  # Завершенные квесты
        self.location_quests = {}   # Квесты по локациям: {location_id: [quests]}
        self.location_quest_day = {}  # День последнего обновления квестов: {location_id: day}

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
            if quest.is_ready_to_turn_in():
                if location_id is None or quest.location_id == location_id:
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
            enemy_type: Тип убитого врага ('bandit', 'undead', 'necromancer')

        Returns:
            list: Список сообщений о прогрессе
        """
        messages = []
        # Словарь для поиска врагов по описанию цели
        enemy_keywords = {
            'bandit': ['бандит', 'разбойник'],
            'undead': ['нежить', 'мертв', 'зомби', 'скелет'],
            'necromancer': ['некромант', 'темный маг']
        }

        for quest in self.active_quests:
            if quest.quest_type == QuestType.KILL_ENEMIES:
                # Проверяем основной target_enemy
                if quest.target_enemy == enemy_type:
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
            'wood': ['древесин', 'дерево'],
            'magic_crystal': ['магическ', 'кристалл'],
            'artifact_fragment': ['артефакт', 'фрагмент'],
            'ancient_coin': ['древн', 'монет'],
            'old_scroll': ['свиток', 'старый']
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
        # Словарь соответствий ключей и отображаемых имен
        key_to_name = {
            'copper_ore': 'Медная руда',
            'iron_ore': 'Железная руда',
            'silver_ore': 'Серебряная руда',
            'gold_ore': 'Золотая руда',
            'mithril_ore': 'Мифриловая руда',
            'wood': 'Древесина',
            'ancient_coin': 'Древняя монета',
            'artifact_fragment': 'Фрагмент артефакта',
            'magic_crystal': 'Магический кристалл',
            'old_scroll': 'Старый свиток',
        }

        item_name = key_to_name.get(item_key)
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
        messages = []
        for quest in self.active_quests:
            if quest.quest_type == QuestType.GATHER_RESOURCE:
                if quest.target_item and quest.objectives:
                    current_count = self._get_item_count_in_inventory(player, quest.target_item)
                    old_count = quest.objectives[0].current_count
                    quest.objectives[0].current_count = min(current_count, quest.objectives[0].required_count)
                    quest.objectives[0].completed = quest.objectives[0].current_count >= quest.objectives[0].required_count

                    quest.check_completion()

                    if quest.is_ready_to_turn_in() and old_count < quest.objectives[0].required_count:
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

    def rotate_location_quests(self, location_id, location_name, location_type, current_day, player_level=1):
        """
        Обновить квесты в локации если прошло достаточно времени
        Активные квесты не удаляются

        Args:
            location_id: ID локации
            location_name: Название локации
            location_type: Тип локации (для генерации уникальных квестов)
            current_day: Текущий игровой день
            player_level: Уровень игрока

        Returns:
            bool: True если квесты были обновлены
        """
        # Проверяем нужно ли обновлять квесты
        last_update_day = self.location_quest_day.get(location_id, 0)
        days_since_update = current_day - last_update_day

        if days_since_update < self.QUEST_ROTATION_DAYS:
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
        new_quests = QuestGenerator.generate_quests_for_location(
            location_name, location_id, player_level, count=num_quests
        )

        for quest in new_quests:
            self.location_quests[location_id].append(quest)

        # Обновляем день последнего обновления
        self.location_quest_day[location_id] = current_day

        return True

    def check_and_rotate_all_quests(self, game_map, current_day, player_level=1):
        """
        Проверить и обновить квесты во всех локациях

        Args:
            game_map: Игровая карта
            current_day: Текущий игровой день
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
                    current_day,
                    player_level
                ):
                    updated_locations.append(location.name)

        return updated_locations


def create_alchemist_quests(npc_name):
    """
    Создать квесты для алхимика

    Args:
        npc_name: Имя алхимика (для giver_location)

    Returns:
        list: Список квестов
    """
    quests = []

    # Квест на сбор ингредиентов
    quests.append(Quest(
        quest_id=f"alchemist_gather_{random.randint(1000, 9999)}",
        name="Сбор ингредиентов",
        description="Алхимику нужны магические кристаллы для зелий.",
        objectives=[
            QuestObjective("Собрать магические кристаллы", 3)
        ],
        rewards={"experience": 150, "gold": 100, "items": ["health_potion", "mana_potion"]},
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    ))

    # Квест на уничтожение нежити
    quests.append(Quest(
        quest_id=f"alchemist_undead_{random.randint(1000, 9999)}",
        name="Очищение руин",
        description="Нежить в руинах мешает собирать редкие ингредиенты.",
        objectives=[
            QuestObjective("Уничтожить нежить", 5)
        ],
        rewards={"experience": 200, "gold": 150},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.HARD,
        giver_location=npc_name
    ))

    return quests


def create_hunter_quests(npc_name):
    """
    Создать квесты для охотника

    Args:
        npc_name: Имя охотника (для giver_location)

    Returns:
        list: Список квестов
    """
    quests = []

    # Квест на уничтожение бандитов
    quests.append(Quest(
        quest_id=f"hunter_bandits_{random.randint(1000, 9999)}",
        name="Охота на бандитов",
        description="Бандиты угрожают путникам на дорогах. Необходимо их остановить.",
        objectives=[
            QuestObjective("Уничтожить бандитов", 5)
        ],
        rewards={"experience": 180, "gold": 120},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    ))

    # Квест на охоту на элитных врагов
    quests.append(Quest(
        quest_id=f"hunter_elite_{random.randint(1000, 9999)}",
        name="Опасная охота",
        description="В округе появился опасный главарь банды. Нужен опытный охотник.",
        objectives=[
            QuestObjective("Уничтожить главаря банды", 1)
        ],
        rewards={"experience": 300, "gold": 250},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location=npc_name
    ))

    return quests


class AchievementManager:
    """Менеджер достижений"""

    def __init__(self):
        """Инициализация менеджера достижений"""
        self.achievements = []
        self._setup_achievements()

    def _setup_achievements(self):
        """Настроить список достижений"""
        # Базовые достижения
        self.achievements.append(Achievement(
            achievement_id="first_blood",
            name="Первая кровь",
            description="Убейте первого врага",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 1
        ))

        self.achievements.append(Achievement(
            achievement_id="slayer",
            name="Убийца",
            description="Убейте 10 врагов",
            condition_func=lambda p: hasattr(p, 'enemies_killed') and p.enemies_killed >= 10
        ))

        self.achievements.append(Achievement(
            achievement_id="veteran",
            name="Ветеран",
            description="Достигните 20 уровня",
            condition_func=lambda p: p.level >= 20
        ))

        self.achievements.append(Achievement(
            achievement_id="expert",
            name="Эксперт",
            description="Достигните 30 уровня",
            condition_func=lambda p: p.level >= 30
        ))

        self.achievements.append(Achievement(
            achievement_id="rich",
            name="Богач",
            description="Накопите 1000 золота",
            condition_func=lambda p: p.inventory.gold >= 1000
        ))

        self.achievements.append(Achievement(
            achievement_id="collector",
            name="Коллекционер",
            description="Соберите 50 различных предметов",
            condition_func=lambda p: len(p.inventory.get_all_items()) >= 50,
            hidden=True
        ))

        self.achievements.append(Achievement(
            achievement_id="explorer",
            name="Исследователь",
            description="Посетите все типы локаций",
            condition_func=lambda p: hasattr(p, 'visited_location_types') and
                                    len(p.visited_location_types) >= 5
        ))

    def check_achievements(self, player):
        """
        Проверить все достижения для игрока

        Args:
            player: Игрок для проверки

        Returns:
            list: Список разблокированных достижений
        """
        unlocked = []
        for achievement in self.achievements:
            if achievement.check(player):
                unlocked.append(achievement)

        return unlocked

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


def create_starter_quests():
    """
    Создать стартовые квесты

    Returns:
        list: Список квестов
    """
    quests = []

    # Квест 1: Первые шаги
    objectives = [
        QuestObjective("Убейте 3 врагов", required_count=3),
        QuestObjective("Достигните 3 уровня", required_count=1),
    ]
    rewards = {'exp': 100, 'gold': 50}
    quest1 = Quest(
        quest_id="first_steps",
        name="Первые шаги",
        description="Изучите основы боя и прокачки",
        objectives=objectives,
        rewards=rewards
    )
    quests.append(quest1)

    # Квест 2: Охотник за сокровищами
    objectives = [
        QuestObjective("Соберите ресурсы с 5 локаций", required_count=5),
    ]
    rewards = {'exp': 150, 'gold': 100}
    quest2 = Quest(
        quest_id="treasure_hunter",
        name="Охотник за сокровищами",
        description="Исследуйте локации и собирайте ресурсы",
        objectives=objectives,
        rewards=rewards
    )
    quests.append(quest2)

    # Квест 3: Торговец
    objectives = [
        QuestObjective("Продайте 10 предметов торговцам", required_count=10),
    ]
    rewards = {'exp': 200, 'gold': 150}
    quest3 = Quest(
        quest_id="merchant",
        name="Начинающий торговец",
        description="Научитесь торговать с NPC",
        objectives=objectives,
        rewards=rewards
    )
    quests.append(quest3)

    return quests


class QuestGenerator:
    """Генератор динамических квестов для городов"""

    # Шаблоны квестов на сбор ресурсов
    GATHER_QUESTS = {
        'copper_ore': {
            'name': 'Медная руда',
            'display_name': 'Медная руда',
            'quest_names': [
                'Добыча меди',
                'Медные запасы',
                'Заказ на медь'
            ],
            'descriptions': [
                'Городу нужна медная руда для кузнецов.',
                'Местные ремесленники просят добыть медную руду.',
                'Торговая гильдия заказала партию медной руды.'
            ]
        },
        'iron_ore': {
            'name': 'Железная руда',
            'display_name': 'Железная руда',
            'quest_names': [
                'Добыча железа',
                'Железные запасы',
                'Стальное задание'
            ],
            'descriptions': [
                'Кузнецы города нуждаются в железной руде.',
                'Городская стража заказала железо для нового оружия.',
                'Ремесленная гильдия просит добыть железную руду.'
            ]
        },
        'silver_ore': {
            'name': 'Серебряная руда',
            'display_name': 'Серебряная руда',
            'quest_names': [
                'Серебряная жила',
                'Благородный металл',
                'Серебряный заказ'
            ],
            'descriptions': [
                'Ювелиры города ищут серебряную руду.',
                'Магическая академия нуждается в серебре.',
                'Храм заказал серебро для священных предметов.'
            ]
        },
        'gold_ore': {
            'name': 'Золотая руда',
            'display_name': 'Золотая руда',
            'quest_names': [
                'Золотая лихорадка',
                'Драгоценная добыча',
                'Королевский заказ'
            ],
            'descriptions': [
                'Казначейство города нуждается в золоте.',
                'Ювелирная гильдия просит добыть золотую руду.',
                'Знатный лорд заказал золото для украшений.'
            ]
        },
        'wood': {
            'name': 'Древесина',
            'display_name': 'Древесина',
            'quest_names': [
                'Заготовка древесины',
                'Лесной промысел',
                'Строительные материалы'
            ],
            'descriptions': [
                'Городу нужна древесина для строительства.',
                'Плотники просят заготовить древесину.',
                'Требуется древесина для ремонта стен.'
            ]
        },
        'ancient_coin': {
            'name': 'Древняя монета',
            'display_name': 'Древняя монета',
            'quest_names': [
                'Поиск древностей',
                'Нумизматика',
                'Древние сокровища'
            ],
            'descriptions': [
                'Коллекционер ищет древние монеты из руин.',
                'Музей города просит найти исторические артефакты.',
                'Историк изучает древние монеты.'
            ]
        },
        'artifact_fragment': {
            'name': 'Фрагмент артефакта',
            'display_name': 'Фрагмент артефакта',
            'quest_names': [
                'Осколки прошлого',
                'Поиск артефактов',
                'Магические фрагменты'
            ],
            'descriptions': [
                'Маги ищут фрагменты древних артефактов.',
                'Археолог просит найти осколки в руинах.',
                'Магическая академия нуждается в артефактах.'
            ]
        },
        'magic_crystal': {
            'name': 'Магический кристалл',
            'display_name': 'Магический кристалл',
            'quest_names': [
                'Магические кристаллы',
                'Поиск источника силы',
                'Кристальная миссия'
            ],
            'descriptions': [
                'Маги города нуждаются в магических кристаллах.',
                'Алхимики просят найти источники магической энергии.',
                'Магическая башня заказала кристаллы.'
            ]
        }
    }

    # Шаблоны квестов на убийство врагов
    KILL_QUESTS = {
        'bandit': {
            'name': 'Бандит',
            'display_name': 'Бандиты',
            'quest_names': [
                'Охота на бандитов',
                'Зачистка дорог',
                'Возмездие разбойникам'
            ],
            'descriptions': [
                'Бандиты терроризируют окрестности города.',
                'Караваны страдают от нападений разбойников.',
                'Стража просит помочь в борьбе с бандитами.'
            ]
        },
        'undead': {
            'name': 'Нежить',
            'display_name': 'Нежить',
            'quest_names': [
                'Очищение от нежити',
                'Упокоение мертвых',
                'Святая миссия'
            ],
            'descriptions': [
                'Нежить из руин угрожает путникам.',
                'Священники просят очистить руины от нечисти.',
                'Жители жалуются на появление нежити.'
            ]
        }
    }

    @staticmethod
    def generate_quest_for_location(location_name, location_id, player_level=1):
        """
        Сгенерировать квест для локации

        Args:
            location_name: Название локации
            location_id: ID локации
            player_level: Уровень игрока для масштабирования

        Returns:
            Quest: Сгенерированный квест
        """
        # Выбираем тип квеста случайно
        quest_type = random.choice([QuestType.GATHER_RESOURCE, QuestType.KILL_ENEMIES])

        if quest_type == QuestType.GATHER_RESOURCE:
            return QuestGenerator._generate_gather_quest(location_name, location_id, player_level)
        else:
            return QuestGenerator._generate_kill_quest(location_name, location_id, player_level)

    @staticmethod
    def _generate_gather_quest(location_name, location_id, player_level):
        """Сгенерировать квест на сбор ресурсов"""
        # Выбираем ресурс случайно
        resource_key = random.choice(list(QuestGenerator.GATHER_QUESTS.keys()))
        resource_data = QuestGenerator.GATHER_QUESTS[resource_key]

        # Определяем сложность на основе ресурса
        if resource_key in ['copper_ore', 'wood']:
            difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])
        elif resource_key in ['iron_ore', 'ancient_coin']:
            difficulty = random.choice([QuestDifficulty.MEDIUM, QuestDifficulty.HARD])
        elif resource_key in ['silver_ore', 'artifact_fragment']:
            difficulty = random.choice([QuestDifficulty.MEDIUM, QuestDifficulty.HARD])
        else:  # gold_ore, magic_crystal
            difficulty = random.choice([QuestDifficulty.HARD, QuestDifficulty.VERY_HARD])

        # Определяем количество на основе сложности
        base_amounts = {
            QuestDifficulty.EASY: (3, 5),
            QuestDifficulty.MEDIUM: (5, 8),
            QuestDifficulty.HARD: (8, 12),
            QuestDifficulty.VERY_HARD: (10, 15)
        }
        min_amount, max_amount = base_amounts[difficulty]
        required_amount = random.randint(min_amount, max_amount)

        # Рассчитываем награды
        base_exp = 50 + player_level * 10
        base_gold = 30 + player_level * 5

        exp_reward = int(base_exp * difficulty.reward_multiplier * (required_amount / 5))
        gold_reward = int(base_gold * difficulty.reward_multiplier * (required_amount / 5))

        # Создаем квест
        quest_name = random.choice(resource_data['quest_names'])
        description = random.choice(resource_data['descriptions'])
        quest_id = f"gather_{resource_key}_{location_id}_{random.randint(1000, 9999)}"

        objective = QuestObjective(
            f"Добыть {resource_data['display_name']} x{required_amount}",
            required_count=required_amount
        )

        quest = Quest(
            quest_id=quest_id,
            name=quest_name,
            description=description,
            objectives=[objective],
            rewards={'exp': exp_reward, 'gold': gold_reward},
            quest_type=QuestType.GATHER_RESOURCE,
            difficulty=difficulty,
            location_id=location_id,
            giver_location=location_name
        )
        quest.target_item = resource_key

        return quest

    @staticmethod
    def _generate_kill_quest(location_name, location_id, player_level):
        """Сгенерировать квест на убийство врагов"""
        # Выбираем тип врага случайно
        enemy_key = random.choice(list(QuestGenerator.KILL_QUESTS.keys()))
        enemy_data = QuestGenerator.KILL_QUESTS[enemy_key]

        # Определяем сложность случайно
        difficulty = random.choice([
            QuestDifficulty.EASY,
            QuestDifficulty.MEDIUM,
            QuestDifficulty.HARD,
            QuestDifficulty.VERY_HARD
        ])

        # Определяем количество на основе сложности
        base_amounts = {
            QuestDifficulty.EASY: (2, 4),
            QuestDifficulty.MEDIUM: (4, 6),
            QuestDifficulty.HARD: (6, 10),
            QuestDifficulty.VERY_HARD: (8, 15)
        }
        min_amount, max_amount = base_amounts[difficulty]
        required_amount = random.randint(min_amount, max_amount)

        # Рассчитываем награды (больше за убийства)
        base_exp = 80 + player_level * 15
        base_gold = 50 + player_level * 8

        exp_reward = int(base_exp * difficulty.reward_multiplier * (required_amount / 4))
        gold_reward = int(base_gold * difficulty.reward_multiplier * (required_amount / 4))

        # Создаем квест
        quest_name = random.choice(enemy_data['quest_names'])
        description = random.choice(enemy_data['descriptions'])
        quest_id = f"kill_{enemy_key}_{location_id}_{random.randint(1000, 9999)}"

        objective = QuestObjective(
            f"Убить {enemy_data['display_name']} x{required_amount}",
            required_count=required_amount
        )

        quest = Quest(
            quest_id=quest_id,
            name=quest_name,
            description=description,
            objectives=[objective],
            rewards={'exp': exp_reward, 'gold': gold_reward},
            quest_type=QuestType.KILL_ENEMIES,
            difficulty=difficulty,
            location_id=location_id,
            giver_location=location_name
        )
        quest.target_enemy = enemy_key

        return quest

    @staticmethod
    def generate_quests_for_location(location_name, location_id, player_level=1, count=3):
        """
        Сгенерировать несколько квестов для локации

        Args:
            location_name: Название локации
            location_id: ID локации
            player_level: Уровень игрока
            count: Количество квестов

        Returns:
            list: Список квестов
        """
        quests = []
        for _ in range(count):
            quest = QuestGenerator.generate_quest_for_location(
                location_name, location_id, player_level
            )
            quests.append(quest)
        return quests


def create_unique_quests():
    """
    Создать уникальные квесты с особыми наградами

    Returns:
        list: Список уникальных квестов
    """
    from game.inventory import PREDEFINED_ITEMS

    quests = []

    # ===== КВЕСТЫ АЛХИМИКА =====

    # Квест 1: Сбор редких ингредиентов
    objectives = [
        QuestObjective("Собрать магические кристаллы", required_count=5),
        QuestObjective("Собрать фрагменты артефактов", required_count=3),
    ]
    rewards = {
        'exp': 500,
        'gold': 300,
        'items': [
            (PREDEFINED_ITEMS["elixir_of_life"], 2),
            (PREDEFINED_ITEMS["elixir_of_power"], 3),
        ]
    }
    quest = Quest(
        quest_id="alchemist_rare_ingredients",
        name="Редкие ингредиенты",
        description="Алхимик ищет редкие компоненты для создания мощных эликсиров.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Алхимик"
    )
    quest.target_item = "magic_crystal"
    quests.append(quest)

    # Квест 2: Философский камень
    objectives = [
        QuestObjective("Найти осколки Философского Камня в руинах", required_count=1),
        QuestObjective("Собрать золотую руду", required_count=10),
        QuestObjective("Собрать серебряную руду", required_count=15),
    ]
    rewards = {
        'exp': 1000,
        'gold': 800,
        'items': [
            (PREDEFINED_ITEMS["alchemists_staff"], 1),
            (PREDEFINED_ITEMS["book_heal"], 1),
        ]
    }
    quest = Quest(
        quest_id="alchemist_philosophers_stone",
        name="Тайна Философского Камня",
        description="Помогите алхимику в поисках легендарного артефакта.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Алхимик"
    )
    quests.append(quest)

    # ===== КВЕСТЫ ОХОТНИКА =====

    # Квест 3: Охота на бандитов
    objectives = [
        QuestObjective("Уничтожить бандитов", required_count=10),
    ]
    rewards = {
        'exp': 600,
        'gold': 400,
        'items': [
            (PREDEFINED_ITEMS["hunters_bow"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_bandit_hunt",
        name="Чистка дорог",
        description="Охотник просит помочь очистить территорию от бандитов.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.HARD,
        giver_location="Охотник"
    )
    quest.target_enemy = "bandit"
    quests.append(quest)

    # Квест 4: Охота на нежить
    objectives = [
        QuestObjective("Уничтожить нежить в руинах", required_count=15),
    ]
    rewards = {
        'exp': 800,
        'gold': 500,
        'items': [
            (PREDEFINED_ITEMS["shadow_blade"], 1),
            (PREDEFINED_ITEMS["greater_health_potion"], 5),
        ]
    }
    quest = Quest(
        quest_id="hunter_undead_hunt",
        name="Очищение руин",
        description="Охотник поручает вам очистить древние руины от нежити.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник"
    )
    quest.target_enemy = "undead"
    quests.append(quest)

    # Квест 5: Мастер охоты
    objectives = [
        QuestObjective("Уничтожить бандитов", required_count=20),
        QuestObjective("Уничтожить нежить", required_count=20),
    ]
    rewards = {
        'exp': 1500,
        'gold': 1000,
        'items': [
            (PREDEFINED_ITEMS["book_power_strike"], 1),
            (PREDEFINED_ITEMS["book_battle_cry"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_master_hunt",
        name="Мастер Охоты",
        description="Докажите, что вы достойны звания Мастера Охоты.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник"
    )
    quests.append(quest)

    # ===== КВЕСТЫ НЕКРОМАНТА (для победы над ним) =====

    # Квест 6: Остановить некроманта
    objectives = [
        QuestObjective("Победить некроманта", required_count=1),
    ]
    rewards = {
        'exp': 2000,
        'gold': 1500,
        'items': [
            (PREDEFINED_ITEMS["book_fireball"], 1),
            (PREDEFINED_ITEMS["book_lightning"], 1),
        ]
    }
    quest = Quest(
        quest_id="stop_necromancer",
        name="Угроза из руин",
        description="Некромант угрожает живым. Остановите его!",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия"
    )
    quest.target_enemy = "necromancer"
    quests.append(quest)

    # ===== КВЕСТЫ НА СБОР =====

    # Квест 7: Богатство земли
    objectives = [
        QuestObjective("Собрать медную руду", required_count=20),
        QuestObjective("Собрать железную руду", required_count=15),
        QuestObjective("Собрать серебряную руду", required_count=10),
        QuestObjective("Собрать золотую руду", required_count=5),
    ]
    rewards = {
        'exp': 800,
        'gold': 1000,
        'items': [
            (PREDEFINED_ITEMS["book_regeneration"], 1),
        ]
    }
    quest = Quest(
        quest_id="mining_master",
        name="Богатство земли",
        description="Соберите руды всех типов для кузнецов города.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Город"
    )
    quests.append(quest)

    # Квест 8: Древние знания
    objectives = [
        QuestObjective("Собрать древние монеты", required_count=10),
        QuestObjective("Собрать фрагменты артефактов", required_count=5),
        QuestObjective("Собрать старые свитки", required_count=8),
    ]
    rewards = {
        'exp': 1200,
        'gold': 800,
        'items': [
            (PREDEFINED_ITEMS["book_magic_missile"], 1),
            (PREDEFINED_ITEMS["book_ice_bolt"], 1),
        ]
    }
    quest = Quest(
        quest_id="ancient_knowledge",
        name="Древние знания",
        description="Соберите артефакты из руин для исследований.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия"
    )
    quests.append(quest)

    return quests


def get_unique_quest_for_location(location_type, location_name):
    """
    Получить уникальный квест для типа локации с вероятностью

    Args:
        location_type: Тип локации (city, village, magic_school)
        location_name: Название локации для установки giver_location

    Returns:
        Quest или None: Уникальный квест или None если не повезло
    """
    import random
    from game.inventory import PREDEFINED_ITEMS
    from game.constants import LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL

    # Вероятность появления уникального квеста
    # Города: 30%, Деревни: 15%, Школа магов: 40%
    probabilities = {
        LOCATION_CITY: 0.30,
        LOCATION_VILLAGE: 0.15,
        LOCATION_MAGIC_SCHOOL: 0.40
    }

    probability = probabilities.get(location_type, 0)
    if random.random() > probability:
        return None

    # Пулы уникальных квестов для разных типов локаций
    city_quests = [
        # Квест кузнеца
        {
            'quest_id': f'blacksmith_order_{random.randint(1000, 9999)}',
            'name': 'Заказ кузнеца',
            'description': 'Кузнец ищет материалы для особого заказа.',
            'objectives': [
                QuestObjective("Собрать железную руду", required_count=10),
                QuestObjective("Собрать медную руду", required_count=8),
            ],
            'rewards': {
                'exp': 400,
                'gold': 350,
                'items': [(PREDEFINED_ITEMS["steel_sword"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.MEDIUM,
            'target_item': 'iron_ore'
        },
        # Квест главы города
        {
            'quest_id': f'mayor_protection_{random.randint(1000, 9999)}',
            'name': 'Защита торговых путей',
            'description': 'Глава города просит очистить окрестности от бандитов.',
            'objectives': [
                QuestObjective("Уничтожить бандитов", required_count=12),
            ],
            'rewards': {
                'exp': 600,
                'gold': 500,
                'items': [(PREDEFINED_ITEMS["greater_health_potion"], 3)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.HARD,
            'target_enemy': 'bandit'
        },
        # Квест торговца
        {
            'quest_id': f'merchant_collection_{random.randint(1000, 9999)}',
            'name': 'Ценные находки',
            'description': 'Торговец готов заплатить за редкие артефакты.',
            'objectives': [
                QuestObjective("Собрать древние монеты", required_count=8),
                QuestObjective("Собрать фрагменты артефактов", required_count=4),
            ],
            'rewards': {
                'exp': 500,
                'gold': 600,
                'items': [(PREDEFINED_ITEMS["elixir_of_power"], 2)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'ancient_coin'
        },
    ]

    village_quests = [
        # Квест старосты
        {
            'quest_id': f'elder_herbs_{random.randint(1000, 9999)}',
            'name': 'Лечебные травы',
            'description': 'Староста деревни просит помочь собрать лекарства.',
            'objectives': [
                QuestObjective("Собрать магические кристаллы", required_count=3),
            ],
            'rewards': {
                'exp': 250,
                'gold': 150,
                'items': [(PREDEFINED_ITEMS["health_potion"], 5)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.EASY,
            'target_item': 'magic_crystal'
        },
        # Квест охотника деревни
        {
            'quest_id': f'village_hunter_{random.randint(1000, 9999)}',
            'name': 'Помощь охотнику',
            'description': 'Местный охотник просит помочь с бандитами.',
            'objectives': [
                QuestObjective("Уничтожить бандитов", required_count=6),
            ],
            'rewards': {
                'exp': 300,
                'gold': 200,
                'items': [(PREDEFINED_ITEMS["hunters_bow"], 1)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.MEDIUM,
            'target_enemy': 'bandit'
        },
        # Квест шахтёра
        {
            'quest_id': f'village_miner_{random.randint(1000, 9999)}',
            'name': 'Руда для кузни',
            'description': 'Кузнец деревни нуждается в руде.',
            'objectives': [
                QuestObjective("Собрать медную руду", required_count=12),
            ],
            'rewards': {
                'exp': 200,
                'gold': 180,
                'items': [(PREDEFINED_ITEMS["mana_potion"], 3)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.EASY,
            'target_item': 'copper_ore'
        },
    ]

    magic_school_quests = [
        # Квест архимага
        {
            'quest_id': f'archmage_research_{random.randint(1000, 9999)}',
            'name': 'Исследование древних',
            'description': 'Архимаг изучает древние артефакты и нуждается в материалах.',
            'objectives': [
                QuestObjective("Собрать старые свитки", required_count=10),
                QuestObjective("Собрать фрагменты артефактов", required_count=6),
            ],
            'rewards': {
                'exp': 800,
                'gold': 600,
                'items': [(PREDEFINED_ITEMS["book_magic_missile"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'old_scroll'
        },
        # Квест мастера боевой магии
        {
            'quest_id': f'battle_mage_training_{random.randint(1000, 9999)}',
            'name': 'Боевая практика',
            'description': 'Мастер боевой магии предлагает испытание против нежити.',
            'objectives': [
                QuestObjective("Уничтожить нежить", required_count=15),
            ],
            'rewards': {
                'exp': 700,
                'gold': 400,
                'items': [(PREDEFINED_ITEMS["book_fireball"], 1)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.HARD,
            'target_enemy': 'undead'
        },
        # Квест хранителя знаний
        {
            'quest_id': f'lorekeeper_crystals_{random.randint(1000, 9999)}',
            'name': 'Магические кристаллы',
            'description': 'Хранитель знаний ищет кристаллы для магических исследований.',
            'objectives': [
                QuestObjective("Собрать магические кристаллы", required_count=8),
            ],
            'rewards': {
                'exp': 600,
                'gold': 500,
                'items': [(PREDEFINED_ITEMS["book_ice_bolt"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'magic_crystal'
        },
        # Квест на некроманта
        {
            'quest_id': f'necromancer_hunt_{random.randint(1000, 9999)}',
            'name': 'Угроза некромантии',
            'description': 'Академия просит остановить некроманта, угрожающего региону.',
            'objectives': [
                QuestObjective("Победить некроманта", required_count=1),
            ],
            'rewards': {
                'exp': 1500,
                'gold': 1000,
                'items': [
                    (PREDEFINED_ITEMS["book_lightning"], 1),
                    (PREDEFINED_ITEMS["elixir_of_life"], 2)
                ]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.VERY_HARD,
            'target_enemy': 'necromancer'
        },
    ]

    # Выбираем пул квестов по типу локации
    quest_pools = {
        LOCATION_CITY: city_quests,
        LOCATION_VILLAGE: village_quests,
        LOCATION_MAGIC_SCHOOL: magic_school_quests
    }

    quest_pool = quest_pools.get(location_type, [])
    if not quest_pool:
        return None

    # Выбираем случайный квест из пула
    quest_data = random.choice(quest_pool)

    # Создаём объект квеста
    quest = Quest(
        quest_id=quest_data['quest_id'],
        name=quest_data['name'],
        description=quest_data['description'],
        objectives=quest_data['objectives'],
        rewards=quest_data['rewards'],
        quest_type=quest_data['quest_type'],
        difficulty=quest_data['difficulty'],
        giver_location=location_name
    )

    # Устанавливаем target_item или target_enemy
    if 'target_item' in quest_data:
        quest.target_item = quest_data['target_item']
    if 'target_enemy' in quest_data:
        quest.target_enemy = quest_data['target_enemy']

    return quest


def create_alchemist_quests(location_name="Алхимик"):
    """
    Создать квесты для алхимика

    Args:
        location_name: Название локации для сдачи

    Returns:
        list: Список квестов алхимика
    """
    from game.inventory import PREDEFINED_ITEMS

    quests = []

    # Квест на сбор магических кристаллов
    objectives = [
        QuestObjective("Собрать магические кристаллы", required_count=3),
    ]
    rewards = {
        'exp': 300,
        'gold': 200,
        'items': [
            (PREDEFINED_ITEMS["health_potion"], 5),
            (PREDEFINED_ITEMS["mana_potion"], 3),
        ]
    }
    quest = Quest(
        quest_id=f"alchemist_crystals_{random.randint(1000, 9999)}",
        name="Магические компоненты",
        description="Алхимик нуждается в магических кристаллах для экспериментов.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=location_name
    )
    quest.target_item = "magic_crystal"
    quests.append(quest)

    return quests


def create_hunter_quests(location_name="Охотник"):
    """
    Создать квесты для охотника

    Args:
        location_name: Название локации для сдачи

    Returns:
        list: Список квестов охотника
    """
    from game.inventory import PREDEFINED_ITEMS

    quests = []

    # Квест на охоту на бандитов
    objectives = [
        QuestObjective("Уничтожить бандитов", required_count=5),
    ]
    rewards = {
        'exp': 400,
        'gold': 250,
        'items': [
            (PREDEFINED_ITEMS["stamina_potion"], 3),
        ]
    }
    quest = Quest(
        quest_id=f"hunter_bandits_{random.randint(1000, 9999)}",
        name="Разбойники на дорогах",
        description="Охотник просит помочь в борьбе с бандитами.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=location_name
    )
    quest.target_enemy = "bandit"
    quests.append(quest)

    # Квест на охоту на нежить
    objectives = [
        QuestObjective("Уничтожить нежить", required_count=5),
    ]
    rewards = {
        'exp': 450,
        'gold': 300,
        'items': [
            (PREDEFINED_ITEMS["greater_health_potion"], 2),
        ]
    }
    quest = Quest(
        quest_id=f"hunter_undead_{random.randint(1000, 9999)}",
        name="Нежить в руинах",
        description="Охотник поручает очистить руины от нежити.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=location_name
    )
    quest.target_enemy = "undead"
    quests.append(quest)

    return quests
