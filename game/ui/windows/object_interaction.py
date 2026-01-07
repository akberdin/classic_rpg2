"""
Окно взаимодействия с объектами подземелий (ловушками).
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
        self.object_type = None  # 'trap'
        self.object_info = None  # Информация об объекте
        self.player = None  # Ссылка на игрока
        self.actions = []  # Список доступных действий

    def set_object(self, object_type: str, object_info: dict, player):
        """
        Установить объект для взаимодействия

        Args:
            object_type: Тип объекта ('trap')
            object_info: Информация об объекте (level, dc, и т.д.)
            player: Объект игрока
        """
        self.object_type = object_type
        self.object_info = object_info
        self.player = player
        self._build_actions()

    def _build_actions(self):
        """Построить список доступных действий на основе типа объекта и навыков игрока"""
        self.actions = []

        if not self.object_type or not self.object_info or not self.player:
            return

        # Проверяем наличие навыков
        has_disarm_trap = False

        if hasattr(self.player, 'skill_manager') and self.player.skill_manager:
            has_disarm_trap = self.player.skill_manager.get_skill("Обезвреживание") is not None

        if self.object_type == 'trap':
            # Действия для ловушки
            if has_disarm_trap:
                dc = self.object_info.get('dc', 15)
                # Примерный расчет шанса (можно уточнить)
                player_bonus = (
                    self.player.dexterity // 3 +
                    self.player.luck // 5 +
                    self.player.intelligence // 6
                )
                chance = max(5, min(95, (21 - dc + player_bonus) * 5))

                self.actions.append({
                    'key': 'D',
                    'label': 'Обезвредить ловушку',
                    'details': [
                        f'DC: {dc} (Ваш бонус: +{player_bonus})',
                        f'Шанс успеха: ~{chance}%',
                        'Стоимость: 10 Stamina'
                    ],
                    'action': 'disarm'
                })
            else:
                self.actions.append({
                    'key': 'W',
                    'label': 'Обойти осторожно',
                    'details': ['Попытка обойти ловушку'],
                    'action': 'bypass'
                })

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
            # ESC всегда отменяет
            if event.key == pygame.K_ESCAPE:
                return 'cancel'

            # Проверяем нажатие клавиш действий
            key_map = {
                pygame.K_d: 'D',
                pygame.K_w: 'W'
            }

            pressed_key = key_map.get(event.key)
            if pressed_key:
                # Ищем действие с этой клавишей
                for action in self.actions:
                    if action['key'] == pressed_key:
                        return action['action']

        return None

    def render(self):
        """Отрисовать окно взаимодействия"""
        if not self.object_type or not self.object_info:
            return

        screen_width, screen_height = self.screen.get_size()

        # Затемнение фона (легкое)
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.scaler:
            window_width = self.scaler.scale_width(450)
            max_height = self.scaler.scale_height(500)
        else:
            window_width = 450
            max_height = 500

        # Вычисляем высоту на основе количества действий
        header_height = 50
        action_spacing = 90
        window_height = header_height + len(self.actions) * action_spacing + 40

        if window_height > max_height:
            window_height = max_height

        # Центрирование
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Цвета
        border_color = (255, 215, 0)  # Золотой (для объектов)
        title_color = (255, 255, 100)  # Ярко-желтый
        text_color = (220, 220, 220)  # Светло-серый
        detail_color = (180, 180, 180)  # Серый

        # Фон окна
        pygame.draw.rect(self.screen, (30, 30, 35),
                        (window_x, window_y, window_width, window_height))

        # Рамка
        pygame.draw.rect(self.screen, border_color,
                        (window_x, window_y, window_width, window_height), 3)

        # Заголовок
        pygame.draw.rect(self.screen, (25, 25, 35),
                        (window_x + 3, window_y + 3, window_width - 6, header_height))

        title = self._get_title()
        title_text = self.font.render(title, True, title_color)
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.centery = window_y + header_height // 2
        self.screen.blit(title_text, title_rect)

        # Отрисовка действий
        current_y = window_y + header_height + 20

        for action in self.actions:
            # Клавиша и название
            key_label = f"[{action['key']}]"
            key_surface = self.font.render(key_label, True, border_color)
            action_surface = self.font.render(action['label'], True, text_color)

            self.screen.blit(key_surface, (window_x + 20, current_y))
            self.screen.blit(action_surface, (window_x + 80, current_y))

            # Детали
            detail_y = current_y + 25
            for detail in action['details']:
                detail_surface = self.info_font.render(f"└─ {detail}", True, detail_color)
                self.screen.blit(detail_surface, (window_x + 80, detail_y))
                detail_y += 20

            current_y += action_spacing

    def _get_title(self) -> str:
        """Получить заголовок окна"""
        if self.object_type == 'trap':
            trap_name = self.object_info.get('name', 'Ловушка')
            return f"Ловушка: {trap_name}"
        return "Интерактивный объект"
