"""Helper utilities for the map editor."""

import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load editor configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "editor_config.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config: Dict[str, Any], config_path: str = None) -> None:
    """Save editor configuration to JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "editor_config.json"

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


class PerlinNoise:
    """Perlin noise generator for terrain generation."""

    def __init__(self, seed: int = None):
        self.seed = seed if seed is not None else random.randint(0, 2**31)
        random.seed(self.seed)
        self.permutation = list(range(256))
        random.shuffle(self.permutation)
        self.permutation += self.permutation

    def _fade(self, t: float) -> float:
        """Smoothstep function."""
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Compute gradient."""
        h = hash_val & 3
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:
            return -x - y

    def noise(self, x: float, y: float) -> float:
        """Generate 2D Perlin noise at given coordinates."""
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255

        x -= math.floor(x)
        y -= math.floor(y)

        u = self._fade(x)
        v = self._fade(y)

        A = self.permutation[X] + Y
        AA = self.permutation[A]
        AB = self.permutation[A + 1]
        B = self.permutation[X + 1] + Y
        BA = self.permutation[B]
        BB = self.permutation[B + 1]

        return self._lerp(
            self._lerp(
                self._grad(self.permutation[AA], x, y),
                self._grad(self.permutation[BA], x - 1, y),
                u
            ),
            self._lerp(
                self._grad(self.permutation[AB], x, y - 1),
                self._grad(self.permutation[BB], x - 1, y - 1),
                u
            ),
            v
        )

    def octave_noise(self, x: float, y: float, octaves: int, persistence: float = 0.5) -> float:
        """Generate multi-octave Perlin noise."""
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0

        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0

        return total / max_value


def perlin_noise(width: int, height: int, scale: float, octaves: int = 1,
                 seed: int = None) -> List[List[float]]:
    """Generate a 2D array of Perlin noise values."""
    noise_gen = PerlinNoise(seed)
    noise_map = []

    for y in range(height):
        row = []
        for x in range(width):
            nx = x / scale
            ny = y / scale
            value = noise_gen.octave_noise(nx, ny, octaves)
            row.append(value)
        noise_map.append(row)

    return noise_map


def normalize_value(value: float, min_val: float = -0.5, max_val: float = 0.5) -> float:
    """Normalize a value from [min_val, max_val] to [0, 1]."""
    return (value - min_val) / (max_val - min_val)


def normalize_map(noise_map: List[List[float]]) -> List[List[float]]:
    """Normalize entire noise map to [0, 1] range."""
    min_val = min(min(row) for row in noise_map)
    max_val = max(max(row) for row in noise_map)

    if max_val == min_val:
        return [[0.5 for _ in row] for row in noise_map]

    return [[normalize_value(v, min_val, max_val) for v in row] for row in noise_map]


def get_neighbors(x: int, y: int, width: int, height: int,
                  include_diagonals: bool = True) -> List[Tuple[int, int]]:
    """Get neighboring coordinates."""
    neighbors = []

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if include_diagonals:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            neighbors.append((nx, ny))

    return neighbors


def distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x2 - x1) + abs(y2 - y1)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def lerp_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int],
               t: float) -> Tuple[int, int, int]:
    """Linear interpolation between two colors."""
    t = clamp(t, 0, 1)
    return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))


def point_in_rect(point: Tuple[int, int], rect: Tuple[int, int, int, int]) -> bool:
    """Check if point is inside rectangle (x, y, width, height)."""
    x, y = point
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


def bresenham_circle(cx: int, cy: int, radius: int) -> List[Tuple[int, int]]:
    """Get all points within a circle using Bresenham-style approach."""
    points = []
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                points.append((x, y))
    return points
