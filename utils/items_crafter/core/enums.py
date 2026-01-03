"""
Перечисления для системы предметов v2.0
Чёткие определения всех типов без двоякого толкования
"""

from enum import Enum
from typing import Dict, Tuple, List


class ItemCategory(Enum):
    """
    Категория предмета - определяет базовое поведение
    """
    RESOURCE = "resource"       # Ресурс (стакается, не экипируется)
    EQUIPMENT = "equipment"     # Экипировка (не стакается, экипируется)
    CONSUMABLE = "consumable"   # Расходник (стакается, используется)
    QUEST = "quest"             # Квестовый предмет
    MISC = "misc"               # Прочее

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.RESOURCE.value: "Ресурс",
            cls.EQUIPMENT.value: "Экипировка",
            cls.CONSUMABLE.value: "Расходник",
            cls.QUEST.value: "Квестовый",
            cls.MISC.value: "Прочее",
        }


class EquipmentType(Enum):
    """
    Тип экипировки - определяет слот и базовые характеристики
    """
    # Оружие
    WEAPON_MELEE_1H = "weapon_melee_1h"     # Одноручное ближнее
    WEAPON_MELEE_2H = "weapon_melee_2h"     # Двуручное ближнее
    WEAPON_RANGED = "weapon_ranged"         # Дальнобойное
    WEAPON_MAGIC = "weapon_magic"           # Магическое

    # Броня
    ARMOR_HEAD = "armor_head"               # Шлем
    ARMOR_CHEST = "armor_chest"             # Нагрудник
    ARMOR_HANDS = "armor_hands"             # Перчатки
    ARMOR_FEET = "armor_feet"               # Обувь
    ARMOR_BELT = "armor_belt"               # Пояс

    # Украшения
    JEWELRY_RING = "jewelry_ring"           # Кольцо
    JEWELRY_AMULET = "jewelry_amulet"       # Амулет
    JEWELRY_BRACELET = "jewelry_bracelet"   # Браслет

    # Прочее
    TOOL = "tool"                           # Инструмент
    BACKPACK = "backpack"                   # Рюкзак

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.WEAPON_MELEE_1H.value: "Одноручное оружие",
            cls.WEAPON_MELEE_2H.value: "Двуручное оружие",
            cls.WEAPON_RANGED.value: "Дальнобойное оружие",
            cls.WEAPON_MAGIC.value: "Магическое оружие",
            cls.ARMOR_HEAD.value: "Шлем",
            cls.ARMOR_CHEST.value: "Нагрудник",
            cls.ARMOR_HANDS.value: "Перчатки",
            cls.ARMOR_FEET.value: "Обувь",
            cls.ARMOR_BELT.value: "Пояс",
            cls.JEWELRY_RING.value: "Кольцо",
            cls.JEWELRY_AMULET.value: "Амулет",
            cls.JEWELRY_BRACELET.value: "Браслет",
            cls.TOOL.value: "Инструмент",
            cls.BACKPACK.value: "Рюкзак",
        }

    @classmethod
    def get_weapons(cls) -> List["EquipmentType"]:
        return [cls.WEAPON_MELEE_1H, cls.WEAPON_MELEE_2H, cls.WEAPON_RANGED, cls.WEAPON_MAGIC]

    @classmethod
    def get_armor(cls) -> List["EquipmentType"]:
        return [cls.ARMOR_HEAD, cls.ARMOR_CHEST, cls.ARMOR_HANDS, cls.ARMOR_FEET, cls.ARMOR_BELT]

    @classmethod
    def get_jewelry(cls) -> List["EquipmentType"]:
        return [cls.JEWELRY_RING, cls.JEWELRY_AMULET, cls.JEWELRY_BRACELET]

    def is_weapon(self) -> bool:
        return self in self.get_weapons()

    def is_armor(self) -> bool:
        return self in self.get_armor()

    def is_jewelry(self) -> bool:
        return self in self.get_jewelry()


