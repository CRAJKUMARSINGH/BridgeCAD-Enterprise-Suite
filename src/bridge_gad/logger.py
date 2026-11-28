import sys
import traceback
import datetime
import platform
import zipfile
import tempfile
from pathlib import Path

LOG_DIR = Path.home() / "Bridge_GAD_Logs"
LOG_DIR.mkdir(exist_ok=True)


def get_log_file():
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"bridge_gad_{date}.log"


def log_error(exc_type, exc_value, exc_tb):
    """Write a formatted crash log."""
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_path = get_log_file()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write(f"System: {platform.system()} {platform.release()} ({platform.version()})\n")
        f.write(f"Python: {platform.python_version()}\n")
        f.write(f"Executable: {sys.executable}\n\n")
        f.write(tb_str + "\n")
    print(f"Error logged to: {log_path}")
    return log_path


def log_plugin_sandbox(plugin_name, status):
    """Log plugin sandbox events."""
    path = get_log_file()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[PLUGIN-SANDBOX] {plugin_name}: {status}\n")


def export_diagnostics():
    """Zip the recent logs for support."""
    temp_zip = Path(tempfile.gettempdir()) / "Bridge_GAD_Diagnostics.zip"
    with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for log in LOG_DIR.glob("bridge_gad_*.log"):
            z.write(log, log.name)
    return temp_zip
