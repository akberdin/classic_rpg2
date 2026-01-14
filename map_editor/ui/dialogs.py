"""Dialog windows for the map editor."""

import pygame
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from ..tools.generator import (
    GeneratorParams,
    LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE,
    LOCATION_MINE, LOCATION_RUINS,
    LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY,
    LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER,
    Guard, GUARD_TYPES, GUARD_NONE,
    RESOURCE_TYPES,
    Floor, FLOOR_TYPES, FLOOR_NONE,
    FloorNPC, FLOOR_NPC_TYPES, FLOOR_NPC_RANKS, FLOOR_NPC_NONE,
    Merchant, MerchantWaypoint, MERCHANT_RANKS, MERCHANT_SPECIALIZATIONS,
    Quest, QUEST_TYPES, QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS,
    QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION, QUEST_COLLECT_ITEMS,
    QUEST_RESOURCE_TARGETS, QUEST_ANIMAL_TARGETS, QUEST_TARGETS,
    QUEST_DIFFICULTIES, QUEST_GIVER_LOCATIONS, QUEST_CLEARABLE_LOCATIONS,
    QUEST_TARGET_WOOD, QUEST_TARGET_WOLF
)


@dataclass
class DialogButton:
    """Button in a dialog."""
    rect: pygame.Rect
    text: str
    action: str
    primary: bool = False


@dataclass
class DialogSlider:
    """Slider control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    value: float
    min_val: float
    max_val: float
    step: float = 1.0
    is_int: bool = True


@dataclass
class DialogCheckbox:
    """Checkbox control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    checked: bool = False


@dataclass
class DialogTextInput:
    """Text input control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    value: str = ""
    max_length: int = 50
    active: bool = False


@dataclass
class DialogDropdown:
    """Dropdown/combobox control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    options: Dict[str, str]  # key -> display name
    selected: str = ""  # selected option key
    expanded: bool = False


class Dialog:
    """Base dialog class."""

    def __init__(self, title: str, width: int = 400, height: int = 300):
        self.title = title
        self.width = width
        self.height = height
        self.visible = False
        self.result: Optional[str] = None
        self.data: Dict[str, Any] = {}

        # Colors
        self.bg_color = (45, 45, 48)
        self.title_bg = (30, 30, 32)
        self.text_color = (255, 255, 255)
        self.button_color = (62, 62, 66)
        self.button_hover = (80, 80, 85)
        self.button_primary = (0, 122, 204)
        self.border_color = (70, 70, 75)
        self.slider_bg = (30, 30, 32)
        self.slider_fill = (0, 122, 204)

        # Font - use default pygame font for crisp rendering
        self.font = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 22)

        # UI elements
        self.buttons: List[DialogButton] = []
        self.sliders: List[DialogSlider] = []
        self.checkboxes: List[DialogCheckbox] = []
        self.text_inputs: List[DialogTextInput] = []
        self.dropdowns: List[DialogDropdown] = []
        self.hovered_button: Optional[int] = None
        self.active_slider: Optional[DialogSlider] = None
        self.active_text_input: Optional[DialogTextInput] = None
        self.active_dropdown: Optional[DialogDropdown] = None

        # Position (will be set when showing)
        self.x = 0
        self.y = 0

        # Callbacks
        self.on_close: Optional[Callable[[str, Dict[str, Any]], None]] = None

    def show(self, screen_width: int, screen_height: int) -> None:
        """Show the dialog centered on screen."""
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.visible = True
        self.result = None

    def hide(self) -> None:
        """Hide the dialog."""
        self.visible = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Update slider if dragging
            if self.active_slider:
                self._update_slider(self.active_slider, local_x)
                return True

            # Update hovered button
            self.hovered_button = None
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(local_x, local_y):
                    self.hovered_button = i
                    break

            return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return True

            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check if click is outside dialog
            if not (0 <= local_x <= self.width and 0 <= local_y <= self.height):
                return True

            # Check buttons
            for button in self.buttons:
                if button.rect.collidepoint(local_x, local_y):
                    self._handle_button_click(button)
                    return True

            # Check sliders
            for slider in self.sliders:
                if slider.rect.collidepoint(local_x, local_y):
                    self.active_slider = slider
                    self._update_slider(slider, local_x)
                    return True

            # Check checkboxes
            for checkbox in self.checkboxes:
                if checkbox.rect.collidepoint(local_x, local_y):
                    checkbox.checked = not checkbox.checked
                    self.data[checkbox.key] = checkbox.checked
                    return True

            # Check dropdowns FIRST (so expanded dropdowns are on top)
            # First pass: check if clicking on expanded dropdown options
            for dropdown in self.dropdowns:
                if dropdown.expanded:
                    # Check if clicking on an option
                    option_height = 28
                    options_y = dropdown.rect.bottom
                    for i, (key, value) in enumerate(dropdown.options.items()):
                        option_rect = pygame.Rect(dropdown.rect.x, options_y + i * option_height,
                                                  dropdown.rect.width, option_height)
                        if option_rect.collidepoint(local_x, local_y):
                            dropdown.selected = key
                            dropdown.expanded = False
                            self.active_dropdown = None
                            self.data[dropdown.key] = key
                            return True

            # Second pass: check if clicking on dropdown headers
            for dropdown in self.dropdowns:
                if dropdown.rect.collidepoint(local_x, local_y):
                    # Toggle dropdown
                    dropdown.expanded = not dropdown.expanded
                    # Close other dropdowns
                    for dd in self.dropdowns:
                        if dd != dropdown:
                            dd.expanded = False
                    self.active_dropdown = dropdown if dropdown.expanded else None
                    return True

            # Close all dropdowns if clicking elsewhere
            dropdown_was_open = any(dd.expanded for dd in self.dropdowns)
            for dropdown in self.dropdowns:
                dropdown.expanded = False
            self.active_dropdown = None

            # If a dropdown was open and we closed it, consume the click
            if dropdown_was_open:
                return True

            # Check text inputs
            for text_input in self.text_inputs:
                if text_input.rect.collidepoint(local_x, local_y):
                    # Deactivate all other inputs
                    for ti in self.text_inputs:
                        ti.active = False
                    text_input.active = True
                    self.active_text_input = text_input
                    return True
                else:
                    text_input.active = False

            self.active_text_input = None

            return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active_slider = None
            return self.visible

        elif event.type == pygame.KEYDOWN:
            # Handle text input first
            if self.active_text_input:
                if event.key == pygame.K_BACKSPACE:
                    self.active_text_input.value = self.active_text_input.value[:-1]
                    self.data[self.active_text_input.key] = self.active_text_input.value
                    return True
                elif event.key == pygame.K_RETURN:
                    # Deactivate text input on Enter
                    self.active_text_input.active = False
                    self.active_text_input = None
                    return True
                elif event.key == pygame.K_ESCAPE:
                    # Deactivate text input on Escape
                    self.active_text_input.active = False
                    self.active_text_input = None
                    return True
                elif event.key == pygame.K_TAB:
                    # Move to next text input
                    self._focus_next_text_input()
                    return True
                elif event.unicode and len(self.active_text_input.value) < self.active_text_input.max_length:
                    # Add character (filter control characters)
                    if event.unicode.isprintable():
                        self.active_text_input.value += event.unicode
                        self.data[self.active_text_input.key] = self.active_text_input.value
                return True

            if event.key == pygame.K_ESCAPE:
                self.result = "cancel"
                self.hide()
                if self.on_close:
                    self.on_close("cancel", self.data)
                return True
            elif event.key == pygame.K_RETURN:
                self.result = "ok"
                self.hide()
                if self.on_close:
                    self.on_close("ok", self.data)
                return True

        return self.visible

    def _focus_next_text_input(self) -> None:
        """Focus the next text input field."""
        if not self.text_inputs:
            return

        current_idx = -1
        for i, ti in enumerate(self.text_inputs):
            if ti.active:
                current_idx = i
                ti.active = False
                break

        next_idx = (current_idx + 1) % len(self.text_inputs)
        self.text_inputs[next_idx].active = True
        self.active_text_input = self.text_inputs[next_idx]

    def _handle_button_click(self, button: DialogButton) -> None:
        """Handle button click."""
        self.result = button.action
        self.hide()
        if self.on_close:
            self.on_close(button.action, self.data)

    def _update_slider(self, slider: DialogSlider, local_x: int) -> None:
        """Update slider value based on mouse position."""
        rel_x = local_x - slider.rect.x
        ratio = max(0, min(1, rel_x / slider.rect.width))
        raw_value = slider.min_val + ratio * (slider.max_val - slider.min_val)

        if slider.step > 0:
            raw_value = round(raw_value / slider.step) * slider.step

        if slider.is_int:
            raw_value = int(raw_value)

        slider.value = raw_value
        self.data[slider.key] = slider.value

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # Dialog background
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, dialog_rect, border_radius=8)
        pygame.draw.rect(surface, self.border_color, dialog_rect, width=1, border_radius=8)

        # Title bar
        title_rect = pygame.Rect(self.x, self.y, self.width, 30)
        pygame.draw.rect(surface, self.title_bg, title_rect,
                        border_top_left_radius=8, border_top_right_radius=8)

        title_surface = self.font_title.render(self.title, True, self.text_color)
        surface.blit(title_surface, (self.x + 10, self.y + 7))

        # Draw sliders
        for slider in self.sliders:
            self._draw_slider(surface, slider)

        # Draw checkboxes
        for checkbox in self.checkboxes:
            self._draw_checkbox(surface, checkbox)

        # Draw text inputs
        for text_input in self.text_inputs:
            self._draw_text_input(surface, text_input)

        # Draw buttons
        for i, button in enumerate(self.buttons):
            self._draw_button(surface, button, i == self.hovered_button)

        # Draw dropdowns in two passes:
        # First pass: draw all collapsed dropdowns
        # Second pass: draw expanded dropdown last (so it's on top)
        expanded_dropdown = None
        for dropdown in self.dropdowns:
            if dropdown.expanded:
                expanded_dropdown = dropdown
            else:
                self._draw_dropdown(surface, dropdown)

        # Draw expanded dropdown last so it appears on top
        if expanded_dropdown:
            self._draw_dropdown(surface, expanded_dropdown)

    def _draw_slider(self, surface: pygame.Surface, slider: DialogSlider) -> None:
        """Draw a slider control."""
        rect = pygame.Rect(
            self.x + slider.rect.x,
            self.y + slider.rect.y,
            slider.rect.width,
            slider.rect.height
        )

        # Label
        label_surface = self.font.render(
            f"{slider.label}: {slider.value}",
            True, self.text_color
        )
        surface.blit(label_surface, (rect.x, rect.y - 18))

        # Background
        pygame.draw.rect(surface, self.slider_bg, rect, border_radius=4)

        # Fill
        ratio = (slider.value - slider.min_val) / (slider.max_val - slider.min_val)
        fill_width = int(rect.width * ratio)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(surface, self.slider_fill, fill_rect, border_radius=4)

        # Border
        pygame.draw.rect(surface, self.border_color, rect, width=1, border_radius=4)

    def _draw_checkbox(self, surface: pygame.Surface, checkbox: DialogCheckbox) -> None:
        """Draw a checkbox control."""
        rect = pygame.Rect(
            self.x + checkbox.rect.x,
            self.y + checkbox.rect.y,
            checkbox.rect.width,
            checkbox.rect.height
        )

        # Box
        box_rect = pygame.Rect(rect.x, rect.y, 18, 18)
        pygame.draw.rect(surface, self.slider_bg, box_rect, border_radius=2)
        pygame.draw.rect(surface, self.border_color, box_rect, width=1, border_radius=2)

        # Check mark
        if checkbox.checked:
            pygame.draw.rect(surface, self.slider_fill,
                           pygame.Rect(box_rect.x + 3, box_rect.y + 3, 12, 12),
                           border_radius=2)

        # Label
        label_surface = self.font.render(checkbox.label, True, self.text_color)
        surface.blit(label_surface, (rect.x + 24, rect.y + 2))

    def _draw_text_input(self, surface: pygame.Surface, text_input: DialogTextInput) -> None:
        """Draw a text input control."""
        rect = pygame.Rect(
            self.x + text_input.rect.x,
            self.y + text_input.rect.y,
            text_input.rect.width,
            text_input.rect.height
        )

        # Label
        label_surface = self.font.render(text_input.label, True, self.text_color)
        surface.blit(label_surface, (rect.x, rect.y - 18))

        # Input background
        bg_color = (50, 50, 55) if text_input.active else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

        # Border (highlight when active)
        border_color = self.slider_fill if text_input.active else self.border_color
        pygame.draw.rect(surface, border_color, rect, width=2 if text_input.active else 1, border_radius=4)

        # Text
        display_text = text_input.value
        if text_input.active:
            # Add cursor
            display_text += "|"

        text_surface = self.font.render(display_text, True, self.text_color)

        # Clip text to fit
        text_rect = text_surface.get_rect(midleft=(rect.x + 8, rect.centery))
        if text_rect.width > rect.width - 16:
            # Show end of text when too long
            text_rect.right = rect.right - 8

        surface.blit(text_surface, text_rect)

    def _draw_dropdown(self, surface: pygame.Surface, dropdown: DialogDropdown) -> None:
        """Draw a dropdown control."""
        rect = pygame.Rect(
            self.x + dropdown.rect.x,
            self.y + dropdown.rect.y,
            dropdown.rect.width,
            dropdown.rect.height
        )

        # Label
        if dropdown.label:
            label_surface = self.font.render(dropdown.label, True, self.text_color)
            surface.blit(label_surface, (rect.x, rect.y - 18))

        # Dropdown background
        bg_color = (50, 50, 55) if dropdown.expanded else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, rect, width=1, border_radius=4)

        # Display selected option
        display_text = dropdown.options.get(dropdown.selected, "Нет")
        text_surface = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surface, (rect.x + 8, rect.y + 6))

        # Arrow indicator
        arrow = "▼" if not dropdown.expanded else "▲"
        arrow_surface = self.font.render(arrow, True, self.text_color)
        surface.blit(arrow_surface, (rect.right - 20, rect.y + 6))

        # Draw expanded options if dropdown is open
        if dropdown.expanded:
            option_height = 28
            options_y = rect.bottom
            for i, (key, value) in enumerate(dropdown.options.items()):
                option_rect = pygame.Rect(rect.x, options_y + i * option_height,
                                         rect.width, option_height)
                # Highlight selected option
                if key == dropdown.selected:
                    pygame.draw.rect(surface, (70, 70, 75), option_rect)
                else:
                    pygame.draw.rect(surface, self.slider_bg, option_rect)
                pygame.draw.rect(surface, self.border_color, option_rect, width=1)

                option_text = self.font.render(value, True, self.text_color)
                surface.blit(option_text, (option_rect.x + 8, option_rect.y + 6))

    def _draw_button(self, surface: pygame.Surface, button: DialogButton,
                     hovered: bool) -> None:
        """Draw a button."""
        rect = pygame.Rect(
            self.x + button.rect.x,
            self.y + button.rect.y,
            button.rect.width,
            button.rect.height
        )

        if button.primary:
            color = self.button_primary
        elif hovered:
            color = self.button_hover
        else:
            color = self.button_color

        pygame.draw.rect(surface, color, rect, border_radius=4)

        text_surface = self.font.render(button.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)


