"""
Main Window View.
Pure UI component. Handles layout, widget creation, styling, and visual states.
"""

from __future__ import annotations
import os

from PySide6.QtCore import (
    Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QRect,
    QSettings
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QPalette, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy, QFrame,
    QStackedWidget, QApplication
)

from shared.widgets.clickable_label import ClickableLabel
from features.Main_Window.main_window_models import UserProfileDTO
from shared import set_svg_icon, render_colored_svg
import features.Main_Window.main_window_assets as icons

# Constants
SETTINGS_ORG = "Maher"
SETTINGS_APP = "MotarjemYar"
SIDEBAR_EXPANDED_WIDTH = 200
SIDEBAR_COLLAPSED_WIDTH = 70

# --- Stylesheet for Sidebar Items ---
SIDEBAR_STYLESHEET = """
    /* Container (QFrame) Style */
    SidebarButton {
        background-color: transparent;
        border-radius: 8px;
        margin: 2px 5px;
    }

    /* Hover Effect */
    SidebarButton:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }

    /* Active State (Current Page) - Background & Border */
    SidebarButton[active="true"] {
        background-color: #dbeafe; /* Light Blue Background */
        border-right: 4px solid #3b82f6; /* Blue Accent Border */
    }

    /* Inner Buttons (Icon & Text) - Default State */
    SidebarButton QPushButton {
        border: none;
        background: transparent;
        text-align: right;
        color: #374151; /* Gray-700 */
    }

    /* Inner Buttons - Active State (Bold & Blue Text) */
    SidebarButton[active="true"] QPushButton {
        font-weight: bold;
        color: #1d4ed8; /* Blue-700 */
    }
"""


class ExitDialog(QDialog):
    """Exit Confirmation Dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خروج")
        self.resize(420, 200)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { color: #374151; }
        """)

        self.exit_text = QLabel("آیا می‌خواهید از مترجم‌یار خارج شوید؟")
        self.exit_text.setFont(QFont("IranSans", 12))
        self.exit_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_exit = QPushButton("بله")
        self.button_exit.setFont(QFont("IranSans", 11))
        self.button_exit.setMinimumWidth(80)

        self.button_cancel = QPushButton("خیر")
        self.button_cancel.setFont(QFont("IranSans", 11))
        self.button_cancel.setMinimumWidth(80)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.button_exit)
        btn_layout.addWidget(self.button_cancel)
        btn_layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.exit_text)
        main_layout.addSpacing(20)
        main_layout.addLayout(btn_layout)
        main_layout.addSpacing(10)

        self.button_exit.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)


