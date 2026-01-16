"""
Окно взаимодействия с инфраструктурой поселения.
Отображает доступные здания и услуги в населенном пункте.
"""
import pygame
from game.ui.windows.base import BaseWindow


# Словарь локализации инфраструктурных объектов
INFRASTRUCTURE_NAMES = {
    "forge": "Кузница",
    "workshop": "Мастерская",
    "jewelry_workshop": "Ювелирная мастерская",
    "alchemy_lab": "Алхимическая лаборатория",
    "enchanting_workshop": "Мастерская зачарования",
    "shop": "Магазин",
    "tavern": "Таверна",
    "town_hall": "Ратуша",
    "warrior_guild": "Гильдия воинов",
    "hunter_guild": "Гильдия охотников",
    "shadow_guild": "Гильдия теней",
    "mage_guild": "Гильдия магов",
    "sawmill": "Лесопилка",
    "smeltery": "Плавильня",
    "charcoal_burners": "Углежоги",
    "tannery": "Кожевенная мастерская",
    "house": "Дом",
    "palace": "Дворец"
}

# Описания инфраструктурных объектов
INFRASTRUCTURE_DESCRIPTIONS = {
    "forge": "Ковка и улучшение оружия и доспехов",
    "workshop": "Изготовление и ремонт предметов",
    "jewelry_workshop": "Создание украшений и магических колец",
    "alchemy_lab": "Варка зелий и изучение рецептов",
    "enchanting_workshop": "Зачарование предметов магией",
    "shop": "Покупка и продажа товаров",
    "tavern": "Отдых, слухи и наем спутников",
    "town_hall": "Управление городом и квесты",
    "warrior_guild": "Обучение воинскому искусству",
    "hunter_guild": "Обучение охоте и выслеживанию",
    "shadow_guild": "Обучение скрытности и воровству",
    "mage_guild": "Обучение магическим искусствам",
    "sawmill": "Переработка древесины",
    "smeltery": "Плавка руды в металлы",
    "charcoal_burners": "Производство угля для кузницы",
    "tannery": "Обработка кожи и шкур",
    "house": "Жилье для отдыха",
    "palace": "Резиденция правителя"
}

# Категории инфраструктуры для группировки
INFRASTRUCTURE_CATEGORIES = {
    "Мастерские": ["forge", "workshop", "jewelry_workshop", "alchemy_lab", "enchanting_workshop"],
    "Услуги": ["shop", "tavern", "town_hall"],
    "Гильдии": ["warrior_guild", "hunter_guild", "shadow_guild", "mage_guild"],
    "Производство": ["sawmill", "smeltery", "charcoal_burners", "tannery"],
    "Прочее": ["house", "palace"]
}

# Порядок отображения (без категорий, простой список)
INFRASTRUCTURE_ORDER = [
    "shop", "tavern", "town_hall",
    "forge", "workshop", "jewelry_workshop", "alchemy_lab", "enchanting_workshop",
    "warrior_guild", "hunter_guild", "shadow_guild", "mage_guild",
    "sawmill", "smeltery", "charcoal_burners", "tannery",
    "house", "palace"
]


class InfrastructureButton:
    """Класс для представления кликабельной кнопки инфраструктуры"""

    def __init__(self, infrastructure_id, name, rank, rect, description=""):
        """
        Инициализация кнопки.

        Args:
            infrastructure_id: ID инфраструктуры (forge, shop и т.д.)
            name: Отображаемое имя
            rank: Ранг здания
            rect: pygame.Rect области кнопки
            description: Описание здания
        """
        self.id = infrastructure_id
        self.name = name
        self.rank = rank
        self.rect = rect
        self.description = description
        self.hovered = False

    def contains_point(self, x, y):
        """Проверить, находится ли точка внутри кнопки"""
        return self.rect.collidepoint(x, y)


