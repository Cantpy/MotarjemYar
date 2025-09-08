from PySide6.QtCore import QPropertyAnimation, Qt, QEasingCurve, QPoint, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette, QIcon
from PySide6.QtWidgets import (QMainWindow, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication,
                               QFrame)

from modules.helper_functions import (return_resource, render_colored_svg, set_svg_icon, show_error_message_box)

from modules.user_context import UserContext
from modules.page_manager import PageManager

import sqlite3
import os



# ----------------------  Exit Dialog  ---------------------- #
class ExitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(400, 200)
        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()
        self.exit_text = QLabel(self)
        self.exit_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTrailing |
                                    Qt.AlignmentFlag.AlignVCenter)
        self.button_exit = QPushButton(self)
        self.button_cancel = QPushButton(self)

        self.setWindowTitle("خروج")
        self.exit_text.setText("آیا می‌خواهید از مترجم‌یار خارج شوید؟")
        self.exit_text.setFont(QFont("IranSans", 12))
        self.button_exit.setText("بله")
        self.button_exit.setFont(QFont("IranSans", 11))
        self.button_cancel.setText("خیر")
        self.button_cancel.setFont(QFont("IranSans", 11))

        self.button_exit.clicked.connect(self.confirm_exit)
        self.button_cancel.clicked.connect(self.reject_exit)

        self.vertical_layout.addWidget(self.exit_text)
        self.horizontal_layout.addWidget(self.button_exit)
        self.horizontal_layout.addWidget(self.button_cancel)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.main_window = self.parent()

    def confirm_exit(self):
        """Animate fade-out for ExitDialog first, then Main_Window before quitting."""
        if not self.main_window:  # Fallback if there's no parent
            self.close_and_exit()
            return

        # Step 1: Animate ExitDialog fade-out
        self.exit_animation = QPropertyAnimation(self, b"windowOpacity")
        self.exit_animation.setDuration(300)  # 300ms duration for dialog
        self.exit_animation.setStartValue(1.0)
        self.exit_animation.setEndValue(0.0)
        self.exit_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Step 2: Animate Main_Window fade-out AFTER ExitDialog animation finishes
        self.exit_animation.finished.connect(self.fade_out_main_window)

        self.exit_animation.start()  # Start exit animation for ExitDialog

    def fade_out_main_window(self):
        """Animate Main_Window fade-out after ExitDialog fades out."""
        self.main_window.exit_animation = QPropertyAnimation(self.main_window, b"windowOpacity")
        self.main_window.exit_animation.setDuration(500)  # 500ms duration for main window
        self.main_window.exit_animation.setStartValue(1.0)
        self.main_window.exit_animation.setEndValue(0.0)
        self.main_window.exit_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Close both ExitDialog and app after main window animation
        self.main_window.exit_animation.finished.connect(self.close_and_exit)

        self.main_window.exit_animation.start()

    def close_and_exit(self):
        """Close ExitDialog and exit the app."""
        self.accept()
        QApplication.quit()

    def reject_exit(self):
        """Close the dialog without exiting."""
        self.reject()


