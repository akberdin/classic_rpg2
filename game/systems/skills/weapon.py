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
from game.systems.skills.base import Skill, SkillCategory
from game.systems.skills.effects import PoisonEffect


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

class PreciseShot(WeaponSkill):
    """Точный выстрел - высокий шанс критического попадания"""

    def __init__(self):
        from game.inventory import WeaponType
        super().__init__(
            name="Точный выстрел",
            description="Прицельный выстрел с высоким шансом крита. Шанс растет с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=12,
            cooldown=2
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать точный выстрел"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Базовый урон с множителем от ловкости
            base_damage = user.get_total_damage()
            dex_bonus = getattr(user, 'dexterity', 10) * 0.3
            damage_multiplier = 1.2 + (self.rank - 1) * 0.2  # 1.2x -> 2.0x

            # Гарантированный крит с шансом, растущим от ранга
            crit_chance = 0.3 + (self.rank - 1) * 0.15  # 30% -> 90%
            is_crit = random.random() < crit_chance

            total_damage = int((base_damage + dex_bonus) * damage_multiplier)
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
            category=SkillCategory.COMBAT,
            stamina_cost=20,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать быструю стрельбу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Количество стрел зависит от ранга
            num_arrows = 2 + (self.rank - 1)  # 2-6 стрел

            base_damage = user.get_total_damage()
            damage_per_arrow = int(base_damage * 0.6)  # 60% урона за стрелу
            target_defense = target.get_total_defense()

            total_damage = 0
            for _ in range(num_arrows):
                arrow_damage = max(1, damage_per_arrow - target_defense // num_arrows)
                total_damage += arrow_damage

            target.take_damage(total_damage)

            result['damage'] = total_damage
            result['arrows'] = num_arrows
            result['message'] = f"{user.name} выпускает {num_arrows} стрел в {target.name} на {total_damage} общего урона!"

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
            category=SkillCategory.COMBAT,
            stamina_cost=15,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.BOW

    def use(self, user, target=None):
        """Использовать пронзающую стрелу"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            damage_multiplier = 1.5 + (self.rank - 1) * 0.25  # 1.5x -> 2.5x

            # Пробитие брони
            armor_penetration = 0.4 + (self.rank - 1) * 0.1  # 40% -> 80%

            total_damage = int(base_damage * damage_multiplier)
            target_defense = target.get_total_defense()
            effective_defense = int(target_defense * (1 - armor_penetration))
            actual_damage = max(1, total_damage - effective_defense)

            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['armor_penetration'] = int(armor_penetration * 100)
            result['message'] = f"{user.name} выпускает пронзающую стрелу в {target.name} на {actual_damage} урона (пробитие {int(armor_penetration * 100)}% брони)!"

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
            category=SkillCategory.COMBAT,
            stamina_cost=18,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.KNIFE

    def use(self, user, target=None):
        """Использовать удар в спину"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            dex_bonus = getattr(user, 'dexterity', 10) * 0.5

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
            category=SkillCategory.COMBAT,
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
            category=SkillCategory.COMBAT,
            stamina_cost=16,
            cooldown=3
        )
        self.required_weapon_type = WeaponType.KNIFE

    def use(self, user, target=None):
        """Использовать шаг тени"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            dex_bonus = getattr(user, 'dexterity', 10) * 0.4

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
            category=SkillCategory.COMBAT,
            stamina_cost=22,
            cooldown=4
        )
        self.required_weapon_type = WeaponType.SWORD

    def use(self, user, target=None):
        """Использовать вихревой удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            base_damage = user.get_total_damage()
            str_bonus = getattr(user, 'strength', 10) * 0.4

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
            category=SkillCategory.COMBAT,
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
            category=SkillCategory.COMBAT,
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
            str_bonus = getattr(user, 'strength', 10) * 0.2
            dex_bonus = getattr(user, 'dexterity', 10) * 0.2

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


