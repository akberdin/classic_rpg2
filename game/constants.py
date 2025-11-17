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

# Проходимость биомов
PASSABLE_BIOMES = [BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST]
