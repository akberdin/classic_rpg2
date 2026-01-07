"""
Окно взаимодействия с объектами подземелий.
Зарезервировано для будущих интерактивных объектов.
"""
import pygame
from game.ui.windows.base import BaseWindow


class ObjectInteractionWindow(BaseWindow):
    """Контекстное меню для взаимодействия с объектами подземелий"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна взаимодействия

        Args:
            screen: Экран pygame
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект масштабирования UI
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.object_type = None
        self.object_info = None
        self.player = None
        self.actions = []

    def set_object(self, object_type: str, object_info: dict, player):
        """
        Установить объект для взаимодействия

        Args:
            object_type: Тип объекта
            object_info: Информация об объекте
            player: Объект игрока
        """
        self.object_type = object_type
        self.object_info = object_info
        self.player = player
        self._build_actions()

    def _build_actions(self):
        """Построить список доступных действий на основе типа объекта"""
        self.actions = []
        # Зарезервировано для будущих интерактивных объектов

        # Всегда добавляем отмену
        self.actions.append({
            'key': 'ESC',
            'label': 'Отмена',
            'details': [],
            'action': 'cancel'
        })

    def handle_input(self, event):
        """
        Обработать ввод

        Args:
            event: Событие pygame

        Returns:
            str: Действие для выполнения или None
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'cancel'
        return None

    def render(self):
        """Отрисовать окно взаимодействия"""
        if not self.object_type or not self.object_info:
            return
        # Зарезервировано для будущих интерактивных объектов

    def _get_title(self) -> str:
        """Получить заголовок окна"""
        return "Интерактивный объект"