class WeaponSubtype(Enum):
    """
    Подтип оружия - конкретный вид оружия
    """
    # Одноручное ближнее
    DAGGER = "dagger"
    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"

    # Двуручное ближнее
    GREATSWORD = "greatsword"
    GREATAXE = "greataxe"
    SPEAR = "spear"
    STAFF_MELEE = "staff_melee"

    # Дальнобойное
    BOW = "bow"
    CROSSBOW = "crossbow"

    # Магическое
    WAND = "wand"
    STAFF_MAGIC = "staff_magic"
    ORB = "orb"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.DAGGER.value: "Кинжал",
            cls.SWORD.value: "Меч",
            cls.AXE.value: "Топор",
            cls.MACE.value: "Булава",
            cls.GREATSWORD.value: "Двуручный меч",
            cls.GREATAXE.value: "Двуручный топор",
            cls.SPEAR.value: "Копьё",
            cls.STAFF_MELEE.value: "Боевой посох",
            cls.BOW.value: "Лук",
            cls.CROSSBOW.value: "Арбалет",
            cls.WAND.value: "Жезл",
            cls.STAFF_MAGIC.value: "Магический посох",
            cls.ORB.value: "Сфера",
        }

    @classmethod
    def get_tactical_range(cls) -> Dict[str, int]:
        """Тактический радиус атаки"""
        return {
            cls.DAGGER.value: 1,
            cls.SWORD.value: 1,
            cls.AXE.value: 1,
            cls.MACE.value: 1,
            cls.GREATSWORD.value: 1,
            cls.GREATAXE.value: 1,
            cls.SPEAR.value: 2,
            cls.STAFF_MELEE.value: 2,
            cls.BOW.value: 6,
            cls.CROSSBOW.value: 5,
            cls.WAND.value: 4,
            cls.STAFF_MAGIC.value: 4,
            cls.ORB.value: 3,
        }

    @classmethod
    def get_base_damage_multiplier(cls) -> Dict[str, float]:
        """Базовый множитель урона"""
        return {
            cls.DAGGER.value: 0.8,
            cls.SWORD.value: 1.0,
            cls.AXE.value: 1.1,
            cls.MACE.value: 1.0,
            cls.GREATSWORD.value: 1.5,
            cls.GREATAXE.value: 1.6,
            cls.SPEAR.value: 1.3,
            cls.STAFF_MELEE.value: 1.2,
            cls.BOW.value: 1.2,
            cls.CROSSBOW.value: 1.4,
            cls.WAND.value: 0.9,
            cls.STAFF_MAGIC.value: 1.1,
            cls.ORB.value: 0.7,
        }

    @classmethod
    def get_equipment_type(cls, subtype: "WeaponSubtype") -> EquipmentType:
        """Получить тип экипировки для подтипа оружия"""
        one_handed = [cls.DAGGER, cls.SWORD, cls.AXE, cls.MACE]
        two_handed = [cls.GREATSWORD, cls.GREATAXE, cls.SPEAR, cls.STAFF_MELEE]
        ranged = [cls.BOW, cls.CROSSBOW]
        magic = [cls.WAND, cls.STAFF_MAGIC, cls.ORB]

        if subtype in one_handed:
            return EquipmentType.WEAPON_MELEE_1H
        elif subtype in two_handed:
            return EquipmentType.WEAPON_MELEE_2H
        elif subtype in ranged:
            return EquipmentType.WEAPON_RANGED
        elif subtype in magic:
            return EquipmentType.WEAPON_MAGIC
        return EquipmentType.WEAPON_MELEE_1H


