"""
Базовые компоненты UI.

Содержит:
- UIScaler - масштабирование UI под разные разрешения
- UIHelper - вспомогательные методы для отрисовки
"""
import pygame
from game.constants import BASE_WIDTH, BASE_HEIGHT


class UIScaler:
    """Класс для масштабирования UI элементов под разные разрешения экрана"""

    def __init__(self, screen_width, screen_height):
        """
        Инициализация масштабировщика

        Args:
            screen_width: Фактическая ширина экрана
            screen_height: Фактическая высота экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Вычисляем коэффициенты масштабирования
        self.scale_x = screen_width / BASE_WIDTH
        self.scale_y = screen_height / BASE_HEIGHT

        # Используем минимальный коэффициент для сохранения пропорций
        self.scale = min(self.scale_x, self.scale_y)

    def scale_value(self, value):
        """Масштабировать одиночное значение"""
        return int(value * self.scale)

    def scale_width(self, width):
        """Масштабировать ширину"""
        return int(width * self.scale_x)

    def scale_height(self, height):
        """Масштабировать высоту"""
        return int(height * self.scale_y)

    def scale_pos(self, x, y):
        """Масштабировать позицию (x, y)"""
        return int(x * self.scale_x), int(y * self.scale_y)

    def scale_rect(self, x, y, width, height):
        """Масштабировать прямоугольник"""
        return (
            int(x * self.scale_x),
            int(y * self.scale_y),
            int(width * self.scale_x),
            int(height * self.scale_y)
        )

    def scale_font_size(self, base_size):
        """Масштабировать размер шрифта"""
        return max(12, int(base_size * self.scale))

    def get_centered_x(self, width):
        """Получить X координату для центрирования элемента"""
        return (self.screen_width - width) // 2

    def get_centered_y(self, height):
        """Получить Y координату для центрирования элемента"""
        return (self.screen_height - height) // 2


class UIHelper:
    """Вспомогательные методы для UI"""

    @staticmethod
    def draw_panel(surface, x, y, width, height, color=(40, 40, 45), border_color=(100, 100, 120), border_width=2):
        """
        Отрисовка панели с рамкой

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            color: Цвет фона
            border_color: Цвет рамки
            border_width: Толщина рамки
        """
        # Фон панели
        pygame.draw.rect(surface, color, (x, y, width, height))
        # Рамка
        pygame.draw.rect(surface, border_color, (x, y, width, height), border_width)

    @staticmethod
    def draw_gradient_rect(surface, x, y, width, height, color1, color2, vertical=True):
        """
        Отрисовка прямоугольника с градиентом

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            color1, color2: Цвета градиента
            vertical: Вертикальный или горизонтальный градиент
        """
        if vertical:
            if height <= 0:
                return
            for i in range(height):
                ratio = i / height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x, y + i), (x + width, y + i))
        else:
            if width <= 0:
                return
            for i in range(width):
                ratio = i / width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + height))

    @staticmethod
    def draw_progress_bar(surface, x, y, width, height, current, maximum,
                          bg_color=(40, 40, 40), fill_color=(100, 200, 100),
                          border_color=(200, 200, 200), text=None, font=None):
        """
        Отрисовка полосы прогресса

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            current, maximum: Текущее и максимальное значение
            bg_color: Цвет фона
            fill_color: Цвет заполнения
            border_color: Цвет рамки
            text: Текст для отображения
            font: Шрифт для текста
        """
        # Фон
        pygame.draw.rect(surface, bg_color, (x, y, width, height))

        # Заполнение
        if maximum > 0:
            # Вычисляем заполнение с ограничением (clamp)
            fill_ratio = min(1.0, max(0.0, current / maximum))
            fill_width = int(fill_ratio * width)
            pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))

        # Рамка
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1)

        # Текст
        if text and font:
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.center = (x + width // 2, y + height // 2)
            surface.blit(text_surface, text_rect)

    @staticmethod
    def draw_rounded_progress_bar(surface, x, y, width, height, current, maximum,
                                   bg_color=(40, 40, 40), fill_color=(100, 200, 100),
                                   border_radius=None):
        """
        Отрисовка закруглённой полосы прогресса без текста

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            current, maximum: Текущее и максимальное значение
            bg_color: Цвет фона
            fill_color: Цвет заполнения
            border_radius: Радиус закругления (по умолчанию height // 2)
        """
        if border_radius is None:
            border_radius = height // 2

        # Фон с закруглением
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=border_radius)

        # Заполнение с закруглением
        if maximum > 0:
            fill_ratio = min(1.0, max(0.0, current / maximum))
            fill_width = int(fill_ratio * width)
            if fill_width > 0:
                # Минимальная ширина для корректного закругления
                min_fill_width = border_radius * 2 if fill_width >= border_radius else fill_width
                actual_fill_width = max(min_fill_width, fill_width)
                if actual_fill_width > width:
                    actual_fill_width = width
                fill_rect = pygame.Rect(x, y, actual_fill_width, height)
                pygame.draw.rect(surface, fill_color, fill_rect, border_radius=border_radius)

    @staticmethod
    def draw_tooltip(surface, text, x, y, font, bg_color=(40, 40, 40), text_color=(255, 255, 255), padding=8):
        """
        Отрисовка всплывающей подсказки

        Args:
            surface: Поверхность для рисования
            text: Текст подсказки
            x, y: Координаты
            font: Шрифт
            bg_color: Цвет фона
            text_color: Цвет текста
            padding: Отступ от краёв
        """
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect()

        # Размеры окна подсказки
        tooltip_width = text_rect.width + padding * 2
        tooltip_height = text_rect.height + padding * 2

        # Корректируем позицию, чтобы не выходить за экран
        screen_width, screen_height = surface.get_size()
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 5
        if y + tooltip_height > screen_height:
            y = y - tooltip_height - 10

        # Фон подсказки с рамкой
        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, bg_color, tooltip_rect, border_radius=4)
        pygame.draw.rect(surface, (100, 100, 100), tooltip_rect, 1, border_radius=4)

        # Текст
        surface.blit(text_surface, (x + padding, y + padding))

    @staticmethod
    def wrap_text(text, font, max_width):
        """
        Разбивает текст на строки с переносом по словам

        Args:
            text: Текст для разбивки
            font: Шрифт для измерения ширины
            max_width: Максимальная ширина строки в пикселях

        Returns:
            list: Список строк
        """
        if not text:
            return [""]

        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            # Пробуем добавить слово к текущей строке
            test_line = current_line + (" " if current_line else "") + word
            test_surface = font.render(test_line, True, (255, 255, 255))

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                # Если текущая строка не пуста, сохраняем её
                if current_line:
                    lines.append(current_line)
                # Проверяем, помещается ли слово само по себе
                word_surface = font.render(word, True, (255, 255, 255))
                if word_surface.get_width() > max_width:
                    # Слово слишком длинное, разбиваем по символам
                    current_word = ""
                    for char in word:
                        test_word = current_word + char
                        char_surface = font.render(test_word, True, (255, 255, 255))
                        if char_surface.get_width() <= max_width:
                            current_word = test_word
                        else:
                            if current_word:
                                lines.append(current_word)
                            current_word = char
                    current_line = current_word
                else:
                    current_line = word

        # Добавляем последнюю строку
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]
