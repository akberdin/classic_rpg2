"""
Класс QuestManager - менеджер квестов игрока.
"""

from typing import Dict, Any, List, Set, Optional, TYPE_CHECKING
from game.quests.quest_instance import QuestInstance
from game.quests.quest_types import QUEST_SOURCE_LOCATIONS

if TYPE_CHECKING:
    from game.entities.player import Player


class QuestManager:
    """Менеджер квестов игрока."""

    def __init__(self):
        """Инициализировать менеджер квестов."""
        # Активные квесты игрока
        self.active_quests: List[QuestInstance] = []
        # ID выполненных неповторяемых квестов
        self.completed_quests: Set[str] = set()
        # Кулдауны квестов: {quest_id: оставшееся время}
        self.cooldowns: Dict[str, int] = {}
        # Ссылка на игрока (устанавливается при интеграции)
        self._player: Optional['Player'] = None
        # Callback для событий (устанавливается игрой)
        self._event_callback = None

    def set_player(self, player: 'Player') -> None:
        """Установить ссылку на игрока."""
        self._player = player

    def set_event_callback(self, callback) -> None:
        """Установить callback для событий завершения квестов."""
        self._event_callback = callback

    def get_available_quests(self, location) -> List[Dict[str, Any]]:
        """
        Получить доступные квесты в локации.

        Args:
            location: Объект локации

        Returns:
            Список конфигураций доступных квестов
        """
        # Проверяем, может ли локация выдавать квесты
        if not hasattr(location, 'quests') or not location.quests:
            return []

        if location.location_type not in QUEST_SOURCE_LOCATIONS:
            return []

        available = []
        player_attitude = getattr(location, 'player_attitude', 0)

        for quest_config in location.quests:
            quest_id = quest_config.get('id', '')

            # Пропускаем неповторяемые выполненные квесты
            if not quest_config.get('is_repeatable', True):
                if quest_id in self.completed_quests:
                    continue

            # Пропускаем квесты на перезарядке
            if quest_id in self.cooldowns and self.cooldowns[quest_id] > 0:
                continue

            # Пропускаем уже взятые квесты
            if any(q.id == quest_id for q in self.active_quests):
                continue

            # Проверяем минимальное отношение
            min_attitude = quest_config.get('min_player_attitude', 0)
            if player_attitude < min_attitude:
                continue

            available.append(quest_config)

        return available

    def get_quests_to_turn_in(self, location) -> List[QuestInstance]:
        """
        Получить квесты, которые можно сдать в этой локации.

        Args:
            location: Объект локации

        Returns:
            Список квестов для сдачи
        """
        from game.quests.quest_types import QuestType

        turn_in = []
        location_id = getattr(location, 'id', '') or ''
        location_name = getattr(location, 'name', '') or ''

        for quest in self.active_quests:
            # Передаём player для проверки inventory-based квестов
            if not quest.is_complete(self._player):
                continue

            # Для квестов доставки - сдача в точке назначения
            if quest.quest_type == QuestType.DELIVER_MESSAGE:
                id_match = quest.target_location_id and location_id == quest.target_location_id
                name_match = quest.target_location_name and location_name == quest.target_location_name
                if id_match or name_match:
                    turn_in.append(quest)
            # Для остальных квестов - сдача в локации-источнике
            elif quest.source_location_id == location_id:
                turn_in.append(quest)

        return turn_in

    def accept_quest(self, quest_config: Dict[str, Any], source_location_id: str = "") -> Optional[QuestInstance]:
        """
        Принять квест.

        Args:
            quest_config: Конфигурация квеста
            source_location_id: ID локации-источника

        Returns:
            Созданный экземпляр квеста или None
        """
        if not self._player:
            return None

        # Проверяем, не взят ли уже этот квест
        quest_id = quest_config.get('id', '')
        if any(q.id == quest_id for q in self.active_quests):
            return None

        # Создаем экземпляр квеста
        quest = QuestInstance(quest_config, self._player.level, source_location_id)
        self.active_quests.append(quest)

        print(f"Квест принят: {quest.name}")
        return quest

    def complete_quest(self, quest: QuestInstance) -> Dict[str, Any]:
        """
        Завершить квест и получить награды.

        Args:
            quest: Экземпляр квеста

        Returns:
            Словарь с наградами
        """
        if not self._player:
            return {}

        # Для квестов на сбор ресурсов/предметов - забираем предметы из инвентаря
        if quest.is_inventory_based():
            item_id = quest.get_inventory_item_id()
            if item_id:
                removed = self._player.inventory.remove_item_by_id(item_id, quest.target_amount)
                if removed < quest.target_amount:
                    print(f"Предупреждение: удалено только {removed}/{quest.target_amount} предметов")

        rewards = {
            'gold': quest.reward_gold,
            'exp': quest.reward_exp,
            'reputation': quest.reward_reputation,
            'item_id': quest.reward_item_id,
            'item_amount': quest.reward_item_amount,
            'completion_event_id': quest.completion_event_id,
        }

        # Выдаем награды
        self._player.inventory.add_gold(rewards['gold'])
        self._player.add_experience(rewards['exp'])

        # Выдаем предмет если указан
        if rewards['item_id']:
            from game.item_registry import get_item
            item = get_item(rewards['item_id'])
            if item:
                self._player.inventory.add_item(item, rewards['item_amount'])

        # Обрабатываем повторяемость
        quest_id = quest.id
        if quest.is_repeatable:
            self.cooldowns[quest_id] = quest.cooldown
        else:
            self.completed_quests.add(quest_id)

        # Удаляем из активных
        if quest in self.active_quests:
            self.active_quests.remove(quest)

        # Запускаем событие завершения если указано
        if rewards['completion_event_id'] and self._event_callback:
            self._event_callback(rewards['completion_event_id'])

        print(f"Квест завершен: {quest.name}")
        print(f"  Награда: {quest.get_rewards_text()}")

        return rewards

    def fail_quest(self, quest: QuestInstance, location=None) -> None:
        """
        Провалить квест (истечение времени или отказ).

        Args:
            quest: Экземпляр квеста
            location: Локация для применения штрафа (опционально)
        """
        # Применяем штраф к отношению локации
        if quest.fail_attitude_penalty > 0 and location:
            if hasattr(location, 'player_attitude'):
                location.player_attitude = max(-10, location.player_attitude - quest.fail_attitude_penalty)
                print(f"Отношение локации {location.name} снизилось на {quest.fail_attitude_penalty}")

        # Удаляем из активных
        if quest in self.active_quests:
            self.active_quests.remove(quest)

        print(f"Квест провален: {quest.name}")

    def abandon_quest(self, quest: QuestInstance, location=None) -> None:
        """
        Отказаться от квеста.

        Args:
            quest: Экземпляр квеста
            location: Локация для применения штрафа (опционально)
        """
        self.fail_quest(quest, location)

    def update_quest_progress(self, event_type: str, event_data: Dict[str, Any]) -> List[QuestInstance]:
        """
        Обновить прогресс всех активных квестов на основе события.

        Args:
            event_type: Тип события
            event_data: Данные события

        Returns:
            Список квестов, прогресс которых изменился
        """
        updated = []
        for quest in self.active_quests:
            if quest.update_progress(event_type, event_data):
                updated.append(quest)
                # Выводим сообщение о прогрессе
                if quest.is_complete(self._player):
                    print(f"Квест выполнен! Вернитесь для получения награды: {quest.name}")
                else:
                    print(f"Прогресс квеста '{quest.name}': {quest.get_progress_text(self._player)}")
        return updated

    def tick(self) -> List[QuestInstance]:
        """
        Обновить состояние (вызывается каждый ход).

        Returns:
            Список просроченных квестов
        """
        expired = []

        # Обновляем таймеры активных квестов
        for quest in self.active_quests:
            quest.tick()
            if quest.is_expired():
                expired.append(quest)

        # Уменьшаем кулдауны
        for quest_id in list(self.cooldowns.keys()):
            self.cooldowns[quest_id] -= 1
            if self.cooldowns[quest_id] <= 0:
                del self.cooldowns[quest_id]

        return expired

    def get_active_quests(self) -> List[QuestInstance]:
        """Получить список активных квестов."""
        return self.active_quests.copy()

    def get_completed_count(self) -> int:
        """Получить количество выполненных неповторяемых квестов."""
        return len(self.completed_quests)

    def get_quest_by_id(self, quest_id: str) -> Optional[QuestInstance]:
        """Найти активный квест по ID."""
        for quest in self.active_quests:
            if quest.id == quest_id:
                return quest
        return None

    def has_active_quest(self, quest_id: str) -> bool:
        """Проверить, есть ли активный квест с указанным ID."""
        return any(q.id == quest_id for q in self.active_quests)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализовать менеджер для сохранения."""
        return {
            'active_quests': [q.to_dict() for q in self.active_quests],
            'completed_quests': list(self.completed_quests),
            'cooldowns': self.cooldowns.copy(),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Десериализовать менеджер из сохранения."""
        self.active_quests = [
            QuestInstance.from_dict(qd) for qd in data.get('active_quests', [])
        ]
        self.completed_quests = set(data.get('completed_quests', []))
        self.cooldowns = data.get('cooldowns', {})
