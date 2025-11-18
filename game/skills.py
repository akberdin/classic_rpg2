"""
Система умений и способностей с категориями, рангами и прогрессом
"""
import random
from enum import Enum


class SkillCategory(Enum):
    """Категории умений"""
    COMBAT = "combat"  # Боевые умения
    CRAFTING = "crafting"  # Ремесленные умения
    MAGIC = "magic"  # Магические умения


class StatusEffect:
    """Базовый класс для статус-эффектов"""

    def __init__(self, name, duration, description=""):
        """
        Инициализация статус-эффекта

        Args:
            name: Название эффекта
            duration: Длительность в ходах
            description: Описание эффекта
        """
        self.name = name
        self.duration = duration
        self.remaining_duration = duration
        self.description = description

    def apply(self, character):
        """
        Применить эффект к персонажу

        Args:
            character: Персонаж

        Returns:
            str: Сообщение о применении эффекта
        """
        return f"{character.name} получает эффект: {self.name}"

    def tick(self, character):
        """
        Обновить эффект (вызывается каждый ход)

        Args:
            character: Персонаж

        Returns:
            str: Сообщение о действии эффекта
        """
        self.remaining_duration -= 1
        return ""

    def is_expired(self):
        """
        Проверить, истек ли эффект

        Returns:
            bool: True если эффект истек
        """
        return self.remaining_duration <= 0

    def remove(self, character):
        """
        Удалить эффект с персонажа

        Args:
            character: Персонаж

        Returns:
            str: Сообщение об удалении эффекта
        """
        return f"{self.name} снят с {character.name}"


class PoisonEffect(StatusEffect):
    """Эффект отравления - наносит урон каждый ход"""

    def __init__(self, duration=3, damage_per_turn=5):
        """
        Инициализация отравления

        Args:
            duration: Длительность в ходах
            damage_per_turn: Урон за ход
        """
        super().__init__(
            name="Отравление",
            duration=duration,
            description=f"Наносит {damage_per_turn} урона каждый ход"
        )
        self.damage_per_turn = damage_per_turn

    def tick(self, character):
        """Нанести урон от яда"""
        super().tick(character)
        character.take_damage(self.damage_per_turn)
        return f"{character.name} получает {self.damage_per_turn} урона от яда"


class StunEffect(StatusEffect):
    """Эффект оглушения - пропуск хода"""

    def __init__(self, duration=1):
        """
        Инициализация оглушения

        Args:
            duration: Длительность в ходах
        """
        super().__init__(
            name="Оглушение",
            duration=duration,
            description="Пропуск хода"
        )

    def apply(self, character):
        """Применить оглушение"""
        character.stunned = True
        return f"{character.name} оглушен!"

    def remove(self, character):
        """Снять оглушение"""
        character.stunned = False
        return f"{character.name} пришел в себя"


class RegenerationEffect(StatusEffect):
    """Эффект регенерации - восстановление HP каждый ход"""

    def __init__(self, duration=3, heal_per_turn=10):
        """
        Инициализация регенерации

        Args:
            duration: Длительность в ходах
            heal_per_turn: Лечение за ход
        """
        super().__init__(
            name="Регенерация",
            duration=duration,
            description=f"Восстанавливает {heal_per_turn} HP каждый ход"
        )
        self.heal_per_turn = heal_per_turn

    def tick(self, character):
        """Восстановить здоровье"""
        super().tick(character)
        old_health = character.health
        character.health = min(character.max_health, character.health + self.heal_per_turn)
        actual_heal = character.health - old_health
        return f"{character.name} восстанавливает {actual_heal} HP от регенерации"


class StrengthBoostEffect(StatusEffect):
    """Эффект усиления силы"""

    def __init__(self, duration=3, boost_amount=5):
        """
        Инициализация усиления

        Args:
            duration: Длительность в ходах
            boost_amount: Бонус к силе
        """
        super().__init__(
            name="Усиление",
            duration=duration,
            description=f"+{boost_amount} к силе"
        )
        self.boost_amount = boost_amount

    def apply(self, character):
        """Применить усиление"""
        character.temp_strength_boost = self.boost_amount
        return f"{character.name} получает +{self.boost_amount} к силе!"

    def remove(self, character):
        """Снять усиление"""
        character.temp_strength_boost = 0
        return f"Усиление спадает с {character.name}"


