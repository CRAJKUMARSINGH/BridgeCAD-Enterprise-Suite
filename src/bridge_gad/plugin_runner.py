import multiprocessing
import traceback
from tkinter import messagebox
from bridge_gad import logger


def _plugin_target(plugin_class):
    """Executed in a separate process."""
    try:
        plugin = plugin_class()
        plugin.run()
    except Exception as e:
        tb = traceback.format_exc()
        print("Plugin crashed:\n", tb)
        messagebox.showerror("Plugin Error", f"{plugin_class.name} failed:\n{e}")


def safe_run(plugin_class):
    """Run plugin safely in isolated process."""
    try:
        logger.log_plugin_sandbox(plugin_class.name, "Running in sandbox")
        p = multiprocessing.Process(target=_plugin_target, args=(plugin_class,))
        p.start()
        p.join(timeout=180)  # 180 second timeout
        if p.is_alive():
            p.terminate()
            logger.log_plugin_sandbox(plugin_class.name, "Terminated (timeout)")
        else:
            logger.log_plugin_sandbox(plugin_class.name, "Exited safely")
    except Exception as e:
        logger.log_plugin_sandbox(plugin_class.name, f"Failed to launch: {e}")