class ArmorWeight(Enum):
    """
    Класс брони - определяет защиту и требования
    """
    CLOTH = "cloth"         # Тканевая
    LIGHT = "light"         # Лёгкая (кожа)
    MEDIUM = "medium"       # Средняя (кольчуга)
    HEAVY = "heavy"         # Тяжёлая (латы)

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.CLOTH.value: "Тканевая",
            cls.LIGHT.value: "Лёгкая",
            cls.MEDIUM.value: "Средняя",
            cls.HEAVY.value: "Тяжёлая",
        }

    @classmethod
    def get_defense_multiplier(cls) -> Dict[str, float]:
        """Множитель защиты"""
        return {
            cls.CLOTH.value: 0.5,
            cls.LIGHT.value: 1.0,
            cls.MEDIUM.value: 1.5,
            cls.HEAVY.value: 2.0,
        }


class ItemQuality(Enum):
    """
    Качество предмета - влияет на характеристики и цену
    Каждое качество имеет чёткие множители
    """
    POOR = "poor"               # Плохое (серый)
    COMMON = "common"           # Обычное (белый)
    UNCOMMON = "uncommon"       # Необычное (зелёный)
    RARE = "rare"               # Редкое (синий)
    EPIC = "epic"               # Эпическое (фиолетовый)
    LEGENDARY = "legendary"     # Легендарное (оранжевый)
    ARTIFACT = "artifact"       # Артефакт (золотой)

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.POOR.value: "Плохое",
            cls.COMMON.value: "Обычное",
            cls.UNCOMMON.value: "Необычное",
            cls.RARE.value: "Редкое",
            cls.EPIC.value: "Эпическое",
            cls.LEGENDARY.value: "Легендарное",
            cls.ARTIFACT.value: "Артефакт",
        }

    @classmethod
    def get_colors(cls) -> Dict[str, Tuple[int, int, int]]:
        """RGB цвета для отображения"""
        return {
            cls.POOR.value: (128, 128, 128),
            cls.COMMON.value: (255, 255, 255),
            cls.UNCOMMON.value: (30, 255, 0),
            cls.RARE.value: (0, 112, 255),
            cls.EPIC.value: (163, 53, 238),
            cls.LEGENDARY.value: (255, 128, 0),
            cls.ARTIFACT.value: (230, 204, 128),
        }

    @classmethod
    def get_hex_colors(cls) -> Dict[str, str]:
        """HEX цвета для UI"""
        return {
            cls.POOR.value: "#808080",
            cls.COMMON.value: "#FFFFFF",
            cls.UNCOMMON.value: "#1EFF00",
            cls.RARE.value: "#0070FF",
            cls.EPIC.value: "#A335EE",
            cls.LEGENDARY.value: "#FF8000",
            cls.ARTIFACT.value: "#E6CC80",
        }

    @classmethod
    def get_stat_multiplier(cls) -> Dict[str, float]:
        """Множитель характеристик"""
        return {
            cls.POOR.value: 0.7,
            cls.COMMON.value: 1.0,
            cls.UNCOMMON.value: 1.2,
            cls.RARE.value: 1.5,
            cls.EPIC.value: 1.8,
            cls.LEGENDARY.value: 2.2,
            cls.ARTIFACT.value: 2.5,
        }

    @classmethod
    def get_price_multiplier(cls) -> Dict[str, float]:
        """Множитель цены"""
        return {
            cls.POOR.value: 0.5,
            cls.COMMON.value: 1.0,
            cls.UNCOMMON.value: 2.0,
            cls.RARE.value: 5.0,
            cls.EPIC.value: 15.0,
            cls.LEGENDARY.value: 50.0,
            cls.ARTIFACT.value: 200.0,
        }

    @classmethod
    def get_bonus_slots(cls) -> Dict[str, int]:
        """Количество дополнительных бонусов"""
        return {
            cls.POOR.value: 0,
            cls.COMMON.value: 0,
            cls.UNCOMMON.value: 1,
            cls.RARE.value: 2,
            cls.EPIC.value: 3,
            cls.LEGENDARY.value: 4,
            cls.ARTIFACT.value: 5,
        }


