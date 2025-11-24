"""
Окно взаимодействия с NPC.
"""
import pygame
from game.ui.windows.base import BaseWindow


class InteractionWindow(BaseWindow):
    """Окно взаимодействия с NPC"""

    BASE_WIDTH = 500
    BASE_HEIGHT = 300

    # Действия для разных типов NPC
    NPC_ACTIONS = {
        'mage': [
            "[1] Купить заклинания",
            "[2] Обучение ({training_cost} зол.)",
            "[3] Агрессия",
            "[4] Уйти"
        ],
        'alchemist': [
            "[1] Торговля зельями",
            "[2] Взять квест",
            "[3] Сдать квест",
            "[4] Уйти"
        ],
        'hunter': [
            "[1] Торговля",
            "[2] Взять квест",
            "[3] Сдать квест",
            "[4] Уйти"
        ],
        'merchant': [
            "[1] Торговля",
            "[2] Агрессия",
            "[3] Уйти"
        ],
        'animal': [
            "[1] Агрессия",
            "[2] Уйти"
        ],
        'default': [
            "[1] Торговля",
            "[2] Агрессия",
            "[3] Уйти"
        ]
    }

    def render(self, npc):
        """
        Отрисовка окна взаимодействия с NPC.

        Args:
            npc: NPC для взаимодействия
        """
        if not npc:
            return

        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title=f"Взаимодействие: {npc.name}"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        scale_h = win['scale_h']

        # Информация о NPC
        info_y = window_y + int(70 * scale_h)
        npc_info = [
            f"Уровень: {npc.level}",
            f"Здоровье: {npc.health}/{npc.max_health}",
            f"Тип: {npc.npc_type}"
        ]

        for i, info in enumerate(npc_info):
            info_text = self.info_font.render(info, True, (200, 200, 200))
            info_rect = info_text.get_rect()
            info_rect.centerx = window_x + window_width // 2
            info_rect.y = info_y + i * int(25 * scale_h)
            self.screen.blit(info_text, info_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            self.FRAME_COLOR,
            (window_x + int(20 * scale_h), window_y + int(160 * scale_h)),
            (window_x + window_width - int(20 * scale_h), window_y + int(160 * scale_h)),
            2
        )

        # Варианты действий
        actions_y = window_y + int(180 * scale_h)
        actions_title = self.font.render("Выберите действие:", True, (200, 200, 200))
        actions_title_rect = actions_title.get_rect()
        actions_title_rect.centerx = window_x + window_width // 2
        actions_title_rect.y = actions_y
        self.screen.blit(actions_title, actions_title_rect)

        # Получаем действия для типа NPC
        actions = self._get_actions_for_npc(npc)

        # Отрисовка кнопок действий
        buttons_y = actions_y + int(40 * scale_h)
        for i, action in enumerate(actions):
            action_text = self.info_font.render(action, True, (150, 255, 150))
            action_rect = action_text.get_rect()
            action_rect.centerx = window_x + window_width // 2
            action_rect.y = buttons_y + i * int(30 * scale_h)
            self.screen.blit(action_text, action_rect)

    def _get_actions_for_npc(self, npc):
        """
        Получить список действий для типа NPC.

        Args:
            npc: NPC объект

        Returns:
            list: Список строк с действиями
        """
        npc_type = npc.npc_type

        # Животные
        if npc_type in ['wolf', 'bear', 'deer']:
            return self.NPC_ACTIONS['animal']

        # Маги - с расчётом стоимости обучения
        if npc_type == 'mage':
            training_cost = 50 * npc.level
            actions = self.NPC_ACTIONS['mage'].copy()
            actions[1] = actions[1].format(training_cost=training_cost)
            return actions

        # Другие типы NPC
        if npc_type in self.NPC_ACTIONS:
            return self.NPC_ACTIONS[npc_type]

        return self.NPC_ACTIONS['default']
