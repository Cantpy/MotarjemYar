
DOCUMENT_SELECTION_STYLES = """QWidget { font-family: "IranSANS", "Tahoma"; font-size: 11pt; } 
QPushButton#PrimaryButton { background-color: #007bff; color: white; font-weight: bold; border-radius: 5px; padding: 
8px; } #RemoveButton { background-color: #dc3545; color: white; font-weight: bold; border-radius: 5px; padding: 5px; 
} QTableWidget { background-color: white; border: 1px solid #ddd; } QHeaderView::section { background-color: #f0f0f0; 
padding: 5px; border: 1px solid #ddd; font-weight: bold; } QGroupBox { background-color: #f7f7f7; border: 1px solid 
#e0e0e0; border-radius: 8px; margin-top: 1em; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: 
top center; padding: 5px 15px; }"""

DIALOG_STYLESHEET = """
QDialog {
    background-color: #f7f9fc;
}
QGroupBox {
    font-weight: bold;
    background-color: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    margin-top: 1em;
}
QGroupBox::title {
    font-family: "IranSANS", "Tahoma";
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 5px 15px;
    background-color: transparent;
    color: #4a5568;
}
QLabel {
    color: #4a5568;
    font-family: "IranSANS", "Tahoma";
    font-size: 10pt;
}
QLineEdit, QSpinBox, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 8px;
    color: #2d3748;
    font-size: 10pt;
}
QLineEdit:read-only {
    background-color: #f7f9fc;
}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #3182ce; /* Blue accent */
}
QCheckBox {
    color: #2d3748;
    spacing: 8px;
    font-size: 10pt;
}
QPushButton {
    font-weight: bold;
    border-radius: 5px;
    padding: 10px 25px;
    font-size: 10pt;
}
/* Style for BOTH our custom spinbox and standard line edits */
PersianSpinBox, QLineEdit, QSpinBox, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 8px 10px;
    color: #2d3748;
    font-size: 10pt;
}
PersianSpinBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #3182ce;
}
/* Primary Button (e.g., OK) */
QPushButton#PrimaryButton {
    background-color: #3182ce;
    color: white;
}
QPushButton#PrimaryButton:hover {
    background-color: #2b6cb0;
}
/* Secondary Button (e.g., Cancel) */
QPushButton {
    background-color: #e2e8f0;
    color: #4a5568;
    border: 1px solid #d2d6dc;
}
QPushButton:hover {
    background-color: #cbd5e0;
}
#PriceDisplay {
    font-weight: bold;
    color: #4a5568;
}
#TotalPriceDisplay {
    font-weight: bold;
    font-size: 12pt;
    color: #2d3748;
    background-color: #edf2f7;
}
"""