"""
Path and resource utilities for the application.
"""
import os
import sys
import json
import subprocess
from pathlib import Path


APP_NAME = "MotarjemYar"

# Determine the project root. This is the most robust way.
# It assumes this file is inside `shared/utils/`.
# Path(__file__) -> .../shared/utils/path_utils.py
# .parent -> .../shared/utils/
# .parent -> .../shared/
# .parent -> PROJECT_ROOT
# Adjust the number of `.parent` calls if you place this file elsewhere.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_resource_path(*path_segments):
    """
    Returns the absolute path to a READ-ONLY resource file.

    Use this for accessing assets bundled with the application, like
    images, fonts, or default configuration files.

    In a packaged app (PyInstaller), this points to the temporary _MEIPASS folder.
    When running from source, it points to the project's root directory.

    Args:
        *path_segments: A sequence of folder/file names (e.g., "assets", "icon.png").

    Returns:
        Path: A pathlib.Path object for the resource.
    """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (PyInstaller)
        base_path = Path(sys._MEIPASS)
    else:
        # We are running in a normal Python environment
        base_path = PROJECT_ROOT

    return base_path.joinpath(*path_segments)


# --- 3. The Function for WRITABLE User Data ---

def get_user_data_path(*path_segments, create_dirs=True):
    """
    Returns the absolute path to a WRITABLE user data file or directory.

    Use this for any file the application needs to create, write, or modify,
    such as settings.json, user_database.db, or log files.

    This path points to a permanent, user-specific directory
    (e.g., C:/Users/YourUser/.YourAppName/).

    Args:
        *path_segments: A sequence of folder/file names (e.g., "config", "settings.json").
        create_dirs (bool): If True, ensures the directory containing the final path exists.

    Returns:
        Path: A pathlib.Path object for the user data location.
    """
    # Use os.path.expanduser to find the user's home directory
    # The dot prefix makes the folder hidden on Linux/macOS
    base_path = Path(os.path.expanduser('~')) / f".{APP_NAME}"

    # Join the rest of the path segments
    user_path = base_path.joinpath(*path_segments)

    # Ensure the parent directory exists before returning the path
    if create_dirs:
        user_path.parent.mkdir(parents=True, exist_ok=True)

    return user_path


def return_folder(folder1, folder2=None, folder3=None):
    """
        Return the path to a folder based on the application's execution context.

        Args:
            folder1 (str): First folder level
            folder2 (str): Second folder level
            folder3 (str, optional): Third folder level

        Returns:
            str: Full path to the folder
        """
    if getattr(sys, 'frozen', False):
        # App is frozen (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Running from source
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Go two levels up to get to a deeper root
    project_root = os.path.abspath(os.path.join(base_path, "..", ".."))

    # Build the path components conditionally
    if folder2:
        path = os.path.join(project_root, folder1, folder2)
    elif folder3:
        path = os.path.join(project_root, folder1, folder2, folder3)
    else:
        path = os.path.join(project_root, folder1)

    return path


def get_absolute_path(project_root: Path, relative_path: str) -> str:
    """
    Constructs a foolproof, absolute path from the project root
    and a relative path string.

    Args:
        project_root: The absolute Path object for the project's root directory.
        relative_path: The relative path to the resource (e.g., 'data/logo.png').

    Returns:
        A string representation of the absolute path.
    """
    # The '/' operator in pathlib intelligently and safely joins path components,
    # handling all OS-specific separators for you.
    absolute_path = project_root / relative_path

    # For PyInstaller's sake, we might need a check here in the future,
    # but for now, this is much cleaner for development.

    return str(absolute_path)


def get_remembered_user_info():
    """
    Get remembered user information from settings file.

    Returns:
        dict: UsersModel information or empty dict if not found
    """
    try:
        settings_path = get_resource_path("databases", "login_settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading remembered user info: {e}")
    return {}


def open_file(path):
    if sys.platform.startswith('darwin'):  # macOS
        subprocess.call(('open', path))
    elif os.name == 'nt':  # Windows
        os.startfile(path)
    elif os.name == 'posix':  # Linux
        subprocess.call(('xdg-open', path))
