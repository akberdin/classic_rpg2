"""
Система инвентаря и предметов
"""
import random
from enum import Enum


# Качество предметов
class ItemQuality(Enum):
    """Качество предмета"""
    POOR = ("Плохое", 0.5, (128, 128, 128))  # Серый
    COMMON = ("Обычное", 1.0, (255, 255, 255))  # Белый
    UNCOMMON = ("Необычное", 1.5, (30, 255, 0))  # Зеленый
    RARE = ("Редкое", 2.0, (0, 112, 255))  # Синий
    EPIC = ("Эпическое", 3.0, (163, 53, 238))  # Фиолетовый
    LEGENDARY = ("Легендарное", 5.0, (255, 128, 0))  # Оранжевый
    ARTIFACT = ("Артефакт", 10.0, (230, 204, 128))  # Золотой

    def __init__(self, rus_name, multiplier, color):
        self.rus_name = rus_name
        self.multiplier = multiplier
        self.color = color


# Типы доспехов
class ArmorType(Enum):
    """Тип доспеха"""
    LIGHT = ("Легкое", 1.0)
    MEDIUM = ("Среднее", 1.5)
    HEAVY = ("Тяжелое", 2.0)

    def __init__(self, rus_name, defense_multiplier):
        self.rus_name = rus_name
        self.defense_multiplier = defense_multiplier


# Слоты экипировки
class EquipmentSlot(Enum):
    """Слот экипировки"""
    WEAPON = "weapon"
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    FEET = "feet"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    RING_3 = "ring_3"
    RING_4 = "ring_4"
    AMULET = "amulet"
    BRACELET_1 = "bracelet_1"
    BRACELET_2 = "bracelet_2"


# Типы оружия
class WeaponType(Enum):
    """Тип оружия"""
    KNIFE = ("Нож", 1.0, 0.5)
    CLUB = ("Дубина", 1.2, 2.0)
    SWORD = ("Меч", 1.5, 3.0)
    SPEAR = ("Копье", 1.4, 2.5)
    BOW = ("Лук", 1.3, 1.5)
    STAFF = ("Посох", 1.1, 2.0)
    WAND = ("Жезл", 1.0, 0.8)
    AXE = ("Топор", 1.4, 2.8)
    PICKAXE = ("Кирка", 1.1, 2.5)

    def __init__(self, rus_name, damage_multiplier, weight):
        self.rus_name = rus_name
        self.damage_multiplier = damage_multiplier
        self.weight = weight


class Item:
    """Базовый класс для предмета"""

    def __init__(self, name, item_type, value=0, weight=0.1, quality=ItemQuality.COMMON, description=""):
        """
        Инициализация предмета

        Args:
            name: Название предмета
            item_type: Тип предмета (resource, potion, equipment, etc.)
            value: Стоимость предмета в золоте
            weight: Вес предмета в кг
            quality: Качество предмета
            description: Описание предмета
        """
        self.name = name
        self.item_type = item_type
        self.base_value = value
        self.weight = weight
        self.quality = quality
        self.description = description

    @property
    def value(self):
        """Стоимость с учетом качества"""
        return int(self.base_value * self.quality.multiplier)

    def get_full_name(self):
        """Полное название с качеством"""
        if self.quality == ItemQuality.COMMON:
            return self.name
        return f"{self.name} ({self.quality.rus_name})"


class ResourceItem(Item):
    """Класс для ресурсов (руда, древесина, травы и т.д.)"""

    def __init__(self, name, value=10, weight=0.5, quality=ItemQuality.COMMON):
        super().__init__(name, "resource", value, weight, quality, f"Ресурс: {name}")


