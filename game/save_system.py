"""
Система сохранения и загрузки игры
"""
import json
import os
from datetime import datetime
import pickle


class SaveSystem:
    """Система сохранения/загрузки игрового прогресса"""

    SAVE_DIR = "saves"
    SAVE_EXTENSION = ".sav"

    @staticmethod
    def _ensure_save_dir():
        """Создать директорию для сохранений если её нет"""
        if not os.path.exists(SaveSystem.SAVE_DIR):
            os.makedirs(SaveSystem.SAVE_DIR)

    @staticmethod
    def _serialize_item(item):
        """
        Сериализовать предмет в словарь

        Args:
            item: Предмет для сериализации

        Returns:
            dict: Сериализованные данные предмета
        """
        from game.inventory import EquipmentItem, WeaponItem, ArmorItem

        data = {
            'name': item.name,
            'item_type': item.item_type,
            'value': item.value,
            'weight': item.weight,
            'description': getattr(item, 'description', ''),
        }

        if isinstance(item, EquipmentItem):
            data['is_equipment'] = True
            data['slot'] = item.slot.value
            data['required_level'] = item.required_level
            data['quality'] = item.quality.value
            data['stats_bonus'] = item.stats_bonus

            if isinstance(item, WeaponItem):
                data['weapon'] = True
                data['damage'] = item.damage
                data['weapon_type'] = item.weapon_type

            if isinstance(item, ArmorItem):
                data['armor'] = True
                data['defense'] = item.defense
                data['armor_type'] = item.armor_type

        # Для зелий и других простых предметов
        if hasattr(item, 'effect_type'):
            data['effect_type'] = item.effect_type
        if hasattr(item, 'effect_value'):
            data['effect_value'] = item.effect_value

        return data

    @staticmethod
    def _deserialize_item(data):
        """
        Десериализовать предмет из словаря

        Args:
            data: Словарь с данными предмета

        Returns:
            Item: Восстановленный предмет
        """
        from game.inventory import (
            Item, WeaponItem, ArmorItem, EquipmentItem,
            EquipmentSlot, ItemQuality
        )

        # Если это снаряжение
        if data.get('is_equipment', False):
            slot = EquipmentSlot(data['slot'])
            quality = ItemQuality(data['quality'])

            if data.get('weapon', False):
                item = WeaponItem(
                    name=data['name'],
                    value=data['value'],
                    weight=data['weight'],
                    slot=slot,
                    damage=data['damage'],
                    required_level=data['required_level'],
                    quality=quality,
                    stats_bonus=data.get('stats_bonus', {}),
                    weapon_type=data.get('weapon_type', 'Оружие')
                )
            elif data.get('armor', False):
                item = ArmorItem(
                    name=data['name'],
                    value=data['value'],
                    weight=data['weight'],
                    slot=slot,
                    defense=data['defense'],
                    required_level=data['required_level'],
                    quality=quality,
                    stats_bonus=data.get('stats_bonus', {}),
                    armor_type=data.get('armor_type', 'Доспех')
                )
            else:
                item = EquipmentItem(
                    name=data['name'],
                    value=data['value'],
                    weight=data['weight'],
                    slot=slot,
                    required_level=data['required_level'],
                    quality=quality,
                    stats_bonus=data.get('stats_bonus', {})
                )
        else:
            # Обычный предмет
            item = Item(
                name=data['name'],
                item_type=data['item_type'],
                value=data['value'],
                weight=data['weight']
            )

            # Восстанавливаем дополнительные атрибуты
            if 'effect_type' in data:
                item.effect_type = data['effect_type']
            if 'effect_value' in data:
                item.effect_value = data['effect_value']

        return item

    @staticmethod
    def save_game(game, save_name="autosave"):
        """
        Сохранить игру

        Args:
            game: Объект игры для сохранения
            save_name: Имя сохранения

        Returns:
            bool: True если сохранение успешно
        """
        try:
            SaveSystem._ensure_save_dir()

            save_data = {
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'player': SaveSystem._serialize_player(game.player),
                'game_state': {
                    'game_hour': game.game_hour,
                    'game_day': game.game_day,
                    'camera_x': game.camera_x,
                    'camera_y': game.camera_y,
                },
                'map': SaveSystem._serialize_map(game.game_map),
                'npcs': SaveSystem._serialize_npcs(game),
                'fog_of_war': SaveSystem._serialize_fog(game.fog_of_war),
            }

            # Добавляем данные квестов если есть
            if hasattr(game, 'quest_manager'):
                save_data['quests'] = SaveSystem._serialize_quest_manager(game.quest_manager)

            # Добавляем данные достижений если есть
            if hasattr(game, 'achievement_manager'):
                save_data['achievements'] = SaveSystem._serialize_achievement_manager(game.achievement_manager)

            save_path = os.path.join(
                SaveSystem.SAVE_DIR,
                save_name + SaveSystem.SAVE_EXTENSION
            )

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"Игра сохранена: {save_path}")
            return True

        except Exception as e:
            print(f"Ошибка при сохранении игры: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def _serialize_player(player):
        """Сериализовать данные игрока"""
        data = {
            'name': player.name,
            'x': player.x,
            'y': player.y,
            'level': player.level,
            'experience': player.experience,
            'experience_to_next_level': player.experience_to_next_level,
            'stat_points': player.stat_points,
            'health': player.health,
            'max_health': player.max_health,
            'mana': player.mana,
            'max_mana': player.max_mana,
            'stamina': player.stamina,
            'max_stamina': player.max_stamina,
            'is_resting': player.is_resting,
            'rest_threshold': player.rest_threshold,
            'stats': {
                'strength': player.strength,
                'dexterity': player.dexterity,
                'constitution': player.constitution,
                'spirit': player.spirit,
                'intelligence': player.intelligence,
                'luck': player.luck,
            },
            'inventory': SaveSystem._serialize_inventory(player.inventory),
        }

        # Сохраняем навыки если есть
        if hasattr(player, 'skill_manager'):
            data['skills'] = [skill.name for skill in player.skill_manager.learned_skills.values()]

        # Сохраняем дополнительные атрибуты
        if hasattr(player, 'enemies_killed'):
            data['enemies_killed'] = player.enemies_killed
        if hasattr(player, 'visited_location_types'):
            data['visited_location_types'] = list(player.visited_location_types)

        return data

    @staticmethod
    def _serialize_inventory(inventory):
        """Сериализовать инвентарь"""
        data = {
            'gold': inventory.gold,
            'max_slots': inventory.max_slots,
            'max_weight': inventory.max_weight,
            'items': []
        }

        # Сериализуем предметы
        for item, quantity in inventory.items.items():
            item_data = SaveSystem._serialize_item(item)
            item_data['quantity'] = quantity
            data['items'].append(item_data)

        # Сериализуем экипировку
        data['equipment'] = {}
        from game.inventory import EquipmentSlot
        for slot in EquipmentSlot:
            equipped = inventory.equipment.get(slot)
            if equipped:
                data['equipment'][slot.value] = SaveSystem._serialize_item(equipped)

        return data

    @staticmethod
    def _serialize_map(game_map):
        """Сериализовать карту (сохраняем все локации и биомы)"""
        # Сохраняем ВСЕ локации
        all_locations = []
        for location in game_map.locations:
            all_locations.append({
                'x': location.x,
                'y': location.y,
                'name': location.name,
                'location_type': location.location_type,
                'loot_collected': location.loot_collected,
            })

        # Сохраняем seed для воспроизводимости карты
        seed = getattr(game_map, 'seed', None)

        return {
            'seed': seed,
            'width': game_map.width,
            'height': game_map.height,
            'locations': all_locations,  # Сохраняем ВСЕ локации
        }

    @staticmethod
    def _serialize_npcs(game):
        """Сериализовать NPC"""
        npcs_data = {
            'guards': [],
            'merchants': [],
            'bandits': [],
            'miners': [],
            'undead': [],
        }

        # Сериализуем каждый тип NPC
        for guard in game.guards:
            if guard.is_alive:
                npcs_data['guards'].append({
                    'name': guard.name,
                    'x': guard.x,
                    'y': guard.y,
                    'level': guard.level,
                    'health': guard.health,
                    'max_health': guard.max_health,
                })

        for merchant in game.merchants:
            if merchant.is_alive:
                npcs_data['merchants'].append({
                    'name': merchant.name,
                    'x': merchant.x,
                    'y': merchant.y,
                    'level': merchant.level,
                    'health': merchant.health,
                    'inventory': SaveSystem._serialize_inventory(merchant.inventory),
                })

        for bandit in game.bandits:
            if bandit.is_alive:
                npcs_data['bandits'].append({
                    'name': bandit.name,
                    'x': bandit.x,
                    'y': bandit.y,
                    'level': bandit.level,
                    'health': bandit.health,
                    'camp_x': bandit.camp_x,
                    'camp_y': bandit.camp_y,
                })

        for miner in game.miners:
            if miner.is_alive:
                npcs_data['miners'].append({
                    'name': miner.name,
                    'x': miner.x,
                    'y': miner.y,
                    'level': miner.level,
                    'health': miner.health,
                    'mine_x': miner.mine_x,
                    'mine_y': miner.mine_y,
                })

        for undead in game.undead:
            if undead.is_alive:
                npcs_data['undead'].append({
                    'name': undead.name,
                    'x': undead.x,
                    'y': undead.y,
                    'level': undead.level,
                    'health': undead.health,
                    'ruins_x': undead.ruins_x,
                    'ruins_y': undead.ruins_y,
                })

        return npcs_data

    @staticmethod
    def _serialize_fog(fog_of_war):
        """Сериализовать туман войны"""
        explored = []
        for x in range(len(fog_of_war.explored)):
            for y in range(len(fog_of_war.explored[x])):
                if fog_of_war.explored[x][y]:
                    explored.append((x, y))

        return {'explored': explored}

    @staticmethod
    def _serialize_quest_manager(quest_manager):
        """Сериализовать менеджер квестов"""
        return {
            'active_quests': [q.quest_id for q in quest_manager.active_quests],
            'completed_quests': [q.quest_id for q in quest_manager.completed_quests],
        }

    @staticmethod
    def _serialize_achievement_manager(achievement_manager):
        """Сериализовать менеджер достижений"""
        unlocked = [a.achievement_id for a in achievement_manager.achievements if a.unlocked]
        return {'unlocked': unlocked}

    @staticmethod
    def load_game(save_name="autosave"):
        """
        Загрузить игру

        Args:
            save_name: Имя сохранения для загрузки

        Returns:
            dict: Загруженные данные или None если ошибка
        """
        try:
            save_path = os.path.join(
                SaveSystem.SAVE_DIR,
                save_name + SaveSystem.SAVE_EXTENSION
            )

            if not os.path.exists(save_path):
                print(f"Сохранение не найдено: {save_path}")
                return None

            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            print(f"Игра загружена: {save_path}")
            return save_data

        except Exception as e:
            print(f"Ошибка при загрузке игры: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_save_list():
        """
        Получить список доступных сохранений

        Returns:
            list: Список кортежей (имя_сохранения, дата_модификации)
        """
        SaveSystem._ensure_save_dir()

        saves = []
        for filename in os.listdir(SaveSystem.SAVE_DIR):
            if filename.endswith(SaveSystem.SAVE_EXTENSION):
                save_name = filename[:-len(SaveSystem.SAVE_EXTENSION)]
                save_path = os.path.join(SaveSystem.SAVE_DIR, filename)
                mod_time = os.path.getmtime(save_path)
                saves.append((save_name, mod_time))

        # Сортируем по дате модификации (новые первые)
        saves.sort(key=lambda x: x[1], reverse=True)

        return saves

    @staticmethod
    def delete_save(save_name):
        """
        Удалить сохранение

        Args:
            save_name: Имя сохранения для удаления

        Returns:
            bool: True если удаление успешно
        """
        try:
            save_path = os.path.join(
                SaveSystem.SAVE_DIR,
                save_name + SaveSystem.SAVE_EXTENSION
            )

            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"Сохранение удалено: {save_path}")
                return True

            return False

        except Exception as e:
            print(f"Ошибка при удалении сохранения: {e}")
            return False
