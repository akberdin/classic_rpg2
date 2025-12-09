"""
Менеджер спрайтов для загрузки и управления графикой
"""
import pygame
import json
import os


class SpriteManager:
    """Класс для загрузки и управления спрайтами"""

    # Путь к единому конфигу ассетов
    DEFAULT_CONFIG_PATH = "game/config/assets_config.json"

    def __init__(self, config_path=None, tile_size=32):
        """
        Инициализация менеджера спрайтов

        Args:
            config_path: Путь к конфигурационному файлу (по умолчанию game/config/assets_config.json)
            tile_size: Размер клетки в пикселях
        """
        self.tile_size = tile_size
        self.config = {}
        self.sprites = {}
        self.sprite_size = 64  # Размер исходных спрайтов

        # Загружаем конфигурацию
        actual_config_path = config_path if config_path else self.DEFAULT_CONFIG_PATH
        self.load_config(actual_config_path)

        # Загружаем спрайты
        self.load_sprites()

    def load_config(self, config_path):
        """
        Загрузка конфигурации спрайтов

        Args:
            config_path: Путь к конфигурационному файлу
        """
        if not os.path.exists(config_path):
            print(f"Конфигурационный файл спрайтов не найден: {config_path}")
            print("Будут использоваться геометрические фигуры")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.sprite_size = self.config.get('sprite_size', 64)
                print(f"Конфигурация спрайтов загружена: {config_path}")
        except Exception as e:
            print(f"Ошибка загрузки конфигурации спрайтов: {e}")
            print("Будут использоваться геометрические фигуры")

    def load_sprites(self):
        """Загрузка всех спрайтов из конфигурации"""
        if not self.config:
            return

        # Загружаем спрайты NPC (с поддержкой вложенной структуры)
        for npc_type, sprite_data in self.config.get('npcs', {}).items():
            if isinstance(sprite_data, dict):
                # Новая вложенная структура: {default: ..., novice: ..., regular: ...}
                for rank, sprite_path in sprite_data.items():
                    if rank == 'default':
                        self.load_sprite(npc_type, sprite_path, 'npc')
                    else:
                        self.load_sprite(f"{npc_type}_{rank}", sprite_path, 'npc')
            else:
                # Старая плоская структура: строка с путем
                self.load_sprite(npc_type, sprite_data, 'npc')

        # Загружаем спрайты локаций
        for location_type, sprite_path in self.config.get('locations', {}).items():
            self.load_sprite(location_type, sprite_path, 'location')

        # Загружаем спрайты биомов
        for biome_type, sprite_path in self.config.get('biomes', {}).items():
            self.load_sprite(biome_type, sprite_path, 'biome')

        # Загружаем спрайты умений
        for skill_id, sprite_path in self.config.get('skills', {}).items():
            self.load_skill_sprite(skill_id, sprite_path)

        # Загружаем спрайты зелий
        for potion_id, sprite_path in self.config.get('potions', {}).items():
            self.load_sprite(potion_id, sprite_path, 'potion')

        print(f"Загружено спрайтов: {len(self.sprites)}")

    def load_sprite(self, sprite_type, sprite_path, category):
        """
        Загрузка одного спрайта

        Args:
            sprite_type: Тип спрайта (guard, city, forest и т.д.)
            sprite_path: Путь к файлу спрайта
            category: Категория (npc, location, biome, potion)
        """
        if not os.path.exists(sprite_path):
            # Спрайт не найден, будет использоваться fallback
            return

        try:
            # Загружаем изображение
            original_sprite = pygame.image.load(sprite_path).convert_alpha()

            # Масштабируем под размер клетки
            scaled_sprite = pygame.transform.scale(original_sprite, (self.tile_size, self.tile_size))

            # Сохраняем в словарь
            key = f"{category}_{sprite_type}"
            self.sprites[key] = scaled_sprite

        except Exception as e:
            print(f"Ошибка загрузки спрайта {sprite_path}: {e}")

    def get_sprite(self, sprite_type, category):
        """
        Получить спрайт по типу и категории

        Args:
            sprite_type: Тип спрайта
            category: Категория (npc, location, biome, potion)

        Returns:
            pygame.Surface или None если спрайт не найден
        """
        key = f"{category}_{sprite_type}"
        return self.sprites.get(key)

    def get_rank_suffix(self, level):
        """
        Получить суффикс ранга на основе уровня

        Args:
            level: Уровень персонажа

        Returns:
            str: Суффикс ранга (_novice, _regular, _veteran, _expert)
        """
        if level <= 10:
            return "_novice"
        elif level <= 20:
            return "_regular"
        elif level <= 30:
            return "_veteran"
        else:
            return "_expert"

    def get_npc_sprite_with_rank(self, npc_type, level):
        """
        Получить спрайт NPC с учетом ранга

        Args:
            npc_type: Тип NPC (guard, bandit, etc.)
            level: Уровень NPC

        Returns:
            pygame.Surface или None если спрайт не найден
        """
        # Сначала пробуем получить спрайт с рангом
        rank_suffix = self.get_rank_suffix(level)
        ranked_key = f"npc_{npc_type}{rank_suffix}"

        if ranked_key in self.sprites:
            return self.sprites[ranked_key]

        # Если не найден, используем базовый спрайт
        base_key = f"npc_{npc_type}"
        return self.sprites.get(base_key)

    def has_sprite(self, sprite_type, category):
        """
        Проверить, есть ли спрайт

        Args:
            sprite_type: Тип спрайта
            category: Категория (npc, location, biome, potion)

        Returns:
            bool: True если спрайт загружен
        """
        key = f"{category}_{sprite_type}"
        return key in self.sprites

    def render_npc(self, screen, npc_type, x, y, default_renderer, level=None):
        """
        Отрисовка NPC (спрайт или геометрическая фигура)

        Args:
            screen: Pygame экран
            npc_type: Тип NPC
            x: X координата на экране
            y: Y координата на экране
            default_renderer: Функция для отрисовки по умолчанию
            level: Уровень NPC для выбора спрайта по рангу (опционально)
        """
        sprite = None

        # Если указан уровень, пробуем получить спрайт с рангом
        if level is not None:
            sprite = self.get_npc_sprite_with_rank(npc_type, level)
        else:
            sprite = self.get_sprite(npc_type, 'npc')

        if sprite:
            screen.blit(sprite, (x, y))
        else:
            # Используем геометрическую фигуру
            default_renderer()

    def render_location(self, screen, location_type, x, y, default_renderer, darken=False):
        """
        Отрисовка локации (спрайт или цвет)

        Args:
            screen: Pygame экран
            location_type: Тип локации
            x: X координата на экране
            y: Y координата на экране
            default_renderer: Функция для отрисовки по умолчанию
            darken: Затемнить спрайт (для тумана войны)
        """
        sprite = self.get_sprite(location_type, 'location')
        if sprite:
            if darken:
                # Создаем затемненную версию спрайта
                darkened_sprite = sprite.copy()
                darkened_sprite.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(darkened_sprite, (x, y))
            else:
                screen.blit(sprite, (x, y))
        else:
            # Используем цветной прямоугольник
            default_renderer()

    def render_biome(self, screen, biome_type, x, y, default_renderer):
        """
        Отрисовка биома (спрайт или цвет)

        Args:
            screen: Pygame экран
            biome_type: Тип биома
            x: X координата на экране
            y: Y координата на экране
            default_renderer: Функция для отрисовки по умолчанию
        """
        sprite = self.get_sprite(biome_type, 'biome')
        if sprite:
            screen.blit(sprite, (x, y))
        else:
            # Используем цветной прямоугольник
            default_renderer()

    def load_skill_sprite(self, skill_id, sprite_path, target_size=48):
        """
        Загрузка спрайта умения

        Args:
            skill_id: ID умения (basic_attack, fireball, etc.)
            sprite_path: Путь к файлу спрайта
            target_size: Целевой размер спрайта для иконок (по умолчанию 48)
        """
        if not os.path.exists(sprite_path):
            # Спрайт не найден, будет использоваться fallback
            return

        try:
            # Загружаем изображение
            original_sprite = pygame.image.load(sprite_path).convert_alpha()

            # Сохраняем оригинальный спрайт (64x64)
            key = f"skill_{skill_id}"
            self.sprites[key] = original_sprite

            # Также сохраняем масштабированную версию для иконок (48x48)
            scaled_sprite = pygame.transform.scale(original_sprite, (target_size, target_size))
            self.sprites[f"{key}_icon"] = scaled_sprite

        except Exception as e:
            print(f"Ошибка загрузки спрайта умения {sprite_path}: {e}")

    def get_skill_sprite(self, skill_id, icon_size=None):
        """
        Получить спрайт умения

        Args:
            skill_id: ID умения
            icon_size: Размер иконки (если нужен масштабированный вариант)

        Returns:
            pygame.Surface или None если спрайт не найден
        """
        if icon_size:
            # Пробуем получить готовую иконку
            icon_key = f"skill_{skill_id}_icon"
            if icon_key in self.sprites:
                sprite = self.sprites[icon_key]
                # Если размер не совпадает, масштабируем
                if sprite.get_width() != icon_size:
                    return pygame.transform.scale(sprite, (icon_size, icon_size))
                return sprite

        # Возвращаем оригинальный спрайт
        key = f"skill_{skill_id}"
        sprite = self.sprites.get(key)

        # Если нужен конкретный размер, масштабируем
        if sprite and icon_size:
            return pygame.transform.scale(sprite, (icon_size, icon_size))

        return sprite

    def has_skill_sprite(self, skill_id):
        """
        Проверить, есть ли спрайт для умения

        Args:
            skill_id: ID умения

        Returns:
            bool: True если спрайт загружен
        """
        key = f"skill_{skill_id}"
        return key in self.sprites

    def render_skill_icon(self, screen, skill_id, x, y, size, fallback_text=None):
        """
        Отрисовка иконки умения (спрайт или fallback текст)

        Args:
            screen: Pygame экран
            skill_id: ID умения
            x: X координата
            y: Y координата
            size: Размер иконки
            fallback_text: Текст для отображения если спрайт не найден (обычно первая буква)

        Returns:
            bool: True если спрайт был отрисован, False если использован fallback
        """
        sprite = self.get_skill_sprite(skill_id, icon_size=size)
        if sprite:
            screen.blit(sprite, (x, y))
            return True
        elif fallback_text:
            # Fallback - рисуем текст (первую букву названия)
            icon_font = pygame.font.Font(None, int(size * 0.7))
            icon_text = icon_font.render(fallback_text, True, (255, 255, 255))
            icon_rect = icon_text.get_rect()
            icon_rect.center = (x + size // 2, y + size // 2)
            screen.blit(icon_text, icon_rect)
        return False

    def get_potion_sprite(self, potion_id, icon_size=None):
        """
        Получить спрайт зелья

        Args:
            potion_id: ID зелья (minor_health_potion, mana_potion, etc.)
            icon_size: Размер иконки (если нужен масштабированный вариант)

        Returns:
            pygame.Surface или None если спрайт не найден
        """
        sprite = self.get_sprite(potion_id, 'potion')

        # Если нужен конкретный размер, масштабируем
        if sprite and icon_size:
            return pygame.transform.scale(sprite, (icon_size, icon_size))

        return sprite

    def has_potion_sprite(self, potion_id):
        """
        Проверить, есть ли спрайт для зелья

        Args:
            potion_id: ID зелья

        Returns:
            bool: True если спрайт загружен
        """
        return self.has_sprite(potion_id, 'potion')

    def update_tile_size(self, new_tile_size):
        """
        Обновить размер клетки и перезагрузить спрайты

        Args:
            new_tile_size: Новый размер клетки
        """
        if self.tile_size != new_tile_size:
            self.tile_size = new_tile_size
            self.sprites.clear()
            self.load_sprites()
