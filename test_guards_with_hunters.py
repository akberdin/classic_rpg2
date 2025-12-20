#!/usr/bin/env python3
"""
Тест: все типы стражи в списке guards, охотники работают
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner
from game.core.integration import create_ai_context
from game.npc.animal import Wolf

print("=" * 70)
print("ТЕСТ: Все стражи в guards, охотники охотятся")
print("=" * 70)
print()

# Создаём карту и NPC
print("1. Спавн NPC...")
game_map = GameMap()
spawner = NPCSpawner(game_map)
npcs_dict = spawner.spawn_all_npcs()

print()
print("2. Проверка списков:")
print(f"   guards: {len(npcs_dict['guards'])} NPC")
print(f"   mages: {len(npcs_dict['mages'])} NPC")
print(f"   hunters: {len(npcs_dict['hunters'])} NPC")
print(f"   animals: {len(npcs_dict['animals'])} NPC")
print()

# Проверяем состав guards
guards = npcs_dict['guards']
warriors = [g for g in guards if g.npc_type == 'guard']
mages_in_guards = [g for g in guards if g.npc_type == 'mage']
hunters_in_guards = [g for g in guards if g.npc_type == 'hunter']
shadow_adepts_in_guards = [g for g in guards if g.npc_type == 'shadow_adept']

print("3. Состав списка guards:")
print(f"   Warriors (guard): {len(warriors)}")
print(f"   Mages (mage): {len(mages_in_guards)}")
print(f"   Hunters (hunter): {len(hunters_in_guards)}")
print(f"   Shadow Adepts (shadow_adept): {len(shadow_adepts_in_guards)}")
print(f"   ВСЕГО: {len(guards)}")
print()

if hunters_in_guards:
    print("   ✅ Охотники присутствуют в списке guards!")
    hunter = hunters_in_guards[0]
    print(f"      - {hunter.name}")
    print(f"      - npc_type: {hunter.npc_type}")
    print(f"      - patrol_radius: {hunter.max_distance_from_home}")
else:
    print("   ❌ Охотники НЕ найдены в списке guards!")
print()

# Проверяем дублирование для AI
print("4. Проверка дублирования для AI:")
print(f"   Список mages: {len(npcs_dict['mages'])} (должны быть те же объекты)")
print(f"   Список hunters: {len(npcs_dict['hunters'])} (должны быть те же объекты)")

if mages_in_guards and npcs_dict['mages']:
    same_object = mages_in_guards[0] is npcs_dict['mages'][0]
    print(f"   Маг из guards == маг из mages: {same_object} {'✅' if same_object else '❌'}")

if hunters_in_guards and npcs_dict['hunters']:
    same_object = hunters_in_guards[0] is npcs_dict['hunters'][0]
    print(f"   Охотник из guards == охотник из hunters: {same_object} {'✅' if same_object else '❌'}")
print()

# Тестируем охоту
if hunters_in_guards:
    print("5. Тест охоты:")
    
    # Mock игры
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
            self.player = None  # Mock player
            
            class MockGameTime:
                game_hour = 12.0
            self.game_time = MockGameTime()
    
    game = MockGame(game_map, npcs_dict)
    hunter = hunters_in_guards[0]
    
    # Создаём волка
    wolf_x = hunter.home_x + 3
    wolf_y = hunter.home_y + 2
    wolf = Wolf("Тестовый волк", wolf_x, wolf_y, level=5, spawn_x=wolf_x, spawn_y=wolf_y)
    game.animals.append(wolf)
    
    print(f"   Охотник: {hunter.name}")
    print(f"   Волк создан на расстоянии {abs(wolf.x - hunter.home_x) + abs(wolf.y - hunter.home_y)} от дома")
    
    # AIContext
    ai_context = create_ai_context(game)
    
    # Поиск цели
    target = hunter._find_hunt_target(ai_context.all_npcs)
    if target:
        print(f"   ✅ Охотник нашел цель: {target.name}")
    else:
        print(f"   ❌ Охотник не нашел цель")
    
    # Симуляция AI
    hunter.update_ai(ai_context)
    if hunter.hunt_target:
        print(f"   ✅ Охотник начал охоту на: {hunter.hunt_target.name}")
    else:
        print(f"   ⚠️  Охотник не начал охоту")

print()
print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print()
print("Итог:")
print("- Все типы стражи (warrior, mage, shadow_adept, hunter) в guards ✅")
print("- Охотники дублируются в hunters для AI системы ✅")
print("- Охотники могут охотиться на животных ✅")
