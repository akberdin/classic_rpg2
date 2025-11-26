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
    KILL_ANIMALS = "kill_animals"  # Убить животных
    STORY = "story"  # Сюжетные квесты
    UNIQUE = "unique"  # Уникальные квесты с особыми наградами


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
                 location_id=None, giver_location=None, is_unique=False, is_starter=False):
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
            is_unique: Уникальный квест с особыми наградами (красная рамка в UI)
            is_starter: Стартовый квест (автоматически назначается)
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
        self.is_unique = is_unique  # Уникальный квест (красная рамка)
        self.is_starter = is_starter  # Стартовый квест

        # Данные для отслеживания прогресса
        self.target_item = None  # Для квестов на сбор ресурсов
        self.target_enemy = None  # Для квестов на убийство
        self.target_animal = None  # Для квестов на убийство животных

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


class AchievementRarity(Enum):
    """Редкость достижения"""
    COMMON = ("Обычное", (180, 180, 180), 1.0)  # Серый
    UNCOMMON = ("Необычное", (100, 255, 100), 1.5)  # Зеленый
    RARE = ("Редкое", (100, 150, 255), 2.0)  # Синий
    EPIC = ("Эпическое", (180, 100, 255), 3.0)  # Фиолетовый
    LEGENDARY = ("Легендарное", (255, 170, 50), 5.0)  # Оранжевый

    def __init__(self, display_name, color, reward_multiplier):
        self.display_name = display_name
        self.color = color
        self.reward_multiplier = reward_multiplier


class Achievement:
    """Достижение с наградами и редкостью"""

    def __init__(self, achievement_id, name, description, condition_func, hidden=False,
                 rarity=None, rewards=None, icon=None):
        """
        Инициализация достижения

        Args:
            achievement_id: Уникальный ID достижения
            name: Название достижения
            description: Описание достижения
            condition_func: Функция проверки условия получения
            hidden: Скрытое ли достижение
            rarity: Редкость достижения (AchievementRarity)
            rewards: Награды {'exp': int, 'gold': int, 'items': []}
            icon: Иконка для отображения
        """
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.condition_func = condition_func
        self.hidden = hidden
        self.rarity = rarity or AchievementRarity.COMMON
        self.rewards = rewards or {}
        self.icon = icon or "★"
        self.unlocked = False
        self.unlock_time = None
        self.reward_claimed = False

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

    def claim_rewards(self, player):
        """
        Получить награды за достижение

        Args:
            player: Игрок

        Returns:
            list: Список сообщений о наградах
        """
        if not self.unlocked or self.reward_claimed:
            return []

        messages = []
        self.reward_claimed = True

        if 'exp' in self.rewards:
            exp = self.rewards['exp']
            player.add_experience(exp)
            messages.append(f"+{exp} опыта")

        if 'gold' in self.rewards:
            gold = self.rewards['gold']
            player.inventory.add_gold(gold)
            messages.append(f"+{gold} золота")

        if 'items' in self.rewards:
            for item, count in self.rewards['items']:
                if player.inventory.add_item(item, count):
                    messages.append(f"+{item.name} x{count}")

        return messages

    def get_display_info(self):
        """Получить информацию для отображения в UI"""
        return {
            'name': self.name,
            'description': self.description,
            'rarity': self.rarity.display_name,
            'rarity_color': self.rarity.color,
            'unlocked': self.unlocked,
            'icon': self.icon,
            'rewards': self.rewards,
            'reward_claimed': self.reward_claimed
        }


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
            # Ресурсы животных
            'wolf_fang': 'Клык волка',
            'wolf_hide': 'Шкура волка',
            'bear_fang': 'Клык медведя',
            'bear_hide': 'Шкура медведя',
            'bear_meat': 'Медвежатина',
            'deer_hide': 'Шкура оленя',
            'deer_meat': 'Оленина',
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
    gather_quest = Quest(
        quest_id=f"alchemist_gather_{random.randint(1000, 9999)}",
        name="Сбор ингредиентов",
        description="Алхимику нужны магические кристаллы для зелий.",
        objectives=[
            QuestObjective("Собрать магические кристаллы", 3)
        ],
        rewards={"exp": 150, "gold": 100},
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    )
    gather_quest.target_item = "magic_crystal"
    quests.append(gather_quest)

    # Квест на уничтожение нежити
    kill_quest = Quest(
        quest_id=f"alchemist_undead_{random.randint(1000, 9999)}",
        name="Очищение руин",
        description="Нежить в руинах мешает собирать редкие ингредиенты.",
        objectives=[
            QuestObjective("Уничтожить нежить", 5)
        ],
        rewards={"exp": 200, "gold": 150},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.HARD,
        giver_location=npc_name
    )
    kill_quest.target_enemy = "undead"
    quests.append(kill_quest)

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
    bandit_quest = Quest(
        quest_id=f"hunter_bandits_{random.randint(1000, 9999)}",
        name="Охота на бандитов",
        description="Бандиты угрожают путникам на дорогах. Необходимо их остановить.",
        objectives=[
            QuestObjective("Уничтожить бандитов", 5)
        ],
        rewards={"exp": 180, "gold": 120},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location=npc_name
    )
    bandit_quest.target_enemy = "bandit"
    quests.append(bandit_quest)

    # Квест на охоту на элитных врагов
    elite_quest = Quest(
        quest_id=f"hunter_elite_{random.randint(1000, 9999)}",
        name="Опасная охота",
        description="В округе появился опасный главарь банды. Нужен опытный охотник.",
        objectives=[
            QuestObjective("Уничтожить главаря банды", 1)
        ],
        rewards={"exp": 300, "gold": 250},
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location=npc_name
    )
    elite_quest.target_enemy = "bandit"  # Главарь тоже считается бандитом
    quests.append(elite_quest)

    return quests


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


