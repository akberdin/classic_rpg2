"""
Система тайников для подземелий
"""
import random
from enum import Enum
from typing import List, Tuple, Optional


class StashType(Enum):
    """Типы тайников"""
    CHEST = "chest"              # Сундук - обычный лут
    HIDDEN_CACHE = "hidden"      # Скрытый тайник - хороший лут
    SKELETON = "skeleton"        # Скелет искателя - случайный лут
    ALTAR_OFFERING = "altar"     # Подношение на алтаре - магический лут
    ORE_DEPOSIT = "ore"          # Залежи руды - ресурсы
    ANCIENT_TOMB = "tomb"        # Древняя гробница - редкий лут


class StashLevel(Enum):
    """Уровни тайников"""
    SIMPLE = 1             # Простой (виден сразу)
    HIDDEN = 2             # Скрытый
    WELL_HIDDEN = 3        # Хорошо спрятанный
    MASTERFULLY_HIDDEN = 4 # Мастерски скрытый
    LEGENDARY_TREASURE = 5 # Легендарное сокровище


# Параметры уровней тайников
STASH_LEVEL_DATA = {
    StashLevel.SIMPLE: {
        "name": "Простой",
        "dc_modifier": 0,              # Виден сразу (DC = 0)
        "gold_multiplier": 1.0,        # 100% золота
        "quality_weights": {           # Веса качества предметов
            "poor": 50,
            "common": 40,
            "uncommon": 10,
        },
        "trap_chance": 0.0,            # Нет ловушек
        "extra_items": 0,              # Доп. предметов
    },
    StashLevel.HIDDEN: {
        "name": "Скрытый",
        "dc_modifier": 10,             # DC обнаружения +10
        "gold_multiplier": 1.5,        # 150% золота
        "quality_weights": {
            "common": 60,
            "uncommon": 30,
            "rare": 10,
        },
        "trap_chance": 0.10,           # 10% шанс ловушки (уровень 1)
        "extra_items": 0,
    },
    StashLevel.WELL_HIDDEN: {
        "name": "Хорошо Спрятанный",
        "dc_modifier": 15,             # DC обнаружения +15
        "gold_multiplier": 2.0,        # 200% золота
        "quality_weights": {
            "common": 40,
            "uncommon": 40,
            "rare": 15,
            "epic": 5,
        },
        "trap_chance": 0.30,           # 30% шанс ловушки (уровень 2)
        "extra_items": 1,              # +1 предмет
    },
    StashLevel.MASTERFULLY_HIDDEN: {
        "name": "Мастерски Скрытый",
        "dc_modifier": 20,             # DC обнаружения +20
        "gold_multiplier": 3.0,        # 300% золота
        "quality_weights": {
            "common": 20,
            "uncommon": 35,
            "rare": 30,
            "epic": 12,
            "legendary": 3,
        },
        "trap_chance": 0.60,           # 60% шанс ловушки (уровень 3)
        "extra_items": 2,              # +2 предмета
        "skill_book_chance": 0.05,    # 5% шанс книги умений
    },
    StashLevel.LEGENDARY_TREASURE: {
        "name": "Легендарное Сокровище",
        "dc_modifier": 25,             # DC обнаружения +25
        "gold_multiplier": 5.0,        # 500% золота
        "quality_weights": {
            "uncommon": 25,
            "rare": 30,
            "epic": 25,
            "legendary": 15,
            "artifact": 5,
        },
        "trap_chance": 0.90,           # 90% шанс ловушки (уровень 4-5)
        "extra_items": 3,              # +3 предмета
        "skill_book_chance": 1.0,     # Гарантированная книга умений
        "recipe_chance": 0.15,        # 15% шанс рецепта
    },
}

