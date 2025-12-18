"""
Класс карты игры для загрузки и работы с готовыми картами

Карта загружается из JSON файла (по умолчанию map1.json).
Генерация карт больше не поддерживается - используйте map_editor для создания карт.
"""
import json
import os
from game.tile import Tile, Location
from game.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    LOCATION_CITY, LOCATION_VILLAGE
)


class GameMap:
    """Класс игровой карты"""

    # Путь к файлу карты по умолчанию
    DEFAULT_MAP_FILE = os.path.join(os.path.dirname(__file__), 'config', 'map1.json')

    def __init__(self, width=MAP_WIDTH, height=MAP_HEIGHT, map_file=None):
        """
        Инициализация карты

        Карта ВСЕГДА загружается из JSON файла. Генерация карт удалена.
        Используйте map_editor для создания новых карт.

        Args:
            width: Ширина карты (игнорируется при загрузке из файла)
            height: Высота карты (игнорируется при загрузке из файла)
            map_file: Путь к файлу карты (по умолчанию map1.json)
        """
        # Определяем путь к файлу карты
        filepath = map_file if map_file else self.DEFAULT_MAP_FILE

        # Проверяем существование файла
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Файл карты не найден: {filepath}\n"
                f"Используйте map_editor для создания карты или убедитесь, что файл map1.json существует в папке game/config/"
            )

        # Загружаем карту из файла
        self._load_from_file(filepath)

    def _load_from_file(self, filepath: str):
        """
        Загрузить карту из JSON файла (внутренний метод)

        Args:
            filepath: Путь к файлу
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.width = data["width"]
        self.height = data["height"]
        self.seed = data.get("seed", 0)
        self.tiles = []
        self.locations = []
        self.starting_village = None

        # Восстанавливаем биомы
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = Tile(x, y)
                tile.biome = data["biomes"][y][x]
                row.append(tile)
            self.tiles.append(row)

        # Восстанавливаем локации
        for loc_data in data["locations"]:
            location = Location(
                loc_data["x"],
                loc_data["y"],
                loc_data["type"],
                loc_data["name"]
            )
            self.locations.append(location)
            self.tiles[loc_data["y"]][loc_data["x"]].set_location(location)

        # Восстанавливаем стартовую деревню
        if data.get("starting_village"):
            sv = data["starting_village"]
            for loc in self.locations:
                if loc.x == sv["x"] and loc.y == sv["y"]:
                    self.starting_village = loc
                    break

        print(f"Карта загружена из {filepath}")

    def get_tile(self, x, y):
        """
        Получить тайл по координатам

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            Tile или None
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_valid_position(self, x, y):
        """
        Проверить, находятся ли координаты в пределах карты

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если координаты валидны
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def find_spawn_point(self):
        """
        Найти подходящую точку спавна игрока в стартовой деревне "Тихая"

        Returns:
            tuple: (x, y) координаты точки спавна
        """
        # Приоритет - стартовая деревня "Тихая"
        if self.starting_village is not None:
            settlement = self.starting_village
        else:
            # Запасной вариант - ищем все города и деревни
            settlements = [loc for loc in self.locations
                          if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]]

            if not settlements:
                # Если нет поселений, спавним в центре карты
                center_x = self.width // 2
                center_y = self.height // 2
                return (center_x, center_y)

            # Выбираем первое поселение
            settlement = settlements[0]

        # Ищем проходимое место рядом с поселением (в радиусе 3-7 клеток)
        search_radius = 7
        for radius in range(3, search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = settlement.x + dx
                    y = settlement.y + dy

                    if self.is_valid_position(x, y):
                        tile = self.get_tile(x, y)
                        if tile.is_passable() and not tile.has_location():
                            return (x, y)

        # Если не нашли рядом с поселением, возвращаем координаты поселения
        return (settlement.x, settlement.y)

    # =========================================================================
    # СОХРАНЕНИЕ И ЗАГРУЗКА КАРТЫ
    # =========================================================================

    def save_to_json(self, filepath: str):
        """
        Сохранить карту в JSON файл

        Args:
            filepath: Путь к файлу для сохранения
        """
        data = {
            "version": "1.0",
            "width": self.width,
            "height": self.height,
            "seed": getattr(self, 'seed', 0),
            "biomes": [],
            "locations": [],
            "starting_village": None
        }

        # Сохраняем биомы (компактно - как 2D массив строк)
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(self.tiles[y][x].biome)
            data["biomes"].append(row)

        # Сохраняем локации
        for loc in self.locations:
            loc_data = {
                "x": loc.x,
                "y": loc.y,
                "type": loc.location_type,
                "name": loc.name
            }
            data["locations"].append(loc_data)

            # Отмечаем стартовую деревню
            if self.starting_village and loc.x == self.starting_village.x and loc.y == self.starting_village.y:
                data["starting_village"] = {"x": loc.x, "y": loc.y, "name": loc.name}

        # Записываем в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Карта сохранена в {filepath}")

    @classmethod
    def load_from_json(cls, filepath: str) -> 'GameMap':
        """
        Загрузить карту из JSON файла

        Args:
            filepath: Путь к файлу карты

        Returns:
            GameMap: Загруженная карта
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Создаем пустую карту без генерации
        game_map = cls.__new__(cls)
        game_map.width = data["width"]
        game_map.height = data["height"]
        game_map.seed = data.get("seed", 0)
        game_map.tiles = []
        game_map.locations = []
        game_map.starting_village = None

        # Восстанавливаем биомы
        for y in range(game_map.height):
            row = []
            for x in range(game_map.width):
                tile = Tile(x, y)
                tile.biome = data["biomes"][y][x]
                row.append(tile)
            game_map.tiles.append(row)

        # Восстанавливаем локации
        for loc_data in data["locations"]:
            location = Location(
                loc_data["x"],
                loc_data["y"],
                loc_data["type"],
                loc_data["name"]
            )
            game_map.locations.append(location)
            game_map.tiles[loc_data["y"]][loc_data["x"]].set_location(location)

        # Восстанавливаем стартовую деревню
        if data.get("starting_village"):
            sv = data["starting_village"]
            for loc in game_map.locations:
                if loc.x == sv["x"] and loc.y == sv["y"]:
                    game_map.starting_village = loc
                    break

        print(f"Карта загружена из {filepath}")
        return game_map

    @staticmethod
    def get_default_map_path() -> str:
        """Получить путь к файлу карты по умолчанию"""
        return os.path.join(os.path.dirname(__file__), 'config', 'map1.json')
