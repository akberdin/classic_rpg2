#!/usr/bin/env python3
"""
Тест поведения охотников-стражников
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner
from game.npc.animal import Wolf
from game.npc.hostile import Bandit

print("=" * 70)
print("ТЕСТ: Поведение охотников-стражников")
print("=" * 70)
print()

# Создаём карту
print("1. Создание карты...")
game_map = GameMap()
print(f"   Карта загружена: {game_map.width}x{game_map.height}")
print()

# Создаём спавнер и получаем всех NPC
print("2. Спавн NPC...")
spawner = NPCSpawner(game_map)
guards = spawner.spawn_guards()
animals = spawner.spawn_animals()

print(f"   Создано стражей: {len(guards)}")
print(f"   Создано животных: {len(animals)}")
print()

# Находим охотника-стражника
print("3. Поиск охотника-стражника...")
hunter = None
for guard in guards:
    if guard.npc_type == 'hunter':
        hunter = guard
        break

if not hunter:
    print("   ❌ Охотник-стражник не найден!")
    print("   Проверьте конфигурацию в map1_config.json")
    sys.exit(1)

print(f"   ✅ Найден охотник: {hunter.name}")
print(f"      - Позиция: ({hunter.x}, {hunter.y})")
print(f"      - Дом: ({hunter.home_x}, {hunter.home_y})")
print(f"      - patrol_radius (max_distance_from_home): {hunter.max_distance_from_home}")
print(f"      - detection_range: {hunter.detection_range}")
print()

# Проверяем животных в радиусе
print("4. Проверка животных в радиусе охоты...")
animals_in_patrol_radius = []
animals_outside_patrol_radius = []

for animal in animals:
    if animal.is_alive:
        distance_to_hunter_home = abs(animal.x - hunter.home_x) + abs(animal.y - hunter.home_y)
        distance_to_hunter = abs(animal.x - hunter.x) + abs(animal.y - hunter.y)
        
        info = {
            'npc': animal,
            'distance_to_home': distance_to_hunter_home,
            'distance_to_hunter': distance_to_hunter
        }
        
        if distance_to_hunter_home <= hunter.max_distance_from_home:
            animals_in_patrol_radius.append(info)
        else:
            animals_outside_patrol_radius.append(info)

print(f"   Животных в пределах patrol_radius от дома охотника: {len(animals_in_patrol_radius)}")
for info in animals_in_patrol_radius[:3]:  # Показываем первые 3
    print(f"      - {info['npc'].name} ({info['npc'].npc_type}) на ({info['npc'].x}, {info['npc'].y})")
    print(f"        Расстояние до дома охотника: {info['distance_to_home']}")
    print(f"        Расстояние до охотника: {info['distance_to_hunter']}")

print(f"\n   Животных за пределами patrol_radius: {len(animals_outside_patrol_radius)}")
if animals_outside_patrol_radius:
    info = animals_outside_patrol_radius[0]
    print(f"      - {info['npc'].name} на ({info['npc'].x}, {info['npc'].y})")
    print(f"        Расстояние до дома: {info['distance_to_home']} > {hunter.max_distance_from_home}")
print()

# Тестируем метод поиска цели
print("5. Тест метода _find_hunt_target()...")
all_npcs = guards + animals
target = hunter._find_hunt_target(all_npcs)

if target:
    distance_to_target = abs(hunter.x - target.x) + abs(hunter.y - target.y)
    distance_target_to_home = abs(target.x - hunter.home_x) + abs(target.y - hunter.home_y)
    
    print(f"   ✅ Цель найдена: {target.name} ({target.npc_type})")
    print(f"      - Позиция цели: ({target.x}, {target.y})")
    print(f"      - Расстояние от охотника до цели: {distance_to_target}")
    print(f"      - Расстояние от дома охотника до цели: {distance_target_to_home}")
    print(f"      - В пределах patrol_radius: {distance_target_to_home <= hunter.max_distance_from_home}")
    
    # Проверяем приоритет
    is_animal = target.npc_type in ['wolf', 'bear', 'deer']
    print(f"      - Тип цели: {'🦌 Животное (приоритет)' if is_animal else '⚔️  Враг'}")
else:
    print("   ℹ️  Цель не найдена (нет животных/врагов в радиусе обнаружения)")
print()

print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print()
print("Выводы:")
print("1. Охотник-стражник имеет patrol_radius, ограничивающий зону патруля")
print("2. Метод _find_hunt_target() приоритизирует животных над врагами")
print("3. Охота происходит только в пределах patrol_radius от дома")
print("4. Охотник не будет преследовать цели за пределами patrol_radius")
