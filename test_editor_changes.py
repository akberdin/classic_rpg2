#!/usr/bin/env python3
"""Test script to verify map editor changes."""

from map_editor.tools.generator import MapLocation, LOCATION_MINE, RESOURCE_TYPES

# Test 1: Create mine with resource type
print("Test 1: Creating mine with resource type...")
mine = MapLocation(
    x=10, y=20,
    location_type=LOCATION_MINE,
    name="Test Mine",
    resource_type="gold"
)
print(f"  Mine created: {mine.name} at ({mine.x}, {mine.y})")
print(f"  Resource type: {mine.resource_type}")
assert mine.resource_type == "gold", "Resource type not set correctly"
print("  ✓ Test 1 passed")

# Test 2: Verify resource types available
print("\nTest 2: Checking resource types...")
print(f"  Available resource types: {list(RESOURCE_TYPES.keys())}")
assert "copper" in RESOURCE_TYPES, "Copper not in resource types"
assert "iron" in RESOURCE_TYPES, "Iron not in resource types"
assert "silver" in RESOURCE_TYPES, "Silver not in resource types"
assert "gold" in RESOURCE_TYPES, "Gold not in resource types"
assert "mithril" in RESOURCE_TYPES, "Mithril not in resource types"
print("  ✓ Test 2 passed")

# Test 3: Test bidirectional connections
print("\nTest 3: Testing bidirectional connections...")
village = MapLocation(
    x=5, y=5,
    location_type="village",
    name="Test Village"
)
mine.add_connection(village.x, village.y)
village.add_connection(mine.x, mine.y)
assert mine.has_connection_to(village.x, village.y), "Connection from mine to village not created"
assert village.has_connection_to(mine.x, mine.y), "Connection from village to mine not created"
print(f"  ✓ Bidirectional connection established between {mine.name} and {village.name}")
print("  ✓ Test 3 passed")

# Test 4: Test connection removal
print("\nTest 4: Testing connection removal...")
mine.remove_connection(village.x, village.y)
village.remove_connection(mine.x, mine.y)
assert not mine.has_connection_to(village.x, village.y), "Connection from mine to village not removed"
assert not village.has_connection_to(mine.x, mine.y), "Connection from village to mine not removed"
print("  ✓ Bidirectional connection removed")
print("  ✓ Test 4 passed")

# Test 5: Test serialization with resource_type
print("\nTest 5: Testing serialization...")
mine_dict = mine.to_dict()
print(f"  Serialized mine: {mine_dict}")
assert "resource_type" in mine_dict, "resource_type not in serialized data"
assert mine_dict["resource_type"] == "gold", "resource_type not serialized correctly"
print("  ✓ Test 5 passed")

# Test 6: Test deserialization with resource_type
print("\nTest 6: Testing deserialization...")
mine_data = {
    'x': 15,
    'y': 25,
    'type': LOCATION_MINE,
    'name': 'Loaded Mine',
    'resource_type': 'mithril',
    'miners_count': 5,
    'respawn_time': 100
}
loaded_mine = MapLocation.from_dict(mine_data)
print(f"  Deserialized mine: {loaded_mine.name} at ({loaded_mine.x}, {loaded_mine.y})")
print(f"  Resource type: {loaded_mine.resource_type}")
assert loaded_mine.resource_type == "mithril", "resource_type not deserialized correctly"
print("  ✓ Test 6 passed")

print("\n" + "="*50)
print("All tests passed! ✓")
print("="*50)
