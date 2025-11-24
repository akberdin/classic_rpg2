"""
Базовый класс для UI окон.

Содержит общую логику отрисовки: затемнение фона, расчёт размеров,
отрисовка рамки и заголовка.
"""
import pygame
from game.ui.base import UIHelper


class BaseWindow:
    """Базовый класс для всех UI окон"""

    # Цвета по умолчанию
    OVERLAY_ALPHA = 150
    OVERLAY_COLOR = (0, 0, 0)
    FRAME_COLOR = (120, 120, 150)
    TITLE_COLOR = (255, 215, 0)
    GRADIENT_TOP = (35, 35, 45)
    GRADIENT_BOTTOM = (55, 55, 70)

    def __init__(self, screen, font, info_font=None, scaler=None):
        """
        Инициализация базового окна.

        Args:
            screen: pygame Surface для отрисовки
            font: Основной шрифт
            info_font: Информационный шрифт (по умолчанию = font)
            scaler: UIScaler для адаптивного масштабирования
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font or font
        self.scaler = scaler

    def draw_overlay(self, alpha=None):
        """
        Отрисовка затемняющего оверлея.

        Args:
            alpha: Прозрачность (0-255), по умолчанию OVERLAY_ALPHA
        """
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(alpha or self.OVERLAY_ALPHA)
        overlay.fill(self.OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

    def calculate_window_rect(self, base_width, base_height, width_ratio=0.7, height_ratio=0.7):
        """
        Рассчитать размеры и позицию окна по центру экрана.

        Args:
            base_width: Базовая ширина окна
            base_height: Базовая высота окна
            width_ratio: Максимальное соотношение к ширине экрана (если нет scaler)
            height_ratio: Максимальное соотношение к высоте экрана (если нет scaler)

        Returns:
            tuple: (x, y, width, height, scale_w, scale_h)
        """
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.scaler:
            window_width = self.scaler.scale_width(base_width)
            window_height = self.scaler.scale_height(base_height)
        else:
            window_width = min(base_width, int(screen_width * width_ratio))
            window_height = min(base_height, int(screen_height * height_ratio))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Коэффициенты масштабирования для внутренних элементов
        scale_w = window_width / base_width
        scale_h = window_height / base_height

        return (window_x, window_y, window_width, window_height, scale_w, scale_h)

    def draw_window_background(self, x, y, width, height):
        """
        Отрисовка фона окна с градиентом и рамкой.

        Args:
            x, y: Позиция окна
            width, height: Размеры окна
        """
        # Градиентный фон
        UIHelper.draw_gradient_rect(
            self.screen, x, y, width, height,
            self.GRADIENT_TOP, self.GRADIENT_BOTTOM
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            self.FRAME_COLOR,
            (x, y, width, height),
            3
        )

    def draw_title(self, title, window_x, window_y, window_width, scale_h=1.0):
        """
        Отрисовка заголовка окна.

        Args:
            title: Текст заголовка
            window_x, window_y: Позиция окна
            window_width: Ширина окна
            scale_h: Коэффициент вертикального масштабирования

        Returns:
            int: Y-координата следующей строки
        """
        title_text = self.font.render(title, True, self.TITLE_COLOR)
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * scale_h)
        self.screen.blit(title_text, title_rect)

        return title_rect.bottom + int(10 * scale_h)

    def begin_render(self, base_width, base_height, title=None, width_ratio=0.7, height_ratio=0.7):
        """
        Начать отрисовку окна: оверлей, фон, заголовок.

        Args:
            base_width: Базовая ширина окна
            base_height: Базовая высота окна
            title: Заголовок окна (опционально)
            width_ratio: Максимальное соотношение к ширине экрана
            height_ratio: Максимальное соотношение к высоте экрана

        Returns:
            dict: Словарь с параметрами окна {x, y, width, height, scale_w, scale_h, content_y}
        """
        self.draw_overlay()

        x, y, width, height, scale_w, scale_h = self.calculate_window_rect(
            base_width, base_height, width_ratio, height_ratio
        )

        self.draw_window_background(x, y, width, height)

        content_y = y + int(10 * scale_h)
        if title:
            content_y = self.draw_title(title, x, y, width, scale_h)

        return {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'scale_w': scale_w,
            'scale_h': scale_h,
            'content_y': content_y
        }
