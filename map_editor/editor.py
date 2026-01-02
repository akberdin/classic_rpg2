"""Main map editor class."""

import pygame
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from .utils.helpers import load_config
from .tools.generator import (
    MapGenerator, GeneratedMap, GeneratorParams, MapLocation, MapConfig, Guard,
    LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER,
    Merchant, MerchantWaypoint, MERCHANT_RANKS
)
from .tools.brush import BiomeBrush, BrushSettings, BrushMode
from .tools.objects import ObjectPlacer, PlacementMode
from .ui.toolbar import Toolbar, ToolType
from .ui.sidebar import Sidebar
from .ui.dialogs import (
    Dialog, GeneratorDialog, LocationEditDialog, SaveDialog, LoadDialog, ConfirmDialog,
    MerchantEditDialog, RouteEditDialog, FloorEditDialog, FloorNPCEditDialog
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

        # Get screen resolution for fullscreen mode
        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h

        # Use fullscreen mode with screen resolution
        self.fullscreen = window_config.get('fullscreen', True)
        if self.fullscreen:
            self.width = self.screen_width
            self.height = self.screen_height
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts - without antialiasing for crisp rendering
        self.font = pygame.font.Font(None, 18)  # Use default pygame font, size 18
        self.font_large = pygame.font.Font(None, 22)  # Larger font for headers

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

        # Connection tool state
        self.connection_source: Optional[MapLocation] = None  # First selected location (A)

        # Merchant tool state
        self.selected_merchant: Optional[Merchant] = None
        self.merchant_edit_dialog: Optional[MerchantEditDialog] = None
        self.route_edit_dialog: Optional[RouteEditDialog] = None
        self.merchant_adding_waypoint: bool = False  # True when adding waypoints by clicking on map

    def _setup_callbacks(self) -> None:
        """Setup UI callbacks."""
        # Toolbar callbacks
        self.toolbar.on_tool_change = self._on_tool_change
        self.toolbar.on_action = self._on_toolbar_action

        # Sidebar callbacks
        self.sidebar.on_biome_select = self._on_biome_select
        self.sidebar.on_location_select = self._on_location_select
        self.sidebar.on_brush_change = self._on_brush_change
        self.sidebar.on_edit_location = self._on_edit_location
        self.sidebar.on_create_merchant = self._on_create_merchant
        self.sidebar.on_edit_merchant = self._on_edit_merchant
        self.sidebar.on_delete_merchant = self._on_delete_merchant
        self.sidebar.on_select_merchant = self._on_select_merchant

        # Dialog callbacks
        self.generator_dialog.on_close = self._on_generator_dialog_close

        # Location editing state
        self._editing_location = None
        self._floor_edit_dialog = None

    def _on_tool_change(self, tool: ToolType) -> None:
        """Handle tool change."""
        self.current_tool = tool
        self.sidebar.set_tool(tool)

        # Reset connection tool state when switching tools
        if tool != ToolType.CONNECTION:
            self.connection_source = None

        # Reset merchant tool state when switching tools
        if tool != ToolType.MERCHANT:
            self.merchant_adding_waypoint = False
        else:
            # Update sidebar with merchants list
            if self.current_map:
                self.sidebar.set_merchants(self.current_map.merchants)

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
            self.toolbar.set_grid_active(self.show_grid)
        elif action == "exit":
            self.running = False

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

    def _on_edit_location(self, location_info: Dict[str, Any]) -> None:
        """Handle location edit request from sidebar."""
        if not self.current_map or not location_info:
            return

        # Find the location in the map by coordinates
        loc_x = location_info.get('x', -1)
        loc_y = location_info.get('y', -1)

        for location in self.current_map.locations:
            if location.x == loc_x and location.y == loc_y:
                self._editing_location = location
                break
        else:
            self._set_status("Локация не найдена")
            return

        # Prepare location info for dialog
        dialog_info = {
            'name': self._editing_location.name,
            'type': self._editing_location.location_type,
            'type_display': location_info.get('type_display', self._editing_location.location_type),
            'x': self._editing_location.x,
            'y': self._editing_location.y,
            'is_starting': (self._editing_location == self.current_map.starting_village),
            'rank': self._editing_location.rank,
            'shop_rank': self._editing_location.shop_rank,
            'miners_count': self._editing_location.miners_count,
            'respawn_time': self._editing_location.respawn_time,
            'player_attitude': self._editing_location.player_attitude,
            'spawn_radius': self._editing_location.spawn_radius,
            'guards': self._editing_location.guards,
            'connections': self._editing_location.connections
        }

        # Create and show the dialog
        dialog = LocationEditDialog(dialog_info)
        dialog.on_close = self._on_location_edit_dialog_close
        self.active_dialog = dialog
        dialog.show(self.width, self.height)

    def _on_location_edit_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle location edit dialog close."""
        self.active_dialog = None

        if not self._editing_location:
            return

        if action == "ok":
            # Update location name
            new_name = data.get('name', '').strip()
            if new_name and new_name != self._editing_location.name:
                self._editing_location.name = new_name
                self.has_unsaved_changes = True
                self._set_status(f"Локация переименована: {new_name}")

            # Update rank for mines and ruins
            if 'rank' in data:
                new_rank = int(data.get('rank', 1))
                if new_rank != self._editing_location.rank:
                    self._editing_location.rank = new_rank
                    self.has_unsaved_changes = True

            # Update shop_rank for settlements
            if 'shop_rank' in data:
                new_shop_rank = int(data.get('shop_rank', 1))
                if new_shop_rank != self._editing_location.shop_rank:
                    self._editing_location.shop_rank = new_shop_rank
                    self.has_unsaved_changes = True

            # Update starting village status (only for villages)
            if self._editing_location.location_type == 'village':
                set_starting = data.get('set_starting', False)
                if set_starting and self._editing_location != self.current_map.starting_village:
                    self.current_map.starting_village = self._editing_location
                    self.has_unsaved_changes = True
                    self._set_status(f"Стартовая деревня: {self._editing_location.name}")

            # Update miners_count for mines
            if 'miners_count' in data:
                new_miners_count = int(data.get('miners_count', 0))
                if new_miners_count != self._editing_location.miners_count:
                    self._editing_location.miners_count = new_miners_count
                    self.has_unsaved_changes = True

            # Update respawn_time for mines
            if 'respawn_time' in data:
                new_respawn_time = int(data.get('respawn_time', 0))
                if new_respawn_time != self._editing_location.respawn_time:
                    self._editing_location.respawn_time = new_respawn_time
                    self.has_unsaved_changes = True

            # Update resource_type for mines
            if 'resource_type' in data:
                new_resource_type = data.get('resource_type', 'copper')
                if new_resource_type != self._editing_location.resource_type:
                    self._editing_location.resource_type = new_resource_type
                    self.has_unsaved_changes = True

            # Update player_attitude (for all locations)
            if 'player_attitude' in data:
                new_attitude = int(data.get('player_attitude', 0))
                if new_attitude != self._editing_location.player_attitude:
                    self._editing_location.player_attitude = new_attitude
                    self.has_unsaved_changes = True

            # Update spawn_radius (for all locations)
            if 'spawn_radius' in data:
                new_spawn_radius = int(data.get('spawn_radius', 5))
                if new_spawn_radius != self._editing_location.spawn_radius:
                    self._editing_location.spawn_radius = new_spawn_radius
                    self.has_unsaved_changes = True

            # Update animal_count (for animal spawn points)
            if self._editing_location.location_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
                if 'animal_count' in data:
                    new_animal_count = int(data.get('animal_count', 3))
                    if new_animal_count != self._editing_location.animal_count:
                        self._editing_location.animal_count = new_animal_count
                        self.has_unsaved_changes = True

                # respawn_time for animal spawns
                if 'respawn_time' in data:
                    new_respawn_time = int(data.get('respawn_time', 50))
                    if new_respawn_time != self._editing_location.respawn_time:
                        self._editing_location.respawn_time = new_respawn_time
                        self.has_unsaved_changes = True

            # Update connections (parse from string)
            if 'connections' in data:
                connections_str = data.get('connections', '').strip()
                new_connections = []
                if connections_str:
                    try:
                        # Парсим строку формата "x,y; x,y; x,y"
                        pairs = connections_str.split(';')
                        for pair in pairs:
                            pair = pair.strip()
                            if pair:
                                coords = pair.split(',')
                                if len(coords) == 2:
                                    x = int(coords[0].strip())
                                    y = int(coords[1].strip())
                                    new_connections.append((x, y))
                    except (ValueError, IndexError):
                        # Игнорируем некорректный формат
                        pass

                if new_connections != self._editing_location.connections:
                    self._editing_location.connections = new_connections
                    self.has_unsaved_changes = True

            # Update guards (for settlements and academies)
            guards_updated = False
            new_guards = []
            for i in range(5):
                guard_type_key = f"guard_{i}_type"
                guard_rank_key = f"guard_{i}_rank"
                guard_count_key = f"guard_{i}_count"
                guard_patrol_radius_key = f"guard_{i}_patrol_radius"
                guard_respawn_time_key = f"guard_{i}_respawn_time"

                if guard_type_key in data:
                    guard_type = data.get(guard_type_key, "")
                    try:
                        guard_rank = int(data.get(guard_rank_key, "1"))
                        guard_count = int(data.get(guard_count_key, "0"))
                        guard_patrol_radius = int(data.get(guard_patrol_radius_key, "5"))
                        guard_respawn_time = int(data.get(guard_respawn_time_key, "0"))
                        # Validate rank (1-4), count (0-20), patrol_radius (3-20), and respawn_time (0-999)
                        guard_rank = max(1, min(4, guard_rank))
                        guard_count = max(0, min(20, guard_count))
                        guard_patrol_radius = max(3, min(20, guard_patrol_radius))
                        guard_respawn_time = max(0, min(999, guard_respawn_time))
                        new_guards.append(Guard(guard_type=guard_type, rank=guard_rank, count=guard_count,
                                                patrol_radius=guard_patrol_radius, respawn_time=guard_respawn_time))
                    except ValueError:
                        # Use default values if parsing fails
                        new_guards.append(Guard(guard_type=guard_type, rank=1, count=0, patrol_radius=5, respawn_time=0))

            # Update if guards have changed
            if new_guards:
                # Compare guards
                if len(new_guards) != len(self._editing_location.guards):
                    guards_updated = True
                else:
                    for i, (new_guard, old_guard) in enumerate(zip(new_guards, self._editing_location.guards)):
                        if (new_guard.guard_type != old_guard.guard_type or
                            new_guard.rank != old_guard.rank or
                            new_guard.count != old_guard.count or
                            new_guard.patrol_radius != old_guard.patrol_radius or
                            new_guard.respawn_time != old_guard.respawn_time):
                            guards_updated = True
                            break

                if guards_updated:
                    self._editing_location.guards = new_guards
                    self.has_unsaved_changes = True

            # Update sidebar info
            info = self.object_placer.get_location_info(self._editing_location)
            info['is_starting'] = (self._editing_location == self.current_map.starting_village)
            self.sidebar.set_location_info(info)

        elif action == "edit_floors":
            # Open floor edit dialog for mines and ruins
            if self._editing_location and self._editing_location.location_type in ['mine', 'ruins']:
                dialog = FloorEditDialog(self._editing_location.floors)
                dialog.on_close = self._on_floor_edit_dialog_close
                dialog.on_edit_npc = self._on_open_floor_npc_dialog
                self._floor_edit_dialog = dialog  # Save reference for later
                self.active_dialog = dialog
                dialog.show(self.width, self.height)
                return  # Don't reset _editing_location yet

        elif action == "delete":
            # Delete the location
            loc_name = self._editing_location.name
            if self._editing_location == self.current_map.starting_village:
                self.current_map.starting_village = None

            self.current_map.locations.remove(self._editing_location)
            self.has_unsaved_changes = True
            self.sidebar.set_location_info(None)
            self._set_status(f"Локация удалена: {loc_name}")

        self._editing_location = None

    def _on_floor_edit_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle floor edit dialog close."""
        if not self._editing_location:
            self.active_dialog = None
            return

        if action == "ok":
            # Get floors from saved dialog reference
            if hasattr(self, '_floor_edit_dialog') and self._floor_edit_dialog:
                new_floors = self._floor_edit_dialog.get_floors()
                self._editing_location.floors = new_floors
                self.has_unsaved_changes = True
                self._set_status("Этажи обновлены")

        # Clean up floor dialog reference
        self._floor_edit_dialog = None
        self.active_dialog = None

        # Reopen location edit dialog
        info = self.object_placer.get_location_info(self._editing_location)
        if info:
            info['is_starting'] = (self._editing_location == self.current_map.starting_village)
            dialog = LocationEditDialog(info)
            dialog.on_close = self._on_location_edit_dialog_close
            self.active_dialog = dialog
            dialog.show(self.width, self.height)

    def _on_open_floor_npc_dialog(self, floor, floor_number: int) -> None:
        """Handle request to open NPC edit dialog for a floor."""
        if not self._floor_edit_dialog:
            return

        # Store reference to editing floor number
        self._editing_floor_number = floor_number

        # Create NPC edit dialog for the floor
        dialog = FloorNPCEditDialog(floor, floor_number)
        dialog.on_close = self._on_floor_npc_dialog_close
        self._floor_npc_dialog = dialog
        self.active_dialog = dialog
        dialog.show(self.width, self.height)

    def _on_floor_npc_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle floor NPC edit dialog close."""
        if action == "ok" and hasattr(self, '_floor_npc_dialog') and self._floor_npc_dialog:
            # Get the edited NPCs
            new_npcs = self._floor_npc_dialog.get_npcs()

            # Update the floor in FloorEditDialog
            if hasattr(self, '_floor_edit_dialog') and self._floor_edit_dialog:
                self._floor_edit_dialog.update_floor_npcs(
                    self._editing_floor_number,
                    new_npcs
                )
                self._set_status(f"NPC этажа {self._editing_floor_number} обновлены")

        # Clean up
        self._floor_npc_dialog = None
        self._editing_floor_number = None

        # Restore FloorEditDialog as active
        if hasattr(self, '_floor_edit_dialog') and self._floor_edit_dialog:
            self.active_dialog = self._floor_edit_dialog

    def _on_generator_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle generator dialog close."""
        self.active_dialog = None
        if action == "ok":
            params = self.generator_dialog.get_params()
            self._generate_map(params)

    def _on_create_merchant(self) -> None:
        """Handle create merchant request."""
        if not self.current_map:
            return

        # Create new merchant with default values
        new_merchant = Merchant()
        new_merchant.name = f"Торговец {len(self.current_map.merchants) + 1}"

        dialog = MerchantEditDialog(new_merchant, is_new=True)
        dialog.on_close = self._on_merchant_dialog_close
        dialog.on_edit_route = self._on_open_route_dialog
        self.active_dialog = dialog
        self.merchant_edit_dialog = dialog
        dialog.show(self.width, self.height)

    def _on_edit_merchant(self, merchant: Merchant) -> None:
        """Handle edit merchant request."""
        if not self.current_map or not merchant:
            return

        dialog = MerchantEditDialog(merchant, is_new=False)
        dialog.on_close = self._on_merchant_dialog_close
        dialog.on_edit_route = self._on_open_route_dialog
        self.active_dialog = dialog
        self.merchant_edit_dialog = dialog
        dialog.show(self.width, self.height)

    def _on_open_route_dialog(self) -> None:
        """Handle request to open route edit dialog."""
        if not self.merchant_edit_dialog:
            return

        # Create route dialog with current waypoints from merchant dialog
        waypoints = self.merchant_edit_dialog.waypoints_copy
        is_loop = self.merchant_edit_dialog.merchant.is_loop

        route_dialog = RouteEditDialog(waypoints, is_loop)
        route_dialog.on_close = self._on_route_dialog_close
        route_dialog.on_add_waypoints_on_map = self._on_add_waypoints_on_map
        self.route_edit_dialog = route_dialog
        self.active_dialog = route_dialog
        route_dialog.show(self.width, self.height)

    def _on_route_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle route edit dialog close."""
        route_dialog = self.route_edit_dialog
        self.route_edit_dialog = None

        if action == "ok" and route_dialog and self.merchant_edit_dialog:
            # Update merchant dialog with new waypoints
            new_waypoints = route_dialog.get_waypoints()
            new_is_loop = route_dialog.get_is_loop()
            self.merchant_edit_dialog.update_waypoints(new_waypoints, new_is_loop)
            self._set_status(f"Маршрут обновлён: {len(new_waypoints)} точек")

        # Return to merchant dialog
        if self.merchant_edit_dialog:
            self.active_dialog = self.merchant_edit_dialog
            self.merchant_edit_dialog.show(self.width, self.height)
        else:
            self.active_dialog = None

    def _on_add_waypoints_on_map(self) -> None:
        """Handle request to add waypoints by clicking on map."""
        # Check which dialog to use for adding waypoints
        active_dialog = self.route_edit_dialog or self.merchant_edit_dialog
        if not active_dialog:
            return

        # Hide dialog temporarily
        active_dialog.hide()
        self.active_dialog = None
        self.merchant_adding_waypoint = True
        self._set_status("Кликните на карте для добавления точек маршрута. ПКМ/ESC - завершить")

    def _finish_adding_waypoints(self) -> None:
        """Finish adding waypoints and return to dialog."""
        self.merchant_adding_waypoint = False

        # Return to route dialog if it exists, otherwise to merchant dialog
        if self.route_edit_dialog:
            waypoints_count = len(self.route_edit_dialog.waypoints_copy)
            self.route_edit_dialog.show(self.width, self.height)
            self.active_dialog = self.route_edit_dialog
            self._set_status(f"Добавлено точек: {waypoints_count}")
        elif self.merchant_edit_dialog:
            waypoints_count = len(self.merchant_edit_dialog.waypoints_copy)
            self.merchant_edit_dialog.show(self.width, self.height)
            self.active_dialog = self.merchant_edit_dialog
            self._set_status(f"Добавлено точек: {waypoints_count}")

    def _on_delete_merchant(self, merchant: Merchant) -> None:
        """Handle delete merchant request."""
        if not self.current_map or not merchant:
            return

        self.current_map.remove_merchant(merchant.id)
        self.selected_merchant = None
        self.sidebar.set_selected_merchant(None)
        self.sidebar.set_merchants(self.current_map.merchants)
        self.has_unsaved_changes = True
        self._set_status(f"Торговец удалён: {merchant.name}")

    def _on_select_merchant(self, merchant: Merchant) -> None:
        """Handle merchant selection."""
        self.selected_merchant = merchant
        self.sidebar.set_selected_merchant(merchant)

    def _on_merchant_dialog_close(self, action: str, data: Dict[str, Any]) -> None:
        """Handle merchant edit dialog close."""
        self.active_dialog = None
        dialog = self.merchant_edit_dialog
        self.merchant_edit_dialog = None
        self.merchant_adding_waypoint = False  # Reset adding mode

        if not dialog or not self.current_map:
            return

        if action == "ok":
            # Get updated merchant from dialog
            merchant = dialog.get_merchant()

            # Check if it's a new merchant or existing one
            existing = self.current_map.get_merchant_by_id(merchant.id)
            if not existing:
                # New merchant
                self.current_map.add_merchant(merchant)
                self._set_status(f"Торговец создан: {merchant.name}")
            else:
                # Update existing merchant (reference is same, so already updated)
                self._set_status(f"Торговец обновлён: {merchant.name}")

            self.has_unsaved_changes = True
            self.selected_merchant = merchant
            self.sidebar.set_selected_merchant(merchant)
            self.sidebar.set_merchants(self.current_map.merchants)

        elif action == "delete":
            merchant = dialog.merchant
            self.current_map.remove_merchant(merchant.id)
            self.selected_merchant = None
            self.sidebar.set_selected_merchant(None)
            self.sidebar.set_merchants(self.current_map.merchants)
            self.has_unsaved_changes = True
            self._set_status(f"Торговец удалён: {merchant.name}")

    def _new_map(self) -> None:
        """Create a new empty map."""
        params = GeneratorParams()
        self._generate_map(params)
        self.current_file = None
        self.has_unsaved_changes = True
        self._set_status("Создана новая карта")

    def _open_map(self) -> None:
        """Open a map file."""
        # Use game's maps directory as default
        default_dir = Path(__file__).parent.parent / "game" / "maps"
        if not default_dir.exists():
            # Fallback to config directory for backward compatibility
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
            # Load main map file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Try to load config file
            config_data = None
            filepath_obj = Path(filepath)
            # Check for config file: map1.json -> map1_config.json
            config_path = filepath_obj.parent / f"{filepath_obj.stem}_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

            self.current_map = GeneratedMap.from_dict(data, config_data)
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

        # Default to game maps directory
        default_dir = Path(__file__).parent.parent / "game" / "maps"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_file = default_dir / "map1.json"

        self._save_to_file(str(default_file))

    def _save_to_file(self, filepath: str) -> None:
        """Save map to specified file."""
        if not self.current_map:
            return

        # Check if file already exists
        filepath_obj = Path(filepath)
        config_path = filepath_obj.parent / f"{filepath_obj.stem}_config.json"

        if filepath_obj.exists() or config_path.exists():
            # Show confirmation dialog
            message = f"Файл {filepath_obj.name} уже существует. Перезаписать?"
            dialog = ConfirmDialog(message, "Подтверждение перезаписи")
            dialog.on_close = lambda action, data: self._on_save_confirm_dialog_close(action, filepath)
            self.active_dialog = dialog
            dialog.show(self.width, self.height)
            return

        # If file doesn't exist, save directly
        self._do_save_to_file(filepath)

    def _on_save_confirm_dialog_close(self, action: str, filepath: str) -> None:
        """Handle save confirmation dialog close."""
        self.active_dialog = None
        if action == "yes":
            self._do_save_to_file(filepath)

    def _do_save_to_file(self, filepath: str) -> None:
        """Actually save map to specified file."""
        if not self.current_map:
            return

        try:
            # Save main map file (terrain only)
            data = self.current_map.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Save config file (locations and their properties)
            filepath_obj = Path(filepath)
            config_path = filepath_obj.parent / f"{filepath_obj.stem}_config.json"
            config_data = self.current_map.to_config_dict()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            self.current_file = filepath
            self.has_unsaved_changes = False
            self._set_status(f"Сохранено: {Path(filepath).name} и конфиг")

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

    def _draw_dashed_line(self, surface: pygame.Surface, color: Tuple[int, int, int],
                          start: Tuple[int, int], end: Tuple[int, int],
                          width: int = 1, dash_length: int = 8) -> None:
        """Draw a dashed line between two points."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)
        if distance == 0:
            return

        # Normalize direction
        dx /= distance
        dy /= distance

        # Draw dashes
        current = 0
        drawing = True
        while current < distance:
            segment_length = min(dash_length, distance - current)
            if drawing:
                start_x = start[0] + dx * current
                start_y = start[1] + dy * current
                end_x = start[0] + dx * (current + segment_length)
                end_y = start[1] + dy * (current + segment_length)
                pygame.draw.line(surface, color,
                               (int(start_x), int(start_y)),
                               (int(end_x), int(end_y)), width)
            current += dash_length
            drawing = not drawing

    def _distance_to_line(self, px: int, py: int, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate distance from point (px, py) to line segment (x1, y1) - (x2, y2)."""
        # Vector from point 1 to point 2
        dx = x2 - x1
        dy = y2 - y1

        # If the line segment has zero length
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Calculate parameter t for the closest point on the line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        # Find the closest point on the line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Return distance from point to closest point
        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    def _find_connection_near_click(self, tile_x: int, tile_y: int) -> Optional[Tuple]:
        """Find connection near the click point. Returns (source_location, target_location) or None."""
        if not self.current_map:
            return None

        max_distance = 3  # Maximum distance in tiles to consider a click "near" a connection
        closest_connection = None
        closest_distance = float('inf')

        # Check all connections
        for source_loc in self.current_map.locations:
            for target_x, target_y in source_loc.connections:
                # Find target location
                target_loc = self.current_map.get_location_at(target_x, target_y)
                if not target_loc:
                    continue

                # Calculate distance from click to connection line
                distance = self._distance_to_line(
                    tile_x, tile_y,
                    source_loc.x, source_loc.y,
                    target_x, target_y
                )

                if distance < closest_distance and distance <= max_distance:
                    closest_distance = distance
                    closest_connection = (source_loc, target_loc)

        return closest_connection

    def handle_events(self) -> None:
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                continue

            # Handle Escape during waypoint adding mode
            if self.merchant_adding_waypoint and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._finish_adding_waypoints()
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

        # Handle waypoint adding mode
        if self.merchant_adding_waypoint:
            # Determine which dialog to add waypoints to
            target_dialog = self.route_edit_dialog or self.merchant_edit_dialog
            if target_dialog:
                # Add waypoint to dialog's waypoints list
                target_dialog.waypoints_copy.append(
                    MerchantWaypoint(x=tile_x, y=tile_y, duration=10)
                )
                target_dialog._update_waypoints_data()
                self._set_status(f"Добавлена точка ({tile_x}, {tile_y}). ПКМ/ESC - завершить")
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

        elif self.current_tool == ToolType.CONNECTION:
            # Connection mode: click on location to create connection, click near line to delete
            location = self.object_placer.select_location(self.current_map, tile_x, tile_y)

            if not location:
                # No location at click - try to find and delete connection near click
                connection = self._find_connection_near_click(tile_x, tile_y)
                if connection:
                    source_loc, target_loc = connection
                    # Remove unidirectional connection (master -> subordinate)
                    source_loc.remove_connection(target_loc.x, target_loc.y)
                    self.has_unsaved_changes = True
                    self._set_status(f"Удалена связь: {source_loc.name} → {target_loc.name}")
                else:
                    self._set_status("Выберите объект для связи или кликните на линию для удаления")
                return

            if not self.connection_source:
                # First click - select master object (A)
                self.connection_source = location
                self._set_status(f"Выбран главный: {location.name}. Выберите подчиненный объект")
            else:
                # Second click - select target object (B) and create connection
                if location == self.connection_source:
                    self._set_status("Нельзя создать связь с самим собой")
                    return

                # Check if connection already exists
                if self.connection_source.has_connection_to(location.x, location.y):
                    self._set_status(f"Связь уже существует: {self.connection_source.name} -> {location.name}")
                    self.connection_source = None
                    return

                # Create unidirectional connection: A -> B (A is master, B is subordinate)
                self.connection_source.add_connection(location.x, location.y)
                self.has_unsaved_changes = True
                self._set_status(f"Создана связь: {self.connection_source.name} → {location.name} (главный → подчиненный)")

                # Reset for next connection
                self.connection_source = None

        elif self.current_tool == ToolType.MERCHANT:
            # Merchant mode: click to add waypoint to selected merchant or select waypoint
            if self.selected_merchant:
                # Add waypoint at click position
                self.selected_merchant.add_waypoint(tile_x, tile_y, duration=10)
                self.has_unsaved_changes = True
                self.sidebar.set_merchants(self.current_map.merchants)
                self.sidebar.set_selected_merchant(self.selected_merchant)
                self._set_status(f"Добавлена точка маршрута ({tile_x}, {tile_y})")
            else:
                # Try to select a waypoint/merchant at click position
                merchant = self.current_map.get_merchant_at(tile_x, tile_y)
                if merchant:
                    self.selected_merchant = merchant
                    self.sidebar.set_selected_merchant(merchant)
                    self._set_status(f"Выбран торговец: {merchant.name}")
                else:
                    self._set_status("Выберите торговца в боковой панели")

    def _handle_right_click(self, pos: Tuple[int, int]) -> None:
        """Handle right mouse click."""
        if not self.current_map:
            return

        # Handle waypoint adding mode - finish and return to dialog
        if self.merchant_adding_waypoint:
            self._finish_adding_waypoints()
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
                self._render_connections()  # Draw connections first (behind locations)
                self._render_locations()

            # Draw merchants and their routes
            self._render_merchants()

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

    def _render_connections(self) -> None:
        """Render arrows between connected locations (master -> subordinate)."""
        if not self.current_map:
            return

        # Draw all connections
        for source_location in self.current_map.locations:
            for target_x, target_y in source_location.connections:
                # Find target location
                target_location = self.current_map.get_location_at(target_x, target_y)
                if not target_location:
                    continue  # Skip invalid connections

                # Get screen positions
                source_screen = self._tile_to_screen(source_location.x, source_location.y)
                target_screen = self._tile_to_screen(target_x, target_y)

                # Calculate center points
                source_center = (
                    source_screen[0] + self.tile_size // 2,
                    source_screen[1] + self.tile_size // 2
                )
                target_center = (
                    target_screen[0] + self.tile_size // 2,
                    target_screen[1] + self.tile_size // 2
                )

                # Calculate direction
                dx = target_center[0] - source_center[0]
                dy = target_center[1] - source_center[1]
                line_length = math.sqrt(dx * dx + dy * dy)
                if line_length == 0:
                    continue

                # Normalize direction
                ndx = dx / line_length
                ndy = dy / line_length

                # Shorten line to not overlap with location markers
                marker_radius = max(6, self.tile_size) // 2 + 4
                start_point = (
                    source_center[0] + ndx * marker_radius,
                    source_center[1] + ndy * marker_radius
                )
                end_point = (
                    target_center[0] - ndx * marker_radius,
                    target_center[1] - ndy * marker_radius
                )

                # Draw line with gradient (green at master, blue at subordinate)
                # Main line - use gradient effect
                master_color = (50, 200, 50)  # Green - master
                subordinate_color = (100, 150, 255)  # Blue - subordinate

                # Draw the line
                pygame.draw.line(self.screen, subordinate_color, start_point, end_point, 2)

                # Draw small circle at master end (green)
                pygame.draw.circle(self.screen, master_color,
                                   (int(start_point[0]), int(start_point[1])), 4)

                # Draw arrowhead at subordinate end (blue)
                angle = math.atan2(dy, dx)
                arrow_size = 10
                arrow_angle = math.pi / 6  # 30 degrees

                p1 = end_point
                p2 = (
                    end_point[0] - arrow_size * math.cos(angle - arrow_angle),
                    end_point[1] - arrow_size * math.sin(angle - arrow_angle)
                )
                p3 = (
                    end_point[0] - arrow_size * math.cos(angle + arrow_angle),
                    end_point[1] - arrow_size * math.sin(angle + arrow_angle)
                )

                pygame.draw.polygon(self.screen, subordinate_color, [p1, p2, p3])

        # Highlight source location when in connection mode
        if self.current_tool == ToolType.CONNECTION and self.connection_source:
            source_screen = self._tile_to_screen(
                self.connection_source.x,
                self.connection_source.y
            )
            center = (
                source_screen[0] + self.tile_size // 2,
                source_screen[1] + self.tile_size // 2
            )
            marker_size = max(10, self.tile_size + 4)
            pygame.draw.circle(self.screen, (255, 255, 0), center, marker_size // 2, 3)

    def _render_merchants(self) -> None:
        """Render merchants and their routes."""
        if not self.current_map:
            return

        # Render existing merchants
        if not self.current_map.merchants and not self.merchant_adding_waypoint:
            return

        for merchant in self.current_map.merchants:
            if not merchant.waypoints:
                continue

            # Draw route lines between waypoints
            color = merchant.color
            waypoints = merchant.waypoints

            # Determine how many lines to draw
            # If is_loop is True or route is physically closed, draw all lines including loop back
            should_loop = merchant.is_loop or merchant.is_route_closed()
            line_count = len(waypoints) if should_loop else len(waypoints) - 1

            for i in range(line_count):
                wp = waypoints[i]
                next_idx = (i + 1) % len(waypoints)
                next_wp = waypoints[next_idx]

                # Get screen positions
                wp_screen = self._tile_to_screen(wp.x, wp.y)
                next_screen = self._tile_to_screen(next_wp.x, next_wp.y)

                wp_center = (
                    wp_screen[0] + self.tile_size // 2,
                    wp_screen[1] + self.tile_size // 2
                )
                next_center = (
                    next_screen[0] + self.tile_size // 2,
                    next_screen[1] + self.tile_size // 2
                )

                # Use dashed line for loop-back segment
                is_loop_segment = (i == len(waypoints) - 1 and should_loop)
                if is_loop_segment:
                    # Draw dashed line for loop segment
                    self._draw_dashed_line(self.screen, color, wp_center, next_center, 2, 8)
                else:
                    # Draw solid line for regular segments
                    pygame.draw.line(self.screen, color, wp_center, next_center, 2)

                # Draw arrowhead
                dx = next_center[0] - wp_center[0]
                dy = next_center[1] - wp_center[1]
                if dx != 0 or dy != 0:  # Avoid division by zero
                    angle = math.atan2(dy, dx)

                    arrow_size = 8
                    arrow_angle = math.pi / 6

                    # Midpoint of the line
                    mid_x = (wp_center[0] + next_center[0]) // 2
                    mid_y = (wp_center[1] + next_center[1]) // 2

                    p1 = (mid_x, mid_y)
                    p2 = (
                        mid_x - arrow_size * math.cos(angle - arrow_angle),
                        mid_y - arrow_size * math.sin(angle - arrow_angle)
                    )
                    p3 = (
                        mid_x - arrow_size * math.cos(angle + arrow_angle),
                        mid_y - arrow_size * math.sin(angle + arrow_angle)
                    )

                    pygame.draw.polygon(self.screen, color, [p1, p2, p3])

            # Draw waypoint markers
            for i, wp in enumerate(waypoints):
                wp_screen = self._tile_to_screen(wp.x, wp.y)
                center = (
                    wp_screen[0] + self.tile_size // 2,
                    wp_screen[1] + self.tile_size // 2
                )

                # Check if visible
                if center[0] < -20 or center[0] > self.width + 20:
                    continue
                if center[1] < self.toolbar_height - 20 or center[1] > self.height + 20:
                    continue

                marker_size = max(8, self.tile_size)

                # Highlight selected merchant's waypoints
                if merchant == self.selected_merchant:
                    # Outer highlight
                    pygame.draw.circle(self.screen, (255, 255, 255), center, marker_size // 2 + 3, 2)

                # Waypoint marker (diamond shape)
                diamond_size = marker_size // 2
                diamond_points = [
                    (center[0], center[1] - diamond_size),  # Top
                    (center[0] + diamond_size, center[1]),  # Right
                    (center[0], center[1] + diamond_size),  # Bottom
                    (center[0] - diamond_size, center[1])   # Left
                ]
                pygame.draw.polygon(self.screen, (0, 0, 0), diamond_points)  # Border
                pygame.draw.polygon(self.screen, color, diamond_points, 0)

                # Draw waypoint number
                if self.tile_size >= 6:
                    num_text = self.font.render(str(i + 1), True, (255, 255, 255))
                    num_rect = num_text.get_rect(center=center)
                    self.screen.blit(num_text, num_rect)

                # Draw duration on hover/selection
                if merchant == self.selected_merchant and self.tile_size >= 8:
                    duration_text = self.font.render(f"{wp.duration}ход", True, (200, 200, 200))
                    self.screen.blit(duration_text, (center[0] + marker_size, center[1] - 8))

        # Render temporary waypoints during adding mode
        if self.merchant_adding_waypoint:
            target_dialog = self.route_edit_dialog or self.merchant_edit_dialog
            if not target_dialog:
                return
            waypoints = target_dialog.waypoints_copy
            temp_color = (100, 200, 255)  # Light blue for temporary waypoints

            # Draw lines between waypoints
            for i in range(len(waypoints)):
                if i < len(waypoints) - 1:
                    wp = waypoints[i]
                    next_wp = waypoints[i + 1]

                    wp_screen = self._tile_to_screen(wp.x, wp.y)
                    next_screen = self._tile_to_screen(next_wp.x, next_wp.y)

                    wp_center = (
                        wp_screen[0] + self.tile_size // 2,
                        wp_screen[1] + self.tile_size // 2
                    )
                    next_center = (
                        next_screen[0] + self.tile_size // 2,
                        next_screen[1] + self.tile_size // 2
                    )

                    pygame.draw.line(self.screen, temp_color, wp_center, next_center, 2)

            # Draw waypoint markers
            for i, wp in enumerate(waypoints):
                wp_screen = self._tile_to_screen(wp.x, wp.y)
                center = (
                    wp_screen[0] + self.tile_size // 2,
                    wp_screen[1] + self.tile_size // 2
                )

                marker_size = max(8, self.tile_size)

                # Diamond shape
                diamond_size = marker_size // 2
                diamond_points = [
                    (center[0], center[1] - diamond_size),
                    (center[0] + diamond_size, center[1]),
                    (center[0], center[1] + diamond_size),
                    (center[0] - diamond_size, center[1])
                ]
                pygame.draw.polygon(self.screen, (0, 0, 0), diamond_points)
                pygame.draw.polygon(self.screen, temp_color, diamond_points, 0)

                # Draw waypoint number
                if self.tile_size >= 6:
                    num_text = self.font.render(str(i + 1), True, (255, 255, 255))
                    num_rect = num_text.get_rect(center=center)
                    self.screen.blit(num_text, num_rect)

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
