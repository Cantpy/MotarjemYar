"""
Path and resource utilities for the application.
"""
import os
import sys
import json
import subprocess


def return_resource(folder1, resource, folder2=None):
    """
    Return the path to a resource file based on the application's execution context.

    Args:
        folder1 (str): First folder level
        resource (str): Resource filename
        folder2 (str, optional): Second folder level

    Returns:
        str: Full path to the resource
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
        path = os.path.join(project_root, folder1, folder2, resource)
    else:
        path = os.path.join(project_root, folder1, resource)

    return path


def get_remembered_user_info():
    """
    Get remembered user information from settings file.

    Returns:
        dict: UsersModel information or empty dict if not found
    """
    try:
        settings_path = return_resource("databases", "login_settings.json")
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
