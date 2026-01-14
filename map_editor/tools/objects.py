"""Object placement tool for the map editor."""

import uuid
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .generator import (
    GeneratedMap, MapLocation, PASSABLE_BIOMES,
    LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE, LOCATION_MINE,
    LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL,
    LOCATION_WARRIOR_ACADEMY, LOCATION_SECRET_CAMP,
    LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER,
    BIOME_MOUNTAIN, BIOME_HILLS, BIOME_FOREST, BIOME_PLAINS, BIOME_SAND,
    BIOME_SWAMP
)
from ..utils.helpers import distance


class PlacementMode(Enum):
    """Object placement modes."""
    SINGLE = "single"
    MULTI = "multi"
    DELETE = "delete"
    MOVE = "move"
    EDIT = "edit"


@dataclass
class LocationTemplate:
    """Template for location placement."""
    location_type: str
    name: str = ""
    valid_biomes: List[str] = field(default_factory=list)
    min_distance_from_same: int = 8
    min_distance_from_settlements: int = 0
    required_nearby_biomes: List[str] = field(default_factory=list)
    required_nearby_distance: int = 5
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.valid_biomes:
            self.valid_biomes = list(PASSABLE_BIOMES)


# Default templates for each location type
LOCATION_TEMPLATES: Dict[str, LocationTemplate] = {
    LOCATION_CAPITAL: LocationTemplate(
        location_type=LOCATION_CAPITAL,
        valid_biomes=[BIOME_PLAINS, BIOME_SAND],
        min_distance_from_same=100  # Only one capital
    ),
    LOCATION_CITY: LocationTemplate(
        location_type=LOCATION_CITY,
        valid_biomes=[BIOME_PLAINS, BIOME_SAND],
        min_distance_from_same=20
    ),
    LOCATION_VILLAGE: LocationTemplate(
        location_type=LOCATION_VILLAGE,
        valid_biomes=[BIOME_PLAINS, BIOME_FOREST],
        min_distance_from_same=8
    ),
    LOCATION_MINE: LocationTemplate(
        location_type=LOCATION_MINE,
        valid_biomes=[BIOME_MOUNTAIN, BIOME_HILLS],
        min_distance_from_same=10
    ),
    LOCATION_BANDIT_CAMP: LocationTemplate(
        location_type=LOCATION_BANDIT_CAMP,
        valid_biomes=[BIOME_FOREST],
        min_distance_from_same=15,
        min_distance_from_settlements=15
    ),
    LOCATION_RUINS: LocationTemplate(
        location_type=LOCATION_RUINS,
        valid_biomes=list(PASSABLE_BIOMES),
        min_distance_from_same=12,
        min_distance_from_settlements=15
    ),
    LOCATION_MAGIC_SCHOOL: LocationTemplate(
        location_type=LOCATION_MAGIC_SCHOOL,
        valid_biomes=list(PASSABLE_BIOMES),
        min_distance_from_same=50
    ),
    LOCATION_WARRIOR_ACADEMY: LocationTemplate(
        location_type=LOCATION_WARRIOR_ACADEMY,
        valid_biomes=list(PASSABLE_BIOMES),
        min_distance_from_same=50
    ),
    LOCATION_SECRET_CAMP: LocationTemplate(
        location_type=LOCATION_SECRET_CAMP,
        valid_biomes=[BIOME_FOREST],
        min_distance_from_same=30,
        min_distance_from_settlements=20
    ),
    # Spawn points for beasts
    LOCATION_SPAWN_WOLF: LocationTemplate(
        location_type=LOCATION_SPAWN_WOLF,
        valid_biomes=[BIOME_FOREST, BIOME_HILLS],
        min_distance_from_same=15
    ),
    LOCATION_SPAWN_BEAR: LocationTemplate(
        location_type=LOCATION_SPAWN_BEAR,
        valid_biomes=[BIOME_FOREST, BIOME_MOUNTAIN],
        min_distance_from_same=20
    ),
    LOCATION_SPAWN_DEER: LocationTemplate(
        location_type=LOCATION_SPAWN_DEER,
        valid_biomes=[BIOME_FOREST, BIOME_PLAINS],
        min_distance_from_same=12
    )
}


