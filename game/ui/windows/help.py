"""
Окно помощи (F1).
"""
import pygame
from game.ui.base import UIHelper


class HelpWindow:
    """Окно помощи (F1)"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.is_open = False

        self.help_data = [
            ("=== УПРАВЛЕНИЕ ===", None),
            ("Перемещение:", "W/A/S/D или Стрелки"),
            ("Отдых:", "R - восстановить здоровье и ману"),
            ("Работа:", "T - получить опыт и золото"),
            ("Взаимодействие:", "E - разговор с NPC"),
            ("Сбор ресурсов:", "F - собрать лут с локации"),
            ("Инвентарь:", "I - открыть/закрыть"),
            ("Характеристики:", "C - открыть окно персонажа"),
            ("Крафт:", "V - открыть окно крафта"),
            ("Помощь:", "F1 - открыть/закрыть это окно"),
            ("Выход:", "ESC - выйти из игры"),
            ("", None),
            ("=== ИНВЕНТАРЬ ===", None),
            ("Навигация:", "W/S - выбор предмета"),
            ("Использовать:", "Enter/U - использовать предмет"),
            ("Экипировать:", "E - экипировать предмет"),
            ("Снять предмет:", "ПКМ - снять экипированный предмет"),
            ("Надеть предмет:", "ПКМ - экипировать из инвентаря"),
            ("Информация:", "Наведите мышь на предмет"),
            ("Закрыть:", "I/ESC - закрыть инвентарь"),
            ("", None),
            ("=== ВЗАИМОДЕЙСТВИЕ С NPC ===", None),
            ("Меню выбора:", "[1] Торговля, [2] Агрессия, [3] Уйти"),
            ("", None),
            ("=== ТОРГОВЛЯ ===", None),
            ("Режим покупки:", "Tab - переключить на продажу"),
            ("Режим продажи:", "Tab - переключить на покупку"),
            ("Навигация:", "W/S - выбор товара"),
            ("Подтвердить:", "Enter - купить/продать"),
            ("Закрыть:", "ESC - закрыть окно торговли"),
            ("", None),
            ("=== БОЙ ===", None),
            ("Атака:", "1 - обычная атака"),
            ("Побег:", "2 - попытка сбежать"),
        ]

    def toggle(self):
        """Переключить состояние окна"""
        self.is_open = not self.is_open

    def render(self):
        """Отрисовка окна помощи"""
        if not self.is_open:
            return

        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(700)
            window_height = self.scaler.scale_height(600)
        else:
            window_width = min(700, int(screen_width * 0.7))
            window_height = min(600, int(screen_height * 0.7))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (30, 30, 40), (50, 50, 65)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render("СПРАВКА", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(15 * (window_height / 600))
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle = self.info_font.render("Нажмите F1 для закрытия", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + int(45 * (window_height / 600))
        self.screen.blit(subtitle, subtitle_rect)

        # Разделитель
        separator_y = int(70 * (window_height / 600))
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (window_x + int(20 * (window_width / 700)), window_y + separator_y),
            (window_x + window_width - int(20 * (window_width / 700)), window_y + separator_y),
            2
        )

        # Содержимое в двух столбцах
        content_y_left = window_y + int(85 * (window_height / 600))
        content_y_right = content_y_left
        line_height = max(16, int(18 * (window_height / 600)))

        margin_left = int(20 * (window_width / 700))
        margin_left_text = int(35 * (window_width / 700))
        value_offset = int(180 * (window_width / 700))

        # Разделяем данные на два столбца
        column_width = (window_width - int(60 * (window_width / 700))) // 2
        right_column_x = window_x + column_width + int(40 * (window_width / 700))

        # Определяем точку разделения (половина данных в каждом столбце)
        split_index = len(self.help_data) // 2
        left_data = self.help_data[:split_index]
        right_data = self.help_data[split_index:]

        # Отрисовка левого столбца
        for label, value in left_data:
            if label.startswith("==="):
                section_text = self.font.render(label, True, (100, 200, 255))
                self.screen.blit(section_text, (window_x + margin_left, content_y_left))
                content_y_left += line_height + int(4 * (window_height / 600))
            elif label == "":
                content_y_left += int(8 * (window_height / 600))
            else:
                label_text = self.info_font.render(label, True, (200, 200, 200))
                self.screen.blit(label_text, (window_x + margin_left_text, content_y_left))
                if value:
                    value_text = self.info_font.render(value, True, (150, 255, 150))
                    self.screen.blit(value_text, (window_x + value_offset, content_y_left))
                content_y_left += line_height

        # Отрисовка правого столбца
        for label, value in right_data:
            if label.startswith("==="):
                section_text = self.font.render(label, True, (100, 200, 255))
                self.screen.blit(section_text, (right_column_x, content_y_right))
                content_y_right += line_height + int(4 * (window_height / 600))
            elif label == "":
                content_y_right += int(8 * (window_height / 600))
            else:
                label_text = self.info_font.render(label, True, (200, 200, 200))
                self.screen.blit(label_text, (right_column_x + int(15 * (window_width / 700)), content_y_right))
                if value:
                    value_text = self.info_font.render(value, True, (150, 255, 150))
                    self.screen.blit(value_text, (right_column_x + int(160 * (window_width / 700)), content_y_right))
                content_y_right += line_height
