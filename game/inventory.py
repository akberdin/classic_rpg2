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
    BELT = "belt"
    BACKPACK = "backpack"
    # Слоты для зелий в поясе
    BELT_POTION_1 = "belt_potion_1"
    BELT_POTION_2 = "belt_potion_2"
    BELT_POTION_3 = "belt_potion_3"
    BELT_POTION_4 = "belt_potion_4"
    # Слоты для талисманов в поясе
    BELT_TALISMAN_1 = "belt_talisman_1"
    BELT_TALISMAN_2 = "belt_talisman_2"
    BELT_TALISMAN_3 = "belt_talisman_3"
    BELT_TALISMAN_4 = "belt_talisman_4"


# Типы оружия
class WeaponType(Enum):
    """Тип оружия"""
    KNIFE = ("Нож", 1.0, 0.5, 1)
    CLUB = ("Дубина", 1.2, 2.0, 1)
    SWORD = ("Меч", 1.5, 3.0, 1)
    SPEAR = ("Копье", 1.4, 2.5, 2)
    BOW = ("Лук", 1.3, 1.5, 5)  # Базовый радиус, увеличивается с качеством
    STAFF = ("Посох", 1.1, 2.0, 1)
    WAND = ("Жезл", 1.0, 0.8, 1)
    AXE = ("Топор", 1.4, 2.8, 1)
    PICKAXE = ("Кирка", 1.1, 2.5, 1)

    def __init__(self, rus_name, damage_multiplier, weight, tactical_range):
        self.rus_name = rus_name
        self.damage_multiplier = damage_multiplier
        self.weight = weight
        self.tactical_range = tactical_range  # Радиус действия в тактическом бою


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
        self.item_id = None  # Устанавливается реестром при создании

    @property
    def value(self):
        """Стоимость с учетом качества"""
        return int(self.base_value * self.quality.multiplier)

    @property
    def is_stackable(self):
        """Проверить, можно ли стекировать предмет"""
        # Экипируемые предметы не стекируются
        return self.item_type not in ["equipment", "skill_book"]

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
            max_health = character.get_effective_max_health() if hasattr(character, 'get_effective_max_health') else character.max_health
            character.health = min(max_health, character.health + self.effect_value)
            restored = character.health - old_health
            return f"Восстановлено {restored} здоровья"
        elif self.effect_type == "mana":
            if hasattr(character, 'mana'):
                old_mana = character.mana
                max_mana = character.get_effective_max_mana() if hasattr(character, 'get_effective_max_mana') else character.max_mana
                character.mana = min(max_mana, character.mana + self.effect_value)
                restored = character.mana - old_mana
                return f"Восстановлено {restored} маны"
            return "Не применимо к этому персонажу"
        elif self.effect_type == "stamina":
            old_stamina = character.stamina
            max_stamina = character.get_effective_max_stamina() if hasattr(character, 'get_effective_max_stamina') else character.max_stamina
            character.stamina = min(max_stamina, character.stamina + self.effect_value)
            character.is_resting = False  # Снимаем состояние отдыха
            restored = character.stamina - old_stamina
            return f"Восстановлено {restored} выносливости"
        return "Эффект не применен"


class SkillBookItem(Item):
    """Класс для книг умений"""

    # Кэш описаний умений (загружается из конфига)
    _skill_descriptions_cache = None

    @classmethod
    def _load_skill_descriptions(cls):
        """Загрузить описания умений из конфига (ленивая загрузка)."""
        if cls._skill_descriptions_cache is not None:
            return cls._skill_descriptions_cache

        import json
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'skill_book_descriptions.json'
        )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._skill_descriptions_cache = {
                    'skills': data.get('skills', {}),
                    'category_names': data.get('category_names', {
                        'combat': 'Боевое',
                        'magic': 'Магическое',
                        'crafting': 'Ремесленное'
                    })
                }
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback если конфиг не найден
            cls._skill_descriptions_cache = {'skills': {}, 'category_names': {}}

        return cls._skill_descriptions_cache

    @classmethod
    def get_skill_description(cls, skill_id):
        """Получить описание умения по ID."""
        cache = cls._load_skill_descriptions()
        return cache['skills'].get(skill_id)

    def __init__(self, name, skill_id, value=100, weight=0.5, quality=ItemQuality.COMMON):
        """
        Инициализация книги умения

        Args:
            name: Название книги
            skill_id: ID умения для изучения
            value: Стоимость книги
            weight: Вес книги
            quality: Качество книги
        """
        # Генерируем подробное описание книги из конфига
        cache = self._load_skill_descriptions()
        skill_info = cache['skills'].get(skill_id)

        if skill_info:
            skill_name = skill_info.get('name', skill_id)
            category = skill_info.get('category', 'combat')
            effect_desc = skill_info.get('description', '')
            cat_name = cache['category_names'].get(category, 'Умение')
            description = f"{cat_name} умение: {skill_name}. {effect_desc}"
        else:
            description = f"Книга умения: {name}"

        super().__init__(name, "skill_book", value, weight, quality, description)
        self.skill_id = skill_id

    def use(self, character):
        """
        Использовать книгу для изучения умения

        Args:
            character: Персонаж для изучения умения

        Returns:
            str: Сообщение о результате
        """
        if not hasattr(character, 'skill_manager'):
            return "Этот персонаж не может изучать умения"

        # Проверяем, изучено ли уже умение
        if self.skill_id in character.skill_manager.learned_skills:
            return f"Умение '{self.name}' уже изучено"

        # Пытаемся изучить умение
        if character.skill_manager.learn_skill(self.skill_id):
            return f"Изучено умение: {self.name}"
        else:
            return f"Не удалось изучить умение: {self.name}"


class RecipeItem(Item):
    """Класс для рецептов крафта"""

    def __init__(self, name, recipe_id, value=50, weight=0.1, quality=ItemQuality.COMMON, description=""):
        """
        Инициализация рецепта

        Args:
            name: Название рецепта
            recipe_id: ID рецепта в системе крафта
            value: Стоимость рецепта
            weight: Вес рецепта
            quality: Качество рецепта
            description: Описание рецепта
        """
        if not description:
            description = f"Рецепт крафта: {name}"

        super().__init__(name, "recipe", value, weight, quality, description)
        self.recipe_id = recipe_id

    def use(self, character):
        """
        Использовать рецепт для изучения

        Args:
            character: Персонаж для изучения рецепта

        Returns:
            str: Сообщение о результате
        """
        # Проверяем наличие системы рецептов у персонажа
        if not hasattr(character, 'known_recipes'):
            character.known_recipes = set()

        # Проверяем, изучен ли уже рецепт
        if self.recipe_id in character.known_recipes:
            return f"Рецепт '{self.name}' уже изучен"

        # Изучаем рецепт
        character.known_recipes.add(self.recipe_id)
        return f"Изучен рецепт: {self.name}"


class EquipmentItem(Item):
    """Базовый класс для экипируемых предметов"""

    def __init__(self, name, slot, value=100, weight=1.0, quality=ItemQuality.COMMON,
                 stats_bonus=None, param_bonus=None, skill_bonus=None, description=""):
        """
        Инициализация экипируемого предмета

        Args:
            name: Название предмета
            slot: Слот экипировки
            value: Стоимость
            weight: Вес
            quality: Качество
            stats_bonus: Словарь бонусов к характеристикам (strength, dexterity, etc.)
            param_bonus: Словарь процентных бонусов к параметрам (health, mana, stamina)
            skill_bonus: Словарь бонусов к навыкам (skill_id: bonus_value)
            description: Описание
        """
        super().__init__(name, "equipment", value, weight, quality, description)
        # Валидация слота - должен быть EquipmentSlot
        if not isinstance(slot, EquipmentSlot):
            raise ValueError(f"slot must be EquipmentSlot, got {type(slot)}: {slot}")
        self.slot = slot
        self.stats_bonus = stats_bonus or {}
        self.param_bonus = param_bonus or {}  # Процентные бонусы к health/mana/stamina
        self.skill_bonus = skill_bonus or {}  # Бонусы к навыкам

    def get_stat_bonus(self, stat_name):
        """Получить бонус к характеристике (без дополнительных множителей, т.к. они уже в конфиге)"""
        return self.stats_bonus.get(stat_name, 0)

    def get_stats_description(self):
        """Получить описание бонусов"""
        parts = []

        # Бонусы к характеристикам
        if self.stats_bonus:
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
            for stat, bonus in self.stats_bonus.items():
                actual_bonus = self.get_stat_bonus(stat)
                stat_name = stat_names.get(stat, stat)
                parts.append(f"+{actual_bonus} {stat_name}")

        # Процентные бонусы к параметрам
        if self.param_bonus:
            param_names = {
                'health': 'Здоровье',
                'mana': 'Мана',
                'stamina': 'Выносливость'
            }
            for param, bonus in self.param_bonus.items():
                param_name = param_names.get(param, param)
                parts.append(f"+{bonus}% {param_name}")

        # Бонусы к навыкам
        if self.skill_bonus:
            for skill_id, bonus in self.skill_bonus.items():
                parts.append(f"+{bonus} к навыку")

        return ", ".join(parts) if parts else ""


