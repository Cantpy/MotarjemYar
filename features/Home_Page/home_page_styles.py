HOME_PAGE_STYLES = """
        QWidget#HomePageView {
            background-color: #f5f5f5;
        }

        QLabel#pageTitle {
            font-family: IranSANS;
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        QLabel#sectionTitle {
            font-family: IranSANS;
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            margin-bottom: 10px;
        }

        QPushButton#refreshButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: bold;
        }

        QPushButton#refreshButton:hover {
            background-color: #2980b9;
        }

        QPushButton#refreshButton:pressed {
            background-color: #21618c;
        }

        QPushButton#settingsButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 18px;
        }

        QPushButton#settingsButton:hover {
            background-color: #7f8c8d;
        }

        QPushButton#viewAllButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
        }

        QPushButton#viewAllButton:hover {
            background-color: #7f8c8d;
        }

        QPushButton#actionButton {
            background-color: #27ae60;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: IranSANS;
            font-size: 12px;
        }

        QPushButton#actionButton:hover {
            background-color: #229954;
        }

        QWidget#statsWidget {
            background-color: transparent;
        }

        QTableWidget#invoicesTable {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            selection-background-color: #e3f2fd;
            gridline-color: #f0f0f0;
        }

        QTableWidget#invoicesTable::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        QHeaderView::section {
            background-color: #f8f9fa;
            color: #495057;
            padding: 10px;
            border: 1px solid #dee2e6;
            font-family: IranSANS;
            font-weight: bold;
        }
        """

STAT_WIDGET_STYLES = """
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin: 2px 0;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-color: #bdc3c7;
            }
            QLabel#cardTitle {
                font-family: IranSANS;
                font-size: 13px;
                color: #2c3e50;
                font-weight: normal;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #bdc3c7;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url(:/icons/check.png);
            }
            QCheckBox::indicator:hover {
                border-color: #95a5a6;
            }
        """

HOME_SETTINGS_STYLES = """
            /* Dialog background */
            QDialog {
                background-color: #f5f5f5;
                font-family: IranSANS;
                border-radius: 10px;
            }

            /* Scroll area */
            QScrollArea#settingsScroll {
                border: none;
                background-color: transparent;
            }
            QScrollArea#settingsScroll QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollArea#settingsScroll QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollArea#settingsScroll QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }

            /* Dialog title */
            QLabel#dialogTitle {
                font-family: IranSANS;
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: transparent;
            }

            /* Group boxes */
            QGroupBox#settingsGroup {
                font-family: IranSANS;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #f5f5f5;
            }

            /* Info label */
            QLabel#infoLabel {
                font-family: IranSANS;
                font-size: 12px;
                color: #7f8c8d;
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #3498db;
            }

            /* Card count label */
            QLabel#cardCountLabel {
                font-family: IranSANS;
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
                background-color: #ecf0f1;
            }

            /* Separators */
            QFrame#titleSeparator, QFrame#bottomSeparator {
                color: #bdc3c7;
                background-color: #bdc3c7;
                border: none;
                height: 1px;
                margin: 5px 0;
            }

            /* Settings labels */
            QLabel#settingsLabel {
                font-family: IranSANS;
                font-size: 14px;
                font-weight: normal;
                color: #34495e;
                padding: 8px 10px;
                background-color: transparent;
                min-width: 200px;
            }

            /* SpinBox styling to match homepage buttons */
            QSpinBox#settingsSpinBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px 15px;
                font-family: IranSANS;
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
                selection-background-color: #3498db;
                selection-color: white;
                min-width: 100px;
                max-width: 120px;
            }

            QSpinBox#settingsSpinBox:hover {
                border-color: #95a5a6;
                background-color: #fafafa;
            }

            QSpinBox#settingsSpinBox:focus {
                border-color: #3498db;
                background-color: white;
                outline: none;
            }

            /* SpinBox buttons */
            QSpinBox#settingsSpinBox::up-button {
                background-color: #ecf0f1;
                border: none;
                border-left: 1px solid #bdc3c7;
                border-radius: 0 4px 0 0;
                width: 18px;
                height: 15px;
            }

            QSpinBox#settingsSpinBox::up-button:hover {
                background-color: #d5dbdb;
            }

            QSpinBox#settingsSpinBox::up-button:pressed {
                background-color: #bdc3c7;
            }

            QSpinBox#settingsSpinBox::down-button {
                background-color: #ecf0f1;
                border: none;
                border-left: 1px solid #bdc3c7;
                border-radius: 0 0 4px 0;
                width: 18px;
                height: 15px;
            }

            QSpinBox#settingsSpinBox::down-button:hover {
                background-color: #d5dbdb;
            }

            QSpinBox#settingsSpinBox::down-button:pressed {
                background-color: #bdc3c7;
            }

            /* SpinBox arrows */
            QSpinBox#settingsSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #7f8c8d;
                width: 0;
                height: 0;
            }

            QSpinBox#settingsSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #7f8c8d;
                width: 0;
                height: 0;
            }

            /* Dialog buttons container */
            QDialogButtonBox#dialogButtons {
                background-color: transparent;
                border: none;
                padding: 10px 0;
            }

            /* OK Button - matches refreshButton style */
            QDialogButtonBox#dialogButtons QPushButton:default {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-family: IranSANS;
                font-size: 14px;
                font-weight: bold;
                min-width: 90px;
                margin: 0 5px;
            }

            QDialogButtonBox#dialogButtons QPushButton:default:hover {
                background-color: #2980b9;
            }

            QDialogButtonBox#dialogButtons QPushButton:default:pressed {
                background-color: #21618c;
            }

            /* Cancel Button - matches settingsButton style */
            QDialogButtonBox#dialogButtons QPushButton:!default {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-family: IranSANS;
                font-size: 14px;
                font-weight: bold;
                min-width: 90px;
                margin: 0 5px;
            }

            QDialogButtonBox#dialogButtons QPushButton:!default:hover {
                background-color: #7f8c8d;
            }

            QDialogButtonBox#dialogButtons QPushButton:!default:pressed {
                background-color: #6c7b7d;
            }

            /* Form layout spacing adjustments */
            QFormLayout {
                spacing: 20px;
            }
        """