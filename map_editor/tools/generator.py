"""Map generator for procedural terrain creation."""

import random
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

from ..utils.helpers import (
    PerlinNoise, normalize_map, get_neighbors, distance
)


# Biome constants
BIOME_WATER = "water"
BIOME_SAND = "sand"
BIOME_PLAINS = "plains"
BIOME_FOREST = "forest"
BIOME_HILLS = "hills"
BIOME_MOUNTAIN = "mountain"
BIOME_SWAMP = "swamp"

# Location constants
LOCATION_CITY = "city"
LOCATION_VILLAGE = "village"
LOCATION_MINE = "mine"
LOCATION_BANDIT_CAMP = "bandit_camp"
LOCATION_RUINS = "ruins"
LOCATION_MAGIC_SCHOOL = "magic_school"
LOCATION_WARRIOR_ACADEMY = "warrior_academy"
LOCATION_SECRET_CAMP = "secret_camp"

PASSABLE_BIOMES = [BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST, BIOME_MOUNTAIN, BIOME_SWAMP]


@dataclass
class GeneratorParams:
    """Parameters for map generation."""
    width: int = 200
    height: int = 200
    seed: Optional[int] = None

    # Noise parameters
    elevation_scale: float = 150.0
    elevation_octaves: int = 3
    moisture_scale: float = 120.0
    moisture_octaves: int = 2

    # Biome thresholds
    water_level: float = 0.30
    beach_level: float = 0.35
    plains_level: float = 0.50
    hills_level: float = 0.60
    mountain_level: float = 0.75
    forest_moisture: float = 0.55
    swamp_moisture: float = 0.70

    # Options
    temperature_gradient: bool = True
    smooth_iterations: int = 2
    generate_beaches: bool = True
    generate_rivers: bool = True
    river_count: int = 5

    # Location counts
    city_count: int = 5
    village_count: int = 15
    mine_count: int = 8
    bandit_camp_count: int = 8
    ruins_count: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'elevation_scale': self.elevation_scale,
            'elevation_octaves': self.elevation_octaves,
            'moisture_scale': self.moisture_scale,
            'moisture_octaves': self.moisture_octaves,
            'water_level': self.water_level,
            'beach_level': self.beach_level,
            'plains_level': self.plains_level,
            'hills_level': self.hills_level,
            'mountain_level': self.mountain_level,
            'forest_moisture': self.forest_moisture,
            'swamp_moisture': self.swamp_moisture,
            'temperature_gradient': self.temperature_gradient,
            'smooth_iterations': self.smooth_iterations,
            'generate_beaches': self.generate_beaches,
            'generate_rivers': self.generate_rivers,
            'river_count': self.river_count,
            'city_count': self.city_count,
            'village_count': self.village_count,
            'mine_count': self.mine_count,
            'bandit_camp_count': self.bandit_camp_count,
            'ruins_count': self.ruins_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratorParams':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MapLocation:
    """Represents a location on the map."""
    x: int
    y: int
    location_type: str
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'x': self.x,
            'y': self.y,
            'type': self.location_type,
            'name': self.name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapLocation':
        """Create from dictionary."""
        return cls(
            x=data['x'],
            y=data['y'],
            location_type=data['type'],
            name=data.get('name', '')
        )


