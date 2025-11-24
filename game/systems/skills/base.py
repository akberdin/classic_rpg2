"""
Базовые классы системы умений.

Содержит:
- SkillCategory - категории умений (Enum)
- Skill - базовый класс умения
- SkillManager - менеджер умений персонажа
"""
import random
from enum import Enum


# Ленивый доступ к словарю умений (избегает циклических импортов)
_available_skills_cache = None


def get_available_skills():
    """Получить словарь всех доступных умений."""
    global _available_skills_cache
    if _available_skills_cache is None:
        from game.systems.skills import AVAILABLE_SKILLS
        _available_skills_cache = AVAILABLE_SKILLS
    return _available_skills_cache


class SkillCategory(Enum):
    """Категории умений"""
    COMBAT = "combat"  # Боевые умения
    CRAFTING = "crafting"  # Ремесленные умения
    MAGIC = "magic"  # Магические умения


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
        self.use_count = 0  # Счётчик использований

    @property
    def description(self):
        """Получить описание с учетом текущего ранга"""
        return f"{self.base_description} [Ранг {self.rank}/{self.max_rank}]"

    def get_required_uses_for_rank(self):
        """Получить требуемое количество использований для следующего ранга"""
        return 20 * self.rank  # 20, 40, 60, 80 для рангов 2, 3, 4, 5

    def get_required_player_level_for_rank(self):
        """Получить минимальный уровень игрока для следующего ранга"""
        return 5 * self.rank  # 5, 10, 15, 20 для рангов 2, 3, 4, 5

    def get_gold_cost_for_rank(self):
        """Получить стоимость в золоте для повышения ранга"""
        return 50 * self.rank * self.rank  # 50, 200, 450, 800 для рангов 2, 3, 4, 5

    def can_rank_up(self, player):
        """
        Проверить, можно ли повысить ранг умения

        Args:
            player: Игрок

        Returns:
            tuple: (bool, str) - можно ли повысить и причина если нет
        """
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        # Проверка опыта
        if self.experience < self.experience_to_next_rank:
            return False, f"Недостаточно опыта умения ({self.experience}/{self.experience_to_next_rank})"

        # Проверка использований
        required_uses = self.get_required_uses_for_rank()
        if self.use_count < required_uses:
            return False, f"Недостаточно использований ({self.use_count}/{required_uses})"

        # Проверка уровня игрока
        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Недостаточный уровень персонажа ({player.level}/{required_level})"

        # Проверка золота
        gold_cost = self.get_gold_cost_for_rank()
        if player.inventory.gold < gold_cost:
            return False, f"Недостаточно золота ({player.inventory.gold}/{gold_cost})"

        return True, ""

    def get_rank_up_requirements(self):
        """Получить строку с требованиями для повышения ранга"""
        if self.rank >= self.max_rank:
            return "Максимальный ранг достигнут"

        return (f"Требования для ранга {self.rank + 1}:\n"
                f"  Опыт: {self.experience}/{self.experience_to_next_rank}\n"
                f"  Использований: {self.use_count}/{self.get_required_uses_for_rank()}\n"
                f"  Уровень персонажа: {self.get_required_player_level_for_rank()}\n"
                f"  Золото: {self.get_gold_cost_for_rank()}")

    def add_experience(self, amount):
        """
        Добавить опыт умению

        Args:
            amount: Количество опыта

        Returns:
            bool: True если достигнуто достаточно опыта (но ранг не повышается автоматически)
        """
        if self.rank >= self.max_rank:
            return False

        self.experience += amount

        # Теперь повышение ранга НЕ происходит автоматически
        # Нужно явно вызвать try_rank_up с проверкой всех условий
        return self.experience >= self.experience_to_next_rank

    def try_rank_up(self, player):
        """
        Попытаться повысить ранг умения с проверкой всех условий

        Args:
            player: Игрок

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        can_up, reason = self.can_rank_up(player)
        if not can_up:
            return False, reason

        # Списываем золото
        gold_cost = self.get_gold_cost_for_rank()
        player.inventory.gold -= gold_cost

        # Повышаем ранг
        self.experience -= self.experience_to_next_rank
        self.rank += 1
        self.use_count = 0  # Сбрасываем счётчик использований

        # Увеличиваем требуемый опыт для следующего ранга
        self.experience_to_next_rank = int(self.experience_to_next_rank * 1.5)

        return True, f"Умение '{self.name}' повышено до ранга {self.rank}! Потрачено {gold_cost} золота."

    def rank_up(self):
        """Устаревший метод - используйте try_rank_up с проверкой условий"""
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

        # Увеличиваем счётчик использований для системы рангов
        self.use_count += 1

        return {
            'success': True,
            'message': f"{user.name} использует {self.name}!"
        }

    def tick_cooldown(self):
        """Уменьшить перезарядку на 1"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def get_rank_progression_info(self):
        """
        Получить подробную информацию о развитии умения по рангам.
        Переопределяется в подклассах для специфичной информации.

        Returns:
            list: Список строк с описанием эффектов на каждом ранге
        """
        return [
            f"Ранг 1: Базовые эффекты",
            f"Ранг 2: +20% эффективность",
            f"Ранг 3: +40% эффективность",
            f"Ранг 4: +60% эффективность",
            f"Ранг 5: +80% эффективность"
        ]

    def get_current_rank_description(self):
        """
        Получить описание текущих эффектов на текущем ранге.

        Returns:
            str: Описание текущих эффектов
        """
        progression = self.get_rank_progression_info()
        if self.rank <= len(progression):
            return progression[self.rank - 1]
        return "Максимальный уровень"


