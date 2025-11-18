"""
Система боя с пошаговым управлением
"""
import pygame
import random
from game.constants import COLORS


class CombatSystem:
    """Класс управления боевой системой"""

    def __init__(self, player, enemy, screen, font, scaler=None, game_map=None):
        """
        Инициализация боевой системы

        Args:
            player: Игрок
            enemy: Враг
            screen: Pygame экран
            font: Шрифт для отображения текста
            scaler: UIScaler для адаптивного масштабирования (опционально)
            game_map: Карта игры (для размещения лута)
        """
        self.player = player
        self.enemy = enemy
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.game_map = game_map
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
        Обработка ввода игрока

        Args:
            event: Pygame событие

        Returns:
            str: Результат боя ("continue", "victory", "defeat", "fled")
        """
        if event.type != pygame.KEYDOWN:
            return "continue"

        if self.turn != "player":
            return "continue"

        # Обработка выбора действия
        for action in self.actions:
            if event.key == getattr(pygame, f"K_{action['key']}"):
                return self.execute_player_action(action['action'])

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

                    # Оставляем лут на тайле (если есть карта и у врага есть предметы)
                    if self.game_map and hasattr(self.enemy, 'inventory'):
                        if len(self.enemy.inventory.items) > 0 or self.enemy.inventory.gold > 0:
                            tile = self.game_map.get_tile(self.enemy.x, self.enemy.y)
                            if tile:
                                tile.set_loot(self.enemy.inventory)
                                self.add_to_log(f"На земле остался лут!")

                    # Даем опыт за победу
                    exp_gained = self.enemy.level * 20
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

    def execute_enemy_turn(self):
        """
        Выполнить ход врага

        Returns:
            str: Результат боя
        """
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
            combat_width = self.scaler.scale_width(1000)
            combat_height = self.scaler.scale_height(700)
        else:
            combat_width = min(1000, int(screen_width * 0.85))
            combat_height = min(700, int(screen_height * 0.75))

        combat_x = (screen_width - combat_width) // 2
        combat_y = (screen_height - combat_height) // 2

        # Коэффициенты масштабирования
        scale_w = combat_width / 1000
        scale_h = combat_height / 700

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

        # Отрисовка статистики игрока (слева)
        self._render_character_stats(
            self.player,
            combat_x + 30,
            combat_y + 70,
            "Игрок",
            True
        )

        # Отрисовка статистики врага (справа)
        self._render_character_stats(
            self.enemy,
            combat_x + combat_width - 350,
            combat_y + 70,
            "Противник",
            False
        )

        # ОТДЕЛЬНЫЙ БЛОК ЛОГА БОЯ (центр экрана)
        log_block_x = combat_x + 30
        log_block_y = combat_y + 280
        log_block_width = combat_width - 60
        log_block_height = 280

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
        log_title = self.font.render("📜 Журнал боевых действий", True, (150, 200, 255))
        self.screen.blit(log_title, (log_block_x + 15, log_block_y + 10))

        # Линия под заголовком лога
        pygame.draw.line(
            self.screen,
            (80, 80, 120),
            (log_block_x + 10, log_block_y + 40),
            (log_block_x + log_block_width - 10, log_block_y + 40),
            1
        )

        # Отрисовка логов с прокруткой
        log_line_height = 24
        max_visible_logs = 9
        log_start_y = log_block_y + 50

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

        # Действия игрока
        actions_y = combat_y + combat_height - 80
        if self.turn == "player":
            actions_title = self.font.render("⚡ Ваш ход! Выберите действие:", True, (100, 255, 100))
        else:
            actions_title = self.font.render("⏳ Ход противника...", True, (255, 150, 150))

        self.screen.blit(actions_title, (combat_x + 30, actions_y))

        # Отрисовка кнопок действий с рамками
        if self.turn == "player":
            for i, action in enumerate(self.actions):
                action_x = combat_x + 30 + i * 280
                action_y = actions_y + 35

                # Фон кнопки
                pygame.draw.rect(
                    self.screen,
                    (50, 70, 50),
                    (action_x, action_y, 250, 35)
                )

                # Рамка кнопки
                pygame.draw.rect(
                    self.screen,
                    (100, 200, 100),
                    (action_x, action_y, 250, 35),
                    2
                )

                action_text = self.info_font.render(
                    f"[{action['key']}] {action['name']}",
                    True,
                    (200, 255, 200)
                )
                self.screen.blit(action_text, (action_x + 10, action_y + 8))

    def _render_character_stats(self, character, x, y, label, is_player):
        """
        Отрисовка улучшенной статистики персонажа

        Args:
            character: Персонаж
            x: Позиция X
            y: Позиция Y
            label: Название (Игрок/Противник)
            is_player: True если это игрок
        """
        # Фон панели статистики
        panel_width = 320
        panel_height = 190
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
        name_text = self.font.render(f"{icon} {label}: {character.name}", True, (255, 255, 255))
        self.screen.blit(name_text, (x, y))

        # Уровень и ранг
        rank = character.get_rank() if hasattr(character, 'get_rank') else ""
        level_text = self.info_font.render(
            f"Уровень: {character.level} ({rank})",
            True,
            (255, 215, 0)
        )
        self.screen.blit(level_text, (x, y + 30))

        # Здоровье с процентами
        health_percent = (character.health / character.max_health) * 100
        health_color = (255, 100, 100) if health_percent < 30 else (255, 165, 0) if health_percent < 60 else (100, 255, 100)

        health_text = self.info_font.render(
            f"❤ HP: {character.health}/{character.max_health} ({health_percent:.0f}%)",
            True,
            health_color
        )
        self.screen.blit(health_text, (x, y + 55))

        # Улучшенная полоса здоровья с градиентом
        bar_width = 280
        bar_height = 20
        bar_x = x
        bar_y = y + 80

        # Фон полосы
        pygame.draw.rect(
            self.screen,
            (60, 60, 60),
            (bar_x, bar_y, bar_width, bar_height)
        )

        # Заполнение полосы здоровья
        fill_width = int(bar_width * (character.health / character.max_health))
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

        # Расширенные характеристики
        stats_y = y + 110
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
            stat_y_offset = stats_y + (i % 2) * 25
            self.screen.blit(stat_text, (stat_x, stat_y_offset))
