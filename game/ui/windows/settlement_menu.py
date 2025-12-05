"""
Окно выбора действий в городе/деревне.
"""
import pygame
from game.ui.windows.base import BaseWindow


class SettlementMenuWindow(BaseWindow):
    """Окно меню города/деревни"""

    BASE_WIDTH = 500
    BASE_HEIGHT = 350

    def __init__(self, screen, font, info_font, ui_scaler, game_map):
        """
        Инициализация окна меню города/деревни.

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект для масштабирования UI
            game_map: Карта игры (для определения позиции академии)
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.game_map = game_map
        self.location = None
        self.selected_action = None

    def set_location(self, location):
        """
        Установить текущую локацию.

        Args:
            location: Объект локации
        """
        self.location = location

    def render(self):
        """Отрисовка окна меню города/деревни."""
        if not self.location:
            return

        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title=f"{self.location.name}"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Приветственный текст
        welcome_y = window_y + int(70 * scale_h)
        welcome_text = self.font.render(
            f"Добро пожаловать в {self.location.name}!",
            True, (200, 200, 200)
        )
        welcome_rect = welcome_text.get_rect()
        welcome_rect.centerx = window_x + window_width // 2
        welcome_rect.y = welcome_y
        self.screen.blit(welcome_text, welcome_rect)

        # Описание локации
        desc_y = welcome_y + int(40 * scale_h)
        desc_text = self.info_font.render(
            self.location.get_description(),
            True, (150, 150, 150)
        )
        desc_rect = desc_text.get_rect()
        desc_rect.centerx = window_x + window_width // 2
        desc_rect.y = desc_y
        self.screen.blit(desc_text, desc_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), window_y + int(150 * scale_h)),
            (window_x + window_width - int(20 * scale_h), window_y + int(150 * scale_h)),
            2
        )

        # Варианты действий
        actions_y = window_y + int(170 * scale_h)
        actions_title = self.font.render("Выберите действие:", True, (200, 200, 200))
        actions_title_rect = actions_title.get_rect()
        actions_title_rect.centerx = window_x + window_width // 2
        actions_title_rect.y = actions_y
        self.screen.blit(actions_title, actions_title_rect)

        # Список действий (зависит от типа локации)
        from game.constants import LOCATION_MAGIC_SCHOOL

        actions = [
            "[1] Магазин",
            "[2] Расспросить жителей"
        ]

        # Добавляем опцию покупки умения в зависимости от локации
        if self.location.location_type == LOCATION_MAGIC_SCHOOL:
            actions.append("[3] Купить умение Зачарование (10000 зол.)")
        else:
            actions.append("[3] Купить умение Изготовление (500 зол.)")

        actions.append("[ESC] Выйти")

        # Отрисовка кнопок действий
        buttons_y = actions_y + int(40 * scale_h)
        for i, action in enumerate(actions):
            action_text = self.info_font.render(action, True, (150, 255, 150))
            action_rect = action_text.get_rect()
            action_rect.centerx = window_x + window_width // 2
            action_rect.y = buttons_y + i * int(30 * scale_h)
            self.screen.blit(action_text, action_rect)


class InquiryMenuWindow(BaseWindow):
    """Окно расспроса жителей"""

    BASE_WIDTH = 600
    BASE_HEIGHT = 400

    def __init__(self, screen, font, info_font, ui_scaler, game_map):
        """
        Инициализация окна расспроса жителей.

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект для масштабирования UI
            game_map: Карта игры (для определения позиции академии)
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.game_map = game_map
        self.location = None

    def set_location(self, location):
        """
        Установить текущую локацию.

        Args:
            location: Объект локации
        """
        self.location = location

    def render(self):
        """Отрисовка окна расспроса жителей."""
        if not self.location:
            return

        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title="Расспросить жителей"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Заголовок
        header_y = window_y + int(70 * scale_h)
        header_text = self.font.render(
            "О чем вы хотите спросить?",
            True, (200, 200, 200)
        )
        header_rect = header_text.get_rect()
        header_rect.centerx = window_x + window_width // 2
        header_rect.y = header_y
        self.screen.blit(header_text, header_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), window_y + int(120 * scale_h)),
            (window_x + window_width - int(20 * scale_h), window_y + int(120 * scale_h)),
            2
        )

        # Вопросы
        questions_y = window_y + int(140 * scale_h)
        questions = [
            "[1] Где находится магическая академия?",
            "[ESC] Назад"
        ]

        for i, question in enumerate(questions):
            question_text = self.info_font.render(question, True, (150, 255, 150))
            question_rect = question_text.get_rect()
            question_rect.centerx = window_x + window_width // 2
            question_rect.y = questions_y + i * int(40 * scale_h)
            self.screen.blit(question_text, question_rect)

    def get_direction_to_academy(self, from_location):
        """
        Получить направление к магической академии от текущей локации.

        Args:
            from_location: Объект локации, откуда ищем

        Returns:
            str: Направление (север, юг, запад, восток)
        """
        from game.constants import LOCATION_MAGIC_SCHOOL

        # Ищем магическую академию на карте
        academy_x, academy_y = None, None

        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                tile = self.game_map.get_tile(x, y)
                if tile.has_location():
                    if tile.location.location_type == LOCATION_MAGIC_SCHOOL:
                        academy_x, academy_y = x, y
                        break
            if academy_x is not None:
                break

        if academy_x is None:
            return "Неизвестно где находится академия..."

        # Определяем направление
        dx = academy_x - from_location.x
        dy = academy_y - from_location.y

        # Определяем основное направление
        if abs(dx) > abs(dy):
            # Горизонтальное направление доминирует
            if dx > 0:
                direction = "восток"
            else:
                direction = "запад"
        else:
            # Вертикальное направление доминирует
            if dy > 0:
                direction = "юг"
            else:
                direction = "север"

        return direction


class InquiryResponseWindow(BaseWindow):
    """Окно ответа на вопрос"""

    BASE_WIDTH = 650
    BASE_HEIGHT = 350

    def __init__(self, screen, font, info_font, ui_scaler):
        """
        Инициализация окна ответа.

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект для масштабирования UI
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.response_text = ""

    def set_response(self, text):
        """
        Установить текст ответа.

        Args:
            text: Текст ответа
        """
        self.response_text = text

    def render(self):
        """Отрисовка окна ответа."""
        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title="Ответ местного жителя"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Иконка жителя (опционально)
        npc_y = window_y + int(70 * scale_h)
        npc_text = self.font.render("🧑", True, (200, 200, 200))
        npc_rect = npc_text.get_rect()
        npc_rect.centerx = window_x + window_width // 2
        npc_rect.y = npc_y
        self.screen.blit(npc_text, npc_rect)

        # Текст ответа
        response_y = window_y + int(130 * scale_h)

        # Разбиваем текст на строки если он длинный
        words = self.response_text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.info_font.render(test_line, True, (200, 200, 200))
            if test_surface.get_width() < window_width - int(40 * scale_h):
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Отрисовка строк
        for i, line in enumerate(lines):
            line_text = self.info_font.render(line, True, (200, 200, 200))
            line_rect = line_text.get_rect()
            line_rect.centerx = window_x + window_width // 2
            line_rect.y = response_y + i * int(30 * scale_h)
            self.screen.blit(line_text, line_rect)

        # Подсказка внизу
        hint_y = window_y + int(280 * scale_h)
        hint_text = self.info_font.render(
            "Нажмите любую клавишу для продолжения...",
            True, (100, 100, 100)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hint_y
        self.screen.blit(hint_text, hint_rect)
