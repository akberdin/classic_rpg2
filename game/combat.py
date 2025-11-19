"""
Система боя с пошаговым управлением
"""
import pygame
import random
from game.constants import COLORS


def calculate_combat_exp(player_level, enemy_level, base_exp_per_level=20):
    """
    Рассчитать опыт за победу над врагом с учётом разницы уровней

    Args:
        player_level: Уровень игрока
        enemy_level: Уровень врага
        base_exp_per_level: Базовый опыт за уровень врага

    Returns:
        int: Количество опыта
    """
    base_exp = enemy_level * base_exp_per_level
    level_diff = enemy_level - player_level

    # Бонус/штраф за разницу уровней
    if level_diff > 0:
        # Враг сильнее - бонус до 100% (10% за каждый уровень разницы)
        bonus = min(1.0, level_diff * 0.1)
        exp = int(base_exp * (1 + bonus))
    elif level_diff < 0:
        # Враг слабее - штраф до 90% (5% за каждый уровень разницы)
        penalty = min(0.9, abs(level_diff) * 0.05)
        exp = int(base_exp * (1 - penalty))
    else:
        exp = base_exp

    # Минимум 10% от базового опыта
    return max(int(base_exp * 0.1), exp)


class CombatSystem:
    """Класс управления боевой системой"""

    def __init__(self, player, enemy, screen, font, scaler=None, game_map=None, respawn_manager=None):
        """
        Инициализация боевой системы

        Args:
            player: Игрок
            enemy: Враг
            screen: Pygame экран
            font: Шрифт для отображения текста
            scaler: UIScaler для адаптивного масштабирования (опционально)
            game_map: Карта игры (для размещения лута)
            respawn_manager: Менеджер респавна NPC
        """
        self.player = player
        self.enemy = enemy
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.game_map = game_map
        self.respawn_manager = respawn_manager
        info_font_size = scaler.scale_font_size(20) if scaler else 20
        self.info_font = pygame.font.Font(None, info_font_size)

        # Состояние боя
        self.active = True
        self.turn = "player"  # player или enemy
        self.combat_log = []  # Лог боевых событий
        self.max_log_entries = 10  # Увеличено с 5 до 10 для более полного лога

        # Варианты действий игрока
        self.actions = [
            {"name": "Атака", "key": "1", "action": "attack"},
            {"name": "Убежать", "key": "2", "action": "flee"}
        ]
        self.selected_action = None
        self.hovered_action = None  # Действие под курсором мыши
        self.action_buttons = []  # Список прямоугольников кнопок для обработки мыши

        # Добавляем начальное сообщение в лог
        self.add_to_log(f"Бой начался! Противник: {enemy.name} (Уровень {enemy.level})")

    def add_to_log(self, message):
        """
        Добавить сообщение в лог боя

        Args:
            message: Текст сообщения
        """
        self.combat_log.append(message)
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)

    def handle_input(self, event):
        """
        Обработка ввода игрока (клавиатура и мышь)

        Args:
            event: Pygame событие

        Returns:
            str: Результат боя ("continue", "victory", "defeat", "fled")
        """
        if self.turn != "player":
            return "continue"

        # Обработка клавиатуры
        if event.type == pygame.KEYDOWN:
            # ESC - попытка сбежать из боя
            if event.key == pygame.K_ESCAPE:
                return self.execute_player_action("flee")

            # Обработка использования умений (клавиши 1-8)
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                slot_index = event.key - pygame.K_1  # 0-7
                skill = self.player.skill_manager.get_slot_skill(slot_index)

                if skill:
                    # Проверяем, является ли умение боевым или магическим
                    from game.skills import SkillCategory
                    if skill.category in [SkillCategory.COMBAT, SkillCategory.MAGIC]:
                        return self.execute_skill_action(skill)
                    else:
                        self.add_to_log(f"{skill.name} нельзя использовать в бою!")
                else:
                    self.add_to_log(f"Слот {slot_index + 1} пуст!")

                return "continue"

        return "continue"

    def execute_player_action(self, action_type):
        """
        Выполнить действие игрока

        Args:
            action_type: Тип действия

        Returns:
            str: Результат боя
        """
        if action_type == "attack":
            # Атака
            attack_result = self.player.attack(self.enemy)

            if attack_result['dodged']:
                self.add_to_log(f"{self.enemy.name} увернулся от вашей атаки!")
            elif attack_result['hit']:
                crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""
                armor_msg = f" (броня заблокировала {attack_result['blocked_by_armor']} урона)" if attack_result['blocked_by_armor'] > 0 else ""
                self.add_to_log(f"Вы атакуете {self.enemy.name} и наносите {attack_result['damage']} урона!{crit_msg}{armor_msg}")

                if not self.enemy.is_alive:
                    self.add_to_log(f"Вы победили {self.enemy.name}!")

                    # Увеличиваем счетчик убитых врагов
                    if hasattr(self.player, 'enemies_killed'):
                        self.player.enemies_killed += 1

                    # Регистрируем смерть NPC для респавна
                    if self.respawn_manager:
                        self.respawn_manager.register_death(self.enemy)

                    # Оставляем лут на тайле (если есть карта и у врага есть предметы)
                    if self.game_map and hasattr(self.enemy, 'inventory'):
                        if len(self.enemy.inventory.items) > 0 or self.enemy.inventory.gold > 0:
                            tile = self.game_map.get_tile(self.enemy.x, self.enemy.y)
                            if tile:
                                tile.set_loot(self.enemy.inventory)
                                self.add_to_log(f"На земле остался лут!")

                    # Даем опыт за победу (с учётом разницы уровней)
                    exp_gained = calculate_combat_exp(self.player.level, self.enemy.level)
                    self.player.add_experience(exp_gained)
                    self.add_to_log(f"Получено {exp_gained} опыта!")
                    return "victory"

            # Переход хода к врагу
            self.turn = "enemy"
            return self.execute_enemy_turn()

        elif action_type == "heal":
            # Отдых - восстановление здоровья
            health_restored = int(self.player.max_health * 0.3)
            old_health = self.player.health
            self.player.health = min(self.player.max_health, self.player.health + health_restored)
            actual_restored = self.player.health - old_health

            self.add_to_log(f"Вы отдыхаете и восстанавливаете {actual_restored} HP!")

            # Переход хода к врагу
            self.turn = "enemy"
            return self.execute_enemy_turn()

        elif action_type == "flee":
            # Попытка побега (50% шанс)
            if random.random() < 0.5:
                self.add_to_log("Вы успешно сбежали из боя!")
                return "fled"
            else:
                self.add_to_log("Не удалось сбежать!")
                # Переход хода к врагу
                self.turn = "enemy"
                return self.execute_enemy_turn()

        return "continue"

    def execute_skill_action(self, skill):
        """
        Выполнить использование умения

        Args:
            skill: Объект умения для использования

        Returns:
            str: Результат боя
        """
        # Используем умение
        result = self.player.skill_manager.use_skill(skill, self.enemy)

        if result['success']:
            self.add_to_log(result['message'])

            # Обрабатываем результаты в зависимости от типа умения
            if 'damage' in result:
                # Боевое умение с уроном
                if result.get('killed'):
                    self.add_to_log(f"Вы победили {self.enemy.name}!")

                    # Увеличиваем счетчик убитых врагов
                    if hasattr(self.player, 'enemies_killed'):
                        self.player.enemies_killed += 1

                    # Регистрируем смерть NPC для респавна
                    if self.respawn_manager:
                        self.respawn_manager.register_death(self.enemy)

                    # Даем опыт за победу (с учётом разницы уровней)
                    exp_gained = calculate_combat_exp(self.player.level, self.enemy.level)
                    self.player.add_experience(exp_gained)
                    self.add_to_log(f"Получено {exp_gained} опыта!")
                    return "victory"

            if 'heal' in result:
                # Лечение
                pass  # Сообщение уже добавлено

            if 'poison_applied' in result:
                # Яд наложен
                pass  # Сообщение уже добавлено

            if 'stunned' in result and result['stunned']:
                # Оглушение
                pass  # Сообщение уже добавлено

            # Переход хода к врагу
            self.turn = "enemy"
            return self.execute_enemy_turn()
        else:
            # Умение не удалось использовать
            self.add_to_log(result['message'])
            return "continue"

    def execute_enemy_turn(self):
        """
        Выполнить ход врага

        Returns:
            str: Результат боя
        """
        # Обрабатываем статус-эффекты врага (яд, оглушение и т.д.)
        if hasattr(self.enemy, 'status_effects'):
            for effect in self.enemy.status_effects[:]:
                message = effect.tick(self.enemy)
                if message:
                    self.add_to_log(message)
                if effect.is_expired():
                    remove_msg = effect.remove(self.enemy)
                    if remove_msg:
                        self.add_to_log(remove_msg)
                    self.enemy.status_effects.remove(effect)

            # Проверяем, не умер ли враг от яда
            if not self.enemy.is_alive:
                self.add_to_log(f"{self.enemy.name} погиб от эффектов!")

                # Увеличиваем счетчик убитых врагов
                if hasattr(self.player, 'enemies_killed'):
                    self.player.enemies_killed += 1

                # Регистрируем смерть NPC для респавна
                if self.respawn_manager:
                    self.respawn_manager.register_death(self.enemy)

                # Даем опыт за победу (с учётом разницы уровней)
                exp_gained = calculate_combat_exp(self.player.level, self.enemy.level)
                self.player.add_experience(exp_gained)
                self.add_to_log(f"Получено {exp_gained} опыта!")
                return "victory"

            # Проверяем оглушение врага
            if hasattr(self.enemy, 'stunned') and self.enemy.stunned:
                self.add_to_log(f"{self.enemy.name} оглушен и пропускает ход!")
                # Снимаем оглушение
                self.enemy.stunned = False
                # Уменьшаем перезарядку умений игрока
                self.player.skill_manager.tick_cooldowns()
                self.turn = "player"
                return "continue"

        # Враг всегда атакует
        attack_result = self.enemy.attack(self.player)

        if attack_result['dodged']:
            self.add_to_log(f"Вы увернулись от атаки {self.enemy.name}!")
        elif attack_result['hit']:
            crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""

            # Проверяем режим бессмертия
            if attack_result.get('godmode', False):
                self.add_to_log(f"{self.enemy.name} атакует вас, но ЧИТ-МОД блокирует весь урон!")
            else:
                armor_msg = f" (ваша броня заблокировала {attack_result['blocked_by_armor']} урона)" if attack_result.get('blocked_by_armor', 0) > 0 else ""
                self.add_to_log(f"{self.enemy.name} атакует вас и наносит {attack_result['damage']} урона!{crit_msg}{armor_msg}")

                if not self.player.is_alive:
                    self.add_to_log("Вы погибли!")
                    return "defeat"

        # Уменьшаем перезарядку умений игрока после полного хода
        self.player.skill_manager.tick_cooldowns()

        # Обрабатываем статус-эффекты игрока (регенерация и т.д.)
        if hasattr(self.player, 'skill_manager'):
            effect_messages = self.player.skill_manager.tick_status_effects()
            for msg in effect_messages:
                self.add_to_log(msg)

        # Возвращаем ход игроку
        self.turn = "player"
        return "continue"

    def render(self):
        """Отрисовка улучшенного окна боя с отдельным блоком лога"""
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемняем фон
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна боя (увеличены для лога)
        if self.scaler:
            combat_width = self.scaler.scale_width(1100)
            combat_height = self.scaler.scale_height(750)
        else:
            combat_width = min(1100, int(screen_width * 0.85))
            combat_height = min(750, int(screen_height * 0.8))

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
        title_text = self.font.render("⚔ БОЙ ⚔", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = combat_x + combat_width // 2
        title_rect.y = combat_y + 15
        self.screen.blit(title_text, title_rect)

        # Разделительная линия после заголовка
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (combat_x + 10, combat_y + 50),
            (combat_x + combat_width - 10, combat_y + 50),
            2
        )

        # Отрисовка статистики игрока (слева, компактнее)
        self._render_character_stats(
            self.player,
            combat_x + 30,
            combat_y + 65,
            "Игрок",
            True
        )

        # Отрисовка статистики врага (справа, компактнее)
        self._render_character_stats(
            self.enemy,
            combat_x + combat_width - 350,
            combat_y + 65,
            "Противник",
            False
        )

        # ОТДЕЛЬНЫЙ БЛОК ЛОГА БОЯ (ниже статистики персонажей)
        log_block_x = combat_x + 30
        log_block_y = combat_y + 240  # Опустили ниже чтобы не накладывался
        log_block_width = combat_width - 60
        log_block_height = 330  # Увеличили высоту

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
        log_title = self.info_font.render("📜 Журнал боевых действий", True, (150, 200, 255))
        self.screen.blit(log_title, (log_block_x + 15, log_block_y + 10))

        # Линия под заголовком лога
        pygame.draw.line(
            self.screen,
            (80, 80, 120),
            (log_block_x + 10, log_block_y + 38),
            (log_block_x + log_block_width - 10, log_block_y + 38),
            1
        )

        # Отрисовка логов с прокруткой
        log_line_height = 24
        max_visible_logs = 11  # Увеличено с 9 до 11
        log_start_y = log_block_y + 48

        # Показываем последние записи
        visible_logs = self.combat_log[-max_visible_logs:] if len(self.combat_log) > max_visible_logs else self.combat_log

        for i, log_entry in enumerate(visible_logs):
            # Цвет в зависимости от содержания
            if "Вы атакуете" in log_entry or "Вы победили" in log_entry:
                log_color = (150, 255, 150)  # Зеленый для успешных действий
            elif "атакует вас" in log_entry or "Вы погибли" in log_entry:
                log_color = (255, 150, 150)  # Красный для урона
            elif "КРИТИЧЕСКИЙ УДАР" in log_entry:
                log_color = (255, 215, 0)  # Золотой для критов
            elif "увернулся" in log_entry or "сбежали" in log_entry:
                log_color = (150, 200, 255)  # Синий для уворотов
            else:
                log_color = (200, 200, 200)  # Серый для остального

            log_text = self.info_font.render(log_entry, True, log_color)
            self.screen.blit(log_text, (log_block_x + 15, log_start_y + i * log_line_height))

        # Действия игрока - отображение слотов умений
        actions_y = combat_y + combat_height - 110
        if self.turn == "player":
            actions_title = self.font.render("⚡ Ваш ход! Используйте умения (клавиши 1-8):", True, (100, 255, 100))
        else:
            actions_title = self.font.render("⏳ Ход противника...", True, (255, 150, 150))

        self.screen.blit(actions_title, (combat_x + 30, actions_y))

        # Отрисовка слотов умений с подсветкой
        slot_size = 48
        slot_spacing = 8
        slots_start_x = combat_x + (combat_width - (slot_size + slot_spacing) * 8) // 2
        slots_y = actions_y + 35

        for i in range(8):
            slot_x = slots_start_x + i * (slot_size + slot_spacing)
            skill = self.player.skill_manager.get_slot_skill(i)

            # Проверяем, доступно ли умение для использования в бою
            is_usable = False
            if skill:
                from game.skills import SkillCategory
                can_use, reason = skill.can_use(self.player)
                is_usable = can_use and skill.category in [SkillCategory.COMBAT, SkillCategory.MAGIC]

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

            pygame.draw.rect(self.screen, bg_color, (slot_x, slots_y, slot_size, slot_size))

            # Рамка слота
            if skill and is_usable:
                border_color = (200, 200, 100)  # Яркая желтая рамка для доступных
            elif skill:
                border_color = (80, 80, 80)  # Темная рамка для недоступных
            else:
                border_color = (100, 100, 100)

            pygame.draw.rect(self.screen, border_color, (slot_x, slots_y, slot_size, slot_size), 2)

            # Номер слота
            key_text = self.info_font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(key_text, (slot_x + 4, slots_y + 4))

            # Если есть умение, показываем его
            if skill:
                # Иконка умения (первая буква названия)
                icon_font = pygame.font.Font(None, 32)
                icon_text = icon_font.render(skill.name[0], True, (255, 255, 255))
                icon_rect = icon_text.get_rect()
                icon_rect.center = (slot_x + slot_size // 2, slots_y + slot_size // 2 + 4)
                self.screen.blit(icon_text, icon_rect)

                # Перезарядка (если есть)
                if skill.current_cooldown > 0:
                    cooldown_text = self.info_font.render(str(skill.current_cooldown), True, (255, 100, 100))
                    cooldown_rect = cooldown_text.get_rect()
                    cooldown_rect.center = (slot_x + slot_size // 2, slots_y + slot_size // 2)
                    self.screen.blit(cooldown_text, cooldown_rect)

        # Подсказка внизу
        hint_y = combat_y + combat_height - 35
        hint_text = self.info_font.render(
            "Клавиши 1-8 - использовать умение | ESC - сбежать",
            True,
            (180, 180, 200)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = combat_x + combat_width // 2
        hint_rect.y = hint_y
        self.screen.blit(hint_text, hint_rect)

    def _render_character_stats(self, character, x, y, label, is_player):
        """
        Отрисовка компактной статистики персонажа

        Args:
            character: Персонаж
            x: Позиция X
            y: Позиция Y
            label: Название (Игрок/Противник)
            is_player: True если это игрок
        """
        # Фон панели статистики (компактный)
        panel_width = 320
        panel_height = 160  # Уменьшено с 190 до 160
        pygame.draw.rect(
            self.screen,
            (45, 45, 60),
            (x - 10, y - 10, panel_width, panel_height)
        )

        # Рамка панели
        border_color = (100, 200, 100) if is_player else (200, 100, 100)
        pygame.draw.rect(
            self.screen,
            border_color,
            (x - 10, y - 10, panel_width, panel_height),
            3
        )

        # Имя и иконка
        icon = "🛡" if is_player else "⚔"
        name_text = self.info_font.render(f"{icon} {label}: {character.name}", True, (255, 255, 255))
        self.screen.blit(name_text, (x, y))

        # Уровень и ранг
        rank = character.get_rank() if hasattr(character, 'get_rank') else ""
        level_text = self.info_font.render(
            f"Ур. {character.level} ({rank})",
            True,
            (255, 215, 0)
        )
        self.screen.blit(level_text, (x, y + 24))

        # Здоровье с процентами (используем эффективное максимальное здоровье с учетом экипировки)
        effective_max_health = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
        health_percent = (character.health / effective_max_health) * 100 if effective_max_health > 0 else 0
        health_color = (255, 100, 100) if health_percent < 30 else (255, 165, 0) if health_percent < 60 else (100, 255, 100)

        health_text = self.info_font.render(
            f"❤ {character.health}/{effective_max_health} ({health_percent:.0f}%)",
            True,
            health_color
        )
        self.screen.blit(health_text, (x, y + 48))

        # Улучшенная полоса здоровья с градиентом (компактнее)
        bar_width = 280
        bar_height = 18  # Уменьшено с 20 до 18
        bar_x = x
        bar_y = y + 72

        # Фон полосы
        pygame.draw.rect(
            self.screen,
            (60, 60, 60),
            (bar_x, bar_y, bar_width, bar_height)
        )

        # Заполнение полосы здоровья
        fill_width = int(bar_width * (character.health / effective_max_health)) if effective_max_health > 0 else 0
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                health_color,
                (bar_x, bar_y, fill_width, bar_height)
            )

        # Рамка полосы
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (bar_x, bar_y, bar_width, bar_height),
            2
        )

        # Компактные характеристики
        stats_y = y + 100
        stats = [
            f"⚔ Урон: {character.get_total_damage()}",
            f"🛡 Защита: {character.get_total_defense()}",
            f"💨 Уворот: {character.calculate_dodge_chance():.1f}%",
            f"✨ Крит: {character.calculate_crit_chance():.1f}%"
        ]

        for i, stat in enumerate(stats):
            stat_text = self.info_font.render(stat, True, (200, 200, 220))
            # Размещаем в два столбца
            stat_x = x if i < 2 else x + 140
            stat_y_offset = stats_y + (i % 2) * 22  # Уменьшено с 25 до 22
            self.screen.blit(stat_text, (stat_x, stat_y_offset))
