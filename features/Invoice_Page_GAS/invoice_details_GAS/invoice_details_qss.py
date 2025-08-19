INVOICE_DETAILS_QSS = """
QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QComboBox {
    padding: 8px;
    border: 2px solid #e9ecef;
    border-radius: 6px;
    background-color: white;
    selection-background-color: #007bff;
}
QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, 
QTextEdit:focus, QComboBox:focus {
    border-color: #007bff;
    outline: none;
}
QDateEdit::drop-down, QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #e9ecef;
    border-left-style: solid;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #f8f9fa;
}
QDateEdit::down-arrow, QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QCheckBox {
    spacing: 8px;
    font-weight: bold;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #e9ecef;
    border-radius: 4px;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #007bff;
    border-color: #007bff;
}
QGroupBox {
    font-weight: bold;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #495057;
}
    """
