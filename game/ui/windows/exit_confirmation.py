"""
Окно подтверждения выхода из игры.
"""
import pygame
from game.ui.windows.base import BaseWindow


class ExitConfirmationWindow(BaseWindow):
    """Окно подтверждения выхода из игры"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна подтверждения выхода

        Args:
            screen: Экран pygame
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект масштабирования UI
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.yes_button_rect = None
        self.no_button_rect = None

    def handle_input(self, event):
        """
        Обработать ввод

        Args:
            event: Событие pygame

        Returns:
            str: 'yes' для выхода, 'no' для отмены, None для продолжения
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'no'  # ESC отменяет выход
            elif event.key == pygame.K_RETURN:
                return 'yes'  # Enter подтверждает выход

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                # Проверяем клик по кнопке "Да"
                if self.yes_button_rect and self.yes_button_rect.collidepoint(mouse_pos):
                    return 'yes'
                # Проверяем клик по кнопке "Нет"
                if self.no_button_rect and self.no_button_rect.collidepoint(mouse_pos):
                    return 'no'

        return None

    def render(self):
        """
        Отрисовать окно подтверждения выхода
        """
        screen_width, screen_height = self.screen.get_size()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.scaler:
            window_width = self.scaler.scale_width(400)
            window_height = self.scaler.scale_height(250)
        else:
            window_width = 400
            window_height = 250

        # Центрирование
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Цвета
        border_color = (200, 150, 100)  # Оранжевый
        title_color = (255, 215, 0)  # Золотой
        text_color = (220, 220, 220)  # Светло-серый

        # Фон окна
        pygame.draw.rect(self.screen, (40, 40, 45),
                        (window_x, window_y, window_width, window_height))

        # Рамка
        pygame.draw.rect(self.screen, border_color,
                        (window_x, window_y, window_width, window_height), 3)

        # Заголовок
        header_height = 50
        pygame.draw.rect(self.screen, (35, 35, 45),
                        (window_x + 3, window_y + 3, window_width - 6, header_height))

        title_text = self.font.render("Выход из игры", True, title_color)
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.centery = window_y + header_height // 2
        self.screen.blit(title_text, title_rect)

        # Вопрос
        content_y = window_y + header_height + 40
        question_text = self.font.render("Вы уверены, что хотите выйти?", True, text_color)
        question_rect = question_text.get_rect()
        question_rect.centerx = window_x + window_width // 2
        question_rect.y = content_y
        self.screen.blit(question_text, question_rect)

        # Предупреждение
        content_y += 45
        warning_text = self.info_font.render(
            "Прогресс будет сохранён автоматически",
            True, (150, 150, 150)
        )
        warning_rect = warning_text.get_rect()
        warning_rect.centerx = window_x + window_width // 2
        warning_rect.y = content_y
        self.screen.blit(warning_text, warning_rect)

        # Кнопки
        button_width = 140
        button_height = 40
        button_spacing = 20
        buttons_y = window_y + window_height - button_height - 20

        # Кнопка "Нет" (слева)
        no_button_x = window_x + (window_width // 2) - button_width - (button_spacing // 2)
        self.no_button_rect = pygame.Rect(no_button_x, buttons_y, button_width, button_height)

        # Проверяем, наведена ли мышь на кнопку "Нет"
        mouse_pos = pygame.mouse.get_pos()
        no_hover = self.no_button_rect.collidepoint(mouse_pos)
        no_bg_color = (80, 80, 90) if no_hover else (60, 60, 70)

        pygame.draw.rect(self.screen, no_bg_color, self.no_button_rect)
        pygame.draw.rect(self.screen, (100, 180, 100), self.no_button_rect, 2)

        no_text = self.font.render("Нет", True, (150, 255, 150))
        no_text_rect = no_text.get_rect(center=self.no_button_rect.center)
        self.screen.blit(no_text, no_text_rect)

        # Кнопка "Да" (справа)
        yes_button_x = window_x + (window_width // 2) + (button_spacing // 2)
        self.yes_button_rect = pygame.Rect(yes_button_x, buttons_y, button_width, button_height)

        # Проверяем, наведена ли мышь на кнопку "Да"
        yes_hover = self.yes_button_rect.collidepoint(mouse_pos)
        yes_bg_color = (90, 70, 70) if yes_hover else (70, 60, 60)

        pygame.draw.rect(self.screen, yes_bg_color, self.yes_button_rect)
        pygame.draw.rect(self.screen, (200, 100, 100), self.yes_button_rect, 2)

        yes_text = self.font.render("Да", True, (255, 150, 150))
        yes_text_rect = yes_text.get_rect(center=self.yes_button_rect.center)
        self.screen.blit(yes_text, yes_text_rect)

        # Подсказка
        hint_text = self.info_font.render(
            "Enter - Да | ESC - Нет",
            True, (100, 100, 100)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - button_height - 50
        self.screen.blit(hint_text, hint_rect)
