import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import webbrowser
import os
import threading
from bridge_gad.geometry import summarize
from bridge_gad.io_utils import save_results_to_excel
from bridge_gad.config import DEFAULT_E, DEFAULT_I

# Import version from the package
from bridge_gad import __version__

# Import the updater, logger, and telemetry modules
from bridge_gad import updater, logger, telemetry, core_updater

# Import plugin loader, generator, registry, and runner
from bridge_gad.plugins import load_plugins
from bridge_gad import plugin_generator
from bridge_gad.plugin_registry import build_registry, get_registry, check_for_plugin_updates
from bridge_gad.plugin_runner import safe_run

# Import plugin installer
from bridge_gad.plugin_installer import update_all_plugins

# Try to import PIL for image support (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageTk = None
    print("PIL not available - using text-based splash screen")

# Try to import tkPDFViewer for embedded PDF viewing (optional)
try:
    from tkPDFViewer import tkPDFViewer as pdf
    PDF_VIEWER_AVAILABLE = True
except ImportError:
    PDF_VIEWER_AVAILABLE = False
    pdf = None
    print("tkPDFViewer not available - using external PDF viewer")


def show_splash(root, duration=2.5):
    """Show a professional splash screen before the main window."""
    try:
        # Create splash screen window
        splash = tk.Toplevel(root)
        splash.overrideredirect(True)
        splash.geometry("400x300+600+300")

        # Configure splash screen style
        splash.configure(bg="#f8f9fa")

        # Create main frame
        splash_frame = tk.Frame(splash, bg="#f8f9fa", relief="raised", bd=2)
        splash_frame.pack(fill="both", expand=True)

        # Try to show logo if PIL is available
        if PIL_AVAILABLE and Image and ImageTk:
            try:
                # Try to load logo image
                img = Image.open("bridge_logo.png")
                img = img.resize((100, 100))
                tk_img = ImageTk.PhotoImage(img)
                logo_label = tk.Label(splash_frame, image=tk_img, bg="#f8f9fa")
                # Keep a reference to prevent garbage collection
                setattr(logo_label, 'image_ref', tk_img)
                logo_label.pack(pady=10)
            except Exception as e:
                # Fallback to text if image not found
                print(f"Logo not found, using text fallback: {e}")
                tk.Label(
                    splash_frame,
                    text="BRIDGE\n  ___   \n |   |  \n |___|  \nGAD",
                    font=("Courier", 12, "bold"),
                    bg="#f8f9fa",
                    fg="#2c3e50"
                ).pack(pady=10)
        else:
            # Show text-based logo
            tk.Label(
                splash_frame,
                text="BRIDGE\n  ___   \n |   |  \n |___|  \nGAD",
                font=("Courier", 12, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            ).pack(pady=10)

        # Add title
        tk.Label(
            splash_frame,
            text="Bridge_GAD",
            font=("Segoe UI", 20, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        ).pack(pady=10)

        # Add subtitle
        tk.Label(
            splash_frame,
            text="Structural Engineering Analysis Tool",
            font=("Segoe UI", 11),
            bg="#f8f9fa",
            fg="#34495e"
        ).pack()

        # Add version info
        tk.Label(
            splash_frame,
            text=f"Version {__version__}",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#7f8c8d"
        ).pack(pady=5)

        # Add developer info
        tk.Label(
            splash_frame,
            text="Developed by Er. Rajkumar Singh Chauhan",
            font=("Segoe UI", 10, "bold"),
            bg="#f8f9fa",
            fg="#2980b9"
        ).pack(pady=5)

        tk.Label(
            splash_frame,
            text="Institution of Engineers (India)",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#34495e"
        ).pack()

        tk.Label(
            splash_frame,
            text="Udaipur Local Centre Initiative (2025)",
            font=("Segoe UI", 8),
            bg="#f8f9fa",
            fg="#7f8c8d"
        ).pack(pady=5)

        # Add loading indicator
        loading_label = tk.Label(
            splash_frame,
            text="Loading...",
            font=("Segoe UI", 8),
            bg="#f8f9fa",
            fg="#95a5a6"
        )
        loading_label.pack(side="bottom", pady=10)

        # Update splash screen
        splash.update()

        # Schedule splash screen to close and show main window
        root.after(int(duration * 1000), lambda: [splash.destroy(), root.deiconify()])
        root.withdraw()

    except Exception as e:
        print(f"Splash screen error: {e}")
        root.deiconify()


def show_plugin_registry():
    build_registry()
    data = get_registry()

    win = tk.Toplevel()
    win.title("Bridge_GAD Plugin Registry")
    tree = ttk.Treeview(win, columns=("Version", "Author", "Description"), show="headings")
    tree.pack(fill="both", expand=True)

    tree.heading("Version", text="Version")
    tree.heading("Author", text="Author")
    tree.heading("Description", text="Description")

    tree.column("Version", width=100)
    tree.column("Author", width=150)
    tree.column("Description", width=300)

    for name, info in data.items():
        tree.insert("", "end", values=(name, info["version"], info["author"], info["description"]))


def _update_plugins():
    try:
        results = update_all_plugins()
        messagebox.showinfo("Plugin Manager", "\n".join(results))
    except Exception as e:
        messagebox.showerror("Update Error", str(e))


def setup_plugins(menu_bar):
    """Set up the plugins menu and load all available plugins."""
    plugin_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Plugins", menu=plugin_menu)

    # Add the plugin generator option
    plugin_menu.add_command(label="➕ New Bridge Module...", command=plugin_generator.create_plugin)
    plugin_menu.add_separator()

    plugins = load_plugins()
    if plugins:
        for p in plugins:
            # Capture the plugin in a closure to avoid late binding issues
            plugin_menu.add_command(
                label=p.name,
                command=lambda plug=p: safe_run(plug.__class__)
            )
    else:
        plugin_menu.add_command(label="No Plugins Found", state="disabled")

    plugin_menu.add_separator()
    plugin_menu.add_command(label="📜 Plugin Registry", command=show_plugin_registry)
    plugin_menu.add_command(label="🔄 Check Plugin Updates", command=lambda: messagebox.showinfo("Plugin Updates", check_for_plugin_updates()))
    plugin_menu.add_command(label="📥 Update / Install Plugins", command=_update_plugins)

    return plugins


class BridgeGADApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bridge_GAD Calculator")
        self.geometry("450x350")
        self.resizable(False, False)

        # Track session start
        telemetry.telemetry.event("sessions")

        # Create menubar
        self.create_menubar()

        # Check for updates when the app starts (using the new updater)
        self.after(1000, lambda: updater.auto_check_in_background_simple(__version__))

        # Check for core updates in background
        threading.Thread(target=lambda: core_updater.check_core_update(__version__), daemon=True).start()

        self.create_widgets()

    def create_menubar(self):
        """Create the application menubar."""
        menubar = Menu(self)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Manual", command=lambda: (telemetry.telemetry.event("feature_user_manual"), self.open_user_manual()))
        help_menu.add_separator()
        help_menu.add_command(label="Check for Updates", command=lambda: (telemetry.telemetry.event("feature_check_updates"), updater.manual_check_for_updates(__version__)))
        help_menu.add_command(label="Check for Core Update", command=lambda: core_updater.check_core_update(__version__))
        help_menu.add_command(label="Export Diagnostics", command=lambda: (telemetry.telemetry.event("feature_export_diag"), self.export_diagnostics()))
        help_menu.add_command(label="View Usage Summary", command=lambda: (telemetry.telemetry.event("feature_view_summary"), self.view_usage_summary()))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Set up plugins menu
        self.plugins = setup_plugins(menubar)

        self.config(menu=menubar)

    def export_diagnostics(self):
        """Export diagnostic logs for support."""
        try:
            zip_path = logger.export_diagnostics()
            messagebox.showinfo("Diagnostics Exported",
                                f"Logs zipped to:\n{zip_path}\nPlease attach it in your support email.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export diagnostics:\n{e}")

    def view_usage_summary(self):
        """Show usage summary dialog."""
        summary = telemetry.telemetry.summarize()
        messagebox.showinfo("Bridge GAD Usage", summary)

    def open_user_manual(self):
        """Open the user manual PDF in the default viewer or show embedded viewer."""
        # First try to find the PDF manual
        manual_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "docs", "Bridge_GAD_User_Manual.pdf"),
            os.path.join(os.path.dirname(__file__), "..", "..", "docs", "Bridge_GAD_User_Manual.md"),
            os.path.join("docs", "Bridge_GAD_User_Manual.pdf"),
            os.path.join("docs", "Bridge_GAD_User_Manual.md")
        ]

        manual_path = None
        for path in manual_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                manual_path = abs_path
                break

        if manual_path:
            # If it's a PDF and we have the embedded viewer, use it
            if manual_path.endswith('.pdf') and PDF_VIEWER_AVAILABLE and pdf:
                self.show_embedded_manual(manual_path)
            else:
                # Otherwise open with default application
                try:
                    webbrowser.open_new(manual_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open manual: {e}")
        else:
            messagebox.showerror("Manual Not Found",
                                 "Bridge_GAD_User_Manual.pdf or .md not found.\n"
                                 "Please regenerate it using build_manual.bat.")

    def show_embedded_manual(self, pdf_path):
        """Show the manual in an embedded PDF viewer."""
        try:
            win = tk.Toplevel(self)
            win.title("Bridge_GAD User Manual")
            win.geometry("900x600")

            # Create a frame for the PDF viewer
            pdf_frame = tk.Frame(win)
            pdf_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Show the PDF
            if pdf and PDF_VIEWER_AVAILABLE:
                v1 = pdf.ShowPdf()
                v2 = v1.pdf_view(pdf_frame, pdf_location=pdf_path, width=100, height=80)
                v2.pack(fill="both", expand=True)
            else:
                # Fallback to external viewer
                webbrowser.open_new(pdf_path)

        except Exception as e:
            messagebox.showerror("Error", f"Could not display PDF: {e}\nOpening in external viewer instead.")
            webbrowser.open_new(pdf_path)

    def show_about(self):
        """Show the About dialog."""
        messagebox.showinfo(
            "About Bridge_GAD",
            f"Bridge_GAD v{__version__}\n\n"
            "Developed by: Er. Rajkumar Singh Chauhan\n"
            "Institution of Engineers (India)\n"
            "Udaipur Local Centre Initiative (2025)\n\n"
            "GitHub: CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse"
        )

    def create_widgets(self):
        ttk.Label(self, text="Bridge_GAD Calculator", font=("Segoe UI", 14, "bold")).pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack(pady=10)

        self.span_var = tk.DoubleVar()
        self.load_var = tk.DoubleVar()
        self.E_var = tk.DoubleVar(value=DEFAULT_E)
        self.I_var = tk.DoubleVar(value=DEFAULT_I)

        labels = ["Span (m):", "Load (kN/m):", "E (kN/m²):", "I (m⁴):"]
        vars_ = [self.span_var, self.load_var, self.E_var, self.I_var]

        for i, (label, var) in enumerate(zip(labels, vars_)):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", pady=5, padx=5)
            ttk.Entry(frame, textvariable=var, width=25).grid(row=i, column=1, padx=5)

        ttk.Button(self, text="Compute", command=lambda: (telemetry.telemetry.event("feature_compute"), self.compute())).pack(pady=10)
        ttk.Button(self, text="Export to Excel", command=lambda: (telemetry.telemetry.event("feature_export_excel"), self.export_to_excel())).pack()

        self.output_box = tk.Text(self, width=50, height=8, state="disabled", bg="#f4f4f4")
        self.output_box.pack(pady=10)

    def compute(self):
        try:
            results = summarize(self.span_var.get(), self.load_var.get(), self.E_var.get(), self.I_var.get())
            self.display_results(results)
        except Exception as e:
            messagebox.showerror("Error", f"Computation failed:\n{e}")

    def display_results(self, results):
        self.output_box.config(state="normal")
        self.output_box.delete(1.0, tk.END)
        for k, v in results.items():
            self.output_box.insert(tk.END, f"{k:15s}: {v:10.4f}\n")
        self.output_box.config(state="disabled")

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            results = summarize(self.span_var.get(), self.load_var.get(), self.E_var.get(), self.I_var.get())
            save_results_to_excel(results, file_path)
            messagebox.showinfo("Saved", f"Results saved to:\n{file_path}")


def main():
    app = BridgeGADApp()
    # Show splash screen
    show_splash(app)
    app.mainloop()


if __name__ == "__main__":
    main()