# --------------------------- Main Window -------------------------- #
class MainWindow(QMainWindow):
    MARGIN = 8  # Thickness of the resizing border

    def __init__(self, app_manager, user_context: UserContext):
        super().__init__()

        # UsersModel context variables
        self.user_context = user_context
        self.current_user = self.user_context.username
        self.current_role = self.user_context.role
        self.current_role = "admin"

        self.app_manager = app_manager

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.resize(1024, 768)

        from qt_designer_ui.ui_second_MainWindow import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.app_logo.setPixmap(QPixmap(logo_file))

        # Initialize pages
        self.initialize_pages()

        # Set initial page index
        self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.indexOf(self.home_page))

        # Set initial states
        self.ui.frame.setFixedWidth(100)  # Start with collapsed menu
        self.expanded_width = 225  # Expanded width of the menu
        self.collapsed_width = 100  # Collapsed width of the menu

        self.normal_geometry = None
        self.max_animation = None
        self.login_window = None

        # Install event filters for hover detection
        self.ui.frame.installEventFilter(self)

        # Initialize the animation for the menu
        self.animation = QPropertyAnimation(self.ui.frame, b"maximumWidth")
        self.animation.setDuration(450)  # Set duration to 450ms for a snappier feel
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)  # Use a smooth easing curve

        # Setup connections
        self.setup_page_manager()
        self.setup_connections()

        # Titlebar Widget
        self.pressed = False
        self.is_maximized = False
        self.resizing = False
        self.drag_position = None
        self.resize_direction = None
        self.start_pos = QPoint()
        self.window_pos = QPoint()

        self.hide_menu_labels()
        self.set_icons()

    def initialize_pages(self):
        """Initialize only home page initially; others load lazily"""
        from modules.Home import HomePage
        self.pages = {}  # Dictionary to hold references to pages

        self.home_page = HomePage(self.ui.stackedWidget)
        self.ui.stackedWidget.addWidget(self.home_page)
        self.pages['home'] = self.home_page

    def load_page(self, page_name):
        """Lazy-load and add the page to the stacked widget if not loaded"""
        if page_name in self.pages:
            return self.pages[page_name]

        if page_name == "invoice":
            from modules.InvoicePage.invoice_page import InvoicePage
            page = InvoicePage(self.ui.stackedWidget)  # user_context=self.user_context

        elif page_name == "documents":
            from modules.Documents import TabbedServicesManager
            page = TabbedServicesManager(self.ui.stackedWidget)

        elif page_name == "invoice_table":
            from modules.InvoiceTable.invoice_table import InvoiceTable
            page = InvoiceTable(self.ui.stackedWidget)

        elif page_name == "reports":
            from modules.Reports.reports_page import ReportsPage
            page = ReportsPage(self.ui.stackedWidget)

        elif page_name == "settings":
            from modules.Settings import AppSettings
            page = AppSettings(self.ui.stackedWidget)

        else:
            raise ValueError(f"Unknown page: {page_name}")

        self.ui.stackedWidget.addWidget(page)
        self.pages[page_name] = page
        return page

    def setup_page_manager(self):
        self.page_manager = PageManager(self.ui.stackedWidget)

        # HomePage — initially visible
        from modules.Home import HomePage
        self.page_manager.register("home", lambda: HomePage(self.ui.stackedWidget))

        from modules.InvoicePage.invoice_page import InvoicePage
        self.page_manager.register("invoice",
                                   lambda: InvoicePage(self.ui.stackedWidget))  # user_context=self.user_context

        from modules.Documents import TabbedServicesManager
        self.page_manager.register("documents", lambda: TabbedServicesManager(self.ui.stackedWidget))

        from modules.InvoiceTable.invoice_table import InvoiceTable
        self.page_manager.register("invoice_table", lambda: InvoiceTable(self.ui.stackedWidget))

        from modules.Reports.reports_page import ReportsPage
        self.page_manager.register("reports", lambda: ReportsPage(self.ui.stackedWidget))

        from modules.Settings import AppSettings
        self.page_manager.register("settings", lambda: AppSettings(self.ui.stackedWidget))

        # Show only the home page initially
        self.page_manager.show("home")

        # Optional preload after UI is shown
        QTimer.singleShot(3000, lambda: self.page_manager.preload("settings"))
        QTimer.singleShot(5000, lambda: self.page_manager.preload("documents"))

    def setup_connections(self):
        """Setup all signal connections using page manager"""

        # Map buttons to page names in the PageManager
        button_page_map = {
            self.ui.home_button: "home",
            self.ui.home_text_button: "home",
            self.ui.invoice_button: "invoice",
            self.ui.invoice_text_button: "invoice",
            self.ui.documents_button: "documents",
            self.ui.documents_text__button: "documents",
            self.ui.issued_invoices_button: "invoice_table",
            self.ui.issued_invoices_text_button: "invoice_table",
            self.ui.reports_button: "reports",
            self.ui.reports_text_button: "reports",
            self.ui.settings_button: "settings",
            self.ui.settings_text_button: "settings",
        }

        for button, page_name in button_page_map.items():
            button.clicked.connect(lambda _, name=page_name: self.page_manager.show(name))

        # UsersModel and window controls
        self.ui.large_user_pic.clicked.connect(self.show_users_page)
        self.ui.x_button.clicked.connect(self.show_exit_dialog)
        self.ui.maximize_button.clicked.connect(self.smooth_maximize)
        self.ui.minimize_button.clicked.connect(self.smooth_minimize)

    def set_user_context(self, user_full_name, user_role_fa, avatar):
        """Set the current user context and update UI"""
        self.user_context.full_name = user_full_name
        self.user_context.role_fa = user_role_fa
        self.user_context.avatar = avatar

        # Update user labels in the sidebar
        if hasattr(self.ui, 'user_name_label'):
            self.ui.user_name_label.setText(user_full_name)
        if hasattr(self.ui, 'user_position_label'):
            self.ui.user_position_label.setText(user_role_fa)
        if hasattr(self.ui, 'large_user_pic'):
            self.ui.large_user_pic.setPixmap(QPixmap(avatar) if avatar else QPixmap(user_icon))
            self.ui.large_user_pic.setScaledContents(True)

        print(f"UsersModel context set: {user_full_name} with role {user_role_fa}")

    def get_role_display_name(self, role):
        """Get Persian display name for role"""
        role_names = {
            'admin': 'مدیر',
            'translator': 'مترجم',
            'clerk': 'منشی',
            'accountant': 'حسابدار'
        }
        return role_names.get(role, 'کاربر')

    def show_users_page(self):
        """Show user management page based on role"""
        if not self.current_role:
            # If no role is set, show login window
            self.show_login_window()
            return

        if self.current_role == "admin":
            self.show_admin_page()
        else:
            # All users can _view their own profile
            self.show_user_page()

    def show_user_page(self):
        """Show user profile page"""
        from modules.RBAC import UsersTabbedWidget
        if not hasattr(self, 'user_page'):
            self.user_page = UsersTabbedWidget(self.ui.stackedWidget, self.user_context)
            self.user_page.logout_requested.connect(self.logout)
            # DEFERRED ADDITION — safe time to add is after layout
            QTimer.singleShot(0, lambda: self.ui.stackedWidget.addWidget(self.user_page))

            if hasattr(self, 'login_window') and self.login_window:
                self.login_window.hide()

        # DEFERRED PAGE SWITCH
        QTimer.singleShot(0, lambda: self.ui.stackedWidget.setCurrentWidget(self.user_page))

    def show_admin_page(self):
        """Show admin panel page"""
        if not hasattr(self, 'admin_page'):
            from modules.RBAC import TabbedAdminPanel
            self.admin_page = TabbedAdminPanel(self.ui.stackedWidget, self.user_context)
            self.admin_page.logout_requested.connect(self.logout)
            # DEFERRED ADDITION — safe time to add is after layout
            QTimer.singleShot(0, lambda: self.ui.stackedWidget.addWidget(self.admin_page))

            if hasattr(self, 'login_window') and self.login_window:
                self.login_window.hide()

        # DEFERRED PAGE SWITCH
        QTimer.singleShot(0, lambda: self.ui.stackedWidget.setCurrentWidget(self.admin_page))

    def show_login_window(self):
        """Show the login window and handle re-initialization after successful login"""
        try:
            # Hide the main window instead of closing it
            self.hide()

            # If login window doesn't exist or was closed, create a new one
            if not hasattr(self, 'login_window') or not self.login_window:
                from modules.Login.login_window import LoginWidget
                self.login_window = LoginWidget()
                # Connect to handle successful login
                self.login_window.login_successful.connect(self.on_login_successful)

            # Show the login window
            self.login_window.show()
            self.login_window.raise_()
            self.login_window.activateWindow()

        except Exception as e:
            print(f"Error showing login window: {e}")

    def get_user_info(self, username):
        """Fetch full name of the user from user_profiles table"""
        try:
            with sqlite3.connect(users_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT full_name, role_fa, avatar_path
                    FROM user_profiles
                    WHERE username = ?
                """, (username,))
                result = cursor.fetchone()
                if result:
                    return result[0], result[1], result[2]  # full_name, role_fa, avatar_path
        except Exception as e:
            print(f"Error getting full name: {e}")
            return ""

    def on_login_successful(self, username, role):
        """Handle successful login"""
        try:
            full_name, role_fa, avatar_path = self.get_user_info(username)
            self.current_user = username
            self.current_role = role

            self.user_context = UserContext(username=username,
                                            full_name=full_name,
                                            role=role,
                                            role_fa=role_fa,
                                            avatar=avatar_path)

            print(f"UsersModel {username} ({full_name}) logged in with role: {role}")

            # IMPORTANT: Update application_manager state too
            if self.app_manager:
                self.app_manager.current_user = username
                self.app_manager.current_role = role
                self.app_manager.current_user_fullname = full_name
                self.app_manager.current_user_role_fa = role_fa
                self.app_manager.user_context = self.user_context

            self.set_user_context(full_name, role_fa, avatar_path)

            if self.login_window:
                self.login_window.hide()

            old_geometry = self.geometry()

            new_main_window = self.__class__(self.user_context)
            new_main_window.setGeometry(old_geometry)
            new_main_window.show()
            from databases.postgres_users import log_user_login
            log_user_login(username, status='success')

        except Exception as e:
            title = "خطا در ورود"
            message = ("خطا پس از ورود به برنامه:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)

    def clear_remember_settings(self):
        """Clear saved remember me settings"""
        try:
            settings_path = return_resource("databases", "login_settings.json")
            if os.path.exists(settings_path):
                os.remove(settings_path)
        except Exception as e:
            print(f"Error clearing remember settings: {e}")

    def invalidate_user_token(self, username):
        """Invalidate the user's remember token in the database"""
        try:
            with sqlite3.connect(users_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET token_hash = NULL, expires_at = NULL 
                    WHERE username = ?
                """, (username,))
                conn.commit()
        except Exception as e:
            print(f"Error invalidating user token: {e}")

    def show_exit_dialog(self):
        """Show the exit confirmation dialog with logout option."""
        exit_dialog = ExitDialog(self)

        # Add logout option to exit dialog if it supports it
        if hasattr(exit_dialog, 'add_logout_option'):
            exit_dialog.add_logout_option()

        result = exit_dialog.exec()

        # Handle logout if supported
        if hasattr(exit_dialog, 'logout_requested') and exit_dialog.logout_requested:
            self.logout()

    def logout(self):
        """Handle user logout"""
        try:
            from databases.postgres_users import log_user_logout
            log_user_logout(self.current_user)

            # Invalidate token in database (optional but more secure)
            if self.current_user:
                self.invalidate_user_token(self.current_user)

            # Clear the remember me settings
            self.clear_remember_settings()

            # Clear current user context in Main_Window
            self.current_user = None
            self.current_role = None
            self.current_user_fullname = None
            self.current_user_role_fa = None
            self.user_context = None

            # IMPORTANT: Clear application_manager state too
            if self.app_manager:
                self.app_manager.current_user = None
                self.app_manager.current_role = None
                self.app_manager.user_context = None

            # Hide the current admin panel
            if hasattr(self, 'admin_page') and self.admin_page:
                self.admin_page.close()
                self.admin_page = None

            if hasattr(self, 'user_page') and self.user_page:
                self.user_page.close()
                self.user_page = None

            # Show the login window again
            self.show_login_window()

            print("UsersModel logged out successfully")

        except Exception as e:
            print(f"Error during logout: {e}")

    def restart_application(self):
        """Restart the application to return to login"""
        import os
        import sys

        # Close current window
        self.close()

        # Restart the application
        os.execl(sys.executable, sys.executable, *sys.argv)

    def add_logout_to_menu(self):
        """Add logout option to a menu (call this during UI setup if you have a menu)"""
        # This is an example - modify based on your actual menu structure
        if hasattr(self.ui, 'menubar'):
            file_menu = self.ui.menubar.addMenu('فایل')
            logout_action = file_menu.addAction('خروج از حساب کاربری')
            logout_action.triggered.connect(self.logout)

    # Keep all your existing methods below this point
    def animate_user_frame(self, frame: QFrame, expand: bool):
        target_size = 250 if expand else 100

        self.user_frame_animation = QPropertyAnimation(frame, b"maximumSize")
        self.user_frame_animation.setDuration(350)
        self.user_frame_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.user_frame_animation.setStartValue(frame.maximumSize())
        self.user_frame_animation.setEndValue(QSize(target_size, target_size))
        self.user_frame_animation.start()

    def hide_menu_labels(self):
        """Hide the labels on collapse menu."""
        self.ui.user_name_label.hide()
        self.ui.user_position_label.hide()
        self.ui.home_text_button.hide()
        self.ui.invoice_text_button.hide()
        self.ui.documents_text__button.hide()
        self.ui.issued_invoices_text_button.hide()
        self.ui.reports_text_button.hide()
        self.ui.help_text_button.hide()
        self.ui.settings_text_button.hide()

    def show_menu_labels(self):
        """Show the labels on expand menu."""
        self.ui.user_name_label.show()
        self.ui.user_position_label.show()
        self.ui.home_text_button.show()
        self.ui.invoice_text_button.show()
        self.ui.documents_text__button.show()
        self.ui.issued_invoices_text_button.show()
        self.ui.reports_text_button.show()
        self.ui.help_text_button.show()
        self.ui.settings_text_button.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.ui.titlebar_widget.underMouse():
            self.pressed = True
            self.start_pos = event.globalPosition().toPoint()
            self.window_pos = self.pos()

    def mouseMoveEvent(self, event):
        if self.pressed:
            if self.isMaximized():  # If maximized, restore before moving
                self.showNormal()
                self.move(event.globalPosition().toPoint() - self.start_pos)
                self.is_maximized = False
            else:
                delta = event.globalPosition().toPoint() - self.start_pos
                self.move(self.window_pos + delta)

    def mouseReleaseEvent(self, event):
        self.pressed = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.ui.titlebar_widget.underMouse():
            if self.isMaximized():
                self.showNormal()
                self.is_maximized = False
            else:
                self.showMaximized()
                self.is_maximized = True

    def eventFilter(self, obj, event):
        if obj == self.ui.frame:
            if event.type() == event.Type.Enter:
                self.expand_menu()
                self.show_menu_labels()

            elif event.type() == event.Type.Leave:
                self.collapse_menu()

                def hide_labels_after_animation():
                    self.hide_menu_labels()
                    try:
                        self.animation.finished.disconnect(hide_labels_after_animation)
                    except TypeError:
                        pass

                self.animation.finished.connect(hide_labels_after_animation)

            # Don't filter out the event — just react to it
            return False

        return super().eventFilter(obj, event)

    def expand_menu(self):
        """Expand the menu with animation and show text."""
        self.animation.stop()
        self.animation.setStartValue(self.ui.frame.width())
        self.animation.setEndValue(self.expanded_width)

        # Temporarily allow expansion
        self.ui.frame.setMaximumWidth(self.expanded_width)
        self.ui.frame.setMinimumWidth(self.expanded_width)

        self.animation.start()

    def collapse_menu(self):
        """Collapse the menu with animation and hide text."""
        self.animation.stop()
        self.animation.setStartValue(self.ui.frame.width())
        self.animation.setEndValue(self.collapsed_width)

        # Delay fixing the max width until after animation
        def on_animation_finished():
            self.ui.frame.setMaximumWidth(self.collapsed_width)
            self.ui.frame.setMinimumWidth(self.collapsed_width)
            try:
                self.animation.finished.disconnect(on_animation_finished)
            except TypeError:
                pass

        self.animation.finished.connect(on_animation_finished)
        self.animation.start()

    def smooth_minimize(self):
        """Fade out before minimizing the window."""
        self.minimize_animation = QPropertyAnimation(self, b"windowOpacity")
        self.minimize_animation.setDuration(300)  # 300ms duration
        self.minimize_animation.setStartValue(1.0)
        self.minimize_animation.setEndValue(0.0)
        self.minimize_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # After animation finishes, minimize window & restore opacity
        self.minimize_animation.finished.connect(self.minimize_and_restore)

        self.minimize_animation.start()

    def minimize_and_restore(self):
        """Minimize the window and restore opacity after animation."""
        self.showMinimized()
        self.setWindowOpacity(1.0)  # Restore full opacity immediately after minimizing

    def smooth_maximize(self):
        """Animate the transition between maximized and normal states."""
        screen_geometry = self.screen().availableGeometry()

        if self.isMaximized():
            if self.normal_geometry is None:
                self.normal_geometry = self.geometry()  # Set default normal geometry
            target_geometry = self.normal_geometry
        else:
            self.normal_geometry = self.geometry()  # Save current size before maximizing
            target_geometry = screen_geometry

        # Create animation
        self.max_animation = QPropertyAnimation(self, b"geometry")
        self.max_animation.setDuration(400)  # 400ms duration
        self.max_animation.setStartValue(self.geometry())
        self.max_animation.setEndValue(target_geometry)
        self.max_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Ensure the correct maximize/restore state is applied after animation
        self.max_animation.finished.connect(lambda: self.set_maximized_state())

        self.max_animation.start()

    def set_maximized_state(self):
        """Ensure proper window state after animation ends."""
        if self.geometry() == self.screen().availableGeometry():
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        else:
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMaximized)

    def set_icons(self):
        """changes current button icons to generated svg icons."""
        self.ui.minimize_button.setIcon(QIcon(minimize_icon))
        self.ui.maximize_button.setIcon(QIcon(maximize_icon))
        self.ui.x_button.setIcon(QIcon(close_icon))

        base_color = QApplication.instance().palette().color(QPalette.Highlight).name()

        set_svg_icon(user_icon, QSize(65, 65), self.ui.large_user_pic)

        home_pixmap = render_colored_svg(home_icon, QSize(45, 45), base_color)
        self.ui.home_button.setIcon(QIcon(home_pixmap))
        self.ui.home_button.setIconSize(QSize(45, 45))

        invoice_pixmap = render_colored_svg(invoice_icon, QSize(45, 45), base_color)
        self.ui.invoice_button.setIcon(QIcon(invoice_pixmap))
        self.ui.invoice_button.setIconSize(QSize(45, 45))

        documents_pixmap = render_colored_svg(documents_icon, QSize(45, 45), base_color)
        self.ui.documents_button.setIcon(QIcon(documents_pixmap))
        self.ui.documents_button.setIconSize(QSize(45, 45))

        invoices_pixmap = render_colored_svg(invoices_icon, QSize(45, 45), base_color)
        self.ui.issued_invoices_button.setIcon(QIcon(invoices_pixmap))
        self.ui.issued_invoices_button.setIconSize(QSize(45, 45))

        help_pixmap = render_colored_svg(help_icon, QSize(45, 45), base_color)
        self.ui.help_button.setIcon(QIcon(help_pixmap))
        self.ui.help_button.setIconSize(QSize(45, 45))

        settings_pixmap = render_colored_svg(settings_icon, QSize(45, 45), base_color)
        self.ui.settings_button.setIcon(QIcon(settings_pixmap))
        self.ui.settings_button.setIconSize(QSize(45, 45))
