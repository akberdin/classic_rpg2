"""
Окно выбора NPC при наличии нескольких NPC в одной клетке.
"""
import pygame
from game.ui.windows.base import BaseWindow


class NPCSelectionWindow(BaseWindow):
    """Окно выбора NPC для взаимодействия"""

    BASE_WIDTH = 500
    BASE_HEIGHT = 400

    def __init__(self, screen, font, info_font, ui_scaler):
        """
        Инициализация окна выбора NPC.

        Args:
            screen: Поверхность pygame для отрисовки
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Масштабировщик UI
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.npcs = []  # Список NPC для выбора
        self.selected_index = 0  # Индекс выбранного NPC

    def set_npcs(self, npcs):
        """
        Установить список NPC для выбора.

        Args:
            npcs: Список NPC объектов
        """
        self.npcs = npcs
        self.selected_index = 0

    def get_selected_npc(self):
        """
        Получить выбранного NPC.

        Returns:
            NPC объект или None
        """
        if 0 <= self.selected_index < len(self.npcs):
            return self.npcs[self.selected_index]
        return None

    def handle_input(self, event):
        """
        Обработка ввода пользователя.

        Args:
            event: Событие pygame

        Returns:
            str: "select" если выбран NPC, "cancel" если отменено, None иначе
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if self.npcs:
                    self.selected_index = max(0, self.selected_index - 1)
                return None
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if self.npcs:
                    self.selected_index = min(len(self.npcs) - 1, self.selected_index + 1)
                return None
            elif event.key == pygame.K_RETURN or event.key == pygame.K_e:
                return "select"
            elif event.key == pygame.K_ESCAPE:
                return "cancel"
            # Цифровые клавиши 1-9 для быстрого выбора
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                             pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                digit = event.key - pygame.K_1  # 0-8
                if 0 <= digit < len(self.npcs):
                    self.selected_index = digit
                    return "select"
        return None

    def render(self):
        """
        Отрисовка окна выбора NPC.
        """
        if not self.npcs:
            return

        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title="Выберите NPC для взаимодействия"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Информационный текст
        info_y = window_y + int(70 * scale_h)
        info_text = self.info_font.render(
            f"В этой клетке находится {len(self.npcs)} NPC. Выберите с кем взаимодействовать:",
            True,
            (200, 200, 200)
        )
        info_rect = info_text.get_rect()
        info_rect.centerx = window_x + window_width // 2
        info_rect.y = info_y
        self.screen.blit(info_text, info_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), window_y + int(110 * scale_h)),
            (window_x + window_width - int(20 * scale_h), window_y + int(110 * scale_h)),
            2
        )

        # Список NPC
        list_y = window_y + int(130 * scale_h)
        for i, npc in enumerate(self.npcs):
            is_selected = (i == self.selected_index)

            # Цвет в зависимости от выбора
            color = (255, 255, 100) if is_selected else (200, 200, 200)

            # Формируем информацию о NPC
            npc_type_display = self._get_npc_type_display(npc.npc_type)
            npc_info = f"[{i+1}] {npc.name} ({npc_type_display}, ур. {npc.level})"

            # Отрисовка имени NPC
            npc_text = self.info_font.render(npc_info, True, color)
            npc_rect = npc_text.get_rect()
            npc_rect.x = window_x + int(40 * scale_h)
            npc_rect.y = list_y + i * int(35 * scale_h)
            self.screen.blit(npc_text, npc_rect)

            # Маркер выбранного элемента
            if is_selected:
                marker = "→"
                marker_text = self.font.render(marker, True, (255, 255, 100))
                marker_rect = marker_text.get_rect()
                marker_rect.right = npc_rect.left - int(10 * scale_h)
                marker_rect.centery = npc_rect.centery
                self.screen.blit(marker_text, marker_rect)

        # Подсказки управления
        hints_y = window_y + int(350 * scale_h)
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), hints_y - int(10 * scale_h)),
            (window_x + window_width - int(20 * scale_h), hints_y - int(10 * scale_h)),
            2
        )

        hints = [
            "[1-9] - Быстрый выбор",
            "[W/S или ↑/↓] - Навигация",
            "[Enter или E] - Подтвердить | [Esc] - Отмена"
        ]

        for i, hint in enumerate(hints):
            hint_text = self.info_font.render(hint, True, (150, 150, 150))
            hint_rect = hint_text.get_rect()
            hint_rect.centerx = window_x + window_width // 2
            hint_rect.y = hints_y + i * int(20 * scale_h)
            self.screen.blit(hint_text, hint_rect)

    def _get_npc_type_display(self, npc_type):
        """
        Получить отображаемое название типа NPC.

        Args:
            npc_type: Тип NPC

        Returns:
            str: Отображаемое название
        """
        type_names = {
            'merchant': 'Торговец',
            'guard': 'Стражник',
            'mage': 'Маг',
            'alchemist': 'Алхимик',
            'hunter': 'Охотник',
            'bandit': 'Бандит',
            'miner': 'Шахтёр',
            'undead': 'Нежить',
            'necromancer': 'Некромант',
            'wolf': 'Волк',
            'bear': 'Медведь',
            'deer': 'Олень'
        }
        return type_names.get(npc_type, npc_type.capitalize())