class PotionItem(Item):
    """Класс для зелий"""

    def __init__(self, name, effect_type, effect_value, value=50, weight=0.2, quality=ItemQuality.COMMON):
        """
        Инициализация зелья

        Args:
            name: Название зелья
            effect_type: Тип эффекта (health, mana, stamina)
            effect_value: Значение эффекта
            value: Стоимость зелья
            weight: Вес зелья
            quality: Качество зелья
        """
        super().__init__(name, "potion", value, weight, quality, f"Зелье: {name}")
        self.effect_type = effect_type
        self.base_effect_value = effect_value

    @property
    def effect_value(self):
        """Эффект с учетом качества"""
        return int(self.base_effect_value * self.quality.multiplier)

    def use(self, character):
        """
        Использовать зелье на персонаже

        Args:
            character: Персонаж для применения эффекта

        Returns:
            str: Сообщение о результате
        """
        if self.effect_type == "health":
            old_health = character.health
            character.health = min(character.max_health, character.health + self.effect_value)
            restored = character.health - old_health
            return f"Восстановлено {restored} здоровья"
        elif self.effect_type == "mana":
            if hasattr(character, 'mana'):
                old_mana = character.mana
                character.mana = min(character.max_mana, character.mana + self.effect_value)
                restored = character.mana - old_mana
                return f"Восстановлено {restored} маны"
            return "Не применимо к этому персонажу"
        elif self.effect_type == "stamina":
            old_stamina = character.stamina
            character.stamina = min(character.max_stamina, character.stamina + self.effect_value)
            character.is_resting = False  # Снимаем состояние отдыха
            restored = character.stamina - old_stamina
            return f"Восстановлено {restored} выносливости"
        return "Эффект не применен"


class EquipmentItem(Item):
    """Базовый класс для экипируемых предметов"""

    def __init__(self, name, slot, value=100, weight=1.0, quality=ItemQuality.COMMON,
                 stats_bonus=None, description=""):
        """
        Инициализация экипируемого предмета

        Args:
            name: Название предмета
            slot: Слот экипировки
            value: Стоимость
            weight: Вес
            quality: Качество
            stats_bonus: Словарь бонусов к характеристикам
            description: Описание
        """
        super().__init__(name, "equipment", value, weight, quality, description)
        self.slot = slot
        self.stats_bonus = stats_bonus or {}

    def get_stat_bonus(self, stat_name):
        """Получить бонус к характеристике с учетом качества"""
        base_bonus = self.stats_bonus.get(stat_name, 0)
        if self.quality == ItemQuality.COMMON:
            return base_bonus
        # Бонусы от качества (меньший множитель чем для цены)
        quality_multipliers = {
            ItemQuality.POOR: 0.7,
            ItemQuality.COMMON: 1.0,
            ItemQuality.UNCOMMON: 1.2,
            ItemQuality.RARE: 1.5,
            ItemQuality.EPIC: 2.0,
            ItemQuality.LEGENDARY: 3.0,
            ItemQuality.ARTIFACT: 5.0
        }
        multiplier = quality_multipliers.get(self.quality, 1.0)
        return int(base_bonus * multiplier)

    def get_stats_description(self):
        """Получить описание бонусов"""
        if not self.stats_bonus:
            return ""

        stat_names = {
            'strength': 'Сила',
            'dexterity': 'Ловкость',
            'constitution': 'Телосложение',
            'spirit': 'Дух',
            'intelligence': 'Интеллект',
            'luck': 'Удача',
            'damage': 'Урон',
            'defense': 'Защита'
        }

        parts = []
        for stat, bonus in self.stats_bonus.items():
            actual_bonus = self.get_stat_bonus(stat)
            stat_name = stat_names.get(stat, stat)
            parts.append(f"+{actual_bonus} {stat_name}")

        return ", ".join(parts)


class WeaponItem(EquipmentItem):
    """Класс оружия"""

    def __init__(self, name, weapon_type, base_damage, value=100,
                 quality=ItemQuality.COMMON, stats_bonus=None):
        """
        Инициализация оружия

        Args:
            name: Название оружия
            weapon_type: Тип оружия (WeaponType)
            base_damage: Базовый урон
            value: Стоимость
            quality: Качество
            stats_bonus: Дополнительные бонусы к характеристикам
        """
        weight = weapon_type.weight
        stats = stats_bonus or {}

        # Добавляем урон в статы
        if 'damage' not in stats:
            stats['damage'] = base_damage

        description = f"{weapon_type.rus_name}. Урон: {base_damage}"

        super().__init__(name, EquipmentSlot.WEAPON, value, weight, quality, stats, description)
        self.weapon_type = weapon_type
        self.base_damage = base_damage

    @property
    def damage(self):
        """Урон с учетом типа оружия и качества"""
        return int(self.get_stat_bonus('damage') * self.weapon_type.damage_multiplier)


