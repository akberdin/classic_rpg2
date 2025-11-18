"""
Менеджер спрайтов для загрузки и управления графикой
"""
import pygame
import json
import os


class SpriteManager:
    """Класс для загрузки и управления спрайтами"""

    def __init__(self, config_path="sprites_config.json", tile_size=32):
        """
        Инициализация менеджера спрайтов

        Args:
            config_path: Путь к конфигурационному файлу
            tile_size: Размер клетки в пикселях
        """
        self.tile_size = tile_size
        self.config = {}
        self.sprites = {}
        self.sprite_size = 64  # Размер исходных спрайтов

        # Загружаем конфигурацию
        self.load_config(config_path)

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

        # Загружаем спрайты NPC
        for npc_type, sprite_path in self.config.get('npcs', {}).items():
            self.load_sprite(npc_type, sprite_path, 'npc')

        # Загружаем спрайты локаций
        for location_type, sprite_path in self.config.get('locations', {}).items():
            self.load_sprite(location_type, sprite_path, 'location')

        # Загружаем спрайты биомов
        for biome_type, sprite_path in self.config.get('biomes', {}).items():
            self.load_sprite(biome_type, sprite_path, 'biome')

        print(f"Загружено спрайтов: {len(self.sprites)}")

    def load_sprite(self, sprite_type, sprite_path, category):
        """
        Загрузка одного спрайта

        Args:
            sprite_type: Тип спрайта (guard, city, forest и т.д.)
            sprite_path: Путь к файлу спрайта
            category: Категория (npc, location, biome)
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
            category: Категория (npc, location, biome)

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
            category: Категория (npc, location, biome)

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

    def render_location(self, screen, location_type, x, y, default_renderer):
        """
        Отрисовка локации (спрайт или цвет)

        Args:
            screen: Pygame экран
            location_type: Тип локации
            x: X координата на экране
            y: Y координата на экране
            default_renderer: Функция для отрисовки по умолчанию
        """
        sprite = self.get_sprite(location_type, 'location')
        if sprite:
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
