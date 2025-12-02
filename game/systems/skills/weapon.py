"""
Оружейные умения.

Содержит:
- WeaponSkill - базовый класс оружейного умения
- PreciseShot - точный выстрел (лук)
- RapidFire - скорострельность (лук)
- PiercingArrow - пронзающая стрела (лук)
- Backstab - удар в спину (кинжал)
- BleedingCut - кровоточащий порез (кинжал)
- ShadowStep - шаг сквозь тень (кинжал)
- WhirlwindStrike - вихревой удар (меч)
- ShieldBreaker - пробивание щита (меч)
- BladeDance - танец клинков (меч)
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import PoisonEffect, StatusEffect


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


# --- УМЕНИЯ ДЛЯ ЛУКА ---

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

        if target and user.can_attack(target):
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


class PreciseShot(WeaponSkill):
    """Точный выстрел - высокий шанс критического попадания"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Точный выстрел",
            description="Прицельный выстрел с высоким шансом крита. Шанс растет с рангом",
            category=SkillCategory.HUNTER, tactical_range=8,
            stamina_cost=12,
            cooldown=2
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать точный выстрел"""
        result = super().use(user, target)

        if target and user.can_attack(target):
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
            damage_multiplier = 1.2 + (self.rank - 1) * 0.2  # 1.2x -> 2.0x
            total_damage = int(base_damage * damage_multiplier)

            # Высокий шанс крита, растущий от ранга
            base_crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            skill_crit_bonus = 30 + (self.rank - 1) * 15  # +30% -> +90%
            crit_chance = min(95.0, base_crit_chance + skill_crit_bonus)  # Максимум 95%
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
            result['message'] = f"{user.name} совершает точный выстрел по {target.name} на {actual_damage} урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class RapidFire(WeaponSkill):
    """Быстрая стрельба - несколько выстрелов за ход"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Быстрая стрельба",
            description="Выпускает несколько стрел за один ход. Количество растет с рангом",
            category=SkillCategory.HUNTER, tactical_range=8,
            stamina_cost=20,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать быструю стрельбу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Количество выстрелов = 2 + (ранг - 1)
            num_shots = 2 + (self.rank - 1)  # 2 -> 6 выстрелов

            # Получаем урон от оружия (без бонуса силы)
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage_per_shot = weapon_damage + dexterity

            # Получаем шанс крита игрока
            base_crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0

            target_defense = target.get_total_defense()
            total_damage = 0
            crit_count = 0

            # Каждый выстрел с отдельным шансом крита
            for _ in range(num_shots):
                shot_damage = base_damage_per_shot

                # Проверяем крит для каждого выстрела отдельно
                is_crit = random.random() < (base_crit_chance / 100)
                if is_crit:
                    shot_damage = int(shot_damage * 2)
                    crit_count += 1

                # Применяем защиту
                actual_shot_damage = max(1, shot_damage - target_defense)
                total_damage += actual_shot_damage

            target.take_damage(total_damage)

            result['damage'] = total_damage
            result['shots'] = num_shots
            result['crits'] = crit_count
            crit_text = f" ({crit_count} крит!)" if crit_count > 0 else ""
            result['message'] = f"{user.name} выпускает {num_shots} стрел в {target.name} на {total_damage} общего урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class PiercingArrow(WeaponSkill):
    """Пронзающая стрела - игнорирует часть брони"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Пронзающая стрела",
            description="Стрела пробивает броню противника. Пробитие растет с рангом",
            category=SkillCategory.HUNTER, tactical_range=8,
            stamina_cost=15,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать пронзающую стрелу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия (без бонуса силы)
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.5 + (self.rank - 1) * 0.25  # 1.5x -> 2.5x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит (базовый шанс от удачи)
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Пробитие брони растет с рангом
            armor_penetration = 0.4 + (self.rank - 1) * 0.1  # 40% -> 80%

            # Применяем пробитие брони
            target_defense = target.get_total_defense()
            effective_defense = int(target_defense * (1 - armor_penetration))
            actual_damage = max(1, total_damage - effective_defense)

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = is_crit
            result['armor_penetration'] = int(armor_penetration * 100)
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            result['message'] = f"{user.name} выпускает пронзающую стрелу в {target.name} на {actual_damage} урона{crit_text} (пробитие {int(armor_penetration * 100)}% брони)!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class LongRangeShot(WeaponSkill):
    """Дальний выстрел - удвоенная дальность, не работает вблизи"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Дальний выстрел",
            description="Удваивает дальность выстрела. Урон растет с рангом. Не может применяться ближе 3 клеток до цели",
            category=SkillCategory.HUNTER, tactical_range=16,  # Удвоенная дальность от базовой 8
            stamina_cost=15,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.BOW
        self.min_range = 3  # Минимальная дистанция для использования

    def can_use(self, user, target=None):
        """Проверить возможность использования с учетом минимальной дистанции"""
        # Проверяем базовые условия и наличие оружия
        base_check, base_msg = super().can_use(user)
        if not base_check:
            return False, base_msg

        # Проверяем дистанцию до цели (только если цель указана)
        if target:
            distance = max(abs(user.x - target.x), abs(user.y - target.y))
            if distance < self.min_range:
                return False, f"Слишком близко для дальнего выстрела! Минимальная дистанция: {self.min_range}"

        return True, ""

    def use(self, user, target=None):
        """Использовать дальний выстрел"""
        # Проверяем минимальную дистанцию
        if target:
            distance = max(abs(user.x - target.x), abs(user.y - target.y))
            if distance < self.min_range:
                return {
                    'success': False,
                    'message': f"Слишком близко! Дальний выстрел требует минимум {self.min_range} клеток дистанции"
                }

        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия (без бонуса силы)
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга (растет урон, но не дальность)
            damage_multiplier = 1.5 + (self.rank - 1) * 0.3  # 1.5x -> 2.7x
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
            result['message'] = f"{user.name} совершает дальний выстрел по {target.name} на {actual_damage} урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


