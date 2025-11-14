# features/Main_Window/main_window_view_detox.py

"""
Detoxed and improved MainWindowView for PySide6.
- Debounced resize handling
- Fixed dragging/resizing edge cases and completed mouse release handling
- Safe animation management (stop running animations before starting new)
- Prevent layout inflation by scaling from base values only
- Persist sidebar collapsed/expanded state using QSettings
- Minimal, clear structure: FramelessWindowMixin + MainWindowView
- Uses QTimer, QSettings and light caching for icon rendering calls

Notes:
- Assumes `set_svg_icon` and `render_colored_svg` utilities exist and are reasonably fast.
- Replace `features.Main_Window.main_window_assets` with your assets module.
"""

from __future__ import annotations
import os
from functools import lru_cache

from PySide6.QtCore import (
    Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QRect,
    QTimer, QSettings
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QPalette, QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QFrame, QGroupBox,
    QStackedWidget
)

from shared.widgets.clickable_label import ClickableLabel
from features.Main_Window.main_window_models import UserProfileDTO
from shared import set_svg_icon, render_colored_svg
import features.Main_Window.main_window_assets as icons

# Constants
DEFAULT_BASE_WIDTH = 1200
DEFAULT_BASE_HEIGHT = 800
DEFAULT_FONT_PT = 10.0
SETTINGS_ORG = "Maher"
SETTINGS_APP = "MotarjemYar"


