"""
Test Arena - Тестовая площадка для проверки умений
Основной класс арены с рендерингом и логикой
"""

import pygame
import os
import sys
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .entities import TestCharacter, TestPlayer, TestNPC, NPCGroup, EntityType
from .skill_loader import SkillsCrafterLoader, TestSkill


@dataclass
class ArenaUnit:
    """Юнит на арене"""
    character: TestCharacter
    x: int  # Позиция на сетке
    y: int
    is_selected: bool = False


@dataclass
class AnimationState:
    """Состояние анимации умения"""
    active: bool = False
    skill: Optional[TestSkill] = None
    caster: Optional[ArenaUnit] = None
    target: Optional[ArenaUnit] = None
    start_time: float = 0.0
    duration: float = 0.5
    current_frame: int = 0
    frame_start_time: float = 0.0

    # Для снарядов
    projectile_x: float = 0.0
    projectile_y: float = 0.0
    projectile_start_x: float = 0.0
    projectile_start_y: float = 0.0
    projectile_end_x: float = 0.0
    projectile_end_y: float = 0.0

    # Дополнительные параметры
    trajectory: str = "straight"
    speed: float = 300.0
    distance: float = 0.0
    effect_color: Tuple[int, int, int] = (255, 200, 100)

    # Загруженные спрайты анимации
    loaded_sprites: List = field(default_factory=list)
    impact_active: bool = False
    impact_start_time: float = 0.0


