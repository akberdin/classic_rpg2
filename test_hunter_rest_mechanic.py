"""
Тест механики отдыха охотников после убийства животных
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.npc.unique import Hunter
from game.npc.animal import Wolf
from game.map import GameMap
from game.core.ai_context import AIContext


def test_hunter_rest_after_kill():
    """
    Тестируем полный цикл:
    1. Охотник находит и убивает животное
    2. Охотник возвращается в город
    3. Охотник отдыхает 20 ходов (скрыт с карты)
    4. Охотник возвращается к патрулированию
    """
    print("=" * 60)
    print("ТЕСТ: Механика отдыха охотников после убийства животных")
    print("=" * 60)

    # Создаем карту (используется карта по умолчанию)
    game_map = GameMap()

    # Создаем охотника в точке (50, 50) - это его дом
    hunter = Hunter(name="Тестовый охотник", x=50, y=50, level=20, home_x=50, home_y=50)
    print(f"\n✓ Создан охотник: {hunter.name}")
    print(f"  Позиция: ({hunter.x}, {hunter.y})")
    print(f"  Дом: ({hunter.home_x}, {hunter.home_y})")
    print(f"  Состояние: {hunter.state}")

    # Создаем волка рядом с охотником (прямо рядом для быстрого боя)
    wolf = Wolf(name="Тестовый волк", x=51, y=50, level=1)
    # Делаем волка слабым, чтобы охотник гарантированно убил его
    wolf.health = 5
    wolf.max_health = 5
    print(f"\n✓ Создан волк: {wolf.name}")
    print(f"  Позиция: ({wolf.x}, {wolf.y})")
    print(f"  HP: {wolf.health}/{wolf.max_health}")

    # Создаем AI контекст
    all_npcs = [hunter, wolf]
    context = AIContext(
        game_map=game_map,
        all_npcs=all_npcs,
        current_hour=12,
        player=None
    )

    # Симулируем ходы до тех пор, пока охотник не найдет цель
    print("\n" + "=" * 60)
    print("ФАЗА 1: Поиск и убийство животного")
    print("=" * 60)

    max_turns_to_find = 50
    for turn in range(max_turns_to_find):
        if hunter.state == "hunt":
            print(f"\n✓ Ход {turn}: Охотник обнаружил цель и начал охоту!")
            print(f"  Цель: {hunter.hunt_target.name if hunter.hunt_target else 'None'}")
            break
        hunter.update_ai(context)

    if hunter.state != "hunt":
        print(f"\n✗ ОШИБКА: Охотник не нашел цель за {max_turns_to_find} ходов")
        return False

    # Продолжаем симуляцию до убийства
    max_turns_to_kill = 100
    killed = False
    for turn in range(max_turns_to_kill):
        prev_state = hunter.state
        hunter.update_ai(context)

        if not wolf.is_alive:
            print(f"\n✓ Ход {turn}: Волк убит!")
            print(f"  Состояние охотника: {hunter.state}")
            killed = True

            if hunter.state != "returning_to_town":
                print(f"\n✗ ОШИБКА: После убийства животного охотник должен быть в состоянии 'returning_to_town', но в состоянии '{hunter.state}'")
                return False
            break

    if not killed:
        print(f"\n✗ ОШИБКА: Волк не был убит за {max_turns_to_kill} ходов")
        return False

    # Фаза 2: Возвращение в город
    print("\n" + "=" * 60)
    print("ФАЗА 2: Возвращение в город")
    print("=" * 60)

    # Обновляем список NPC (волк мертв)
    all_npcs = [hunter]
    context = AIContext(
        game_map=game_map,
        all_npcs=all_npcs,
        current_hour=12,
        player=None
    )

    max_turns_to_return = 200
    returned = False
    for turn in range(max_turns_to_return):
        prev_hidden = hunter.is_hidden()
        prev_state = hunter.state

        hunter.update_ai(context)

        if not prev_hidden and hunter.is_hidden():
            print(f"\n✓ Ход {turn}: Охотник достиг дома и скрылся для отдыха!")
            print(f"  Позиция: ({hunter.x}, {hunter.y})")
            print(f"  Состояние: {hunter.state}")
            print(f"  Скрыт: {hunter.is_hidden()}")
            if hasattr(hunter, '_hidden_turns_remaining'):
                print(f"  Осталось ходов отдыха: {hunter._hidden_turns_remaining}")
            returned = True
            break

        if turn % 20 == 0:
            print(f"  Ход {turn}: Возвращается... Позиция: ({hunter.x}, {hunter.y}), расстояние до дома: {abs(hunter.x - hunter.home_x) + abs(hunter.y - hunter.home_y)}")

    if not returned:
        print(f"\n✗ ОШИБКА: Охотник не вернулся домой за {max_turns_to_return} ходов")
        print(f"  Текущая позиция: ({hunter.x}, {hunter.y})")
        print(f"  Состояние: {hunter.state}")
        return False

    # Проверяем что охотник скрыт на 20 ходов
    if not hasattr(hunter, '_hidden_turns_remaining'):
        print(f"\n✗ ОШИБКА: У охотника нет атрибута _hidden_turns_remaining")
        return False

    if hunter._hidden_turns_remaining != 20:
        print(f"\n✗ ОШИБКА: Ожидалось 20 ходов отдыха, но установлено {hunter._hidden_turns_remaining}")
        return False

    print(f"\n✓ Охотник корректно скрыт на 20 ходов отдыха")

    # Фаза 3: Отдых
    print("\n" + "=" * 60)
    print("ФАЗА 3: Отдых (20 ходов)")
    print("=" * 60)

    # Симулируем 20 ходов отдыха
    for turn in range(20):
        # Обновляем состояние скрытия (это обычно делает npc_manager)
        hunter.update_hidden_state()

        if turn % 5 == 0:
            print(f"  Ход {turn}: Отдых... Осталось ходов: {hunter._hidden_turns_remaining if hasattr(hunter, '_hidden_turns_remaining') else 0}")

    # После 20 ходов охотник должен появиться
    hunter.update_hidden_state()

    if hunter.is_hidden():
        print(f"\n✗ ОШИБКА: После 20 ходов охотник все еще скрыт")
        return False

    print(f"\n✓ Охотник вышел из скрытия после 20 ходов")

    # Фаза 4: Возвращение к патрулированию
    print("\n" + "=" * 60)
    print("ФАЗА 4: Возвращение к патрулированию")
    print("=" * 60)

    # Обновляем AI один раз для обработки появления
    hunter.update_ai(context)

    if hunter.state != "patrol":
        print(f"\n✗ ОШИБКА: После отдыха охотник должен быть в состоянии 'patrol', но в состоянии '{hunter.state}'")
        return False

    print(f"\n✓ Охотник вернулся к патрулированию")
    print(f"  Состояние: {hunter.state}")
    print(f"  Позиция: ({hunter.x}, {hunter.y})")

    print("\n" + "=" * 60)
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    print("\nМеханика работает корректно:")
    print("1. ✓ Охотник находит и убивает животное")
    print("2. ✓ Охотник возвращается в город (returning_to_town)")
    print("3. ✓ Охотник скрывается на 20 ходов (resting)")
    print("4. ✓ После отдыха охотник возвращается к патрулированию (patrol)")

    return True


if __name__ == "__main__":
    success = test_hunter_rest_after_kill()
    sys.exit(0 if success else 1)
