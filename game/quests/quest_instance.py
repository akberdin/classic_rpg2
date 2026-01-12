"""
Класс QuestInstance - экземпляр активного квеста у игрока.
"""

from typing import Dict, Any, Optional
from game.quests.quest_types import QuestType, DIFFICULTY_NAMES


class QuestInstance:
    """Экземпляр активного квеста у игрока."""

    def __init__(self, quest_config: Dict[str, Any], player_level: int, source_location_id: str = ""):
        """
        Создать экземпляр квеста.

        Args:
            quest_config: Конфигурация квеста из конфига карты
            player_level: Уровень игрока на момент принятия квеста
            source_location_id: ID локации, выдавшей квест
        """
        self.config = quest_config
        self.player_level = player_level
        self.source_location_id = source_location_id

        # Базовые параметры из конфига
        self.id = quest_config.get('id', '')
        self.name = quest_config.get('name', 'Неизвестный квест')
        self.description = quest_config.get('description', '')
        self.quest_type = quest_config.get('quest_type', QuestType.GATHER_RESOURCE)
        self.difficulty = quest_config.get('difficulty', 1)

        # Параметры масштабирования
        scaling = quest_config.get('scaling_factor', 1.1)

        # Цели квеста
        self.target_type = quest_config.get('target_type', '')
        self.target_item_id = quest_config.get('target_item_id', '')
        self.target_location_id = quest_config.get('target_location_id', '')
        self.target_location_name = quest_config.get('target_location_name', '')
        self.target_floor = quest_config.get('target_floor', 0)

        # Масштабируемое количество целей
        base_amount = quest_config.get('target_amount', 10)
        self.target_amount = self._scale(base_amount, scaling, self.difficulty)
        self.current_amount = 0

        # Для clear_location - отслеживание зачищенных этажей
        self.cleared_floors = set()

        # Масштабируемые награды
        self.reward_gold = self._scale(
            quest_config.get('reward_gold', 100), scaling, self.difficulty
        )
        self.reward_exp = self._scale(
            quest_config.get('reward_exp', 50), scaling, self.difficulty
        )

        # НЕ масштабируемые награды
        self.reward_reputation = quest_config.get('reward_reputation', 5)
        self.reward_item_id = quest_config.get('reward_item_id', '')
        self.reward_item_amount = quest_config.get('reward_item_amount', 1)

        # Событие завершения
        self.completion_event_id = quest_config.get('completion_event_id', '')

        # Время и повторяемость
        self.time_limit = quest_config.get('time_limit', 0)
        self.time_remaining = self.time_limit
        self.is_repeatable = quest_config.get('is_repeatable', True)
        self.cooldown = quest_config.get('cooldown', 100)

        # Штраф за провал
        self.fail_attitude_penalty = quest_config.get('fail_attitude_penalty', 0)

        # Минимальное отношение (сохраняем для справки)
        self.min_player_attitude = quest_config.get('min_player_attitude', 0)

    def _scale(self, base: int, scaling: float, difficulty: int) -> int:
        """
        Применить масштабирование к значению.

        Args:
            base: Базовое значение
            scaling: Коэффициент масштабирования (1.0 - 2.0)
            difficulty: Сложность квеста (1-5)

        Returns:
            Масштабированное значение (минимум 1)
        """
        # Множитель сложности: 1.0, 1.2, 1.4, 1.6, 1.8
        diff_mult = 1.0 + (difficulty - 1) * 0.2
        # Множитель уровня (экспоненциальный рост)
        level_mult = scaling ** (self.player_level - 1)
        return max(1, round(base * level_mult * diff_mult))

    def update_progress(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Обновить прогресс квеста на основе события.

        Args:
            event_type: Тип события:
                - 'resource_gathered': Собран ресурс
                - 'animal_killed': Убито животное
                - 'item_collected': Собран предмет
                - 'location_visited': Посещена локация
                - 'floor_cleared': Зачищен этаж

            event_data: Данные события:
                - resource_type: Тип ресурса
                - animal_type: Тип животного
                - item_id: ID предмета
                - location_id: ID локации
                - floor: Номер этажа
                - amount: Количество

        Returns:
            True если прогресс обновлен
        """
        if self.quest_type == QuestType.GATHER_RESOURCE and event_type == 'resource_gathered':
            if event_data.get('resource_type') == self.target_type:
                self.current_amount += event_data.get('amount', 1)
                return True

        elif self.quest_type == QuestType.HUNT_ANIMALS and event_type == 'animal_killed':
            if event_data.get('animal_type') == self.target_type:
                self.current_amount += 1
                return True

        elif self.quest_type == QuestType.COLLECT_ITEMS and event_type == 'item_collected':
            if event_data.get('item_id') == self.target_item_id:
                self.current_amount += event_data.get('amount', 1)
                return True

        elif self.quest_type == QuestType.DELIVER_MESSAGE and event_type == 'location_visited':
            if event_data.get('location_id') == self.target_location_id:
                self.current_amount = 1
                return True

        elif self.quest_type == QuestType.CLEAR_LOCATION and event_type == 'floor_cleared':
            if event_data.get('location_id') == self.target_location_id:
                floor = event_data.get('floor', 0)
                if self.target_floor == 0:
                    # Все этажи - добавляем зачищенный этаж
                    self.cleared_floors.add(floor)
                    # Проверяем все ли этажи зачищены
                    total_floors = event_data.get('total_floors', 1)
                    if len(self.cleared_floors) >= total_floors:
                        self.current_amount = 1
                        return True
                elif floor == self.target_floor:
                    # Конкретный этаж
                    self.current_amount = 1
                    return True

        return False

    def is_complete(self) -> bool:
        """Проверить, выполнен ли квест."""
        if self.quest_type in (QuestType.GATHER_RESOURCE, QuestType.HUNT_ANIMALS, QuestType.COLLECT_ITEMS):
            return self.current_amount >= self.target_amount
        elif self.quest_type in (QuestType.DELIVER_MESSAGE, QuestType.CLEAR_LOCATION):
            return self.current_amount >= 1
        return False

    def is_expired(self) -> bool:
        """Проверить, истек ли срок квеста."""
        if self.time_limit <= 0:
            return False
        return self.time_remaining <= 0

    def tick(self) -> None:
        """Обновить таймер (вызывается каждый ход)."""
        if self.time_limit > 0 and self.time_remaining > 0:
            self.time_remaining -= 1

    def get_progress_text(self) -> str:
        """Получить текст прогресса."""
        if self.quest_type in (QuestType.GATHER_RESOURCE, QuestType.HUNT_ANIMALS, QuestType.COLLECT_ITEMS):
            return f"{self.current_amount}/{self.target_amount}"
        elif self.quest_type == QuestType.DELIVER_MESSAGE:
            if self.current_amount >= 1:
                return "Доставлено"
            return f"Доставить в: {self.target_location_name}"
        elif self.quest_type == QuestType.CLEAR_LOCATION:
            if self.target_floor == 0:
                return f"Этажей зачищено: {len(self.cleared_floors)}"
            else:
                if self.current_amount >= 1:
                    return f"Этаж {self.target_floor} зачищен"
                return f"Зачистить этаж {self.target_floor}"
        return ""

    def get_difficulty_name(self) -> str:
        """Получить название сложности."""
        return DIFFICULTY_NAMES.get(self.difficulty, "Неизвестно")

    def get_time_remaining_text(self) -> str:
        """Получить текст оставшегося времени."""
        if self.time_limit <= 0:
            return "Без ограничения"
        if self.time_remaining <= 0:
            return "Время истекло!"
        return f"{self.time_remaining} ходов"

    def get_rewards_text(self) -> str:
        """Получить текст наград."""
        rewards = []
        if self.reward_gold > 0:
            rewards.append(f"{self.reward_gold} золота")
        if self.reward_exp > 0:
            rewards.append(f"{self.reward_exp} опыта")
        if self.reward_reputation > 0:
            rewards.append(f"+{self.reward_reputation} репутации")
        if self.reward_item_id:
            rewards.append(f"Предмет x{self.reward_item_amount}")
        return ", ".join(rewards) if rewards else "Нет награды"

    def to_dict(self) -> Dict[str, Any]:
        """Сериализовать квест для сохранения."""
        return {
            'config': self.config,
            'player_level': self.player_level,
            'source_location_id': self.source_location_id,
            'current_amount': self.current_amount,
            'time_remaining': self.time_remaining,
            'cleared_floors': list(self.cleared_floors),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestInstance':
        """Десериализовать квест из сохранения."""
        quest = cls(
            data['config'],
            data['player_level'],
            data.get('source_location_id', '')
        )
        quest.current_amount = data.get('current_amount', 0)
        quest.time_remaining = data.get('time_remaining', quest.time_limit)
        quest.cleared_floors = set(data.get('cleared_floors', []))
        return quest
