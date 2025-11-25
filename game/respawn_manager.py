"""
Система автоматического респавна NPC
"""
import random
from game.npc import (Guard, Merchant, MagicMerchant, MagePatrol, Bandit, Miner, Undead)
from game.npc.animal import Wolf, Bear, Deer
from game.npc.unique import Alchemist, Hunter, Necromancer
from game.constants import (
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_BANDIT_CAMP,
    LOCATION_MINE, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL
)


class RespawnManager:
    """Менеджер автоматического респавна NPC"""

    def __init__(self, game_map):
        """
        Инициализация менеджера респавна

        Args:
            game_map: Игровая карта
        """
        self.game_map = game_map
        # Очередь респавна: [(npc_data, turns_remaining), ...]
        self.respawn_queue = []
        # Фиксированное время респавна (в игровых часах) - сокращено для динамичного геймплея
        self.respawn_time = 2
        # Счетчик успешных респавнов
        self.total_respawns = 0

    def register_death(self, npc, game=None):
        """
        Зарегистрировать смерть NPC для последующего респавна

        Args:
            npc: Умерший NPC
            game: Объект игры (для удаления NPC из списков)
        """
        # Удаляем мертвого NPC из списков игры
        if game and hasattr(game, 'npc_manager'):
            self._remove_dead_npc_from_manager(npc, game.npc_manager)

        # Сохраняем данные для респавна
        respawn_data = {
            'npc_type': npc.npc_type,
            'name_base': self._extract_name_base(npc.name),
            'level_range': self._get_level_range(npc),
            'spawn_location': self._get_spawn_location(npc),
            'npc_class': type(npc).__name__
        }

        # Фиксированное время респавна
        self.respawn_queue.append((respawn_data, self.respawn_time))
        print(f"[РЕСПАВН] {npc.name} ({respawn_data['npc_class']}) зарегистрирован для респавна через {self.respawn_time} часов")
        print(f"[РЕСПАВН] Всего в очереди: {len(self.respawn_queue)} NPC")

    def _remove_dead_npc_from_manager(self, npc, npc_manager):
        """
        Удалить мертвого NPC из менеджера NPC

        Args:
            npc: Мертвый NPC для удаления
            npc_manager: Менеджер NPC
        """
        from game.core.npc_manager import NPCType

        # Определяем тип NPC по классу
        npc_class = type(npc).__name__
        npc_type_map = {
            'Guard': NPCType.GUARD,
            'Merchant': NPCType.MERCHANT,
            'MagicMerchant': NPCType.MERCHANT,
            'MagePatrol': NPCType.MAGE,
            'Bandit': NPCType.BANDIT,
            'Miner': NPCType.MINER,
            'Undead': NPCType.UNDEAD,
            'Alchemist': NPCType.ALCHEMIST,
            'Hunter': NPCType.HUNTER,
            'Necromancer': NPCType.NECROMANCER,
            'Wolf': NPCType.ANIMAL,
            'Bear': NPCType.ANIMAL,
            'Deer': NPCType.ANIMAL,
        }

        npc_type = npc_type_map.get(npc_class)
        if npc_type:
            removed = npc_manager.remove_npc(npc, npc_type)
            if removed:
                print(f"[Респавн] {npc.name} удален из списков NPC")
            else:
                print(f"[Респавн] Предупреждение: {npc.name} не найден в списках для удаления")

    def _extract_name_base(self, full_name):
        """
        Извлечь базовое имя NPC без названия локации

        Args:
            full_name: Полное имя NPC

        Returns:
            str: Базовое имя
        """
        # Имена обычно в формате "Тип Название_локации"
        parts = full_name.split()
        if len(parts) >= 1:
            return parts[0]  # Возвращаем первое слово (тип)
        return full_name

    def _get_level_range(self, npc):
        """
        Получить диапазон уровней для респавна на основе уровня NPC

        Args:
            npc: NPC для анализа

        Returns:
            tuple: (min_level, max_level)
        """
        level = npc.level
        # Респавним с небольшой вариацией уровня
        min_level = max(1, level - 2)
        max_level = level + 2
        return (min_level, max_level)

    def _get_spawn_location(self, npc):
        """
        Получить место спавна для NPC

        Args:
            npc: NPC для анализа

        Returns:
            tuple: (x, y, location_type) или None
        """
        npc_class = type(npc).__name__

        if npc_class == 'Bandit':
            # Бандиты привязаны к лагерю
            return (npc.camp_x, npc.camp_y, LOCATION_BANDIT_CAMP)
        elif npc_class == 'Undead':
            # Нежить привязана к руинам
            return (npc.ruins_x, npc.ruins_y, LOCATION_RUINS)
        elif npc_class == 'Miner':
            # Шахтеры привязаны к шахте
            if hasattr(npc, 'mine_x'):
                return (npc.mine_x, npc.mine_y, LOCATION_MINE)
        elif npc_class == 'MagePatrol':
            # Маги привязаны к академии
            if hasattr(npc, 'academy_x'):
                return (npc.academy_x, npc.academy_y, LOCATION_MAGIC_SCHOOL)
        elif npc_class == 'Guard':
            # Стражники патрулируют, используем начальную позицию маршрута
            if hasattr(npc, 'patrol_route') and npc.patrol_route and len(npc.patrol_route) > 0:
                route = npc.patrol_route
                center_x = sum(p[0] for p in route) // len(route)
                center_y = sum(p[1] for p in route) // len(route)
                return (center_x, center_y, LOCATION_CITY)
        elif npc_class in ['Wolf', 'Bear', 'Deer']:
            # Животные привязаны к точке спавна
            if hasattr(npc, 'spawn_x') and hasattr(npc, 'spawn_y'):
                return (npc.spawn_x, npc.spawn_y, None)
        elif npc_class == 'Hunter':
            # Охотники привязаны к дому
            if hasattr(npc, 'home_x') and hasattr(npc, 'home_y'):
                return (npc.home_x, npc.home_y, None)
        elif npc_class == 'Necromancer':
            # Некроманты привязаны к руинам
            if hasattr(npc, 'ruins_x') and hasattr(npc, 'ruins_y'):
                return (npc.ruins_x, npc.ruins_y, LOCATION_RUINS)
        elif npc_class == 'Alchemist':
            # Алхимики стационарны
            return (npc.x, npc.y, None)

        # Для остальных NPC используем их текущую позицию
        return (npc.x, npc.y, None)

    def update(self, hours=1):
        """
        Обновить таймеры респавна

        Args:
            hours: Количество прошедших игровых часов

        Returns:
            list: Список данных для респавна NPC, у которых истекло время
        """
        ready_to_respawn = []
        remaining_queue = []

        for respawn_data, turns_remaining in self.respawn_queue:
            turns_remaining -= hours

            if turns_remaining <= 0:
                # NPC готов к респавну
                ready_to_respawn.append(respawn_data)
                print(f"[РЕСПАВН] {respawn_data['npc_class']} готов к респавну!")
            else:
                # Еще не время
                remaining_queue.append((respawn_data, turns_remaining))

        self.respawn_queue = remaining_queue

        if ready_to_respawn:
            print(f"\n{'='*60}")
            print(f"[РЕСПАВН] Готовы к респавну {len(ready_to_respawn)} NPC")
            print(f"[РЕСПАВН] В очереди осталось: {len(self.respawn_queue)} NPC")
            print(f"{'='*60}\n")

        return ready_to_respawn

    def respawn_npc(self, respawn_data, game):
        """
        Выполнить респавн NPC

        Args:
            respawn_data: Данные для респавна
            game: Объект игры

        Returns:
            NPC или None: Созданный NPC или None при ошибке
        """
        spawn_location = respawn_data['spawn_location']
        if not spawn_location:
            return None

        spawn_x, spawn_y, location_type = spawn_location

        # Находим позицию для спавна рядом с локацией
        spawn_pos = self._find_spawn_position(spawn_x, spawn_y)
        if not spawn_pos:
            return None

        x, y = spawn_pos

        level_range = respawn_data['level_range']
        level = random.randint(level_range[0], level_range[1])
        npc_class = respawn_data['npc_class']
        name_base = respawn_data['name_base']

        # Получаем имя локации для полного имени NPC
        location_name = self._get_location_name(spawn_x, spawn_y)

        # Создаем NPC соответствующего типа
        new_npc = None

        if npc_class == 'Bandit':
            bandit_names = [
                "Бандит", "Разбойник", "Головорез", "Грабитель",
                "Налетчик", "Лихой человек", "Бандюган", "Воришка"
            ]
            name = f"{random.choice(bandit_names)} {location_name}"
            new_npc = Bandit(name, x, y, level, spawn_x, spawn_y)
            # Используем npc_manager для правильного добавления NPC с инвалидацией кэша
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.BANDIT)

        elif npc_class == 'Undead':
            undead_names = [
                "Зомби", "Скелет", "Мертвец", "Призрак",
                "Нежить", "Упырь", "Костяк", "Тень"
            ]
            name = f"{random.choice(undead_names)} {location_name}"
            new_npc = Undead(name, x, y, level, spawn_x, spawn_y)
            # Используем npc_manager для правильного добавления NPC с инвалидацией кэша
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.UNDEAD)

        elif npc_class == 'Miner':
            miner_names = ["Шахтер", "Рудокоп", "Горняк", "Копатель"]
            name = f"{random.choice(miner_names)} {location_name}"
            new_npc = Miner(name, x, y, level, spawn_x, spawn_y)
            # Используем npc_manager для правильного добавления NPC с инвалидацией кэша
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.MINER)

        elif npc_class == 'Guard':
            name = f"Стражник {location_name}"
            new_npc = Guard(name, x, y, level)
            # Создаем маршрут патрулирования
            patrol_route = self._create_patrol_route(x, y, radius=5)
            new_npc.set_patrol_route(patrol_route)
            # Используем npc_manager для правильного добавления NPC с инвалидацией кэша
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.GUARD)

        elif npc_class == 'MagePatrol':
            mage_names = [
                "Адепт", "Чародей", "Волшебник", "Маг",
                "Заклинатель", "Колдун", "Ученик мага", "Магистр"
            ]
            name = f"{random.choice(mage_names)} {location_name}"
            new_npc = MagePatrol(name, x, y, level, spawn_x, spawn_y)
            # Используем npc_manager для правильного добавления NPC с инвалидацией кэша
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.MAGE)

        elif npc_class == 'Wolf':
            wolf_names = ["Волк", "Серый волк", "Лесной волк", "Степной волк"]
            name = f"{random.choice(wolf_names)} {location_name}"
            # Волки могут патрулировать или странствовать
            behavior_mode = random.choice(["patrol", "wander"])
            new_npc = Wolf(name, x, y, level, spawn_x, spawn_y, behavior_mode)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.ANIMAL)

        elif npc_class == 'Bear':
            bear_names = ["Медведь", "Бурый медведь", "Лесной медведь", "Горный медведь"]
            name = f"{random.choice(bear_names)} {location_name}"
            # Медведи обычно патрулируют территорию
            behavior_mode = random.choice(["patrol", "wander"])
            new_npc = Bear(name, x, y, level, spawn_x, spawn_y, behavior_mode)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.ANIMAL)

        elif npc_class == 'Deer':
            deer_names = ["Олень", "Благородный олень", "Лесной олень", "Пятнистый олень"]
            name = f"{random.choice(deer_names)} {location_name}"
            # Олени обычно странствуют
            behavior_mode = random.choice(["patrol", "wander"])
            new_npc = Deer(name, x, y, level, spawn_x, spawn_y, behavior_mode)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.ANIMAL)

        elif npc_class == 'Alchemist':
            name = f"Алхимик {location_name}"
            new_npc = Alchemist(name, x, y, level)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.ALCHEMIST)

        elif npc_class == 'Hunter':
            hunter_names = ["Охотник", "Следопыт", "Егерь", "Ловчий"]
            name = f"{random.choice(hunter_names)} {location_name}"
            new_npc = Hunter(name, x, y, level, spawn_x, spawn_y)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.HUNTER)

        elif npc_class == 'Necromancer':
            necromancer_names = ["Некромант", "Темный маг", "Повелитель мертвых", "Некромант-отступник"]
            name = f"{random.choice(necromancer_names)} {location_name}"
            new_npc = Necromancer(name, x, y, level, spawn_x, spawn_y)
            from game.core.npc_manager import NPCType
            game.npc_manager.add_npc(new_npc, NPCType.NECROMANCER)

        if new_npc:
            self.total_respawns += 1
            print(f"[РЕСПАВН #{self.total_respawns}] {new_npc.name} (Ур. {level}) возродился в {location_name}")

        return new_npc

    def _find_spawn_position(self, center_x, center_y):
        """
        Найти позицию для спавна рядом с центром

        Args:
            center_x: X координата центра
            center_y: Y координата центра

        Returns:
            tuple или None: (x, y) позиция или None
        """
        # Сначала пробуем найти позицию в случайном направлении
        for _ in range(20):
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            x = center_x + offset_x
            y = center_y + offset_y

            if self.game_map.is_valid_position(x, y):
                tile = self.game_map.get_tile(x, y)
                if tile.is_passable():
                    return (x, y)

        # Если не нашли, пробуем систематически
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy

                    if self.game_map.is_valid_position(x, y):
                        tile = self.game_map.get_tile(x, y)
                        if tile.is_passable():
                            return (x, y)

        return None

    def _get_location_name(self, x, y):
        """
        Получить имя ближайшей локации

        Args:
            x: Координата X
            y: Координата Y

        Returns:
            str: Имя локации или пустая строка
        """
        # Ищем ближайшую локацию
        closest_location = None
        closest_distance = float('inf')

        for location in self.game_map.locations:
            distance = abs(location.x - x) + abs(location.y - y)
            if distance < closest_distance:
                closest_distance = distance
                closest_location = location

        if closest_location:
            return closest_location.name

        return ""

    def _create_patrol_route(self, center_x, center_y, radius=5):
        """
        Создать маршрут патрулирования вокруг точки

        Args:
            center_x: X координата центра
            center_y: Y координата центра
            radius: Радиус патрулирования

        Returns:
            list: Список точек маршрута
        """
        route = [
            (center_x + radius, center_y),
            (center_x + radius, center_y + radius),
            (center_x, center_y + radius),
            (center_x - radius, center_y + radius),
            (center_x - radius, center_y),
            (center_x - radius, center_y - radius),
            (center_x, center_y - radius),
            (center_x + radius, center_y - radius),
        ]
        return route

    def get_queue_size(self):
        """
        Получить количество NPC в очереди на респавн

        Returns:
            int: Количество NPC
        """
        return len(self.respawn_queue)

    def get_queue_info(self):
        """
        Получить информацию об очереди респавна

        Returns:
            list: Список (npc_type, turns_remaining)
        """
        return [(data['npc_class'], turns) for data, turns in self.respawn_queue]
