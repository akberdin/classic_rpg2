"""
Константы и настройки игры
"""

# Базовое разрешение для дизайна UI (для масштабирования)
BASE_WIDTH = 1920
BASE_HEIGHT = 1200

# Фактические размеры окна (будут установлены при инициализации)
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1200
FPS = 60

# Размеры тайлов и карты
TILE_SIZE = 32
MAP_WIDTH = 200
MAP_HEIGHT = 200

# Радиус видимости игрока (для тумана войны)
VISION_RADIUS = 5

# Цвета для биомов (более естественная палитра)
COLORS = {
    # Биомы
    'water': (65, 105, 225),       # Вода - королевский синий
    'sand': (194, 178, 128),       # Песок - натуральный бежевый
    'plains': (107, 142, 35),      # Равнины - оливково-зеленый
    'hills': (160, 140, 100),      # Холмы - серо-коричневый
    'forest': (34, 100, 34),       # Леса - лесной зеленый

    # Объекты
    'city': (169, 169, 169),       # Города - темно-серый
    'village': (139, 115, 85),     # Деревни - коричневый
    'mine': (96, 96, 96),          # Шахты - темно-серый
    'bandit_camp': (178, 34, 34),  # Бандитские лагеря - огненно-красный
    'ruins': (128, 128, 128),      # Руины - серый камень
    'magic_school': (138, 43, 226), # Школа магов - фиолетовый

    # UI
    'player': (255, 215, 0),       # Игрок - золотой
    'fog': (40, 40, 45),           # Туман войны - темно-серый с синевой
    'background': (20, 20, 25),    # Фон - почти черный
    'text': (255, 255, 255),       # Текст - белый
}

# Типы биомов
BIOME_WATER = 'water'
BIOME_SAND = 'sand'
BIOME_PLAINS = 'plains'
BIOME_HILLS = 'hills'
BIOME_FOREST = 'forest'

# Типы объектов
LOCATION_CITY = 'city'
LOCATION_VILLAGE = 'village'
LOCATION_MINE = 'mine'
LOCATION_BANDIT_CAMP = 'bandit_camp'
LOCATION_RUINS = 'ruins'
LOCATION_MAGIC_SCHOOL = 'magic_school'

# Проходимость биомов
PASSABLE_BIOMES = [BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST]

# Система уровней и рангов
MAX_LEVEL = 40
RANKS = {
    (1, 10): "Новичок",
    (11, 20): "Обычный",
    (21, 30): "Опытный",
    (31, 40): "Эксперт"
}

# Система отношений
RELATIONSHIP_HOSTILE = "hostile"      # Враждебный
RELATIONSHIP_UNFRIENDLY = "unfriendly"  # Недружелюбный
RELATIONSHIP_NEUTRAL = "neutral"      # Нейтральный
RELATIONSHIP_FRIENDLY = "friendly"    # Дружелюбный
RELATIONSHIP_ALLIED = "allied"        # Союзный

# Типы NPC
NPC_TYPE_GUARD = "guard"
NPC_TYPE_MERCHANT = "merchant"
NPC_TYPE_BANDIT = "bandit"
NPC_TYPE_NEUTRAL = "neutral"
NPC_TYPE_MINER = "miner"
NPC_TYPE_UNDEAD = "undead"