class GeneratorDialog(Dialog):
    """Dialog for generator settings."""

    def __init__(self, params: GeneratorParams = None):
        super().__init__("Настройки генератора", 450, 650)
        self.params = params or GeneratorParams()
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        y = 50
        slider_height = 16
        spacing = 45

        # Map size
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Ширина карты",
            key="width",
            value=self.params.width,
            min_val=50, max_val=1000, step=10
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Высота карты",
            key="height",
            value=self.params.height,
            min_val=50, max_val=1000, step=10
        ))
        y += spacing

        # Terrain parameters
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Масштаб рельефа",
            key="elevation_scale",
            value=self.params.elevation_scale,
            min_val=50, max_val=300, step=10, is_int=False
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Уровень воды",
            key="water_level",
            value=int(self.params.water_level * 100),
            min_val=10, max_val=50, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Уровень гор",
            key="mountain_level",
            value=int(self.params.mountain_level * 100),
            min_val=60, max_val=90, step=1
        ))
        y += spacing

        # Location counts
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество городов",
            key="city_count",
            value=self.params.city_count,
            min_val=1, max_val=15, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество деревень",
            key="village_count",
            value=self.params.village_count,
            min_val=0, max_val=40, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество шахт",
            key="mine_count",
            value=self.params.mine_count,
            min_val=0, max_val=20, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество руин",
            key="ruins_count",
            value=self.params.ruins_count,
            min_val=0, max_val=100, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество лагерей бандитов",
            key="bandit_camp_count",
            value=self.params.bandit_camp_count,
            min_val=0, max_val=100, step=1
        ))
        y += spacing

        # Options
        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Температурный градиент",
            key="temperature_gradient",
            checked=self.params.temperature_gradient
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Генерировать пляжи",
            key="generate_beaches",
            checked=self.params.generate_beaches
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Генерировать реки",
            key="generate_rivers",
            checked=self.params.generate_rivers
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Без ограничения дистанции объектов",
            key="ignore_min_distance",
            checked=self.params.ignore_min_distance
        ))
        y += 40

        # Buttons
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Применить",
            action="ok",
            primary=True
        ))

        # Initialize data
        for slider in self.sliders:
            self.data[slider.key] = slider.value
        for checkbox in self.checkboxes:
            self.data[checkbox.key] = checkbox.checked

    def get_params(self) -> GeneratorParams:
        """Get generator params from dialog data."""
        return GeneratorParams(
            width=int(self.data.get('width', 200)),
            height=int(self.data.get('height', 200)),
            elevation_scale=float(self.data.get('elevation_scale', 150)),
            water_level=self.data.get('water_level', 30) / 100.0,
            mountain_level=self.data.get('mountain_level', 75) / 100.0,
            city_count=int(self.data.get('city_count', 5)),
            village_count=int(self.data.get('village_count', 15)),
            mine_count=int(self.data.get('mine_count', 8)),
            ruins_count=int(self.data.get('ruins_count', 10)),
            bandit_camp_count=int(self.data.get('bandit_camp_count', 10)),
            temperature_gradient=self.data.get('temperature_gradient', True),
            generate_beaches=self.data.get('generate_beaches', True),
            generate_rivers=self.data.get('generate_rivers', True),
            ignore_min_distance=self.data.get('ignore_min_distance', False)
        )


class LocationEditDialog(Dialog):
    """Dialog for editing location properties with name input."""

    def __init__(self, location_info: Dict[str, Any] = None):
        self.location_info = location_info or {}
        # Calculate dialog height based on location type
        loc_type = self.location_info.get('type', '')
        height = 450  # Base height increased for spawn_radius slider
        height += 50  # Space for rank slider (for all location types)
        if loc_type in [LOCATION_MINE, LOCATION_RUINS]:
            height += 45  # Space for "Edit floors" button
        if loc_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
            height += 50  # Space for shop_rank slider
        if loc_type == LOCATION_MINE:
            height += 170  # Space for miners_count, respawn_time sliders and resource_type dropdown
        # Add space for animal spawn points
        if loc_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            height += 150  # Space for animal_count, respawn_time, and spawn_radius sliders
        # Add space for guards (for settlements and academies)
        if loc_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                        LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            height += 305  # Space for 5 guard slots (headers + 5*45 + spacing)
        # Add space for quests button (for quest-giving locations)
        if loc_type in QUEST_GIVER_LOCATIONS:
            height += 45  # Space for "Edit quests" button
        # Include location type in dialog title
        type_display = self.location_info.get('type_display', '')
        title = f"Редактирование локации ({type_display})" if type_display else "Редактирование локации"
        super().__init__(title, 720, height)  # Increased width to 720 for guards with respawn_time
        # Guard headers (will be set in _setup_controls if location has guards)
        self._guard_headers_y = None
        self._guard_headers = None
        # Callback for opening quests dialog
        self.on_edit_quests: Optional[Callable[[List[Quest]], None]] = None
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls with text input for name."""
        y = 50
        loc_type = self.location_info.get('type', '')

        # Name input
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(20, y + 20, self.width - 40, 28),
            label="Название локации:",
            key="name",
            value=self.location_info.get('name', ''),
            max_length=40
        ))
        self.data['name'] = self.location_info.get('name', '')
        y += 70

        # Rank slider for all location types
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y + 20, self.width - 40, 16),
            label="Ранг локации (1-4)",
            key="rank",
            value=self.location_info.get('rank', 1),
            min_val=1, max_val=4, step=1
        ))
        self.data['rank'] = self.location_info.get('rank', 1)
        y += 50

        # Button to edit floors (only for mines and ruins)
        if loc_type in [LOCATION_MINE, LOCATION_RUINS]:
            self.buttons.append(DialogButton(
                rect=pygame.Rect(20, y, 200, 30),
                text="Редактировать этажи",
                action="edit_floors"
            ))
            y += 45

        # Shop rank slider for settlements
        if loc_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Ранг магазина",
                key="shop_rank",
                value=self.location_info.get('shop_rank', 1),
                min_val=1, max_val=4, step=1
            ))
            self.data['shop_rank'] = self.location_info.get('shop_rank', 1)
            y += 50

        # Checkbox for starting village (only for villages)
        if loc_type == LOCATION_VILLAGE:
            self.checkboxes.append(DialogCheckbox(
                rect=pygame.Rect(20, y, self.width - 40, 20),
                label="Сделать стартовой деревней",
                key="set_starting",
                checked=self.location_info.get('is_starting', False)
            ))
            self.data['set_starting'] = self.location_info.get('is_starting', False)
            y += 40

        # Miners count slider (only for mines)
        if loc_type == LOCATION_MINE:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Количество шахтеров (0-10)",
                key="miners_count",
                value=self.location_info.get('miners_count', 0),
                min_val=0, max_val=10, step=1
            ))
            self.data['miners_count'] = self.location_info.get('miners_count', 0)
            y += 50

        # Respawn time slider (only for mines)
        if loc_type == LOCATION_MINE:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Время респавна (0-200 ходов)",
                key="respawn_time",
                value=self.location_info.get('respawn_time', 0),
                min_val=0, max_val=200, step=5
            ))
            self.data['respawn_time'] = self.location_info.get('respawn_time', 0)
            y += 50

        # Resource type dropdown (only for mines)
        if loc_type == LOCATION_MINE:
            self.dropdowns.append(DialogDropdown(
                rect=pygame.Rect(20, y + 20, self.width - 40, 28),
                label="Тип добываемого ресурса:",
                key="resource_type",
                options=RESOURCE_TYPES,
                selected=self.location_info.get('resource_type', 'copper')
            ))
            self.data['resource_type'] = self.location_info.get('resource_type', 'copper')
            y += 70

        # Animal spawn settings (only for animal spawn points)
        if loc_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            # Animal count slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Количество животных (1-10)",
                key="animal_count",
                value=self.location_info.get('animal_count', 3),
                min_val=1, max_val=10, step=1
            ))
            self.data['animal_count'] = self.location_info.get('animal_count', 3)
            y += 50

            # Respawn time slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Время респавна (0-999 ходов)",
                key="respawn_time",
                value=self.location_info.get('respawn_time', 50),
                min_val=0, max_val=999, step=5
            ))
            self.data['respawn_time'] = self.location_info.get('respawn_time', 50)
            y += 50

            # Spawn radius slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Зона действия (3-10)",
                key="spawn_radius",
                value=self.location_info.get('spawn_radius', 5),
                min_val=3, max_val=10, step=1
            ))
            self.data['spawn_radius'] = self.location_info.get('spawn_radius', 5)
            y += 50

        # Player attitude slider (for all locations)
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y + 20, self.width - 40, 16),
            label="Отношение к игроку (-10 до 10)",
            key="player_attitude",
            value=self.location_info.get('player_attitude', 0),
            min_val=-10, max_val=10, step=1
        ))
        self.data['player_attitude'] = self.location_info.get('player_attitude', 0)
        y += 50

        # Spawn radius slider (for all locations except animal spawns)
        # Animal spawns have their own spawn_radius slider in the animal spawn settings section
        if loc_type not in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Радиус спавна NPC (1-20)",
                key="spawn_radius",
                value=self.location_info.get('spawn_radius', 5),
                min_val=1, max_val=20, step=1
            ))
            self.data['spawn_radius'] = self.location_info.get('spawn_radius', 5)
            y += 50

        # Guards section (for settlements and academies)
        if loc_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                        LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            # Guards title and column headers
            y += 10
            guards = self.location_info.get('guards', [Guard() for _ in range(5)])
            # Ensure we have exactly 5 guards
            while len(guards) < 5:
                guards.append(Guard())

            # Add column headers - store them as a special attribute for rendering
            self._guard_headers_y = y
            self._guard_headers = [
                ("Тип", 20, 180),           # (label, x, width)
                ("Ранг", 210, 80),
                ("Кол-во", 300, 80),
                ("Радиус патр.", 390, 100),  # Patrol radius column
                ("Время респ.", 500, 110)    # Respawn time column
            ]
            y += 25  # Space for headers

            for i in range(5):
                guard = guards[i] if i < len(guards) else Guard()

                # Dropdown for guard type (180px wide)
                self.dropdowns.append(DialogDropdown(
                    rect=pygame.Rect(20, y + 20, 180, 28),
                    label=f"Стража {i+1}:",
                    key=f"guard_{i}_type",
                    options=GUARD_TYPES,
                    selected=guard.guard_type
                ))
                self.data[f"guard_{i}_type"] = guard.guard_type

                # Rank dropdown (80px wide) - changed from text input to dropdown
                rank_options = {
                    "1": "1",
                    "2": "2",
                    "3": "3",
                    "4": "4"
                }
                self.dropdowns.append(DialogDropdown(
                    rect=pygame.Rect(210, y + 20, 80, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_rank",
                    options=rank_options,
                    selected=str(guard.rank)
                ))
                self.data[f"guard_{i}_rank"] = str(guard.rank)

                # Count input (80px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(300, y + 20, 80, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_count",
                    value=str(guard.count),
                    max_length=2
                ))
                self.data[f"guard_{i}_count"] = str(guard.count)

                # Patrol radius input (100px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(390, y + 20, 100, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_patrol_radius",
                    value=str(guard.patrol_radius),
                    max_length=2
                ))
                self.data[f"guard_{i}_patrol_radius"] = str(guard.patrol_radius)

                # Respawn time input (110px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(500, y + 20, 110, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_respawn_time",
                    value=str(guard.respawn_time),
                    max_length=3
                ))
                self.data[f"guard_{i}_respawn_time"] = str(guard.respawn_time)

                y += 45

            y += 5  # Extra spacing after guards section

        # Connections text input (для шахт, деревень и городов)
        if loc_type in [LOCATION_MINE, LOCATION_VILLAGE, LOCATION_CITY]:
            # Форматируем существующие связи для отображения
            connections = self.location_info.get('connections', [])
            connections_str = '; '.join([f"{x},{y}" for x, y in connections])

            self.text_inputs.append(DialogTextInput(
                rect=pygame.Rect(20, y + 20, self.width - 40, 28),
                label="Связи (x,y; x,y):",
                key="connections",
                value=connections_str,
                max_length=100
            ))
            self.data['connections'] = connections_str
            y += 70

        # Quests button (for quest-giving locations)
        if loc_type in QUEST_GIVER_LOCATIONS:
            quests = self.location_info.get('quests', [])
            quest_count = len(quests) if quests else 0
            self.buttons.append(DialogButton(
                rect=pygame.Rect(20, y, 250, 30),
                text=f"Управление квестами ({quest_count})",
                action="edit_quests"
            ))
            y += 45

        # Buttons
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(20, btn_y, btn_width, btn_height),
            text="Удалить",
            action="delete"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with location info."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw coordinates at bottom, above "Delete" button
        # (Location type is now shown in the dialog title)
        btn_height = 30
        btn_y = self.height - btn_height - 15
        coords_y = self.y + btn_y - 30  # 30px above the buttons
        coords_text = f"Координаты: ({self.location_info.get('x', 0)}, {self.location_info.get('y', 0)})"
        coords_surface = self.font.render(coords_text, True, (180, 180, 180))
        surface.blit(coords_surface, (self.x + 20, coords_y))

        # Draw guard column headers if guards section is present
        if self._guard_headers_y is not None and self._guard_headers is not None:
            header_y = self.y + self._guard_headers_y
            for label, col_x, col_width in self._guard_headers:
                # Draw header text
                header_text = self.font.render(label, True, (200, 200, 200))
                surface.blit(header_text, (self.x + col_x, header_y))
                # Draw underline
                pygame.draw.line(surface, (100, 100, 105),
                               (self.x + col_x, header_y + 18),
                               (self.x + col_x + col_width - 5, header_y + 18),
                               1)


# Keep old name for backwards compatibility
ObjectDialog = LocationEditDialog


class SaveDialog(Dialog):
    """Dialog for save confirmation."""

    def __init__(self, filename: str = ""):
        super().__init__("Сохранить карту", 400, 150)
        self.filename = filename
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 3 - 30, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 2 - 20, btn_y, btn_width, btn_height),
            text="Сохранить как...",
            action="save_as"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw filename
        text = f"Файл: {self.filename}" if self.filename else "Новая карта (не сохранена)"
        text_surface = self.font.render(text, True, self.text_color)
        surface.blit(text_surface, (self.x + 20, self.y + 60))


class LoadDialog(Dialog):
    """Dialog for selecting a file to load."""

    def __init__(self, directory: str = ""):
        super().__init__("Открыть карту", 500, 400)
        self.directory = directory or str(Path.home())
        self.files: List[str] = []
        self.selected_file: Optional[str] = None
        self.scroll_offset = 0
        self._scan_files()
        self._setup_controls()

    def _scan_files(self) -> None:
        """Scan directory for map files."""
        try:
            path = Path(self.directory)
            self.files = sorted([
                f.name for f in path.glob("*.json")
                if f.is_file()
            ])
        except Exception:
            self.files = []

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Открыть",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events including file selection."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                local_x = event.pos[0] - self.x
                local_y = event.pos[1] - self.y

                # Check file list area
                list_rect = pygame.Rect(10, 40, self.width - 20, self.height - 100)
                if list_rect.collidepoint(local_x, local_y):
                    # Calculate which file was clicked
                    file_y = local_y - 40 + self.scroll_offset
                    file_idx = file_y // 24
                    if 0 <= file_idx < len(self.files):
                        self.selected_file = self.files[file_idx]
                        self.data['filename'] = str(Path(self.directory) / self.selected_file)
                    return True

            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 24)
                return True
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.files) * 24 - (self.height - 100))
                self.scroll_offset = min(max_scroll, self.scroll_offset + 24)
                return True

        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with file list."""
        super().draw(surface)

        if not self.visible:
            return

        # File list area
        list_rect = pygame.Rect(self.x + 10, self.y + 40, self.width - 20, self.height - 100)
        pygame.draw.rect(surface, self.slider_bg, list_rect, border_radius=4)

        # Draw files
        y = self.y + 44
        for i, filename in enumerate(self.files):
            file_y = y + i * 24 - self.scroll_offset
            if self.y + 40 <= file_y < self.y + self.height - 60:
                # Highlight selected
                if filename == self.selected_file:
                    highlight_rect = pygame.Rect(self.x + 12, file_y - 2, self.width - 24, 22)
                    pygame.draw.rect(surface, self.slider_fill, highlight_rect, border_radius=2)

                text_surface = self.font.render(filename, True, self.text_color)
                surface.blit(text_surface, (self.x + 16, file_y))

        # Border
        pygame.draw.rect(surface, self.border_color, list_rect, width=1, border_radius=4)


