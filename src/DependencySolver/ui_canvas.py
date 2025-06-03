import tkinter as tk
from tkinter import ttk


class GroupLabel:
    def __init__(self, canvas, name, y):
        self.canvas = canvas
        self.name = name
        self.logical_y = y
        self.item = canvas.create_text(0, 0, text=name, anchor="w", font=("Arial", 12, "bold"), tags="group_label")

    def redraw(self):
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        self.canvas.coords(self.item, 10, self.logical_y * scale)


class DraggableTestBox:
    def __init__(self, canvas, test_name, x, y, width=120, height=40, fill="lightblue"):
        self.canvas = canvas
        self.test_name = test_name
        self.display_name = test_name.split('.')[-1]
        self.width = width
        self.height = height
        self.fill = fill
        self.original_x = x
        self.original_y = y
        self.logical_x = x  # logical (unscaled) coordinates
        self.logical_y = y
        self.group_bounds = None  # tuple (min_y, max_y)

        self.rect = canvas.create_rectangle(0, 0, 0, 0, fill=fill, tags="box")
        self.text = canvas.create_text(0, 0, text="", tags="box")

        self.arrows_out = []
        self.arrows_in = []

        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.text, "<ButtonPress-1>", self.start_drag)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.drag_y_only)
        self.canvas.tag_bind(self.text, "<B1-Motion>", self.drag_y_only)
        self.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.end_drag)
        self.canvas.tag_bind(self.text, "<ButtonRelease-1>", self.end_drag)

        self.canvas.tag_bind(self.rect, "<Enter>", self.show_tooltip)
        self.canvas.tag_bind(self.text, "<Enter>", self.show_tooltip)
        self.canvas.tag_bind(self.rect, "<Leave>", self.hide_tooltip)
        self.canvas.tag_bind(self.text, "<Leave>", self.hide_tooltip)

        self.set_position(x, y)

    def shorten_text(self):
        zoom = getattr(self.canvas.canvas_view, 'scale', 1.0)
        max_chars = int(self.width * zoom / 8)
        return self.display_name if len(self.display_name) <= max_chars else self.display_name[:max_chars - 3] + "..."

    def update_text(self):
        short = self.shorten_text()
        self.canvas.itemconfig(self.text, text=short)

    def start_drag(self, event):
        self.drag_offset_y = self.canvas.canvasy(event.y) - self.get_screen_y()
        self.canvas.canvas_view.push_undo()

    def drag_y_only(self, event):
        new_screen_y = self.canvas.canvasy(event.y) - self.drag_offset_y
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        new_logical_y = new_screen_y / scale

        if self.group_bounds:
            min_y, max_y = self.group_bounds
            new_logical_y = max(min_y, min(max_y, new_logical_y))

        self.logical_y = new_logical_y
        self.redraw()

    def end_drag(self, event):
        self.update_arrows()

    def redraw(self):
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        x = self.logical_x * scale
        y = self.logical_y * scale
        w = self.width * scale
        h = self.height * scale
        self.canvas.coords(self.rect, x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        self.canvas.coords(self.text, x, y)
        self.update_text()
        self.update_arrows()

    def get_screen_x(self):
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        return self.logical_x * scale

    def get_screen_y(self):
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        return self.logical_y * scale

    def set_position(self, x, y):
        self.logical_x = x
        self.logical_y = y
        self.redraw()

    def set_group_bounds(self, min_y, max_y):
        self.group_bounds = (min_y, max_y)

    def reset_position(self):
        self.set_position(self.original_x, self.original_y)

    def update_arrows(self):
        for arrow in self.arrows_out + self.arrows_in:
            arrow.update_position()

    def show_tooltip(self, event):
        if hasattr(self.canvas, 'tooltip') and self.canvas.tooltip:
            self.canvas.delete(self.canvas.tooltip)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.tooltip = self.canvas.create_text(x + 10, y + 10, anchor="nw", text=self.test_name, tag="tooltip", fill="black", font=("Arial", 10))

    def hide_tooltip(self, event):
        if hasattr(self.canvas, 'tooltip') and self.canvas.tooltip:
            self.canvas.delete(self.canvas.tooltip)
            self.canvas.tooltip = None


class TestArrow:
    def __init__(self, canvas, from_box: DraggableTestBox, to_box: DraggableTestBox):
        self.canvas = canvas
        self.from_box = from_box
        self.to_box = to_box
        self.line = canvas.create_line(0, 0, 0, 0, arrow=tk.LAST, fill="black", width=2)
        from_box.arrows_out.append(self)
        to_box.arrows_in.append(self)
        self.update_position()

    def update_position(self):
        scale = getattr(self.canvas.canvas_view, 'scale', 1.0)
        fx = self.from_box.get_screen_x() - (self.from_box.width * scale) / 2
        fy = self.from_box.get_screen_y()
        tx = self.to_box.get_screen_x() + (self.to_box.width * scale) / 2
        ty = self.to_box.get_screen_y()
        self.canvas.coords(self.line, fx, fy, tx, ty)


class CanvasView:
    def __init__(self, canvas, zoom_label):
        self.canvas = canvas
        self.zoom_label = zoom_label
        self.scale = 1.0
        self.zoom_levels = [0.2 + i * 0.1 for i in range(39)]
        self.canvas.tooltip = None
        self.boxes = []
        self.undo_stack = []
        self.redo_stack = []
        self.counter_label = None

    def zoom_in(self):
        current = self.scale
        for level in self.zoom_levels:
            if level > current:
                self.set_zoom(level)
                break

    def zoom_out(self):
        current = self.scale
        for level in reversed(self.zoom_levels):
            if level < current:
                self.set_zoom(level)
                break

    def set_zoom(self, new_scale):
        if new_scale == self.scale:
            return
        self.scale = new_scale
        for box in self.boxes:
            box.redraw()
        self.redraw_labels()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.update_label()

    def zoom_to_fit(self):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        if bw == 0 or bh == 0:
            return
        fit_scale = min(w / bw, h / bh)
        fit_scale = max(0.2, min(4.0, fit_scale))
        self.set_zoom(fit_scale)

    def reset_zoom_and_positions(self):
        self.set_zoom(1.0)
        for box in self.boxes:
            box.reset_position()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def update_label(self):
        self.zoom_label.config(text=f"Zoom: {int(self.scale * 100)}%")
        if self.counter_label:
            count = 0
            if hasattr(self.canvas, "dependency_manager") and hasattr(self.canvas.dependency_manager, "get_total_tests"):
                count = self.canvas.dependency_manager.get_total_tests()
            else:
                count = len(self.boxes)
            self.counter_label.config(text=f"Total Selected Tests: {count}")

    def register_boxes(self, boxes):
        self.boxes = boxes
        for box in self.boxes:
            box.update_text()
        self.update_label()

    def set_counter_label(self, label):
        self.counter_label = label

    def push_undo(self):
        state = [(box.test_name, box.logical_x, box.logical_y) for box in self.boxes]
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        state = self.undo_stack.pop()
        self.redo_stack.append([(box.test_name, box.logical_x, box.logical_y) for box in self.boxes])
        self.restore_state(state)

    def redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append([(box.test_name, box.logical_x, box.logical_y) for box in self.boxes])
        self.restore_state(state)

    def restore_state(self, state):
        box_map = {box.test_name: box for box in self.boxes}
        for name, x, y in state:
            if name in box_map:
                box_map[name].set_position(x, y)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def redraw_labels(self):
        if hasattr(self.canvas, "dependency_manager"):
            for label in self.canvas.dependency_manager.labels:
                label.redraw()


class DependencyCanvasManager():
    def __init__(self, canvas, tests, selected_tests):
        self.canvas = canvas
        self.tests = tests
        self.selected_tests = selected_tests
        self.boxes = {}
        self.labels = []
        self.build_canvas()
        self.canvas.dependency_manager = self

    def get_total_tests(self):
        return sum(len(group) for group in self.groups)

    def build_canvas(self):
        self.canvas.delete("all")
        x_spacing = 200
        y_spacing = 80
        x_start = 150
        y_start = 100
        row_spacing = 100
        color_palette = ["lightblue", "lightgreen", "lightyellow", "lightpink", "lightgray", "#FFD580", "#B0E0E6"]

        def collect_with_dependencies(test, collected):
            if test in collected:
                return
            collected.add(test)
            for dep in self.tests.get(test, {}).get("dependencies", []):
                if dep in self.tests:
                    collect_with_dependencies(dep, collected)

        full_selected = set()
        for test in self.selected_tests:
            collect_with_dependencies(test, full_selected)

        visited = set()
        self.groups = []

        def dfs_group(test, group):
            if test in visited:
                return
            visited.add(test)
            group.add(test)
            for dep in self.tests.get(test, {}).get("dependencies", []):
                if dep in full_selected:
                    dfs_group(dep, group)
            for t in full_selected:
                if test in self.tests.get(t, {}).get("dependencies", []):
                    dfs_group(t, group)

        ungrouped = full_selected.copy()
        while ungrouped:
            group = set()
            dfs_group(next(iter(ungrouped)), group)
            self.groups.append(group)
            ungrouped -= group

        individual_tests = [g for g in self.groups if len(g) == 1]
        grouped_tests = [g for g in self.groups if len(g) > 1]
        grouped_tests.sort(key=lambda g: -len(g))

        individual_group = set.union(*individual_tests) if individual_tests else set()
        sorted_groups = grouped_tests
        if individual_group:
            sorted_groups.append(individual_group) 

        current_y = y_start
        for idx, group in enumerate(grouped_tests):
            group_color = color_palette[idx % len(color_palette)]
            if not any(t in self.selected_tests for t in group):
                continue

            level_map = {}

            def compute_level(test, visited):
                if test in visited:
                    return 0
                visited.add(test)
                if not self.tests[test]["dependencies"]:
                    return 0
                return 1 + max(compute_level(dep, visited.copy()) for dep in self.tests[test]["dependencies"] if dep in full_selected)

            for test in group:
                level_map[test] = compute_level(test, set())

            level_tests = {}
            for test in group:
                level = level_map[test]
                level_tests.setdefault(level, []).append(test)

            max_height = max(len(tests) for tests in level_tests.values())
            level_y_offsets = {lvl: current_y for lvl in level_tests}

            group_name = "Individual Test Cases" if individual_group and group == individual_group else f"Group {idx + 1}"

            label = GroupLabel(self.canvas, f"{group_name} ({len(group)} tests)", current_y - 50)
            self.labels.append(label)
            label.redraw()

            for level in sorted(level_tests):
                for test in sorted(level_tests[level]):
                    x = x_start + level * x_spacing
                    y = level_y_offsets[level]
                    box = DraggableTestBox(self.canvas, test, x, y, fill=group_color)
                    box.set_group_bounds(
                        min_y=(current_y - 10),
                        max_y=(current_y + (max_height + 1) * y_spacing)
                    )
                    self.boxes[test] = box
                    level_y_offsets[level] += y_spacing

            for test in group:
                for dep in self.tests[test]["dependencies"]:
                    if dep in self.boxes and self.boxes[dep].logical_x < self.boxes[test].logical_x:
                        TestArrow(self.canvas, self.boxes[test], self.boxes[dep])

            current_y += (max_height + 1) * y_spacing + row_spacing

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.tooltip = None
