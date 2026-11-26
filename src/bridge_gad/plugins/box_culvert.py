from bridge_gad.plugins import PluginBase
from tkinter import messagebox


class BoxCulvertPlugin(PluginBase):
    name = "Box Culvert Design"
    version = "1.0.0"
    author = "Er. Rajkumar Singh Chauhan"
    description = "Performs design calculations for box culverts."

    def run(self, parent=None):
        messagebox.showinfo("Box Culvert", "Launching Box Culvert Design Module...")
