"""
Окно квестов.
"""
import pygame
from game.ui.base import UIHelper


class QuestWindow:
    """Окно квестов города"""

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
        self.location_name = ""
        self.location_id = None
        self.available_quests = []
        self.active_quests = []
        self.turn_in_quests = []

        # Для хранения координат элементов при рендеринге
        self.tab_rects = []      # Прямоугольники вкладок
        self.quest_rects = []    # Прямоугольники квестов
        self.window_rect = None  # Прямоугольник окна

    def set_data(self, location_name, location_id, available_quests, active_quests, turn_in_quests):
        """
        Установить данные для отображения

        Args:
            location_name: Название локации
            location_id: ID локации
            available_quests: Доступные квесты в локации
            active_quests: Активные квесты игрока
            turn_in_quests: Квесты готовые к сдаче
        """
        self.location_name = location_name
        self.location_id = location_id
        self.available_quests = available_quests
        self.active_quests = active_quests
        self.turn_in_quests = turn_in_quests
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
            str: Действие для выполнения ('accept', 'turn_in', 'abandon') или None
        """
        import pygame

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

            # Проверяем клик по квестам
            for i, rect in enumerate(self.quest_rects):
                if rect.collidepoint(mouse_pos):
                    quest_idx = i + self.scroll_offset
                    quests = self.get_current_list()
                    if quest_idx < len(quests):
                        self.selected_index = quest_idx

                        # Левая кнопка - выбор, двойной клик - действие
                        if event.button == 1:
                            # Проверяем двойной клик
                            if hasattr(self, '_last_click_time'):
                                import time
                                if time.time() - self._last_click_time < 0.3:
                                    # Двойной клик - выполняем действие
                                    if self.mode == "available":
                                        return 'accept'
                                    elif self.mode == "turn_in":
                                        return 'turn_in'
                            import time
                            self._last_click_time = time.time()

                        # Правая кнопка - действие
                        elif event.button == 3:
                            if self.mode == "available":
                                return 'accept'
                            elif self.mode == "active":
                                return 'abandon'
                            elif self.mode == "turn_in":
                                return 'turn_in'
                    return None

            # Прокрутка колёсиком мыши
            if event.button == 4:  # Колёсико вверх
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
                return None
            elif event.button == 5:  # Колёсико вниз
                quests = self.get_current_list()
                # Определяем количество видимых квестов
                if self.window_rect:
                    quest_height = 95
                    list_height = self.window_rect.height - 200
                    visible_quests = list_height // quest_height
                    max_scroll = max(0, len(quests) - visible_quests)
                    if self.scroll_offset < max_scroll:
                        self.scroll_offset += 1
                return None

        return None

    def render(self, player):
        """Отрисовать окно квестов"""
        import pygame
        from game.quest_system.models import QuestStatus

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

        # Информация о лимите квестов
        from game.config.config_loader import get_quest_config
        config = get_quest_config()
        max_active = config.get_quest_limit('max_active_quests', default=5)
        limit_text = self.info_font.render(
            f"Активных квестов: {len(self.active_quests)}/{max_active}",
            True,
            (150, 150, 150)
        )
        self.screen.blit(limit_text, (window_x + 20, window_y + 50))

        # Вкладки
        tab_y = window_y + 75
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
            pygame.draw.rect(
                self.screen,
                tab_color,
                (tab_x, tab_y, tab_width, 30)
            )

            # Рамка вкладки
            border_color = (255, 215, 0) if is_selected else (100, 100, 100)
            pygame.draw.rect(
                self.screen,
                border_color,
                (tab_x, tab_y, tab_width, 30),
                2
            )

            # Текст вкладки
            text_color = (255, 215, 0) if is_selected else (180, 180, 180)
            tab_text = self.info_font.render(
                f"{tab_name} ({count})",
                True,
                text_color
            )
            tab_text_rect = tab_text.get_rect()
            tab_text_rect.centerx = tab_x + tab_width // 2
            tab_text_rect.centery = tab_y + 15
            self.screen.blit(tab_text, tab_text_rect)

        # Область списка квестов
        list_y = tab_y + 45
        list_height = window_height - 200
        list_width = window_width - 40

        # Фон списка
        pygame.draw.rect(
            self.screen,
            (30, 30, 35),
            (window_x + 20, list_y, list_width, list_height)
        )

        # Текущий список квестов
        quests = self.get_current_list()

        if not quests:
            no_quests_text = self.info_font.render(
                "Нет доступных квестов" if self.mode == "available"
                else "Нет активных квестов" if self.mode == "active"
                else "Нет квестов для сдачи",
                True,
                (150, 150, 150)
            )
            no_quests_rect = no_quests_text.get_rect()
            no_quests_rect.centerx = window_x + window_width // 2
            no_quests_rect.centery = list_y + list_height // 2
            self.screen.blit(no_quests_text, no_quests_rect)
        else:
            # Отображаем список квестов
            quest_height = 95

            # Для активных квестов используем два столбца
            if self.mode == "active":
                # Два столбца по 5 квестов
                column_width = (list_width - 30) // 2
                quests_per_column = 5
                visible_quests = quests_per_column * 2

                for i in range(min(visible_quests, len(quests))):
                    quest_idx = i + self.scroll_offset
                    if quest_idx >= len(quests):
                        break

                    quest = quests[quest_idx]

                    # Определяем столбец и позицию в столбце
                    column = i // quests_per_column
                    row = i % quests_per_column

                    quest_x = window_x + 25 + column * (column_width + 10)
                    quest_y = list_y + row * quest_height

                    # Сохраняем прямоугольник квеста
                    quest_rect = pygame.Rect(quest_x, quest_y + 5, column_width - 10, quest_height - 10)
                    self.quest_rects.append(quest_rect)

                    # Фон элемента
                    is_selected = quest_idx == self.selected_index
                    is_unique = getattr(quest, 'is_unique', False)
                    is_starter = getattr(quest, 'is_starter', False)

                    # Цвет фона: уникальные - темно-красный, стартовые - темно-зеленый, обычные - серый
                    if is_unique:
                        bg_color = (70, 40, 40) if is_selected else (50, 30, 30)
                    elif is_starter:
                        bg_color = (40, 60, 40) if is_selected else (30, 45, 30)
                    else:
                        bg_color = (60, 60, 70) if is_selected else (40, 40, 45)

                    pygame.draw.rect(
                        self.screen,
                        bg_color,
                        (quest_x, quest_y + 5, column_width - 10, quest_height - 10)
                    )

                    # Рамка: уникальные - красная, стартовые - зеленая, выбранные - золотая
                    if is_unique:
                        border_color = (255, 100, 100) if is_selected else (200, 50, 50)
                        pygame.draw.rect(
                            self.screen,
                            border_color,
                            (quest_x, quest_y + 5, column_width - 10, quest_height - 10),
                            3 if is_selected else 2
                        )
                    elif is_starter:
                        border_color = (100, 255, 100) if is_selected else (50, 200, 50)
                        pygame.draw.rect(
                            self.screen,
                            border_color,
                            (quest_x, quest_y + 5, column_width - 10, quest_height - 10),
                            3 if is_selected else 2
                        )
                    elif is_selected:
                        pygame.draw.rect(
                            self.screen,
                            (255, 215, 0),
                            (quest_x, quest_y + 5, column_width - 10, quest_height - 10),
                            2
                        )

                    # Название квеста с цветом по типу
                    difficulty_str = f" [{quest.difficulty.display_name}]" if hasattr(quest.difficulty, 'display_name') else ""
                    if is_unique:
                        name_color = (255, 150, 150)
                    elif is_starter:
                        name_color = (150, 255, 150)
                    else:
                        name_color = (255, 255, 255)

                    # Укорачиваем название для компактности в двух столбцах
                    max_name_len = 20
                    quest_name = quest.name[:max_name_len] + "..." if len(quest.name) > max_name_len else quest.name
                    name_text = self.font.render(
                        f"{quest_name}",
                        True,
                        name_color
                    )
                    self.screen.blit(name_text, (quest_x + 10, quest_y + 10))

                    # Описание (укороченное)
                    max_desc_len = 30
                    desc_text = self.info_font.render(
                        quest.description[:max_desc_len] + "..." if len(quest.description) > max_desc_len else quest.description,
                        True,
                        (180, 180, 180)
                    )
                    self.screen.blit(desc_text, (quest_x + 10, quest_y + 32))

                    # Цели
                    if quest.objectives:
                        from game.quest_system.models import QuestType
                        obj = quest.objectives[0]

                        # Для квестов на сбор ресурсов всегда показываем количество из инвентаря
                        if quest.target_item and player:
                            inventory_count = player.inventory.get_item_count(quest.target_item)
                            progress = f"{inventory_count}/{obj.required_count}"
                            is_objective_complete = inventory_count >= obj.required_count
                        else:
                            progress = f"{obj.current_count}/{obj.required_count}"
                            is_objective_complete = obj.is_completed()

                        obj_text = self.info_font.render(
                            f"({progress})",
                            True,
                            (100, 255, 100) if is_objective_complete else (200, 200, 100)
                        )
                        self.screen.blit(obj_text, (quest_x + 10, quest_y + 54))

                    # Награды
                    rewards_parts = []
                    if 'exp' in quest.rewards:
                        rewards_parts.append(f"{quest.rewards['exp']} XP")
                    if 'gold' in quest.rewards:
                        rewards_parts.append(f"{quest.rewards['gold']}g")
                    rewards_str = " | ".join(rewards_parts)

                    rewards_text = self.info_font.render(
                        rewards_str,
                        True,
                        (255, 215, 0)
                    )
                    self.screen.blit(rewards_text, (quest_x + 10, quest_y + 76))
            else:
                # Для остальных режимов - один столбец
                visible_quests = list_height // quest_height

                for i in range(min(visible_quests, len(quests))):
                    quest_idx = i + self.scroll_offset
                    if quest_idx >= len(quests):
                        break

                    quest = quests[quest_idx]
                    quest_y = list_y + i * quest_height

                    # Сохраняем прямоугольник квеста
                    quest_rect = pygame.Rect(window_x + 25, quest_y + 5, list_width - 10, quest_height - 10)
                    self.quest_rects.append(quest_rect)

                    # Фон элемента
                    is_selected = quest_idx == self.selected_index
                    is_unique = getattr(quest, 'is_unique', False)
                    is_starter = getattr(quest, 'is_starter', False)

                    # Цвет фона: уникальные - темно-красный, стартовые - темно-зеленый, обычные - серый
                    if is_unique:
                        bg_color = (70, 40, 40) if is_selected else (50, 30, 30)
                    elif is_starter:
                        bg_color = (40, 60, 40) if is_selected else (30, 45, 30)
                    else:
                        bg_color = (60, 60, 70) if is_selected else (40, 40, 45)

                    pygame.draw.rect(
                        self.screen,
                        bg_color,
                        (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10)
                    )

                    # Рамка: уникальные - красная, стартовые - зеленая, выбранные - золотая
                    if is_unique:
                        # Красная рамка для уникальных квестов (всегда)
                        border_color = (255, 100, 100) if is_selected else (200, 50, 50)
                        pygame.draw.rect(
                            self.screen,
                            border_color,
                            (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                            3 if is_selected else 2
                        )
                    elif is_starter:
                        # Зеленая рамка для стартовых квестов (всегда)
                        border_color = (100, 255, 100) if is_selected else (50, 200, 50)
                        pygame.draw.rect(
                            self.screen,
                            border_color,
                            (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                            3 if is_selected else 2
                        )
                    elif is_selected:
                        # Золотая рамка только для выбранных обычных квестов
                        pygame.draw.rect(
                            self.screen,
                            (255, 215, 0),
                            (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                            2
                        )

                    # Название квеста с цветом по типу
                    difficulty_str = f" [{quest.difficulty.display_name}]" if hasattr(quest.difficulty, 'display_name') else ""
                    if is_unique:
                        name_color = (255, 150, 150)  # Красноватый для уникальных
                    elif is_starter:
                        name_color = (150, 255, 150)  # Зеленоватый для стартовых
                    else:
                        name_color = (255, 255, 255)  # Белый для обычных

                    name_text = self.font.render(
                        f"{quest.name}{difficulty_str}",
                        True,
                        name_color
                    )
                    self.screen.blit(name_text, (window_x + 35, quest_y + 10))

                    # Место выдачи квеста (если есть)
                    if quest.giver_location:
                        giver_text = self.info_font.render(
                            f"Место: {quest.giver_location}",
                            True,
                            (150, 200, 255)
                        )
                        self.screen.blit(giver_text, (window_x + 35, quest_y + 32))
                        desc_y_offset = 50
                    else:
                        desc_y_offset = 32

                    # Описание
                    desc_text = self.info_font.render(
                        quest.description[:60] + "..." if len(quest.description) > 60 else quest.description,
                        True,
                        (180, 180, 180)
                    )
                    self.screen.blit(desc_text, (window_x + 35, quest_y + desc_y_offset))

                    # Цели и награды
                    if quest.objectives:
                        from game.quest_system.models import QuestType
                        obj = quest.objectives[0]

                        # Для квестов где требуются предметы, показываем количество в инвентаре
                        # Это включает квесты на сбор ресурсов и квесты на убийство животных (части животных)
                        if quest.target_item and player:
                            inventory_count = player.inventory.get_item_count(quest.target_item)
                            progress = f"{inventory_count}/{obj.required_count}"
                            is_objective_complete = inventory_count >= obj.required_count
                        else:
                            progress = f"{obj.current_count}/{obj.required_count}"
                            is_objective_complete = obj.is_completed()

                        obj_text = self.info_font.render(
                            f"Цель: {obj.description[:30]}... ({progress})" if len(obj.description) > 30
                            else f"Цель: {obj.description} ({progress})",
                            True,
                            (100, 255, 100) if is_objective_complete else (200, 200, 100)
                        )
                        obj_y_offset = desc_y_offset + 22
                        self.screen.blit(obj_text, (window_x + 35, quest_y + obj_y_offset))

                    # Награды (справа)
                    rewards_parts = []
                    if 'exp' in quest.rewards:
                        rewards_parts.append(f"{quest.rewards['exp']} XP")
                    if 'gold' in quest.rewards:
                        rewards_parts.append(f"{quest.rewards['gold']}g")
                    rewards_str = " | ".join(rewards_parts)

                    rewards_text = self.info_font.render(
                        rewards_str,
                        True,
                        (255, 215, 0)
                    )
                    rewards_rect = rewards_text.get_rect()
                    rewards_rect.right = window_x + window_width - 35
                    rewards_rect.y = quest_y + 32
                    self.screen.blit(rewards_text, rewards_rect)

        # Подсказки управления
        controls_y = window_y + window_height - 50

        if self.mode == "available":
            action_text = "Enter/ПКМ - Принять"
        elif self.mode == "active":
            action_text = "Delete/ПКМ - Отменить"
        else:
            action_text = "Enter/ПКМ - Сдать"

        controls_text = self.info_font.render(
            f"Tab/Клик - Вкладки | W/S/Колёсико - Выбор | {action_text} | Esc - Закрыть",
            True,
            (150, 150, 150)
        )
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = window_x + window_width // 2
        controls_rect.y = controls_y
        self.screen.blit(controls_text, controls_rect)


