# features/Main_Window/main_window_view.py

import os
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PySide6.QtGui import QPixmap, QFont, QIcon, QPalette, QMouseEvent
from PySide6.QtWidgets import (QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QSpacerItem, QSizePolicy, QFrame, QGroupBox, QStackedWidget)
from shared.widgets.clickable_label import ClickableLabel
from features.Main_Window.main_window_models import UserProfileDTO
from shared import set_svg_icon, render_colored_svg
import features.Main_Window.main_window_assets as icons


class ExitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # Store a reference to the main window for animation
        self.setWindowTitle("خروج")
        self.resize(400, 200)
        self.setModal(True)  # Block interaction with the main window

        # Widgets
        self.exit_text = QLabel("آیا می‌خواهید از مترجم‌یار خارج شوید؟")
        self.exit_text.setFont(QFont("IranSans", 12))
        self.exit_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_exit = QPushButton("بله")
        self.button_exit.setFont(QFont("IranSans", 11))
        self.button_cancel = QPushButton("خیر")
        self.button_cancel.setFont(QFont("IranSans", 11))

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_exit)
        button_layout.addWidget(self.button_cancel)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.exit_text)
        main_layout.addLayout(button_layout)

        # Connections
        self.button_exit.clicked.connect(self._start_exit_sequence)
        self.button_cancel.clicked.connect(self.reject)  # QDialog's built-in reject slot

    def _start_exit_sequence(self):
        """Animate this dialog out, then the main window, then quit."""
        # Animate this dialog (self)
        self.anim_dialog = QPropertyAnimation(self, b"windowOpacity")
        self.anim_dialog.setDuration(300)
        self.anim_dialog.setStartValue(1.0)
        self.anim_dialog.setEndValue(0.0)
        self.anim_dialog.finished.connect(self._fade_out_main_window)
        self.anim_dialog.start()

    def _fade_out_main_window(self):
        """Animate the main window out after this dialog is gone."""
        self.anim_main = QPropertyAnimation(self.main_window, b"windowOpacity")
        self.anim_main.setDuration(500)
        self.anim_main.setStartValue(1.0)
        self.anim_main.setEndValue(0.0)
        self.anim_main.finished.connect(QApplication.quit)
        self.anim_main.start()


