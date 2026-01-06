"""
Менеджер подземелий - управление переходами между картами
"""
import random
from typing import Optional, List, Tuple

from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.generator import DungeonGenerator
from game.dungeon.tiles import DungeonTileType
from game.constants import DUNGEON_VISION_RADIUS


class DungeonManager:
    """Менеджер подземелий и шахт"""

    def __init__(self, game):
        """
        Инициализация менеджера

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.generator = DungeonGenerator()

        # Текущее подземелье (если игрок находится в нем)
        self.current_dungeon: Optional[DungeonMap] = None

        # Флаг нахождения в подземелье
        self.is_in_dungeon = False

        # Сохраненная позиция игрока на основной карте
        self.saved_world_x: int = 0
        self.saved_world_y: int = 0

        # Кэш сгенерированных подземелий (по координатам локации)
        self._dungeon_cache: dict = {}

        # Многоуровневость подземелий
        self.current_depth: int = 1  # Текущая глубина (1-based)
        self.max_depth: int = 5      # Максимальная глубина подземелья
        self.dungeon_levels: dict = {}  # Кэш уровней текущего подземелья {depth: DungeonMap}
        self.current_dungeon_key: Optional[str] = None  # Ключ текущего подземелья
        self.current_floors_config: List[dict] = []  # Конфиг этажей текущего подземелья

        # NPC для подземелий
        self.dungeon_npcs: List = []

        # Система боя в подземелье
        self.selected_target = None  # Выбранный враг
        self.target_index = 0  # Индекс для циклического выбора

        # Режим выбора цели для умения
        self.skill_targeting_mode = False
        self.pending_skill = None  # Умение, ожидающее выбора цели

        # Выбранный интерактивный объект (ловушка/тайник)
        self.selected_object = None
        self.selected_object_type = None  # 'trap' или 'stash'

        # Выбранный объект руды для добычи
        self.selected_ore = None  # DungeonTile с ore_data

        # Отношение локации к игроку (для определения агрессии NPC)
        self.current_player_attitude: int = 0

        # Тип ресурса текущей шахты (для генерации руды)
        self.current_resource_type: Optional[str] = None

    def _get_floor_config(self, depth: int) -> Optional[dict]:
        """
        Получить конфигурацию этажа по глубине

        Args:
            depth: Номер этажа (1-based)

        Returns:
            dict или None: Конфигурация этажа {floor_number, floor_type, size, npc}
        """
        for floor_config in self.current_floors_config:
            if floor_config.get('floor_number') == depth:
                return floor_config
        return None

    def _load_floors_config(self, location) -> List[dict]:
        """
        Загрузить конфигурацию этажей из локации

        Args:
            location: Объект локации

        Returns:
            List[dict]: Список конфигураций этажей
        """
        floors = getattr(location, 'floors', None)
        if floors:
            return floors
        # Fallback: пустой список (будет использоваться авто-расчёт)
        return []

    def can_enter_dungeon(self, player) -> Tuple[bool, str, str]:
        """
        Проверить, может ли игрок войти в подземелье

        Args:
            player: Объект игрока

        Returns:
            Tuple[bool, str, str]: (можно ли войти, тип подземелья, название)
        """
        from game.constants import LOCATION_RUINS, LOCATION_MINE

        # Получаем текущий тайл игрока
        tile = self.game.game_map.get_tile(player.x, player.y)

        if not tile or not tile.has_location():
            return False, "", ""

        location = tile.location

        # Проверяем тип локации

        if location.location_type == LOCATION_RUINS:
            return True, "dungeon", location.name
        elif location.location_type == LOCATION_MINE:
            return True, "mine", location.name

        return False, "", ""

    def enter_dungeon(self, player, dungeon_type: str, location_name: str) -> dict:
        """
        Вход в подземелье

        Args:
            player: Объект игрока
            dungeon_type: Тип подземелья ("dungeon" или "mine")
            location_name: Название локации

        Returns:
            dict: Результат входа
        """
        if self.is_in_dungeon:
            return {
                "success": False,
                "message": "Вы уже находитесь в подземелье!"
            }

        # Сохраняем позицию на основной карте
        self.saved_world_x = player.x
        self.saved_world_y = player.y

        # Инициализируем многоуровневость
        self.current_depth = 1
        self.current_dungeon_key = f"{self.saved_world_x}_{self.saved_world_y}"

        # Загружаем конфигурацию этажей из локации
        tile = self.game.game_map.get_tile(player.x, player.y)
        if tile and tile.has_location():
            self.current_floors_config = self._load_floors_config(tile.location)
            # Если есть конфиг этажей, используем его для определения max_depth
            if self.current_floors_config:
                self.max_depth = len(self.current_floors_config)
            # Сохраняем player_attitude локации для определения агрессии NPC
            self.current_player_attitude = getattr(tile.location, 'player_attitude', 0)
            # Сохраняем тип ресурса шахты для генерации руды
            self.current_resource_type = getattr(tile.location, 'resource_type', None)
        else:
            self.current_floors_config = []
            self.current_player_attitude = 0
            self.current_resource_type = None

        # Проверяем кэш уровней
        if self.current_dungeon_key not in self.dungeon_levels:
            self.dungeon_levels[self.current_dungeon_key] = {}

        cache = self.dungeon_levels[self.current_dungeon_key]

        if 1 in cache:
            # Используем сохраненный первый уровень
            self.current_dungeon = cache[1]
            self.dungeon_npcs = self.current_dungeon.npcs.copy()
        else:
            # Генерируем новое подземелье (первый уровень)
            location_type = "mine" if dungeon_type == "mine" else "ruins"

            # Получаем параметры первого этажа из конфига
            floor_config = self._get_floor_config(1)
            floor_type = floor_config.get('floor_type') if floor_config else None
            floor_size = floor_config.get('size') if floor_config else None

            self.current_dungeon = self.generator.generate_dungeon_for_location(
                location_type, location_name, player.x, player.y,
                current_depth=1, max_depth=self.max_depth,
                floor_type=floor_type, floor_size=floor_size,
                resource_type=self.current_resource_type
            )

            # Генерируем NPC для подземелья
            self._spawn_dungeon_npcs()

            # Сохраняем первый уровень в кэш
            cache[1] = self.current_dungeon

        # Перемещаем игрока на вход подземелья
        if self.current_dungeon.entrance:
            player.x, player.y = self.current_dungeon.entrance
        else:
            # Fallback - в центр карты
            player.x = self.current_dungeon.width // 2
            player.y = self.current_dungeon.height // 2

        self.is_in_dungeon = True

        # Обновляем видимость для инициализации fog of war
        self.current_dungeon.update_visibility(player.x, player.y, DUNGEON_VISION_RADIUS)

        return {
            "success": True,
            "message": f"Вы вошли в {self.current_dungeon.name}",
            "dungeon_name": self.current_dungeon.name,
            "dungeon_level": self.current_dungeon.dungeon_level,
        }

    def exit_dungeon(self, player) -> dict:
        """
        Выход из подземелья

        Args:
            player: Объект игрока

        Returns:
            dict: Результат выхода
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return {
                "success": False,
                "message": "Вы не находитесь в подземелье!"
            }

        # Проверяем, на выходе ли игрок
        if not self.current_dungeon.is_exit_tile(player.x, player.y):
            return {
                "success": False,
                "message": "Выход только через специальные точки выхода!"
            }

        # Возвращаем игрока на основную карту
        player.x = self.saved_world_x
        player.y = self.saved_world_y

        dungeon_name = self.current_dungeon.name
        self.is_in_dungeon = False

        return {
            "success": True,
            "message": f"Вы покинули {dungeon_name}",
        }

    def go_down_stairs(self, player) -> dict:
        """
        Спуститься на следующий уровень подземелья

        Args:
            player: Объект игрока

        Returns:
            dict: Результат перехода
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return {
                "success": False,
                "message": "Вы не находитесь в подземелье!"
            }

        # Проверяем, на лестнице ли игрок
        tile = self.current_dungeon.get_tile(player.x, player.y)
        if not tile or not tile.is_stairs_down():
            return {
                "success": False,
                "message": "Здесь нет лестницы вниз!"
            }

        # Проверяем, не достигнут ли предел глубины
        if self.current_depth >= self.max_depth:
            return {
                "success": False,
                "message": "Это последний уровень подземелья!"
            }

        # Сохраняем NPC текущего уровня
        self.current_dungeon.npcs = self.dungeon_npcs.copy()

        # Переходим на следующий уровень
        self.current_depth += 1

        # Проверяем кэш уровней
        cache = self.dungeon_levels[self.current_dungeon_key]

        if self.current_depth in cache:
            # Загружаем сохранённый уровень
            self.current_dungeon = cache[self.current_depth]
            self.dungeon_npcs = self.current_dungeon.npcs.copy()
        else:
            # Генерируем новый уровень
            tile = self.game.game_map.get_tile(self.saved_world_x, self.saved_world_y)
            location_type = "mine" if self.current_dungeon.dungeon_type == "mine" else "ruins"
            location_name = self.current_dungeon.name.split(" (")[0].replace("Подземелье под ", "").replace("Шахта ", "")

            # Получаем параметры этажа из конфига
            floor_config = self._get_floor_config(self.current_depth)
            floor_type = floor_config.get('floor_type') if floor_config else None
            floor_size = floor_config.get('size') if floor_config else None

            self.current_dungeon = self.generator.generate_dungeon_for_location(
                location_type, location_name, self.saved_world_x, self.saved_world_y,
                current_depth=self.current_depth, max_depth=self.max_depth,
                floor_type=floor_type, floor_size=floor_size,
                resource_type=self.current_resource_type
            )

            # Генерируем NPC для нового уровня
            self._spawn_dungeon_npcs()

            # Сохраняем в кэш
            cache[self.current_depth] = self.current_dungeon

        # Перемещаем игрока на лестницу вверх (точку входа нового уровня)
        if self.current_dungeon.stairs_up:
            player.x, player.y = self.current_dungeon.stairs_up
        elif self.current_dungeon.entrance:
            player.x, player.y = self.current_dungeon.entrance
        else:
            player.x = self.current_dungeon.width // 2
            player.y = self.current_dungeon.height // 2

        # Обновляем видимость
        self.current_dungeon.update_visibility(player.x, player.y, DUNGEON_VISION_RADIUS)

        return {
            "success": True,
            "message": f"Вы спустились на уровень {self.current_depth}",
            "dungeon_name": self.current_dungeon.name,
            "current_depth": self.current_depth,
            "max_depth": self.max_depth
        }

    def go_up_stairs(self, player) -> dict:
        """
        Подняться на предыдущий уровень подземелья

        Args:
            player: Объект игрока

        Returns:
            dict: Результат перехода
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return {
                "success": False,
                "message": "Вы не находитесь в подземелье!"
            }

        # Проверяем, на лестнице ли игрок
        tile = self.current_dungeon.get_tile(player.x, player.y)
        if not tile or not tile.is_stairs_up():
            return {
                "success": False,
                "message": "Здесь нет лестницы вверх!"
            }

        # Проверяем, не на первом ли уровне
        if self.current_depth <= 1:
            return {
                "success": False,
                "message": "Это первый уровень подземелья! Используйте выход для возврата."
            }

        # Сохраняем NPC текущего уровня
        self.current_dungeon.npcs = self.dungeon_npcs.copy()

        # Переходим на предыдущий уровень
        self.current_depth -= 1

        # Загружаем предыдущий уровень из кэша
        cache = self.dungeon_levels[self.current_dungeon_key]
        self.current_dungeon = cache[self.current_depth]
        self.dungeon_npcs = self.current_dungeon.npcs.copy()

        # Перемещаем игрока на лестницу вниз
        if self.current_dungeon.stairs_down:
            player.x, player.y = self.current_dungeon.stairs_down
        else:
            player.x, player.y = self.current_dungeon.entrance

        # Обновляем видимость
        self.current_dungeon.update_visibility(player.x, player.y, DUNGEON_VISION_RADIUS)

        return {
            "success": True,
            "message": f"Вы поднялись на уровень {self.current_depth}",
            "dungeon_name": self.current_dungeon.name,
            "current_depth": self.current_depth,
            "max_depth": self.max_depth
        }

    def _spawn_dungeon_npcs(self):
        """
        Генерация NPC для текущего подземелья на основе конфигурации этажа.

        Конфигурация берется из floors[].npcs в map_config.json.
        Если npcs не указано для этажа - NPC не спавнятся.

        Формат конфига npcs:
        [
            {"type": "rat", "rank": 1, "count": 10},
            {"type": "miner", "rank": 2, "count": 4},
            {"type": "warrior", "rank": 2, "count": 4}
        ]
        """
        if not self.current_dungeon:
            return

        self.dungeon_npcs.clear()
        dungeon = self.current_dungeon

        # Получаем конфигурацию текущего этажа
        floor_config = self._get_floor_config(self.current_depth)
        if not floor_config:
            return  # Нет конфига - нет NPC

        # Получаем список NPC для спавна
        npcs_config = floor_config.get('npcs', [])
        if not npcs_config:
            return  # npcs не указаны - не спавним NPC

        # Импортируем классы NPC
        from game.npc.hostile import Undead
        from game.npc.worker import Miner
        from game.npc.guard import Guard
        from game.npc.animal import Rat

        # Спавним NPC по конфигурации
        for npc_entry in npcs_config:
            npc_type = npc_entry.get('type', 'undead')
            npc_rank = npc_entry.get('rank', 1)
            npc_count = npc_entry.get('count', 1)

            # Определяем диапазон уровней по рангу
            # Ранг 1: 1-10, Ранг 2: 11-20, Ранг 3: 21-30, Ранг 4: 31-40
            level_min = (npc_rank - 1) * 10 + 1
            level_max = npc_rank * 10

            for _ in range(npc_count):
                # Находим случайную свободную клетку
                pos = dungeon.get_random_floor_tile(exclude_special=True)
                if pos is None:
                    continue

                x, y = pos

                # Проверяем, нет ли там уже NPC
                if dungeon.get_npc_at(x, y) is not None:
                    continue

                # Проверяем безопасную зону вокруг входа (радиус 5 клеток)
                if dungeon.entrance:
                    entrance_x, entrance_y = dungeon.entrance
                    distance_to_entrance = abs(x - entrance_x) + abs(y - entrance_y)
                    if distance_to_entrance < 5:
                        continue  # Слишком близко к входу, пропускаем

                # Определяем уровень NPC в диапазоне ранга
                level = random.randint(level_min, level_max)

                # Создаем NPC нужного типа с учётом player_attitude локации
                npc = self._create_dungeon_npc(npc_type, x, y, level, self.current_player_attitude)
                if npc:
                    self.dungeon_npcs.append(npc)
                    dungeon.add_npc(npc)

    def _create_dungeon_npc(self, npc_type: str, x: int, y: int, level: int, player_attitude: int = 0):
        """
        Создать NPC заданного типа для подземелья.

        Args:
            npc_type: Тип NPC (любой тип из game/npc)
            x, y: Координаты спавна
            level: Уровень NPC
            player_attitude: Отношение локации к игроку (влияет на агрессию)

        Returns:
            NPC объект или None
        """
        from game.constants import RELATIONSHIP_HOSTILE, RELATIONSHIP_NEUTRAL

        # Импортируем все классы NPC
        from game.npc import (
            Guard, Merchant, MagicMerchant, WarriorMerchant, ShadowMerchant,
            MagePatrol, Bandit, Undead, ShadowAdept, Miner,
            Alchemist, Hunter, Necromancer, Wolf, Bear, Deer, Rat
        )

        # Маппинг типов NPC на классы и имена
        # 'hostile': True означает, что NPC всегда агрессивен
        # 'hostile': False означает, что агрессия зависит от player_attitude
        npc_configs = {
            'rat': {
                'class': Rat,
                'names': ["Крыса", "Гигантская крыса", "Пещерная крыса", "Тварь"],
                'args': lambda: {'spawn_x': x, 'spawn_y': y},
                'hostile': True  # Всегда агрессивны
            },
            'miner': {
                'class': Miner,
                'names': ["Шахтёр", "Рудокоп", "Горняк", "Копатель"],
                'args': lambda: {
                    'mine_x': x, 'mine_y': y, 'mine_name': "Подземелье",
                    'rest_x': x, 'rest_y': y, 'rest_location_name': None,
                    'spawn_radius': 10
                },
                'hostile': False  # Зависит от player_attitude
            },
            'warrior': {
                'class': Guard,
                'names': ["Стражник", "Воин", "Защитник", "Страж"],
                'args': lambda: {},
                'post_init': lambda npc: npc.set_patrol_route([
                    (x + 2, y), (x + 2, y + 2), (x, y + 2),
                    (x - 2, y + 2), (x - 2, y), (x - 2, y - 2),
                    (x, y - 2), (x + 2, y - 2)
                ]),
                'hostile': False
            },
            'guard': {
                'class': Guard,
                'names': ["Стражник", "Охранник", "Дозорный"],
                'args': lambda: {},
                'post_init': lambda npc: npc.set_patrol_route([
                    (x + 2, y), (x + 2, y + 2), (x, y + 2),
                    (x - 2, y + 2), (x - 2, y), (x - 2, y - 2),
                    (x, y - 2), (x + 2, y - 2)
                ]),
                'hostile': False
            },
            'undead': {
                'class': Undead,
                'names': ["Скелет", "Зомби", "Призрак", "Вурдалак", "Умертвие",
                          "Костяной воин", "Гуль", "Дух тьмы", "Тень", "Мертвец"],
                'args': lambda: {'ruins_x': x, 'ruins_y': y},
                'hostile': True  # Всегда агрессивны
            },
            'bandit': {
                'class': Bandit,
                'names': ["Бандит", "Разбойник", "Головорез", "Грабитель"],
                'args': lambda: {'camp_x': x, 'camp_y': y},
                'hostile': True  # Всегда агрессивны
            },
            'mage': {
                'class': MagePatrol,
                'names': ["Маг", "Чародей", "Волшебник", "Адепт"],
                'args': lambda: {'academy_x': x, 'academy_y': y},
                'hostile': False
            },
            'shadow_adept': {
                'class': ShadowAdept,
                'names': ["Адепт Тени", "Теневой Страж", "Ночной Дозор"],
                'args': lambda: {'camp_x': x, 'camp_y': y},
                'hostile': False
            },
            'hunter': {
                'class': Hunter,
                'names': ["Охотник", "Следопыт", "Рейнджер", "Ловчий"],
                'args': lambda: {'home_x': x, 'home_y': y},
                'hostile': False
            },
            'alchemist': {
                'class': Alchemist,
                'names': ["Алхимик", "Зельевар", "Знахарь"],
                'args': lambda: {},
                'hostile': False
            },
            'necromancer': {
                'class': Necromancer,
                'names': ["Некромант", "Темный Маг", "Владыка Нежити", "Чернокнижник"],
                'args': lambda: {'ruins_x': x, 'ruins_y': y},
                'hostile': True  # Всегда агрессивны
            },
            'wolf': {
                'class': Wolf,
                'names': ["Волк", "Серый волк", "Матёрый волк"],
                'args': lambda: {'spawn_x': x, 'spawn_y': y},
                'hostile': True  # Хищник - всегда агрессивен
            },
            'bear': {
                'class': Bear,
                'names': ["Медведь", "Бурый медведь", "Пещерный медведь"],
                'args': lambda: {'spawn_x': x, 'spawn_y': y},
                'hostile': True  # Хищник - всегда агрессивен
            },
            'deer': {
                'class': Deer,
                'names': ["Олень", "Лань", "Косуля"],
                'args': lambda: {'spawn_x': x, 'spawn_y': y},
                'hostile': False  # Травоядное - не агрессивно
            },
            'merchant': {
                'class': Merchant,
                'names': ["Торговец", "Купец", "Барышник"],
                'args': lambda: {},
                'hostile': False
            },
            'magic_merchant': {
                'class': MagicMerchant,
                'names': ["Магический торговец", "Продавец артефактов"],
                'args': lambda: {},
                'hostile': False
            },
            'warrior_merchant': {
                'class': WarriorMerchant,
                'names': ["Военный торговец", "Оружейник"],
                'args': lambda: {},
                'hostile': False
            },
            'shadow_merchant': {
                'class': ShadowMerchant,
                'names': ["Теневой торговец", "Скупщик"],
                'args': lambda: {},
                'hostile': False
            }
        }

        # Получаем конфигурацию для типа NPC
        config = npc_configs.get(npc_type)

        if not config:
            # Неизвестный тип - создаём нежить по умолчанию
            print(f"Предупреждение: Неизвестный тип NPC '{npc_type}', создаём нежить")
            config = npc_configs['undead']
            npc_type = 'undead'

        # Генерируем имя
        name = f"{random.choice(config['names'])} (Ур. {level})"

        # Создаём NPC
        npc_class = config['class']
        extra_args = config['args']()

        try:
            npc = npc_class(name=name, x=x, y=y, level=level, **extra_args)
        except TypeError:
            # Некоторые классы могут иметь другую сигнатуру
            try:
                npc = npc_class(name, x, y, level, **extra_args)
            except TypeError as e:
                print(f"Ошибка создания NPC типа '{npc_type}': {e}")
                return None

        # Выполняем пост-инициализацию если есть
        if 'post_init' in config:
            config['post_init'](npc)

        # Устанавливаем общие параметры для подземелий
        if hasattr(npc, 'patrol_radius'):
            npc.patrol_radius = 10
        if hasattr(npc, 'max_distance_from_spawn'):
            npc.max_distance_from_spawn = 15
        if hasattr(npc, 'max_distance_from_ruins'):
            npc.max_distance_from_ruins = 15

        # Устанавливаем агрессию NPC на основе типа и player_attitude
        is_hostile_type = config.get('hostile', False)

        if is_hostile_type:
            # Враждебный тип - всегда агрессивен
            npc.relationship = RELATIONSHIP_HOSTILE
            npc.dungeon_hostile = True
        elif player_attitude < -5:
            # Нейтральный/дружественный тип, но player_attitude < -5
            # Становится враждебным
            npc.relationship = RELATIONSHIP_HOSTILE
            npc.dungeon_hostile = True
        else:
            # Нейтральный/дружественный тип, player_attitude >= -5
            # Остаётся нейтральным
            npc.relationship = RELATIONSHIP_NEUTRAL
            npc.dungeon_hostile = False

        # Сохраняем player_attitude для возможного использования в AI
        npc.dungeon_player_attitude = player_attitude

        return npc

    def update_dungeon(self, player):
        """
        Обновление состояния подземелья

        Args:
            player: Объект игрока
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return

        # Примечание: НЕ обновляем AI NPC здесь, так как enemy_turn() вызывается
        # отдельно после каждого действия игрока (одно действие за ход)

    def interact_with_tile(self, player) -> Optional[dict]:
        """
        Взаимодействие с текущей клеткой

        Args:
            player: Объект игрока

        Returns:
            dict или None: Результат взаимодействия
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        dungeon = self.current_dungeon
        tile = dungeon.get_tile(player.x, player.y)

        if not tile:
            return None

        # Проверяем останки
        remains = dungeon.get_remains_at(player.x, player.y)
        if remains and not remains.get('looted', False):
            loot_result = dungeon.loot_remains(player.x, player.y, player)
            if loot_result:
                messages = [f"Вы обыскали останки {loot_result['enemy_name']}:"]
                if loot_result['gold'] > 0:
                    messages.append(f"  +{loot_result['gold']} золота")
                for item_name, quantity in loot_result['items']:
                    messages.append(f"  +{item_name} x{quantity}")

                # Если ничего не найдено
                if loot_result['gold'] == 0 and not loot_result['items']:
                    messages.append("  Пусто!")

                return {
                    "type": "remains",
                    "success": True,
                    "message": "\n".join(messages),
                    "gold": loot_result['gold'],
                    "items": loot_result['items']
                }

        # Проверяем выход
        if dungeon.is_exit_tile(player.x, player.y):
            return {
                "type": "exit",
                "message": "Нажмите E чтобы покинуть подземелье"
            }

        return None

    def can_move_in_dungeon(self, player, new_x: int, new_y: int) -> bool:
        """
        Проверить, можно ли переместиться на клетку в подземелье

        Args:
            player: Объект игрока
            new_x: Новая координата X
            new_y: Новая координата Y

        Returns:
            bool: True если можно переместиться
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return False

        dungeon = self.current_dungeon

        # Проверяем границы
        if not dungeon.is_valid_position(new_x, new_y):
            return False

        # Проверяем проходимость
        if not dungeon.is_passable(new_x, new_y):
            return False

        # Проверяем NPC
        npc = dungeon.get_npc_at(new_x, new_y)
        if npc and npc.is_alive:
            # Можно стоять на клетке с NPC (для боя)
            pass

        return True

    def move_player(self, player, dx: int, dy: int) -> Optional[dict]:
        """
        Переместить игрока в подземелье

        Args:
            player: Объект игрока
            dx: Смещение по X (-1, 0, 1)
            dy: Смещение по Y (-1, 0, 1)

        Returns:
            dict или None: Результат перемещения
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        new_x = player.x + dx
        new_y = player.y + dy

        # Проверяем возможность перемещения
        if not self.can_move_in_dungeon(player, new_x, new_y):
            return {"success": False, "message": "Нельзя пройти туда"}

        dungeon = self.current_dungeon

        # Проверяем NPC на клетке
        npc = dungeon.get_npc_at(new_x, new_y)
        if npc and npc.is_alive:
            return {"success": False, "message": f"Клетка занята: {npc.name}"}

        # Перемещаем игрока
        player.x = new_x
        player.y = new_y

        # Обновляем видимость (используем увеличенный радиус для подземелий)
        dungeon.update_visibility(player.x, player.y, DUNGEON_VISION_RADIUS)

        result = {"success": True, "message": ""}

        # Проверяем останки
        remains = dungeon.get_remains_at(new_x, new_y)
        if remains and not remains.get('looted', False):
            result["remains_found"] = True
            result["message"] = f"Останки {remains['enemy_name']}. Нажмите E чтобы обыскать."

        return result

    def get_current_dungeon_info(self) -> Optional[dict]:
        """Получить информацию о текущем подземелье"""
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        return self.current_dungeon.get_statistics()

    def clear_cache(self):
        """Очистить кэш подземелий"""
        self._dungeon_cache.clear()

    # ===== Система боя в подземелье =====

    def get_visible_enemies(self, player) -> List:
        """
        Получить список видимых врагов

        Args:
            player: Объект игрока

        Returns:
            List: Список видимых живых NPC
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return []

        visible = []
        dungeon = self.current_dungeon

        for npc in dungeon.npcs:
            if not npc.is_alive:
                continue

            # Проверяем видимость клетки
            tile = dungeon.get_tile(npc.x, npc.y)
            if tile and tile.visible:
                visible.append(npc)

        return visible

    def cycle_target(self, player, direction: int = 1):
        """
        Переключить выбранную цель

        Args:
            player: Объект игрока
            direction: 1 для следующего, -1 для предыдущего
        """
        enemies = self.get_visible_enemies(player)

        if not enemies:
            self.selected_target = None
            self.target_index = 0
            return

        self.target_index = (self.target_index + direction) % len(enemies)
        self.selected_target = enemies[self.target_index]

    def select_target(self, npc):
        """
        Выбрать конкретную цель

        Args:
            npc: NPC для выбора
        """
        self.selected_target = npc

    def deselect_target(self):
        """Снять выделение с цели"""
        self.selected_target = None
        self.target_index = 0
        self.skill_targeting_mode = False
        self.pending_skill = None

    def get_npc_at_screen_pos(self, player, screen_x: int, screen_y: int, tile_size: int):
        """
        Получить NPC по позиции на экране

        Args:
            player: Игрок
            screen_x, screen_y: Позиция на экране
            tile_size: Размер тайла

        Returns:
            NPC или None
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        dungeon = self.current_dungeon
        screen_width = self.game.window_width
        screen_height = self.game.window_height

        # Вычисляем центр экрана в тайлах (аналогично renderer.py с +2)
        tiles_x = screen_width // tile_size + 2
        tiles_y = screen_height // tile_size + 2
        start_x = player.x - tiles_x // 2
        start_y = player.y - tiles_y // 2

        # Переводим экранные координаты в координаты карты
        tile_x = start_x + screen_x // tile_size
        tile_y = start_y + screen_y // tile_size

        return dungeon.get_npc_at(tile_x, tile_y)

    def can_attack_target(self, player, target, skill=None) -> Tuple[bool, str]:
        """
        Проверить можно ли атаковать цель

        Args:
            player: Игрок
            target: Цель (NPC)
            skill: Умение (опционально)

        Returns:
            Tuple[bool, str]: (можно ли атаковать, причина)
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return False, "Не в подземелье"

        if not target or not target.is_alive:
            return False, "Цель недоступна"

        dungeon = self.current_dungeon

        # Проверяем линию видимости
        if not dungeon.has_line_of_sight(player.x, player.y, target.x, target.y):
            return False, "Нет линии видимости"

        # Проверяем расстояние
        distance = abs(player.x - target.x) + abs(player.y - target.y)

        if skill:
            # Получаем радиус умения (tactical_range - основной атрибут дальности умения)
            skill_range = getattr(skill, 'tactical_range', getattr(skill, 'range', 1))
            if distance > skill_range:
                return False, f"Слишком далеко (нужно {skill_range})"
        else:
            # Базовая атака - только рядом
            if distance > 1:
                return False, "Слишком далеко"

        return True, ""

    def use_skill_on_target(self, player, skill, target=None) -> Optional[dict]:
        """
        Использовать умение на цели (аналогично тактическому бою)

        Args:
            player: Игрок
            skill: Умение
            target: Цель (если None - используется selected_target или ближайший враг)

        Returns:
            dict или None: Результат использования
        """
        if target is None:
            target = self.selected_target

        # Если цель не выбрана, автоматически выбираем ближайшего видимого врага
        if target is None:
            visible_enemies = self.get_visible_enemies(player)
            if visible_enemies:
                # Сортируем по расстоянию и выбираем ближайшего
                visible_enemies.sort(key=lambda e: abs(e.x - player.x) + abs(e.y - player.y))
                target = visible_enemies[0]
                self.selected_target = target  # Выделяем выбранного врага

        if target is None:
            return {"success": False, "message": "Нет видимых врагов"}

        # Проверяем возможность атаки (дистанция и линия видимости)
        can_attack, reason = self.can_attack_target(player, target, skill)
        if not can_attack:
            return {"success": False, "message": reason}

        # Используем умение через skill_manager (как в тактическом бою)
        # Это обеспечивает правильный расчет урона, эффектов и прогресса умения
        skill_result = player.skill_manager.use_skill(skill, target)

        if not skill_result.get('success', False):
            return {"success": False, "message": skill_result.get('message', 'Не удалось использовать умение')}

        # Формируем результат для системы подземелий
        result = {
            "success": True,
            "damage": skill_result.get('damage', 0),
            "target": target.name,
            "skill": getattr(skill, 'name', 'Атака'),
            "killed": skill_result.get('killed', False) or not target.is_alive,
            "critical": skill_result.get('critical', False),
            "message": skill_result.get('message', '')
        }

        # Помечаем атакованного NPC как агрессивного (теперь он будет преследовать игрока)
        target._aggro_target = player

        # Если враг убит
        if not target.is_alive:
            self._on_enemy_killed(player, target)
            if self.selected_target == target:
                self.deselect_target()

        return result

    def basic_attack(self, player) -> Optional[dict]:
        """
        Базовая атака по выбранной цели

        Args:
            player: Игрок

        Returns:
            dict или None: Результат атаки
        """
        # Если цель не выбрана, автоматически выбираем ближайшего видимого врага
        if self.selected_target is None:
            visible_enemies = self.get_visible_enemies(player)
            if visible_enemies:
                # Сортируем по расстоянию и выбираем ближайшего
                visible_enemies.sort(key=lambda e: abs(e.x - player.x) + abs(e.y - player.y))
                self.selected_target = visible_enemies[0]

        if self.selected_target is None:
            return {"success": False, "message": "Нет видимых врагов"}

        can_attack, reason = self.can_attack_target(player, self.selected_target)
        if not can_attack:
            return {"success": False, "message": reason}

        target = self.selected_target
        damage = player.get_total_damage()

        # Учитываем защиту врага
        defense = getattr(target, 'defense', 0)
        final_damage = max(1, damage - defense // 2)

        actual_damage = target.take_damage(final_damage)

        # Помечаем атакованного NPC как агрессивного
        target._aggro_target = player

        result = {
            "success": True,
            "damage": actual_damage,
            "target": target.name,
            "skill": "Атака",
            "killed": not target.is_alive
        }

        if not target.is_alive:
            self._on_enemy_killed(player, target)
            self.deselect_target()

        return result

    def _on_enemy_killed(self, player, enemy):
        """
        Обработка убийства врага

        Args:
            player: Игрок
            enemy: Убитый враг
        """
        # Используем правильный расчет опыта с учетом разницы уровней
        from game.combat import calculate_combat_exp
        exp_reward = calculate_combat_exp(player.level, enemy.level)
        player.add_experience(exp_reward)
        print(f"Получено {exp_reward} опыта!")

        # Создаём останки на месте врага (золото и лут можно получить при обыске)
        # Используем полноценную систему лута для генерации
        from game.loot_system import LootSystem

        loot_system = LootSystem(player)
        loot_items, gold_reward = loot_system.generate_loot(enemy)

        # Добавляем останки (если есть что добавить)
        if gold_reward > 0 or len(loot_items) > 0:
            self.current_dungeon.add_remains(enemy.x, enemy.y, enemy.name, gold_reward, loot_items)
            print(f"Останки {enemy.name} можно обыскать [E]")
        else:
            # Даже без лута добавляем останки (но с 0 золота)
            self.current_dungeon.add_remains(enemy.x, enemy.y, enemy.name, 0, [])
            print(f"Останки {enemy.name} (без лута)")

        # Помечаем NPC как агрессивного к игроку (для других NPC)
        enemy._aggro_target = player

    def enemy_turn(self, player) -> List[dict]:
        """
        Ход врагов - они атакуют игрока если рядом

        Args:
            player: Игрок

        Returns:
            List[dict]: Список результатов атак врагов
        """
        results = []

        if not self.is_in_dungeon or not self.current_dungeon:
            return results

        dungeon = self.current_dungeon

        # Уменьшаем cooldown умений игрока после каждого хода (один раз за ход, а не за каждого врага)
        if hasattr(player, 'skill_manager'):
            player.skill_manager.tick_cooldowns()

        # Обрабатываем действия всех врагов
        for npc in dungeon.npcs:
            if not npc.is_alive:
                continue

            # Проверяем, является ли NPC враждебным
            # NPC враждебен если: dungeon_hostile=True ИЛИ был спровоцирован игроком
            is_hostile = getattr(npc, 'dungeon_hostile', True)  # По умолчанию True для обратной совместимости
            is_provoked = hasattr(npc, '_aggro_target') and npc._aggro_target == player

            # Нейтральные NPC не атакуют и не преследуют (если не спровоцированы)
            if not is_hostile and not is_provoked:
                continue

            # Расстояние до игрока (чебышевская метрика для 8 направлений)
            dist = max(abs(npc.x - player.x), abs(npc.y - player.y))

            # NPC атакует если рядом (дистанция 1)
            if dist == 1:
                # Проверяем режим бессмертия игрока
                if getattr(player, 'godmode', False):
                    # В режиме бессмертия урон не наносится
                    results.append({
                        "attacker": npc.name,
                        "damage": 0,
                        "player_hp": player.health,
                        "blocked_by_godmode": True
                    })
                    # Помечаем NPC как агрессивного
                    npc._aggro_target = player
                    continue

                # Атакуем игрока
                attack_damage = npc.get_total_damage()
                defense = player.get_total_defense()
                final_damage = max(1, attack_damage - defense // 2)

                player.health -= final_damage
                if player.health < 0:
                    player.health = 0

                results.append({
                    "attacker": npc.name,
                    "damage": final_damage,
                    "player_hp": player.health
                })

                # Помечаем NPC как агрессивного
                npc._aggro_target = player
            elif dist > 1:
                # Проверяем линию видимости для преследования
                has_los = dungeon.has_line_of_sight(npc.x, npc.y, player.x, player.y)

                # Получаем радиус обнаружения NPC (используем detection_range_player если есть)
                detection_range = getattr(npc, 'detection_range_player', 5)

                # Если NPC агрессивен (был атакован или атаковал), преследует игрока (но только если видит)
                if is_provoked:
                    if has_los:
                        self._move_enemy_towards_player(npc, player)
                elif is_hostile and dist <= detection_range and has_los:
                    # Враждебный NPC - движется к игроку если в радиусе обнаружения И видит игрока
                    self._move_enemy_towards_player(npc, player)
                    # Помечаем NPC как агрессивного при первом обнаружении
                    npc._aggro_target = player

        return results

    def _move_enemy_towards_player(self, npc, player):
        """Двигаем врага к игроку (по 8 направлениям)"""
        if not self.current_dungeon:
            return

        dungeon = self.current_dungeon

        # Вычисляем направление к игроку
        dx = 0
        dy = 0

        if player.x > npc.x:
            dx = 1
        elif player.x < npc.x:
            dx = -1

        if player.y > npc.y:
            dy = 1
        elif player.y < npc.y:
            dy = -1

        new_x = npc.x + dx
        new_y = npc.y + dy

        # Не двигаемся на клетку игрока (предотвращение слипания)
        if new_x == player.x and new_y == player.y:
            return

        # Сохраняем старые координаты для проверки движения
        old_x = npc.x
        old_y = npc.y

        # Проверяем можно ли туда пойти
        if dungeon.is_passable(new_x, new_y):
            # Проверяем нет ли там другого NPC
            other_npc = dungeon.get_npc_at(new_x, new_y)
            if other_npc is None or not other_npc.is_alive:
                npc.x = new_x
                npc.y = new_y
                return

        # Если диагональный путь заблокирован, пробуем по одной оси
        if dx != 0 and dy != 0:
            # Пробуем только по X
            if player.x != npc.x + dx:  # Не на клетку игрока
                if dungeon.is_passable(npc.x + dx, npc.y):
                    other = dungeon.get_npc_at(npc.x + dx, npc.y)
                    if other is None or not other.is_alive:
                        npc.x += dx
                        return
            # Пробуем только по Y
            if player.y != npc.y + dy:  # Не на клетку игрока
                if dungeon.is_passable(npc.x, npc.y + dy):
                    other = dungeon.get_npc_at(npc.x, npc.y + dy)
                    if other is None or not other.is_alive:
                        npc.y += dy

    def get_target_info(self) -> Optional[dict]:
        """
        Получить информацию о выбранной цели

        Returns:
            dict или None: Информация о цели
        """
        if self.selected_target is None:
            return None

        target = self.selected_target

        # Проверяем, что цель жива
        if not getattr(target, 'is_alive', False):
            self.deselect_target()  # Снимаем выделение с мертвого врага
            return None

        # Проверяем видимость цели
        if self.current_dungeon:
            tile = self.current_dungeon.get_tile(target.x, target.y)
            if not tile or not tile.visible:
                # Цель не видна - снимаем выделение
                self.deselect_target()
                return None

        return {
            "name": getattr(target, 'name', 'Враг'),
            "level": getattr(target, 'level', 1),
            "hp": getattr(target, 'health', 0),  # Используем health, а не hp
            "max_hp": getattr(target, 'max_health', 1),  # Используем max_health, а не max_hp
            "attack": getattr(target, 'strength', 5),  # Используем strength как атаку
            "defense": getattr(target, 'constitution', 0),  # Используем constitution как защиту
            "npc_type": getattr(target, 'npc_type', 'undead'),
            "x": target.x,
            "y": target.y
        }

    # ===== Система интерактивных объектов =====

    def get_nearest_interactive_object(self, player_x: int, player_y: int,
                                        max_distance: int = 5) -> Optional[Tuple]:
        """
        Найти ближайший интерактивный объект (ловушку или тайник)

        Args:
            player_x: Координата X игрока
            player_y: Координата Y игрока
            max_distance: Максимальная дистанция поиска

        Returns:
            Tuple[object, str] или None: (объект, тип) где тип = 'trap' или 'stash'
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        dungeon = self.current_dungeon
        nearest_obj = None
        nearest_type = None
        nearest_distance = max_distance + 1

        # Проверяем ловушки
        for trap in dungeon.trap_manager.traps:
            # Пропускаем сработавшие или обезвреженные ловушки
            if trap.is_triggered or trap.is_disarmed:
                continue

            # Проверяем, обнаружена ли ловушка
            if not trap.is_detected:
                continue

            # Проверяем видимость клетки
            tile = dungeon.get_tile(trap.x, trap.y)
            if not tile or not tile.visible:
                continue

            distance = abs(trap.x - player_x) + abs(trap.y - player_y)
            if distance <= max_distance and distance < nearest_distance:
                nearest_obj = trap
                nearest_type = 'trap'
                nearest_distance = distance

        # Проверяем тайники
        for stash in dungeon.stash_manager.stashes:
            # Пропускаем обысканные тайники
            if stash.is_looted:
                continue

            # Проверяем, обнаружен ли тайник
            if not stash.is_detected:
                continue

            # Проверяем видимость клетки
            tile = dungeon.get_tile(stash.x, stash.y)
            if not tile or not tile.visible:
                continue

            distance = abs(stash.x - player_x) + abs(stash.y - player_y)
            if distance <= max_distance and distance < nearest_distance:
                nearest_obj = stash
                nearest_type = 'stash'
                nearest_distance = distance

        if nearest_obj:
            return (nearest_obj, nearest_type)
        return None

    def select_object(self, obj, obj_type: str):
        """
        Выбрать интерактивный объект

        Args:
            obj: Объект (Trap или Stash)
            obj_type: Тип объекта ('trap' или 'stash')
        """
        self.selected_object = obj
        self.selected_object_type = obj_type

    def deselect_object(self):
        """Снять выделение с интерактивного объекта"""
        self.selected_object = None
        self.selected_object_type = None

    def get_selected_object_info(self) -> Optional[dict]:
        """
        Получить информацию о выбранном интерактивном объекте

        Returns:
            dict или None: Информация об объекте
        """
        if self.selected_object is None:
            return None

        obj = self.selected_object
        obj_type = self.selected_object_type

        if obj_type == 'trap':
            return {
                "type": "trap",
                "name": obj.name,
                "level": obj.level_name,
                "trap_type": obj.trap_type.value,
                "is_detected": obj.is_detected,
                "is_disarmed": obj.is_disarmed,
                "is_triggered": obj.is_triggered,
                "x": obj.x,
                "y": obj.y
            }
        elif obj_type == 'stash':
            return {
                "type": "stash",
                "name": obj.name,
                "level": obj.level_name,
                "stash_type": obj.stash_type.value,
                "is_detected": obj.is_detected,
                "is_looted": obj.is_looted,
                "has_trap": obj.has_trap,
                "x": obj.x,
                "y": obj.y
            }

        return None

    # ===== Система взаимодействия с рудой =====

    def select_ore(self, tile):
        """
        Выбрать объект руды

        Args:
            tile: DungeonTile с ore_data
        """
        self.selected_ore = tile

    def deselect_ore(self):
        """Снять выделение с объекта руды"""
        self.selected_ore = None

    def deplete_ore(self, tile):
        """
        Истощить объект руды (после добычи)

        Args:
            tile: DungeonTile с ore_data для истощения
        """
        if not tile or not self.current_dungeon:
            return

        # Меняем тип тайла на обычный пол/коридор
        # Руда была непроходимой, теперь становится проходимой
        tile.tile_type = DungeonTileType.FLOOR
        tile.ore_data = None

        # Снимаем выделение с этого объекта
        if self.selected_ore == tile:
            self.selected_ore = None

    def get_ore_at_screen_pos(self, player, screen_x: int, screen_y: int, tile_size: int):
        """
        Получить объект руды по позиции на экране

        Args:
            player: Игрок
            screen_x, screen_y: Позиция на экране
            tile_size: Размер тайла

        Returns:
            DungeonTile или None: Тайл с рудой или None
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        dungeon = self.current_dungeon
        screen_width = self.game.window_width
        screen_height = self.game.window_height

        # Вычисляем центр экрана в тайлах (аналогично renderer.py с +2)
        tiles_x = screen_width // tile_size + 2
        tiles_y = screen_height // tile_size + 2
        start_x = player.x - tiles_x // 2
        start_y = player.y - tiles_y // 2

        # Переводим экранные координаты в координаты карты
        tile_x = start_x + screen_x // tile_size
        tile_y = start_y + screen_y // tile_size

        # Получаем тайл
        tile = dungeon.get_tile(tile_x, tile_y)
        if not tile:
            return None

        # Проверяем, что это объект руды и он видим
        if tile.tile_type == DungeonTileType.ORE and tile.ore_data and tile.visible:
            return tile

        return None

    def get_selected_ore_info(self) -> Optional[dict]:
        """
        Получить информацию о выбранном объекте руды

        Returns:
            dict или None: Информация о руде
        """
        if self.selected_ore is None:
            return None

        tile = self.selected_ore
        ore_data = tile.ore_data

        if not ore_data:
            return None

        # Названия типов руды
        ore_names = {
            "copper": "Медная руда",
            "iron": "Железная руда",
            "silver": "Серебряная руда",
            "gold": "Золотая руда",
            "mithril": "Мифриловая руда"
        }

        # Минимальный ранг для добычи
        ore_rank_requirements = {
            "copper": 1,
            "iron": 2,
            "silver": 3,
            "gold": 4,
            "mithril": 5
        }

        resource_type = ore_data.get('resource_type', 'unknown')

        return {
            "type": "ore",
            "name": ore_names.get(resource_type, "Неизвестная руда"),
            "resource_type": resource_type,
            "required_rank": ore_rank_requirements.get(resource_type, 99),
            "x": tile.x,
            "y": tile.y
        }

