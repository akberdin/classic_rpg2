"""
Менеджер подземелий - управление переходами между картами
"""
import random
from typing import Optional, List, Tuple

from game.dungeon.dungeon_map import DungeonMap
from game.dungeon.generator import DungeonGenerator
from game.dungeon.tiles import DungeonTileType


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

        # NPC для подземелий
        self.dungeon_npcs: List = []

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

        # Проверяем кэш подземелий
        cache_key = (self.saved_world_x, self.saved_world_y)

        if cache_key in self._dungeon_cache:
            # Используем сохраненное подземелье
            self.current_dungeon = self._dungeon_cache[cache_key]
        else:
            # Генерируем новое подземелье
            tile = self.game.game_map.get_tile(player.x, player.y)
            location_type = "mine" if dungeon_type == "mine" else "ruins"

            self.current_dungeon = self.generator.generate_dungeon_for_location(
                location_type, location_name, player.x, player.y
            )

            # Генерируем NPC для подземелья
            self._spawn_dungeon_npcs()

            # Сохраняем в кэш
            self._dungeon_cache[cache_key] = self.current_dungeon

        # Перемещаем игрока на вход подземелья
        if self.current_dungeon.entrance:
            player.x, player.y = self.current_dungeon.entrance
        else:
            # Fallback - в центр карты
            player.x = self.current_dungeon.width // 2
            player.y = self.current_dungeon.height // 2

        self.is_in_dungeon = True

        # Обновляем видимость
        self.current_dungeon.update_visibility(player.x, player.y, 5)

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

            undead = Undead(name, x, y, level, dungeon.entrance[0], dungeon.entrance[1])

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

        # Обновляем видимость
        dungeon.update_visibility(player.x, player.y, 5)

        # Проверяем ловушки
        trap_result = dungeon.trap_manager.check_player_position(player)
        if trap_result:
            # Обновляем тип клетки
            dungeon.set_tile_type(player.x, player.y, DungeonTileType.TRAP_TRIGGERED)
            print(trap_result["message"])

        # Пытаемся обнаружить ловушки и тайники поблизости
        detected_traps = dungeon.trap_manager.try_detect_nearby(player, radius=2)
        for trap in detected_traps:
            print(f"Вы заметили {trap.name}!")
            dungeon.set_tile_type(trap.x, trap.y, DungeonTileType.TRAP)

        detected_stashes = dungeon.stash_manager.try_detect_nearby(player, radius=2)
        for stash in detected_stashes:
            print(f"Вы заметили {stash.name}!")
            dungeon.set_tile_type(stash.x, stash.y, DungeonTileType.STASH)

        # Обновляем AI NPC
        self._update_dungeon_npcs(player)

    def _update_dungeon_npcs(self, player):
        """Обновление AI NPC в подземелье"""
        if not self.current_dungeon:
            return

        # Создаем контекст AI
        from game.core.ai_context import AIContext

        context = AIContext(
            game_map=self.current_dungeon,  # Используем карту подземелья
            all_npcs=self.dungeon_npcs,
            player=player,
            current_hour=self.game.game_time.hour if hasattr(self.game, 'game_time') else 12
        )

        # Обновляем каждого NPC
        for npc in self.dungeon_npcs:
            if npc.is_alive:
                npc.update_ai(context)

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
                # Меняем тип клетки
                dungeon.set_tile_type(target_x, target_y, DungeonTileType.FLOOR)
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

    def get_current_dungeon_info(self) -> Optional[dict]:
        """Получить информацию о текущем подземелье"""
        if not self.is_in_dungeon or not self.current_dungeon:
            return None

        return self.current_dungeon.get_statistics()

    def clear_cache(self):
        """Очистить кэш подземелий"""
        self._dungeon_cache.clear()
