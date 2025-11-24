"""
Окно характеристик персонажа.
"""
import pygame
from game.ui.windows.base import BaseWindow


class CharacterWindow(BaseWindow):
    """Окно характеристик персонажа"""

    BASE_WIDTH = 700
    BASE_HEIGHT = 600

    def __init__(self, screen, font, info_font, scaler=None):
        super().__init__(screen, font, info_font, scaler)
        self.selected_stat_index = 0

        # Список характеристик для навигации
        self.stats_list = [
            ('strength', 'Сила'),
            ('dexterity', 'Ловкость'),
            ('constitution', 'Телосложение'),
            ('spirit', 'Дух'),
            ('intelligence', 'Интеллект'),
            ('luck', 'Удача')
        ]

    def render(self, player):
        """
        Отрисовка окна характеристик

        Args:
            player: Объект игрока
        """
        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title="ХАРАКТЕРИСТИКИ ПЕРСОНАЖА"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        window_height = win['height']
        scale_w = win['scale_w']
        scale_h = win['scale_h']

        # Информация о персонаже
        info_y = window_y + int(50 * scale_h)
        player_rank = player.get_rank()

        info_lines = [
            f"Имя: {player.name}",
            f"Уровень: {player.level} ({player_rank})",
            f"Опыт: {player.experience}/{player.experience_to_next_level}",
            f"Золото: {player.inventory.gold}",
        ]

        for i, line in enumerate(info_lines):
            info_text = self.info_font.render(line, True, (200, 200, 200))
            self.screen.blit(info_text, (window_x + int(50 * scale_w), info_y + i * int(25 * scale_h)))

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(20 * scale_w), window_y + int(180 * scale_h)),
            (window_x + window_width - int(20 * scale_w), window_y + int(180 * scale_h)),
            2
        )

        # Характеристики
        stats_y = window_y + int(200 * scale_h)
        stats = player.get_stats()
        base_stats = player.get_base_stats()
        equip_bonuses = player.inventory.get_total_stats_bonus()

        # Свободные очки
        if player.stat_points > 0:
            points_text = self.font.render(
                f"Свободных очков: {player.stat_points}",
                True,
                (100, 255, 100)
            )
            points_rect = points_text.get_rect()
            points_rect.centerx = window_x + window_width // 2
            points_rect.y = stats_y - int(30 * scale_h)
            self.screen.blit(points_text, points_rect)

        # Отображение характеристик
        stat_line_height = max(28, int(32 * scale_h))
        for i, (stat_key, stat_name) in enumerate(self.stats_list):
            display_y = stats_y + i * stat_line_height

            # Подсветка выбранной характеристики
            if i == self.selected_stat_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 80, 100),
                    (window_x + int(40 * scale_w), display_y - int(5 * scale_h), window_width - int(80 * scale_w), int(35 * scale_h))
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 150, 200),
                    (window_x + int(40 * scale_w), display_y - int(5 * scale_h), window_width - int(80 * scale_w), int(35 * scale_h)),
                    2
                )

            # Название характеристики
            name_text = self.info_font.render(
                f"{stat_name}:",
                True,
                (220, 220, 220)
            )
            self.screen.blit(name_text, (window_x + int(60 * scale_w), display_y))

            # Значение
            base_value = base_stats[stat_key]
            bonus = equip_bonuses.get(stat_key, 0)
            total_value = stats[stat_key]

            if bonus > 0:
                # Компактный формат для больших значений
                if total_value > 999:
                    value_str = f"{base_value}+{bonus}={total_value}"
                else:
                    value_str = f"{base_value} (+{bonus}) = {total_value}"
                value_color = (150, 255, 150)
            else:
                value_str = f"{total_value}"
                value_color = (200, 200, 200)

            value_text = self.info_font.render(value_str, True, value_color)
            # Ограничиваем ширину текста
            max_text_width = int(180 * scale_w)
            if value_text.get_width() > max_text_width:
                # Используем самый компактный формат
                value_str = f"{total_value}"
                if bonus > 0:
                    value_str += f"(+{bonus})"
                value_text = self.info_font.render(value_str, True, value_color)
            self.screen.blit(value_text, (window_x + int(300 * scale_w), display_y))

            # Кнопка + для добавления очка
            if player.stat_points > 0 and i == self.selected_stat_index:
                plus_text = self.info_font.render("[+]", True, (100, 255, 100))
                self.screen.blit(plus_text, (window_x + window_width - int(120 * scale_w), display_y))

        # Дополнительная информация
        additional_y = stats_y + len(self.stats_list) * stat_line_height + int(10 * scale_h)

        # Используем эффективные значения с учетом бонусов от экипировки
        effective_max_health = player.get_effective_max_health()
        effective_max_mana = player.get_effective_max_mana()
        effective_max_stamina = player.get_effective_max_stamina()

        additional_info = [
            f"Здоровье: {player.health}/{effective_max_health}",
            f"Мана: {player.mana}/{effective_max_mana}",
            f"Выносливость: {player.stamina}/{effective_max_stamina}",
            f"Урон: {player.get_total_damage()}",
            f"Защита: {player.get_total_defense()}",
        ]

        for i, line in enumerate(additional_info):
            info_text = self.info_font.render(line, True, (180, 180, 200))
            self.screen.blit(info_text, (window_x + int(60 * scale_w), additional_y + i * int(25 * scale_h)))

        # Подсказки внизу
        hints_y = window_y + window_height - int(40 * scale_h)
        if player.stat_points > 0:
            hint_text = self.info_font.render(
                "W/S - выбор | Enter - добавить очко | C/ESC - закрыть",
                True,
                (180, 180, 180)
            )
        else:
            hint_text = self.info_font.render(
                "C/ESC - закрыть",
                True,
                (180, 180, 180)
            )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)


