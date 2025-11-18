"""
Модуль оптимизации производительности игры
"""
import math
from collections import defaultdict


class SpatialGrid:
    """
    Пространственная сетка для быстрого поиска ближайших объектов
    Разбивает карту на ячейки и хранит ссылки на объекты в каждой ячейке
    """

    def __init__(self, cell_size=10):
        """
        Инициализация пространственной сетки

        Args:
            cell_size: Размер ячейки в клетках карты
        """
        self.cell_size = cell_size
        self.grid = defaultdict(list)  # {(cell_x, cell_y): [objects]}

    def _get_cell(self, x, y):
        """
        Получить координаты ячейки для позиции

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            tuple: (cell_x, cell_y)
        """
        return (x // self.cell_size, y // self.cell_size)

    def clear(self):
        """Очистить всю сетку"""
        self.grid.clear()

    def add_object(self, obj, x, y):
        """
        Добавить объект в сетку

        Args:
            obj: Объект для добавления
            x: Координата X объекта
            y: Координата Y объекта
        """
        cell = self._get_cell(x, y)
        self.grid[cell].append(obj)

    def get_nearby_objects(self, x, y, radius):
        """
        Получить объекты в радиусе от позиции

        Args:
            x: Координата X
            y: Координата Y
            radius: Радиус поиска

        Returns:
            list: Список объектов в радиусе
        """
        # Определяем диапазон ячеек для поиска
        cell_x, cell_y = self._get_cell(x, y)
        cell_radius = math.ceil(radius / self.cell_size)

        nearby = []
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.grid:
                    for obj in self.grid[cell]:
                        # Проверяем реальное расстояние
                        distance = abs(obj.x - x) + abs(obj.y - y)
                        if distance <= radius:
                            nearby.append(obj)

        return nearby

    def rebuild(self, objects):
        """
        Перестроить всю сетку с новым списком объектов

        Args:
            objects: Список объектов с атрибутами x и y
        """
        self.clear()
        for obj in objects:
            self.add_object(obj, obj.x, obj.y)


class PerformanceOptimizer:
    """
    Класс для оптимизации производительности игры
    """

    def __init__(self):
        """Инициализация оптимизатора"""
        self.npc_grid = SpatialGrid(cell_size=15)
        self.update_counter = 0
        self.ai_update_interval = {
            'near': 1,    # Близкие NPC обновляются каждый кадр
            'medium': 3,  # Средние NPC обновляются раз в 3 кадра
            'far': 10     # Дальние NPC обновляются раз в 10 кадров
        }

    def should_update_ai(self, npc, player_x, player_y):
        """
        Определить, нужно ли обновлять AI этого NPC в текущем кадре

        Args:
            npc: NPC для проверки
            player_x: Координата X игрока
            player_y: Координата Y игрока

        Returns:
            bool: True если нужно обновлять
        """
        # Всегда обновляем NPC в бою
        if hasattr(npc, 'state') and npc.state == 'combat':
            return True

        # Вычисляем расстояние до игрока
        distance = abs(npc.x - player_x) + abs(npc.y - player_y)

        # Определяем категорию дистанции
        if distance <= 20:
            interval = self.ai_update_interval['near']
        elif distance <= 50:
            interval = self.ai_update_interval['medium']
        else:
            interval = self.ai_update_interval['far']

        # Проверяем, нужно ли обновлять в этом кадре
        return self.update_counter % interval == 0

    def increment_counter(self):
        """Увеличить счетчик обновлений"""
        self.update_counter = (self.update_counter + 1) % 30  # Сброс каждые 30 кадров

    def rebuild_spatial_grid(self, all_npcs):
        """
        Перестроить пространственную сетку для NPC

        Args:
            all_npcs: Список всех NPC
        """
        living_npcs = [npc for npc in all_npcs if npc.is_alive]
        self.npc_grid.rebuild(living_npcs)

    def get_nearby_npcs(self, x, y, radius):
        """
        Быстро получить ближайших NPC

        Args:
            x: Координата X
            y: Координата Y
            radius: Радиус поиска

        Returns:
            list: Список NPC в радиусе
        """
        return self.npc_grid.get_nearby_objects(x, y, radius)


class RenderCache:
    """
    Кэш для рендеринга - хранит предварительно вычисленные данные
    """

    def __init__(self):
        """Инициализация кэша"""
        self.tile_colors = {}  # {(x, y): color}
        self.visible_tiles = set()  # Множество видимых тайлов
        self.dirty = True  # Флаг необходимости обновления кэша

    def mark_dirty(self):
        """Пометить кэш как устаревший"""
        self.dirty = True

    def update_visible_tiles(self, camera_x, camera_y, tiles_x, tiles_y):
        """
        Обновить множество видимых тайлов

        Args:
            camera_x: Координата X камеры
            camera_y: Координата Y камеры
            tiles_x: Количество тайлов по X
            tiles_y: Количество тайлов по Y
        """
        self.visible_tiles.clear()
        for dy in range(tiles_y):
            for dx in range(tiles_x):
                map_x = camera_x + dx
                map_y = camera_y + dy
                self.visible_tiles.add((map_x, map_y))

    def is_visible(self, x, y):
        """
        Проверить, виден ли тайл

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            bool: True если тайл виден
        """
        return (x, y) in self.visible_tiles

    def clear(self):
        """Очистить весь кэш"""
        self.tile_colors.clear()
        self.visible_tiles.clear()
        self.dirty = True
