
DOC_SELECTION_STYLES = """
QWidget#DocumentSelectionWidget {
    font-family: "IranSANS", "Tahoma", sans-serif;
    background-color: #f7f9fc;
    color: #2d3748;
}
QLabel {
    background-color: transparent;
}
QGroupBox {
    font-weight: bold;
    background-color: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    margin-top: 1em;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 5px 15px;
    color: #4a5568;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 10px;
    font-size: 11pt;
}
QLineEdit:focus {
    border: 1px solid #3182ce;
}
QTableWidget {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #e2e8f0;
    background-color: #ffffff;
    alternate-background-color: #f7fafc;
}
QTableWidget::item {
    padding: 6px 8px; /* Reduce vertical padding for more compact rows */
}
QHeaderView::section {
    background-color: #edf2f7;
    padding: 8px; /* Slightly reduce header padding */
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    color: #4a5568;
}
QHeaderView::section {
    background-color: #edf2f7;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    color: #4a5568;
}
QPushButton#PrimaryButton {
    background-color: #2b6cb0;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
}
QPushButton#PrimaryButton:hover {
    background-color: #2c5282;
}
QPushButton#PrimaryButton:disabled {
    background-color: #a0aec0;
}
QPushButton#RemoveButton {
    background-color: #c53030;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    padding: 5px 10px;
}
QPushButton#RemoveButton:hover {
    background-color: #9b2c2c;
}
QPushButton {
    background-color: #e2e8f0;
    color: #4a5568;
    font-weight: bold;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 10px 20px;
}
QPushButton:hover {
    background-color: #cbd5e0;
}
"""

DIALOG_STYLESHEET = """
QDialog#CalculationDialog {
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
    background-color: transparent;
}
QCheckBox {
    color: #2d3748;
    font-family: "IranSANS", "Tahoma";
    font-size: 10pt;
    spacing: 8px;
    background-color: transparent;
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

COMPLETER_POPUP = """
QListView {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    font-family: "IranSANS", "Tahoma";
    font-size: 11pt;
}
QListView::item:hover {
    background-color: #edf2f7;
}
QListView::item:selected {
    background-color: #2b6cb0;
    color: white;
}
    """