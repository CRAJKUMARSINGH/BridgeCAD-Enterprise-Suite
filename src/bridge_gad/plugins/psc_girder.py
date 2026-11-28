from bridge_gad.plugins import PluginBase
from tkinter import messagebox


class PSCGirderPlugin(PluginBase):
    name = "PSC Girder Design"
    version = "1.0.0"
    author = "Er. Rajkumar Singh Chauhan"
    description = "Performs design calculations for prestressed concrete girders."

    def run(self, parent=None):
        messagebox.showinfo("PSC Girder", "Launching PSC Girder Design Module...")
