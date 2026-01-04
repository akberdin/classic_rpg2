"""
Общие виджеты для Items Config Editor
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict, Any


class ScrollableFrame(ttk.Frame):
    """Фрейм с прокруткой"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Canvas для прокрутки
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Привязка изменения размера
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Привязка колеса мыши
        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        width: int = 20,
        value: str = "",
        readonly: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side="left", padx=(0, 5))

        self.var = tk.StringVar(value=value)
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        if readonly:
            self.entry.configure(state="readonly")
        self.entry.pack(side="left", fill="x", expand=True)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledSpinbox(ttk.Frame):
    """Спинбокс с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        value: float = 0,
        width: int = 10,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side="left", padx=(0, 5))

        self.var = tk.DoubleVar(value=value)
        self.spinbox = ttk.Spinbox(
            self,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=self.var,
            width=width
        )
        self.spinbox.pack(side="left")

    def get(self) -> float:
        try:
            return self.var.get()
        except tk.TclError:
            return 0.0

    def get_int(self) -> int:
        return int(self.get())

    def set(self, value: float):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledCombobox(ttk.Frame):
    """Комбобокс с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        values: List[str],
        value: str = "",
        width: int = 15,
        readonly: bool = True,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side="left", padx=(0, 5))

        self.var = tk.StringVar(value=value)
        state = "readonly" if readonly else "normal"
        self.combobox = ttk.Combobox(
            self,
            textvariable=self.var,
            values=values,
            state=state,
            width=width
        )
        self.combobox.pack(side="left")

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def set_values(self, values: List[str]):
        self.combobox["values"] = values

    def bind_change(self, callback: Callable):
        self.combobox.bind("<<ComboboxSelected>>", lambda e: callback())


