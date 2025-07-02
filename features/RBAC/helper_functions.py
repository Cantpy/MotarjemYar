import sqlite3
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QSettings, Signal, QThread
from PySide6.QtGui import QPixmap
import bcrypt
from modules.helper_functions import return_resource


users_database = return_resource("databases", "users.db")
invoices_database = return_resource("databases", "invoices.db")


class DatabaseWorker(QThread):
    """Worker thread for database operations to avoid blocking UI"""
    data_loaded = Signal(dict)

    def __init__(self, username, operation_type):
        super().__init__()
        self.username = username
        self.operation_type = operation_type

    def run(self):
        if self.operation_type == "profile":
            data = self.get_user_profile()
        elif self.operation_type == "stats":
            data = self.get_dashboard_data()
        else:
            data = {}

        self.data_loaded.emit(data)

    def get_user_profile(self):
        """Get user profile data from database"""
        try:
            with sqlite3.connect(users_database) as conn:
                cursor = conn.cursor()

                # Get user profile
                cursor.execute("""
                    SELECT full_name, role_fa, date_of_birth, email, phone, 
                           national_id, address, bio, avatar_path, created_at
                    FROM user_profiles 
                    WHERE username = ?
                """, (self.username,))

                profile = cursor.fetchone()

                # Get user account info
                cursor.execute("""
                    SELECT role, active, start_date, created_at
                    FROM users 
                    WHERE username = ?
                """, (self.username,))

                user_info = cursor.fetchone()

                return {
                    'profile': profile,
                    'user_info': user_info,
                    'username': self.username
                }

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}

    def get_dashboard_data(self):
        """Get dashboard statistics"""
        try:
            with sqlite3.connect(users_database) as conn:
                cursor = conn.cursor()

                # Get session stats for last 30 days
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_logins,
                        AVG(time_on_app) as avg_time_seconds,
                        SUM(time_on_app) as total_time_seconds,
                        MAX(time_on_app) as max_session_seconds,
                        MIN(time_on_app) as min_session_seconds
                    FROM login_logs 
                    WHERE username = ? 
                    AND login_time >= datetime('now', '-30 days')
                    AND time_on_app IS NOT NULL
                """, (self.username,))

                session_stats = cursor.fetchone()

                # Get recent logins (last 7 days)
                cursor.execute("""
                    SELECT DATE(login_time) as login_date, COUNT(*) as daily_logins
                    FROM login_logs 
                    WHERE username = ? 
                    AND login_time >= datetime('now', '-7 days')
                    GROUP BY DATE(login_time)
                    ORDER BY login_date DESC
                """, (self.username,))

                daily_stats = cursor.fetchall()
                invoice_stats = self.get_user_invoices()

                return {
                    'session_stats': session_stats,
                    'daily_stats': daily_stats,
                    'invoice_stats': invoice_stats,
                    'username': self.username
                }

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}
    def get_user_invoices(self):
        """Get user's invoice statistics if they are a translator"""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                                    SELECT COUNT(*) as total_invoices,
                                           SUM(CASE WHEN invoice_status = 1 THEN 1 ELSE 0 END) as completed_invoices,
                                           SUM(total_amount) as total_revenue
                                    FROM issued_invoices 
                                    WHERE translator = ? OR username = ?
                                """, (self.username, self.username))

                invoice_stats = cursor.fetchone()
                return invoice_stats

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}


class ImageViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("نمایش تصویر")
        self.setMinimumSize(400, 400)

        layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.load_image(image_path)

    def load_image(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("تصویر قابل نمایش نیست.")
        else:
            # Resize to fit the dialog while maintaining aspect ratio
            scaled = pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password)


def check_login(username: str, password: str):
    with sqlite3.connect(users_database) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT password_hash, role, active FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if not row:
            return None  # user not found

        password_hash, role, active = row
        if not active:
            return None  # deactivated user

        if verify_password(password, password_hash):
            return role
        return None  # incorrect password


def add_user_and_profile(user_data, profile_data):
    with sqlite3.connect(users_database) as conn:
        cursor = conn.cursor()
        try:
            # Insert user
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, user_data)

            # Insert profile
            cursor.execute("""
                INSERT INTO user_profiles (username, full_name, role_fa, date_of_birth, email, phone, national_id, address, bio, avatar_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, profile_data)

            print("✅ User and profile created.")
        except sqlite3.Error as e:
            print("❌ Failed:", e)


def get_user_data_from_db(username):
    with sqlite3.connect(users_database) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, u.start_date, up.full_name, up.role_fa,
                   up.date_of_birth, up.email, up.phone, up.national_id,
                   up.address, up.bio, up.avatar_path
            FROM users u
            JOIN user_profiles up ON u.username = up.username
            WHERE u.username = ?
        """, (username,))
        row = cursor.fetchone()

        if row:
            return {
                "username": row[0],
                "start_date": row[1],
                "full_name": row[2],
                "role_fa": row[3],
                "date_of_birth": row[4],
                "email": row[5],
                "phone": row[6],
                "national_id": row[7],
                "address": row[8],
                "bio": row[9],
                "avatar_path": row[10],
            }
        else:
            return None


def fetch_active_user_profiles():
    with sqlite3.connect(users_database) as conn:

        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.id AS user_id,
                up.full_name,
                up.role_fa,
                up.phone,
                up.email,
                up.avatar_path
            FROM users u
            JOIN user_profiles up ON u.username = up.username
            WHERE u.active = 1;
        """)

        results = cursor.fetchall()
        return results