class TestArena:
    """
    Тестовая арена для проверки умений из Skills Crafter

    Изолированная среда, максимально приближенная к тактическому бою,
    но работающая независимо от основного кода игры.
    """

    # Размеры арены
    ARENA_WIDTH = 16  # клеток
    ARENA_HEIGHT = 10  # клеток
    CELL_SIZE = 64  # пикселей

    # Цвета
    COLORS = {
        "background": (30, 30, 40),
        "grid": (60, 60, 80),
        "grid_highlight": (80, 80, 120),
        "player": (80, 180, 80),
        "player_selected": (120, 255, 120),
        "enemy": (180, 80, 80),
        "enemy_selected": (255, 120, 120),
        "ally": (80, 80, 180),
        "neutral": (150, 150, 150),
        "skill_range": (100, 100, 200, 100),
        "skill_area": (200, 100, 100, 80),
        "text": (255, 255, 255),
        "text_dark": (180, 180, 180),
        "panel": (40, 40, 55),
        "panel_border": (100, 100, 140),
        "button": (60, 60, 80),
        "button_hover": (80, 80, 100),
        "button_active": (100, 100, 140),
        "health_bar": (80, 200, 80),
        "health_bar_low": (200, 80, 80),
        "mana_bar": (80, 120, 200),
        "stamina_bar": (200, 180, 80),
    }

    def __init__(self, screen_width: int = 1400, screen_height: int = 900):
        """
        Инициализация тестовой арены

        Args:
            screen_width: Ширина экрана
            screen_height: Высота экрана
        """
        # Инициализация pygame
        pygame.init()
        pygame.font.init()

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Skills Crafter - Test Arena")

        # Шрифты
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 18)

        # Юниты на арене
        self.player_unit: Optional[ArenaUnit] = None
        self.ally_units: List[ArenaUnit] = []
        self.enemy_units: List[ArenaUnit] = []
        self.all_units: List[ArenaUnit] = []

        # Загрузчик умений
        self.skill_loader = SkillsCrafterLoader()
        self.available_skills: Dict[str, TestSkill] = {}

        # Состояние арены
        self.selected_unit: Optional[ArenaUnit] = None
        self.selected_skill: Optional[TestSkill] = None
        self.hovered_cell: Optional[Tuple[int, int]] = None
        self.target_unit: Optional[ArenaUnit] = None

        # Анимация
        self.animation = AnimationState()

        # Лог событий
        self.combat_log: List[str] = []
        self.max_log_entries = 15

        # Состояние UI
        self.skill_buttons: List[Tuple[pygame.Rect, TestSkill]] = []
        self.action_buttons: List[Tuple[pygame.Rect, str, str]] = []  # rect, action_id, label

        # Флаги
        self.running = True
        self.paused = False

        # Размеры панелей
        self.arena_x = 20
        self.arena_y = 80
        self.side_panel_width = 320
        self.bottom_panel_height = 180

        # Спрайты (опционально загружаются)
        self.sprites: Dict[str, pygame.Surface] = {}
        self.skill_icons: Dict[str, pygame.Surface] = {}  # Иконки умений
        self._load_sprites()

    def _load_sprites(self):
        """Попытаться загрузить спрайты из основного конфига игры"""
        config_path = "game/config/assets_config.json"
        if not os.path.exists(config_path):
            return

        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Загружаем спрайты NPC
            for npc_type, sprite_data in config.get('npcs', {}).items():
                if isinstance(sprite_data, dict):
                    sprite_path = sprite_data.get('default', '')
                else:
                    sprite_path = sprite_data

                if sprite_path and os.path.exists(sprite_path):
                    try:
                        sprite = pygame.image.load(sprite_path).convert_alpha()
                        sprite = pygame.transform.scale(sprite, (self.CELL_SIZE - 8, self.CELL_SIZE - 8))
                        self.sprites[npc_type] = sprite
                    except Exception:
                        pass

            # Загружаем спрайт игрока
            player_sprite = config.get('npcs', {}).get('player', '')
            if isinstance(player_sprite, dict):
                player_sprite = player_sprite.get('default', '')
            if player_sprite and os.path.exists(player_sprite):
                try:
                    sprite = pygame.image.load(player_sprite).convert_alpha()
                    sprite = pygame.transform.scale(sprite, (self.CELL_SIZE - 8, self.CELL_SIZE - 8))
                    self.sprites['player'] = sprite
                except Exception:
                    pass

        except Exception as e:
            print(f"Не удалось загрузить спрайты: {e}")

    def _load_skill_icons(self):
        """Загрузить иконки умений"""
        for skill_id, skill in self.available_skills.items():
            if skill.icon_path:
                # Нормализуем путь
                icon_path = skill.icon_path.replace("\\", "/")

                # Пробуем разные базовые пути
                paths_to_try = [
                    icon_path,
                    os.path.join("utils/skills_crafter", icon_path),
                    os.path.join("game/assets", icon_path),
                    os.path.join("assets", icon_path),
                ]

                for path in paths_to_try:
                    if os.path.exists(path):
                        try:
                            icon = pygame.image.load(path).convert_alpha()
                            icon = pygame.transform.scale(icon, (40, 40))
                            self.skill_icons[skill_id] = icon
                            break
                        except Exception as e:
                            print(f"Ошибка загрузки иконки {path}: {e}")

    def setup_default_arena(self):
        """Настроить арену с дефолтным расположением"""
        # Загружаем умения из test_skills.json
        self.available_skills = self.skill_loader.load_from_test_config()

        # Если конфиг пуст, используем умения по умолчанию
        if not self.available_skills:
            print("Конфиг test_skills.json не найден, используем дефолтные умения")
            self.available_skills = self.skill_loader.create_default_skills()

        # Загружаем иконки умений
        self._load_skill_icons()

        # Создаем игрока
        player = TestPlayer("Герой", level=15)
        self.player_unit = ArenaUnit(player, 2, self.ARENA_HEIGHT // 2)
        self.all_units.append(self.player_unit)

        # Создаем группу врагов
        enemy_group = NPCGroup.create_enemy_group("bandit", 3, base_level=10)
        for i, npc in enumerate(enemy_group.npcs):
            unit = ArenaUnit(npc, self.ARENA_WIDTH - 3, 2 + i * 2)
            self.enemy_units.append(unit)
            self.all_units.append(unit)

        # Создаем одиночных врагов разных типов
        solo_enemies = [
            ("mage", 12, self.ARENA_WIDTH - 4, 1),
            ("undead", 8, self.ARENA_WIDTH - 2, 5),
            ("wolf", 6, self.ARENA_WIDTH - 2, 8),
        ]
        for npc_type, level, x, y in solo_enemies:
            npc = TestNPC(npc_type, level, EntityType.NPC_ENEMY)
            unit = ArenaUnit(npc, x, y)
            self.enemy_units.append(unit)
            self.all_units.append(unit)

        # Создаем союзников
        ally_configs = [
            ("guard", 10, 1, 3),
            ("guard", 12, 1, 7),
        ]
        for npc_type, level, x, y in ally_configs:
            npc = TestNPC(npc_type, level, EntityType.NPC_ALLY)
            unit = ArenaUnit(npc, x, y)
            self.ally_units.append(unit)
            self.all_units.append(unit)

        # Добавляем манекен для тестирования
        dummy = TestNPC("dummy", 1, EntityType.NPC_NEUTRAL, "Тренировочный манекен")
        dummy_unit = ArenaUnit(dummy, self.ARENA_WIDTH // 2, self.ARENA_HEIGHT // 2)
        self.all_units.append(dummy_unit)

        # Назначаем умения игроку
        self.selected_unit = self.player_unit

        self.add_to_log("=== ТЕСТОВАЯ АРЕНА ГОТОВА ===")
        self.add_to_log("Выберите умение и цель для тестирования")

    def add_to_log(self, message: str):
        """Добавить сообщение в лог"""
        self.combat_log.append(message)
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)

    def get_cell_at_screen_pos(self, screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """Получить координаты клетки по экранным координатам"""
        x = screen_x - self.arena_x
        y = screen_y - self.arena_y

        if x < 0 or y < 0:
            return None

        cell_x = x // self.CELL_SIZE
        cell_y = y // self.CELL_SIZE

        if cell_x >= self.ARENA_WIDTH or cell_y >= self.ARENA_HEIGHT:
            return None

        return (cell_x, cell_y)

    def get_unit_at_cell(self, cell_x: int, cell_y: int) -> Optional[ArenaUnit]:
        """Получить юнита в указанной клетке"""
        for unit in self.all_units:
            if unit.x == cell_x and unit.y == cell_y and unit.character.is_alive:
                return unit
        return None

    def get_screen_pos_for_cell(self, cell_x: int, cell_y: int) -> Tuple[int, int]:
        """Получить экранные координаты центра клетки"""
        screen_x = self.arena_x + cell_x * self.CELL_SIZE + self.CELL_SIZE // 2
        screen_y = self.arena_y + cell_y * self.CELL_SIZE + self.CELL_SIZE // 2
        return (screen_x, screen_y)

    def can_move_to(self, cell_x: int, cell_y: int) -> bool:
        """Проверить, можно ли переместиться в клетку"""
        # Проверяем границы
        if cell_x < 0 or cell_x >= self.ARENA_WIDTH:
            return False
        if cell_y < 0 or cell_y >= self.ARENA_HEIGHT:
            return False

        # Проверяем, занята ли клетка
        if self.get_unit_at_cell(cell_x, cell_y):
            return False

        return True

    def move_player_to(self, cell_x: int, cell_y: int) -> bool:
        """Переместить игрока в указанную клетку"""
        if not self.player_unit:
            return False

        if not self.can_move_to(cell_x, cell_y):
            return False

        old_x, old_y = self.player_unit.x, self.player_unit.y
        self.player_unit.x = cell_x
        self.player_unit.y = cell_y

        # Логируем перемещение (опционально)
        # self.add_to_log(f"Герой перемещается ({old_x},{old_y}) -> ({cell_x},{cell_y})")

        return True

    def get_movement_range(self) -> List[Tuple[int, int]]:
        """Получить список клеток, доступных для перемещения"""
        if not self.player_unit:
            return []

        reachable = []
        px, py = self.player_unit.x, self.player_unit.y

        # Простое перемещение - любая клетка в пределах арены
        for x in range(self.ARENA_WIDTH):
            for y in range(self.ARENA_HEIGHT):
                if self.can_move_to(x, y):
                    reachable.append((x, y))

        return reachable

    def use_skill_on_target(self, skill: TestSkill, caster: ArenaUnit, target: ArenaUnit):
        """Использовать умение на цель"""
        result = skill.use(caster.character, target.character)

        if result["success"]:
            self.add_to_log(result["message"])

            # Запускаем анимацию
            self.start_animation(skill, caster, target)

            # Удаляем мертвых
            for unit in self.all_units[:]:
                if not unit.character.is_alive:
                    if unit != self.player_unit:
                        self.add_to_log(f"{unit.character.name} уничтожен!")
        else:
            self.add_to_log(f"Ошибка: {result['message']}")

    def start_animation(self, skill: TestSkill, caster: ArenaUnit, target: ArenaUnit):
        """Запустить анимацию умения"""
        self.animation.active = True
        self.animation.skill = skill
        self.animation.caster = caster
        self.animation.target = target
        self.animation.start_time = pygame.time.get_ticks() / 1000.0
        self.animation.current_frame = 0
        self.animation.frame_start_time = self.animation.start_time
        self.animation.impact_active = False

        # Получаем цвет эффекта из скилла
        self.animation.effect_color = skill.get_effect_color()

        # Загружаем спрайты анимации, если есть
        self.animation.loaded_sprites = []
        if skill.animation_frames:
            for frame in skill.animation_frames:
                if frame.sprite_path:
                    # Нормализуем путь
                    sprite_path = frame.sprite_path.replace("\\", "/")

                    # Пробуем разные базовые пути
                    paths_to_try = [
                        sprite_path,
                        os.path.join("utils/skills_crafter", sprite_path),
                        os.path.join("game/assets", sprite_path),
                        os.path.join("assets", sprite_path),
                    ]

                    loaded = False
                    for path in paths_to_try:
                        if os.path.exists(path):
                            try:
                                sprite = pygame.image.load(path).convert_alpha()
                                # Масштабируем спрайт согласно визуальному размеру
                                sprite_size = int(64 * skill.animation_scale)
                                sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))
                                self.animation.loaded_sprites.append((sprite, frame.duration_ms))
                                loaded = True
                                self.add_to_log(f"Загружен спрайт: {os.path.basename(path)}")
                                break
                            except Exception as e:
                                self.add_to_log(f"Ошибка загрузки спрайта: {e}")

                    if not loaded and frame.sprite_path:
                        self.add_to_log(f"Спрайт не найден: {frame.sprite_path}")

        # Параметры траектории
        self.animation.trajectory = skill.projectile_trajectory
        self.animation.speed = skill.projectile_speed

        # Для снарядов
        if skill.animation_type == "projectile":
            caster_pos = self.get_screen_pos_for_cell(caster.x, caster.y)
            target_pos = self.get_screen_pos_for_cell(target.x, target.y)
            self.animation.projectile_start_x = caster_pos[0]
            self.animation.projectile_start_y = caster_pos[1]
            self.animation.projectile_end_x = target_pos[0]
            self.animation.projectile_end_y = target_pos[1]
            self.animation.projectile_x = caster_pos[0]
            self.animation.projectile_y = caster_pos[1]

            # Вычисляем дистанцию и длительность на основе скорости
            dx = target_pos[0] - caster_pos[0]
            dy = target_pos[1] - caster_pos[1]
            self.animation.distance = math.sqrt(dx * dx + dy * dy)

            # Длительность = дистанция / скорость (скорость в пикселях/сек)
            self.animation.duration = self.animation.distance / self.animation.speed
        else:
            # Для других типов: если есть кадры анимации, считаем общую длительность
            if self.animation.loaded_sprites:
                total_duration_ms = sum(duration for _, duration in self.animation.loaded_sprites)
                self.animation.duration = total_duration_ms / 1000.0
            elif skill.animation_duration > 0:
                self.animation.duration = skill.animation_duration
            else:
                self.animation.duration = 0.5

    def update_animation(self):
        """Обновить состояние анимации"""
        if not self.animation.active:
            return

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.animation.start_time
        progress = min(1.0, elapsed / self.animation.duration) if self.animation.duration > 0 else 1.0

        skill = self.animation.skill
        if skill and skill.animation_type == "projectile":
            # Базовое линейное перемещение
            base_x = (
                self.animation.projectile_start_x +
                (self.animation.projectile_end_x - self.animation.projectile_start_x) * progress
            )
            base_y = (
                self.animation.projectile_start_y +
                (self.animation.projectile_end_y - self.animation.projectile_start_y) * progress
            )

            # Применяем траекторию
            trajectory = self.animation.trajectory

            if trajectory == "arc":
                # Дуговая траектория - параболическое смещение по вертикали
                arc_height = self.animation.distance * 0.3  # Высота дуги - 30% от дистанции
                arc_offset = -arc_height * 4 * progress * (1 - progress)  # Парабола
                base_y += arc_offset

            elif trajectory == "wave":
                # Волнистая траектория - синусоидальное смещение
                wave_amplitude = 30  # Амплитуда волны
                wave_frequency = 3  # Частота волн
                # Направление волны перпендикулярно движению
                dx = self.animation.projectile_end_x - self.animation.projectile_start_x
                dy = self.animation.projectile_end_y - self.animation.projectile_start_y
                dist = math.sqrt(dx * dx + dy * dy) if dx or dy else 1
                # Перпендикулярный вектор
                perp_x = -dy / dist
                perp_y = dx / dist
                wave_offset = math.sin(progress * wave_frequency * math.pi * 2) * wave_amplitude
                base_x += perp_x * wave_offset
                base_y += perp_y * wave_offset

            elif trajectory == "homing":
                # Самонаводящаяся траектория - движется к текущей позиции цели
                if self.animation.target:
                    target_pos = self.get_screen_pos_for_cell(
                        self.animation.target.x,
                        self.animation.target.y
                    )
                    # Плавное наведение
                    lerp_factor = min(1.0, progress * 2)
                    base_x = base_x + (target_pos[0] - base_x) * lerp_factor * 0.5
                    base_y = base_y + (target_pos[1] - base_y) * lerp_factor * 0.5

            self.animation.projectile_x = base_x
            self.animation.projectile_y = base_y

            # Проверяем достижение цели
            if progress >= 1.0:
                # Запускаем эффект попадания
                self.animation.impact_active = True
                self.animation.impact_start_time = current_time

        # Обновляем текущий кадр анимации
        if self.animation.loaded_sprites:
            frame_elapsed = (current_time - self.animation.frame_start_time) * 1000  # в мс
            if self.animation.current_frame < len(self.animation.loaded_sprites):
                _, frame_duration = self.animation.loaded_sprites[self.animation.current_frame]
                if frame_elapsed >= frame_duration:
                    self.animation.current_frame += 1
                    self.animation.frame_start_time = current_time

        # Проверяем завершение
        if progress >= 1.0:
            if skill and skill.animation_type == "projectile":
                # Для снарядов даем время на эффект попадания
                impact_elapsed = current_time - self.animation.impact_start_time
                if impact_elapsed >= 0.3:  # 300мс на эффект попадания
                    self.animation.active = False
                    self.animation.impact_active = False
            else:
                self.animation.active = False

    def tick_all_effects(self):
        """Обработать все статус-эффекты"""
        for unit in self.all_units:
            if unit.character.is_alive:
                messages = unit.character.tick_status_effects()
                for msg in messages:
                    self.add_to_log(msg)

        # Сбрасываем перезарядки
        for skill in self.available_skills.values():
            skill.tick_cooldown()

    def reset_arena(self):
        """Сбросить состояние арены"""
        for unit in self.all_units:
            unit.character.reset()

        for skill in self.available_skills.values():
            skill.current_cooldown = 0

        self.combat_log.clear()
        self.add_to_log("=== АРЕНА СБРОШЕНА ===")

    def handle_events(self):
        """Обработка событий pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Блокируем действия во время анимации
                elif self.animation.active:
                    continue
                elif event.key == pygame.K_r:
                    self.reset_arena()
                elif event.key == pygame.K_SPACE:
                    self.tick_all_effects()
                    self.add_to_log("--- Новый ход ---")
                # Выбор умений клавишами 1-8
                elif event.key in range(pygame.K_1, pygame.K_9):
                    skill_index = event.key - pygame.K_1
                    skills = list(self.available_skills.values())
                    if skill_index < len(skills):
                        self.selected_skill = skills[skill_index]
                        self.add_to_log(f"Выбрано умение: {self.selected_skill.name}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Блокируем клики во время анимации
                if self.animation.active:
                    continue
                if event.button == 1:  # ЛКМ
                    self.handle_click(event.pos)
                elif event.button == 3:  # ПКМ
                    self.selected_skill = None
                    self.target_unit = None

            elif event.type == pygame.MOUSEMOTION:
                self.hovered_cell = self.get_cell_at_screen_pos(*event.pos)

    def handle_click(self, pos: Tuple[int, int]):
        """Обработка клика мыши"""
        # Сначала проверяем клик по кнопкам умений
        for rect, skill in self.skill_buttons:
            if rect.collidepoint(pos):
                self.selected_skill = skill
                self.add_to_log(f"Выбрано умение: {skill.name}")
                return

        # Проверяем клик по кнопкам действий
        for rect, action_id, _ in self.action_buttons:
            if rect.collidepoint(pos):
                if action_id == "reset":
                    self.reset_arena()
                elif action_id == "next_turn":
                    self.tick_all_effects()
                    self.add_to_log("--- Новый ход ---")
                return

        # Проверяем клик по арене
        cell = self.get_cell_at_screen_pos(*pos)
        if cell:
            unit = self.get_unit_at_cell(*cell)

            if self.selected_skill and unit:
                # Используем умение на цель
                if self.player_unit and unit != self.player_unit:
                    self.use_skill_on_target(self.selected_skill, self.player_unit, unit)
                    self.selected_skill = None
            elif unit:
                # Выбираем юнита как цель
                self.target_unit = unit
                self.add_to_log(f"Выбрана цель: {unit.character.name}")
            else:
                # Клик на пустую клетку - перемещение игрока
                if self.move_player_to(cell[0], cell[1]):
                    pass  # Перемещение успешно
                    # self.add_to_log(f"Перемещение в ({cell[0]}, {cell[1]})")

    def render(self):
        """Отрисовка арены"""
        self.screen.fill(self.COLORS["background"])

        # Заголовок
        self._render_header()

        # Арена (сетка)
        self._render_arena_grid()

        # Область действия умения
        if self.selected_skill:
            self._render_skill_range()

        # Юниты
        self._render_units()

        # Анимация
        if self.animation.active:
            self._render_animation()

        # Боковая панель
        self._render_side_panel()

        # Панель умений
        self._render_skills_panel()

        # Лог
        self._render_combat_log()

        pygame.display.flip()

    def _render_header(self):
        """Отрисовка заголовка"""
        title = self.font_large.render("SKILLS CRAFTER - TEST ARENA", True, (255, 215, 0))
        self.screen.blit(title, (self.arena_x, 20))

        # Подсказки
        hints = [
            "1-8: умение",
            "ЛКМ(пусто): ходить",
            "ЛКМ(враг): атака/цель",
            "ПКМ: отмена",
            "R: сброс",
            "Space: ход",
            "Esc: выход"
        ]
        hint_text = " | ".join(hints)
        hint_surface = self.font_small.render(hint_text, True, self.COLORS["text_dark"])
        self.screen.blit(hint_surface, (self.arena_x, 50))

    def _render_arena_grid(self):
        """Отрисовка сетки арены"""
        arena_width = self.ARENA_WIDTH * self.CELL_SIZE
        arena_height = self.ARENA_HEIGHT * self.CELL_SIZE

        # Фон арены
        pygame.draw.rect(
            self.screen,
            (45, 45, 60),
            (self.arena_x, self.arena_y, arena_width, arena_height)
        )

        # Сетка
        for x in range(self.ARENA_WIDTH + 1):
            start = (self.arena_x + x * self.CELL_SIZE, self.arena_y)
            end = (self.arena_x + x * self.CELL_SIZE, self.arena_y + arena_height)
            pygame.draw.line(self.screen, self.COLORS["grid"], start, end, 1)

        for y in range(self.ARENA_HEIGHT + 1):
            start = (self.arena_x, self.arena_y + y * self.CELL_SIZE)
            end = (self.arena_x + arena_width, self.arena_y + y * self.CELL_SIZE)
            pygame.draw.line(self.screen, self.COLORS["grid"], start, end, 1)

        # Подсветка клетки под курсором
        if self.hovered_cell:
            hx, hy = self.hovered_cell
            pygame.draw.rect(
                self.screen,
                self.COLORS["grid_highlight"],
                (
                    self.arena_x + hx * self.CELL_SIZE,
                    self.arena_y + hy * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE
                ),
                2
            )

        # Рамка арены
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel_border"],
            (self.arena_x, self.arena_y, arena_width, arena_height),
            3
        )

    def _render_skill_range(self):
        """Отрисовка радиуса действия умения"""
        if not self.selected_skill or not self.player_unit:
            return

        skill = self.selected_skill
        center_x, center_y = self.player_unit.x, self.player_unit.y
        skill_range = skill.tactical_range

        # Создаем полупрозрачную поверхность
        range_surface = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE), pygame.SRCALPHA)
        range_surface.fill(self.COLORS["skill_range"])

        for dx in range(-skill_range, skill_range + 1):
            for dy in range(-skill_range, skill_range + 1):
                cell_x = center_x + dx
                cell_y = center_y + dy

                if cell_x < 0 or cell_x >= self.ARENA_WIDTH:
                    continue
                if cell_y < 0 or cell_y >= self.ARENA_HEIGHT:
                    continue

                # Евклидово расстояние
                distance = (dx * dx + dy * dy) ** 0.5
                if distance > skill_range:
                    continue

                screen_x = self.arena_x + cell_x * self.CELL_SIZE
                screen_y = self.arena_y + cell_y * self.CELL_SIZE

                self.screen.blit(range_surface, (screen_x, screen_y))

    def _render_units(self):
        """Отрисовка юнитов"""
        for unit in self.all_units:
            if not unit.character.is_alive:
                continue

            self._render_unit(unit)

    def _render_unit(self, unit: ArenaUnit):
        """Отрисовка одного юнита"""
        screen_x = self.arena_x + unit.x * self.CELL_SIZE
        screen_y = self.arena_y + unit.y * self.CELL_SIZE

        # Определяем цвет
        if unit.character.entity_type == EntityType.PLAYER:
            color = self.COLORS["player_selected"] if unit == self.selected_unit else self.COLORS["player"]
        elif unit.character.entity_type == EntityType.NPC_ENEMY:
            color = self.COLORS["enemy_selected"] if unit == self.target_unit else self.COLORS["enemy"]
        elif unit.character.entity_type == EntityType.NPC_ALLY:
            color = self.COLORS["ally"]
        else:
            color = self.COLORS["neutral"]

        # Фон клетки
        pygame.draw.rect(
            self.screen,
            color,
            (screen_x + 2, screen_y + 2, self.CELL_SIZE - 4, self.CELL_SIZE - 4)
        )

        # Рамка
        border_color = (255, 255, 255) if unit == self.target_unit else (200, 200, 200)
        border_width = 3 if unit == self.target_unit else 2
        pygame.draw.rect(
            self.screen,
            border_color,
            (screen_x + 2, screen_y + 2, self.CELL_SIZE - 4, self.CELL_SIZE - 4),
            border_width
        )

        # Спрайт или текст
        sprite_id = unit.character.sprite_id
        if sprite_id and sprite_id in self.sprites:
            sprite = self.sprites[sprite_id]
            sprite_x = screen_x + (self.CELL_SIZE - sprite.get_width()) // 2
            sprite_y = screen_y + (self.CELL_SIZE - sprite.get_height()) // 2
            self.screen.blit(sprite, (sprite_x, sprite_y))
        else:
            # Fallback - первая буква имени
            label = unit.character.name[0].upper()
            label_surface = self.font_large.render(label, True, (255, 255, 255))
            label_x = screen_x + (self.CELL_SIZE - label_surface.get_width()) // 2
            label_y = screen_y + (self.CELL_SIZE - label_surface.get_height()) // 2
            self.screen.blit(label_surface, (label_x, label_y))

        # Полоски здоровья
        self._render_unit_bars(unit, screen_x, screen_y)

    def _render_unit_bars(self, unit: ArenaUnit, screen_x: int, screen_y: int):
        """Отрисовка полосок ресурсов юнита"""
        bar_width = self.CELL_SIZE - 8
        bar_height = 4
        bar_x = screen_x + 4
        bar_y = screen_y - 12

        char = unit.character

        # HP
        hp_ratio = char.health / char.max_health
        hp_color = self.COLORS["health_bar"] if hp_ratio > 0.3 else self.COLORS["health_bar_low"]

        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        if hp_ratio > 0:
            pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

        # Mana
        bar_y += bar_height + 1
        mana_ratio = char.mana / char.max_mana if char.max_mana > 0 else 0
        pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_width, bar_height))
        if mana_ratio > 0:
            pygame.draw.rect(
                self.screen,
                self.COLORS["mana_bar"],
                (bar_x, bar_y, int(bar_width * mana_ratio), bar_height)
            )
        pygame.draw.rect(self.screen, (150, 150, 200), (bar_x, bar_y, bar_width, bar_height), 1)

    def _render_animation(self):
        """Отрисовка анимации"""
        if not self.animation.active or not self.animation.skill:
            return

        skill = self.animation.skill
        color = self.animation.effect_color
        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.animation.start_time
        progress = min(1.0, elapsed / self.animation.duration) if self.animation.duration > 0 else 1.0

        if skill.animation_type == "projectile":
            # Рисуем снаряд, если еще не достиг цели
            if not self.animation.impact_active:
                proj_x = int(self.animation.projectile_x)
                proj_y = int(self.animation.projectile_y)

                # Если есть загруженные спрайты, используем их
                if self.animation.loaded_sprites and self.animation.current_frame < len(self.animation.loaded_sprites):
                    sprite, _ = self.animation.loaded_sprites[self.animation.current_frame]
                    sprite_x = proj_x - sprite.get_width() // 2
                    sprite_y = proj_y - sprite.get_height() // 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    # Рисуем снаряд с цветом из конфига
                    pygame.draw.circle(self.screen, color, (proj_x, proj_y), 10)

                    # Эффект свечения
                    glow_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (*color, 100), (20, 20), 18)
                    pygame.draw.circle(glow_surface, (*color, 50), (20, 20), 24)
                    self.screen.blit(glow_surface, (proj_x - 20, proj_y - 20))

                    # Хвост снаряда
                    trail_length = 5
                    for i in range(trail_length):
                        trail_progress = max(0, progress - i * 0.02)
                        if trail_progress > 0:
                            trail_x = int(
                                self.animation.projectile_start_x +
                                (self.animation.projectile_end_x - self.animation.projectile_start_x) * trail_progress
                            )
                            trail_y = int(
                                self.animation.projectile_start_y +
                                (self.animation.projectile_end_y - self.animation.projectile_start_y) * trail_progress
                            )
                            trail_alpha = int(150 * (1 - i / trail_length))
                            trail_radius = int(8 * (1 - i / trail_length))
                            trail_surface = pygame.Surface((trail_radius * 2, trail_radius * 2), pygame.SRCALPHA)
                            pygame.draw.circle(trail_surface, (*color, trail_alpha), (trail_radius, trail_radius), trail_radius)
                            self.screen.blit(trail_surface, (trail_x - trail_radius, trail_y - trail_radius))

            # Эффект попадания
            if self.animation.impact_active and self.animation.target:
                self._render_impact_effect(color)

        elif skill.animation_type == "impact":
            # Мгновенный эффект на цели (молния и т.п.)
            if self.animation.target:
                target_pos = self.get_screen_pos_for_cell(
                    self.animation.target.x,
                    self.animation.target.y
                )

                # Если есть загруженные спрайты, используем их
                if self.animation.loaded_sprites and self.animation.current_frame < len(self.animation.loaded_sprites):
                    sprite, _ = self.animation.loaded_sprites[self.animation.current_frame]
                    sprite_x = target_pos[0] - sprite.get_width() // 2
                    sprite_y = target_pos[1] - sprite.get_height() // 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    # Fallback на burst эффект
                    self._render_impact_effect(color, "burst")

        elif skill.animation_type == "on_target":
            # Эффект на цели (лечение и т.п.)
            if self.animation.target:
                target_pos = self.get_screen_pos_for_cell(
                    self.animation.target.x,
                    self.animation.target.y
                )
                self._render_healing_effect(target_pos, color, progress)

        elif skill.animation_type == "on_caster":
            # Эффект на кастере (баффы, регенерация)
            if self.animation.caster:
                caster_pos = self.get_screen_pos_for_cell(
                    self.animation.caster.x,
                    self.animation.caster.y
                )
                self._render_buff_effect(caster_pos, color, progress)

        elif skill.animation_type == "static":
            # Статичный эффект (ближний бой)
            if self.animation.target:
                self._render_melee_effect(color, progress)

        elif skill.animation_type == "beam":
            # Луч от кастера к цели
            if self.animation.caster and self.animation.target:
                self._render_beam_effect(color, progress)

    def _render_beam_effect(self, color: Tuple[int, int, int], progress: float):
        """Отрисовка эффекта луча"""
        if not self.animation.caster or not self.animation.target:
            return

        caster_pos = self.get_screen_pos_for_cell(
            self.animation.caster.x,
            self.animation.caster.y
        )
        target_pos = self.get_screen_pos_for_cell(
            self.animation.target.x,
            self.animation.target.y
        )

        # Фаза появления (0-0.2), удержания (0.2-0.8), затухания (0.8-1.0)
        if progress < 0.2:
            # Луч растет от кастера к цели
            beam_progress = progress / 0.2
            end_x = caster_pos[0] + (target_pos[0] - caster_pos[0]) * beam_progress
            end_y = caster_pos[1] + (target_pos[1] - caster_pos[1]) * beam_progress
            alpha = 255
            width = int(6 * beam_progress) + 2
        elif progress < 0.8:
            # Луч держится
            end_x, end_y = target_pos[0], target_pos[1]
            alpha = 255
            # Пульсация ширины
            pulse = abs(math.sin((progress - 0.2) * 10 * math.pi))
            width = int(6 + 4 * pulse)
        else:
            # Луч затухает
            fade_progress = (progress - 0.8) / 0.2
            end_x, end_y = target_pos[0], target_pos[1]
            alpha = int(255 * (1 - fade_progress))
            width = int(8 * (1 - fade_progress)) + 2

        # Рисуем внешнее свечение
        glow_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        glow_color = (*color, int(alpha * 0.3))
        pygame.draw.line(glow_surface, glow_color, caster_pos, (int(end_x), int(end_y)), width + 8)
        self.screen.blit(glow_surface, (0, 0))

        # Рисуем средний слой
        mid_color = (*color, int(alpha * 0.6))
        mid_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.draw.line(mid_surface, mid_color, caster_pos, (int(end_x), int(end_y)), width + 4)
        self.screen.blit(mid_surface, (0, 0))

        # Рисуем яркое ядро луча
        core_color = (255, 255, 255, alpha)
        core_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.draw.line(core_surface, core_color, caster_pos, (int(end_x), int(end_y)), width)
        self.screen.blit(core_surface, (0, 0))

        # Эффект на цели (только когда луч достиг)
        if progress >= 0.2:
            impact_alpha = alpha
            impact_radius = int(15 + 10 * abs(math.sin(progress * 8 * math.pi)))
            impact_surface = pygame.Surface((impact_radius * 2, impact_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(impact_surface, (*color, int(impact_alpha * 0.5)), (impact_radius, impact_radius), impact_radius)
            self.screen.blit(impact_surface, (target_pos[0] - impact_radius, target_pos[1] - impact_radius))

    def _render_impact_effect(self, color: Tuple[int, int, int], effect_type: str = "explosion"):
        """Отрисовка эффекта попадания"""
        if not self.animation.target:
            return

        target_pos = self.get_screen_pos_for_cell(
            self.animation.target.x,
            self.animation.target.y
        )

        current_time = pygame.time.get_ticks() / 1000.0
        impact_elapsed = current_time - self.animation.impact_start_time if self.animation.impact_active else 0
        impact_progress = min(1.0, impact_elapsed / 0.3)

        if effect_type == "burst":
            # Взрыв с лучами (для молнии)
            current_time = pygame.time.get_ticks() / 1000.0
            elapsed = current_time - self.animation.start_time
            progress = min(1.0, elapsed / self.animation.duration) if self.animation.duration > 0 else 1.0

            num_rays = 8
            max_ray_length = 40
            ray_length = max_ray_length * (1 - abs(progress - 0.5) * 2)

            for i in range(num_rays):
                angle = (i / num_rays) * math.pi * 2 + current_time * 5
                end_x = target_pos[0] + math.cos(angle) * ray_length
                end_y = target_pos[1] + math.sin(angle) * ray_length
                pygame.draw.line(self.screen, color, target_pos, (int(end_x), int(end_y)), 3)

            # Центральная вспышка
            flash_radius = int(25 * (1 - abs(progress - 0.5) * 2))
            flash_alpha = int(200 * (1 - progress))
            flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surface, (*color, flash_alpha), (flash_radius, flash_radius), flash_radius)
            self.screen.blit(flash_surface, (target_pos[0] - flash_radius, target_pos[1] - flash_radius))
        else:
            # Расширяющийся взрыв
            max_radius = 35
            radius = int(max_radius * impact_progress)
            alpha = int(200 * (1 - impact_progress))

            explosion_surface = pygame.Surface((max_radius * 2 + 10, max_radius * 2 + 10), pygame.SRCALPHA)
            center = max_radius + 5
            pygame.draw.circle(explosion_surface, (*color, alpha), (center, center), radius)
            pygame.draw.circle(explosion_surface, (*color, int(alpha * 0.5)), (center, center), radius + 5)
            self.screen.blit(explosion_surface, (target_pos[0] - center, target_pos[1] - center))

            # Частицы
            num_particles = 8
            for i in range(num_particles):
                angle = (i / num_particles) * math.pi * 2
                particle_dist = radius * 0.8
                particle_x = target_pos[0] + math.cos(angle) * particle_dist
                particle_y = target_pos[1] + math.sin(angle) * particle_dist
                particle_radius = int(4 * (1 - impact_progress))
                if particle_radius > 0:
                    pygame.draw.circle(self.screen, color, (int(particle_x), int(particle_y)), particle_radius)

    def _render_healing_effect(self, pos: Tuple[int, int], color: Tuple[int, int, int], progress: float):
        """Отрисовка эффекта лечения"""
        # Зеленые частицы поднимающиеся вверх
        heal_color = (100, 255, 100) if color == (200, 180, 100) else color

        num_particles = 6
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2
            base_x = pos[0] + math.cos(angle) * 20
            offset_y = -40 * progress
            particle_y = pos[1] + offset_y + math.sin(progress * math.pi * 2 + i) * 10

            alpha = int(200 * (1 - progress))
            particle_radius = int(5 * (1 - progress * 0.5))

            if particle_radius > 0:
                particle_surface = pygame.Surface((particle_radius * 2, particle_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (*heal_color, alpha), (particle_radius, particle_radius), particle_radius)
                self.screen.blit(particle_surface, (int(base_x) - particle_radius, int(particle_y) - particle_radius))

        # Центральный эффект
        pulse = abs(math.sin(progress * math.pi * 3))
        center_radius = int(15 + 10 * pulse)
        center_alpha = int(150 * (1 - progress))
        center_surface = pygame.Surface((center_radius * 2, center_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(center_surface, (*heal_color, center_alpha), (center_radius, center_radius), center_radius)
        self.screen.blit(center_surface, (pos[0] - center_radius, pos[1] - center_radius))

    def _render_buff_effect(self, pos: Tuple[int, int], color: Tuple[int, int, int], progress: float):
        """Отрисовка эффекта баффа на кастере"""
        # Вращающиеся кольца
        num_rings = 2
        for ring in range(num_rings):
            ring_radius = 25 + ring * 15
            ring_alpha = int(150 * (1 - progress))
            ring_rotation = progress * math.pi * 4 + ring * math.pi

            # Рисуем сегментированное кольцо
            num_segments = 8
            for seg in range(num_segments):
                if seg % 2 == 0:
                    start_angle = ring_rotation + (seg / num_segments) * math.pi * 2
                    end_angle = ring_rotation + ((seg + 1) / num_segments) * math.pi * 2

                    # Рисуем дугу как серию точек
                    points = []
                    for t in range(5):
                        angle = start_angle + (end_angle - start_angle) * (t / 4)
                        px = pos[0] + math.cos(angle) * ring_radius
                        py = pos[1] + math.sin(angle) * ring_radius
                        points.append((int(px), int(py)))

                    if len(points) >= 2:
                        ring_surface = pygame.Surface((ring_radius * 3, ring_radius * 3), pygame.SRCALPHA)
                        offset = ring_radius * 1.5
                        adjusted_points = [(int(p[0] - pos[0] + offset), int(p[1] - pos[1] + offset)) for p in points]
                        pygame.draw.lines(ring_surface, (*color, ring_alpha), False, adjusted_points, 3)
                        self.screen.blit(ring_surface, (pos[0] - offset, pos[1] - offset))

        # Центральный свет
        glow_radius = int(20 + 10 * abs(math.sin(progress * math.pi * 4)))
        glow_alpha = int(100 * (1 - progress))
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*color, glow_alpha), (glow_radius, glow_radius), glow_radius)
        self.screen.blit(glow_surface, (pos[0] - glow_radius, pos[1] - glow_radius))

    def _render_melee_effect(self, color: Tuple[int, int, int], progress: float):
        """Отрисовка эффекта ближнего боя"""
        if not self.animation.caster or not self.animation.target:
            return

        caster_pos = self.get_screen_pos_for_cell(
            self.animation.caster.x,
            self.animation.caster.y
        )
        target_pos = self.get_screen_pos_for_cell(
            self.animation.target.x,
            self.animation.target.y
        )

        # Линия удара
        slash_progress = min(1.0, progress * 2)
        if slash_progress < 1.0:
            # Удар летит к цели
            current_x = caster_pos[0] + (target_pos[0] - caster_pos[0]) * slash_progress
            current_y = caster_pos[1] + (target_pos[1] - caster_pos[1]) * slash_progress

            # Рисуем след удара
            pygame.draw.line(self.screen, color, caster_pos, (int(current_x), int(current_y)), 4)

            # Свечение на конце
            glow_radius = 8
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, 200), (glow_radius, glow_radius), glow_radius)
            self.screen.blit(glow_surface, (int(current_x) - glow_radius, int(current_y) - glow_radius))
        else:
            # Эффект попадания
            impact_progress = (progress - 0.5) * 2
            if impact_progress > 0:
                impact_radius = int(20 * (1 - impact_progress))
                impact_alpha = int(200 * (1 - impact_progress))
                if impact_radius > 0:
                    impact_surface = pygame.Surface((impact_radius * 2, impact_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(impact_surface, (*color, impact_alpha), (impact_radius, impact_radius), impact_radius)
                    self.screen.blit(impact_surface, (target_pos[0] - impact_radius, target_pos[1] - impact_radius))

    def _render_side_panel(self):
        """Отрисовка боковой панели с информацией"""
        arena_width = self.ARENA_WIDTH * self.CELL_SIZE
        panel_x = self.arena_x + arena_width + 20
        panel_y = self.arena_y
        panel_width = self.side_panel_width
        panel_height = self.ARENA_HEIGHT * self.CELL_SIZE

        # Фон панели
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel"],
            (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel_border"],
            (panel_x, panel_y, panel_width, panel_height),
            2
        )

        current_y = panel_y + 10

        # Информация об игроке
        if self.player_unit:
            current_y = self._render_character_info(
                self.player_unit.character,
                panel_x + 10,
                current_y,
                panel_width - 20,
                "ИГРОК"
            )
            current_y += 20

        # Информация о выбранной цели
        if self.target_unit and self.target_unit != self.player_unit:
            current_y = self._render_character_info(
                self.target_unit.character,
                panel_x + 10,
                current_y,
                panel_width - 20,
                "ЦЕЛЬ"
            )
            current_y += 20

        # Выбранное умение
        if self.selected_skill:
            self._render_skill_info(self.selected_skill, panel_x + 10, current_y, panel_width - 20)

        # Кнопки действий
        self._render_action_buttons(panel_x, panel_y + panel_height - 70, panel_width)

    def _render_character_info(
        self,
        char: TestCharacter,
        x: int,
        y: int,
        width: int,
        title: str
    ) -> int:
        """Отрисовка информации о персонаже"""
        # Заголовок
        title_surface = self.font.render(title, True, (255, 215, 0))
        self.screen.blit(title_surface, (x, y))
        y += 22

        # Имя
        name_surface = self.font.render(char.name, True, self.COLORS["text"])
        self.screen.blit(name_surface, (x, y))
        y += 20

        # Уровень
        level_surface = self.font_small.render(f"Уровень: {char.level}", True, self.COLORS["text_dark"])
        self.screen.blit(level_surface, (x, y))
        y += 18

        # Ресурсы
        hp_text = f"HP: {char.health}/{char.max_health}"
        hp_surface = self.font_small.render(hp_text, True, self.COLORS["health_bar"])
        self.screen.blit(hp_surface, (x, y))
        y += 16

        mana_text = f"Мана: {char.mana}/{char.max_mana}"
        mana_surface = self.font_small.render(mana_text, True, self.COLORS["mana_bar"])
        self.screen.blit(mana_surface, (x, y))
        y += 16

        stamina_text = f"Вын.: {char.stamina}/{char.max_stamina}"
        stamina_surface = self.font_small.render(stamina_text, True, self.COLORS["stamina_bar"])
        self.screen.blit(stamina_surface, (x, y))
        y += 18

        # Статус-эффекты
        if char.status_effects:
            effects_text = "Эффекты: " + ", ".join([e.name for e in char.status_effects])
            effects_surface = self.font_small.render(effects_text, True, (200, 150, 100))
            self.screen.blit(effects_surface, (x, y))
            y += 16

        return y

    def _render_skill_info(self, skill: TestSkill, x: int, y: int, width: int):
        """Отрисовка информации об умении"""
        # Заголовок
        title_surface = self.font.render("УМЕНИЕ", True, (255, 215, 0))
        self.screen.blit(title_surface, (x, y))
        y += 22

        # Название
        name_surface = self.font.render(skill.name, True, self.COLORS["text"])
        self.screen.blit(name_surface, (x, y))
        y += 20

        # Описание (если есть)
        if skill.description:
            desc_surface = self.font_small.render(skill.description[:40], True, self.COLORS["text_dark"])
            self.screen.blit(desc_surface, (x, y))
            y += 16

        # Стоимость
        costs = []
        if skill.mana_cost:
            costs.append(f"Мана: {skill.mana_cost}")
        if skill.stamina_cost:
            costs.append(f"Вын.: {skill.stamina_cost}")
        if skill.cooldown:
            costs.append(f"КД: {skill.cooldown}")
        if costs:
            cost_text = " | ".join(costs)
            cost_surface = self.font_small.render(cost_text, True, self.COLORS["mana_bar"])
            self.screen.blit(cost_surface, (x, y))
            y += 16

        # Урон/лечение
        if skill.base_damage:
            damage_text = f"Урон: {skill.base_damage} ({skill.damage_type})"
            damage_surface = self.font_small.render(damage_text, True, (255, 100, 100))
            self.screen.blit(damage_surface, (x, y))
            y += 16

        if skill.base_healing:
            heal_text = f"Лечение: {skill.base_healing}"
            heal_surface = self.font_small.render(heal_text, True, (100, 255, 100))
            self.screen.blit(heal_surface, (x, y))

    def _render_action_buttons(self, panel_x: int, y: int, panel_width: int):
        """Отрисовка кнопок действий"""
        self.action_buttons.clear()

        button_width = (panel_width - 30) // 2
        button_height = 30

        buttons = [
            ("reset", "Сброс (R)"),
            ("next_turn", "Ход (Space)"),
        ]

        mouse_pos = pygame.mouse.get_pos()

        for i, (action_id, label) in enumerate(buttons):
            btn_x = panel_x + 10 + i * (button_width + 10)
            btn_rect = pygame.Rect(btn_x, y, button_width, button_height)

            # Подсветка при наведении
            color = self.COLORS["button_hover"] if btn_rect.collidepoint(mouse_pos) else self.COLORS["button"]

            pygame.draw.rect(self.screen, color, btn_rect)
            pygame.draw.rect(self.screen, self.COLORS["panel_border"], btn_rect, 2)

            label_surface = self.font_small.render(label, True, self.COLORS["text"])
            label_x = btn_x + (button_width - label_surface.get_width()) // 2
            label_y = y + (button_height - label_surface.get_height()) // 2
            self.screen.blit(label_surface, (label_x, label_y))

            self.action_buttons.append((btn_rect, action_id, label))

    def _render_skills_panel(self):
        """Отрисовка панели умений"""
        arena_height = self.ARENA_HEIGHT * self.CELL_SIZE
        panel_x = self.arena_x
        panel_y = self.arena_y + arena_height + 20
        panel_width = self.ARENA_WIDTH * self.CELL_SIZE
        panel_height = 120

        # Фон панели
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel"],
            (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel_border"],
            (panel_x, panel_y, panel_width, panel_height),
            2
        )

        # Заголовок
        title = self.font.render("УМЕНИЯ", True, (255, 215, 0))
        self.screen.blit(title, (panel_x + 10, panel_y + 8))

        # Кнопки умений
        self.skill_buttons.clear()
        slot_size = 48
        slot_spacing = 8
        start_x = panel_x + 10
        start_y = panel_y + 35

        mouse_pos = pygame.mouse.get_pos()
        skills = list(self.available_skills.values())

        for i, skill in enumerate(skills):
            slot_x = start_x + i * (slot_size + slot_spacing)
            slot_y = start_y

            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)

            # Определяем цвет фона
            can_use, _ = skill.can_use(self.player_unit.character) if self.player_unit else (False, "")

            if skill == self.selected_skill:
                bg_color = self.COLORS["button_active"]
            elif slot_rect.collidepoint(mouse_pos):
                bg_color = self.COLORS["button_hover"]
            elif can_use:
                bg_color = self.COLORS["button"]
            else:
                bg_color = (40, 40, 50)

            pygame.draw.rect(self.screen, bg_color, slot_rect)
            border_color = (255, 215, 0) if skill == self.selected_skill else self.COLORS["panel_border"]
            pygame.draw.rect(self.screen, border_color, slot_rect, 2)

            # Номер слота
            slot_num = self.font_small.render(str(i + 1), True, self.COLORS["text_dark"])
            self.screen.blit(slot_num, (slot_x + 4, slot_y + 4))

            # Иконка умения или первая буква
            if skill.skill_id in self.skill_icons:
                icon = self.skill_icons[skill.skill_id]
                icon_x = slot_x + (slot_size - icon.get_width()) // 2
                icon_y = slot_y + (slot_size - icon.get_height()) // 2
                self.screen.blit(icon, (icon_x, icon_y))
            else:
                # Fallback - первая буква названия
                skill_label = self.font.render(skill.name[0], True, self.COLORS["text"])
                label_x = slot_x + (slot_size - skill_label.get_width()) // 2
                label_y = slot_y + (slot_size - skill_label.get_height()) // 2
                self.screen.blit(skill_label, (label_x, label_y))

            # Перезарядка
            if skill.current_cooldown > 0:
                cd_text = self.font_small.render(str(skill.current_cooldown), True, (255, 100, 100))
                self.screen.blit(cd_text, (slot_x + slot_size - 12, slot_y + slot_size - 14))

            self.skill_buttons.append((slot_rect, skill))

            # Подпись под слотом
            skill_name = skill.name[:8] + ".." if len(skill.name) > 10 else skill.name
            name_surface = self.font_small.render(skill_name, True, self.COLORS["text_dark"])
            self.screen.blit(name_surface, (slot_x, slot_y + slot_size + 4))

    def _render_combat_log(self):
        """Отрисовка лога боя"""
        arena_width = self.ARENA_WIDTH * self.CELL_SIZE
        arena_height = self.ARENA_HEIGHT * self.CELL_SIZE
        panel_x = self.arena_x + arena_width + 20
        panel_y = self.arena_y + arena_height + 20
        panel_width = self.side_panel_width
        panel_height = 120

        # Фон
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel"],
            (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            self.screen,
            self.COLORS["panel_border"],
            (panel_x, panel_y, panel_width, panel_height),
            2
        )

        # Заголовок
        title = self.font.render("ЖУРНАЛ", True, (150, 200, 255))
        self.screen.blit(title, (panel_x + 10, panel_y + 5))

        # Сообщения
        log_y = panel_y + 28
        visible_logs = self.combat_log[-7:]  # Последние 7 сообщений

        for msg in visible_logs:
            # Обрезаем длинные сообщения
            display_msg = msg[:45] + ".." if len(msg) > 47 else msg
            msg_surface = self.font_small.render(display_msg, True, self.COLORS["text_dark"])
            self.screen.blit(msg_surface, (panel_x + 10, log_y))
            log_y += 14

    def run(self):
        """Главный цикл арены"""
        clock = pygame.time.Clock()

        while self.running:
            self.handle_events()
            self.update_animation()
            self.render()
            clock.tick(60)

        pygame.quit()


def main():
    """Точка входа для тестовой арены"""
    arena = TestArena()
    arena.setup_default_arena()
    arena.run()


if __name__ == "__main__":
    main()