# ==================== БОЕВЫЕ УМЕНИЯ ====================



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
        # Временные умения от экипировки: {skill_id: {'from_equipment': bool, 'original_rank': int, 'equipment_rank_boost': int}}
        self.equipment_skills = {}

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
            if skill_id not in get_available_skills():
                return False
            skill_class = get_available_skills()[skill_id]
        else:
            skill_class = skill_class_or_id
            # Ищем ID по классу
            skill_id = None
            for sid, sclass in get_available_skills().items():
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

    def grant_equipment_skill(self, skill_id, skill_rank=1):
        """
        Добавить умение от экипировки. Если умения нет - добавляет временно.
        Если умение есть - повышает ранг на указанное значение.

        Args:
            skill_id: ID умения
            skill_rank: Ранг умения на предмете

        Returns:
            bool: True если успешно
        """
        if skill_id not in get_available_skills():
            return False

        # Инициализируем equipment_skills если нет
        if not hasattr(self, 'equipment_skills'):
            self.equipment_skills = {}

        if skill_id in self.learned_skills:
            # Умение уже изучено - сохраняем оригинальный ранг и повышаем
            skill = self.learned_skills[skill_id]

            if skill_id not in self.equipment_skills:
                # Первый раз получаем бонус от предмета
                self.equipment_skills[skill_id] = {
                    'from_equipment': False,  # Умение было изучено, не от предмета
                    'original_rank': skill.rank,
                    'equipment_rank_boost': skill_rank
                }
            else:
                # Уже есть бонус - увеличиваем его
                self.equipment_skills[skill_id]['equipment_rank_boost'] += skill_rank

            # Повышаем ранг умения (максимум 5)
            new_rank = min(5, self.equipment_skills[skill_id]['original_rank'] +
                          self.equipment_skills[skill_id]['equipment_rank_boost'])
            skill.rank = new_rank
            print(f"Ранг умения {skill.name} повышен до {skill.rank} (от экипировки)")
        else:
            # Умение не изучено - добавляем временно
            skill_class = get_available_skills()[skill_id]
            skill = skill_class()
            skill.rank = min(5, skill_rank)  # Ранг от предмета

            self.learned_skills[skill_id] = skill
            self.equipment_skills[skill_id] = {
                'from_equipment': True,  # Умение только от предмета
                'original_rank': 0,
                'equipment_rank_boost': skill_rank
            }
            print(f"Получено временное умение от экипировки: {skill.name} (ранг {skill.rank})")

        return True

    def revoke_equipment_skill(self, skill_id, skill_rank=1):
        """
        Убрать умение от экипировки. Если умение было только от предмета - удаляет.
        Если умение было изучено ранее - понижает ранг до оригинального.

        Args:
            skill_id: ID умения
            skill_rank: Ранг умения на предмете

        Returns:
            bool: True если успешно
        """
        if not hasattr(self, 'equipment_skills'):
            return False

        if skill_id not in self.equipment_skills:
            return False

        if skill_id not in self.learned_skills:
            return False

        skill = self.learned_skills[skill_id]
        equip_info = self.equipment_skills[skill_id]

        # Уменьшаем бонус от предметов
        equip_info['equipment_rank_boost'] = max(0, equip_info['equipment_rank_boost'] - skill_rank)

        if equip_info['from_equipment'] and equip_info['equipment_rank_boost'] <= 0:
            # Умение было только от предмета и бонус исчерпан - удаляем
            # Убираем из слотов
            for i, slot_skill_id in enumerate(self.skill_slots):
                if slot_skill_id == skill_id:
                    self.skill_slots[i] = None

            del self.learned_skills[skill_id]
            del self.equipment_skills[skill_id]
            print(f"Временное умение {skill.name} снято (предмет снят)")
        else:
            # Умение было изучено - возвращаем оригинальный ранг
            if equip_info['equipment_rank_boost'] <= 0:
                skill.rank = equip_info['original_rank']
                del self.equipment_skills[skill_id]
                print(f"Ранг умения {skill.name} вернулся к {skill.rank}")
            else:
                # Ещё есть бонусы от других предметов
                skill.rank = min(5, equip_info['original_rank'] + equip_info['equipment_rank_boost'])
                print(f"Ранг умения {skill.name} понижен до {skill.rank}")

        return True

    def is_equipment_skill(self, skill_id):
        """Проверить, является ли умение временным от экипировки"""
        if not hasattr(self, 'equipment_skills'):
            return False
        if skill_id not in self.equipment_skills:
            return False
        return self.equipment_skills[skill_id].get('from_equipment', False)

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

    def try_rank_up_skill(self, skill_id, player):
        """
        Попытаться повысить ранг умения

        Args:
            skill_id: ID умения
            player: Игрок

        Returns:
            tuple: (bool, str) - успех и сообщение
        """
        if skill_id not in self.learned_skills:
            return False, "Умение не найдено"

        skill = self.learned_skills[skill_id]
        return skill.try_rank_up(player)
