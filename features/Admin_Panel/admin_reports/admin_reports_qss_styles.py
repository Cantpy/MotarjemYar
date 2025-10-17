
ADVANCED_SEARCH_QSS = """
QGroupBox {
    font-size: 11pt;
    font-weight: bold;
    color: #333;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    background-color: #F0F2F5; /* Match the window background */
    color: #0078D7;
}

AdvancedSearchView QRadioButton {
    padding: 5px;
    spacing: 5px;
}

AdvancedSearchView QLineEdit,
AdvancedSearchView QDateEdit,
AdvancedSearchView QSpinBox {
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
}

AdvancedSearchView QLineEdit:focus,
AdvancedSearchView QDateEdit:focus,
AdvancedSearchView QSpinBox:focus {
    border-color: #0078D7;
}

AdvancedSearchView QPushButton#clearButton {
    background-color: #6c757d;
    color: white;
    padding: 8px 15px;
    border-radius: 5px;
}
AdvancedSearchView QPushButton#clearButton:hover {
    background-color: #5a6268;
}

AdvancedSearchView QPushButton#exportButton {
    background-color: #1D6F42;
    color: white;
    padding: 8px 15px;
    border-radius: 5px;
}
AdvancedSearchView QPushButton#exportButton:hover {
    background-color: #185c37;
}
AdvancedSearchView QPushButton#exportButton:disabled {
    background-color: #a0a0a0;
}
"""