class Skill:
    """Базовый класс для умений с системой рангов и прогресса"""

    def __init__(self, name, description, category, mana_cost=0, stamina_cost=0, cooldown=0, max_rank=5):
        """
        Инициализация умения

        Args:
            name: Название умения
            description: Описание умения
            category: Категория умения (SkillCategory)
            mana_cost: Стоимость в мане
            stamina_cost: Стоимость в выносливости
            cooldown: Перезарядка в ходах
            max_rank: Максимальный ранг умения
        """
        self.name = name
        self.base_description = description
        self.category = category
        self.mana_cost = mana_cost
        self.stamina_cost = stamina_cost
        self.cooldown = cooldown
        self.current_cooldown = 0

        # Система рангов и прогресса
        self.rank = 1
        self.max_rank = max_rank
        self.experience = 0
        self.experience_to_next_rank = 100  # Базовое значение для ранга 2

    @property
    def description(self):
        """Получить описание с учетом текущего ранга"""
        return f"{self.base_description} [Ранг {self.rank}/{self.max_rank}]"

    def add_experience(self, amount):
        """
        Добавить опыт умению

        Args:
            amount: Количество опыта

        Returns:
            bool: True если произошло повышение ранга
        """
        if self.rank >= self.max_rank:
            return False

        self.experience += amount

        if self.experience >= self.experience_to_next_rank:
            self.rank_up()
            return True

        return False

    def rank_up(self):
        """Повысить ранг умения"""
        if self.rank >= self.max_rank:
            return

        self.experience -= self.experience_to_next_rank
        self.rank += 1
        # Увеличиваем требуемый опыт для следующего ранга
        self.experience_to_next_rank = int(self.experience_to_next_rank * 1.5)

        print(f"Умение '{self.name}' повышено до ранга {self.rank}!")

    def can_use(self, user):
        """
        Проверить, можно ли использовать умение

        Args:
            user: Использующий персонаж

        Returns:
            tuple: (bool, str) - можно ли использовать и причина если нет
        """
        if self.current_cooldown > 0:
            return False, f"{self.name} перезаряжается ({self.current_cooldown} ходов)"

        if hasattr(user, 'mana') and user.mana < self.mana_cost:
            return False, f"Недостаточно маны для {self.name}"

        if hasattr(user, 'stamina') and user.stamina < self.stamina_cost:
            return False, f"Недостаточно выносливости для {self.name}"

        return True, ""

    def use(self, user, target=None):
        """
        Использовать умение

        Args:
            user: Использующий персонаж
            target: Цель умения (если есть)

        Returns:
            dict: Результат использования умения
        """
        # Списываем ресурсы
        if hasattr(user, 'mana'):
            user.mana -= self.mana_cost
        if hasattr(user, 'stamina'):
            user.stamina -= self.stamina_cost

        # Запускаем перезарядку
        self.current_cooldown = self.cooldown

        # Добавляем опыт за использование
        self.add_experience(10)

        return {
            'success': True,
            'message': f"{user.name} использует {self.name}!"
        }

    def tick_cooldown(self):
        """Уменьшить перезарядку на 1"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


# ==================== БОЕВЫЕ УМЕНИЯ ====================

class BasicAttack(Skill):
    """Базовая атака - доступна с самого начала"""

    def __init__(self):
        super().__init__(
            name="Базовая атака",
            description="Простой удар оружием. Урон увеличивается с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=5,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать базовую атаку"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Вычисляем урон с учетом ранга (10% за ранг)
            base_damage = user.get_total_damage()
            rank_bonus = int(base_damage * (self.rank - 1) * 0.1)
            total_damage = base_damage + rank_bonus

            # Учитываем защиту цели
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['message'] = f"{user.name} наносит базовую атаку {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class PowerStrike(Skill):
    """Мощный удар - наносит увеличенный урон"""

    def __init__(self):
        super().__init__(
            name="Мощный удар",
            description="Наносит урон с увеличенным коэффициентом. Сила растет с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=10,
            cooldown=2
        )

    def use(self, user, target=None):
        """Использовать мощный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Коэффициент урона растет с рангом (1.5x + 0.2x за ранг)
            damage_multiplier = 1.5 + (self.rank - 1) * 0.2

            base_damage = user.get_total_damage()
            total_damage = int(base_damage * damage_multiplier)

            # Учитываем защиту цели
            target_defense = target.get_total_defense()
            actual_damage = max(1, total_damage - target_defense)

            # Применяем урон
            target.take_damage(actual_damage)

            result['damage'] = actual_damage
            result['message'] = f"{user.name} наносит мощный удар {target.name} на {actual_damage} урона!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class PoisonStrike(Skill):
    """Отравленный удар - наносит урон и накладывает яд"""

    def __init__(self):
        super().__init__(
            name="Отравленный удар",
            description="Наносит урон и накладывает отравление. Длительность растет с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=15,
            cooldown=4
        )

    def use(self, user, target=None):
        """Использовать отравленный удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим обычный урон
            base_damage = user.get_total_damage()
            target_defense = target.get_total_defense()
            actual_damage = max(1, base_damage - target_defense)

            target.take_damage(actual_damage)

            # Длительность и сила яда растут с рангом
            poison_duration = 2 + self.rank
            poison_damage = 3 + self.rank * 2

            # Накладываем отравление
            poison = PoisonEffect(duration=poison_duration, damage_per_turn=poison_damage)
            if not hasattr(target, 'status_effects'):
                target.status_effects = []
            target.status_effects.append(poison)

            result['damage'] = actual_damage
            result['poison_applied'] = True
            result['message'] = f"{user.name} наносит отравленный удар {target.name} на {actual_damage} урона и накладывает яд на {poison_duration} ходов!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class StunStrike(Skill):
    """Оглушающий удар - наносит урон и оглушает"""

    def __init__(self):
        super().__init__(
            name="Оглушающий удар",
            description="Наносит урон и оглушает. Шанс оглушения растет с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=20,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать оглушающий удар"""
        result = super().use(user, target)

        if target and user.can_attack(target):
            # Наносим урон
            base_damage = user.get_total_damage()
            target_defense = target.get_total_defense()
            actual_damage = max(1, base_damage - target_defense)

            target.take_damage(actual_damage)

            # Шанс оглушения растет с рангом (40% + 10% за ранг)
            stun_chance = 0.4 + (self.rank - 1) * 0.1
            stunned = False
            if random.random() < stun_chance:
                stun = StunEffect(duration=1)
                if not hasattr(target, 'status_effects'):
                    target.status_effects = []
                target.status_effects.append(stun)
                stunned = True

            result['damage'] = actual_damage
            result['stunned'] = stunned
            result['message'] = f"{user.name} наносит оглушающий удар {target.name} на {actual_damage} урона!"

            if stunned:
                result['message'] += f" {target.name} оглушен!"

            if not target.is_alive:
                result['killed'] = True
                result['message'] += f" {target.name} повержен!"

        return result


