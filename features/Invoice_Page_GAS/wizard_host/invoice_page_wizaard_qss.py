
WIZARD_STYLESHEET = """
/* --- Global Font and Background --- */
QWidget {
    font-family: "IranSANS", "Tahoma", sans-serif;
    font-size: 11pt;
    background-color: #f7f9fc; /* Light, clean background */
    color: #2d3748; /* Dark gray text for contrast */
}

/* --- Main Window Progress Bar --- */
QLabel#StepLabel {
    color: #888;
    font-weight: bold;
    padding: 10px;
    border-bottom: 3px solid transparent;
}
QLabel#StepLabel[state="active"] {
    color: #2b6cb0; /* A strong blue for the active step */
    border-bottom: 3px solid #2b6cb0;
}

/* --- Group Boxes --- */
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

/* --- General Widget Styles --- */
QLabel {
    background-color: transparent; /* Prevents inheriting parent background */
}
QLineEdit, PersianSpinBox, QSpinBox, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 10px;
}
QLineEdit:focus, PersianSpinBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #3182ce; /* Blue accent on focus */
}

/* --- Table Styling --- */
QTableWidget {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #e2e8f0;
    background-color: #ffffff;
    alternate-background-color: #f7fafc; /* Subtle striping */
}
QTableWidget::item {
    padding: 6px 8px; /* Compact rows */
}
QHeaderView::section {
    background-color: #edf2f7;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    color: #4a5568;
}

/* --- Button Styling --- */
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
QPushButton:disabled {
    background-color: #e2e8f0;
    color: #a0aec0;
    border-color: #e2e8f0;
}

QPushButton#PrimaryButton {
    background-color: #2b6cb0;
    color: white;
    border: none;
}
QPushButton#PrimaryButton:hover {
    background-color: #2c5282;
}
QPushButton#PrimaryButton:disabled {
    background-color: #a0aec0;
    border: none;
}

QPushButton#RemoveButton {
    background-color: #c53030;
    color: white;
    border: none;
}
QPushButton#RemoveButton:hover {
    background-color: #9b2c2c;
}

/* --- Completer Popup List --- */
QCompleter QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    font-family: "IranSANS", "Tahoma";
    font-size: 11pt;
}
QCompleter QAbstractItemView::item:hover {
    background-color: #edf2f7;
}
QCompleter QAbstractItemView::item:selected {
    background-color: #2b6cb0;
    color: white;
}
"""