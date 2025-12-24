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


class AnimationFrameItem(ttk.Frame):
    """Элемент кадра анимации с превью и кнопками"""

    def __init__(
        self,
        parent: tk.Widget,
        frame_index: int,
        on_select: Callable = None,
        on_delete: Callable = None,
        on_move_up: Callable = None,
        on_move_down: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.frame_index = frame_index
        self.sprite_path = ""
        self.image = None
        self.photo_image = None

        self.configure(relief=tk.GROOVE, padding=3)

        # Верхняя часть - номер кадра и кнопки
        header = ttk.Frame(self)
        header.pack(fill=tk.X)

        ttk.Label(header, text=f"Кадр {frame_index + 1}", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        if on_move_up:
            ttk.Button(btn_frame, text="↑", width=2, command=lambda: on_move_up(self)).pack(side=tk.LEFT, padx=1)
        if on_move_down:
            ttk.Button(btn_frame, text="↓", width=2, command=lambda: on_move_down(self)).pack(side=tk.LEFT, padx=1)
        if on_delete:
            ttk.Button(btn_frame, text="✕", width=2, command=lambda: on_delete(self)).pack(side=tk.LEFT, padx=1)

        # Превью спрайта
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.X, pady=5)

        self.preview_container = ttk.Frame(preview_frame, width=64, height=64, relief=tk.SUNKEN)
        self.preview_container.pack(side=tk.LEFT, padx=5)
        self.preview_container.pack_propagate(False)

        self.preview_label = ttk.Label(self.preview_container, text="—")
        self.preview_label.pack(expand=True)

        # Кнопка выбора
        select_btn = ttk.Button(preview_frame, text="Выбрать спрайт", command=lambda: on_select(self) if on_select else None)
        select_btn.pack(side=tk.LEFT, padx=5)

        # Путь к файлу
        self.path_label = ttk.Label(preview_frame, text="Не выбран", wraplength=200)
        self.path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def set_sprite(self, path: str, image=None):
        """Установка спрайта"""
        self.sprite_path = path
        self.path_label.configure(text=path if path else "Не выбран")

        if image:
            try:
                # Импорт здесь, чтобы избежать проблем при отсутствии PIL
                from PIL import Image, ImageTk

                # Ресайз для превью
                img = image.copy()
                img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.photo_image, text="")
            except Exception as e:
                self.preview_label.configure(image="", text="!")
        else:
            self.preview_label.configure(image="", text="—")

    def get_data(self) -> Dict[str, Any]:
        return {
            "sprite_path": self.sprite_path,
            "duration_ms": 100,  # По умолчанию
        }


