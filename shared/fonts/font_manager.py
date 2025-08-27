# shared/fonts/font_manager.py
from PySide6.QtGui import QFontDatabase, QFont
import os
from shared.utils.path_utils import return_folder

fonts_path = return_folder('resources', 'fonts')


class FontManager:
    _loaded_family = None

    @staticmethod
    def load_fonts():
        """Load all .ttf fonts from the resources/fonts/ folder"""
        if not os.path.exists(fonts_path):
            raise FileNotFoundError(f"Fonts directory not found: {fonts_path}")

        for file in os.listdir(fonts_path):
            if file.lower().endswith(".ttf"):
                font_id = QFontDatabase.addApplicationFont(os.path.join(fonts_path, file))
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        FontManager._loaded_family = families[0]  # Save the first loaded family

    @staticmethod
    def get_font(size=10, bold=False):
        """Return a QFont using the loaded font family, with fallback"""
        if FontManager._loaded_family:
            font = QFont(FontManager._loaded_family, size)
        else:
            font = QFont("Sans Serif", size)  # fallback if load failed

        font.setBold(bold)
        return font