class BattleCry(Skill):
    """Боевой клич - усиливает силу на несколько ходов"""

    def __init__(self):
        super().__init__(
            name="Боевой клич",
            description="Увеличивает силу. Бонус и длительность растут с рангом",
            category=SkillCategory.COMBAT,
            stamina_cost=15,
            cooldown=6
        )

    def use(self, user, target=None):
        """Использовать боевой клич"""
        result = super().use(user, target)

        # Бонус и длительность растут с рангом
        boost_amount = 3 + self.rank * 2
        boost_duration = 2 + self.rank

        # Накладываем усиление на себя
        boost = StrengthBoostEffect(duration=boost_duration, boost_amount=boost_amount)
        if not hasattr(user, 'status_effects'):
            user.status_effects = []
        user.status_effects.append(boost)

        result['message'] = f"{user.name} издает боевой клич! Сила увеличена на {boost_amount} на {boost_duration} ходов!"

        return result


# ==================== МАГИЧЕСКИЕ УМЕНИЯ ====================

class Heal(Skill):
    """Лечение - восстанавливает здоровье"""

    def __init__(self):
        super().__init__(
            name="Лечение",
            description="Восстанавливает HP. Эффективность растет с рангом",
            category=SkillCategory.MAGIC,
            mana_cost=20,
            cooldown=3
        )

    def use(self, user, target=None):
        """Использовать лечение"""
        result = super().use(user, target)

        # Если цель не указана, лечим себя
        if target is None:
            target = user

        # Эффективность лечения растет с рангом (30% + 10% за ранг)
        heal_percent = 0.3 + (self.rank - 1) * 0.1
        heal_amount = int(target.max_health * heal_percent)

        old_health = target.health
        target.health = min(target.max_health, target.health + heal_amount)
        actual_heal = target.health - old_health

        result['heal'] = actual_heal
        result['message'] = f"{user.name} восстанавливает {actual_heal} HP для {target.name}!"

        return result


