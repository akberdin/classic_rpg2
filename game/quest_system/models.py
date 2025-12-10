"""
Модели данных для системы квестов и достижений
"""
from enum import Enum


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
                 location_id=None, giver_location=None, is_unique=False, is_starter=False,
                 min_rank=1):
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
            min_rank: Минимальный ранг игрока для доступа к квесту (1-4)
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
        self.min_rank = min_rank  # Минимальный ранг для квеста

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

        # ВАЖНО: Сначала удаляем ресурсы (освобождаем место), потом выдаём награды!
        # Для квестов на сбор ресурсов - удаляем собранные предметы из инвентаря
        if self.quest_type == QuestType.GATHER_RESOURCE and self.target_item:
            from .quest_data import ITEM_KEY_TO_NAME
            # Конвертируем английский ключ в русское название для работы с инвентарем
            item_name = ITEM_KEY_TO_NAME.get(self.target_item, self.target_item)

            for objective in self.objectives:
                # Проверяем фактическое количество в инвентаре, а не objective.is_completed()
                inventory_count = player.inventory.get_item_count(item_name)
                if inventory_count >= objective.required_count:
                    # Удаляем требуемое количество предмета из инвентаря
                    success = player.inventory.remove_item(item_name, objective.required_count)
                    if success:
                        messages.append(f"Сдано: {item_name} x{objective.required_count}")

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

        # Умения
        if 'skills' in self.rewards:
            for skill_key in self.rewards['skills']:
                if hasattr(player, 'skill_manager'):
                    success = player.skill_manager.learn_skill(skill_key)
                    if success:
                        # Получаем название умения для сообщения
                        skill = player.skill_manager.get_skill(skill_key)
                        skill_name = skill.name if skill else skill_key
                        messages.append(f"Получено умение: {skill_name}")
                    else:
                        messages.append(f"Умение {skill_key} уже изучено")

        # Спутники
        if 'companions' in self.rewards:
            if hasattr(player, 'companion_manager'):
                for companion_data in self.rewards['companions']:
                    companion_type = companion_data.get('type', 'wolf')
                    companion_level = companion_data.get('level', 1)
                    companion = player.companion_manager.add_companion(companion_type, companion_level)
                    messages.append(f"К вам присоединился: {companion.name}!")

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