# Матрица отношений между типами NPC
# Ключ - (тип1, тип2), значение - отношение типа1 к типу2
NPC_RELATIONSHIPS = {
    # Бандиты
    (NPC_TYPE_BANDIT, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_BANDIT): RELATIONSHIP_FRIENDLY,

    # Стражники
    (NPC_TYPE_GUARD, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,

    # Торговцы
    (NPC_TYPE_MERCHANT, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,

    # Нейтральные
    (NPC_TYPE_NEUTRAL, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,

    # Шахтеры
    (NPC_TYPE_MINER, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MINER, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,

    # Нежить
    (NPC_TYPE_UNDEAD, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_UNDEAD): RELATIONSHIP_FRIENDLY,

    # Обратные отношения к нежити
    (NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MERCHANT, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,

    # Обратные отношения к шахтерам
    (NPC_TYPE_BANDIT, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
}

# Параметры выносливости
STAMINA_PER_STAT_POINT = 10  # Каждая единица силы/телосложения дает 10 выносливости
STAMINA_COST_PER_MOVE = 2    # Стоимость перемещения
STAMINA_REST_MIN = 0.6       # Минимальный % для окончания отдыха (60%)
STAMINA_REST_MAX = 0.8       # Максимальный % для окончания отдыха (80%)

# Параметры боя
COMBAT_RANGE = 1  # Дальность атаки (в клетках)
BANDIT_CAMP_RADIUS = 40  # Радиус движения бандитов от лагеря

# Параметры уворота и крита
DODGE_BASE_CHANCE = 5  # Базовый шанс уворота при 1 ловкости (5%)
CRIT_BASE_CHANCE = 5   # Базовый шанс крита при 1 удаче (5%)

# Параметры AI для NPC
GUARD_DETECTION_RANGE = 10  # Дальность обнаружения врагов для стражников
GUARD_REST_DURATION_MIN = 3  # Минимальная длительность отдыха стражника (в часах)
GUARD_REST_DURATION_MAX = 3  # Максимальная длительность отдыха стражника (в часах)

MERCHANT_DETECTION_RANGE = 8  # Дальность обнаружения угроз для торговцев
MERCHANT_REST_DURATION_MIN = 5  # Минимальная длительность отдыха торговца (в часах)
MERCHANT_REST_DURATION_MAX = 8  # Максимальная длительность отдыха торговца (в часах)

BANDIT_DETECTION_RANGE = 10  # Дальность обнаружения врагов для бандитов
BANDIT_REST_DURATION_MIN = 2  # Минимальная длительность отдыха бандита (в часах)
BANDIT_REST_DURATION_MAX = 4  # Максимальная длительность отдыха бандита (в часах)

MINER_DETECTION_RANGE = 8  # Дальность обнаружения угроз для шахтеров
MINER_REST_DURATION_MIN = 3  # Минимальная длительность отдыха шахтера (в часах)
MINER_REST_DURATION_MAX = 5  # Максимальная длительность отдыха шахтера (в часах)
MINER_MAX_DISTANCE_FROM_MINE = 20  # Максимальная дистанция шахтера от шахты

UNDEAD_DETECTION_RANGE = 12  # Дальность обнаружения врагов для нежити
UNDEAD_REST_DURATION_MIN = 2  # Минимальная длительность отдыха нежити (в часах)
UNDEAD_REST_DURATION_MAX = 3  # Максимальная длительность отдыха нежити (в часах)
UNDEAD_MAX_DISTANCE_FROM_RUINS = 7  # Максимальная дистанция нежити от руин

# Действия игрока при взаимодействии с NPC
INTERACTION_TRADE = "trade"      # Торговля
INTERACTION_ATTACK = "attack"    # Агрессия
INTERACTION_LEAVE = "leave"      # Уйти

# Имена для локаций
CITY_NAMES = [
    "Златоград", "Каменск", "Серебряный Град", "Королевская Гавань",
    "Вольный Город", "Изумрудный Город", "Белокаменск", "Красноярск",
    "Северная Столица", "Южный Порт", "Восточный Форт", "Западный Град"
]

VILLAGE_NAMES = [
    "Зеленая Долина", "Тихий Ручей", "Ясная Поляна", "Светлый Берег",
    "Дубовая Роща", "Каменный Брод", "Солнечная Деревня", "Хлебное Поле",
    "Лесная Опушка", "Речная Заводь", "Старая Мельница", "Вишневый Сад",
    "Медовая Пасека", "Березовая Роща", "Тихая Гавань", "Золотые Нивы",
    "Рыбацкий Берег", "Горный Приют", "Сосновый Бор", "Кленовая Роща",
    "Цветочная Долина", "Утренняя Роса", "Ивовая Заводь", "Песчаный Берег",
    "Зеркальное Озеро", "Каменная Гряда", "Веселая Долина", "Тихая Пристань"
]

MAGIC_SCHOOL_NAMES = [
    "Академия Высшей Магии", "Школа Чародейства", "Башня Мудрецов"
]

MINE_NAMES = [
    "Медная Шахта", "Медный Рудник", "Великий Медный Рудник",
    "Железная Шахта", "Железный Рудник", "Глубокая Железная Шахта",
    "Серебряная Шахта", "Серебряная Жила", "Древняя Серебряная Шахта",
    "Золотая Шахта", "Золотой Прииск", "Богатая Золотая Жила",
    "Мифриловая Шахта", "Мифриловый Рудник", "Редкий Мифриловый Прииск",
    "Угольная Шахта", "Каменоломня", "Самоцветная Жила"
]

BANDIT_CAMP_NAMES = [
    "Логово Разбойников", "Лагерь Головорезов", "Стоянка Бандитов",
    "Волчье Логово", "Разбойничий Стан", "Черный Лагерь",
    "Темный Лес", "Медвежья Берлога", "Воронье Гнездо", "Лисья Нора",
    "Дубовый Стан", "Кровавая Поляна"
]

RUIN_NAMES = [
    "Древние Руины", "Забытый Храм", "Разрушенная Крепость",
    "Старое Святилище", "Проклятые Развалины", "Заброшенный Замок",
    "Руины Старого Города", "Разваленная Башня", "Древнее Капище",
    "Забытая Обсерватория", "Разрушенный Монастырь", "Старая Цитадель",
    "Павшая Твердыня", "Мертвый Город", "Призрачный Замок",
    "Разбитая Крепость", "Заброшенная Башня", "Темный Храм",
    "Проклятый Собор", "Руины Дворца", "Разваленная Крепость",
    "Гробница Королей", "Древний Некрополь", "Темные Катакомбы"
]