class Regeneration(Skill):
    """Регенерация - накладывает эффект восстановления HP"""

    def __init__(self):
        super().__init__(
            name="Регенерация",
            description="Восстанавливает HP каждый ход. Эффективность растет с рангом",
            category=SkillCategory.MAGIC,
            mana_cost=15,
            cooldown=5
        )

    def use(self, user, target=None):
        """Использовать регенерацию"""
        result = super().use(user, target)

        # Если цель не указана, накладываем на себя
        if target is None:
            target = user

        # Эффективность регенерации растет с рангом
        heal_per_turn = 8 + self.rank * 3
        regen_duration = 2 + self.rank

        # Накладываем эффект регенерации
        regen = RegenerationEffect(duration=regen_duration, heal_per_turn=heal_per_turn)
        if not hasattr(target, 'status_effects'):
            target.status_effects = []
        target.status_effects.append(regen)

        result['message'] = f"{user.name} накладывает регенерацию на {target.name}! (+{heal_per_turn} HP/ход на {regen_duration} ходов)"

        return result


# ==================== РЕМЕСЛЕННЫЕ УМЕНИЯ ====================

class Mining(Skill):
    """Рудокоп - добыча руды"""

    def __init__(self):
        super().__init__(
            name="Рудокоп",
            description="Позволяет добывать руду в шахтах. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение рудокопа"""
        # Получаем профессию рудокопа
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        mining_profession = user.profession_manager.get_profession('mining')
        if not mining_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Рудокоп не найдена"
            return result

        # Проверяем, можно ли использовать профессию
        # Получаем текущую локацию
        location = None
        if hasattr(user, 'x') and hasattr(user, 'y'):
            # Пытаемся получить локацию из текущей позиции игрока
            # Это требует доступа к карте, который мы получим из контекста
            pass

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = mining_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Добыто: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} добыл ресурсы!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

        return result


class Lumberjacking(Skill):
    """Лесоруб - рубка деревьев"""

    def __init__(self):
        super().__init__(
            name="Лесоруб",
            description="Позволяет рубить деревья. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение лесоруба"""
        # Получаем профессию лесоруба
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        lumberjacking_profession = user.profession_manager.get_profession('lumberjacking')
        if not lumberjacking_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Лесоруб не найдена"
            return result

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = lumberjacking_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Срублено: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} срубил деревья!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

        return result


# Список всех доступных умений
AVAILABLE_SKILLS = {
    # Боевые
    'basic_attack': BasicAttack,
    'power_strike': PowerStrike,
    'poison_strike': PoisonStrike,
    'stun_strike': StunStrike,
    'battle_cry': BattleCry,
    # Магические
    'heal': Heal,
    'regeneration': Regeneration,
    # Ремесленные
    'mining': Mining,
    'lumberjacking': Lumberjacking,
}


