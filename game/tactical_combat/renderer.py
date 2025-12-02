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

        # Используем переданный шрифт для всех элементов
        # Это избегает проблем с созданием новых шрифтов pygame
        self.info_font = font
        self.small_font = font

        # Цвета из конфига
        ui_config = self.combat.config.get('ui', {})
        self.grid_color = tuple(ui_config.get('grid_color', [100, 100, 120]))
        self.player_color = tuple(ui_config.get('player_unit_color', [100, 200, 100]))
        self.enemy_color = tuple(ui_config.get('enemy_unit_color', [200, 100, 100]))

        # Для отслеживания кнопок умений (позиции для клика)
        self.skill_buttons = []  # Список прямоугольников кнопок умений
        self.hovered_skill_slot = None  # Слот умения под курсором

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

        # Ширина боковой панели
        side_panel_width = 320

        # Поле боя смещено влево, чтобы освободить место для боковой панели
        field_x = 20
        field_y = 100

        # Отрисовываем заголовок
        self._render_header(field_x + field_width // 2, 50)

        # Отрисовываем поле боя
        self._render_battlefield(field_x, field_y)

        # Отрисовываем юнитов
        self._render_units(field_x, field_y)

        # Отрисовываем боковую панель с характеристиками NPC свиты
        side_panel_x = field_x + field_width + 20
        self._render_entourage_panel(side_panel_x, field_y, side_panel_width, field_height)

        # Отрисовываем UI панели (под полем боя)
        ui_y = field_y + field_height + 20
        self._render_ui_panel(field_x, ui_y, field_width)

        # Отрисовываем лог
        log_y = ui_y + 130  # Высота UI панели (120) + 10
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
        self._render_unit(self.combat.player_unit, field_x, field_y, self.player_color, "P", is_target=False)

        # Отрисовка всех врагов (с подсветкой если выбран как цель)
        from game.tactical_combat.ui_handler import TacticalCombatUIHandler
        for i, enemy_unit in enumerate(self.combat.enemy_units):
            # Пропускаем мертвых врагов
            if not enemy_unit.character.is_alive:
                continue

            # Проверяем, выбран ли этот враг как цель
            is_target = (hasattr(self.combat, '_ui_handler') and
                         self.combat._ui_handler.selected_target_unit == enemy_unit)

            # Метка врага: E для основного, E1, E2... для свиты
            label = "E" if i == 0 else f"E{i}"

            self._render_unit(enemy_unit, field_x, field_y, self.enemy_color, label, is_target=is_target)

    def _render_unit(self, unit, field_x, field_y, color, label, is_target=False):
        """
        Отрисовка юнита

        Args:
            unit: Юнит для отрисовки
            field_x, field_y: Координаты поля
            color: Цвет юнита
            label: Метка (P для игрока, E для врага)
            is_target: True если юнит выбран как цель
        """
        cell_x = field_x + unit.x * self.combat.cell_size
        cell_y = field_y + unit.y * self.combat.cell_size

        # Фон клетки юнита (подсветка)
        bg_color = color
        if is_target:
            # Яркая подсветка для выбранной цели
            bg_color = (255, 215, 0)  # Золотой цвет

        pygame.draw.rect(self.screen, bg_color,
                        (cell_x + 2, cell_y + 2,
                         self.combat.cell_size - 4, self.combat.cell_size - 4))

        # Рамка (более толстая для выбранной цели)
        border_width = 4 if is_target else 2
        border_color = (255, 215, 0) if is_target else (255, 255, 255)
        pygame.draw.rect(self.screen, border_color,
                        (cell_x + 2, cell_y + 2,
                         self.combat.cell_size - 4, self.combat.cell_size - 4), border_width)

        # Отрисовка спрайта персонажа
        character = unit.character
        sprite_displayed = False

        # Пытаемся получить спрайт через sprite_manager
        if self.combat.sprite_manager:
            # Для игрока используем спрайт "player"
            if unit == self.combat.player_unit:
                sprite = self.combat.sprite_manager.get_sprite('player', 'npc')
                if sprite:
                    sprite_x = cell_x + (self.combat.cell_size - sprite.get_width()) // 2
                    sprite_y = cell_y + (self.combat.cell_size - sprite.get_height()) // 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                    sprite_displayed = True
            # Для NPC используем их npc_type
            elif hasattr(character, 'npc_type'):
                sprite = self.combat.sprite_manager.get_npc_sprite_with_rank(
                    character.npc_type,
                    character.level
                )
                if sprite:
                    sprite_x = cell_x + (self.combat.cell_size - sprite.get_width()) // 2
                    sprite_y = cell_y + (self.combat.cell_size - sprite.get_height()) // 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                    sprite_displayed = True

        # Fallback: метка, если спрайт недоступен
        if not sprite_displayed:
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
        hp_ratio = min(1.0, character.health / max_hp) if max_hp > 0 else 0

        # Фон
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        # Заполнение
        if hp_ratio > 0:
            hp_color = (100, 255, 100) if hp_ratio > 0.5 else (255, 165, 0) if hp_ratio > 0.25 else (255, 100, 100)
            pygame.draw.rect(self.screen, hp_color,
                           (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        # Рамка
        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

        # Mana bar (только для персонажей с маной, но не для животных)
        # Животные не используют магию, поэтому не показываем полосу маны
        from game.constants import NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER
        is_animal = hasattr(character, 'npc_type') and character.npc_type in [NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER]

        if hasattr(character, 'mana') and not is_animal:
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
            stamina_ratio = min(1.0, character.stamina / max_stamina) if max_stamina > 0 else 0

            pygame.draw.rect(self.screen, (50, 40, 20), (bar_x, bar_y, bar_width, bar_height))
            if stamina_ratio > 0:
                pygame.draw.rect(self.screen, (255, 220, 100),
                               (bar_x, bar_y, int(bar_width * stamina_ratio), bar_height))
            pygame.draw.rect(self.screen, (200, 180, 100), (bar_x, bar_y, bar_width, bar_height), 1)

    def _render_entourage_panel(self, x, y, width, max_height):
        """
        Отрисовка боковой панели с характеристиками NPC свиты

        Args:
            x, y: Позиция панели
            width: Ширина панели
            max_height: Максимальная высота панели
        """
        # Фон панели
        pygame.draw.rect(self.screen, (35, 35, 45), (x, y, width, max_height))
        pygame.draw.rect(self.screen, (100, 100, 150), (x, y, width, max_height), 3)

        # Заголовок панели
        title = self.info_font.render("Противники", True, (255, 215, 0))
        self.screen.blit(title, (x + 10, y + 10))

        # Линия под заголовком
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (x + 10, y + 35),
            (x + width - 10, y + 35),
            2
        )

        # Отрисовка информации о каждом NPC
        current_y = y + 45
        spacing = 10
        max_units_to_show = 5  # Максимум NPC для отображения

        # Показываем только живых врагов
        alive_enemies = [unit for unit in self.combat.enemy_units if unit.character.is_alive]

        # Ограничиваем количество отображаемых врагов
        enemies_to_show = alive_enemies[:max_units_to_show]

        for i, enemy_unit in enumerate(enemies_to_show):
            # Высота одного блока информации о NPC
            unit_info_height = 180

            # Проверяем, влезает ли еще один блок
            if current_y + unit_info_height > y + max_height - 10:
                # Если не влезает, показываем сообщение о том, что есть еще враги
                remaining = len(alive_enemies) - i
                if remaining > 0:
                    more_text = self.small_font.render(
                        f"... и еще {remaining} противников",
                        True,
                        (180, 180, 200)
                    )
                    self.screen.blit(more_text, (x + 10, current_y))
                break

            self._render_unit_info_compact(enemy_unit, x + 10, current_y, width - 20, i)
            current_y += unit_info_height + spacing

    def _render_unit_info_compact(self, unit, x, y, width, index):
        """
        Отрисовка компактной информации о юните

        Args:
            unit: Юнит для отрисовки
            x, y: Позиция блока
            width: Ширина блока
            index: Индекс врага (0 для основного, 1+ для свиты)
        """
        character = unit.character

        # Фон блока
        pygame.draw.rect(self.screen, (45, 45, 60), (x, y, width, 175))
        pygame.draw.rect(self.screen, (200, 100, 100), (x, y, width, 175), 2)

        # Спрайт NPC (слева)
        sprite_size = 48
        sprite_x = x + 5
        sprite_y = y + 5

        # Отрисовываем спрайт
        if self.combat.sprite_manager and hasattr(character, 'npc_type'):
            sprite = self.combat.sprite_manager.get_npc_sprite_with_rank(
                character.npc_type,
                character.level
            )
            if sprite:
                # Масштабируем спрайт до нужного размера
                scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))
                self.screen.blit(scaled_sprite, (sprite_x, sprite_y))
            else:
                # Fallback: рисуем рамку
                pygame.draw.rect(self.screen, (80, 80, 100), (sprite_x, sprite_y, sprite_size, sprite_size), 2)
        else:
            # Fallback: рисуем рамку
            pygame.draw.rect(self.screen, (80, 80, 100), (sprite_x, sprite_y, sprite_size, sprite_size), 2)

        # Имя и уровень (справа от спрайта)
        name_x = sprite_x + sprite_size + 10
        name_y = y + 5

        # Метка врага
        label = "Гл." if index == 0 else f"С{index}"
        label_text = self.small_font.render(label, True, (255, 100, 100))
        self.screen.blit(label_text, (name_x, name_y))

        # Имя
        name_text = self.info_font.render(character.name, True, (255, 255, 255))
        # Обрезаем имя если оно слишком длинное
        max_name_width = width - sprite_size - 20
        if name_text.get_width() > max_name_width:
            # Обрезаем имя
            short_name = character.name[:15] + "..."
            name_text = self.info_font.render(short_name, True, (255, 255, 255))
        self.screen.blit(name_text, (name_x, name_y + 18))

        # Уровень
        rank = character.get_rank() if hasattr(character, 'get_rank') else ""
        level_text = self.small_font.render(f"Ур. {character.level} ({rank})", True, (255, 215, 0))
        self.screen.blit(level_text, (name_x, name_y + 36))

        # Прогресс-бары и статы (под спрайтом и именем)
        bars_y = y + sprite_size + 15
        bar_width = width - 10
        bar_height = 8

        # HP
        max_hp = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        hp_ratio = min(1.0, character.health / max_hp) if max_hp > 0 else 0
        hp_percent = int(hp_ratio * 100)

        hp_label = self.small_font.render(f"HP: {character.health}/{max_hp} ({hp_percent}%)", True, (255, 100, 100))
        self.screen.blit(hp_label, (x + 5, bars_y))

        bars_y += 18
        pygame.draw.rect(self.screen, (60, 60, 60), (x + 5, bars_y, bar_width, bar_height))
        if hp_ratio > 0:
            hp_color = (100, 255, 100) if hp_ratio > 0.5 else (255, 165, 0) if hp_ratio > 0.25 else (255, 100, 100)
            pygame.draw.rect(self.screen, hp_color, (x + 5, bars_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (x + 5, bars_y, bar_width, bar_height), 1)

        # Mana (только для персонажей с маной, но не для животных)
        from game.constants import NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER
        is_animal = hasattr(character, 'npc_type') and character.npc_type in [NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER]

        if hasattr(character, 'mana') and not is_animal:
            bars_y += bar_height + 8
            max_mana = character.get_effective_max_mana() if hasattr(character, 'get_effective_max_mana') else character.max_mana
            mana_ratio = min(1.0, character.mana / max_mana) if max_mana > 0 else 0
            mana_percent = int(mana_ratio * 100)

            mana_label = self.small_font.render(f"Мана: {character.mana}/{max_mana} ({mana_percent}%)", True, (100, 150, 255))
            self.screen.blit(mana_label, (x + 5, bars_y))

            bars_y += 18
            pygame.draw.rect(self.screen, (30, 30, 50), (x + 5, bars_y, bar_width, bar_height))
            if mana_ratio > 0:
                pygame.draw.rect(self.screen, (100, 150, 255), (x + 5, bars_y, int(bar_width * mana_ratio), bar_height))
            pygame.draw.rect(self.screen, (150, 150, 200), (x + 5, bars_y, bar_width, bar_height), 1)

        # Stamina
        if hasattr(character, 'stamina'):
            bars_y += bar_height + 8
            max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina
            stamina_ratio = min(1.0, character.stamina / max_stamina) if max_stamina > 0 else 0
            stamina_percent = int(stamina_ratio * 100)

            stamina_label = self.small_font.render(f"Вын.: {character.stamina}/{max_stamina} ({stamina_percent}%)", True, (255, 220, 100))
            self.screen.blit(stamina_label, (x + 5, bars_y))

            bars_y += 18
            pygame.draw.rect(self.screen, (50, 40, 20), (x + 5, bars_y, bar_width, bar_height))
            if stamina_ratio > 0:
                pygame.draw.rect(self.screen, (255, 220, 100), (x + 5, bars_y, int(bar_width * stamina_ratio), bar_height))
            pygame.draw.rect(self.screen, (200, 180, 100), (x + 5, bars_y, bar_width, bar_height), 1)

        # Статы (компактно в две колонки)
        bars_y += bar_height + 12
        stats = [
            f"Урон: {character.get_total_damage()}",
            f"Защ.: {character.get_total_defense()}",
            f"М.защ.: {character.get_magic_defense()}",
        ]

        for i, stat in enumerate(stats):
            stat_text = self.small_font.render(stat, True, (200, 200, 220))
            stat_x = x + 5 + (i % 2) * (width // 2)
            stat_y = bars_y + (i // 2) * 16
            self.screen.blit(stat_text, (stat_x, stat_y))

    def _render_ui_panel(self, x, y, width):
        """Отрисовка панели UI с панелью умений и параметрами игрока"""
        panel_height = 120

        # Фон панели
        pygame.draw.rect(self.screen, (35, 35, 45), (x, y, width, panel_height))
        pygame.draw.rect(self.screen, (100, 100, 150), (x, y, width, panel_height), 2)

        if self.combat.current_turn == "player":
            # Заголовок умений
            title = self.info_font.render("Умения:", True, (200, 200, 220))
            self.screen.blit(title, (x + 10, y + 10))

            # Отрисовка панели умений (слева)
            skill_panel_width = 480  # 8 слотов * (48 + 8)
            self._render_skill_panel(x + 10, y + 35, skill_panel_width)

            # Параметры игрока (справа от панели умений)
            self._render_player_stats(x + skill_panel_width + 30, y + 10, width - skill_panel_width - 40)

        else:
            # Ход противника
            title = self.info_font.render("Действия:", True, (200, 200, 220))
            self.screen.blit(title, (x + 10, y + 10))
            wait_text = self.info_font.render("Ход противника...", True, (255, 150, 150))
            self.screen.blit(wait_text, (x + 20, y + 50))

    def _render_player_stats(self, x, y, width):
        """
        Отрисовка параметров игрока

        Args:
            x, y: Позиция блока
            width: Ширина блока
        """
        player = self.combat.player

        # Заголовок
        title = self.info_font.render("Параметры:", True, (255, 215, 0))
        self.screen.blit(title, (x, y))

        # Получаем эффективные характеристики с учетом экипировки
        effective_str = player.get_effective_strength() if hasattr(player, 'get_effective_strength') else player.strength
        effective_dex = player.get_effective_dexterity() if hasattr(player, 'get_effective_dexterity') else player.dexterity
        effective_luck = player.get_effective_luck() if hasattr(player, 'get_effective_luck') else player.luck

        damage = player.get_total_damage()
        defense = player.get_total_defense()
        crit_chance = player.calculate_crit_chance()
        dodge_chance = player.calculate_dodge_chance()

        stats_y = y + 25

        # Левая колонка
        left_stats = [
            f"Урон: {damage}",
            f"Защита: {defense}",
            f"Сила: {effective_str}",
            f"Ловкость: {effective_dex}"
        ]

        for i, stat in enumerate(left_stats):
            stat_text = self.small_font.render(stat, True, (200, 200, 220))
            self.screen.blit(stat_text, (x, stats_y + i * 18))

        # Правая колонка (если есть место)
        if width > 300:
            stats_right_x = x + 150

            right_stats = [
                f"Крит: {crit_chance:.1f}%",
                f"Уворот: {dodge_chance:.1f}%",
                f"Удача: {effective_luck}",
                f"Уровень: {player.level}"
            ]

            for i, stat in enumerate(right_stats):
                stat_text = self.small_font.render(stat, True, (200, 200, 220))
                self.screen.blit(stat_text, (stats_right_x, stats_y + i * 18))
        else:
            # Если мало места - все в одну колонку
            right_stats = [
                f"Крит: {crit_chance:.1f}%",
                f"Уворот: {dodge_chance:.1f}%",
                f"Удача: {effective_luck}",
                f"Уровень: {player.level}"
            ]

            for i, stat in enumerate(right_stats):
                stat_text = self.small_font.render(stat, True, (200, 200, 220))
                self.screen.blit(stat_text, (x, stats_y + (i + 4) * 18))

    def _render_skill_panel(self, x, y, width):
        """Отрисовка панели умений"""
        # Очищаем список кнопок перед отрисовкой
        self.skill_buttons = []

        slot_size = 48
        slot_spacing = 8
        slots_per_row = 8

        # Получаем позицию мыши для подсветки
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill_slot = None

        for i in range(8):
            slot_x = x + i * (slot_size + slot_spacing)
            slot_y = y

            skill = self.combat.player.skill_manager.get_slot_skill(i)

            # Проверяем, доступно ли умение для использования в бою
            is_usable = False
            if skill:
                from game.skills import SkillCategory
                can_use, reason = skill.can_use(self.combat.player)
                combat_categories = [
                    SkillCategory.COMBAT, SkillCategory.MAGIC,
                    SkillCategory.SHADOW, SkillCategory.WARRIOR,
                    SkillCategory.HUNTER, SkillCategory.MAGE, SkillCategory.GENERAL
                ]
                is_usable = can_use and skill.category in combat_categories

            # Фон слота
            if skill:
                if is_usable:
                    # Яркие цвета для доступных умений
                    if skill.category.value == 'combat':
                        bg_color = (80, 50, 50)
                    elif skill.category.value == 'magic':
                        bg_color = (50, 50, 80)
                    else:
                        bg_color = (40, 40, 40)
                else:
                    # Темные цвета для недоступных умений
                    bg_color = (30, 30, 30)
            else:
                bg_color = (30, 30, 30)

            # Создаем rect для кнопки
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            self.skill_buttons.append((slot_rect, i, skill, is_usable))

            # Проверяем наведение мыши
            if slot_rect.collidepoint(mouse_pos) and is_usable:
                self.hovered_skill_slot = i
                # Подсветка при наведении
                bg_color = tuple(min(255, c + 30) for c in bg_color)

            pygame.draw.rect(self.screen, bg_color, slot_rect)

            # Рамка слота
            if skill and is_usable:
                border_color = (200, 200, 100)  # Яркая желтая рамка для доступных
            elif skill:
                border_color = (80, 80, 80)  # Темная рамка для недоступных
            else:
                border_color = (100, 100, 100)

            pygame.draw.rect(self.screen, border_color, slot_rect, 2)

            # Номер слота
            key_text = self.info_font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(key_text, (slot_x + 4, slot_y + 4))

            # Если есть умение, показываем его
            if skill:
                # Иконка умения (спрайт или первая буква названия как fallback)
                skill_id = self.combat.player.skill_manager.get_slot_skill_id(i)
                icon_size = slot_size - 8
                icon_x = slot_x + 4
                icon_y = slot_y + 4

                # Пробуем отрисовать спрайт умения
                if skill_id and self.combat.sprite_manager:
                    self.combat.sprite_manager.render_skill_icon(
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
                    icon_rect.center = (slot_x + slot_size // 2, slot_y + slot_size // 2 + 4)
                    self.screen.blit(icon_text, icon_rect)

                # Перезарядка (если есть)
                if skill.current_cooldown > 0:
                    cooldown_text = self.info_font.render(str(skill.current_cooldown), True, (255, 100, 100))
                    cooldown_rect = cooldown_text.get_rect()
                    cooldown_rect.center = (slot_x + slot_size // 2, slot_y + slot_size // 2)
                    self.screen.blit(cooldown_text, cooldown_rect)

    def _render_combat_log(self, x, y, width):
        """Отрисовка лога боя с цветовым выделением"""
        log_height = 190

        # Фон лога
        pygame.draw.rect(self.screen, (25, 25, 35), (x, y, width, log_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (x, y, width, log_height), 2)

        # Заголовок
        log_title = self.info_font.render("Журнал боя", True, (150, 200, 255))
        self.screen.blit(log_title, (x + 10, y + 10))

        # Логи с уменьшенным шрифтом
        log_y = y + 35
        line_height = 16  # Уменьшено с 20 до 16
        max_visible = 9  # Увеличено с 5 до 9

        # Создаем мелкий шрифт для лога (размер 16)
        log_font = pygame.font.Font(None, 18)

        visible_logs = self.combat.combat_log[-max_visible:]
        for i, log_entry in enumerate(visible_logs):
            # Определяем цвет сообщения по ключевым словам
            color = self._get_log_color(log_entry)
            log_text = log_font.render(log_entry, True, color)
            self.screen.blit(log_text, (x + 10, log_y + i * line_height))

    def _get_log_color(self, message):
        """
        Определить цвет сообщения лога по ключевым словам

        Args:
            message: Текст сообщения

        Returns:
            tuple: RGB цвет для отображения
        """
        message_lower = message.lower()

        # КРИТИЧЕСКИЙ УДАР - ярко-красный/оранжевый
        if "критический" in message_lower or "крит" in message_lower:
            return (255, 100, 50)

        # Яд/отравление - зеленый
        if "яд" in message_lower or "отравл" in message_lower:
            return (100, 255, 100)

        # Уворот - голубой
        if "уклон" in message_lower or "уворот" in message_lower:
            return (100, 200, 255)

        # Оглушение/заморозка - фиолетовый
        if "оглуш" in message_lower or "заморож" in message_lower or "обморож" in message_lower:
            return (200, 100, 255)

        # Лечение/регенерация - светло-зеленый
        if "лечен" in message_lower or "восстан" in message_lower or "регенер" in message_lower:
            return (150, 255, 150)

        # Смерть/поражение - темно-красный
        if "повержен" in message_lower or "убит" in message_lower or "погиб" in message_lower:
            return (200, 50, 50)

        # Победа - золотой
        if "победа" in message_lower or "===":
            return (255, 215, 0)

        # Обычное сообщение - серый
        return (200, 200, 200)
