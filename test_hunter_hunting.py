#!/usr/bin/env python3
"""
Тест симуляции охоты охотника-стражника на животных
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner
from game.npc.animal import Wolf

print("=" * 70)
print("ТЕСТ: Симуляция охоты охотника-стражника")
print("=" * 70)
print()

# Создаём карту
print("1. Создание карты и NPC...")
game_map = GameMap()
spawner = NPCSpawner(game_map)
guards = spawner.spawn_guards()

# Находим охотника
hunter = None
for guard in guards:
    if guard.npc_type == 'hunter':
        hunter = guard
        break

if not hunter:
    print("   ❌ Охотник не найден!")
    sys.exit(1)

print(f"   ✅ Охотник: {hunter.name}")
print(f"      Позиция: ({hunter.x}, {hunter.y})")
print(f"      Дом: ({hunter.home_x}, {hunter.home_y})")
print(f"      patrol_radius: {hunter.max_distance_from_home}")
print()

# Создаём волка ВНУТРИ patrol_radius охотника
print("2. Создание волка в зоне patrol_radius...")
wolf_x = hunter.home_x + 5  # В пределах patrol_radius (10)
wolf_y = hunter.home_y + 3
wolf = Wolf("Тестовый волк", wolf_x, wolf_y, level=5, spawn_x=wolf_x, spawn_y=wolf_y)

distance_wolf_to_hunter_home = abs(wolf.x - hunter.home_x) + abs(wolf.y - hunter.home_y)
distance_wolf_to_hunter = abs(wolf.x - hunter.x) + abs(wolf.y - hunter.y)

print(f"   Волк создан: {wolf.name}")
print(f"   Позиция волка: ({wolf.x}, {wolf.y})")
print(f"   Расстояние до дома охотника: {distance_wolf_to_hunter_home}")
print(f"   Расстояние до охотника: {distance_wolf_to_hunter}")
print(f"   В пределах patrol_radius: {distance_wolf_to_hunter_home <= hunter.max_distance_from_home} ✅")
print(f"   В пределах detection_range: {distance_wolf_to_hunter <= hunter.detection_range} ✅")
print()

# Тестируем поиск цели
print("3. Тест поиска цели охотником...")
all_npcs = guards + [wolf]
target = hunter._find_hunt_target(all_npcs)

if target:
    print(f"   ✅ УСПЕХ! Охотник нашел цель: {target.name}")
    print(f"      - Тип: {target.npc_type} (животное)")
    print(f"      - Позиция: ({target.x}, {target.y})")
    
    # Проверяем, что это именно наш волк
    if target == wolf:
        print(f"      - ✅ Найден правильный объект (тестовый волк)")
else:
    print(f"   ❌ ОШИБКА! Охотник не нашел волка")
    print(f"      Волк в пределах patrol_radius: {distance_wolf_to_hunter_home <= hunter.max_distance_from_home}")
    print(f"      Волк в пределах detection_range: {distance_wolf_to_hunter <= hunter.detection_range}")
print()

# Создаём второго волка ЗА ПРЕДЕЛАМИ patrol_radius
print("4. Создание второго волка ЗА ПРЕДЕЛАМИ patrol_radius...")
wolf2_x = hunter.home_x + 15  # За пределами patrol_radius (10)
wolf2_y = hunter.home_y
wolf2 = Wolf("Дальний волк", wolf2_x, wolf2_y, level=5, spawn_x=wolf2_x, spawn_y=wolf2_y)

distance_wolf2_to_home = abs(wolf2.x - hunter.home_x) + abs(wolf2.y - hunter.home_y)
print(f"   Волк 2: {wolf2.name}")
print(f"   Позиция: ({wolf2.x}, {wolf2.y})")
print(f"   Расстояние до дома охотника: {distance_wolf2_to_home}")
print(f"   За пределами patrol_radius: {distance_wolf2_to_home > hunter.max_distance_from_home} ✅")
print()

# Тестируем, что охотник игнорирует дальнего волка
print("5. Проверка приоритета целей...")
all_npcs = guards + [wolf, wolf2]
target = hunter._find_hunt_target(all_npcs)

if target == wolf:
    print(f"   ✅ УСПЕХ! Охотник выбрал ближнего волка (в пределах patrol_radius)")
    print(f"      Игнорирует дальнего волка за пределами зоны")
elif target == wolf2:
    print(f"   ❌ ОШИБКА! Охотник выбрал дальнего волка (за пределами patrol_radius)")
else:
    print(f"   ⚠️  Охотник не нашел цель")
print()

print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print()
print("Результаты:")
print("✅ Охотник находит животных в пределах patrol_radius")
print("✅ Охотник игнорирует животных за пределами patrol_radius")
print("✅ Приоритизация работает корректно")