class SkillManager:
    """Менеджер умений персонажа"""

    def __init__(self, character):
        """
        Инициализация менеджера умений

        Args:
            character: Персонаж-владелец умений
        """
        self.character = character
        self.learned_skills = {}  # Словарь {skill_id: skill_instance}
        self.status_effects = []  # Активные статус-эффекты
        self.skill_slots = [None] * 8  # 8 слотов для быстрого доступа к умениям

    def learn_skill(self, skill_class_or_id):
        """
        Изучить новый навык

        Args:
            skill_class_or_id: Класс навыка или его ID

        Returns:
            bool: True если навык успешно изучен
        """
        # Если передан строковый ID, получаем класс
        if isinstance(skill_class_or_id, str):
            skill_id = skill_class_or_id
            if skill_id not in AVAILABLE_SKILLS:
                return False
            skill_class = AVAILABLE_SKILLS[skill_id]
        else:
            skill_class = skill_class_or_id
            # Ищем ID по классу
            skill_id = None
            for sid, sclass in AVAILABLE_SKILLS.items():
                if sclass == skill_class:
                    skill_id = sid
                    break
            if not skill_id:
                return False

        # Проверяем, не изучен ли уже этот навык
        if skill_id in self.learned_skills:
            return False

        skill = skill_class()
        self.learned_skills[skill_id] = skill

        print(f"Изучено умение: {skill.name} ({skill.category.value})")
        return True

    def assign_to_slot(self, skill_id, slot_index):
        """
        Назначить умение в слот быстрого доступа

        Args:
            skill_id: ID умения
            slot_index: Индекс слота (0-7)

        Returns:
            bool: True если успешно назначено
        """
        if slot_index < 0 or slot_index >= 8:
            return False

        if skill_id not in self.learned_skills:
            return False

        self.skill_slots[slot_index] = skill_id
        return True

    def unassign_from_slot(self, slot_index):
        """
        Убрать умение из слота

        Args:
            slot_index: Индекс слота (0-7)
        """
        if 0 <= slot_index < 8:
            self.skill_slots[slot_index] = None

    def get_slot_skill(self, slot_index):
        """
        Получить умение из слота

        Args:
            slot_index: Индекс слота (0-7)

        Returns:
            Skill or None: Умение в слоте или None
        """
        if slot_index < 0 or slot_index >= 8:
            return None

        skill_id = self.skill_slots[slot_index]
        if not skill_id:
            return None

        return self.learned_skills.get(skill_id)

    def use_skill_from_slot(self, slot_index, target=None):
        """
        Использовать умение из слота

        Args:
            slot_index: Индекс слота (0-7)
            target: Цель умения

        Returns:
            dict: Результат использования
        """
        skill = self.get_slot_skill(slot_index)
        if not skill:
            return {
                'success': False,
                'message': f"Слот {slot_index + 1} пуст"
            }

        return self.use_skill(skill, target)

    def use_skill(self, skill_or_name, target=None):
        """
        Использовать умение

        Args:
            skill_or_name: Объект умения или его название/ID
            target: Цель умения

        Returns:
            dict: Результат использования
        """
        # Ищем умение
        skill = None
        if isinstance(skill_or_name, str):
            # Ищем по ID
            if skill_or_name in self.learned_skills:
                skill = self.learned_skills[skill_or_name]
            else:
                # Ищем по имени
                for s in self.learned_skills.values():
                    if s.name == skill_or_name:
                        skill = s
                        break
        else:
            skill = skill_or_name

        if not skill:
            return {
                'success': False,
                'message': f"Умение не найдено"
            }

        # Проверяем возможность использования
        can_use, reason = skill.can_use(self.character)
        if not can_use:
            return {
                'success': False,
                'message': reason
            }

        # Используем умение
        return skill.use(self.character, target)

    def tick_cooldowns(self):
        """Уменьшить перезарядки всех умений"""
        for skill in self.learned_skills.values():
            skill.tick_cooldown()

    def tick_status_effects(self):
        """
        Обновить все статус-эффекты

        Returns:
            list: Список сообщений от эффектов
        """
        messages = []

        # Обновляем эффекты
        for effect in self.status_effects[:]:  # Копия списка для безопасного удаления
            message = effect.tick(self.character)
            if message:
                messages.append(message)

            # Удаляем истекшие эффекты
            if effect.is_expired():
                remove_message = effect.remove(self.character)
                if remove_message:
                    messages.append(remove_message)
                self.status_effects.remove(effect)

        return messages

    def add_status_effect(self, effect):
        """
        Добавить статус-эффект

        Args:
            effect: Эффект для добавления
        """
        # Применяем эффект
        message = effect.apply(self.character)
        self.status_effects.append(effect)
        return message

    def has_effect(self, effect_name):
        """
        Проверить наличие эффекта

        Args:
            effect_name: Название эффекта

        Returns:
            bool: True если эффект активен
        """
        for effect in self.status_effects:
            if effect.name == effect_name:
                return True
        return False

    def get_skills_by_category(self, category):
        """
        Получить все изученные умения определенной категории

        Args:
            category: Категория умений (SkillCategory)

        Returns:
            list: Список умений
        """
        return [skill for skill in self.learned_skills.values() if skill.category == category]

    def get_all_skills(self):
        """
        Получить все изученные умения

        Returns:
            dict: Словарь {skill_id: skill}
        """
        return self.learned_skills
