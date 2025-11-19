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

    def __init__(self):
        """Инициализация менеджера квестов"""
        self.available_quests = []  # Доступные квесты
        self.active_quests = []     # Активные квесты
        self.completed_quests = []  # Завершенные квесты
        self.location_quests = {}   # Квесты по локациям: {location_id: [quests]}

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

    def accept_quest(self, quest_id, location_id=None):
        """
        Принять квест

        Args:
            quest_id: ID квеста
            location_id: ID локации (опционально)

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
            enemy_type: Тип убитого врага ('bandit', 'undead')

        Returns:
            list: Список сообщений о прогрессе
        """
        messages = []
        for quest in self.active_quests:
            if quest.quest_type == QuestType.KILL_ENEMIES and quest.target_enemy == enemy_type:
                if quest.objectives:
                    completed = quest.objectives[0].progress(1)
                    quest.check_completion()
                    if completed:
                        messages.append(f"Цель выполнена: {quest.objectives[0].description}")
                    elif quest.is_ready_to_turn_in():
                        messages.append(f"Квест '{quest.name}' готов к сдаче в {quest.giver_location}!")
        return messages

    def update_gather_progress(self, item_name, amount=1):
        """
        Обновить прогресс квестов на сбор ресурсов

        Args:
            item_name: Название собранного предмета
            amount: Количество

        Returns:
            list: Список сообщений о прогрессе
        """
        messages = []
        for quest in self.active_quests:
            if quest.quest_type == QuestType.GATHER_RESOURCE and quest.target_item == item_name:
                if quest.objectives:
                    completed = quest.objectives[0].progress(amount)
                    quest.check_completion()
                    if completed:
                        messages.append(f"Цель выполнена: {quest.objectives[0].description}")
                    if quest.is_ready_to_turn_in():
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
