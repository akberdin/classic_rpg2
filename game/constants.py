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

# Цвета для биомов (временные, до добавления спрайтов)
COLORS = {
    # Биомы
    'water': (30, 144, 255),      # Вода - синий
    'sand': (238, 214, 175),      # Песок - светло-коричневый
    'plains': (124, 252, 0),      # Равнины - светло-зеленый
    'hills': (139, 90, 43),       # Холмы - коричневый
    'forest': (34, 139, 34),      # Леса - темно-зеленый

    # Объекты
    'city': (128, 128, 128),      # Города - серый
    'village': (160, 82, 45),     # Деревни - коричневый
    'mine': (64, 64, 64),         # Шахты - темно-серый
    'bandit_camp': (139, 0, 0),   # Бандитские лагеря - темно-красный
    'ruins': (105, 105, 105),     # Руины - светло-серый

    # UI
    'player': (255, 215, 0),      # Игрок - золотой
    'fog': (50, 50, 50),          # Туман войны - темно-серый
    'background': (0, 0, 0),      # Фон - черный
    'text': (255, 255, 255),      # Текст - белый
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
