"""
Окно квестов.

Отображает доступные, активные и готовые к сдаче квесты.
"""
import pygame
from game.ui.base import UIHelper
from game.quests.quest_types import QuestType, DIFFICULTY_NAMES


class QuestWindow:
    """Окно квестов"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна квестов

        Args:
            screen: Поверхность pygame для отрисовки
            font: Основной шрифт
            info_font: Шрифт для информации
            ui_scaler: Масштабировщик UI (опционально)
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.ui_scaler = ui_scaler

        # Состояние окна
        self.mode = "available"  # available, active, turn_in
        self.selected_index = 0
        self.scroll_offset = 0

        # Данные
        self.location = None
        self.location_name = ""
        self.available_quests = []
        self.active_quests = []
        self.turn_in_quests = []

        # Для хранения координат элементов при рендеринге
        self.tab_rects = []
        self.quest_rects = []
        self.button_rects = {}
        self.window_rect = None

    def _scale_quest_value(self, base: int, scaling: float, difficulty: int, player_level: int) -> int:
        """
        Применить масштабирование к значению квеста.

        Использует ту же формулу, что и QuestInstance._scale().

        Args:
            base: Базовое значение
            scaling: Коэффициент масштабирования (1.0 - 2.0)
            difficulty: Сложность квеста (1-5)
            player_level: Уровень игрока

        Returns:
            Масштабированное значение (минимум 1)
        """
        diff_mult = 1.0 + (difficulty - 1) * 0.2
        level_mult = scaling ** (player_level - 1)
        return max(1, round(base * level_mult * diff_mult))

    def set_data(self, location_name, location, available_quests, active_quests, turn_in_quests, player=None):
        """
        Установить данные для отображения

        Args:
            location_name: Название локации
            location: Объект локации (или None для журнала)
            available_quests: Доступные квесты в локации (list of dict)
            active_quests: Активные квесты игрока (list of QuestInstance)
            turn_in_quests: Квесты готовые к сдаче (list of QuestInstance)
            player: Объект игрока (для проверки инвентаря)
        """
        self.location_name = location_name
        self.location = location
        self.available_quests = available_quests or []
        self.active_quests = active_quests or []
        self.turn_in_quests = turn_in_quests or []
        self.player = player
        self.selected_index = 0
        self.scroll_offset = 0

        # Если есть квесты для сдачи, открываем на этой вкладке
        if turn_in_quests:
            self.mode = "turn_in"
        elif available_quests:
            self.mode = "available"
        else:
            self.mode = "active"

    def get_current_list(self):
        """Получить текущий список квестов"""
        if self.mode == "available":
            return self.available_quests
        elif self.mode == "active":
            return self.active_quests
        else:
            return self.turn_in_quests

    def get_selected_quest(self):
        """Получить выбранный квест"""
        quests = self.get_current_list()
        if quests and 0 <= self.selected_index < len(quests):
            return quests[self.selected_index]
        return None

    def handle_mouse_event(self, event, game):
        """
        Обработка событий мыши в окне квестов

        Args:
            event: Событие pygame
            game: Объект игры

        Returns:
            str: Действие для выполнения или None
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Проверяем клик по вкладкам
            for i, rect in enumerate(self.tab_rects):
                if rect.collidepoint(mouse_pos):
                    modes = ["available", "active", "turn_in"]
                    self.mode = modes[i]
                    self.selected_index = 0
                    self.scroll_offset = 0
                    return None

            # Проверяем клик по квестам в списке
            for i, rect in enumerate(self.quest_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = i + self.scroll_offset
                    return None

            # Проверяем клик по кнопкам действий
            for action, rect in self.button_rects.items():
                if rect.collidepoint(mouse_pos):
                    return action

            # Прокрутка колёсиком мыши
            if event.button == 4:  # Колёсико вверх
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
                return None
            elif event.button == 5:  # Колёсико вниз
                quests = self.get_current_list()
                if self.window_rect:
                    quest_height = 80
                    list_height = self.window_rect.height - 200
                    visible_quests = list_height // quest_height
                    max_scroll = max(0, len(quests) - visible_quests)
                    if self.scroll_offset < max_scroll:
                        self.scroll_offset += 1
                return None

        return None

    def _get_quest_type_name(self, quest_type):
        """Получить название типа квеста"""
        type_names = {
            QuestType.GATHER_RESOURCE: "Добыча ресурсов",
            QuestType.HUNT_ANIMALS: "Охота",
            QuestType.DELIVER_MESSAGE: "Доставка",
            QuestType.CLEAR_LOCATION: "Зачистка",
            QuestType.COLLECT_ITEMS: "Сбор предметов",
            "gather_resource": "Добыча ресурсов",
            "hunt_animals": "Охота",
            "deliver_message": "Доставка",
            "clear_location": "Зачистка",
            "collect_items": "Сбор предметов",
        }
        return type_names.get(quest_type, "Квест")

    def _get_difficulty_color(self, difficulty):
        """Получить цвет для сложности"""
        colors = {
            1: (100, 255, 100),  # Легкий - зеленый
            2: (200, 200, 100),  # Нормальный - желтый
            3: (255, 165, 0),    # Сложный - оранжевый
            4: (255, 100, 100),  # Очень сложный - красный
            5: (200, 50, 200),   # Экстремальный - фиолетовый
        }
        return colors.get(difficulty, (200, 200, 200))

    def render(self, player):
        """Отрисовать окно квестов"""
        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(1260)
            window_height = self.ui_scaler.scale_height(780)
        else:
            window_width = min(1260, int(screen_width * 0.85))
            window_height = min(780, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Сохраняем прямоугольник окна
        self.window_rect = pygame.Rect(window_x, window_y, window_width, window_height)

        # Очищаем списки прямоугольников
        self.tab_rects = []
        self.quest_rects = []
        self.button_rects = {}

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (200, 180, 100),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render(
            f"КВЕСТЫ - {self.location_name}",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Вкладки
        tab_y = window_y + 55
        tab_width = (window_width - 60) // 3
        tabs = [
            ("Доступные", "available", len(self.available_quests)),
            ("Активные", "active", len(self.active_quests)),
            ("Готовые к сдаче", "turn_in", len(self.turn_in_quests))
        ]

        for i, (tab_name, tab_mode, count) in enumerate(tabs):
            tab_x = window_x + 20 + i * (tab_width + 10)
            is_selected = self.mode == tab_mode

            # Сохраняем прямоугольник вкладки
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, 30)
            self.tab_rects.append(tab_rect)

            # Фон вкладки
            tab_color = (80, 80, 90) if is_selected else (50, 50, 55)
            pygame.draw.rect(self.screen, tab_color, (tab_x, tab_y, tab_width, 30))

            # Рамка вкладки
            border_color = (255, 215, 0) if is_selected else (100, 100, 100)
            pygame.draw.rect(self.screen, border_color, (tab_x, tab_y, tab_width, 30), 2)

            # Текст вкладки
            text_color = (255, 215, 0) if is_selected else (180, 180, 180)
            tab_text = self.info_font.render(f"{tab_name} ({count})", True, text_color)
            tab_text_rect = tab_text.get_rect()
            tab_text_rect.centerx = tab_x + tab_width // 2
            tab_text_rect.centery = tab_y + 15
            self.screen.blit(tab_text, tab_text_rect)

        # Область списка квестов
        list_y = tab_y + 45
        list_height = window_height - 200
        list_width = window_width // 2 - 30

        # Фон списка
        pygame.draw.rect(
            self.screen,
            (30, 30, 35),
            (window_x + 20, list_y, list_width, list_height)
        )
        pygame.draw.rect(
            self.screen,
            (80, 80, 90),
            (window_x + 20, list_y, list_width, list_height),
            1
        )

        # Отрисовка списка квестов
        quests = self.get_current_list()
        quest_height = 80
        visible_quests = list_height // quest_height

        if not quests:
            # Пустой список
            empty_text = self.info_font.render("Нет квестов", True, (150, 150, 150))
            empty_rect = empty_text.get_rect()
            empty_rect.centerx = window_x + 20 + list_width // 2
            empty_rect.centery = list_y + list_height // 2
            self.screen.blit(empty_text, empty_rect)
        else:
            # Отрисовываем квесты
            for i in range(min(visible_quests, len(quests) - self.scroll_offset)):
                quest_index = i + self.scroll_offset
                if quest_index >= len(quests):
                    break

                quest = quests[quest_index]
                quest_y = list_y + i * quest_height + 5
                quest_x = window_x + 25

                # Определяем данные квеста (разные для конфига и экземпляра)
                if self.mode == "available":
                    # Это dict конфига - применяем масштабирование для отображения
                    name = quest.get('name', 'Неизвестный квест')
                    quest_type = quest.get('quest_type', '')
                    difficulty = quest.get('difficulty', 1)
                    scaling = quest.get('scaling_factor', 1.1)
                    player_level = self.player.level if self.player else 1
                    # Масштабируем награды для корректного отображения
                    reward_gold = self._scale_quest_value(
                        quest.get('reward_gold', 0), scaling, difficulty, player_level
                    )
                    reward_exp = self._scale_quest_value(
                        quest.get('reward_exp', 0), scaling, difficulty, player_level
                    )
                    time_limit = quest.get('time_limit', 0)
                else:
                    # Это QuestInstance
                    name = quest.name
                    quest_type = quest.quest_type
                    difficulty = quest.difficulty
                    reward_gold = quest.reward_gold
                    reward_exp = quest.reward_exp
                    time_limit = quest.time_limit

                is_selected = quest_index == self.selected_index

                # Сохраняем прямоугольник квеста
                quest_rect = pygame.Rect(quest_x - 5, quest_y, list_width - 10, quest_height - 5)
                self.quest_rects.append(quest_rect)

                # Фон квеста
                bg_color = (60, 60, 70) if is_selected else (45, 45, 50)
                pygame.draw.rect(self.screen, bg_color, quest_rect)

                # Рамка выделенного квеста
                if is_selected:
                    pygame.draw.rect(self.screen, (255, 215, 0), quest_rect, 2)

                # Название квеста
                name_text = self.info_font.render(name[:30], True, (255, 255, 255))
                self.screen.blit(name_text, (quest_x, quest_y + 5))

                # Тип квеста и сложность
                type_name = self._get_quest_type_name(quest_type)
                diff_name = DIFFICULTY_NAMES.get(difficulty, "Неизвестно")
                diff_color = self._get_difficulty_color(difficulty)

                type_text = self.info_font.render(f"{type_name}", True, (150, 150, 150))
                self.screen.blit(type_text, (quest_x, quest_y + 25))

                diff_text = self.info_font.render(f"[{diff_name}]", True, diff_color)
                self.screen.blit(diff_text, (quest_x + 150, quest_y + 25))

                # Награды
                rewards = []
                if reward_gold > 0:
                    rewards.append(f"{reward_gold}g")
                if reward_exp > 0:
                    rewards.append(f"{reward_exp}xp")
                rewards_str = " ".join(rewards)
                rewards_text = self.info_font.render(rewards_str, True, (200, 180, 100))
                self.screen.blit(rewards_text, (quest_x, quest_y + 45))

                # Время (если есть)
                if time_limit > 0:
                    if self.mode == "available":
                        time_str = f"Время: {time_limit} ходов"
                    else:
                        time_str = f"Осталось: {quest.time_remaining} ходов"
                    time_color = (255, 100, 100) if self.mode != "available" and quest.time_remaining < 20 else (150, 150, 150)
                    time_text = self.info_font.render(time_str, True, time_color)
                    self.screen.blit(time_text, (quest_x + 150, quest_y + 45))

                # Прогресс для активных квестов
                if self.mode in ("active", "turn_in") and hasattr(quest, 'get_progress_text'):
                    progress_text = self.info_font.render(
                        quest.get_progress_text(self.player),
                        True,
                        (100, 255, 100) if quest.is_complete(self.player) else (200, 200, 200)
                    )
                    self.screen.blit(progress_text, (quest_x + list_width - 150, quest_y + 25))

        # Область детальной информации
        detail_x = window_x + window_width // 2 + 10
        detail_width = window_width // 2 - 30

        pygame.draw.rect(
            self.screen,
            (30, 30, 35),
            (detail_x, list_y, detail_width, list_height)
        )
        pygame.draw.rect(
            self.screen,
            (80, 80, 90),
            (detail_x, list_y, detail_width, list_height),
            1
        )

        # Отображаем детали выбранного квеста
        selected_quest = self.get_selected_quest()
        if selected_quest:
            self._render_quest_details(selected_quest, detail_x, list_y, detail_width, list_height)

        # Кнопки действий
        buttons_y = window_y + window_height - 60
        button_width = 150
        button_height = 35

        if self.mode == "available" and selected_quest:
            # Кнопка "Принять"
            accept_rect = pygame.Rect(
                window_x + window_width // 2 - button_width - 10,
                buttons_y,
                button_width,
                button_height
            )
            pygame.draw.rect(self.screen, (60, 120, 60), accept_rect)
            pygame.draw.rect(self.screen, (100, 200, 100), accept_rect, 2)
            accept_text = self.info_font.render("Принять", True, (255, 255, 255))
            accept_text_rect = accept_text.get_rect(center=accept_rect.center)
            self.screen.blit(accept_text, accept_text_rect)
            self.button_rects['accept'] = accept_rect

        elif self.mode == "active" and selected_quest:
            # Кнопка "Отказаться"
            abandon_rect = pygame.Rect(
                window_x + window_width // 2 - button_width - 10,
                buttons_y,
                button_width,
                button_height
            )
            pygame.draw.rect(self.screen, (120, 60, 60), abandon_rect)
            pygame.draw.rect(self.screen, (200, 100, 100), abandon_rect, 2)
            abandon_text = self.info_font.render("Отказаться", True, (255, 255, 255))
            abandon_text_rect = abandon_text.get_rect(center=abandon_rect.center)
            self.screen.blit(abandon_text, abandon_text_rect)
            self.button_rects['abandon'] = abandon_rect

        elif self.mode == "turn_in" and selected_quest:
            # Кнопка "Сдать"
            turn_in_rect = pygame.Rect(
                window_x + window_width // 2 - button_width - 10,
                buttons_y,
                button_width,
                button_height
            )
            pygame.draw.rect(self.screen, (120, 100, 60), turn_in_rect)
            pygame.draw.rect(self.screen, (200, 180, 100), turn_in_rect, 2)
            turn_in_text = self.info_font.render("Сдать квест", True, (255, 255, 255))
            turn_in_text_rect = turn_in_text.get_rect(center=turn_in_rect.center)
            self.screen.blit(turn_in_text, turn_in_text_rect)
            self.button_rects['turn_in'] = turn_in_rect

        # Кнопка "Закрыть"
        close_rect = pygame.Rect(
            window_x + window_width // 2 + 10,
            buttons_y,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (60, 60, 70), close_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), close_rect, 2)
        close_text = self.info_font.render("Закрыть", True, (200, 200, 200))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)
        self.button_rects['close'] = close_rect

        # Подсказки управления
        controls_text = self.info_font.render(
            "Tab - Вкладки | Enter - Действие | Esc - Закрыть",
            True,
            (150, 150, 150)
        )
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = window_x + window_width // 2
        controls_rect.y = window_y + window_height - 25
        self.screen.blit(controls_text, controls_rect)

    def _render_quest_details(self, quest, x, y, width, height):
        """Отрисовать детальную информацию о квесте"""
        padding = 15
        line_y = y + padding

        # Определяем данные квеста
        if self.mode == "available":
            # Это dict конфига - применяем масштабирование для корректного отображения
            name = quest.get('name', 'Неизвестный квест')
            description = quest.get('description', 'Нет описания')
            quest_type = quest.get('quest_type', '')
            difficulty = quest.get('difficulty', 1)
            scaling = quest.get('scaling_factor', 1.1)
            player_level = self.player.level if self.player else 1
            target_type = quest.get('target_type', '')
            # Масштабируем количество целей
            target_amount = self._scale_quest_value(
                quest.get('target_amount', 0), scaling, difficulty, player_level
            )
            target_item_id = quest.get('target_item_id', '')
            target_location_name = quest.get('target_location_name', '')
            target_floor = quest.get('target_floor', 0)
            # Масштабируем награды
            reward_gold = self._scale_quest_value(
                quest.get('reward_gold', 0), scaling, difficulty, player_level
            )
            reward_exp = self._scale_quest_value(
                quest.get('reward_exp', 0), scaling, difficulty, player_level
            )
            reward_reputation = quest.get('reward_reputation', 0)
            reward_item_id = quest.get('reward_item_id', '')
            reward_item_amount = quest.get('reward_item_amount', 0)
            time_limit = quest.get('time_limit', 0)
            is_repeatable = quest.get('is_repeatable', True)
            cooldown = quest.get('cooldown', 0)
        else:
            # Это QuestInstance
            name = quest.name
            description = quest.description
            quest_type = quest.quest_type
            difficulty = quest.difficulty
            target_type = quest.target_type
            target_amount = quest.target_amount
            target_item_id = quest.target_item_id
            target_location_name = quest.target_location_name
            target_floor = quest.target_floor
            reward_gold = quest.reward_gold
            reward_exp = quest.reward_exp
            reward_reputation = quest.reward_reputation
            reward_item_id = quest.reward_item_id
            reward_item_amount = quest.reward_item_amount
            time_limit = quest.time_limit
            is_repeatable = quest.is_repeatable
            cooldown = quest.cooldown

        # Название
        name_text = self.font.render(name, True, (255, 215, 0))
        self.screen.blit(name_text, (x + padding, line_y))
        line_y += 35

        # Тип и сложность
        type_name = self._get_quest_type_name(quest_type)
        diff_name = DIFFICULTY_NAMES.get(difficulty, "Неизвестно")
        diff_color = self._get_difficulty_color(difficulty)

        type_text = self.info_font.render(f"Тип: {type_name}", True, (180, 180, 180))
        self.screen.blit(type_text, (x + padding, line_y))
        line_y += 22

        diff_text = self.info_font.render(f"Сложность: {diff_name}", True, diff_color)
        self.screen.blit(diff_text, (x + padding, line_y))
        line_y += 30

        # Разделитель
        pygame.draw.line(
            self.screen,
            (80, 80, 90),
            (x + padding, line_y),
            (x + width - padding, line_y)
        )
        line_y += 10

        # Описание
        desc_label = self.info_font.render("Описание:", True, (150, 150, 150))
        self.screen.blit(desc_label, (x + padding, line_y))
        line_y += 22

        # Разбиваем описание на строки
        max_width = width - padding * 2
        words = description.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            test_text = self.info_font.render(test_line, True, (255, 255, 255))
            if test_text.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for line in lines[:4]:  # Максимум 4 строки
            line_text = self.info_font.render(line, True, (200, 200, 200))
            self.screen.blit(line_text, (x + padding, line_y))
            line_y += 20
        line_y += 10

        # Цель квеста
        pygame.draw.line(
            self.screen,
            (80, 80, 90),
            (x + padding, line_y),
            (x + width - padding, line_y)
        )
        line_y += 10

        goal_label = self.info_font.render("Цель:", True, (150, 150, 150))
        self.screen.blit(goal_label, (x + padding, line_y))
        line_y += 22

        # Формируем текст цели в зависимости от типа
        goal_text = ""
        if quest_type in (QuestType.GATHER_RESOURCE, "gather_resource"):
            goal_text = f"Собрать {target_type}: {target_amount}"
        elif quest_type in (QuestType.HUNT_ANIMALS, "hunt_animals"):
            goal_text = f"Убить {target_type}: {target_amount}"
        elif quest_type in (QuestType.COLLECT_ITEMS, "collect_items"):
            goal_text = f"Собрать предмет ({target_item_id}): {target_amount}"
        elif quest_type in (QuestType.DELIVER_MESSAGE, "deliver_message"):
            goal_text = f"Доставить послание в: {target_location_name}"
        elif quest_type in (QuestType.CLEAR_LOCATION, "clear_location"):
            if target_floor == 0:
                goal_text = f"Зачистить все этажи: {target_location_name}"
            else:
                goal_text = f"Зачистить этаж {target_floor}: {target_location_name}"

        goal_text_render = self.info_font.render(goal_text, True, (200, 200, 200))
        self.screen.blit(goal_text_render, (x + padding, line_y))
        line_y += 25

        # Прогресс для активных квестов
        if self.mode in ("active", "turn_in") and hasattr(quest, 'get_progress_text'):
            progress_label = self.info_font.render("Прогресс:", True, (150, 150, 150))
            self.screen.blit(progress_label, (x + padding, line_y))
            line_y += 22

            progress_color = (100, 255, 100) if quest.is_complete(self.player) else (200, 200, 100)
            progress_text = self.info_font.render(quest.get_progress_text(self.player), True, progress_color)
            self.screen.blit(progress_text, (x + padding, line_y))
            line_y += 25

        # Разделитель
        pygame.draw.line(
            self.screen,
            (80, 80, 90),
            (x + padding, line_y),
            (x + width - padding, line_y)
        )
        line_y += 10

        # Награды
        reward_label = self.info_font.render("Награда:", True, (150, 150, 150))
        self.screen.blit(reward_label, (x + padding, line_y))
        line_y += 22

        if reward_gold > 0:
            gold_text = self.info_font.render(f"Золото: {reward_gold}", True, (255, 215, 0))
            self.screen.blit(gold_text, (x + padding, line_y))
            line_y += 20

        if reward_exp > 0:
            exp_text = self.info_font.render(f"Опыт: {reward_exp}", True, (100, 200, 255))
            self.screen.blit(exp_text, (x + padding, line_y))
            line_y += 20

        if reward_reputation > 0:
            rep_text = self.info_font.render(f"Репутация: +{reward_reputation}", True, (100, 255, 100))
            self.screen.blit(rep_text, (x + padding, line_y))
            line_y += 20

        if reward_item_id:
            item_text = self.info_font.render(f"Предмет: {reward_item_id} x{reward_item_amount}", True, (200, 150, 255))
            self.screen.blit(item_text, (x + padding, line_y))
            line_y += 20

        line_y += 10

        # Дополнительная информация
        if time_limit > 0:
            if self.mode == "available":
                time_text = self.info_font.render(f"Лимит времени: {time_limit} ходов", True, (255, 165, 0))
            else:
                time_color = (255, 100, 100) if quest.time_remaining < 20 else (255, 165, 0)
                time_text = self.info_font.render(f"Осталось времени: {quest.time_remaining} ходов", True, time_color)
            self.screen.blit(time_text, (x + padding, line_y))
            line_y += 20

        repeat_text = "Повторяемый" if is_repeatable else "Одноразовый"
        repeat_color = (100, 200, 100) if is_repeatable else (200, 100, 100)
        repeat_render = self.info_font.render(repeat_text, True, repeat_color)
        self.screen.blit(repeat_render, (x + padding, line_y))

        if is_repeatable and cooldown > 0:
            cooldown_text = self.info_font.render(f"(Кулдаун: {cooldown} ходов)", True, (150, 150, 150))
            self.screen.blit(cooldown_text, (x + padding + 120, line_y))
