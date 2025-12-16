"""
Модуль игрока - содержит класс Player.

Player наследуется от Character и добавляет функциональность,
специфичную для игрока: опыт, уровни, инвентарь, профессии.
"""

import random
from game.character import Character
from game.inventory import Inventory
from game.constants import MAX_LEVEL, RANKS


class Player(Character):
    """Класс игрока"""

    def __init__(self, name="Hero", x=0, y=0):
        """
        Инициализация игрока

        Args:
            name: Имя игрока
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        super().__init__(name, x, y)

        # Устанавливаем базовые характеристики игрока
        self.strength = 1
        self.dexterity = 1
        self.constitution = 1
        self.spirit = 1
        self.intelligence = 1
        self.luck = 1

        # Дополнительные параметры игрока
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100  # Опыт для следующего уровня
        self.stat_points = 0  # Нераспределенные очки характеристик

        # Параметр маг (по умолчанию - нет)
        self.is_mage = False

        # Мана зависит от духа (1 дух = 10 маны)
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

        # Обновляем производные характеристики (здоровье, выносливость)
        self.update_derived_stats()

        # Инвентарь (передаём self как владельца для системы умений от предметов)
        # По умолчанию 5 слотов, можно увеличить рюкзаком
        self.inventory = Inventory(max_slots=5, owner=self)
        # Обновляем грузоподъемность на основе силы
        self.inventory.update_max_weight(self.strength)

        # Менеджер навыков
        from game.skills import SkillManager
        self.skill_manager = SkillManager(self)

        # Менеджер профессий
        from game.professions import ProfessionManager
        self.profession_manager = ProfessionManager()

        # Менеджер спутников
        from game.companion_manager import CompanionManager
        self.companion_manager = CompanionManager()

        # Чит-мод (бессмертие)
        self.godmode = False

        # Атрибуты для достижений
        self.enemies_killed = 0
        self.visited_location_types = set()
        self.items_sold = 0
        self.resources_collected = 0

        # Флаг оглушения
        self.stunned = False

        # Временный бонус к силе (от навыков)
        self.temp_strength_boost = 0

        # Флаг атаки от NPC (для принудительного открытия окна боя)
        self.attacked_by_npc = None

        # Изученные рецепты крафта
        self.known_recipes = set()

    def get_effective_max_mana(self):
        """
        Получить эффективную максимальную ману с учетом бонусов от экипировки

        Returns:
            int: Эффективная максимальная мана
        """
        base_spirit = self.spirit

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_spirit += equipment_bonus.get('spirit', 0)

        base_max_mana = base_spirit * 10

        # Добавляем процентный бонус от param_bonus (округляем до целого)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_param_bonus'):
            param_bonus = self.inventory.get_total_param_bonus()
            mana_percent_bonus = param_bonus.get('mana', 0)
            if mana_percent_bonus > 0:
                base_max_mana = int(base_max_mana * (1 + mana_percent_bonus / 100))

        return base_max_mana

    def can_move_to(self, x, y, game_map):
        """
        Проверить, может ли игрок переместиться на данную клетку

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если можно переместиться
        """
        # Проверка границ карты
        if x < 0 or x >= game_map.width or y < 0 or y >= game_map.height:
            return False

        # Проверка проходимости тайла
        tile = game_map.get_tile(x, y)
        return tile.is_passable()

    def move_to(self, x, y, game_map):
        """
        Переместить игрока на указанную позицию с проверкой

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если перемещение успешно
        """
        if self.can_move_to(x, y, game_map):
            self.x = x
            self.y = y
            return True
        return False

    def add_experience(self, amount):
        """
        Добавить опыт игроку

        Args:
            amount: Количество опыта

        Returns:
            bool: True если произошло повышение уровня
        """
        self.experience += amount
        leveled_up = False

        # Проверяем, достаточно ли опыта для повышения уровня
        while self.experience >= self.experience_to_next_level:
            leveled_up = True
            self.level_up()

        # Добавляем опыт спутникам (30% от полученного опыта)
        if hasattr(self, 'companion_manager'):
            companion_exp = int(amount * 0.3)
            if companion_exp > 0:
                leveled_companions = self.companion_manager.add_experience_to_all(companion_exp)
                for companion_id, companion_leveled in leveled_companions:
                    if companion_leveled:
                        companion = self.companion_manager.get_companion(companion_id)
                        if companion:
                            print(f"{companion.name} повысил уровень! Теперь {companion.level} уровень")

        return leveled_up

    def level_up(self):
        """Повысить уровень игрока"""
        # Проверяем, не достигнут ли максимальный уровень
        if self.level >= MAX_LEVEL:
            print(f"Вы достигли максимального уровня {MAX_LEVEL}!")
            self.experience = 0
            return

        self.experience -= self.experience_to_next_level
        self.level += 1

        # Увеличиваем требуемый опыт для следующего уровня (менее агрессивный рост)
        self.experience_to_next_level = int(self.experience_to_next_level * 1.35)

        # Даем игроку 3 очка характеристик для распределения
        self.stat_points += 3

        # Обновляем производные характеристики
        self.update_derived_stats()

        # Обновляем максимальную ману (пропорционально увеличиваем текущую)
        old_max_mana = getattr(self, 'max_mana', 0)
        self.max_mana = self.spirit * 10
        if old_max_mana > 0:
            mana_diff = self.max_mana - old_max_mana
            self.mana = min(self.max_mana, self.mana + mana_diff)
        else:
            self.mana = self.max_mana

        # Получаем ранг
        rank = self.get_rank()
        print(f"Поздравляем! Вы достигли {self.level} уровня! Ранг: {rank}")
        print(f"Вы получили 3 очка характеристик! Нажмите C для их распределения.")

    def add_stat_point(self, stat_name):
        """
        Распределить очко характеристики

        Args:
            stat_name: Название характеристики

        Returns:
            bool: True если удалось распределить
        """
        if self.stat_points <= 0:
            return False

        stat_map = {
            'strength': 'strength',
            'dexterity': 'dexterity',
            'constitution': 'constitution',
            'spirit': 'spirit',
            'intelligence': 'intelligence',
            'luck': 'luck'
        }

        if stat_name in stat_map:
            setattr(self, stat_map[stat_name], getattr(self, stat_map[stat_name]) + 1)
            self.stat_points -= 1

            # Обновляем максимальную ману если изменился дух (сохраняем процент от эффективного максимума)
            if stat_name == 'spirit':
                old_effective_max_mana = self.get_effective_max_mana()
                mana_percent = self.mana / old_effective_max_mana if old_effective_max_mana > 0 else 1.0

                self.max_mana = self.spirit * 10

                # Восстанавливаем ману на основе сохраненного процента от нового эффективного максимума
                new_effective_max_mana = self.get_effective_max_mana()
                self.mana = int(new_effective_max_mana * mana_percent)

            # Обновляем производные характеристики
            self.update_derived_stats()

            # Обновляем грузоподъемность если изменилась сила
            if stat_name == 'strength':
                self.update_inventory_max_weight()

            return True

        return False

    def update_inventory_max_weight(self):
        """
        Обновить максимальный вес инвентаря с учетом бонусов от экипировки
        Этот метод нужно вызывать при изменении силы или экипировки
        """
        effective_strength = self.get_effective_strength()
        self.inventory.update_max_weight(effective_strength)

    def recover_mana(self, is_active_rest=False):
        """
        Восстановить ману (вызывается каждый игровой час)

        Args:
            is_active_rest: True если это активный отдых (команда R)
        """
        # Получаем эффективное значение с учетом экипировки
        effective_max_mana = self.get_effective_max_mana()

        if self.mana < effective_max_mana:
            # Получаем эффективный дух с учетом экипировки
            effective_spirit = self.get_effective_spirit()

            # При активном отдыхе восстанавливаем на основе духа
            if is_active_rest:
                # Каждая единица духа повышает скорость восстановления на 0.5% от максимума
                recovery = max(1, int(effective_max_mana * effective_spirit * 0.005))
            else:
                # При обычном движении восстановления нет (только отдых и зелья)
                recovery = 0

            self.mana = min(effective_max_mana, self.mana + recovery)

    def rest(self):
        """
        Отдых - восстанавливает здоровье, ману и выносливость
        Занимает 1 час игрового времени

        Использует методы recover_* с флагом is_active_rest=True для восстановления
        """
        # Используем эффективные значения с учетом бонусов от экипировки
        effective_max_health = self.get_effective_max_health()
        effective_max_mana = self.get_effective_max_mana()
        effective_max_stamina = self.get_effective_max_stamina()

        # Сохраняем текущие значения для подсчета восстановленных
        old_health = self.health
        old_mana = self.mana
        old_stamina = self.stamina

        # Восстанавливаем здоровье используя метод recover_health
        self.recover_health(is_active_rest=True)
        health_restored = self.health - old_health

        # Восстанавливаем ману используя метод recover_mana
        self.recover_mana(is_active_rest=True)
        mana_restored = self.mana - old_mana

        # Восстанавливаем выносливость (используя активный отдых)
        # Временно устанавливаем max_stamina на эффективное значение
        original_max_stamina = self.max_stamina
        self.max_stamina = effective_max_stamina
        self.recover_stamina(is_active_rest=True)
        self.max_stamina = original_max_stamina
        stamina_restored = self.stamina - old_stamina

        print(f"Здоровье восстановлено: +{health_restored} ({self.health}/{effective_max_health})")
        print(f"Мана восстановлена: +{mana_restored} ({self.mana}/{effective_max_mana})")
        print(f"Выносливость восстановлена: +{stamina_restored} ({self.stamina}/{effective_max_stamina})")

        # Восстанавливаем здоровье и выносливость спутников
        if hasattr(self, 'companion_manager') and self.companion_manager:
            companion_recovery = self.companion_manager.rest_all_companions()
            if companion_recovery:
                print("\nСпутники также отдохнули:")
                for info in companion_recovery:
                    if info['health_restored'] > 0 or info['stamina_restored'] > 0:
                        print(f"  {info['name']}: здоровье +{info['health_restored']} ({info['current_health']}/{info['max_health']}), "
                              f"выносливость +{info['stamina_restored']} ({info['current_stamina']}/{info['max_stamina']})")

    def work(self, game_map=None):
        """
        Работа - сбор ресурсов с использованием профессий или получение золота
        Занимает 1 час игрового времени

        Args:
            game_map: Карта игры (для определения биома и локации)
        """
        if not game_map:
            # Простая работа за золото
            gold_gained = 5 + self.level
            self.inventory.add_gold(gold_gained)
            print(f"Вы поработали и получили {gold_gained} золота")
            return

        # Получаем текущий тайл
        tile = game_map.get_tile(self.x, self.y)
        biome = tile.biome
        location = tile.location if tile.has_location() else None

        # Попытка использовать профессии
        resources_gathered = False

        # Проверяем рудокопство
        mining = self.profession_manager.get_profession('mining')
        can_mine, mine_msg = mining.can_use(self, location)
        if can_mine:
            resources = mining.gather(self)
            if resources:
                for item, quantity in resources:
                    self.inventory.add_item(item, quantity)
                    print(f"Добыто: {item.name} x{quantity}")
                    self.resources_collected += 1
                resources_gathered = True
            else:
                print("Вам не удалось ничего добыть в этот раз.")
                resources_gathered = True

        # Проверяем лесорубство
        lumberjacking = self.profession_manager.get_profession('lumberjacking')
        can_lumber, lumber_msg = lumberjacking.can_use(self, biome)
        if can_lumber and not resources_gathered:
            resources = lumberjacking.gather(self)
            if resources:
                for item, quantity in resources:
                    self.inventory.add_item(item, quantity)
                    print(f"Срублено: {item.name} x{quantity}")
                    self.resources_collected += 1
                resources_gathered = True
            else:
                print("Вам не удалось ничего добыть в этот раз.")
                resources_gathered = True

        # Если не удалось использовать профессии, работаем за золото
        if not resources_gathered:
            gold_gained = 5 + self.level
            self.inventory.add_gold(gold_gained)
            print(f"Вы поработали и получили {gold_gained} золота")

    def use_item(self, item_name):
        """
        Использовать предмет из инвентаря

        Args:
            item_name: Название предмета

        Returns:
            str: Сообщение о результате
        """
        item_data = self.inventory.get_item(item_name)
        if not item_data:
            return "Предмет не найден в инвентаре"

        item, quantity = item_data

        # Проверяем тип предмета
        if item.item_type == "potion":
            # Используем зелье
            result = item.use(self)
            self.inventory.remove_item(item_name, 1)
            return result
        elif item.item_type == "skill_book":
            # Используем книгу умения
            result = item.use(self)
            # Удаляем книгу только если умение было успешно изучено
            if "Изучено умение" in result:
                self.inventory.remove_item(item_name, 1)
            return result
        else:
            return "Этот предмет нельзя использовать"
