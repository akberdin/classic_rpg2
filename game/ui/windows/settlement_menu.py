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

    # Цвета кнопок
    BUTTON_COLOR = (50, 50, 60)
    BUTTON_HOVER_COLOR = (70, 70, 85)
    BUTTON_BORDER_COLOR = (100, 100, 120)
    BUTTON_TEXT_COLOR = (220, 220, 220)
    BACK_BUTTON_COLOR = (80, 50, 50)
    BACK_BUTTON_HOVER_COLOR = (100, 60, 60)

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
        self.buttons = []  # Список кнопок (rect, action)
        self.back_button = None  # Кнопка "Назад"

    def set_location(self, location):
        """
        Установить текущую локацию.

        Args:
            location: Объект локации
        """
        self.location = location
        self.buttons = []

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
        window_height = win['height']
        scale_h = win['scale_h']
        scale_w = win['scale_w']

        # Очищаем список кнопок перед отрисовкой
        self.buttons = []

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
            (window_x + int(20 * scale_w), window_y + int(120 * scale_h)),
            (window_x + window_width - int(20 * scale_w), window_y + int(120 * scale_h)),
            2
        )

        # Параметры кнопок
        button_width = int(400 * scale_w)
        button_height = int(40 * scale_h)
        button_margin = int(15 * scale_h)
        buttons_start_y = window_y + int(150 * scale_h)

        mouse_pos = pygame.mouse.get_pos()

        # Кнопки вопросов
        questions = [
            ("magic_academy", "Где находится магическая академия?"),
            ("warrior_academy", "Где находится военная академия?"),
        ]

        for i, (action, text) in enumerate(questions):
            btn_x = window_x + (window_width - button_width) // 2
            btn_y = buttons_start_y + i * (button_height + button_margin)

            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
            is_hovered = btn_rect.collidepoint(mouse_pos)

            bg_color = self.BUTTON_HOVER_COLOR if is_hovered else self.BUTTON_COLOR

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, btn_rect, 2, border_radius=5)

            btn_text = self.info_font.render(text, True, self.BUTTON_TEXT_COLOR)
            btn_text_rect = btn_text.get_rect()
            btn_text_rect.center = btn_rect.center
            self.screen.blit(btn_text, btn_text_rect)

            self.buttons.append((btn_rect, action))

        # Кнопка "Назад"
        back_btn_width = int(120 * scale_w)
        back_btn_height = int(40 * scale_h)
        back_btn_x = window_x + (window_width - back_btn_width) // 2
        back_btn_y = window_y + window_height - int(60 * scale_h)

        back_btn_rect = pygame.Rect(back_btn_x, back_btn_y, back_btn_width, back_btn_height)
        back_hovered = back_btn_rect.collidepoint(mouse_pos)

        back_bg_color = self.BACK_BUTTON_HOVER_COLOR if back_hovered else self.BACK_BUTTON_COLOR
        pygame.draw.rect(self.screen, back_bg_color, back_btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, back_btn_rect, 2, border_radius=5)

        back_text = self.info_font.render("Назад", True, self.BUTTON_TEXT_COLOR)
        back_text_rect = back_text.get_rect()
        back_text_rect.center = back_btn_rect.center
        self.screen.blit(back_text, back_text_rect)

        self.back_button = back_btn_rect

    def handle_click(self, mouse_pos):
        """
        Обработка клика мыши.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            str or None: ID выбранного действия или None
        """
        x, y = mouse_pos

        # Проверяем кнопку "Назад"
        if self.back_button and self.back_button.collidepoint(x, y):
            return "back"

        # Проверяем кнопки вопросов
        for btn_rect, action in self.buttons:
            if btn_rect.collidepoint(x, y):
                return action

        return None

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

    def get_direction_to_warrior_academy(self, from_location):
        """
        Получить направление к военной академии от текущей локации.

        Args:
            from_location: Объект локации, откуда ищем

        Returns:
            str: Направление (север, юг, запад, восток)
        """
        from game.constants import LOCATION_WARRIOR_ACADEMY

        # Ищем военную академию на карте
        academy_x, academy_y = None, None

        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                tile = self.game_map.get_tile(x, y)
                if tile.has_location():
                    if tile.location.location_type == LOCATION_WARRIOR_ACADEMY:
                        academy_x, academy_y = x, y
                        break
            if academy_x is not None:
                break

        if academy_x is None:
            return "Неизвестно где находится военная академия..."

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

    # Цвета кнопки
    BUTTON_COLOR = (50, 70, 50)
    BUTTON_HOVER_COLOR = (60, 90, 60)
    BUTTON_BORDER_COLOR = (100, 100, 120)
    BUTTON_TEXT_COLOR = (220, 220, 220)

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
        self.continue_button = None  # Кнопка "Продолжить"

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
        window_height = win['height']
        scale_h = win['scale_h']
        scale_w = win['scale_w']

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
            if test_surface.get_width() < window_width - int(40 * scale_w):
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

        # Кнопка "Продолжить" внизу
        btn_width = int(150 * scale_w)
        btn_height = int(40 * scale_h)
        btn_x = window_x + (window_width - btn_width) // 2
        btn_y = window_y + window_height - int(60 * scale_h)

        btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = btn_rect.collidepoint(mouse_pos)

        bg_color = self.BUTTON_HOVER_COLOR if is_hovered else self.BUTTON_COLOR
        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, btn_rect, 2, border_radius=5)

        btn_text = self.info_font.render("Продолжить", True, self.BUTTON_TEXT_COLOR)
        btn_text_rect = btn_text.get_rect()
        btn_text_rect.center = btn_rect.center
        self.screen.blit(btn_text, btn_text_rect)

        self.continue_button = btn_rect

    def handle_click(self, mouse_pos):
        """
        Обработка клика мыши.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            bool: True если клик был по кнопке "Продолжить"
        """
        if self.continue_button and self.continue_button.collidepoint(mouse_pos):
            return True
        return False