# Параметры тайников
STASH_DATA = {
    StashType.CHEST: {
        "name": "Сундук",
        "description": "Старый деревянный сундук",
        "detection_dc": 0,  # Виден сразу
        "gold_min": 10,
        "gold_max": 50,
        "item_chance": 70,  # Шанс найти предмет (%)
        "item_quality_bonus": 0,
        "weight": 35,
    },
    StashType.HIDDEN_CACHE: {
        "name": "Скрытый тайник",
        "description": "Тайник, скрытый в стене",
        "detection_dc": 12,
        "gold_min": 30,
        "gold_max": 100,
        "item_chance": 85,
        "item_quality_bonus": 1,  # Бонус к качеству предметов
        "weight": 20,
    },
    StashType.SKELETON: {
        "name": "Скелет искателя",
        "description": "Останки несчастного искателя приключений",
        "detection_dc": 0,
        "gold_min": 5,
        "gold_max": 30,
        "item_chance": 60,
        "item_quality_bonus": 0,
        "weight": 25,
    },
    StashType.ALTAR_OFFERING: {
        "name": "Подношение на алтаре",
        "description": "Древние подношения богам",
        "detection_dc": 0,
        "gold_min": 20,
        "gold_max": 80,
        "item_chance": 90,
        "item_quality_bonus": 2,  # Магические предметы
        "weight": 10,
    },
    StashType.ORE_DEPOSIT: {
        "name": "Залежи руды",
        "description": "Богатая рудная жила",
        "detection_dc": 0,
        "gold_min": 0,
        "gold_max": 0,
        "item_chance": 100,  # Всегда руда
        "item_quality_bonus": 0,
        "resource_type": "ore",
        "weight": 15,
    },
    StashType.ANCIENT_TOMB: {
        "name": "Древняя гробница",
        "description": "Гробница древнего воина",
        "detection_dc": 8,
        "gold_min": 50,
        "gold_max": 200,
        "item_chance": 95,
        "item_quality_bonus": 3,  # Лучшие предметы
        "weight": 5,
    },
}

# Лут для разных уровней подземелий
DUNGEON_LOOT_TABLES = {
    # Уровень 1-3 (начальные)
    "low": {
        "common_items": [
            ("Лечебное зелье (малое)", "potion_health_small", 30),
            ("Зелье маны (малое)", "potion_mana_small", 25),
            ("Факел", "torch", 40),
            ("Верёвка", "rope", 20),
            ("Бинты", "bandage", 35),
        ],
        "uncommon_items": [
            ("Лечебное зелье (среднее)", "potion_health_medium", 25),
            ("Зелье выносливости", "potion_stamina", 20),
            ("Противоядие", "antidote", 15),
        ],
        "rare_items": [
            ("Свиток телепортации", "scroll_teleport", 10),
        ],
        "ores": [
            ("Железная руда", "iron_ore", 50),
            ("Медная руда", "copper_ore", 40),
            ("Уголь", "coal", 30),
        ],
    },
    # Уровень 4-6 (средние)
    "medium": {
        "common_items": [
            ("Лечебное зелье (среднее)", "potion_health_medium", 35),
            ("Зелье маны (среднее)", "potion_mana_medium", 30),
            ("Масло оружия", "weapon_oil", 20),
        ],
        "uncommon_items": [
            ("Лечебное зелье (большое)", "potion_health_large", 20),
            ("Эликсир силы", "elixir_strength", 15),
            ("Эликсир ловкости", "elixir_dexterity", 15),
        ],
        "rare_items": [
            ("Свиток воскрешения", "scroll_resurrect", 5),
            ("Камень душ", "soul_gem", 10),
        ],
        "ores": [
            ("Железная руда", "iron_ore", 40),
            ("Серебряная руда", "silver_ore", 35),
            ("Золотая руда", "gold_ore", 20),
        ],
    },
    # Уровень 7+ (высокие)
    "high": {
        "common_items": [
            ("Лечебное зелье (большое)", "potion_health_large", 40),
            ("Зелье маны (большое)", "potion_mana_large", 35),
        ],
        "uncommon_items": [
            ("Эликсир неуязвимости", "elixir_invulnerability", 15),
            ("Эликсир мудрости", "elixir_wisdom", 15),
        ],
        "rare_items": [
            ("Свиток желания", "scroll_wish", 3),
            ("Философский камень", "philosopher_stone", 2),
            ("Древний артефакт", "ancient_artifact", 5),
        ],
        "ores": [
            ("Золотая руда", "gold_ore", 35),
            ("Мифриловая руда", "mithril_ore", 25),
            ("Адамантит", "adamantite_ore", 10),
        ],
    },
}


