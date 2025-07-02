from PySide6.QtCore import QSettings


def is_dark_theme():
    settings = QSettings("AppTheme", "CurrentTheme")
    theme_name = settings.value("theme", "بهاری")
    return theme_name == "دراکولا"
