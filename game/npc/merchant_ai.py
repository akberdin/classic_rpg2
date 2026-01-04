"""
Модуль AI логики для торговцев.

Отвечает за:
- Движение по маршрутам (waypoints)
- Обнаружение и избегание угроз
- Отдых в точках маршрута
"""
import random
from game.constants import NPC_RELATIONSHIPS, RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY


class MerchantAI:
    """AI логика для торговцев"""

    @staticmethod
    def update(merchant, game_map, all_npcs=None, current_hour=12):
        """
        Обновление AI торговца за 1 глобальный ход

        Args:
            merchant: Торговец
            game_map: Карта игры
            all_npcs: Список всех NPC
            current_hour: Текущий час суток
        """
        if not merchant.is_alive:
            return

        # Обновляем расписание
        merchant.update_schedule(current_hour, game_map)

        if merchant.is_hidden():
            return

        # Восстанавливаем выносливость
        merchant.recover_stamina(is_active_rest=True)

        # Проверяем обновление ассортимента
        MerchantAI._check_assortment_update(merchant)

        # Проверяем угрозы
        if all_npcs:
            MerchantAI._check_for_threats(merchant, all_npcs)

        # Выполняем действие в зависимости от состояния
        if merchant.state == "flee":
            MerchantAI._flee_step(merchant, game_map)
        elif merchant.state == "travel":
            MerchantAI._travel_step(merchant, game_map)
        elif merchant.state == "rest":
            MerchantAI._rest_at_waypoint(merchant)

    @staticmethod
    def _check_assortment_update(merchant):
        """Проверить необходимость обновления ассортимента"""
        merchant.assortment_update_counter += 1
        if merchant.assortment_update_counter >= merchant.assortment_update:
            merchant.assortment_update_counter = 0
            from game.npc.merchant_goods import MerchantGoodsGenerator
            MerchantGoodsGenerator.generate_goods(merchant)
            print(f"[Торговец] {merchant.name}: ассортимент обновлён")

    @staticmethod
    def _check_for_threats(merchant, all_npcs):
        """Проверить наличие угроз поблизости"""
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            relationship = NPC_RELATIONSHIPS.get(
                (merchant.npc_type, npc.npc_type),
                RELATIONSHIP_NEUTRAL
            )

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(merchant.x - npc.x) + abs(merchant.y - npc.y)

                if distance <= merchant.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        if closest_threat:
            merchant.threat = closest_threat
            merchant.state = "flee"
        elif merchant.state == "flee":
            merchant.threat = None
            merchant.state = "travel"

    @staticmethod
    def _flee_step(merchant, game_map):
        """Один шаг побега от угрозы"""
        if not merchant.threat or not merchant.threat.is_alive:
            merchant.threat = None
            merchant.state = "travel"
            return

        # Убегаем в противоположную сторону
        dx_away = merchant.x - merchant.threat.x
        dy_away = merchant.y - merchant.threat.y

        dx = 1 if dx_away > 0 else (-1 if dx_away < 0 else 0)
        dy = 1 if dy_away > 0 else (-1 if dy_away < 0 else 0)

        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        new_x = merchant.x + dx
        new_y = merchant.y + dy

        if merchant._can_move(new_x, new_y, game_map):
            merchant.x = new_x
            merchant.y = new_y
        else:
            # Пробуем альтернативные направления
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            random.shuffle(directions)
            for alt_dx, alt_dy in directions:
                new_x = merchant.x + alt_dx
                new_y = merchant.y + alt_dy
                if merchant._can_move(new_x, new_y, game_map):
                    merchant.x = new_x
                    merchant.y = new_y
                    break

    @staticmethod
    def _travel_step(merchant, game_map):
        """Один шаг путешествия к текущей точке waypoint"""
        # Система waypoints
        if merchant.waypoints:
            current_wp = MerchantAI._get_current_waypoint(merchant)
            if not current_wp:
                return False

            target_x = current_wp.get('x', merchant.x)
            target_y = current_wp.get('y', merchant.y)
        else:
            # Старая система
            if not merchant.target_location:
                MerchantAI._choose_new_destination(merchant)
                return False

            target_x = merchant.target_location.x
            target_y = merchant.target_location.y

        # Проверяем достижение цели
        if merchant.x == target_x and merchant.y == target_y:
            merchant.state = "rest"
            merchant.rest_counter = 0
            if merchant.waypoints:
                current_wp = MerchantAI._get_current_waypoint(merchant)
                merchant.current_waypoint_duration = current_wp.get('duration', 20) if current_wp else 20
            else:
                merchant.rest_duration = random.randint(5, 8)
            return False

        # Проверяем проходимость цели
        if not game_map.is_valid_position(target_x, target_y):
            if merchant.waypoints:
                MerchantAI._advance_to_next_waypoint(merchant)
            return False

        target_tile = game_map.get_tile(target_x, target_y)
        if not target_tile.is_passable():
            if merchant.waypoints:
                MerchantAI._advance_to_next_waypoint(merchant)
            return False

        # Находим следующий шаг
        dx, dy = merchant._find_next_step(target_x, target_y, game_map, max_search_distance=100)

        old_x, old_y = merchant.x, merchant.y
        moved = False

        if dx != 0 or dy != 0:
            if merchant._can_move(merchant.x + dx, merchant.y + dy, game_map):
                merchant.x += dx
                merchant.y += dy
                moved = True

        # Если BFS не нашёл путь, пробуем напрямую
        if not moved:
            direct_dx = 1 if target_x > merchant.x else (-1 if target_x < merchant.x else 0)
            direct_dy = 1 if target_y > merchant.y else (-1 if target_y < merchant.y else 0)

            for try_dx, try_dy in [(direct_dx, direct_dy), (direct_dx, 0), (0, direct_dy)]:
                if try_dx == 0 and try_dy == 0:
                    continue
                if merchant._can_move(merchant.x + try_dx, merchant.y + try_dy, game_map):
                    merchant.x += try_dx
                    merchant.y += try_dy
                    moved = True
                    break

        # Проверка застревания
        if not moved or (merchant.x == old_x and merchant.y == old_y):
            merchant.stuck_counter += 1
            if merchant.stuck_counter > 10:
                if merchant.waypoints:
                    MerchantAI._advance_to_next_waypoint(merchant)
                else:
                    MerchantAI._choose_new_destination(merchant)
                merchant.stuck_counter = 0
                return False
        else:
            merchant.stuck_counter = 0

        return True

    @staticmethod
    def _rest_at_waypoint(merchant):
        """Отдых в текущей точке waypoint"""
        merchant.rest_counter += 1

        if merchant.waypoints:
            if merchant.rest_counter >= merchant.current_waypoint_duration:
                merchant.state = "travel"
                merchant.rest_counter = 0
                MerchantAI._advance_to_next_waypoint(merchant)
        else:
            if merchant.rest_counter >= merchant.rest_duration:
                merchant.state = "travel"
                merchant.rest_counter = 0
                MerchantAI._choose_new_destination(merchant)

    @staticmethod
    def _get_current_waypoint(merchant):
        """Получить текущую целевую точку маршрута"""
        if not merchant.waypoints:
            return None
        if merchant.current_waypoint_index >= len(merchant.waypoints):
            if merchant.is_loop:
                merchant.current_waypoint_index = 0
            else:
                return None
        return merchant.waypoints[merchant.current_waypoint_index]

    @staticmethod
    def _advance_to_next_waypoint(merchant):
        """Перейти к следующей точке маршрута"""
        if not merchant.waypoints:
            return

        attempts = 0
        max_attempts = len(merchant.waypoints)

        while attempts < max_attempts:
            merchant.current_waypoint_index += 1
            if merchant.current_waypoint_index >= len(merchant.waypoints):
                if merchant.is_loop:
                    merchant.current_waypoint_index = 0
                else:
                    merchant.state = "rest"
                    return

            current_wp = MerchantAI._get_current_waypoint(merchant)
            if current_wp:
                target_x = current_wp.get('x', merchant.x)
                target_y = current_wp.get('y', merchant.y)

                if merchant.x == target_x and merchant.y == target_y:
                    attempts += 1
                    continue

                merchant.current_waypoint_duration = current_wp.get('duration', 20)
                break

            attempts += 1

        merchant.rest_counter = 0
        merchant.stuck_counter = 0

    @staticmethod
    def _choose_new_destination(merchant):
        """Выбрать новую цель для путешествия (старая система)"""
        if merchant.waypoints:
            MerchantAI._advance_to_next_waypoint(merchant)
            return

        if not merchant.settlements:
            return

        available = [s for s in merchant.settlements
                    if abs(s.x - merchant.x) > 5 or abs(s.y - merchant.y) > 5]

        if available:
            merchant.target_location = random.choice(available)
        elif merchant.settlements:
            merchant.target_location = random.choice(merchant.settlements)

        merchant.stuck_counter = 0
