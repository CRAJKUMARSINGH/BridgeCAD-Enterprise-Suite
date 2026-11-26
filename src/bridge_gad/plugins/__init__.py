import importlib
import pkgutil
import inspect


class PluginBase:
    """Base class every plugin must subclass."""
    name = "Unnamed Plugin"
    version = "1.0.0"
    author = "Unknown"
    description = "No description available."

    def run(self, parent=None):
        raise NotImplementedError("Each plugin must implement run()")


def load_plugins():
    """Auto-discover plugins under bridge_gad.plugins package."""
    plugins = []
    pkgpath = __path__
    for _, module_name, _ in pkgutil.iter_modules(pkgpath):
        mod = importlib.import_module(f"{__name__}.{module_name}")
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, PluginBase) and obj is not PluginBase:
                plugins.append(obj())
    return plugins
