"""
Модуль для обработки пользовательского ввода
"""
import pygame
from game.inventory import EquipmentItem, EquipmentSlot, SkillBookItem
from game.save_system import SaveSystem
from game.constants import LOCATION_CITY, LOCATION_VILLAGE


class InputHandler:
    """Класс для обработки пользовательского ввода"""

    def __init__(self, game):
        """
        Инициализация обработчика ввода

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game

    def handle_inventory_input(self, key):
        """
        Обработка ввода в меню инвентаря

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_i:
            self.game.inventory_menu_open = False
            return

        all_items = self.game.player.inventory.get_all_items()

        if key == pygame.K_UP or key == pygame.K_w:
            if all_items:
                self.game.inventory_window.selected_inventory_index = max(0, self.game.inventory_window.selected_inventory_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if all_items:
                self.game.inventory_window.selected_inventory_index = min(len(all_items) - 1, self.game.inventory_window.selected_inventory_index + 1)
        elif key == pygame.K_RETURN or key == pygame.K_u:
            # Использовать выбранный предмет
            if all_items and 0 <= self.game.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.game.inventory_window.selected_inventory_index]
                result = self.game.player.use_item(item.name)
                print(result)
                # Если предметов больше нет, корректируем индекс
                if self.game.player.inventory.get_item(item.name) is None:
                    all_items = self.game.player.inventory.get_all_items()
                    self.game.inventory_window.selected_inventory_index = min(self.game.inventory_window.selected_inventory_index, len(all_items) - 1)
                    if self.game.inventory_window.selected_inventory_index < 0:
                        self.game.inventory_window.selected_inventory_index = 0
        elif key == pygame.K_e:
            # Экипировать выбранный предмет
            if all_items and 0 <= self.game.inventory_window.selected_inventory_index < len(all_items):
                item, quantity = all_items[self.game.inventory_window.selected_inventory_index]
                if isinstance(item, EquipmentItem):
                    success, message = self.game.player.inventory.equip_item(item.name)
                    print(message)
                    # Обновляем производные характеристики после экипировки
                    if success:
                        self.game.player.update_derived_stats()
                        # Обновляем максимальный вес с учетом бонусов от экипировки
                        self.game.player.update_inventory_max_weight()
                else:
                    print("Этот предмет нельзя экипировать")
        elif key == pygame.K_q:
            # Снять экипированный предмет через выбранный слот
            if self.game.inventory_window.selected_equipment_slot:
                slot = self.game.inventory_window.selected_equipment_slot
                item = self.game.player.inventory.get_equipped_item(slot)
                if item:
                    success, message = self.game.player.inventory.unequip_item(slot)
                    print(message)
                    if success:
                        self.game.player.update_derived_stats()
                        # Обновляем максимальный вес с учетом бонусов от экипировки
                        self.game.player.update_inventory_max_weight()
                else:
                    print("В этом слоте нет предмета")
            else:
                print("Выберите слот экипировки для снятия предмета")

    def handle_inventory_right_click(self, mouse_pos):
        """
        Обработка правого клика мыши в инвентаре

        Args:
            mouse_pos: Позиция мыши (x, y)
        """
        mouse_x, mouse_y = mouse_pos

        # Проверяем клик по предмету в инвентаре
        item = self.game.inventory_window.get_item_at_mouse(self.game.player, mouse_x, mouse_y)
        if item:
            # Клик по предмету в инвентаре
            if isinstance(item, EquipmentItem):
                # Экипировать предмет
                success, message = self.game.player.inventory.equip_item(item.name)
                print(message)
                if success:
                    self.game.player.update_derived_stats()
                    # Обновляем максимальный вес с учетом бонусов от экипировки
                    self.game.player.update_inventory_max_weight()
            elif isinstance(item, SkillBookItem):
                # Изучить умение из книги
                result = item.use(self.game.player)
                print(result)
                # Если умение успешно изучено, удаляем книгу из инвентаря
                if "Изучено умение" in result:
                    self.game.player.inventory.remove_item(item.name, 1)
            else:
                print("Этот предмет нельзя использовать таким образом")
            return

        # Проверяем клик по экипированному предмету
        # Получаем размеры экрана
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()

        # Размеры окна (адаптивные)
        if self.game.ui_scaler:
            window_width = self.game.ui_scaler.scale_width(900)
            window_height = self.game.ui_scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Левая панель - экипировка
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        equipment_panel_x = window_x + margin
        equipment_panel_y = window_y + panel_y_offset
        equipment_panel_width = int(400 * (window_width / 900))

        # Проверяем, находится ли курсор в области экипировки
        if equipment_panel_x <= mouse_x <= equipment_panel_x + equipment_panel_width:
            # Вычисляем на какой слот кликнули
            slot_y_start = equipment_panel_y + int(40 * (window_height / 650))
            slot_height = max(22, int(28 * (window_height / 650)))

            # Группировка слотов (такая же как в ui.py)
            slot_groups = [
                ("Оружие", [EquipmentSlot.WEAPON]),
                ("Доспехи", [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]),
                ("Кольца", [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]),
                ("Украшения", [EquipmentSlot.AMULET, EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]),
            ]

            current_y = slot_y_start
            for group_name, slots in slot_groups:
                # Пропускаем заголовок группы
                current_y += max(20, int(25 * (window_height / 650)))

                for slot in slots:
                    # Проверяем клик по этому слоту
                    if current_y <= mouse_y <= current_y + slot_height:
                        item = self.game.player.inventory.get_equipped_item(slot)
                        if item:
                            success, message = self.game.player.inventory.unequip_item(slot)
                            print(message)
                            if success:
                                self.game.player.update_derived_stats()
                                # Обновляем максимальный вес с учетом бонусов от экипировки
                                self.game.player.update_inventory_max_weight()
                        else:
                            print(f"Слот {group_name} пуст")
                        return

                    current_y += slot_height

                # Пропускаем отступ между группами
                current_y += max(8, int(10 * (window_height / 650)))

    def handle_interaction_choice(self, key):
        """
        Обработка выбора в меню взаимодействия

        Args:
            key: Нажатая клавиша
        """
        npc_type = self.game.nearby_npc.npc_type if self.game.nearby_npc else None

        if key == pygame.K_1:
            # Торговля / Магия / Зелья / Агрессия (для животных)
            if npc_type in ["wolf", "bear", "deer"]:
                # Для животных кнопка 1 - это Агрессия
                self.game._start_combat(self.game.nearby_npc)
                # Помечаем животное как провоцированное
                if hasattr(self.game.nearby_npc, 'mark_as_provoked'):
                    self.game.nearby_npc.mark_as_provoked()
            elif npc_type in ["merchant", "mage", "alchemist", "hunter"]:
                self.game.trade_menu_open = True
                self.game.trade_window.mode = "buy"
                self.game.trade_window.selected_merchant_index = 0
                self.game.trade_window.selected_player_index = 0
                print(f"Торговля с {self.game.nearby_npc.name}")
            else:
                print(f"{self.game.nearby_npc.name} не торгует")
            self.game.interaction_menu_open = False

        elif key == pygame.K_2:
            # Действие 2: Обучение / Агрессия / Квест / Уйти (для животных)
            if npc_type in ["wolf", "bear", "deer"]:
                # Для животных кнопка 2 - это Уйти
                print("Вы ушли.")
                self.game.nearby_npc = None
            elif npc_type == "mage":
                self.handle_magic_training()
            elif npc_type in ["alchemist", "hunter"]:
                self.handle_unique_npc_quest()
            else:
                self.game._start_combat(self.game.nearby_npc)
            self.game.interaction_menu_open = False

        elif key == pygame.K_3:
            # Действие 3: Агрессия / Уйти / Сдать квест
            if npc_type == "mage":
                self.game._start_combat(self.game.nearby_npc)
            elif npc_type in ["alchemist", "hunter"]:
                self.handle_turn_in_quest()
            elif npc_type not in ["wolf", "bear", "deer"]:
                print("Вы ушли от разговора.")
                self.game.nearby_npc = None
            self.game.interaction_menu_open = False

        elif key == pygame.K_4:
            # Уйти (для магов и уникальных NPC)
            if npc_type in ["mage", "alchemist", "hunter"]:
                print("Вы ушли от разговора.")
                self.game.nearby_npc = None
            self.game.interaction_menu_open = False

        elif key == pygame.K_ESCAPE:
            self.game.interaction_menu_open = False
            self.game.nearby_npc = None

    def handle_unique_npc_quest(self):
        """Обработка получения квеста от уникального NPC"""
        from game.quests import create_alchemist_quests, create_hunter_quests

        if not self.game.nearby_npc:
            return

        npc_type = self.game.nearby_npc.npc_type
        npc_name = self.game.nearby_npc.name

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
        if not self.game.quest_manager.can_accept_quest():
            print("У вас уже максимум активных квестов!")
            return

        quest = quests[0]
        self.game.quest_manager.add_available_quest(quest)
        success, message = self.game.quest_manager.accept_quest(quest.quest_id, player=self.game.player)
        print(message)

    def handle_turn_in_quest(self):
        """Обработка сдачи квеста уникальному NPC"""
        if not self.game.nearby_npc:
            return

        npc_name = self.game.nearby_npc.name

        # Ищем квесты готовые к сдаче у этого NPC
        ready_quests = []
        for quest in self.game.quest_manager.active_quests:
            if quest.is_ready_to_turn_in() and quest.giver_location == npc_name:
                ready_quests.append(quest)

        if not ready_quests:
            print(f"У вас нет квестов готовых к сдаче для {npc_name}.")
            return

        # Сдаём первый готовый квест
        quest = ready_quests[0]
        success, messages = self.game.quest_manager.complete_quest(quest.quest_id, self.game.player)
        if success:
            print(f"Квест '{quest.name}' завершён!")
            for msg in messages:
                print(f"  {msg}")

    def handle_magic_training(self):
        """Обработка магического обучения от мага"""
        if not self.game.nearby_npc:
            return

        training_cost = 50 * self.game.nearby_npc.level

        if self.game.player.inventory.gold < training_cost:
            print(f"Недостаточно золота! Нужно {training_cost} золота для обучения.")
            return

        # Забираем золото
        self.game.player.inventory.remove_gold(training_cost)

        # Даем опыт магическим навыкам
        exp_bonus = 20 * self.game.nearby_npc.level

        # Находим магические навыки и даем им опыт
        magic_skills_trained = []
        for skill_id, skill in self.game.player.skill_manager.learned_skills.items():
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
            self.game.player.spirit += 1
            self.game.player.update_derived_stats()
            print(f"Обучение завершено за {training_cost} золота! Ваш Дух повышен на 1.")

    def handle_trade_input(self, key):
        """
        Обработка ввода в меню торговли

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE:
            self.game.trade_menu_open = False
            self.game.nearby_npc = None
            return
        elif key == pygame.K_TAB:
            # Переключение между покупкой и продажей
            if self.game.trade_window.mode == "buy":
                self.game.trade_window.mode = "sell"
            else:
                self.game.trade_window.mode = "buy"
            return

        if self.game.trade_window.mode == "buy":
            # Режим покупки
            if not hasattr(self.game.nearby_npc, 'inventory'):
                return

            merchant_items = self.game.nearby_npc.inventory.get_all_items()
            if not merchant_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.game.trade_window.selected_merchant_index = max(0, self.game.trade_window.selected_merchant_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.game.trade_window.selected_merchant_index = min(len(merchant_items) - 1, self.game.trade_window.selected_merchant_index + 1)
            elif key == pygame.K_RETURN:
                # Купить выбранный предмет
                if 0 <= self.game.trade_window.selected_merchant_index < len(merchant_items):
                    item, quantity = merchant_items[self.game.trade_window.selected_merchant_index]
                    buy_price = int(item.value * 1.5)  # Торговец продает с наценкой 50%

                    if self.game.player.inventory.gold >= buy_price:
                        if self.game.nearby_npc.inventory.remove_item(item.name, 1):
                            if self.game.player.inventory.add_item(item, 1):
                                self.game.player.inventory.remove_gold(buy_price)
                                self.game.nearby_npc.inventory.add_gold(buy_price)
                                print(f"Вы купили {item.name} за {buy_price} золота")
                            else:
                                # Возвращаем предмет торговцу если не поместился в инвентарь
                                self.game.nearby_npc.inventory.add_item(item, 1)
                                print("Ваш инвентарь переполнен!")
                    else:
                        print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.game.player.inventory.gold}")
        else:
            # Режим продажи
            player_items = self.game.player.inventory.get_all_items()
            if not player_items:
                return

            if key == pygame.K_UP or key == pygame.K_w:
                self.game.trade_window.selected_player_index = max(0, self.game.trade_window.selected_player_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self.game.trade_window.selected_player_index = min(len(player_items) - 1, self.game.trade_window.selected_player_index + 1)
            elif key == pygame.K_RETURN:
                # Продать выбранный предмет
                if 0 <= self.game.trade_window.selected_player_index < len(player_items):
                    item, quantity = player_items[self.game.trade_window.selected_player_index]
                    sell_price = int(item.value * 0.7)  # Торговец покупает за 70% от стоимости

                    if self.game.nearby_npc.inventory.gold >= sell_price:
                        if self.game.player.inventory.remove_item(item.name, 1):
                            if self.game.nearby_npc.inventory.add_item(item, 1):
                                self.game.player.inventory.add_gold(sell_price)
                                self.game.nearby_npc.inventory.remove_gold(sell_price)
                                print(f"Вы продали {item.name} за {sell_price} золота")

                                # Обновляем прогресс квеста "Начинающий торговец"
                                self.game.player.items_sold += 1
                                self.game.quest_manager.update_quest_progress("merchant", 0, 1)
                            else:
                                # Возвращаем предмет игроку если не поместился в инвентарь торговца
                                self.game.player.inventory.add_item(item, 1)
                                print("У торговца нет места для этого предмета!")
                    else:
                        print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.game.nearby_npc.inventory.gold}")

    def handle_trade_right_click(self, pos):
        """
        Обработка правого клика мыши в окне торговли

        Args:
            pos: Позиция клика (x, y)
        """
        mouse_x, mouse_y = pos

        # Получаем индекс предмета под курсором
        item_index = self.game.trade_window.get_item_index_at_mouse(mouse_x, mouse_y)

        if item_index is None:
            return

        if self.game.trade_window.mode == "buy":
            # Режим покупки
            if not hasattr(self.game.nearby_npc, 'inventory'):
                return

            merchant_items = self.game.nearby_npc.inventory.get_all_items()
            if not merchant_items or item_index >= len(merchant_items):
                return

            # Выбираем предмет и покупаем
            self.game.trade_window.selected_merchant_index = item_index
            item, quantity = merchant_items[item_index]
            buy_price = int(item.value * 1.5)

            if self.game.player.inventory.gold >= buy_price:
                if self.game.nearby_npc.inventory.remove_item(item.name, 1):
                    if self.game.player.inventory.add_item(item, 1):
                        self.game.player.inventory.remove_gold(buy_price)
                        self.game.nearby_npc.inventory.add_gold(buy_price)
                        print(f"Вы купили {item.name} за {buy_price} золота")
                    else:
                        self.game.nearby_npc.inventory.add_item(item, 1)
                        print("Ваш инвентарь переполнен!")
            else:
                print(f"Недостаточно золота! Нужно {buy_price}, у вас {self.game.player.inventory.gold}")
        else:
            # Режим продажи
            player_items = self.game.player.inventory.get_all_items()
            if not player_items or item_index >= len(player_items):
                return

            # Выбираем предмет и продаем
            self.game.trade_window.selected_player_index = item_index
            item, quantity = player_items[item_index]
            sell_price = int(item.value * 0.7)

            if self.game.nearby_npc.inventory.gold >= sell_price:
                if self.game.player.inventory.remove_item(item.name, 1):
                    if self.game.nearby_npc.inventory.add_item(item, 1):
                        self.game.player.inventory.add_gold(sell_price)
                        self.game.nearby_npc.inventory.remove_gold(sell_price)
                        print(f"Вы продали {item.name} за {sell_price} золота")

                        # Обновляем прогресс квеста "Начинающий торговец"
                        self.game.player.items_sold += 1
                        self.game.quest_manager.update_quest_progress("merchant", 0, 1)
                    else:
                        self.game.player.inventory.add_item(item, 1)
                        print("У торговца нет места для этого предмета!")
            else:
                print(f"У торговца недостаточно золота! Нужно {sell_price}, у него {self.game.nearby_npc.inventory.gold}")

    def handle_character_input(self, key):
        """
        Обработка ввода в окне характеристик

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE or key == pygame.K_c:
            self.game.character_menu_open = False
            return

        # Навигация по характеристикам
        if key == pygame.K_UP or key == pygame.K_w:
            self.game.character_window.selected_stat_index = max(0, self.game.character_window.selected_stat_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.game.character_window.selected_stat_index = min(5, self.game.character_window.selected_stat_index + 1)
        elif key == pygame.K_RETURN:
            # Добавить очко к выбранной характеристике
            if self.game.player.stat_points > 0:
                stat_key, stat_name = self.game.character_window.stats_list[self.game.character_window.selected_stat_index]
                if self.game.player.add_stat_point(stat_key):
                    print(f"{stat_name} увеличена! Осталось очков: {self.game.player.stat_points}")

    def handle_skill_book_input(self, key):
        """
        Обработка ввода в окне книги умений

        Args:
            key: Нажатая клавиша
        """
        from game.skills import SkillCategory

        if key == pygame.K_ESCAPE or key == pygame.K_k:
            self.game.skill_book_menu_open = False
            return

        # Переключение между вкладками (TAB)
        if key == pygame.K_TAB:
            self.game.skill_book_window.selected_tab = (self.game.skill_book_window.selected_tab + 1) % 3
            self.game.skill_book_window.selected_skill_index = 0
            return

        # Навигация по умениям (W/S)
        if key == pygame.K_UP or key == pygame.K_w:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.game.skill_book_window.selected_tab]
            skills_dict = self.game.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.game.skill_book_window.selected_skill_index = max(0, self.game.skill_book_window.selected_skill_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.game.skill_book_window.selected_tab]
            skills_dict = self.game.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]
            if skills:
                self.game.skill_book_window.selected_skill_index = min(len(skills) - 1, self.game.skill_book_window.selected_skill_index + 1)

        # Навигация по слотам (A/D)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self.game.skill_book_window.selected_slot_index = max(0, self.game.skill_book_window.selected_slot_index - 1)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.game.skill_book_window.selected_slot_index = min(7, self.game.skill_book_window.selected_slot_index + 1)

        # Назначить умение в слот (Enter)
        elif key == pygame.K_RETURN:
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.game.skill_book_window.selected_tab]
            skills_dict = self.game.player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]

            if skills and self.game.skill_book_window.selected_skill_index < len(skills):
                # Найдем ID умения
                selected_skill = skills[self.game.skill_book_window.selected_skill_index]
                skill_id = None
                for sid, skill in skills_dict.items():
                    if skill == selected_skill:
                        skill_id = sid
                        break

                if skill_id:
                    success = self.game.player.skill_manager.assign_to_slot(
                        skill_id,
                        self.game.skill_book_window.selected_slot_index
                    )
                    if success:
                        print(f"{selected_skill.name} назначено в слот {self.game.skill_book_window.selected_slot_index + 1}")
                    else:
                        print("Не удалось назначить умение в слот")

        # Убрать умение из слота (Delete)
        elif key == pygame.K_DELETE:
            self.game.player.skill_manager.unassign_from_slot(self.game.skill_book_window.selected_slot_index)
            print(f"Слот {self.game.skill_book_window.selected_slot_index + 1} очищен")

    def handle_key_press(self, key):
        """
        Обработка нажатия клавиш

        Args:
            key: Код нажатой клавиши
        """
        # Движение игрока (стрелки или WASD)
        moved = False
        new_x, new_y = self.game.player.x, self.game.player.y

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
            self.game.player.rest()
            self.game.game_time.advance_time(1/3, skip_player_recovery=True)
            print(f"Вы отдохнули. {self.game.game_time.get_time_string()}")
            return
        elif key == pygame.K_ESCAPE:
            self.game.running = False
        elif key == pygame.K_e:
            # Взаимодействие с NPC
            self.game._check_npc_nearby()
            return
        elif key == pygame.K_f:
            # Сбор ресурсов с локации
            self.game._collect_resources()
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
            self.game.skill_book_menu_open = not getattr(self.game, 'skill_book_menu_open', False)
            return
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                     pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
            # Использовать умение из слота (клавиши 1-8)
            slot_index = key - pygame.K_1  # Преобразуем код клавиши в индекс слота (0-7)
            skill = self.game.player.skill_manager.get_slot_skill(slot_index)
            if skill:
                # Используем умение вне боя (применяется только к ремесленным умениям)
                if skill.category.value == 'crafting':
                    # Проверяем требования к местности для ремесленных умений
                    tile = self.game.game_map.get_tile(self.game.player.x, self.game.player.y)
                    biome = tile.biome
                    location = tile.location if tile.has_location() else None

                    skill_id = self.game.player.skill_manager.skill_slots[slot_index]

                    # Проверяем рудокопство
                    if skill_id == 'mining':
                        mining = self.game.player.profession_manager.get_profession('mining')
                        can_use, msg = mining.can_use(self.game.player, location)
                        if not can_use:
                            print(msg)
                            return

                    # Проверяем лесорубство
                    elif skill_id == 'lumberjacking':
                        lumberjacking = self.game.player.profession_manager.get_profession('lumberjacking')
                        can_use, msg = lumberjacking.can_use(self.game.player, biome)
                        if not can_use:
                            print(msg)
                            return

                    result = self.game.player.skill_manager.use_skill_from_slot(slot_index)
                    print(result['message'])

                    # Обновляем прогресс квестов при добыче ресурсов
                    if result.get('success') and 'gathered' in result:
                        for item_key, quantity in result['gathered']:
                            messages = self.game.quest_manager.update_gather_progress(item_key, quantity, self.game.player)
                            for msg in messages:
                                print(f"  {msg}")
                else:
                    print(f"{skill.name} можно использовать только в бою!")
            else:
                print(f"Слот {slot_index + 1} пуст!")
            return
        elif key == pygame.K_i:
            # Открыть/закрыть инвентарь
            self.game.inventory_menu_open = not self.game.inventory_menu_open
            return
        elif key == pygame.K_c:
            # Открыть/закрыть окно характеристик
            self.game.character_menu_open = not self.game.character_menu_open
            return
        elif key == pygame.K_q:
            # Открыть окно квестов (можно просматривать активные из любого места)
            tile = self.game.game_map.get_tile(self.game.player.x, self.game.player.y)
            if tile.has_location():
                location = tile.location
                if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                    # В городе/деревне - полный доступ к квестам
                    self.game.open_quest_window(location)
                else:
                    # Вне города - только просмотр активных квестов
                    self.game.open_quest_window_anywhere()
            else:
                # Вне локации - только просмотр активных квестов
                self.game.open_quest_window_anywhere()
            return
        elif key == pygame.K_F1:
            # Открыть/закрыть окно помощи
            self.game.help_window.toggle()
            return
        elif key == pygame.K_F2:
            # Открыть/закрыть чит-меню
            self.game.cheat_menu_open = not self.game.cheat_menu_open
            return

        # Попытка переместить игрока
        if moved:
            # Проверяем выносливость перед движением
            if self.game.player.is_resting:
                print("Вы слишком устали и должны отдохнуть!")
                return

            if not self.game.player.consume_stamina():
                print("У вас недостаточно выносливости! Нажмите R для отдыха.")
                return

            # Игрок может проходить сквозь NPC (коллизии убраны)
            if self.game.player.move_to(new_x, new_y, self.game.game_map):
                # Продвигаем время на 20 минут (1/3 часа) за перемещение
                self.game.game_time.advance_time(1/3)

                # Обновляем системы событий
                if hasattr(self.game, 'weather_system'):
                    weather_msg = self.game.weather_system.update(1/3)
                    if weather_msg:
                        print(weather_msg)

                if hasattr(self.game, 'killstreak_system'):
                    self.game.killstreak_system.update(1/3)

                # Проверяем случайные события при путешествии
                if hasattr(self.game, 'random_event_system'):
                    event_messages = self.game.random_event_system.check_for_event(
                        self.game.player, self.game
                    )
                    if event_messages:
                        for msg in event_messages:
                            print(msg)
                        # Открываем окно события
                        if hasattr(self.game, 'event_window_open'):
                            self.game.event_window_open = True

                # Обновляем туман войны
                self.game.fog_of_war.update_vision(self.game.player.x, self.game.player.y)
                # Обновляем камеру
                self.game.camera.update()

                # Проверяем, есть ли локация на новой позиции
                tile = self.game.game_map.get_tile(self.game.player.x, self.game.player.y)
                if tile.has_location():
                    print(f"Вы прибыли в: {tile.location.name}")
                    print(f"  {tile.location.get_description()}")
                    print(f"Время: {self.game.game_time.get_time_string()}")

    def handle_quest_input(self, key):
        """
        Обработка ввода в окне квестов

        Args:
            key: Нажатая клавиша
        """
        if key == pygame.K_ESCAPE:
            self.game.quest_window_open = False
            return

        # Переключение вкладок
        if key == pygame.K_TAB:
            modes = ["available", "active", "turn_in"]
            current_idx = modes.index(self.game.quest_window.mode)
            self.game.quest_window.mode = modes[(current_idx + 1) % 3]
            self.game.quest_window.selected_index = 0
            self.game.quest_window.scroll_offset = 0
            return

        # Навигация по списку
        quests = self.game.quest_window.get_current_list()
        if key == pygame.K_UP or key == pygame.K_w:
            if quests:
                self.game.quest_window.selected_index = max(0, self.game.quest_window.selected_index - 1)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if quests:
                self.game.quest_window.selected_index = min(len(quests) - 1, self.game.quest_window.selected_index + 1)
        elif key == pygame.K_RETURN:
            # Принять или сдать квест
            quest = self.game.quest_window.get_selected_quest()
            if quest:
                if self.game.quest_window.mode == "available":
                    # Принять квест
                    success, message = self.game.quest_manager.accept_quest(
                        quest.quest_id,
                        self.game.quest_window.location_id,
                        self.game.player
                    )
                    print(message)
                    if success:
                        # Обновляем данные окна
                        self._refresh_quest_window()
                elif self.game.quest_window.mode == "turn_in":
                    # Сдать квест
                    success, messages = self.game.quest_manager.complete_quest(
                        quest.quest_id,
                        self.game.player
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
            if self.game.quest_window.mode == "active":
                quest = self.game.quest_window.get_selected_quest()
                if quest:
                    success, message = self.game.quest_manager.abandon_quest(quest.quest_id)
                    print(message)
                    if success:
                        # Обновляем данные окна
                        self._refresh_quest_window()

    def _refresh_quest_window(self):
        """Обновить данные в окне квестов"""
        location_id = self.game.quest_window.location_id
        location_name = self.game.quest_window.location_name

        # Проверяем прогресс всех квестов на сбор ресурсов
        self.game.quest_manager.check_all_quest_progress(self.game.player)

        available_quests = self.game.quest_manager.get_location_quests(location_id)
        active_quests = self.game.quest_manager.get_active_quests()
        turn_in_quests = self.game.quest_manager.get_quests_ready_to_turn_in(location_id)

        self.game.quest_window.set_data(
            location_name,
            location_id,
            available_quests,
            active_quests,
            turn_in_quests
        )

