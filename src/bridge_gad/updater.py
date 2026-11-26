"""
Bridge_GAD Auto-Updater Module

This module provides automatic background updating functionality for Bridge_GAD.
It checks for new versions on GitHub and can download and install updates silently.
"""

import os
import sys
import requests
import shutil
import tempfile
import threading
import subprocess
from tkinter import messagebox
from typing import Optional, Callable, Dict, Any

# GitHub API endpoint for latest release
GITHUB_RELEASES = "https://api.github.com/repos/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/releases/latest"


def check_for_update(current_version: str) -> Dict[str, Any]:
    """
    Check GitHub for a newer tagged version.

    Args:
        current_version (str): Current version of the application

    Returns:
        dict: Update information with keys:
            - 'available': bool indicating if update is available
            - 'latest_version': str of latest version
            - 'current_version': str of current version
            - 'release_info': dict with release information
            - 'download_url': str URL for download (if available)
    """
    result = {
        'available': False,
        'latest_version': current_version,
        'current_version': current_version,
        'release_info': None,
        'download_url': None
    }

    try:
        # Make request to GitHub API
        response = requests.get(GITHUB_RELEASES, timeout=10)
        response.raise_for_status()
        latest_release = response.json()

        # Extract version information
        latest_tag = latest_release["tag_name"]
        # Remove 'v' prefix if present
        if latest_tag.startswith("v"):
            latest_version = latest_tag[1:]
        else:
            latest_version = latest_tag

        result['latest_version'] = latest_version
        result['release_info'] = latest_release

        # Check if update is available
        if latest_version != current_version:
            result['available'] = True

            # Find the appropriate asset to download
            # Prefer installer, fallback to GUI executable
            download_url = None
            for asset in latest_release.get("assets", []):
                asset_name = asset["name"].lower()
                if "setup" in asset_name and asset_name.endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break
                elif "gui" in asset_name and asset_name.endswith(".exe") and not download_url:
                    download_url = asset["browser_download_url"]
                elif asset_name.endswith(".exe") and not download_url:
                    download_url = asset["browser_download_url"]

            result['download_url'] = download_url

    except Exception as e:
        print(f"Update check failed: {e}")

    return result


def _download_and_replace(url: str, progress_callback: Optional[Callable] = None) -> str:
    """
    Download the new installer or exe, save, and launch it.

    Args:
        url (str): URL to download the update from
        progress_callback (callable): Optional callback for progress updates

    Returns:
        str: Path to downloaded file
    """
    try:
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        local_file = os.path.join(temp_dir, "Bridge_GAD_Update.exe")

        # Download with progress tracking
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(local_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress)

        # Verify file was downloaded
        if not os.path.exists(local_file) or os.path.getsize(local_file) == 0:
            raise Exception("Downloaded file is empty or missing")

        return local_file

    except Exception as e:
        print(f"Download failed: {e}")
        raise


def install_update(downloaded_file: str) -> bool:
    """
    Install the downloaded update.

    Args:
        downloaded_file (str): Path to the downloaded update file

    Returns:
        bool: True if installation initiated successfully
    """
    try:
        # Launch the installer/update executable
        # For installer, run silently if possible
        # For executable, replace current one on next launch
        subprocess.Popen([downloaded_file], shell=True)
        return True
    except Exception as e:
        print(f"Failed to launch installer: {e}")
        return False


def auto_check_in_background(current_version: str, callback: Optional[Callable] = None) -> threading.Thread:
    """
    Run update check in a separate thread to avoid blocking GUI.

    Args:
        current_version (str): Current version of the application
        callback (callable): Optional callback function to handle results

    Returns:
        threading.Thread: Thread object running the update check
    """
    def _check_wrapper():
        try:
            result = check_for_update(current_version)
            if callback:
                callback(result)
        except Exception as e:
            print(f"Background update check failed: {e}")

    thread = threading.Thread(target=_check_wrapper, daemon=True)
    thread.start()
    return thread


def manual_check_for_updates(current_version: str, parent_window=None) -> None:
    """
    Manually check for updates and show appropriate dialogs.

    Args:
        current_version (str): Current version of the application
        parent_window: Parent window for dialogs (optional)
    """
    try:
        # Show checking message
        if parent_window:
            # In a real implementation, you might show a progress dialog here
            pass

        # Check for updates
        result = check_for_update(current_version)

        if result['available']:
            # Update is available
            message = (f"A new version (v{result['latest_version']}) is available.\n"
                       f"Current version: v{result['current_version']}\n\n"
                       f"Do you want to download and install it now?")

            ask_result = messagebox.askyesno("Bridge_GAD Update", message)
            if ask_result:
                if result['download_url']:
                    try:
                        # Download the update
                        downloaded_file = _download_and_replace(result['download_url'])

                        # Confirm installation
                        confirm_result = messagebox.askyesno(
                            "Update Ready",
                            "Update downloaded successfully.\n\n"
                            "Bridge_GAD will now restart to complete the installation.\n"
                            "Click OK to continue."
                        )
                        if confirm_result:
                            # Install and restart
                            if install_update(downloaded_file):
                                # Exit current application
                                sys.exit(0)
                            else:
                                messagebox.showerror(
                                    "Update Failed",
                                    "Could not start the update process."
                                )
                    except Exception as e:
                        messagebox.showerror(
                            "Update Failed",
                            f"Could not download or install update:\n{e}"
                        )
                else:
                    messagebox.showinfo(
                        "Update",
                        "No suitable download found in release assets."
                    )
        else:
            # No update available
            messagebox.showinfo(
                "Bridge_GAD Update",
                f"You are running the latest version (v{current_version})."
            )

    except Exception as e:
        messagebox.showerror(
            "Update Check Failed",
            f"Could not check for updates:\n{e}"
        )

# Simplified functions to match the user's specification


def check_for_update_simple(current_version: str):
    """Check GitHub for a newer tagged version - simplified version."""
    try:
        r = requests.get(GITHUB_RELEASES, timeout=5)
        r.raise_for_status()
        latest = r.json()
        latest_tag = latest["tag_name"].lstrip("v")

        if latest_tag != current_version:
            if messagebox.askyesno("Bridge_GAD Update",
                                   f"A new version ({latest_tag}) is available.\n"
                                   f"Do you want to download and install it now?"):
                asset = next((a for a in latest["assets"]
                              if a["name"].endswith(".exe")), None)
                if asset:
                    _download_and_replace_simple(asset["browser_download_url"])
                else:
                    messagebox.showinfo("Update", "Installer not found in release assets.")
    except Exception as e:
        print("Update check failed:", e)


def _download_and_replace_simple(url):
    """Download the new installer or exe, save, and launch it - simplified version."""
    try:
        temp_dir = tempfile.mkdtemp()
        local_file = os.path.join(temp_dir, "Bridge_GAD_Update.exe")
        with requests.get(url, stream=True, timeout=20) as r:
            with open(local_file, "wb") as f:
                shutil.copyfileobj(r.raw, f)
        messagebox.showinfo("Update", "Update downloaded. Bridge_GAD will now restart.")
        os.startfile(local_file)
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Update Failed", f"Could not complete update:\n{e}")


def auto_check_in_background_simple(current_version):
    """Run update check in a separate thread to avoid blocking GUI - simplified version."""
    t = threading.Thread(target=check_for_update_simple, args=(current_version,), daemon=True)
    t.start()
