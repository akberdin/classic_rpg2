"""Brush tools for editing biomes on the map."""

from typing import List, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.helpers import bresenham_circle, get_neighbors
from .generator import GeneratedMap, BIOME_WATER, PASSABLE_BIOMES


class BrushShape(Enum):
    """Brush shape types."""
    CIRCLE = "circle"
    SQUARE = "square"
    DIAMOND = "diamond"


class BrushMode(Enum):
    """Brush operation modes."""
    PAINT = "paint"
    SMOOTH = "smooth"
    RAISE = "raise"
    LOWER = "lower"
    NOISE = "noise"


@dataclass
class BrushSettings:
    """Settings for brush tool."""
    size: int = 3
    shape: BrushShape = BrushShape.CIRCLE
    mode: BrushMode = BrushMode.PAINT
    biome: str = "plains"
    strength: float = 1.0
    smooth_iterations: int = 1

    def increase_size(self, max_size: int = 50) -> None:
        """Increase brush size."""
        self.size = min(self.size + 1, max_size)

    def decrease_size(self, min_size: int = 1) -> None:
        """Decrease brush size."""
        self.size = max(self.size - 1, min_size)


class BiomeBrush:
    """Brush tool for painting biomes."""

    # Biome order for raise/lower operations
    BIOME_HEIGHT_ORDER = [
        BIOME_WATER,
        "sand",
        "swamp",
        "plains",
        "forest",
        "hills",
        "mountain"
    ]

    def __init__(self, settings: BrushSettings = None):
        self.settings = settings or BrushSettings()
        self._last_paint_pos: Optional[Tuple[int, int]] = None
        self._paint_history: List[Set[Tuple[int, int]]] = []

    def get_brush_area(self, cx: int, cy: int, width: int, height: int) -> List[Tuple[int, int]]:
        """Get all tiles affected by brush at position."""
        points = []
        radius = self.settings.size // 2

        if self.settings.shape == BrushShape.CIRCLE:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                        if 0 <= x < width and 0 <= y < height:
                            points.append((x, y))

        elif self.settings.shape == BrushShape.SQUARE:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if 0 <= x < width and 0 <= y < height:
                        points.append((x, y))

        elif self.settings.shape == BrushShape.DIAMOND:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if abs(x - cx) + abs(y - cy) <= radius:
                        if 0 <= x < width and 0 <= y < height:
                            points.append((x, y))

        return points

    def apply(self, game_map: GeneratedMap, x: int, y: int) -> Set[Tuple[int, int]]:
        """Apply brush at position and return modified tiles."""
        modified = set()

        if self.settings.mode == BrushMode.PAINT:
            modified = self._paint(game_map, x, y)
        elif self.settings.mode == BrushMode.SMOOTH:
            modified = self._smooth(game_map, x, y)
        elif self.settings.mode == BrushMode.RAISE:
            modified = self._raise_terrain(game_map, x, y)
        elif self.settings.mode == BrushMode.LOWER:
            modified = self._lower_terrain(game_map, x, y)
        elif self.settings.mode == BrushMode.NOISE:
            modified = self._apply_noise(game_map, x, y)

        self._last_paint_pos = (x, y)
        if modified:
            self._paint_history.append(modified)

        return modified

    def _paint(self, game_map: GeneratedMap, cx: int, cy: int) -> Set[Tuple[int, int]]:
        """Paint biome at position."""
        modified = set()
        area = self.get_brush_area(cx, cy, game_map.width, game_map.height)

        for x, y in area:
            old_biome = game_map.get_biome(x, y)
            if old_biome != self.settings.biome:
                game_map.set_biome(x, y, self.settings.biome)
                modified.add((x, y))

        return modified

    def _smooth(self, game_map: GeneratedMap, cx: int, cy: int) -> Set[Tuple[int, int]]:
        """Smooth biomes in area using neighbor voting."""
        modified = set()
        area = self.get_brush_area(cx, cy, game_map.width, game_map.height)

        # Create a copy of biomes for the area
        original = {(x, y): game_map.get_biome(x, y) for x, y in area}

        for _ in range(self.settings.smooth_iterations):
            changes = {}
            for x, y in area:
                neighbors = get_neighbors(x, y, game_map.width, game_map.height)
                biome_counts = {}

                for nx, ny in neighbors:
                    b = original.get((nx, ny), game_map.get_biome(nx, ny))
                    biome_counts[b] = biome_counts.get(b, 0) + 1

                current = original[(x, y)]
                biome_counts[current] = biome_counts.get(current, 0) + 2

                most_common = max(biome_counts.keys(), key=lambda k: biome_counts[k])
                if most_common != current:
                    changes[(x, y)] = most_common

            for (x, y), biome in changes.items():
                original[(x, y)] = biome

        for (x, y), biome in original.items():
            if game_map.get_biome(x, y) != biome:
                game_map.set_biome(x, y, biome)
                modified.add((x, y))

        return modified

    def _raise_terrain(self, game_map: GeneratedMap, cx: int, cy: int) -> Set[Tuple[int, int]]:
        """Raise terrain (move to higher biome in order)."""
        modified = set()
        area = self.get_brush_area(cx, cy, game_map.width, game_map.height)

        for x, y in area:
            current = game_map.get_biome(x, y)
            if current in self.BIOME_HEIGHT_ORDER:
                idx = self.BIOME_HEIGHT_ORDER.index(current)
                if idx < len(self.BIOME_HEIGHT_ORDER) - 1:
                    new_biome = self.BIOME_HEIGHT_ORDER[idx + 1]
                    game_map.set_biome(x, y, new_biome)
                    modified.add((x, y))

        return modified

    def _lower_terrain(self, game_map: GeneratedMap, cx: int, cy: int) -> Set[Tuple[int, int]]:
        """Lower terrain (move to lower biome in order)."""
        modified = set()
        area = self.get_brush_area(cx, cy, game_map.width, game_map.height)

        for x, y in area:
            current = game_map.get_biome(x, y)
            if current in self.BIOME_HEIGHT_ORDER:
                idx = self.BIOME_HEIGHT_ORDER.index(current)
                if idx > 0:
                    new_biome = self.BIOME_HEIGHT_ORDER[idx - 1]
                    game_map.set_biome(x, y, new_biome)
                    modified.add((x, y))

        return modified

    def _apply_noise(self, game_map: GeneratedMap, cx: int, cy: int) -> Set[Tuple[int, int]]:
        """Apply random noise to biomes."""
        import random
        modified = set()
        area = self.get_brush_area(cx, cy, game_map.width, game_map.height)

        for x, y in area:
            if random.random() < self.settings.strength * 0.3:
                current = game_map.get_biome(x, y)
                if current in self.BIOME_HEIGHT_ORDER:
                    idx = self.BIOME_HEIGHT_ORDER.index(current)
                    # Random up or down
                    delta = random.choice([-1, 1])
                    new_idx = max(0, min(len(self.BIOME_HEIGHT_ORDER) - 1, idx + delta))
                    if new_idx != idx:
                        game_map.set_biome(x, y, self.BIOME_HEIGHT_ORDER[new_idx])
                        modified.add((x, y))

        return modified

    def fill_area(self, game_map: GeneratedMap, start_x: int, start_y: int,
                  target_biome: str = None) -> Set[Tuple[int, int]]:
        """Flood fill area with current biome."""
        if target_biome is None:
            target_biome = game_map.get_biome(start_x, start_y)

        if target_biome == self.settings.biome:
            return set()

        modified = set()
        to_fill = [(start_x, start_y)]
        visited = set()

        while to_fill:
            x, y = to_fill.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if game_map.get_biome(x, y) != target_biome:
                continue

            game_map.set_biome(x, y, self.settings.biome)
            modified.add((x, y))

            for nx, ny in get_neighbors(x, y, game_map.width, game_map.height, False):
                if (nx, ny) not in visited:
                    to_fill.append((nx, ny))

        return modified

    def line_to(self, game_map: GeneratedMap, x1: int, y1: int,
                x2: int, y2: int) -> Set[Tuple[int, int]]:
        """Draw a line of brush strokes from (x1,y1) to (x2,y2)."""
        modified = set()

        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx > dy:
            err = dx / 2
            while x != x2:
                modified.update(self.apply(game_map, x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != y2:
                modified.update(self.apply(game_map, x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        modified.update(self.apply(game_map, x2, y2))
        return modified

    def undo_last(self, game_map: GeneratedMap) -> bool:
        """Undo last paint operation (placeholder - needs state tracking)."""
        # This would require storing previous biome states
        # For now, return False indicating undo not available
        return False

    def reset(self) -> None:
        """Reset brush state."""
        self._last_paint_pos = None
        self._paint_history.clear()