# Default names for locations
DEFAULT_NAMES: Dict[str, List[str]] = {
    LOCATION_CAPITAL: [
        "Королевская столица", "Имперский престол", "Великий Трон"
    ],
    LOCATION_CITY: [
        "Кристальград", "Златоград", "Серебряный Пик", "Королевская Гавань",
        "Драконий Утёс", "Орлиное Гнездо", "Железный Форт", "Солнечный Берег"
    ],
    LOCATION_VILLAGE: [
        "Тихая", "Дубравка", "Речная", "Лесная", "Полянка", "Холмовка",
        "Берёзовка", "Ивовка", "Сосновка", "Ельники", "Озёрная", "Луговая"
    ],
    LOCATION_MINE: [
        "Железная жила", "Медный рудник", "Серебряная шахта", "Золотые копи",
        "Угольный разрез", "Изумрудная штольня", "Рубиновая пещера"
    ],
    LOCATION_BANDIT_CAMP: [
        "Волчье логово", "Разбойничий схрон", "Воровская нора",
        "Лагерь Кровавого Клыка", "Притон Чёрных Масок"
    ],
    LOCATION_RUINS: [
        "Забытый храм", "Древние развалины", "Руины замка",
        "Проклятые катакомбы", "Заброшенный монастырь"
    ],
    LOCATION_MAGIC_SCHOOL: ["Академия Магии", "Башня Волшебников"],
    LOCATION_WARRIOR_ACADEMY: ["Академия Воинов", "Школа Боевых Искусств"],
    LOCATION_SECRET_CAMP: ["Тайное убежище", "Скрытый лагерь"],
    # Spawn point names
    LOCATION_SPAWN_WOLF: ["Волчье логово"],
    LOCATION_SPAWN_BEAR: ["Медвежья берлога"],
    LOCATION_SPAWN_DEER: ["Оленья поляна"]
}


@dataclass
class PlacementResult:
    """Result of a placement attempt."""
    success: bool
    message: str = ""
    location: Optional[MapLocation] = None