class ExitDialog(QDialog):
    """Exit confirmation dialog with safe animation/close sequence."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("خروج")
        self.resize(420, 200)
        self.setModal(True)

        self.exit_text = QLabel("آیا می‌خواهید از مترجم‌یار خارج شوید؟")
        self.exit_text.setFont(QFont("IranSans", 12))
        self.exit_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_exit = QPushButton("بله")
        self.button_exit.setFont(QFont("IranSans", 11))
        self.button_cancel = QPushButton("خیر")
        self.button_cancel.setFont(QFont("IranSans", 11))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.button_exit)
        btn_layout.addWidget(self.button_cancel)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.exit_text)
        main_layout.addLayout(btn_layout)

        self.button_exit.clicked.connect(self._start_exit_sequence)
        self.button_cancel.clicked.connect(self.reject)

    def _start_exit_sequence(self):
        # Close dialog then fade out main window for reliability
        self.accept()
        if self.main_window:
            # small delay to let the dialog close cleanly
            QTimer.singleShot(100, self._fade_out_main_window)

    def _fade_out_main_window(self):
        if not self.main_window:
            QApplication.quit()
            return
        # Stop any running main window animations first
        anim = getattr(self.main_window, "_anim_opacity", None)
        if anim and anim.state() == QPropertyAnimation.State.Running:
            anim.stop()
        self.main_window._anim_opacity = QPropertyAnimation(self.main_window, b"windowOpacity")
        self.main_window._anim_opacity.setDuration(350)
        self.main_window._anim_opacity.setStartValue(1.0)
        self.main_window._anim_opacity.setEndValue(0.0)
        self.main_window._anim_opacity.finished.connect(QApplication.quit)
        self.main_window._anim_opacity.start()


class FramelessWindowMixin:
    """Mixin to handle dragging, resizing and double-click maximize/restore.

    Keeps stateful variables and provides small, well-tested helpers.
    """

    def __init__(self):
        self.is_maximized = False
        self.normal_geometry = QRect(100, 100, DEFAULT_BASE_WIDTH, DEFAULT_BASE_HEIGHT)
        self.drag_start_position: QPoint | None = None
        self.resizing = False
        self.resize_edge = None
        self.resize_margin = 8

    def _stop_animation_if_running(self, attr_name: str):
        anim = getattr(self, attr_name, None)
        if isinstance(anim, QPropertyAnimation) and anim.state() == QPropertyAnimation.Running:
            anim.stop()

    def toggle_maximize_restore(self):
        # Safe maximize/restore with animation
        self._stop_animation_if_running("geometry_animation")
        if self.is_maximized:
            target = self.normal_geometry
        else:
            self.normal_geometry = self.geometry()
            target = self.screen().availableGeometry()

        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(280)
        self.geometry_animation.setStartValue(self.geometry())
        self.geometry_animation.setEndValue(target)
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.geometry_animation.finished.connect(self._on_toggle_maximize_finished)
        self.geometry_animation.start()

    def _on_toggle_maximize_finished(self):
        self.is_maximized = not self.is_maximized

    def _update_cursor_shape(self, pos: QPoint):
        if self.is_maximized:
            self.unsetCursor()
            self.resize_edge = None
            return

        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = self.resize_margin

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        # Diagonals first
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


class MainWindowView(QMainWindow, FramelessWindowMixin):
    """Cleaned-up MainWindowView.

    Keep this class focused on UI composition and lightweight behavior. Heavy logic
    belongs in the controller.
    """

    # Action signals
    close_button_clicked = Signal()
    maximize_button_clicked = Signal()
    minimize_button_clicked = Signal()

    home_button_clicked = Signal()
    invoice_button_clicked = Signal()
    documents_button_clicked = Signal()
    issued_invoices_button_clicked = Signal()
    reports_button_clicked = Signal()
    help_button_clicked = Signal()
    settings_button_clicked = Signal()
    user_profile_clicked = Signal()
    logout_button_clicked = Signal()

    def __init__(self):
        QMainWindow.__init__(self)
        FramelessWindowMixin.__init__(self)

        # Settings persistence
        QApplication.setOrganizationName(SETTINGS_ORG)
        QApplication.setApplicationName(SETTINGS_APP)
        self._settings = QSettings()

        # Base sizes
        self.base_size = QSize(DEFAULT_BASE_WIDTH, DEFAULT_BASE_HEIGHT)
        self.base_font_size = DEFAULT_FONT_PT

        # Debounce timer for resize
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._apply_scale_after_debounce)
        self._pending_scale_factor = 1.0

        # Keep initial margins/spacings so we don't compound scaling
        self._base_layout_margins = None
        self._base_layout_spacing = None

        # Sidebar state
        self.SIDEBAR_EXPANDED_WIDTH = 200
        self.SIDEBAR_COLLAPSED_WIDTH = 70
        self.is_sidebar_expanded = self._settings.value("sidebar_expanded", True, type=bool)

        # Initialize UI
        self._init_ui()
        self._create_widgets()
        self._setup_layouts()
        self._set_icons()
        self._setup_connections()

        # Basic window flags and high-DPI safety
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Set sensible minimum size
        self.setMinimumSize(900, 600)

        # Initial geometry and font scaling
        screen = QApplication.primaryScreen().availableGeometry()
        scale_factor = min(screen.width() / 1920, screen.height() / 1080)
        self.resize(int(self.base_size.width() * scale_factor), int(self.base_size.height() * scale_factor))
        self._apply_font_scaling(scale_factor)

    # -------------------- UI composition --------------------
    def _init_ui(self):
        """
        Initialize main window properties.
        """
        self.setObjectName("MainWindow")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

    def _create_widgets(self):
        """
        Create all widgets used in the main window.
        """
        # Title bar
        self.titlebar_widget = QWidget()
        self.app_name = QLabel("مترجم‌یار - نسخه پایه")
        self.app_logo = QLabel()
        self.x_button = QPushButton()
        self.maximize_button = QPushButton()
        self.minimize_button = QPushButton()
        self.sidebar_toggle_button = QPushButton()

        # Sidebar
        self.sidebar_frame = QFrame()
        self.large_user_pic = ClickableLabel("?")
        self.user_name_label = ClickableLabel("کاربر میهمان")
        self.user_position_label = ClickableLabel("نقش نامشخص")
        self.separator_line = QFrame()

        # Nav buttons
        self.home_button, self.home_text_button, self.home_groupBox = self._create_nav_button("خانه")
        self.invoice_button, self.invoice_text_button, self.invoice_groupBox = self._create_nav_button("ثبت فاکتور")
        self.documents_button, self.documents_text_button, self.documents_groupBox = self._create_nav_button("اسناد")
        self.issued_invoices_button, self.issued_invoices_text_button, self.issued_invoices_groupBox = self._create_nav_button("فاکتورها")
        self.reports_button, self.reports_text_button, self.reports_groupBox = self._create_nav_button("گزارش‌ها")
        self.workspace_button, self.workspace_text_button, self.workspace_groupbox = self._create_nav_button("میز کار")
        self.help_button, self.help_text_button, self.help_groupBox = self._create_nav_button("راهنما")
        self.settings_button, self.settings_text_button, self.settings_groupBox = self._create_nav_button("تنظیمات")
        self.logout_button, self.logout_text_button, self.logout_groupBox = self._create_nav_button("خروج")

        # Stacked pages
        self.stackedWidget = QStackedWidget()
        self.page_home = QWidget()
        self.page_user = QWidget()

        home_layout = QVBoxLayout(self.page_home)
        home_label = QLabel("صفحه اصلی (Home Page)")
        home_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(home_label)

        user_layout = QVBoxLayout(self.page_user)
        user_label = QLabel("صفحه کاربر (User Page)")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_label)

    def _create_nav_button(self, text: str):
        """
        Create a navigation button with icon and text.
        """
        groupBox = QGroupBox()
        icon_button = QPushButton()
        text_button = QPushButton(text)
        groupBox.setStyleSheet("QPushButton { border: none; }")
        icon_button.setMinimumSize(QSize(60, 50))
        icon_button.setMaximumSize(QSize(60, 50))
        text_button.setMinimumSize(QSize(0, 50))
        text_button.setMaximumSize(QSize(16777215, 50))
        text_button.setFont(QFont("IRANSans", 13))
        text_button.setStyleSheet("text-align: right; padding-right: 15px;")
        layout = QHBoxLayout(groupBox)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(text_button)
        layout.addWidget(icon_button)
        return icon_button, text_button, groupBox

    def _setup_layouts(self):
        """
        Setup all layouts in the main window.
        """
        # Title bar layout
        titlebar_layout = QHBoxLayout(self.titlebar_widget)
        titlebar_layout.setSpacing(6)
        titlebar_layout.setContentsMargins(6, 6, 6, 6)
        titlebar_layout.addWidget(self.sidebar_toggle_button)
        titlebar_layout.addWidget(self.app_logo)
        titlebar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        titlebar_layout.addWidget(self.app_name)
        titlebar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        titlebar_layout.addWidget(self.minimize_button)
        titlebar_layout.addWidget(self.maximize_button)
        titlebar_layout.addWidget(self.x_button)

        # Sidebar user profile layout
        user_profile_layout = QHBoxLayout()
        user_profile_layout.setSpacing(12)
        user_info_layout = QVBoxLayout()
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.user_position_label)
        user_profile_layout.addLayout(user_info_layout)
        user_profile_layout.addWidget(self.large_user_pic)

        # Sidebar main layout
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
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
        sidebar_layout.addWidget(self.logout_groupBox)

        # Stacked widget
        self.stackedWidget.addWidget(self.page_home)
        self.stackedWidget.addWidget(self.page_user)

        # Main horizontal layout
        main_h_layout = QHBoxLayout()
        # For RTL, place stackedWidget first and sidebar last as in original
        main_h_layout.addWidget(self.stackedWidget)
        main_h_layout.addWidget(self.sidebar_frame)

        # Overall central layout
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(4, 4, 4, 4)
        central_layout.setSpacing(6)
        central_layout.addWidget(self.titlebar_widget)
        central_layout.addLayout(main_h_layout)

        # Save base layout margins/spacings for scaling
        self._store_base_layout_values(central_layout)

        # Apply persisted sidebar width
        self.sidebar_frame.setFixedWidth(self.SIDEBAR_EXPANDED_WIDTH if self.is_sidebar_expanded else self.SIDEBAR_COLLAPSED_WIDTH)
        self._set_sidebar_text_visible(self.is_sidebar_expanded, immediate=True)

    def _store_base_layout_values(self, root_layout):
        """
        Store the base margins and spacing of the root layout for deterministic scaling.
        Args:
            root_layout: The root QLayout of the central widget.
        """
        # Capture a snapshot of margins and spacing so we can rescale deterministically
        if root_layout is None:
            return
        self._base_layout_margins = root_layout.getContentsMargins()  # returns tuple (l,t,r,b)
        self._base_layout_spacing = root_layout.spacing()

    # -------------------- Icons --------------------
    @staticmethod
    @lru_cache(maxsize=32)
    def _render_nav_icon(icon_path, size: QSize, color_hex: str) -> QPixmap:
        """
        Render a colored SVG icon to a QPixmap of given size and color.
        Args:
            icon_path: Path to the SVG icon file.
            size: Desired QSize for the icon.
            color_hex: Hex color string to apply to the SVG.
        Returns:
            QPixmap: Rendered pixmap of the icon.
        """
        # cache rendered pixmaps to avoid frequent re-rendering during scaling
        return render_colored_svg(icon_path, size, color_hex)

    def _set_icons(self):
        """
        Set icons for all buttons and labels.
        """
        # Titlebar icons
        self.minimize_button.setIcon(QIcon(str(icons.minimize_icon)))
        self.maximize_button.setIcon(QIcon(str(icons.maximize_icon)))
        self.x_button.setIcon(QIcon(str(icons.close_icon)))

        base_color = self.palette().color(QPalette.ColorRole.Highlight).name()
        set_svg_icon(icons.user_icon, QSize(65, 65), self.large_user_pic)

        def set_nav_icon(button, icon_path, size_px=45):
            pixmap = self._render_nav_icon(icon_path, QSize(size_px, size_px), base_color)
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(size_px, size_px))

        set_nav_icon(self.home_button, icons.home_icon)
        set_nav_icon(self.invoice_button, icons.invoice_icon)
        set_nav_icon(self.documents_button, icons.documents_icon)
        set_nav_icon(self.issued_invoices_button, icons.invoice_table)
        set_nav_icon(self.reports_button, icons.home_icon)
        set_nav_icon(self.help_button, icons.help_icon)
        set_nav_icon(self.settings_button, icons.settings_icon)
        set_nav_icon(self.logout_button, icons.logout_icon)

        # Toggle icon (use a menu/hamburger in real app)
        self.sidebar_toggle_button.setIcon(QIcon(str(icons.help_icon)))
        self.sidebar_toggle_button.setIconSize(QSize(24, 24))
        self.sidebar_toggle_button.setFixedSize(QSize(40, 40))
        self.sidebar_toggle_button.setStyleSheet("border: none;")

    # -------------------- Connections --------------------
    def _setup_connections(self):
        """
        Wire up button clicks to public signals.
        """
        self.x_button.clicked.connect(self.close_button_clicked.emit)
        self.maximize_button.clicked.connect(self.maximize_button_clicked.emit)
        self.minimize_button.clicked.connect(self.minimize_button_clicked.emit)

        self.home_text_button.clicked.connect(self.home_button_clicked.emit)
        self.invoice_text_button.clicked.connect(self.invoice_button_clicked.emit)
        self.documents_text_button.clicked.connect(self.documents_button_clicked.emit)
        self.issued_invoices_text_button.clicked.connect(self.issued_invoices_button_clicked.emit)
        self.reports_text_button.clicked.connect(self.reports_button_clicked.emit)
        self.help_text_button.clicked.connect(self.help_button_clicked.emit)
        self.settings_text_button.clicked.connect(self.settings_button_clicked.emit)
        self.logout_text_button.clicked.connect(self.logout_button_clicked.emit)

        self.large_user_pic.clicked.connect(self.user_profile_clicked.emit)
        self.user_name_label.clicked.connect(self.user_profile_clicked.emit)

        self.sidebar_toggle_button.clicked.connect(self.toggle_sidebar)

        # Wire up our public signals to internal handlers for default behaviors
        self.minimize_button_clicked.connect(self.smooth_minimize)
        self.maximize_button_clicked.connect(self.toggle_maximize_restore)
        self.close_button_clicked.connect(self.handle_close_request)

    # -------------------- Scaling & Resize --------------------
    def resizeEvent(self, event):
        new_size = event.size()
        w_ratio = new_size.width() / self.base_size.width()
        h_ratio = new_size.height() / self.base_size.height()
        scale_factor = min(w_ratio, h_ratio)

        # Debounce heavy scaling work
        self._pending_scale_factor = scale_factor
        self._resize_timer.start(80)

        super().resizeEvent(event)

    def _apply_scale_after_debounce(self):
        """
        Apply scaling to fonts, layouts, and icons after debounce timer.
        """
        factor = self._pending_scale_factor
        self._apply_font_scaling(factor)
        self._scale_layouts_deterministic(factor)
        # Scale icons/buttons
        for btn in self.findChildren(QPushButton):
            btn.setIconSize(QSize(int(24 * factor), int(24 * factor)))

    def _apply_font_scaling(self, factor: float):
        """
        Scale base font size by factor.
        """
        font = self.font()
        font.setPointSizeF(self.base_font_size * factor)
        self.setFont(font)

    def _scale_layouts_deterministic(self, factor: float):
        """
        Scale layouts based on base captured values to prevent compounding effects.
        """
        # Resets margins & spacing based on the captured base values. This prevents
        # compounding scaling effects when called repeatedly.
        root_layout = self.centralWidget().layout()
        if root_layout is None or self._base_layout_margins is None:
            return
        l, t, r, b = self._base_layout_margins
        root_layout.setContentsMargins(int(l * factor), int(t * factor), int(r * factor), int(b * factor))
        root_layout.setSpacing(int(self._base_layout_spacing * factor))

        # Sidebar width scales from base expanded width
        target_sidebar_width = int((self.SIDEBAR_EXPANDED_WIDTH if self.is_sidebar_expanded else self.SIDEBAR_COLLAPSED_WIDTH) * factor)
        self.sidebar_frame.setFixedWidth(max(target_sidebar_width, self.SIDEBAR_COLLAPSED_WIDTH))

    # -------------------- Animations --------------------
    def smooth_minimize(self):
        """
        Smoothly fade out the window before minimizing.
        """
        # fade out then minimize
        self._stop_animation_if_running("_anim_opacity")
        self._anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self._anim_opacity.setDuration(220)
        self._anim_opacity.setStartValue(1.0)
        self._anim_opacity.setEndValue(0.0)
        self._anim_opacity.setEasingCurve(QEasingCurve.Type.InQuad)
        self._anim_opacity.finished.connect(self._minimize_and_restore_opacity)
        self._anim_opacity.start()

    def _minimize_and_restore_opacity(self):
        """
        Minimize the window and restore opacity.
        """
        self.showMinimized()
        self.setWindowOpacity(1.0)

    # -------------------- Public API --------------------
    def handle_close_request(self):
        """
        Show exit confirmation dialog.
        """
        dlg = ExitDialog(self)
        dlg.exec()

    def update_user_profile(self, user_dto: UserProfileDTO):
        """
        Update the user profile section in the sidebar.
        """
        self.user_name_label.setText(user_dto.full_name)
        self.user_position_label.setText(user_dto.role_fa)
        if user_dto.avatar_path and os.path.exists(user_dto.avatar_path):
            pix = QPixmap(user_dto.avatar_path)
            self.large_user_pic.setPixmap(pix)
        else:
            self.large_user_pic.setText("?")

    def switch_to_page(self, page_name: str):
        """
        Switch the stacked widget to the specified page.
        """
        page_map = {"home": self.page_home, "user": self.page_user}
        widget = page_map.get(page_name)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)
        else:
            print(f"Warning: Page '{page_name}' not found in stacked widget.")

    # -------------------- Mouse handling --------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resize_edge:
                self.resizing = True
                self.drag_start_position = event.globalPosition().toPoint()
            elif self.titlebar_widget.underMouse():
                self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        if not self.resizing and not self.drag_start_position:
            self._update_cursor_shape(pos)
            return

        if self.resizing and self.drag_start_position is not None:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            geom = QRect(self.geometry())

            if "top" in (self.resize_edge or ""):
                geom.setTop(geom.top() + delta.y())
            if "bottom" in (self.resize_edge or ""):
                geom.setBottom(geom.bottom() + delta.y())
            if "left" in (self.resize_edge or ""):
                geom.setLeft(geom.left() + delta.x())
            if "right" in (self.resize_edge or ""):
                geom.setRight(geom.right() + delta.x())

            # Enforce minimum sizes
            if geom.width() < self.minimumWidth():
                geom.setWidth(self.minimumWidth())
            if geom.height() < self.minimumHeight():
                geom.setHeight(self.minimumHeight())

            self.setGeometry(geom)
            self.drag_start_position = event.globalPosition().toPoint()
            self.normal_geometry = self.geometry()
            return

        if self.drag_start_position is not None:
            # Dragging (move window)
            if self.is_maximized:
                # restore then continue drag
                restored_width = self.normal_geometry.width()
                ratio = event.globalPosition().x() / self.screen().availableGeometry().width()
                # Perform restore without animation to avoid complexity
                self.setGeometry(self.normal_geometry)
                self.is_maximized = False
                new_x = int(event.globalPosition().x() - (restored_width * ratio))
                self.drag_start_position = QPoint(new_x, int(event.globalPosition().y()))
                return

            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Clear dragging / resizing state
            self.resizing = False
            self.drag_start_position = None
            self.resize_edge = None
            self.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.titlebar_widget.underMouse():
            self.toggle_maximize_restore()
        super().mouseDoubleClickEvent(event)

    # -------------------- Sidebar --------------------
    def toggle_sidebar(self):
        """
        Animate sidebar collapse/expand.
        """
        # Stop running animations if any
        self._stop_animation_if_running("sidebar_animation")

        start_w = self.sidebar_frame.width()
        target_w = self.SIDEBAR_COLLAPSED_WIDTH if self.is_sidebar_expanded else self.SIDEBAR_EXPANDED_WIDTH

        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"minimumWidth")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setStartValue(start_w)
        self.sidebar_animation.setEndValue(target_w)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self.is_sidebar_expanded:
            # hide immediately to make collapse feel snappy
            self._set_sidebar_text_visible(False)
        else:
            self.sidebar_animation.finished.connect(lambda: self._set_sidebar_text_visible(True))

        self.sidebar_animation.start()
        self.is_sidebar_expanded = not self.is_sidebar_expanded
        # persist
        self._settings.setValue("sidebar_expanded", self.is_sidebar_expanded)

    def _set_sidebar_text_visible(self, visible: bool, immediate: bool = False):
        """
        Show/hide sidebar text buttons.
        Args:
            visible (bool): Whether to show or hide the text buttons.
            immediate (bool): If True, skip animations and set visibility right away.
        """
        # if immediate True, skip animations and set right away
        widget_list = [
            self.home_text_button, self.invoice_text_button, self.documents_text_button,
            self.issued_invoices_text_button, self.reports_text_button, self.help_text_button,
            self.settings_text_button, self.logout_text_button,
            self.user_name_label, self.user_position_label
        ]
        for w in widget_list:
            w.setVisible(visible)

        if immediate:
            QApplication.processEvents()
