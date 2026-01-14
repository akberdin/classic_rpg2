"""
Окно отображения событий завершения квестов.

Показывает название и описание события с автоматическим
переносом текста и масштабированием окна по высоте.
"""
import pygame
from game.ui.base import UIHelper


class QuestEventWindow:
    """Окно отображения событий завершения квестов"""

    # Цвета
    OVERLAY_ALPHA = 200
    BACKGROUND_COLOR = (40, 40, 50)
    BORDER_COLOR = (100, 180, 220)  # Голубой для событий квестов
    TITLE_COLOR = (255, 215, 0)  # Золотой для заголовка
    TEXT_COLOR = (220, 220, 220)
    BUTTON_COLOR = (60, 60, 70)
    BUTTON_HOVER_COLOR = (80, 80, 90)

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна событий квестов.

        Args:
            screen: Экран pygame
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект масштабирования UI
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.ui_scaler = ui_scaler

        # Кнопка закрытия
        self.close_button_rect = None

        # Текущее событие для отображения
        self.current_event = None

    def set_event(self, event_name: str, event_description: str):
        """
        Установить событие для отображения.

        Args:
            event_name: Название события
            event_description: Описание события
        """
        self.current_event = {
            'name': event_name,
            'description': event_description
        }

    def handle_input(self, event) -> bool:
        """
        Обработать ввод.

        Args:
            event: Событие pygame

        Returns:
            bool: True если окно нужно закрыть
        """
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                if self.close_button_rect and self.close_button_rect.collidepoint(mouse_pos):
                    return True

        return False

    def _wrap_text(self, text: str, max_width: int) -> list:
        """
        Разбить текст на строки с переносом по словам.

        Args:
            text: Исходный текст
            max_width: Максимальная ширина строки в пикселях

        Returns:
            list: Список строк
        """
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            # Проверяем, помещается ли слово с текущей строкой
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.info_font.render(test_line, True, self.TEXT_COLOR)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                # Текущая строка заполнена, начинаем новую
                if current_line:
                    lines.append(current_line)
                current_line = word

        # Добавляем последнюю строку
        if current_line:
            lines.append(current_line)

        return lines

    def _calculate_window_height(self, description_lines: list, base_width: int) -> int:
        """
        Рассчитать высоту окна на основе количества строк описания.

        Args:
            description_lines: Список строк описания
            base_width: Базовая ширина окна

        Returns:
            int: Высота окна
        """
        # Компоненты высоты:
        # - Отступ сверху: 20
        # - Заголовок: 35
        # - Отступ после заголовка: 15
        # - Разделитель: 10
        # - Отступ перед описанием: 15
        # - Строки описания: line_height * количество строк
        # - Отступ после описания: 20
        # - Кнопка: 40
        # - Подсказка: 25
        # - Отступ снизу: 15

        line_height = 28
        header_section = 20 + 35 + 15 + 10 + 15  # 95
        description_height = line_height * len(description_lines)
        footer_section = 20 + 40 + 25 + 15  # 100

        total_height = header_section + description_height + footer_section

        # Минимальная высота
        min_height = 200
        return max(total_height, min_height)

    def render(self):
        """Отрисовать окно события."""
        if not self.current_event:
            return

        screen_width, screen_height = self.screen.get_size()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(self.OVERLAY_ALPHA)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Базовая ширина окна
        if self.ui_scaler:
            base_width = self.ui_scaler.scale_width(450)
        else:
            base_width = min(450, int(screen_width * 0.8))

        # Отступы для текста
        padding = 25
        text_max_width = base_width - (padding * 2)

        # Разбиваем описание на строки
        description_lines = self._wrap_text(
            self.current_event['description'],
            text_max_width
        )

        # Рассчитываем высоту окна
        window_width = base_width
        window_height = self._calculate_window_height(description_lines, base_width)

        # Ограничиваем максимальную высоту
        max_height = int(screen_height * 0.8)
        window_height = min(window_height, max_height)

        # Центрирование окна
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна
        pygame.draw.rect(
            self.screen,
            self.BACKGROUND_COLOR,
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            self.BORDER_COLOR,
            (window_x, window_y, window_width, window_height),
            3
        )

        # === Заголовок ===
        current_y = window_y + 20

        # Иконка события (звезда)
        icon_text = self.font.render("[*]", True, self.BORDER_COLOR)
        icon_rect = icon_text.get_rect()
        icon_rect.x = window_x + padding
        icon_rect.y = current_y
        self.screen.blit(icon_text, icon_rect)

        # Название события
        title_text = self.font.render(self.current_event['name'], True, self.TITLE_COLOR)
        title_rect = title_text.get_rect()
        title_rect.x = window_x + padding + 40
        title_rect.y = current_y
        self.screen.blit(title_text, title_rect)

        current_y += 35

        # Разделитель
        current_y += 15
        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (window_x + padding, current_y),
            (window_x + window_width - padding, current_y),
            1
        )
        current_y += 10

        # === Описание события ===
        current_y += 15
        line_height = 28

        for line in description_lines:
            line_text = self.info_font.render(line, True, self.TEXT_COLOR)
            self.screen.blit(line_text, (window_x + padding, current_y))
            current_y += line_height

        # === Кнопка закрытия ===
        button_width = 120
        button_height = 40
        button_x = window_x + (window_width - button_width) // 2
        button_y = window_y + window_height - 80

        self.close_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Проверяем наведение мыши
        mouse_pos = pygame.mouse.get_pos()
        if self.close_button_rect.collidepoint(mouse_pos):
            button_bg_color = self.BUTTON_HOVER_COLOR
        else:
            button_bg_color = self.BUTTON_COLOR

        # Фон кнопки
        pygame.draw.rect(self.screen, button_bg_color, self.close_button_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.close_button_rect, 2)

        # Текст кнопки
        button_text = self.info_font.render("Закрыть", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=self.close_button_rect.center)
        self.screen.blit(button_text, button_text_rect)

        # === Подсказка ===
        hint_text = self.info_font.render(
            "Enter/Esc/Пробел для закрытия",
            True,
            (100, 100, 120)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 35
        self.screen.blit(hint_text, hint_rect)

    def clear(self):
        """Очистить текущее событие."""
        self.current_event = None