class WeaponItem(EquipmentItem):
    """Класс оружия"""

    def __init__(self, name, weapon_type, base_damage, value=100,
                 quality=ItemQuality.COMMON, stats_bonus=None, param_bonus=None, skill_bonus=None):
        """
        Инициализация оружия

        Args:
            name: Название оружия
            weapon_type: Тип оружия (WeaponType)
            base_damage: Базовый урон
            value: Стоимость
            quality: Качество
            stats_bonus: Дополнительные бонусы к характеристикам
            param_bonus: Процентные бонусы к параметрам
            skill_bonus: Бонусы к навыкам
        """
        weight = weapon_type.weight
        stats = stats_bonus or {}

        # Добавляем урон в статы
        if 'damage' not in stats:
            stats['damage'] = base_damage

        description = f"{weapon_type.rus_name}. Урон: {base_damage}"

        super().__init__(name, EquipmentSlot.WEAPON, value, weight, quality, stats, param_bonus, skill_bonus, description)
        self.weapon_type = weapon_type
        self.base_damage = base_damage

    @property
    def damage(self):
        """Урон с учетом типа оружия и качества"""
        return int(self.get_stat_bonus('damage') * self.weapon_type.damage_multiplier)

    def get_tactical_range(self):
        """
        Получить радиус действия оружия в тактическом бою

        Returns:
            int: Радиус действия в клетках
        """
        base_range = self.weapon_type.tactical_range

        # Для луков радиус увеличивается с качеством
        if self.weapon_type == WeaponType.BOW:
            quality_bonus = {
                ItemQuality.POOR: 0,
                ItemQuality.COMMON: 1,
                ItemQuality.UNCOMMON: 2,
                ItemQuality.RARE: 3,
                ItemQuality.EPIC: 4,
                ItemQuality.LEGENDARY: 5,
                ItemQuality.ARTIFACT: 7
            }
            return base_range + quality_bonus.get(self.quality, 0)

        return base_range


