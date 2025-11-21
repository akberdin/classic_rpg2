"""
Класс Мага-патрульного с AI патрулирования территории академии
"""
import random
from game.npc.base import NPC
from game.constants import (
    NPC_TYPE_MAGE, NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD
)


class MagePatrol(NPC):
    """Класс Мага-патрульного с AI патрулирования территории академии"""

    def __init__(self, name, x=0, y=0, level=8, academy_x=None, academy_y=None):
        """
        Инициализация Мага-патрульного

        Args:
            name: Имя мага
            x: Позиция X
            y: Позиция Y
            level: Уровень мага
            academy_x: Координата X академии
            academy_y: Координата Y академии
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MAGE, level=level)

        # Модификация статов для мага: высокие интеллект и дух, низкие сила и ловкость
        self._adjust_mage_stats()

        # Генерация магических товаров для торговли
        self._generate_magical_goods()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.academy_x = academy_x if academy_x is not None else x  # Позиция академии
        self.academy_y = academy_y if academy_y is not None else y
        self.max_distance_from_academy = 20  # Радиус патрулирования от академии
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)  # Отдых 2-4 часа
        self.steps_per_hour = 1  # Шагов за час
        self.patrol_point_index = 0
        self.patrol_points = self._generate_patrol_points()
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range = 12  # Дальность обнаружения врагов
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 6  # Маги не любят долго преследовать

        # Состояние по умолчанию для расписания
        self.default_state = "patrol"

    def _adjust_mage_stats(self):
        """Модификация статов для мага - заклинатель, не воин"""
        # Повышаем магические характеристики (макс +5% для баланса)
        self.intelligence = int(self.intelligence * 1.05)
        self.spirit = int(self.spirit * 1.05)

        # Значительно снижаем боевые характеристики
        self.strength = max(1, int(self.strength * 0.4))
        self.dexterity = max(1, int(self.dexterity * 0.5))

        # Телосложение немного снижаем
        self.constitution = max(1, int(self.constitution * 0.7))

        # Обновляем производные статы
        self.update_derived_stats()

        # Обновляем ману на основе духа
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

    def _generate_magical_goods(self):
        """Генерация магических товаров для продажи"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Стартовое золото
        self.inventory.add_gold(500 + self.level * 50)

        # Книги лечебной магии
        self.inventory.add_item(PREDEFINED_ITEMS["book_heal"], 1)

        if self.level >= 5:
            self.inventory.add_item(PREDEFINED_ITEMS["book_regeneration"], 1)

        # Книги атакующей магии (зависят от уровня мага)
        if self.level >= 8:
            self.inventory.add_item(PREDEFINED_ITEMS["book_magic_missile"], 1)

        if self.level >= 12:
            if random.random() < 0.5:
                self.inventory.add_item(PREDEFINED_ITEMS["book_ice_bolt"], 1)

        if self.level >= 15:
            if random.random() < 0.3:
                self.inventory.add_item(PREDEFINED_ITEMS["book_fireball"], 1)

        if self.level >= 20:
            if random.random() < 0.1:
                self.inventory.add_item(PREDEFINED_ITEMS["book_lightning"], 1)

        # Зелья маны
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(2, 4))
        if self.level >= 10:
            self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(1, 2))

        # Магические украшения
        if random.random() < 0.5:
            jewelry = ItemGenerator.generate_jewelry(self.level)
            self.inventory.add_item(jewelry, 1)

    def _generate_patrol_points(self):
        """Генерация точек патрулирования вокруг академии"""
        points = []
        # Создаем квадратный маршрут вокруг академии
        offsets = [
            (-8, -8), (0, -8), (8, -8),
            (8, 0), (8, 8),
            (0, 8), (-8, 8),
            (-8, 0)
        ]
        for dx, dy in offsets:
            points.append((self.academy_x + dx, self.academy_y + dy))
        return points

    def update_ai(self, game_map, all_npcs=None, player=None, current_hour=12):
        """
        Обновление AI мага за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока
            current_hour: Текущий час суток (0-23)
        """
        if not self.is_alive:
            return

        # Обновляем расписание (проверка времени активности)
        self.update_schedule(current_hour, game_map)

        # Если NPC скрыт (в локации), не обновляем AI
        if self.is_hidden():
            return

        # Восстанавливаем выносливость и ману
        self.recover_stamina()
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + 3)  # Медленное восстановление маны

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            if self.consume_stamina():
                self._combat_step(game_map)
        elif self.state == "patrol":
            # Делаем 1 шаг за 1 час (избегаем телепортации)
            if self.consume_stamina():
                self._patrol_step(game_map)
        elif self.state == "rest":
            self._rest()

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости
        Маги враждебны к бандитам и нежити

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего врага
        closest_enemy = None
        closest_distance = float('inf')

        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Маги враждебны к бандитам и нежити
                if npc.npc_type in [NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD]:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                    if distance <= self.detection_range and distance < closest_distance:
                        closest_enemy = npc
                        closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
            self.pursuit_counter = 0
        elif self.state == "combat":
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения

        Args:
            game_map: Объект карты игры
        """
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем расстояние до академии
        distance_to_academy = abs(self.x - self.academy_x) + abs(self.y - self.academy_y)
        if distance_to_academy > self.max_distance_from_academy:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Используем упрощенный бой для NPC vs NPC
            enemy_killed = self._simplified_npc_combat(self.target_enemy)

            if enemy_killed:
                print(f"{self.name} победил {self.target_enemy.name} в быстром бою!")
                self.target_enemy = None
                self.state = "patrol"
                self.pursuit_counter = 0
        else:
            # Двигаемся к цели
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=20)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                distance_to_academy_new = abs(new_x - self.academy_x) + abs(new_y - self.academy_y)
                if distance_to_academy_new <= self.max_distance_from_academy:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1
                else:
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории академии"""
        # Проверяем расстояние до академии
        distance_to_academy = abs(self.x - self.academy_x) + abs(self.y - self.academy_y)

        # Если слишком далеко от академии, возвращаемся
        if distance_to_academy > self.max_distance_from_academy:
            dx, dy = self._find_next_step(self.academy_x, self.academy_y, game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Получаем текущую точку патрулирования
        if not self.patrol_points:
            return

        target_x, target_y = self.patrol_points[self.patrol_point_index]

        # Если достигли точки, переходим к следующей
        if self.x == target_x and self.y == target_y:
            self.patrol_point_index = (self.patrol_point_index + 1) % len(self.patrol_points)
            # Небольшой шанс отдохнуть
            if random.random() < 0.1:
                self.state = "rest"
                self.rest_counter = 0
            return

        # Двигаемся к точке патрулирования
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=15)
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
        else:
            # Если не можем достичь точки, переходим к следующей
            self.patrol_point_index = (self.patrol_point_index + 1) % len(self.patrol_points)

    def _rest(self):
        """Отдых мага"""
        self.rest_counter += 1
        # Усиленное восстановление маны во время отдыха
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + 5)

        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0
            self.rest_duration = random.randint(2, 4)