def create_starter_quests():
    """
    Создать стартовые квесты (автоматически назначаются при старте игры)

    Returns:
        list: Список стартовых квестов
    """
    quests = []

    # Квест 1: Первые шаги - автоматически назначается
    objectives = [
        QuestObjective("Убейте 5 врагов", required_count=5),
    ]
    rewards = {'exp': 150, 'gold': 75}
    quest1 = Quest(
        quest_id="first_steps",
        name="Первые шаги",
        description="Изучите основы боя. Уничтожьте врагов в окрестностях.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest1.target_enemy = "any_enemy"  # Засчитываются любые враги (bandit, undead, necromancer)
    quests.append(quest1)

    # Квест 2: Первая охота - автоматически назначается
    objectives = [
        QuestObjective("Убейте 3 волков", required_count=3),
    ]
    rewards = {'exp': 120, 'gold': 60}
    quest2 = Quest(
        quest_id="first_hunt",
        name="Первая охота",
        description="Охотьтесь на волков в лесах.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ANIMALS,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest2.target_animal = "wolf"
    quests.append(quest2)

    # Квест 3: Сборщик ресурсов - автоматически назначается
    objectives = [
        QuestObjective("Добыть Медная руда x5", required_count=5),
    ]
    rewards = {'exp': 100, 'gold': 50}
    quest3 = Quest(
        quest_id="resource_gatherer",
        name="Сборщик ресурсов",
        description="Соберите медную руду в шахтах.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest3.target_item = "copper_ore"
    quests.append(quest3)

    # Квест 4: Исследователь - автоматически назначается
    objectives = [
        QuestObjective("Посетите 3 разных локации", required_count=3),
    ]
    rewards = {'exp': 200, 'gold': 100}
    quest4 = Quest(
        quest_id="explorer_start",
        name="Исследователь",
        description="Исследуйте мир и посетите различные локации.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.STORY,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quests.append(quest4)

    return quests


def auto_assign_starter_quests(quest_manager):
    """
    Автоматически назначить стартовые квесты игроку
    Вызывается при создании нового персонажа

    Args:
        quest_manager: Менеджер квестов

    Returns:
        list: Список назначенных квестов
    """
    starter_quests = create_starter_quests()
    assigned = []

    for quest in starter_quests:
        if quest.is_starter:
            quest.start()  # Автоматически активируем
            quest_manager.active_quests.append(quest)
            assigned.append(quest)

    return assigned


class QuestGenerator:
    """Генератор динамических квестов для локаций и NPC"""

    # ===== ШАБЛОНЫ КВЕСТОВ НА СБОР РЕСУРСОВ =====

    # Руды (для городов)
    CITY_GATHER_QUESTS = {
        'silver_ore': {
            'display_name': 'Серебряная руда',
            'quest_names': ['Серебряная жила', 'Благородный металл', 'Серебряный заказ'],
            'descriptions': [
                'Ювелиры города ищут серебряную руду.',
                'Магическая академия нуждается в серебре.',
                'Храм заказал серебро для священных предметов.'
            ]
        },
        'gold_ore': {
            'display_name': 'Золотая руда',
            'quest_names': ['Золотая лихорадка', 'Драгоценная добыча', 'Королевский заказ'],
            'descriptions': [
                'Казначейство города нуждается в золоте.',
                'Ювелирная гильдия просит добыть золотую руду.',
                'Знатный лорд заказал золото для украшений.'
            ]
        },
        'mithril_ore': {
            'display_name': 'Мифриловая руда',
            'quest_names': ['Мифриловые залежи', 'Легендарный металл', 'Редкая руда'],
            'descriptions': [
                'Мастер-кузнец ищет мифриловую руду.',
                'Военный заказ на мифриловую броню.',
                'Редкий металл нужен для королевского доспеха.'
            ]
        },
        'bear_hide': {
            'display_name': 'Шкура медведя',
            'quest_names': ['Медвежьи шкуры', 'Заказ скорняка', 'Теплые одежды'],
            'descriptions': [
                'Скорняк города заказал медвежьи шкуры.',
                'Торговец мехами ищет медвежьи шкуры.',
                'Городская гильдия готовит зимние припасы.'
            ]
        },
        'deer_hide': {
            'display_name': 'Шкура оленя',
            'quest_names': ['Оленьи шкуры', 'Кожевенный заказ', 'Благородная кожа'],
            'descriptions': [
                'Кожевник просит добыть оленьи шкуры.',
                'Мастер брони нуждается в оленьей коже.',
                'Торговая гильдия скупает оленьи шкуры.'
            ]
        },
        'bear_meat': {
            'display_name': 'Медвежатина',
            'quest_names': ['Медвежье мясо', 'Деликатес', 'Редкое мясо'],
            'descriptions': [
                'Городской ресторан заказал медвежатину.',
                'Знатная семья просит добыть медвежье мясо.',
                'Королевский повар ищет редкое мясо.'
            ]
        },
        'deer_meat': {
            'display_name': 'Оленина',
            'quest_names': ['Оленина', 'Благородная дичь', 'Королевская охота'],
            'descriptions': [
                'Городской ресторан нуждается в оленине.',
                'Знатный лорд заказал оленину для пира.',
                'Королевский двор закупает оленину.'
            ]
        },
        'wolf_hide': {
            'display_name': 'Шкура волка',
            'quest_names': ['Волчьи шкуры', 'Охотничья добыча', 'Зимние запасы'],
            'descriptions': [
                'Скорняк города скупает волчьи шкуры.',
                'Гильдия охотников ищет волчьи шкуры.',
                'Городская стража заказала шкуры для экипировки.'
            ]
        },
        'bear_fang': {
            'display_name': 'Клык медведя',
            'quest_names': ['Медвежьи клыки', 'Трофеи охотника', 'Амулеты силы'],
            'descriptions': [
                'Городской мастер делает амулеты из клыков.',
                'Магическая академия ищет медвежьи клыки.',
                'Торговец редкостями скупает клыки медведей.'
            ]
        },
        'wolf_fang': {
            'display_name': 'Клык волка',
            'quest_names': ['Волчьи клыки', 'Трофеи охоты', 'Амулеты защиты'],
            'descriptions': [
                'Городской мастер делает обереги из волчьих клыков.',
                'Магическая академия ищет волчьи зубы для зелий.',
                'Торговец амулетами скупает волчьи клыки.'
            ]
        }
    }

    # Ресурсы для деревень
    VILLAGE_GATHER_QUESTS = {
        'copper_ore': {
            'display_name': 'Медная руда',
            'quest_names': ['Добыча меди', 'Медные запасы', 'Заказ на медь'],
            'descriptions': [
                'Деревенскому кузнецу нужна медная руда.',
                'Местные ремесленники просят добыть медную руду.',
                'Торговец заказал партию медной руды.'
            ]
        },
        'iron_ore': {
            'display_name': 'Железная руда',
            'quest_names': ['Добыча железа', 'Железные запасы', 'Стальное задание'],
            'descriptions': [
                'Кузнец деревни нуждается в железной руде.',
                'Деревенская стража заказала железо.',
                'Ремесленники просят добыть железную руду.'
            ]
        },
        'wolf_hide': {
            'display_name': 'Шкура волка',
            'quest_names': ['Волчьи шкуры', 'Охотничья добыча', 'Зимние запасы'],
            'descriptions': [
                'Скорняк деревни скупает волчьи шкуры.',
                'Охотники ищут волчьи шкуры для торговли.',
                'Деревне нужны шкуры для зимних одежд.'
            ]
        },
        'wolf_fang': {
            'display_name': 'Клык волка',
            'quest_names': ['Волчьи клыки', 'Трофеи охоты', 'Амулеты защиты'],
            'descriptions': [
                'Знахарь деревни ищет волчьи клыки.',
                'Торговец амулетами скупает волчьи зубы.',
                'Местный мастер делает обереги из клыков.'
            ]
        },
        'bear_meat': {
            'display_name': 'Медвежатина',
            'quest_names': ['Медвежье мясо', 'Запасы мяса', 'Провизия'],
            'descriptions': [
                'Деревенский трактир закупает мясо.',
                'Охотничий отряд ищет провизию.',
                'Торговец мясом дает хорошую цену.'
            ]
        },
        'deer_meat': {
            'display_name': 'Оленина',
            'quest_names': ['Оленина', 'Дичь для стола', 'Мясные запасы'],
            'descriptions': [
                'Трактир деревни закупает оленину.',
                'Охотники просят добыть оленье мясо.',
                'Торговец мясом ищет свежую дичь.'
            ]
        },
        'deer_hide': {
            'display_name': 'Шкура оленя',
            'quest_names': ['Оленьи шкуры', 'Кожевенный заказ', 'Мягкая кожа'],
            'descriptions': [
                'Деревенский кожевник ищет оленьи шкуры.',
                'Местный мастер нуждается в оленьей коже.',
                'Торговец скупает оленьи шкуры.'
            ]
        },
        'bear_hide': {
            'display_name': 'Шкура медведя',
            'quest_names': ['Медвежьи шкуры', 'Охотничьи трофеи', 'Теплые меха'],
            'descriptions': [
                'Скорняк деревни заказал медвежьи шкуры.',
                'Торговец мехами ищет медвежьи шкуры.',
                'Деревня готовит запасы на зиму.'
            ]
        },
        'bear_fang': {
            'display_name': 'Клык медведя',
            'quest_names': ['Медвежьи клыки', 'Охотничьи трофеи', 'Талисманы'],
            'descriptions': [
                'Знахарь деревни ищет медвежьи клыки.',
                'Местный мастер делает талисманы из клыков.',
                'Торговец редкостями скупает клыки.'
            ]
        },
        'deer_meat': {
            'display_name': 'Оленина',
            'quest_names': ['Оленина', 'Свежее мясо', 'Праздничный заказ'],
            'descriptions': [
                'Трактирщик просит добыть оленину.',
                'В деревне готовится праздник - нужно мясо.',
                'Торговец провизией скупает оленину.'
            ]
        }
    }

    # Ресурсы для охотников
    HUNTER_GATHER_QUESTS = {
        'wolf_hide': {
            'display_name': 'Шкура волка',
            'quest_names': ['Волчья охота', 'Шкуры для гильдии', 'Заказ охотника'],
            'descriptions': [
                'Гильдия охотников скупает волчьи шкуры.',
                'Охотничий союз принимает шкуры.',
                'Торговец мехами платит хорошо.'
            ]
        },
        'bear_hide': {
            'display_name': 'Шкура медведя',
            'quest_names': ['Медвежья охота', 'Трофейные шкуры', 'Большой заказ'],
            'descriptions': [
                'Охотничья гильдия ищет медвежьи шкуры.',
                'Опытные охотники собирают трофеи.',
                'Знатный заказчик ищет медвежьи шкуры.'
            ]
        },
        'deer_hide': {
            'display_name': 'Шкура оленя',
            'quest_names': ['Охота на оленей', 'Оленьи шкуры', 'Кожевенный заказ'],
            'descriptions': [
                'Охотничья гильдия принимает оленьи шкуры.',
                'Кожевник ищет качественные шкуры.',
                'Торговая гильдия скупает кожу.'
            ]
        },
        'wolf_fang': {
            'display_name': 'Клык волка',
            'quest_names': ['Волчьи трофеи', 'Клыки хищников', 'Охотничьи амулеты'],
            'descriptions': [
                'Охотники ценят волчьи клыки как трофеи.',
                'Мастер амулетов скупает клыки.',
                'Коллекционер охотничьих трофеев ищет клыки.'
            ]
        },
        'bear_fang': {
            'display_name': 'Клык медведя',
            'quest_names': ['Медвежьи клыки', 'Мощные трофеи', 'Редкие амулеты'],
            'descriptions': [
                'Медвежьи клыки - ценные трофеи.',
                'Мастер амулетов платит за медвежьи клыки.',
                'Опытные охотники собирают такие трофеи.'
            ]
        },
        'bear_meat': {
            'display_name': 'Медвежатина',
            'quest_names': ['Медвежье мясо', 'Добыча охотника', 'Трактирный заказ'],
            'descriptions': [
                'Трактиры охотно покупают медвежатину.',
                'Гильдия охотников принимает мясо.',
                'Хороший охотник всегда находит покупателя.'
            ]
        },
        'deer_meat': {
            'display_name': 'Оленина',
            'quest_names': ['Охотничья добыча', 'Свежая оленина', 'Заказ трактирщика'],
            'descriptions': [
                'Трактирщики ищут свежее мясо.',
                'Охотничья гильдия принимает оленину.',
                'Торговец провизией дает хорошую цену.'
            ]
        }
    }

    # Ресурсы для некроманта
    NECROMANCER_GATHER_QUESTS = {
        'artifact_fragment': {
            'display_name': 'Фрагмент артефакта',
            'quest_names': ['Осколки тьмы', 'Древние фрагменты', 'Поиск реликвий'],
            'descriptions': [
                'Некромант ищет фрагменты древних артефактов.',
                'Темные силы требуют артефактов.',
                'Исследования тьмы требуют материалов.'
            ]
        },
        'ancient_coin': {
            'display_name': 'Древняя монета',
            'quest_names': ['Монеты мертвых', 'Древнее золото', 'Проклятые сокровища'],
            'descriptions': [
                'Некромант собирает древние монеты.',
                'Монеты из гробниц имеют особую силу.',
                'Древние монеты нужны для ритуалов.'
            ]
        }
    }

    # Ресурсы для алхимика
    ALCHEMIST_GATHER_QUESTS = {
        'wolf_fang': {
            'display_name': 'Клык волка',
            'quest_names': ['Ингредиенты силы', 'Звериные клыки', 'Алхимические компоненты'],
            'descriptions': [
                'Алхимику нужны волчьи клыки для зелий.',
                'Клыки хищников - важный ингредиент.',
                'Эликсиры силы требуют звериных клыков.'
            ]
        },
        'bear_fang': {
            'display_name': 'Клык медведя',
            'quest_names': ['Мощные ингредиенты', 'Редкие компоненты', 'Зелья мощи'],
            'descriptions': [
                'Медвежьи клыки усиливают зелья.',
                'Алхимик ищет редкие ингредиенты.',
                'Для мощных эликсиров нужны медвежьи клыки.'
            ]
        },
        'old_scroll': {
            'display_name': 'Старый свиток',
            'quest_names': ['Древние свитки', 'Забытые знания', 'Тайны алхимии'],
            'descriptions': [
                'Алхимик изучает древние свитки.',
                'Старые рецепты скрыты в свитках.',
                'Поиск забытых алхимических знаний.'
            ]
        },
        'magic_crystal': {
            'display_name': 'Магический кристалл',
            'quest_names': ['Кристаллы силы', 'Магические ингредиенты', 'Источники маны'],
            'descriptions': [
                'Алхимику нужны магические кристаллы.',
                'Кристаллы усиливают зелья.',
                'Магия кристаллов необходима для экспериментов.'
            ]
        }
    }

    # ===== ШАБЛОНЫ КВЕСТОВ НА УБИЙСТВО =====

    # Враги для городов (бандиты и нежить 3-4 ранга)
    CITY_KILL_QUESTS = {
        'bandit_elite': {
            'display_name': 'Главари бандитов',
            'quest_names': ['Охота на главарей', 'Элитные разбойники', 'Опасные преступники'],
            'descriptions': [
                'Главари бандитов терроризируют округу.',
                'Опасные преступники угрожают городу.',
                'Стража не справляется с элитными бандитами.'
            ],
            'target': 'bandit',
            'min_level': 15
        },
        'undead_elite': {
            'display_name': 'Могущественную нежить',
            'quest_names': ['Древнее зло', 'Могущественные мертвецы', 'Тьма из руин'],
            'descriptions': [
                'Могущественная нежить угрожает городу.',
                'Древние мертвецы пробудились.',
                'Темные силы требуют внимания.'
            ],
            'target': 'undead',
            'min_level': 15
        }
    }

    # Враги для деревень (бандиты и нежить 1-2 ранга + животные)
    VILLAGE_KILL_QUESTS = {
        'bandit': {
            'display_name': 'Бандиты',
            'quest_names': ['Охота на бандитов', 'Зачистка дорог', 'Защита деревни'],
            'descriptions': [
                'Бандиты нападают на путников.',
                'Разбойники угрожают деревне.',
                'Стража просит помочь с бандитами.'
            ],
            'target': 'bandit',
            'min_level': 1
        },
        'undead': {
            'display_name': 'Нежить',
            'quest_names': ['Упокоение мертвых', 'Очищение', 'Святое дело'],
            'descriptions': [
                'Нежить из старого кладбища.',
                'Мертвецы беспокоят жителей.',
                'Священник просит помочь с нежитью.'
            ],
            'target': 'undead',
            'min_level': 1
        },
        'wolf': {
            'display_name': 'Волков',
            'quest_names': ['Волчья угроза', 'Охота на волков', 'Защита стада'],
            'descriptions': [
                'Волки нападают на домашний скот.',
                'Стая волков угрожает деревне.',
                'Пастухи просят помочь с волками.'
            ],
            'target': 'wolf',
            'min_level': 1
        },
        'bear': {
            'display_name': 'Медведей',
            'quest_names': ['Медвежья угроза', 'Опасный зверь', 'Защита угодий'],
            'descriptions': [
                'Медведь разоряет пасеки.',
                'Опасный медведь пугает жителей.',
                'Охотники просят помощи с медведем.'
            ],
            'target': 'bear',
            'min_level': 5
        }
    }

    # Охотничьи квесты на убийство
    HUNTER_KILL_QUESTS = {
        'wolf': {
            'display_name': 'Волков',
            'quest_names': ['Охота на волков', 'Волчья стая', 'Хищники леса'],
            'descriptions': [
                'Охотник просит помочь с волками.',
                'Волчья стая расплодилась.',
                'Хищники угрожают дичи.'
            ],
            'target': 'wolf',
            'min_level': 1
        },
        'bear': {
            'display_name': 'Медведей',
            'quest_names': ['Большая охота', 'Медвежья тропа', 'Опасная дичь'],
            'descriptions': [
                'Охотник предлагает охоту на медведя.',
                'Медведи стали агрессивными.',
                'Опасный зверь в угодьях.'
            ],
            'target': 'bear',
            'min_level': 5
        },
        'deer': {
            'display_name': 'Оленей',
            'quest_names': ['Охота на оленей', 'Благородная дичь', 'Трофейная охота'],
            'descriptions': [
                'Охотник организует охоту на оленей.',
                'Сезон охоты на оленей открыт.',
                'Нужно пополнить запасы мяса.'
            ],
            'target': 'deer',
            'min_level': 1
        },
        'bandit': {
            'display_name': 'Бандитов',
            'quest_names': ['Охота на разбойников', 'Защита угодий', 'Охотничий патруль'],
            'descriptions': [
                'Бандиты мешают охоте.',
                'Разбойники в охотничьих угодьях.',
                'Охотники объединяются против бандитов.'
            ],
            'target': 'bandit',
            'min_level': 1
        }
    }

    # Квесты некроманта на убийство нежити (1-4 ранга)
    NECROMANCER_KILL_QUESTS = {
        'undead_weak': {
            'display_name': 'Слабую нежить',
            'quest_names': ['Чистка слуг', 'Слабые мертвецы', 'Неудачные эксперименты'],
            'descriptions': [
                'Некромант избавляется от слабых слуг.',
                'Неудачные эксперименты нужно уничтожить.',
                'Слабая нежить мешает исследованиям.'
            ],
            'target': 'undead',
            'min_level': 1
        },
        'undead_strong': {
            'display_name': 'Сильную нежить',
            'quest_names': ['Испытание силы', 'Мощные мертвецы', 'Конкуренты'],
            'descriptions': [
                'Некромант ищет сильных противников.',
                'Чужая нежить вторглась в руины.',
                'Испытание для достойного воина.'
            ],
            'target': 'undead',
            'min_level': 10
        }
    }

    # Совместимость со старым кодом
    GATHER_QUESTS = {
        'copper_ore': {
            'name': 'Медная руда',
            'display_name': 'Медная руда',
            'quest_names': ['Добыча меди', 'Медные запасы', 'Заказ на медь'],
            'descriptions': [
                'Городу нужна медная руда для кузнецов.',
                'Местные ремесленники просят добыть медную руду.',
                'Торговая гильдия заказала партию медной руды.'
            ]
        },
        'iron_ore': {
            'name': 'Железная руда',
            'display_name': 'Железная руда',
            'quest_names': ['Добыча железа', 'Железные запасы', 'Стальное задание'],
            'descriptions': [
                'Кузнецы города нуждаются в железной руде.',
                'Городская стража заказала железо для нового оружия.',
                'Ремесленная гильдия просит добыть железную руду.'
            ]
        },
        'silver_ore': {
            'name': 'Серебряная руда',
            'display_name': 'Серебряная руда',
            'quest_names': ['Серебряная жила', 'Благородный металл', 'Серебряный заказ'],
            'descriptions': [
                'Ювелиры города ищут серебряную руду.',
                'Магическая академия нуждается в серебре.',
                'Храм заказал серебро для священных предметов.'
            ]
        },
        'gold_ore': {
            'name': 'Золотая руда',
            'display_name': 'Золотая руда',
            'quest_names': ['Золотая лихорадка', 'Драгоценная добыча', 'Королевский заказ'],
            'descriptions': [
                'Казначейство города нуждается в золоте.',
                'Ювелирная гильдия просит добыть золотую руду.',
                'Знатный лорд заказал золото для украшений.'
            ]
        },
        'wood': {
            'name': 'Древесина',
            'display_name': 'Древесина',
            'quest_names': ['Заготовка древесины', 'Лесной промысел', 'Строительные материалы'],
            'descriptions': [
                'Городу нужна древесина для строительства.',
                'Плотники просят заготовить древесину.',
                'Требуется древесина для ремонта стен.'
            ]
        },
        'ancient_coin': {
            'name': 'Древняя монета',
            'display_name': 'Древняя монета',
            'quest_names': ['Поиск древностей', 'Нумизматика', 'Древние сокровища'],
            'descriptions': [
                'Коллекционер ищет древние монеты из руин.',
                'Музей города просит найти исторические артефакты.',
                'Историк изучает древние монеты.'
            ]
        },
        'artifact_fragment': {
            'name': 'Фрагмент артефакта',
            'display_name': 'Фрагмент артефакта',
            'quest_names': ['Осколки прошлого', 'Поиск артефактов', 'Магические фрагменты'],
            'descriptions': [
                'Маги ищут фрагменты древних артефактов.',
                'Археолог просит найти осколки в руинах.',
                'Магическая академия нуждается в артефактах.'
            ]
        },
        'magic_crystal': {
            'name': 'Магический кристалл',
            'display_name': 'Магический кристалл',
            'quest_names': ['Магические кристаллы', 'Поиск источника силы', 'Кристальная миссия'],
            'descriptions': [
                'Маги города нуждаются в магических кристаллах.',
                'Алхимики просят найти источники магической энергии.',
                'Магическая башня заказала кристаллы.'
            ]
        }
    }

    KILL_QUESTS = {
        'bandit': {
            'name': 'Бандит',
            'display_name': 'Бандиты',
            'quest_names': ['Охота на бандитов', 'Зачистка дорог', 'Возмездие разбойникам'],
            'descriptions': [
                'Бандиты терроризируют окрестности города.',
                'Караваны страдают от нападений разбойников.',
                'Стража просит помочь в борьбе с бандитами.'
            ]
        },
        'undead': {
            'name': 'Нежить',
            'display_name': 'Нежить',
            'quest_names': ['Очищение от нежити', 'Упокоение мертвых', 'Святая миссия'],
            'descriptions': [
                'Нежить из руин угрожает путникам.',
                'Священники просят очистить руины от нечисти.',
                'Жители жалуются на появление нежити.'
            ]
        },
        'wolf': {
            'name': 'Волк',
            'display_name': 'Волков',
            'quest_names': ['Волчья угроза', 'Охота на волков', 'Защита стада'],
            'descriptions': [
                'Волки нападают на домашний скот.',
                'Стая волков угрожает путникам.',
                'Охотники просят помочь с волками.'
            ]
        },
        'bear': {
            'name': 'Медведь',
            'display_name': 'Медведей',
            'quest_names': ['Медвежья угроза', 'Опасный зверь', 'Большая охота'],
            'descriptions': [
                'Медведь разоряет окрестности.',
                'Опасный зверь пугает путников.',
                'Охотники объединяются против медведя.'
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

    # ===== СПЕЦИАЛИЗИРОВАННЫЕ ГЕНЕРАТОРЫ ДЛЯ ТИПОВ ЛОКАЦИЙ =====

    @staticmethod
    def generate_city_quests(location_name, location_id, player_level=1, count=3):
        """
        Генерация квестов для городов
        Города: серебро, золото, мифрил, бандиты 3-4 рангов, нежить 3-4 рангов, шкуры медведей и оленей
        """
        quests = []
        quest_types = ['gather', 'gather', 'kill']  # Больше квестов на сбор
        random.shuffle(quest_types)

        # Гарантируем хотя бы один квест на части животных
        animal_parts = ['bear_hide', 'deer_hide', 'bear_meat', 'deer_meat', 'wolf_hide', 'bear_fang', 'wolf_fang']
        other_resources = ['silver_ore', 'gold_ore', 'mithril_ore']
        animal_quest_added = False

        for i in range(min(count, len(quest_types))):
            if quest_types[i] == 'gather':
                # Если это первый квест на сбор и мы еще не добавили квест на части животных
                if not animal_quest_added and random.random() < 0.7:  # 70% шанс на части животных
                    resource_key = random.choice(animal_parts)
                    animal_quest_added = True
                else:
                    # Выбираем из всех ресурсов
                    resource_key = random.choice(list(QuestGenerator.CITY_GATHER_QUESTS.keys()))
                    if resource_key in animal_parts:
                        animal_quest_added = True

                quest = QuestGenerator._generate_specialized_gather_quest(
                    resource_key, QuestGenerator.CITY_GATHER_QUESTS[resource_key],
                    location_name, location_id, player_level,
                    difficulty_range=[QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
                )
            else:
                enemy_key = random.choice(list(QuestGenerator.CITY_KILL_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_kill_quest(
                    enemy_key, QuestGenerator.CITY_KILL_QUESTS[enemy_key],
                    location_name, location_id, player_level
                )
            quests.append(quest)
        return quests

    @staticmethod
    def generate_village_quests(location_name, location_id, player_level=1, count=3):
        """
        Генерация квестов для деревень
        Деревни: шкуры волков, зубы и мясо животных, волки, медведи, железо, медь, бандиты 1-2, нежить 1-2
        """
        quests = []
        quest_types = ['gather', 'kill', 'gather']  # Смешанные квесты
        random.shuffle(quest_types)

        # Гарантируем хотя бы один квест на части животных
        # Все части животных из VILLAGE_GATHER_QUESTS
        animal_parts = ['wolf_hide', 'wolf_fang', 'bear_meat', 'deer_meat', 'deer_hide', 'bear_hide', 'bear_fang']
        other_resources = ['copper_ore', 'iron_ore']
        animal_quest_added = False

        for i in range(min(count, len(quest_types))):
            if quest_types[i] == 'gather':
                # Если это первый квест на сбор и мы еще не добавили квест на части животных
                if not animal_quest_added and random.random() < 0.7:  # 70% шанс на части животных
                    resource_key = random.choice(animal_parts)
                    animal_quest_added = True
                else:
                    # Выбираем из всех ресурсов
                    resource_key = random.choice(list(QuestGenerator.VILLAGE_GATHER_QUESTS.keys()))
                    if resource_key in animal_parts:
                        animal_quest_added = True

                quest = QuestGenerator._generate_specialized_gather_quest(
                    resource_key, QuestGenerator.VILLAGE_GATHER_QUESTS[resource_key],
                    location_name, location_id, player_level,
                    difficulty_range=[QuestDifficulty.EASY, QuestDifficulty.MEDIUM]
                )
            else:
                enemy_key = random.choice(list(QuestGenerator.VILLAGE_KILL_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_kill_quest(
                    enemy_key, QuestGenerator.VILLAGE_KILL_QUESTS[enemy_key],
                    location_name, location_id, player_level
                )
            quests.append(quest)
        return quests

    @staticmethod
    def generate_hunter_quests(location_name, location_id, player_level=1, count=3):
        """
        Генерация квестов для охотников
        Охотники: шкуры, зубы и мясо всех животных, убийство всех животных
        """
        quests = []
        quest_types = ['gather', 'kill', 'gather']
        random.shuffle(quest_types)

        for i in range(min(count, len(quest_types))):
            if quest_types[i] == 'gather':
                resource_key = random.choice(list(QuestGenerator.HUNTER_GATHER_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_gather_quest(
                    resource_key, QuestGenerator.HUNTER_GATHER_QUESTS[resource_key],
                    location_name, location_id, player_level,
                    difficulty_range=[QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
                )
            else:
                enemy_key = random.choice(list(QuestGenerator.HUNTER_KILL_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_kill_quest(
                    enemy_key, QuestGenerator.HUNTER_KILL_QUESTS[enemy_key],
                    location_name, location_id, player_level,
                    is_animal=enemy_key in ['wolf', 'bear', 'deer']
                )
            quests.append(quest)
        return quests

    @staticmethod
    def generate_necromancer_quests(location_name, location_id, player_level=1, count=2):
        """
        Генерация квестов для некроманта
        Некромант: артефакты, древние монеты, нежить 1-4 рангов
        """
        quests = []
        quest_types = ['gather', 'kill']
        random.shuffle(quest_types)

        for i in range(min(count, len(quest_types))):
            if quest_types[i] == 'gather':
                resource_key = random.choice(list(QuestGenerator.NECROMANCER_GATHER_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_gather_quest(
                    resource_key, QuestGenerator.NECROMANCER_GATHER_QUESTS[resource_key],
                    location_name, location_id, player_level,
                    difficulty_range=[QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
                )
            else:
                enemy_key = random.choice(list(QuestGenerator.NECROMANCER_KILL_QUESTS.keys()))
                quest = QuestGenerator._generate_specialized_kill_quest(
                    enemy_key, QuestGenerator.NECROMANCER_KILL_QUESTS[enemy_key],
                    location_name, location_id, player_level
                )
            quests.append(quest)
        return quests

    @staticmethod
    def generate_alchemist_quests(location_name, location_id, player_level=1, count=2):
        """
        Генерация квестов для алхимика
        Алхимик: зубы животных, древние свитки, магические кристаллы
        """
        quests = []

        for _ in range(count):
            resource_key = random.choice(list(QuestGenerator.ALCHEMIST_GATHER_QUESTS.keys()))
            quest = QuestGenerator._generate_specialized_gather_quest(
                resource_key, QuestGenerator.ALCHEMIST_GATHER_QUESTS[resource_key],
                location_name, location_id, player_level,
                difficulty_range=[QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
            )
            quests.append(quest)
        return quests

    @staticmethod
    def _generate_specialized_gather_quest(resource_key, resource_data, location_name, location_id,
                                           player_level, difficulty_range=None):
        """Генерация квеста на сбор с заданными параметрами"""
        if difficulty_range is None:
            difficulty_range = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]

        difficulty = random.choice(difficulty_range)

        base_amounts = {
            QuestDifficulty.EASY: (3, 5),
            QuestDifficulty.MEDIUM: (5, 8),
            QuestDifficulty.HARD: (6, 10),
            QuestDifficulty.VERY_HARD: (8, 12)
        }
        min_amount, max_amount = base_amounts[difficulty]
        required_amount = random.randint(min_amount, max_amount)

        base_exp = 50 + player_level * 10
        base_gold = 30 + player_level * 5
        exp_reward = int(base_exp * difficulty.reward_multiplier * (required_amount / 5))
        gold_reward = int(base_gold * difficulty.reward_multiplier * (required_amount / 5))

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
    def _generate_specialized_kill_quest(enemy_key, enemy_data, location_name, location_id,
                                         player_level, is_animal=False):
        """Генерация квеста на убийство с заданными параметрами"""
        min_level = enemy_data.get('min_level', 1)
        target = enemy_data.get('target', enemy_key)

        # Сложность зависит от уровня врага
        if min_level >= 15:
            difficulty = random.choice([QuestDifficulty.HARD, QuestDifficulty.VERY_HARD])
        elif min_level >= 10:
            difficulty = random.choice([QuestDifficulty.MEDIUM, QuestDifficulty.HARD])
        elif min_level >= 5:
            difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])
        else:
            difficulty = random.choice([QuestDifficulty.EASY, QuestDifficulty.MEDIUM])

        base_amounts = {
            QuestDifficulty.EASY: (2, 4),
            QuestDifficulty.MEDIUM: (3, 6),
            QuestDifficulty.HARD: (5, 8),
            QuestDifficulty.VERY_HARD: (6, 10)
        }
        min_amount, max_amount = base_amounts[difficulty]
        required_amount = random.randint(min_amount, max_amount)

        base_exp = 80 + player_level * 15
        base_gold = 50 + player_level * 8
        exp_reward = int(base_exp * difficulty.reward_multiplier * (required_amount / 4))
        gold_reward = int(base_gold * difficulty.reward_multiplier * (required_amount / 4))

        quest_name = random.choice(enemy_data['quest_names'])
        description = random.choice(enemy_data['descriptions'])
        quest_id = f"kill_{enemy_key}_{location_id}_{random.randint(1000, 9999)}"

        objective = QuestObjective(
            f"Убить {enemy_data['display_name']} x{required_amount}",
            required_count=required_amount
        )

        quest_type = QuestType.KILL_ANIMALS if is_animal else QuestType.KILL_ENEMIES

        quest = Quest(
            quest_id=quest_id,
            name=quest_name,
            description=description,
            objectives=[objective],
            rewards={'exp': exp_reward, 'gold': gold_reward},
            quest_type=quest_type,
            difficulty=difficulty,
            location_id=location_id,
            giver_location=location_name
        )

        if is_animal:
            quest.target_animal = target
        else:
            quest.target_enemy = target

        return quest


def create_unique_quests():
    """
    Создать уникальные квесты с особыми наградами (красная рамка в UI)

    Returns:
        list: Список уникальных квестов
    """
    from game.inventory import PREDEFINED_ITEMS

    quests = []

    # ===== КВЕСТЫ АЛХИМИКА (УНИКАЛЬНЫЕ) =====

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
        name="[УНИК] Редкие ингредиенты",
        description="Алхимик ищет редкие компоненты для создания мощных эликсиров.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Алхимик",
        is_unique=True
    )
    quest.target_item = "magic_crystal"
    quests.append(quest)

    # Квест 2: Философский камень (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Найти осколки Философского Камня в руинах", required_count=1),
        QuestObjective("Собрать золотую руду", required_count=10),
        QuestObjective("Собрать серебряную руду", required_count=15),
    ]
    rewards = {
        'exp': 1500,
        'gold': 1200,
        'items': [
            (PREDEFINED_ITEMS["alchemists_staff"], 1),
            (PREDEFINED_ITEMS["book_heal"], 1),
        ]
    }
    quest = Quest(
        quest_id="alchemist_philosophers_stone",
        name="[ЛЕГЕНД] Тайна Философского Камня",
        description="Помогите алхимику в поисках легендарного артефакта.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Алхимик",
        is_unique=True
    )
    quests.append(quest)

    # ===== КВЕСТЫ ОХОТНИКА (УНИКАЛЬНЫЕ) =====

    # Квест 3: Великая охота на волков
    objectives = [
        QuestObjective("Убить волков", required_count=15),
        QuestObjective("Добыть Шкура волка x8", required_count=8),
    ]
    rewards = {
        'exp': 600,
        'gold': 400,
        'items': [
            (PREDEFINED_ITEMS["hunters_bow"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_wolf_master",
        name="[УНИК] Великая охота на волков",
        description="Охотник предлагает масштабную охоту на волков.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "wolf"
    quests.append(quest)

    # Квест 4: Медвежий охотник
    objectives = [
        QuestObjective("Убить медведей", required_count=10),
        QuestObjective("Добыть Шкура медведя x5", required_count=5),
    ]
    rewards = {
        'exp': 800,
        'gold': 600,
        'items': [
            (PREDEFINED_ITEMS["shadow_blade"], 1),
            (PREDEFINED_ITEMS["greater_health_potion"], 5),
        ]
    }
    quest = Quest(
        quest_id="hunter_bear_master",
        name="[УНИК] Медвежий охотник",
        description="Докажите мастерство в охоте на медведей.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "bear"
    quests.append(quest)

    # Квест 5: Мастер охоты (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Уничтожить бандитов", required_count=20),
        QuestObjective("Уничтожить нежить", required_count=20),
        QuestObjective("Убить волков", required_count=15),
        QuestObjective("Убить медведей", required_count=10),
    ]
    rewards = {
        'exp': 2500,
        'gold': 1500,
        'items': [
            (PREDEFINED_ITEMS["book_power_strike"], 1),
            (PREDEFINED_ITEMS["book_battle_cry"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_master_hunt",
        name="[ЛЕГЕНД] Мастер Охоты",
        description="Докажите, что вы достойны звания Мастера Охоты.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quests.append(quest)

    # ===== КВЕСТЫ НЕКРОМАНТА (УНИКАЛЬНЫЕ) =====

    # Квест 6: Остановить некроманта (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Победить некроманта", required_count=1),
    ]
    rewards = {
        'exp': 3000,
        'gold': 2000,
        'items': [
            (PREDEFINED_ITEMS["book_fireball"], 1),
            (PREDEFINED_ITEMS["book_lightning"], 1),
        ]
    }
    quest = Quest(
        quest_id="stop_necromancer",
        name="[ЛЕГЕНД] Угроза из руин",
        description="Некромант угрожает живым. Остановите его!",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия",
        is_unique=True
    )
    quest.target_enemy = "necromancer"
    quests.append(quest)

    # ===== КВЕСТЫ НА СБОР (УНИКАЛЬНЫЕ) =====

    # Квест 7: Богатство земли
    objectives = [
        QuestObjective("Собрать медную руду", required_count=20),
        QuestObjective("Собрать железную руду", required_count=15),
        QuestObjective("Собрать серебряную руду", required_count=10),
        QuestObjective("Собрать золотую руду", required_count=5),
    ]
    rewards = {
        'exp': 1000,
        'gold': 1200,
        'items': [
            (PREDEFINED_ITEMS["book_regeneration"], 1),
        ]
    }
    quest = Quest(
        quest_id="mining_master",
        name="[УНИК] Богатство земли",
        description="Соберите руды всех типов для кузнецов города.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Город",
        is_unique=True
    )
    quests.append(quest)

    # Квест 8: Древние знания (УНИКАЛЬНЫЙ)
    objectives = [
        QuestObjective("Собрать древние монеты", required_count=10),
        QuestObjective("Собрать фрагменты артефактов", required_count=5),
        QuestObjective("Собрать старые свитки", required_count=8),
    ]
    rewards = {
        'exp': 1500,
        'gold': 1000,
        'items': [
            (PREDEFINED_ITEMS["book_magic_missile"], 1),
            (PREDEFINED_ITEMS["book_ice_bolt"], 1),
        ]
    }
    quest = Quest(
        quest_id="ancient_knowledge",
        name="[УНИК] Древние знания",
        description="Соберите артефакты из руин для исследований.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия",
        is_unique=True
    )
    quests.append(quest)

    # Квест 9: Охотник на оленей (УНИКАЛЬНЫЙ)
    objectives = [
        QuestObjective("Убить оленей", required_count=12),
        QuestObjective("Добыть Оленина x10", required_count=10),
        QuestObjective("Добыть Шкура оленя x6", required_count=6),
    ]
    rewards = {
        'exp': 700,
        'gold': 500,
        'items': [
            (PREDEFINED_ITEMS["stamina_potion"], 5),
        ]
    }
    quest = Quest(
        quest_id="deer_hunter_master",
        name="[УНИК] Охотник на оленей",
        description="Масштабная охота на оленей для торговой гильдии.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "deer"
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
