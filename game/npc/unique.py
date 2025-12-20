"""
Уникальные NPC персонажи с особыми способностями и заданиями
"""
import random
from game.npc.base import NPC
from game.npc.merchant import Merchant
from game.constants import (
    RELATIONSHIP_HOSTILE, RELATIONSHIP_FRIENDLY, RELATIONSHIP_NEUTRAL,
    NPC_TYPE_UNDEAD
)
from game.item_registry import get_item


class Alchemist(Merchant):
    """
    Алхимик - специализируется на зельях и магических ингредиентах.
    Дает уникальные квесты на сбор редких материалов.
    Бродит вокруг своей лавки и убегает от врагов.
    """

    def __init__(self, name, x=0, y=0, level=10):
        """
        Инициализация Алхимика

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            level: Уровень NPC
        """
        super().__init__(name, x, y, level)
        self.npc_type = "alchemist"

        # AI параметры для активного поведения
        self.state = "wander"  # wander, rest, flee
        self.home_x = x  # Базовая позиция (лавка)
        self.home_y = y
        self.max_distance_from_home = 15  # Максимальная дистанция от лавки
        self.detection_range = 10  # Дальность обнаружения угроз
        self.threat = None  # Текущая угроза от которой убегаем
        self.wander_target = None  # Целевая точка для блуждания
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)  # Короткий отдых 2-4 часа
        self.steps_in_current_state = 0

        # Состояние по умолчанию для расписания
        self.default_state = "wander"

        self._adjust_alchemist_stats()
        self._generate_alchemist_goods()

    def _adjust_alchemist_stats(self):
        """Настройка характеристик алхимика"""
        # Алхимики умны и духовны (макс +5% для баланса)
        self.intelligence = int(self.intelligence * 1.05)
        self.spirit = int(self.spirit * 1.05)
        self.luck = int(self.luck * 1.03)
        # Но физически слабы, однако имеют бонус +10 к силе для переноски ингредиентов
        self.strength = int(self.strength * 0.7) + 10  # Бонус +10 к силе
        self.dexterity = int(self.dexterity * 0.8)
        self.update_derived_stats()

    def _generate_alchemist_goods(self):
        """Генерация товаров алхимика"""
        from game.inventory import ItemGenerator, ItemQuality

        # Очищаем стандартные товары торговца
        self.inventory.items.clear()

        # Зелья: Большие зелье здоровья, маны и выносливости
        potions = [
            ("greater_health_potion", random.randint(4, 8)),
            ("mana_potion", random.randint(5, 10)),
            ("stamina_potion", random.randint(4, 8)),
        ]

        for potion_key, quantity in potions:
            potion_item = get_item(potion_key)
            if potion_item:
                self.inventory.add_item(potion_item, quantity)

        # Ресурсы: магические кристаллы, осколки артефактов
        ingredients = [
            ("magic_crystal", random.randint(2, 4)),
            ("artifact_fragment", random.randint(2, 4)),
        ]

        for ing_key, quantity in ingredients:
            ing_item = get_item(ing_key)
            if ing_item:
                self.inventory.add_item(ing_item, quantity)

        # Рецепты алхимии: зелья здоровья, маны и выносливости (малые и средние)
        alchemy_recipes = [
            "recipe_minor_health_potion_recipe",
            "recipe_health_potion_recipe",
            "recipe_minor_mana_potion_recipe",
            "recipe_mana_potion_recipe",
            "recipe_minor_stamina_potion_recipe",
            "recipe_stamina_potion_recipe"
        ]

        # Добавляем все рецепты алхимии (по 1 штуке каждого)
        for recipe_key in alchemy_recipes:
            recipe_item = get_item(recipe_key)
            if recipe_item:
                self.inventory.add_item(recipe_item, 1)

        # Добавляем золото для торговли
        self.inventory.add_gold(random.randint(500, 1500) * 3)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """
        Обновление AI алхимика за 1 час игрового времени

        Args:
            context_or_map: AIContext или карта игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (0-23)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        self.steps_in_current_state += 1

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "wander":
            self._wander_step(game_map)
        elif self.state == "rest":
            self._rest_step()

    def _check_for_threats(self, all_npcs):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
        """
        from game.constants import NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY

        # Ищем ближайшую угрозу
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue
            if npc == self:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Если есть угроза и есть выносливость для бегства, убегаем
        if closest_threat and self.stamina > 0:
            self.threat = closest_threat
            self.state = "flee"
            self.steps_in_current_state = 0
        elif self.state == "flee" and not closest_threat:
            # Если угрозы больше нет, возвращаемся к блужданию
            self.threat = None
            self.state = "wander"
            self.steps_in_current_state = 0

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к блужданию
        if not self.threat or not self.threat.is_alive:
            self.threat = None
            self.state = "wander"
            self.steps_in_current_state = 0
            return

        # Если нет выносливости, переходим в отдых
        if self.stamina <= 0:
            self.state = "rest"
            self.steps_in_current_state = 0
            return

        # Убегаем в противоположную от угрозы сторону
        dx_away = self.x - self.threat.x
        dy_away = self.y - self.threat.y

        # Нормализуем направление
        if dx_away > 0:
            dx = 1
        elif dx_away < 0:
            dx = -1
        else:
            dx = 0

        if dy_away > 0:
            dy = 1
        elif dy_away < 0:
            dy = -1
        else:
            dy = 0

        # Если оба направления 0, выбираем случайное
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        # Пытаемся двигаться (тратим выносливость)
        if self.consume_stamina():
            new_x = self.x + dx
            new_y = self.y + dy

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
            else:
                # Если не можем идти прямо, пробуем другие направления
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                random.shuffle(directions)
                for alt_dx, alt_dy in directions:
                    new_x = self.x + alt_dx
                    new_y = self.y + alt_dy
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        break

    def _wander_step(self, game_map):
        """
        Один шаг блуждания вокруг лавки

        Args:
            game_map: Объект карты игры
        """
        # Проверяем расстояние до дома (лавки)
        distance_to_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)

        # Если слишком далеко от дома, возвращаемся
        if distance_to_home > self.max_distance_from_home:
            dx, dy = self._find_next_step(self.home_x, self.home_y, game_map, max_search_distance=50)
            if dx != 0 or dy != 0:
                if self.consume_stamina():
                    if self._can_move(self.x + dx, self.y + dy, game_map):
                        self.x += dx
                        self.y += dy
            return

        # Если достигли цели блуждания или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_wander_target()

        # Идем к цели блуждания
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=30)
            if dx != 0 or dy != 0:
                if self.consume_stamina():
                    if self._can_move(self.x + dx, self.y + dy, game_map):
                        self.x += dx
                        self.y += dy

        # Случайный отдых (15% шанс - алхимики любят отдыхать и работать над зельями)
        if random.random() < 0.15:
            self.state = "rest"
            self.rest_counter = 0
            self.rest_duration = random.randint(2, 4)
            self.steps_in_current_state = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для блуждания в пределах территории лавки"""
        # Выбираем случайную точку в пределах радиуса от дома
        max_offset = min(self.max_distance_from_home, 10)  # Ограничиваем радиус блуждания

        target_x = self.home_x + random.randint(-max_offset, max_offset)
        target_y = self.home_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest_step(self):
        """Отдых - обновляется каждый игровой час"""
        # Восстанавливаем выносливость активно во время отдыха
        self.recover_stamina(is_active_rest=True)

        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "wander"
            self.rest_counter = 0
            self.steps_in_current_state = 0
            self.rest_duration = random.randint(2, 4)


class Hunter(NPC):
    """
    Охотник - опытный следопыт и боец.
    Патрулирует дикие территории и охотится на монстров.
    Может давать квесты на охоту.
    """

    def __init__(self, name, x=0, y=0, level=15, home_x=None, home_y=None):
        """
        Инициализация Охотника

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            level: Уровень NPC
            home_x: X координата дома охотника
            home_y: Y координата дома охотника
        """
        super().__init__(name, x, y, npc_type="hunter", level=level)
        self.home_x = home_x if home_x is not None else x
        self.home_y = home_y if home_y is not None else y
        self._adjust_hunter_stats()

        # AI параметры
        self.state = "patrol"  # patrol, rest, hunt, return_home, returning_to_town, resting
        self.detection_range = 12
        self.hunt_target = None
        self.max_distance_from_home = 30
        self.steps_in_current_state = 0
        self.max_steps_patrol = random.randint(8, 15)

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

    def _adjust_hunter_stats(self):
        """Настройка характеристик охотника"""
        # Охотники ловкие и наблюдательные (макс +5% для баланса)
        self.dexterity = int(self.dexterity * 1.05)
        self.luck = int(self.luck * 1.05)
        self.strength = int(self.strength * 1.04)
        self.constitution = int(self.constitution * 1.03)
        # Средний интеллект и дух
        self.intelligence = int(self.intelligence * 0.9)
        self.spirit = int(self.spirit * 0.9)
        self.update_derived_stats()

        # Охотники дружелюбны к игрокам
        self.relationship = RELATIONSHIP_FRIENDLY

    def _generate_initial_equipment(self):
        """Генерация экипировки охотника"""
        from game.inventory import ItemGenerator, ItemQuality, WeaponType

        # Лук - основное оружие охотника
        bow = ItemGenerator.generate_weapon(
            self.level,
            quality=ItemQuality.UNCOMMON
        )
        bow.name = "Охотничий лук"
        bow.weapon_type = WeaponType.BOW
        if self.inventory.add_item(bow, 1):
            self.inventory.equip_item(bow.name)

        # Легкая броня
        armor = ItemGenerator.generate_armor(
            self.level,
            quality=ItemQuality.UNCOMMON
        )
        if self.inventory.add_item(armor, 1):
            self.inventory.equip_item(armor.name)

        self.update_derived_stats()

    def update_ai(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map
            context = None
        """
        Обновление AI охотника

        Args:
            game_map: Карта игры
            all_npcs: Список всех NPC
            player: Игрок
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Проверяем только что ли появился после отдыха
        if self.state == "resting":
            self._handle_appearance()
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        self.steps_in_current_state += 1

        if self.state == "patrol":
            self._patrol_step(game_map, all_npcs)
        elif self.state == "hunt":
            self._hunt_step(game_map, all_npcs, context)
        elif self.state == "rest":
            self._rest_step()
        elif self.state == "return_home":
            self._return_home_step(game_map)
        elif self.state == "returning_to_town":
            self._returning_to_town_step(game_map)

    def _patrol_step(self, game_map, all_npcs):
        """Шаг патрулирования"""
        # Проверяем расстояние от дома
        distance_from_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
        if distance_from_home > self.max_distance_from_home:
            self.state = "return_home"
            return

        # Ищем цели для охоты (приоритет - животные, потом враги)
        target = self._find_hunt_target(all_npcs)
        if target:
            self.hunt_target = target
            self.state = "hunt"
            self.steps_in_current_state = 0
            return

        # Патрулируем случайно
        if self.steps_in_current_state >= self.max_steps_patrol:
            self.state = "rest"
            self.steps_in_current_state = 0
            return

        # Случайное движение
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        new_x = self.x + dx
        new_y = self.y + dy

        if self._can_move(new_x, new_y, game_map):
            self.x = new_x
            self.y = new_y

    def _hunt_step(self, game_map, all_npcs, context=None):
        """Шаг охоты на цель"""
        if not self.hunt_target or not self.hunt_target.is_alive:
            self.hunt_target = None
            self.state = "patrol"
            self.steps_in_current_state = 0
            return

        # Проверяем, не вышла ли цель за пределы patrol_radius от дома
        distance_target_to_home = abs(self.hunt_target.x - self.home_x) + abs(self.hunt_target.y - self.home_y)
        if distance_target_to_home > self.max_distance_from_home:
            # Цель ушла за пределы patrol_radius - прекращаем охоту
            self.hunt_target = None
            self.state = "patrol"
            self.steps_in_current_state = 0
            return

        # Проверяем, не слишком ли далеко охотник от дома
        distance_from_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
        if distance_from_home > self.max_distance_from_home:
            # Вышли за пределы patrol_radius - возвращаемся
            self.hunt_target = None
            self.state = "return_home"
            self.steps_in_current_state = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.hunt_target):
            # Используем упрощенный бой для NPC vs NPC
            target_type = self.hunt_target.npc_type
            enemy_killed = self._simplified_npc_combat(self.hunt_target, context)
            if enemy_killed:
                print(f"{self.name} победил {self.hunt_target.name} в быстром бою!")

                # Если убили животное - идем в город на отдых
                if target_type in ['wolf', 'bear', 'deer']:
                    print(f"{self.name} убил {target_type} и возвращается в город для отдыха")
                    self.hunt_target = None
                    self.state = "returning_to_town"
                    self.steps_in_current_state = 0
                else:
                    # Если убили врага - продолжаем патрулирование
                    self.hunt_target = None
                    self.state = "patrol"
                    self.steps_in_current_state = 0
            return

        # Двигаемся к цели
        dx, dy = self._find_next_step(
            self.hunt_target.x, self.hunt_target.y, game_map
        )
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy

            # Проверяем, не выведет ли это движение за пределы patrol_radius
            new_distance_from_home = abs(new_x - self.home_x) + abs(new_y - self.home_y)
            if new_distance_from_home > self.max_distance_from_home:
                # Движение выведет за пределы - прекращаем охоту
                self.hunt_target = None
                self.state = "patrol"
                self.steps_in_current_state = 0
                return

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
        else:
            # Не можем найти путь
            self.hunt_target = None
            self.state = "patrol"
            self.steps_in_current_state = 0

    def _rest_step(self):
        """Шаг отдыха"""
        self.recover_stamina(is_active_rest=True)
        if self.steps_in_current_state >= random.randint(2, 4):
            self.state = "patrol"
            self.steps_in_current_state = 0
            self.max_steps_patrol = random.randint(8, 15)

    def _return_home_step(self, game_map):
        """Возвращение домой"""
        if abs(self.x - self.home_x) <= 5 and abs(self.y - self.home_y) <= 5:
            self.state = "patrol"
            self.steps_in_current_state = 0
            return

        dx, dy = self._find_next_step(self.home_x, self.home_y, game_map)
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y

    def _returning_to_town_step(self, game_map):
        """
        Возвращение в город после удачной охоты.
        При достижении дома - скрывается для отдыха на 20 ходов.

        Args:
            game_map: Объект карты игры
        """
        # Проверяем, достигли ли дома (точное попадание на клетку)
        if self.x == self.home_x and self.y == self.home_y:
            # Достигли дома - начинаем отдыхать
            self.state = "resting"
            rest_duration = 20  # 20 ходов отдыха
            self.hide_from_map(rest_duration, f"Город (отдых после охоты)")
            print(f"{self.name} достиг города и отдыхает {rest_duration} ходов")
            return

        # Проверяем выносливость
        if not self.consume_stamina():
            return  # Нет выносливости

        # Делаем шаг к дому
        dx, dy = self._find_next_step(self.home_x, self.home_y, game_map, max_search_distance=100)
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy

    def _handle_appearance(self):
        """
        Обработка появления NPC на карте после скрытия.
        Возвращает охотника к патрулированию.
        """
        if self.state == "resting":
            # Закончили отдыхать - возвращаемся к патрулированию
            print(f"{self.name} закончил отдых и возвращается к патрулированию")
            self.state = "patrol"
            self.steps_in_current_state = 0

    def _find_hunt_target(self, all_npcs):
        """
        Найти цель для охоты

        Приоритет целей:
        1. Животные (wolf, bear, deer) в пределах patrol_radius от дома
        2. Враги (bandit, undead, necromancer) в detection_range

        Returns:
            NPC или None
        """
        if not all_npcs:
            return None

        # Список животных и врагов в зоне обнаружения
        animals_in_range = []
        enemies_in_range = []

        for npc in all_npcs:
            if not npc.is_alive:
                continue
            if npc == self:
                continue

            distance_to_target = abs(self.x - npc.x) + abs(self.y - npc.y)

            # Проверяем, что цель находится в пределах обнаружения
            if distance_to_target > self.detection_range:
                continue

            # Проверяем, что цель не уведет охотника за пределы patrol_radius от дома
            # (для охотников-стражников)
            distance_target_to_home = abs(npc.x - self.home_x) + abs(npc.y - self.home_y)
            if distance_target_to_home > self.max_distance_from_home:
                continue

            # Разделяем на животных и врагов
            if npc.npc_type in ['wolf', 'bear', 'deer']:
                animals_in_range.append((distance_to_target, npc))
            elif npc.npc_type in ['bandit', 'undead', 'necromancer']:
                enemies_in_range.append((distance_to_target, npc))

        # Приоритет 1: Ближайшее животное
        if animals_in_range:
            animals_in_range.sort(key=lambda x: x[0])  # Сортируем по расстоянию
            return animals_in_range[0][1]

        # Приоритет 2: Ближайший враг
        if enemies_in_range:
            enemies_in_range.sort(key=lambda x: x[0])
            return enemies_in_range[0][1]

        return None


