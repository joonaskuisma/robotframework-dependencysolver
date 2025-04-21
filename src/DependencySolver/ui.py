import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

from DependencySolver._version import __version__

class TestUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"DependencySolver-UI {__version__}")
        self.root.protocol("WM_DELETE_WINDOW", self.export_and_close)

        self.tests = {}
        self.test_order = []
        self.current_selected_tests = []
        self.parse_tests_file()
        self.tooltip = None
        self.active_scroll_target = None

        # Menubar
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Show Chosen Tests", command=self.update_ui)
        filemenu.add_command(label="Save and Close", command=self.export_and_close)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Info", command=self.show_info)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.root.config(menu=menubar)

        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Reset zoom", command=self.reset_zoom)
        menubar.add_cascade(label="View", menu=viewmenu)

        # Main panel which divides left (Treeview) and right (Canvas) areas
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Treeview container frame
        self.tree_frame = ttk.Frame(self.paned)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10, expand=True)

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll_y.set)
        self.tree.heading("#0", text="Test Cases")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")

        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.test_vars = {}
        self.build_tree()
        self.paned.add(self.tree_frame, weight=1)

        # Canvas-side (scrollable)
        self.canvas_frame = ttk.Frame(self.paned)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.grid(row=0, column=1, sticky="ns")

        self.scroll_x = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.paned.add(self.canvas_frame, weight=4)

        self.canvas_toolbar = ttk.Frame(self.canvas_frame)
        self.canvas_toolbar.place(relx=1.0, x=-30, y=10, anchor="ne")

        self.total_selected_label = tk.Label(self.canvas_toolbar, text="Total Selected Tests: 0", font=("Arial", 10, "italic"))
        self.total_selected_label.pack(side=tk.TOP, padx=10)
        ttk.Button(self.canvas_toolbar, text="+", width=2, command=self._on_key_zoom_in).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="-", width=2, command=self._on_key_zoom_out).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="⭯", width=2, command=self.reset_zoom).pack(side=tk.LEFT)

        zoom_fit_button = ttk.Button(self.canvas_toolbar, text="Zoom to Fit", command=self.zoom_to_fit)
        zoom_fit_button.pack(side=tk.LEFT)

        self.zoom_label = ttk.Label(self.canvas_toolbar, text="Zoom: 100%")
        self.zoom_label.pack(side=tk.LEFT, padx=10)

        # Define fixed zoom levels (as float values)
        self.zoom_levels = [0.2 + i * 0.1 for i in range(39)]  # 0.2 to 4.0 by 0.1
        self.canvas_scale = 1.0
        self.canvas.bind_all("<Control-MouseWheel>", self._on_canvas_zoom)

        self.tree.bind("<Enter>", lambda e: self._set_scroll_target("tree"))
        self.tree.bind("<Leave>", lambda e: self._set_scroll_target(None))

        self.canvas.bind("<Enter>", lambda e: self._set_scroll_target("canvas"))
        self.canvas.bind("<Leave>", lambda e: self._set_scroll_target(None))

        # Mouse scroll
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Shift-MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)  # Linux up
        self.root.bind_all("<Button-5>", self._on_mousewheel)  # Linux down


    def _set_scroll_target(self, target):
        self.active_scroll_target = target


    def _on_mousewheel(self, event):
        is_shift = (event.state & 0x0001) != 0  # Shift = bit 0x0001

        if event.num in (4, 5):  # Linux
            direction = -1 if event.num == 4 else 1
            if self.active_scroll_target == "canvas":
                self.canvas.yview_scroll(direction, "units")
            elif self.active_scroll_target == "tree":
                self.tree.yview_scroll(direction, "units")
            return

        # Windows/macOS (MouseWheel)
        delta = int(event.delta / 120)
        if self.active_scroll_target == "canvas":
            if is_shift:
                self.canvas.xview_scroll(-delta, "units")
            else:
                self.canvas.yview_scroll(-delta, "units")
        elif self.active_scroll_target == "tree":
            if not is_shift:
                self.tree.yview_scroll(-delta, "units")


    def _bind_canvas_scroll(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_canvas_scroll)
        self.canvas.bind_all("<Button-4>", self._on_canvas_scroll)  # Linux support
        self.canvas.bind_all("<Button-5>", self._on_canvas_scroll)


    def _unbind_canvas_scroll(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")


    def _on_canvas_scroll(self, event):
        if event.delta:
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        elif event.num == 4:  # Linux: scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux: scroll down
            self.canvas.yview_scroll(1, "units")


    def build_tree(self):
        self.tree_nodes = {}  # path -> item_id
        for test_name in self.test_order:
            parts = test_name.split('.')
            path = ""
            parent = ""
            for i, part in enumerate(parts):
                path = '.'.join(parts[:i + 1])
                if path not in self.tree_nodes:
                    label = part
                    node_id = self.tree.insert(parent, "end", text=f"[ ] {label}", open=True)
                    self.tree_nodes[path] = node_id
                parent = self.tree_nodes[path]

            # Last part is test itself
            var = tk.BooleanVar()
            var.set(False)
            self.test_vars[test_name] = var

            display_text = f"[ ] {parts[-1]}"
            self.tree.item(self.tree_nodes[path], text=display_text)

            self.tree.tag_bind(test_name, '<Button-1>', lambda e, name=test_name: self.toggle_checkbox(name))

        # Click events on whole tree
        self.tree.bind("<Button-1>", self.on_tree_click)


    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        full_path = self.get_full_path(item_id)

        # Prevent checkbox toggle if clicked to the far left (on top of expander)
        if event.x < 20 * len(full_path.split(".")):
            return
        
        # Checking whether the tests include
        if full_path in self.test_vars:
            self.toggle_checkbox(full_path)
        else:
            self.toggle_group_checkbox(item_id)
        self.update_ui()


    def toggle_checkbox(self, test_name):
        var = self.test_vars[test_name]
        var.set(not var.get())
        item_id = self.tree_nodes[test_name]
        new_state = "[x]" if var.get() else "[ ]"
        label = test_name.split('.')[-1]
        self.tree.item(item_id, text=f"{new_state} {label}")


    def toggle_group_checkbox(self, item_id):
        # Determine the selected status (x or no)
        current_text = self.tree.item(item_id, "text")
        new_state = not current_text.strip().startswith("[x]")

        # Update current node
        self.update_tree_item_checkbox(item_id, new_state)

        # Recursively update all child nodes
        def update_children_recursive(parent_id):
            for child_id in self.tree.get_children(parent_id):
                self.update_tree_item_checkbox(child_id, new_state)
                update_children_recursive(child_id)

        update_children_recursive(item_id)


    def update_tree_item_checkbox(self, item_id, state):
        full_path = self.get_full_path(item_id)
        label = self.tree.item(item_id, "text").replace("[x] ", "").replace("[ ] ", "").strip()

        # Update view
        self.tree.item(item_id, text=f"[x] {label}" if state else f"[ ] {label}")

        # If it is a correct test, update the var
        if full_path in self.test_vars:
            self.test_vars[full_path].set(state)


    def update_checkbox_display_recursive(self, item_id):
        text = self.tree.item(item_id, "text")
        full_path = self.get_full_path(item_id)
        if full_path in self.test_vars:
            var = self.test_vars[full_path]
            new_text = text.replace("[x]", "[ ]").replace("[ ]", "[x]" if var.get() else "[ ]")
            self.tree.item(item_id, text=new_text)

        for child_id in self.tree.get_children(item_id):
            self.update_checkbox_display_recursive(child_id)


    def get_full_path(self, item_id):
        parts = []
        while item_id:
            raw_text = self.tree.item(item_id, "text")
            clean_text = raw_text.replace("[ ] ", "").replace("[x] ", "")
            parts.insert(0, clean_text)
            item_id = self.tree.parent(item_id)
        return '.'.join(parts)


    def parse_tests_file(self):
        test_data = """
        --test Tests.suite A.Test A5
        {
        --test Tests.suite A.Test A1
        --test Tests.suite A.Test A2 #DEPENDS Tests.suite A.Test A1
        --test Tests.suite A.Test A3 #DEPENDS Tests.suite A.Test A2
        --test Tests.suite A.Test A4 #DEPENDS Tests.suite A.Test A3
        }
        {
        --test Tests.suite B.Test A6
        --test Tests.suite B.Test A7 #DEPENDS Tests.suite B.Test A6
        --test Tests.suite B.Test A8 #DEPENDS Tests.suite B.Test A6 
        --test Tests.suite B.Test A9 #DEPENDS Tests.suite B.Test A6 
        --test Tests.suite B.Test A10 #DEPENDS Tests.suite B.Test A7
        --test Tests.suite B.Test A11 #DEPENDS Tests.suite B.Test A7
        --test Tests.suite B.Test A12 #DEPENDS Tests.suite B.Test A8 
        --test Tests.suite B.Test A13 #DEPENDS Tests.suite B.Test A8 #DEPENDS Tests.suite B.Test A6
        --test Tests.suite B.Test A14 #DEPENDS Tests.suite B.Test A9 #DEPENDS Tests.suite B.Test A6
        }
        {
        --test Tests.suite C.Test C1
        --test Tests.suite C.Test C2
        --test Tests.suite C.Test C3
        --test Tests.suite C.Test C4 #DEPENDS Tests.suite C.Test C1 #DEPENDS Tests.suite C.Test C2 #DEPENDS Tests.suite C.Test C3
        }
        --test Tests.Test D1
        --test Tests.Test D2
        --test Test E1
        {
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A1 
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A2 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A1
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A3 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A2
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A4 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A3
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A5 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A4
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A6 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A5
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A7 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A6
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A8 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A7
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A9 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A8
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A10 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A9
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A11 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A10
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A12 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A11
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A13 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A12
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A14 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A13
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A15 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A14
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A16 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A15
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A17 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A16
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A18 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A17
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A19 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A18
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A20 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A19
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A21 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A20
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A22 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A21
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A23 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A22
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A24 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A23
        --test Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A25 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.subsubsubsuite A.Test A24
        --test Tests.suite D.subsuite A.subsubsuite A.Test A1
        --test Tests.suite D.subsuite A.subsubsuite A.Test A2 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A1
        --test Tests.suite D.subsuite A.subsubsuite A.Test A3 
        --test Tests.suite D.subsuite A.subsubsuite A.Test A4 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A3
        --test Tests.suite D.subsuite A.subsubsuite A.Test A5 
        --test Tests.suite D.subsuite A.subsubsuite A.Test A6 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A5
        --test Tests.suite D.subsuite A.subsubsuite A.Test A7 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A2 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A4 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A6
        --test Tests.suite D.subsuite A.subsubsuite A.Test A8 
        --test Tests.suite D.subsuite A.subsubsuite A.Test A9 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A8 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A7
        --test Tests.suite D.subsuite A.subsubsuite A.Test A10 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A9
        --test Tests.suite D.subsuite A.subsubsuite A.Test A11 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A9
        --test Tests.suite D.subsuite A.subsubsuite A.Test A12 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A9
        --test Tests.suite D.subsuite A.subsubsuite A.Test A13 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A10 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A11 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A12
        --test Tests.suite D.subsuite A.subsubsuite A.Test A14 
        --test Tests.suite D.subsuite A.subsubsuite A.Test A15
        --test Tests.suite D.subsuite A.subsubsuite A.Test A16
        --test Tests.suite D.subsuite A.subsubsuite A.Test A17 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A14
        --test Tests.suite D.subsuite A.subsubsuite A.Test A18 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A15
        --test Tests.suite D.subsuite A.subsubsuite A.Test A19 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A16
        --test Tests.suite D.subsuite A.subsubsuite A.Test A20 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A17 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A18 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A19
        --test Tests.suite D.subsuite A.subsubsuite A.Test A21 
        --test Tests.suite D.subsuite A.subsubsuite A.Test A22
        --test Tests.suite D.subsuite A.subsubsuite A.Test A23 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A21 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A22
        --test Tests.suite D.subsuite A.subsubsuite A.Test A24 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A20 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A23
        --test Tests.suite D.subsuite A.subsubsuite A.Test A25 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A13 #DEPENDS Tests.suite D.subsuite A.subsubsuite A.Test A24
        --test Tests.suite D.subsuite A.Test A1
        --test Tests.suite D.subsuite A.Test A2
        --test Tests.suite D.subsuite A.Test A3
        --test Tests.suite D.subsuite A.Test A4
        --test Tests.suite D.subsuite A.Test A5
        --test Tests.suite D.subsuite A.Test A6
        --test Tests.suite D.subsuite A.Test A7
        --test Tests.suite D.subsuite A.Test A8
        --test Tests.suite D.subsuite A.Test A9
        --test Tests.suite D.subsuite A.Test A10
        --test Tests.suite D.subsuite A.Test A11
        --test Tests.suite D.subsuite A.Test A12
        --test Tests.suite D.subsuite A.Test A13
        --test Tests.suite D.subsuite A.Test A14
        --test Tests.suite D.subsuite A.Test A15
        --test Tests.suite D.subsuite A.Test A16
        --test Tests.suite D.subsuite A.Test A17
        --test Tests.suite D.subsuite A.Test A18
        --test Tests.suite D.subsuite A.Test A19
        --test Tests.suite D.subsuite A.Test A20
        --test Tests.suite D.subsuite A.Test A21
        --test Tests.suite D.subsuite A.Test A22
        --test Tests.suite D.subsuite A.Test A23
        --test Tests.suite D.subsuite A.Test A24
        --test Tests.suite D.subsuite A.Test A25
        --test Tests.suite D.Test A1
        --test Tests.suite D.Test A2
        --test Tests.suite D.Test A3
        --test Tests.suite D.Test A4
        --test Tests.suite D.Test A5
        --test Tests.suite D.Test A6
        --test Tests.suite D.Test A7
        --test Tests.suite D.Test A8
        --test Tests.suite D.Test A9
        --test Tests.suite D.Test A10
        --test Tests.suite D.Test A11
        --test Tests.suite D.Test A12
        --test Tests.suite D.Test A13
        --test Tests.suite D.Test A14
        --test Tests.suite D.Test A15
        --test Tests.suite D.Test A16
        --test Tests.suite D.Test A17
        --test Tests.suite D.Test A18
        --test Tests.suite D.Test A19
        --test Tests.suite D.Test A20
        --test Tests.suite D.Test A21
        --test Tests.suite D.Test A22
        --test Tests.suite D.Test A23
        --test Tests.suite D.Test A24
        --test Tests.suite D.Test A25
        }
        """
        
        lines = test_data.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('--test'):
                data = line.split("--test ")[1].split("#DEPENDS")
                test_name = data[0].strip()
                deps = []
                for n in range(1, len(data)):
                    deps.append(data[n].strip())
                print("test name:", test_name)
                self.tests[test_name] = {"name": test_name, "dependencies": deps}
                self.test_order.append(test_name)
            

    def build_check_buttons(self):
        # Create checkboxes for all tests
        self.checkbuttons = {}
        for idx, test_name in enumerate(self.test_order):
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.check_frame, text=test_name, variable=var)
            cb.grid(row=idx, sticky='w')
            self.checkbuttons[test_name] = var


    def draw_dependencies(self, selected_tests_original):
        self.current_selected_tests = selected_tests_original.copy()
        self.canvas.delete("all")

        x_spacing = 200
        y_spacing = 80
        x_start = 100
        y_start = 50
        row_spacing = 200

        positions = {}

        def collect_with_dependencies(test, collected):
            if test in collected:
                return
            collected.add(test)
            for dep in self.tests.get(test, {}).get("dependencies", []):
                if dep in self.tests:
                    collect_with_dependencies(dep, collected)

        full_selected = set()
        for test in selected_tests_original:
            collect_with_dependencies(test, full_selected)

        visited = set()
        groups = []

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
            groups.append(group)
            ungrouped -= group

        # Sort groups by size descending, but collect individual ones separately
        individual_tests = [g for g in groups if len(g) == 1]
        grouped_tests = [g for g in groups if len(g) > 1]
        grouped_tests.sort(key=lambda g: -len(g))

        individual_group = set.union(*individual_tests) if individual_tests else set()
        sorted_groups = grouped_tests
        if individual_group:
            sorted_groups.append(individual_group) 

        color_palette = ["lightblue", "lightgreen", "lightyellow", "lightpink", "lightgray", "#FFD580", "#B0E0E6"]
        current_y = y_start

        for idx, group in enumerate(sorted_groups):
            group_color = color_palette[idx % len(color_palette)]

            if not any(t in selected_tests_original for t in group):
                continue

            group_level_map = {}
            def compute_level(test, visited):
                if test in visited:
                    return 0
                visited.add(test)
                if not self.tests[test]["dependencies"]:
                    return 0
                return 1 + max(compute_level(dep, visited.copy()) for dep in self.tests[test]["dependencies"] if dep in full_selected)

            for test in group:
                group_level_map[test] = compute_level(test, set())

            level_tests = {}
            for test in group:
                level = group_level_map[test]
                level_tests.setdefault(level, []).append(test)

            max_height = max(len(tests) for tests in level_tests.values())
            level_y_offsets = {lvl: current_y for lvl in level_tests}

            # Group title
            if individual_group and group == individual_group:
                group_name = "Individual Test Cases"
            else:
                group_name = f"Group {idx + 1}"
            self.canvas.create_text(x_start - 100, current_y - 100,
                                    text=f"{group_name} ({len(group)} tests)",
                                    anchor="w", font=("Arial", 14, "bold"))

            for level in sorted(level_tests):
                for test in sorted(level_tests[level]):
                    x = x_start + level * x_spacing
                    y = level_y_offsets[level]
                    positions[test] = (x, y)
                    box = self.canvas.create_rectangle(x - 60, y - 20, x + 60, y + 20, fill=group_color)
                    display_text = self.shorten_text_to_fit(test.split('.')[-1], 100 * self.canvas_scale)
                    label = self.canvas.create_text(x, y, text=display_text)

                    self.canvas.tag_bind(box, "<Enter>", lambda e, t=test: self.show_tooltip(e, t))
                    self.canvas.tag_bind(box, "<Leave>", self.hide_tooltip)
                    self.canvas.tag_bind(label, "<Enter>", lambda e, t=test: self.show_tooltip(e, t))
                    self.canvas.tag_bind(label, "<Leave>", self.hide_tooltip)

                    level_y_offsets[level] += y_spacing

            # Arrows
            for test in group:
                for dep in self.tests[test]["dependencies"]:
                    if dep in group:
                        x1, y1 = positions[test]
                        x2, y2 = positions[dep]
                        self.canvas.create_line(x1 - 60, y1, x2 + 60, y2, arrow=tk.LAST)

            current_y += (max_height + 1) * y_spacing + row_spacing

        # Show total count
        self.total_selected_label.config(text=f"Total Selected Tests: {len(full_selected)}")

        self.canvas.scale("all", 0, 0, self.canvas_scale, self.canvas_scale)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


    def shorten_text_to_fit(self, text, max_width, font=("TkDefaultFont", 10)):
        test_id = self.canvas.create_text(0, 0, text=text, font=font, anchor="nw", tags="temp")
        bbox = self.canvas.bbox(test_id)
        self.canvas.delete(test_id)

        if not bbox:
            return text  # fallback if font measuring fails

        width = bbox[2] - bbox[0]
        if width <= max_width:
            return text

        # Shorten the text until it fits
        for i in range(len(text), 0, -1):
            shortened = text[:i] + "..."
            test_id = self.canvas.create_text(0, 0, text=shortened, font=font, anchor="nw", tags="temp")
            bbox = self.canvas.bbox(test_id)
            self.canvas.delete(test_id)

            if bbox and (bbox[2] - bbox[0]) <= max_width:
                return shortened

        return "..."  # fallback if nothing works


    def reset_zoom(self):
        self.canvas_scale = 1.0
        self._update_zoom_label()
        self.draw_dependencies(self.current_selected_tests)


    def show_info(self):
        messagebox.showinfo("Instructions", "\n- Select tests from the tree on the left.\n- Selected tests and their dependencies will be drawn on the right.\n- If you select a test, its prerequisites will be automatically selected.\n- Close and save selections by clicking \"Save and Close\".")


    def show_tooltip(self, event, text):
        if self.tooltip:
            self.canvas.delete(self.tooltip)
            self.tooltip = None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.tooltip = self.canvas.create_text(x + 10, y + 10, anchor="nw", text=text, tag="tooltip", fill="black", font=("Arial", 10))


    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.canvas.delete(self.tooltip)
            self.tooltip = None


    def _on_key_zoom_in(self):
        current = self.canvas_scale
        for level in self.zoom_levels:
            if level > current:
                self._zoom_canvas_direct(level)
                break


    def _on_key_zoom_out(self):
        current = self.canvas_scale
        for level in reversed(self.zoom_levels):
            if level < current:
                self._zoom_canvas_direct(level)
                break


    def _zoom_canvas_direct(self, new_scale):
        if new_scale == self.canvas_scale:
            return

        self.canvas_scale = new_scale
        self._update_zoom_label()
        self.draw_dependencies(self.current_selected_tests)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    
    def _on_canvas_zoom(self, event):
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        old_scale = self.canvas_scale
        new_scale = old_scale * zoom_factor
        new_scale = max(0.2, min(4.0, new_scale))

        if abs(new_scale - old_scale) < 0.001:
            return

        canvas_mouse_x = self.canvas.canvasx(event.x)
        canvas_mouse_y = self.canvas.canvasy(event.y)

        bbox = self.canvas.bbox("all")
        if not bbox:
            return

        content_width = bbox[2] - bbox[0]
        content_height = bbox[3] - bbox[1]

        rel_x = (canvas_mouse_x - bbox[0]) / max(content_width, 1)
        rel_y = (canvas_mouse_y - bbox[1]) / max(content_height, 1)

        self.canvas_scale = new_scale
        self._update_zoom_label()
        self.draw_dependencies(self.current_selected_tests)

        bbox = self.canvas.bbox("all")
        if bbox:
            new_width = bbox[2] - bbox[0]
            new_height = bbox[3] - bbox[1]

            new_x = bbox[0] + rel_x * new_width
            new_y = bbox[1] + rel_y * new_height

            self.canvas.xview_moveto((new_x - self.canvas.winfo_width() / 2) / max(new_width, 1))
            self.canvas.yview_moveto((new_y - self.canvas.winfo_height() / 2) / max(new_height, 1))

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    
    def zoom_to_fit(self):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        content_width = bbox[2] - bbox[0]
        content_height = bbox[3] - bbox[1]

        if content_width == 0 or content_height == 0:
            return

        scale_x = canvas_width / content_width
        scale_y = canvas_height / content_height

        fit_scale = min(scale_x, scale_y)
        fit_scale = max(0.2, min(4.0, fit_scale))

        self.canvas_scale = fit_scale
        self._update_zoom_label()
        self.draw_dependencies(self.current_selected_tests)

        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)


    def _update_zoom_label(self):
        percent = int(self.canvas_scale * 100)
        self.zoom_label.config(text=f"Zoom: {percent}%")


    def update_ui(self):
        selected = [name for name, var in self.test_vars.items() if var.get()]
        self.draw_dependencies(selected)


    def export_and_close(self):
        selected = [name for name, var in self.test_vars.items() if var.get()]
        print("Chosen Test Cases:", selected)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TestUI(root)
    root.geometry("1920x1080")
    root.mainloop()


if __name__ == "__main__":
    main()