class ResourceCategory(Enum):
    """
    Категория ресурса
    """
    ORE = "ore"                 # Руда
    INGOT = "ingot"             # Слиток
    WOOD = "wood"               # Древесина
    LEATHER = "leather"         # Кожа
    CLOTH = "cloth"             # Ткань
    HERB = "herb"               # Трава
    GEM = "gem"                 # Драгоценный камень
    ESSENCE = "essence"         # Эссенция
    COMPONENT = "component"     # Компонент
    RARE_MATERIAL = "rare"      # Редкий материал

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.ORE.value: "Руда",
            cls.INGOT.value: "Слиток",
            cls.WOOD.value: "Древесина",
            cls.LEATHER.value: "Кожа",
            cls.CLOTH.value: "Ткань",
            cls.HERB.value: "Трава",
            cls.GEM.value: "Драгоценный камень",
            cls.ESSENCE.value: "Эссенция",
            cls.COMPONENT.value: "Компонент",
            cls.RARE_MATERIAL.value: "Редкий материал",
        }


class MaterialTier(Enum):
    """
    Уровень материала - определяет базовые характеристики
    """
    TIER_1 = 1      # Начальный (медь, берёза)
    TIER_2 = 2      # Базовый (железо, дуб)
    TIER_3 = 3      # Продвинутый (сталь, ясень)
    TIER_4 = 4      # Элитный (мифрил, чёрное дерево)
    TIER_5 = 5      # Легендарный (адамантий, мировое древо)

    @classmethod
    def get_display_names(cls) -> Dict[int, str]:
        return {
            1: "Начальный",
            2: "Базовый",
            3: "Продвинутый",
            4: "Элитный",
            5: "Легендарный",
        }

    @classmethod
    def get_stat_multiplier(cls) -> Dict[int, float]:
        """Множитель характеристик по уровню"""
        return {
            1: 1.0,
            2: 1.3,
            3: 1.7,
            4: 2.2,
            5: 3.0,
        }


class StatType(Enum):
    """
    Тип характеристики персонажа
    """
    STRENGTH = "strength"           # Сила
    DEXTERITY = "dexterity"         # Ловкость
    CONSTITUTION = "constitution"   # Телосложение
    INTELLIGENCE = "intelligence"   # Интеллект
    SPIRIT = "spirit"               # Дух
    LUCK = "luck"                   # Удача

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.STRENGTH.value: "Сила",
            cls.DEXTERITY.value: "Ловкость",
            cls.CONSTITUTION.value: "Телосложение",
            cls.INTELLIGENCE.value: "Интеллект",
            cls.SPIRIT.value: "Дух",
            cls.LUCK.value: "Удача",
        }

    @classmethod
    def get_short_names(cls) -> Dict[str, str]:
        return {
            cls.STRENGTH.value: "СИЛ",
            cls.DEXTERITY.value: "ЛОВ",
            cls.CONSTITUTION.value: "ТЕЛ",
            cls.INTELLIGENCE.value: "ИНТ",
            cls.SPIRIT.value: "ДУХ",
            cls.LUCK.value: "УДЧ",
        }


class DerivedStat(Enum):
    """
    Производные характеристики
    """
    MAX_HEALTH = "max_health"       # Максимальное здоровье
    MAX_MANA = "max_mana"           # Максимальная мана
    MAX_STAMINA = "max_stamina"     # Максимальная выносливость
    DAMAGE = "damage"               # Урон
    DEFENSE = "defense"             # Защита
    CRIT_CHANCE = "crit_chance"     # Шанс крита
    CRIT_DAMAGE = "crit_damage"     # Множитель крита
    DODGE_CHANCE = "dodge_chance"   # Шанс уклонения
    BLOCK_CHANCE = "block_chance"   # Шанс блока

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.MAX_HEALTH.value: "Здоровье",
            cls.MAX_MANA.value: "Мана",
            cls.MAX_STAMINA.value: "Выносливость",
            cls.DAMAGE.value: "Урон",
            cls.DEFENSE.value: "Защита",
            cls.CRIT_CHANCE.value: "Шанс крита",
            cls.CRIT_DAMAGE.value: "Урон крита",
            cls.DODGE_CHANCE.value: "Уклонение",
            cls.BLOCK_CHANCE.value: "Блок",
        }

    @classmethod
    def is_percent(cls, stat: "DerivedStat") -> bool:
        """Является ли характеристика процентной"""
        percent_stats = [
            cls.CRIT_CHANCE, cls.CRIT_DAMAGE,
            cls.DODGE_CHANCE, cls.BLOCK_CHANCE
        ]
        return stat in percent_stats