class ObjectPlacer:
    """Tool for placing and managing objects on the map."""

    def __init__(self):
        self.mode = PlacementMode.SINGLE
        self.current_template: Optional[LocationTemplate] = None
        self.selected_location: Optional[MapLocation] = None
        self._used_names: Dict[str, set] = {lt: set() for lt in LOCATION_TEMPLATES}
        self._moving_location: Optional[MapLocation] = None

    def set_location_type(self, location_type: str) -> None:
        """Set current location type for placement."""
        if location_type in LOCATION_TEMPLATES:
            self.current_template = LocationTemplate(
                location_type=location_type,
                **{k: v for k, v in LOCATION_TEMPLATES[location_type].__dict__.items()
                   if k != 'location_type'}
            )

    def set_mode(self, mode: PlacementMode) -> None:
        """Set placement mode."""
        self.mode = mode
        if mode != PlacementMode.MOVE:
            self._moving_location = None

    def can_place_at(self, game_map: GeneratedMap, x: int, y: int,
                     template: LocationTemplate = None) -> Tuple[bool, str]:
        """Check if a location can be placed at coordinates."""
        template = template or self.current_template
        if not template:
            return False, "Тип локации не выбран"

        # Check bounds
        if not (0 <= x < game_map.width and 0 <= y < game_map.height):
            return False, "Координаты за пределами карты"

        # Check biome
        biome = game_map.get_biome(x, y)
        if biome not in template.valid_biomes:
            valid_names = ", ".join(template.valid_biomes)
            return False, f"Неподходящий биом. Требуется: {valid_names}"

        # Check if location already exists here
        existing = game_map.get_location_at(x, y)
        if existing and existing != self._moving_location:
            return False, "Здесь уже есть локация"

        # Check distance from same type
        for loc in game_map.locations:
            if loc == self._moving_location:
                continue
            if loc.location_type == template.location_type:
                d = distance(x, y, loc.x, loc.y)
                if d < template.min_distance_from_same:
                    return False, f"Слишком близко к другой {template.location_type} (мин. {template.min_distance_from_same})"

        # Check distance from settlements
        if template.min_distance_from_settlements > 0:
            for loc in game_map.locations:
                if loc == self._moving_location:
                    continue
                if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                    d = distance(x, y, loc.x, loc.y)
                    if d < template.min_distance_from_settlements:
                        return False, f"Слишком близко к поселению (мин. {template.min_distance_from_settlements})"

        # Check required nearby biomes
        if template.required_nearby_biomes:
            found = False
            for dy in range(-template.required_nearby_distance, template.required_nearby_distance + 1):
                for dx in range(-template.required_nearby_distance, template.required_nearby_distance + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                        if game_map.get_biome(nx, ny) in template.required_nearby_biomes:
                            found = True
                            break
                if found:
                    break
            if not found:
                return False, f"Требуется {template.required_nearby_biomes} поблизости"

        return True, "OK"

    def place_location(self, game_map: GeneratedMap, x: int, y: int,
                       name: str = None) -> PlacementResult:
        """Place a location at coordinates."""
        if self.mode == PlacementMode.DELETE:
            return self.delete_location(game_map, x, y)

        if self.mode == PlacementMode.MOVE:
            return self._handle_move(game_map, x, y)

        if not self.current_template:
            return PlacementResult(False, "Тип локации не выбран")

        can_place, message = self.can_place_at(game_map, x, y)
        if not can_place:
            return PlacementResult(False, message)

        # Generate name if not provided
        if not name:
            name = self._get_next_name(self.current_template.location_type)

        # Set default values for mines
        if self.current_template.location_type == LOCATION_MINE:
            location = MapLocation(
                x=x,
                y=y,
                location_type=self.current_template.location_type,
                name=name,
                id=str(uuid.uuid4()),
                rank=1,
                spawn_radius=3,
                miners_count=3,
                respawn_time=100
            )
        # Set default values for animal spawn points
        elif self.current_template.location_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            location = MapLocation(
                x=x,
                y=y,
                location_type=self.current_template.location_type,
                name=name,
                id=str(uuid.uuid4()),
                animal_count=3,
                respawn_time=50,
                spawn_radius=5
            )
        else:
            location = MapLocation(
                x=x,
                y=y,
                location_type=self.current_template.location_type,
                name=name,
                id=str(uuid.uuid4())
            )

        game_map.add_location(location)
        self._used_names[self.current_template.location_type].add(name)

        return PlacementResult(True, f"Размещено: {name}", location)

    def delete_location(self, game_map: GeneratedMap, x: int, y: int) -> PlacementResult:
        """Delete location at coordinates."""
        location = game_map.get_location_at(x, y)
        if not location:
            return PlacementResult(False, "Локация не найдена")

        # Check if it's the starting village
        if game_map.starting_village and location == game_map.starting_village:
            return PlacementResult(False, "Нельзя удалить стартовую деревню")

        name = location.name
        loc_type = location.location_type

        # Remove all connections pointing to this location before deleting it
        self._remove_connections_to_location(game_map, x, y)

        game_map.remove_location(x, y)

        if name in self._used_names.get(loc_type, set()):
            self._used_names[loc_type].discard(name)

        return PlacementResult(True, f"Удалено: {name}")

    def _remove_connections_to_location(self, game_map: GeneratedMap, x: int, y: int) -> None:
        """Remove all connections pointing to a specific location."""
        for location in game_map.locations:
            # Remove connections to the deleted location
            location.connections = [
                (target_x, target_y) for target_x, target_y in location.connections
                if not (target_x == x and target_y == y)
            ]

    def _handle_move(self, game_map: GeneratedMap, x: int, y: int) -> PlacementResult:
        """Handle move mode click."""
        if self._moving_location is None:
            # Select location to move
            location = game_map.get_location_at(x, y)
            if not location:
                return PlacementResult(False, "Выберите локацию для перемещения")

            self._moving_location = location
            self.current_template = LOCATION_TEMPLATES.get(location.location_type)
            return PlacementResult(True, f"Выбрано для перемещения: {location.name}")
        else:
            # Move to new location
            template = LOCATION_TEMPLATES.get(self._moving_location.location_type)
            can_place, message = self.can_place_at(game_map, x, y, template)

            if not can_place:
                return PlacementResult(False, message)

            old_x, old_y = self._moving_location.x, self._moving_location.y
            self._moving_location.x = x
            self._moving_location.y = y

            # Update all connections that point to old coordinates
            self._update_connections_after_move(game_map, old_x, old_y, x, y)

            result = PlacementResult(
                True,
                f"Перемещено: {self._moving_location.name} ({old_x},{old_y}) -> ({x},{y})",
                self._moving_location
            )
            self._moving_location = None
            return result

    def _update_connections_after_move(self, game_map: GeneratedMap,
                                       old_x: int, old_y: int,
                                       new_x: int, new_y: int) -> None:
        """Update all connections pointing to old coordinates after moving a location."""
        # Go through all locations and update their connections
        for location in game_map.locations:
            updated_connections = []
            for target_x, target_y in location.connections:
                # If connection points to old position, update to new position
                if target_x == old_x and target_y == old_y:
                    updated_connections.append((new_x, new_y))
                else:
                    updated_connections.append((target_x, target_y))
            location.connections = updated_connections

    def cancel_move(self) -> None:
        """Cancel current move operation."""
        self._moving_location = None

    def select_location(self, game_map: GeneratedMap, x: int, y: int) -> Optional[MapLocation]:
        """Select location at coordinates for editing."""
        self.selected_location = game_map.get_location_at(x, y)
        return self.selected_location

    def update_location_name(self, game_map: GeneratedMap, location: MapLocation,
                            new_name: str) -> PlacementResult:
        """Update location name."""
        if not new_name.strip():
            return PlacementResult(False, "Имя не может быть пустым")

        old_name = location.name
        loc_type = location.location_type

        # Update used names tracking
        if old_name in self._used_names.get(loc_type, set()):
            self._used_names[loc_type].discard(old_name)

        location.name = new_name.strip()
        self._used_names[loc_type].add(location.name)

        return PlacementResult(True, f"Переименовано: {old_name} -> {location.name}")

    def set_starting_village(self, game_map: GeneratedMap,
                            location: MapLocation) -> PlacementResult:
        """Set location as starting village."""
        if location.location_type != LOCATION_VILLAGE:
            return PlacementResult(False, "Стартовой может быть только деревня")

        game_map.starting_village = location
        return PlacementResult(True, f"Стартовая деревня: {location.name}")

    def get_location_info(self, location: MapLocation) -> Dict[str, Any]:
        """Get detailed information about a location."""
        info = {
            'type': location.location_type,
            'type_display': self._get_type_display_name(location.location_type),
            'name': location.name,
            'x': location.x,
            'y': location.y,
            'is_starting': False,  # Will be updated by caller
            'rank': location.rank,
            'shop_rank': location.shop_rank,
            'miners_count': location.miners_count,
            'respawn_time': location.respawn_time,
            'resource_type': location.resource_type,
            'player_attitude': location.player_attitude,
            'spawn_radius': location.spawn_radius,
            'animal_count': location.animal_count,
            'connections': location.connections,
            'guards': location.guards,
            'floors': location.floors
        }
        return info

    def _get_type_display_name(self, location_type: str) -> str:
        """Get display name for location type."""
        names = {
            LOCATION_CAPITAL: "Столица",
            LOCATION_CITY: "Город",
            LOCATION_VILLAGE: "Деревня",
            LOCATION_MINE: "Шахта",
            LOCATION_BANDIT_CAMP: "Лагерь разбойников",
            LOCATION_RUINS: "Руины",
            LOCATION_MAGIC_SCHOOL: "Школа магии",
            LOCATION_WARRIOR_ACADEMY: "Академия воинов",
            LOCATION_SECRET_CAMP: "Тайный лагерь",
            LOCATION_SPAWN_WOLF: "Спавн: Волки",
            LOCATION_SPAWN_BEAR: "Спавн: Медведи",
            LOCATION_SPAWN_DEER: "Спавн: Олени"
        }
        return names.get(location_type, location_type)

    def _get_next_name(self, location_type: str) -> str:
        """Get next available name for location type."""
        names = DEFAULT_NAMES.get(location_type, [])
        used = self._used_names.get(location_type, set())

        for name in names:
            if name not in used:
                return name

        # Generate numbered name
        base = names[0] if names else "Локация"
        i = 1
        while f"{base} {i}" in used:
            i += 1
        return f"{base} {i}"

    def get_statistics(self, game_map: GeneratedMap) -> Dict[str, int]:
        """Get location statistics for the map."""
        stats = {lt: 0 for lt in LOCATION_TEMPLATES}
        for loc in game_map.locations:
            if loc.location_type in stats:
                stats[loc.location_type] += 1
        return stats

    def validate_map(self, game_map: GeneratedMap) -> List[str]:
        """Validate map and return list of warnings/errors."""
        warnings = []

        # Check for starting village
        if not game_map.starting_village:
            warnings.append("ОШИБКА: Не задана стартовая деревня")

        # Check minimum location counts
        stats = self.get_statistics(game_map)

        if stats[LOCATION_CITY] < 1:
            warnings.append("ПРЕДУПРЕЖДЕНИЕ: Нет городов на карте")

        if stats[LOCATION_VILLAGE] < 3:
            warnings.append("ПРЕДУПРЕЖДЕНИЕ: Мало деревень (рекомендуется минимум 3)")

        if stats[LOCATION_MINE] < 1:
            warnings.append("ПРЕДУПРЕЖДЕНИЕ: Нет шахт на карте")

        # Check for locations on invalid biomes
        for loc in game_map.locations:
            biome = game_map.get_biome(loc.x, loc.y)
            template = LOCATION_TEMPLATES.get(loc.location_type)
            if template and biome not in template.valid_biomes:
                warnings.append(
                    f"ПРЕДУПРЕЖДЕНИЕ: {loc.name} находится на неподходящем биоме ({biome})"
                )

        return warnings

    def sync_used_names(self, game_map: GeneratedMap) -> None:
        """Synchronize used names tracking with actual map locations."""
        self._used_names = {lt: set() for lt in LOCATION_TEMPLATES}
        for loc in game_map.locations:
            if loc.location_type in self._used_names:
                self._used_names[loc.location_type].add(loc.name)
