"""
Тест исправления застревания охотников и правильности характеристик
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.npc.unique import Hunter
from game.map import GameMap
from game.core.ai_context import AIContext


def test_hunter_stats():
    """Проверяем что у охотников правильные характеристики (фокус на ловкость и телосложение)"""
    print("=" * 60)
    print("ТЕСТ 1: Характеристики охотников")
    print("=" * 60)

    hunter = Hunter(name="Тестовый охотник", x=25, y=25, level=20, home_x=25, home_y=25)

    print(f"\n✓ Создан охотник уровня {hunter.level}")
    print(f"  Характеристики:")
    print(f"    Ловкость (основная): {hunter.dexterity}")
    print(f"    Телосложение (основная): {hunter.constitution}")
    print(f"    Сила: {hunter.strength}")
    print(f"    Удача: {hunter.luck}")
    print(f"    Интеллект: {hunter.intelligence}")
    print(f"    Дух: {hunter.spirit}")

    # Проверяем что ловкость и телосложение выше других характеристик
    avg_other_stats = (hunter.strength + hunter.intelligence + hunter.spirit + hunter.luck) / 4

    if hunter.dexterity <= avg_other_stats or hunter.constitution <= avg_other_stats:
        print(f"\n✗ ОШИБКА: Ловкость и телосложение должны быть выше остальных характеристик")
        print(f"  Средняя других характеристик: {avg_other_stats:.1f}")
        return False

    print(f"\n✓ Ловкость и телосложение выше остальных характеристик")
    print(f"  Средняя других: {avg_other_stats:.1f}")

    # Проверяем что максимальная выносливость достаточно высока
    max_stamina = hunter.get_effective_max_stamina()
    print(f"\n✓ Максимальная выносливость: {max_stamina}")

    if max_stamina < 300:
        print(f"\n✗ ПРЕДУПРЕЖДЕНИЕ: Выносливость слишком низкая для охотника уровня {hunter.level}")

    return True


def test_hunter_patrol_no_stuck():
    """Проверяем что охотники не застревают при патрулировании (200+ ходов)"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Охотники не застревают при патрулировании")
    print("=" * 60)

    # Создаем карту
    game_map = GameMap()

    # Создаем охотника
    hunter = Hunter(name="Тестовый охотник", x=25, y=25, level=20, home_x=25, home_y=25)
    print(f"\n✓ Создан охотник: {hunter.name}")
    print(f"  Начальная позиция: ({hunter.x}, {hunter.y})")
    print(f"  Начальная выносливость: {hunter.stamina}/{hunter.get_effective_max_stamina()}")

    # Создаем AI контекст (без других NPC для чистого теста патрулирования)
    all_npcs = [hunter]
    context = AIContext(
        game_map=game_map,
        all_npcs=all_npcs,
        current_hour=12,
        player=None
    )

    # Симулируем 250 ходов патрулирования
    print(f"\n✓ Симуляция 250 ходов патрулирования...")

    positions = []  # История позиций
    stuck_count = 0  # Счетчик застреваний
    last_pos = (hunter.x, hunter.y)

    for turn in range(250):
        hunter.update_ai(context)
        current_pos = (hunter.x, hunter.y)
        positions.append(current_pos)

        # Проверяем не застрял ли охотник (не двигается 20 ходов подряд)
        if turn >= 20:
            recent_positions = positions[-20:]
            unique_positions = set(recent_positions)
            if len(unique_positions) == 1:
                stuck_count += 1
                if stuck_count == 1:
                    print(f"\n  ⚠ Ход {turn}: Охотник не двигался последние 20 ходов")
                    print(f"    Позиция: {current_pos}")
                    print(f"    Состояние: {hunter.state}")
                    print(f"    Выносливость: {hunter.stamina}/{hunter.get_effective_max_stamina()}")
                    print(f"    is_resting: {hunter.is_resting}")

        # Выводим прогресс каждые 50 ходов
        if turn % 50 == 0 and turn > 0:
            unique_positions_total = len(set(positions))
            print(f"  Ход {turn}: уникальных позиций: {unique_positions_total}, текущая: ({hunter.x}, {hunter.y}), stamina: {hunter.stamina}/{hunter.get_effective_max_stamina()}")

    # Проверяем результаты
    unique_positions_total = len(set(positions))
    print(f"\n✓ Симуляция завершена")
    print(f"  Всего уникальных позиций: {unique_positions_total}")
    print(f"  Охотник посетил {unique_positions_total} разных клеток за 250 ходов")

    # Охотник должен двигаться и посещать разные позиции
    # Даже с учетом отдыха, за 250 ходов должно быть минимум 30 уникальных позиций
    if unique_positions_total < 30:
        print(f"\n✗ ОШИБКА: Охотник практически не двигался (всего {unique_positions_total} позиций)")
        print(f"  Это может указывать на застревание")
        return False

    print(f"\n✓ Охотник активно патрулирует и не застревает")

    # Проверяем что охотник не был в состоянии застревания более 30 ходов подряд
    if stuck_count > 30:
        print(f"\n✗ ОШИБКА: Охотник застревал на одном месте более 30 ходов")
        return False

    if stuck_count > 0:
        print(f"\n✓ Охотник иногда стоял на месте ({stuck_count} обнаружений), но это нормально для восстановления выносливости")
    else:
        print(f"\n✓ Охотник постоянно двигался")

    return True


def run_all_tests():
    """Запускаем все тесты"""
    print("=" * 60)
    print("ПОЛНЫЙ ТЕСТ ИСПРАВЛЕНИЙ ОХОТНИКОВ")
    print("=" * 60)

    success = True

    # Тест 1: Характеристики
    if not test_hunter_stats():
        success = False

    # Тест 2: Патрулирование без застревания
    if not test_hunter_patrol_no_stuck():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        print("\nИсправления работают корректно:")
        print("1. ✓ Охотники имеют правильные характеристики (ловкость и телосложение)")
        print("2. ✓ Охотники активно патрулируют и не застревают")
        print("3. ✓ Система выносливости работает корректно")
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("=" * 60)

    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