class InfrastructureMenuWindow(BaseWindow):
    """Окно меню инфраструктуры поселения"""

    BASE_WIDTH = 700
    BASE_HEIGHT = 550

    # Цвета кнопок
    BUTTON_COLOR = (50, 50, 60)
    BUTTON_HOVER_COLOR = (70, 70, 85)
    BUTTON_BORDER_COLOR = (100, 100, 120)
    BUTTON_TEXT_COLOR = (220, 220, 220)
    BUTTON_RANK_COLOR = (180, 150, 80)
    LEAVE_BUTTON_COLOR = (80, 50, 50)
    LEAVE_BUTTON_HOVER_COLOR = (100, 60, 60)
    SPECIAL_BUTTON_COLOR = (50, 70, 50)
    SPECIAL_BUTTON_HOVER_COLOR = (60, 90, 60)

    def __init__(self, screen, font, info_font, ui_scaler, game_map):
        """
        Инициализация окна инфраструктуры.

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект для масштабирования UI
            game_map: Карта игры
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.game_map = game_map
        self.location = None
        self.buttons = []  # Список InfrastructureButton
        self.leave_button = None  # Кнопка "Уйти"
        self.ask_locals_button = None  # Кнопка "Расспросить местных"
        self.selected_action = None  # Выбранное действие
        self.scroll_offset = 0  # Смещение прокрутки
        self.hovered_button = None  # Кнопка под курсором

    def set_location(self, location):
        """
        Установить текущую локацию.

        Args:
            location: Объект локации
        """
        self.location = location
        self.selected_action = None
        self.scroll_offset = 0
        self.buttons = []
        self.hovered_button = None

    def get_available_infrastructure(self):
        """
        Получить список доступной инфраструктуры в локации.

        Returns:
            list: Список кортежей (id, name, rank, description)
        """
        if not self.location:
            return []

        infrastructure = getattr(self.location, 'infrastructure', {})
        if not infrastructure:
            return []

        available = []
        for infra_id in INFRASTRUCTURE_ORDER:
            if infra_id in infrastructure:
                rank = infrastructure[infra_id]
                if rank > 0:
                    name = INFRASTRUCTURE_NAMES.get(infra_id, infra_id)
                    description = INFRASTRUCTURE_DESCRIPTIONS.get(infra_id, "")
                    available.append((infra_id, name, rank, description))

        return available

    def render(self):
        """Отрисовка окна инфраструктуры."""
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
        window_height = win['height']
        scale_h = win['scale_h']
        scale_w = win['scale_w']

        # Очищаем список кнопок перед отрисовкой
        self.buttons = []

        # Приветственный текст
        welcome_y = window_y + int(60 * scale_h)
        welcome_text = self.font.render(
            f"Добро пожаловать в {self.location.name}!",
            True, (200, 200, 200)
        )
        welcome_rect = welcome_text.get_rect()
        welcome_rect.centerx = window_x + window_width // 2
        welcome_rect.y = welcome_y
        self.screen.blit(welcome_text, welcome_rect)

        # Описание локации
        desc_y = welcome_y + int(30 * scale_h)
        desc_text = self.info_font.render(
            self.location.get_description(),
            True, (150, 150, 150)
        )
        desc_rect = desc_text.get_rect()
        desc_rect.centerx = window_x + window_width // 2
        desc_rect.y = desc_y
        self.screen.blit(desc_text, desc_rect)

        # Разделительная линия
        line_y = desc_y + int(40 * scale_h)
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_w), line_y),
            (window_x + window_width - int(20 * scale_w), line_y),
            2
        )

        # Заголовок "Доступные услуги"
        services_title_y = line_y + int(15 * scale_h)
        services_title = self.font.render("Доступные услуги:", True, (200, 200, 200))
        services_title_rect = services_title.get_rect()
        services_title_rect.centerx = window_x + window_width // 2
        services_title_rect.y = services_title_y
        self.screen.blit(services_title, services_title_rect)

        # Получаем доступную инфраструктуру
        infrastructure = self.get_available_infrastructure()

        # Область для кнопок
        buttons_start_y = services_title_y + int(40 * scale_h)
        buttons_area_height = window_height - (buttons_start_y - window_y) - int(80 * scale_h)

        # Параметры кнопок
        button_width = int(300 * scale_w)
        button_height = int(35 * scale_h)
        button_margin = int(8 * scale_h)
        columns = 2
        column_width = (window_width - int(60 * scale_w)) // columns

        # Отрисовка кнопок инфраструктуры
        for i, (infra_id, name, rank, description) in enumerate(infrastructure):
            col = i % columns
            row = i // columns

            btn_x = window_x + int(30 * scale_w) + col * column_width + (column_width - button_width) // 2
            btn_y = buttons_start_y + row * (button_height + button_margin)

            # Проверяем, не выходит ли кнопка за область
            if btn_y + button_height > window_y + window_height - int(70 * scale_h):
                continue

            # Создаем rect для кнопки
            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)

            # Проверяем наведение мыши
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = btn_rect.collidepoint(mouse_pos)

            # Выбираем цвет в зависимости от состояния
            if infra_id == "shop":
                bg_color = self.SPECIAL_BUTTON_HOVER_COLOR if is_hovered else self.SPECIAL_BUTTON_COLOR
            else:
                bg_color = self.BUTTON_HOVER_COLOR if is_hovered else self.BUTTON_COLOR

            # Отрисовка кнопки
            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, btn_rect, 2, border_radius=5)

            # Текст кнопки
            display_name = f"{name}"
            if rank > 1:
                display_name += f" (ур. {rank})"

            btn_text = self.info_font.render(display_name, True, self.BUTTON_TEXT_COLOR)
            btn_text_rect = btn_text.get_rect()
            btn_text_rect.centery = btn_y + button_height // 2
            btn_text_rect.x = btn_x + int(15 * scale_w)
            self.screen.blit(btn_text, btn_text_rect)

            # Создаем объект кнопки
            button = InfrastructureButton(infra_id, name, rank, btn_rect, description)
            button.hovered = is_hovered
            self.buttons.append(button)

        # Нижняя панель с кнопками "Расспросить" и "Уйти"
        bottom_panel_y = window_y + window_height - int(60 * scale_h)

        # Кнопка "Расспросить местных жителей"
        ask_btn_width = int(250 * scale_w)
        ask_btn_height = int(40 * scale_h)
        ask_btn_x = window_x + int(30 * scale_w)
        ask_btn_y = bottom_panel_y

        ask_btn_rect = pygame.Rect(ask_btn_x, ask_btn_y, ask_btn_width, ask_btn_height)
        mouse_pos = pygame.mouse.get_pos()
        ask_hovered = ask_btn_rect.collidepoint(mouse_pos)

        ask_bg_color = self.SPECIAL_BUTTON_HOVER_COLOR if ask_hovered else self.SPECIAL_BUTTON_COLOR
        pygame.draw.rect(self.screen, ask_bg_color, ask_btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, ask_btn_rect, 2, border_radius=5)

        ask_text = self.info_font.render("Расспросить местных", True, self.BUTTON_TEXT_COLOR)
        ask_text_rect = ask_text.get_rect()
        ask_text_rect.center = ask_btn_rect.center
        self.screen.blit(ask_text, ask_text_rect)

        self.ask_locals_button = ask_btn_rect

        # Кнопка "Уйти"
        leave_btn_width = int(120 * scale_w)
        leave_btn_height = int(40 * scale_h)
        leave_btn_x = window_x + window_width - leave_btn_width - int(30 * scale_w)
        leave_btn_y = bottom_panel_y

        leave_btn_rect = pygame.Rect(leave_btn_x, leave_btn_y, leave_btn_width, leave_btn_height)
        leave_hovered = leave_btn_rect.collidepoint(mouse_pos)

        leave_bg_color = self.LEAVE_BUTTON_HOVER_COLOR if leave_hovered else self.LEAVE_BUTTON_COLOR
        pygame.draw.rect(self.screen, leave_bg_color, leave_btn_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, leave_btn_rect, 2, border_radius=5)

        leave_text = self.info_font.render("Уйти", True, self.BUTTON_TEXT_COLOR)
        leave_text_rect = leave_text.get_rect()
        leave_text_rect.center = leave_btn_rect.center
        self.screen.blit(leave_text, leave_text_rect)

        self.leave_button = leave_btn_rect

        # Подсказка для наведенной кнопки
        for button in self.buttons:
            if button.hovered and button.description:
                self._draw_tooltip(button.description, mouse_pos[0], mouse_pos[1])
                break

    def _draw_tooltip(self, text, x, y):
        """Отрисовка подсказки"""
        padding = 8
        text_surface = self.info_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()

        tooltip_width = text_rect.width + padding * 2
        tooltip_height = text_rect.height + padding * 2

        # Корректируем позицию
        screen_width, screen_height = self.screen.get_size()
        tooltip_x = x + 15
        tooltip_y = y - tooltip_height - 5

        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5
        if tooltip_y < 0:
            tooltip_y = y + 20

        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(self.screen, (30, 30, 35), tooltip_rect, border_radius=4)
        pygame.draw.rect(self.screen, (100, 100, 120), tooltip_rect, 1, border_radius=4)

        self.screen.blit(text_surface, (tooltip_x + padding, tooltip_y + padding))

    def handle_click(self, mouse_pos):
        """
        Обработка клика мыши.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            str or None: ID выбранного действия или None
        """
        x, y = mouse_pos

        # Проверяем кнопку "Уйти"
        if self.leave_button and self.leave_button.collidepoint(x, y):
            return "leave"

        # Проверяем кнопку "Расспросить местных"
        if self.ask_locals_button and self.ask_locals_button.collidepoint(x, y):
            return "ask_locals"

        # Проверяем кнопки инфраструктуры
        for button in self.buttons:
            if button.contains_point(x, y):
                return button.id

        return None

    def get_button_at_pos(self, mouse_pos):
        """
        Получить кнопку под указанной позицией.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            InfrastructureButton or None
        """
        x, y = mouse_pos
        for button in self.buttons:
            if button.contains_point(x, y):
                return button
        return None
