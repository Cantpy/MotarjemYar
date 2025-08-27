# shared/widgets/custom_widgets.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from ..fonts.font_manager import FontManager # Assuming your font manager is here


def create_stat_card(title: str, color: str, object_name: str = "statCard") -> QFrame:
    """
    Creates a styled KPI card widget with separate alignment for title and value.
    This is a reusable factory function.

    Args:
        title (str): The descriptive text for the card (e.g., "درآمد امروز").
        color (str): The hex color code for the value text and side border.
        object_name (str): The Qt object name for applying QSS styles.

    Returns:
        QFrame: The fully constructed and styled stat card widget.
    """
    card = QFrame()
    card.setObjectName(object_name)
    card.setStyleSheet(f"""
        QFrame#{object_name} {{
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            border-right: 5px solid {color};
        }}
    """)

    # Main vertical layout for the card
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

    # --- Title Label (Right-to-Left) ---
    title_label = QLabel(title)
    title_label.setObjectName("statTitle")
    title_label.setFont(FontManager.get_font(size=11))
    title_label.setStyleSheet("color: #555;")
    # title_label.setAlignment(Qt.AlignRight)
    title_label.setLayoutDirection(Qt.RightToLeft)
    layout.addWidget(title_label)

    # --- Value Label (Left-to-Right) ---
    value_label = QLabel("...") # Placeholder
    value_label.setObjectName("statValue")
    value_label.setFont(FontManager.get_font(size=16, bold=True))
    value_label.setStyleSheet(f"color: {color}; margin-top: 5px;")
    value_label.setAlignment(Qt.AlignRight)
    value_label.setLayoutDirection(Qt.LeftToRight)
    layout.addWidget(value_label)

    return card
