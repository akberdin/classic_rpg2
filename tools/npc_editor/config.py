"""
Конфигурация и константы для NPC Editor
"""

# Типы NPC (id, название)
NPC_TYPES = [
    ("guard", "Стражник"),
    ("merchant", "Торговец"),
    ("bandit", "Бандит"),
    ("miner", "Шахтёр"),
    ("undead", "Нежить"),
    ("mage", "Маг"),
    ("alchemist", "Алхимик"),
    ("hunter", "Охотник"),
    ("necromancer", "Некромант"),
    ("shadow_adept", "Адепт Тени"),
    ("wolf", "Волк"),
    ("bear", "Медведь"),
    ("deer", "Олень"),
]

# Ранги NPC
RANKS = [1, 2, 3, 4, 5]

# Уровни качества предметов (id, название, цвет)
QUALITY_LEVELS = [
    ("poor", "Плохое", "#9d9d9d"),
    ("common", "Обычное", "#ffffff"),
    ("uncommon", "Необычное", "#1eff00"),
    ("rare", "Редкое", "#0070dd"),
    ("epic", "Эпическое", "#a335ee"),
    ("legendary", "Легендарное", "#ff8000"),
    ("artifact", "Артефакт", "#e6cc80"),
]

# Категории лута
LOOT_CATEGORIES = [
    ("weapon", "Оружие", "⚔"),
    ("armor", "Броня", "🛡"),
    ("jewelry", "Украшения", "💎"),
    ("potion", "Зелья", "🧪"),
    ("material", "Материалы", "📦"),
]

# Характеристики
STATS = [
    ("strength", "Сила", "STR"),
    ("dexterity", "Ловкость", "DEX"),
    ("constitution", "Телосложение", "CON"),
    ("spirit", "Дух", "SPI"),
    ("intelligence", "Интеллект", "INT"),
    ("luck", "Удача", "LCK"),
]

# Папки спрайтов для типов NPC
SPRITE_FOLDERS = {
    "guard": "soldier",
    "merchant": "trader",
    "bandit": "bandits",
    "miner": "miners",
    "undead": "skeletons",
    "mage": "mage",
    "alchemist": "alchemist",
    "hunter": "hunter",
    "necromancer": "necro",
    "shadow_adept": "mage",
    "wolf": "wolf",
    "bear": "bear",
    "deer": "deer",
}

# Отношения к игроку
RELATIONSHIPS = [
    ("hostile", "Враждебный", "#ff4444"),
    ("unfriendly", "Недружелюбный", "#ff8844"),
    ("neutral", "Нейтральный", "#ffff44"),
    ("friendly", "Дружелюбный", "#88ff44"),
    ("allied", "Союзный", "#44ff44"),
]

# Умения (id, название, категория, описание)
SKILLS = [
    # Ближний бой
    ("basic_attack", "Базовая атака", "combat", "Стандартная атака оружием"),
    ("power_strike", "Мощный удар", "combat", "Усиленный удар с повышенным уроном"),
    ("poison_strike", "Отравленный удар", "combat", "Удар с отравлением цели"),
    ("stun_strike", "Оглушающий удар", "combat", "Удар с шансом оглушения"),
    ("battle_cry", "Боевой клич", "combat", "Повышает боевой дух союзников"),
    # Магия
    ("fireball", "Огненный шар", "magic", "Огненная атака по области"),
    ("ice_bolt", "Ледяная стрела", "magic", "Замедляющая ледяная атака"),
    ("lightning", "Молния", "magic", "Быстрая атака молнией"),
    ("magic_missile", "Магическая стрела", "magic", "Точная магическая атака"),
    ("heal", "Исцеление", "magic", "Восстанавливает здоровье"),
    ("regeneration", "Регенерация", "magic", "Постепенное восстановление"),
    ("mage_shield", "Щит мага", "magic", "Магический барьер"),
    # Дальний бой
    ("basic_shot", "Выстрел", "ranged", "Стандартный выстрел из лука"),
    ("precise_shot", "Точный выстрел", "ranged", "Прицельный выстрел"),
    ("rapid_fire", "Быстрая стрельба", "ranged", "Серия быстрых выстрелов"),
    ("piercing_arrow", "Пронзающая стрела", "ranged", "Стрела, пробивающая броню"),
    # Скрытность
    ("backstab", "Удар в спину", "stealth", "Критический урон со спины"),
    ("bleeding_cut", "Кровоточащий порез", "stealth", "Наносит кровотечение"),
    ("shadow_step", "Шаг тени", "stealth", "Мгновенное перемещение"),
    # Оружейные приёмы
    ("whirlwind_strike", "Вихревой удар", "weapon", "Атака по всем врагам вокруг"),
    ("shield_breaker", "Разрушитель щита", "weapon", "Игнорирует часть защиты"),
    ("blade_dance", "Танец клинка", "weapon", "Серия быстрых ударов"),
]

