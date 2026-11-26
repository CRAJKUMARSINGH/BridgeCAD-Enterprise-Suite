from pathlib import Path
from tkinter import simpledialog, messagebox

PLUGIN_DIR = Path(__file__).parent / "plugins"

TEMPLATE = '''from bridge_gad.plugins import PluginBase
from tkinter import messagebox

class {class_name}(PluginBase):
    name = "{display_name}"
    description = "{description}"

    def run(self, parent=None):
        messagebox.showinfo("{display_name}", "This is a placeholder for {display_name} module.")
'''


def create_plugin():
    """Prompt user for plugin details and auto-create module."""
    name = simpledialog.askstring("New Bridge Module", "Enter bridge module name (e.g., T-Beam Bridge):")
    if not name:
        return

    class_name = name.title().replace(" ", "") + "Plugin"
    filename = name.lower().replace(" ", "_") + ".py"
    filepath = PLUGIN_DIR / filename

    if filepath.exists():
        messagebox.showwarning("Exists", f"A plugin named '{name}' already exists.")
        return

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            class_name=class_name,
            display_name=name,
            description=f"Auto-generated module for {name} design."
        ))

    messagebox.showinfo("Plugin Created", f"New bridge module created:\n{filepath}")
