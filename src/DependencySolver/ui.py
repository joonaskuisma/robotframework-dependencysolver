import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

from DependencySolver._version import __version__
from DependencySolver.ui_canvas import DependencyCanvasManager, CanvasView
from DependencySolver.ui_treeview import TestTreeView


class TestUI:
    def __init__(self, root, data, default_test_cases):
        self.root = root
        self.root.title(f"DependencySolver-GUI {__version__}")
        self.root.protocol("WM_DELETE_WINDOW", self.export_and_close)

        self.tests = {}
        self.test_order = []
        self.current_selected_tests = []
        self.default_test_cases = default_test_cases
        self.test_vars = {}

        self.parse_tests_file(data)

        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Treeview (left side)
        self.tree_view = TestTreeView(
            parent=self.paned,
            test_order=self.test_order,
            test_vars=self.test_vars,
            default_test_cases=self.default_test_cases,
            on_selection_change=self.update_ui
        )
        self.paned.add(self.tree_view.frame, weight=1)

        # Canvas (right side)
        self.canvas_frame = ttk.Frame(self.paned)
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        self.canvas_toolbar = ttk.Frame(self.canvas_frame)
        self.canvas_toolbar.place(relx=1.0, x=-30, y=10, anchor="ne")

        self.zoom_label = ttk.Label(self.canvas_toolbar, text="Zoom: 100%")
        self.total_selected_label = tk.Label(self.canvas_toolbar, text="Total Selected Tests: 0", font=("Arial", 10, "italic"))
        self.total_selected_label.pack(side=tk.TOP, padx=10)

        self.canvas_view = CanvasView(self.canvas, self.zoom_label)
        self.canvas.canvas_view = self.canvas_view
        self.canvas_view.set_counter_label(self.total_selected_label)

        ttk.Button(self.canvas_toolbar, text="+", width=2, command=self.canvas_view.zoom_in).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="-", width=2, command=self.canvas_view.zoom_out).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="⭯", width=2, command=self.canvas_view.reset_zoom_and_positions).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="Zoom to Fit", command=self.canvas_view.zoom_to_fit).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="Undo", command=self.canvas_view.undo).pack(side=tk.LEFT)
        ttk.Button(self.canvas_toolbar, text="Redo", command=self.canvas_view.redo).pack(side=tk.LEFT)
        self.zoom_label.pack(side=tk.LEFT, padx=10)

        self.paned.add(self.canvas_frame, weight=4)

        # Menubar
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        #filemenu.add_command(label="Show Chosen Tests", command=self.update_ui)
        filemenu.add_command(label="Save and Close", command=self.export_and_close)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Info", command=self.show_info)
        menubar.add_cascade(label="Help", menu=helpmenu)

        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Reset zoom", command=self.canvas_view.reset_zoom_and_positions)
        menubar.add_cascade(label="View", menu=viewmenu)

        self.root.config(menu=menubar)

        # Scroll & zoom bindings
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Shift-MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)
        self.canvas.bind_all("<Control-MouseWheel>", self._on_canvas_zoom)

        self.active_scroll_target = None
        self.canvas.bind("<Enter>", lambda e: self._set_scroll_target("canvas"))
        self.canvas.bind("<Leave>", lambda e: self._set_scroll_target(None))
        self.tree_view.tree.bind("<Enter>", lambda e: self._set_scroll_target("tree"))
        self.tree_view.tree.bind("<Leave>", lambda e: self._set_scroll_target(None))

        self.draw_dependencies(self.default_test_cases)

    def _set_scroll_target(self, target):
        self.active_scroll_target = target

    def _on_mousewheel(self, event):
        is_shift = (event.state & 0x0001) != 0
        delta = -1 if event.num == 5 or event.delta < 0 else 1

        if self.active_scroll_target == "canvas":
            if is_shift:
                self.canvas.xview_scroll(delta, "units")
            else:
                self.canvas.yview_scroll(delta, "units")
        elif self.active_scroll_target == "tree":
            self.tree_view.tree.yview_scroll(delta, "units")
            self.tree_view.tree.yview_scroll(delta, "units")

    def _on_canvas_zoom(self, event):
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        old_scale = self.canvas_view.scale
        new_scale = max(0.2, min(4.0, old_scale * zoom_factor))
        self.canvas_view.set_zoom(new_scale)

    def parse_tests_file(self, data):
        lines = data.strip().split('\n')
        for line in lines:
            if line.strip().startswith('--test'):
                parts = line.split("--test ")[1].split("#DEPENDS")
                test_name = parts[0].strip()
                deps = [d.strip() for d in parts[1:]]
                self.tests[test_name] = {"name": test_name, "dependencies": deps}
                self.test_order.append(test_name)

    def draw_dependencies(self, selected_tests):
        self.current_selected_tests = selected_tests.copy()
        self.dependency_manager = DependencyCanvasManager(self.canvas, self.tests, self.current_selected_tests)
        self.canvas_view.register_boxes(list(self.dependency_manager.boxes.values()))

    def update_ui(self):
        selected = [name for name, var in self.test_vars.items() if var.get()]
        self.draw_dependencies(selected)

    def show_info(self):
        messagebox.showinfo("Instructions",
            "- Select tests from the tree on the left.\n"
            "- Selected tests and their dependencies will be drawn on the right.\n"
            "- Close and save selections by clicking \"Save and Close\".")

    def export_and_close(self):
        self.selected_tests_result = list(self.dependency_manager.boxes.keys())
        self.root.destroy()


def main_application(data, default_test_cases):
    root = tk.Tk()
    app = TestUI(root, data, default_test_cases)
    root.geometry("1920x1080")
    root.mainloop()
    selected_tests = getattr(app, "selected_tests_result", None)
    return selected_tests


if __name__ == "__main__":
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
    selected_tests = main_application(test_data, ['Tests.suite A.Test A5'])

    if selected_tests is not None:
        print("Chosen tests:", selected_tests)
    else:
        print("No tests selected.")
