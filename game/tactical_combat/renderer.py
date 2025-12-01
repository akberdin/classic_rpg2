"""
Отрисовка тактического боя
"""
import pygame


class TacticalCombatRenderer:
    """Рендерер для тактического боя"""

    def __init__(self, combat_system, screen, font, scaler=None):
        """
        Инициализация рендерера

        Args:
            combat_system: Система тактического боя
            screen: Pygame экран
            font: Шрифт
            scaler: UIScaler (опционально)
        """
        self.combat = combat_system
        self.screen = screen
        self.font = font
        self.scaler = scaler

        # Создаем шрифты разных размеров
        info_font_size = scaler.scale_font_size(16) if scaler else 16
        self.info_font = pygame.font.Font(None, info_font_size)

        small_font_size = scaler.scale_font_size(14) if scaler else 14
        self.small_font = pygame.font.Font(None, small_font_size)

        # Цвета из конфига
        ui_config = self.combat.config.get('ui', {})
        self.grid_color = tuple(ui_config.get('grid_color', [100, 100, 120]))
        self.player_color = tuple(ui_config.get('player_unit_color', [100, 200, 100]))
        self.enemy_color = tuple(ui_config.get('enemy_unit_color', [200, 100, 100]))

    def render(self):
        """Основной метод отрисовки"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемняем фон
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Вычисляем размеры и позицию поля боя
        field_width = self.combat.battlefield_width * self.combat.cell_size
        field_height = self.combat.battlefield_height * self.combat.cell_size

        # Центрируем поле по горизонтали, оставляем место для UI
        field_x = (screen_width - field_width) // 2
        field_y = 100

        # Отрисовываем заголовок
        self._render_header(field_x + field_width // 2, 50)

        # Отрисовываем поле боя
        self._render_battlefield(field_x, field_y)

        # Отрисовываем юнитов
        self._render_units(field_x, field_y)

        # Отрисовываем UI панели
        ui_y = field_y + field_height + 20
        self._render_ui_panel(field_x, ui_y, field_width)

        # Отрисовываем лог
        log_y = ui_y + 150
        self._render_combat_log(field_x, log_y, field_width)

    def _render_header(self, center_x, y):
        """Отрисовка заголовка"""
        title_text = self.font.render("ТАКТИЧЕСКИЙ БОЙ", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = center_x
        title_rect.y = y
        self.screen.blit(title_text, title_rect)

        # Индикатор хода
        turn_text = "Ваш ход" if self.combat.current_turn == "player" else "Ход противника"
        turn_color = (100, 255, 100) if self.combat.current_turn == "player" else (255, 100, 100)
        turn_surface = self.info_font.render(turn_text, True, turn_color)
        turn_rect = turn_surface.get_rect()
        turn_rect.centerx = center_x
        turn_rect.y = y + 30
        self.screen.blit(turn_surface, turn_rect)

    def _render_battlefield(self, field_x, field_y):
        """Отрисовка поля боя"""
        # Фон поля
        field_width = self.combat.battlefield_width * self.combat.cell_size
        field_height = self.combat.battlefield_height * self.combat.cell_size
        pygame.draw.rect(self.screen, (40, 40, 50),
                        (field_x, field_y, field_width, field_height))

        # Отрисовка сетки
        for x in range(self.combat.battlefield_width + 1):
            start_pos = (field_x + x * self.combat.cell_size, field_y)
            end_pos = (field_x + x * self.combat.cell_size, field_y + field_height)
            pygame.draw.line(self.screen, self.grid_color, start_pos, end_pos, 1)

        for y in range(self.combat.battlefield_height + 1):
            start_pos = (field_x, field_y + y * self.combat.cell_size)
            end_pos = (field_x + field_width, field_y + y * self.combat.cell_size)
            pygame.draw.line(self.screen, self.grid_color, start_pos, end_pos, 1)

        # Рамка поля
        pygame.draw.rect(self.screen, (150, 150, 200),
                        (field_x, field_y, field_width, field_height), 3)

    def _render_units(self, field_x, field_y):
        """Отрисовка юнитов на поле"""
        # Отрисовка игрока
        self._render_unit(self.combat.player_unit, field_x, field_y, self.player_color, "P")

        # Отрисовка врага
        self._render_unit(self.combat.enemy_unit, field_x, field_y, self.enemy_color, "E")

    def _render_unit(self, unit, field_x, field_y, color, label):
        """
        Отрисовка юнита

        Args:
            unit: Юнит для отрисовки
            field_x, field_y: Координаты поля
            color: Цвет юнита
            label: Метка (P для игрока, E для врага)
        """
        cell_x = field_x + unit.x * self.combat.cell_size
        cell_y = field_y + unit.y * self.combat.cell_size

        # Фон клетки юнита
        pygame.draw.rect(self.screen, color,
                        (cell_x + 2, cell_y + 2,
                         self.combat.cell_size - 4, self.combat.cell_size - 4))

        # Рамка
        pygame.draw.rect(self.screen, (255, 255, 255),
                        (cell_x + 2, cell_y + 2,
                         self.combat.cell_size - 4, self.combat.cell_size - 4), 2)

        # Метка
        label_surface = self.font.render(label, True, (255, 255, 255))
        label_rect = label_surface.get_rect()
        label_rect.center = (cell_x + self.combat.cell_size // 2,
                             cell_y + self.combat.cell_size // 2)
        self.screen.blit(label_surface, label_rect)

        # Прогресс-бары над юнитом
        self._render_unit_bars(unit, cell_x, cell_y)

    def _render_unit_bars(self, unit, cell_x, cell_y):
        """Отрисовка прогресс-баров юнита"""
        bar_width = self.combat.cell_size - 8
        bar_height = 4
        bar_x = cell_x + 4
        bar_y = cell_y - 16

        character = unit.character

        # HP bar
        max_hp = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        hp_ratio = character.health / max_hp if max_hp > 0 else 0

        # Фон
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        # Заполнение
        if hp_ratio > 0:
            hp_color = (100, 255, 100) if hp_ratio > 0.5 else (255, 165, 0) if hp_ratio > 0.25 else (255, 100, 100)
            pygame.draw.rect(self.screen, hp_color,
                           (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        # Рамка
        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

        # Mana bar (если есть)
        if hasattr(character, 'mana'):
            bar_y += bar_height + 2
            max_mana = character.get_effective_max_mana() if hasattr(character, 'get_effective_max_mana') else character.max_mana
            mana_ratio = character.mana / max_mana if max_mana > 0 else 0

            pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_width, bar_height))
            if mana_ratio > 0:
                pygame.draw.rect(self.screen, (100, 150, 255),
                               (bar_x, bar_y, int(bar_width * mana_ratio), bar_height))
            pygame.draw.rect(self.screen, (150, 150, 200), (bar_x, bar_y, bar_width, bar_height), 1)

        # Stamina bar
        if hasattr(character, 'stamina'):
            bar_y += bar_height + 2
            max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina
            stamina_ratio = character.stamina / max_stamina if max_stamina > 0 else 0

            pygame.draw.rect(self.screen, (50, 40, 20), (bar_x, bar_y, bar_width, bar_height))
            if stamina_ratio > 0:
                pygame.draw.rect(self.screen, (255, 220, 100),
                               (bar_x, bar_y, int(bar_width * stamina_ratio), bar_height))
            pygame.draw.rect(self.screen, (200, 180, 100), (bar_x, bar_y, bar_width, bar_height), 1)

    def _render_ui_panel(self, x, y, width):
        """Отрисовка панели UI с действиями"""
        panel_height = 140

        # Фон панели
        pygame.draw.rect(self.screen, (35, 35, 45), (x, y, width, panel_height))
        pygame.draw.rect(self.screen, (100, 100, 150), (x, y, width, panel_height), 2)

        # Заголовок
        title = self.info_font.render("Действия:", True, (200, 200, 220))
        self.screen.blit(title, (x + 10, y + 10))

        if self.combat.current_turn == "player":
            # Показываем доступные действия
            actions_y = y + 35

            # Кнопки действий
            actions = [
                ("1 - Переместиться", "MOVE"),
                ("2 - Использовать умение", "SKILL"),
                ("3 - Использовать зелье", "POTION"),
                ("4 - Пропустить ход", "PASS")
            ]

            for i, (text, action_type) in enumerate(actions):
                action_text = self.info_font.render(text, True, (150, 200, 150))
                self.screen.blit(action_text, (x + 20, actions_y + i * 25))

        else:
            # Ход противника
            wait_text = self.info_font.render("Ход противника...", True, (255, 150, 150))
            self.screen.blit(wait_text, (x + 20, y + 50))

    def _render_combat_log(self, x, y, width):
        """Отрисовка лога боя"""
        log_height = 150

        # Фон лога
        pygame.draw.rect(self.screen, (25, 25, 35), (x, y, width, log_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (x, y, width, log_height), 2)

        # Заголовок
        log_title = self.info_font.render("Журнал боя", True, (150, 200, 255))
        self.screen.blit(log_title, (x + 10, y + 10))

        # Логи
        log_y = y + 35
        line_height = 20
        max_visible = 5

        visible_logs = self.combat.combat_log[-max_visible:]
        for i, log_entry in enumerate(visible_logs):
            log_text = self.small_font.render(log_entry, True, (200, 200, 200))
            self.screen.blit(log_text, (x + 10, log_y + i * line_height))
