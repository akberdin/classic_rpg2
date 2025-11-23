"""
Окно случайных событий.
"""
import pygame
from game.ui.base import UIHelper


class RandomEventWindow:
    """Окно отображения случайных событий"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна событий

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

    def handle_input(self, event):
        """
        Обработать ввод

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
                # Проверяем клик по кнопке закрытия
                if self.close_button_rect and self.close_button_rect.collidepoint(mouse_pos):
                    return True

        return False

    def render(self, event_result):
        """
        Отрисовать окно события

        Args:
            event_result: Объект EventResult с информацией о событии
        """
        if not event_result or not event_result.event:
            return

        screen_width, screen_height = self.screen.get_size()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(500)
            window_height = self.ui_scaler.scale_height(350)
        else:
            window_width = 500
            window_height = 350

        # Центрирование
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Цвета в зависимости от типа события
        event = event_result.event
        from game.events import EventType

        if event.event_type == EventType.POSITIVE:
            border_color = (100, 200, 100)  # Зелёный
            title_color = (150, 255, 150)
            icon_color = (100, 255, 100)
        elif event.event_type == EventType.NEGATIVE:
            border_color = (200, 100, 100)  # Красный
            title_color = (255, 150, 150)
            icon_color = (255, 100, 100)
        else:
            border_color = (200, 180, 100)  # Жёлтый/нейтральный
            title_color = (255, 215, 0)
            icon_color = (255, 215, 0)

        # Фон окна
        pygame.draw.rect(self.screen, (40, 40, 45),
                        (window_x, window_y, window_width, window_height))

        # Рамка
        pygame.draw.rect(self.screen, border_color,
                        (window_x, window_y, window_width, window_height), 3)

        # Заголовок с иконкой
        header_height = 50
        pygame.draw.rect(self.screen, (35, 35, 45),
                        (window_x + 3, window_y + 3, window_width - 6, header_height))

        # Иконка события
        icon_text = self.font.render(f"[{event.icon}]", True, icon_color)
        icon_rect = icon_text.get_rect()
        icon_rect.x = window_x + 15
        icon_rect.centery = window_y + header_height // 2
        self.screen.blit(icon_text, icon_rect)

        # Название события
        title_text = self.font.render(event.name, True, title_color)
        title_rect = title_text.get_rect()
        title_rect.x = window_x + 60
        title_rect.centery = window_y + header_height // 2
        self.screen.blit(title_text, title_rect)

        # Ранг игрока
        rank_text = self.info_font.render(
            f"Ранг: {event_result.player_rank}",
            True, (150, 150, 150)
        )
        rank_rect = rank_text.get_rect()
        rank_rect.right = window_x + window_width - 15
        rank_rect.centery = window_y + header_height // 2
        self.screen.blit(rank_text, rank_rect)

        # Описание события
        content_y = window_y + header_height + 20

        # Разбиваем описание на строки
        description = event.description
        words = description.split(' ')
        lines = []
        current_line = ""
        max_width = window_width - 40

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.info_font.render(test_line, True, (255, 255, 255))
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Отрисовка описания
        for line in lines:
            desc_text = self.info_font.render(line, True, (220, 220, 220))
            self.screen.blit(desc_text, (window_x + 20, content_y))
            content_y += 25

        # Разделитель
        content_y += 10
        pygame.draw.line(self.screen, (80, 80, 90),
                        (window_x + 20, content_y),
                        (window_x + window_width - 20, content_y), 1)
        content_y += 15

        # Эффекты события
        effects_title = self.info_font.render("Эффекты:", True, (200, 200, 100))
        self.screen.blit(effects_title, (window_x + 20, content_y))
        content_y += 30

        for effect in event_result.effects:
            # Цвет эффекта в зависимости от содержимого
            if "Получено" in effect or "Восстановлено" in effect:
                effect_color = (100, 255, 100)
            elif "Потеряно" in effect or "урона" in effect:
                effect_color = (255, 100, 100)
            else:
                effect_color = (200, 200, 200)

            effect_text = self.info_font.render(effect, True, effect_color)
            self.screen.blit(effect_text, (window_x + 20, content_y))
            content_y += 22

        # Кнопка закрытия
        button_width = 120
        button_height = 35
        button_x = window_x + (window_width - button_width) // 2
        button_y = window_y + window_height - button_height - 15

        self.close_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Фон кнопки
        pygame.draw.rect(self.screen, (60, 60, 70), self.close_button_rect)
        pygame.draw.rect(self.screen, border_color, self.close_button_rect, 2)

        # Текст кнопки
        button_text = self.info_font.render("OK", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=self.close_button_rect.center)
        self.screen.blit(button_text, button_text_rect)

        # Подсказка
        hint_text = self.info_font.render(
            "Нажмите Enter/Esc или кликните OK для закрытия",
            True, (100, 100, 100)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 55
        self.screen.blit(hint_text, hint_rect)


