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

        # Цвета для контуров области действия
        self.skill_area_color = tuple(ui_config.get('cell_attack_range_color', [200, 100, 100, 128]))
        self.support_skill_area_color = (100, 200, 100, 128)  # Зеленый для поддерживающих умений

    def _get_hovered_skill_info(self):
        """
        Получить информацию об умении под курсором мыши

        Returns:
            tuple: (skill, tactical_range, is_support) или (None, 0, False) если нет умения
        """
        if self.hovered_skill_slot is None:
            return None, 0, False

        skill = self.combat.player.skill_manager.get_slot_skill(self.hovered_skill_slot)
        if not skill:
            return None, 0, False

        # Проверяем, можно ли использовать умение
        from game.skills import SkillCategory
        can_use, _ = skill.can_use(self.combat.player)
        combat_categories = [
            SkillCategory.COMBAT, SkillCategory.MAGIC,
            SkillCategory.SHADOW, SkillCategory.WARRIOR,
            SkillCategory.HUNTER, SkillCategory.MAGE, SkillCategory.GENERAL
        ]

        if not can_use or skill.category not in combat_categories:
            return None, 0, False

        # Получаем радиус действия умения (используем метод get_tactical_range если доступен)
        if hasattr(skill, 'get_tactical_range'):
            tactical_range = skill.get_tactical_range()
        else:
            tactical_range = getattr(skill, 'tactical_range', 1)

        # Определяем, является ли умение поддерживающим (применяется на себя)
        skill_id = self.combat.player.skill_manager.get_skill_id(skill)
        support_skills = ['heal', 'regeneration', 'stamina_recovery', 'mage_shield']
        is_support = skill_id in support_skills

        return skill, tactical_range, is_support

    def _render_skill_area_outline(self, field_x, field_y):
        """
        Отрисовка контура области действия умения при наведении на пиктограмму

        Args:
            field_x, field_y: Координаты поля боя на экране
        """
        skill, tactical_range, is_support = self._get_hovered_skill_info()

        if not skill or tactical_range <= 0:
            return

        # Позиция игрока как центр области действия
        center_x = self.combat.player_unit.x
        center_y = self.combat.player_unit.y

        # Выбираем цвет в зависимости от типа умения
        if is_support:
            outline_color = self.support_skill_area_color
        else:
            outline_color = self.skill_area_color

        # Создаем полупрозрачную поверхность для заливки
        cell_size = self.combat.cell_size
        cell_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        cell_surface.fill(outline_color)

        # Отрисовываем все клетки в радиусе действия (радиальная область)
        for dx in range(-tactical_range, tactical_range + 1):
            for dy in range(-tactical_range, tactical_range + 1):
                cell_x = center_x + dx
                cell_y = center_y + dy

                # Проверяем границы поля
                if cell_x < 0 or cell_x >= self.combat.battlefield_width:
                    continue
                if cell_y < 0 or cell_y >= self.combat.battlefield_height:
                    continue

                # Вычисляем евклидово расстояние для радиальной области
                distance = (dx * dx + dy * dy) ** 0.5
                if distance > tactical_range:
                    continue

                # Пропускаем клетку игрока для атакующих умений
                if not is_support and dx == 0 and dy == 0:
                    continue

                # Позиция клетки на экране
                screen_x = field_x + cell_x * cell_size
                screen_y = field_y + cell_y * cell_size

                # Отрисовываем полупрозрачную заливку
                self.screen.blit(cell_surface, (screen_x, screen_y))

        # Отрисовываем контур границы области действия
        self._render_area_border(field_x, field_y, center_x, center_y, tactical_range, outline_color, is_support)

    def _render_area_border(self, field_x, field_y, center_x, center_y, radius, color, is_support):
        """
        Отрисовка границы области действия (контур вокруг области)

        Args:
            field_x, field_y: Координаты поля боя
            center_x, center_y: Центр области (позиция игрока)
            radius: Радиус области
            color: Цвет контура
            is_support: Является ли умение поддерживающим
        """
        cell_size = self.combat.cell_size
        border_color = (color[0], color[1], color[2])  # RGB без альфа

        # Для каждой клетки в области проверяем, является ли её грань границей (радиальная область)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                cell_x = center_x + dx
                cell_y = center_y + dy

                # Проверяем границы поля
                if cell_x < 0 or cell_x >= self.combat.battlefield_width:
                    continue
                if cell_y < 0 or cell_y >= self.combat.battlefield_height:
                    continue

                # Вычисляем евклидово расстояние для радиальной области
                distance = (dx * dx + dy * dy) ** 0.5
                if distance > radius:
                    continue

                # Пропускаем клетку игрока для атакующих умений
                if not is_support and dx == 0 and dy == 0:
                    continue

                screen_x = field_x + cell_x * cell_size
                screen_y = field_y + cell_y * cell_size

                # Проверяем каждую грань клетки
                # Верхняя грань
                if self._is_area_border(center_x, center_y, cell_x, cell_y - 1, radius, is_support):
                    pygame.draw.line(self.screen, border_color,
                                   (screen_x, screen_y),
                                   (screen_x + cell_size, screen_y), 3)

                # Нижняя грань
                if self._is_area_border(center_x, center_y, cell_x, cell_y + 1, radius, is_support):
                    pygame.draw.line(self.screen, border_color,
                                   (screen_x, screen_y + cell_size),
                                   (screen_x + cell_size, screen_y + cell_size), 3)

                # Левая грань
                if self._is_area_border(center_x, center_y, cell_x - 1, cell_y, radius, is_support):
                    pygame.draw.line(self.screen, border_color,
                                   (screen_x, screen_y),
                                   (screen_x, screen_y + cell_size), 3)

                # Правая грань
                if self._is_area_border(center_x, center_y, cell_x + 1, cell_y, radius, is_support):
                    pygame.draw.line(self.screen, border_color,
                                   (screen_x + cell_size, screen_y),
                                   (screen_x + cell_size, screen_y + cell_size), 3)

    def _is_area_border(self, center_x, center_y, check_x, check_y, radius, is_support):
        """
        Проверить, является ли соседняя клетка границей области (вне области)

        Args:
            center_x, center_y: Центр области
            check_x, check_y: Проверяемая соседняя клетка
            radius: Радиус области
            is_support: Является ли умение поддерживающим

        Returns:
            bool: True если соседняя клетка вне области
        """
        # За пределами поля - это граница
        if check_x < 0 or check_x >= self.combat.battlefield_width:
            return True
        if check_y < 0 or check_y >= self.combat.battlefield_height:
            return True

        # Вычисляем евклидово расстояние от центра для радиальной области
        dx = check_x - center_x
        dy = check_y - center_y
        distance = (dx * dx + dy * dy) ** 0.5

        # Вне радиуса - это граница
        if distance > radius:
            return True

        # Для атакующих умений клетка игрока тоже считается границей
        if not is_support and dx == 0 and dy == 0:
            return True

        return False

    def _update_skill_hover(self):
        """
        Обновить состояние наведения на слот умения.
        Вызывается в начале render() для определения hovered_skill_slot до отрисовки поля боя.
        """
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill_slot = None

        # Пропускаем, если не ход игрока
        if self.combat.current_turn != "player":
            return

        # Вычисляем позицию панели умений (те же вычисления, что в render())
        field_width = self.combat.battlefield_width * self.combat.cell_size
        field_height = self.combat.battlefield_height * self.combat.cell_size
        field_x = 20
        field_y = 100
        ui_y = field_y + field_height + 20

        # Позиция панели умений
        skill_panel_x = field_x + 10
        skill_panel_y = ui_y + 35

        slot_size = 48
        slot_spacing = 8

        # Проверяем каждый слот
        for i in range(8):
            slot_x = skill_panel_x + i * (slot_size + slot_spacing)
            slot_y = skill_panel_y

            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)

            if slot_rect.collidepoint(mouse_pos):
                # Проверяем, есть ли в слоте используемое умение
                skill = self.combat.player.skill_manager.get_slot_skill(i)
                if skill:
                    from game.skills import SkillCategory
                    can_use, _ = skill.can_use(self.combat.player)
                    combat_categories = [
                        SkillCategory.COMBAT, SkillCategory.MAGIC,
                        SkillCategory.SHADOW, SkillCategory.WARRIOR,
                        SkillCategory.HUNTER, SkillCategory.MAGE, SkillCategory.GENERAL
                    ]
                    if can_use and skill.category in combat_categories:
                        self.hovered_skill_slot = i
                break

    def render(self):
        """Основной метод отрисовки"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Обновляем состояние наведения на слот умения (до отрисовки поля боя)
        self._update_skill_hover()

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

        # Отрисовываем контур области действия умения (если наведено на пиктограмму)
        self._render_skill_area_outline(field_x, field_y)

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
            # Для игрока используем спрайт "player" с учетом ранга
            if unit == self.combat.player_unit:
                sprite = self.combat.sprite_manager.get_npc_sprite_with_rank(
                    'player',
                    character.level
                )
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

        # Отрисовка информации о каждом NPC (без заголовка для экономии места)
        current_y = y + 5
        spacing = 5
        max_units_to_show = 5  # Максимум NPC для отображения

        # Показываем только живых врагов
        alive_enemies = [unit for unit in self.combat.enemy_units if unit.character.is_alive]

        # Ограничиваем количество отображаемых врагов
        enemies_to_show = alive_enemies[:max_units_to_show]

        # Рассчитываем высоту блока для размещения до 5 противников
        available_height = max_height - 15  # Отступы сверху и снизу
        unit_info_height = min(120, (available_height - spacing * (len(enemies_to_show) - 1)) // max(len(enemies_to_show), 1))

        for i, enemy_unit in enumerate(enemies_to_show):
            # Проверяем, влезает ли еще один блок
            if current_y + unit_info_height > y + max_height - 5:
                # Если не влезает, показываем сообщение о том, что есть еще враги
                remaining = len(alive_enemies) - i
                if remaining > 0:
                    more_text = self.small_font.render(
                        f"... и еще {remaining}",
                        True,
                        (180, 180, 200)
                    )
                    self.screen.blit(more_text, (x + 10, current_y))
                break

            self._render_unit_info_compact(enemy_unit, x + 5, current_y, width - 10, i, unit_info_height)
            current_y += unit_info_height + spacing

    def _render_unit_info_compact(self, unit, x, y, width, index, block_height=120):
        """
        Отрисовка компактной информации о юните

        Args:
            unit: Юнит для отрисовки
            x, y: Позиция блока
            width: Ширина блока
            index: Индекс врага (0 для основного, 1+ для свиты)
            block_height: Высота блока информации
        """
        character = unit.character

        # Фон блока
        pygame.draw.rect(self.screen, (45, 45, 60), (x, y, width, block_height))
        pygame.draw.rect(self.screen, (200, 100, 100), (x, y, width, block_height), 2)

        # Спрайт NPC (слева) - размер адаптируется под высоту блока
        sprite_size = min(40, block_height - 10)
        sprite_x = x + 3
        sprite_y = y + 3

        # Отрисовываем спрайт
        if self.combat.sprite_manager and hasattr(character, 'npc_type'):
            sprite = self.combat.sprite_manager.get_npc_sprite_with_rank(
                character.npc_type,
                character.level
            )
            if sprite:
                scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))
                self.screen.blit(scaled_sprite, (sprite_x, sprite_y))
            else:
                pygame.draw.rect(self.screen, (80, 80, 100), (sprite_x, sprite_y, sprite_size, sprite_size), 2)
        else:
            pygame.draw.rect(self.screen, (80, 80, 100), (sprite_x, sprite_y, sprite_size, sprite_size), 2)

        # Информация справа от спрайта
        info_x = sprite_x + sprite_size + 5
        info_y = y + 2

        # Метка врага и имя в одну строку
        label = "[Гл]" if index == 0 else f"[С{index}]"
        short_name = character.name[:12] + ".." if len(character.name) > 14 else character.name
        header_text = self.small_font.render(f"{label} {short_name}", True, (255, 255, 255))
        self.screen.blit(header_text, (info_x, info_y))

        # Уровень
        rank = character.get_rank() if hasattr(character, 'get_rank') else ""
        level_text = self.small_font.render(f"Ур.{character.level} ({rank})", True, (255, 215, 0))
        self.screen.blit(level_text, (info_x, info_y + 14))

        # HP бар под спрайтом (компактный)
        bar_y = y + sprite_size + 6
        bar_width = width - 6
        bar_height = 6

        max_hp = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        hp_ratio = min(1.0, character.health / max_hp) if max_hp > 0 else 0

        # HP бар с текстом
        hp_text = self.small_font.render(f"HP:{character.health}/{max_hp}", True, (255, 100, 100))
        self.screen.blit(hp_text, (x + 3, bar_y))
        bar_y += 12

        pygame.draw.rect(self.screen, (60, 60, 60), (x + 3, bar_y, bar_width, bar_height))
        if hp_ratio > 0:
            hp_color = (100, 255, 100) if hp_ratio > 0.5 else (255, 165, 0) if hp_ratio > 0.25 else (255, 100, 100)
            pygame.draw.rect(self.screen, hp_color, (x + 3, bar_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (x + 3, bar_y, bar_width, bar_height), 1)

        # Mana и Stamina только если места достаточно
        from game.constants import NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER
        is_animal = hasattr(character, 'npc_type') and character.npc_type in [NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER]

        if block_height >= 100:
            bar_y += bar_height + 4

            # Mana (только для персонажей с маной, но не для животных)
            if hasattr(character, 'mana') and not is_animal:
                max_mana = character.get_effective_max_mana() if hasattr(character, 'get_effective_max_mana') else character.max_mana
                mana_ratio = min(1.0, character.mana / max_mana) if max_mana > 0 else 0

                pygame.draw.rect(self.screen, (30, 30, 50), (x + 3, bar_y, bar_width, bar_height))
                if mana_ratio > 0:
                    pygame.draw.rect(self.screen, (100, 150, 255), (x + 3, bar_y, int(bar_width * mana_ratio), bar_height))
                pygame.draw.rect(self.screen, (150, 150, 200), (x + 3, bar_y, bar_width, bar_height), 1)
                bar_y += bar_height + 2

            # Stamina
            if hasattr(character, 'stamina'):
                max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina
                stamina_ratio = min(1.0, character.stamina / max_stamina) if max_stamina > 0 else 0

                pygame.draw.rect(self.screen, (50, 40, 20), (x + 3, bar_y, bar_width, bar_height))
                if stamina_ratio > 0:
                    pygame.draw.rect(self.screen, (255, 220, 100), (x + 3, bar_y, int(bar_width * stamina_ratio), bar_height))
                pygame.draw.rect(self.screen, (200, 180, 100), (x + 3, bar_y, bar_width, bar_height), 1)

        # Статы внизу блока (компактно)
        if block_height >= 110:
            stats_y = y + block_height - 16
            stats_text = f"Ур:{character.get_total_damage()} Зщ:{character.get_total_defense()} МЗ:{character.get_magic_defense()}"
            stat_surface = self.small_font.render(stats_text, True, (180, 180, 200))
            self.screen.blit(stat_surface, (x + 3, stats_y))

        # Пиктограммы статус-эффектов (справа вверху)
        self._render_status_effect_icons(character, x + width - 40, y + 2)

    def _render_status_effect_icons(self, character, x, y):
        """
        Отрисовка пиктограмм активных статус-эффектов (DoT, баффы, дебаффы)

        Args:
            character: Персонаж с эффектами
            x, y: Позиция для отрисовки иконок (справа от спрайта)
        """
        # Получаем список активных эффектов
        effects = []
        if hasattr(character, 'skill_manager') and character.skill_manager:
            effects = character.skill_manager.status_effects
        elif hasattr(character, 'status_effects'):
            effects = character.status_effects

        if not effects:
            return

        # Параметры иконок
        icon_size = 16
        icon_spacing = 2
        max_icons_per_row = 4
        current_x = x
        current_y = y

        # Отрисовываем иконки для каждого эффекта
        for i, effect in enumerate(effects):
            if not hasattr(effect, 'icon_id') or not effect.icon_id:
                continue

            # Вычисляем позицию иконки
            row = i // max_icons_per_row
            col = i % max_icons_per_row
            icon_x = current_x + col * (icon_size + icon_spacing)
            icon_y = current_y + row * (icon_size + icon_spacing)

            # Пытаемся загрузить спрайт эффекта
            icon_sprite = self._load_effect_icon(effect.icon_id, icon_size)

            if icon_sprite:
                # Отрисовываем спрайт
                self.screen.blit(icon_sprite, (icon_x, icon_y))
            else:
                # Fallback: рисуем цветной квадратик
                color = self._get_effect_fallback_color(effect.icon_id)
                pygame.draw.rect(self.screen, color, (icon_x, icon_y, icon_size, icon_size))
                pygame.draw.rect(self.screen, (255, 255, 255), (icon_x, icon_y, icon_size, icon_size), 1)

            # Отрисовываем счетчик длительности в правом нижнем углу иконки
            if hasattr(effect, 'remaining_duration'):
                duration_text = self.small_font.render(str(effect.remaining_duration), True, (255, 255, 255))
                duration_text = pygame.transform.scale(
                    duration_text,
                    (int(duration_text.get_width() * 0.5), int(duration_text.get_height() * 0.5))
                )
                self.screen.blit(duration_text, (icon_x + icon_size - 8, icon_y + icon_size - 8))

    def _load_effect_icon(self, icon_id, size):
        """
        Загрузить спрайт иконки эффекта

        Args:
            icon_id: ID иконки из конфига (например, 'burn', 'poison')
            size: Размер иконки

        Returns:
            pygame.Surface или None
        """
        if not self.combat.sprite_manager:
            return None

        try:
            # Пытаемся получить спрайт через sprite_manager
            return self.combat.sprite_manager.get_effect_icon(icon_id, icon_size=size)
        except Exception:
            pass

        return None

    def _get_effect_fallback_color(self, icon_id):
        """
        Получить цвет для fallback отображения эффекта

        Args:
            icon_id: ID иконки эффекта

        Returns:
            tuple: RGB цвет
        """
        colors = {
            'burn': (255, 100, 0),      # Оранжевый
            'poison': (100, 255, 100),  # Зеленый
            'bleed': (200, 0, 0),       # Красный
            'regeneration': (100, 255, 200),  # Светло-зеленый
            'shield': (100, 150, 255),  # Синий
            'stun': (200, 200, 0),      # Желтый
            'slow': (150, 150, 255),    # Голубой
            'strength_boost': (255, 150, 0),  # Оранжевый
            'armor_break': (150, 150, 150)    # Серый
        }
        return colors.get(icon_id, (200, 200, 200))

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

            # Отрисовка панели зелий (под умениями)
            self._render_potion_panel(x + 10, y + 90, skill_panel_width)

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

    def _render_potion_panel(self, x, y, width):
        """Отрисовка панели быстрых зелий"""
        from game.inventory import EquipmentSlot

        # Получаем пояс игрока
        belt = self.combat.player.inventory.get_equipped_item(EquipmentSlot.BELT)
        if not belt or not hasattr(belt, 'potion_slots') or belt.potion_slots == 0:
            return  # Нет пояса или нет слотов для зелий

        # Очищаем список кнопок перед отрисовкой
        if not hasattr(self, 'potion_buttons'):
            self.potion_buttons = []
        else:
            self.potion_buttons.clear()

        slot_size = 48
        slot_spacing = 8

        # Слоты зелий
        potion_slots = [
            EquipmentSlot.BELT_POTION_1,
            EquipmentSlot.BELT_POTION_2,
            EquipmentSlot.BELT_POTION_3,
            EquipmentSlot.BELT_POTION_4
        ][:belt.potion_slots]

        # Получаем позицию мыши для подсветки
        mouse_pos = pygame.mouse.get_pos()

        for i, slot in enumerate(potion_slots):
            slot_x = x + i * (slot_size + slot_spacing)
            slot_y = y

            potion = self.combat.player.inventory.get_equipped_item(slot)

            # Фон слота
            bg_color = (60, 40, 60) if potion else (30, 30, 30)
            border_color = (150, 100, 150) if potion else (100, 100, 100)

            # Создаем rect для кнопки
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            self.potion_buttons.append((slot_rect, slot, potion))

            # Проверяем наведение мыши
            if slot_rect.collidepoint(mouse_pos) and potion:
                # Подсветка при наведении
                bg_color = tuple(min(255, c + 30) for c in bg_color)

            pygame.draw.rect(self.screen, bg_color, slot_rect)
            pygame.draw.rect(self.screen, border_color, slot_rect, 2)

            # Метка "ПКМ"
            label_text = self.info_font.render("ПКМ", True, (180, 180, 180))
            self.screen.blit(label_text, (slot_x + 4, slot_y + 4))

            # Если есть зелье, отображаем информацию
            if potion:
                # Иконка зелья (спрайт или первая буква названия как fallback)
                icon_size = slot_size - 8  # Немного меньше слота для отступов
                icon_x = slot_x + 4
                icon_y = slot_y + 4

                potion_name = potion.get_full_name() if hasattr(potion, 'get_full_name') else potion.name
                potion_id = potion.item_id if hasattr(potion, 'item_id') else None

                # Пробуем отрисовать спрайт зелья
                if potion_id and self.combat.sprite_manager:
                    self.combat.sprite_manager.render_potion_icon(
                        self.screen,
                        potion_id,
                        icon_x,
                        icon_y,
                        icon_size,
                        fallback_text=potion_name[0]
                    )
                else:
                    # Fallback: первая буква названия
                    icon_font = pygame.font.Font(None, 32)
                    icon_text = icon_font.render(potion_name[0], True, (200, 100, 200))
                    icon_rect = icon_text.get_rect()
                    icon_rect.center = (slot_x + slot_size // 2, slot_y + slot_size // 2 + 4)
                    self.screen.blit(icon_text, icon_rect)

                # Количество зелий в инвентаре
                potion_count = self.combat.player.inventory.get_item_count(potion)
                if potion_count > 1:
                    count_text = self.info_font.render(f"x{potion_count}", True, (255, 215, 0))
                    self.screen.blit(count_text, (slot_x + slot_size - 24, slot_y + slot_size - 18))

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

        # Горение/огонь/кровотечение - оранжевый (DoT эффекты)
        if ("горен" in message_lower or "огон" in message_lower or "пламен" in message_lower or
            "загора" in message_lower or "поджог" in message_lower or "перекинул" in message_lower or
            "кровотеч" in message_lower or "урона от огня" in message_lower):
            return (255, 165, 0)

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
