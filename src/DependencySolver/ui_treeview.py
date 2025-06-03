import tkinter as tk
from tkinter import ttk


class TestTreeView:
    def __init__(self, parent, test_order, test_vars, default_test_cases, on_selection_change):
        self.frame = ttk.Frame(parent)
        self.frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10, expand=True)

        self.scroll_y = ttk.Scrollbar(self.frame, orient="vertical")
        self.tree = ttk.Treeview(self.frame, yscrollcommand=self.scroll_y.set)
        self.tree.heading("#0", text="Test Cases")

        self.scroll_y.config(command=self.tree.yview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.test_order = test_order
        self.test_vars = test_vars
        self.tree_nodes = {}
        self.on_selection_change = on_selection_change

        self.build_tree(default_test_cases)

        self.tree.bind("<Button-1>", self.on_tree_click)

    def build_tree(self, default_test_cases):
        for test_name in self.test_order:
            parts = test_name.split('.')
            path = ""
            parent = ""
            for i, part in enumerate(parts):
                path = '.'.join(parts[:i + 1])
                if path not in self.tree_nodes:
                    node_id = self.tree.insert(parent, "end", text=f"[ ] {part}", open=True)
                    self.tree_nodes[path] = node_id
                parent = self.tree_nodes[path]

            var = tk.BooleanVar(value=(test_name in default_test_cases))
            self.test_vars[test_name] = var
            label = parts[-1]
            self.tree.item(self.tree_nodes[path], text=f"[x] {label}" if var.get() else f"[ ] {label}")

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        full_path = self.get_full_path(item_id)
        if event.x < 20 * len(full_path.split(".")):
            return

        if full_path in self.test_vars:
            self.toggle_checkbox(full_path)
        else:
            self.toggle_group_checkbox(item_id)
        self.on_selection_change()

    def toggle_checkbox(self, test_name):
        var = self.test_vars[test_name]
        var.set(not var.get())
        item_id = self.tree_nodes[test_name]
        new_state = "[x]" if var.get() else "[ ]"
        label = test_name.split('.')[-1]
        self.tree.item(item_id, text=f"{new_state} {label}")

    def toggle_group_checkbox(self, item_id):
        current_text = self.tree.item(item_id, "text")
        new_state = not current_text.strip().startswith("[x]")
        self.update_tree_item_checkbox(item_id, new_state)

        for child_id in self.tree.get_children(item_id):
            self.toggle_group_checkbox(child_id)

    def update_tree_item_checkbox(self, item_id, state):
        full_path = self.get_full_path(item_id)
        label = self.tree.item(item_id, "text").replace("[x] ", "").replace("[ ] ", "").strip()
        self.tree.item(item_id, text=f"[x] {label}" if state else f"[ ] {label}")
        if full_path in self.test_vars:
            self.test_vars[full_path].set(state)

    def get_full_path(self, item_id):
        parts = []
        while item_id:
            raw_text = self.tree.item(item_id, "text")
            clean_text = raw_text.replace("[x] ", "").replace("[ ] ", "")
            parts.insert(0, clean_text)
            item_id = self.tree.parent(item_id)
        return '.'.join(parts)
