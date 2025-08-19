
WIZARD_STYLESHEET = """
/* --- 1. Top-Level Container Style --- */
/* This is the only part that sets the global font and background for the wizard. */
/* The #InvoiceWizard makes it specific to our main widget. */
QWidget#InvoiceWizard {
    font-family: "IranSANS", "Tahoma", sans-serif;
    font-size: 11pt;
    background-color: #f7f9fc; /* Light, clean background */
    color: #2d3748; /* Dark gray text for contrast */
}

/* --- 2. Styles for Direct Children of the Wizard --- */
/* These rules only apply to widgets that are INSIDE #InvoiceWizard */

#InvoiceWizard QLabel#StepLabel {
    color: #888;
    font-weight: bold;
    padding: 10px;
    border-bottom: 3px solid transparent;
}
#InvoiceWizard QLabel#StepLabel[state="active"] {
    color: #2b6cb0;
    border-bottom: 3px solid #2b6cb0;
}

#InvoiceWizard QGroupBox {
    font-weight: bold;
    background-color: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    margin-top: 1em;
}
#InvoiceWizard QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 5px 15px;
    color: #4a5568;
}

#InvoiceWizard QLabel {
    background-color: transparent;
}
#InvoiceWizard QLineEdit, 
#InvoiceWizard PersianSpinBox, 
#InvoiceWizard QSpinBox, 
#InvoiceWizard QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 10px;
}
#InvoiceWizard QLineEdit:focus, 
#InvoiceWizard PersianSpinBox:focus, 
#InvoiceWizard QSpinBox:focus, 
#InvoiceWizard QTextEdit:focus {
    border: 1px solid #3182ce;
}

/* --- Table Styling (scoped to the wizard) --- */
#InvoiceWizard QTableWidget {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #e2e8f0;
    background-color: #ffffff;
    alternate-background-color: #f7fafc;
}
#InvoiceWizard QTableWidget::item {
    padding: 6px 8px;
}
#InvoiceWizard QHeaderView::section {
    background-color: #edf2f7;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    color: #4a5568;
}

/* --- Button Styling (scoped to the wizard) --- */
/* We define the default button style within the wizard first */
#InvoiceWizard QPushButton {
    background-color: #e2e8f0;
    color: #4a5568;
    font-weight: bold;
    border: 1px solid #d2d6dc;
    border-radius: 5px;
    padding: 10px 20px;
}
#InvoiceWizard QPushButton:hover {
    background-color: #cbd5e0;
}
#InvoiceWizard QPushButton:disabled {
    background-color: #e2e8f0;
    color: #a0aec0;
    border-color: #e2e8f0;
}

/* Then we define the specific button styles */
#InvoiceWizard QPushButton#PrimaryButton {
    background-color: #2b6cb0;
    color: white;
    border: none;
}
#InvoiceWizard QPushButton#PrimaryButton:hover { background-color: #2c5282; }
#InvoiceWizard QPushButton#PrimaryButton:disabled { background-color: #a0aec0; border: none; }

#InvoiceWizard QPushButton#RemoveButton {
    background-color: #c53030;
    color: white;
    border: none;
}
#InvoiceWizard QPushButton#RemoveButton:hover { background-color: #9b2c2c; }

/* --- Completer Popup List --- */
/* This is a special case. QCompleter popups are top-level windows, */
/* so they are not children of #InvoiceWizard. This style can remain global */
/* as it's very specific and unlikely to cause conflicts. */
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
