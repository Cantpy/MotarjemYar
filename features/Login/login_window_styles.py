
LOGIN_WINDOW_STYLES = """
    QWidget {
        background-color: #f5f5f5;
        font-family: 'IRANSans', Tahoma, Arial, sans-serif;
    }
    QLabel#welcome_text {
        color: #2c3e50;
        font-size: 32px;
        font-weight: bold;
    }
    QLabel#login_text {
        color: #7f8c8d;
        font-size: 20px;
    }
    QLabel#role_text {
        color: #27ae60;
        font-size: 20px;
        font-weight: bold;
    }
    QLineEdit {
        padding: 15px;
        border: 2px solid #bdc3c7;
        border-radius: 8px;
        font-size: 14px;
        background-color: white;
        max-width: 300px;
        min-height: 20px;
    }
    QLineEdit:focus {
        border-color: #3498db;
        outline: none;
    }
    QPushButton#enter_button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: bold;
        min-width: 100px;
    }
    QPushButton#enter_button:hover {
        background-color: #2980b9;
    }
    QPushButton#enter_button:pressed {
        background-color: #21618c;
    }
    QPushButton#show_password_btn {
        background-color: #95a5a6;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 5px;
        font-size: 11px;
        max-width: 60px;
    }
    QPushButton#show_password_btn:hover {
        background-color: #7f8c8d;
    }
    QLabel#forgot_password_label, QLabel#register_label {
        color: #7f8c8d;
        font-size: 11px;
    }
    """


REMEMBER_ME_STYLES = """
    QCheckBox {
        color: #7f8c8d;
        font-size: 12px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #bdc3c7;
        border-radius: 3px;
        background-color: white;
    }
    QCheckBox::indicator:checked {
        border-color: #3498db;
        background-color: #3498db;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
    }
    QCheckBox::indicator:hover {
        border-color: #3498db;
    }
    """

LOGIN_SUCCESS_STYLES = """QLabel#role_text { color: #27ae60; font-size: 20px; font-weight: bold; }"""

LOGIN_FAILED_STYLES = """QLabel#error_text { color: #e74c3c; font-size: 12px; }"""

RESET_FORM_STYLES = """QLabel#login_text { color: #7f8c8d; font-size: 20px; }"""
