"""
Окно выбора режима боя
"""
import pygame
from game.ui.windows.base import BaseWindow


class CombatModeSelectionWindow(BaseWindow):
    """Окно выбора режима боя"""

    BASE_WIDTH = 400
    BASE_HEIGHT = 250

    def render(self, enemy_name="Противник", is_aggression=False):
        """
        Отрисовка окна выбора режима боя

        Args:
            enemy_name: Имя противника
            is_aggression: True если враг сам напал (не показывать кнопку "Уйти")
        """
        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title=f"Выбор режима боя: {enemy_name}"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Информация
        info_y = window_y + int(70 * scale_h)
        if is_aggression:
            info_text = "На вас напали! Выберите тип сражения:"
            info_color = (255, 150, 150)  # Красноватый цвет для агрессии
        else:
            info_text = "Выберите тип сражения:"
            info_color = (200, 200, 200)

        info_surface = self.font.render(info_text, True, info_color)
        info_rect = info_surface.get_rect()
        info_rect.centerx = window_x + window_width // 2
        info_rect.y = info_y
        self.screen.blit(info_surface, info_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), window_y + int(110 * scale_h)),
            (window_x + window_width - int(20 * scale_h), window_y + int(110 * scale_h)),
            2
        )

        # Варианты действий
        actions_y = window_y + int(130 * scale_h)
        if is_aggression:
            # При агрессии нельзя уйти
            actions = [
                "[1] Быстрый бой",
                "[2] Сражение"
            ]
        else:
            actions = [
                "[1] Быстрый бой",
                "[2] Сражение",
                "[3] Уйти"
            ]

        # Отрисовка кнопок действий
        for i, action in enumerate(actions):
            color = (150, 255, 150)  # Зеленый для всех вариантов
            action_text = self.info_font.render(action, True, color)
            action_rect = action_text.get_rect()
            action_rect.centerx = window_x + window_width // 2
            action_rect.y = actions_y + i * int(30 * scale_h)
            self.screen.blit(action_text, action_rect)
