#!/usr/bin/env python3
"""
Тест интеграции AI охотника с животными
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner
from game.core.integration import create_ai_context
from game.npc.animal import Wolf

print("=" * 70)
print("ТЕСТ: Интеграция AI охотника с животными")
print("=" * 70)
print()

# Имитация объекта game
class MockGame:
    def __init__(self, game_map, npcs_dict):
        self.game_map = game_map
        self.guards = npcs_dict.get('guards', [])
        self.merchants = npcs_dict.get('merchants', [])
        self.mages = npcs_dict.get('mages', [])
        self.hunters = npcs_dict.get('hunters', [])
        self.bandits = npcs_dict.get('bandits', [])
        self.miners = npcs_dict.get('miners', [])
        self.undead = npcs_dict.get('undead', [])
        self.alchemists = npcs_dict.get('alchemists', [])
        self.necromancers = npcs_dict.get('necromancers', [])
        self.animals = npcs_dict.get('animals', [])
        self.player = None  # Для простоты
        
        # Mock для game_time
        class MockGameTime:
            game_hour = 12.0
        self.game_time = MockGameTime()

# Создаём карту
print("1. Создание карты и NPC...")
game_map = GameMap()
spawner = NPCSpawner(game_map)
npcs_dict = spawner.spawn_all_npcs()

# Создаём mock игры
game = MockGame(game_map, npcs_dict)

print(f"   Guards: {len(game.guards)}")
print(f"   Mages: {len(game.mages)}")
print(f"   Hunters: {len(game.hunters)}")
print(f"   Animals: {len(game.animals)}")
print()

# Находим охотника
if not game.hunters:
    print("   ❌ Охотников нет!")
    sys.exit(1)

hunter = game.hunters[0]
print(f"2. Охотник: {hunter.name}")
print(f"   Позиция: ({hunter.x}, {hunter.y})")
print(f"   Дом: ({hunter.home_x}, {hunter.home_y})")
print()

# Создаём волка рядом с охотником
print("3. Создание волка рядом с охотником...")
wolf_x = hunter.home_x + 3
wolf_y = hunter.home_y + 2
wolf = Wolf("Тестовый волк", wolf_x, wolf_y, level=5, spawn_x=wolf_x, spawn_y=wolf_y)
game.animals.append(wolf)

distance_to_wolf = abs(hunter.x - wolf.x) + abs(hunter.y - wolf.y)
distance_wolf_to_home = abs(wolf.x - hunter.home_x) + abs(wolf.y - hunter.home_y)

print(f"   Волк: {wolf.name}")
print(f"   Позиция: ({wolf.x}, {wolf.y})")
print(f"   Расстояние до охотника: {distance_to_wolf}")
print(f"   Расстояние до дома охотника: {distance_wolf_to_home}")
print(f"   В пределах patrol_radius ({hunter.max_distance_from_home}): {distance_wolf_to_home <= hunter.max_distance_from_home}")
print(f"   В пределах detection_range ({hunter.detection_range}): {distance_to_wolf <= hunter.detection_range}")
print()

# Создаём AIContext
print("4. Создание AIContext...")
ai_context = create_ai_context(game)
print(f"   Всего NPC в контексте: {len(ai_context.all_npcs)}")

# Проверяем, что волк есть в all_npcs
wolves_in_context = [npc for npc in ai_context.all_npcs if npc.npc_type == 'wolf']
print(f"   Волков в контексте: {len(wolves_in_context)}")

if wolf in ai_context.all_npcs:
    print(f"   ✅ Тестовый волк присутствует в AIContext")
else:
    print(f"   ❌ Тестовый волк НЕ найден в AIContext!")
print()

# Проверяем поиск цели
print("5. Проверка поиска цели охотником...")
target = hunter._find_hunt_target(ai_context.all_npcs)

if target:
    print(f"   ✅ Цель найдена: {target.name}")
    print(f"      npc_type: {target.npc_type}")
    print(f"      Это наш тестовый волк: {target == wolf}")
else:
    print(f"   ❌ Цель не найдена!")
    print(f"   Дебаг:")
    print(f"      - Волк жив: {wolf.is_alive}")
    print(f"      - Расстояние до волка: {distance_to_wolf} <= {hunter.detection_range}")
    print(f"      - Волк в пределах patrol_radius: {distance_wolf_to_home} <= {hunter.max_distance_from_home}")
print()

# Симулируем один шаг AI
print("6. Симуляция update_ai охотника...")
initial_state = hunter.state
hunter.update_ai(ai_context)
new_state = hunter.state

print(f"   Начальное состояние: {initial_state}")
print(f"   Состояние после update: {new_state}")

if hunter.hunt_target:
    print(f"   ✅ Охотник взял цель: {hunter.hunt_target.name}")
else:
    print(f"   ⚠️  Охотник не взял цель")

print()
print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
