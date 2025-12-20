#!/usr/bin/env python3
"""
Тест разделения NPC по спискам
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner

print("=" * 70)
print("ТЕСТ: Разделение NPC по спискам")
print("=" * 70)
print()

# Создаём карту
print("1. Создание карты...")
game_map = GameMap()
print(f"   Карта загружена: {game_map.width}x{game_map.height}")
print()

# Создаём спавнер и получаем всех NPC
print("2. Спавн всех NPC...")
spawner = NPCSpawner(game_map)
npcs_dict = spawner.spawn_all_npcs()

print()
print("3. Проверка структуры словаря npcs:")
print()

for key, npc_list in npcs_dict.items():
    print(f"   {key}: {len(npc_list)} NPC")
    if npc_list:
        # Показываем типы первых 3 NPC в каждом списке
        sample = npc_list[:3]
        for npc in sample:
            print(f"      - {npc.name} (npc_type={npc.npc_type})")

print()
print("4. Проверка охотников:")
hunters = npcs_dict.get('hunters', [])
print(f"   Найдено охотников в списке 'hunters': {len(hunters)}")

if hunters:
    for hunter in hunters:
        print(f"   - {hunter.name}")
        print(f"     npc_type: {hunter.npc_type}")
        print(f"     max_distance_from_home: {hunter.max_distance_from_home}")
        print(f"     detection_range: {hunter.detection_range}")
else:
    print("   ⚠️  Список охотников пуст!")

print()
print("5. Проверка магов:")
mages = npcs_dict.get('mages', [])
print(f"   Найдено магов в списке 'mages': {len(mages)}")

if mages:
    for mage in mages:
        print(f"   - {mage.name} (npc_type={mage.npc_type})")
else:
    print("   Список магов пуст")

print()
print("6. Проверка воинов-стражников:")
guards = npcs_dict.get('guards', [])
print(f"   Найдено стражей в списке 'guards': {len(guards)}")

if guards:
    # Проверяем, что там только warriors и shadow_adepts
    warriors = [g for g in guards if g.npc_type == 'guard']
    shadow_adepts = [g for g in guards if g.npc_type == 'shadow_adept']
    others = [g for g in guards if g.npc_type not in ['guard', 'shadow_adept']]
    
    print(f"   - Warriors: {len(warriors)}")
    print(f"   - Shadow Adepts: {len(shadow_adepts)}")
    if others:
        print(f"   - Другие типы: {len(others)} (ОШИБКА!)")
        for other in others:
            print(f"      ! {other.name} (npc_type={other.npc_type})")

print()
print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print()
print("Ожидаемый результат:")
print("- hunters: содержит NPC с npc_type='hunter'")
print("- mages: содержит NPC с npc_type='mage'")
print("- guards: содержит NPC с npc_type='guard' и 'shadow_adept'")
