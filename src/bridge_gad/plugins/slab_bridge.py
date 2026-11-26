from bridge_gad.plugins import PluginBase
from tkinter import messagebox


class SlabBridgePlugin(PluginBase):
    name = "Slab Bridge Design"
    version = "1.0.0"
    author = "Er. Rajkumar Singh Chauhan"
    description = "Performs design calculations for slab bridges."

    def run(self, parent=None):
        messagebox.showinfo("Slab Bridge", "Launching Slab Bridge Design Module...")