@dataclass
class GeneratedMap:
    """Container for generated map data."""
    width: int
    height: int
    seed: int
    biomes: List[List[str]]
    elevation: List[List[float]]
    moisture: List[List[float]]
    locations: List[MapLocation] = field(default_factory=list)
    starting_village: Optional[MapLocation] = None

    def get_biome(self, x: int, y: int) -> str:
        """Get biome at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.biomes[y][x]
        return BIOME_WATER

    def set_biome(self, x: int, y: int, biome: str) -> None:
        """Set biome at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.biomes[y][x] = biome

    def is_passable(self, x: int, y: int) -> bool:
        """Check if tile is passable."""
        return self.get_biome(x, y) in PASSABLE_BIOMES

    def get_location_at(self, x: int, y: int) -> Optional[MapLocation]:
        """Get location at coordinates if any."""
        for loc in self.locations:
            if loc.x == x and loc.y == y:
                return loc
        return None

    def add_location(self, location: MapLocation) -> None:
        """Add a location to the map."""
        self.locations.append(location)

    def remove_location(self, x: int, y: int) -> bool:
        """Remove location at coordinates."""
        for i, loc in enumerate(self.locations):
            if loc.x == x and loc.y == y:
                if self.starting_village and loc == self.starting_village:
                    self.starting_village = None
                self.locations.pop(i)
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        data = {
            'version': '1.0',
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'biomes': self.biomes,
            'locations': [loc.to_dict() for loc in self.locations]
        }
        if self.starting_village:
            data['starting_village'] = {
                'x': self.starting_village.x,
                'y': self.starting_village.y,
                'name': self.starting_village.name
            }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratedMap':
        """Create from dictionary."""
        width = data['width']
        height = data['height']
        seed = data.get('seed', 0)
        biomes = data['biomes']

        # Create empty elevation/moisture maps
        elevation = [[0.5 for _ in range(width)] for _ in range(height)]
        moisture = [[0.5 for _ in range(width)] for _ in range(height)]

        locations = [MapLocation.from_dict(loc) for loc in data.get('locations', [])]

        # Find starting village in locations list (by coordinates)
        starting_village = None
        if 'starting_village' in data:
            sv_data = data['starting_village']
            sv_x, sv_y = sv_data['x'], sv_data['y']
            sv_name = sv_data.get('name', 'Тихая')

            # Find matching location in list
            for loc in locations:
                if loc.x == sv_x and loc.y == sv_y:
                    starting_village = loc
                    if not loc.name:
                        loc.name = sv_name
                    break

            # If not found in locations, create new and add
            if starting_village is None:
                starting_village = MapLocation(
                    x=sv_x,
                    y=sv_y,
                    location_type=LOCATION_VILLAGE,
                    name=sv_name
                )
                locations.append(starting_village)

        return cls(
            width=width,
            height=height,
            seed=seed,
            biomes=biomes,
            elevation=elevation,
            moisture=moisture,
            locations=locations,
            starting_village=starting_village
        )


