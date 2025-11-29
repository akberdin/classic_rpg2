"""
Модуль для отрисовки HUD (интерфейса игрока).

Извлечено из engine.py для уменьшения сложности.
"""
import pygame
from game.ui import UIHelper
from game.constants import COLORS
from game.core.game_context import GameContext


class HUDRenderer:
    """Класс для отрисовки HUD игрока"""

    def __init__(self, game):
        """
        Инициализация рендерера HUD.

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.ctx = GameContext(game)

    @property
    def screen(self):
        return self.ctx.screen

    @property
    def font(self):
        return self.game.font

    @property
    def info_font(self):
        return self.game.info_font

    @property
    def ui_scaler(self):
        return self.game.ui_scaler

    @property
    def player(self):
        return self.ctx.player

    @property
    def sprite_manager(self):
        return self.game.sprite_manager

    def render(self):
        """Отрисовка пользовательского интерфейса"""
        # Панель внизу экрана (масштабируется под разрешение)
        ui_height = self.ui_scaler.scale_height(100)
        ui_y = self.ctx.window_height - ui_height

        # Фон панели
        pygame.draw.rect(
            self.screen,
            (32, 32, 32),
            (0, ui_y, self.ctx.window_width, ui_height)
        )

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (0, ui_y),
            (self.ctx.window_width, ui_y),
            2
        )

        # Информация об игроке
        info_x = 20
        info_y = ui_y + 10

        # Имя и уровень
        player_rank = self.player.get_rank()
        name_text = self.font.render(
            f"{self.player.name} | Ур: {self.player.level} ({player_rank})",
            True,
            COLORS['text']
        )
        self.screen.blit(name_text, (info_x, info_y))

        # Игровое время, погода и золото
        self._render_time_weather_gold(info_y)

        # Серия убийств (если активна)
        self._render_killstreak(info_y)

        # Прогресс-бары
        bar_y = info_y + 35
        self._render_status_bars(info_x, bar_y)

        # Опыт и информация о статах
        self._render_exp_and_stats(info_x, bar_y)

        # Подсказка о помощи
        help_hint = self.info_font.render(
            "F1 - Справка | C - Характеристики | I - Инвентарь | K - Книга умений",
            True,
            (180, 180, 180)
        )
        help_hint_x = self.ui_scaler.scale_width(800)
        self.screen.blit(help_hint, (info_x + 0, info_y + 55))

        # Панель умений (8 слотов)
        self._render_skill_panel()

    def _render_time_weather_gold(self, info_y):
        """Отрисовка времени, погоды и золота."""
        weather_str = ""
        if self.ctx.weather_system:
            weather_str = f" | {self.ctx.weather_system.current_weather.display_name}"

        time_gold_text = self.info_font.render(
            f"{self.ctx.game_time.get_time_string()}{weather_str} | Золото: {self.player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        time_gold_x = self.ctx.window_width - self.ui_scaler.scale_width(450)
        self.screen.blit(time_gold_text, (time_gold_x, info_y + 5))

    def _render_killstreak(self, info_y):
        """Отрисовка серии убийств."""
        if self.ctx.killstreak_system and self.ctx.killstreak_system.current_streak >= 3:
            streak_text = self.info_font.render(
                f"Серия: x{self.ctx.killstreak_system.current_streak}",
                True,
                (255, 100, 100)
            )
            time_gold_x = self.ctx.window_width - self.ui_scaler.scale_width(450)
            self.screen.blit(streak_text, (time_gold_x, info_y + 22))

    def _render_status_bars(self, info_x, bar_y):
        """Отрисовка полос здоровья, маны и выносливости."""
        bar_width = self.ui_scaler.scale_width(350)
        bar_height = 18
        bar_spacing = self.ui_scaler.scale_width(30)

        # Получаем эффективные максимумы с учетом экипировки
        effective_max_health = self.player.get_effective_max_health()
        effective_max_mana = self.player.get_effective_max_mana()
        effective_max_stamina = self.player.get_effective_max_stamina()

        # Вычисляем проценты
        health_percent = int((self.player.health / effective_max_health * 100) if effective_max_health > 0 else 0)
        mana_percent = int((self.player.mana / effective_max_mana * 100) if effective_max_mana > 0 else 0)
        stamina_percent = int((self.player.stamina / effective_max_stamina * 100) if effective_max_stamina > 0 else 0)

        # Полоса здоровья (красная)
        UIHelper.draw_progress_bar(
            self.screen,
            info_x, bar_y, bar_width, bar_height,
            self.player.health, effective_max_health,
            bg_color=(60, 20, 20),
            fill_color=(200, 50, 50),
            border_color=(255, 100, 100),
            text=f"HP: {self.player.health}/{effective_max_health} ({health_percent}%)",
            font=self.info_font
        )

        # Полоса маны (синяя)
        mana_x = info_x + bar_width + bar_spacing
        UIHelper.draw_progress_bar(
            self.screen,
            mana_x, bar_y, bar_width, bar_height,
            self.player.mana, effective_max_mana,
            bg_color=(20, 20, 60),
            fill_color=(50, 100, 200),
            border_color=(100, 150, 255),
            text=f"MP: {self.player.mana}/{effective_max_mana} ({mana_percent}%)",
            font=self.info_font
        )

        # Полоса выносливости (оранжевая)
        stamina_x = mana_x + bar_width + bar_spacing
        stamina_color = (200, 120, 50) if not self.player.is_resting else (150, 70, 30)
        stamina_status = " [ОТДЫХ]" if self.player.is_resting else ""
        UIHelper.draw_progress_bar(
            self.screen,
            stamina_x, bar_y, bar_width, bar_height,
            self.player.stamina, effective_max_stamina,
            bg_color=(60, 40, 20),
            fill_color=stamina_color,
            border_color=(255, 165, 0),
            text=f"Stamina: {self.player.stamina}/{effective_max_stamina} ({stamina_percent}%){stamina_status}",
            font=self.info_font
        )

    def _render_exp_and_stats(self, info_x, bar_y):
        """Отрисовка опыта и очков характеристик."""
        exp_text = self.info_font.render(
            f"Опыт: {self.player.experience}/{self.player.experience_to_next_level}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(exp_text, (info_x, bar_y + 30))

        # Нераспределенные очки характеристик (если есть)
        if self.player.stat_points > 0:
            stat_points_text = self.info_font.render(
                f"Свободных очков: {self.player.stat_points} [Нажми C]",
                True,
                (100, 255, 100)
            )
            stat_points_x = self.ui_scaler.scale_width(320)
            self.screen.blit(stat_points_text, (stat_points_x, bar_y + 30))

    def _render_skill_panel(self):
        """Отрисовка панели умений над панелью параметров."""
        slot_size = self.ui_scaler.scale_value(48)
        slot_spacing = self.ui_scaler.scale_value(8)
        panel_x = (self.ctx.window_width - (slot_size + slot_spacing) * 8) // 2

        ui_height = self.ui_scaler.scale_height(100)
        ui_y = self.ctx.window_height - ui_height
        panel_offset = self.ui_scaler.scale_value(15)
        panel_y = ui_y - slot_size - panel_offset

        for i in range(8):
            slot_x = panel_x + i * (slot_size + slot_spacing)
            skill = self.player.skill_manager.get_slot_skill(i)

            # Проверяем, доступно ли умение для использования
            is_usable = False
            if skill:
                can_use, _ = skill.can_use(self.player)
                is_usable = can_use

            # Фон и рамка слота
            bg_color, border_color = self._get_slot_colors(skill, is_usable)

            pygame.draw.rect(self.screen, bg_color, (slot_x, panel_y, slot_size, slot_size))
            pygame.draw.rect(self.screen, border_color, (slot_x, panel_y, slot_size, slot_size), 2)

            # Номер слота (клавиша)
            key_text = self.info_font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(key_text, (slot_x + 4, panel_y + 4))

            # Если есть умение, показываем его информацию
            if skill:
                skill_id = self.player.skill_manager.get_slot_skill_id(i)
                self._render_skill_slot(skill, skill_id, slot_x, panel_y, slot_size)

    def _get_slot_colors(self, skill, is_usable):
        """
        Получить цвета для слота умения.

        Returns:
            tuple: (bg_color, border_color)
        """
        if not skill:
            return (30, 30, 30), (100, 100, 100)

        # Цветовые схемы по категориям
        color_map = {
            'combat': ((80, 50, 50), (40, 25, 25)),
            'magic': ((50, 50, 80), (25, 25, 40)),
            'crafting': ((70, 70, 50), (35, 35, 25)),
        }

        category = skill.category.value
        bright, dark = color_map.get(category, ((60, 60, 60), (30, 30, 30)))

        bg_color = bright if is_usable else dark
        border_color = (200, 200, 100) if is_usable else (80, 80, 80)

        return bg_color, border_color

    def _render_skill_slot(self, skill, skill_id, slot_x, panel_y, slot_size):
        """Отрисовка содержимого слота умения."""
        # Иконка умения (спрайт или первая буква названия как fallback)
        icon_size = slot_size - 8  # Немного меньше слота для отступов
        icon_x = slot_x + 4
        icon_y = panel_y + 4

        # Пробуем отрисовать спрайт умения
        if skill_id and self.sprite_manager:
            self.sprite_manager.render_skill_icon(
                self.screen,
                skill_id,
                icon_x,
                icon_y,
                icon_size,
                fallback_text=skill.name[0]
            )
        else:
            # Fallback: первая буква названия
            icon_font = pygame.font.Font(None, 32)
            icon_text = icon_font.render(skill.name[0], True, (255, 255, 255))
            icon_rect = icon_text.get_rect()
            icon_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2 + 4)
            self.screen.blit(icon_text, icon_rect)

        # Ранг умения
        rank_text = self.info_font.render(f"R{skill.rank}", True, (255, 215, 0))
        self.screen.blit(rank_text, (slot_x + slot_size - 22, panel_y + slot_size - 18))

        # Шкала прогресса кулдауна (тонкая полоска внизу слота)
        cooldown_bar_height = 4
        cooldown_bar_y = panel_y + slot_size - cooldown_bar_height

        if skill.cooldown > 0:
            # Вычисляем прогресс восстановления (от 0 до 1)
            # Если current_cooldown = 0, то умение готово (прогресс = 1)
            # Если current_cooldown = cooldown, то умение только что использовано (прогресс = 0)
            if skill.current_cooldown > 0:
                cooldown_progress = 1.0 - (skill.current_cooldown / skill.cooldown)
            else:
                cooldown_progress = 1.0

            # Фон шкалы (темный)
            pygame.draw.rect(
                self.screen,
                (40, 40, 40),
                (slot_x, cooldown_bar_y, slot_size, cooldown_bar_height)
            )

            # Заполнение шкалы (зеленое - готово, красное - на кулдауне)
            filled_width = int(slot_size * cooldown_progress)
            if filled_width > 0:
                bar_color = (100, 255, 100) if cooldown_progress >= 1.0 else (255, 100, 100)
                pygame.draw.rect(
                    self.screen,
                    bar_color,
                    (slot_x, cooldown_bar_y, filled_width, cooldown_bar_height)
                )

        # Перезарядка (текст если есть)
        if skill.current_cooldown > 0:
            cooldown_text = self.info_font.render(
                str(skill.current_cooldown), True, (255, 100, 100)
            )
            cooldown_rect = cooldown_text.get_rect()
            cooldown_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2)
            self.screen.blit(cooldown_text, cooldown_rect)
