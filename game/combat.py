"""
Система боя с пошаговым управлением.

Отвечает только за боевую логику:
- Обработка ввода игрока
- Выполнение атак и умений
- Управление ходами
- Обработка статус-эффектов

Рендеринг вынесен в combat_renderer.py (CombatRenderer).
"""
import pygame
import random

from game.combat_renderer import CombatRenderer


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

    if level_diff > 0:
        bonus = min(1.0, level_diff * 0.1)
        exp = int(base_exp * (1 + bonus))
    elif level_diff < 0:
        penalty = min(0.9, abs(level_diff) * 0.05)
        exp = int(base_exp * (1 - penalty))
    else:
        exp = base_exp

    return max(int(base_exp * 0.1), exp)


class CombatSystem:
    """Класс управления боевой системой"""

    def __init__(self, player, enemy, screen, font, scaler=None, game_map=None,
                 respawn_manager=None, sprite_manager=None, game=None):
        """
        Инициализация боевой системы

        Args:
            player: Игрок
            enemy: Враг
            screen: Pygame экран
            font: Шрифт для отображения текста
            scaler: UIScaler для адаптивного масштабирования
            game_map: Карта игры (для размещения лута)
            respawn_manager: Менеджер респавна NPC
            sprite_manager: Менеджер спрайтов для иконок умений
            game: Объект игры (для удаления мертвых NPC)
        """
        self.player = player
        self.enemy = enemy
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.game_map = game_map
        self.respawn_manager = respawn_manager
        self.sprite_manager = sprite_manager
        self.game = game

        # Создаём рендерер для UI
        self.renderer = CombatRenderer(screen, font, scaler, sprite_manager)

        # Состояние боя
        self.active = True
        self.turn = "player"
        self.combat_log = []
        self.max_log_entries = 15

        # Действия игрока
        self.actions = [
            {"name": "Атака", "key": "1", "action": "attack"},
            {"name": "Убежать", "key": "2", "action": "flee"}
        ]
        self.selected_action = None
        self.hovered_action = None

        # Начальные сообщения в лог
        self._init_combat_log()

    def _init_combat_log(self):
        """Инициализация лога боя с информацией о противниках"""
        self.add_to_log(f"═══ БОЙ НАЧАЛСЯ! ═══")
        self.add_to_log(f"Противник: {self.enemy.name} (Уровень {self.enemy.level})")

        enemy_dodge = self.enemy.calculate_dodge_chance()
        enemy_crit = self.enemy.calculate_crit_chance()
        enemy_dmg = self.enemy.get_total_damage()
        enemy_def = self.enemy.get_total_defense()
        enemy_mag_def = self.enemy.get_magic_defense()
        self.add_to_log(f"  [Урон: {enemy_dmg}, Защита: {enemy_def}, Маг. защита: {enemy_mag_def}]")
        self.add_to_log(f"  [Уворот: {enemy_dodge:.1f}%, Крит: {enemy_crit:.1f}%]")

        player_dodge = self.player.calculate_dodge_chance()
        player_crit = self.player.calculate_crit_chance()
        player_dmg = self.player.get_total_damage()
        player_def = self.player.get_total_defense()
        self.add_to_log(f"Ваши статы: Урон {player_dmg}, Защита {player_def}")
        self.add_to_log(f"  [Уворот: {player_dodge:.1f}%, Крит: {player_crit:.1f}%]")

    def add_to_log(self, message):
        """Добавить сообщение в лог боя"""
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
        if self.turn != "player":
            return "continue"

        # Проверяем оглушение игрока
        if hasattr(self.player, 'stunned') and self.player.stunned:
            if event.type == pygame.KEYDOWN:
                self.add_to_log(f"Вы оглушены и пропускаете ход!")
                self.player.stunned = False
                self.turn = "enemy"
                return self.execute_enemy_turn()
            return "continue"

        # Обработка клавиатуры
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self.execute_player_action("flee")

            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                slot_index = event.key - pygame.K_1
                skill = self.player.skill_manager.get_slot_skill(slot_index)

                if skill:
                    from game.skills import SkillCategory
                    combat_categories = [SkillCategory.GENERAL]
                    if skill.category in combat_categories:
                        return self.execute_skill_action(skill)
                    else:
                        self.add_to_log(f"{skill.name} нельзя использовать в бою!")
                else:
                    self.add_to_log(f"Слот {slot_index + 1} пуст!")

                return "continue"

        # Обработка мыши (ПКМ для зелий)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            return self._handle_potion_click(event.pos)

        return "continue"

    def _handle_potion_click(self, mouse_pos):
        """Обработка клика по зелью"""
        mouse_x, mouse_y = mouse_pos

        for slot_rect, slot, potion in self.renderer.potion_buttons:
            if slot_rect.collidepoint(mouse_x, mouse_y):
                if potion:
                    result = potion.use(self.player)
                    self.add_to_log(result)
                    self.player.inventory.remove_item(potion, 1)
                    if self.player.inventory.get_item_count(potion) == 0:
                        self.player.inventory.unequip_item(slot)
                    return "continue"
                else:
                    self.add_to_log("Слот зелья пуст")
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
            attack_result = self.player.attack(self.enemy)
            self._log_attack_result(attack_result, is_player=True)

            if not self.enemy.is_alive:
                return self._handle_enemy_death()

            self.turn = "enemy"
            return self.execute_enemy_turn()

        elif action_type == "flee":
            if random.random() < 0.5:
                self.add_to_log("Вы успешно сбежали из боя!")
                return "fled"
            else:
                self.add_to_log("Не удалось сбежать!")
                self.turn = "enemy"
                return self.execute_enemy_turn()

        return "continue"

    def _log_attack_result(self, attack_result, is_player=True):
        """Логирование результата атаки"""
        attacker = self.player if is_player else self.enemy
        defender = self.enemy if is_player else self.player
        attacker_name = "Вы" if is_player else self.enemy.name

        if attack_result['dodged']:
            if is_player:
                dodge_msgs = [
                    f"{defender.name} ловко увернулся от вашего удара!",
                    f"Ваш удар прошел мимо - {defender.name} уклонился!",
                ]
            else:
                dodge_msgs = [
                    f"Вы ловко уворачиваетесь от атаки {attacker.name}!",
                    f"Атака {attacker.name} проходит мимо - вы уклонились!",
                ]
            self.add_to_log(random.choice(dodge_msgs))
            dodge_chance = defender.calculate_dodge_chance()
            self.add_to_log(f"  [Шанс уворота: {dodge_chance:.1f}%]")

        elif attack_result['hit']:
            if attack_result.get('godmode', False):
                self.add_to_log(f"{attacker.name} атакует вас, но ЧИТ-МОД блокирует весь урон!")
                return

            if attack_result['critical']:
                if is_player:
                    self.add_to_log(f"КРИТИЧЕСКИЙ УДАР! Вы наносите сокрушительный удар!")
                else:
                    self.add_to_log(f"КРИТИЧЕСКИЙ УДАР! {attacker.name} наносит мощнейший удар!")
                crit_chance = attacker.calculate_crit_chance()
                self.add_to_log(f"  [Урон: {attack_result['damage']}, шанс крита: {crit_chance:.1f}%]")
            else:
                if is_player:
                    self.add_to_log(f"Вы наносите удар по {defender.name}!")
                else:
                    self.add_to_log(f"{attacker.name} атакует вас!")
                self.add_to_log(f"  [Урон: {attack_result['damage']}]")

            if attack_result.get('armor_penetration_percent', 0) > 0:
                armor_pen = attack_result['armor_penetration_percent']
                self.add_to_log(f"  [Магическая атака игнорирует {armor_pen}% брони!]")

            if attack_result.get('blocked_by_armor', 0) > 0:
                armor_blocked = attack_result['blocked_by_armor']
                defender_def = defender.get_total_defense()
                self.add_to_log(f"  [Броня ({defender_def}) заблокировала {armor_blocked} урона]")

            if attack_result.get('stunned', False):
                if is_player:
                    self.add_to_log(f"  [{defender.name} ОГЛУШЁН!]")
                else:
                    self.add_to_log(f"  [ВЫ ОГЛУШЕНЫ! Пропускаете следующий ход!]")

    def _handle_enemy_death(self):
        """Обработка смерти противника"""
        self.add_to_log(f"Вы победили {self.enemy.name}!")

        if hasattr(self.player, 'enemies_killed'):
            self.player.enemies_killed += 1

        if self.respawn_manager:
            self.respawn_manager.register_death(self.enemy, self.game)

        if self.game_map and hasattr(self.enemy, 'inventory'):
            if len(self.enemy.inventory.items) > 0 or self.enemy.inventory.gold > 0:
                tile = self.game_map.get_tile(self.enemy.x, self.enemy.y)
                if tile:
                    tile.set_loot(self.enemy.inventory)
                    self.add_to_log(f"На земле остался лут!")

        exp_gained = calculate_combat_exp(self.player.level, self.enemy.level)
        self.player.add_experience(exp_gained)
        self.add_to_log(f"Получено {exp_gained} опыта!")

        return "victory"

    def execute_skill_action(self, skill):
        """Выполнить использование умения"""
        result = self.player.skill_manager.use_skill(skill, self.enemy)

        if result['success']:
            self.add_to_log(result['message'])

            if 'damage' in result and result.get('killed'):
                return self._handle_enemy_death()

            self.turn = "enemy"
            return self.execute_enemy_turn()
        else:
            self.add_to_log(result['message'])
            return "continue"

    def execute_enemy_turn(self):
        """Выполнить ход врага"""
        # Проверяем оглушение врага
        if hasattr(self.enemy, 'stunned') and self.enemy.stunned:
            self.add_to_log(f"{self.enemy.name} оглушен/заморожен и пропускает ход!")
            self._process_status_effects(self.enemy)
            self._end_enemy_turn()
            return "continue"

        # Обрабатываем статус-эффекты врага
        self._process_status_effects(self.enemy)

        if not self.enemy.is_alive:
            self.add_to_log(f"{self.enemy.name} погиб от эффектов!")
            return self._handle_enemy_death_from_effects()

        # Враг атакует
        attack_result = self.enemy.attack(self.player)
        self._log_attack_result(attack_result, is_player=False)

        if not self.player.is_alive:
            self.add_to_log("Вы погибли в бою...")
            return "defeat"

        self._end_enemy_turn()
        return "continue"

    def _process_status_effects(self, character):
        """Обработка статус-эффектов персонажа"""
        if hasattr(character, 'status_effects'):
            for effect in character.status_effects[:]:
                message = effect.tick(character)
                if message:
                    self.add_to_log(message)
                if effect.is_expired():
                    remove_msg = effect.remove(character)
                    if remove_msg:
                        self.add_to_log(remove_msg)
                    character.status_effects.remove(effect)

    def _handle_enemy_death_from_effects(self):
        """Обработка смерти врага от статус-эффектов"""
        if hasattr(self.player, 'enemies_killed'):
            self.player.enemies_killed += 1

        if self.respawn_manager:
            self.respawn_manager.register_death(self.enemy, self.game)

        exp_gained = calculate_combat_exp(self.player.level, self.enemy.level)
        self.player.add_experience(exp_gained)
        self.add_to_log(f"Получено {exp_gained} опыта!")

        return "victory"

    def _end_enemy_turn(self):
        """Завершение хода врага"""
        self.player.skill_manager.tick_cooldowns()

        if hasattr(self.player, 'skill_manager'):
            effect_messages = self.player.skill_manager.tick_status_effects()
            for msg in effect_messages:
                self.add_to_log(msg)

        self.turn = "player"

    def render(self):
        """Отрисовка окна боя через рендерер"""
        self.renderer.render(
            self.player,
            self.enemy,
            self.combat_log,
            self.turn,
            self.player.skill_manager
        )
