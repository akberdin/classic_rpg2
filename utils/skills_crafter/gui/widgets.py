"""
Кастомные виджеты для Skills Crafter GUI
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, List, Dict


class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        width: int = 30,
        default: str = "",
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = tk.StringVar(value=default)
        self.entry = ttk.Entry(self, textvariable=self.var, width=width, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if tooltip:
            self._create_tooltip(tooltip)

    def _create_tooltip(self, text: str):
        """Создание всплывающей подсказки"""
        tooltip = ToolTip(self.entry, text)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledSpinbox(ttk.Frame):
    """Числовое поле с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        default: float = 0,
        width: int = 10,
        is_float: bool = False,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.is_float = is_float

        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        if is_float:
            self.var = tk.DoubleVar(value=default)
        else:
            self.var = tk.IntVar(value=int(default))

        self.spinbox = ttk.Spinbox(
            self,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=self.var,
            width=width,
            **kwargs
        )
        self.spinbox.pack(side=tk.LEFT)

        if tooltip:
            ToolTip(self.spinbox, tooltip)

    def get(self) -> float:
        try:
            return float(self.var.get()) if self.is_float else int(self.var.get())
        except (ValueError, tk.TclError):
            return 0.0 if self.is_float else 0

    def set(self, value: float):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledCombobox(ttk.Frame):
    """Выпадающий список с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        values: List[str],
        display_names: Optional[Dict[str, str]] = None,
        default: str = "",
        width: int = 25,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.values = values
        self.display_names = display_names or {}
        self.reverse_names = {v: k for k, v in self.display_names.items()}

        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = tk.StringVar()
        display_values = [self.display_names.get(v, v) for v in values]
        self.combobox = ttk.Combobox(
            self,
            textvariable=self.var,
            values=display_values,
            width=width,
            state="readonly",
            **kwargs
        )
        self.combobox.pack(side=tk.LEFT)

        # Установить значение по умолчанию
        if default:
            self.set(default)
        elif values:
            self.set(values[0])

        if tooltip:
            ToolTip(self.combobox, tooltip)

    def get(self) -> str:
        """Получить реальное значение (не отображаемое)"""
        display = self.var.get()
        return self.reverse_names.get(display, display)

    def set(self, value: str):
        """Установить значение (передается реальное значение)"""
        display = self.display_names.get(value, value)
        self.var.set(display)

    def bind_change(self, callback: Callable):
        self.combobox.bind("<<ComboboxSelected>>", lambda e: callback())


class LabeledCheckbox(ttk.Frame):
    """Чекбокс с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        default: bool = False,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)

        self.var = tk.BooleanVar(value=default)
        self.checkbox = ttk.Checkbutton(
            self, text=label, variable=self.var, **kwargs
        )
        self.checkbox.pack(side=tk.LEFT)

        if tooltip:
            ToolTip(self.checkbox, tooltip)

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class ScrollableFrame(ttk.Frame):
    """Прокручиваемый фрейм"""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent)

        # Canvas для прокрутки
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Прокрутка колесом мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Привязка изменения размера canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class CollapsibleFrame(ttk.Frame):
    """Сворачиваемая секция"""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        expanded: bool = True,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self._expanded = expanded

        # Заголовок
        self.header = ttk.Frame(self)
        self.header.pack(fill=tk.X)

        self.toggle_btn = ttk.Button(
            self.header,
            text="▼" if expanded else "▶",
            width=2,
            command=self._toggle
        )
        self.toggle_btn.pack(side=tk.LEFT)

        self.title_label = ttk.Label(
            self.header, text=title, font=("TkDefaultFont", 10, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=5)

        # Содержимое
        self.content = ttk.Frame(self)
        if expanded:
            self.content.pack(fill=tk.BOTH, expand=True, pady=5)

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.content.pack(fill=tk.BOTH, expand=True, pady=5)
            self.toggle_btn.configure(text="▼")
        else:
            self.content.pack_forget()
            self.toggle_btn.configure(text="▶")


class ToolTip:
    """Всплывающая подсказка"""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            padding=5
        )
        label.pack()

    def _hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class StatusEffectEditor(ttk.Frame):
    """Редактор одного статус-эффекта"""

    def __init__(
        self,
        parent: tk.Widget,
        effect_types: Dict[str, str],
        on_delete: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.effect_types = effect_types
        self.on_delete = on_delete

        # Основной контейнер
        self.configure(relief=tk.GROOVE, padding=5)

        # Заголовок с кнопкой удаления
        header = ttk.Frame(self)
        header.pack(fill=tk.X)

        self.type_combo = LabeledCombobox(
            header,
            "Тип эффекта:",
            values=list(effect_types.keys()),
            display_names=effect_types,
            width=20
        )
        self.type_combo.pack(side=tk.LEFT)

        if on_delete:
            delete_btn = ttk.Button(header, text="✕", width=3, command=self._delete)
            delete_btn.pack(side=tk.RIGHT)

        # Параметры
        params = ttk.Frame(self)
        params.pack(fill=tk.X, pady=5)

        # Первый ряд
        row1 = ttk.Frame(params)
        row1.pack(fill=tk.X)

        self.chance_base = LabeledSpinbox(
            row1, "Шанс (база):", 0, 1, 0.1, 1.0, is_float=True,
            tooltip="Базовый шанс срабатывания (1.0 = 100%)"
        )
        self.chance_base.pack(side=tk.LEFT, padx=5)

        self.chance_per_rank = LabeledSpinbox(
            row1, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.chance_per_rank.pack(side=tk.LEFT, padx=5)

        # Второй ряд
        row2 = ttk.Frame(params)
        row2.pack(fill=tk.X, pady=2)

        self.duration_base = LabeledSpinbox(
            row2, "Длительность:", 0, 20, 1, 3,
            tooltip="Базовая длительность в ходах"
        )
        self.duration_base.pack(side=tk.LEFT, padx=5)

        self.duration_per_rank = LabeledSpinbox(
            row2, "+ за ранг:", 0, 5, 1, 0
        )
        self.duration_per_rank.pack(side=tk.LEFT, padx=5)

        # Третий ряд
        row3 = ttk.Frame(params)
        row3.pack(fill=tk.X, pady=2)

        self.value_base = LabeledSpinbox(
            row3, "Значение:", 0, 100, 1, 5, is_float=True,
            tooltip="Урон/лечение/бонус за ход"
        )
        self.value_base.pack(side=tk.LEFT, padx=5)

        self.value_per_rank = LabeledSpinbox(
            row3, "+ за ранг:", 0, 20, 1, 2, is_float=True
        )
        self.value_per_rank.pack(side=tk.LEFT, padx=5)

    def _delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.destroy()

    def get_data(self) -> Dict[str, Any]:
        return {
            "effect_type": self.type_combo.get(),
            "chance_base": self.chance_base.get(),
            "chance_per_rank": self.chance_per_rank.get(),
            "duration_base": int(self.duration_base.get()),
            "duration_per_rank": int(self.duration_per_rank.get()),
            "value_base": self.value_base.get(),
            "value_per_rank": self.value_per_rank.get(),
        }

    def set_data(self, data: Dict[str, Any]):
        self.type_combo.set(data.get("effect_type", "poison"))
        self.chance_base.set(data.get("chance_base", 1.0))
        self.chance_per_rank.set(data.get("chance_per_rank", 0))
        self.duration_base.set(data.get("duration_base", 3))
        self.duration_per_rank.set(data.get("duration_per_rank", 0))
        self.value_base.set(data.get("value_base", 5))
        self.value_per_rank.set(data.get("value_per_rank", 2))


class ScalingEditor(ttk.Frame):
    """Редактор масштабирования по атрибуту"""

    def __init__(
        self,
        parent: tk.Widget,
        attributes: Dict[str, str],
        on_delete: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.attributes = attributes
        self.on_delete = on_delete

        self.configure(relief=tk.GROOVE, padding=3)

        row = ttk.Frame(self)
        row.pack(fill=tk.X)

        self.attr_combo = LabeledCombobox(
            row,
            "Атрибут:",
            values=list(attributes.keys()),
            display_names=attributes,
            width=15
        )
        self.attr_combo.pack(side=tk.LEFT, padx=2)

        self.multiplier = LabeledSpinbox(
            row, "× ", 0, 10, 0.1, 1.0, is_float=True, width=6
        )
        self.multiplier.pack(side=tk.LEFT, padx=2)

        self.per_rank = LabeledSpinbox(
            row, "+ за ранг:", 0, 2, 0.1, 0, is_float=True, width=6
        )
        self.per_rank.pack(side=tk.LEFT, padx=2)

        if on_delete:
            delete_btn = ttk.Button(row, text="✕", width=2, command=self._delete)
            delete_btn.pack(side=tk.RIGHT)

    def _delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.destroy()

    def get_data(self) -> Dict[str, Any]:
        return {
            "attribute": self.attr_combo.get(),
            "multiplier": self.multiplier.get(),
            "multiplier_per_rank": self.per_rank.get(),
        }

    def set_data(self, data: Dict[str, Any]):
        self.attr_combo.set(data.get("attribute", "strength"))
        self.multiplier.set(data.get("multiplier", 1.0))
        self.per_rank.set(data.get("multiplier_per_rank", 0))