class AnimationPreview(ttk.Frame):
    """Виджет предпросмотра анимации с управлением воспроизведением"""

    def __init__(
        self,
        parent: tk.Widget,
        preview_size: int = 128,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.preview_size = preview_size
        self.frames: List[Any] = []  # PIL Images
        self.photo_frames: List[Any] = []  # PhotoImage для отображения
        self.current_frame = 0
        self.is_playing = False
        self.fps = 10
        self.loop_mode = "loop"  # once, loop, ping_pong
        self.direction = 1  # 1 = вперед, -1 = назад (для ping_pong)
        self.animation_job = None

        # Основной контейнер
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Превью анимации
        preview_container = ttk.Frame(main_frame)
        preview_container.pack(pady=10)

        self.canvas = tk.Canvas(
            preview_container,
            width=preview_size,
            height=preview_size,
            bg="#2c2c2c",
            highlightthickness=1,
            highlightbackground="#555"
        )
        self.canvas.pack()

        # Текст по умолчанию
        self.default_text = self.canvas.create_text(
            preview_size // 2, preview_size // 2,
            text="Нет кадров",
            fill="#888",
            font=("TkDefaultFont", 10)
        )
        self.image_item = None

        # Индикатор кадра
        self.frame_label = ttk.Label(main_frame, text="Кадр: 0 / 0")
        self.frame_label.pack()

        # Панель управления
        controls = ttk.Frame(main_frame)
        controls.pack(pady=10)

        # Кнопки управления воспроизведением
        self.prev_btn = ttk.Button(controls, text="◀◀", width=4, command=self._prev_frame)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.play_btn = ttk.Button(controls, text="▶", width=4, command=self._toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.next_btn = ttk.Button(controls, text="▶▶", width=4, command=self._next_frame)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(controls, text="◼", width=4, command=self._stop)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Настройки
        settings = ttk.Frame(main_frame)
        settings.pack(fill=tk.X, pady=5)

        # FPS
        fps_frame = ttk.Frame(settings)
        fps_frame.pack(fill=tk.X, pady=2)

        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        self.fps_var = tk.IntVar(value=10)
        self.fps_spinbox = ttk.Spinbox(
            fps_frame,
            from_=1, to=60,
            textvariable=self.fps_var,
            width=5,
            command=self._on_fps_change
        )
        self.fps_spinbox.pack(side=tk.LEFT)
        self.fps_spinbox.bind("<Return>", lambda e: self._on_fps_change())

        # Режим воспроизведения
        mode_frame = ttk.Frame(settings)
        mode_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mode_frame, text="Режим:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="loop")
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["once", "loop", "ping_pong"],
            state="readonly",
            width=12
        )
        self.mode_combo.pack(side=tk.LEFT)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda e: self._on_mode_change())

        # Шкала времени (слайдер)
        timeline_frame = ttk.Frame(main_frame)
        timeline_frame.pack(fill=tk.X, pady=5, padx=10)

        self.timeline = ttk.Scale(
            timeline_frame,
            from_=0, to=1,
            orient=tk.HORIZONTAL,
            command=self._on_timeline_change
        )
        self.timeline.pack(fill=tk.X)

    def set_frames(self, images: List[Any]):
        """Установка кадров анимации (PIL Images)"""
        self.frames = images
        self.photo_frames = []

        if not images:
            self.canvas.delete(self.image_item) if self.image_item else None
            self.image_item = None
            self.canvas.itemconfigure(self.default_text, state="normal")
            self.frame_label.configure(text="Кадр: 0 / 0")
            self.timeline.configure(to=1)
            return

        try:
            from PIL import Image, ImageTk

            # Конвертируем все кадры
            for img in images:
                # Ресайз с сохранением пропорций
                img_copy = img.copy()
                img_copy.thumbnail((self.preview_size, self.preview_size), Image.Resampling.LANCZOS)

                # Центрирование на холсте
                photo = ImageTk.PhotoImage(img_copy)
                self.photo_frames.append(photo)

            self.canvas.itemconfigure(self.default_text, state="hidden")
            self.timeline.configure(to=max(0, len(images) - 1))
            self.current_frame = 0
            self._show_frame(0)

        except Exception as e:
            print(f"Error loading frames: {e}")

    def _show_frame(self, index: int):
        """Отображение кадра по индексу"""
        if not self.photo_frames or index < 0 or index >= len(self.photo_frames):
            return

        self.current_frame = index

        # Удаляем старое изображение
        if self.image_item:
            self.canvas.delete(self.image_item)

        # Отображаем новое
        self.image_item = self.canvas.create_image(
            self.preview_size // 2,
            self.preview_size // 2,
            image=self.photo_frames[index],
            anchor=tk.CENTER
        )

        # Обновляем индикаторы
        self.frame_label.configure(text=f"Кадр: {index + 1} / {len(self.photo_frames)}")
        self.timeline.set(index)

    def _toggle_play(self):
        """Переключение воспроизведения"""
        if self.is_playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        """Запуск воспроизведения"""
        if not self.photo_frames:
            return

        self.is_playing = True
        self.play_btn.configure(text="⏸")
        self._animate()

    def _pause(self):
        """Пауза"""
        self.is_playing = False
        self.play_btn.configure(text="▶")
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def _stop(self):
        """Остановка и сброс"""
        self._pause()
        self.current_frame = 0
        self.direction = 1
        self._show_frame(0)

    def _animate(self):
        """Анимация кадра"""
        if not self.is_playing or not self.photo_frames:
            return

        # Следующий кадр
        next_frame = self.current_frame + self.direction

        if self.loop_mode == "once":
            if next_frame >= len(self.photo_frames):
                self._pause()
                return
            elif next_frame < 0:
                next_frame = 0
        elif self.loop_mode == "loop":
            next_frame = next_frame % len(self.photo_frames)
        elif self.loop_mode == "ping_pong":
            if next_frame >= len(self.photo_frames):
                self.direction = -1
                next_frame = len(self.photo_frames) - 2
            elif next_frame < 0:
                self.direction = 1
                next_frame = 1
            next_frame = max(0, min(next_frame, len(self.photo_frames) - 1))

        self._show_frame(next_frame)

        # Следующий тик
        delay = int(1000 / self.fps)
        self.animation_job = self.after(delay, self._animate)

    def _prev_frame(self):
        """Предыдущий кадр"""
        if self.photo_frames:
            new_frame = (self.current_frame - 1) % len(self.photo_frames)
            self._show_frame(new_frame)

    def _next_frame(self):
        """Следующий кадр"""
        if self.photo_frames:
            new_frame = (self.current_frame + 1) % len(self.photo_frames)
            self._show_frame(new_frame)

    def _on_timeline_change(self, value):
        """Обработка изменения таймлайна"""
        if self.photo_frames:
            frame = int(float(value))
            if frame != self.current_frame:
                self._show_frame(frame)

    def _on_fps_change(self):
        """Обработка изменения FPS"""
        try:
            self.fps = max(1, min(60, self.fps_var.get()))
        except tk.TclError:
            self.fps = 10

    def _on_mode_change(self):
        """Обработка изменения режима"""
        self.loop_mode = self.mode_var.get()
        self.direction = 1

    def get_fps(self) -> int:
        return self.fps

    def set_fps(self, fps: int):
        self.fps = max(1, min(60, fps))
        self.fps_var.set(self.fps)

    def get_loop_mode(self) -> str:
        return self.loop_mode

    def set_loop_mode(self, mode: str):
        if mode in ["once", "loop", "ping_pong"]:
            self.loop_mode = mode
            self.mode_var.set(mode)


