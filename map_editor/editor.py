"""Main map editor class."""

import pygame
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from .utils.helpers import load_config
from .tools.generator import MapGenerator, GeneratedMap, GeneratorParams, MapLocation
from .tools.brush import BiomeBrush, BrushSettings, BrushMode
from .tools.objects import ObjectPlacer, PlacementMode
from .ui.toolbar import Toolbar, ToolType
from .ui.sidebar import Sidebar
from .ui.dialogs import (
    Dialog, GeneratorDialog, ObjectDialog, SaveDialog, LoadDialog
)


class MapEditor:
    """Main map editor application."""

    def __init__(self):
        # Load configuration
        self.config = load_config()

        # Window settings
        window_config = self.config.get('window', {})
        self.width = window_config.get('width', 1400)
        self.height = window_config.get('height', 900)
        self.title = window_config.get('title', 'Classic RPG - Map Editor')
        self.fps = window_config.get('fps', 60)

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.font = pygame.font.SysFont('Arial', 12)
        self.font_large = pygame.font.SysFont('Arial', 14, bold=True)

        # Colors from config
        self.biome_colors = {}
        for biome, data in self.config.get('biomes', {}).items():
            self.biome_colors[biome] = tuple(data.get('color', [128, 128, 128]))

        self.location_colors = {}
        for loc_type, data in self.config.get('locations', {}).items():
            self.location_colors[loc_type] = tuple(data.get('color', [255, 255, 255]))

        # Map settings
        map_config = self.config.get('map', {})
        self.tile_size = map_config.get('tile_size', 4)
        self.min_tile_size = map_config.get('min_tile_size', 2)
        self.max_tile_size = map_config.get('max_tile_size', 20)

        # UI settings
        ui_config = self.config.get('ui', {})
        self.sidebar_width = ui_config.get('sidebar_width', 280)
        self.toolbar_height = ui_config.get('toolbar_height', 50)
        self.bg_color = tuple(ui_config.get('panel_color', [45, 45, 48]))

        # Tools
        self.generator = MapGenerator()
        self.brush = BiomeBrush()
        self.object_placer = ObjectPlacer()

        # Current map
        self.current_map: Optional[GeneratedMap] = None
        self.current_file: Optional[str] = None
        self.has_unsaved_changes = False

        # View state
        self.camera_x = 0
        self.camera_y = 0
        self.dragging = False
        self.drag_start = (0, 0)
        self.show_grid = False
        self.show_locations = True

        # Current tool
        self.current_tool = ToolType.SELECT

        # UI Components
        self.toolbar = Toolbar(self.width, self.toolbar_height, self.config)
        self.sidebar = Sidebar(
            self.width - self.sidebar_width,
            self.toolbar_height,
            self.sidebar_width,
            self.height - self.toolbar_height,
            self.config
        )

        # Dialogs
        self.generator_dialog = GeneratorDialog()
        self.active_dialog: Optional[Dialog] = None

        # Setup callbacks
        self._setup_callbacks()

        # Mouse state
        self.mouse_down = False
        self.last_brush_pos: Optional[Tuple[int, int]] = None

        # Map surface cache
        self.map_surface: Optional[pygame.Surface] = None
        self.map_surface_dirty = True

        # Status bar message
        self.status_message = "Готов"
        self.status_time = 0

    def _setup_callbacks(self) -> None:
        """Setup UI callbacks."""
        # Toolbar callbacks
        self.toolbar.on_tool_change = self._on_tool_change
        self.toolbar.on_action = self._on_toolbar_action

        # Sidebar callbacks
        self.sidebar.on_biome_select = self._on_biome_select
        self.sidebar.on_location_select = self._on_location_select
        self.sidebar.on_brush_change = self._on_brush_change

        # Dialog callbacks
        self.generator_dialog.on_close = self._on_generator_dialog_close

    def _on_tool_change(self, tool: ToolType) -> None:
        """Handle tool change."""
        self.current_tool = tool
        self.sidebar.set_tool(tool)

        # Update object placer mode
        if tool == ToolType.OBJECT:
            self.object_placer.set_mode(PlacementMode.SINGLE)
        elif tool == ToolType.ERASER:
            self.object_placer.set_mode(PlacementMode.DELETE)
        elif tool == ToolType.MOVE:
            self.object_placer.set_mode(PlacementMode.MOVE)

    def _on_toolbar_action(self, action: str) -> None:
        """Handle toolbar action."""
        if action == "new":
            self._new_map()
        elif action == "open":
            self._open_map()
        elif action == "save":
            self._save_map()
        elif action == "save_as":
            self._save_map_as()
        elif action == "generate":
            self._show_generator_dialog()
        elif action == "regenerate":
            self._regenerate_map()
        elif action == "gen_settings":
            self._show_generator_dialog()
        elif action == "zoom_in":
            self._zoom_in()
        elif action == "zoom_out":
            self._zoom_out()
        elif action == "fit_view":
            self._fit_view()
        elif action == "toggle_grid":
            self.show_grid = not self.show_grid

    def _on_biome_select(self, biome: str) -> None:
        """Handle biome selection."""
        self.brush.settings.biome = biome
        self.sidebar.selected_biome = biome

    def _on_location_select(self, location_type: str) -> None:
        """Handle location type selection."""
        self.object_placer.set_location_type(location_type)
        self.sidebar.selected_location = location_type

    def _on_brush_change(self, settings: BrushSettings) -> None:
        """Handle brush settings change."""
        self.brush.settings = settings

    def _on_generator_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle generator dialog close."""
        self.active_dialog = None
        if action == "ok":
            params = self.generator_dialog.get_params()
            self._generate_map(params)

    def _new_map(self) -> None:
        """Create a new empty map."""
        params = GeneratorParams()
        self._generate_map(params)
        self.current_file = None
        self.has_unsaved_changes = True
        self._set_status("Создана новая карта")

    def _open_map(self) -> None:
        """Open a map file."""
        # Use game's config directory as default
        default_dir = Path(__file__).parent.parent / "game" / "config"
        if not default_dir.exists():
            default_dir = Path.home()

        dialog = LoadDialog(str(default_dir))
        dialog.on_close = self._on_load_dialog_close
        self.active_dialog = dialog
        dialog.show(self.width, self.height)

    def _on_load_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle load dialog close."""
        self.active_dialog = None
        if action == "ok" and 'filename' in data:
            self._load_map(data['filename'])

    def _load_map(self, filepath: str) -> None:
        """Load a map from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.current_map = GeneratedMap.from_dict(data)
            self.current_file = filepath
            self.has_unsaved_changes = False
            self.map_surface_dirty = True

            # Sync object placer names
            self.object_placer.sync_used_names(self.current_map)

            self._fit_view()
            self._set_status(f"Загружено: {Path(filepath).name}")

        except Exception as e:
            self._set_status(f"Ошибка загрузки: {e}")

    def _save_map(self) -> None:
        """Save the current map."""
        if not self.current_map:
            return

        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._save_map_as()

    def _save_map_as(self) -> None:
        """Save the map to a new file."""
        if not self.current_map:
            return

        # Default to game config directory
        default_dir = Path(__file__).parent.parent / "game" / "config"
        default_file = default_dir / "map1.json"

        self._save_to_file(str(default_file))

    def _save_to_file(self, filepath: str) -> None:
        """Save map to specified file."""
        if not self.current_map:
            return

        try:
            data = self.current_map.to_dict()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.current_file = filepath
            self.has_unsaved_changes = False
            self._set_status(f"Сохранено: {Path(filepath).name}")

        except Exception as e:
            self._set_status(f"Ошибка сохранения: {e}")

    def _show_generator_dialog(self) -> None:
        """Show the generator settings dialog."""
        self.generator_dialog = GeneratorDialog(self.generator.params)
        self.generator_dialog.on_close = self._on_generator_dialog_close
        self.active_dialog = self.generator_dialog
        self.generator_dialog.show(self.width, self.height)

    def _generate_map(self, params: GeneratorParams) -> None:
        """Generate a new map with given parameters."""
        self._set_status("Генерация карты...")
        pygame.display.flip()

        self.current_map = self.generator.generate(params)
        self.map_surface_dirty = True
        self.has_unsaved_changes = True

        # Sync object placer
        self.object_placer.sync_used_names(self.current_map)

        self._fit_view()
        self._set_status(f"Карта сгенерирована (seed: {self.current_map.seed})")

    def _regenerate_map(self) -> None:
        """Regenerate map with new seed."""
        if not self.current_map:
            self._generate_map(GeneratorParams())
            return

        # Keep locations, regenerate terrain
        self.generator.params.seed = None
        self.current_map = self.generator.regenerate_terrain_only(
            self.current_map,
            self.generator.params
        )
        self.map_surface_dirty = True
        self.has_unsaved_changes = True
        self._set_status(f"Карта перегенерирована (seed: {self.current_map.seed})")

    def _zoom_in(self) -> None:
        """Zoom in."""
        if self.tile_size < self.max_tile_size:
            self.tile_size = min(self.tile_size + 1, self.max_tile_size)
            self.map_surface_dirty = True

    def _zoom_out(self) -> None:
        """Zoom out."""
        if self.tile_size > self.min_tile_size:
            self.tile_size = max(self.tile_size - 1, self.min_tile_size)
            self.map_surface_dirty = True

    def _fit_view(self) -> None:
        """Fit map to view."""
        if not self.current_map:
            return

        view_width = self.width - self.sidebar_width
        view_height = self.height - self.toolbar_height

        # Calculate tile size to fit
        tile_w = view_width // self.current_map.width
        tile_h = view_height // self.current_map.height
        self.tile_size = max(self.min_tile_size, min(tile_w, tile_h, self.max_tile_size))

        # Center the map
        map_width = self.current_map.width * self.tile_size
        map_height = self.current_map.height * self.tile_size

        self.camera_x = (view_width - map_width) // 2
        self.camera_y = (view_height - map_height) // 2

        self.map_surface_dirty = True

    def _set_status(self, message: str) -> None:
        """Set status bar message."""
        self.status_message = message
        self.status_time = pygame.time.get_ticks()

    def _screen_to_tile(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to tile coordinates."""
        map_x = screen_x - self.camera_x
        map_y = screen_y - self.toolbar_height - self.camera_y

        tile_x = map_x // self.tile_size
        tile_y = map_y // self.tile_size

        return tile_x, tile_y

    def _tile_to_screen(self, tile_x: int, tile_y: int) -> Tuple[int, int]:
        """Convert tile coordinates to screen coordinates."""
        screen_x = tile_x * self.tile_size + self.camera_x
        screen_y = tile_y * self.tile_size + self.camera_y + self.toolbar_height
        return screen_x, screen_y

    def handle_events(self) -> None:
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                continue

            # Handle active dialog first
            if self.active_dialog and self.active_dialog.visible:
                self.active_dialog.handle_event(event)
                continue

            # UI components
            if self.toolbar.handle_event(event):
                continue

            if self.sidebar.handle_event(event):
                continue

            # Map interaction
            self._handle_map_event(event)

    def _handle_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

        # Update UI components
        self.toolbar.resize(width)
        self.sidebar.resize(
            width - self.sidebar_width,
            self.toolbar_height,
            self.sidebar_width,
            height - self.toolbar_height
        )

    def _handle_map_event(self, event: pygame.event.Event) -> None:
        """Handle map-related events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_left_click(event.pos)
            elif event.button == 2:  # Middle click - start dragging
                self.dragging = True
                self.drag_start = event.pos
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
            elif event.button == 4:  # Scroll up
                self._zoom_in()
            elif event.button == 5:  # Scroll down
                self._zoom_out()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_down = False
                self.last_brush_pos = None
            elif event.button == 2:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                self.camera_x += dx
                self.camera_y += dy
                self.drag_start = event.pos
            elif self.mouse_down:
                self._handle_mouse_drag(event.pos)

    def _handle_left_click(self, pos: Tuple[int, int]) -> None:
        """Handle left mouse click on map."""
        if not self.current_map:
            return

        # Check if click is in map area
        if pos[0] >= self.width - self.sidebar_width:
            return
        if pos[1] < self.toolbar_height:
            return

        tile_x, tile_y = self._screen_to_tile(pos[0], pos[1])

        if not (0 <= tile_x < self.current_map.width and
                0 <= tile_y < self.current_map.height):
            return

        self.mouse_down = True
        self.last_brush_pos = (tile_x, tile_y)

        if self.current_tool == ToolType.BRUSH:
            self.brush.apply(self.current_map, tile_x, tile_y)
            self.map_surface_dirty = True
            self.has_unsaved_changes = True

        elif self.current_tool == ToolType.FILL:
            self.brush.fill_area(self.current_map, tile_x, tile_y)
            self.map_surface_dirty = True
            self.has_unsaved_changes = True

        elif self.current_tool == ToolType.OBJECT:
            result = self.object_placer.place_location(self.current_map, tile_x, tile_y)
            self._set_status(result.message)
            if result.success:
                self.has_unsaved_changes = True

        elif self.current_tool == ToolType.ERASER:
            result = self.object_placer.delete_location(self.current_map, tile_x, tile_y)
            self._set_status(result.message)
            if result.success:
                self.has_unsaved_changes = True

        elif self.current_tool == ToolType.SELECT:
            location = self.object_placer.select_location(self.current_map, tile_x, tile_y)
            if location:
                info = self.object_placer.get_location_info(location)
                info['is_starting'] = (location == self.current_map.starting_village)
                self.sidebar.set_location_info(info)
            else:
                self.sidebar.set_location_info(None)

        elif self.current_tool == ToolType.MOVE:
            result = self.object_placer.place_location(self.current_map, tile_x, tile_y)
            self._set_status(result.message)
            if result.success:
                self.has_unsaved_changes = True

    def _handle_right_click(self, pos: Tuple[int, int]) -> None:
        """Handle right mouse click."""
        if not self.current_map:
            return

        tile_x, tile_y = self._screen_to_tile(pos[0], pos[1])

        if not (0 <= tile_x < self.current_map.width and
                0 <= tile_y < self.current_map.height):
            return

        # Show location info on right click
        location = self.current_map.get_location_at(tile_x, tile_y)
        if location:
            info = self.object_placer.get_location_info(location)
            info['is_starting'] = (location == self.current_map.starting_village)
            self.sidebar.set_location_info(info)

    def _handle_mouse_drag(self, pos: Tuple[int, int]) -> None:
        """Handle mouse drag for painting."""
        if not self.current_map:
            return

        if self.current_tool not in [ToolType.BRUSH]:
            return

        tile_x, tile_y = self._screen_to_tile(pos[0], pos[1])

        if not (0 <= tile_x < self.current_map.width and
                0 <= tile_y < self.current_map.height):
            return

        if self.last_brush_pos and (tile_x, tile_y) != self.last_brush_pos:
            # Draw line from last position
            self.brush.line_to(
                self.current_map,
                self.last_brush_pos[0], self.last_brush_pos[1],
                tile_x, tile_y
            )
            self.map_surface_dirty = True
            self.has_unsaved_changes = True

        self.last_brush_pos = (tile_x, tile_y)

    def update(self) -> None:
        """Update game state."""
        pass  # Most updates happen in event handling

    def _render_map_surface(self) -> None:
        """Render map to cached surface."""
        if not self.current_map:
            return

        width = self.current_map.width * self.tile_size
        height = self.current_map.height * self.tile_size

        self.map_surface = pygame.Surface((width, height))

        # Draw biomes
        for y in range(self.current_map.height):
            for x in range(self.current_map.width):
                biome = self.current_map.get_biome(x, y)
                color = self.biome_colors.get(biome, (128, 128, 128))

                rect = pygame.Rect(
                    x * self.tile_size,
                    y * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )
                pygame.draw.rect(self.map_surface, color, rect)

        # Draw grid if enabled
        if self.show_grid and self.tile_size >= 4:
            grid_color = (50, 50, 50)
            for x in range(0, width, self.tile_size):
                pygame.draw.line(self.map_surface, grid_color, (x, 0), (x, height))
            for y in range(0, height, self.tile_size):
                pygame.draw.line(self.map_surface, grid_color, (0, y), (width, y))

        self.map_surface_dirty = False

    def render(self) -> None:
        """Render the editor."""
        # Background
        self.screen.fill(self.bg_color)

        # Render map
        if self.current_map:
            if self.map_surface_dirty or self.map_surface is None:
                self._render_map_surface()

            if self.map_surface:
                # Draw map surface
                self.screen.blit(
                    self.map_surface,
                    (self.camera_x, self.camera_y + self.toolbar_height)
                )

            # Draw locations on top
            if self.show_locations:
                self._render_locations()

            # Draw brush preview
            if self.current_tool == ToolType.BRUSH:
                self._render_brush_preview()

        # Draw "no map" message if no map loaded
        if not self.current_map:
            text = self.font_large.render(
                "Нажмите F5 для генерации карты или Ctrl+O для открытия",
                True, (150, 150, 150)
            )
            text_rect = text.get_rect(center=(
                (self.width - self.sidebar_width) // 2,
                (self.height + self.toolbar_height) // 2
            ))
            self.screen.blit(text, text_rect)

        # Draw UI components
        self.toolbar.draw(self.screen)
        self.sidebar.draw(self.screen)

        # Draw status bar
        self._render_status_bar()

        # Draw active dialog
        if self.active_dialog and self.active_dialog.visible:
            self.active_dialog.draw(self.screen)

        pygame.display.flip()

    def _render_locations(self) -> None:
        """Render location markers."""
        if not self.current_map:
            return

        for location in self.current_map.locations:
            screen_x, screen_y = self._tile_to_screen(location.x, location.y)

            # Check if visible
            if screen_x < -self.tile_size or screen_x > self.width:
                continue
            if screen_y < self.toolbar_height or screen_y > self.height:
                continue

            # Location marker
            color = self.location_colors.get(location.location_type, (255, 255, 255))

            # Draw marker
            marker_size = max(6, self.tile_size)
            center = (screen_x + self.tile_size // 2, screen_y + self.tile_size // 2)

            # Outer circle
            pygame.draw.circle(self.screen, (0, 0, 0), center, marker_size // 2 + 2)
            pygame.draw.circle(self.screen, color, center, marker_size // 2)

            # Starting village indicator
            if location == self.current_map.starting_village:
                pygame.draw.circle(self.screen, (255, 255, 255), center, marker_size // 2, 2)

            # Draw name if zoomed in enough
            if self.tile_size >= 6:
                name_surface = self.font.render(location.name, True, (255, 255, 255))
                name_bg = pygame.Surface(
                    (name_surface.get_width() + 4, name_surface.get_height() + 2),
                    pygame.SRCALPHA
                )
                name_bg.fill((0, 0, 0, 180))
                self.screen.blit(name_bg, (screen_x, screen_y - 16))
                self.screen.blit(name_surface, (screen_x + 2, screen_y - 15))

    def _render_brush_preview(self) -> None:
        """Render brush preview at mouse position."""
        mouse_pos = pygame.mouse.get_pos()

        # Check if in map area
        if mouse_pos[0] >= self.width - self.sidebar_width:
            return
        if mouse_pos[1] < self.toolbar_height:
            return

        tile_x, tile_y = self._screen_to_tile(mouse_pos[0], mouse_pos[1])

        if not self.current_map:
            return

        if not (0 <= tile_x < self.current_map.width and
                0 <= tile_y < self.current_map.height):
            return

        # Get brush area
        area = self.brush.get_brush_area(
            tile_x, tile_y,
            self.current_map.width, self.current_map.height
        )

        # Draw preview
        preview_color = (*self.biome_colors.get(self.brush.settings.biome, (128, 128, 128)), 100)
        preview_surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        preview_surface.fill(preview_color)

        for x, y in area:
            screen_x, screen_y = self._tile_to_screen(x, y)
            self.screen.blit(preview_surface, (screen_x, screen_y))

    def _render_status_bar(self) -> None:
        """Render status bar at bottom."""
        bar_height = 24
        bar_y = self.height - bar_height

        # Background
        pygame.draw.rect(
            self.screen,
            (30, 30, 32),
            (0, bar_y, self.width - self.sidebar_width, bar_height)
        )

        # Status message
        text_surface = self.font.render(self.status_message, True, (200, 200, 200))
        self.screen.blit(text_surface, (8, bar_y + 5))

        # Map info
        if self.current_map:
            mouse_pos = pygame.mouse.get_pos()
            tile_x, tile_y = self._screen_to_tile(mouse_pos[0], mouse_pos[1])

            if (0 <= tile_x < self.current_map.width and
                    0 <= tile_y < self.current_map.height):
                biome = self.current_map.get_biome(tile_x, tile_y)
                info_text = f"X: {tile_x}  Y: {tile_y}  Биом: {biome}  Масштаб: {self.tile_size}x"
            else:
                info_text = f"Масштаб: {self.tile_size}x"

            info_surface = self.font.render(info_text, True, (150, 150, 150))
            self.screen.blit(
                info_surface,
                (self.width - self.sidebar_width - info_surface.get_width() - 8, bar_y + 5)
            )

    def run(self) -> None:
        """Main game loop."""
        # Generate initial map
        self._generate_map(GeneratorParams())

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)

        pygame.quit()


def main():
    """Entry point for the map editor."""
    editor = MapEditor()
    editor.run()


if __name__ == "__main__":
    main()