class Necromancer(NPC):
    """
    Некромант - враждебный маг, повелевающий нежитью.
    Обитает в руинах и представляет серьезную угрозу.
    """

    def __init__(self, name, x=0, y=0, level=20, ruins_x=None, ruins_y=None):
        """
        Инициализация Некроманта

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            level: Уровень NPC
            ruins_x: X координата руин
            ruins_y: Y координата руин
        """
        super().__init__(name, x, y, npc_type="necromancer", level=level)
        self.ruins_x = ruins_x if ruins_x is not None else x
        self.ruins_y = ruins_y if ruins_y is not None else y
        self._adjust_necromancer_stats()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.detection_range = 15
        self.target = None
        self.max_distance_from_ruins = 20
        self.steps_in_current_state = 0
        self.pursuit_steps = 0
        self.max_pursuit_steps = 15

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

        # Некроманты всегда враждебны
        self.relationship = RELATIONSHIP_HOSTILE

        # Магические способности
        self.max_mana = self.spirit * 15
        self.mana = self.max_mana

    def _adjust_necromancer_stats(self):
        """Настройка характеристик некроманта"""
        # Некроманты умны и духовны (макс +5% для баланса)
        self.intelligence = int(self.intelligence * 1.05)
        self.spirit = int(self.spirit * 1.05)
        # Но физически слабы
        self.strength = int(self.strength * 0.6)
        self.constitution = int(self.constitution * 0.8)
        self.dexterity = int(self.dexterity * 0.7)
        # Слегка повышенная удача
        self.luck = int(self.luck * 1.04)
        self.update_derived_stats()

    def _generate_initial_equipment(self):
        """Генерация экипировки некроманта"""
        from game.inventory import ItemGenerator, ItemQuality, ArmorType, EquipmentSlot, WeaponType

        # Посох тьмы - мощное магическое оружие
        staff = ItemGenerator.generate_weapon(
            self.level,
            quality=ItemQuality.EPIC
        )
        staff.name = "Посох Тьмы"
        staff.weapon_type = WeaponType.STAFF
        if self.inventory.add_item(staff, 1):
            self.inventory.equip_item(staff.name)

        # Мантия некроманта
        robe = ItemGenerator.generate_armor(
            self.level,
            slot=EquipmentSlot.CHEST,
            armor_type=ArmorType.LIGHT,
            quality=ItemQuality.RARE
        )
        if self.inventory.add_item(robe, 1):
            self.inventory.equip_item(robe.name)

        # Кольцо силы
        ring = ItemGenerator.generate_jewelry(self.level, quality=ItemQuality.RARE)
        if self.inventory.add_item(ring, 1):
            self.inventory.equip_item(ring.name)

        self.update_derived_stats()

    def update_ai(self, context_or_map, all_npcs=None, player=None, current_hour=12):
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map
            context = None
        """
        Обновление AI некроманта

        Args:
            game_map: Карта игры
            all_npcs: Список всех NPC
            player: Игрок
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Восстанавливаем ману
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + 3)

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        self.steps_in_current_state += 1

        if self.state == "patrol":
            self._patrol_step(game_map, all_npcs, player)
        elif self.state == "combat":
            self._combat_step(game_map, all_npcs, player, context)
        elif self.state == "rest":
            self._rest_step()

    def _patrol_step(self, game_map, all_npcs, player):
        """Шаг патрулирования"""
        # Проверяем расстояние от руин
        distance_from_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Ищем врагов
        target = self._find_target(all_npcs, player)
        if target:
            self.target = target
            self.state = "combat"
            self.steps_in_current_state = 0
            self.pursuit_steps = 0
            return

        # Если слишком далеко от руин - возвращаемся
        if distance_from_ruins > self.max_distance_from_ruins:
            dx, dy = self._find_next_step(self.ruins_x, self.ruins_y, game_map)
            if dx != 0 or dy != 0:
                new_x = self.x + dx
                new_y = self.y + dy
                if self._can_move(new_x, new_y, game_map):
                    self.x = new_x
                    self.y = new_y
            return

        # Патрулируем или отдыхаем
        if self.steps_in_current_state >= random.randint(5, 10):
            self.state = "rest"
            self.steps_in_current_state = 0
            return

        # Случайное движение в пределах руин
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        new_x = self.x + dx
        new_y = self.y + dy

        # Проверяем, не уходим ли слишком далеко
        new_distance = abs(new_x - self.ruins_x) + abs(new_y - self.ruins_y)
        if new_distance <= self.max_distance_from_ruins:
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y

    def _combat_step(self, game_map, all_npcs, player, context=None):
        """Шаг боя"""
        if not self.target or not self.target.is_alive:
            self.target = None
            self.state = "patrol"
            self.steps_in_current_state = 0
            return

        # Проверяем расстояние преследования
        self.pursuit_steps += 1
        if self.pursuit_steps > self.max_pursuit_steps:
            self.target = None
            self.state = "patrol"
            self.steps_in_current_state = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target):
            # Используем упрощенный бой для NPC vs NPC
            enemy_killed = self._simplified_npc_combat(self.target, context)
            if enemy_killed:
                print(f"{self.name} победил {self.target.name} в быстром бою!")
                self.target = None
                self.state = "patrol"
                self.steps_in_current_state = 0
                self.pursuit_steps = 0
            return

        # Двигаемся к цели
        dx, dy = self._find_next_step(
            self.target.x, self.target.y, game_map
        )
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
        else:
            # Не можем найти путь
            self.target = None
            self.state = "patrol"

    def _rest_step(self):
        """Шаг отдыха и восстановления маны"""
        self.recover_stamina(is_active_rest=True)
        # Восстанавливаем ману
        self.mana = min(self.max_mana, self.mana + self.spirit)

        if self.steps_in_current_state >= random.randint(2, 4):
            self.state = "patrol"
            self.steps_in_current_state = 0

    def _find_target(self, all_npcs, player):
        """Найти цель для атаки"""
        targets = []

        # Проверяем игрока
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range:
                targets.append((player, distance))

        # Проверяем NPC (атакуем всех, кроме нежити)
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue
                if npc == self:
                    continue
                # Не атакуем нежить и других некромантов
                if npc.npc_type in ['undead', 'necromancer']:
                    continue

                distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                if distance <= self.detection_range:
                    targets.append((npc, distance))

        # Выбираем ближайшую цель
        if targets:
            targets.sort(key=lambda x: x[1])
            return targets[0][0]

        return None

    def get_total_damage(self):
        """Получить урон с учетом магической силы"""
        base_damage = super().get_total_damage()
        # Бонус от интеллекта для магической атаки
        magic_bonus = max(1, self.intelligence // 2)
        return base_damage + magic_bonus
