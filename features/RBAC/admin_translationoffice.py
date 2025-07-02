import sqlite3
import webbrowser
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QLineEdit,
                               QTextEdit, QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from modules.helper_functions import (show_warning_message_box, show_question_message_box, show_information_message_box,
                                      show_error_message_box)


class DatabaseManager(QWidget):
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database and create the translation_office table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create translation_office table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_office (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                reg_no TEXT,
                representative TEXT,
                manager TEXT,
                address TEXT,
                phone TEXT,
                website TEXT,
                whatsapp TEXT,
                instagram TEXT,
                telegram TEXT,
                other_media TEXT,
                open_hours TEXT,
                map_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM translation_office")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO translation_office (
                    name, reg_no, representative, manager, address, phone, website,
                    whatsapp, instagram, telegram, other_media, open_hours, map_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                'دفتر ترجمه جهانی',
                'REG-2024-001',
                'جان اسمیت',
                'سارا جانسون',
                'خیابان اصلی 123، مرکز شهر، شهر 12345',
                '+1-555-0123',
                'https://globaltranslation.com',
                '+1-555-0123',
                '@globaltranslation',
                '@globaltrans',
                'LinkedIn: company/global-translation',
                'دوشنبه تا جمعه: 9:00 صبح - 6:00 عصر، شنبه: 10:00 صبح - 2:00 عصر',
                'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3360.1488696677907!2d51.6427506!3d32.628858799999996!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3fbc379e64a0e77f%3A0x39b5c34e4afdf531!2z2K_Zgdiq2LEg2qnYp9ix24zYp9io24wg2KjbjNmGINin2YTZhdmE2YTbjCDZiCDYqtix2KzZhdmHINix2LPZhduMINis2YjYp9ivINin2qnYqNix24w!5e0!3m2!1sen!2s!4v1749253948071!5m2!1sen!2s'
            ])

        conn.commit()
        conn.close()

    def get_office_data(self):
        """Get the first translation office data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM translation_office LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            columns = ['id', 'name', 'reg_no', 'representative', 'manager', 'address',
                       'phone', 'website', 'whatsapp', 'instagram', 'telegram',
                       'other_media', 'open_hours', 'map_url', 'created_at', 'updated_at']
            return dict(zip(columns, row))
        return None

    def update_office_data(self, data):
        """Update translation office data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE translation_office SET
                name=?, reg_no=?, representative=?, manager=?, address=?, phone=?,
                website=?, whatsapp=?, instagram=?, telegram=?, other_media=?,
                open_hours=?, map_url=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', [
            data['name'], data['reg_no'], data['representative'], data['manager'],
            data['address'], data['phone'], data['website'], data['whatsapp'],
            data['instagram'], data['telegram'], data['other_media'],
            data['open_hours'], data['map_url'], data['id']
        ])
        conn.commit()
        conn.close()