class ConfirmDialog(Dialog):
    """Dialog for confirmation with Yes/No buttons."""

    def __init__(self, message: str, title: str = "Подтверждение"):
        super().__init__(title, 400, 180)
        self.message = message
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        # No button (Esc / Right click)
        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 2 - 20, btn_y, btn_width, btn_height),
            text="Нет",
            action="no"
        ))

        # Yes button (Enter / Left click) - primary
        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Да",
            action="yes",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        if not self.visible:
            return False

        # Handle right click as "No"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            self.result = "no"
            self.hide()
            if self.on_close:
                self.on_close("no", self.data)
            return True

        # Call parent handle_event for normal handling
        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw message
        y = self.y + 60
        # Split message into multiple lines if needed
        words = self.message.split(' ')
        lines = []
        current_line = ""
        max_width = self.width - 40

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = self.font.render(test_line, True, self.text_color)
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line in lines:
            text_surface = self.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, y))
            surface.blit(text_surface, text_rect)
            y += 25


class MerchantEditDialog(Dialog):
    """Dialog for editing merchant properties and specializations."""

    # Predefined merchant colors
    MERCHANT_COLORS = [
        ((255, 165, 0), "Оранжевый"),
        ((255, 215, 0), "Золотой"),
        ((138, 43, 226), "Фиолетовый"),
        ((0, 191, 255), "Голубой"),
        ((50, 205, 50), "Зелёный"),
        ((255, 69, 0), "Красный"),
        ((255, 105, 180), "Розовый"),
        ((64, 224, 208), "Бирюзовый")
    ]

    # Specialization rank options (0 = disabled)
    SPEC_RANK_OPTIONS = {
        "0": "Нет",
        "1": "Ранг 1",
        "2": "Ранг 2",
        "3": "Ранг 3",
        "4": "Ранг 4"
    }

    def __init__(self, merchant: Merchant = None, is_new: bool = False):
        self.merchant = merchant or Merchant()
        self.is_new = is_new
        self.waypoints_copy = [MerchantWaypoint(wp.x, wp.y, wp.duration) for wp in self.merchant.waypoints]

        # Dialog size (includes all sliders)
        height = 630
        width = 700

        title = "Создать торговца" if is_new else "Редактировать торговца"
        super().__init__(title, width, height)

        self._color_rects: List[Tuple[pygame.Rect, Tuple[int, int, int]]] = []
        self._selected_color = self.merchant.color
        self._edit_route_rect: Optional[pygame.Rect] = None

        # Callback for opening route edit dialog
        self.on_edit_route: Optional[Callable[[], None]] = None

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        y = 50

        # === ROW 1: Name and Rank ===

        # Name input
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(20, y + 20, 320, 28),
            label="Имя торговца:",
            key="name",
            value=self.merchant.name,
            max_length=40
        ))
        self.data['name'] = self.merchant.name

        # Rank dropdown (right side of name)
        rank_options = {str(k): v for k, v in MERCHANT_RANKS.items()}
        self.dropdowns.append(DialogDropdown(
            rect=pygame.Rect(360, y + 20, 320, 28),
            label="Ранг торговца:",
            key="rank",
            options=rank_options,
            selected=str(self.merchant.rank)
        ))
        self.data['rank'] = str(self.merchant.rank)
        y += 70

        # === ROW 2: Color selection ===
        self.data['color'] = list(self._selected_color)
        y += 50  # Space for color selection

        # === SPECIALIZATIONS SECTION ===
        # Store specializations data
        for spec_key in MERCHANT_SPECIALIZATIONS.keys():
            spec_rank = self.merchant.get_specialization(spec_key)
            self.data[f'spec_{spec_key}'] = str(spec_rank)

        # Create 2 columns of specialization dropdowns
        spec_items = list(MERCHANT_SPECIALIZATIONS.items())
        spec_y = y + 25
        col_width = 330

        for i, (spec_key, spec_name) in enumerate(spec_items):
            col = i % 2
            row = i // 2
            x_pos = 20 + col * col_width
            y_pos = spec_y + row * 50

            self.dropdowns.append(DialogDropdown(
                rect=pygame.Rect(x_pos, y_pos + 20, col_width - 20, 28),
                label=f"{spec_name}:",
                key=f"spec_{spec_key}",
                options=self.SPEC_RANK_OPTIONS,
                selected=str(self.merchant.get_specialization(spec_key))
            ))

        # === SLIDERS SECTION ===
        # Calculate position after specializations (4 rows * 50)
        slider_y = spec_y + 4 * 50 + 10

        # Respawn time slider
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, slider_y + 20, self.width - 40, 16),
            label="Время респавна (ходов)",
            key="respawn_time",
            value=self.merchant.respawn_time,
            min_val=0, max_val=999, step=10
        ))
        self.data['respawn_time'] = self.merchant.respawn_time
        slider_y += 50

        # Assortment update slider
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, slider_y + 20, self.width - 40, 16),
            label="Обновление ассортимента (ходов)",
            key="assortment_update",
            value=self.merchant.assortment_update,
            min_val=10, max_val=1000, step=10
        ))
        self.data['assortment_update'] = self.merchant.assortment_update
        slider_y += 50

        # Wealth slider
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, slider_y + 20, self.width - 40, 16),
            label="Состояние (золото)",
            key="wealth",
            value=self.merchant.wealth,
            min_val=1000, max_val=50000, step=500
        ))
        self.data['wealth'] = self.merchant.wealth

        # Buttons at the bottom
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        if not self.is_new:
            self.buttons.append(DialogButton(
                rect=pygame.Rect(20, btn_y, btn_width, btn_height),
                text="Удалить",
                action="delete"
            ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check color selection
            for rect, color in self._color_rects:
                if rect.collidepoint(local_x, local_y):
                    self._selected_color = color
                    self.data['color'] = list(color)
                    return True

            # Check route edit button
            if self._edit_route_rect and self._edit_route_rect.collidepoint(local_x, local_y):
                if self.on_edit_route:
                    self.on_edit_route()
                return True

        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with merchant-specific elements."""
        super().draw(surface)

        if not self.visible:
            return

        # === Draw color selection ===
        y = self.y + 120
        color_label = self.font.render("Цвет маркера:", True, self.text_color)
        surface.blit(color_label, (self.x + 20, y))

        self._color_rects = []
        color_size = 22
        padding = 6
        x_offset = self.x + 20
        y += 20

        for color, name in self.MERCHANT_COLORS:
            rect = pygame.Rect(x_offset, y, color_size, color_size)
            self._color_rects.append((pygame.Rect(x_offset - self.x, y - self.y, color_size, color_size), color))

            pygame.draw.rect(surface, color, rect, border_radius=3)
            if color == self._selected_color:
                pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=3)
            else:
                pygame.draw.rect(surface, (80, 80, 80), rect, width=1, border_radius=3)

            x_offset += color_size + padding

        # === Edit route button (right side of color selection) ===
        route_btn_rect = pygame.Rect(self.x + 360, y, 180, 26)
        self._edit_route_rect = pygame.Rect(360, y - self.y, 180, 26)
        pygame.draw.rect(surface, (45, 70, 130), route_btn_rect, border_radius=3)

        # Show waypoints count
        wp_count = len(self.waypoints_copy)
        route_text = f"Маршрут ({wp_count} точек)"
        route_text_surface = self.font.render(route_text, True, (255, 255, 255))
        route_text_rect = route_text_surface.get_rect(center=route_btn_rect.center)
        surface.blit(route_text_surface, route_text_rect)

        # === Draw specializations header ===
        y = self.y + 165
        spec_label = self.font.render("Специализации товаров:", True, self.text_color)
        surface.blit(spec_label, (self.x + 20, y))

        # IMPORTANT: Redraw ALL expanded dropdowns LAST to fix z-order issue
        for dropdown in self.dropdowns:
            if dropdown.expanded:
                self._draw_dropdown(surface, dropdown)

    def get_merchant(self) -> Merchant:
        """Get the edited merchant with updated values."""
        name = self.data.get('name', '').strip()
        rank = int(self.data.get('rank', '1'))
        color_data = self.data.get('color', [255, 165, 0])
        respawn_time = int(self.data.get('respawn_time', 200))
        assortment_update = int(self.data.get('assortment_update', 100))
        wealth = int(self.data.get('wealth', 3000))

        if isinstance(color_data, (list, tuple)):
            color = tuple(int(c) for c in color_data[:3])
        else:
            color = (255, 165, 0)

        # Update merchant basic properties
        self.merchant.name = name if name else "Торговец"
        self.merchant.rank = max(1, min(4, rank))
        self.merchant.color = color
        self.merchant.waypoints = self.waypoints_copy
        self.merchant.respawn_time = max(0, min(999, respawn_time))
        self.merchant.assortment_update = max(10, min(1000, assortment_update))
        self.merchant.wealth = max(1000, min(50000, wealth))

        # Update specializations
        for spec_key in MERCHANT_SPECIALIZATIONS.keys():
            spec_rank = int(self.data.get(f'spec_{spec_key}', '0'))
            self.merchant.set_specialization(spec_key, spec_rank)

        return self.merchant

    def update_waypoints(self, waypoints: List[MerchantWaypoint], is_loop: bool) -> None:
        """Update waypoints from route dialog."""
        self.waypoints_copy = waypoints
        self.merchant.is_loop = is_loop


class RouteEditDialog(Dialog):
    """Dialog for editing merchant route waypoints."""

    def __init__(self, waypoints: List[MerchantWaypoint] = None, is_loop: bool = True):
        self.waypoints_copy = [MerchantWaypoint(wp.x, wp.y, wp.duration) for wp in (waypoints or [])]
        self.is_loop = is_loop

        # Dialog size
        height = 480
        width = 420
        super().__init__("Маршрут", width, height)

        self._waypoint_delete_rects: List[Tuple[pygame.Rect, int]] = []
        self._waypoint_duration_rects: List[Tuple[pygame.Rect, int]] = []
        self._add_waypoint_rect: Optional[pygame.Rect] = None
        self._add_waypoint_on_map_rect: Optional[pygame.Rect] = None
        self._editing_duration_idx: Optional[int] = None
        self._duration_input_value: str = ""

        # Scroll offset for waypoints list
        self._waypoints_scroll_offset = 0
        self._waypoints_visible_count = 10  # Visible waypoints

        # Callback for adding waypoints on map
        self.on_add_waypoints_on_map: Optional[Callable[[], None]] = None

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        # Store waypoints data
        for i, wp in enumerate(self.waypoints_copy):
            self.data[f'wp_{i}_x'] = str(wp.x)
            self.data[f'wp_{i}_y'] = str(wp.y)
            self.data[f'wp_{i}_duration'] = str(wp.duration)

        # Is loop checkbox
        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, 45, 200, 20),
            label="Замкнутый маршрут",
            key="is_loop",
            checked=self.is_loop
        ))
        self.data['is_loop'] = self.is_loop

        # Buttons at the bottom
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom waypoint handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check waypoint duration editing
            for rect, idx in self._waypoint_duration_rects:
                if rect.collidepoint(local_x, local_y):
                    self._editing_duration_idx = idx
                    if 0 <= idx < len(self.waypoints_copy):
                        self._duration_input_value = str(self.waypoints_copy[idx].duration)
                    return True

            # Check waypoint delete buttons
            for rect, idx in self._waypoint_delete_rects:
                if rect.collidepoint(local_x, local_y):
                    if 0 <= idx < len(self.waypoints_copy):
                        self.waypoints_copy.pop(idx)
                        self._update_waypoints_data()
                        # Adjust scroll if needed
                        max_scroll = max(0, len(self.waypoints_copy) - self._waypoints_visible_count)
                        if self._waypoints_scroll_offset > max_scroll:
                            self._waypoints_scroll_offset = max_scroll
                    return True

            # Check add waypoint button
            if self._add_waypoint_rect and self._add_waypoint_rect.collidepoint(local_x, local_y):
                self.waypoints_copy.append(MerchantWaypoint(x=0, y=0, duration=10))
                self._update_waypoints_data()
                return True

            # Check "Add waypoints on map" button
            if self._add_waypoint_on_map_rect and self._add_waypoint_on_map_rect.collidepoint(local_x, local_y):
                if self.on_add_waypoints_on_map:
                    self.on_add_waypoints_on_map()
                return True

            # Click elsewhere - stop duration editing
            if self._editing_duration_idx is not None:
                self._apply_duration_edit()
                self._editing_duration_idx = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            # Scroll waypoints list
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check if in waypoints area
            if 20 <= local_x <= self.width - 20 and 70 <= local_y <= 380:
                max_scroll = max(0, len(self.waypoints_copy) - self._waypoints_visible_count)
                if event.button == 4:  # Scroll up
                    self._waypoints_scroll_offset = max(0, self._waypoints_scroll_offset - 1)
                else:  # Scroll down
                    self._waypoints_scroll_offset = min(max_scroll, self._waypoints_scroll_offset + 1)
                return True

        elif event.type == pygame.KEYDOWN and self._editing_duration_idx is not None:
            # Handle duration input
            if event.key == pygame.K_RETURN:
                self._apply_duration_edit()
                self._editing_duration_idx = None
                return True
            elif event.key == pygame.K_ESCAPE:
                self._editing_duration_idx = None
                return True
            elif event.key == pygame.K_BACKSPACE:
                self._duration_input_value = self._duration_input_value[:-1]
                return True
            elif event.unicode.isdigit() and len(self._duration_input_value) < 4:
                self._duration_input_value += event.unicode
                return True
            return True

        return super().handle_event(event)

    def _apply_duration_edit(self) -> None:
        """Apply the duration edit to the waypoint."""
        if self._editing_duration_idx is not None and 0 <= self._editing_duration_idx < len(self.waypoints_copy):
            try:
                duration = int(self._duration_input_value) if self._duration_input_value else 10
                duration = max(1, min(999, duration))
                self.waypoints_copy[self._editing_duration_idx].duration = duration
                self._update_waypoints_data()
            except ValueError:
                pass

    def _update_waypoints_data(self) -> None:
        """Update waypoints data dictionary."""
        keys_to_remove = [k for k in self.data.keys() if k.startswith('wp_')]
        for k in keys_to_remove:
            del self.data[k]

        for i, wp in enumerate(self.waypoints_copy):
            self.data[f'wp_{i}_x'] = str(wp.x)
            self.data[f'wp_{i}_y'] = str(wp.y)
            self.data[f'wp_{i}_duration'] = str(wp.duration)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with waypoints list."""
        super().draw(surface)

        if not self.visible:
            return

        # === Draw waypoints section ===
        y = self.y + 75
        waypoints_label = self.font.render("Точки маршрута:", True, self.text_color)
        surface.blit(waypoints_label, (self.x + 20, y))

        # Route closed indicator
        if len(self.waypoints_copy) >= 2:
            is_closed = (self.waypoints_copy[0].x == self.waypoints_copy[-1].x and
                        self.waypoints_copy[0].y == self.waypoints_copy[-1].y)
            if is_closed:
                closed_text = self.font.render("(маршрут замкнут)", True, (100, 200, 100))
                surface.blit(closed_text, (self.x + 150, y))

        y += 20

        self._waypoint_delete_rects = []
        self._waypoint_duration_rects = []

        if not self.waypoints_copy:
            no_wp_text = self.font.render("Нет точек маршрута", True, (150, 150, 150))
            surface.blit(no_wp_text, (self.x + 20, y))
            y += 20
        else:
            # Header row
            header_x = self.x + 20
            headers = [("№", 30), ("X", 55), ("Y", 55), ("Остановка", 75), ("", 25)]
            for header, width in headers:
                header_surface = self.font.render(header, True, (180, 180, 180))
                surface.blit(header_surface, (header_x, y))
                header_x += width
            y += 20

            # Waypoint rows with scroll
            visible_waypoints = self.waypoints_copy[self._waypoints_scroll_offset:
                                                    self._waypoints_scroll_offset + self._waypoints_visible_count]

            for display_idx, wp in enumerate(visible_waypoints):
                actual_idx = display_idx + self._waypoints_scroll_offset
                row_x = self.x + 20

                # Number
                num_surface = self.font.render(f"{actual_idx + 1}.", True, self.text_color)
                surface.blit(num_surface, (row_x, y + 4))
                row_x += 30

                # X value
                x_rect = pygame.Rect(row_x, y, 48, 22)
                pygame.draw.rect(surface, (45, 45, 50), x_rect, border_radius=3)
                pygame.draw.rect(surface, (60, 60, 65), x_rect, width=1, border_radius=3)
                x_text = self.font.render(str(wp.x), True, self.text_color)
                surface.blit(x_text, (x_rect.x + 4, x_rect.y + 4))
                row_x += 55

                # Y value
                y_rect = pygame.Rect(row_x, y, 48, 22)
                pygame.draw.rect(surface, (45, 45, 50), y_rect, border_radius=3)
                pygame.draw.rect(surface, (60, 60, 65), y_rect, width=1, border_radius=3)
                y_text = self.font.render(str(wp.y), True, self.text_color)
                surface.blit(y_text, (y_rect.x + 4, y_rect.y + 4))
                row_x += 55

                # Duration (editable)
                dur_rect = pygame.Rect(row_x, y, 65, 22)
                self._waypoint_duration_rects.append((pygame.Rect(row_x - self.x, y - self.y, 65, 22), actual_idx))

                if self._editing_duration_idx == actual_idx:
                    pygame.draw.rect(surface, (60, 60, 70), dur_rect, border_radius=3)
                    pygame.draw.rect(surface, (0, 122, 204), dur_rect, width=2, border_radius=3)
                    dur_text = self.font.render(self._duration_input_value + "|", True, self.text_color)
                else:
                    pygame.draw.rect(surface, (45, 45, 50), dur_rect, border_radius=3)
                    pygame.draw.rect(surface, (60, 60, 65), dur_rect, width=1, border_radius=3)
                    dur_text = self.font.render(str(wp.duration), True, self.text_color)
                surface.blit(dur_text, (dur_rect.x + 4, dur_rect.y + 4))
                row_x += 75

                # Delete button
                del_rect = pygame.Rect(row_x, y, 22, 22)
                self._waypoint_delete_rects.append((pygame.Rect(row_x - self.x, y - self.y, 22, 22), actual_idx))
                pygame.draw.rect(surface, (140, 45, 45), del_rect, border_radius=3)
                del_text = self.font.render("X", True, (255, 255, 255))
                del_text_rect = del_text.get_rect(center=del_rect.center)
                surface.blit(del_text, del_text_rect)

                y += 26

            # Draw scroll indicator if needed
            if len(self.waypoints_copy) > self._waypoints_visible_count:
                scroll_text = f"({self._waypoints_scroll_offset + 1}-{min(self._waypoints_scroll_offset + self._waypoints_visible_count, len(self.waypoints_copy))} из {len(self.waypoints_copy)})"
                scroll_surface = self.font.render(scroll_text, True, (150, 150, 150))
                surface.blit(scroll_surface, (self.x + 260, self.y + 75))

        # Add waypoint buttons
        y = self.y + 390

        add_btn_rect = pygame.Rect(self.x + 20, y, 130, 26)
        self._add_waypoint_rect = pygame.Rect(20, y - self.y, 130, 26)
        pygame.draw.rect(surface, (45, 100, 45), add_btn_rect, border_radius=3)
        add_text = self.font.render("+ Добавить", True, (255, 255, 255))
        add_text_rect = add_text.get_rect(center=add_btn_rect.center)
        surface.blit(add_text, add_text_rect)

        map_btn_rect = pygame.Rect(self.x + 170, y, 160, 26)
        self._add_waypoint_on_map_rect = pygame.Rect(170, y - self.y, 160, 26)
        pygame.draw.rect(surface, (45, 70, 130), map_btn_rect, border_radius=3)
        map_text = self.font.render("Добавить на карте", True, (255, 255, 255))
        map_text_rect = map_text.get_rect(center=map_btn_rect.center)
        surface.blit(map_text, map_text_rect)

        # Hint
        y += 30
        hint_text = self.font.render("Клик на время для редактирования", True, (130, 130, 130))
        surface.blit(hint_text, (self.x + 20, y))

    def get_waypoints(self) -> List[MerchantWaypoint]:
        """Get the edited waypoints list."""
        return self.waypoints_copy

    def get_is_loop(self) -> bool:
        """Get the is_loop value."""
        return self.data.get('is_loop', True)

    def add_waypoint_from_map(self, x: int, y: int, duration: int = 10) -> None:
        """Add a waypoint from map click."""
        self.waypoints_copy.append(MerchantWaypoint(x=x, y=y, duration=duration))
        self._update_waypoints_data()


class FloorEditDialog(Dialog):
    """Dialog for editing floors in mines and ruins."""

    # Size options (1-10)
    SIZE_OPTIONS = {str(i): str(i) for i in range(1, 11)}

    def __init__(self, floors: List[Floor] = None):
        """Initialize floor edit dialog."""
        # Deep copy floors with their NPCs
        self.floors_copy = []
        for f in (floors or []):
            floor_copy = Floor(
                floor_number=f.floor_number,
                floor_type=f.floor_type,
                size=f.size,
                npcs=[FloorNPC(npc_type=npc.npc_type, rank=npc.rank, count=npc.count)
                      for npc in f.npcs]
            )
            self.floors_copy.append(floor_copy)

        # Ensure we have 10 floors
        existing_nums = {f.floor_number for f in self.floors_copy}
        for i in range(1, 11):
            if i not in existing_nums:
                self.floors_copy.append(Floor(floor_number=i))
        self.floors_copy.sort(key=lambda f: f.floor_number)

        # Dialog size (10 floors * 40 + headers + buttons + padding)
        height = 540
        width = 620  # Wider for NPC column with button
        super().__init__("Редактирование этажей", width, height)

        self._scroll_offset = 0
        self._visible_count = 10  # All floors visible

        # NPC edit button rectangles for click detection
        self._npc_edit_rects: List[Tuple[pygame.Rect, int]] = []

        # Callback for opening NPC edit dialog
        self.on_edit_npc: Optional[Callable[[Floor, int], None]] = None

        # Currently editing floor (for NPC dialog)
        self._editing_floor_idx: Optional[int] = None

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        # Store floors data
        for floor in self.floors_copy:
            self.data[f'floor_{floor.floor_number}_type'] = floor.floor_type
            self.data[f'floor_{floor.floor_number}_size'] = str(floor.size)

        # Buttons at the bottom
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom floor handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # FIRST: Check dropdown options if any is active (must be checked before triggers)
            if hasattr(self, '_active_dropdown') and self._active_dropdown:
                if self._active_dropdown.startswith('dropdown_floor_'):
                    floor_num = int(self._active_dropdown.split('_')[-1])
                    floor_idx = floor_num - 1
                    row_y = 75 + floor_idx * 40
                    option_y = row_y + 28

                    # Check if click is within options area
                    options_height = len(FLOOR_TYPES) * 28
                    options_rect = pygame.Rect(70, option_y, 180, options_height)
                    if options_rect.collidepoint(local_x, local_y):
                        for i, (key, value) in enumerate(FLOOR_TYPES.items()):
                            option_rect = pygame.Rect(70, option_y + i * 28, 180, 28)
                            if option_rect.collidepoint(local_x, local_y):
                                self.floors_copy[floor_idx].floor_type = key
                                self.data[f'floor_{floor_num}_type'] = key
                                self._active_dropdown = None
                                return True

                elif self._active_dropdown.startswith('dropdown_size_'):
                    floor_num = int(self._active_dropdown.split('_')[-1])
                    floor_idx = floor_num - 1
                    row_y = 75 + floor_idx * 40
                    option_y = row_y + 28

                    # Check if click is within options area
                    options_height = len(self.SIZE_OPTIONS) * 28
                    options_rect = pygame.Rect(260, option_y, 80, options_height)
                    if options_rect.collidepoint(local_x, local_y):
                        for i, (key, value) in enumerate(self.SIZE_OPTIONS.items()):
                            option_rect = pygame.Rect(260, option_y + i * 28, 80, 28)
                            if option_rect.collidepoint(local_x, local_y):
                                self.floors_copy[floor_idx].size = int(key)
                                self.data[f'floor_{floor_num}_size'] = key
                                self._active_dropdown = None
                                return True

                # Close dropdown if clicked outside options
                self._active_dropdown = None
                return True

            # SECOND: Check floor type dropdown triggers
            for i, floor in enumerate(self.floors_copy):
                row_y = 75 + i * 40

                # Type dropdown area
                type_rect = pygame.Rect(70, row_y, 180, 28)
                if type_rect.collidepoint(local_x, local_y):
                    # Toggle dropdown for this floor
                    floor_key = f'dropdown_floor_{floor.floor_number}'
                    if hasattr(self, '_active_dropdown') and self._active_dropdown == floor_key:
                        self._active_dropdown = None
                    else:
                        self._active_dropdown = floor_key
                    return True

                # Size dropdown area
                size_rect = pygame.Rect(260, row_y, 80, 28)
                if size_rect.collidepoint(local_x, local_y):
                    floor_key = f'dropdown_size_{floor.floor_number}'
                    if hasattr(self, '_active_dropdown') and self._active_dropdown == floor_key:
                        self._active_dropdown = None
                    else:
                        self._active_dropdown = floor_key
                    return True

                # NPC edit button area
                npc_rect = pygame.Rect(350, row_y, 120, 28)
                if npc_rect.collidepoint(local_x, local_y):
                    # Store the floor index for NPC editing
                    self._editing_floor_idx = i
                    # Call callback if set
                    if self.on_edit_npc:
                        self.on_edit_npc(floor, floor.floor_number)
                    return True

        return super().handle_event(event)

    def update_floor_npcs(self, floor_number: int, npcs: List[FloorNPC]) -> None:
        """Update NPCs for a specific floor."""
        for floor in self.floors_copy:
            if floor.floor_number == floor_number:
                floor.npcs = npcs
                break

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with floors table."""
        super().draw(surface)

        if not self.visible:
            return

        # Initialize active dropdown if not exists
        if not hasattr(self, '_active_dropdown'):
            self._active_dropdown = None

        # Draw table header
        y = self.y + 50
        headers = [("Этаж", 20, 45), ("Тип этажа", 70, 180), ("Размер", 260, 80), ("NPC", 350, 120)]
        for label, col_x, col_width in headers:
            header_text = self.font.render(label, True, (200, 200, 200))
            surface.blit(header_text, (self.x + col_x, y))
            # Draw underline
            pygame.draw.line(surface, (100, 100, 105),
                           (self.x + col_x, y + 18),
                           (self.x + col_x + col_width - 5, y + 18), 1)

        # Draw floor rows
        y = self.y + 75
        for floor in self.floors_copy:
            row_y = y + (floor.floor_number - 1) * 40

            # Floor number (read-only)
            num_text = self.font.render(str(floor.floor_number), True, self.text_color)
            surface.blit(num_text, (self.x + 20, row_y + 6))

            # Floor type dropdown
            type_rect = pygame.Rect(self.x + 70, row_y, 180, 28)
            is_type_active = self._active_dropdown == f'dropdown_floor_{floor.floor_number}'
            bg_color = (60, 60, 65) if is_type_active else (45, 45, 50)
            pygame.draw.rect(surface, bg_color, type_rect, border_radius=3)
            pygame.draw.rect(surface, (80, 80, 85), type_rect, width=1, border_radius=3)

            type_display = FLOOR_TYPES.get(floor.floor_type, "Нет")
            type_text = self.font.render(type_display, True, self.text_color)
            surface.blit(type_text, (type_rect.x + 6, type_rect.y + 6))

            # Arrow
            arrow = "▼" if not is_type_active else "▲"
            arrow_text = self.font.render(arrow, True, self.text_color)
            surface.blit(arrow_text, (type_rect.right - 18, type_rect.y + 6))

            # Size dropdown
            size_rect = pygame.Rect(self.x + 260, row_y, 80, 28)
            is_size_active = self._active_dropdown == f'dropdown_size_{floor.floor_number}'
            bg_color = (60, 60, 65) if is_size_active else (45, 45, 50)
            pygame.draw.rect(surface, bg_color, size_rect, border_radius=3)
            pygame.draw.rect(surface, (80, 80, 85), size_rect, width=1, border_radius=3)

            size_text = self.font.render(str(floor.size), True, self.text_color)
            surface.blit(size_text, (size_rect.x + 6, size_rect.y + 6))

            # Arrow
            arrow = "▼" if not is_size_active else "▲"
            arrow_text = self.font.render(arrow, True, self.text_color)
            surface.blit(arrow_text, (size_rect.right - 18, size_rect.y + 6))

            # NPC edit button (clickable)
            npc_rect = pygame.Rect(self.x + 350, row_y, 120, 28)
            # Check if floor is empty (no type set)
            if floor.is_empty():
                # Disabled style for empty floors
                pygame.draw.rect(surface, (35, 35, 40), npc_rect, border_radius=3)
                pygame.draw.rect(surface, (50, 50, 55), npc_rect, width=1, border_radius=3)
                npc_text = self.font.render("-", True, (80, 80, 80))
            else:
                # Enabled style - button-like appearance
                has_npcs = len(floor.npcs) > 0 and floor.get_total_npc_count() > 0
                if has_npcs:
                    # Green-ish background if NPCs are configured
                    pygame.draw.rect(surface, (40, 60, 45), npc_rect, border_radius=3)
                    pygame.draw.rect(surface, (70, 100, 75), npc_rect, width=1, border_radius=3)
                else:
                    # Normal button style
                    pygame.draw.rect(surface, (50, 50, 55), npc_rect, border_radius=3)
                    pygame.draw.rect(surface, (80, 80, 85), npc_rect, width=1, border_radius=3)

                # Show NPC summary or "Добавить"
                npc_summary = floor.get_npc_summary()
                if npc_summary == "-":
                    npc_text = self.font.render("+ Добавить", True, (150, 150, 150))
                else:
                    npc_text = self.font.render(npc_summary, True, self.text_color)
            surface.blit(npc_text, (npc_rect.x + 6, npc_rect.y + 6))

        # Draw dropdown options if active (must be drawn last to be on top)
        if self._active_dropdown:
            if self._active_dropdown.startswith('dropdown_floor_'):
                floor_num = int(self._active_dropdown.split('_')[-1])
                floor_idx = floor_num - 1
                row_y = self.y + 75 + floor_idx * 40
                option_y = row_y + 28

                # Draw options background
                options_height = len(FLOOR_TYPES) * 28
                options_rect = pygame.Rect(self.x + 70, option_y, 180, options_height)
                pygame.draw.rect(surface, (50, 50, 55), options_rect)
                pygame.draw.rect(surface, (80, 80, 85), options_rect, width=1)

                for i, (key, value) in enumerate(FLOOR_TYPES.items()):
                    opt_rect = pygame.Rect(self.x + 70, option_y + i * 28, 180, 28)
                    if key == self.floors_copy[floor_idx].floor_type:
                        pygame.draw.rect(surface, (70, 70, 80), opt_rect)
                    opt_text = self.font.render(value, True, self.text_color)
                    surface.blit(opt_text, (opt_rect.x + 6, opt_rect.y + 6))

            elif self._active_dropdown.startswith('dropdown_size_'):
                floor_num = int(self._active_dropdown.split('_')[-1])
                floor_idx = floor_num - 1
                row_y = self.y + 75 + floor_idx * 40
                option_y = row_y + 28

                # Draw options background
                options_height = len(self.SIZE_OPTIONS) * 28
                options_rect = pygame.Rect(self.x + 260, option_y, 80, options_height)
                pygame.draw.rect(surface, (50, 50, 55), options_rect)
                pygame.draw.rect(surface, (80, 80, 85), options_rect, width=1)

                for i, (key, value) in enumerate(self.SIZE_OPTIONS.items()):
                    opt_rect = pygame.Rect(self.x + 260, option_y + i * 28, 80, 28)
                    if int(key) == self.floors_copy[floor_idx].size:
                        pygame.draw.rect(surface, (70, 70, 80), opt_rect)
                    opt_text = self.font.render(value, True, self.text_color)
                    surface.blit(opt_text, (opt_rect.x + 6, opt_rect.y + 6))

    def get_floors(self) -> List[Floor]:
        """Get the edited floors list."""
        return self.floors_copy


class FloorNPCEditDialog(Dialog):
    """Dialog for editing NPCs on a specific floor."""

    # NPC type dropdown options (filtered from FLOOR_NPC_TYPES, excluding empty)
    NPC_TYPE_OPTIONS = {k: v for k, v in FLOOR_NPC_TYPES.items() if k != FLOOR_NPC_NONE}

    # Rank dropdown options
    RANK_OPTIONS = {str(k): v for k, v in FLOOR_NPC_RANKS.items()}

    def __init__(self, floor: Floor, floor_number: int):
        """Initialize NPC edit dialog for a floor."""
        self.floor = floor
        self.floor_number = floor_number
        # Create a copy of NPCs for editing
        self.npcs_copy = [FloorNPC(npc_type=npc.npc_type, rank=npc.rank, count=npc.count)
                         for npc in floor.npcs]

        # Dialog size
        height = 520
        width = 600
        super().__init__(f"NPC на этаже {floor_number}", width, height)

        self._scroll_offset = 0
        self._visible_count = 8  # Max visible NPCs
        self._npc_delete_rects: List[Tuple[pygame.Rect, int]] = []
        self._add_npc_rect: Optional[pygame.Rect] = None

        # Active dropdown tracking
        self._active_dropdown_type: Optional[int] = None  # Index of NPC with active type dropdown
        self._active_dropdown_rank: Optional[int] = None  # Index of NPC with active rank dropdown

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        # Buttons at the bottom
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(20, btn_y, 120, btn_height),
            text="Очистить всё",
            action="clear"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom NPC handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # First check if clicking on expanded dropdown options
            if self._active_dropdown_type is not None:
                idx = self._active_dropdown_type
                row_y = 95 + (idx - self._scroll_offset) * 36
                option_y = row_y + 28
                options_rect = pygame.Rect(20, option_y, 200, len(self.NPC_TYPE_OPTIONS) * 28)
                if options_rect.collidepoint(local_x, local_y):
                    for i, (key, value) in enumerate(self.NPC_TYPE_OPTIONS.items()):
                        opt_rect = pygame.Rect(20, option_y + i * 28, 200, 28)
                        if opt_rect.collidepoint(local_x, local_y):
                            self.npcs_copy[idx].npc_type = key
                            self._active_dropdown_type = None
                            return True
                self._active_dropdown_type = None
                return True

            if self._active_dropdown_rank is not None:
                idx = self._active_dropdown_rank
                row_y = 95 + (idx - self._scroll_offset) * 36
                option_y = row_y + 28
                options_rect = pygame.Rect(230, option_y, 80, len(self.RANK_OPTIONS) * 28)
                if options_rect.collidepoint(local_x, local_y):
                    for i, (key, value) in enumerate(self.RANK_OPTIONS.items()):
                        opt_rect = pygame.Rect(230, option_y + i * 28, 80, 28)
                        if opt_rect.collidepoint(local_x, local_y):
                            self.npcs_copy[idx].rank = int(key)
                            self._active_dropdown_rank = None
                            return True
                self._active_dropdown_rank = None
                return True

            # Check NPC row interactions
            for display_idx in range(min(self._visible_count, len(self.npcs_copy) - self._scroll_offset)):
                actual_idx = display_idx + self._scroll_offset
                row_y = 95 + display_idx * 36

                # Type dropdown (column 1)
                type_rect = pygame.Rect(20, row_y, 200, 28)
                if type_rect.collidepoint(local_x, local_y):
                    self._active_dropdown_type = actual_idx
                    self._active_dropdown_rank = None
                    return True

                # Rank dropdown (column 2)
                rank_rect = pygame.Rect(230, row_y, 80, 28)
                if rank_rect.collidepoint(local_x, local_y):
                    self._active_dropdown_rank = actual_idx
                    self._active_dropdown_type = None
                    return True

                # Count +/- buttons (column 3)
                # - button
                minus_rect = pygame.Rect(322, row_y + 2, 20, 24)
                if minus_rect.collidepoint(local_x, local_y):
                    if self.npcs_copy[actual_idx].count > 1:
                        self.npcs_copy[actual_idx].count -= 1
                    return True

                # + button
                plus_rect = pygame.Rect(378, row_y + 2, 20, 24)
                if plus_rect.collidepoint(local_x, local_y):
                    if self.npcs_copy[actual_idx].count < 99:
                        self.npcs_copy[actual_idx].count += 1
                    return True

            # Check delete buttons
            for rect, idx in self._npc_delete_rects:
                if rect.collidepoint(local_x, local_y):
                    if 0 <= idx < len(self.npcs_copy):
                        self.npcs_copy.pop(idx)
                        # Adjust scroll if needed
                        max_scroll = max(0, len(self.npcs_copy) - self._visible_count)
                        if self._scroll_offset > max_scroll:
                            self._scroll_offset = max_scroll
                    return True

            # Check add NPC button
            if self._add_npc_rect and self._add_npc_rect.collidepoint(local_x, local_y):
                # Add new empty NPC slot
                self.npcs_copy.append(FloorNPC(npc_type="miner", rank=1, count=1))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Scroll NPC list
            if 20 <= local_x <= self.width - 20 and 70 <= local_y <= 400:
                max_scroll = max(0, len(self.npcs_copy) - self._visible_count)
                if event.button == 4:  # Scroll up
                    self._scroll_offset = max(0, self._scroll_offset - 1)
                else:  # Scroll down
                    self._scroll_offset = min(max_scroll, self._scroll_offset + 1)
                return True

        elif event.type == pygame.KEYDOWN:
            # Handle keyboard input for count editing
            pass

        # Handle button clear action
        result = super().handle_event(event)
        if self.result == "clear":
            self.npcs_copy = []
            self.result = None
            self.visible = True
            return True

        return result

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with NPC list."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw header
        y = self.y + 50
        header_text = self.font.render(f"Всего NPC: {sum(npc.count for npc in self.npcs_copy if not npc.is_empty())}",
                                       True, self.text_color)
        surface.blit(header_text, (self.x + 20, y))

        # Draw table header
        y = self.y + 75
        headers = [("Тип NPC", 20, 200), ("Ранг", 230, 80), ("Кол-во", 320, 80), ("", 410, 30)]
        for label, col_x, col_width in headers:
            header_text = self.font.render(label, True, (200, 200, 200))
            surface.blit(header_text, (self.x + col_x, y))
            pygame.draw.line(surface, (100, 100, 105),
                           (self.x + col_x, y + 18),
                           (self.x + col_x + col_width - 5, y + 18), 1)

        # Draw NPC rows
        self._npc_delete_rects = []
        y = self.y + 95

        if not self.npcs_copy:
            no_npc_text = self.font.render("Нет NPC. Нажмите '+ Добавить' для добавления.", True, (150, 150, 150))
            surface.blit(no_npc_text, (self.x + 20, y))
        else:
            visible_npcs = self.npcs_copy[self._scroll_offset:self._scroll_offset + self._visible_count]

            for display_idx, npc in enumerate(visible_npcs):
                actual_idx = display_idx + self._scroll_offset
                row_y = y + display_idx * 36

                # Type dropdown
                type_rect = pygame.Rect(self.x + 20, row_y, 200, 28)
                is_type_active = self._active_dropdown_type == actual_idx
                bg_color = (60, 60, 65) if is_type_active else (45, 45, 50)
                pygame.draw.rect(surface, bg_color, type_rect, border_radius=3)
                pygame.draw.rect(surface, (80, 80, 85), type_rect, width=1, border_radius=3)

                type_display = FLOOR_NPC_TYPES.get(npc.npc_type, npc.npc_type)
                type_text = self.font.render(type_display, True, self.text_color)
                surface.blit(type_text, (type_rect.x + 6, type_rect.y + 6))

                arrow = "▼" if not is_type_active else "▲"
                arrow_text = self.font.render(arrow, True, self.text_color)
                surface.blit(arrow_text, (type_rect.right - 18, type_rect.y + 6))

                # Rank dropdown
                rank_rect = pygame.Rect(self.x + 230, row_y, 80, 28)
                is_rank_active = self._active_dropdown_rank == actual_idx
                bg_color = (60, 60, 65) if is_rank_active else (45, 45, 50)
                pygame.draw.rect(surface, bg_color, rank_rect, border_radius=3)
                pygame.draw.rect(surface, (80, 80, 85), rank_rect, width=1, border_radius=3)

                rank_text = self.font.render(str(npc.rank), True, self.text_color)
                surface.blit(rank_text, (rank_rect.x + 6, rank_rect.y + 6))

                arrow = "▼" if not is_rank_active else "▲"
                arrow_text = self.font.render(arrow, True, self.text_color)
                surface.blit(arrow_text, (rank_rect.right - 18, rank_rect.y + 6))

                # Count input (editable with +/- buttons)
                count_rect = pygame.Rect(self.x + 320, row_y, 80, 28)
                pygame.draw.rect(surface, (45, 45, 50), count_rect, border_radius=3)
                pygame.draw.rect(surface, (80, 80, 85), count_rect, width=1, border_radius=3)

                # - button
                minus_rect = pygame.Rect(self.x + 322, row_y + 2, 20, 24)
                pygame.draw.rect(surface, (80, 50, 50), minus_rect, border_radius=2)
                minus_text = self.font.render("-", True, (255, 255, 255))
                minus_text_rect = minus_text.get_rect(center=minus_rect.center)
                surface.blit(minus_text, minus_text_rect)

                # Count value
                count_text = self.font.render(str(npc.count), True, self.text_color)
                count_text_rect = count_text.get_rect(center=(count_rect.centerx, count_rect.centery))
                surface.blit(count_text, count_text_rect)

                # + button
                plus_rect = pygame.Rect(self.x + 378, row_y + 2, 20, 24)
                pygame.draw.rect(surface, (50, 80, 50), plus_rect, border_radius=2)
                plus_text = self.font.render("+", True, (255, 255, 255))
                plus_text_rect = plus_text.get_rect(center=plus_rect.center)
                surface.blit(plus_text, plus_text_rect)

                # Delete button
                del_rect = pygame.Rect(self.x + 410, row_y + 2, 24, 24)
                self._npc_delete_rects.append((pygame.Rect(410, row_y + 2 - self.y, 24, 24), actual_idx))
                pygame.draw.rect(surface, (140, 45, 45), del_rect, border_radius=3)
                del_text = self.font.render("X", True, (255, 255, 255))
                del_text_rect = del_text.get_rect(center=del_rect.center)
                surface.blit(del_text, del_text_rect)

            # Draw scroll indicator if needed
            if len(self.npcs_copy) > self._visible_count:
                scroll_text = f"({self._scroll_offset + 1}-{min(self._scroll_offset + self._visible_count, len(self.npcs_copy))} из {len(self.npcs_copy)})"
                scroll_surface = self.font.render(scroll_text, True, (150, 150, 150))
                surface.blit(scroll_surface, (self.x + self.width - 150, self.y + 50))

        # Draw add NPC button
        add_btn_y = self.y + 95 + min(len(self.npcs_copy), self._visible_count) * 36 + 10
        add_btn_rect = pygame.Rect(self.x + 20, add_btn_y, 150, 28)
        self._add_npc_rect = pygame.Rect(20, add_btn_y - self.y, 150, 28)
        pygame.draw.rect(surface, (45, 100, 45), add_btn_rect, border_radius=3)
        add_text = self.font.render("+ Добавить NPC", True, (255, 255, 255))
        add_text_rect = add_text.get_rect(center=add_btn_rect.center)
        surface.blit(add_text, add_text_rect)

        # Draw dropdown options if active (must be drawn last to be on top)
        if self._active_dropdown_type is not None:
            idx = self._active_dropdown_type
            if self._scroll_offset <= idx < self._scroll_offset + self._visible_count:
                display_idx = idx - self._scroll_offset
                row_y = self.y + 95 + display_idx * 36
                option_y = row_y + 28

                options_height = len(self.NPC_TYPE_OPTIONS) * 28
                options_rect = pygame.Rect(self.x + 20, option_y, 200, options_height)
                pygame.draw.rect(surface, (50, 50, 55), options_rect)
                pygame.draw.rect(surface, (80, 80, 85), options_rect, width=1)

                for i, (key, value) in enumerate(self.NPC_TYPE_OPTIONS.items()):
                    opt_rect = pygame.Rect(self.x + 20, option_y + i * 28, 200, 28)
                    if key == self.npcs_copy[idx].npc_type:
                        pygame.draw.rect(surface, (70, 70, 80), opt_rect)
                    opt_text = self.font.render(value, True, self.text_color)
                    surface.blit(opt_text, (opt_rect.x + 6, opt_rect.y + 6))

        if self._active_dropdown_rank is not None:
            idx = self._active_dropdown_rank
            if self._scroll_offset <= idx < self._scroll_offset + self._visible_count:
                display_idx = idx - self._scroll_offset
                row_y = self.y + 95 + display_idx * 36
                option_y = row_y + 28

                options_height = len(self.RANK_OPTIONS) * 28
                options_rect = pygame.Rect(self.x + 230, option_y, 80, options_height)
                pygame.draw.rect(surface, (50, 50, 55), options_rect)
                pygame.draw.rect(surface, (80, 80, 85), options_rect, width=1)

                for i, (key, value) in enumerate(self.RANK_OPTIONS.items()):
                    opt_rect = pygame.Rect(self.x + 230, option_y + i * 28, 80, 28)
                    if int(key) == self.npcs_copy[idx].rank:
                        pygame.draw.rect(surface, (70, 70, 80), opt_rect)
                    opt_text = self.font.render(key, True, self.text_color)
                    surface.blit(opt_text, (opt_rect.x + 6, opt_rect.y + 6))

    def _handle_count_click(self, local_x: int, local_y: int) -> bool:
        """Handle click on count +/- buttons."""
        for display_idx in range(min(self._visible_count, len(self.npcs_copy) - self._scroll_offset)):
            actual_idx = display_idx + self._scroll_offset
            row_y = 95 + display_idx * 36

            # - button area
            minus_rect = pygame.Rect(322, row_y + 2, 20, 24)
            if minus_rect.collidepoint(local_x, local_y):
                if self.npcs_copy[actual_idx].count > 1:
                    self.npcs_copy[actual_idx].count -= 1
                return True

            # + button area
            plus_rect = pygame.Rect(378, row_y + 2, 20, 24)
            if plus_rect.collidepoint(local_x, local_y):
                if self.npcs_copy[actual_idx].count < 99:
                    self.npcs_copy[actual_idx].count += 1
                return True

        return False

    def get_npcs(self) -> List[FloorNPC]:
        """Get the edited NPCs list (only non-empty)."""
        return [npc for npc in self.npcs_copy if not npc.is_empty()]


class QuestEditDialog(Dialog):
    """Dialog for editing a single quest."""

    def __init__(self, quest: Quest = None, all_locations: List = None):
        """Initialize quest edit dialog.

        Args:
            quest: Quest to edit, or None to create new
            all_locations: List of all locations on the map (for deliver destination)
        """
        self.quest = Quest() if quest is None else Quest(
            id=quest.id,
            quest_type=quest.quest_type,
            name=quest.name,
            description=quest.description,
            target_type=quest.target_type,
            target_item_id=quest.target_item_id,
            target_amount=quest.target_amount,
            time_limit=quest.time_limit,
            difficulty=quest.difficulty,
            target_location_id=quest.target_location_id,
            target_location_name=quest.target_location_name,
            target_floor=quest.target_floor,
            reward_gold=quest.reward_gold,
            reward_item_id=quest.reward_item_id,
            reward_item_amount=quest.reward_item_amount,
            reward_exp=quest.reward_exp,
            reward_reputation=quest.reward_reputation,
            is_repeatable=quest.is_repeatable,
            cooldown=quest.cooldown,
            min_player_attitude=quest.min_player_attitude,
            min_player_rank=quest.min_player_rank,
            min_player_level=quest.min_player_level,
            fail_attitude_penalty=quest.fail_attitude_penalty,
            completion_event_id=quest.completion_event_id,
            scaling_factor=quest.scaling_factor
        )
        self.all_locations = all_locations or []
        self.is_new = quest is None

        # Callback for selecting location on map
        self.on_select_location: Optional[Callable[[str], None]] = None  # 'deliver' or 'clear'

        title = "Новый квест" if self.is_new else "Редактирование квеста"
        super().__init__(title, width=500, height=890)  # Increased height for min_player_level field

        self._active_dropdown: Optional[str] = None
        self._active_text_field: Optional[str] = None  # 'target_item_id' or 'reward_item_id'
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        # Store initial data
        self.data['quest_type'] = self.quest.quest_type
        self.data['name'] = self.quest.name
        self.data['description'] = self.quest.description
        self.data['target_type'] = self.quest.target_type
        self.data['target_item_id'] = self.quest.target_item_id
        self.data['target_amount'] = self.quest.target_amount
        self.data['time_limit'] = self.quest.time_limit
        self.data['difficulty'] = self.quest.difficulty
        self.data['target_location_id'] = self.quest.target_location_id
        self.data['target_location_name'] = self.quest.target_location_name
        self.data['target_floor'] = self.quest.target_floor
        self.data['reward_gold'] = self.quest.reward_gold
        self.data['reward_item_id'] = self.quest.reward_item_id
        self.data['reward_item_amount'] = self.quest.reward_item_amount
        self.data['reward_exp'] = self.quest.reward_exp
        self.data['reward_reputation'] = self.quest.reward_reputation
        self.data['is_repeatable'] = self.quest.is_repeatable
        self.data['cooldown'] = self.quest.cooldown
        self.data['min_player_attitude'] = self.quest.min_player_attitude
        self.data['min_player_rank'] = self.quest.min_player_rank
        self.data['min_player_level'] = self.quest.min_player_level
        self.data['fail_attitude_penalty'] = self.quest.fail_attitude_penalty
        self.data['completion_event_id'] = self.quest.completion_event_id
        self.data['scaling_factor'] = self.quest.scaling_factor

        # Text inputs
        y = 50
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(120, y, 360, 28),
            label="Название",
            key="name",
            value=self.quest.name,
            max_length=100
        ))

        y += 40
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(120, y, 360, 28),
            label="Описание",
            key="description",
            value=self.quest.description,
            max_length=200
        ))

        # Buttons at the bottom
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def _get_target_options(self) -> Dict[str, str]:
        """Get target options based on quest type."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
        if quest_type == QUEST_GATHER_RESOURCE:
            return QUEST_RESOURCE_TARGETS
        elif quest_type == QUEST_HUNT_ANIMALS:
            return QUEST_ANIMAL_TARGETS
        return {}

    def _needs_target_location(self) -> bool:
        """Check if quest type requires target location selection."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
        return quest_type in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION)

    def _needs_target_floor(self) -> bool:
        """Check if quest type requires floor selection."""
        return self.data.get('quest_type') == QUEST_CLEAR_LOCATION

    def set_target_location(self, location_id: str, location_name: str) -> None:
        """Set target location from map selection."""
        self.data['target_location_id'] = location_id
        self.data['target_location_name'] = location_name

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom quest handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Handle active dropdown options click
            if self._active_dropdown:
                consumed = self._handle_dropdown_selection(local_x, local_y)
                if consumed:
                    return True
                self._active_dropdown = None
                return True

            # Check dropdown triggers
            if self._check_dropdown_triggers(local_x, local_y):
                return True

            # Check +/- buttons for numeric fields
            if self._check_numeric_buttons(local_x, local_y):
                return True

            # Check text field clicks
            if self._check_text_field_clicks(local_x, local_y):
                return True

            # Check "Select on map" button
            if self._check_select_location_button(local_x, local_y):
                return True

            # Check checkbox is_repeatable
            # For gather/hunt/collect: y=680 (reward_base=560 + 120)
            # For deliver/clear: y=640 (reward_base=520 + 120)
            quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
            if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
                checkbox_y = 680
            else:
                checkbox_y = 640
            checkbox_rect = pygame.Rect(120, checkbox_y, 20, 20)
            if checkbox_rect.collidepoint(local_x, local_y):
                self.data['is_repeatable'] = not self.data.get('is_repeatable', True)
                return True

            # Deselect text fields if clicked elsewhere
            self._active_text_field = None

        # Handle keyboard input for text fields
        if event.type == pygame.KEYDOWN and self._active_text_field:
            if self._handle_text_field_input(event):
                return True

        # Handle base dialog events
        return super().handle_event(event)

    def _check_dropdown_triggers(self, local_x: int, local_y: int) -> bool:
        """Check if any dropdown trigger was clicked."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)

        # Quest type dropdown (always at y=130)
        type_rect = pygame.Rect(120, 130, 200, 28)
        if type_rect.collidepoint(local_x, local_y):
            self._active_dropdown = 'quest_type' if self._active_dropdown != 'quest_type' else None
            return True

        # Target type dropdown (y=170) - only for gather/hunt quests
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS):
            target_rect = pygame.Rect(120, 170, 200, 28)
            if target_rect.collidepoint(local_x, local_y):
                self._active_dropdown = 'target_type' if self._active_dropdown != 'target_type' else None
                return True

        # Difficulty dropdown - position depends on quest type
        # For gather/hunt/collect: y=290 (after target_type/item + target_amount + time_limit)
        # For deliver/clear: y=250 (after time_limit at y=210)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            diff_y = 290
        else:
            diff_y = 250
        diff_rect = pygame.Rect(120, diff_y, 200, 28)
        if diff_rect.collidepoint(local_x, local_y):
            self._active_dropdown = 'difficulty' if self._active_dropdown != 'difficulty' else None
            return True

        return False

    def _check_select_location_button(self, local_x: int, local_y: int) -> bool:
        """Check if 'Select on map' button was clicked."""
        if self._needs_target_location():
            quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
            # For deliver/clear: y=410 (after min_player_level at y=370)
            # For gather/hunt/collect this button is not shown
            if quest_type in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION):
                btn_y = 410
            else:
                btn_y = 450  # fallback, should not reach here
            btn_rect = pygame.Rect(340, btn_y, 140, 28)
            if btn_rect.collidepoint(local_x, local_y):
                if self.on_select_location:
                    self.on_select_location(quest_type)
                return True
        return False

    def _handle_dropdown_selection(self, local_x: int, local_y: int) -> bool:
        """Handle selection from active dropdown."""
        if self._active_dropdown == 'quest_type':
            options = QUEST_TYPES
            base_y = 130 + 28
            for i, (key, value) in enumerate(options.items()):
                option_rect = pygame.Rect(120, base_y + i * 28, 200, 28)
                if option_rect.collidepoint(local_x, local_y):
                    self.data['quest_type'] = key
                    # Reset target type when switching quest type
                    if key == QUEST_GATHER_RESOURCE:
                        self.data['target_type'] = QUEST_TARGET_WOOD
                        self.data['target_item_id'] = ''
                    elif key == QUEST_HUNT_ANIMALS:
                        self.data['target_type'] = QUEST_TARGET_WOLF
                        self.data['target_item_id'] = ''
                    elif key == QUEST_COLLECT_ITEMS:
                        self.data['target_type'] = ''
                    elif key in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION):
                        # These quest types don't use target_type/target_amount
                        self.data['target_type'] = ''
                        self.data['target_amount'] = 0
                    # Reset target location/floor when switching to non-location quests
                    if key not in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION):
                        self.data['target_location_id'] = ''
                        self.data['target_location_name'] = ''
                        self.data['target_floor'] = 0
                    # Reset target_item_id for non-collect quests
                    if key != QUEST_COLLECT_ITEMS:
                        self.data['target_item_id'] = ''
                    self._active_dropdown = None
                    return True

        elif self._active_dropdown == 'target_type':
            options = self._get_target_options()
            base_y = 170 + 28
            for i, (key, value) in enumerate(options.items()):
                option_rect = pygame.Rect(120, base_y + i * 28, 200, 28)
                if option_rect.collidepoint(local_x, local_y):
                    self.data['target_type'] = key
                    self._active_dropdown = None
                    return True

        elif self._active_dropdown == 'difficulty':
            options = QUEST_DIFFICULTIES
            # Difficulty position depends on quest type
            quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
            if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
                base_y = 290 + 28
            else:
                base_y = 250 + 28
            for i, (key, value) in enumerate(options.items()):
                option_rect = pygame.Rect(120, base_y + i * 28, 200, 28)
                if option_rect.collidepoint(local_x, local_y):
                    self.data['difficulty'] = key
                    self._active_dropdown = None
                    return True

        return False

    def _check_numeric_buttons(self, local_x: int, local_y: int) -> bool:
        """Check +/- buttons for numeric fields."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)

        # Target amount (y=210) - for gather/hunt/collect
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            minus_rect = pygame.Rect(120, 212, 30, 24)
            plus_rect = pygame.Rect(220, 212, 30, 24)
            if minus_rect.collidepoint(local_x, local_y):
                self.data['target_amount'] = max(1, self.data.get('target_amount', 10) - 1)
                return True
            if plus_rect.collidepoint(local_x, local_y):
                self.data['target_amount'] = min(999, self.data.get('target_amount', 10) + 1)
                return True

        # Time limit - position depends on quest type
        # For gather/hunt/collect: y=250 (after target_type/item + target_amount)
        # For deliver/clear: y=210 (y+=40 still happens after empty target_amount position)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            time_y = 252
        else:
            time_y = 212
        minus_rect = pygame.Rect(120, time_y, 30, 24)
        plus_rect = pygame.Rect(220, time_y, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['time_limit'] = max(0, self.data.get('time_limit', 0) - 10)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['time_limit'] = min(9999, self.data.get('time_limit', 0) + 10)
            return True

        # Difficulty position (for click detection is handled in dropdown)
        # For gather/hunt/collect: y=290
        # For deliver/clear: y=250

        # min_player_attitude - after difficulty
        # For gather/hunt/collect: y=330
        # For deliver/clear: y=290
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            attitude_y = 332
        else:
            attitude_y = 292
        minus_rect = pygame.Rect(120, attitude_y, 30, 24)
        plus_rect = pygame.Rect(220, attitude_y, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['min_player_attitude'] = max(-10, self.data.get('min_player_attitude', 0) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['min_player_attitude'] = min(10, self.data.get('min_player_attitude', 0) + 1)
            return True

        # min_player_rank - after min_player_attitude
        # For gather/hunt/collect: y=372 (330 + 40 + 2)
        # For deliver/clear: y=332 (290 + 40 + 2)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            rank_y = 372
        else:
            rank_y = 332
        minus_rect = pygame.Rect(120, rank_y, 30, 24)
        plus_rect = pygame.Rect(220, rank_y, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['min_player_rank'] = max(0, self.data.get('min_player_rank', 0) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['min_player_rank'] = min(4, self.data.get('min_player_rank', 0) + 1)
            return True

        # min_player_level - after min_player_rank
        # For gather/hunt/collect: y=412 (372 + 40)
        # For deliver/clear: y=372 (332 + 40)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            level_y = 412
        else:
            level_y = 372
        minus_rect = pygame.Rect(120, level_y, 30, 24)
        plus_rect = pygame.Rect(220, level_y, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['min_player_level'] = max(0, self.data.get('min_player_level', 0) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['min_player_level'] = min(100, self.data.get('min_player_level', 0) + 1)
            return True

        # Target floor - only for clear_location
        # For clear_location: y=452 (after target_location at y=412)
        if quest_type == QUEST_CLEAR_LOCATION:
            minus_rect = pygame.Rect(120, 452, 30, 24)
            plus_rect = pygame.Rect(220, 452, 30, 24)
            if minus_rect.collidepoint(local_x, local_y):
                self.data['target_floor'] = max(0, self.data.get('target_floor', 0) - 1)
                return True
            if plus_rect.collidepoint(local_x, local_y):
                self.data['target_floor'] = min(10, self.data.get('target_floor', 0) + 1)
                return True

        # Calculate base Y for rewards section based on quest type
        # For gather/hunt/collect: rewards start at y=560 (header at y=530)
        # For deliver/clear: rewards start at y=520 (header at y=490)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            reward_base_y = 560
        else:
            reward_base_y = 520

        # Reward gold
        minus_rect = pygame.Rect(120, reward_base_y + 2, 30, 24)
        plus_rect = pygame.Rect(220, reward_base_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['reward_gold'] = max(0, self.data.get('reward_gold', 100) - 10)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['reward_gold'] = min(99999, self.data.get('reward_gold', 100) + 10)
            return True

        # Reward exp (right side)
        minus_rect = pygame.Rect(290, reward_base_y + 2, 30, 24)
        plus_rect = pygame.Rect(390, reward_base_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['reward_exp'] = max(0, self.data.get('reward_exp', 50) - 10)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['reward_exp'] = min(99999, self.data.get('reward_exp', 50) + 10)
            return True

        # Reward reputation (y = reward_base_y + 30)
        rep_y = reward_base_y + 30
        minus_rect = pygame.Rect(120, rep_y + 2, 30, 24)
        plus_rect = pygame.Rect(220, rep_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['reward_reputation'] = max(-100, self.data.get('reward_reputation', 5) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['reward_reputation'] = min(100, self.data.get('reward_reputation', 5) + 1)
            return True

        # Reward item amount (y = reward_base_y + 60)
        item_y = reward_base_y + 60
        minus_rect = pygame.Rect(320, item_y + 2, 30, 24)
        plus_rect = pygame.Rect(390, item_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['reward_item_amount'] = max(1, self.data.get('reward_item_amount', 1) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['reward_item_amount'] = min(99, self.data.get('reward_item_amount', 1) + 1)
            return True

        # fail_attitude_penalty (y = reward_base_y + 150, after completion_event_id and is_repeatable)
        fail_penalty_y = reward_base_y + 150
        minus_rect = pygame.Rect(120, fail_penalty_y + 2, 30, 24)
        plus_rect = pygame.Rect(220, fail_penalty_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['fail_attitude_penalty'] = max(0, self.data.get('fail_attitude_penalty', 0) - 1)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['fail_attitude_penalty'] = min(20, self.data.get('fail_attitude_penalty', 0) + 1)
            return True

        # Cooldown (y = reward_base_y + 180)
        cooldown_y = reward_base_y + 180
        minus_rect = pygame.Rect(120, cooldown_y + 2, 30, 24)
        plus_rect = pygame.Rect(220, cooldown_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            self.data['cooldown'] = max(0, self.data.get('cooldown', 100) - 10)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            self.data['cooldown'] = min(9999, self.data.get('cooldown', 100) + 10)
            return True

        # Scaling factor (y = reward_base_y + 210)
        scaling_y = reward_base_y + 210
        minus_rect = pygame.Rect(120, scaling_y + 2, 30, 24)
        plus_rect = pygame.Rect(220, scaling_y + 2, 30, 24)
        if minus_rect.collidepoint(local_x, local_y):
            current = self.data.get('scaling_factor', 1.1)
            self.data['scaling_factor'] = round(max(1.0, current - 0.05), 2)
            return True
        if plus_rect.collidepoint(local_x, local_y):
            current = self.data.get('scaling_factor', 1.1)
            self.data['scaling_factor'] = round(min(2.0, current + 0.05), 2)
            return True

        return False

    def _check_text_field_clicks(self, local_x: int, local_y: int) -> bool:
        """Check if text fields were clicked."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)

        # Calculate base Y position for text fields
        y = 130 + 40  # After quest type dropdown

        # Target item ID field (only for collect_items)
        if quest_type == QUEST_COLLECT_ITEMS:
            target_item_rect = pygame.Rect(120, y + 2, 200, 24)
            if target_item_rect.collidepoint(local_x, local_y):
                self._active_text_field = 'target_item_id'
                return True
            y += 40
        elif quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS):
            y += 40  # target type dropdown

        # Calculate reward_item_id position based on quest type
        # For gather/hunt/collect: y=580 (reward_base=520 + 60)
        # For deliver/clear: y=540 (reward_base=480 + 60)
        if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
            reward_item_y = 580
        else:
            reward_item_y = 540

        # Reward item ID field
        reward_item_rect = pygame.Rect(120, reward_item_y + 2, 140, 24)
        if reward_item_rect.collidepoint(local_x, local_y):
            self._active_text_field = 'reward_item_id'
            return True

        # completion_event_id position (y = reward_item_y + 30)
        event_id_y = reward_item_y + 30
        event_id_rect = pygame.Rect(120, event_id_y + 2, 200, 24)
        if event_id_rect.collidepoint(local_x, local_y):
            self._active_text_field = 'completion_event_id'
            return True

        return False

    def _handle_text_field_input(self, event: pygame.event.Event) -> bool:
        """Handle keyboard input for active text field."""
        if not self._active_text_field:
            return False

        field_key = self._active_text_field
        current_value = self.data.get(field_key, '')

        if event.key == pygame.K_BACKSPACE:
            if current_value:
                self.data[field_key] = current_value[:-1]
            return True
        elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            self._active_text_field = None
            return True
        elif event.key == pygame.K_TAB:
            # Switch between text fields
            if self._active_text_field == 'target_item_id':
                self._active_text_field = 'reward_item_id'
            elif self._active_text_field == 'reward_item_id':
                self._active_text_field = 'completion_event_id'
            elif self._active_text_field == 'completion_event_id':
                quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
                if quest_type == QUEST_COLLECT_ITEMS:
                    self._active_text_field = 'target_item_id'
                else:
                    self._active_text_field = 'reward_item_id'
            return True
        elif event.unicode and event.unicode.isprintable():
            # Allow alphanumeric, underscore, and dash
            char = event.unicode
            if char.isalnum() or char in '_-':
                if len(current_value) < 50:  # Max length
                    self.data[field_key] = current_value + char
            return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the quest edit dialog."""
        if not self.visible:
            return

        # Draw dialog base
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, dialog_rect)
        pygame.draw.rect(surface, self.border_color, dialog_rect, 1)

        # Draw title bar
        title_rect = pygame.Rect(self.x, self.y, self.width, 35)
        pygame.draw.rect(surface, self.title_bg, title_rect)
        title_text = self.font_title.render(self.title, True, self.text_color)
        surface.blit(title_text, (self.x + 10, self.y + 8))

        # Draw text inputs
        for text_input in self.text_inputs:
            self._draw_text_input(surface, text_input)

        # Current Y position for drawing
        y = 130
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)
        needs_target_location = quest_type in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION)
        needs_target_floor = quest_type == QUEST_CLEAR_LOCATION
        needs_target_type = quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS)
        needs_target_item = quest_type == QUEST_COLLECT_ITEMS

        # Quest type dropdown
        self._draw_label(surface, "Тип квеста", self.x + 15, self.y + y + 4)
        quest_type_name = QUEST_TYPES.get(quest_type, quest_type)
        self._draw_dropdown_field(surface, quest_type_name, self.x + 120, self.y + y, 200,
                                  self._active_dropdown == 'quest_type')
        y += 40

        # Target type dropdown (only for gather/hunt)
        if needs_target_type:
            self._draw_label(surface, "Цель", self.x + 15, self.y + y + 4)
            target_type = self.data.get('target_type', QUEST_TARGET_WOOD)
            target_name = QUEST_TARGETS.get(target_type, target_type)
            self._draw_dropdown_field(surface, target_name, self.x + 120, self.y + y, 200,
                                      self._active_dropdown == 'target_type')
            y += 40

        # Target item ID (only for collect_items)
        if needs_target_item:
            self._draw_label(surface, "ID предмета", self.x + 15, self.y + y + 4)
            item_id = self.data.get('target_item_id', '')
            self._draw_text_field(surface, item_id, self.x + 120, self.y + y, 200, 'target_item_id')
            y += 40

        # Target amount (for gather/hunt/collect)
        if needs_target_type or needs_target_item:
            self._draw_label(surface, "Количество", self.x + 15, self.y + y + 4)
            self._draw_numeric_field(surface, self.data.get('target_amount', 10),
                                     self.x + 120, self.y + y, 130)
        y += 40

        # Time limit
        self._draw_label(surface, "Время (ходов)", self.x + 15, self.y + y + 4)
        time_limit = self.data.get('time_limit', 0)
        time_text = str(time_limit) if time_limit > 0 else "Без лимита"
        self._draw_numeric_field(surface, time_limit, self.x + 120, self.y + y, 130,
                                 display_text=time_text)
        y += 40

        # Difficulty dropdown
        self._draw_label(surface, "Сложность", self.x + 15, self.y + y + 4)
        difficulty = self.data.get('difficulty', 1)
        diff_name = QUEST_DIFFICULTIES.get(difficulty, f"Уровень {difficulty}")
        self._draw_dropdown_field(surface, diff_name, self.x + 120, self.y + y, 200,
                                  self._active_dropdown == 'difficulty')
        y += 40

        # Minimum player attitude (requirement to get quest)
        self._draw_label(surface, "Мин. отношение", self.x + 15, self.y + y + 4)
        min_attitude = self.data.get('min_player_attitude', 0)
        attitude_text = str(min_attitude)
        self._draw_numeric_field(surface, min_attitude, self.x + 120, self.y + y, 130,
                                 display_text=attitude_text)
        y += 40

        # Minimum player rank (requirement to get quest)
        self._draw_label(surface, "Мин. ранг игрока", self.x + 15, self.y + y + 4)
        min_rank = self.data.get('min_player_rank', 0)
        rank_text = "Без ограничения" if min_rank == 0 else f"Ранг {min_rank}"
        self._draw_numeric_field(surface, min_rank, self.x + 120, self.y + y, 130,
                                 display_text=rank_text)
        y += 40

        # Minimum player level (requirement to get quest)
        self._draw_label(surface, "Мин. уровень", self.x + 15, self.y + y + 4)
        min_level = self.data.get('min_player_level', 0)
        level_text = "Без ограничения" if min_level == 0 else f"Уровень {min_level}"
        self._draw_numeric_field(surface, min_level, self.x + 120, self.y + y, 130,
                                 display_text=level_text)
        y += 40

        # Target location (for deliver_message and clear_location)
        if needs_target_location:
            if quest_type == QUEST_DELIVER_MESSAGE:
                self._draw_label(surface, "Цель доставки", self.x + 15, self.y + y + 4)
            else:
                self._draw_label(surface, "Локация", self.x + 15, self.y + y + 4)

            # Display selected location or placeholder
            loc_name = self.data.get('target_location_name', '')
            if not loc_name:
                loc_name = "Не выбрано"
            # Draw location display field
            loc_rect = pygame.Rect(self.x + 120, self.y + y, 210, 28)
            pygame.draw.rect(surface, self.slider_bg, loc_rect)
            pygame.draw.rect(surface, self.border_color, loc_rect, 1)
            loc_text = self.font.render(loc_name[:25], True, self.text_color)
            surface.blit(loc_text, (loc_rect.x + 5, loc_rect.y + 6))

            # Draw "Select on map" button
            btn_rect = pygame.Rect(self.x + 340, self.y + y, 140, 28)
            pygame.draw.rect(surface, self.button_color, btn_rect)
            pygame.draw.rect(surface, self.border_color, btn_rect, 1)
            btn_text = self.font.render("Выбрать на карте", True, self.text_color)
            surface.blit(btn_text, (btn_rect.x + 5, btn_rect.y + 6))
        y += 40

        # Target floor (only for clear_location)
        if needs_target_floor:
            self._draw_label(surface, "Этаж", self.x + 15, self.y + y + 4)
            target_floor = self.data.get('target_floor', 0)
            floor_text = "Все этажи" if target_floor == 0 else str(target_floor)
            self._draw_numeric_field(surface, target_floor, self.x + 120, self.y + y, 130,
                                     display_text=floor_text)
        y += 40

        # Rewards header
        self._draw_label(surface, "— Награда —", self.x + 15, self.y + y)
        y += 30

        # Reward gold and exp on same line
        self._draw_label(surface, "Золото", self.x + 15, self.y + y + 4)
        self._draw_numeric_field(surface, self.data.get('reward_gold', 100),
                                 self.x + 120, self.y + y, 130)
        self._draw_label(surface, "Опыт", self.x + 250, self.y + y + 4)
        self._draw_numeric_field(surface, self.data.get('reward_exp', 50),
                                 self.x + 290, self.y + y, 130)
        y += 30

        # Reward reputation
        self._draw_label(surface, "Репутация", self.x + 15, self.y + y + 4)
        self._draw_numeric_field(surface, self.data.get('reward_reputation', 5),
                                 self.x + 120, self.y + y, 130)
        y += 30

        # Reward item ID and amount
        self._draw_label(surface, "ID предмета", self.x + 15, self.y + y + 4)
        reward_item = self.data.get('reward_item_id', '')
        self._draw_text_field(surface, reward_item, self.x + 120, self.y + y, 140, 'reward_item_id')
        self._draw_label(surface, "Кол-во", self.x + 270, self.y + y + 4)
        self._draw_numeric_field(surface, self.data.get('reward_item_amount', 1),
                                 self.x + 320, self.y + y, 100)
        y += 30

        # Completion event ID (event to trigger on completion)
        self._draw_label(surface, "ID события", self.x + 15, self.y + y + 4)
        event_id = self.data.get('completion_event_id', '')
        self._draw_text_field(surface, event_id, self.x + 120, self.y + y, 200, 'completion_event_id')
        y += 30

        # Is repeatable checkbox
        self._draw_label(surface, "Повторяемый", self.x + 15, self.y + y + 2)
        is_rep = self.data.get('is_repeatable', True)
        checkbox_rect = pygame.Rect(self.x + 120, self.y + y, 20, 20)
        pygame.draw.rect(surface, self.slider_bg, checkbox_rect)
        pygame.draw.rect(surface, self.border_color, checkbox_rect, 1)
        if is_rep:
            inner = checkbox_rect.inflate(-6, -6)
            pygame.draw.rect(surface, self.button_primary, inner)
        y += 30

        # Fail attitude penalty (penalty to player attitude on quest failure)
        self._draw_label(surface, "Штраф отнош.", self.x + 15, self.y + y + 4)
        fail_penalty = self.data.get('fail_attitude_penalty', 0)
        penalty_text = str(fail_penalty)
        self._draw_numeric_field(surface, fail_penalty, self.x + 120, self.y + y, 130,
                                 display_text=penalty_text)
        y += 30

        # Cooldown
        self._draw_label(surface, "Перезарядка", self.x + 15, self.y + y + 4)
        self._draw_numeric_field(surface, self.data.get('cooldown', 100),
                                 self.x + 120, self.y + y, 130)
        y += 30

        # Scaling factor
        self._draw_label(surface, "Коэффициент", self.x + 15, self.y + y + 4)
        scaling = self.data.get('scaling_factor', 1.1)
        scaling_text = f"{scaling:.2f}"
        self._draw_float_field(surface, scaling, self.x + 120, self.y + y, 130,
                               display_text=scaling_text)

        # Draw dropdown options on top
        if self._active_dropdown:
            self._draw_dropdown_options(surface)

        # Draw buttons
        for i, button in enumerate(self.buttons):
            self._draw_button(surface, button, i == self.hovered_button)

    def _draw_label(self, surface: pygame.Surface, text: str, x: int, y: int) -> None:
        """Draw a label."""
        label_surf = self.font.render(text, True, self.text_color)
        surface.blit(label_surf, (x, y))

    def _draw_dropdown_field(self, surface: pygame.Surface, text: str, x: int, y: int,
                             width: int, is_active: bool = False) -> None:
        """Draw a dropdown field."""
        rect = pygame.Rect(x, y, width, 28)
        color = self.button_hover if is_active else self.slider_bg
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)

        text_surf = self.font.render(text[:35], True, self.text_color)
        surface.blit(text_surf, (x + 5, y + 6))

        # Draw dropdown arrow
        arrow_x = x + width - 15
        arrow_y = y + 12
        pygame.draw.polygon(surface, self.text_color, [
            (arrow_x, arrow_y), (arrow_x + 8, arrow_y), (arrow_x + 4, arrow_y + 6)
        ])

    def _draw_numeric_field(self, surface: pygame.Surface, value: int, x: int, y: int,
                            width: int, display_text: str = None) -> None:
        """Draw a numeric field with +/- buttons."""
        # Minus button
        minus_rect = pygame.Rect(x, y + 2, 30, 24)
        pygame.draw.rect(surface, self.button_color, minus_rect)
        pygame.draw.rect(surface, self.border_color, minus_rect, 1)
        minus_text = self.font.render("-", True, self.text_color)
        surface.blit(minus_text, (x + 10, y + 6))

        # Value display
        value_rect = pygame.Rect(x + 35, y + 2, width - 70, 24)
        pygame.draw.rect(surface, self.slider_bg, value_rect)
        pygame.draw.rect(surface, self.border_color, value_rect, 1)
        text = display_text if display_text else str(value)
        val_text = self.font.render(text, True, self.text_color)
        text_x = value_rect.x + (value_rect.width - val_text.get_width()) // 2
        surface.blit(val_text, (text_x, y + 6))

        # Plus button
        plus_rect = pygame.Rect(x + width - 30, y + 2, 30, 24)
        pygame.draw.rect(surface, self.button_color, plus_rect)
        pygame.draw.rect(surface, self.border_color, plus_rect, 1)
        plus_text = self.font.render("+", True, self.text_color)
        surface.blit(plus_text, (x + width - 20, y + 6))

    def _draw_float_field(self, surface: pygame.Surface, value: float, x: int, y: int,
                          width: int, display_text: str = None) -> None:
        """Draw a float field with +/- buttons."""
        # Minus button
        minus_rect = pygame.Rect(x, y + 2, 30, 24)
        pygame.draw.rect(surface, self.button_color, minus_rect)
        pygame.draw.rect(surface, self.border_color, minus_rect, 1)
        minus_text = self.font.render("-", True, self.text_color)
        surface.blit(minus_text, (x + 10, y + 6))

        # Value display
        value_rect = pygame.Rect(x + 35, y + 2, width - 70, 24)
        pygame.draw.rect(surface, self.slider_bg, value_rect)
        pygame.draw.rect(surface, self.border_color, value_rect, 1)
        text = display_text if display_text else f"{value:.2f}"
        val_text = self.font.render(text, True, self.text_color)
        text_x = value_rect.x + (value_rect.width - val_text.get_width()) // 2
        surface.blit(val_text, (text_x, y + 6))

        # Plus button
        plus_rect = pygame.Rect(x + width - 30, y + 2, 30, 24)
        pygame.draw.rect(surface, self.button_color, plus_rect)
        pygame.draw.rect(surface, self.border_color, plus_rect, 1)
        plus_text = self.font.render("+", True, self.text_color)
        surface.blit(plus_text, (x + width - 20, y + 6))

    def _draw_text_field(self, surface: pygame.Surface, value: str, x: int, y: int,
                         width: int, field_key: str) -> None:
        """Draw an editable text field."""
        is_active = self._active_text_field == field_key
        rect = pygame.Rect(x, y + 2, width, 24)
        bg_color = self.button_hover if is_active else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)

        # Draw text
        display_text = value[-25:] if value else ""
        text_surf = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surf, (rect.x + 5, rect.y + 4))

        # Draw cursor if active
        if is_active:
            cursor_x = rect.x + 5 + text_surf.get_width() + 2
            pygame.draw.line(surface, self.text_color,
                           (cursor_x, rect.y + 3),
                           (cursor_x, rect.y + rect.height - 3))

    def _draw_dropdown_options(self, surface: pygame.Surface) -> None:
        """Draw dropdown options overlay."""
        quest_type = self.data.get('quest_type', QUEST_GATHER_RESOURCE)

        if self._active_dropdown == 'quest_type':
            options = QUEST_TYPES
            base_x, base_y = self.x + 120, self.y + 130 + 28
            width = 200
        elif self._active_dropdown == 'target_type':
            options = self._get_target_options()
            base_x, base_y = self.x + 120, self.y + 170 + 28
            width = 200
        elif self._active_dropdown == 'difficulty':
            options = QUEST_DIFFICULTIES
            # Difficulty position depends on quest type
            if quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS, QUEST_COLLECT_ITEMS):
                diff_y = 290
            else:
                diff_y = 250
            base_x, base_y = self.x + 120, self.y + diff_y + 28
            width = 200
        else:
            return

        # Draw options background
        opt_height = len(options) * 28
        bg_rect = pygame.Rect(base_x, base_y, width, opt_height)
        pygame.draw.rect(surface, self.bg_color, bg_rect)
        pygame.draw.rect(surface, self.border_color, bg_rect, 1)

        for i, (key, value) in enumerate(options.items()):
            opt_rect = pygame.Rect(base_x, base_y + i * 28, width, 28)
            # Highlight on hover
            mouse_pos = pygame.mouse.get_pos()
            local_x = mouse_pos[0] - self.x
            local_y = mouse_pos[1] - self.y
            if opt_rect.move(-self.x, -self.y).collidepoint(local_x, local_y):
                pygame.draw.rect(surface, self.button_hover, opt_rect)

            text_surf = self.font.render(str(value)[:40], True, self.text_color)
            surface.blit(text_surf, (base_x + 5, base_y + i * 28 + 6))

    def _draw_text_input(self, surface: pygame.Surface, text_input: DialogTextInput) -> None:
        """Draw a text input field."""
        # Draw label
        label_surf = self.font.render(text_input.label, True, self.text_color)
        surface.blit(label_surf, (self.x + 15, self.y + text_input.rect.y + 6))

        # Draw input field
        rect = text_input.rect.move(self.x, self.y)
        bg_color = self.button_hover if text_input.active else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)

        # Draw text
        text_surf = self.font.render(text_input.value[-40:], True, self.text_color)
        surface.blit(text_surf, (rect.x + 5, rect.y + 6))

        # Draw cursor if active
        if text_input.active:
            cursor_x = rect.x + 5 + text_surf.get_width() + 2
            pygame.draw.line(surface, self.text_color,
                           (cursor_x, rect.y + 5),
                           (cursor_x, rect.y + rect.height - 5))

    def _draw_button(self, surface: pygame.Surface, button: DialogButton, hovered: bool) -> None:
        """Draw a dialog button."""
        rect = button.rect.move(self.x, self.y)
        if button.primary:
            color = self.button_primary
        elif hovered:
            color = self.button_hover
        else:
            color = self.button_color
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)

        text_surf = self.font.render(button.text, True, self.text_color)
        text_x = rect.x + (rect.width - text_surf.get_width()) // 2
        text_y = rect.y + (rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))

    def get_quest(self) -> Quest:
        """Get the edited quest."""
        # Update name and description from text inputs
        for ti in self.text_inputs:
            if ti.key == 'name':
                self.data['name'] = ti.value
            elif ti.key == 'description':
                self.data['description'] = ti.value

        return Quest(
            id=self.quest.id,
            quest_type=self.data.get('quest_type', QUEST_GATHER_RESOURCE),
            name=self.data.get('name', ''),
            description=self.data.get('description', ''),
            target_type=self.data.get('target_type', QUEST_TARGET_WOOD),
            target_item_id=self.data.get('target_item_id', ''),
            target_amount=self.data.get('target_amount', 10),
            time_limit=self.data.get('time_limit', 0),
            difficulty=self.data.get('difficulty', 1),
            target_location_id=self.data.get('target_location_id', ''),
            target_location_name=self.data.get('target_location_name', ''),
            target_floor=self.data.get('target_floor', 0),
            reward_gold=self.data.get('reward_gold', 100),
            reward_item_id=self.data.get('reward_item_id', ''),
            reward_item_amount=self.data.get('reward_item_amount', 1),
            reward_exp=self.data.get('reward_exp', 50),
            reward_reputation=self.data.get('reward_reputation', 5),
            is_repeatable=self.data.get('is_repeatable', True),
            cooldown=self.data.get('cooldown', 100),
            min_player_attitude=self.data.get('min_player_attitude', 0),
            min_player_rank=self.data.get('min_player_rank', 0),
            min_player_level=self.data.get('min_player_level', 0),
            fail_attitude_penalty=self.data.get('fail_attitude_penalty', 0),
            completion_event_id=self.data.get('completion_event_id', ''),
            scaling_factor=self.data.get('scaling_factor', 1.1)
        )


class QuestListDialog(Dialog):
    """Dialog for managing quests list for a location."""

    def __init__(self, quests: List[Quest] = None, all_locations: List = None):
        """Initialize quest list dialog.

        Args:
            quests: List of quests to edit
            all_locations: List of all locations on the map
        """
        self.quests_copy = []
        for q in (quests or []):
            self.quests_copy.append(Quest(
                id=q.id,
                quest_type=q.quest_type,
                name=q.name,
                description=q.description,
                target_type=q.target_type,
                target_item_id=q.target_item_id,
                target_amount=q.target_amount,
                time_limit=q.time_limit,
                difficulty=q.difficulty,
                target_location_id=q.target_location_id,
                target_location_name=q.target_location_name,
                target_floor=q.target_floor,
                reward_gold=q.reward_gold,
                reward_item_id=q.reward_item_id,
                reward_item_amount=q.reward_item_amount,
                reward_exp=q.reward_exp,
                reward_reputation=q.reward_reputation,
                is_repeatable=q.is_repeatable,
                cooldown=q.cooldown,
                min_player_attitude=q.min_player_attitude,
                min_player_rank=q.min_player_rank,
                min_player_level=q.min_player_level,
                fail_attitude_penalty=q.fail_attitude_penalty,
                completion_event_id=q.completion_event_id,
                scaling_factor=q.scaling_factor
            ))
        self.all_locations = all_locations or []

        super().__init__("Управление квестами", width=550, height=450)

        self._scroll_offset = 0
        self._visible_count = 8
        self._selected_index: Optional[int] = None

        # Callback for opening quest edit dialog
        self.on_edit_quest: Optional[Callable[[Quest, int], None]] = None

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        # Bottom buttons
        self.buttons.append(DialogButton(
            rect=pygame.Rect(10, btn_y, btn_width, btn_height),
            text="Добавить",
            action="add"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(120, btn_y, btn_width, btn_height),
            text="Редактировать",
            action="edit"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(230, btn_y, btn_width, btn_height),
            text="Удалить",
            action="delete"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Закрыть",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            if event.button == 1:
                # Check quest row click
                list_y = 60
                for i in range(self._visible_count):
                    actual_idx = i + self._scroll_offset
                    if actual_idx >= len(self.quests_copy):
                        break
                    row_rect = pygame.Rect(10, list_y + i * 40, self.width - 40, 38)
                    if row_rect.collidepoint(local_x, local_y):
                        self._selected_index = actual_idx
                        return True

            elif event.button == 4:  # Scroll up
                if self._scroll_offset > 0:
                    self._scroll_offset -= 1
                return True

            elif event.button == 5:  # Scroll down
                max_offset = max(0, len(self.quests_copy) - self._visible_count)
                if self._scroll_offset < max_offset:
                    self._scroll_offset += 1
                return True

        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(local_x, local_y):
                    if button.action == "add":
                        self._add_quest()
                        return True
                    elif button.action == "edit":
                        self._edit_selected()
                        return True
                    elif button.action == "delete":
                        self._delete_selected()
                        return True

        return super().handle_event(event)

    def _add_quest(self) -> None:
        """Add a new quest."""
        if self.on_edit_quest:
            self.on_edit_quest(None, -1)

    def _edit_selected(self) -> None:
        """Edit selected quest."""
        if self._selected_index is not None and 0 <= self._selected_index < len(self.quests_copy):
            if self.on_edit_quest:
                self.on_edit_quest(self.quests_copy[self._selected_index], self._selected_index)

    def _delete_selected(self) -> None:
        """Delete selected quest."""
        if self._selected_index is not None and 0 <= self._selected_index < len(self.quests_copy):
            self.quests_copy.pop(self._selected_index)
            if self._selected_index >= len(self.quests_copy):
                self._selected_index = len(self.quests_copy) - 1 if self.quests_copy else None

    def update_quest(self, quest: Quest, index: int) -> None:
        """Update or add a quest."""
        if index >= 0 and index < len(self.quests_copy):
            self.quests_copy[index] = quest
        else:
            self.quests_copy.append(quest)
            self._selected_index = len(self.quests_copy) - 1

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the quest list dialog."""
        if not self.visible:
            return

        # Draw dialog base
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, dialog_rect)
        pygame.draw.rect(surface, self.border_color, dialog_rect, 1)

        # Draw title bar
        title_rect = pygame.Rect(self.x, self.y, self.width, 35)
        pygame.draw.rect(surface, self.title_bg, title_rect)
        title_text = self.font_title.render(self.title, True, self.text_color)
        surface.blit(title_text, (self.x + 10, self.y + 8))

        # Draw quest count
        count_text = self.font.render(f"Квестов: {len(self.quests_copy)}", True, (180, 180, 180))
        surface.blit(count_text, (self.x + self.width - 100, self.y + 42))

        # Draw header
        header_y = self.y + 45
        pygame.draw.rect(surface, self.title_bg, (self.x + 10, header_y, self.width - 40, 25))
        headers = [("Название", 10), ("Тип", 200), ("Сложн.", 350), ("Награда", 420)]
        for text, offset in headers:
            surf = self.font.render(text, True, (180, 180, 180))
            surface.blit(surf, (self.x + 15 + offset, header_y + 4))

        # Draw quest list
        list_y = 60
        for i in range(self._visible_count):
            actual_idx = i + self._scroll_offset
            if actual_idx >= len(self.quests_copy):
                break

            quest = self.quests_copy[actual_idx]
            row_y = self.y + list_y + i * 40

            # Row background
            row_rect = pygame.Rect(self.x + 10, row_y, self.width - 40, 38)
            if actual_idx == self._selected_index:
                pygame.draw.rect(surface, self.button_primary, row_rect)
            elif actual_idx % 2 == 0:
                pygame.draw.rect(surface, (50, 50, 55), row_rect)
            else:
                pygame.draw.rect(surface, (40, 40, 45), row_rect)

            # Quest name
            name = quest.name[:25] if quest.name else "Без названия"
            name_surf = self.font.render(name, True, self.text_color)
            surface.blit(name_surf, (self.x + 15, row_y + 10))

            # Quest type
            type_name = quest.get_type_display()[:15]
            type_surf = self.font.render(type_name, True, (180, 180, 180))
            surface.blit(type_surf, (self.x + 210, row_y + 10))

            # Difficulty
            diff_name = quest.get_difficulty_display()[:10]
            diff_surf = self.font.render(diff_name, True, (180, 180, 180))
            surface.blit(diff_surf, (self.x + 360, row_y + 10))

            # Reward (gold)
            reward_text = f"{quest.reward_gold}g"
            reward_surf = self.font.render(reward_text, True, (255, 215, 0))
            surface.blit(reward_surf, (self.x + 430, row_y + 10))

        # Draw scrollbar if needed
        if len(self.quests_copy) > self._visible_count:
            scrollbar_height = self._visible_count * 40
            total_height = len(self.quests_copy) * 40
            thumb_height = max(20, int(scrollbar_height * self._visible_count / len(self.quests_copy)))
            thumb_y = int(self._scroll_offset / (len(self.quests_copy) - self._visible_count) * (scrollbar_height - thumb_height))

            sb_x = self.x + self.width - 25
            sb_y = self.y + 70
            pygame.draw.rect(surface, self.slider_bg, (sb_x, sb_y, 10, scrollbar_height))
            pygame.draw.rect(surface, self.button_color, (sb_x, sb_y + thumb_y, 10, thumb_height))

        # Draw buttons
        for i, button in enumerate(self.buttons):
            self._draw_button(surface, button, i == self.hovered_button)

    def _draw_button(self, surface: pygame.Surface, button: DialogButton, hovered: bool) -> None:
        """Draw a dialog button."""
        rect = button.rect.move(self.x, self.y)
        if button.primary:
            color = self.button_primary
        elif hovered:
            color = self.button_hover
        else:
            color = self.button_color
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, self.border_color, rect, 1)

        text_surf = self.font.render(button.text, True, self.text_color)
        text_x = rect.x + (rect.width - text_surf.get_width()) // 2
        text_y = rect.y + (rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))

    def get_quests(self) -> List[Quest]:
        """Get the edited quests list."""
        return [q for q in self.quests_copy if not q.is_empty()]