class SidebarButton(QFrame):
    """
    Custom Widget for Sidebar Menu Items.
    Encapsulates Icon, Text, Cursor, and Active State.
    """
    clicked = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)

        # Layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(10)

        # Text Widget
        self.text_btn = QPushButton(text)
        self.text_btn.setFont(QFont("IRANSans", 12))
        self.text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Icon Widget
        self.icon_btn = QPushButton()
        self.icon_btn.setFixedSize(30, 30)
        self.icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Add to layout (RTL Order: Text -> Icon)
        self._layout.addWidget(self.text_btn)
        self._layout.addWidget(self.icon_btn)

        # Forward clicks
        self.text_btn.clicked.connect(self.clicked.emit)
        self.icon_btn.clicked.connect(self.clicked.emit)

    def set_icon(self, icon: QIcon):
        self.icon_btn.setIcon(icon)
        self.icon_btn.setIconSize(QSize(24, 24))

    def set_text_visible(self, visible: bool):
        self.text_btn.setVisible(visible)

    def set_active(self, is_active: bool):
        """Sets the visual state for selection via Dynamic Property."""
        self.setProperty("active", is_active)
        self.style().unpolish(self)
        self.style().polish(self)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class FramelessWindowMixin:
    """Mixin to handle dragging, resizing and maximize/restore."""

    def __init__(self):
        self.is_maximized = False
        self.normal_geometry = QRect(100, 100, 1200, 800)
        self.drag_start_position: QPoint | None = None
        self.resizing = False
        self.resize_edge = None
        self.resize_margin = 8
        self.geometry_animation = None

    def toggle_maximize_restore(self):
        if self.geometry_animation and self.geometry_animation.state() == QPropertyAnimation.Running:
            self.geometry_animation.stop()

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
    # Action signals
    close_button_clicked = Signal()
    maximize_button_clicked = Signal()
    minimize_button_clicked = Signal()

    # Navigation Signals
    home_button_clicked = Signal()
    invoice_button_clicked = Signal()
    documents_button_clicked = Signal()
    issued_invoices_button_clicked = Signal()
    reports_button_clicked = Signal()
    help_button_clicked = Signal()
    settings_button_clicked = Signal()
    user_profile_clicked = Signal()
    logout_button_clicked = Signal()
    workspace_button_clicked = Signal()

    def __init__(self):
        QMainWindow.__init__(self)
        FramelessWindowMixin.__init__(self)

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.is_sidebar_expanded = self._settings.value("sidebar_expanded", True, type=bool)

        self.nav_items: dict[str, SidebarButton] = {}

        self._init_ui()
        self._create_widgets()
        self._setup_layouts()
        self._set_icons()
        self._setup_connections()

        self.setStyleSheet(SIDEBAR_STYLESHEET)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.sidebar_frame.setFixedWidth(
            SIDEBAR_EXPANDED_WIDTH if self.is_sidebar_expanded else SIDEBAR_COLLAPSED_WIDTH)
        self._set_sidebar_text_visible(self.is_sidebar_expanded, immediate=True)

    def _init_ui(self):
        self.setObjectName("MainWindow")
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet("#CentralWidget { background-color: #f3f4f6; }")
        self.setCentralWidget(self.central_widget)

    def _create_widgets(self):
        # Title bar
        self.titlebar_widget = QWidget()
        self.titlebar_widget.setFixedHeight(50)
        self.titlebar_widget.setStyleSheet("background-color: white; border-bottom: 1px solid #e5e7eb;")

        self.app_name = QLabel("مترجم‌یار - نسخه پایه")
        self.app_name.setFont(QFont("IranSans", 10, QFont.Weight.Bold))
        self.app_name.setStyleSheet("color: #374151;")

        # App Icon Label
        self.app_logo = QLabel()
        self.app_logo.setFixedSize(35, 35)
        self.app_logo.setScaledContents(True)

        # Window Controls
        self.x_button = QPushButton()
        self.maximize_button = QPushButton()
        self.minimize_button = QPushButton()

        win_ctrl_style = """
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: #e5e7eb; }
        """
        self.x_button.setStyleSheet(win_ctrl_style.replace("#e5e7eb", "#fee2e2"))
        self.maximize_button.setStyleSheet(win_ctrl_style)
        self.minimize_button.setStyleSheet(win_ctrl_style)
        self.x_button.setFixedSize(30, 30)
        self.maximize_button.setFixedSize(30, 30)
        self.minimize_button.setFixedSize(30, 30)

        # Toggle Button
        self.sidebar_toggle_button = QPushButton()
        self.sidebar_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_toggle_button.setStyleSheet("border: none; background: transparent;")

        # Sidebar Header
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("background-color: white; border-left: 1px solid #e5e7eb;")

        self.large_user_pic = ClickableLabel("?")
        self.large_user_pic.setCursor(Qt.CursorShape.PointingHandCursor)

        self.user_name_label = ClickableLabel("کاربر میهمان")
        self.user_name_label.setFont(QFont("IranSans", 10, QFont.Weight.Bold))
        self.user_name_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.user_position_label = ClickableLabel("نقش نامشخص")
        self.user_position_label.setFont(QFont("IranSans", 9))
        self.user_position_label.setStyleSheet("color: #6b7280;")

        self.separator_line = QFrame()
        self.separator_line.setFrameShape(QFrame.Shape.HLine)
        self.separator_line.setFrameShadow(QFrame.Shadow.Plain)
        self.separator_line.setStyleSheet("color: #e5e7eb;")

        # Navigation Buttons
        self.btn_home = self._create_sidebar_btn("home", "خانه")
        self.btn_invoice = self._create_sidebar_btn("invoice", "ثبت فاکتور")
        self.btn_documents = self._create_sidebar_btn("documents", "اسناد")
        self.btn_issued = self._create_sidebar_btn("issued", "فاکتورها")
        self.btn_reports = self._create_sidebar_btn("reports", "گزارش‌ها")
        self.btn_workspace = self._create_sidebar_btn("workspace", "میز کار")
        self.btn_help = self._create_sidebar_btn("help", "راهنما")
        self.btn_settings = self._create_sidebar_btn("settings", "تنظیمات")
        self.btn_logout = self._create_sidebar_btn("logout", "خروج")

        # Stacked pages
        self.stackedWidget = QStackedWidget()
        self.page_home = QWidget()
        self.page_user = QWidget()
        self.stackedWidget.addWidget(self.page_home)
        self.stackedWidget.addWidget(self.page_user)

    def _create_sidebar_btn(self, btn_id: str, text: str) -> SidebarButton:
        btn = SidebarButton(text)
        self.nav_items[btn_id] = btn
        return btn

    def _setup_layouts(self):
        # Title bar
        titlebar_layout = QHBoxLayout(self.titlebar_widget)
        titlebar_layout.setContentsMargins(10, 0, 10, 0)

        # Left Side: Logo & App Name
        titlebar_layout.addWidget(self.app_logo)
        titlebar_layout.addSpacing(10)
        titlebar_layout.addWidget(self.app_name)

        # Spacer
        titlebar_layout.addStretch()

        # Right Side: Toggle Button, then Window Controls
        titlebar_layout.addWidget(self.sidebar_toggle_button)
        titlebar_layout.addSpacing(10)  # Gap between toggle and window controls
        titlebar_layout.addWidget(self.minimize_button)
        titlebar_layout.addWidget(self.maximize_button)
        titlebar_layout.addWidget(self.x_button)

        # User Profile
        user_profile_layout = QHBoxLayout()
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.user_position_label)
        user_profile_layout.addLayout(user_info_layout)
        user_profile_layout.addWidget(self.large_user_pic)

        # Sidebar Main
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(5)

        sidebar_layout.addLayout(user_profile_layout)
        sidebar_layout.addSpacing(5)
        sidebar_layout.addWidget(self.separator_line)
        sidebar_layout.addSpacing(10)

        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_invoice)
        sidebar_layout.addWidget(self.btn_documents)
        sidebar_layout.addWidget(self.btn_issued)
        sidebar_layout.addWidget(self.btn_reports)
        sidebar_layout.addWidget(self.btn_workspace)

        sidebar_layout.addStretch()

        sidebar_layout.addWidget(self.btn_help)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addWidget(self.btn_logout)

        # Main Layout
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(0)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.addWidget(self.stackedWidget)
        main_h_layout.addWidget(self.sidebar_frame)

        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.titlebar_widget)
        central_layout.addLayout(main_h_layout)

    def _set_icons(self):
        # Window Controls
        self.minimize_button.setIcon(QIcon(str(icons.minimize_icon)))
        self.maximize_button.setIcon(QIcon(str(icons.maximize_icon)))
        self.x_button.setIcon(QIcon(str(icons.close_icon)))

        # App Icon (PNG)
        if os.path.exists(str(icons.app_icon)):
            self.app_logo.setPixmap(QPixmap(str(icons.app_icon)))

        # User Avatar Placeholder
        set_svg_icon(icons.user_icon, QSize(50, 50), self.large_user_pic)

        # Sidebar Icons
        base_color = "#3b82f6"

        def set_nav_icon(btn: SidebarButton, icon_path):
            pixmap = render_colored_svg(icon_path, QSize(24, 24), base_color)
            btn.set_icon(QIcon(pixmap))

        set_nav_icon(self.btn_home, icons.home_icon)
        set_nav_icon(self.btn_invoice, icons.invoice_icon)
        set_nav_icon(self.btn_documents, icons.documents_icon)
        set_nav_icon(self.btn_issued, icons.invoice_table)
        set_nav_icon(self.btn_reports, icons.home_icon)
        set_nav_icon(self.btn_workspace, icons.documents_icon)
        set_nav_icon(self.btn_help, icons.help_icon)
        set_nav_icon(self.btn_settings, icons.settings_icon)
        set_nav_icon(self.btn_logout, icons.logout_icon)

        # Sidebar Toggle (Using help icon as placeholder or specific menu icon if available)
        # Assuming you want a "menu" icon, but using available assets:
        self.sidebar_toggle_button.setIcon(QIcon(str(icons.settings_icon)))
        self.sidebar_toggle_button.setIconSize(QSize(24, 24))

    def _setup_connections(self):
        # Window controls
        self.x_button.clicked.connect(self.close_button_clicked.emit)
        self.maximize_button.clicked.connect(self.maximize_button_clicked.emit)
        self.minimize_button.clicked.connect(self.minimize_button_clicked.emit)

        # Nav items
        self.btn_home.clicked.connect(self.home_button_clicked.emit)
        self.btn_invoice.clicked.connect(self.invoice_button_clicked.emit)
        self.btn_documents.clicked.connect(self.documents_button_clicked.emit)
        self.btn_issued.clicked.connect(self.issued_invoices_button_clicked.emit)
        self.btn_reports.clicked.connect(self.reports_button_clicked.emit)
        self.btn_workspace.clicked.connect(self.workspace_button_clicked.emit)
        self.btn_help.clicked.connect(self.help_button_clicked.emit)
        self.btn_settings.clicked.connect(self.settings_button_clicked.emit)
        self.btn_logout.clicked.connect(self.logout_button_clicked.emit)

        self.large_user_pic.clicked.connect(self.user_profile_clicked.emit)
        self.user_name_label.clicked.connect(self.user_profile_clicked.emit)
        self.sidebar_toggle_button.clicked.connect(self.toggle_sidebar)

    # -------------------- Public API for Controller --------------------

    def set_active_nav_item(self, item_id: str):
        """Visually highlights the selected sidebar item."""
        for _id, btn in self.nav_items.items():
            is_active = (_id == item_id)
            btn.set_active(is_active)

    def smooth_minimize(self):
        self._anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self._anim_opacity.setDuration(220)
        self._anim_opacity.setStartValue(1.0)
        self._anim_opacity.setEndValue(0.0)
        self._anim_opacity.setEasingCurve(QEasingCurve.Type.InQuad)
        self._anim_opacity.finished.connect(self._minimize_and_restore)
        self._anim_opacity.start()

    def _minimize_and_restore(self):
        self.showMinimized()
        self.setWindowOpacity(1.0)

    def update_user_profile(self, user_dto: UserProfileDTO):
        self.user_name_label.setText(user_dto.full_name)
        self.user_position_label.setText(user_dto.role_fa)
        if user_dto.avatar_path and os.path.exists(user_dto.avatar_path):
            pix = QPixmap(user_dto.avatar_path)
            self.large_user_pic.setPixmap(pix)

    # -------------------- Mouse Handling (Frameless) --------------------
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

            if geom.width() < self.minimumWidth():
                geom.setWidth(self.minimumWidth())
            if geom.height() < self.minimumHeight():
                geom.setHeight(self.minimumHeight())

            self.setGeometry(geom)
            self.drag_start_position = event.globalPosition().toPoint()
            self.normal_geometry = self.geometry()
            return

        if self.drag_start_position is not None:
            if self.is_maximized:
                ratio = event.globalPosition().x() / self.width()
                self.setGeometry(self.normal_geometry)
                self.is_maximized = False
                new_x = int(event.globalPosition().x() - (self.width() * ratio))
                self.drag_start_position = QPoint(new_x, int(event.globalPosition().y()))
                self.move(self.drag_start_position)
            else:
                delta = event.globalPosition().toPoint() - self.drag_start_position
                self.move(self.pos() + delta)
                self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.drag_start_position = None
            self.resize_edge = None
            self.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.titlebar_widget.underMouse():
            self.toggle_maximize_restore()
        super().mouseDoubleClickEvent(event)

    # -------------------- Sidebar Visual Logic --------------------
    def toggle_sidebar(self):
        start_w = self.sidebar_frame.width()
        target_w = SIDEBAR_COLLAPSED_WIDTH if self.is_sidebar_expanded else SIDEBAR_EXPANDED_WIDTH

        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"minimumWidth")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setStartValue(start_w)
        self.sidebar_animation.setEndValue(target_w)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.sidebar_animation.valueChanged.connect(lambda v: self.sidebar_frame.setFixedWidth(int(v)))

        if self.is_sidebar_expanded:
            self._set_sidebar_text_visible(False)
        else:
            self.sidebar_animation.finished.connect(lambda: self._set_sidebar_text_visible(True))

        self.sidebar_animation.start()
        self.is_sidebar_expanded = not self.is_sidebar_expanded
        self._settings.setValue("sidebar_expanded", self.is_sidebar_expanded)

    def _set_sidebar_text_visible(self, visible: bool, immediate: bool = False):
        for btn in self.nav_items.values():
            btn.set_text_visible(visible)

        self.user_name_label.setVisible(visible)
        self.user_position_label.setVisible(visible)

        if immediate:
            QApplication.processEvents()