class LabeledCheckbox(ttk.Frame):
    """Чекбокс с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        value: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.var = tk.BooleanVar(value=value)
        self.checkbox = ttk.Checkbutton(self, text=label, variable=self.var)
        self.checkbox.pack(side="left")

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class ColorPicker(ttk.Frame):
    """Выбор цвета RGB"""

    def __init__(
        self,
        parent,
        label: str,
        color: List[int] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        if color is None:
            color = [255, 255, 255]

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side="left", padx=(0, 5))

        self.r_var = tk.IntVar(value=color[0])
        self.g_var = tk.IntVar(value=color[1])
        self.b_var = tk.IntVar(value=color[2])

        # R
        ttk.Label(self, text="R:").pack(side="left")
        self.r_spinbox = ttk.Spinbox(
            self, from_=0, to=255, textvariable=self.r_var, width=4,
            command=self._update_preview
        )
        self.r_spinbox.pack(side="left", padx=2)

        # G
        ttk.Label(self, text="G:").pack(side="left")
        self.g_spinbox = ttk.Spinbox(
            self, from_=0, to=255, textvariable=self.g_var, width=4,
            command=self._update_preview
        )
        self.g_spinbox.pack(side="left", padx=2)

        # B
        ttk.Label(self, text="B:").pack(side="left")
        self.b_spinbox = ttk.Spinbox(
            self, from_=0, to=255, textvariable=self.b_var, width=4,
            command=self._update_preview
        )
        self.b_spinbox.pack(side="left", padx=2)

        # Превью цвета
        self.preview = tk.Label(self, width=4, relief="solid", borderwidth=1)
        self.preview.pack(side="left", padx=5)
        self._update_preview()

        # Привязка изменений
        for var in (self.r_var, self.g_var, self.b_var):
            var.trace_add("write", lambda *args: self._update_preview())

    def _update_preview(self):
        try:
            r = max(0, min(255, self.r_var.get()))
            g = max(0, min(255, self.g_var.get()))
            b = max(0, min(255, self.b_var.get()))
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.preview.configure(bg=color)
        except tk.TclError:
            pass

    def get(self) -> List[int]:
        try:
            return [self.r_var.get(), self.g_var.get(), self.b_var.get()]
        except tk.TclError:
            return [255, 255, 255]

    def set(self, color: List[int]):
        if len(color) >= 3:
            self.r_var.set(color[0])
            self.g_var.set(color[1])
            self.b_var.set(color[2])


class RangeEditor(ttk.Frame):
    """Редактор диапазона [min, max]"""

    def __init__(
        self,
        parent,
        label: str,
        range_values: List[int] = None,
        from_: int = 0,
        to: int = 100,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        if range_values is None:
            range_values = [0, 0]

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side="left", padx=(0, 5))

        self.min_var = tk.IntVar(value=range_values[0] if range_values else 0)
        self.max_var = tk.IntVar(value=range_values[1] if len(range_values) > 1 else 0)

        ttk.Label(self, text="от:").pack(side="left")
        self.min_spinbox = ttk.Spinbox(
            self, from_=from_, to=to, textvariable=self.min_var, width=6
        )
        self.min_spinbox.pack(side="left", padx=2)

        ttk.Label(self, text="до:").pack(side="left")
        self.max_spinbox = ttk.Spinbox(
            self, from_=from_, to=to, textvariable=self.max_var, width=6
        )
        self.max_spinbox.pack(side="left", padx=2)

    def get(self) -> List[int]:
        try:
            return [self.min_var.get(), self.max_var.get()]
        except tk.TclError:
            return [0, 0]

    def set(self, range_values: List[int]):
        if range_values and len(range_values) >= 2:
            self.min_var.set(range_values[0])
            self.max_var.set(range_values[1])


class ListEditor(ttk.Frame):
    """Редактор списка строк"""

    def __init__(
        self,
        parent,
        label: str,
        values: List[str] = None,
        available_values: List[str] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        if values is None:
            values = []
        if available_values is None:
            available_values = []

        self.available_values = available_values

        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Label(header, text=label).pack(side="left")

        # Список
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.listbox = tk.Listbox(list_frame, height=4, selectmode="single")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for v in values:
            self.listbox.insert(tk.END, v)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x")

        if available_values:
            self.add_var = tk.StringVar()
            self.add_combo = ttk.Combobox(
                btn_frame, textvariable=self.add_var,
                values=available_values, state="readonly", width=15
            )
            self.add_combo.pack(side="left", padx=2)
        else:
            self.add_var = tk.StringVar()
            self.add_entry = ttk.Entry(btn_frame, textvariable=self.add_var, width=15)
            self.add_entry.pack(side="left", padx=2)

        ttk.Button(btn_frame, text="+", width=3, command=self._add_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="-", width=3, command=self._remove_item).pack(side="left", padx=2)

    def _add_item(self):
        value = self.add_var.get().strip()
        if value and value not in self.listbox.get(0, tk.END):
            self.listbox.insert(tk.END, value)
        self.add_var.set("")

    def _remove_item(self):
        selection = self.listbox.curselection()
        if selection:
            self.listbox.delete(selection[0])

    def get(self) -> List[str]:
        return list(self.listbox.get(0, tk.END))

    def set(self, values: List[str]):
        self.listbox.delete(0, tk.END)
        for v in values:
            self.listbox.insert(tk.END, v)


class DictEditor(ttk.Frame):
    """Редактор словаря ключ-значение"""

    def __init__(
        self,
        parent,
        label: str,
        data: Dict[str, Any] = None,
        key_label: str = "Ключ",
        value_label: str = "Значение",
        available_keys: List[str] = None,
        value_type: str = "int",  # int, float, str
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        if data is None:
            data = {}

        self.available_keys = available_keys
        self.value_type = value_type

        # Заголовок
        ttk.Label(self, text=label, font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        # Treeview для отображения
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, pady=5)

        columns = ("key", "value")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=4)
        self.tree.heading("key", text=key_label)
        self.tree.heading("value", text=value_label)
        self.tree.column("key", width=100)
        self.tree.column("value", width=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Заполнение данными
        for k, v in data.items():
            self.tree.insert("", tk.END, values=(k, v))

        # Редактирование
        edit_frame = ttk.Frame(self)
        edit_frame.pack(fill="x")

        # Выбор ключа
        if available_keys:
            self.key_var = tk.StringVar()
            self.key_combo = ttk.Combobox(
                edit_frame, textvariable=self.key_var,
                values=available_keys, state="readonly", width=12
            )
            self.key_combo.pack(side="left", padx=2)
        else:
            self.key_var = tk.StringVar()
            self.key_entry = ttk.Entry(edit_frame, textvariable=self.key_var, width=12)
            self.key_entry.pack(side="left", padx=2)

        # Значение
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(edit_frame, textvariable=self.value_var, width=8)
        self.value_entry.pack(side="left", padx=2)

        # Кнопки
        ttk.Button(edit_frame, text="Добавить", command=self._add_item).pack(side="left", padx=2)
        ttk.Button(edit_frame, text="Удалить", command=self._remove_item).pack(side="left", padx=2)

        # Двойной клик для редактирования
        self.tree.bind("<Double-1>", self._on_double_click)

    def _add_item(self):
        key = self.key_var.get().strip()
        value = self.value_var.get().strip()
        if not key or not value:
            return

        # Проверяем, существует ли уже
        for item in self.tree.get_children():
            if self.tree.item(item)["values"][0] == key:
                # Обновляем существующее
                self.tree.item(item, values=(key, value))
                self.key_var.set("")
                self.value_var.set("")
                return

        self.tree.insert("", tk.END, values=(key, value))
        self.key_var.set("")
        self.value_var.set("")

    def _remove_item(self):
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])

    def _on_double_click(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item[0])["values"]
            self.key_var.set(values[0])
            self.value_var.set(str(values[1]))

    def get(self) -> Dict[str, Any]:
        result = {}
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            key = str(values[0])
            value = values[1]

            if self.value_type == "int":
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            elif self.value_type == "float":
                try:
                    value = float(value)
                except ValueError:
                    value = 0.0

            result[key] = value
        return result

    def set(self, data: Dict[str, Any]):
        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Заполнение
        for k, v in data.items():
            self.tree.insert("", tk.END, values=(k, v))


class SearchableListbox(ttk.Frame):
    """Список с поиском"""

    def __init__(
        self,
        parent,
        items: List[str] = None,
        on_select: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        if items is None:
            items = []

        self.all_items = items
        self.on_select = on_select

        # Поиск
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(search_frame, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_var.trace_add("write", lambda *args: self._filter_items())

        # Список
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode="single", exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        self._populate()

    def _populate(self):
        self.listbox.delete(0, tk.END)
        for item in self.all_items:
            self.listbox.insert(tk.END, item)

    def _filter_items(self):
        search_text = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)

        for item in self.all_items:
            if search_text in item.lower():
                self.listbox.insert(tk.END, item)

    def _on_select(self, event):
        selection = self.listbox.curselection()
        if selection and self.on_select:
            item = self.listbox.get(selection[0])
            self.on_select(item)

    def set_items(self, items: List[str]):
        self.all_items = items
        self._filter_items()

    def get_selection(self) -> Optional[str]:
        selection = self.listbox.curselection()
        if selection:
            return self.listbox.get(selection[0])
        return None

    def select_item(self, item: str):
        self.listbox.selection_clear(0, tk.END)
        for i in range(self.listbox.size()):
            if self.listbox.get(i) == item:
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break
