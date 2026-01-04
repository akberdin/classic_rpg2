"""
Окно характеристик персонажа.

Оптимизированный интерфейс с:
- Разбивкой на логические блоки
- Управлением мышью для распределения очков
- Полным отображением зависимостей параметров
"""
import pygame
from game.ui.windows.base import BaseWindow
from game.ui.base import UIHelper


class CharacterWindow(BaseWindow):
    """Окно характеристик персонажа"""

    BASE_WIDTH = 750
    BASE_HEIGHT = 750

    # Цвета
    SECTION_TITLE_COLOR = (255, 215, 0)
    STAT_NAME_COLOR = (220, 220, 220)
    STAT_VALUE_COLOR = (200, 200, 200)
    STAT_BONUS_COLOR = (150, 255, 150)
    DERIVED_COLOR = (180, 180, 200)
    FORMULA_COLOR = (120, 140, 180)
    BUTTON_COLOR = (70, 130, 70)
    BUTTON_HOVER_COLOR = (90, 160, 90)
    BUTTON_TEXT_COLOR = (255, 255, 255)
    SEPARATOR_COLOR = (80, 80, 100)

    def __init__(self, screen, font, info_font, scaler=None):
        super().__init__(screen, font, info_font, scaler)
        self.selected_stat_index = 0

        # Список характеристик для навигации
        self.stats_list = [
            ('strength', 'Сила', 'СИЛ'),
            ('dexterity', 'Ловкость', 'ЛОВ'),
            ('constitution', 'Телосложение', 'ТЕЛ'),
            ('spirit', 'Дух', 'ДУХ'),
            ('intelligence', 'Интеллект', 'ИНТ'),
            ('luck', 'Удача', 'УДЧ')
        ]

        # Описания влияния характеристик
        self.stat_effects = {
            'strength': ['Урон в ближнем бою', 'Грузоподъёмность', 'Макс. выносливость'],
            'dexterity': ['Шанс уворота', 'Скорость восст. выносливости'],
            'constitution': ['Макс. здоровье', 'Макс. выносливость', 'Скорость восст. здоровья'],
            'spirit': ['Макс. мана', 'Маг. защита', 'Скорость восст. маны'],
            'intelligence': ['Сила заклинаний', 'Эффективность умений'],
            'luck': ['Шанс крит. удара', 'Качество добычи']
        }

        # Хранение прямоугольников кнопок [+] для обработки мыши
        self.stat_buttons = {}  # {stat_key: pygame.Rect}
        self.hovered_button = None

        # Параметры последнего рендера (для проверки позиции мыши)
        self.last_window_rect = None

    def render(self, player):
        """
        Отрисовка окна характеристик

        Args:
            player: Объект игрока
        """
        # Очищаем кнопки перед новой отрисовкой
        self.stat_buttons = {}

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

        # Сохраняем параметры окна для обработки мыши
        self.last_window_rect = pygame.Rect(window_x, window_y, window_width, window_height)

        # Получаем данные игрока
        stats = player.get_stats()
        base_stats = player.get_base_stats()
        equip_bonuses = player.inventory.get_total_stats_bonus()

        # === БЛОК 1: ИНФОРМАЦИЯ О ПЕРСОНАЖЕ ===
        block1_y = window_y + int(50 * scale_h)
        self._render_player_info_block(player, window_x, block1_y, window_width, scale_w, scale_h)

        # Разделитель
        sep1_y = block1_y + int(85 * scale_h)
        self._draw_separator(window_x, sep1_y, window_width, scale_w)

        # === БЛОК 2: ХАРАКТЕРИСТИКИ ===
        block2_y = sep1_y + int(15 * scale_h)
        block2_height = self._render_stats_block(
            player, stats, base_stats, equip_bonuses,
            window_x, block2_y, window_width, scale_w, scale_h
        )

        # Разделитель
        sep2_y = block2_y + block2_height + int(10 * scale_h)
        self._draw_separator(window_x, sep2_y, window_width, scale_w)

        # === БЛОК 3: ПРОИЗВОДНЫЕ ПАРАМЕТРЫ ===
        block3_y = sep2_y + int(15 * scale_h)
        block3_height = self._render_derived_stats_block(
            player, stats, window_x, block3_y, window_width, scale_w, scale_h
        )

        # Разделитель
        sep3_y = block3_y + block3_height + int(10 * scale_h)
        self._draw_separator(window_x, sep3_y, window_width, scale_w)

        # === БЛОК 4: БОЕВЫЕ ПАРАМЕТРЫ ===
        block4_y = sep3_y + int(15 * scale_h)
        block4_height = self._render_combat_block(
            player, stats, window_x, block4_y, window_width, scale_w, scale_h
        )

        # Разделитель
        sep4_y = block4_y + block4_height + int(10 * scale_h)
        self._draw_separator(window_x, sep4_y, window_width, scale_w)

        # === БЛОК 5: ВОССТАНОВЛЕНИЕ ===
        block5_y = sep4_y + int(15 * scale_h)
        self._render_recovery_block(
            player, stats, window_x, block5_y, window_width, scale_w, scale_h
        )

        # === ПОДСКАЗКИ ===
        self._render_hints(player, window_x, window_y, window_width, window_height, scale_w, scale_h)

    def _draw_separator(self, window_x, y, window_width, scale_w):
        """Отрисовка разделительной линии"""
        pygame.draw.line(
            self.screen,
            self.SEPARATOR_COLOR,
            (window_x + int(20 * scale_w), y),
            (window_x + window_width - int(20 * scale_w), y),
            1
        )

    def _render_section_title(self, title, x, y, width, scale_w, scale_h, center=False):
        """Отрисовка заголовка секции"""
        text = self.info_font.render(title, True, self.SECTION_TITLE_COLOR)
        if center:
            text_rect = text.get_rect()
            text_rect.centerx = x + width // 2
            text_rect.y = y
            self.screen.blit(text, text_rect)
        else:
            self.screen.blit(text, (x + int(30 * scale_w), y))
        return int(25 * scale_h)

    def _render_player_info_block(self, player, x, y, width, scale_w, scale_h):
        """Отрисовка блока информации о персонаже"""
        # Левая колонка
        left_x = x + int(30 * scale_w)
        right_x = x + width // 2 + int(20 * scale_w)
        line_height = int(22 * scale_h)

        player_rank = player.get_rank()

        # Имя и ранг
        name_text = self.info_font.render(f"{player.name}", True, (255, 255, 255))
        self.screen.blit(name_text, (left_x, y))

        rank_text = self.info_font.render(f"[{player_rank}]", True, (200, 180, 100))
        self.screen.blit(rank_text, (left_x + name_text.get_width() + int(10 * scale_w), y))

        # Уровень
        level_text = self.info_font.render(f"Уровень: {player.level}", True, self.STAT_VALUE_COLOR)
        self.screen.blit(level_text, (right_x, y))

        # Опыт с прогресс-баром
        exp_y = y + line_height
        exp_label = self.info_font.render("Опыт:", True, self.STAT_VALUE_COLOR)
        self.screen.blit(exp_label, (left_x, exp_y))

        # Прогресс-бар опыта
        bar_x = left_x + int(60 * scale_w)
        bar_width = int(200 * scale_w)
        bar_height = int(16 * scale_h)
        UIHelper.draw_progress_bar(
            self.screen, bar_x, exp_y + int(2 * scale_h),
            bar_width, bar_height,
            player.experience, player.experience_to_next_level,
            bg_color=(40, 40, 50), fill_color=(100, 150, 200),
            border_color=(120, 120, 150),
            text=f"{player.experience}/{player.experience_to_next_level}",
            font=self.info_font
        )

        # Золото
        gold_text = self.info_font.render(f"Золото: {player.inventory.gold}", True, (255, 215, 0))
        self.screen.blit(gold_text, (right_x, exp_y))

        # Свободные очки характеристик
        if player.stat_points > 0:
            points_y = exp_y + line_height
            points_text = self.font.render(
                f"Свободных очков: {player.stat_points}",
                True,
                (100, 255, 100)
            )
            points_rect = points_text.get_rect()
            points_rect.centerx = x + width // 2
            points_rect.y = points_y
            self.screen.blit(points_text, points_rect)

    def _render_stats_block(self, player, stats, base_stats, equip_bonuses, x, y, width, scale_w, scale_h):
        """Отрисовка блока характеристик"""
        title_height = self._render_section_title("ХАРАКТЕРИСТИКИ", x, y, width, scale_w, scale_h)
        current_y = y + title_height

        # Расположение в две колонки
        left_x = x + int(30 * scale_w)
        right_x = x + width // 2 + int(10 * scale_w)
        stat_height = int(50 * scale_h)

        # Проверяем позицию мыши для hover эффекта
        mouse_pos = pygame.mouse.get_pos()

        for i, (stat_key, stat_name, stat_short) in enumerate(self.stats_list):
            # Определяем позицию (левая или правая колонка)
            col_x = left_x if i % 2 == 0 else right_x
            stat_y = current_y + (i // 2) * stat_height

            # Значения
            base_value = base_stats[stat_key]
            bonus = equip_bonuses.get(stat_key, 0)
            total_value = stats[stat_key]

            # Подсветка выбранной характеристики (для клавиатуры)
            is_selected = (i == self.selected_stat_index)
            stat_rect = pygame.Rect(
                col_x - int(5 * scale_w),
                stat_y - int(3 * scale_h),
                int(340 * scale_w),
                stat_height - int(5 * scale_h)
            )

            if is_selected:
                pygame.draw.rect(self.screen, (60, 60, 80), stat_rect)
                pygame.draw.rect(self.screen, (100, 120, 160), stat_rect, 1)

            # Название характеристики
            name_text = self.info_font.render(f"{stat_name}:", True, self.STAT_NAME_COLOR)
            self.screen.blit(name_text, (col_x, stat_y))

            # Значение
            value_x = col_x + int(130 * scale_w)
            if bonus > 0:
                value_str = f"{base_value} (+{bonus}) = {total_value}"
                value_color = self.STAT_BONUS_COLOR
            elif bonus < 0:
                value_str = f"{base_value} ({bonus}) = {total_value}"
                value_color = (255, 150, 150)
            else:
                value_str = str(total_value)
                value_color = self.STAT_VALUE_COLOR

            value_text = self.info_font.render(value_str, True, value_color)
            self.screen.blit(value_text, (value_x, stat_y))

            # Кнопка [+] для добавления очка
            if player.stat_points > 0:
                btn_x = col_x + int(280 * scale_w)
                btn_y = stat_y - int(2 * scale_h)
                btn_width = int(28 * scale_w)
                btn_height = int(24 * scale_h)
                btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)

                # Сохраняем rect кнопки
                self.stat_buttons[stat_key] = btn_rect

                # Проверяем hover
                is_hovered = btn_rect.collidepoint(mouse_pos)
                if is_hovered:
                    self.hovered_button = stat_key

                btn_color = self.BUTTON_HOVER_COLOR if is_hovered else self.BUTTON_COLOR
                pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=3)
                pygame.draw.rect(self.screen, (100, 180, 100), btn_rect, 1, border_radius=3)

                plus_text = self.info_font.render("+", True, self.BUTTON_TEXT_COLOR)
                plus_rect = plus_text.get_rect(center=btn_rect.center)
                self.screen.blit(plus_text, plus_rect)

            # Эффекты характеристики (маленький текст под названием)
            effects = self.stat_effects.get(stat_key, [])
            if effects:
                effects_str = ", ".join(effects[:2])
                if len(effects_str) > 35:
                    effects_str = effects_str[:32] + "..."
                effects_text = self.info_font.render(effects_str, True, self.FORMULA_COLOR)
                self.screen.blit(effects_text, (col_x, stat_y + int(18 * scale_h)))

        # Возвращаем высоту блока
        return title_height + ((len(self.stats_list) + 1) // 2) * stat_height

    def _render_derived_stats_block(self, player, stats, x, y, width, scale_w, scale_h):
        """Отрисовка блока производных параметров"""
        title_height = self._render_section_title("РЕСУРСЫ", x, y, width, scale_w, scale_h)
        current_y = y + title_height

        # Получаем эффективные значения
        eff_max_health = player.get_effective_max_health()
        eff_max_mana = player.get_effective_max_mana()
        eff_max_stamina = player.get_effective_max_stamina()
        eff_max_weight = player.get_effective_max_weight()

        left_x = x + int(30 * scale_w)
        right_x = x + width // 2 + int(10 * scale_w)
        line_height = int(40 * scale_h)

        # Здоровье с прогресс-баром
        self._render_resource_bar(
            "Здоровье", player.health, eff_max_health,
            (180, 60, 60), f"ТЕЛ × 20",
            left_x, current_y, scale_w, scale_h
        )

        # Мана с прогресс-баром
        self._render_resource_bar(
            "Мана", player.mana, eff_max_mana,
            (60, 100, 180), f"ДУХ × 10",
            right_x, current_y, scale_w, scale_h
        )

        current_y += line_height

        # Выносливость
        self._render_resource_bar(
            "Выносливость", player.stamina, eff_max_stamina,
            (180, 150, 60), f"(СИЛ + ТЕЛ) × 10",
            left_x, current_y, scale_w, scale_h
        )

        # Грузоподъёмность
        current_weight = player.inventory.current_weight
        self._render_resource_bar(
            "Вес", current_weight, eff_max_weight,
            (120, 100, 80), f"30 + СИЛ × 10",
            right_x, current_y, scale_w, scale_h
        )

        return title_height + 2 * line_height

    def _render_resource_bar(self, name, current, maximum, color, formula, x, y, scale_w, scale_h):
        """Отрисовка ресурса с прогресс-баром"""
        # Название
        name_text = self.info_font.render(f"{name}:", True, self.STAT_NAME_COLOR)
        self.screen.blit(name_text, (x, y))

        # Прогресс-бар
        bar_x = x
        bar_y = y + int(18 * scale_h)
        bar_width = int(150 * scale_w)
        bar_height = int(14 * scale_h)

        UIHelper.draw_progress_bar(
            self.screen, bar_x, bar_y,
            bar_width, bar_height,
            current, maximum,
            bg_color=(30, 30, 40), fill_color=color,
            border_color=(80, 80, 100),
            text=f"{current}/{maximum}",
            font=self.info_font
        )

        # Формула расчёта
        formula_x = x + bar_width + int(10 * scale_w)
        formula_text = self.info_font.render(formula, True, self.FORMULA_COLOR)
        self.screen.blit(formula_text, (formula_x, bar_y))

    def _render_combat_block(self, player, stats, x, y, width, scale_w, scale_h):
        """Отрисовка блока боевых параметров"""
        title_height = self._render_section_title("БОЕВЫЕ ПАРАМЕТРЫ", x, y, width, scale_w, scale_h)
        current_y = y + title_height

        left_x = x + int(30 * scale_w)
        right_x = x + width // 2 + int(10 * scale_w)
        line_height = int(24 * scale_h)

        # Урон
        total_damage = player.get_total_damage()
        damage_text = self.info_font.render(f"Урон: {total_damage}", True, (255, 150, 100))
        self.screen.blit(damage_text, (left_x, current_y))

        formula = self.info_font.render("(СИЛ + оружие)", True, self.FORMULA_COLOR)
        self.screen.blit(formula, (left_x + int(100 * scale_w), current_y))

        # Защита
        total_defense = player.get_total_defense()
        defense_text = self.info_font.render(f"Защита: {total_defense}", True, (100, 150, 255))
        self.screen.blit(defense_text, (right_x, current_y))

        formula2 = self.info_font.render("(ТЕЛ + доспехи)", True, self.FORMULA_COLOR)
        self.screen.blit(formula2, (right_x + int(110 * scale_w), current_y))

        current_y += line_height

        # Маг. защита
        magic_def = player.get_magic_defense()
        magic_text = self.info_font.render(f"Маг. защита: {magic_def}", True, (150, 100, 200))
        self.screen.blit(magic_text, (left_x, current_y))

        formula3 = self.info_font.render("(ДУХ × 0.8)", True, self.FORMULA_COLOR)
        self.screen.blit(formula3, (left_x + int(140 * scale_w), current_y))

        current_y += line_height

        # Шанс уворота
        dodge_chance = player.calculate_dodge_chance()
        dodge_text = self.info_font.render(f"Шанс уворота: {dodge_chance:.1f}%", True, (100, 200, 150))
        self.screen.blit(dodge_text, (left_x, current_y))

        formula4 = self.info_font.render("(от ЛОВ)", True, self.FORMULA_COLOR)
        self.screen.blit(formula4, (left_x + int(180 * scale_w), current_y))

        # Шанс крита
        crit_chance = player.calculate_crit_chance()
        crit_text = self.info_font.render(f"Шанс крита: {crit_chance:.1f}%", True, (255, 200, 100))
        self.screen.blit(crit_text, (right_x, current_y))

        formula5 = self.info_font.render("(от УДЧ)", True, self.FORMULA_COLOR)
        self.screen.blit(formula5, (right_x + int(160 * scale_w), current_y))

        return title_height + 3 * line_height

    def _render_recovery_block(self, player, stats, x, y, width, scale_w, scale_h):
        """Отрисовка блока восстановления"""
        title_height = self._render_section_title("ВОССТАНОВЛЕНИЕ (за ход отдыха)", x, y, width, scale_w, scale_h)
        current_y = y + title_height

        left_x = x + int(30 * scale_w)
        line_height = int(22 * scale_h)

        # Получаем эффективные характеристики
        eff_max_health = player.get_effective_max_health()
        eff_max_mana = player.get_effective_max_mana()
        eff_max_stamina = player.get_effective_max_stamina()
        eff_constitution = stats['constitution']
        eff_spirit = stats['spirit']
        eff_dexterity = stats['dexterity']

        # Вычисляем восстановление
        health_recovery = max(1, int(eff_max_health * eff_constitution * 0.005))
        mana_recovery = max(1, int(eff_max_mana * eff_spirit * 0.005))
        stamina_recovery = max(1, int(eff_max_stamina * eff_dexterity * 0.005))

        # Здоровье
        hp_text = self.info_font.render(f"Здоровье: +{health_recovery}", True, (150, 255, 150))
        self.screen.blit(hp_text, (left_x, current_y))

        hp_formula = self.info_font.render(f"(макс.HP × ТЕЛ × 0.5%)", True, self.FORMULA_COLOR)
        self.screen.blit(hp_formula, (left_x + int(150 * scale_w), current_y))

        current_y += line_height

        # Мана
        mp_text = self.info_font.render(f"Мана: +{mana_recovery}", True, (150, 150, 255))
        self.screen.blit(mp_text, (left_x, current_y))

        mp_formula = self.info_font.render(f"(макс.MP × ДУХ × 0.5%)", True, self.FORMULA_COLOR)
        self.screen.blit(mp_formula, (left_x + int(150 * scale_w), current_y))

        current_y += line_height

        # Выносливость
        st_text = self.info_font.render(f"Выносливость: +{stamina_recovery}", True, (255, 220, 150))
        self.screen.blit(st_text, (left_x, current_y))

        st_formula = self.info_font.render(f"(макс.ST × ЛОВ × 0.5%)", True, self.FORMULA_COLOR)
        self.screen.blit(st_formula, (left_x + int(180 * scale_w), current_y))

    def _render_hints(self, player, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка подсказок внизу окна"""
        hints_y = window_y + window_height - int(35 * scale_h)

        if player.stat_points > 0:
            hint_text = self.info_font.render(
                "W/S - выбор | Enter/ЛКМ - добавить очко | C/ESC - закрыть",
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

    def get_stat_at_mouse(self, mouse_x, mouse_y):
        """
        Получить характеристику под курсором мыши

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            str или None: Ключ характеристики или None
        """
        for stat_key, btn_rect in self.stat_buttons.items():
            if btn_rect.collidepoint(mouse_x, mouse_y):
                return stat_key
        return None

    def handle_mouse_click(self, mouse_x, mouse_y, player):
        """
        Обработка клика мыши

        Args:
            mouse_x: X координата клика
            mouse_y: Y координата клика
            player: Объект игрока

        Returns:
            tuple: (success: bool, message: str или None)
        """
        if player.stat_points <= 0:
            return False, None

        stat_key = self.get_stat_at_mouse(mouse_x, mouse_y)
        if stat_key:
            # Находим название характеристики
            stat_name = None
            for key, name, short in self.stats_list:
                if key == stat_key:
                    stat_name = name
                    break

            if player.add_stat_point(stat_key):
                return True, f"{stat_name} увеличена! Осталось очков: {player.stat_points}"

        return False, None

    def get_stat_index_at_mouse(self, mouse_x, mouse_y):
        """
        Получить индекс характеристики под курсором для выделения

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            int или None: Индекс характеристики или None
        """
        for i, (stat_key, _, _) in enumerate(self.stats_list):
            if stat_key in self.stat_buttons:
                btn_rect = self.stat_buttons[stat_key]
                # Расширяем область проверки на всю строку характеристики
                extended_rect = pygame.Rect(
                    btn_rect.x - 300,
                    btn_rect.y - 5,
                    350,
                    btn_rect.height + 30
                )
                if extended_rect.collidepoint(mouse_x, mouse_y):
                    return i
        return None
