"""
Обработчик событий завершения квестов.

Этот модуль обрабатывает события, которые срабатывают при завершении квестов.
События определяются в конфиге quest_events_config.json.
"""

import json
import os
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.player import Player


class QuestEventHandler:
    """Обработчик событий завершения квестов."""

    def __init__(self, player: 'Player', show_window_callback=None):
        """
        Инициализировать обработчик событий.

        Args:
            player: Ссылка на игрока
            show_window_callback: Callback для показа окна события (name, description)
        """
        self._player = player
        self._events_config = self._load_events_config()
        self._show_window_callback = show_window_callback

    def set_show_window_callback(self, callback):
        """
        Установить callback для показа окна события.

        Args:
            callback: Функция (event_name, event_description) -> None
        """
        self._show_window_callback = callback

    def _load_events_config(self) -> Dict[str, Any]:
        """
        Загрузить конфигурацию событий из JSON файла.

        Returns:
            Словарь с конфигурацией событий
        """
        config_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'quest_events_config.json'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Предупреждение: Файл конфигурации событий не найден: {config_path}")
            return {"events": {}}
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга конфигурации событий: {e}")
            return {"events": {}}

    def handle_event(self, event_id: str) -> bool:
        """
        Обработать событие по его ID.

        Args:
            event_id: ID события из конфига

        Returns:
            True если событие успешно обработано
        """
        events = self._events_config.get("events", {})
        event_config = events.get(str(event_id))

        if not event_config:
            print(f"Предупреждение: Событие {event_id} не найдено в конфигурации")
            return False

        event_type = event_config.get("type")
        event_name = event_config.get("name", f"Событие {event_id}")
        event_description = event_config.get("description", "")
        params = event_config.get("params", {})

        print(f"Событие: {event_name}")

        # Диспетчеризация по типу события
        handlers = {
            "add_companion": self._handle_add_companion,
            "add_item": self._handle_add_item,
            "add_gold": self._handle_add_gold,
            "add_experience": self._handle_add_experience,
            "change_reputation": self._handle_change_reputation,
        }

        handler = handlers.get(event_type)
        if handler:
            result = handler(params, event_config)
            # Показываем окно события если обработка успешна
            if result and self._show_window_callback:
                self._show_window_callback(event_name, event_description)
            return result
        else:
            print(f"Предупреждение: Неизвестный тип события: {event_type}")
            return False

    def _handle_add_companion(self, params: Dict[str, Any], event_config: Dict[str, Any]) -> bool:
        """
        Обработать событие добавления спутника.

        Args:
            params: Параметры события (companion_type, level)
            event_config: Полная конфигурация события

        Returns:
            True если спутник успешно добавлен
        """
        companion_type = params.get("companion_type")
        level = params.get("level", 1)

        if not companion_type:
            print("Ошибка: Не указан тип спутника")
            return False

        if not hasattr(self._player, 'companion_manager'):
            print("Ошибка: У игрока нет companion_manager")
            return False

        # Добавляем спутника
        companion = self._player.companion_manager.add_companion(companion_type, level)

        if companion:
            description = event_config.get("description", "")
            print(f"  {description}")
            print(f"  Новый спутник: {companion.name} (уровень {level})")
            return True
        else:
            print(f"Ошибка: Не удалось добавить спутника типа {companion_type}")
            return False

    def _handle_add_item(self, params: Dict[str, Any], event_config: Dict[str, Any]) -> bool:
        """
        Обработать событие добавления предмета.

        Args:
            params: Параметры события (item_id, amount)
            event_config: Полная конфигурация события

        Returns:
            True если предмет успешно добавлен
        """
        item_id = params.get("item_id")
        amount = params.get("amount", 1)

        if not item_id:
            print("Ошибка: Не указан ID предмета")
            return False

        from game.item_registry import get_item
        item = get_item(item_id)

        if item:
            added = self._player.inventory.add_item(item, amount)
            if added:
                print(f"  Получен предмет: {item.name} x{amount}")
                return True
            else:
                print(f"  Инвентарь полон, предмет {item.name} не добавлен")
                return False
        else:
            print(f"Ошибка: Предмет {item_id} не найден")
            return False

    def _handle_add_gold(self, params: Dict[str, Any], event_config: Dict[str, Any]) -> bool:
        """
        Обработать событие добавления золота.

        Args:
            params: Параметры события (amount)
            event_config: Полная конфигурация события

        Returns:
            True если золото успешно добавлено
        """
        amount = params.get("amount", 0)

        if amount <= 0:
            print("Ошибка: Некорректное количество золота")
            return False

        self._player.inventory.add_gold(amount)
        print(f"  Получено золото: {amount}")
        return True

    def _handle_add_experience(self, params: Dict[str, Any], event_config: Dict[str, Any]) -> bool:
        """
        Обработать событие добавления опыта.

        Args:
            params: Параметры события (amount)
            event_config: Полная конфигурация события

        Returns:
            True если опыт успешно добавлен
        """
        amount = params.get("amount", 0)

        if amount <= 0:
            print("Ошибка: Некорректное количество опыта")
            return False

        self._player.add_experience(amount)
        print(f"  Получен опыт: {amount}")
        return True

    def _handle_change_reputation(self, params: Dict[str, Any], event_config: Dict[str, Any]) -> bool:
        """
        Обработать событие изменения репутации.

        Args:
            params: Параметры события (location_id, amount)
            event_config: Полная конфигурация события

        Returns:
            True если репутация успешно изменена
        """
        location_id = params.get("location_id")
        amount = params.get("amount", 0)

        if not location_id:
            print("Ошибка: Не указан ID локации")
            return False

        # Репутацию локации нужно менять через game_map
        # Это будет реализовано при необходимости
        print(f"  Изменение репутации в локации {location_id}: {amount:+d}")
        return True

    def get_event_info(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о событии.

        Args:
            event_id: ID события

        Returns:
            Словарь с информацией о событии или None
        """
        events = self._events_config.get("events", {})
        return events.get(str(event_id))
