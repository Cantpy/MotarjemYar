# customer_info_qss_styles.py

CUSTOMER_INFO_STYLES = """
        QWidget#CustomerInfoWidget {
            font-family: "IranSANS", "Tahoma", sans-serif;
            font-size: 11pt;
            background-color: #f7f7f7;
            color: #333;
        }
        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-top: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 5px 15px;
            background-color: #f0f0f0;
            border: 1px solid #e0e0e0;
            border-bottom: 1px solid #ffffff;
            border-radius: 5px;
            color: #555;
            font-weight: bold;
        }
        /* The base QLineEdit style is now set programmatically */
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px;
            color: #333333;
        }
        QLineEdit:focus {
            border: 2px solid #007bff; /* Focus style still works perfectly */
        }
        QPushButton#PrimaryButton {
            background-color: #007bff; color: white; font-weight: bold;
            border: none; border-radius: 5px; padding: 10px 20px;
        }
        QPushButton#PrimaryButton:hover { background-color: #0069d9; }
        QPushButton {
            background-color: #6c757d; color: white; font-weight: bold;
            border: none; border-radius: 5px; padding: 10px 20px;
        }
        QPushButton:hover { background-color: #5a6268; }
        #RemoveButton {
            background-color: #dc3545; max-width: 30px; font-size: 14pt; padding: 5px;
        }
        #RemoveButton:hover { background-color: #c82333; }
        QCheckBox { spacing: 10px; font-weight: bold; }
        QScrollArea { border: none; background-color: transparent; }
        """

BASE_LINEEDIT_STYLE = """background-color: #ffffff;
                         border: 1px solid #cccccc; 
                         border-radius: 4px; 
                         padding: 8px;
                         color: #333333;"""

VALID_LINEEDIT_STYLE = BASE_LINEEDIT_STYLE + " border: 2px solid #28a745;"  # Green
INVALID_LINEEDIT_STYLE = BASE_LINEEDIT_STYLE + " border: 2px solid #dc3545;"  # Red