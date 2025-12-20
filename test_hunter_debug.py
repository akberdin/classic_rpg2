"""
Отладочный тест для понимания почему охотники застревают
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.npc.unique import Hunter
from game.map import GameMap
from game.core.ai_context import AIContext


def test_hunter_movement_debug():
    """Детальный лог движения охотника"""
    print("=" * 60)
    print("ОТЛАДКА: Движение охотника")
    print("=" * 60)

    # Создаем карту
    game_map = GameMap()

    # Создаем охотника (используем центр карты 25,25 вместо 50,50 которое за пределами карты 50x50)
    hunter = Hunter(name="Тестовый охотник", x=25, y=25, level=20, home_x=25, home_y=25)
    print(f"\n✓ Создан охотник")
    print(f"  Позиция: ({hunter.x}, {hunter.y})")
    print(f"  Состояние: {hunter.state}")
    print(f"  Выносливость: {hunter.stamina}/{hunter.get_effective_max_stamina()}")
    print(f"  is_resting: {hunter.is_resting}")
    print(f"  steps_in_current_state: {hunter.steps_in_current_state}")
    print(f"  max_steps_patrol: {hunter.max_steps_patrol}")

    # Создаем AI контекст
    all_npcs = [hunter]
    context = AIContext(
        game_map=game_map,
        all_npcs=all_npcs,
        current_hour=12,
        player=None
    )

    # Симулируем 10 ходов с детальным логом
    print(f"\n" + "=" * 60)
    print("СИМУЛЯЦИЯ 10 ХОДОВ")
    print("=" * 60)

    for turn in range(10):
        print(f"\n--- Ход {turn} ---")
        prev_x, prev_y = hunter.x, hunter.y
        prev_stamina = hunter.stamina
        prev_state = hunter.state
        prev_is_resting = hunter.is_resting

        # Вызываем update_ai
        hunter.update_ai(context)

        # Выводим что изменилось
        print(f"  Позиция: ({prev_x}, {prev_y}) -> ({hunter.x}, {hunter.y}) [двинулся: {prev_x != hunter.x or prev_y != hunter.y}]")
        print(f"  Состояние: {prev_state} -> {hunter.state}")
        print(f"  Выносливость: {prev_stamina} -> {hunter.stamina} [потрачено: {prev_stamina - hunter.stamina}]")
        print(f"  is_resting: {prev_is_resting} -> {hunter.is_resting}")
        print(f"  steps_in_current_state: {hunter.steps_in_current_state}")

        # Проверяем тайл на котором стоит охотник
        tile = game_map.get_tile(hunter.x, hunter.y)
        if tile:
            print(f"  Тайл: passable={tile.is_passable()}")
        else:
            print(f"  Тайл: None (позиция за пределами карты?)")

        # Проверяем соседние тайлы
        can_move_anywhere = False
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = hunter.x + dx, hunter.y + dy
                if hunter._can_move(new_x, new_y, game_map):
                    can_move_anywhere = True
                    break
            if can_move_anywhere:
                break

        print(f"  Может двигаться в соседние клетки: {can_move_anywhere}")

    print(f"\n" + "=" * 60)
    print("РЕЗУЛЬТАТ:")
    print(f"  Охотник переместился с (25, 25) в ({hunter.x}, {hunter.y})")
    print(f"  Расстояние: {abs(hunter.x - 25) + abs(hunter.y - 25)}")
    print("=" * 60)


if __name__ == "__main__":
    test_hunter_movement_debug()
