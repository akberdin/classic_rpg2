"""
Окно взаимодействия для входа в подземелье или шахту
"""
import pygame
from game.ui.windows.base import BaseWindow


class DungeonEntryWindow(BaseWindow):
    """Окно подтверждения входа в подземелье/шахту"""

    def __init__(self, screen, font, info_font, ui_scaler):
        """
        Инициализация окна

        Args:
            screen: Экран pygame
            font: Основной шрифт
            info_font: Шрифт для информации
            ui_scaler: Масштабировщик UI
        """
        super().__init__(screen, font, info_font, ui_scaler)

        # Параметры окна
        self.window_width = 500
        self.window_height = 280

        # Данные о локации
        self.location_name = ""
        self.dungeon_type = ""  # "dungeon" или "mine"
        self.location_level = 1

        # Выбранный пункт меню
        self.selected_option = 0

        # Опции меню
        self.options = []

    def set_location(self, location_name: str, dungeon_type: str, location_level: int = 1):
        """
        Установить информацию о локации

        Args:
            location_name: Название локации
            dungeon_type: Тип ("dungeon" или "mine")
            location_level: Уровень подземелья
        """
        self.location_name = location_name
        self.dungeon_type = dungeon_type
        self.location_level = location_level
        self.selected_option = 0

        # Формируем опции меню
        if dungeon_type == "dungeon":
            self.options = [
                ("1. Войти в подземелье", "enter"),
                ("2. Уйти", "leave"),
            ]
        else:
            self.options = [
                ("1. Войти в шахту", "enter"),
                ("2. Уйти", "leave"),
            ]

    def handle_input(self, event) -> str:
        """
        Обработка ввода

        Args:
            event: Событие pygame

        Returns:
            str: Действие ("enter", "leave", или "")
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return "enter"
            elif event.key == pygame.K_2 or event.key == pygame.K_ESCAPE:
                return "leave"
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = max(0, self.selected_option - 1)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = min(len(self.options) - 1, self.selected_option + 1)
            elif event.key == pygame.K_RETURN:
                if self.options:
                    return self.options[self.selected_option][1]

        return ""

    def render(self):
        """Отрисовка окна"""
        # Затемнение фона
        self.draw_overlay()

        # Размеры окна с масштабированием
        win_w = self.scaler.scale_x(self.window_width)
        win_h = self.scaler.scale_y(self.window_height)

        # Центрируем окно
        win_x = (self.screen.get_width() - win_w) // 2
        win_y = (self.screen.get_height() - win_h) // 2

        # Фон окна
        pygame.draw.rect(self.screen, (40, 40, 50), (win_x, win_y, win_w, win_h))
        pygame.draw.rect(self.screen, (100, 100, 120), (win_x, win_y, win_w, win_h), 2)

        # Заголовок
        title_height = self.scaler.scale_y(40)
        title_rect = pygame.Rect(win_x, win_y, win_w, title_height)
        pygame.draw.rect(self.screen, (60, 60, 80), title_rect)
        pygame.draw.line(self.screen, (100, 100, 120),
                        (win_x, win_y + title_height),
                        (win_x + win_w, win_y + title_height), 2)

        # Текст заголовка
        if self.dungeon_type == "dungeon":
            title_text = "Вход в подземелье"
            title_color = (200, 150, 100)  # Оранжевый для подземелья
        else:
            title_text = "Вход в шахту"
            title_color = (150, 150, 200)  # Синеватый для шахты

        title_surface = self.font.render(title_text, True, title_color)
        title_x = win_x + (win_w - title_surface.get_width()) // 2
        title_y = win_y + (title_height - title_surface.get_height()) // 2
        self.screen.blit(title_surface, (title_x, title_y))

        # Контент
        content_y = win_y + title_height + self.scaler.scale_y(15)
        line_height = self.scaler.scale_y(25)
        padding_x = self.scaler.scale_x(20)

        # Название локации
        loc_text = f"Локация: {self.location_name}"
        loc_surface = self.info_font.render(loc_text, True, (220, 220, 220))
        self.screen.blit(loc_surface, (win_x + padding_x, content_y))
        content_y += line_height

        # Уровень
        level_text = f"Уровень опасности: {self.location_level}"
        level_color = self._get_level_color(self.location_level)
        level_surface = self.info_font.render(level_text, True, level_color)
        self.screen.blit(level_surface, (win_x + padding_x, content_y))
        content_y += line_height

        # Описание
        if self.dungeon_type == "dungeon":
            desc_lines = [
                "В подземелье обитает нежить.",
                "Будьте осторожны с ловушками!",
                "Выход возможен только через специальные точки.",
            ]
        else:
            desc_lines = [
                "В шахте можно найти ценную руду.",
                "Остерегайтесь обвалов и монстров!",
                "Выход возможен только через специальные точки.",
            ]

        content_y += self.scaler.scale_y(10)
        for desc in desc_lines:
            desc_surface = self.info_font.render(desc, True, (180, 180, 180))
            self.screen.blit(desc_surface, (win_x + padding_x, content_y))
            content_y += line_height

        # Опции меню
        content_y += self.scaler.scale_y(15)
        pygame.draw.line(self.screen, (80, 80, 100),
                        (win_x + padding_x, content_y),
                        (win_x + win_w - padding_x, content_y), 1)
        content_y += self.scaler.scale_y(10)

        for i, (option_text, _) in enumerate(self.options):
            if i == self.selected_option:
                # Подсветка выбранного пункта
                highlight_rect = pygame.Rect(
                    win_x + padding_x - 5,
                    content_y - 2,
                    win_w - 2 * padding_x + 10,
                    line_height
                )
                pygame.draw.rect(self.screen, (60, 80, 100), highlight_rect)
                text_color = (255, 255, 100)
            else:
                text_color = (200, 200, 200)

            option_surface = self.font.render(option_text, True, text_color)
            self.screen.blit(option_surface, (win_x + padding_x, content_y))
            content_y += line_height

    def _get_level_color(self, level: int) -> tuple:
        """Получить цвет для уровня опасности"""
        if level <= 2:
            return (100, 255, 100)  # Зеленый - легко
        elif level <= 4:
            return (200, 255, 100)  # Желто-зеленый
        elif level <= 6:
            return (255, 200, 100)  # Оранжевый
        elif level <= 8:
            return (255, 150, 100)  # Красно-оранжевый
        else:
            return (255, 100, 100)  # Красный - опасно


class DungeonExitWindow(BaseWindow):
    """Окно подтверждения выхода из подземелья"""

    def __init__(self, screen, font, info_font, ui_scaler):
        """Инициализация окна"""
        super().__init__(screen, font, info_font, ui_scaler)

        self.window_width = 400
        self.window_height = 180

        self.dungeon_name = ""

    def set_dungeon_name(self, name: str):
        """Установить название подземелья"""
        self.dungeon_name = name

    def handle_input(self, event) -> str:
        """
        Обработка ввода

        Returns:
            str: "exit", "stay", или ""
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 or event.key == pygame.K_RETURN:
                return "exit"
            elif event.key == pygame.K_2 or event.key == pygame.K_ESCAPE:
                return "stay"

        return ""

    def render(self):
        """Отрисовка окна"""
        self.draw_overlay()

        win_w = self.scaler.scale_x(self.window_width)
        win_h = self.scaler.scale_y(self.window_height)
        win_x = (self.screen.get_width() - win_w) // 2
        win_y = (self.screen.get_height() - win_h) // 2

        # Фон
        pygame.draw.rect(self.screen, (40, 40, 50), (win_x, win_y, win_w, win_h))
        pygame.draw.rect(self.screen, (100, 100, 120), (win_x, win_y, win_w, win_h), 2)

        # Заголовок
        title_height = self.scaler.scale_y(35)
        pygame.draw.rect(self.screen, (60, 60, 80), (win_x, win_y, win_w, title_height))

        title_surface = self.font.render("Выход из подземелья", True, (150, 200, 150))
        title_x = win_x + (win_w - title_surface.get_width()) // 2
        title_y = win_y + (title_height - title_surface.get_height()) // 2
        self.screen.blit(title_surface, (title_x, title_y))

        # Вопрос
        content_y = win_y + title_height + self.scaler.scale_y(20)
        line_height = self.scaler.scale_y(25)
        padding_x = self.scaler.scale_x(20)

        question = f"Покинуть {self.dungeon_name}?"
        q_surface = self.info_font.render(question, True, (220, 220, 220))
        q_x = win_x + (win_w - q_surface.get_width()) // 2
        self.screen.blit(q_surface, (q_x, content_y))
        content_y += line_height + self.scaler.scale_y(15)

        # Опции
        options = [
            ("1. Выйти", (150, 255, 150)),
            ("2. Остаться", (200, 200, 200)),
        ]

        for text, color in options:
            opt_surface = self.font.render(text, True, color)
            opt_x = win_x + (win_w - opt_surface.get_width()) // 2
            self.screen.blit(opt_surface, (opt_x, content_y))
            content_y += line_height
