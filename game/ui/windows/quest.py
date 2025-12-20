"""
Окно квестов.

Система квестов на переработке - окно показывает заглушку.
"""
import pygame
from game.ui.base import UIHelper


class QuestWindow:
    """Окно квестов (система квестов на переработке)"""

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

            # Прокрутка колёсиком мыши
            if event.button == 4:  # Колёсико вверх
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
                return None
            elif event.button == 5:  # Колёсико вниз
                quests = self.get_current_list()
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

        # Информация о системе квестов
        info_text = self.info_font.render(
            "Система квестов на переработке",
            True,
            (200, 150, 100)
        )
        self.screen.blit(info_text, (window_x + 20, window_y + 50))

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

        # Сообщение о переработке системы квестов
        message_lines = [
            "Система квестов находится на переработке.",
            "",
            "Новая система квестов будет доступна в следующем обновлении.",
            "Приносим извинения за временные неудобства."
        ]

        line_y = list_y + list_height // 2 - len(message_lines) * 15
        for line in message_lines:
            if line:
                line_text = self.info_font.render(line, True, (150, 150, 150))
                line_rect = line_text.get_rect()
                line_rect.centerx = window_x + window_width // 2
                line_rect.y = line_y
                self.screen.blit(line_text, line_rect)
            line_y += 30

        # Подсказки управления
        controls_y = window_y + window_height - 50

        controls_text = self.info_font.render(
            "Tab - Вкладки | Esc - Закрыть",
            True,
            (150, 150, 150)
        )
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = window_x + window_width // 2
        controls_rect.y = controls_y
        self.screen.blit(controls_text, controls_rect)
