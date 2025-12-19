#!/usr/bin/env python3
"""
Тестовый скрипт для полной проверки системы спавна всех NPC
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.map import GameMap
from game.npc_spawner import NPCSpawner


def test_full_npc_spawn():
    """Тестирование полной системы спавна NPC"""
    print("=" * 60)
    print("ТЕСТ: Полная система спавна NPC")
    print("=" * 60)

    # Создаем карту
    print("\n1. Создание карты...")
    game_map = GameMap()
    print(f"   Карта загружена: {game_map.width}x{game_map.height}")
    print(f"   Локаций: {len(game_map.locations)}")

    # Создаем спавнер
    print("\n2. Создание спавнера...")
    spawner = NPCSpawner(game_map)

    # Спавним всех NPC
    print("\n3. Спавн всех NPC...")
    npcs = spawner.spawn_all_npcs()

    # Анализируем результаты
    print(f"\n4. Результаты спавна всех NPC:")
    total_npcs = 0
    for category, npc_list in npcs.items():
        count = len(npc_list)
        total_npcs += count
        print(f"   {category}: {count}")

    print(f"\n   ВСЕГО NPC: {total_npcs}")

    # Детальный анализ стражи
    print(f"\n5. Детальный анализ стражи:")
    guards = npcs.get('guards', [])
    print(f"   Всего стражей: {len(guards)}")

    # Группируем по типам
    guard_types = {}
    for guard in guards:
        guard_type = type(guard).__name__
        if guard_type not in guard_types:
            guard_types[guard_type] = []
        guard_types[guard_type].append(guard)

    for guard_type, guards_list in guard_types.items():
        print(f"   - {guard_type}: {len(guards_list)}")

    # Проверяем магов отдельно
    print(f"\n6. Проверка магов:")
    mages = npcs.get('mages', [])
    print(f"   Маги из spawn_mages(): {len(mages)}")

    mage_guards = guard_types.get('MagePatrol', [])
    print(f"   Маги из guards: {len(mage_guards)}")

    print(f"   ИТОГО магов: {len(mages) + len(mage_guards)}")

    # Проверяем адептов тени
    print(f"\n7. Проверка адептов тени:")
    shadow_adepts = npcs.get('shadow_adepts', [])
    print(f"   Адепты из spawn_shadow_adepts(): {len(shadow_adepts)}")

    shadow_guards = guard_types.get('ShadowAdept', [])
    print(f"   Адепты из guards: {len(shadow_guards)}")

    print(f"   ИТОГО адептов тени: {len(shadow_adepts) + len(shadow_guards)}")

    # Проверяем охотников
    print(f"\n8. Проверка охотников:")
    hunters = npcs.get('hunters', [])
    print(f"   Охотники из spawn_hunters(): {len(hunters)}")

    hunter_guards = guard_types.get('Hunter', [])
    print(f"   Охотники из guards: {len(hunter_guards)}")

    print(f"   ИТОГО охотников: {len(hunters) + len(hunter_guards)}")

    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН УСПЕШНО")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_full_npc_spawn()
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