class EditDialog(QDialog):
    def __init__(self, office_data, parent=None):
        super().__init__(parent)
        self.office_data = office_data.copy()
        self.setWindowTitle("ویرایش اطلاعات دفتر ترجمه")
        self.setModal(True)
        self.resize(500, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Create scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # Create input fields
        self.fields = {}
        field_labels = {
            'name': 'نام دفتر',
            'reg_no': 'شماره ثبت',
            'representative': 'مترجم مسئول',
            'manager': 'مدیر',
            'address': 'آدرس',
            'phone': 'تلفن',
            'website': 'وب‌سایت',
            'whatsapp': 'واتس‌اپ',
            'instagram': 'اینستاگرام',
            'telegram': 'تلگرام',
            'other_media': 'سایر رسانه‌ها',
            'open_hours': 'ساعات کاری',
            'map_url': 'لینک نقشه'
        }

        for field, label in field_labels.items():
            if field in ['address', 'other_media', 'map_url']:
                widget = QTextEdit()
                widget.setMaximumHeight(80)
                widget.setPlainText(str(self.office_data.get(field, '')))
            else:
                widget = QLineEdit()
                widget.setText(str(self.office_data.get(field, '')))

            self.fields[field] = widget
            form_layout.addRow(label + ":", widget)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره")
        cancel_btn = QPushButton("انصراف")

        save_btn.clicked.connect(self.save_data)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def save_data(self):
        """Save the edited data"""
        for field, widget in self.fields.items():
            if isinstance(widget, QTextEdit):
                self.office_data[field] = widget.toPlainText()
            else:
                self.office_data[field] = widget.text()
        self.accept()

    def get_data(self):
        return self.office_data


class TranslationOfficeWidget(QWidget):
    def __init__(self, parent, db_path):
        super().__init__(parent=None)
        self.db_manager = DatabaseManager(db_path)
        self.office_data = self.db_manager.get_office_data()
        self.web_view = None  # Initialize as None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title and Edit Button
        header_layout = QHBoxLayout()

        title = QLabel("اطلاعات دفتر ترجمه")
        title.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        edit_btn = QPushButton("ویرایش اطلاعات")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: Tahoma;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        edit_btn.clicked.connect(self.open_edit_dialog)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(edit_btn)
        layout.addLayout(header_layout)

        # Main content in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Office Information Section
        self.create_info_section(content_layout)

        # Map Section
        self.create_map_section(content_layout)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def create_info_section(self, parent_layout):
        """Create the information display section"""
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        info_layout = QVBoxLayout(info_frame)

        # Basic Information
        basic_info = [
            ("نام دفتر", self.office_data.get('name', '')),
            ("شماره ثبت", self.office_data.get('reg_no', '')),
            ("مترجم مسئول", self.office_data.get('representative', '')),
            ("مدیر", self.office_data.get('manager', '')),
        ]

        for label, value in basic_info:
            self.add_info_row(info_layout, label, value)

        # Contact Information
        contact_title = QLabel("اطلاعات تماس")
        contact_title.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        contact_title.setStyleSheet("color: #34495e; margin-top: 15px; margin-bottom: 10px;")
        info_layout.addWidget(contact_title)

        contact_info = [
            ("آدرس", self.office_data.get('address', '')),
            ("تلفن", self.office_data.get('phone', '')),
            ("وب‌سایت", self.office_data.get('website', '')),
            ("واتس‌اپ", self.office_data.get('whatsapp', '')),
            ("اینستاگرام", self.office_data.get('instagram', '')),
            ("تلگرام", self.office_data.get('telegram', '')),
            ("سایر رسانه‌ها", self.office_data.get('other_media', '')),
            ("ساعات کاری", self.office_data.get('open_hours', '')),
        ]

        for label, value in contact_info:
            self.add_info_row(info_layout, label, value)

        parent_layout.addWidget(info_frame)

    def add_info_row(self, layout, label, value):
        """Add an information row"""
        row_layout = QHBoxLayout()

        label_widget = QLabel(label + ":")
        label_widget.setFont(QFont("Tahoma", 9, QFont.Weight.Bold))
        label_widget.setStyleSheet("color: #7f8c8d; min-width: 120px;")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignTop)

        value_widget = QLabel(str(value))
        value_widget.setFont(QFont("Tahoma", 9))
        value_widget.setStyleSheet("color: #2c3e50;")
        value_widget.setWordWrap(True)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignTop)

        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget, 1)
        layout.addLayout(row_layout)

    def create_map_section(self, parent_layout):
        """Create the map section - SOLUTION 1: Lazy Loading"""
        map_frame = QFrame()
        map_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        map_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        map_layout = QVBoxLayout(map_frame)

        map_title = QLabel("موقعیت مکانی")
        map_title.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        map_title.setStyleSheet("color: #34495e; margin-bottom: 10px;")
        map_layout.addWidget(map_title)

        # Create a placeholder widget first
        self.map_placeholder = QWidget()
        self.map_placeholder.setFixedHeight(300)
        self.map_placeholder.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 4px;
            }
        """)

        placeholder_layout = QVBoxLayout(self.map_placeholder)
        placeholder_label = QLabel("برای نمایش نقشه کلیک کنید")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #6c757d; font-size: 14px;")
        placeholder_layout.addWidget(placeholder_label)

        # Add click event to load map
        self.map_placeholder.mousePressEvent = self.load_map_on_demand

        map_layout.addWidget(self.map_placeholder)

        # Instructions
        instruction = QLabel("برای باز کردن در گوگل مپ روی نقشه کلیک کنید")
        instruction.setFont(QFont("Tahoma", 8))
        instruction.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 5px;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_layout.addWidget(instruction)

        parent_layout.addWidget(map_frame)

    def load_map_on_demand(self, event):
        """Load the map only when clicked - SOLUTION 1"""
        if self.web_view is None:
            try:
                # Create QWebEngineView with proper initialization
                self.web_view = QWebEngineView()
                self.web_view.setFixedHeight(300)

                # Load the map
                map_url = self.office_data.get('map_url', '')
                if map_url:
                    html_content = f'''
                    <html>
                    <head>
                        <style>
                            body {{ margin: 0; padding: 0; }}
                            iframe {{ width: 100%; height: 300px; border: 0; }}
                        </style>
                    </head>
                    <body>
                        <iframe src="{map_url}" 
                                allowfullscreen="" 
                                loading="lazy">
                        </iframe>
                    </body>
                    </html>
                    '''
                    self.web_view.setHtml(html_content)

                # Replace placeholder with web view
                layout = self.map_placeholder.parent().layout()
                index = layout.indexOf(self.map_placeholder)
                layout.removeWidget(self.map_placeholder)
                self.map_placeholder.deleteLater()
                layout.insertWidget(index, self.web_view)

                # Add click handler for Google Maps
                self.web_view.mousePressEvent = self.open_google_maps

            except Exception as e:
                title = "خطا در بارگذاری نقشه"
                message = (f"{str(e)}\n\n")
                show_error_message_box(self, title, message)
                self.show_map_error()

    def show_map_error(self):
        """Show error message if map fails to load"""
        error_widget = QWidget()
        error_widget.setFixedHeight(300)
        error_widget.setStyleSheet("""
            QWidget {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
            }
        """)

        error_layout = QVBoxLayout(error_widget)
        error_label = QLabel("خطا در بارگذاری نقشه")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #721c24; font-size: 14px;")
        error_layout.addWidget(error_label)

        # Replace placeholder with error widget
        layout = self.map_placeholder.parent().layout()
        index = layout.indexOf(self.map_placeholder)
        layout.removeWidget(self.map_placeholder)
        self.map_placeholder.deleteLater()
        layout.insertWidget(index, error_widget)

    def open_google_maps(self, event):
        """Open location in Google Maps"""
        map_url = self.office_data.get('map_url', '')
        if map_url:
            try:
                # Convert embed URL to regular Google Maps URL
                google_maps_url = map_url.replace('/embed', '').replace('!3m3!1m2!', '!3m1!1s')
                webbrowser.open(google_maps_url)
            except Exception as e:
                title = "خطا در باز کردن گوگل مپ"
                message = (f"خطا در باز کردن نقشه: \n"
                           f"{str(e)}")
                show_error_message_box(self, title, message)

    def showEvent(self, event):
        """Handle widget show event - SOLUTION 2: Delayed initialization"""
        super().showEvent(event)
        # Delay WebEngine creation until widget is actually shown
        if not hasattr(self, '_webengine_initialized'):
            QTimer.singleShot(100, self.initialize_webengine_delayed)
            self._webengine_initialized = True

    def initialize_webengine_delayed(self):
        """Initialize WebEngine after a delay"""
        # Only initialize if the widget is visible and has a valid parent
        if self.isVisible() and self.parent():
            pass  # WebEngine will be loaded on demand

    def open_edit_dialog(self):
        """Open the edit dialog"""
        dialog = EditDialog(self.office_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            self.db_manager.update_office_data(updated_data)
            self.office_data = updated_data
            self.refresh_display()

            # Show success message
            QMessageBox.information(self, "موفقیت", "اطلاعات دفتر با موفقیت به‌روزرسانی شد!")

    def refresh_display(self):
        """Refresh the display with updated data"""
        # Clear and rebuild the layout
        layout = self.layout()
        for i in reversed(range(layout.count())):
            child = layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()

        # Reset web view
        self.web_view = None
        self.setup_ui()

    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        if self.web_view:
            self.web_view.close()
            self.web_view.deleteLater()
            self.web_view = None
        super().closeEvent(event)


# ALTERNATIVE SOLUTION 2: Use QLabel with clickable map image
# class TranslationOfficeWidgetAlternative(QWidget):
#     """Alternative implementation without QWebEngineView"""
#
#     def __init__(self, parent, db_path):
#         super().__init__(parent=None)
#         self.db_manager = DatabaseManager(db_path)
#         self.office_data = self.db_manager.get_office_data()
#         self.setup_ui()
#
#     def create_map_section_alternative(self, parent_layout):
#         """Create map section using QLabel instead of QWebEngineView"""
#         map_frame = QFrame()
#         map_frame.setFrameStyle(QFrame.Shape.StyledPanel)
#         map_frame.setStyleSheet("""
#             QFrame {
#                 background-color: white;
#                 border: 1px solid #ddd;
#                 border-radius: 8px;
#                 padding: 15px;
#             }
#         """)
#
#         map_layout = QVBoxLayout(map_frame)
#
#         map_title = QLabel("موقعیت مکانی")
#         map_title.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
#         map_title.setStyleSheet("color: #34495e; margin-bottom: 10px;")
#         map_layout.addWidget(map_title)
#
#         # Create a clickable map placeholder
#         map_button = QPushButton("نمایش نقشه در مرورگر")
#         map_button.setFixedHeight(300)
#         map_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #e9ecef;
#                 border: 2px solid #dee2e6;
#                 border-radius: 8px;
#                 font-size: 16px;
#                 color: #495057;
#                 font-family: Tahoma;
#             }
#             QPushButton:hover {
#                 background-color: #f8f9fa;
#                 border-color: #adb5bd;
#             }
#             QPushButton:pressed {
#                 background-color: #dee2e6;
#             }
#         """)
#         map_button.clicked.connect(self.open_google_maps_direct)
#         map_layout.addWidget(map_button)
#
#         # Address display
#         address = self.office_data.get('address', '')
#         if address:
#             address_label = QLabel(f"آدرس: {address}")
#             address_label.setFont(QFont("Tahoma", 9))
#             address_label.setStyleSheet("color: #6c757d; margin-top: 5px;")
#             address_label.setWordWrap(True)
#             address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#             map_layout.addWidget(address_label)
#
#         parent_layout.addWidget(map_frame)
#
#     def open_google_maps_direct(self):
#         """Open Google Maps directly"""
#         map_url = self.office_data.get('map_url', '')
#         address = self.office_data.get('address', '')
#
#         if map_url:
#             try:
#                 google_maps_url = map_url.replace('/embed', '').replace('!3m3!1m2!', '!3m1!1s')
#                 webbrowser.open(google_maps_url)
#             except Exception as e:
#                 print(f"Error opening Google Maps: {e}")
#         elif address:
#             # Fallback: search by address
#             search_url = f"https://www.google.com/maps/search/{address}"
#             webbrowser.open(search_url)


