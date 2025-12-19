#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы спавна стражи
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.map import GameMap
from game.npc_spawner import NPCSpawner


def test_guard_spawn():
    """Тестирование системы спавна стражи"""
    print("=" * 60)
    print("ТЕСТ: Система спавна стражи")
    print("=" * 60)

    # Создаем карту
    print("\n1. Создание карты...")
    game_map = GameMap()
    print(f"   Карта загружена: {game_map.width}x{game_map.height}")
    print(f"   Локаций: {len(game_map.locations)}")

    # Создаем спавнер
    print("\n2. Создание спавнера...")
    spawner = NPCSpawner(game_map)

    # Проверяем локации с guards
    print("\n3. Проверка локаций с параметром guards:")
    locations_with_guards = [
        loc for loc in game_map.locations
        if hasattr(loc, 'guards') and loc.guards
    ]
    print(f"   Найдено локаций с guards: {len(locations_with_guards)}")

    for loc in locations_with_guards:
        print(f"\n   Локация: {loc.name} ({loc.location_type})")
        print(f"   - spawn_radius: {getattr(loc, 'spawn_radius', 'не указан')}")
        print(f"   - Конфигураций стражи: {len(loc.guards)}")

        for i, guard_cfg in enumerate(loc.guards, 1):
            print(f"     [{i}] type={guard_cfg.get('type')}, rank={guard_cfg.get('rank')}, "
                  f"count={guard_cfg.get('count')}, patrol_radius={guard_cfg.get('patrol_radius')}, "
                  f"respawn_time={guard_cfg.get('respawn_time')}")

    # Спавним стражу
    print("\n4. Спавн стражи...")
    guards = spawner.spawn_guards()

    # Анализируем результаты
    print(f"\n5. Результаты спавна:")
    print(f"   Всего стражей создано: {len(guards)}")

    # Группируем по типам
    guard_types = {}
    for guard in guards:
        guard_type = type(guard).__name__
        if guard_type not in guard_types:
            guard_types[guard_type] = []
        guard_types[guard_type].append(guard)

    print(f"\n   Распределение по типам:")
    for guard_type, guards_list in guard_types.items():
        print(f"   - {guard_type}: {len(guards_list)}")

    # Детальная информация о первых 5 стражах
    print(f"\n6. Детали первых 5 стражей:")
    for i, guard in enumerate(guards[:5], 1):
        print(f"\n   [{i}] {guard.name}")
        print(f"       - Класс: {type(guard).__name__}")
        print(f"       - Уровень: {guard.level}")
        print(f"       - Позиция: ({guard.x}, {guard.y})")
        print(f"       - respawn_time: {getattr(guard, 'respawn_time', 'не задан')}")
        print(f"       - spawn_location: ({getattr(guard, 'spawn_location_x', 'N/A')}, "
              f"{getattr(guard, 'spawn_location_y', 'N/A')})")
        print(f"       - spawn_radius: {getattr(guard, 'spawn_radius', 'не задан')}")

        # Специфичные параметры
        if hasattr(guard, 'patrol_points'):
            print(f"       - patrol_points: {len(guard.patrol_points)} точек")
        if hasattr(guard, 'max_distance_from_academy'):
            print(f"       - max_distance_from_academy: {guard.max_distance_from_academy}")
        if hasattr(guard, 'max_distance_from_home'):
            print(f"       - max_distance_from_home: {guard.max_distance_from_home}")
        if hasattr(guard, 'max_distance_from_camp'):
            print(f"       - max_distance_from_camp: {guard.max_distance_from_camp}")

    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН УСПЕШНО")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_guard_spawn()
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