class Stash:
    """Класс тайника"""

    def __init__(self, x: int, y: int, stash_type: StashType, dungeon_level: int = 1,
                 stash_level: StashLevel = StashLevel.SIMPLE):
        """
        Создать тайник

        Args:
            x: Координата X
            y: Координата Y
            stash_type: Тип тайника
            dungeon_level: Уровень подземелья
            stash_level: Уровень тайника (1-5)
        """
        self.x = x
        self.y = y
        self.stash_type = stash_type
        self.dungeon_level = dungeon_level
        self.stash_level = stash_level

        # Данные типа тайника
        stash_data = STASH_DATA.get(stash_type, STASH_DATA[StashType.CHEST])
        self.name = stash_data["name"]
        self.description = stash_data["description"]
        self.resource_type = stash_data.get("resource_type", None)

        # Данные уровня тайника
        level_data = STASH_LEVEL_DATA[stash_level]
        self.level_name = level_data["name"]
        self.gold_multiplier = level_data["gold_multiplier"]
        self.quality_weights = level_data["quality_weights"]
        self.trap_chance = level_data["trap_chance"]
        self.extra_items = level_data["extra_items"]

        # Расчет DC с учетом уровня тайника
        base_detection_dc = stash_data["detection_dc"]
        dc_modifier = level_data["dc_modifier"]
        self.detection_dc = max(0, base_detection_dc + dc_modifier)

        # Базовые параметры лута
        self.gold_min = stash_data["gold_min"]
        self.gold_max = stash_data["gold_max"]
        self.item_chance = stash_data["item_chance"]
        self.item_quality_bonus = stash_data["item_quality_bonus"]

        # Состояние
        self.is_detected = (self.detection_dc == 0)  # Виден ли тайник
        self.is_looted = False

        # Ловушка в тайнике (генерируется при создании)
        self.has_trap = False
        self.trap = None
        self._generate_trap()

        # Сгенерированный лут (кэшируется при первом открытии)
        self._cached_loot = None

    def _generate_trap(self):
        """Генерация ловушки в тайнике (если есть шанс)"""
        if self.trap_chance > 0 and random.random() < self.trap_chance:
            # Импортируем здесь, чтобы избежать циклической зависимости
            from game.dungeon.traps import Trap, TrapType, TrapLevel, TRAP_DATA

            self.has_trap = True

            # Выбираем случайный тип ловушки
            trap_types = list(TrapType)
            trap_type = random.choice(trap_types)

            # Определяем уровень ловушки на основе уровня тайника
            trap_level_value = max(1, self.stash_level.value - 1)
            trap_level = TrapLevel(trap_level_value)

            # Создаем ловушку (не отображается на карте)
            self.trap = Trap(self.x, self.y, trap_type, self.dungeon_level, trap_level)
            # Ловушка автоматически не обнаружена
            self.trap.is_detected = False

    def try_detect(self, player) -> bool:
        """
        Попытка обнаружить тайник

        Args:
            player: Объект игрока

        Returns:
            bool: True если тайник обнаружен
        """
        if self.is_detected:
            return True

        # Получаем бонус от навыка Keen Eye (если есть)
        keen_eye_bonus = 0
        if hasattr(player, 'skill_manager') and player.skill_manager:
            keen_eye = player.skill_manager.get_skill("Острый Глаз")
            if keen_eye:
                keen_eye_bonus = keen_eye.get_detection_bonus()

        # Проверка на обнаружение (удача + интеллект + Keen Eye)
        detection_roll = (random.randint(1, 20) +
                         player.luck // 3 +
                         player.intelligence // 5 +
                         keen_eye_bonus)

        if detection_roll >= self.detection_dc:
            self.is_detected = True

            # Прогресс навыка Keen Eye
            if hasattr(player, 'skill_manager') and player.skill_manager:
                keen_eye = player.skill_manager.get_skill("Острый Глаз")
                if keen_eye:
                    keen_eye.on_object_detected()

            return True
        return False

    def _get_loot_table_level(self) -> str:
        """Определить уровень таблицы лута"""
        if self.dungeon_level <= 3:
            return "low"
        elif self.dungeon_level <= 6:
            return "medium"
        else:
            return "high"

    def _generate_loot(self) -> dict:
        """
        Сгенерировать лут

        Returns:
            dict: {"gold": int, "items": List[Tuple[name, id, quantity]]}
        """
        loot = {"gold": 0, "items": []}

        # Золото
        if self.gold_max > 0:
            # Бонус от уровня подземелья
            level_bonus = 1 + 0.2 * (self.dungeon_level - 1)
            gold = random.randint(self.gold_min, self.gold_max)
            loot["gold"] = int(gold * level_bonus)

        # Предметы
        if random.randint(1, 100) <= self.item_chance:
            loot_level = self._get_loot_table_level()
            loot_table = DUNGEON_LOOT_TABLES.get(loot_level, DUNGEON_LOOT_TABLES["low"])

            # Выбор категории предметов
            if self.resource_type == "ore":
                # Только руда
                items = loot_table.get("ores", [])
            else:
                # Определяем категорию на основе бонуса качества
                quality_roll = random.randint(1, 100) + self.item_quality_bonus * 15

                if quality_roll >= 95:
                    items = loot_table.get("rare_items", loot_table.get("uncommon_items", []))
                elif quality_roll >= 70:
                    items = loot_table.get("uncommon_items", loot_table.get("common_items", []))
                else:
                    items = loot_table.get("common_items", [])

            if items:
                # Выбираем 1-3 предмета
                num_items = random.randint(1, min(3, len(items)))
                chosen_items = random.sample(items, num_items)

                for item_name, item_id, base_chance in chosen_items:
                    if random.randint(1, 100) <= base_chance:
                        quantity = random.randint(1, 3) if "ore" in item_id else 1
                        loot["items"].append((item_name, item_id, quantity))

        return loot

    def loot(self, player) -> dict:
        """
        Обыскать тайник

        Args:
            player: Объект игрока

        Returns:
            dict: {"success": bool, "gold": int, "items": list, "message": str, "trap_triggered": bool}
        """
        if not self.is_detected:
            return {
                "success": False,
                "gold": 0,
                "items": [],
                "message": "Вы не видите здесь ничего интересного",
                "trap_triggered": False
            }

        if self.is_looted:
            return {
                "success": False,
                "gold": 0,
                "items": [],
                "message": f"{self.name} уже обыскан",
                "trap_triggered": False
            }

        # Проверяем ловушку ПЕРЕД обыском
        if self.has_trap and self.trap and not self.trap.is_disarmed:
            # Ловушка срабатывает при попытке обыска
            trap_result = self.trap.trigger(player)

            # Если игрок мертв, не даем обыскать тайник
            if player.health <= 0:
                return {
                    "success": False,
                    "gold": 0,
                    "items": [],
                    "message": f"Попытка обыскать {self.name} ({self.level_name}) активировала ловушку!\n{trap_result['message']}",
                    "trap_triggered": True,
                    "trap_result": trap_result
                }
            else:
                # Игрок выжил, можно продолжить обыск (но после урона)
                pass

        self.is_looted = True

        # Генерируем лут (если еще не сгенерирован)
        if self._cached_loot is None:
            self._cached_loot = self._generate_loot()

        loot = self._cached_loot

        # Добавляем золото игроку
        if loot["gold"] > 0 and hasattr(player, 'inventory'):
            player.inventory.add_gold(loot["gold"])

        # Формируем сообщение
        messages = []

        # Если была ловушка
        if self.has_trap and self.trap and not self.trap.is_disarmed:
            messages.append(f"⚠️ ЛОВУШКА! При обыске {self.name} ({self.level_name}) сработала ловушка!")
            trap_result = self.trap.trigger(player)
            if trap_result.get("success"):
                messages.append(trap_result["message"])
            messages.append("")

        messages.append(f"Вы обыскали {self.name} ({self.level_name}):")

        if loot["gold"] > 0:
            messages.append(f"  +{loot['gold']} золота")

        for item_name, item_id, quantity in loot["items"]:
            messages.append(f"  +{item_name} x{quantity}")

        if not loot["gold"] and not loot["items"]:
            messages.append("  Пусто!")

        return {
            "success": True,
            "gold": loot["gold"],
            "items": loot["items"],
            "message": "\n".join(messages),
            "trap_triggered": self.has_trap and self.trap and not self.trap.is_disarmed
        }


