"""
Модуль для обработки пользовательского ввода
"""
import pygame
from game.inventory import EquipmentItem, EquipmentSlot, SkillBookItem
from game.save_system import SaveSystem
from game.constants import LOCATION_CITY, LOCATION_VILLAGE
from game.core.game_context import GameContext


class InputHandler:
    """Класс для обработки пользовательского ввода"""

    def __init__(self, game):
        """
        Инициализация обработчика ввода

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game  # Сохраняем для обратной совместимости
        self.ctx = GameContext(game)  # Контекст для доступа к данным

    def handle_inventory_input(self, key):
        """
        Обработка ввода в меню инвентаря

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_i:
            self.ctx.inventory_menu_open = False
            return

        all_items = self.ctx.player.inventory.get_all_items()

        if key == pygame.K_UP or key == pygame.K_w:
            if all_items:
                self.ctx.inventory_window.selected_inventory_index = max(0, self.ctx.inventory_window.selected_inventory_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if all_items:
                self.ctx.inventory_window.selected_inventory_index = min(len(all_items) - 1, self.ctx.inventory_window.selected_inventory_index + 1)
        elif key == pygame.K_RETURN or key == pygame.K_u:
            # Использовать выбранный предмет
            if all_items and 0 <= self.ctx.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.ctx.inventory_window.selected_inventory_index]
                result = self.ctx.player.use_item(item.name)
                print(result)
                # Если предметов больше нет, корректируем индекс
                if self.ctx.player.inventory.get_item(item.name) is None:
                    all_items = self.ctx.player.inventory.get_all_items()
                    if all_items:
                        self.ctx.inventory_window.selected_inventory_index = min(
                            self.ctx.inventory_window.selected_inventory_index,
                            len(all_items) - 1
                        )
                    else:
                        self.ctx.inventory_window.selected_inventory_index = 0
        elif key == pygame.K_e:
            # Экипировать выбранный предмет
            if all_items and 0 <= self.ctx.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.ctx.inventory_window.selected_inventory_index]
                if isinstance(item, EquipmentItem):
                    success, message = self.ctx.player.inventory.equip_item(item.name)
                    print(message)
                    # Обновляем производные характеристики после экипировки
                    if success:
                        self.ctx.player.update_derived_stats()
                        # Обновляем максимальный вес с учетом бонусов от экипировки
                        self.ctx.player.update_inventory_max_weight()
                else:
                    print("Этот предмет нельзя экипировать")
        elif key == pygame.K_q:
            # Снять экипированный предмет через выбранный слот
            if self.ctx.inventory_window.selected_equipment_slot:
                slot = self.ctx.inventory_window.selected_equipment_slot
                item = self.ctx.player.inventory.get_equipped_item(slot)
                if item:
                    success, message = self.ctx.player.inventory.unequip_item(slot)
                    print(message)
                    if success:
                        self.ctx.player.update_derived_stats()
                        # Обновляем максимальный вес с учетом бонусов от экипировки
                        self.ctx.player.update_inventory_max_weight()
                else:
                    print("В этом слоте нет предмета")
            else:
                print("Выберите слот экипировки для снятия предмета")
        elif key == pygame.K_DELETE or key == pygame.K_d:
            # Выбросить/уничтожить предмет из инвентаря
            if all_items and 0 <= self.ctx.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.ctx.inventory_window.selected_inventory_index]
                # Удаляем 1 штуку выбранного предмета
                if self.ctx.player.inventory.remove_item(item.name, 1):
                    item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                    print(f"Выброшен предмет: {item_name}")
                    # Если предметов больше нет, корректируем индекс
                    if self.ctx.player.inventory.get_item(item.name) is None:
                        all_items = self.ctx.player.inventory.get_all_items()
                        if all_items:
                            self.ctx.inventory_window.selected_inventory_index = min(
                                self.ctx.inventory_window.selected_inventory_index,
                                len(all_items) - 1
                            )
                        else:
                            self.ctx.inventory_window.selected_inventory_index = 0
                else:
                    print("Не удалось выбросить предмет")
            else:
                print("Выберите предмет для выброса")

    def handle_inventory_right_click(self, mouse_pos):
        """
        Обработка правого клика мыши в инвентаре

        Args:
            mouse_pos: Позиция мыши (x, y)
        """
        mouse_x, mouse_y = mouse_pos

        # Сначала проверяем клик по экипированному предмету (используем сохраненные rect'ы)
        slot, equipped_item = self.ctx.inventory_window.get_equipment_slot_at_mouse(mouse_x, mouse_y)
        if slot is not None:
            if equipped_item:
                success, message = self.ctx.player.inventory.unequip_item(slot)
                print(message)
                if success:
                    self.ctx.player.update_derived_stats()
                    self.ctx.player.update_inventory_max_weight()
            else:
                print("Слот пуст")
            return

        # Проверяем клик по предмету в инвентаре (не экипировке)
        item = self.ctx.inventory_window.get_item_at_mouse(self.ctx.player, mouse_x, mouse_y, check_equipment=True)
        if item:
            # Клик по предмету в инвентаре
            if isinstance(item, EquipmentItem):
                # Экипировать предмет
                success, message = self.ctx.player.inventory.equip_item(item.name)
                print(message)
                if success:
                    self.ctx.player.update_derived_stats()
                    # Обновляем максимальный вес с учетом бонусов от экипировки
                    self.ctx.player.update_inventory_max_weight()
            elif isinstance(item, SkillBookItem):
                # Изучить умение из книги
                result = item.use(self.ctx.player)
                print(result)
                # Если умение успешно изучено, удаляем книгу из инвентаря
                if "Изучено умение" in result:
                    self.ctx.player.inventory.remove_item(item.name, 1)
            else:
                print("Этот предмет нельзя использовать таким образом")
            return

    def handle_interaction_choice(self, key):
        """
        Обработка выбора в меню взаимодействия

        Args:
            key: Нажатая клавиша
        """
        npc_type = self.ctx.nearby_npc.npc_type if self.ctx.nearby_npc else None

        if key == pygame.K_1:
            # Торговля / Магия / Зелья / Агрессия (для животных/бандитов/нежити)
            if npc_type in ["wolf", "bear", "deer"]:
                # Для животных кнопка 1 - это Агрессия
                self.ctx.start_combat(self.ctx.nearby_npc)
                # Помечаем животное как провоцированное
                if hasattr(self.ctx.nearby_npc, 'mark_as_provoked'):
                    self.ctx.nearby_npc.mark_as_provoked()
            elif npc_type in ["bandit", "undead"]:
                # Для бандитов и нежити кнопка 1 - это Агрессия
                self.ctx.start_combat(self.ctx.nearby_npc)
            elif npc_type in ["merchant", "mage", "alchemist", "hunter"]:
                self.ctx.trade_menu_open = True
                self.ctx.trade_window.mode = "buy"
                self.ctx.trade_window.selected_merchant_index = 0
                self.ctx.trade_window.selected_player_index = 0
                print(f"Торговля с {self.ctx.nearby_npc.name}")
            else:
                print(f"{self.ctx.nearby_npc.name} не торгует")
            self.ctx.interaction_menu_open = False

        elif key == pygame.K_2:
            # Действие 2: Обучение / Агрессия / Квест / Уйти (для животных)
            if npc_type in ["wolf", "bear", "deer"]:
                # Для животных кнопка 2 - это Уйти
                print("Вы ушли.")
                self.ctx.nearby_npc = None
            elif npc_type == "mage":
                self.handle_magic_training()
            elif npc_type in ["alchemist", "hunter"]:
                self.handle_unique_npc_quest()
            else:
                self.ctx.start_combat(self.ctx.nearby_npc)
            self.ctx.interaction_menu_open = False

        elif key == pygame.K_3:
            # Действие 3: Агрессия / Уйти / Сдать квест
            if npc_type == "mage":
                self.ctx.start_combat(self.ctx.nearby_npc)
            elif npc_type in ["alchemist", "hunter"]:
                self.handle_turn_in_quest()
            elif npc_type not in ["wolf", "bear", "deer"]:
                print("Вы ушли от разговора.")
                self.ctx.nearby_npc = None
            self.ctx.interaction_menu_open = False

        elif key == pygame.K_4:
            # Уйти (для магов и уникальных NPC)
            if npc_type in ["mage", "alchemist", "hunter"]:
                print("Вы ушли от разговора.")
                self.ctx.nearby_npc = None
            self.ctx.interaction_menu_open = False

        elif key == pygame.K_ESCAPE:
            self.ctx.interaction_menu_open = False
            self.ctx.nearby_npc = None

    def handle_unique_npc_quest(self):
        """Обработка получения квеста от уникального NPC"""
        from game.quests import create_alchemist_quests, create_hunter_quests

        if not self.ctx.nearby_npc:
            return

        npc_type = self.ctx.nearby_npc.npc_type
        npc_name = self.ctx.nearby_npc.name

        # Генерируем квесты в зависимости от типа NPC
        if npc_type == "alchemist":
            quests = create_alchemist_quests(npc_name)
        elif npc_type == "hunter":
            quests = create_hunter_quests(npc_name)
        else:
            print(f"{npc_name} не даёт квесты.")
            return

        if not quests:
            print(f"У {npc_name} нет доступных квестов.")
            return

        # Пытаемся принять первый доступный квест
        if not self.ctx.quest_manager.can_accept_quest():
            print("У вас уже максимум активных квестов!")
            return

        quest = quests[0]
        self.ctx.quest_manager.add_available_quest(quest)
        success, message = self.ctx.quest_manager.accept_quest(quest.quest_id, player=self.ctx.player)
        print(message)

    def handle_turn_in_quest(self):
        """Обработка сдачи квеста уникальному NPC"""
        if not self.ctx.nearby_npc:
            return

        npc_name = self.ctx.nearby_npc.name

        # Сначала проверяем прогресс всех квестов
        self.ctx.quest_manager.check_all_quest_progress(self.ctx.player)

        # Ищем квесты готовые к сдаче у этого NPC
        ready_quests = []
        for quest in self.ctx.quest_manager.active_quests:
            # Проверяем статус завершения
            quest.check_completion()

            if quest.is_ready_to_turn_in():
                # Стартовые квесты можно сдать любому NPC
                if quest.is_starter or quest.giver_location == "Любая локация":
                    ready_quests.append(quest)
                # Обычные квесты - только тому NPC, который их дал
                elif quest.giver_location == npc_name:
                    ready_quests.append(quest)

        if not ready_quests:
            print(f"У вас нет квестов готовых к сдаче для {npc_name}.")
            return

        # Сдаём все готовые квесты
        for quest in ready_quests:
            success, messages = self.ctx.quest_manager.complete_quest(quest.quest_id, self.ctx.player)
            if success:
                print(f"Квест '{quest.name}' завершён!")
                for msg in messages:
                    print(f"  {msg}")

    def handle_magic_training(self):
        """Обработка магического обучения от мага"""
        if not self.ctx.nearby_npc:
            return

        training_cost = 50 * self.ctx.nearby_npc.level

        if self.ctx.player.inventory.gold < training_cost:
            print(f"Недостаточно золота! Нужно {training_cost} золота для обучения.")
            return

        # Забираем золото
        self.ctx.player.inventory.remove_gold(training_cost)

        # Даем опыт магическим навыкам
        exp_bonus = 20 * self.ctx.nearby_npc.level

        # Находим магические навыки и даем им опыт
        magic_skills_trained = []
        for skill_id, skill in self.ctx.player.skill_manager.learned_skills.items():
            if skill.category.value == 'magic':
                old_rank = skill.rank
                if skill.add_experience(exp_bonus):
                    magic_skills_trained.append(f"{skill.name} повышен до ранга {skill.rank}")
                else:
                    magic_skills_trained.append(f"{skill.name} +{exp_bonus} опыта")

        if magic_skills_trained:
            print(f"Обучение завершено за {training_cost} золота!")
            for msg in magic_skills_trained:
                print(f"  - {msg}")
        else:
            # Если нет магических навыков, повышаем дух
            self.ctx.player.spirit += 1
            self.ctx.player.update_derived_stats()
            print(f"Обучение завершено за {training_cost} золота! Ваш Дух повышен на 1.")

    def handle_trade_input(self, key):
        """
        Обработка ввода в меню торговли

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE:
            self.ctx.trade_menu_open = False
            self.ctx.nearby_npc = None
            return
        elif key == pygame.K_TAB:
            # Переключение между покупкой и продажей
            if self.ctx.trade_window.mode == "buy":
                self.ctx.trade_window.mode = "sell"
            else:
                self.ctx.trade_window.mode = "buy"
            return

        if self.ctx.trade_window.mode == "buy":
            # Режим покупки - используем сохранённый список из рендера
            merchant_items = self.ctx.trade_window.current_merchant_items
            if not merchant_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.ctx.trade_window.selected_merchant_index = max(0, self.ctx.trade_window.selected_merchant_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.ctx.trade_window.selected_merchant_index = min(len(merchant_items) - 1, self.ctx.trade_window.selected_merchant_index + 1)
            elif key == pygame.K_RETURN:
                # Купить выбранный предмет
                if 0 <= self.ctx.trade_window.selected_merchant_index < len(merchant_items):
                    item, quantity = merchant_items[self.ctx.trade_window.selected_merchant_index]
                    buy_price = int(item.value * 1.5)  # Торговец продает с наценкой 50%

                    if self.ctx.player.inventory.gold >= buy_price:
                        if self.ctx.nearby_npc.inventory.remove_item(item.name, 1):
                            if self.ctx.player.inventory.add_item(item, 1):
                                self.ctx.player.inventory.remove_gold(buy_price)
                                self.ctx.nearby_npc.inventory.add_gold(buy_price)
                                print(f"Вы купили {item.name} за {buy_price} золота")
                            else:
                                # Возвращаем предмет торговцу если не поместился в инвентарь
                                self.ctx.nearby_npc.inventory.add_item(item, 1)
                                print("Ваш инвентарь переполнен!")
                    else:
                        print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.ctx.player.inventory.gold}")
        else:
            # Режим продажи - используем сохранённый список из рендера
            player_items = self.ctx.trade_window.current_player_items
            if not player_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.ctx.trade_window.selected_player_index = max(0, self.ctx.trade_window.selected_player_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.ctx.trade_window.selected_player_index = min(len(player_items) - 1, self.ctx.trade_window.selected_player_index + 1)
            elif key == pygame.K_RETURN:
                # Продать выбранный предмет
                if 0 <= self.ctx.trade_window.selected_player_index < len(player_items):
                    item, quantity = player_items[self.ctx.trade_window.selected_player_index]
                    sell_price = int(item.value * 0.7)  # Торговец покупает за 70% от стоимости

                    if self.ctx.nearby_npc.inventory.gold >= sell_price:
                        if self.ctx.player.inventory.remove_item(item.name, 1):
                            if self.ctx.nearby_npc.inventory.add_item(item, 1):
                                self.ctx.player.inventory.add_gold(sell_price)
                                self.ctx.nearby_npc.inventory.remove_gold(sell_price)
                                print(f"Вы продали {item.name} за {sell_price} золота")

                                # Обновляем прогресс квеста "Начинающий торговец"
                                self.ctx.player.items_sold += 1
                                self.ctx.quest_manager.update_quest_progress("merchant", 0, 1)
                            else:
                                # Возвращаем предмет игроку если не поместился в инвентарь торговца
                                self.ctx.player.inventory.add_item(item, 1)
                                print("У торговца нет места для этого предмета!")
                    else:
                        print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.ctx.nearby_npc.inventory.gold}")

    def handle_trade_left_click(self, pos):
        """
        Обработка левого клика мыши в окне торговли (фильтры и сортировка)

        Args:
            pos: Позиция клика (x, y)
        """
        mouse_x, mouse_y = pos

        # Проверяем клик по фильтрам
        if self.ctx.trade_window.handle_filter_click(mouse_x, mouse_y):
            return True

        # Проверяем клик по сортировке
        if self.ctx.trade_window.handle_sort_click(mouse_x, mouse_y):
            return True

        return False

    def handle_trade_right_click(self, pos):
        """
        Обработка правого клика мыши в окне торговли

        Args:
            pos: Позиция клика (x, y)
        """
        mouse_x, mouse_y = pos

        # Получаем сам предмет под курсором (напрямую из сохранённых rect'ов)
        item = self.ctx.trade_window.get_item_at_mouse_trade(mouse_x, mouse_y)

        if item is None:
            return

        if self.ctx.trade_window.mode == "buy":
            # Режим покупки
            if not hasattr(self.ctx.nearby_npc, 'inventory'):
                return

            buy_price = int(item.value * 1.5)

            if self.ctx.player.inventory.gold >= buy_price:
                if self.ctx.nearby_npc.inventory.remove_item(item.name, 1):
                    if self.ctx.player.inventory.add_item(item, 1):
                        self.ctx.player.inventory.remove_gold(buy_price)
                        self.ctx.nearby_npc.inventory.add_gold(buy_price)
                        print(f"Вы купили {item.name} за {buy_price} золота")
                    else:
                        self.ctx.nearby_npc.inventory.add_item(item, 1)
                        print("Ваш инвентарь переполнен!")
            else:
                print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.ctx.player.inventory.gold}")
        else:
            # Режим продажи
            sell_price = int(item.value * 0.7)

            if self.ctx.nearby_npc.inventory.gold >= sell_price:
                if self.ctx.player.inventory.remove_item(item.name, 1):
                    if self.ctx.nearby_npc.inventory.add_item(item, 1):
                        self.ctx.player.inventory.add_gold(sell_price)
                        self.ctx.nearby_npc.inventory.remove_gold(sell_price)
                        print(f"Вы продали {item.name} за {sell_price} золота")

                        # Обновляем прогресс квеста "Начинающий торговец"
                        self.ctx.player.items_sold += 1
                        self.ctx.quest_manager.update_quest_progress("merchant", 0, 1)
                    else:
                        self.ctx.player.inventory.add_item(item, 1)
                        print("У торговца нет места для этого предмета!")
            else:
                print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.ctx.nearby_npc.inventory.gold}")

    def handle_character_input(self, key):
        """
        Обработка ввода в окне характеристик

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_c:
            self.ctx.character_menu_open = False
            return

        # Навигация по характеристикам
        if key == pygame.K_UP or key == pygame.K_w:
            self.ctx.character_window.selected_stat_index = max(0, self.ctx.character_window.selected_stat_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.ctx.character_window.selected_stat_index = min(5, self.ctx.character_window.selected_stat_index + 1)
        elif key == pygame.K_RETURN:
            # Добавить очко к выбранной характеристике
            if self.ctx.player.stat_points > 0:
                stat_key, stat_name = self.ctx.character_window.stats_list[self.ctx.character_window.selected_stat_index]
                if self.ctx.player.add_stat_point(stat_key):
                    print(f"{stat_name} увеличена! Осталось очков: {self.ctx.player.stat_points}")

    def handle_skill_book_input(self, key):
        """
        Обработка ввода в окне книги умений

        Args:
            key: Нажатая клавиша
        """
        from game.skills import SkillCategory

        if key == pygame.K_ESCAPE or key == pygame.K_k:
            self.ctx.skill_book_menu_open = False
            return

        # Переключение между вкладками (TAB)
        if key == pygame.K_TAB:
            self.ctx.skill_book_window.selected_tab = (self.ctx.skill_book_window.selected_tab + 1) % 3
            self.ctx.skill_book_window.selected_skill_index = 0
            return

        # Навигация по умениям (W/S)
        if key == pygame.K_UP or key == pygame.K_w:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.ctx.skill_book_window.selected_tab]
            skills_dict = self.ctx.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.ctx.skill_book_window.selected_skill_index = max(0, self.ctx.skill_book_window.selected_skill_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.ctx.skill_book_window.selected_tab]
            skills_dict = self.ctx.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.ctx.skill_book_window.selected_skill_index = min(len(skills) - 1, self.ctx.skill_book_window.selected_skill_index + 1)

        # Навигация по слотам (A/D)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self.ctx.skill_book_window.selected_slot_index = max(0, self.ctx.skill_book_window.selected_slot_index - 1)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.ctx.skill_book_window.selected_slot_index = min(7, self.ctx.skill_book_window.selected_slot_index + 1)

        # Назначить умение в слот (Enter)
        elif key == pygame.K_RETURN:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.ctx.skill_book_window.selected_tab]
            skills_dict = self.ctx.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]

            if skills and self.ctx.skill_book_window.selected_skill_index < len(skills):
                # Найдем ID умения
                selected_skill = skills[self.ctx.skill_book_window.selected_skill_index]
                skill_id = None
                for sid, skill in skills_dict.items():
                    if skill == selected_skill:
                        skill_id = sid
                        break

                if skill_id:
                    success = self.ctx.player.skill_manager.assign_to_slot(
                        skill_id,
                        self.ctx.skill_book_window.selected_slot_index
                    )
                    if success:
                        print(f"{selected_skill.name} назначено в слот {self.ctx.skill_book_window.selected_slot_index + 1}")
                    else:
                        print("Не удалось назначить умение в слот")

        # Убрать умение из слота (Delete)
        elif key == pygame.K_DELETE:
            self.ctx.player.skill_manager.unassign_from_slot(self.ctx.skill_book_window.selected_slot_index)
            print(f"Слот {self.ctx.skill_book_window.selected_slot_index + 1} очищен")

    def handle_key_press(self, key):
        """
        Обработка нажатия клавиш

        Args:
            key: Код нажатой клавиши
        """
        # Движение игрока (стрелки или WASD)
        moved = False
        new_x, new_y = self.ctx.player.x, self.ctx.player.y

        if key == pygame.K_UP or key == pygame.K_w:
            new_y -= 1
            moved = True
        elif key == pygame.K_DOWN or key == pygame.K_s:
            new_y += 1
            moved = True
        elif key == pygame.K_LEFT or key == pygame.K_a:
            new_x -= 1
            moved = True
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            new_x += 1
            moved = True
        elif key == pygame.K_r:
            # Отдых - восстанавливает здоровье и ману, занимает 1 час
            self.ctx.player.rest()
            self.ctx.game_time.advance_time(1/3, skip_player_recovery=True)
            print(f"Вы отдохнули. {self.ctx.game_time.get_time_string()}")
            return
        elif key == pygame.K_ESCAPE:
            # Открываем окно подтверждения выхода
            self.ctx.exit_confirmation_open = True
        elif key == pygame.K_e:
            # Взаимодействие с NPC
            self.ctx.check_npc_nearby()
            return
        elif key == pygame.K_f:
            # Сбор ресурсов с локации
            self.ctx.collect_resources()
            return
        elif key == pygame.K_F5:
            # Быстрое сохранение
            SaveSystem.save_game(self.game, "autosave")
            print("Игра сохранена!")
            return
        elif key == pygame.K_F9:
            # Быстрая загрузка (не реализована в этой версии - требует рестарта)
            print("Для загрузки используйте параметр при запуске игры")
            return
        elif key == pygame.K_k:
            # Открыть/закрыть книгу умений
            self.ctx.skill_book_menu_open = not self.ctx.skill_book_menu_open
            return
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                     pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
            # Использовать умение из слота (клавиши 1-8)
            slot_index = key - pygame.K_1  # Преобразуем код клавиши в индекс слота (0-7)
            skill = self.ctx.player.skill_manager.get_slot_skill(slot_index)
            if skill:
                # Используем умение вне боя (применяется только к ремесленным умениям)
                if skill.category.value == 'crafting':
                    # Проверяем требования к местности для ремесленных умений
                    tile = self.ctx.game_map.get_tile(self.ctx.player.x, self.ctx.player.y)
                    biome = tile.biome
                    location = tile.location if tile.has_location() else None

                    skill_id = self.ctx.player.skill_manager.skill_slots[slot_index]

                    # Проверяем рудокопство
                    if skill_id == 'mining':
                        mining = self.ctx.player.profession_manager.get_profession('mining')
                        can_use, msg = mining.can_use(self.ctx.player, location)
                        if not can_use:
                            print(msg)
                            return

                    # Проверяем лесорубство
                    elif skill_id == 'lumberjacking':
                        lumberjacking = self.ctx.player.profession_manager.get_profession('lumberjacking')
                        can_use, msg = lumberjacking.can_use(self.ctx.player, biome)
                        if not can_use:
                            print(msg)
                            return

                    result = self.ctx.player.skill_manager.use_skill_from_slot(slot_index)
                    print(result['message'])

                    # Обновляем прогресс квестов при добыче ресурсов
                    if result.get('success') and 'gathered' in result:
                        for item_key, quantity in result['gathered']:
                            messages = self.ctx.quest_manager.update_gather_progress(item_key, quantity, self.ctx.player)
                            for msg in messages:
                                print(f"  {msg}")
                else:
                    print(f"{skill.name} можно использовать только в бою!")
            else:
                print(f"Слот {slot_index + 1} пуст!")
            return
        elif key == pygame.K_i:
            # Открыть/закрыть инвентарь
            self.ctx.inventory_menu_open = not self.ctx.inventory_menu_open
            return
        elif key == pygame.K_c:
            # Открыть/закрыть окно характеристик
            self.ctx.character_menu_open = not self.ctx.character_menu_open
            return
        elif key == pygame.K_q:
            # Открыть окно квестов (можно просматривать активные из любого места)
            tile = self.ctx.game_map.get_tile(self.ctx.player.x, self.ctx.player.y)
            if tile.has_location():
                location = tile.location
                if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                    # В городе/деревне - полный доступ к квестам
                    self.ctx.open_quest_window(location)
                else:
                    # Вне города - только просмотр активных квестов
                    self.ctx.open_quest_window()
            else:
                # Вне локации - только просмотр активных квестов
                self.ctx.open_quest_window()
            return
        elif key == pygame.K_F1:
            # Открыть/закрыть окно помощи
            self.ctx.help_window.toggle()
            return
        elif key == pygame.K_F2:
            # Открыть/закрыть чит-меню
            self.ctx.cheat_menu_open = not self.ctx.cheat_menu_open
            return

        # Попытка переместить игрока
        if moved:
            # Проверяем выносливость перед движением
            if self.ctx.player.is_resting:
                print("Вы слишком устали и должны отдохнуть!")
                return

            if not self.ctx.player.consume_stamina():
                print("У вас недостаточно выносливости! Нажмите R для отдыха.")
                return

            # Игрок может проходить сквозь NPC (коллизии убраны)
            if self.ctx.player.move_to(new_x, new_y, self.ctx.game_map):
                # Продвигаем время на 20 минут (1/3 часа) за перемещение
                self.ctx.game_time.advance_time(1/3)

                # Обновляем системы событий
                if self.ctx.weather_system:
                    weather_msg = self.ctx.weather_system.update(1/3)
                    if weather_msg:
                        print(weather_msg)

                if self.ctx.killstreak_system:
                    self.ctx.killstreak_system.update(1/3)

                # Проверяем случайные события при путешествии
                if self.ctx.random_event_system:
                    event_messages = self.ctx.random_event_system.check_for_event(
                        self.ctx.player, self.game  # game нужен для event system
                    )
                    if event_messages:
                        for msg in event_messages:
                            print(msg)
                        # Открываем окно события
                        self.ctx.event_window_open = True

                # Обновляем туман войны
                self.ctx.fog_of_war.update_vision(self.ctx.player.x, self.ctx.player.y)
                # Обновляем камеру
                self.ctx.camera.update()

                # Проверяем, есть ли локация на новой позиции
                tile = self.ctx.game_map.get_tile(self.ctx.player.x, self.ctx.player.y)
                if tile.has_location():
                    print(f"Вы прибыли в: {tile.location.name}")
                    print(f"  {tile.location.get_description()}")
                    print(f"Время: {self.ctx.game_time.get_time_string()}")

    def handle_quest_input(self, key):
        """
        Обработка ввода в окне квестов

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE:
            self.ctx.quest_window_open = False
            return

        # Переключение вкладок
        if key == pygame.K_TAB:
            modes = ["available", "active", "turn_in"]
            current_idx = modes.index(self.ctx.quest_window.mode)
            self.ctx.quest_window.mode = modes[(current_idx + 1) % 3]
            self.ctx.quest_window.selected_index = 0
            self.ctx.quest_window.scroll_offset = 0
            return

        # Навигация по списку
        quests = self.ctx.quest_window.get_current_list()
        if key == pygame.K_UP or key == pygame.K_w:
            if quests:
                self.ctx.quest_window.selected_index = max(0, self.ctx.quest_window.selected_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if quests:
                self.ctx.quest_window.selected_index = min(len(quests) - 1, self.ctx.quest_window.selected_index + 1)
        elif key == pygame.K_RETURN:
            # Принять или сдать квест
            quest = self.ctx.quest_window.get_selected_quest()
            if quest:
                if self.ctx.quest_window.mode == "available":
                    # Принять квест
                    success, message = self.ctx.quest_manager.accept_quest(
                        quest.quest_id,
                        self.ctx.quest_window.location_id,
                        self.ctx.player
                    )
                    print(message)
                    if success:
                        # Обновляем данные окна
                        self._refresh_quest_window()
                elif self.ctx.quest_window.mode == "turn_in":
                    # Сдать квест
                    success, messages = self.ctx.quest_manager.complete_quest(
                        quest.quest_id,
                        self.ctx.player
                    )
                    if success:
                        print(f"Квест '{quest.name}' завершён!")
                        for msg in messages:
                            print(f"  {msg}")
                        # Обновляем данные окна
                        self._refresh_quest_window()
                    else:
                        print("Не удалось сдать квест")
        elif key == pygame.K_DELETE:
            # Отменить квест (только для активных)
            if self.ctx.quest_window.mode == "active":
                quest = self.ctx.quest_window.get_selected_quest()
                if quest:
                    success, message = self.ctx.quest_manager.abandon_quest(quest.quest_id)
                    print(message)
                    if success:
                        # Обновляем данные окна
                        self._refresh_quest_window()

    def _refresh_quest_window(self):
        """Обновить данные в окне квестов"""
        location_id = self.ctx.quest_window.location_id
        location_name = self.ctx.quest_window.location_name

        # Проверяем прогресс всех квестов на сбор ресурсов
        self.ctx.quest_manager.check_all_quest_progress(self.ctx.player)

        available_quests = self.ctx.quest_manager.get_location_quests(location_id)
        active_quests = self.ctx.quest_manager.get_active_quests()
        turn_in_quests = self.ctx.quest_manager.get_quests_ready_to_turn_in(location_id)

        self.ctx.quest_window.set_data(
            location_name,
            location_id,
            available_quests,
            active_quests,
            turn_in_quests
        )

    def route_menu_event(self, event, quest_action_handler=None):
        """
        Маршрутизация событий для открытых меню.

        Args:
            event: pygame событие
            quest_action_handler: callback для обработки действий квестов

        Returns:
            bool: True если событие обработано (нужен continue), False иначе
        """
        # Меню взаимодействия
        if self.ctx.interaction_menu_open:
            if event.type == pygame.KEYDOWN:
                self.handle_interaction_choice(event.key)
            return True

        # Меню инвентаря
        if self.ctx.inventory_menu_open:
            if event.type == pygame.KEYDOWN:
                self.handle_inventory_input(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # ПКМ
                    self.handle_inventory_right_click(event.pos)
                elif event.button in (4, 5):  # Колесо мыши
                    self._handle_inventory_scroll(event.button == 4)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_inventory_scroll(event.y > 0)
            return True

        # Меню торговли
        if self.ctx.trade_menu_open:
            if event.type == pygame.KEYDOWN:
                self.handle_trade_input(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_trade_left_click(event.pos)
                elif event.button == 3:
                    self.handle_trade_right_click(event.pos)
            return True

        # Окно характеристик
        if self.ctx.character_menu_open:
            if event.type == pygame.KEYDOWN:
                self.handle_character_input(event.key)
            return True

        # Книга умений
        if self.ctx.skill_book_menu_open:
            if event.type == pygame.KEYDOWN:
                self.handle_skill_book_input(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.ctx.skill_book_window.handle_mouse_event(event, self.ctx.player)
            return True

        # Окно лута
        if self.ctx.loot_window_open:
            if event.type == pygame.KEYDOWN:
                self.ctx.loot_window_open = False
            return True

        # Окно квестов
        if self.ctx.quest_window_open:
            if event.type == pygame.KEYDOWN:
                self.handle_quest_input(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = self.ctx.quest_window.handle_mouse_event(event, self.game)
                if action and quest_action_handler:
                    quest_action_handler(action)
            return True

        # Окно случайных событий
        if self.ctx.event_window_open:
            if self.ctx.random_event_window.handle_input(event):
                self.ctx.event_window_open = False
                self.ctx.random_event_system.clear_last_event()
            return True

        # Чит-меню
        if self.ctx.cheat_menu_open:
            if self.ctx.cheat_menu_window.handle_input(event, self.game):
                self.ctx.cheat_menu_open = False
            return True

        return False

    def _handle_inventory_scroll(self, scroll_up):
        """
        Обработка прокрутки в инвентаре.

        Args:
            scroll_up: True если прокрутка вверх, False если вниз
        """
        all_items = self.ctx.player.inventory.get_all_items()
        if not all_items:
            return

        if scroll_up:
            self.ctx.inventory_window.selected_inventory_index = max(
                0, self.ctx.inventory_window.selected_inventory_index - 1
            )
        else:
            self.ctx.inventory_window.selected_inventory_index = min(
                len(all_items) - 1, self.ctx.inventory_window.selected_inventory_index + 1
            )