# Категории умений
SKILL_CATEGORIES = {
    'combat': 'Ближний бой',
    'magic': 'Магия',
    'ranged': 'Дальний бой',
    'stealth': 'Скрытность',
    'weapon': 'Оружейные приёмы',
}

# Слоты экипировки
EQUIPMENT_SLOTS = [
    ("weapon", "Оружие"),
    ("offhand", "Левая рука"),
    ("head", "Голова"),
    ("body", "Тело"),
    ("hands", "Руки"),
    ("feet", "Ноги"),
    ("amulet", "Амулет"),
    ("ring", "Кольцо"),
]

# Типы брони
ARMOR_TYPES = [
    ("light", "Лёгкая"),
    ("medium", "Средняя"),
    ("heavy", "Тяжёлая"),
]

# Пресеты экипировки по типам NPC
EQUIPMENT_PRESETS = {
    "guard": {
        "weapon": {"enabled": True, "quality": "common", "type": "sword"},
        "offhand": {"enabled": True, "quality": "common", "type": "shield"},
        "body": {"enabled": True, "quality": "common", "armor_type": "heavy"},
    },
    "bandit": {
        "weapon": {"enabled": True, "quality": "poor", "type": "dagger"},
        "body": {"enabled": True, "quality": "poor", "armor_type": "light"},
    },
    "mage": {
        "weapon": {"enabled": True, "quality": "uncommon", "type": "staff"},
        "body": {"enabled": True, "quality": "common", "armor_type": "light"},
        "amulet": {"enabled": True, "quality": "uncommon"},
    },
    "hunter": {
        "weapon": {"enabled": True, "quality": "common", "type": "bow"},
        "body": {"enabled": True, "quality": "common", "armor_type": "medium"},
    },
    "merchant": {
        "body": {"enabled": True, "quality": "common", "armor_type": "light"},
    },
    "miner": {
        "weapon": {"enabled": True, "quality": "poor", "type": "pickaxe"},
        "body": {"enabled": True, "quality": "poor", "armor_type": "light"},
    },
    "undead": {
        "weapon": {"enabled": True, "quality": "poor", "type": "sword"},
        "body": {"enabled": True, "quality": "poor", "armor_type": "medium"},
    },
    "necromancer": {
        "weapon": {"enabled": True, "quality": "rare", "type": "staff"},
        "body": {"enabled": True, "quality": "uncommon", "armor_type": "light"},
        "amulet": {"enabled": True, "quality": "rare"},
    },
    "alchemist": {
        "body": {"enabled": True, "quality": "common", "armor_type": "light"},
        "ring": {"enabled": True, "quality": "uncommon"},
    },
    "shadow_adept": {
        "weapon": {"enabled": True, "quality": "rare", "type": "dagger"},
        "body": {"enabled": True, "quality": "uncommon", "armor_type": "light"},
    },
}