class StashManager:
    """Менеджер тайников подземелья"""

    def __init__(self):
        """Инициализация менеджера"""
        self.stashes: List[Stash] = []

    def add_stash(self, stash: Stash):
        """Добавить тайник"""
        self.stashes.append(stash)

    def get_stash_at(self, x: int, y: int) -> Optional[Stash]:
        """Получить тайник по координатам"""
        for stash in self.stashes:
            if stash.x == x and stash.y == y:
                return stash
        return None

    def try_detect_nearby(self, player, radius: int = 2) -> List[Stash]:
        """
        Попытка обнаружить тайники поблизости

        Args:
            player: Объект игрока
            radius: Радиус обнаружения (может быть расширен Keen Eye)

        Returns:
            List[Stash]: Список обнаруженных тайников
        """
        # Получаем Keen Eye для проверки автообнаружения
        keen_eye = None
        if hasattr(player, 'skill_manager') and player.skill_manager:
            keen_eye = player.skill_manager.get_skill("Острый Глаз")
            if keen_eye:
                # Расширяем радиус поиска на основе навыка
                radius = max(radius, keen_eye.get_auto_detect_radius())

        detected = []
        for stash in self.stashes:
            if stash.is_detected or stash.is_looted:
                continue

            distance = abs(stash.x - player.x) + abs(stash.y - player.y)
            if distance <= radius:
                # Проверяем автообнаружение для низкоуровневых тайников
                auto_detected = False
                if keen_eye and distance <= keen_eye.get_auto_detect_radius():
                    if keen_eye.can_auto_detect(stash.stash_level.value):
                        stash.is_detected = True
                        auto_detected = True
                        keen_eye.on_object_detected()
                        detected.append(stash)

                # Обычное обнаружение, если не было автообнаружения
                if not auto_detected and stash.try_detect(player):
                    detected.append(stash)

        return detected

    def generate_random_stash(self, x: int, y: int, dungeon_level: int = 1,
                               is_mine: bool = False) -> Stash:
        """
        Сгенерировать случайный тайник

        Args:
            x: Координата X
            y: Координата Y
            dungeon_level: Уровень подземелья
            is_mine: Это шахта (генерировать руду)

        Returns:
            Stash: Сгенерированный тайник
        """
        if is_mine:
            # В шахтах преимущественно руда
            stash_type = StashType.ORE_DEPOSIT if random.random() < 0.6 else StashType.CHEST
        else:
            # Выбираем тип тайника с учетом веса
            stash_weights = []
            stash_types = []

            for st, data in STASH_DATA.items():
                if st != StashType.ORE_DEPOSIT:  # Руда только в шахтах
                    stash_types.append(st)
                    stash_weights.append(data["weight"])

            stash_type = random.choices(stash_types, weights=stash_weights, k=1)[0]

        # Определяем уровень тайника на основе уровня подземелья
        stash_level = self._determine_stash_level(dungeon_level)

        return Stash(x, y, stash_type, dungeon_level, stash_level)

    def _determine_stash_level(self, dungeon_level: int) -> StashLevel:
        """
        Определить уровень тайника на основе уровня подземелья

        Args:
            dungeon_level: Уровень подземелья

        Returns:
            StashLevel: Уровень тайника
        """
        # Распределение уровней тайников по уровню подземелья
        if dungeon_level <= 3:
            # Уровень 1-3: в основном простые и скрытые
            weights = [70, 25, 5, 0, 0]
        elif dungeon_level <= 6:
            # Уровень 4-6: скрытые и хорошо спрятанные
            weights = [40, 35, 20, 5, 0]
        elif dungeon_level <= 10:
            # Уровень 7-10: хорошо спрятанные и мастерские
            weights = [20, 30, 30, 15, 5]
        elif dungeon_level <= 15:
            # Уровень 11-15: мастерские с редкими легендарными
            weights = [10, 20, 35, 25, 10]
        elif dungeon_level <= 20:
            # Уровень 16-20: мастерские и легендарные
            weights = [5, 15, 30, 35, 15]
        else:
            # Уровень 21+: в основном мастерские и легендарные
            weights = [0, 10, 25, 40, 25]

        levels = [StashLevel.SIMPLE, StashLevel.HIDDEN, StashLevel.WELL_HIDDEN,
                  StashLevel.MASTERFULLY_HIDDEN, StashLevel.LEGENDARY_TREASURE]

        return random.choices(levels, weights=weights, k=1)[0]

    def clear(self):
        """Очистить все тайники"""
        self.stashes.clear()

    def get_all_stashes(self) -> List[Stash]:
        """Получить все тайники"""
        return self.stashes.copy()

    def get_detected_stashes(self) -> List[Stash]:
        """Получить только обнаруженные тайники"""
        return [s for s in self.stashes if s.is_detected]

    def get_unlooted_stashes(self) -> List[Stash]:
        """Получить необысканные тайники"""
        return [s for s in self.stashes if not s.is_looted]
