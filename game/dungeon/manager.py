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

        # NPC для подземелий
        self.dungeon_npcs: List = []

        # Система боя в подземелье
        self.selected_target = None  # Выбранный враг
        self.target_index = 0  # Индекс для циклического выбора

        # Режим выбора цели для умения
        self.skill_targeting_mode = False
        self.pending_skill = None  # Умение, ожидающее выбора цели

        # Smart Target система для объектов подземелья
        self.selected_object = None  # Выбранный объект (ловушка или тайник)
        self.selected_object_type = None  # Тип объекта: 'trap' или 'stash'

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
            tile = self.game.game_map.get_tile(player.x, player.y)
            location_type = "mine" if dungeon_type == "mine" else "ruins"

            self.current_dungeon = self.generator.generate_dungeon_for_location(
                location_type, location_name, player.x, player.y,
                current_depth=1, max_depth=self.max_depth
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

            self.current_dungeon = self.generator.generate_dungeon_for_location(
                location_type, location_name, self.saved_world_x, self.saved_world_y,
                current_depth=self.current_depth, max_depth=self.max_depth
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
        """Генерация NPC для текущего подземелья"""
        if not self.current_dungeon:
            return

        self.dungeon_npcs.clear()
        dungeon = self.current_dungeon

        # Количество NPC зависит от уровня подземелья
        base_count = 3 + dungeon.dungeon_level
        num_npcs = random.randint(base_count, base_count + 5)

        # Импортируем класс нежити
        from game.npc.hostile import Undead

        for _ in range(num_npcs):
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

            # Создаем нежить
            level = random.randint(
                max(1, dungeon.dungeon_level - 1),
                dungeon.dungeon_level + 3
            )

            npc_names = [
                "Скелет", "Зомби", "Призрак", "Вурдалак", "Умертвие",
                "Костяной воин", "Гуль", "Дух тьмы", "Тень", "Мертвец"
            ]
            name = f"{random.choice(npc_names)} (Ур. {level})"

            # Нежить привязана к своей начальной позиции спавна (не к входу)
            undead = Undead(name, x, y, level, x, y)

            # Уменьшаем радиус патрулирования для подземелий
            undead.patrol_radius = 10
            undead.max_distance_from_ruins = 15

            self.dungeon_npcs.append(undead)
            dungeon.add_npc(undead)

    def update_dungeon(self, player):
        """
        Обновление состояния подземелья

        Args:
            player: Объект игрока
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return

        dungeon = self.current_dungeon

        # Проверяем ловушки
        trap_result = dungeon.trap_manager.check_player_position(player)
        if trap_result:
            # Обновляем тип клетки
            dungeon.set_tile_type(player.x, player.y, DungeonTileType.TRAP_TRIGGERED)
            print(trap_result["message"])
            # Проверяем смерть от ловушки
            if trap_result.get("player_dead"):
                return {"player_dead": True}

        # Пытаемся обнаружить ловушки и тайники поблизости
        detected_traps = dungeon.trap_manager.try_detect_nearby(player, radius=2)
        for trap in detected_traps:
            print(f"Вы заметили {trap.name}!")
            dungeon.set_tile_type(trap.x, trap.y, DungeonTileType.TRAP)

        detected_stashes = dungeon.stash_manager.try_detect_nearby(player, radius=2)
        for stash in detected_stashes:
            print(f"Вы заметили {stash.name}!")
            dungeon.set_tile_type(stash.x, stash.y, DungeonTileType.STASH)

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
                    messages.append(f"  Золото: {loot_result['gold']}")
                for item_name, quantity in loot_result['items']:
                    messages.append(f"  {item_name} x{quantity}")
                return {
                    "type": "remains",
                    "success": True,
                    "message": "\n".join(messages)
                }

        # Проверяем тайник
        stash = dungeon.stash_manager.get_stash_at(player.x, player.y)
        if stash and stash.is_detected and not stash.is_looted:
            result = stash.loot(player)
            if result["success"]:
                dungeon.set_tile_type(player.x, player.y, DungeonTileType.STASH_LOOTED)

                # Добавляем предметы в инвентарь
                for item_name, item_id, quantity in result["items"]:
                    try:
                        from game.item_registry import get_item
                        item = get_item(item_id)
                        if item:
                            player.inventory.add_item(item, quantity)
                    except Exception:
                        pass  # Предмет не найден в реестре

            return result

        # Проверяем выход
        if dungeon.is_exit_tile(player.x, player.y):
            return {
                "type": "exit",
                "message": "Нажмите E чтобы покинуть подземелье"
            }

        return None

    def try_disarm_trap(self, player, direction: Tuple[int, int] = (0, 0)) -> Optional[dict]:
        """
        Попытка обезвредить ловушку

        Args:
            player: Объект игрока
            direction: Направление (dx, dy) или (0, 0) для текущей клетки

        Returns:
            dict или None: Результат
        """
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        dungeon = self.current_dungeon
        target_x = player.x + direction[0]
        target_y = player.y + direction[1]

        trap = dungeon.trap_manager.get_trap_at(target_x, target_y)
        if trap and trap.is_detected and not trap.is_triggered and not trap.is_disarmed:
            success, message = trap.try_disarm(player)
            if success:
                # Меняем тип клетки на сработавшую (обезвреженная = деактивированная)
                dungeon.set_tile_type(target_x, target_y, DungeonTileType.TRAP_TRIGGERED)
            return {"success": success, "message": message}

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

        # Проверяем ловушки
        trap = dungeon.trap_manager.get_trap_at(new_x, new_y)
        if trap and not trap.is_triggered and not trap.is_disarmed:
            # Если ловушка не обнаружена - срабатывает автоматически
            if not trap.is_detected:
                trap_result = trap.trigger(player)
                dungeon.set_tile_type(new_x, new_y, DungeonTileType.TRAP_TRIGGERED)
                result["trap"] = trap_result
                result["message"] = trap_result.get("message", "Ловушка!")
            else:
                # Обнаруженная ловушка - игрок может пройти мимо, но видит предупреждение
                # Чтобы обезвредить, нужно стоять рядом и нажать R
                result["message"] = "Осторожно! Ловушка! Обезвредьте её с соседней клетки (подойдите и нажмите R)."

        # Проверяем тайники (автообнаружение)
        stash = dungeon.stash_manager.get_stash_at(new_x, new_y)
        if stash and not stash.is_detected:
            stash.detect()
            result["stash_found"] = True
            result["message"] = "Вы обнаружили тайник! Нажмите E чтобы обыскать."

        # Проверяем останки
        remains = dungeon.get_remains_at(new_x, new_y)
        if remains and not remains.get('looted', False):
            result["remains_found"] = True
            if not result["message"]:
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
                if hasattr(npc, '_aggro_target') and npc._aggro_target == player:
                    if has_los:
                        self._move_enemy_towards_player(npc, player)
                elif dist <= detection_range and has_los:
                    # Обычное поведение - движение к игроку если в радиусе обнаружения И видит игрока
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
                # Проверяем ловушки после движения
                self._check_npc_trap(npc, dungeon)
                return

        # Если диагональный путь заблокирован, пробуем по одной оси
        if dx != 0 and dy != 0:
            # Пробуем только по X
            if player.x != npc.x + dx:  # Не на клетку игрока
                if dungeon.is_passable(npc.x + dx, npc.y):
                    other = dungeon.get_npc_at(npc.x + dx, npc.y)
                    if other is None or not other.is_alive:
                        npc.x += dx
                        # Проверяем ловушки после движения
                        self._check_npc_trap(npc, dungeon)
                        return
            # Пробуем только по Y
            if player.y != npc.y + dy:  # Не на клетку игрока
                if dungeon.is_passable(npc.x, npc.y + dy):
                    other = dungeon.get_npc_at(npc.x, npc.y + dy)
                    if other is None or not other.is_alive:
                        npc.y += dy
                        # Проверяем ловушки после движения
                        self._check_npc_trap(npc, dungeon)

    def _check_npc_trap(self, npc, dungeon):
        """
        Проверить, наступил ли NPC на ловушку

        Args:
            npc: NPC
            dungeon: Подземелье
        """
        trap = dungeon.trap_manager.get_trap_at(npc.x, npc.y)
        if trap and not trap.is_triggered and not trap.is_disarmed:
            # NPC наступает на ловушку
            trap_result = trap.trigger(npc)
            if trap_result.get("success"):
                # Обновляем тип клетки
                dungeon.set_tile_type(npc.x, npc.y, DungeonTileType.TRAP_TRIGGERED)
                # Выводим сообщение о срабатывании ловушки
                print(trap_result.get("message", ""))

                # Если NPC убит ловушкой, создаем останки
                if trap_result.get("target_dead") and not npc.is_alive:
                    # Используем полноценную систему лута
                    from game.loot_system import LootSystem

                    # Получаем игрока из game для генерации лута
                    player = self.game.player if hasattr(self, 'game') and hasattr(self.game, 'player') else None

                    if player:
                        loot_system = LootSystem(player)
                        loot_items, gold_reward = loot_system.generate_loot(npc)
                    else:
                        loot_items, gold_reward = [], 0

                    # Добавляем останки
                    dungeon.add_remains(npc.x, npc.y, npc.name, gold_reward, loot_items)

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

    # ====================
    # Smart Target система для объектов подземелья
    # ====================

    def get_nearest_interactive_object(self, player_x: int, player_y: int, max_distance: int = 5) -> Optional[Tuple[any, str]]:
        """
        Найти ближайший интерактивный объект (ловушку или тайник)

        Args:
            player_x: Координата X игрока
            player_y: Координата Y игрока
            max_distance: Максимальное расстояние поиска

        Returns:
            Tuple[object, str] или None: (объект, тип) где тип 'trap' или 'stash'
        """
        if not self.current_dungeon:
            return None

        nearest_obj = None
        nearest_type = None
        min_distance = float('inf')

        # Ищем ближайшую обнаруженную ловушку
        for trap in self.current_dungeon.trap_manager.traps:
            if trap.is_detected and not trap.is_triggered:
                # Проверяем видимость
                tile = self.current_dungeon.get_tile(trap.x, trap.y)
                if tile and tile.visible:
                    distance = abs(trap.x - player_x) + abs(trap.y - player_y)
                    if distance <= max_distance and distance < min_distance:
                        min_distance = distance
                        nearest_obj = trap
                        nearest_type = 'trap'

        # Ищем ближайший обнаруженный тайник
        for stash in self.current_dungeon.stash_manager.stashes:
            if stash.is_detected and not stash.is_looted:
                # Проверяем видимость
                tile = self.current_dungeon.get_tile(stash.x, stash.y)
                if tile and tile.visible:
                    distance = abs(stash.x - player_x) + abs(stash.y - player_y)
                    if distance <= max_distance and distance < min_distance:
                        min_distance = distance
                        nearest_obj = stash
                        nearest_type = 'stash'

        if nearest_obj:
            return (nearest_obj, nearest_type)
        return None

    def select_object(self, obj, obj_type: str):
        """
        Выбрать объект подземелья

        Args:
            obj: Объект (ловушка или тайник)
            obj_type: Тип объекта ('trap' или 'stash')
        """
        self.selected_object = obj
        self.selected_object_type = obj_type
        # Снимаем выделение с NPC при выборе объекта
        if self.selected_target:
            self.selected_target = None

    def deselect_object(self):
        """Снять выделение с объекта"""
        self.selected_object = None
        self.selected_object_type = None

    def get_object_at_screen_pos(self, player, screen_x: int, screen_y: int, tile_size: int) -> Optional[Tuple[any, str]]:
        """
        Получить объект подземелья по позиции на экране

        Args:
            player: Объект игрока
            screen_x: Экранная координата X (пиксели)
            screen_y: Экранная координата Y (пиксели)
            tile_size: Размер тайла в пикселях

        Returns:
            Tuple[object, str] или None: (объект, тип) где тип 'trap' или 'stash'
        """
        if not self.current_dungeon:
            return None

        # Вычисляем количество видимых тайлов
        tiles_x = (screen_x // tile_size) + 2
        tiles_y = (screen_y // tile_size) + 2

        # Начальная позиция отрисовки (центрируем на игроке)
        start_x = player.x - tiles_x // 2
        start_y = player.y - tiles_y // 2

        # Вычисляем координаты клетки по позиции мыши
        tile_screen_x = screen_x // tile_size
        tile_screen_y = screen_y // tile_size

        map_x = start_x + tile_screen_x
        map_y = start_y + tile_screen_y

        # Проверяем видимость клетки
        tile = self.current_dungeon.get_tile(map_x, map_y)
        if not tile or not tile.visible:
            return None

        # Ищем ловушку на этой позиции
        for trap in self.current_dungeon.trap_manager.traps:
            if trap.x == map_x and trap.y == map_y:
                # Можно выбрать только обнаруженную, не сработавшую и не обезвреженную ловушку
                if trap.is_detected and not trap.is_triggered and not trap.is_disarmed:
                    return (trap, 'trap')

        # Ищем тайник на этой позиции
        for stash in self.current_dungeon.stash_manager.stashes:
            if stash.x == map_x and stash.y == map_y:
                if stash.is_detected and not stash.is_looted:
                    return (stash, 'stash')

        return None

    def get_object_info(self) -> Optional[dict]:
        """
        Получить информацию о выбранном объекте

        Returns:
            dict или None: Информация об объекте
        """
        if not self.selected_object or not self.selected_object_type:
            return None

        obj = self.selected_object

        # Проверяем видимость объекта
        if self.current_dungeon:
            tile = self.current_dungeon.get_tile(obj.x, obj.y)
            if not tile or not tile.visible:
                # Объект не виден - снимаем выделение
                self.deselect_object()
                return None

        if self.selected_object_type == 'trap':
            # Проверяем, не сработала ли ловушка
            if obj.is_triggered:
                self.deselect_object()
                return None

            return {
                "type": "trap",
                "name": obj.trap_type.value.replace('_', ' ').title(),
                "level": obj.trap_level.value,
                "level_name": obj.trap_level.name,
                "detected": obj.is_detected,
                "dc": obj.disarm_dc,  # DC для обезвреживания
                "x": obj.x,
                "y": obj.y
            }
        elif self.selected_object_type == 'stash':
            # Проверяем, не разграблен ли тайник
            if obj.is_looted:
                self.deselect_object()
                return None

            return {
                "type": "stash",
                "name": "Тайник",
                "level": obj.stash_level.value,
                "level_name": obj.stash_level.name,
                "detected": obj.is_detected,
                "dc": obj.detection_dc,  # DC для обнаружения
                "has_trap": obj.trap is not None,
                "x": obj.x,
                "y": obj.y
            }

        return None