class ArmorItem(EquipmentItem):
    """Класс доспехов"""

    def __init__(self, name, slot, armor_type, base_defense, value=100,
                 quality=ItemQuality.COMMON, stats_bonus=None):
        """
        Инициализация доспеха

        Args:
            name: Название доспеха
            slot: Слот экипировки (HEAD, CHEST, HANDS, FEET)
            armor_type: Тип доспеха (ArmorType)
            base_defense: Базовая защита
            value: Стоимость
            quality: Качество
            stats_bonus: Дополнительные бонусы
        """
        # Вес зависит от типа доспеха и слота
        slot_weights = {
            EquipmentSlot.HEAD: 1.0,
            EquipmentSlot.CHEST: 5.0,
            EquipmentSlot.HANDS: 0.5,
            EquipmentSlot.FEET: 1.5
        }
        base_weight = slot_weights.get(slot, 1.0)
        weight = base_weight * armor_type.defense_multiplier

        stats = stats_bonus or {}
        if 'defense' not in stats:
            stats['defense'] = base_defense

        description = f"{armor_type.rus_name}. Защита: {base_defense}"

        super().__init__(name, slot, value, weight, quality, stats, description)
        self.armor_type = armor_type
        self.base_defense = base_defense

    @property
    def defense(self):
        """Защита с учетом типа доспеха и качества"""
        return int(self.get_stat_bonus('defense') * self.armor_type.defense_multiplier)


class JewelryItem(EquipmentItem):
    """Класс украшений (кольца, амулеты, браслеты)"""

    def __init__(self, name, slot, value=200, quality=ItemQuality.UNCOMMON, stats_bonus=None):
        """
        Инициализация украшения

        Args:
            name: Название украшения
            slot: Слот экипировки (RING_1-4, AMULET, BRACELET_1-2)
            value: Стоимость
            quality: Качество
            stats_bonus: Бонусы к характеристикам
        """
        weight = 0.1  # Украшения очень легкие
        stats = stats_bonus or {}

        description = "Украшение"
        if stats:
            description = f"Украшение. {self._get_bonus_description(stats)}"

        super().__init__(name, slot, value, weight, quality, stats, description)

    def _get_bonus_description(self, stats):
        """Создать описание бонусов"""
        stat_names = {
            'strength': 'Силы',
            'dexterity': 'Ловкости',
            'constitution': 'Телосложения',
            'spirit': 'Духа',
            'intelligence': 'Интеллекта',
            'luck': 'Удачи'
        }
        parts = []
        for stat, bonus in stats.items():
            stat_name = stat_names.get(stat, stat)
            parts.append(f"+{bonus} {stat_name}")
        return ", ".join(parts)


class ArtifactItem(EquipmentItem):
    """Класс артефактов - уникальные предметы с мощными бонусами"""

    def __init__(self, name, slot, value=5000, stats_bonus=None, special_effect=None):
        """
        Инициализация артефакта

        Args:
            name: Название артефакта
            slot: Слот экипировки
            value: Стоимость
            stats_bonus: Бонусы к характеристикам
            special_effect: Описание специального эффекта
        """
        weight = 0.5
        stats = stats_bonus or {}

        description = f"Артефакт. {special_effect or 'Древний предмет силы'}"

        super().__init__(name, slot, value, weight, ItemQuality.ARTIFACT, stats, description)
        self.special_effect = special_effect