class CraftingStation(Enum):
    """
    Станция крафта
    """
    WORKBENCH = "workbench"             # Верстак
    FORGE = "forge"                     # Кузница
    SMELTER = "smelter"                 # Плавильня
    ALCHEMY_TABLE = "alchemy_table"     # Алхимический стол
    ENCHANTING_TABLE = "enchanting_table"  # Стол зачарования
    JEWELERS_BENCH = "jewelers_bench"   # Ювелирный верстак
    TANNING_RACK = "tanning_rack"       # Дубильный станок
    LOOM = "loom"                       # Ткацкий станок

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.WORKBENCH.value: "Верстак",
            cls.FORGE.value: "Кузница",
            cls.SMELTER.value: "Плавильня",
            cls.ALCHEMY_TABLE.value: "Алхимический стол",
            cls.ENCHANTING_TABLE.value: "Стол зачарования",
            cls.JEWELERS_BENCH.value: "Ювелирный верстак",
            cls.TANNING_RACK.value: "Дубильный станок",
            cls.LOOM.value: "Ткацкий станок",
        }


class CraftingSkill(Enum):
    """
    Навык крафта
    """
    SMITHING = "smithing"           # Кузнечное дело
    LEATHERWORKING = "leatherworking"  # Кожевничество
    TAILORING = "tailoring"         # Портняжное дело
    ALCHEMY = "alchemy"             # Алхимия
    ENCHANTING = "enchanting"       # Зачарование
    JEWELCRAFTING = "jewelcrafting" # Ювелирное дело

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.SMITHING.value: "Кузнечное дело",
            cls.LEATHERWORKING.value: "Кожевничество",
            cls.TAILORING.value: "Портняжное дело",
            cls.ALCHEMY.value: "Алхимия",
            cls.ENCHANTING.value: "Зачарование",
            cls.JEWELCRAFTING.value: "Ювелирное дело",
        }


class EffectType(Enum):
    """
    Тип эффекта (для зелий и бафов)
    """
    HEAL_INSTANT = "heal_instant"       # Мгновенное лечение
    HEAL_OVER_TIME = "heal_over_time"   # Лечение со временем
    MANA_INSTANT = "mana_instant"       # Мгновенное восстановление маны
    MANA_OVER_TIME = "mana_over_time"   # Восстановление маны со временем
    STAMINA_INSTANT = "stamina_instant" # Мгновенное восстановление выносливости
    BUFF_STAT = "buff_stat"             # Бафф характеристики
    BUFF_DAMAGE = "buff_damage"         # Бафф урона
    BUFF_DEFENSE = "buff_defense"       # Бафф защиты
    DEBUFF = "debuff"                   # Дебафф
    CLEANSE = "cleanse"                 # Очищение

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        return {
            cls.HEAL_INSTANT.value: "Мгновенное лечение",
            cls.HEAL_OVER_TIME.value: "Лечение со временем",
            cls.MANA_INSTANT.value: "Восстановление маны",
            cls.MANA_OVER_TIME.value: "Мана со временем",
            cls.STAMINA_INSTANT.value: "Восстановление выносливости",
            cls.BUFF_STAT.value: "Бафф характеристики",
            cls.BUFF_DAMAGE.value: "Бафф урона",
            cls.BUFF_DEFENSE.value: "Бафф защиты",
            cls.DEBUFF.value: "Дебафф",
            cls.CLEANSE.value: "Очищение",
        }
