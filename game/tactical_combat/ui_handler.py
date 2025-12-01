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
        self.selected_action = None  # move, skill, potion, pass (оставлено для совместимости)

        # Новая система управления
        self.selected_target_unit = None  # Выбранная цель (юнит)

    def handle_input(self, event):
        """
        Обработка события ввода
        Новая система управления:
        - ЛКМ на поле: перемещение (если цель не выбрана) или применение умения (если цель выбрана)
        - ПКМ на юните: выбор/снятие цели
        - ЛКМ на панели умений: применение умения к выбранной цели

        Args:
            event: Pygame событие

        Returns:
            str: Результат боя ("continue", "victory", "defeat", "fled")
        """
        if self.combat.current_turn != "player":
            return "continue"

        if event.type == pygame.KEYDOWN:
            # ESC - попытка сбежать или снять выбор цели
            if event.key == pygame.K_ESCAPE:
                if self.selected_target_unit:
                    self.selected_target_unit = None
                    self.combat.add_to_log("Цель снята")
                    return "continue"
                else:
                    return self._attempt_flee()

        # Обработка мыши
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # ЛКМ - перемещение или клик по умению
            if event.button == 1:
                # Проверяем клик по панели умений
                if hasattr(self.renderer, 'skill_buttons'):
                    for slot_rect, slot_index, skill, is_usable in self.renderer.skill_buttons:
                        if slot_rect.collidepoint(mouse_x, mouse_y) and skill and is_usable:
                            return self._handle_skill_use(skill, slot_index)

                # Если цель не выбрана - перемещение
                if not self.selected_target_unit:
                    return self._handle_movement_click(mouse_x, mouse_y)

            # ПКМ - выбор/снятие цели
            elif event.button == 3:
                return self._handle_target_selection(mouse_x, mouse_y)

        return "continue"

    def _handle_movement_click(self, mouse_x, mouse_y):
        """
        Обработка клика для перемещения

        Args:
            mouse_x, mouse_y: Координаты клика

        Returns:
            str: Результат боя
        """
        # Вычисляем клетку по координатам мыши
        screen_width = self.renderer.screen.get_width()
        field_width = self.combat.battlefield_width * self.combat.cell_size
        field_x = (screen_width - field_width) // 2
        field_y = 100

        cell_x = (mouse_x - field_x) // self.combat.cell_size
        cell_y = (mouse_y - field_y) // self.combat.cell_size

        # Пытаемся переместить юнита
        if self.combat.move_unit(self.combat.player_unit, cell_x, cell_y):
            # Заканчиваем ход после перемещения
            return self.combat.end_turn()
        else:
            self.combat.add_to_log("Невозможно переместиться (только в соседние 8 клеток)")

        return "continue"

    def _handle_target_selection(self, mouse_x, mouse_y):
        """
        Обработка ПКМ для выбора цели

        Args:
            mouse_x, mouse_y: Координаты клика

        Returns:
            str: Результат боя
        """
        # Вычисляем клетку по координатам мыши
        screen_width = self.renderer.screen.get_width()
        field_width = self.combat.battlefield_width * self.combat.cell_size
        field_x = (screen_width - field_width) // 2
        field_y = 100

        cell_x = (mouse_x - field_x) // self.combat.cell_size
        cell_y = (mouse_y - field_y) // self.combat.cell_size

        # Проверяем, кликнули ли на врага
        if cell_x == self.combat.enemy_unit.x and cell_y == self.combat.enemy_unit.y:
            if self.selected_target_unit == self.combat.enemy_unit:
                # Снимаем выбор
                self.selected_target_unit = None
                self.combat.add_to_log("Цель снята")
            else:
                # Выбираем цель
                self.selected_target_unit = self.combat.enemy_unit
                self.combat.add_to_log(f"Цель выбрана: {self.combat.enemy.name}")

        return "continue"

    def _handle_skill_use(self, skill, slot_index):
        """
        Обработка использования умения

        Args:
            skill: Объект умения
            slot_index: Индекс слота умения

        Returns:
            str: Результат боя
        """
        from game.skills import SkillCategory

        # Проверяем, является ли умение боевым или магическим
        if skill.category not in [SkillCategory.COMBAT, SkillCategory.MAGIC]:
            self.combat.add_to_log(f"{skill.name} нельзя использовать в бою!")
            return "continue"

        # Определяем цель умения
        target_unit = None

        # Лечебные умения применяются на себя
        if skill.skill_id in ['heal', 'regeneration', 'stamina_recovery', 'mage_shield']:
            target_unit = self.combat.player_unit
        else:
            # Боевые умения требуют выбранной цели
            if not self.selected_target_unit:
                self.combat.add_to_log(f"Выберите цель для {skill.name} (ПКМ)")
                return "continue"

            target_unit = self.selected_target_unit

            # Проверяем дистанцию до цели
            targets = self.combat.get_skill_targets(skill, self.combat.player_unit)
            if target_unit not in targets:
                self.combat.add_to_log(f"Цель вне радиуса действия {skill.name}")
                return "continue"

        # Используем умение
        result = self.combat.use_skill(skill, self.combat.player_unit, target_unit)

        # Снимаем выбор цели после использования умения
        self.selected_target_unit = None

        if result['status'] == 'victory':
            return self._handle_victory()

        # Заканчиваем ход после использования умения
        return self.combat.end_turn()

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