class MainWindowView(QMainWindow):
    """
    The main application window (View).
    - It is "dumb" and only knows how to display data and emit signals on user actions.
    - It is initialized and shown by the main application entry point.
    - A Controller will connect to its signals to add _logic.
    """
    # --- Action Signals ---
    # Signals the _view emits for the controller to listen to.
    # Title Bar
    close_button_clicked = Signal()
    maximize_button_clicked = Signal()
    minimize_button_clicked = Signal()

    # Sidebar Navigation
    home_button_clicked = Signal()
    invoice_button_clicked = Signal()
    documents_button_clicked = Signal()
    issued_invoices_button_clicked = Signal()
    reports_button_clicked = Signal()
    help_button_clicked = Signal()
    settings_button_clicked = Signal()
    user_profile_clicked = Signal()

    def __init__(self):
        super().__init__()

        # --- 1. Add State and Constants for Sidebar ---
        self.SIDEBAR_EXPANDED_WIDTH = 200
        self.SIDEBAR_COLLAPSED_WIDTH = 70  # Just enough for icons
        self.is_sidebar_expanded = True  # Start expanded by default

        # --- 1. Add State Variables for Resizing and Dragging ---
        self.DEFAULT_NORMAL_SIZE = QSize(1200, 800)
        self.is_maximized = False
        self.normal_geometry = None

        self.normal_geometry = QRect(
            (self.screen().availableGeometry().center() - QPoint(*self.DEFAULT_NORMAL_SIZE.toTuple()) / 2),
            self.DEFAULT_NORMAL_SIZE
        )

        # For dragging the window
        self.drag_start_position = None

        # For resizing the window
        self.resizing = False
        self.resize_edge = None
        self.resize_margin = 10  # The pixel margin to detect edges

        self._init_ui()
        self._create_widgets()
        self._setup_layouts()
        self._set_icons()
        self._setup_connections()

        # --- 2. Enable Mouse Tracking ---
        # This is crucial for detecting mouse position even when no button is pressed.
        self.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)
        # For child widgets if needed, though centralwidget usually covers it.
        self.titlebar_widget.setMouseTracking(True)

        self.sidebar_frame.setMinimumWidth(self.SIDEBAR_EXPANDED_WIDTH)

    # --- Public Methods (API for the Controller) ---
    def handle_close_request(self):
        """
        Called by the controller. Shows the exit confirmation dialog.
        """
        dialog = ExitDialog(self)
        dialog.exec()

    def update_user_profile(self, user_dto: UserProfileDTO):
        """

        Updates the user profile section in the sidebar with data from the DTO.
        """
        self.user_name_label.setText(user_dto.full_name)
        self.user_position_label.setText(user_dto.role_fa)

        # Example of handling an avatar image
        if user_dto.avatar_path and os.path.exists(user_dto.avatar_path):
            self.large_user_pic.setPixmap(QPixmap(user_dto.avatar_path))
        else:
            # Set a default avatar if none is provided or path is invalid
            # For now, just clearing it. You'd replace this with a default icon path.
            self.large_user_pic.setText("?")  # Placeholder

    def switch_to_page(self, page_name: str):
        """Switches the main content area to the specified page widget."""
        page_map = {
            "home": self.page_home,
            "user": self.page_user,
        }
        widget_to_show = page_map.get(page_name)
        if widget_to_show:
            self.stackedWidget.setCurrentWidget(widget_to_show)
        else:
            print(f"Warning: Page '{page_name}' not found in stacked widget.")

    # --- Internal Setup Methods ---

    def _init_ui(self):
        """Initial window setup."""
        self.setObjectName("MainWindow")
        self.resize(self.DEFAULT_NORMAL_SIZE)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

    def _create_widgets(self):
        """Create all the widgets for the window in one place."""
        self.sidebar_toggle_button = QPushButton()

        # --- Title Bar ---
        self.titlebar_widget = QWidget()
        self.app_name = QLabel("مترجم‌یار - نسخه پایه")
        self.app_logo = QLabel()
        self.x_button = QPushButton()
        self.maximize_button = QPushButton()
        self.minimize_button = QPushButton()

        # --- Sidebar ---
        self.sidebar_frame = QFrame()
        self.large_user_pic = ClickableLabel("?")
        self.user_name_label = ClickableLabel("کاربر میهمان")
        self.user_position_label = ClickableLabel("نقش نامشخص")
        self.separator_line = QFrame()

        # Navigation Buttons (using a helper for consistency)
        self.home_button, self.home_text_button, self.home_groupBox = self._create_nav_button("خانه")
        self.invoice_button, self.invoice_text_button, self.invoice_groupBox = self._create_nav_button("ثبت فاکتور")
        self.documents_button, self.documents_text_button, self.documents_groupBox = self._create_nav_button("اسناد")
        self.issued_invoices_button, self.issued_invoices_text_button, self.issued_invoices_groupBox = (
            self._create_nav_button("فاکتورها"))
        self.reports_button, self.reports_text_button, self.reports_groupBox = self._create_nav_button("گزارش‌ها")
        self.workspace_button, self.workspace_text_button, self.workspace_groupbox = self._create_nav_button("میز کار")
        self.help_button, self.help_text_button, self.help_groupBox = self._create_nav_button("راهنما")
        self.settings_button, self.settings_text_button, self.settings_groupBox = self._create_nav_button("تنظیمات")

        # --- Main Content Area ---
        self.stackedWidget = QStackedWidget()
        self.page_home = QWidget()
        self.page_user = QWidget()

        # Add a label to the placeholder pages for visual feedback
        home_layout = QVBoxLayout(self.page_home)
        home_label = QLabel("صفحه اصلی (Home Page)")
        home_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(home_label)
        user_layout = QVBoxLayout(self.page_user)
        user_label = QLabel("صفحه کاربر (User Page)")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(user_label)

    def _create_nav_button(self, text: str) -> tuple[QPushButton, QPushButton, QGroupBox]:
        """Helper factory method to create a consistent navigation button group."""
        groupBox = QGroupBox()
        icon_button = QPushButton()  # Icon would be set here
        text_button = QPushButton(text)

        # Apply common styling and properties
        groupBox.setStyleSheet("QPushButton { border: none; }")
        icon_button.setMinimumSize(QSize(60, 50))
        icon_button.setMaximumSize(QSize(60, 50))
        text_button.setMinimumSize(QSize(0, 50))
        text_button.setMaximumSize(QSize(16777215, 50))
        text_button.setFont(QFont("IRANSans", 13))
        text_button.setStyleSheet("text-align: right; padding-right: 15px;")  # RTL padding

        layout = QHBoxLayout(groupBox)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(text_button)  # Text first for RTL
        layout.addWidget(icon_button)

        return icon_button, text_button, groupBox

    def _setup_layouts(self):
        """Arrange all the created widgets into layouts."""

        # --- Title Bar Layout ---
        titlebar_layout = QHBoxLayout(self.titlebar_widget)
        titlebar_layout.setSpacing(5)
        titlebar_layout.setContentsMargins(0, 0, 0, 0)
        titlebar_layout.addWidget(self.sidebar_toggle_button)
        titlebar_layout.addWidget(self.app_logo)
        titlebar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        titlebar_layout.addWidget(self.app_name)
        titlebar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        titlebar_layout.addWidget(self.minimize_button)
        titlebar_layout.addWidget(self.maximize_button)
        titlebar_layout.addWidget(self.x_button)

        # --- Sidebar User Profile Layout ---
        user_profile_layout = QHBoxLayout()
        user_profile_layout.setSpacing(15)
        user_info_layout = QVBoxLayout()
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.user_position_label)
        user_profile_layout.addLayout(user_info_layout)
        user_profile_layout.addWidget(self.large_user_pic)

        # --- Sidebar Main Layout ---
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.addLayout(user_profile_layout)
        sidebar_layout.addWidget(self.separator_line)
        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        sidebar_layout.addWidget(self.home_groupBox)
        sidebar_layout.addWidget(self.invoice_groupBox)
        sidebar_layout.addWidget(self.documents_groupBox)
        sidebar_layout.addWidget(self.issued_invoices_groupBox)
        sidebar_layout.addWidget(self.reports_groupBox)
        sidebar_layout.addWidget(self.workspace_groupbox)
        sidebar_layout.addSpacerItem(QSpacerItem(13, 108, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        sidebar_layout.addWidget(self.help_groupBox)
        sidebar_layout.addWidget(self.settings_groupBox)

        # --- Main Content Layout ---
        self.stackedWidget.addWidget(self.page_home)
        self.stackedWidget.addWidget(self.page_user)

        # --- Window Main Horizontal Layout ---
        main_h_layout = QHBoxLayout()
        main_h_layout.addWidget(self.stackedWidget)  # Main content on the left (for RTL)
        main_h_layout.addWidget(self.sidebar_frame)  # Sidebar on the right

        # --- Overall Central Widget Layout ---
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.addWidget(self.titlebar_widget)
        central_layout.addLayout(main_h_layout)

    def _set_icons(self):
        """Sets SVG icons for the relevant buttons in the UI."""
        self.minimize_button.setIcon(QIcon(icons.minimize_icon))
        self.maximize_button.setIcon(QIcon(icons.maximize_icon))
        self.x_button.setIcon(QIcon(icons.close_icon))

        # Get the theme's highlight color for active icons
        base_color = self.palette().color(QPalette.ColorRole.Highlight).name()

        # Set user avatar
        set_svg_icon(icons.user_icon, QSize(65, 65), self.large_user_pic)

        # Helper lambda to reduce repetition for nav buttons
        def set_nav_icon(button, icon_path):
            pixmap = render_colored_svg(icon_path, QSize(45, 45), base_color)
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(45, 45))

        set_nav_icon(self.home_button, icons.home_icon)
        set_nav_icon(self.invoice_button, icons.invoice_icon)
        set_nav_icon(self.documents_button, icons.documents_icon)
        set_nav_icon(self.issued_invoices_button, icons.invoice_table)
        set_nav_icon(self.reports_button, icons.home_icon)  # TODO: Add an icon for reports
        set_nav_icon(self.help_button, icons.help_icon)
        set_nav_icon(self.settings_button, icons.settings_icon)

        # --- 4. Set the Icon for the Toggle Button ---
        self.sidebar_toggle_button.setIcon(QIcon(icons.help_icon))
        self.sidebar_toggle_button.setIconSize(QSize(24, 24))
        self.sidebar_toggle_button.setFixedSize(QSize(40, 40))
        self.sidebar_toggle_button.setStyleSheet("border: none;")

    def _setup_connections(self):
        """Connect widget signals to the _view's public action signals."""
        # Title Bar
        self.x_button.clicked.connect(self.close_button_clicked.emit)
        self.maximize_button.clicked.connect(self.maximize_button_clicked.emit)
        self.minimize_button.clicked.connect(self.minimize_button_clicked.emit)

        # Sidebar Navigation (connecting the whole groupbox's button for a larger click area)
        self.home_text_button.clicked.connect(self.home_button_clicked.emit)
        self.invoice_text_button.clicked.connect(self.invoice_button_clicked.emit)
        self.documents_text_button.clicked.connect(self.documents_button_clicked.emit)
        self.issued_invoices_text_button.clicked.connect(self.issued_invoices_button_clicked.emit)
        self.reports_text_button.clicked.connect(self.reports_button_clicked.emit)
        self.help_text_button.clicked.connect(self.help_button_clicked.emit)
        self.settings_text_button.clicked.connect(self.settings_button_clicked.emit)

        # User profile clickable labels
        self.large_user_pic.clicked.connect(self.user_profile_clicked.emit)
        self.user_name_label.clicked.connect(self.user_profile_clicked.emit)

        # Toggle Sidebar
        self.sidebar_toggle_button.clicked.connect(self.toggle_sidebar)

    # --- 3. Add Custom Title Bar Methods ---

    def smooth_minimize(self):
        """Fade out before minimizing the window."""
        self.minimize_animation = QPropertyAnimation(self, b"windowOpacity")
        self.minimize_animation.setDuration(250)
        self.minimize_animation.setStartValue(1.0)
        self.minimize_animation.setEndValue(0.0)
        self.minimize_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.minimize_animation.finished.connect(self._minimize_and_restore_opacity)
        self.minimize_animation.start()

    def _minimize_and_restore_opacity(self):
        """Minimize the window and restore opacity after animation."""
        self.showMinimized()
        self.setWindowOpacity(1.0)

    def smooth_maximize(self):
        """Animate the transition between maximized and normal states."""
        if self.is_maximized:
            # RESTORE to our saved normal geometry
            target_geometry = self.normal_geometry
        else:
            # MAXIMIZE: Save current geometry and set target to screen
            self.normal_geometry = self.geometry()
            target_geometry = self.screen().availableGeometry()

        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        # Set animation duration to 300ms as requested
        self.geometry_animation.setDuration(300)
        self.geometry_animation.setStartValue(self.geometry())
        self.geometry_animation.setEndValue(target_geometry)
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.geometry_animation.finished.connect(self._update_maximize_state)
        self.geometry_animation.start()

    def _update_maximize_state(self):
        """Internal slot to update the is_maximized flag after animation."""
        self.is_maximized = not self.is_maximized
        print(f"Window is now {'maximized' if self.is_maximized else 'normal'}.")

    # --- 4. Add Mouse Event Handlers for Dragging and Double-Click ---
    def _update_cursor_shape(self, pos: QPoint):
        """Updates the cursor shape based on its position near the window edges."""
        if self.is_maximized:
            self.unsetCursor()
            self.resize_edge = None
            return

        left = pos.x() < self.resize_margin
        top = pos.y() < self.resize_margin
        right = pos.x() > self.width() - self.resize_margin
        bottom = pos.y() > self.height() - self.resize_margin

        if top and left:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self.resize_edge = "top-left"
        elif top and right:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self.resize_edge = "top-right"
        elif bottom and left:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self.resize_edge = "bottom-left"
        elif bottom and right:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self.resize_edge = "bottom-right"
        elif top:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resize_edge = "top"
        elif bottom:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resize_edge = "bottom"
        elif left:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resize_edge = "left"
        elif right:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resize_edge = "right"
        else:
            self.unsetCursor()
            self.resize_edge = None

    def mousePressEvent(self, event: QMouseEvent):
        """Initiates a drag or resize operation."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resize_edge:
                # If we are on an edge, start resizing
                self.resizing = True
                self.drag_start_position = event.globalPosition().toPoint()
            elif self.titlebar_widget.underMouse():
                # If on the title bar, start dragging
                self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handles dragging, resizing, and updating cursor shape."""
        pos = event.position().toPoint()

        if not self.resizing and not self.drag_start_position:
            # If not currently dragging or resizing, just update the cursor
            self._update_cursor_shape(pos)

        elif self.resizing:
            # --- Handle Resizing ---
            delta = event.globalPosition().toPoint() - self.drag_start_position
            geom = self.geometry()

            if "top" in self.resize_edge:
                geom.setTop(geom.top() + delta.y())
            if "bottom" in self.resize_edge:
                geom.setBottom(geom.bottom() + delta.y())
            if "left" in self.resize_edge:
                geom.setLeft(geom.left() + delta.x())
            if "right" in self.resize_edge:
                geom.setRight(geom.right() + delta.x())

            # Prevent window from becoming too small
            if geom.width() < self.minimumWidth():
                geom.setWidth(self.minimumWidth())
            if geom.height() < self.minimumHeight():
                geom.setHeight(self.minimumHeight())

            self.setGeometry(geom)
            self.drag_start_position = event.globalPosition().toPoint()
            self.normal_geometry = self.geometry()

        elif self.drag_start_position:
            # --- Handle Dragging ---
            if self.is_maximized:
                # On the first move after a click, restore the window
                restored_width = self.normal_geometry.width()

                # Calculate the ratio of the cursor's position on the title bar
                # to keep it "stuck" to the same relative spot after restoring.
                ratio = event.globalPosition().x() / self.screen().availableGeometry().width()

                # Trigger the restore animation
                self.smooth_maximize()

                # We need to re-calculate the drag start position relative to the
                # corner of the newly restored window to avoid a jump.
                new_x = int(event.globalPosition().x() - (restored_width * ratio))
                self.drag_start_position = QPoint(new_x, int(event.globalPosition().y()))
                return

            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stops dragging and resizing operations."""
        self.drag_start_position = None
        self.resizing = False
        self.resize_edge = None
        self.unsetCursor()  # Ensure cursor returns to normal
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Maximize or restore the window on double-clicking the title bar."""
        if event.button() == Qt.MouseButton.LeftButton and self.titlebar_widget.underMouse():
            self.smooth_maximize()
        super().mouseDoubleClickEvent(event)

    # --- 5. Sidebar Functionality ---
    def toggle_sidebar(self):
        """
        Toggles the sidebar between its expanded and collapsed states
        with a smooth animation.
        """
        target_width = self.SIDEBAR_COLLAPSED_WIDTH if self.is_sidebar_expanded else self.SIDEBAR_EXPANDED_WIDTH

        # Animate the width of the sidebar frame
        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"minimumWidth")
        self.sidebar_animation.setDuration(350)  # Animation duration in ms
        self.sidebar_animation.setStartValue(self.sidebar_frame.width())
        self.sidebar_animation.setEndValue(target_width)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Before the animation starts, decide which widgets to hide/show
        if self.is_sidebar_expanded:
            # If collapsing, hide text buttons immediately
            self._set_sidebar_text_visible(False)
        else:
            # If expanding, the text will be shown when the animation finishes
            self.sidebar_animation.finished.connect(lambda: self._set_sidebar_text_visible(True))

        self.sidebar_animation.start()

        # Toggle the state flag
        self.is_sidebar_expanded = not self.is_sidebar_expanded

    def _set_sidebar_text_visible(self, visible: bool):
        """
        A helper method to show or hide the text labels in the sidebar nav buttons.
        """
        self.home_text_button.setVisible(visible)
        self.invoice_text_button.setVisible(visible)
        self.documents_text_button.setVisible(visible)
        self.issued_invoices_text_button.setVisible(visible)
        self.reports_text_button.setVisible(visible)
        self.help_text_button.setVisible(visible)
        self.settings_text_button.setVisible(visible)

        # Also hide the user name/role text
        self.user_name_label.setVisible(visible)
        self.user_position_label.setVisible(visible)