class MapGenerator:
    """Procedural map generator using Perlin noise."""

    # Location names
    CITY_NAMES = [
        "Кристальград", "Златоград", "Серебряный Пик", "Королевская Гавань",
        "Драконий Утёс", "Орлиное Гнездо", "Железный Форт", "Солнечный Берег",
        "Лунная Крепость", "Звёздная Твердыня", "Каменный Страж", "Древний Оплот"
    ]

    VILLAGE_NAMES = [
        "Тихая", "Дубравка", "Речная", "Лесная", "Полянка", "Холмовка",
        "Берёзовка", "Ивовка", "Сосновка", "Ельники", "Озёрная", "Луговая",
        "Пригорье", "Заречье", "Подгорная", "Светлая", "Росная", "Туманная",
        "Привольная", "Раздольная", "Ключевая", "Родниковая", "Медовая",
        "Яблоневка", "Вишнёвка", "Грибная", "Охотничья", "Рыбацкая"
    ]

    MINE_NAMES = [
        "Железная жила", "Медный рудник", "Серебряная шахта", "Золотые копи",
        "Угольный разрез", "Изумрудная штольня", "Рубиновая пещера",
        "Сапфировый грот", "Алмазные недра", "Мифриловая жила",
        "Адамантитовая шахта", "Обсидиановая пещера", "Кварцевые залежи",
        "Аметистовый грот", "Малахитовая шахта", "Ониксовые копи",
        "Топазовая жила", "Опаловый рудник"
    ]

    BANDIT_CAMP_NAMES = [
        "Волчье логово", "Разбойничий схрон", "Воровская нора",
        "Лагерь Кровавого Клыка", "Притон Чёрных Масок", "Убежище Теней",
        "Стоянка Головорезов", "Лежбище Мародёров", "Приют Изгоев",
        "Гнездо Ворон", "Логово Гадюк", "Берлога Медведей"
    ]

    RUINS_NAMES = [
        "Забытый храм", "Древние развалины", "Руины замка", "Проклятые катакомбы",
        "Заброшенный монастырь", "Разрушенная башня", "Павший бастион",
        "Мёртвый город", "Потерянное святилище", "Гробница древних",
        "Склеп королей", "Подземелье ужаса", "Лабиринт теней",
        "Обитель проклятых", "Чертоги забвения", "Пещера страха",
        "Колодец душ", "Врата бездны", "Алтарь тьмы", "Престол скорби",
        "Цитадель падших", "Оплот нежити", "Некрополь", "Усыпальница"
    ]

    MAGIC_SCHOOL_NAMES = ["Академия Магии", "Башня Волшебников", "Школа Чародейства"]
    WARRIOR_ACADEMY_NAMES = ["Академия Воинов", "Школа Боевых Искусств", "Арена Героев"]
    SECRET_CAMP_NAMES = ["Тайное убежище", "Скрытый лагерь", "Логово отшельника",
                        "Затерянный приют", "Укрытие мудреца", "Тайная поляна"]

    def __init__(self, params: GeneratorParams = None):
        self.params = params or GeneratorParams()
        self._used_names: Dict[str, set] = {
            LOCATION_CITY: set(),
            LOCATION_VILLAGE: set(),
            LOCATION_MINE: set(),
            LOCATION_BANDIT_CAMP: set(),
            LOCATION_RUINS: set(),
            LOCATION_MAGIC_SCHOOL: set(),
            LOCATION_WARRIOR_ACADEMY: set(),
            LOCATION_SECRET_CAMP: set()
        }

    def generate(self, params: GeneratorParams = None) -> GeneratedMap:
        """Generate a new map with given parameters."""
        if params:
            self.params = params

        # Initialize seed
        if self.params.seed is None:
            self.params.seed = random.randint(0, 2**31)

        random.seed(self.params.seed)

        # Reset used names
        for key in self._used_names:
            self._used_names[key].clear()

        # Generate noise maps with different seeds for variation
        elevation = self._generate_noise(
            self.params.elevation_scale,
            self.params.elevation_octaves,
            seed_offset=0
        )
        moisture = self._generate_noise(
            self.params.moisture_scale,
            self.params.moisture_octaves,
            seed_offset=10000  # Different seed for moisture map
        )

        # Normalize maps
        elevation = normalize_map(elevation)
        moisture = normalize_map(moisture)

        # Generate biomes
        biomes = self._generate_biomes(elevation, moisture)

        # Smooth biomes
        for _ in range(self.params.smooth_iterations):
            biomes = self._smooth_biomes(biomes)

        # Generate beaches
        if self.params.generate_beaches:
            biomes = self._generate_beaches(biomes)

        # Generate rivers
        if self.params.generate_rivers:
            biomes = self._generate_rivers(biomes, elevation)

        # Create map object
        generated_map = GeneratedMap(
            width=self.params.width,
            height=self.params.height,
            seed=self.params.seed,
            biomes=biomes,
            elevation=elevation,
            moisture=moisture
        )

        # Place locations
        self._place_locations(generated_map)

        return generated_map

    def _generate_noise(self, scale: float, octaves: int, seed_offset: int = 0) -> List[List[float]]:
        """Generate Perlin noise map with optional seed offset for variation."""
        noise_seed = self.params.seed + seed_offset if self.params.seed else seed_offset
        noise_gen = PerlinNoise(noise_seed)
        noise_map = []

        for y in range(self.params.height):
            row = []
            for x in range(self.params.width):
                nx = x / scale
                ny = y / scale
                value = noise_gen.octave_noise(nx, ny, octaves)
                row.append(value)
            noise_map.append(row)

        return noise_map

    def _generate_biomes(self, elevation: List[List[float]],
                         moisture: List[List[float]]) -> List[List[str]]:
        """Generate biome map from elevation and moisture."""
        biomes = []

        for y in range(self.params.height):
            row = []
            for x in range(self.params.width):
                e = elevation[y][x]
                m = moisture[y][x]

                # Apply temperature gradient
                if self.params.temperature_gradient:
                    temp_factor = y / self.params.height
                    e = e * (0.8 + 0.4 * temp_factor)
                    e = min(1.0, max(0.0, e))

                biome = self._determine_biome(e, m)
                row.append(biome)
            biomes.append(row)

        return biomes

    def _determine_biome(self, elevation: float, moisture: float) -> str:
        """Determine biome based on elevation and moisture."""
        if elevation < self.params.water_level:
            return BIOME_WATER
        elif elevation < self.params.beach_level:
            return BIOME_SAND
        elif elevation > self.params.mountain_level:
            return BIOME_MOUNTAIN
        elif elevation > self.params.hills_level:
            return BIOME_HILLS
        elif moisture > self.params.swamp_moisture and elevation < self.params.plains_level:
            return BIOME_SWAMP
        elif moisture > self.params.forest_moisture:
            return BIOME_FOREST
        else:
            return BIOME_PLAINS

    def _smooth_biomes(self, biomes: List[List[str]]) -> List[List[str]]:
        """Smooth biomes using neighbor voting."""
        smoothed = [[biomes[y][x] for x in range(self.params.width)]
                   for y in range(self.params.height)]

        for y in range(self.params.height):
            for x in range(self.params.width):
                neighbors = get_neighbors(x, y, self.params.width, self.params.height)
                biome_counts: Dict[str, int] = {}

                for nx, ny in neighbors:
                    b = biomes[ny][nx]
                    biome_counts[b] = biome_counts.get(b, 0) + 1

                current = biomes[y][x]
                biome_counts[current] = biome_counts.get(current, 0) + 2

                most_common = max(biome_counts.keys(), key=lambda k: biome_counts[k])
                smoothed[y][x] = most_common

        return smoothed

    def _generate_beaches(self, biomes: List[List[str]]) -> List[List[str]]:
        """Generate sand beaches around water."""
        result = [[biomes[y][x] for x in range(self.params.width)]
                 for y in range(self.params.height)]

        for y in range(self.params.height):
            for x in range(self.params.width):
                if biomes[y][x] != BIOME_WATER:
                    neighbors = get_neighbors(x, y, self.params.width, self.params.height)
                    has_water = any(biomes[ny][nx] == BIOME_WATER for nx, ny in neighbors)
                    if has_water and biomes[y][x] != BIOME_MOUNTAIN:
                        result[y][x] = BIOME_SAND

        return result

    def _generate_rivers(self, biomes: List[List[str]],
                        elevation: List[List[float]]) -> List[List[str]]:
        """Generate rivers flowing from high to low elevation."""
        result = [[biomes[y][x] for x in range(self.params.width)]
                 for y in range(self.params.height)]

        # Find high points for river sources
        high_points = []
        for y in range(self.params.height):
            for x in range(self.params.width):
                if elevation[y][x] > self.params.hills_level and biomes[y][x] != BIOME_WATER:
                    high_points.append((x, y, elevation[y][x]))

        if not high_points:
            return result

        high_points.sort(key=lambda p: p[2], reverse=True)
        river_sources = high_points[:min(self.params.river_count * 3, len(high_points))]
        random.shuffle(river_sources)

        rivers_created = 0
        for sx, sy, _ in river_sources:
            if rivers_created >= self.params.river_count:
                break

            # Trace river path
            x, y = sx, sy
            path = [(x, y)]
            max_steps = self.params.width + self.params.height

            for _ in range(max_steps):
                if biomes[y][x] == BIOME_WATER:
                    break

                neighbors = get_neighbors(x, y, self.params.width, self.params.height, False)
                if not neighbors:
                    break

                # Find lowest neighbor
                lowest = min(neighbors, key=lambda n: elevation[n[1]][n[0]])
                if elevation[lowest[1]][lowest[0]] >= elevation[y][x]:
                    break

                x, y = lowest
                if (x, y) in path:
                    break
                path.append((x, y))

            # Only create river if it reaches water or is long enough
            if len(path) > 10:
                for rx, ry in path:
                    if result[ry][rx] not in [BIOME_WATER, BIOME_MOUNTAIN]:
                        result[ry][rx] = BIOME_WATER
                rivers_created += 1

        return result

    def _place_locations(self, game_map: GeneratedMap) -> None:
        """Place locations on the map."""
        # Place cities
        self._place_location_type(
            game_map, LOCATION_CITY, self.params.city_count,
            valid_biomes=[BIOME_PLAINS, BIOME_SAND],
            min_distance=20
        )

        # Place villages
        self._place_location_type(
            game_map, LOCATION_VILLAGE, self.params.village_count,
            valid_biomes=[BIOME_PLAINS, BIOME_FOREST],
            min_distance=8
        )

        # Set starting village
        for loc in game_map.locations:
            if loc.location_type == LOCATION_VILLAGE and loc.name == "Тихая":
                game_map.starting_village = loc
                break

        if not game_map.starting_village and game_map.locations:
            villages = [l for l in game_map.locations if l.location_type == LOCATION_VILLAGE]
            if villages:
                game_map.starting_village = villages[0]
                game_map.starting_village.name = "Тихая"

        # Place mines
        self._place_location_type(
            game_map, LOCATION_MINE, self.params.mine_count,
            valid_biomes=[BIOME_MOUNTAIN, BIOME_HILLS],
            min_distance=10
        )

        # Place bandit camps
        self._place_location_type(
            game_map, LOCATION_BANDIT_CAMP, self.params.bandit_camp_count,
            valid_biomes=[BIOME_FOREST],
            min_distance=15,
            min_distance_from_settlements=15
        )

        # Place ruins
        self._place_location_type(
            game_map, LOCATION_RUINS, self.params.ruins_count,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=12,
            min_distance_from_settlements=15
        )

        # Place special locations
        self._place_location_type(
            game_map, LOCATION_MAGIC_SCHOOL, 1,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=20
        )

        self._place_location_type(
            game_map, LOCATION_WARRIOR_ACADEMY, 1,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=20
        )

        self._place_location_type(
            game_map, LOCATION_SECRET_CAMP, 1,
            valid_biomes=[BIOME_FOREST],
            min_distance=25
        )

    def _place_location_type(self, game_map: GeneratedMap, location_type: str,
                            count: int, valid_biomes: List[str],
                            min_distance: int = 8,
                            min_distance_from_settlements: int = 0) -> None:
        """Place locations of a specific type."""
        placed = 0
        attempts = 0
        max_attempts = count * 100

        while placed < count and attempts < max_attempts:
            attempts += 1

            x = random.randint(5, game_map.width - 6)
            y = random.randint(5, game_map.height - 6)

            if game_map.get_biome(x, y) not in valid_biomes:
                continue

            if game_map.get_location_at(x, y):
                continue

            # Check distance from other locations
            too_close = False
            for loc in game_map.locations:
                d = distance(x, y, loc.x, loc.y)
                if d < min_distance:
                    too_close = True
                    break
                if min_distance_from_settlements > 0:
                    if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                        if d < min_distance_from_settlements:
                            too_close = True
                            break

            if too_close:
                continue

            # Generate name
            name = self._get_location_name(location_type)
            location = MapLocation(x, y, location_type, name)
            game_map.add_location(location)
            placed += 1

    def _get_location_name(self, location_type: str) -> str:
        """Get a unique name for a location type."""
        name_lists = {
            LOCATION_CITY: self.CITY_NAMES,
            LOCATION_VILLAGE: self.VILLAGE_NAMES,
            LOCATION_MINE: self.MINE_NAMES,
            LOCATION_BANDIT_CAMP: self.BANDIT_CAMP_NAMES,
            LOCATION_RUINS: self.RUINS_NAMES,
            LOCATION_MAGIC_SCHOOL: self.MAGIC_SCHOOL_NAMES,
            LOCATION_WARRIOR_ACADEMY: self.WARRIOR_ACADEMY_NAMES,
            LOCATION_SECRET_CAMP: self.SECRET_CAMP_NAMES
        }

        names = name_lists.get(location_type, ["Неизвестное место"])
        used = self._used_names.get(location_type, set())

        available = [n for n in names if n not in used]
        if not available:
            # Generate numbered name
            base = names[0] if names else "Место"
            i = 1
            while f"{base} {i}" in used:
                i += 1
            name = f"{base} {i}"
        else:
            name = random.choice(available)

        self._used_names[location_type].add(name)
        return name

    def regenerate_terrain_only(self, game_map: GeneratedMap,
                                params: GeneratorParams = None) -> GeneratedMap:
        """Regenerate only terrain, keeping locations."""
        if params:
            self.params = params

        if self.params.seed is None:
            self.params.seed = random.randint(0, 2**31)

        random.seed(self.params.seed)

        # Generate new terrain with different seeds for variation
        elevation = self._generate_noise(
            self.params.elevation_scale,
            self.params.elevation_octaves,
            seed_offset=0
        )
        moisture = self._generate_noise(
            self.params.moisture_scale,
            self.params.moisture_octaves,
            seed_offset=10000
        )

        elevation = normalize_map(elevation)
        moisture = normalize_map(moisture)

        biomes = self._generate_biomes(elevation, moisture)

        for _ in range(self.params.smooth_iterations):
            biomes = self._smooth_biomes(biomes)

        if self.params.generate_beaches:
            biomes = self._generate_beaches(biomes)

        if self.params.generate_rivers:
            biomes = self._generate_rivers(biomes, elevation)

        # Update map with new terrain
        game_map.biomes = biomes
        game_map.elevation = elevation
        game_map.moisture = moisture
        game_map.seed = self.params.seed

        return game_map
