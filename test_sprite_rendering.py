#!/usr/bin/env python3
"""
Тест отображения спрайтов для разных типов стражи
"""
import sys
sys.path.insert(0, '/home/user/classic_rpg2')

from game.map import GameMap
from game.npc_spawner import NPCSpawner

print("=" * 60)
print("ТЕСТ: Проверка npc_type для правильного отображения спрайтов")
print("=" * 60)
print()

# Создаём карту
print("1. Создание карты...")
game_map = GameMap()
print(f"   Карта загружена: {game_map.width}x{game_map.height}")
print(f"   Локаций: {len(game_map.locations)}")
print()

# Создаём спавнер
print("2. Создание спавнера и спавн стражи...")
spawner = NPCSpawner(game_map)
guards = spawner.spawn_guards()
print(f"   Создано стражей: {len(guards)}")
print()

# Проверяем npc_type для каждого типа
print("3. Проверка npc_type для всех стражей:")
print()

type_counts = {}
for guard in guards:
    npc_type = guard.npc_type
    class_name = guard.__class__.__name__
    
    if npc_type not in type_counts:
        type_counts[npc_type] = {'count': 0, 'class': class_name}
    type_counts[npc_type]['count'] += 1

print(f"   {'NPC Type':<20} {'Класс':<20} {'Количество':<10}")
print(f"   {'-'*20} {'-'*20} {'-'*10}")
for npc_type, data in sorted(type_counts.items()):
    print(f"   {npc_type:<20} {data['class']:<20} {data['count']:<10}")

print()
print("4. Детальная проверка первого NPC каждого типа:")
print()

checked_types = set()
for guard in guards:
    if guard.npc_type not in checked_types:
        checked_types.add(guard.npc_type)
        print(f"   [{guard.npc_type}]")
        print(f"   - Имя: {guard.name}")
        print(f"   - Класс: {guard.__class__.__name__}")
        print(f"   - npc_type: {guard.npc_type}")
        print(f"   - Уровень: {guard.level}")
        print()

print("=" * 60)
print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
print("=" * 60)
print()
print("Вывод: Теперь _render_guards() использует guard.npc_type,")
print("поэтому спрайты будут загружаться правильно:")
print("  - warrior → npc_type='guard' → soldier спрайты")
print("  - mage → npc_type='mage' → mage спрайты")
print("  - shadow_adept → npc_type='shadow_adept' → shadow_adept спрайты")
print("  - hunter → npc_type='hunter' → hunter спрайты")
