"""
Загрузчик конфигурации игры
Обеспечивает централизованный доступ к параметрам баланса
"""
import json
import os
from pathlib import Path


class GameConfig:
    """Синглтон для хранения и доступа к конфигурации игры"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Загрузить конфигурацию из JSON файла"""
        config_path = Path(__file__).parent / "balance_config.json"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}, using defaults")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Warning: Config file is invalid JSON: {e}, using defaults")
            self._config = self._get_default_config()

    def _get_default_config(self):
        """Вернуть конфигурацию по умолчанию"""
        return {
            "player": {
                "base_stats": {
                    "health_per_constitution": 20,
                    "mana_per_spirit": 10,
                    "stamina_per_stat_point": 10,
                    "base_carry_weight": 50,
                    "carry_weight_per_strength": 5
                }
            },
            "combat": {
                "max_dodge_chance": 85,
                "max_crit_chance": 85,
                "crit_damage_multiplier": 2.0,
                "min_damage": 1,
                "defense_soft_cap": 50,
                "defense_reduction_after_cap": 0.5
            },
            "experience": {
                "base_exp_to_level": 100,
                "exp_scaling_factor": 1.35,
                "max_level": 40
            }
        }

    def get(self, *keys, default=None):
        """
        Получить значение из конфигурации по ключам

        Args:
            *keys: Путь к значению (например, 'combat', 'max_dodge_chance')
            default: Значение по умолчанию, если ключ не найден

        Returns:
            Значение из конфигурации или default
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_player_stat(self, stat_name, default=None):
        """Получить параметр игрока"""
        return self.get('player', 'base_stats', stat_name, default=default)

    def get_combat_param(self, param_name, default=None):
        """Получить параметр боя"""
        return self.get('combat', param_name, default=default)

    def get_skill_param(self, skill_name, param_name, default=None):
        """Получить параметр навыка"""
        return self.get('skills', skill_name, param_name, default=default)

    def get_npc_param(self, category, *keys, default=None):
        """Получить параметр NPC"""
        return self.get('npc', category, *keys, default=default)

    def get_item_param(self, *keys, default=None):
        """Получить параметр предмета"""
        return self.get('items', *keys, default=default)

    def get_economy_param(self, param_name, default=None):
        """Получить экономический параметр"""
        return self.get('economy', param_name, default=default)

    def get_regen_param(self, param_name, default=None):
        """Получить параметр регенерации"""
        return self.get('regeneration', param_name, default=default)

    def get_exp_param(self, param_name, default=None):
        """Получить параметр опыта"""
        return self.get('experience', param_name, default=default)

    def get_ui_param(self, param_name, default=None):
        """Получить параметр UI"""
        return self.get('ui', param_name, default=default)

    def reload(self):
        """Перезагрузить конфигурацию"""
        self._load_config()


# Глобальный экземпляр конфигурации
_config = None

def get_config():
    """Получить экземпляр конфигурации"""
    global _config
    if _config is None:
        _config = GameConfig()
    return _config


# Удобные функции-обертки для частого использования
def get_balance(section, *keys, default=None):
    """Получить значение из конфигурации баланса"""
    return get_config().get(section, *keys, default=default)