class Inventory:
    """Класс инвентаря для хранения предметов"""

    def __init__(self, max_slots=20, max_weight=100.0):
        """
        Инициализация инвентаря

        Args:
            max_slots: Максимальное количество слотов
            max_weight: Максимальный вес (кг)
        """
        self.items = {}  # {item_name: (item, quantity)}
        self.max_slots = max_slots
        self.max_weight = max_weight
        self.gold = 0

        # Слоты экипировки
        self.equipment = {slot: None for slot in EquipmentSlot}

    def update_max_weight(self, strength):
        """
        Обновить максимальный вес на основе силы персонажа
        Формула: 30 + сила * 10

        Args:
            strength: Значение силы персонажа
        """
        self.max_weight = 30 + strength * 10

    @property
    def current_weight(self):
        """Текущий вес инвентаря"""
        total = 0.0
        # Вес предметов в инвентаре
        for item, quantity in self.items.values():
            total += item.weight * quantity
        # Вес экипированных предметов
        for item in self.equipment.values():
            if item:
                total += item.weight
        return round(total, 2)

    def add_item(self, item, quantity=1):
        """
        Добавить предмет в инвентарь

        Args:
            item: Объект предмета
            quantity: Количество

        Returns:
            bool: True если успешно добавлен
        """
        # Проверка на количество слотов
        if len(self.items) >= self.max_slots and item.name not in self.items:
            return False  # Инвентарь полон

        # Проверка на вес
        new_weight = self.current_weight + (item.weight * quantity)
        if new_weight > self.max_weight:
            return False  # Превышен максимальный вес

        if item.name in self.items:
            # Увеличиваем количество существующего предмета
            self.items[item.name] = (item, self.items[item.name][1] + quantity)
        else:
            # Добавляем новый предмет
            self.items[item.name] = (item, quantity)

        return True

    def remove_item(self, item_name, quantity=1):
        """
        Удалить предмет из инвентаря

        Args:
            item_name: Название предмета
            quantity: Количество для удаления

        Returns:
            bool: True если успешно удален
        """
        if item_name not in self.items:
            return False

        item, current_quantity = self.items[item_name]

        if current_quantity < quantity:
            return False

        if current_quantity == quantity:
            # Удаляем предмет полностью
            del self.items[item_name]
        else:
            # Уменьшаем количество
            self.items[item_name] = (item, current_quantity - quantity)

        return True

    def get_item(self, item_name):
        """
        Получить предмет по названию

        Args:
            item_name: Название предмета

        Returns:
            tuple: (item, quantity) или None
        """
        return self.items.get(item_name)

    def has_item(self, item_name, quantity=1):
        """
        Проверить наличие предмета

        Args:
            item_name: Название предмета
            quantity: Требуемое количество

        Returns:
            bool: True если предмет есть в нужном количестве
        """
        if item_name not in self.items:
            return False

        _, current_quantity = self.items[item_name]
        return current_quantity >= quantity

    def add_gold(self, amount):
        """Добавить золото"""
        self.gold += amount

    def remove_gold(self, amount):
        """
        Убрать золото

        Returns:
            bool: True если успешно
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def get_items_by_type(self, item_type):
        """
        Получить все предметы определенного типа

        Args:
            item_type: Тип предмета

        Returns:
            list: Список (item, quantity)
        """
        return [(item, quantity) for item, quantity in self.items.values() if item.item_type == item_type]

    def get_all_items(self):
        """Получить все предметы"""
        return list(self.items.values())

    def equip_item(self, item_name):
        """
        Экипировать предмет из инвентаря

        Args:
            item_name: Название предмета для экипировки

        Returns:
            tuple: (success, message)
        """
        if item_name not in self.items:
            return (False, "Предмет не найден в инвентаре")

        item, quantity = self.items[item_name]

        # Проверяем, является ли предмет экипируемым
        if not isinstance(item, EquipmentItem):
            return (False, "Этот предмет нельзя экипировать")

        # Определяем слот
        slot = item.slot

        # Если слот занят, снимаем старый предмет
        old_item = self.equipment[slot]
        if old_item:
            # Возвращаем старый предмет в инвентарь
            if not self.add_item(old_item, 1):
                return (False, "Не удалось снять экипированный предмет - инвентарь переполнен")

        # Экипируем новый предмет
        self.equipment[slot] = item
        # Удаляем из инвентаря
        self.remove_item(item_name, 1)

        return (True, f"{item.get_full_name()} экипирован в слот {slot.value}")

    def unequip_item(self, slot):
        """
        Снять предмет из слота экипировки

        Args:
            slot: Слот экипировки (EquipmentSlot)

        Returns:
            tuple: (success, message)
        """
        if slot not in self.equipment:
            return (False, "Неверный слот экипировки")

        item = self.equipment[slot]
        if not item:
            return (False, "Слот пуст")

        # Пытаемся добавить в инвентарь
        if not self.add_item(item, 1):
            return (False, "Инвентарь переполнен")

        # Снимаем предмет
        self.equipment[slot] = None

        return (True, f"{item.get_full_name()} снят")

    def get_equipped_item(self, slot):
        """
        Получить экипированный предмет в слоте

        Args:
            slot: Слот экипировки

        Returns:
            EquipmentItem или None
        """
        return self.equipment.get(slot)

    def get_total_stats_bonus(self):
        """
        Получить суммарные бонусы от всей экипировки

        Returns:
            dict: Словарь бонусов к характеристикам
        """
        total_bonus = {}

        for item in self.equipment.values():
            if item and isinstance(item, EquipmentItem):
                for stat, bonus in item.stats_bonus.items():
                    actual_bonus = item.get_stat_bonus(stat)
                    total_bonus[stat] = total_bonus.get(stat, 0) + actual_bonus

        return total_bonus


# ===== ГЕНЕРАТОР ПРЕДМЕТОВ =====

class ItemGenerator:
    """Генератор случайных предметов"""

    # Префиксы и суффиксы для названий
    WEAPON_PREFIXES = ["Острый", "Тяжелый", "Легкий", "Мастерский", "Древний", "Зачарованный"]
    WEAPON_SUFFIXES = ["силы", "скорости", "мощи", "точности", "разрушения"]

    ARMOR_PREFIXES = ["Прочный", "Легкий", "Укрепленный", "Зачарованный", "Древний", "Королевский"]
    ARMOR_SUFFIXES = ["защиты", "стойкости", "ловкости", "силы", "выносливости"]

    JEWELRY_PREFIXES = ["Сияющее", "Темное", "Древнее", "Магическое", "Проклятое", "Благословенное"]
    JEWELRY_SUFFIXES = ["силы", "мудрости", "удачи", "здоровья", "маны"]

    @staticmethod
    def generate_quality(base_quality_weights=None):
        """
        Генерация качества предмета

        Args:
            base_quality_weights: Словарь весов для каждого качества

        Returns:
            ItemQuality
        """
        if base_quality_weights is None:
            # Стандартные веса
            base_quality_weights = {
                ItemQuality.POOR: 0.05,
                ItemQuality.COMMON: 0.50,
                ItemQuality.UNCOMMON: 0.25,
                ItemQuality.RARE: 0.12,
                ItemQuality.EPIC: 0.06,
                ItemQuality.LEGENDARY: 0.02,
                ItemQuality.ARTIFACT: 0.001
            }

        qualities = list(base_quality_weights.keys())
        weights = list(base_quality_weights.values())

        return random.choices(qualities, weights=weights)[0]

    @staticmethod
    def generate_weapon(level=1, quality=None):
        """
        Генерация случайного оружия

        Args:
            level: Уровень предмета (влияет на характеристики)
            quality: Качество (если None - случайное)

        Returns:
            WeaponItem
        """
        if quality is None:
            quality = ItemGenerator.generate_quality()

        weapon_type = random.choice(list(WeaponType))

        # Базовый урон зависит от уровня
        base_damage = 5 + (level * 2)

        # Генерация названия
        if quality in [ItemQuality.RARE, ItemQuality.EPIC, ItemQuality.LEGENDARY, ItemQuality.ARTIFACT]:
            prefix = random.choice(ItemGenerator.WEAPON_PREFIXES)
            suffix = random.choice(ItemGenerator.WEAPON_SUFFIXES)
            name = f"{prefix} {weapon_type.rus_name} {suffix}"
        else:
            name = weapon_type.rus_name

        # Генерация бонусов
        stats_bonus = {}
        if quality.multiplier >= 1.5:  # Необычное и выше
            # Добавляем случайные бонусы к характеристикам
            bonus_count = int(quality.multiplier)
            possible_stats = ['strength', 'dexterity', 'luck']

            for _ in range(bonus_count):
                stat = random.choice(possible_stats)
                bonus_value = random.randint(1, level)
                stats_bonus[stat] = stats_bonus.get(stat, 0) + bonus_value

        value = 50 + (level * 10)

        return WeaponItem(name, weapon_type, base_damage, value, quality, stats_bonus)

    @staticmethod
    def generate_armor(level=1, slot=None, armor_type=None, quality=None):
        """
        Генерация случайного доспеха

        Args:
            level: Уровень предмета
            slot: Слот (если None - случайный из HEAD, CHEST, HANDS, FEET)
            armor_type: Тип доспеха (если None - случайный)
            quality: Качество (если None - случайное)

        Returns:
            ArmorItem
        """
        if quality is None:
            quality = ItemGenerator.generate_quality()

        if slot is None:
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                                 EquipmentSlot.HANDS, EquipmentSlot.FEET])

        if armor_type is None:
            armor_type = random.choice(list(ArmorType))

        # Базовая защита зависит от слота и уровня
        slot_defense_base = {
            EquipmentSlot.HEAD: 2,
            EquipmentSlot.CHEST: 5,
            EquipmentSlot.HANDS: 1,
            EquipmentSlot.FEET: 2
        }

        base_defense = slot_defense_base.get(slot, 2) + (level * 1)

        # Генерация названия
        slot_names = {
            EquipmentSlot.HEAD: "Шлем",
            EquipmentSlot.CHEST: "Кираса",
            EquipmentSlot.HANDS: "Перчатки",
            EquipmentSlot.FEET: "Сапоги"
        }

        slot_name = slot_names.get(slot, "Доспех")

        if quality in [ItemQuality.RARE, ItemQuality.EPIC, ItemQuality.LEGENDARY, ItemQuality.ARTIFACT]:
            prefix = random.choice(ItemGenerator.ARMOR_PREFIXES)
            suffix = random.choice(ItemGenerator.ARMOR_SUFFIXES)
            name = f"{prefix} {slot_name} {suffix}"
        else:
            name = f"{armor_type.rus_name} {slot_name}"

        # Генерация бонусов
        stats_bonus = {}
        if quality.multiplier >= 1.5:
            bonus_count = int(quality.multiplier)
            possible_stats = ['constitution', 'strength', 'dexterity']

            for _ in range(bonus_count):
                stat = random.choice(possible_stats)
                bonus_value = random.randint(1, level)
                stats_bonus[stat] = stats_bonus.get(stat, 0) + bonus_value

        value = 60 + (level * 12)

        return ArmorItem(name, slot, armor_type, base_defense, value, quality, stats_bonus)

    @staticmethod
    def generate_jewelry(level=1, slot=None, quality=None):
        """
        Генерация случайного украшения

        Args:
            level: Уровень предмета
            slot: Слот (если None - случайный из украшений)
            quality: Качество (если None - случайное, но не ниже UNCOMMON)

        Returns:
            JewelryItem
        """
        if quality is None:
            # Украшения обычно лучшего качества
            quality_weights = {
                ItemQuality.UNCOMMON: 0.50,
                ItemQuality.RARE: 0.30,
                ItemQuality.EPIC: 0.15,
                ItemQuality.LEGENDARY: 0.04,
                ItemQuality.ARTIFACT: 0.01
            }
            quality = ItemGenerator.generate_quality(quality_weights)

        if slot is None:
            jewelry_slots = [
                EquipmentSlot.RING_1, EquipmentSlot.RING_2,
                EquipmentSlot.RING_3, EquipmentSlot.RING_4,
                EquipmentSlot.AMULET,
                EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2
            ]
            slot = random.choice(jewelry_slots)

        # Генерация названия
        slot_names = {
            EquipmentSlot.RING_1: "Кольцо", EquipmentSlot.RING_2: "Кольцо",
            EquipmentSlot.RING_3: "Кольцо", EquipmentSlot.RING_4: "Кольцо",
            EquipmentSlot.AMULET: "Амулет",
            EquipmentSlot.BRACELET_1: "Браслет", EquipmentSlot.BRACELET_2: "Браслет"
        }

        slot_name = slot_names.get(slot, "Украшение")

        prefix = random.choice(ItemGenerator.JEWELRY_PREFIXES)
        suffix = random.choice(ItemGenerator.JEWELRY_SUFFIXES)
        name = f"{prefix} {slot_name} {suffix}"

        # Украшения дают бонусы ко всем характеристикам
        stats_bonus = {}
        bonus_count = max(1, int(quality.multiplier))
        possible_stats = ['strength', 'dexterity', 'constitution', 'spirit', 'intelligence', 'luck']

        for _ in range(bonus_count):
            stat = random.choice(possible_stats)
            bonus_value = random.randint(1, max(1, level // 2))
            stats_bonus[stat] = stats_bonus.get(stat, 0) + bonus_value

        value = 100 + (level * 20)

        return JewelryItem(name, slot, value, quality, stats_bonus)

    @staticmethod
    def generate_loot_for_location(location_type, level=1):
        """
        Генерация лута для конкретной локации

        Args:
            location_type: Тип локации
            level: Уровень локации (влияет на качество лута)

        Returns:
            list: Список (item, quantity)
        """
        loot = []

        if location_type == "mine":
            # Руда из шахт
            ores = ["copper_ore", "iron_ore", "silver_ore", "gold_ore", "mithril_ore"]
            weights = [0.5, 0.3, 0.12, 0.06, 0.02]
            ore_type = random.choices(ores, weights=weights)[0]
            quantity = random.randint(1, 3)
            loot.append((PREDEFINED_ITEMS[ore_type], quantity))

        elif location_type == "ruins":
            # Артефакты из руин
            artifacts = ["ancient_coin", "artifact_fragment", "magic_crystal", "old_scroll"]
            weights = [0.5, 0.3, 0.1, 0.1]
            artifact_type = random.choices(artifacts, weights=weights)[0]
            quantity = random.randint(1, 2)
            loot.append((PREDEFINED_ITEMS[artifact_type], quantity))

            # Шанс найти экипировку
            if random.random() < 0.4:  # 40% шанс
                item_type = random.choice(['weapon', 'armor', 'jewelry'])
                if item_type == 'weapon':
                    loot.append((ItemGenerator.generate_weapon(level), 1))
                elif item_type == 'armor':
                    loot.append((ItemGenerator.generate_armor(level), 1))
                else:
                    loot.append((ItemGenerator.generate_jewelry(level), 1))

            # Шанс найти зелье
            if random.random() < 0.3:  # 30% шанс
                potions = ["minor_health_potion", "health_potion", "minor_mana_potion"]
                potion_type = random.choice(potions)
                loot.append((PREDEFINED_ITEMS[potion_type], 1))

        elif location_type == "bandit_camp":
            # Бандиты могут иметь разное снаряжение
            if random.random() < 0.3:  # 30% шанс оружия
                loot.append((ItemGenerator.generate_weapon(level), 1))

            if random.random() < 0.2:  # 20% шанс доспехов
                loot.append((ItemGenerator.generate_armor(level), 1))

            # Золото
            gold_amount = random.randint(10, 50) * level
            # Добавляем золото через специальный объект
            loot.append(('gold', gold_amount))

        return loot

    @staticmethod
    def generate_npc_equipment(npc_type, level=1):
        """
        Генерация экипировки для NPC в зависимости от типа

        Args:
            npc_type: Тип NPC (guard, bandit, merchant, etc.)
            level: Уровень NPC

        Returns:
            list: Список предметов экипировки
        """
        equipment = []

        if npc_type == "guard":
            # Стражники носят средние/тяжелые доспехи и мечи/копья
            equipment.append(ItemGenerator.generate_weapon(
                level,
                quality=ItemQuality.COMMON
            ))

            # Полный комплект доспехов
            for slot in [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]:
                armor = ItemGenerator.generate_armor(
                    level,
                    slot=slot,
                    armor_type=random.choice([ArmorType.MEDIUM, ArmorType.HEAVY]),
                    quality=ItemQuality.COMMON
                )
                equipment.append(armor)

        elif npc_type == "bandit":
            # Бандиты носят легкие доспехи и разное оружие
            weapon_types = [WeaponType.KNIFE, WeaponType.CLUB, WeaponType.SWORD]
            weapon_type = random.choice(weapon_types)

            weapon = WeaponItem(
                weapon_type.rus_name,
                weapon_type,
                5 + level,
                quality=random.choice([ItemQuality.POOR, ItemQuality.COMMON])
            )
            equipment.append(weapon)

            # Частичные доспехи
            if random.random() < 0.5:  # 50% шанс иметь доспехи
                armor_slots = random.sample(
                    [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET],
                    k=random.randint(1, 2)
                )
                for slot in armor_slots:
                    armor = ItemGenerator.generate_armor(
                        level,
                        slot=slot,
                        armor_type=ArmorType.LIGHT,
                        quality=ItemQuality.POOR
                    )
                    equipment.append(armor)

        elif npc_type == "merchant":
            # Торговцы имеют легкое оружие и украшения
            equipment.append(WeaponItem(
                "Торговый нож",
                WeaponType.KNIFE,
                3,
                quality=ItemQuality.COMMON
            ))

            # Украшения (символ богатства)
            if random.random() < 0.7:  # 70% шанс
                equipment.append(ItemGenerator.generate_jewelry(level))

        return equipment


# Предопределенные предметы
PREDEFINED_ITEMS = {
    # Ресурсы из шахт
    "copper_ore": ResourceItem("Медная руда", 10),
    "iron_ore": ResourceItem("Железная руда", 20),
    "silver_ore": ResourceItem("Серебряная руда", 50),
    "gold_ore": ResourceItem("Золотая руда", 100),
    "mithril_ore": ResourceItem("Мифриловая руда", 200),

    # Древесина
    "wood": ResourceItem("Древесина", 5, 1.0),

    # Ресурсы из руин
    "ancient_coin": ResourceItem("Древняя монета", 30),
    "artifact_fragment": ResourceItem("Фрагмент артефакта", 80),
    "magic_crystal": ResourceItem("Магический кристалл", 150),
    "old_scroll": ResourceItem("Старый свиток", 40),

    # Зелья
    "minor_health_potion": PotionItem("Малое зелье здоровья", "health", 50, 30),
    "health_potion": PotionItem("Зелье здоровья", "health", 100, 60),
    "greater_health_potion": PotionItem("Большое зелье здоровья", "health", 200, 120),

    "minor_mana_potion": PotionItem("Малое зелье маны", "mana", 30, 25),
    "mana_potion": PotionItem("Зелье маны", "mana", 60, 50),

    "minor_stamina_potion": PotionItem("Малое зелье выносливости", "stamina", 50, 20),
    "stamina_potion": PotionItem("Зелье выносливости", "stamina", 100, 40),

    # Инструменты
    "basic_axe": WeaponItem("Базовый топор", WeaponType.AXE, 15, ItemQuality.COMMON),
    "basic_pickaxe": WeaponItem("Базовая кирка", WeaponType.PICKAXE, 12, ItemQuality.COMMON),
}


def get_random_loot_from_location(location_type, level=1):
    """
    Получить случайный лут с локации (обертка для ItemGenerator)

    Args:
        location_type: Тип локации
        level: Уровень локации

    Returns:
        list: Список (item, quantity)
    """
    return ItemGenerator.generate_loot_for_location(location_type, level)