class AnimationEditor(ttk.Frame):
    """Полный редактор анимации с кадрами и предпросмотром"""

    MAX_FRAMES = 8

    def __init__(
        self,
        parent: tk.Widget,
        assets_path: str = "",
        on_change: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.assets_path = assets_path
        self.on_change = on_change
        self.frame_items: List[AnimationFrameItem] = []
        self.loaded_images: List[Any] = []  # PIL Images

        # Горизонтальный layout
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Левая часть - список кадров
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)

        # Заголовок
        header = ttk.Frame(left_frame)
        header.pack(fill=tk.X, pady=5)

        ttk.Label(header, text="Кадры анимации (1-8)", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)

        self.frame_count_label = ttk.Label(header, text="0 / 8")
        self.frame_count_label.pack(side=tk.RIGHT, padx=10)

        # Кнопка загрузки спрайтов
        ttk.Button(header, text="Загрузить спрайты...", command=self._load_sprites).pack(side=tk.RIGHT)

        # Прокручиваемый список кадров
        self.frames_container = ScrollableFrame(left_frame)
        self.frames_container.pack(fill=tk.BOTH, expand=True)

        # Правая часть - превью
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Предпросмотр", font=("TkDefaultFont", 10, "bold")).pack(pady=5)

        self.preview = AnimationPreview(right_frame, preview_size=128)
        self.preview.pack(fill=tk.BOTH, expand=True)

    def _load_sprites(self):
        """Загрузка нескольких спрайтов для анимации"""
        from tkinter import filedialog, messagebox
        import os

        # Проверяем лимит
        available_slots = self.MAX_FRAMES - len(self.frame_items)
        if available_slots <= 0:
            messagebox.showwarning(
                "Лимит кадров",
                f"Достигнут максимум кадров ({self.MAX_FRAMES}). Удалите существующие кадры для добавления новых."
            )
            return

        initial_dir = self.assets_path
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepaths = filedialog.askopenfilenames(
            title=f"Выберите спрайты (макс. {available_slots})",
            initialdir=initial_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Все файлы", "*.*")
            ]
        )

        if not filepaths:
            return

        # Ограничиваем количество файлов
        if len(filepaths) > available_slots:
            messagebox.showinfo(
                "Ограничение",
                f"Выбрано {len(filepaths)} файлов, но доступно только {available_slots} слотов. "
                f"Будут добавлены первые {available_slots} файлов."
            )
            filepaths = filepaths[:available_slots]

        # Загружаем каждый спрайт
        from PIL import Image

        for filepath in filepaths:
            try:
                # Загружаем изображение
                img = Image.open(filepath)

                # Относительный путь
                try:
                    rel_path = os.path.relpath(filepath, self.assets_path)
                except ValueError:
                    rel_path = filepath

                # Создаем элемент кадра
                frame_item = AnimationFrameItem(
                    self.frames_container.scrollable_frame,
                    frame_index=len(self.frame_items),
                    on_select=self._on_select_sprite,
                    on_delete=self._on_delete_frame,
                    on_move_up=self._on_move_up,
                    on_move_down=self._on_move_down,
                )
                frame_item.pack(fill=tk.X, pady=2, padx=5)

                # Устанавливаем спрайт
                frame_item.set_sprite(rel_path, img)

                self.frame_items.append(frame_item)
                self.loaded_images.append(img)

            except Exception as e:
                print(f"Error loading sprite {filepath}: {e}")

        self._update_frame_count()
        self._update_preview()
        self._notify_change()

    def _on_select_sprite(self, frame_item: AnimationFrameItem):
        """Выбор спрайта для кадра"""
        from tkinter import filedialog
        import os

        initial_dir = self.assets_path
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepath = filedialog.askopenfilename(
            title="Выберите спрайт",
            initialdir=initial_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Все файлы", "*.*")
            ]
        )

        if filepath:
            try:
                from PIL import Image

                # Загружаем изображение
                img = Image.open(filepath)

                # Относительный путь
                try:
                    rel_path = os.path.relpath(filepath, self.assets_path)
                except ValueError:
                    rel_path = filepath

                # Находим индекс кадра
                idx = self.frame_items.index(frame_item)

                # Обновляем данные
                frame_item.set_sprite(rel_path, img)
                self.loaded_images[idx] = img

                # Обновляем превью
                self._update_preview()
                self._notify_change()

            except Exception as e:
                print(f"Error loading sprite: {e}")

    def _on_delete_frame(self, frame_item: AnimationFrameItem):
        """Удаление кадра"""
        if frame_item in self.frame_items:
            idx = self.frame_items.index(frame_item)
            self.frame_items.remove(frame_item)
            del self.loaded_images[idx]
            frame_item.destroy()

            # Перенумеровываем кадры
            for i, item in enumerate(self.frame_items):
                item.frame_index = i

            self._update_frame_count()
            self._update_preview()
            self._notify_change()

    def _on_move_up(self, frame_item: AnimationFrameItem):
        """Перемещение кадра вверх"""
        idx = self.frame_items.index(frame_item)
        if idx > 0:
            # Меняем местами
            self.frame_items[idx], self.frame_items[idx-1] = self.frame_items[idx-1], self.frame_items[idx]
            self.loaded_images[idx], self.loaded_images[idx-1] = self.loaded_images[idx-1], self.loaded_images[idx]

            # Перепаковываем виджеты
            self._repack_frames()
            self._update_preview()
            self._notify_change()

    def _on_move_down(self, frame_item: AnimationFrameItem):
        """Перемещение кадра вниз"""
        idx = self.frame_items.index(frame_item)
        if idx < len(self.frame_items) - 1:
            # Меняем местами
            self.frame_items[idx], self.frame_items[idx+1] = self.frame_items[idx+1], self.frame_items[idx]
            self.loaded_images[idx], self.loaded_images[idx+1] = self.loaded_images[idx+1], self.loaded_images[idx]

            # Перепаковываем виджеты
            self._repack_frames()
            self._update_preview()
            self._notify_change()

    def _repack_frames(self):
        """Перепаковка виджетов кадров"""
        for i, item in enumerate(self.frame_items):
            item.frame_index = i
            item.pack_forget()

        for item in self.frame_items:
            item.pack(fill=tk.X, pady=2, padx=5)

    def _update_frame_count(self):
        """Обновление счетчика кадров"""
        self.frame_count_label.configure(text=f"{len(self.frame_items)} / {self.MAX_FRAMES}")

    def _update_preview(self):
        """Обновление превью анимации"""
        valid_images = [img for img in self.loaded_images if img is not None]
        self.preview.set_frames(valid_images)

    def _notify_change(self):
        """Уведомление об изменении"""
        if self.on_change:
            self.on_change()

    def get_frames_data(self) -> List[Dict[str, Any]]:
        """Получение данных кадров"""
        return [item.get_data() for item in self.frame_items]

    def set_frames_data(self, frames: List[Dict[str, Any]]):
        """Установка данных кадров"""
        # Очищаем
        for item in self.frame_items:
            item.destroy()
        self.frame_items.clear()
        self.loaded_images.clear()

        # Добавляем кадры
        for frame_data in frames[:self.MAX_FRAMES]:
            frame_item = AnimationFrameItem(
                self.frames_container.scrollable_frame,
                frame_index=len(self.frame_items),
                on_select=self._on_select_sprite,
                on_delete=self._on_delete_frame,
                on_move_up=self._on_move_up,
                on_move_down=self._on_move_down,
            )
            frame_item.pack(fill=tk.X, pady=2, padx=5)

            # Загружаем спрайт если есть путь
            sprite_path = frame_data.get("sprite_path", "")
            if sprite_path:
                try:
                    from PIL import Image
                    import os

                    full_path = os.path.join(self.assets_path, sprite_path)
                    if os.path.exists(full_path):
                        img = Image.open(full_path)
                        frame_item.set_sprite(sprite_path, img)
                        self.loaded_images.append(img)
                    else:
                        frame_item.set_sprite(sprite_path, None)
                        self.loaded_images.append(None)
                except Exception:
                    frame_item.set_sprite(sprite_path, None)
                    self.loaded_images.append(None)
            else:
                self.loaded_images.append(None)

            self.frame_items.append(frame_item)

        self._update_frame_count()
        self._update_preview()

    def get_fps(self) -> int:
        return self.preview.get_fps()

    def set_fps(self, fps: int):
        self.preview.set_fps(fps)

    def get_loop_mode(self) -> str:
        return self.preview.get_loop_mode()

    def set_loop_mode(self, mode: str):
        self.preview.set_loop_mode(mode)
