"""
Оружейные умения.

Содержит:
- WeaponSkill - базовый класс оружейного умения
- BasicShot - базовый выстрел из лука
"""
import random
from game.systems.skills.base import Skill, SkillCategory


class WeaponSkill(Skill):
    """Базовый класс для умений, требующих определенный тип оружия"""

    required_weapon_type = None  # Тип оружия (WeaponType enum value)

    def _check_weapon(self, user):
        """
        Проверить, есть ли у пользователя требуемое оружие

        Returns:
            tuple: (bool, str) - есть оружие и сообщение
        """
        if self.required_weapon_type is None:
            return True, ""

        from game.inventory import EquipmentSlot, WeaponItem, WeaponType

        if not hasattr(user, 'inventory') or not user.inventory:
            return False, "Нет инвентаря"

        weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
        if not weapon or not isinstance(weapon, WeaponItem):
            return False, f"Требуется {self.required_weapon_type.value[0]} в руках"

        if weapon.weapon_type != self.required_weapon_type:
            return False, f"Требуется {self.required_weapon_type.value[0]}, а не {weapon.weapon_type.value[0]}"

        return True, ""

    def can_use(self, user):
        """Проверить возможность использования с учетом оружия"""
        # Сначала проверяем базовые условия
        base_check, base_msg = super().can_use(user)
        if not base_check:
            return False, base_msg

        # Затем проверяем оружие
        weapon_check, weapon_msg = self._check_weapon(user)
        if not weapon_check:
            return False, weapon_msg

        return True, ""


class BasicShot(WeaponSkill):
    """Выстрел - базовое умение для лука"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Выстрел",
            description="Базовый выстрел из лука. Доступен сразу при использовании лука",
            category=SkillCategory.GENERAL, tactical_range=8,
            stamina_cost=8,
            cooldown=0
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать базовый выстрел"""
        result = super().use(user, target)

        if target:
            # Получаем урон от оружия (без бонуса силы)
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость (вместо силы)
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.0 + (self.rank - 1) * 0.1  # 1.0x -> 1.4x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит (базовый шанс от удачи)
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Учитываем защиту
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_crit
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            result['message'] = f"{user.name} стреляет в {target.name} на {actual_damage} урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result
