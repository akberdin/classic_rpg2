"""
Константы и настройки игры
"""

# Размеры окна
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Размеры тайлов и карты
TILE_SIZE = 32
MAP_WIDTH = 100
MAP_HEIGHT = 100

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
}

# Параметры выносливости
STAMINA_PER_STAT_POINT = 10  # Каждая единица силы/телосложения дает 10 выносливости
STAMINA_COST_PER_MOVE = 2    # Стоимость перемещения
STAMINA_REST_MIN = 0.6       # Минимальный % для окончания отдыха (60%)
STAMINA_REST_MAX = 0.8       # Максимальный % для окончания отдыха (80%)

# Параметры боя
COMBAT_RANGE = 1  # Дальность атаки (в клетках)
BANDIT_CAMP_RADIUS = 40  # Радиус движения бандитов от лагеря

# Имена для локаций
CITY_NAMES = [
    "Златоград", "Каменск", "Серебряный Град", "Королевская Гавань",
    "Вольный Город", "Изумрудный Город"
]

VILLAGE_NAMES = [
    "Зеленая Долина", "Тихий Ручей", "Ясная Поляна", "Светлый Берег",
    "Дубовая Роща", "Каменный Брод", "Солнечная Деревня", "Хлебное Поле",
    "Лесная Опушка", "Речная Заводь", "Старая Мельница", "Вишневый Сад",
    "Медовая Пасека", "Березовая Роща"
]

MAGIC_SCHOOL_NAMES = [
    "Академия Высшей Магии", "Школа Чародейства", "Башня Мудрецов"
]

MINE_NAMES = [
    "Медная Шахта", "Медный Рудник",
    "Железная Шахта", "Железный Рудник",
    "Серебряная Шахта", "Серебряная Жила",
    "Золотая Шахта", "Золотой Прииск",
    "Мифриловая Шахта", "Мифриловый Рудник"
]

BANDIT_CAMP_NAMES = [
    "Логово Разбойников", "Лагерь Головорезов", "Стоянка Бандитов",
    "Волчье Логово", "Разбойничий Стан", "Черный Лагерь"
]

RUIN_NAMES = [
    "Древние Руины", "Забытый Храм", "Разрушенная Крепость",
    "Старое Святилище", "Проклятые Развалины", "Заброшенный Замок",
    "Руины Старого Города", "Разваленная Башня", "Древнее Капище",
    "Забытая Обсерватория", "Разрушенный Монастырь", "Старая Цитадель"
]