# SOLUTION 3: Separate dialog for map
# class MapDialog(QDialog):
#     """Separate dialog for displaying the map"""
#
#     def __init__(self, map_url, parent=None):
#         super().__init__(parent)
#         self.map_url = map_url
#         self.setWindowTitle("موقعیت مکانی")
#         self.setModal(True)
#         self.resize(800, 600)
#         self.setup_ui()
#
#     def setup_ui(self):
#         layout = QVBoxLayout(self)
#
#         # Create web view in separate dialog
#         self.web_view = QWebEngineView()
#
#         if self.map_url:
#             html_content = f'''
#             <html>
#             <head>
#                 <style>
#                     body {{ margin: 0; padding: 0; }}
#                     iframe {{ width: 100%; height: 100vh; border: 0; }}
#                 </style>
#             </head>
#             <body>
#                 <iframe src="{self.map_url}"
#                         allowfullscreen=""
#                         loading="lazy">
#                 </iframe>
#             </body>
#             </html>
#             '''
#             self.web_view.setHtml(html_content)
#
#         layout.addWidget(self.web_view)
#
#         # Close button
#         close_btn = QPushButton("بستن")
#         close_btn.clicked.connect(self.accept)
#         layout.addWidget(close_btn)
#
#     def show_map_dialog(map_url, parent=None):
#         """Static method to show map dialog"""
#         dialog = MapDialog(map_url, parent)
#         dialog.exec()


# Usage example for the separate dialog approach:
# def show_map_in_dialog(self):
#     """Show map in separate dialog"""
#     map_url = self.office_data.get('map_url', '')
#     if map_url:
#         MapDialog.show_map_dialog(map_url, self)
