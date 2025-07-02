from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QFrame, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QColor
from datetime import datetime
from modules.RBAC.helper_functions import DatabaseWorker
from modules.user_context import UserContext
import math


class UserDashboardWidget(QWidget):
    """Compact user dashboard with statistics and activity overview"""

    def __init__(self, parent):  # user_context: UserContext
        super().__init__()
        # self.username = user_context.username
        # self.role = user_context.role
        # self.role_fa = user_context.role_fa
        # self.full_name = user_context.full_name

        self.setup_ui()
        self.load_dashboard_data()

        # Update timer for real-time stats
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_dashboard_data)
        self.update_timer.start(60000)  # Update every minute

    def setup_ui(self):
        """Setup the dashboard UI with proper spacing in scroll area"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area that takes full parent space
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Scroll widget with proper spacing
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)  # Restored original spacing
        scroll_layout.setContentsMargins(20, 20, 20, 20)  # Restored original margins

        # Welcome header with more space
        welcome_frame = self.create_welcome_header()
        scroll_layout.addWidget(welcome_frame)

        # Statistics cards in 2x2 grid with more space
        stats_frame = self.create_stats_section()
        scroll_layout.addWidget(stats_frame)

        # Activity chart with more space
        activity_frame = self.create_activity_section()
        scroll_layout.addWidget(activity_frame)

        # Quick actions toolbar
        actions_frame = self.create_actions_section()
        scroll_layout.addWidget(actions_frame)

        # Add stretch at the bottom for proper spacing
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def create_welcome_header(self):
        """Create welcome header without time label"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 10px;
                color: white;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        self.welcome_label = QLabel(f"خوش آمدید، {self.full_name}")
        self.welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("color: white;")

        # Removed time_label as requested
        layout.addWidget(self.welcome_label)

        return frame

    def create_stats_section(self):
        """Create statistics section with proper spacing"""
        frame = QFrame()

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("آمار عملکرد")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title)

        # 2x2 grid of stat cards with proper spacing
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)

        self.session_card = self.create_stat_card("آمار جلسات", "0", "ورود امروز", "#2196F3")
        self.time_card = self.create_stat_card("زمان فعالیت", "0 ساعت", "این ماه", "#FF9800")
        self.avg_session_card = self.create_stat_card("میانگین جلسه", "0 دقیقه", "هر ورود", "#9C27B0")
        self.work_card = self.create_stat_card("کارهای انجام شده", "0", "فاکتور", "#4CAF50")

        stats_layout.addWidget(self.session_card, 0, 0)
        stats_layout.addWidget(self.time_card, 0, 1)
        stats_layout.addWidget(self.avg_session_card, 1, 0)
        stats_layout.addWidget(self.work_card, 1, 1)

        layout.addLayout(stats_layout)
        return frame

    def create_stat_card(self, title, value, subtitle, color):
        """Create a statistics card widget with original styling"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {color};")
        title_label.setAlignment(Qt.AlignCenter)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("value_label")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: #666;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)

        return card

    def create_activity_section(self):
        """Create activity chart section with proper spacing"""
        frame = QGroupBox("فعالیت هفتگی")
        frame.setFont(QFont("Arial", 12, QFont.Bold))

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.activity_widget = ActivityChartWidget()
        self.activity_widget.setMinimumHeight(200)
        self.activity_widget.setStyleSheet("background-color: white; border-radius: 5px;")
        layout.addWidget(self.activity_widget)

        return frame

    def create_actions_section(self):
        """Create actions section with proper spacing"""
        actions_group = QGroupBox("عملیات سریع")
        actions_group.setFont(QFont("Arial", 12, QFont.Bold))

        layout = QHBoxLayout(actions_group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        self.refresh_btn = QPushButton("بروزرسانی داده‌ها")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_dashboard_data)

        export_btn = QPushButton("📊 گزارش گیری")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        layout.addWidget(self.refresh_btn)
        layout.addWidget(export_btn)
        layout.addStretch()

        return actions_group

    def load_dashboard_data(self):
        """Load dashboard data from database"""
        # Placeholder for database worker
        self.worker = DatabaseWorker(self.username, "stats")
        self.worker.data_loaded.connect(self.update_dashboard)
        self.worker.start()

        # Mock data for demonstration
        mock_data = {
            'session_stats': [15, 1800, 27000],  # logins, avg_time, total_time
            'daily_stats': [5, 8, 12, 6, 9, 11, 7],  # 7 days of activity
            'invoice_stats': [23]  # total invoices
        }
        self.update_dashboard(mock_data)

    def update_dashboard(self, data):
        """Update dashboard with loaded data"""
        if not data:
            return

        session_stats = data.get('session_stats')
        daily_stats = data.get('daily_stats', [])
        invoice_stats = data.get('invoice_stats')

        if session_stats:
            total_logins = session_stats[0] or 0
            total_time_hours = round(session_stats[2] / 3600, 1) if session_stats[2] else 0
            avg_time_minutes = round(session_stats[1] / 60, 1) if session_stats[1] else 0

            # Update stat cards
            session_value = self.session_card.findChild(QLabel, "value_label")
            if session_value:
                session_value.setText(str(total_logins))

            time_value = self.time_card.findChild(QLabel, "value_label")
            if time_value:
                time_value.setText(f"{total_time_hours}h")

            avg_value = self.avg_session_card.findChild(QLabel, "value_label")
            if avg_value:
                avg_value.setText(f"{avg_time_minutes} دق")

        if invoice_stats:
            total_invoices = invoice_stats[0] or 0
            work_value = self.work_card.findChild(QLabel, "value_label")
            if work_value:
                work_value.setText(str(total_invoices))

        # Update activity chart
        if daily_stats:
            self.activity_widget.update_data(daily_stats)


class ActivityChartWidget(QWidget):
    """Simple bar chart widget for activity data"""

    def __init__(self):
        super().__init__()
        self.data = [0] * 7
        self.days = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

    def update_data(self, data):
        """Update chart data"""
        try:
            # Ensure data is a list of numbers
            if not data:
                self.data = [0] * 7
            else:
                # Convert each item to int/float, handling tuples or other types
                processed_data = []
                for item in data:
                    if isinstance(item, (tuple, list)):
                        # If it's a tuple/list, take the first numeric element
                        numeric_val = next((x for x in item if isinstance(x, (int, float))), 0)
                        processed_data.append(max(0, numeric_val))
                    elif isinstance(item, (int, float)):
                        processed_data.append(max(0, item))
                    else:
                        processed_data.append(0)

                # Ensure we have exactly 7 values
                if len(processed_data) >= 7:
                    self.data = processed_data[:7]
                else:
                    self.data = processed_data + [0] * (7 - len(processed_data))

            self.update()
        except Exception as e:
            print(f"Error updating chart data: {e}")
            self.data = [0] * 7
            self.update()

    def paintEvent(self, event):
        """Paint the bar chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#f8f9fa"))

        try:
            # Safely check if we have valid data
            valid_data = [val for val in self.data if isinstance(val, (int, float)) and val > 0]
            if not valid_data:
                painter.setPen(QPen(QColor("#666"), 1))
                painter.drawText(self.rect(), Qt.AlignCenter, "داده‌ای موجود نیست")
                return

            # Chart area
            margin = 30
            chart_width = self.width() - 2 * margin
            chart_height = self.height() - 2 * margin

            if chart_width <= 0 or chart_height <= 0:
                return

            bar_width = max(1, chart_width // 7)
            max_value = max(valid_data)

            # Draw bars
            for i, value in enumerate(self.data):
                try:
                    # Ensure value is numeric
                    numeric_value = float(value) if isinstance(value, (int, float)) else 0

                    if numeric_value > 0:
                        bar_height = int((numeric_value / max_value) * (chart_height - 30))
                        x = margin + i * bar_width + bar_width // 4
                        y = margin + chart_height - 30 - bar_height

                        # Bar
                        color = QColor("#4CAF50") if i == 6 else QColor("#2196F3")  # Highlight today
                        painter.fillRect(x, y, bar_width // 2, bar_height, QBrush(color))

                        # Value label
                        painter.setPen(QPen(QColor("#333"), 1))
                        painter.setFont(QFont("Arial", 9))
                        painter.drawText(x, y - 5, bar_width // 2, 15, Qt.AlignCenter, str(int(numeric_value)))

                    # Day label
                    painter.setPen(QPen(QColor("#666"), 1))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    day_x = margin + i * bar_width
                    day_y = margin + chart_height - 15
                    if i < len(self.days):
                        painter.drawText(day_x, day_y, bar_width, 15, Qt.AlignCenter, self.days[i])

                except Exception as e:
                    print(f"Error drawing bar {i}: {e}")
                    continue

        except Exception as e:
            print(f"Error in paintEvent: {e}")
            painter.setPen(QPen(QColor("#ff0000"), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "خطا در نمایش نمودار")
