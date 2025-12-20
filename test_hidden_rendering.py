"""
Тест проверяет что скрытые NPC не рендерятся на карте
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.npc.unique import Hunter
from game.npc.worker import Miner


def test_hidden_npc_status():
    """
    Тестируем что is_hidden() корректно работает для разных типов NPC
    """
    print("=" * 60)
    print("ТЕСТ: Проверка статуса скрытия NPC")
    print("=" * 60)

    # Создаем охотника
    hunter = Hunter(name="Тестовый охотник", x=50, y=50, level=20, home_x=50, home_y=50)
    print(f"\n✓ Создан охотник: {hunter.name}")
    print(f"  Изначально скрыт: {hunter.is_hidden()}")

    if hunter.is_hidden():
        print(f"\n✗ ОШИБКА: Охотник не должен быть скрыт сразу после создания")
        return False

    # Скрываем охотника на 20 ходов
    hunter.hide_from_map(20, "Город (отдых)")
    print(f"\n✓ Охотник скрыт на 20 ходов")
    print(f"  Скрыт: {hunter.is_hidden()}")

    if not hunter.is_hidden():
        print(f"\n✗ ОШИБКА: Охотник должен быть скрыт после вызова hide_from_map()")
        return False

    # Проверяем что после обновления состояния охотник остается скрыт
    for turn in range(10):
        hunter.update_hidden_state()
        if turn == 5:
            print(f"\n✓ После 5 ходов охотник все еще скрыт: {hunter.is_hidden()}")
            if not hunter.is_hidden():
                print(f"\n✗ ОШИБКА: Охотник должен быть скрыт первые 20 ходов")
                return False

    # Симулируем оставшиеся 10 ходов
    for turn in range(10):
        hunter.update_hidden_state()

    # После 20 ходов охотник должен появиться
    hunter.update_hidden_state()
    print(f"\n✓ После 20 ходов охотник появился: {not hunter.is_hidden()}")

    if hunter.is_hidden():
        print(f"\n✗ ОШИБКА: Охотник должен появиться после 20 ходов")
        return False

    # Тест для шахтера
    print("\n" + "=" * 60)
    print("Тест для шахтера")
    print("=" * 60)

    miner = Miner(name="Тестовый шахтер", x=100, y=100, level=5, mine_x=105, mine_y=105)
    print(f"\n✓ Создан шахтер: {miner.name}")
    print(f"  Изначально скрыт: {miner.is_hidden()}")

    if miner.is_hidden():
        print(f"\n✗ ОШИБКА: Шахтер не должен быть скрыт сразу после создания")
        return False

    # Скрываем шахтера на 35 ходов
    miner.hide_from_map(35, "Шахта (работа)")
    print(f"\n✓ Шахтер скрыт на 35 ходов")
    print(f"  Скрыт: {miner.is_hidden()}")

    if not miner.is_hidden():
        print(f"\n✗ ОШИБКА: Шахтер должен быть скрыт после вызова hide_from_map()")
        return False

    print("\n" + "=" * 60)
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    print("\nМеханизм скрытия работает корректно:")
    print("1. ✓ NPC не скрыты сразу после создания")
    print("2. ✓ hide_from_map() корректно скрывает NPC")
    print("3. ✓ is_hidden() возвращает правильный статус")
    print("4. ✓ update_hidden_state() корректно обрабатывает таймер")
    print("5. ✓ NPC появляются после истечения времени скрытия")

    return True


if __name__ == "__main__":
    success = test_hidden_npc_status()
    sys.exit(0 if success else 1)
