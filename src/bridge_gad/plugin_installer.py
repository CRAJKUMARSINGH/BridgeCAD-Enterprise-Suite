import os
import json
import zipfile
import requests
from io import BytesIO
from bridge_gad.logger import log_plugin_sandbox

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")


def load_manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "plugin_manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("plugin_manifest.json not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)["plugins"]


def install_plugin(plugin):
    name = plugin["name"]
    url = plugin["source"]
    version = plugin["version"]

    log_plugin_sandbox(name, f"Downloading from {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Download failed for {name}")

    zip_path = os.path.join(PLUGIN_DIR, f"{name}.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(BytesIO(response.content)) as z:
        z.extractall(PLUGIN_DIR)

    log_plugin_sandbox(name, f"Installed v{version}")
    return f"{name} v{version} installed successfully."


def update_all_plugins():
    plugins = load_manifest()
    results = []
    for p in plugins:
        try:
            msg = install_plugin(p)
            results.append(msg)
        except Exception as e:
            results.append(f"{p['name']} failed: {e}")
    return results
