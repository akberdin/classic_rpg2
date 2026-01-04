"""
Модуль рендеринга боевого интерфейса.

Отвечает за отрисовку UI элементов боевой системы:
- Окно боя
- Статистика персонажей
- Журнал боевых действий
- Панель умений и зелий
"""
import pygame
from game.constants import NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER


class CombatRenderer:
    """Класс отрисовки боевого интерфейса"""

    def __init__(self, screen, font, scaler=None, sprite_manager=None):
        """
        Инициализация рендерера боя

        Args:
            screen: Pygame экран
            font: Основной шрифт
            scaler: UIScaler для адаптивного масштабирования
            sprite_manager: Менеджер спрайтов для иконок
        """
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.sprite_manager = sprite_manager

        info_font_size = scaler.scale_font_size(20) if scaler else 20
        self.info_font = pygame.font.Font(None, info_font_size)

        # Текстовые метки
        self.labels = {
            'health': 'HP:',
            'mana': 'Мана:',
            'stamina': 'Выносливость:',
            'damage': 'Урон:',
            'defense': 'Защита:',
            'magic_defense': 'Маг. защ.:',
            'dodge': 'Уворот:',
            'crit': 'Крит:',
        }

        # Кнопки зелий для обработки кликов
        self.potion_buttons = []

    def get_label(self, label_name):
        """Получить текстовую метку"""
        return self.labels.get(label_name, label_name)

    def render(self, player, enemy, combat_log, turn, skill_manager):
        """
        Отрисовка полного окна боя

        Args:
            player: Игрок
            enemy: Противник
            combat_log: Журнал боевых действий
            turn: Текущий ход ('player' или 'enemy')
            skill_manager: Менеджер умений игрока
        """
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемняем фон
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна боя
        if self.scaler:
            combat_width = self.scaler.scale_width(1100)
            combat_height = self.scaler.scale_height(850)
        else:
            combat_width = min(1100, int(screen_width * 0.85))
            combat_height = min(850, int(screen_height * 0.9))

        combat_x = (screen_width - combat_width) // 2
        combat_y = (screen_height - combat_height) // 2

        # Фон окна боя с градиентом
        from game.ui import UIHelper
        UIHelper.draw_gradient_rect(
            self.screen, combat_x, combat_y, combat_width, combat_height,
            (35, 35, 45), (55, 55, 70)
        )

        # Рамка окна боя
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (combat_x, combat_y, combat_width, combat_height),
            4
        )

        # Заголовок
        title_text = self.font.render("БОЙ", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = combat_x + combat_width // 2
        title_rect.y = combat_y + 15
        self.screen.blit(title_text, title_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (combat_x + 10, combat_y + 50),
            (combat_x + combat_width - 10, combat_y + 50),
            2
        )

        # Статистика игрока (слева)
        self._render_character_stats(
            player,
            combat_x + 30,
            combat_y + 65,
            "Игрок",
            True
        )

        # Статистика врага (справа)
        self._render_character_stats(
            enemy,
            combat_x + combat_width - 350,
            combat_y + 65,
            "Противник",
            False
        )

        # Блок лога боя
        self._render_combat_log(combat_log, combat_x, combat_y, combat_width)

        # Панель действий и умений
        self._render_actions_panel(
            player, turn, skill_manager,
            combat_x, combat_y, combat_width, combat_height
        )

        # Подсказка
        hint_y = combat_y + combat_height - 35
        hint_text = self.info_font.render(
            "Клавиши 1-8 - использовать умение | ПКМ на зелье - использовать | ESC - сбежать",
            True,
            (180, 180, 200)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = combat_x + combat_width // 2
        hint_rect.y = hint_y
        self.screen.blit(hint_text, hint_rect)

    def _render_combat_log(self, combat_log, combat_x, combat_y, combat_width):
        """Отрисовка журнала боевых действий"""
        log_block_x = combat_x + 30
        log_block_y = combat_y + 360
        log_block_width = combat_width - 60
        log_block_height = 240

        # Фон блока лога
        pygame.draw.rect(
            self.screen,
            (25, 25, 35),
            (log_block_x, log_block_y, log_block_width, log_block_height)
        )

        # Рамка блока лога
        pygame.draw.rect(
            self.screen,
            (100, 150, 200),
            (log_block_x, log_block_y, log_block_width, log_block_height),
            2
        )

        # Заголовок лога
        log_title = self.info_font.render("Журнал боевых действий", True, (150, 200, 255))
        self.screen.blit(log_title, (log_block_x + 15, log_block_y + 10))

        # Линия под заголовком
        pygame.draw.line(
            self.screen,
            (80, 80, 120),
            (log_block_x + 10, log_block_y + 38),
            (log_block_x + log_block_width - 10, log_block_y + 38),
            1
        )

        # Отрисовка логов
        log_line_height = 24
        max_visible_logs = 7
        log_start_y = log_block_y + 48

        visible_logs = combat_log[-max_visible_logs:] if len(combat_log) > max_visible_logs else combat_log

        for i, log_entry in enumerate(visible_logs):
            log_color = self._get_log_color(log_entry)
            log_text = self.info_font.render(log_entry, True, log_color)
            self.screen.blit(log_text, (log_block_x + 15, log_start_y + i * log_line_height))

    def _get_log_color(self, log_entry):
        """Определить цвет записи лога"""
        if "Вы атакуете" in log_entry or "Вы победили" in log_entry:
            return (150, 255, 150)  # Зеленый
        elif "атакует вас" in log_entry or "Вы погибли" in log_entry:
            return (255, 150, 150)  # Красный
        elif "КРИТИЧЕСКИЙ УДАР" in log_entry:
            return (255, 215, 0)  # Золотой
        elif "увернулся" in log_entry or "сбежали" in log_entry:
            return (150, 200, 255)  # Синий
        return (200, 200, 200)  # Серый

    def _render_actions_panel(self, player, turn, skill_manager, combat_x, combat_y, combat_width, combat_height):
        """Отрисовка панели действий и умений"""
        actions_y = combat_y + combat_height - 110

        if turn == "player":
            actions_title = self.font.render("Ваш ход! Используйте умения (клавиши 1-8):", True, (100, 255, 100))
        else:
            actions_title = self.font.render("Ход противника...", True, (255, 150, 150))

        self.screen.blit(actions_title, (combat_x + 30, actions_y))

        # Слоты умений
        slot_size = 48
        slot_spacing = 8
        slots_start_x = combat_x + (combat_width - (slot_size + slot_spacing) * 8) // 2
        slots_y = actions_y + 35

        for i in range(8):
            slot_x = slots_start_x + i * (slot_size + slot_spacing)
            skill = skill_manager.get_slot_skill(i)

            is_usable = False
            if skill:
                from game.skills import SkillCategory
                can_use, reason = skill.can_use(player)
                combat_categories = [SkillCategory.GENERAL]
                is_usable = can_use and skill.category in combat_categories

            # Фон слота
            bg_color = (40, 40, 40) if skill and is_usable else (30, 30, 30)
            pygame.draw.rect(self.screen, bg_color, (slot_x, slots_y, slot_size, slot_size))

            # Рамка слота
            if skill and is_usable:
                border_color = (200, 200, 100)
            elif skill:
                border_color = (80, 80, 80)
            else:
                border_color = (100, 100, 100)

            pygame.draw.rect(self.screen, border_color, (slot_x, slots_y, slot_size, slot_size), 2)

            # Номер слота
            key_text = self.info_font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(key_text, (slot_x + 4, slots_y + 4))

            # Иконка умения
            if skill:
                skill_id = skill_manager.get_slot_skill_id(i)
                icon_size = slot_size - 8
                icon_x = slot_x + 4
                icon_y = slots_y + 4

                if skill_id and self.sprite_manager:
                    self.sprite_manager.render_skill_icon(
                        self.screen, skill_id, icon_x, icon_y, icon_size,
                        fallback_text=skill.name[0]
                    )
                else:
                    icon_font = pygame.font.Font(None, 32)
                    icon_text = icon_font.render(skill.name[0], True, (255, 255, 255))
                    icon_rect = icon_text.get_rect()
                    icon_rect.center = (slot_x + slot_size // 2, slots_y + slot_size // 2 + 4)
                    self.screen.blit(icon_text, icon_rect)

                # Перезарядка
                if skill.current_cooldown > 0:
                    cooldown_text = self.info_font.render(str(skill.current_cooldown), True, (255, 100, 100))
                    cooldown_rect = cooldown_text.get_rect()
                    cooldown_rect.center = (slot_x + slot_size // 2, slots_y + slot_size // 2)
                    self.screen.blit(cooldown_text, cooldown_rect)

        # Панель зелий
        self._render_potion_panel(
            player,
            slots_start_x + (slot_size + slot_spacing) * 8 + 20,
            slots_y, slot_size, slot_spacing
        )

    def _render_potion_panel(self, player, x, y, slot_size, slot_spacing):
        """Отрисовка панели быстрых зелий"""
        from game.inventory import EquipmentSlot

        belt = player.inventory.get_equipped_item(EquipmentSlot.BELT)
        if not belt or not hasattr(belt, 'potion_slots') or belt.potion_slots == 0:
            return

        self.potion_buttons.clear()

        potion_slots = [
            EquipmentSlot.BELT_POTION_1,
            EquipmentSlot.BELT_POTION_2,
            EquipmentSlot.BELT_POTION_3,
            EquipmentSlot.BELT_POTION_4
        ][:belt.potion_slots]

        for i, slot in enumerate(potion_slots):
            slot_x = x + i * (slot_size + slot_spacing)
            slot_y = y

            potion = player.inventory.get_equipped_item(slot)

            bg_color = (60, 40, 60) if potion else (30, 30, 30)
            border_color = (150, 100, 150) if potion else (100, 100, 100)

            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            self.potion_buttons.append((slot_rect, slot, potion))

            pygame.draw.rect(self.screen, bg_color, slot_rect)
            pygame.draw.rect(self.screen, border_color, slot_rect, 2)

            label_text = self.info_font.render("ПКМ", True, (180, 180, 180))
            self.screen.blit(label_text, (slot_x + 4, slot_y + 4))

            if potion:
                icon_size = slot_size - 8
                icon_x = slot_x + 4
                icon_y = slot_y + 4

                potion_name = potion.get_full_name() if hasattr(potion, 'get_full_name') else potion.name
                potion_id = potion.item_id if hasattr(potion, 'item_id') else None

                if potion_id and self.sprite_manager:
                    self.sprite_manager.render_potion_icon(
                        self.screen, potion_id, icon_x, icon_y, icon_size,
                        fallback_text=potion_name[0]
                    )
                else:
                    icon_font = pygame.font.Font(None, 32)
                    icon_text = icon_font.render(potion_name[0], True, (200, 100, 200))
                    icon_rect = icon_text.get_rect()
                    icon_rect.center = (slot_x + slot_size // 2, slot_y + slot_size // 2 + 4)
                    self.screen.blit(icon_text, icon_rect)

                potion_count = player.inventory.get_item_count(potion)
                if potion_count > 1:
                    count_text = self.info_font.render(f"x{potion_count}", True, (255, 215, 0))
                    self.screen.blit(count_text, (slot_x + slot_size - 24, slot_y + slot_size - 18))

    def _render_character_stats(self, character, x, y, label, is_player):
        """Отрисовка статистики персонажа"""
        panel_width = 320
        panel_height = 280

        pygame.draw.rect(
            self.screen,
            (45, 45, 60),
            (x - 10, y - 10, panel_width, panel_height)
        )

        border_color = (100, 200, 100) if is_player else (200, 100, 100)
        pygame.draw.rect(
            self.screen,
            border_color,
            (x - 10, y - 10, panel_width, panel_height),
            3
        )

        # Имя персонажа
        name_text = self.info_font.render(f"{label}: {character.name}", True, (255, 255, 255))
        self.screen.blit(name_text, (x, y))

        # Уровень и ранг
        rank = character.get_rank() if hasattr(character, 'get_rank') else ""
        level_text = self.info_font.render(f"Ур. {character.level} ({rank})", True, (255, 215, 0))
        self.screen.blit(level_text, (x, y + 24))

        # Здоровье
        effective_max_health = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        health_percent = (character.health / effective_max_health) * 100 if effective_max_health > 0 else 0
        health_color = (255, 100, 100) if health_percent < 30 else (255, 165, 0) if health_percent < 60 else (100, 255, 100)

        health_label = self.get_label('health')
        health_text = self.info_font.render(
            f"{health_label} {character.health}/{effective_max_health} ({health_percent:.0f}%)",
            True, health_color
        )
        self.screen.blit(health_text, (x, y + 48))

        # Полоса здоровья
        bar_width = 280
        bar_height = 18
        bar_x = x
        bar_y = y + 72

        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        health_ratio = min(1.0, character.health / effective_max_health) if effective_max_health > 0 else 0
        fill_width = int(bar_width * health_ratio)
        if fill_width > 0:
            pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, fill_width, bar_height))

        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)

        # Мана (если не животное)
        is_animal = hasattr(character, 'npc_type') and character.npc_type in [NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER]

        if hasattr(character, 'mana') and hasattr(character, 'max_mana') and not is_animal:
            effective_max_mana = character.get_effective_max_mana() if hasattr(character, 'get_effective_max_mana') else character.max_mana

            mana_label = self.get_label('mana')
            mana_text = self.info_font.render(
                f"{mana_label} {character.mana}/{effective_max_mana}",
                True, (100, 150, 255)
            )
            self.screen.blit(mana_text, (x, y + 95))

            mana_bar_y = y + 115
            pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, mana_bar_y, bar_width, bar_height))

            mana_fill_width = int(bar_width * min(1.0, character.mana / effective_max_mana)) if effective_max_mana > 0 else 0
            if mana_fill_width > 0:
                pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, mana_bar_y, mana_fill_width, bar_height))

            pygame.draw.rect(self.screen, (150, 150, 200), (bar_x, mana_bar_y, bar_width, bar_height), 2)

        # Выносливость
        if hasattr(character, 'stamina') and hasattr(character, 'max_stamina'):
            effective_max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina

            stamina_label = self.get_label('stamina')
            stamina_text = self.info_font.render(
                f"{stamina_label} {character.stamina}/{effective_max_stamina}",
                True, (255, 220, 100)
            )
            self.screen.blit(stamina_text, (x, y + 138))

            stamina_bar_y = y + 158
            pygame.draw.rect(self.screen, (50, 40, 20), (bar_x, stamina_bar_y, bar_width, bar_height))

            stamina_fill_width = int(bar_width * min(1.0, character.stamina / effective_max_stamina)) if effective_max_stamina > 0 else 0
            if stamina_fill_width > 0:
                pygame.draw.rect(self.screen, (255, 220, 100), (bar_x, stamina_bar_y, stamina_fill_width, bar_height))

            pygame.draw.rect(self.screen, (200, 180, 100), (bar_x, stamina_bar_y, bar_width, bar_height), 2)

        # Характеристики
        stats_y = y + 185
        stats = [
            f"{self.get_label('damage')} {character.get_total_damage()}",
            f"{self.get_label('defense')} {character.get_total_defense()}",
            f"{self.get_label('magic_defense')} {character.get_magic_defense()}",
            f"{self.get_label('dodge')} {character.calculate_dodge_chance():.1f}%",
            f"{self.get_label('crit')} {character.calculate_crit_chance():.1f}%"
        ]

        for i, stat in enumerate(stats):
            stat_text = self.info_font.render(stat, True, (200, 200, 220))
            if i < 3:
                stat_x = x
                stat_y_offset = stats_y + i * 22
            else:
                stat_x = x + 140
                stat_y_offset = stats_y + (i - 3) * 22
            self.screen.blit(stat_text, (stat_x, stat_y_offset))
