"""
Контроллер UI квестов.

Извлечено из engine.py для уменьшения сложности.
"""
from game.quest_system import get_unique_quest_for_location
from game.quest_system.generators.location import generate_quests_for_location


class QuestUIController:
    """Контроллер для управления UI квестов"""

    def __init__(self, player, quest_manager, quest_window, refresh_callback=None):
        """
        Инициализация контроллера квестов.

        Args:
            player: Объект игрока
            quest_manager: Менеджер квестов
            quest_window: Окно квестов
            refresh_callback: Функция для обновления окна квестов
        """
        self.player = player
        self.quest_manager = quest_manager
        self.quest_window = quest_window
        self.refresh_callback = refresh_callback
        self._quest_window_open = False

    @property
    def is_open(self):
        """Проверить, открыто ли окно квестов."""
        return self._quest_window_open

    @is_open.setter
    def is_open(self, value):
        """Установить состояние окна квестов."""
        self._quest_window_open = value

    def open_for_location(self, location):
        """
        Открыть окно квестов для локации.

        Args:
            location: Объект локации
        """
        location_id = f"{location.x}_{location.y}"

        # Отслеживаем посещение новых типов локаций для квеста "Исследователь"
        if location.location_type not in self.player.visited_location_types:
            self.player.visited_location_types.add(location.location_type)
            # Обновляем прогресс квеста "Исследователь"
            self.quest_manager.update_quest_progress("explorer_start", 0, 1)

        # Генерируем квесты для локации, если их еще нет
        if location_id not in self.quest_manager.location_quests:
            quests = generate_quests_for_location(
                location.name, location_id, self.player.level, count=3, location_type=location.location_type
            )
            for quest in quests:
                self.quest_manager.add_location_quest(location_id, quest)

            # Пробуем добавить уникальный квест
            unique_quest = get_unique_quest_for_location(
                location.location_type, location.name
            )
            if unique_quest:
                unique_quest.location_id = location_id
                self.quest_manager.add_location_quest(location_id, unique_quest)

        # Проверяем прогресс всех квестов на сбор ресурсов
        self.quest_manager.check_all_quest_progress(self.player)

        # Получаем данные для отображения
        available_quests = self.quest_manager.get_location_quests(location_id)

        # Фильтруем квесты по рангу игрока
        player_rank = self.player.get_rank_number()
        available_quests = [q for q in available_quests if getattr(q, 'min_rank', 1) <= player_rank]

        active_quests = self.quest_manager.get_active_quests()
        turn_in_quests = self.quest_manager.get_quests_ready_to_turn_in(location_id)

        # Устанавливаем данные в окно квестов
        self.quest_window.set_data(
            location.name,
            location_id,
            available_quests,
            active_quests,
            turn_in_quests
        )

        self._quest_window_open = True

    def open_anywhere(self):
        """
        Открыть окно квестов из любого места (только активные квесты).
        """
        # Проверяем прогресс всех квестов на сбор ресурсов
        self.quest_manager.check_all_quest_progress(self.player)

        # Получаем активные квесты
        active_quests = self.quest_manager.get_active_quests()

        # Устанавливаем данные в окно квестов
        self.quest_window.set_data(
            "Журнал квестов",
            None,
            [],
            active_quests,
            []
        )

        # Автоматически переключаем на вкладку активных квестов
        self.quest_window.mode = "active"

        self._quest_window_open = True

    def handle_action(self, action):
        """
        Обработка действий с квестами.

        Args:
            action: Тип действия ('accept', 'turn_in', 'abandon')
        """
        quest = self.quest_window.get_selected_quest()
        if not quest:
            return

        if action == 'accept':
            self._accept_quest(quest)
        elif action == 'turn_in':
            self._turn_in_quest(quest)
        elif action == 'abandon':
            self._abandon_quest(quest)

    def _accept_quest(self, quest):
        """Принять квест."""
        success, message = self.quest_manager.accept_quest(
            quest.quest_id,
            self.quest_window.location_id,
            self.player
        )
        print(message)
        if success and self.refresh_callback:
            self.refresh_callback()

    def _turn_in_quest(self, quest):
        """Сдать квест."""
        success, messages = self.quest_manager.complete_quest(
            quest.quest_id,
            self.player
        )
        if success:
            print(f"Квест '{quest.name}' завершён!")
            for msg in messages:
                print(f"  {msg}")
            if self.refresh_callback:
                self.refresh_callback()
        else:
            print("Не удалось сдать квест")

    def _abandon_quest(self, quest):
        """Отменить квест."""
        success, message = self.quest_manager.abandon_quest(quest.quest_id)
        print(message)
        if success and self.refresh_callback:
            self.refresh_callback()

    def close(self):
        """Закрыть окно квестов."""
        self._quest_window_open = False
