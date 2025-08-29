# Admin_Panel/wage_calculator/wage_calculator_styles.py

WAGE_CALCULATOR_STYLES="""


/* --- Styles for Wage Calculator Page --- */

/* Main container for the page */
WageCalculatorView {
    background-color: #f7f9fc;
}

/* Style for the top bar elements */
WageCalculatorView QComboBox {
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
    min-width: 120px;
}

WageCalculatorView QPushButton#runPayrollButton {
    font-weight: bold;
    padding: 8px 15px;
    border-radius: 5px;
    background-color: #28a745;
    color: white;
}
WageCalculatorView QPushButton#runPayrollButton:hover {
    background-color: #218838;
}

/* Main employee table styling */
WageCalculatorView QTableWidget {
    border: 1px solid #e0e0e0;
    gridline-color: #e0e0e0;
    background-color: white;
    alternate-background-color: #f7f9fc;
}

WageCalculatorView QHeaderView::section {
    background-color: #e9ecef;
    padding: 8px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #0078D7;
}

WageCalculatorView QTableWidget::item:selected {
    background-color: #cce5ff;
    color: #004085;
}

/* Payslip Detail Panel on the right */
WageCalculatorView #payslipPanel {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

WageCalculatorView #payslipPanel QLabel#payslipName {
    font-size: 14pt;
    font-weight: bold;
    color: #005A9E;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

WageCalculatorView #payslipPanel QLabel#payslipPeriod {
    font-size: 10pt;
    color: #666;
    margin-bottom: 15px;
}

WageCalculatorView #payslipPanel QLabel#payslipDetails {
    line-height: 1.6;
}

WageCalculatorView #payslipPanel QPushButton {
    font-weight: bold;
    padding: 8px 15px;
    border-radius: 5px;
    background-color: #0078D7;
    color: white;
}
WageCalculatorView #payslipPanel QPushButton:hover {
    background-color: #005A9E;
}
"""