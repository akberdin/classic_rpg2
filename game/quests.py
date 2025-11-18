"""
Система квестов и достижений
"""
from enum import Enum


class QuestStatus(Enum):
    """Статусы квеста"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


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

    def __init__(self, quest_id, name, description, objectives, rewards):
        """
        Инициализация квеста

        Args:
            quest_id: Уникальный ID квеста
            name: Название квеста
            description: Описание квеста
            objectives: Список целей квеста (QuestObjective)
            rewards: Словарь наград {'exp': int, 'gold': int, 'items': []}
        """
        self.quest_id = quest_id
        self.name = name
        self.description = description
        self.objectives = objectives
        self.rewards = rewards
        self.status = QuestStatus.NOT_STARTED

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
            bool: True если квест завершен
        """
        if self.status != QuestStatus.IN_PROGRESS:
            return False

        # Проверяем все цели
        all_completed = all(obj.is_completed() for obj in self.objectives)

        if all_completed:
            self.status = QuestStatus.COMPLETED

        return all_completed

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
        lines = [f"Квест: {self.name}", f"  {self.description}", "  Цели:"]
        for obj in self.objectives:
            lines.append(f"    {obj.get_progress_string()}")
        return "\n".join(lines)

    def claim_rewards(self, player):
        """
        Получить награды за квест

        Args:
            player: Игрок, получающий награды

        Returns:
            list: Список сообщений о полученных наградах
        """
        if not self.is_completed():
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

    def __init__(self):
        """Инициализация менеджера квестов"""
        self.available_quests = []  # Доступные квесты
        self.active_quests = []     # Активные квесты
        self.completed_quests = []  # Завершенные квесты

    def add_available_quest(self, quest):
        """
        Добавить квест в список доступных

        Args:
            quest: Квест для добавления
        """
        self.available_quests.append(quest)

    def accept_quest(self, quest_id):
        """
        Принять квест

        Args:
            quest_id: ID квеста

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        # Ищем квест среди доступных
        quest = None
        for q in self.available_quests:
            if q.quest_id == quest_id:
                quest = q
                break

        if not quest:
            return False, "Квест не найден"

        # Принимаем квест
        if quest.start():
            self.available_quests.remove(quest)
            self.active_quests.append(quest)
            return True, f"Принят квест: {quest.name}"

        return False, "Квест уже принят"

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
            if q.quest_id == quest_id and q.is_completed():
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
