"""
Система боя с пошаговым управлением
"""
import pygame
import random
from game.constants import WINDOW_WIDTH, WINDOW_HEIGHT, COLORS


class CombatSystem:
    """Класс управления боевой системой"""

    def __init__(self, player, enemy, screen, font):
        """
        Инициализация боевой системы

        Args:
            player: Игрок
            enemy: Враг
            screen: Pygame экран
            font: Шрифт для отображения текста
        """
        self.player = player
        self.enemy = enemy
        self.screen = screen
        self.font = font
        self.info_font = pygame.font.Font(None, 20)

        # Состояние боя
        self.active = True
        self.turn = "player"  # player или enemy
        self.combat_log = []  # Лог боевых событий
        self.max_log_entries = 5

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
                self.add_to_log(f"Вы атакуете {self.enemy.name} и наносите {attack_result['damage']} урона!{crit_msg}")

                if not self.enemy.is_alive:
                    self.add_to_log(f"Вы победили {self.enemy.name}!")

                    # Увеличиваем счетчик убитых врагов
                    if hasattr(self.player, 'enemies_killed'):
                        self.player.enemies_killed += 1

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
            self.add_to_log(f"{self.enemy.name} атакует вас и наносит {attack_result['damage']} урона!{crit_msg}")

            if not self.player.is_alive:
                self.add_to_log("Вы погибли!")
                return "defeat"

        # Возвращаем ход игроку
        self.turn = "player"
        return "continue"

    def render(self):
        """Отрисовка окна боя"""
        # Затемняем фон
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна боя
        combat_width = 800
        combat_height = 500
        combat_x = (WINDOW_WIDTH - combat_width) // 2
        combat_y = (WINDOW_HEIGHT - combat_height) // 2

        # Фон окна боя
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (combat_x, combat_y, combat_width, combat_height)
        )

        # Рамка окна боя
        pygame.draw.rect(
            self.screen,
            COLORS['text'],
            (combat_x, combat_y, combat_width, combat_height),
            3
        )

        # Заголовок
        title_text = self.font.render("БОЙ", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = combat_x + combat_width // 2
        title_rect.y = combat_y + 10
        self.screen.blit(title_text, title_rect)

        # Разделительная линия после заголовка
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (combat_x + 10, combat_y + 40),
            (combat_x + combat_width - 10, combat_y + 40),
            2
        )

        # Отрисовка статистики игрока (слева)
        self._render_character_stats(
            self.player,
            combat_x + 20,
            combat_y + 60,
            "Игрок"
        )

        # Отрисовка статистики врага (справа)
        self._render_character_stats(
            self.enemy,
            combat_x + combat_width - 320,
            combat_y + 60,
            "Противник"
        )

        # Лог боя
        log_y = combat_y + 200
        log_title = self.font.render("Журнал боя:", True, COLORS['text'])
        self.screen.blit(log_title, (combat_x + 20, log_y))

        for i, log_entry in enumerate(self.combat_log):
            log_text = self.info_font.render(log_entry, True, (200, 200, 200))
            self.screen.blit(log_text, (combat_x + 30, log_y + 30 + i * 25))

        # Действия игрока
        actions_y = combat_y + combat_height - 80
        if self.turn == "player":
            actions_title = self.font.render("Ваш ход! Выберите действие:", True, (255, 215, 0))
        else:
            actions_title = self.font.render("Ход противника...", True, (255, 100, 100))

        self.screen.blit(actions_title, (combat_x + 20, actions_y))

        # Отрисовка кнопок действий
        if self.turn == "player":
            for i, action in enumerate(self.actions):
                action_x = combat_x + 20 + i * 250
                action_text = self.info_font.render(
                    f"[{action['key']}] {action['name']}",
                    True,
                    (150, 255, 150)
                )
                self.screen.blit(action_text, (action_x, actions_y + 30))

    def _render_character_stats(self, character, x, y, label):
        """
        Отрисовка статистики персонажа

        Args:
            character: Персонаж
            x: Позиция X
            y: Позиция Y
            label: Название (Игрок/Противник)
        """
        # Имя
        name_text = self.font.render(f"{label}: {character.name}", True, COLORS['text'])
        self.screen.blit(name_text, (x, y))

        # Уровень
        level_text = self.info_font.render(
            f"Уровень: {character.level}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(level_text, (x, y + 30))

        # Здоровье
        health_percent = (character.health / character.max_health) * 100
        health_color = (255, 100, 100) if health_percent < 30 else (255, 165, 0) if health_percent < 60 else (100, 255, 100)

        health_text = self.info_font.render(
            f"HP: {character.health}/{character.max_health}",
            True,
            health_color
        )
        self.screen.blit(health_text, (x, y + 55))

        # Полоса здоровья
        bar_width = 200
        bar_height = 15
        bar_x = x
        bar_y = y + 80

        # Фон полосы
        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
            (bar_x, bar_y, bar_width, bar_height)
        )

        # Заполнение полосы здоровья
        fill_width = int(bar_width * (character.health / character.max_health))
        pygame.draw.rect(
            self.screen,
            health_color,
            (bar_x, bar_y, fill_width, bar_height)
        )

        # Рамка полосы
        pygame.draw.rect(
            self.screen,
            COLORS['text'],
            (bar_x, bar_y, bar_width, bar_height),
            2
        )

        # Характеристики
        stats_y = y + 105
        stats = [
            f"Сила: {character.strength}",
            f"Ловкость: {character.dexterity}",
            f"Удача: {character.luck}"
        ]

        for i, stat in enumerate(stats):
            stat_text = self.info_font.render(stat, True, (180, 180, 180))
            self.screen.blit(stat_text, (x, stats_y + i * 20))
