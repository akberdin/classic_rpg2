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
        # Алхимики не путешествуют, всегда отдыхают (для ротации товаров)
        self.state = "rest"
        self.rest_counter = 0
        self.rest_duration = 999999  # Бесконечный отдых
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
        self.state = "patrol"  # patrol, rest, hunt, return_home
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

    def _patrol_step(self, game_map, all_npcs):
        """Шаг патрулирования"""
        # Проверяем расстояние от дома
        distance_from_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
        if distance_from_home > self.max_distance_from_home:
            self.state = "return_home"
            return

        # Ищем врагов (бандитов и нежить)
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

        # Проверяем, можем ли атаковать
        if self.can_attack(self.hunt_target):
            # Используем упрощенный бой для NPC vs NPC
            enemy_killed = self._simplified_npc_combat(self.hunt_target, context)
            if enemy_killed:
                print(f"{self.name} победил {self.hunt_target.name} в быстром бою!")
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
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
        else:
            # Не можем найти путь
            self.hunt_target = None
            self.state = "patrol"

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

    def _find_hunt_target(self, all_npcs):
        """Найти цель для охоты"""
        if not all_npcs:
            return None

        for npc in all_npcs:
            if not npc.is_alive:
                continue
            if npc == self:
                continue

            # Охотимся на бандитов, нежить и животных
            if npc.npc_type in ['bandit', 'undead', 'necromancer', 'wolf', 'bear', 'deer']:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                if distance <= self.detection_range:
                    return npc

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
