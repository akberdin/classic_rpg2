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

        # NPC для подземелий
        self.dungeon_npcs: List = []

        # Система боя в подземелье
        self.selected_target = None  # Выбранный враг
        self.target_index = 0  # Индекс для циклического выбора

        # Режим выбора цели для умения
        self.skill_targeting_mode = False
        self.pending_skill = None  # Умение, ожидающее выбора цели

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

        # Обновляем видимость (используем увеличенный радиус для подземелий)
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

        # Обновляем видимость (используем увеличенный радиус для подземелий)
        dungeon.update_visibility(player.x, player.y, DUNGEON_VISION_RADIUS)

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

        # Примечание: НЕ обновляем AI NPC здесь, так как enemy_turn() вызывается
        # отдельно после каждого действия игрока (одно действие за ход)

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

        # Вычисляем центр экрана в тайлах
        tiles_x = screen_width // tile_size
        tiles_y = screen_height // tile_size
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
            # Получаем радиус умения
            skill_range = getattr(skill, 'range', 1)
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
        # Опыт
        exp_reward = getattr(enemy, 'exp_reward', 10) * self.current_dungeon.dungeon_level
        player.gain_experience(exp_reward)

        # Шанс дропа
        if hasattr(enemy, 'loot_table') and random.random() < 0.3:
            # Можно добавить дроп предметов
            pass

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

        for npc in dungeon.npcs:
            if not npc.is_alive:
                continue

            # Расстояние до игрока
            dist = abs(npc.x - player.x) + abs(npc.y - player.y)

            if dist <= 1:
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
            elif dist <= 5:
                # Движемся к игроку
                self._move_enemy_towards_player(npc, player)

        return results

    def _move_enemy_towards_player(self, npc, player):
        """Двигаем врага к игроку"""
        if not self.current_dungeon:
            return

        dungeon = self.current_dungeon

        # Простой алгоритм - двигаемся по оси с большей разницей
        dx = 0
        dy = 0

        if abs(player.x - npc.x) > abs(player.y - npc.y):
            dx = 1 if player.x > npc.x else -1
        else:
            dy = 1 if player.y > npc.y else -1

        new_x = npc.x + dx
        new_y = npc.y + dy

        # Проверяем можно ли туда пойти
        if dungeon.is_passable(new_x, new_y):
            # Проверяем нет ли там другого NPC
            other_npc = dungeon.get_npc_at(new_x, new_y)
            if other_npc is None or not other_npc.is_alive:
                npc.x = new_x
                npc.y = new_y

    def get_target_info(self) -> Optional[dict]:
        """
        Получить информацию о выбранной цели

        Returns:
            dict или None: Информация о цели
        """
        if self.selected_target is None:
            return None

        target = self.selected_target
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