# --- УМЕНИЯ ДЛЯ КИНЖАЛА/НОЖА ---

class Backstab(WeaponSkill):
    """Удар в спину - огромный урон при внезапной атаке"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Удар в спину",
            description="Коварный удар с огромным уроном. Множитель растет с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=18,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.KNIFE

    def use(self, user, target=None):
        """Использовать удар в спину"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            dex_bonus = dexterity * 0.5

            # Огромный множитель урона
            damage_multiplier = 2.5 + (self.rank - 1) * 0.5  # 2.5x -> 4.5x

            total_damage = int((base_damage + dex_bonus) * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense // 2)  # Игнорирует половину брони

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['message'] = f"{user.name} наносит коварный удар в спину {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class BleedingCut(WeaponSkill):
    """Кровоточащий порез - наносит урон и вызывает кровотечение"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Кровоточащий порез",
            description="Глубокий порез вызывает кровотечение. Длительность растет с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=14,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.KNIFE

    def use(self, user, target=None):
        """Использовать кровоточащий порез"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            damage_multiplier = 1.2 + (self.rank - 1) * 0.15

            total_damage = int(base_damage * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Кровотечение (как улучшенный яд)
            bleed_duration = 3 + (self.rank - 1)  # 3-7 ходов
            bleed_damage = 4 + (self.rank - 1) * 3  # 4-16 урона/ход

            bleed = PoisonEffect(duration=bleed_duration, damage_per_turn=bleed_damage)
            bleed.name = "Кровотечение"
            bleed.description = f"Теряет {bleed_damage} здоровья каждый ход"

            # Добавляем эффект в правильное место
            if hasattr(target, 'skill_manager') and hasattr(target.skill_manager, 'add_status_effect'):
                # Для игрока - используем add_status_effect для правильной инициализации
                target.skill_manager.add_status_effect(bleed)
            elif hasattr(target, 'skill_manager'):
                # Для игрока - в skill_manager (fallback)
                target.skill_manager.status_effects.append(bleed)
            else:
                # Для NPC без skill_manager - в status_effects
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(bleed)

            result['damage'] = actual_damage
            result['bleed_applied'] = True
            result['message'] = f"{user.name} наносит глубокий порез {target.name} на {actual_damage} урона и вызывает кровотечение ({bleed_damage}/ход на {bleed_duration} ходов)!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class ShadowStep(WeaponSkill):
    """Шаг тени - уклонение и контратака"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Шаг тени",
            description="Уклоняетесь и наносите контрудар. Бонус к уклонению растет с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=16,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.KNIFE

    def use(self, user, target=None):
        """Использовать шаг тени"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            dex_bonus = dexterity * 0.4

            # Множитель урона
            damage_multiplier = 1.4 + (self.rank - 1) * 0.2  # 1.4x -> 2.2x

            total_damage = int((base_damage + dex_bonus) * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Временный бонус к уклонению (через эффект)
            dodge_bonus = 20 + (self.rank - 1) * 10  # +20% -> +60%
            dodge_duration = 1 + (self.rank - 1) // 2  # 1-3 хода

            # Создаем эффект уклонения
            dodge_effect = StatusEffect(
                name="Тень",
                duration=dodge_duration,
                description=f"+{dodge_bonus}% к уклонению"
            )
            dodge_effect.dodge_bonus = dodge_bonus

            # Добавляем эффект в правильное место
            if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
                # Для игрока - используем add_status_effect для правильной инициализации
                user.skill_manager.add_status_effect(dodge_effect)
            elif hasattr(user, 'skill_manager'):
                # Для игрока - в skill_manager (fallback)
                user.skill_manager.status_effects.append(dodge_effect)
            else:
                # Для NPC без skill_manager - в status_effects
                if not hasattr(user, 'status_effects'):
                    user.status_effects = []
                user.status_effects.append(dodge_effect)

            result['damage'] = actual_damage
            result['dodge_bonus'] = dodge_bonus
            result['message'] = f"{user.name} совершает шаг тени и наносит {target.name} {actual_damage} урона! (+{dodge_bonus}% к уклонению на {dodge_duration} ходов)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


# --- УМЕНИЯ ДЛЯ МЕЧА ---

class WhirlwindStrike(WeaponSkill):
    """Вихревой удар - мощная круговая атака"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Вихревой удар",
            description="Мощный круговой удар мечом. Урон растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=22,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.SWORD

    def use(self, user, target=None):
        """Использовать вихревой удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            strength = user.get_effective_strength() if hasattr(user, 'get_effective_strength') else getattr(user, 'strength', 10)
            str_bonus = strength * 0.4

            # Высокий множитель урона
            damage_multiplier = 2.0 + (self.rank - 1) * 0.4  # 2.0x -> 3.6x

            total_damage = int((base_damage + str_bonus) * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['message'] = f"{user.name} совершает вихревой удар по {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class ShieldBreaker(WeaponSkill):
    """Разрушитель щита - снижает защиту противника"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Разрушитель щита",
            description="Мощный удар, снижающий защиту врага. Эффект растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=18,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.SWORD

    def use(self, user, target=None):
        """Использовать разрушитель щита"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            damage_multiplier = 1.6 + (self.rank - 1) * 0.2  # 1.6x -> 2.4x

            total_damage = int(base_damage * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Снижение защиты (как отрицательный эффект)
            defense_reduction = 5 + (self.rank - 1) * 3  # -5 -> -17 защиты
            armor_break_duration = 3 + (self.rank - 1)  # 3-7 ходов

            armor_break = StatusEffect(
                name="Сломленная броня",
                duration=armor_break_duration,
                description=f"-{defense_reduction} защиты"
            )
            armor_break.defense_reduction = defense_reduction

            # Добавляем эффект в правильное место
            if hasattr(target, 'skill_manager'):
                # Для игрока - в skill_manager
                target.skill_manager.status_effects.append(armor_break)
            else:
                # Для NPC без skill_manager - в status_effects
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(armor_break)

            result['damage'] = actual_damage
            result['defense_reduced'] = defense_reduction
            result['message'] = f"{user.name} наносит сокрушительный удар {target.name} на {actual_damage} урона и снижает защиту на {defense_reduction} на {armor_break_duration} ходов!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class BladeDance(WeaponSkill):
    """Танец клинка - серия быстрых ударов"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Танец клинка",
            description="Серия быстрых ударов мечом. Количество ударов растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=25,
            cooldown=5
        )
        self.required_weapon_type = WeaponType.SWORD

    def use(self, user, target=None):
        """Использовать танец клинка"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Количество ударов зависит от ранга
            num_hits = 3 + (self.rank - 1)  # 3-7 ударов

            base_damage = user.get_total_damage()
            strength = user.get_effective_strength() if hasattr(user, 'get_effective_strength') else getattr(user, 'strength', 10)
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            str_bonus = strength * 0.2
            dex_bonus = dexterity * 0.2

            damage_per_hit = int((base_damage + str_bonus + dex_bonus) * 0.5)  # 50% за удар
            target_defense = target.get_total_defense()

            total_damage = 0
            crits = 0
            for _ in range(num_hits):
                # Каждый удар имеет шанс крита
                is_crit = random.random() < 0.2  # 20% шанс
                hit_damage = damage_per_hit
                if is_crit:
                    hit_damage = int(hit_damage * 1.5)
                    crits += 1
                actual_hit = max(1, hit_damage - target_defense // num_hits)
                total_damage += actual_hit

            target.take_damage(total_damage)

            result['damage'] = total_damage
            result['hits'] = num_hits
            result['crits'] = crits
            crit_text = f" ({crits} крит!)" if crits > 0 else ""
            result['message'] = f"{user.name} исполняет танец клинка: {num_hits} ударов по {target.name} на {total_damage} урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


# --- УМЕНИЯ ДЛЯ КОПЬЯ ---

class LungeStrike(WeaponSkill):
    """Пронзающий выпад - мощный выпад с увеличенной дальностью"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Пронзающий выпад",
            description="Мощный выпад с увеличенной дальностью. Наносит урон и отталкивает врага",
            category=SkillCategory.HUNTER, tactical_range=2,
            stamina_cost=16,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.SPEAR

    def use(self, user, target=None):
        """Использовать пронзающий выпад"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.6 + (self.rank - 1) * 0.25  # 1.6x -> 2.6x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Учитываем защиту
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Шанс отталкивания растет с рангом
            knockback_chance = 0.5 + (self.rank - 1) * 0.1  # 50% -> 90%
            knockback_success = random.random() < knockback_chance

            result['damage'] = actual_damage
            result['critical'] = is_crit
            result['knockback'] = knockback_success
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            knockback_text = " (отброшен!)" if knockback_success else ""
            result['message'] = f"{user.name} совершает пронзающий выпад по {target.name} на {actual_damage} урона!{crit_text}{knockback_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class SpearSweep(WeaponSkill):
    """Вихревое вращение - круговая атака копьем"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Вихревое вращение",
            description="Круговая атака копьем. Атакует всех врагов в радиусе",
            category=SkillCategory.HUNTER, tactical_range=2,
            stamina_cost=20,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.SPEAR
        self.aoe_range = 2

    def use(self, user, target=None):
        """Использовать вихревое вращение"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.3 + (self.rank - 1) * 0.2  # 1.3x -> 2.1x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Учитываем защиту
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Шанс замедления растет с рангом
            slow_chance = 0.3 + (self.rank - 1) * 0.1  # 30% -> 70%
            if random.random() < slow_chance:
                from game.systems.skills.effects import SlowEffect
                slow_effect = SlowEffect(duration=1)
                if hasattr(user, 'skill_manager'):
                    user.skill_manager.add_status_effect(slow_effect)
                elif hasattr(target, 'skill_manager'):
                    target.skill_manager.add_status_effect(slow_effect)

            result['damage'] = actual_damage
            result['critical'] = is_crit
            result['aoe'] = True
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            result['message'] = f"{user.name} вращает копье по {target.name} на {actual_damage} урона!{crit_text}"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class ArmorBreach(WeaponSkill):
    """Разрыв брони - точный удар в слабое место"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Разрыв брони",
            description="Точный удар в слабое место. Пробивает броню и накладывает уязвимость",
            category=SkillCategory.HUNTER, tactical_range=2,
            stamina_cost=18,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.SPEAR

    def use(self, user, target=None):
        """Использовать разрыв брони"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.4 + (self.rank - 1) * 0.2  # 1.4x -> 2.2x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Пробитие брони растет с рангом
            armor_penetration = 0.5 + (self.rank - 1) * 0.1  # 50% -> 90%

            # Применяем пробитие брони
            target_defense = target.get_total_defense()
            effective_defense = int(target_defense * (1 - armor_penetration))
            actual_damage = max(1, total_damage - effective_defense)

            target.take_damage(actual_damage)

            # Накладываем эффект снижения защиты
            defense_reduction = 8 + (self.rank - 1) * 4  # 8 -> 24
            duration = 3 + (self.rank - 1)  # 3 -> 7
            from game.systems.skills.effects import ArmorBreakEffect
            armor_break_effect = ArmorBreakEffect(duration=duration, defense_reduction=defense_reduction)
            if hasattr(target, 'skill_manager'):
                target.skill_manager.add_status_effect(armor_break_effect)

            result['damage'] = actual_damage
            result['critical'] = is_crit
            result['armor_penetration'] = int(armor_penetration * 100)
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            result['message'] = f"{user.name} пробивает броню {target.name} на {actual_damage} урона!{crit_text} (пробитие {int(armor_penetration * 100)}% брони, -{defense_reduction} защиты)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


# --- ДОПОЛНИТЕЛЬНЫЕ УМЕНИЯ ДЛЯ ТЕНИ (SHADOW) ---

class DeadlyPoison(WeaponSkill):
    """Смертельный яд - накладывает очень мощный яд, усиливающийся со временем"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Смертельный яд",
            description="Накладывает мощный яд, урон которого растет каждый ход. Длительность и урон растут с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=25,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.KNIFE

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Яд 8 урона/ход (растет на 2/ход) на 4 хода",
            "Ранг 2: Яд 12 урона/ход (растет на 3/ход) на 5 ходов",
            "Ранг 3: Яд 16 урона/ход (растет на 4/ход) на 6 ходов",
            "Ранг 4: Яд 20 урона/ход (растет на 5/ход) на 7 ходов",
            "Ранг 5: Яд 24 урона/ход (растет на 6/ход) на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать смертельный яд"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            damage_multiplier = 1.0 + (self.rank - 1) * 0.1

            total_damage = int(base_damage * damage_multiplier)
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Смертельный яд - урон растет каждый ход
            poison_duration = 4 + (self.rank - 1)  # 4-8 ходов
            initial_poison_damage = 8 + (self.rank - 1) * 4  # 8-24 урона/ход
            damage_increase = 2 + (self.rank - 1)  # Рост урона на 2-6 в ход

            # Создаем специальный эффект яда
            class EscalatingPoison(PoisonEffect):
                def __init__(self, duration, initial_damage, damage_increase):
                    super().__init__(duration, initial_damage)
                    self.name = "Смертельный яд"
                    self.damage_increase = damage_increase
                    self.current_damage = initial_damage

                def tick(self, character):
                    message = super().tick(character)
                    self.current_damage += self.damage_increase
                    self.damage_per_turn = self.current_damage
                    return message

            poison = EscalatingPoison(poison_duration, initial_poison_damage, damage_increase)

            # Добавляем эффект
            if hasattr(target, 'skill_manager') and hasattr(target.skill_manager, 'add_status_effect'):
                target.skill_manager.add_status_effect(poison)
            elif hasattr(target, 'skill_manager'):
                target.skill_manager.status_effects.append(poison)
            else:
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(poison)

            result['damage'] = actual_damage
            result['poison_applied'] = True
            result['message'] = f"{user.name} наносит удар с смертельным ядом {target.name} на {actual_damage} урона! Яд начинается с {initial_poison_damage} урона/ход и усиливается на {damage_increase} каждый ход!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class Stealth(WeaponSkill):
    """Скрытность - временно становится невидимым для врагов"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Скрытность",
            description="Сливаетесь с тенями, становясь невидимым. Агрессивные враги не атакуют. Длительность растет с рангом",
            category=SkillCategory.SHADOW,
            stamina_cost=20,
            cooldown=8
        )
        self.required_weapon_type = WeaponType.KNIFE

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Невидимость на 3 хода",
            "Ранг 2: Невидимость на 4 хода",
            "Ранг 3: Невидимость на 5 ходов",
            "Ранг 4: Невидимость на 6 ходов",
            "Ранг 5: Невидимость на 7 ходов"
        ]

    def use(self, user, target=None):
        """Использовать скрытность"""
        result = super().use(user, target)

        # Длительность невидимости растет с рангом
        stealth_duration = 3 + (self.rank - 1)  # 3-7 ходов

        # Создаем эффект невидимости
        stealth_effect = StatusEffect(
            name="Невидимость",
            duration=stealth_duration,
            description="Невидим для врагов"
        )
        stealth_effect.is_invisible = True

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(stealth_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(stealth_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(stealth_effect)

        result['stealth_applied'] = True
        result['duration'] = stealth_duration
        result['message'] = f"{user.name} сливается с тенями и становится невидимым на {stealth_duration} ходов!"

        return result


class CriticalStrike(WeaponSkill):
    """Критический удар - гарантированный критический удар с огромным множителем"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Критический удар",
            description="Точный удар в жизненно важную точку. Гарантированный крит с огромным уроном",
            category=SkillCategory.SHADOW,
            stamina_cost=30,
            cooldown=7
        )
        self.required_weapon_type = WeaponType.KNIFE

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x3.0 (гарантированный крит)",
            "Ранг 2: Урон x3.5 (гарантированный крит)",
            "Ранг 3: Урон x4.0 (гарантированный крит)",
            "Ранг 4: Урон x4.5 (гарантированный крит)",
            "Ранг 5: Урон x5.0 (гарантированный крит)"
        ]

    def use(self, user, target=None):
        """Использовать критический удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            dex_bonus = dexterity * 0.6

            # Огромный множитель урона, растущий с рангом
            damage_multiplier = 3.0 + (self.rank - 1) * 0.5  # 3.0x -> 5.0x

            total_damage = int((base_damage + dex_bonus) * damage_multiplier)
            target_defense = target.get_total_defense()
            # Игнорирует большую часть брони
            effective_defense = target_defense // 3
            actual_damage = max(1, total_damage - effective_defense)

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['critical'] = True
            result['message'] = f"{user.name} наносит КРИТИЧЕСКИЙ УДАР по {target.name} на {actual_damage} урона! СМЕРТЕЛЬНО!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class ShadowAgility(WeaponSkill):
    """Ловкость теней - значительно увеличивает ловкость и уклонение"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Ловкость теней",
            description="Черпаете силу из теней, значительно повышая ловкость и уклонение",
            category=SkillCategory.SHADOW,
            stamina_cost=18,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.KNIFE

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +8 Ловкость, +25% уклонение на 4 хода",
            "Ранг 2: +12 Ловкость, +35% уклонение на 5 ходов",
            "Ранг 3: +16 Ловкость, +45% уклонение на 6 ходов",
            "Ранг 4: +20 Ловкость, +55% уклонение на 7 ходов",
            "Ранг 5: +24 Ловкость, +65% уклонение на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать ловкость теней"""
        result = super().use(user, target)

        # Бонус к ловкости и уклонению растет с рангом
        dexterity_boost = 8 + (self.rank - 1) * 4  # 8-24
        dodge_bonus = 25 + (self.rank - 1) * 10  # 25%-65%
        duration = 4 + (self.rank - 1)  # 4-8 ходов

        # Создаем эффект
        agility_effect = StatusEffect(
            name="Ловкость теней",
            duration=duration,
            description=f"+{dexterity_boost} Ловкость, +{dodge_bonus}% уклонение"
        )
        agility_effect.dexterity_boost = dexterity_boost
        agility_effect.dodge_bonus = dodge_bonus

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(agility_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(agility_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(agility_effect)

        result['dexterity_boost'] = dexterity_boost
        result['dodge_bonus'] = dodge_bonus
        result['duration'] = duration
        result['message'] = f"{user.name} активирует ловкость теней! +{dexterity_boost} Ловкость, +{dodge_bonus}% уклонение на {duration} ходов!"

        return result


# --- ДОПОЛНИТЕЛЬНЫЕ УМЕНИЯ ДЛЯ ВОИНА (WARRIOR) ---

class IronStance(WeaponSkill):
    """Железная стойка - увеличивает защиту и снижает получаемый урон"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Железная стойка",
            description="Принимаете защитную стойку, значительно повышая защиту и снижая получаемый урон",
            category=SkillCategory.WARRIOR,
            stamina_cost=20,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.SWORD

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +10 Защита, -20% получаемый урон на 4 хода",
            "Ранг 2: +15 Защита, -28% получаемый урон на 5 ходов",
            "Ранг 3: +20 Защита, -36% получаемый урон на 6 ходов",
            "Ранг 4: +25 Защита, -44% получаемый урон на 7 ходов",
            "Ранг 5: +30 Защита, -52% получаемый урон на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать железную стойку"""
        result = super().use(user, target)

        # Бонус к защите и снижение урона растет с рангом
        defense_boost = 10 + (self.rank - 1) * 5  # 10-30
        damage_reduction = 20 + (self.rank - 1) * 8  # 20%-52%
        duration = 4 + (self.rank - 1)  # 4-8 ходов

        # Создаем эффект
        stance_effect = StatusEffect(
            name="Железная стойка",
            duration=duration,
            description=f"+{defense_boost} Защита, -{damage_reduction}% урон"
        )
        stance_effect.defense_boost = defense_boost
        stance_effect.damage_reduction = damage_reduction

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(stance_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(stance_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(stance_effect)

        result['defense_boost'] = defense_boost
        result['damage_reduction'] = damage_reduction
        result['duration'] = duration
        result['message'] = f"{user.name} принимает железную стойку! +{defense_boost} Защита, -{damage_reduction}% урон на {duration} ходов!"

        return result


class Intimidate(WeaponSkill):
    """Устрашение - снижает атаку противника"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Устрашение",
            description="Устрашающий крик снижает атаку врага. Эффект растет с рангом",
            category=SkillCategory.WARRIOR,
            stamina_cost=15,
            cooldown=5
        )
        self.required_weapon_type = WeaponType.SWORD

    def get_rank_progression_info(self):
        return [
            "Ранг 1: -10% Атака врага на 3 хода",
            "Ранг 2: -18% Атака врага на 4 хода",
            "Ранг 3: -26% Атака врага на 5 ходов",
            "Ранг 4: -34% Атака врага на 6 ходов",
            "Ранг 5: -42% Атака врага на 7 ходов"
        ]

    def use(self, user, target=None):
        """Использовать устрашение"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Снижение атаки растет с рангом
            attack_reduction = 10 + (self.rank - 1) * 8  # 10%-42%
            duration = 3 + (self.rank - 1)  # 3-7 ходов

            # Создаем эффект
            intimidate_effect = StatusEffect(
                name="Устрашение",
                duration=duration,
                description=f"-{attack_reduction}% Атака"
            )
            intimidate_effect.attack_reduction = attack_reduction

            # Добавляем эффект
            if hasattr(target, 'skill_manager'):
                target.skill_manager.status_effects.append(intimidate_effect)
            else:
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(intimidate_effect)

            result['attack_reduction'] = attack_reduction
            result['duration'] = duration
            result['message'] = f"{user.name} издает устрашающий крик! Атака {target.name} снижена на {attack_reduction}% на {duration} ходов!"

        return result


class SteelSkin(WeaponSkill):
    """Стальная кожа - временная высокая устойчивость к урону"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Стальная кожа",
            description="Кожа становится твердой как сталь, поглощая большую часть урона",
            category=SkillCategory.WARRIOR,
            stamina_cost=30,
            cooldown=9
        )
        self.required_weapon_type = WeaponType.SWORD

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Поглощает 70% урона на 2 хода",
            "Ранг 2: Поглощает 75% урона на 3 хода",
            "Ранг 3: Поглощает 80% урона на 3 хода",
            "Ранг 4: Поглощает 85% урона на 4 хода",
            "Ранг 5: Поглощает 90% урона на 4 хода"
        ]

    def use(self, user, target=None):
        """Использовать стальную кожу"""
        result = super().use(user, target)

        # Поглощение урона растет с рангом
        damage_absorption = 70 + (self.rank - 1) * 5  # 70%-90%
        duration = 2 + (self.rank - 1) // 2  # 2-4 хода

        # Создаем эффект
        steel_skin_effect = StatusEffect(
            name="Стальная кожа",
            duration=duration,
            description=f"Поглощает {damage_absorption}% урона"
        )
        steel_skin_effect.damage_absorption = damage_absorption

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(steel_skin_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(steel_skin_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(steel_skin_effect)

        result['damage_absorption'] = damage_absorption
        result['duration'] = duration
        result['message'] = f"{user.name} активирует стальную кожу! Поглощает {damage_absorption}% урона на {duration} хода!"

        return result


class Counterattack(WeaponSkill):
    """Контратака - автоматически контратакует при получении урона"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Контратака",
            description="Готовитесь к контратаке. При получении урона автоматически наносите ответный удар",
            category=SkillCategory.WARRIOR,
            stamina_cost=22,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.SWORD

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Контратака 80% урона на 2 хода",
            "Ранг 2: Контратака 100% урона на 3 хода",
            "Ранг 3: Контратака 120% урона на 3 хода",
            "Ранг 4: Контратака 140% урона на 4 хода",
            "Ранг 5: Контратака 160% урона на 4 хода"
        ]

    def use(self, user, target=None):
        """Использовать контратаку"""
        result = super().use(user, target)

        # Урон контратаки растет с рангом
        counter_damage_percent = 80 + (self.rank - 1) * 20  # 80%-160%
        duration = 2 + (self.rank - 1) // 2  # 2-4 хода

        # Создаем эффект
        counter_effect = StatusEffect(
            name="Контратака",
            duration=duration,
            description=f"Контратакует на {counter_damage_percent}% урона"
        )
        counter_effect.counter_damage_percent = counter_damage_percent

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(counter_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(counter_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(counter_effect)

        result['counter_damage_percent'] = counter_damage_percent
        result['duration'] = duration
        result['message'] = f"{user.name} готовится к контратаке! Ответный удар {counter_damage_percent}% урона на {duration} хода!"

        return result


class Berserker(WeaponSkill):
    """Берсерк - значительно увеличивает урон, но снижает защиту"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Берсерк",
            description="Впадаете в ярость, значительно увеличивая урон за счет защиты",
            category=SkillCategory.WARRIOR,
            stamina_cost=25,
            cooldown=7
        )
        self.required_weapon_type = WeaponType.SWORD

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +40% Урон, -30% Защита на 4 хода",
            "Ранг 2: +52% Урон, -28% Защита на 5 ходов",
            "Ранг 3: +64% Урон, -26% Защита на 6 ходов",
            "Ранг 4: +76% Урон, -24% Защита на 7 ходов",
            "Ранг 5: +88% Урон, -22% Защита на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать берсерк"""
        result = super().use(user, target)

        # Бонус к урону растет, штраф к защите уменьшается с рангом
        damage_boost = 40 + (self.rank - 1) * 12  # 40%-88%
        defense_penalty = 30 - (self.rank - 1) * 2  # 30%-22%
        duration = 4 + (self.rank - 1)  # 4-8 ходов

        # Создаем эффект
        berserker_effect = StatusEffect(
            name="Берсерк",
            duration=duration,
            description=f"+{damage_boost}% Урон, -{defense_penalty}% Защита"
        )
        berserker_effect.damage_boost = damage_boost
        berserker_effect.defense_penalty = defense_penalty

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(berserker_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(berserker_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(berserker_effect)

        result['damage_boost'] = damage_boost
        result['defense_penalty'] = defense_penalty
        result['duration'] = duration
        result['message'] = f"{user.name} впадает в ярость берсерка! +{damage_boost}% Урон, -{defense_penalty}% Защита на {duration} ходов!"

        return result


# --- ДОПОЛНИТЕЛЬНЫЕ УМЕНИЯ ДЛЯ ОХОТНИКА (HUNTER) ---

class HuntersMark(WeaponSkill):
    """Метка охотника - помечает цель, увеличивая урон по ней"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Метка охотника",
            description="Помечаете цель для охоты, значительно увеличивая весь урон по ней",
            category=SkillCategory.HUNTER, tactical_range=10,
            stamina_cost=18,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.BOW

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +25% урон по цели на 4 хода",
            "Ранг 2: +35% урон по цели на 5 ходов",
            "Ранг 3: +45% урон по цели на 6 ходов",
            "Ранг 4: +55% урон по цели на 7 ходов",
            "Ранг 5: +65% урон по цели на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать метку охотника"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Бонус к урону растет с рангом
            damage_boost = 25 + (self.rank - 1) * 10  # 25%-65%
            duration = 4 + (self.rank - 1)  # 4-8 ходов

            # Создаем эффект
            mark_effect = StatusEffect(
                name="Метка охотника",
                duration=duration,
                description=f"+{damage_boost}% получаемый урон"
            )
            mark_effect.damage_vulnerability = damage_boost

            # Добавляем эффект
            if hasattr(target, 'skill_manager'):
                target.skill_manager.status_effects.append(mark_effect)
            else:
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(mark_effect)

            result['damage_boost'] = damage_boost
            result['duration'] = duration
            result['message'] = f"{user.name} помечает {target.name} меткой охотника! +{damage_boost}% урон по цели на {duration} ходов!"

        return result


class StaminaBoost(WeaponSkill):
    """Укрепление - увеличивает выносливость и скорость её восстановления"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Укрепление",
            description="Укрепляете тело, увеличивая максимальную выносливость и скорость её восстановления",
            category=SkillCategory.HUNTER, tactical_range=0,  # На себя
            stamina_cost=15,
            cooldown=7
        )
        self.required_weapon_type = WeaponType.BOW

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +20 Макс.выносливость, +3 восстановление/ход на 5 ходов",
            "Ранг 2: +28 Макс.выносливость, +4 восстановление/ход на 6 ходов",
            "Ранг 3: +36 Макс.выносливость, +5 восстановление/ход на 7 ходов",
            "Ранг 4: +44 Макс.выносливость, +6 восстановление/ход на 8 ходов",
            "Ранг 5: +52 Макс.выносливость, +7 восстановление/ход на 9 ходов"
        ]

    def use(self, user, target=None):
        """Использовать укрепление"""
        result = super().use(user, target)

        # Бонусы растут с рангом
        max_stamina_boost = 20 + (self.rank - 1) * 8  # 20-52
        stamina_regen = 3 + (self.rank - 1)  # 3-7/ход
        duration = 5 + (self.rank - 1)  # 5-9 ходов

        # Создаем эффект
        boost_effect = StatusEffect(
            name="Укрепление",
            duration=duration,
            description=f"+{max_stamina_boost} Макс.выносливость, +{stamina_regen} восстановление/ход"
        )
        boost_effect.max_stamina_boost = max_stamina_boost
        boost_effect.stamina_regen = stamina_regen

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(boost_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(boost_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(boost_effect)

        result['max_stamina_boost'] = max_stamina_boost
        result['stamina_regen'] = stamina_regen
        result['duration'] = duration
        result['message'] = f"{user.name} укрепляет тело! +{max_stamina_boost} Макс.выносливость, +{stamina_regen} восстановление/ход на {duration} ходов!"

        return result


class EagleEye(WeaponSkill):
    """Меткий глаз - увеличивает шанс крита и дальность атак"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Меткий глаз",
            description="Обостряете зрение, значительно повышая точность и шанс критического попадания",
            category=SkillCategory.HUNTER, tactical_range=0,  # На себя
            stamina_cost=20,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.BOW

    def get_rank_progression_info(self):
        return [
            "Ранг 1: +20% Шанс крита, +2 дальность на 4 хода",
            "Ранг 2: +28% Шанс крита, +3 дальность на 5 ходов",
            "Ранг 3: +36% Шанс крита, +4 дальность на 6 ходов",
            "Ранг 4: +44% Шанс крита, +5 дальность на 7 ходов",
            "Ранг 5: +52% Шанс крита, +6 дальность на 8 ходов"
        ]

    def use(self, user, target=None):
        """Использовать меткий глаз"""
        result = super().use(user, target)

        # Бонусы растут с рангом
        crit_boost = 20 + (self.rank - 1) * 8  # 20%-52%
        range_boost = 2 + (self.rank - 1)  # 2-6
        duration = 4 + (self.rank - 1)  # 4-8 ходов

        # Создаем эффект
        eagle_eye_effect = StatusEffect(
            name="Меткий глаз",
            duration=duration,
            description=f"+{crit_boost}% Шанс крита, +{range_boost} дальность"
        )
        eagle_eye_effect.crit_boost = crit_boost
        eagle_eye_effect.range_boost = range_boost

        # Добавляем эффект
        if hasattr(user, 'skill_manager') and hasattr(user.skill_manager, 'add_status_effect'):
            user.skill_manager.add_status_effect(eagle_eye_effect)
        elif hasattr(user, 'skill_manager'):
            user.skill_manager.status_effects.append(eagle_eye_effect)
        else:
            if not hasattr(user, 'status_effects'):
                user.status_effects = []
            user.status_effects.append(eagle_eye_effect)

        result['crit_boost'] = crit_boost
        result['range_boost'] = range_boost
        result['duration'] = duration
        result['message'] = f"{user.name} обостряет зрение! +{crit_boost}% Шанс крита, +{range_boost} дальность на {duration} ходов!"

        return result


class ExplosiveArrow(WeaponSkill):
    """Взрывная стрела - наносит урон по области"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Взрывная стрела",
            description="Стрела взрывается при попадании, нанося урон по области. Урон и радиус растут с рангом",
            category=SkillCategory.HUNTER, tactical_range=8,
            stamina_cost=28,
            cooldown=6
        )
        self.required_weapon_type = WeaponType.BOW

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон x1.8, радиус 2 клетки",
            "Ранг 2: Урон x2.1, радиус 2 клетки",
            "Ранг 3: Урон x2.4, радиус 3 клетки",
            "Ранг 4: Урон x2.7, радиус 3 клетки",
            "Ранг 5: Урон x3.0, радиус 4 клетки"
        ]

    def use(self, user, target=None):
        """Использовать взрывную стрелу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Получаем урон от оружия
            weapon_damage = 0
            if hasattr(user, 'inventory') and user.inventory:
                from game.inventory import EquipmentSlot, WeaponItem
                weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
                if weapon and isinstance(weapon, WeaponItem):
                    weapon_damage = weapon.damage

            # Базовый урон = урон оружия + ловкость
            dexterity = user.get_effective_dexterity() if hasattr(user, 'get_effective_dexterity') else getattr(user, 'dexterity', 10)
            base_damage = weapon_damage + dexterity

            # Применяем множитель от ранга
            damage_multiplier = 1.8 + (self.rank - 1) * 0.3  # 1.8x -> 3.0x
            total_damage = int(base_damage * damage_multiplier)

            # Проверяем крит
            crit_chance = user.calculate_crit_chance() if hasattr(user, 'calculate_crit_chance') else 0
            is_crit = random.random() < (crit_chance / 100)
            if is_crit:
                total_damage = int(total_damage * 2)

            # Учитываем защиту
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            target.take_damage(actual_damage)

            # Радиус взрыва растет с рангом
            explosion_radius = 2 + (self.rank - 1) // 2  # 2-4 клетки

            result['damage'] = actual_damage
            result['critical'] = is_crit
            result['explosion_radius'] = explosion_radius
            result['aoe'] = True
            crit_text = " КРИТИЧЕСКОЕ ПОПАДАНИЕ!" if is_crit else ""
            result['message'] = f"{user.name} выпускает взрывную стрелу в {target.name} на {actual_damage} урона!{crit_text} (радиус взрыва {explosion_radius} клетки)"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class Trap(WeaponSkill):
    """Ловушка - устанавливает ловушку на клетку"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Ловушка",
            description="Устанавливает ловушку, которая срабатывает при приближении врага. Урон растет с рангом",
            category=SkillCategory.HUNTER, tactical_range=3,
            stamina_cost=20,
            cooldown=8
        )
        self.required_weapon_type = WeaponType.BOW

    def get_rank_progression_info(self):
        return [
            "Ранг 1: Урон 25, замедление на 2 хода",
            "Ранг 2: Урон 38, замедление на 3 хода",
            "Ранг 3: Урон 51, замедление и кровотечение на 3 хода",
            "Ранг 4: Урон 64, замедление и кровотечение на 4 хода",
            "Ранг 5: Урон 77, замедление и кровотечение на 5 ходов"
        ]

    def use(self, user, target=None):
        """Использовать ловушку"""
        result = super().use(user, target)

        # Урон ловушки растет с рангом
        trap_damage = 25 + (self.rank - 1) * 13  # 25-77
        slow_duration = 2 + (self.rank - 1)  # 2-5 ходов
        has_bleed = self.rank >= 3  # С 3 ранга добавляется кровотечение

        result['trap_damage'] = trap_damage
        result['slow_duration'] = slow_duration
        result['has_bleed'] = has_bleed
        result['message'] = f"{user.name} устанавливает ловушку (урон {trap_damage}, замедление {slow_duration} ходов{', кровотечение' if has_bleed else ''})!"

        return result


