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

        # Связываем UI handler с системой боя для доступа из renderer
        self.combat._ui_handler = self

    def handle_input(self, event):
        """
        Обработка события ввода
        Новая система управления:
        - ЛКМ на поле: перемещение (если цель не выбрана) или применение умения (если цель выбрана)
        - ПКМ на юните: выбор/снятие цели
        - ЛКМ на панели умений: применение умения к выбранной цели
        - Tab: переключение между юнитами игрока (игрок и спутники)
        - ЛКМ на своем юните: выбрать этого юнита для управления

        Args:
            event: Pygame событие

        Returns:
            str: Результат боя ("continue", "victory", "defeat", "fled")
        """
        if self.combat.current_turn != "player":
            return "continue"

        # Проверяем, что активный юнит еще не сделал ход
        if self.combat.active_unit and self.combat.active_unit.has_acted:
            # Автоматически переключаемся на следующего юнита, который может ходить
            next_unit = self.combat.switch_to_next_unit()
            if not next_unit:
                # Все юниты сделали ход - это не должно произойти, но на всякий случай
                return self.combat.end_turn()

        # Восстанавливаем последнюю цель в начале хода, если она жива
        if not self.selected_target_unit and self.combat.last_selected_target:
            if self.combat.last_selected_target.character.is_alive:
                self.selected_target_unit = self.combat.last_selected_target

        if event.type == pygame.KEYDOWN:
            # Tab - переключение между юнитами игрока
            if event.key == pygame.K_TAB:
                # Shift+Tab - переключение в обратном направлении
                direction = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                self.combat.cycle_active_unit(direction)
                return "continue"

            # ESC - попытка сбежать или снять выбор цели
            if event.key == pygame.K_ESCAPE:
                if self.selected_target_unit:
                    self.selected_target_unit = None
                    self.combat.add_to_log("Цель снята")
                    return "continue"
                else:
                    return self._attempt_flee()

            # Клавиши 1-8 для быстрого использования умений активного юнита
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                              pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                # Определяем индекс слота (0-7)
                slot_index = event.key - pygame.K_1

                # Получаем активного персонажа и его умения
                active_char = self.combat.active_unit.character

                if hasattr(active_char, 'skill_manager') and active_char.skill_manager:
                    skill = active_char.skill_manager.get_slot_skill(slot_index)
                    if skill:
                        # Проверяем, можно ли использовать умение
                        can_use, reason = skill.can_use(active_char)
                        if can_use:
                            return self._handle_skill_use(skill, slot_index)
                        else:
                            self.combat.add_to_log(reason)
                    else:
                        self.combat.add_to_log(f"Слот {slot_index + 1} пуст")
                else:
                    self.combat.add_to_log(f"{active_char.name} не может использовать умения")
                return "continue"

        # Обработка мыши
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # ЛКМ - перемещение, выбор юнита, или клик по умению
            if event.button == 1:
                # Проверяем клик по панели умений
                if hasattr(self.renderer, 'skill_buttons'):
                    for slot_rect, slot_index, skill, is_usable in self.renderer.skill_buttons:
                        if slot_rect.collidepoint(mouse_x, mouse_y) and skill and is_usable:
                            return self._handle_skill_use(skill, slot_index)

                # Проверяем клик по панели переключения юнитов
                if hasattr(self.renderer, 'unit_switch_buttons'):
                    for btn_rect, unit in self.renderer.unit_switch_buttons:
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            if self.combat.switch_to_unit(unit):
                                return "continue"

                # Проверяем клик по своим юнитам на карте
                clicked_own_unit = self._get_clicked_player_unit(mouse_x, mouse_y)
                if clicked_own_unit:
                    if self.combat.switch_to_unit(clicked_own_unit):
                        return "continue"

                # Если цель не выбрана - перемещение
                if not self.selected_target_unit:
                    return self._handle_movement_click(mouse_x, mouse_y)

            # ПКМ - использование зелья или выбор/снятие цели
            elif event.button == 3:
                # Сначала проверяем клик по панели зелий
                if hasattr(self.renderer, 'potion_buttons'):
                    for slot_rect, slot, potion in self.renderer.potion_buttons:
                        if slot_rect.collidepoint(mouse_x, mouse_y):
                            if potion:
                                # Используем зелье
                                result = potion.use(self.combat.player)
                                self.combat.add_to_log(result)
                                # Удаляем зелье из инвентаря
                                self.combat.player.inventory.remove_item(potion, 1)
                                # Снимаем зелье из слота если его больше нет
                                if self.combat.player.inventory.get_item_count(potion) == 0:
                                    self.combat.player.inventory.unequip_item(slot)
                                # Зелье использовано - ход продолжается
                                return "continue"
                            else:
                                self.combat.add_to_log("Слот зелья пуст")
                                return "continue"

                # Если не кликнули по зельям - выбор цели
                return self._handle_target_selection(mouse_x, mouse_y)

        return "continue"

    def _get_clicked_player_unit(self, mouse_x, mouse_y):
        """
        Проверить, кликнули ли на юнита игрока (игрок или спутник)

        Args:
            mouse_x, mouse_y: Координаты клика

        Returns:
            BattlefieldUnit или None: Юнит под курсором
        """
        # Вычисляем клетку по координатам мыши
        field_x = 20
        field_y = 100

        cell_x = (mouse_x - field_x) // self.combat.cell_size
        cell_y = (mouse_y - field_y) // self.combat.cell_size

        # Проверяем клик по игроку
        if (self.combat.player.is_alive and
            cell_x == self.combat.player_unit.x and
            cell_y == self.combat.player_unit.y):
            return self.combat.player_unit

        # Проверяем клик по спутникам
        for companion_unit in self.combat.companion_units:
            if (companion_unit.character.is_alive and
                cell_x == companion_unit.x and
                cell_y == companion_unit.y):
                return companion_unit

        return None

    def _handle_movement_click(self, mouse_x, mouse_y):
        """
        Обработка клика для перемещения активного юнита

        Args:
            mouse_x, mouse_y: Координаты клика

        Returns:
            str: Результат боя
        """
        # Вычисляем клетку по координатам мыши
        # Используем те же координаты что и в renderer
        field_x = 20
        field_y = 100

        cell_x = (mouse_x - field_x) // self.combat.cell_size
        cell_y = (mouse_y - field_y) // self.combat.cell_size

        # Получаем активного юнита
        active_unit = self.combat.active_unit

        # Пытаемся переместить активного юнита
        if self.combat.move_unit(active_unit, cell_x, cell_y):
            # Заканчиваем ход юнита после перемещения
            return self.combat.end_turn()
        else:
            unit_name = active_unit.character.name if active_unit != self.combat.player_unit else "Игрок"
            self.combat.add_to_log(f"Невозможно переместиться (только в соседние 8 клеток)")

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
        # Используем те же координаты что и в renderer
        field_x = 20
        field_y = 100

        cell_x = (mouse_x - field_x) // self.combat.cell_size
        cell_y = (mouse_y - field_y) // self.combat.cell_size

        # Проверяем, кликнули ли на какого-либо врага
        clicked_enemy = None
        for enemy_unit in self.combat.enemy_units:
            if enemy_unit.character.is_alive and cell_x == enemy_unit.x and cell_y == enemy_unit.y:
                clicked_enemy = enemy_unit
                break

        if clicked_enemy:
            if self.selected_target_unit == clicked_enemy:
                # Снимаем выбор
                self.selected_target_unit = None
                self.combat.last_selected_target = None
                self.combat.add_to_log("Цель снята")
            else:
                # Выбираем цель
                self.selected_target_unit = clicked_enemy
                self.combat.last_selected_target = clicked_enemy
                self.combat.add_to_log(f"Цель выбрана: {clicked_enemy.character.name}")

        return "continue"

    def _handle_skill_use(self, skill, slot_index):
        """
        Обработка использования умения активным юнитом

        Args:
            skill: Объект умения
            slot_index: Индекс слота умения

        Returns:
            str: Результат боя
        """
        from game.skills import SkillCategory

        # Получаем активного юнита и персонажа
        active_unit = self.combat.active_unit
        active_char = active_unit.character

        # Проверяем, является ли умение боевым (все кроме ремесленных)
        combat_categories = [
            SkillCategory.COMBAT, SkillCategory.MAGIC,
            SkillCategory.SHADOW, SkillCategory.WARRIOR,
            SkillCategory.HUNTER, SkillCategory.MAGE, SkillCategory.GENERAL
        ]
        if skill.category not in combat_categories:
            self.combat.add_to_log(f"{skill.name} нельзя использовать в бою!")
            return "continue"

        # Определяем цель умения
        target_unit = None

        # Получаем ID умения через SkillManager персонажа
        skill_id = None
        if hasattr(active_char, 'skill_manager') and active_char.skill_manager:
            skill_id = active_char.skill_manager.get_skill_id(skill)

        # Лечебные/поддерживающие умения применяются на себя
        support_skills = ['heal', 'regeneration', 'stamina_recovery', 'mage_shield', 'wolf_howl']
        if skill_id in support_skills:
            target_unit = active_unit
            unit_name = active_char.name if active_unit != self.combat.player_unit else "Вы"
            self.combat.add_to_log(f"{unit_name} применяет {skill.name}")
        else:
            # Боевые умения требуют выбранной цели
            if not self.selected_target_unit:
                self.combat.add_to_log(f"Выберите цель для {skill.name} (ПКМ)")
                return "continue"

            target_unit = self.selected_target_unit

            # Проверяем дистанцию до цели
            targets = self.combat.get_skill_targets(skill, active_unit)
            if target_unit not in targets:
                self.combat.add_to_log(f"Цель вне радиуса действия {skill.name}")
                return "continue"

        # Используем умение
        result = self.combat.use_skill(skill, active_unit, target_unit)

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

        self.combat.add_to_log(f"=== ПОБЕДА ===")

        # Обрабатываем всех побежденных врагов
        total_exp = 0
        enemies_killed = 0

        for enemy in self.combat.enemies:
            # Пропускаем живых врагов - обрабатываем только мертвых
            if enemy.is_alive:
                continue

            # Увеличиваем счетчик убитых врагов
            enemies_killed += 1

            # Регистрируем смерть NPC для респавна
            if self.combat.respawn_manager:
                self.combat.respawn_manager.register_death(enemy, self.combat.game)

            # Оставляем лут на тайле (если есть карта и у врага есть предметы)
            if self.combat.game_map and hasattr(enemy, 'inventory'):
                if len(enemy.inventory.items) > 0 or enemy.inventory.gold > 0:
                    # Используем позицию игрока, чтобы лут был рядом после боя
                    tile = self.combat.game_map.get_tile(self.combat.player.x, self.combat.player.y)
                    if tile:
                        tile.set_loot(enemy.inventory)
                        self.combat.add_to_log(f"Лут от {enemy.name}: Золото: {enemy.inventory.gold}, предметов: {len(enemy.inventory.items)}")

            # Рассчитываем опыт за этого врага
            exp_for_enemy = calculate_combat_exp(self.combat.player.level, enemy.level)
            total_exp += exp_for_enemy

            self.combat.add_to_log(f"За {enemy.name}: +{exp_for_enemy} опыта")

        # Обновляем счетчик убитых врагов
        if hasattr(self.combat.player, 'enemies_killed'):
            self.combat.player.enemies_killed += enemies_killed

        # Даем общий опыт за победу
        if total_exp > 0:
            self.combat.player.add_experience(total_exp)
            self.combat.add_to_log(f"Всего получено: {total_exp} опыта!")

            # Даем опыт спутникам (30% от общего)
            companion_exp = int(total_exp * 0.3)
            if companion_exp > 0:
                for companion_unit in self.combat.companion_units:
                    if companion_unit.character.is_alive and hasattr(companion_unit.character, 'add_experience'):
                        companion_unit.character.add_experience(companion_exp)
                        self.combat.add_to_log(f"{companion_unit.character.name}: +{companion_exp} опыта")

        return "victory"
