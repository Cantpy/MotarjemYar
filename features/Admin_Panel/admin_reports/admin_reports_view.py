# Admin_Panel/admin_reports/admin_reports_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QGridLayout,
                               QTabWidget)
from PySide6.QtCore import Qt, Signal, QPoint, QEvent
import pyqtgraph as pg
import qtawesome as qta
from shared.fonts.font_manager import FontManager
from features.Admin_Panel.admin_reports.advanced_search_view import AdvancedSearchView
from shared import to_persian_number
from shared.widgets.custom_widgets import create_stat_card


# --- NEW: Move all old chart logic into its own class for cleanliness ---
class FinancialReportsWidget(QWidget):
    """
    The user interface for the Reports Tab.
    Contains multiple charts controlled by a single year navigator.
    This view is "dumb" and only displays data provided by the controller.
    """
    # Signals to notify the controller of user actions
    next_year_requested = Signal()
    previous_year_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ReportsContainer")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFont(FontManager.get_font(size=12))

        # --- Store raw data for tooltips ---
        self._revenue_data = []
        self._expense_data = []
        self._profit_data = []
        self._avg_revenue = 0.0
        self._avg_expense = 0.0
        self._persian_months = []

        # --- Main Layout (will contain the scroll area) ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins for the main layout itself

        # --- 1. Create the Scroll Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Make it seamless
        main_layout.addWidget(scroll_area)

        # --- 2. Create the main container widget that will go INSIDE the scroll area ---
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)

        # --- 3. All content now goes into the container_layout ---
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(25)

        # --- Stat Card Layout ---
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        self.total_revenue_card = create_stat_card("کل درآمد سال", "#28a745")
        self.total_expense_card = create_stat_card("کل هزینه‌های سال", "#d9534f")
        self.total_profit_card = create_stat_card("سود خالص سال", "#0078D7")
        stats_layout.addWidget(self.total_revenue_card, 0, 0)
        stats_layout.addWidget(self.total_expense_card, 0, 1)
        stats_layout.addWidget(self.total_profit_card, 0, 2)
        container_layout.addLayout(stats_layout)

        # --- Year Navigation and Export Button ---
        self._setup_year_navigation(container_layout)

        # --- Chart 1: Revenue ---
        self.revenue_chart = self._create_chart_widget("روند درآمد سالانه")
        container_layout.addWidget(self.revenue_chart)

        # --- Chart 2: Expenses ---
        self.expense_chart = self._create_chart_widget("روند هزینه‌های سالانه")
        container_layout.addWidget(self.expense_chart)

        # --- Chart 3: Profit/Loss Comparison ---
        self.profit_chart = self._create_chart_widget("مقایسه درآمد و هزینه")
        container_layout.addWidget(self.profit_chart)

        # --- Tooltip Setup ---
        self.tooltip = QLabel(self, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.ToolTip)
        self.tooltip.setStyleSheet("""
                    background-color: rgba(30, 30, 30, 220); color: white; padding: 8px;
                    border-radius: 6px; font-size: 12px; line-height: 1.5;
                """)
        self.tooltip.hide()

    def _setup_year_navigation(self, layout: QVBoxLayout):
        """Creates the year navigation buttons and label."""
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)

        self.next_year_btn = QPushButton(icon=qta.icon('fa5s.chevron-right'))
        self.next_year_btn.setToolTip("سال بعد")

        self.year_label = QLabel("...")
        self.year_label.setFont(FontManager.get_font(size=14, bold=True))
        self.year_label.setAlignment(Qt.AlignCenter)

        self.prev_year_btn = QPushButton(icon=qta.icon('fa5s.chevron-left'))
        self.prev_year_btn.setToolTip("سال قبل")

        self.export_btn = QPushButton(text="خروجی اکسل", icon=qta.icon('fa5s.file-excel'))
        self.export_btn.clicked.connect(self.export_requested)
        nav_layout.insertWidget(0, self.export_btn)

        nav_layout.addStretch()
        nav_layout.addWidget(self.next_year_btn)
        nav_layout.addWidget(self.year_label)
        nav_layout.addWidget(self.prev_year_btn)
        nav_layout.addStretch()

        self.prev_year_btn.clicked.connect(self.previous_year_requested)
        self.next_year_btn.clicked.connect(self.next_year_requested)

        layout.addWidget(nav_frame)

    def _create_chart_widget(self, title: str) -> pg.PlotWidget:
        """Helper function to create and configure a standard chart."""
        chart_widget = pg.PlotWidget(background='w')
        chart_widget.getViewBox().setMouseEnabled(x=False, y=False)
        chart_widget.setTitle(title, color="#333", size="14pt")
        chart_widget.setLabel('left', 'مبلغ (میلیون تومان)', color="#555")
        chart_widget.setLabel('bottom', 'ماه', color="#555")
        chart_widget.showGrid(x=True, y=True, alpha=0.3)
        chart_widget.getPlotItem().getViewBox().setBorder(color="#ccc", width=1)
        chart_widget.setMinimumHeight(350)
        chart_widget.installEventFilter(self)
        chart_widget.scene().sigMouseMoved.connect(self._on_mouse_hover)
        return chart_widget

    def eventFilter(self, watched_obj, event: QEvent) -> bool:
        """
        Intercepts events for child widgets (the charts).
        """
        # FIX 2: Intercept mouse wheel events and ignore them,
        # allowing the parent QScrollArea to handle scrolling.
        if event.type() == QEvent.Type.Wheel:
            event.ignore()
            return True  # Event has been handled (by ignoring it)

        # FIX 1: Intercept mouse leave events to hide the sticky tooltip.
        if event.type() == QEvent.Type.Leave:
            self.tooltip.hide()

        # Pass all other events on to the default processing
        return super().eventFilter(watched_obj, event)

    def update_revenue_chart(self, revenues: list, average: float, months: list):
        self.revenue_chart.clear()
        if not revenues: return
        x_ticks = list(range(1, len(months) + 1))
        revenue_bars = pg.BarGraphItem(x=[t - 0.15 for t in x_ticks], height=revenues, width=0.3, brush='#0078D7')
        avg_bars = pg.BarGraphItem(x=[t + 0.15 for t in x_ticks], height=[average] * len(months), width=0.3,
                                   brush='#5bc0de')
        self.revenue_chart.addItem(revenue_bars)
        self.revenue_chart.addItem(avg_bars)
        axis = self.revenue_chart.getAxis('bottom')
        ticks = [(i, name) for i, name in enumerate(months, 1)]
        axis.setTicks([ticks])

    def update_expense_chart(self, expenses: list, average: float, months: list):
        self.expense_chart.clear()
        if not expenses: return
        x_ticks = list(range(1, len(months) + 1))
        expense_bars = pg.BarGraphItem(x=[t - 0.15 for t in x_ticks], height=expenses, width=0.3, brush='#d9534f')
        avg_bars = pg.BarGraphItem(x=[t + 0.15 for t in x_ticks], height=[average] * len(months), width=0.3,
                                   brush='#f0ad4e')
        self.expense_chart.addItem(expense_bars)
        self.expense_chart.addItem(avg_bars)
        axis = self.expense_chart.getAxis('bottom')
        ticks = [(i, name) for i, name in enumerate(months, 1)]
        axis.setTicks([ticks])

    def update_profit_chart(self, revenues: list, expenses: list, profits: list, months: list):
        self.profit_chart.clear()
        self._revenue_data = revenues
        self._expense_data = expenses
        self._profit_data = profits
        if not revenues: return
        x_ticks = list(range(1, len(months) + 1))
        self.profit_chart.addLegend(offset=(30, 10))
        rev_bars = pg.BarGraphItem(x=[t - 0.2 for t in x_ticks], height=revenues, width=0.4, brush='#0078D7',
                                   name="درآمد")
        exp_bars = pg.BarGraphItem(x=[t + 0.2 for t in x_ticks], height=expenses, width=0.4, brush='#d9534f',
                                   name="هزینه")
        profit_line = pg.PlotDataItem(x=x_ticks, y=profits, pen=pg.mkPen('#28a745', width=3), symbol='o',
                                      symbolBrush='#28a745', name="سود")
        self.profit_chart.addItem(rev_bars)
        self.profit_chart.addItem(exp_bars)
        self.profit_chart.addItem(profit_line)
        axis = self.profit_chart.getAxis('bottom')
        ticks = [(i, name) for i, name in enumerate(months, 1)]
        axis.setTicks([ticks])

    def update_tooltip_data(self, revenues, avg_revenue, expenses, avg_expense, profits, persian_months):
        """Stores the raw (non-million) data for accurate tooltip display."""
        self._revenue_data = revenues
        self._avg_revenue = avg_revenue
        self._expense_data = expenses
        self._avg_expense = avg_expense
        self._profit_data = profits
        self._persian_months = persian_months

    def update_stat_cards(self, total_revenue, total_expense, total_profit):
        self.total_revenue_card.findChild(QLabel, "statValue").setText(to_persian_number(f"{total_revenue:,.0f} تومان"))
        self.total_expense_card.findChild(QLabel, "statValue").setText(to_persian_number(f"{total_expense:,.0f} تومان"))
        self.total_profit_card.findChild(QLabel, "statValue").setText(to_persian_number(f"{total_profit:,.0f} تومان"))

    def _on_mouse_hover(self, pos):
        """A single, generic handler for showing tooltips on any chart."""
        active_chart = None
        # Determine which chart the mouse is physically inside
        # Use mapToParent to get coordinates relative to the view, ensuring correct detection
        view_pos = self.sender().parent().mapToParent(pos.toPoint())
        if self.revenue_chart.geometry().contains(view_pos):
            active_chart = self.revenue_chart
        elif self.expense_chart.geometry().contains(view_pos):
            active_chart = self.expense_chart
        elif self.profit_chart.geometry().contains(view_pos):
            active_chart = self.profit_chart
        else:
            self.tooltip.hide()
            return

        mouse_point = active_chart.getPlotItem().vb.mapSceneToView(pos)
        month_tick = int(round(mouse_point.x()))
        month_index = month_tick - 1

        tooltip_text = ""
        is_hovering_bar = False

        if 0 <= month_index < 12:
            block_start = month_tick - 0.5
            block_end = month_tick + 0.5

            # Check if mouse is within the horizontal block
            if block_start <= mouse_point.x() < block_end:
                # Logic for the Revenue Chart
                if active_chart is self.revenue_chart and self._revenue_data:
                    # --- FIX: Check vertical position (Y-axis) ---
                    if 0 <= mouse_point.y() < max(self._revenue_data[month_index], self._avg_revenue):
                        is_hovering_bar = True
                        rev = self._revenue_data[month_index]
                        avg_rev = self._avg_revenue
                        tooltip_text = (f"<b>درآمد ماه:</b> {to_persian_number(f"{rev:,.1f}")} م.ت<br>"
                                        f"<b>میانگین درآمد:</b> {to_persian_number(f"{avg_rev:,.1f}")} م.ت")

                # Logic for the Expense Chart
                elif active_chart is self.expense_chart and self._expense_data:
                    # --- FIX: Check vertical position (Y-axis) ---
                    if 0 <= mouse_point.y() < max(self._expense_data[month_index], self._avg_expense):
                        is_hovering_bar = True
                        exp = self._expense_data[month_index]
                        avg_exp = self._avg_expense
                        tooltip_text = (f"<b>هزینه ماه:</b> {to_persian_number(f"{exp:,.1f}")} م.ت<br>"
                                        f"<b>میانگین هزینه:</b> {to_persian_number(f"{avg_exp:,.1f}")} م.ت")

                # Logic for the Profit Chart
                elif active_chart is self.profit_chart and self._profit_data:
                    # --- FIX: Check vertical position (Y-axis) ---
                    if 0 <= mouse_point.y() < max(self._revenue_data[month_index], self._expense_data[month_index]):
                        is_hovering_bar = True
                        rev = self._revenue_data[month_index]
                        exp = self._expense_data[month_index]
                        prof = self._profit_data[month_index]
                        tooltip_text = (f"<b>درآمد:</b> {to_persian_number(f"{rev:,.1f}")} م.ت<br>"
                                        f"<b>هزینه:</b> {to_persian_number(f"{exp:,.1f}")} م.ت<br>"
                                        f"<b>سود:</b> {to_persian_number(f"{prof:,.1f}")} م.ت")

        if is_hovering_bar:
            month_name = self._persian_months[month_index]
            tooltip_text = f"<b>{month_name}</b><hr>" + tooltip_text
            self.tooltip.setText(tooltip_text)
            self.tooltip.adjustSize()
            global_pos = active_chart.mapToGlobal(pos.toPoint())
            self.tooltip.move(global_pos + QPoint(10, 10))
            self.tooltip.show()
        else:
            self.tooltip.hide()

    def set_year_display(self, year: int):
        """Updates the year label in the navigation bar."""
        self.year_label.setText(f"سال {to_persian_number(year)}")


class AdminReportsView(QWidget):
    """
    The main container for the Reports section, using a TabWidget
    to switch between different report types.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setLayoutDirection(Qt.RightToLeft)
        main_layout.addWidget(self.tab_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        self.financial_reports = FinancialReportsWidget()
        scroll_area.setWidget(self.financial_reports)

        self.advanced_search = AdvancedSearchView()  # Assuming this class exists

        # --- Add them as tabs ---
        self.tab_widget.addTab(scroll_area, "گزارشات مالی سالانه")
        self.tab_widget.addTab(self.advanced_search, "جستجوی پیشرفته")