class ArmorItem(EquipmentItem):
    """Класс доспехов"""

    def __init__(self, name, slot, armor_type, base_defense, value=100,
                 quality=ItemQuality.COMMON, stats_bonus=None, param_bonus=None, skill_bonus=None):
        """
        Инициализация доспеха

        Args:
            name: Название доспеха
            slot: Слот экипировки (HEAD, CHEST, HANDS, FEET)
            armor_type: Тип доспеха (ArmorType)
            base_defense: Базовая защита
            value: Стоимость
            quality: Качество
            stats_bonus: Дополнительные бонусы к характеристикам
            param_bonus: Процентные бонусы к параметрам
            skill_bonus: Бонусы к навыкам
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

        super().__init__(name, slot, value, weight, quality, stats, param_bonus, skill_bonus, description)
        self.armor_type = armor_type
        self.base_defense = base_defense

    @property
    def defense(self):
        """Защита с учетом типа доспеха и качества"""
        return int(self.get_stat_bonus('defense') * self.armor_type.defense_multiplier)


class JewelryItem(EquipmentItem):
    """Класс украшений (кольца, амулеты, браслеты)"""

    def __init__(self, name, slot, value=200, quality=ItemQuality.UNCOMMON,
                 stats_bonus=None, param_bonus=None, skill_bonus=None):
        """
        Инициализация украшения

        Args:
            name: Название украшения
            slot: Слот экипировки (RING_1-4, AMULET, BRACELET_1-2)
            value: Стоимость
            quality: Качество
            stats_bonus: Бонусы к характеристикам
            param_bonus: Процентные бонусы к параметрам
            skill_bonus: Бонусы к навыкам
        """
        weight = 0.1  # Украшения очень легкие
        stats = stats_bonus or {}

        description = "Украшение"
        if stats:
            description = f"Украшение. {self._get_bonus_description(stats)}"

        super().__init__(name, slot, value, weight, quality, stats, param_bonus, skill_bonus, description)

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


class BeltItem(EquipmentItem):
    """Класс пояса - предмет с слотами для зелий и талисманов"""

    # Конфигурация слотов в зависимости от качества
    SLOTS_CONFIG = {
        ItemQuality.POOR: (1, 0),       # зелья, талисманы
        ItemQuality.COMMON: (2, 0),
        ItemQuality.UNCOMMON: (2, 1),
        ItemQuality.RARE: (2, 2),
        ItemQuality.EPIC: (3, 2),
        ItemQuality.LEGENDARY: (3, 3),
        ItemQuality.ARTIFACT: (4, 4)
    }

    def __init__(self, name, value=100, quality=ItemQuality.COMMON, param_bonus=None):
        """
        Инициализация пояса

        Args:
            name: Название пояса
            value: Стоимость
            quality: Качество пояса
            param_bonus: Процентные бонусы к health/mana/stamina (только для необычного и выше)
        """
        weight = 1.2

        # Пояс не дает бонусов на плохом и обычном уровне
        if quality in [ItemQuality.POOR, ItemQuality.COMMON]:
            param_bonus = None

        # Получаем количество слотов для данного качества
        potion_slots, talisman_slots = self.SLOTS_CONFIG.get(quality, (1, 0))

        description = f"Пояс. Слотов для зелий: {potion_slots}, Слотов для талисманов: {talisman_slots}"
        if param_bonus:
            bonus_desc = ", ".join([f"+{v}% {k}" for k, v in param_bonus.items()])
            description += f". {bonus_desc}"

        super().__init__(name, EquipmentSlot.BELT, value, weight, quality, None, param_bonus, None, description)
        self.potion_slots = potion_slots
        self.talisman_slots = talisman_slots

    def get_available_potion_slots(self):
        """Получить количество доступных слотов для зелий"""
        return self.potion_slots

    def get_available_talisman_slots(self):
        """Получить количество доступных слотов для талисманов"""
        return self.talisman_slots


class TalismanItem(EquipmentItem):
    """Класс талисмана - предмет для слотов талисманов в поясе"""

    def __init__(self, name, value=50, quality=ItemQuality.COMMON, stats_bonus=None, param_bonus=None):
        """
        Инициализация талисмана

        Args:
            name: Название талисмана
            value: Стоимость
            quality: Качество
            stats_bonus: Бонусы к характеристикам
            param_bonus: Процентные бонусы к параметрам
        """
        weight = 0.2
        stats = stats_bonus or {}

        description = "Талисман"
        if stats or param_bonus:
            desc_parts = []
            if stats:
                desc_parts.append(self._get_bonus_description(stats))
            if param_bonus:
                desc_parts.append(", ".join([f"+{v}% {k}" for k, v in param_bonus.items()]))
            description = f"Талисман. {', '.join(desc_parts)}"

        # Талисман может быть помещен в любой из слотов талисманов
        super().__init__(name, EquipmentSlot.BELT_TALISMAN_1, value, weight, quality, stats, param_bonus, None, description)

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


class BackpackItem(EquipmentItem):
    """Класс рюкзака - увеличивает размер инвентаря"""

    # Конфигурация дополнительных слотов в зависимости от качества
    SLOTS_CONFIG = {
        ItemQuality.POOR: 5,
        ItemQuality.COMMON: 10,
        ItemQuality.UNCOMMON: 15,
        ItemQuality.RARE: 20,
        ItemQuality.EPIC: 25,
        ItemQuality.LEGENDARY: 30,
        ItemQuality.ARTIFACT: 35
    }

    def __init__(self, name, value=200, quality=ItemQuality.COMMON):
        """
        Инициализация рюкзака

        Args:
            name: Название рюкзака
            value: Стоимость
            quality: Качество
        """
        weight = 3.0

        # Получаем количество дополнительных слотов для данного качества
        bonus_slots = self.SLOTS_CONFIG.get(quality, 10)

        description = f"Рюкзак. Добавляет {bonus_slots} слотов к инвентарю"

        super().__init__(name, EquipmentSlot.BACKPACK, value, weight, quality, None, None, None, description)
        self.bonus_slots = bonus_slots

    def get_bonus_slots(self):
        """Получить количество дополнительных слотов"""
        return self.bonus_slots


class Inventory:
    """Класс инвентаря для хранения предметов"""

    def __init__(self, max_slots=5, max_weight=100.0, owner=None):
        """
        Инициализация инвентаря

        Args:
            max_slots: Максимальное количество слотов (по умолчанию 5)
            max_weight: Максимальный вес (кг)
            owner: Владелец инвентаря (персонаж)
        """
        self.items = {}  # {item_name: (item, quantity)}
        self.base_max_slots = max_slots  # Базовый размер инвентаря без рюкзака
        self.max_slots = max_slots
        self.max_weight = max_weight
        self.gold = 0
        self.owner = owner  # Владелец инвентаря для доступа к skill_manager

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
        """Текущий вес инвентаря (только предметы в рюкзаке, не экипированные)"""
        total = 0.0
        # Вес предметов в инвентаре
        for item, quantity in self.items.values():
            total += item.weight * quantity
        # Экипированные предметы НЕ учитываются в весе инвентаря
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
        # Проверка на вес
        new_weight = self.current_weight + (item.weight * quantity)
        if new_weight > self.max_weight:
            return False  # Превышен максимальный вес

        # Определяем, можно ли стекировать предмет
        can_stack = getattr(item, 'is_stackable', True)

        if can_stack and item.name in self.items:
            # Увеличиваем количество существующего стекируемого предмета
            self.items[item.name] = (item, self.items[item.name][1] + quantity)
            return True
        else:
            # Для не-стекируемых предметов создаем уникальный ключ
            if can_stack:
                item_key = item.name
            else:
                # Генерируем уникальный ключ для не-стекируемых предметов
                base_key = item.name
                item_key = base_key
                counter = 1
                while item_key in self.items:
                    item_key = f"{base_key}#{counter}"
                    counter += 1
                # Сохраняем оригинальное имя для отображения
                item._inventory_key = item_key

            # Проверка на количество слотов
            if len(self.items) >= self.max_slots:
                return False  # Инвентарь полон

            # Добавляем новый предмет (для не-стекируемых quantity всегда 1)
            if not can_stack:
                for _ in range(quantity):
                    if len(self.items) >= self.max_slots:
                        return False
                    # Каждый предмет в отдельный слот
                    counter = 1
                    item_key = base_key
                    while item_key in self.items:
                        item_key = f"{base_key}#{counter}"
                        counter += 1
                    self.items[item_key] = (item, 1)
            else:
                self.items[item_key] = (item, quantity)

            return True

    def remove_item(self, item_name_or_object, quantity=1):
        """
        Удалить предмет из инвентаря

        Args:
            item_name_or_object: Название предмета (строка) или объект предмета
            quantity: Количество для удаления

        Returns:
            bool: True если успешно удален
        """
        # Поддерживаем два варианта: строку (ключ) или объект предмета
        if isinstance(item_name_or_object, str):
            item_key = item_name_or_object
            if item_key not in self.items:
                return False
        else:
            # Передан объект предмета - ищем его в инвентаре
            item_obj = item_name_or_object
            item_key = None

            # Ищем предмет по объекту
            for key, (stored_item, qty) in self.items.items():
                if stored_item is item_obj:
                    item_key = key
                    break

            if item_key is None:
                return False

        item, current_quantity = self.items[item_key]

        if current_quantity < quantity:
            return False

        if current_quantity == quantity:
            # Удаляем предмет полностью
            del self.items[item_key]
        else:
            # Уменьшаем количество
            self.items[item_key] = (item, current_quantity - quantity)

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

    def get_item_count(self, item_name):
        """
        Получить количество предмета в инвентаре

        Args:
            item_name: Название предмета

        Returns:
            int: Количество предмета (0 если предмет отсутствует)
        """
        if item_name not in self.items:
            return 0

        _, current_quantity = self.items[item_name]
        return current_quantity

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

    def get_all_items(self, sorted_items=True):
        """
        Получить все предметы

        Args:
            sorted_items: Если True, сортировать по типу и качеству

        Returns:
            list: Список кортежей (item, quantity)
        """
        items = list(self.items.values())
        if sorted_items:
            # Сортировка: сначала по типу, затем по качеству (по убыванию)
            def sort_key(item_tuple):
                item = item_tuple[0]
                # Порядок типов: оружие, броня, украшения, зелья, книги, ресурсы, прочее
                type_order = {'weapon': 0, 'armor': 1, 'jewelry': 2, 'potion': 3, 'book': 4, 'resource': 5, 'other': 6}
                item_type = 'other'
                if isinstance(item, WeaponItem):
                    item_type = 'weapon'
                elif isinstance(item, ArmorItem):
                    item_type = 'armor'
                elif isinstance(item, (BeltItem, BackpackItem)):
                    # Пояса и рюкзаки относятся к категории броня
                    item_type = 'armor'
                elif isinstance(item, JewelryItem):
                    item_type = 'jewelry'
                elif isinstance(item, TalismanItem):
                    # Талисманы относятся к категории украшения
                    item_type = 'jewelry'
                elif isinstance(item, PotionItem):
                    item_type = 'potion'
                elif isinstance(item, SkillBookItem):
                    item_type = 'book'
                elif isinstance(item, ResourceItem):
                    item_type = 'resource'

                # Качество (по убыванию: 6 - артефакт, 0 - плохое)
                quality_order = {'ARTIFACT': 6, 'LEGENDARY': 5, 'EPIC': 4, 'RARE': 3, 'UNCOMMON': 2, 'COMMON': 1, 'POOR': 0}
                quality_value = 0
                if hasattr(item, 'quality'):
                    quality_value = quality_order.get(item.quality.name, 0)

                return (type_order.get(item_type, 6), -quality_value, item.name)

            items = sorted(items, key=sort_key)
        return items

    def equip_item(self, item_name_or_object):
        """
        Экипировать предмет из инвентаря

        Args:
            item_name_or_object: Название предмета (строка) или объект предмета

        Returns:
            tuple: (success, message)
        """
        # Поддерживаем два варианта: строку (ключ) или объект предмета
        if isinstance(item_name_or_object, str):
            item_key = item_name_or_object
            if item_key not in self.items:
                return (False, "Предмет не найден в инвентаре")
            item, quantity = self.items[item_key]
        else:
            # Передан объект предмета - ищем его в инвентаре
            item = item_name_or_object
            item_key = None

            # Ищем предмет по объекту
            for key, (stored_item, qty) in self.items.items():
                if stored_item is item:
                    item_key = key
                    quantity = qty
                    break

            if item_key is None:
                return (False, "Предмет не найден в инвентаре")

        # Проверяем, является ли предмет экипируемым
        if not isinstance(item, EquipmentItem):
            return (False, "Этот предмет нельзя экипировать")

        # СПЕЦИАЛЬНАЯ ПРОВЕРКА ДЛЯ РЮКЗАКА
        if isinstance(item, BackpackItem):
            # Проверяем, есть ли уже экипированный рюкзак
            old_backpack = self.equipment.get(EquipmentSlot.BACKPACK)
            if old_backpack and isinstance(old_backpack, BackpackItem):
                # Новый размер = базовый + бонус от нового рюкзака
                new_max_slots = self.base_max_slots + item.get_bonus_slots()
                current_items_count = len(self.items)

                # Проверяем, поместятся ли все текущие предметы в новый рюкзак
                if current_items_count > new_max_slots:
                    return (False, f"Не могу сменить рюкзак: занято {current_items_count} слотов, а в новом рюкзаке будет доступно только {new_max_slots} слотов. Освободите {current_items_count - new_max_slots} слотов.")

        # Определяем слот
        slot = item.slot

        # Для колец ищем первый свободный слот среди всех 4 слотов
        if slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
            ring_slots = [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]
            # Ищем первый пустой слот
            empty_slot = None
            for ring_slot in ring_slots:
                if not self.equipment[ring_slot]:
                    empty_slot = ring_slot
                    break

            # Если нашли пустой слот, используем его
            if empty_slot:
                slot = empty_slot
            # Если все слоты заняты, используем первый слот (RING_1)
            else:
                slot = EquipmentSlot.RING_1

        # Для браслетов ищем первый свободный слот среди 2 слотов
        elif slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
            bracelet_slots = [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]
            # Ищем первый пустой слот
            empty_slot = None
            for bracelet_slot in bracelet_slots:
                if not self.equipment[bracelet_slot]:
                    empty_slot = bracelet_slot
                    break

            # Если нашли пустой слот, используем его
            if empty_slot:
                slot = empty_slot
            # Если все слоты заняты, используем первый слот (BRACELET_1)
            else:
                slot = EquipmentSlot.BRACELET_1

        # Для талисманов ищем первый свободный слот среди доступных
        elif slot in [EquipmentSlot.BELT_TALISMAN_1, EquipmentSlot.BELT_TALISMAN_2, EquipmentSlot.BELT_TALISMAN_3, EquipmentSlot.BELT_TALISMAN_4]:
            # Проверяем, есть ли экипированный пояс и сколько слотов он предоставляет
            belt = self.equipment.get(EquipmentSlot.BELT)
            if not belt or not isinstance(belt, BeltItem):
                return (False, "Сначала экипируйте пояс")

            available_slots_count = belt.get_available_talisman_slots()
            if available_slots_count == 0:
                return (False, "Экипированный пояс не имеет слотов для талисманов")

            # Определяем доступные слоты
            all_talisman_slots = [EquipmentSlot.BELT_TALISMAN_1, EquipmentSlot.BELT_TALISMAN_2,
                                  EquipmentSlot.BELT_TALISMAN_3, EquipmentSlot.BELT_TALISMAN_4]
            available_slots = all_talisman_slots[:available_slots_count]

            # Ищем первый пустой слот
            empty_slot = None
            for talisman_slot in available_slots:
                if not self.equipment[talisman_slot]:
                    empty_slot = talisman_slot
                    break

            # Если нашли пустой слот, используем его
            if empty_slot:
                slot = empty_slot
            # Если все слоты заняты, используем первый доступный слот
            else:
                slot = available_slots[0]

        # Если слот занят, снимаем старый предмет
        old_item = self.equipment[slot]
        if old_item:
            # Возвращаем старый предмет в инвентарь
            if not self.add_item(old_item, 1):
                return (False, "Не удалось снять экипированный предмет - инвентарь переполнен")

        # Снимаем бонусы умений от старого предмета
        if old_item and hasattr(old_item, 'skill_bonus') and old_item.skill_bonus:
            if hasattr(self, 'owner') and self.owner and hasattr(self.owner, 'skill_manager'):
                for skill_id, skill_rank in old_item.skill_bonus.items():
                    self.owner.skill_manager.revoke_equipment_skill(skill_id, skill_rank)

        # Экипируем новый предмет
        self.equipment[slot] = item
        # Удаляем из инвентаря (используем найденный ключ)
        self.remove_item(item_key, 1)

        # Применяем бонусы умений от нового предмета
        if hasattr(item, 'skill_bonus') and item.skill_bonus:
            if hasattr(self, 'owner') and self.owner and hasattr(self.owner, 'skill_manager'):
                for skill_id, skill_rank in item.skill_bonus.items():
                    self.owner.skill_manager.grant_equipment_skill(skill_id, skill_rank)

        # Обновляем max_slots если экипирован рюкзак
        if isinstance(item, BackpackItem):
            self.max_slots = self.base_max_slots + item.get_bonus_slots()
        # Или если снимаем рюкзак и надеваем что-то другое
        elif isinstance(old_item, BackpackItem):
            self.max_slots = self.base_max_slots

        return (True, f"{item.get_full_name()} экипирован в слот {slot.value}")

    def equip_item_to_slot(self, item_name_or_object, target_slot):
        """
        Экипировать предмет в указанный слот

        Args:
            item_name_or_object: Название предмета (строка) или объект предмета
            target_slot: Целевой слот экипировки (EquipmentSlot)

        Returns:
            tuple: (success, message)
        """
        # Поддерживаем два варианта: строку (ключ) или объект предмета
        if isinstance(item_name_or_object, str):
            item_key = item_name_or_object
            if item_key not in self.items:
                return (False, "Предмет не найден в инвентаре")
            item, quantity = self.items[item_key]
        else:
            # Передан объект предмета - ищем его в инвентаре
            item = item_name_or_object
            item_key = None

            # Ищем предмет по объекту
            for key, (stored_item, qty) in self.items.items():
                if stored_item is item:
                    item_key = key
                    quantity = qty
                    break

            if item_key is None:
                return (False, "Предмет не найден в инвентаре")

        # Проверяем совместимость предмета и слота
        if isinstance(item, PotionItem):
            # Зелье может быть помещено только в слоты зелий
            if target_slot not in [EquipmentSlot.BELT_POTION_1, EquipmentSlot.BELT_POTION_2,
                                   EquipmentSlot.BELT_POTION_3, EquipmentSlot.BELT_POTION_4]:
                return (False, "Зелье можно поместить только в слот зелий")
        elif isinstance(item, TalismanItem):
            # Талисман может быть помещён только в слоты талисманов
            if target_slot not in [EquipmentSlot.BELT_TALISMAN_1, EquipmentSlot.BELT_TALISMAN_2,
                                   EquipmentSlot.BELT_TALISMAN_3, EquipmentSlot.BELT_TALISMAN_4]:
                return (False, "Талисман можно поместить только в слот талисманов")
        elif isinstance(item, EquipmentItem):
            # Для обычной экипировки проверяем соответствие слота
            if item.slot != target_slot:
                # Исключение для колец и браслетов
                if item.slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
                    if target_slot not in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
                        return (False, "Кольцо можно поместить только в слот колец")
                elif item.slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
                    if target_slot not in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
                        return (False, "Браслет можно поместить только в слот браслетов")
                else:
                    return (False, f"Предмет не подходит для этого слота")
        else:
            return (False, "Этот предмет нельзя экипировать")

        # Снимаем старый предмет из целевого слота
        old_item = self.equipment[target_slot]
        if old_item:
            self.add_item(old_item)

        # Удаляем предмет из инвентаря
        self.remove_item(item, 1)

        # Экипируем предмет в целевой слот
        self.equipment[target_slot] = item

        return (True, f"{item.get_full_name() if hasattr(item, 'get_full_name') else item.name} экипирован в слот {target_slot.value}")

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

        # СПЕЦИАЛЬНАЯ ПРОВЕРКА ДЛЯ РЮКЗАКА
        if isinstance(item, BackpackItem):
            # Проверяем, поместятся ли предметы в базовый размер инвентаря
            new_max_slots = self.base_max_slots
            current_items_count = len(self.items)

            # +1 слот нужен будет для самого рюкзака
            if current_items_count + 1 > new_max_slots:
                return (False, f"Не могу снять рюкзак: занято {current_items_count} слотов, а без рюкзака будет доступно только {new_max_slots} слотов. Освободите {current_items_count + 1 - new_max_slots} слотов.")

        # СПЕЦИАЛЬНАЯ ПРОВЕРКА ДЛЯ ПОЯСА
        if isinstance(item, BeltItem):
            # Проверяем, есть ли предметы в слотах талисманов или зелий
            talisman_slots = [EquipmentSlot.BELT_TALISMAN_1, EquipmentSlot.BELT_TALISMAN_2,
                             EquipmentSlot.BELT_TALISMAN_3, EquipmentSlot.BELT_TALISMAN_4]
            potion_slots = [EquipmentSlot.BELT_POTION_1, EquipmentSlot.BELT_POTION_2,
                           EquipmentSlot.BELT_POTION_3, EquipmentSlot.BELT_POTION_4]

            occupied_slots = []
            for t_slot in talisman_slots:
                if self.equipment.get(t_slot):
                    occupied_slots.append(t_slot)
            for p_slot in potion_slots:
                if self.equipment.get(p_slot):
                    occupied_slots.append(p_slot)

            if occupied_slots:
                return (False, "Сначала освободите все слоты пояса (талисманы и зелья)")

        # Пытаемся добавить в инвентарь
        if not self.add_item(item, 1):
            return (False, "Инвентарь переполнен")

        # Снимаем бонусы умений от предмета
        if hasattr(item, 'skill_bonus') and item.skill_bonus:
            if hasattr(self, 'owner') and self.owner and hasattr(self.owner, 'skill_manager'):
                for skill_id, skill_rank in item.skill_bonus.items():
                    self.owner.skill_manager.revoke_equipment_skill(skill_id, skill_rank)

        # Снимаем предмет
        self.equipment[slot] = None

        # Обновляем max_slots если снят рюкзак
        if isinstance(item, BackpackItem):
            self.max_slots = self.base_max_slots

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

    def get_total_param_bonus(self):
        """
        Получить суммарные процентные бонусы к параметрам от всей экипировки

        Returns:
            dict: Словарь процентных бонусов {health, mana, stamina}
        """
        total_bonus = {}

        for item in self.equipment.values():
            if item and isinstance(item, EquipmentItem):
                if hasattr(item, 'param_bonus') and item.param_bonus:
                    for param, bonus in item.param_bonus.items():
                        total_bonus[param] = total_bonus.get(param, 0) + bonus

        return total_bonus

    def get_resource_count(self, resource_name):
        """
        Получить количество ресурса в инвентаре.
        Обертка для совместимости с системой крафта.

        Args:
            resource_name: Название ресурса

        Returns:
            int: Количество ресурса
        """
        return self.get_item_count(resource_name)

    def remove_resource(self, resource_name, quantity):
        """
        Удалить ресурс из инвентаря.
        Обертка для совместимости с системой крафта.

        Args:
            resource_name: Название ресурса
            quantity: Количество для удаления

        Returns:
            bool: True если успешно удален
        """
        return self.remove_item(resource_name, quantity)

    def add_resource(self, resource_name, quantity):
        """
        Добавить ресурс в инвентарь.
        Обертка для совместимости с системой крафта.

        Args:
            resource_name: Название ресурса
            quantity: Количество для добавления

        Returns:
            bool: True если успешно добавлен
        """
        from game.item_registry import get_item
        # Для добавления ресурса нужно получить объект предмета
        if get_item(resource_name):
            resource_item = get_item(resource_name)
            return self.add_item(resource_item, quantity)
        return False


# ===== ГЕНЕРАТОР ПРЕДМЕТОВ =====

class ItemGenerator:
    """Генератор случайных предметов"""

    # Конфигурация предметов (загружается из JSON)
    _config = None

    @classmethod
    def load_config(cls):
        """Загрузить конфигурацию предметов из JSON файла"""
        if cls._config is None:
            import json
            import os
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'items_config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
            except FileNotFoundError:
                print(f"WARNING: Config file not found: {config_path}")
                cls._config = {}
        return cls._config

    @staticmethod
    def get_item_type_by_armor(armor_type):
        """Получить тип предмета из конфига по типу брони"""
        if armor_type == ArmorType.LIGHT:
            return "light_armor"
        elif armor_type == ArmorType.MEDIUM:
            return "medium_armor"
        elif armor_type == ArmorType.HEAVY:
            return "heavy_armor"
        return "light_armor"

    @staticmethod
    def get_item_type_by_slot(slot):
        """Получить тип предмета из конфига по слоту"""
        if slot == EquipmentSlot.AMULET:
            return "amulet"
        elif slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
            return "ring"
        elif slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
            return "bracelet"
        return "ring"

    @staticmethod
    def _filter_weapon_stats(weapon_type, stat_list):
        """
        Фильтрация характеристик для оружия в зависимости от его типа

        Args:
            weapon_type: Тип оружия (WeaponType)
            stat_list: Список доступных характеристик

        Returns:
            list: Отфильтрованный список характеристик
        """
        # Посохи и жезлы - только интеллект и дух
        if weapon_type in [WeaponType.STAFF, WeaponType.WAND]:
            return [s for s in stat_list if s in ['intelligence', 'spirit']]

        # Мечи, дубины, кирки, топоры - не могут иметь интеллект, дух и ловкость
        elif weapon_type in [WeaponType.SWORD, WeaponType.CLUB, WeaponType.PICKAXE, WeaponType.AXE]:
            return [s for s in stat_list if s not in ['intelligence', 'spirit', 'dexterity']]

        # Ножи, луки, копья - не могут иметь дух, силу и телосложение
        elif weapon_type in [WeaponType.KNIFE, WeaponType.BOW, WeaponType.SPEAR]:
            return [s for s in stat_list if s not in ['spirit', 'strength', 'constitution']]

        # Для остальных типов - без изменений
        return stat_list

    @staticmethod
    def _filter_weapon_params(weapon_type, param_list):
        """
        Фильтрация параметров для оружия в зависимости от его типа

        Args:
            weapon_type: Тип оружия (WeaponType)
            param_list: Список доступных параметров

        Returns:
            list: Отфильтрованный список параметров
        """
        # Посохи и жезлы - только здоровье и мана
        if weapon_type in [WeaponType.STAFF, WeaponType.WAND]:
            return [p for p in param_list if p in ['health', 'mana']]

        # Для остальных типов оружия - без изменений
        return param_list

    @classmethod
    def generate_bonuses_from_config(cls, item_type, quality, weapon_type=None):
        """
        Генерировать бонусы для предмета на основе конфига

        Args:
            item_type: Тип предмета (weapon, armor, jewelry)
            quality: Качество предмета
            weapon_type: Тип оружия (WeaponType) для фильтрации профильных умений

        Returns:
            tuple: (stats_bonus, param_bonus, skill_bonus, damage_or_defense_value)
        """
        config = cls.load_config()
        if not config or 'item_parameters' not in config:
            return {}, {}, {}, 0

        quality_name = quality.name.lower()

        # Получаем параметры из конфига
        params = config['item_parameters'].get(item_type, {}).get(quality_name, {})
        if not params:
            return {}, {}, {}, 0

        # Генерация урона/защиты
        damage_range = params.get('damage_range') or params.get('defense_range', [0, 0])
        damage_or_defense = random.randint(damage_range[0], damage_range[1]) if damage_range else 0

        # Генерация бонусов к характеристикам
        stats_bonus = {}
        stats_count_range = params.get('stats_count_range', [0, 0])
        stats_count = random.randint(stats_count_range[0], stats_count_range[1])

        if stats_count > 0:
            stat_bonus_range = params.get('stat_bonus_range', [1, 1])
            stat_bonus_list = params.get('stat_bonus_list', [])

            # Фильтрация характеристик для оружия в зависимости от типа
            if item_type == "weapon" and weapon_type is not None:
                stat_bonus_list = cls._filter_weapon_stats(weapon_type, stat_bonus_list)

            for _ in range(stats_count):
                if stat_bonus_list:
                    stat = random.choice(stat_bonus_list)
                    bonus = random.randint(stat_bonus_range[0], stat_bonus_range[1])
                    stats_bonus[stat] = stats_bonus.get(stat, 0) + bonus

        # Генерация процентных бонусов к параметрам
        param_bonus = {}
        params_count_range = params.get('params_count_range', [0, 0])
        params_count = random.randint(params_count_range[0], params_count_range[1])

        if params_count > 0:
            param_bonus_range = params.get('param_bonus_range', [1, 1])
            param_bonus_list = params.get('param_bonus_list', [])

            # Фильтрация параметров для оружия в зависимости от типа
            if item_type == "weapon" and weapon_type is not None:
                param_bonus_list = cls._filter_weapon_params(weapon_type, param_bonus_list)

            for _ in range(params_count):
                if param_bonus_list:
                    param = random.choice(param_bonus_list)
                    bonus = random.randint(param_bonus_range[0], param_bonus_range[1])
                    param_bonus[param] = param_bonus.get(param, 0) + bonus

        # Генерация бонусов к навыкам
        skill_bonus = {}

        # НОВАЯ ЛОГИКА: Оружие и броня больше НЕ дают бонусы к умениям
        if item_type in ["weapon", "armor", "light_armor", "medium_armor", "heavy_armor"]:
            # Оружие и броня больше не добавляют умения
            pass
        elif item_type in ["ring", "amulet", "bracelet", "jewelry"]:
            # Ювелирные изделия: только одно умение, максимум 1 пункт (легендарное) или 2 пункта (артефакт)
            if quality in [ItemQuality.LEGENDARY, ItemQuality.ARTIFACT]:
                # Определяем максимальный бонус
                max_bonus = 1 if quality == ItemQuality.LEGENDARY else 2

                # Список доступных умений (магические и поддерживающие)
                magic_skills = ['heal', 'regeneration', 'stamina_recovery', 'mage_shield', 'fireball', 'ice_bolt', 'lightning', 'magic_missile']
                combat_skills = ['basic_attack', 'power_strike', 'poison_strike', 'stun_strike', 'battle_cry']
                available_skills = magic_skills + combat_skills

                # Выбираем одно случайное умение
                if available_skills:
                    skill_id = random.choice(available_skills)
                    # Бонус всегда равен максимуму для данного качества
                    skill_bonus[skill_id] = max_bonus

        return stats_bonus, param_bonus, skill_bonus, damage_or_defense

    @classmethod
    def calculate_item_value(cls, item_type, quality, damage_or_defense, stats_bonus, param_bonus, skill_bonus):
        """Рассчитать стоимость предмета на основе конфига"""
        config = cls.load_config()
        if not config:
            return 100

        # Базовая цена
        base_prices = config.get('base_prices', {})
        base_value = base_prices.get(item_type, 50)

        # Получаем мультипликаторы
        quality_name = quality.name.lower()
        params = config['item_parameters'].get(item_type, {}).get(quality_name, {})
        price_multipliers = params.get('price_multipliers', {})

        # Расчет итоговой цены
        total_value = base_value

        # Добавляем стоимость за урон/защиту
        if damage_or_defense > 0:
            multiplier = price_multipliers.get('per_damage', 0) or price_multipliers.get('per_defense', 0)
            total_value += damage_or_defense * multiplier

        # Добавляем стоимость за характеристики
        if stats_bonus:
            multiplier = price_multipliers.get('per_stat', 0)
            total_stats = sum(stats_bonus.values())
            total_value *= (1 + multiplier * total_stats)

        # Добавляем стоимость за параметры
        if param_bonus:
            multiplier = price_multipliers.get('per_param_percent', 0)
            total_params = sum(param_bonus.values())
            total_value *= (1 + multiplier * (total_params / 100))

        # Добавляем стоимость за навыки
        if skill_bonus:
            multiplier = price_multipliers.get('per_skill', 0)
            total_skills = len(skill_bonus)
            total_value *= (1 + multiplier * total_skills)

        return int(total_value)

    @classmethod
    def generate_item_name(cls, base_name, item_type_name, quality):
        """Сгенерировать название предмета с суффиксом из конфига"""
        config = cls.load_config()
        if not config or 'quality_levels' not in config:
            return base_name

        quality_name = quality.name.lower()
        quality_config = config['quality_levels'].get(quality_name, {})
        suffixes = quality_config.get('suffixes', [])

        if suffixes and quality != ItemQuality.COMMON:
            suffix = random.choice(suffixes)
            return f"{item_type_name} {suffix}"

        return item_type_name

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
    def generate_quality_with_luck(luck=1, base_quality_weights=None):
        """
        Генерация качества предмета с учётом удачи игрока.
        1 очко удачи добавляет 1% к шансу получения лучшего качества.

        Args:
            luck: Значение удачи игрока
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

        # Копируем веса для модификации
        modified_weights = base_quality_weights.copy()

        # Бонус от удачи: каждое очко удачи добавляет 1% к шансу лучшего качества
        luck_bonus = min(luck * 0.01, 0.50)  # Максимум 50% бонуса

        # Перераспределяем веса: уменьшаем POOR и COMMON, увеличиваем остальные
        if luck_bonus > 0:
            # Уменьшаем веса низкого качества
            poor_reduction = min(modified_weights[ItemQuality.POOR], luck_bonus * 0.1)
            common_reduction = min(modified_weights[ItemQuality.COMMON], luck_bonus * 0.5)

            modified_weights[ItemQuality.POOR] = max(0.01, modified_weights[ItemQuality.POOR] - poor_reduction)
            modified_weights[ItemQuality.COMMON] = max(0.20, modified_weights[ItemQuality.COMMON] - common_reduction)

            # Добавляем освободившиеся веса к более высокому качеству
            bonus_to_distribute = poor_reduction + common_reduction
            modified_weights[ItemQuality.UNCOMMON] += bonus_to_distribute * 0.35
            modified_weights[ItemQuality.RARE] += bonus_to_distribute * 0.30
            modified_weights[ItemQuality.EPIC] += bonus_to_distribute * 0.20
            modified_weights[ItemQuality.LEGENDARY] += bonus_to_distribute * 0.10
            modified_weights[ItemQuality.ARTIFACT] += bonus_to_distribute * 0.05

        qualities = list(modified_weights.keys())
        weights = list(modified_weights.values())

        return random.choices(qualities, weights=weights)[0]

    @staticmethod
    def check_extra_item_drop(luck=1):
        """
        Проверить, получит ли игрок дополнительный предмет.
        1 очко удачи добавляет 1% к шансу.

        Args:
            luck: Значение удачи игрока

        Returns:
            bool: True если дополнительный предмет должен выпасть
        """
        extra_chance = min(luck * 1, 30)  # Максимум 30% шанс
        return random.randint(1, 100) <= extra_chance

    @staticmethod
    def generate_quality_for_shop(merchant_rank=1):
        """
        Генерация качества предмета для магазина с учетом ранга торговца

        Args:
            merchant_rank: Ранг торговца (1-4), влияет на шанс лучшего качества

        Returns:
            ItemQuality: Качество предмета
        """
        from game.config.merchant_config import MERCHANT_QUALITY_WEIGHTS

        # Получаем веса из конфига
        shop_quality_weights = MERCHANT_QUALITY_WEIGHTS.get(merchant_rank, {ItemQuality.POOR: 1.0})

        return ItemGenerator.generate_quality(shop_quality_weights)

    @classmethod
    def generate_weapon(cls, level=1, quality=None, max_quality=None):
        """
        Генерация случайного оружия (новая версия с использованием конфига)

        Args:
            level: Уровень предмета (не используется в новой системе)
            quality: Качество (если None - случайное)
            max_quality: Максимальное качество (для ограничения генерации)

        Returns:
            WeaponItem
        """
        if quality is None:
            quality = cls.generate_quality()

        weapon_type = random.choice(list(WeaponType))

        # Генерируем бонусы из конфига с учётом типа оружия
        stats_bonus, param_bonus, skill_bonus, base_damage = cls.generate_bonuses_from_config("weapon", quality, weapon_type)

        # Генерируем название
        name = cls.generate_item_name(weapon_type.rus_name, weapon_type.rus_name, quality)

        # Рассчитываем стоимость
        value = cls.calculate_item_value("weapon", quality, base_damage, stats_bonus, param_bonus, skill_bonus)

        return WeaponItem(name, weapon_type, base_damage, value, quality, stats_bonus, param_bonus, skill_bonus)

    @classmethod
    def generate_weapon_by_type(cls, weapon_type, quality=None):
        """
        Генерация оружия определенного типа

        Args:
            weapon_type: Тип оружия (WeaponType)
            quality: Качество (если None - случайное)

        Returns:
            WeaponItem
        """
        if quality is None:
            quality = cls.generate_quality()

        # Генерируем бонусы из конфига с учётом типа оружия
        stats_bonus, param_bonus, skill_bonus, base_damage = cls.generate_bonuses_from_config("weapon", quality, weapon_type)

        # Генерируем название
        name = cls.generate_item_name(weapon_type.rus_name, weapon_type.rus_name, quality)

        # Рассчитываем стоимость
        value = cls.calculate_item_value("weapon", quality, base_damage, stats_bonus, param_bonus, skill_bonus)

        return WeaponItem(name, weapon_type, base_damage, value, quality, stats_bonus, param_bonus, skill_bonus)

    @classmethod
    def generate_armor(cls, level=1, slot=None, armor_type=None, quality=None):
        """
        Генерация случайного доспеха (новая версия с использованием конфига)

        Args:
            level: Уровень предмета (не используется в новой системе)
            slot: Слот (если None - случайный из HEAD, CHEST, HANDS, FEET)
            armor_type: Тип доспеха (если None - случайный)
            quality: Качество (если None - случайное)

        Returns:
            ArmorItem
        """
        if quality is None:
            quality = cls.generate_quality()

        if slot is None:
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                                 EquipmentSlot.HANDS, EquipmentSlot.FEET])

        if armor_type is None:
            armor_type = random.choice(list(ArmorType))

        # Получаем тип предмета для конфига
        item_type = cls.get_item_type_by_armor(armor_type)

        # Генерируем бонусы из конфига
        stats_bonus, param_bonus, skill_bonus, base_defense = cls.generate_bonuses_from_config(item_type, quality)

        # Генерация названия
        slot_names = {
            EquipmentSlot.HEAD: "Шлем",
            EquipmentSlot.CHEST: "Кираса",
            EquipmentSlot.HANDS: "Перчатки",
            EquipmentSlot.FEET: "Сапоги"
        }
        slot_name = slot_names.get(slot, "Доспех")
        name = cls.generate_item_name(f"{armor_type.rus_name} {slot_name}", slot_name, quality)

        # Рассчитываем стоимость
        value = cls.calculate_item_value(item_type, quality, base_defense, stats_bonus, param_bonus, skill_bonus)

        return ArmorItem(name, slot, armor_type, base_defense, value, quality, stats_bonus, param_bonus, skill_bonus)

    @classmethod
    def generate_jewelry(cls, level=1, slot=None, quality=None):
        """
        Генерация случайного украшения (новая версия с использованием конфига)

        Args:
            level: Уровень предмета (не используется в новой системе)
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
            quality = cls.generate_quality(quality_weights)

        if slot is None:
            jewelry_slots = [
                EquipmentSlot.RING_1, EquipmentSlot.RING_2,
                EquipmentSlot.RING_3, EquipmentSlot.RING_4,
                EquipmentSlot.AMULET,
                EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2
            ]
            slot = random.choice(jewelry_slots)

        # Получаем тип предмета для конфига
        item_type = cls.get_item_type_by_slot(slot)

        # Генерируем бонусы из конфига
        stats_bonus, param_bonus, skill_bonus, _ = cls.generate_bonuses_from_config(item_type, quality)

        # Генерация названия
        slot_names = {
            EquipmentSlot.RING_1: "Кольцо", EquipmentSlot.RING_2: "Кольцо",
            EquipmentSlot.RING_3: "Кольцо", EquipmentSlot.RING_4: "Кольцо",
            EquipmentSlot.AMULET: "Амулет",
            EquipmentSlot.BRACELET_1: "Браслет", EquipmentSlot.BRACELET_2: "Браслет"
        }
        slot_name = slot_names.get(slot, "Украшение")
        name = cls.generate_item_name(slot_name, slot_name, quality)

        # Рассчитываем стоимость
        value = cls.calculate_item_value(item_type, quality, 0, stats_bonus, param_bonus, skill_bonus)

        return JewelryItem(name, slot, value, quality, stats_bonus, param_bonus, skill_bonus)

    @classmethod
    def generate_belt(cls, level=1, quality=None, max_quality=None):
        """
        Генерировать случайный пояс

        Args:
            level: Уровень (влияет на параметры)
            quality: Качество предмета (если None - генерируется случайно)
            max_quality: Максимальное качество (ограничение)

        Returns:
            BeltItem: Сгенерированный пояс
        """
        # Определяем качество
        if quality is None:
            quality = cls.generate_quality(max_quality)

        # Генерируем процентные бонусы к параметрам (только для необычного и выше)
        param_bonus = None
        if quality not in [ItemQuality.POOR, ItemQuality.COMMON]:
            param_bonus = {}
            # Количество бонусов зависит от качества
            bonus_count = {
                ItemQuality.UNCOMMON: 1,
                ItemQuality.RARE: 1,
                ItemQuality.EPIC: 2,
                ItemQuality.LEGENDARY: 2,
                ItemQuality.ARTIFACT: 3
            }.get(quality, 1)

            # Диапазон бонусов зависит от качества
            bonus_range = {
                ItemQuality.UNCOMMON: (2, 4),
                ItemQuality.RARE: (4, 6),
                ItemQuality.EPIC: (6, 8),
                ItemQuality.LEGENDARY: (8, 10),
                ItemQuality.ARTIFACT: (10, 15)
            }.get(quality, (2, 4))

            available_params = ['health', 'mana', 'stamina']
            selected_params = random.sample(available_params, min(bonus_count, len(available_params)))
            for param in selected_params:
                param_bonus[param] = random.randint(bonus_range[0], bonus_range[1])

        # Генерируем название
        name = cls.generate_item_name("Пояс", "Пояс", quality)

        # Рассчитываем стоимость
        base_value = 100
        value = int(base_value * quality.multiplier)
        if param_bonus:
            value += sum(param_bonus.values()) * 10

        return BeltItem(name, value, quality, param_bonus)

    @classmethod
    def generate_backpack(cls, level=1, quality=None, max_quality=None):
        """
        Генерировать случайный рюкзак

        Args:
            level: Уровень (влияет на параметры)
            quality: Качество предмета (если None - генерируется случайно)
            max_quality: Максимальное качество (ограничение)

        Returns:
            BackpackItem: Сгенерированный рюкзак
        """
        # Определяем качество
        if quality is None:
            quality = cls.generate_quality(max_quality)

        # Генерируем название
        name = cls.generate_item_name("Рюкзак", "Рюкзак", quality)

        # Рассчитываем стоимость (базово + за слоты)
        base_value = 200
        bonus_slots = BackpackItem.SLOTS_CONFIG.get(quality, 10)
        value = int(base_value * quality.multiplier + bonus_slots * 5)

        return BackpackItem(name, value, quality)

    @classmethod
    def generate_talisman(cls, level=1, quality=None, max_quality=None):
        """
        Генерировать случайный талисман

        Args:
            level: Уровень (влияет на параметры)
            quality: Качество предмета (если None - генерируется случайно)
            max_quality: Максимальное качество (ограничение)

        Returns:
            TalismanItem: Сгенерированный талисман
        """
        # Определяем качество
        if quality is None:
            quality = cls.generate_quality(max_quality)

        # Генерируем бонусы к характеристикам
        stats_bonus = {}
        param_bonus = {}

        # Количество бонусов зависит от качества
        bonus_count = {
            ItemQuality.POOR: 0,
            ItemQuality.COMMON: 1,
            ItemQuality.UNCOMMON: 1,
            ItemQuality.RARE: 2,
            ItemQuality.EPIC: 2,
            ItemQuality.LEGENDARY: 3,
            ItemQuality.ARTIFACT: 3
        }.get(quality, 1)

        # Диапазон бонусов зависит от качества
        bonus_range = {
            ItemQuality.POOR: (1, 2),
            ItemQuality.COMMON: (1, 2),
            ItemQuality.UNCOMMON: (2, 3),
            ItemQuality.RARE: (3, 5),
            ItemQuality.EPIC: (5, 7),
            ItemQuality.LEGENDARY: (7, 10),
            ItemQuality.ARTIFACT: (10, 15)
        }.get(quality, (1, 2))

        if bonus_count > 0:
            available_stats = ['strength', 'dexterity', 'constitution', 'spirit', 'intelligence', 'luck']
            selected_stats = random.sample(available_stats, min(bonus_count, len(available_stats)))
            for stat in selected_stats:
                stats_bonus[stat] = random.randint(bonus_range[0], bonus_range[1])

        # Генерируем название
        name = cls.generate_item_name("Талисман", "Талисман", quality)

        # Рассчитываем стоимость
        base_value = 50
        value = int(base_value * quality.multiplier)
        if stats_bonus:
            value += sum(stats_bonus.values()) * 5

        return TalismanItem(name, value, quality, stats_bonus, param_bonus)

    @staticmethod
    def generate_loot_for_location(location_type, level=1, luck=1):
        """
        Генерация лута для конкретной локации с учётом удачи

        Args:
            location_type: Тип локации
            level: Уровень локации (влияет на качество лута)
            luck: Удача игрока (влияет на качество и шанс доп. предметов)

        Returns:
            list: Список (item, quantity)
        """
        from game.item_registry import get_item
        from game.constants import LOCATION_MINE, LOCATION_RUINS, LOCATION_BANDIT_CAMP
        loot = []

        if location_type == LOCATION_MINE:
            # Руда из шахт - удача влияет на тип руды
            # Шанс добычи руды уменьшен в 10 раз (10% базовый шанс)
            ore_chance = 0.10 + min(luck * 0.001, 0.05)  # 10% базовый + до 5% от удачи

            if random.random() < ore_chance:
                ores = ["copper_ore", "iron_ore", "silver_ore", "gold_ore", "mithril_ore"]
                # Модифицируем веса с учётом удачи
                luck_modifier = min(luck * 0.005, 0.15)  # Макс 15% смещение
                weights = [
                    max(0.35 - luck_modifier, 0.20),  # copper
                    0.30,  # iron
                    0.12 + luck_modifier * 0.5,  # silver
                    0.06 + luck_modifier * 0.3,  # gold
                    0.02 + luck_modifier * 0.2   # mithril
                ]
                ore_type = random.choices(ores, weights=weights)[0]
                quantity = random.randint(1, 3)
                loot.append((get_item(ore_type), quantity))

                # Шанс доп. руды от удачи (также уменьшен)
                if ItemGenerator.check_extra_item_drop(luck) and random.random() < 0.1:
                    extra_ore = random.choices(ores, weights=weights)[0]
                    loot.append((get_item(extra_ore), 1))

        elif location_type == LOCATION_RUINS:
            # Артефакты из руин
            artifacts = ["ancient_coin", "artifact_fragment", "magic_crystal", "old_scroll"]
            luck_modifier = min(luck * 0.005, 0.15)
            weights = [
                max(0.5 - luck_modifier, 0.30),  # coin
                0.3,  # fragment
                0.1 + luck_modifier * 0.6,  # crystal
                0.1 + luck_modifier * 0.4   # scroll
            ]
            artifact_type = random.choices(artifacts, weights=weights)[0]
            quantity = random.randint(1, 2)
            loot.append((get_item(artifact_type), quantity))

            # Шанс найти экипировку (базовый + бонус от удачи)
            equip_chance = 0.4 + min(luck * 0.01, 0.20)  # Макс +20%
            if random.random() < equip_chance:
                item_type = random.choice(['weapon', 'armor', 'jewelry', 'belt', 'backpack', 'talisman'])
                quality = ItemGenerator.generate_quality_with_luck(luck)
                if item_type == 'weapon':
                    loot.append((ItemGenerator.generate_weapon(level, quality=quality), 1))
                elif item_type == 'armor':
                    loot.append((ItemGenerator.generate_armor(level, quality=quality), 1))
                elif item_type == 'jewelry':
                    loot.append((ItemGenerator.generate_jewelry(level, quality=quality), 1))
                elif item_type == 'belt':
                    loot.append((ItemGenerator.generate_belt(level, quality=quality), 1))
                elif item_type == 'backpack':
                    loot.append((ItemGenerator.generate_backpack(level, quality=quality), 1))
                elif item_type == 'talisman':
                    loot.append((ItemGenerator.generate_talisman(level, quality=quality), 1))

            # Шанс найти зелье
            potion_chance = 0.3 + min(luck * 0.005, 0.15)
            if random.random() < potion_chance:
                potions = ["minor_health_potion", "health_potion", "minor_mana_potion"]
                potion_type = random.choice(potions)
                loot.append((get_item(potion_type), 1))

            # Дополнительный предмет от удачи
            if ItemGenerator.check_extra_item_drop(luck):
                extra_artifact = random.choices(artifacts, weights=weights)[0]
                loot.append((get_item(extra_artifact), 1))

            # Шанс найти книгу умений в руинах (базовый 15% + бонус от удачи до 10%)
            book_chance = 0.15 + min(luck * 0.005, 0.10)
            if random.random() < book_chance:
                # Список всех книг умений
                all_skill_books = [
                    # Общие боевые умения
                    "book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry",
                    # Умения лука
                    "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
                    # Умения кинжала
                    "book_backstab", "book_bleeding_cut", "book_shadow_step",
                    # Умения меча
                    "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance",
                    # Магические умения (поддержка)
                    "book_heal", "book_regeneration", "book_stamina_recovery", "book_mage_shield",
                    # Атакующая магия
                    "book_magic_missile", "book_fireball", "book_ice_bolt", "book_lightning"
                ]

                # Выбираем случайную книгу
                book_id = random.choice(all_skill_books)
                if get_item(book_id):
                    loot.append((get_item(book_id), 1))

            # Шанс найти рецепт крафта в руинах (базовый 10% + бонус от удачи до 5%)
            recipe_chance = 0.10 + min(luck * 0.003, 0.05)
            if random.random() < recipe_chance:
                recipes = [
                    "recipe_copper_ingot", "recipe_iron_ingot", "recipe_silver_ingot",
                    "recipe_gold_ingot", "recipe_mithril_ingot"
                ]
                recipe_id = random.choice(recipes)
                if get_item(recipe_id):
                    loot.append((get_item(recipe_id), 1))

        elif location_type == LOCATION_BANDIT_CAMP:
            # Бандиты могут иметь разное снаряжение
            weapon_chance = 0.3 + min(luck * 0.01, 0.15)
            if random.random() < weapon_chance:
                quality = ItemGenerator.generate_quality_with_luck(luck)
                loot.append((ItemGenerator.generate_weapon(level, quality=quality), 1))

            armor_chance = 0.2 + min(luck * 0.01, 0.15)
            if random.random() < armor_chance:
                quality = ItemGenerator.generate_quality_with_luck(luck)
                loot.append((ItemGenerator.generate_armor(level, quality=quality), 1))

            # Шанс найти ювелирные изделия (награбленные бандитами)
            jewelry_chance = 0.15 + min(luck * 0.008, 0.12)  # 15% базовый + до 12% от удачи
            if random.random() < jewelry_chance:
                quality = ItemGenerator.generate_quality_with_luck(luck)
                loot.append((ItemGenerator.generate_jewelry(level, quality=quality), 1))

            # Золото (бонус от удачи)
            luck_gold_bonus = 1 + min(luck * 0.02, 0.50)  # До +50% золота
            gold_amount = int(random.randint(10, 50) * level * luck_gold_bonus)
            loot.append(('gold', gold_amount))

            # Дополнительный предмет от удачи
            if ItemGenerator.check_extra_item_drop(luck):
                quality = ItemGenerator.generate_quality_with_luck(luck)
                extra_item = random.choice(['weapon', 'armor', 'jewelry'])
                if extra_item == 'weapon':
                    loot.append((ItemGenerator.generate_weapon(level, quality=quality), 1))
                elif extra_item == 'armor':
                    loot.append((ItemGenerator.generate_armor(level, quality=quality), 1))
                else:
                    loot.append((ItemGenerator.generate_jewelry(level, quality=quality), 1))

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
            equipment.append(ItemGenerator.generate_weapon(
                level,
                quality=random.choice([ItemQuality.POOR, ItemQuality.COMMON])
            ))

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
            weapon = ItemGenerator.generate_weapon(
                level,
                quality=ItemQuality.COMMON
            )
            weapon.name = "Торговый нож"  # Переименовываем для уникальности
            equipment.append(weapon)

            # Украшения (символ богатства)
            if random.random() < 0.7:  # 70% шанс
                equipment.append(ItemGenerator.generate_jewelry(level))

        elif npc_type == "miner":
            # Шахтеры имеют кирку и легкие доспехи
            weapon = ItemGenerator.generate_weapon(
                level,
                quality=ItemQuality.COMMON
            )
            weapon.name = "Шахтерская кирка"  # Переименовываем для уникальности
            weapon.weapon_type = WeaponType.PICKAXE
            equipment.append(weapon)

            # Частичные доспехи для защиты
            if random.random() < 0.6:
                armor_slots = random.sample(
                    [EquipmentSlot.HEAD, EquipmentSlot.CHEST],
                    k=random.randint(1, 2)
                )
                for slot in armor_slots:
                    armor = ItemGenerator.generate_armor(
                        level,
                        slot=slot,
                        armor_type=ArmorType.LIGHT,
                        quality=ItemQuality.COMMON
                    )
                    equipment.append(armor)

        elif npc_type == "undead":
            # Нежить носит древнее/проклятое снаряжение
            weapon = ItemGenerator.generate_weapon(
                level,
                quality=random.choice([ItemQuality.POOR, ItemQuality.COMMON])
            )
            # Добавляем префикс "Проклятый" к имени
            weapon.name = f"Проклятый {weapon.name}"
            equipment.append(weapon)

            # Разрушенные доспехи
            if random.random() < 0.4:
                armor_slots = random.sample(
                    [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET],
                    k=random.randint(1, 3)
                )
                for slot in armor_slots:
                    armor = ItemGenerator.generate_armor(
                        level,
                        slot=slot,
                        armor_type=random.choice([ArmorType.LIGHT, ArmorType.MEDIUM]),
                        quality=ItemQuality.POOR
                    )
                    equipment.append(armor)

        elif npc_type == "mage":
            # Маги имеют посох и магическую одежду
            weapon = ItemGenerator.generate_weapon(
                level,
                quality=ItemQuality.UNCOMMON
            )
            weapon.name = "Магический посох"  # Переименовываем для уникальности
            weapon.weapon_type = WeaponType.STAFF
            equipment.append(weapon)

            # Легкие доспехи (мантия)
            chest_armor = ItemGenerator.generate_armor(
                level,
                slot=EquipmentSlot.CHEST,
                armor_type=ArmorType.LIGHT,
                quality=ItemQuality.UNCOMMON
            )
            equipment.append(chest_armor)

            # Украшения (символ магической силы)
            if random.random() < 0.8:
                equipment.append(ItemGenerator.generate_jewelry(level))

        elif npc_type in ["wolf", "bear", "deer"]:
            # Животные не имеют экипировки - только лут после смерти
            # Лут генерируется через generate_animal_loot()
            return []

        return equipment

    @staticmethod
    def generate_npc_equipment_by_rank(npc_type, level=1):
        """
        Генерация экипировки для NPC на основе ранга (уровня)
        Чем выше ранг, тем лучше и больше экипировки

        Args:
            npc_type: Тип NPC
            level: Уровень NPC

        Returns:
            list: Список предметов экипировки
        """
        # Определяем ранг по уровню
        if level <= 10:
            rank = "novice"
            # Ранг 1: плохие, обычные
            quality_weights = {ItemQuality.POOR: 0.4, ItemQuality.COMMON: 0.6}
            num_items = random.randint(1, 2)
        elif level <= 20:
            rank = "regular"
            # Ранг 2: обычные, необычные
            quality_weights = {ItemQuality.COMMON: 0.5, ItemQuality.UNCOMMON: 0.5}
            num_items = random.randint(2, 3)
        elif level <= 30:
            rank = "veteran"
            # Ранг 3: обычные, необычные, редкие
            quality_weights = {ItemQuality.COMMON: 0.3, ItemQuality.UNCOMMON: 0.4, ItemQuality.RARE: 0.3}
            num_items = random.randint(3, 5)
        else:
            rank = "expert"
            # Ранг 4: любого качества
            quality_weights = {
                ItemQuality.POOR: 0.05,
                ItemQuality.COMMON: 0.15,
                ItemQuality.UNCOMMON: 0.25,
                ItemQuality.RARE: 0.3,
                ItemQuality.EPIC: 0.2,
                ItemQuality.LEGENDARY: 0.05
            }
            num_items = random.randint(4, 6)

        equipment = []

        # Всегда добавляем оружие
        weapon_quality = ItemGenerator.generate_quality(quality_weights)
        if npc_type == "guard":
            weapon_type = random.choice([WeaponType.SWORD, WeaponType.SPEAR])
            equipment.append(ItemGenerator.generate_weapon(level, weapon_quality))
        elif npc_type == "bandit":
            weapon_type = random.choice([WeaponType.KNIFE, WeaponType.CLUB, WeaponType.SWORD])
            equipment.append(ItemGenerator.generate_weapon(level, weapon_quality))
        elif npc_type == "miner":
            weapon = ItemGenerator.generate_weapon(level, weapon_quality)
            weapon.name = "Шахтерская кирка"
            weapon.weapon_type = WeaponType.PICKAXE
            equipment.append(weapon)
        elif npc_type == "undead":
            weapon_type = random.choice([WeaponType.SWORD, WeaponType.AXE])
            equipment.append(ItemGenerator.generate_weapon(level, weapon_quality))
        elif npc_type == "mage":
            weapon = ItemGenerator.generate_weapon(level, weapon_quality)
            weapon.name = "Магический посох"
            weapon.weapon_type = WeaponType.STAFF
            equipment.append(weapon)
        else:
            equipment.append(ItemGenerator.generate_weapon(level, weapon_quality))

        # Добавляем доспехи в зависимости от количества предметов
        armor_slots = [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]
        armor_count = min(num_items - 1, len(armor_slots))

        if armor_count > 0:
            selected_slots = random.sample(armor_slots, armor_count)

            # Тип доспехов зависит от типа NPC
            if npc_type in ["guard"]:
                armor_type = random.choice([ArmorType.MEDIUM, ArmorType.HEAVY])
            elif npc_type in ["mage", "merchant"]:
                armor_type = ArmorType.LIGHT
            else:
                armor_type = random.choice(list(ArmorType))

            for slot in selected_slots:
                armor_quality = ItemGenerator.generate_quality(quality_weights)
                armor = ItemGenerator.generate_armor(level, slot, armor_type, armor_quality)
                equipment.append(armor)

        # Для высоких рангов добавляем украшения
        if rank in ["veteran", "expert"] and random.random() < 0.5:
            jewelry_quality = ItemGenerator.generate_quality(quality_weights)
            equipment.append(ItemGenerator.generate_jewelry(level, quality=jewelry_quality))

        return equipment

    @staticmethod
    def generate_animal_loot(npc_type, npc_level=1):
        """
        Генерация лута от животных после смерти

        Args:
            npc_type: Тип животного (wolf, bear, deer)
            npc_level: Уровень животного (для особых дропов)

        Returns:
            list: Список предметов лута
        """
        from game.item_registry import get_item
        loot = []

        if npc_type == "wolf":
            # Волки дают: зубы волка, шкура волка
            # Клык волка - 70% шанс
            if random.random() < 0.7:
                loot.append(get_item("wolf_fang"))

            # Шкура волка - 50% шанс
            if random.random() < 0.5:
                loot.append(get_item("wolf_hide"))

            # Звериные жилы - 40% шанс
            if random.random() < 0.4:
                loot.append(get_item("animal_sinew"))

        elif npc_type == "bear":
            # Медведи дают: зубы медведя, мясо, шкура медведя
            # Клык медведя - 60% шанс
            if random.random() < 0.6:
                loot.append(get_item("bear_fang"))

            # Мясо - 80% шанс
            if random.random() < 0.8:
                loot.append(get_item("bear_meat"))

            # Шкура медведя - 50% шанс
            if random.random() < 0.5:
                loot.append(get_item("bear_hide"))

            # Звериные жилы - 50% шанс
            if random.random() < 0.5:
                loot.append(get_item("animal_sinew"))

        elif npc_type == "deer":
            # Олени дают: мясо, шкура оленя
            # Мясо - 90% шанс
            if random.random() < 0.9:
                loot.append(get_item("deer_meat"))

            # Шкура оленя - 60% шанс
            if random.random() < 0.6:
                loot.append(get_item("deer_hide"))

            # Звериные жилы - 30% шанс
            if random.random() < 0.3:
                loot.append(get_item("animal_sinew"))

            # Рога оленя - только у оленей уровня 2 и выше, 50% шанс
            if npc_level >= 2 and random.random() < 0.5:
                loot.append(get_item("deer_antlers"))

        return loot




def get_random_loot_from_location(location_type, level=1, luck=1):
    """
    Получить случайный лут с локации (обертка для ItemGenerator)

    Args:
        location_type: Тип локации
        level: Уровень локации
        luck: Удача игрока (влияет на качество и шанс доп. предметов)

    Returns:
        list: Список (item, quantity)
    """
    return ItemGenerator.generate_loot_for_location(location_type, level, luck)


def get_predefined_item(item_id):
    """
    Получить предмет по ID.

    Рекомендуемый способ: используйте game.item_registry.get_item() напрямую.

    Args:
        item_id: Идентификатор предмета

    Returns:
        Item: Объект предмета или None
    """
    from game.item_registry import get_item
    return get_item(item_id)


def get_item_by_id(item_id):
    """
    Алиас для get_predefined_item для совместимости.

    DEPRECATED: Используйте game.item_registry.get_item() напрямую.
    """
    return get_predefined_item(item_id)
