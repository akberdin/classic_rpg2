"""
Обработка пользовательского ввода для тактического боя
"""
import pygame


class TacticalCombatUIHandler:
    """Обработчик пользовательского ввода для тактического боя"""

    def __init__(self, combat_system, renderer):
        """
        Инициализация обработчика

        Args:
            combat_system: Система тактического боя
            renderer: Рендерер тактического боя
        """
        self.combat = combat_system
        self.renderer = renderer
        self.selected_action = None  # move, skill, potion, pass

    def handle_input(self, event):
        """
        Обработка события ввода

        Args:
            event: Pygame событие

        Returns:
            str: Результат боя ("continue", "victory", "defeat", "fled")
        """
        if self.combat.current_turn != "player":
            return "continue"

        if event.type == pygame.KEYDOWN:
            # ESC - попытка сбежать
            if event.key == pygame.K_ESCAPE:
                return self._attempt_flee()

            # Выбор действия
            if event.key == pygame.K_1:
                self.selected_action = "move"
                self.combat.add_to_log("Выберите клетку для перемещения")
                return "continue"

            elif event.key == pygame.K_2:
                self.selected_action = "skill"
                self.combat.add_to_log("Нажмите клавишу умения (1-8)")
                return "continue"

            elif event.key == pygame.K_3:
                self.selected_action = "potion"
                self.combat.add_to_log("Использование зелий пока недоступно")
                self.selected_action = None
                return "continue"

            elif event.key == pygame.K_4:
                # Пропустить ход
                self.combat.add_to_log("Вы пропускаете ход")
                return self.combat.end_turn()

            # Использование умения, если выбрано действие "skill"
            if self.selected_action == "skill":
                skill = None
                slot_index = None

                # Определяем слот умения
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                    slot_index = event.key - pygame.K_1  # 0-7

                if slot_index is not None:
                    skill = self.combat.player.skill_manager.get_slot_skill(slot_index)

                    if skill:
                        # Проверяем, является ли умение боевым или магическим
                        from game.skills import SkillCategory
                        if skill.category in [SkillCategory.COMBAT, SkillCategory.MAGIC]:
                            # Получаем возможные цели
                            targets = self.combat.get_skill_targets(skill, self.combat.player_unit)

                            if targets:
                                target = targets[0]
                                result = self.combat.use_skill(skill, self.combat.player_unit, target)

                                self.selected_action = None

                                if result['status'] == 'victory':
                                    return self._handle_victory()

                                # Заканчиваем ход после использования умения
                                return self.combat.end_turn()
                            else:
                                self.combat.add_to_log(f"Цель вне радиуса действия {skill.name}")
                        else:
                            self.combat.add_to_log(f"{skill.name} нельзя использовать в бою!")
                    else:
                        self.combat.add_to_log(f"Слот {slot_index + 1} пуст!")

                    self.selected_action = None

        # Обработка мыши для перемещения
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.selected_action == "move":
                # Вычисляем клетку по координатам мыши
                screen_width = self.renderer.screen.get_width()
                field_width = self.combat.battlefield_width * self.combat.cell_size
                field_x = (screen_width - field_width) // 2
                field_y = 100

                mouse_x, mouse_y = event.pos
                cell_x = (mouse_x - field_x) // self.combat.cell_size
                cell_y = (mouse_y - field_y) // self.combat.cell_size

                # Пытаемся переместить юнита
                if self.combat.move_unit(self.combat.player_unit, cell_x, cell_y):
                    self.selected_action = None
                    # Заканчиваем ход после перемещения
                    return self.combat.end_turn()
                else:
                    self.combat.add_to_log("Невозможно переместиться в эту клетку")

        return "continue"

    def _attempt_flee(self):
        """
        Попытка сбежать из боя

        Returns:
            str: Результат попытки
        """
        import random

        if random.random() < 0.5:
            self.combat.add_to_log("Вы успешно сбежали из боя!")
            return "fled"
        else:
            self.combat.add_to_log("Не удалось сбежать!")
            return self.combat.end_turn()

    def _handle_victory(self):
        """
        Обработка победы

        Returns:
            str: "victory"
        """
        from game.combat import calculate_combat_exp

        self.combat.add_to_log(f"Вы победили {self.combat.enemy.name}!")

        # Увеличиваем счетчик убитых врагов
        if hasattr(self.combat.player, 'enemies_killed'):
            self.combat.player.enemies_killed += 1

        # Регистрируем смерть NPC для респавна
        if self.combat.respawn_manager:
            self.combat.respawn_manager.register_death(self.combat.enemy, self.combat.game)

        # Оставляем лут на тайле (если есть карта и у врага есть предметы)
        if self.combat.game_map and hasattr(self.combat.enemy, 'inventory'):
            if len(self.combat.enemy.inventory.items) > 0 or self.combat.enemy.inventory.gold > 0:
                tile = self.combat.game_map.get_tile(self.combat.enemy.x, self.combat.enemy.y)
                if tile:
                    tile.set_loot(self.combat.enemy.inventory)
                    self.combat.add_to_log("На земле остался лут!")

        # Даем опыт за победу (с учётом разницы уровней)
        exp_gained = calculate_combat_exp(self.combat.player.level, self.combat.enemy.level)
        self.combat.player.add_experience(exp_gained)
        self.combat.add_to_log(f"Получено {exp_gained} опыта!")

        return "victory"