# Пресеты лута по типам NPC
LOOT_PRESETS = {
    "guard": {
        "gold": {"chance": 70, "base": 15, "level_mult": 2.0, "variance": 20},
        "categories": {
            "weapon": {"enabled": True, "base_chance": 15},
            "armor": {"enabled": True, "base_chance": 20},
            "potion": {"enabled": True, "base_chance": 10},
        },
    },
    "bandit": {
        "gold": {"chance": 90, "base": 20, "level_mult": 2.5, "variance": 30},
        "categories": {
            "weapon": {"enabled": True, "base_chance": 25},
            "jewelry": {"enabled": True, "base_chance": 10},
            "potion": {"enabled": True, "base_chance": 15},
        },
    },
    "mage": {
        "gold": {"chance": 60, "base": 25, "level_mult": 3.0, "variance": 25},
        "categories": {
            "weapon": {"enabled": True, "base_chance": 10},
            "jewelry": {"enabled": True, "base_chance": 25},
            "potion": {"enabled": True, "base_chance": 30},
            "material": {"enabled": True, "base_chance": 20},
        },
    },
    "merchant": {
        "gold": {"chance": 95, "base": 50, "level_mult": 5.0, "variance": 40},
        "categories": {
            "weapon": {"enabled": True, "base_chance": 10},
            "armor": {"enabled": True, "base_chance": 10},
            "jewelry": {"enabled": True, "base_chance": 15},
            "potion": {"enabled": True, "base_chance": 20},
            "material": {"enabled": True, "base_chance": 25},
        },
    },
    "undead": {
        "gold": {"chance": 30, "base": 5, "level_mult": 1.0, "variance": 50},
        "categories": {
            "weapon": {"enabled": True, "base_chance": 20},
            "armor": {"enabled": True, "base_chance": 15},
            "material": {"enabled": True, "base_chance": 25},
        },
    },
    "wolf": {
        "gold": {"chance": 0, "base": 0, "level_mult": 0, "variance": 0},
        "categories": {
            "material": {"enabled": True, "base_chance": 80},
        },
    },
    "bear": {
        "gold": {"chance": 0, "base": 0, "level_mult": 0, "variance": 0},
        "categories": {
            "material": {"enabled": True, "base_chance": 90},
        },
    },
    "deer": {
        "gold": {"chance": 0, "base": 0, "level_mult": 0, "variance": 0},
        "categories": {
            "material": {"enabled": True, "base_chance": 95},
        },
    },
}

# Пресеты умений по типам NPC
SKILLS_PRESETS = {
    "guard": ["basic_attack", "power_strike", "shield_breaker"],
    "bandit": ["basic_attack", "backstab", "bleeding_cut"],
    "mage": ["magic_missile", "fireball", "mage_shield"],
    "hunter": ["basic_shot", "precise_shot", "piercing_arrow"],
    "undead": ["basic_attack", "poison_strike"],
    "necromancer": ["magic_missile", "ice_bolt", "regeneration"],
    "wolf": ["basic_attack"],
    "bear": ["basic_attack", "power_strike"],
    "deer": [],
    "merchant": [],
    "miner": ["basic_attack"],
    "alchemist": ["heal", "regeneration"],
    "shadow_adept": ["shadow_step", "backstab", "bleeding_cut", "magic_missile"],
}

# Пресеты статов по типам NPC (в процентах, сумма = 100)
STATS_PRESETS = {
    "guard": {"strength": 25, "dexterity": 15, "constitution": 25, "spirit": 10, "intelligence": 10, "luck": 15},
    "bandit": {"strength": 20, "dexterity": 25, "constitution": 15, "spirit": 10, "intelligence": 15, "luck": 15},
    "mage": {"strength": 5, "dexterity": 10, "constitution": 10, "spirit": 25, "intelligence": 40, "luck": 10},
    "hunter": {"strength": 15, "dexterity": 30, "constitution": 15, "spirit": 10, "intelligence": 15, "luck": 15},
    "merchant": {"strength": 10, "dexterity": 10, "constitution": 15, "spirit": 15, "intelligence": 30, "luck": 20},
    "miner": {"strength": 30, "dexterity": 15, "constitution": 25, "spirit": 10, "intelligence": 10, "luck": 10},
    "undead": {"strength": 20, "dexterity": 15, "constitution": 30, "spirit": 5, "intelligence": 5, "luck": 25},
    "necromancer": {"strength": 5, "dexterity": 10, "constitution": 15, "spirit": 30, "intelligence": 35, "luck": 5},
    "alchemist": {"strength": 10, "dexterity": 15, "constitution": 15, "spirit": 20, "intelligence": 30, "luck": 10},
    "shadow_adept": {"strength": 10, "dexterity": 25, "constitution": 10, "spirit": 20, "intelligence": 25, "luck": 10},
    "wolf": {"strength": 25, "dexterity": 30, "constitution": 20, "spirit": 5, "intelligence": 5, "luck": 15},
    "bear": {"strength": 35, "dexterity": 15, "constitution": 35, "spirit": 5, "intelligence": 5, "luck": 5},
    "deer": {"strength": 10, "dexterity": 40, "constitution": 20, "spirit": 10, "intelligence": 10, "luck": 10},
}

# Качества по умолчанию для разных рангов
QUALITY_BY_RANK = {
    1: ["poor", "common"],
    2: ["poor", "common", "uncommon"],
    3: ["common", "uncommon", "rare"],
    4: ["uncommon", "rare", "epic"],
    5: ["rare", "epic", "legendary"],
}
