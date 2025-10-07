# features/Admin_Panel/admin_dashboard/admin_dashboard_view.py

import qtawesome as qta
from datetime import date

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
                               QGridLayout, QListWidget, QListWidgetItem)
from PySide6.QtCore import Signal, Qt

from features.Admin_Panel.admin_dashboard.admin_dashboard_models import KpiData, AttentionQueueItem
from features.Admin_Panel.admin_dashboard.admin_dashboard_qss import ADMIN_DASHBOARD_STYLES

from shared.utils.persian_tools import to_persian_jalali_string, to_persian_numbers
from shared.widgets.custom_widgets import create_stat_card


class AdminDashboardView(QWidget):
    """
    The main dashboard _view for the admin panel.
    """
    calculate_wage_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardContainer")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Quick Actions Bar ---
        actions_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(" بروزرسانی")
        self.refresh_btn.setIcon(qta.icon('fa5s.sync-alt'))

        actions_layout.addWidget(self.refresh_btn)
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        # --- Main Content Area (Two Columns) ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        # --- Main Column (Left) ---
        main_column = QVBoxLayout()
        content_layout.addLayout(main_column, 7)  # 70% width

        # KPI Cards
        kpi_layout = QGridLayout()
        self.kpi_revenue_today = create_stat_card("درآمد امروز", "#28a745")
        self.kpi_revenue_month = create_stat_card("درآمد این ماه", "#17a2b8")
        self.kpi_outstanding = create_stat_card("مطالبات معوق", "#ffc107")
        self.kpi_new_customers = create_stat_card("مشتریان جدید (این ماه)", "#6f42c1")
        kpi_layout.addWidget(self.kpi_revenue_today, 0, 0)
        kpi_layout.addWidget(self.kpi_revenue_month, 0, 1)
        kpi_layout.addWidget(self.kpi_outstanding, 1, 0)
        kpi_layout.addWidget(self.kpi_new_customers, 1, 1)
        main_column.addLayout(kpi_layout)

        # Action Queue
        attention_group = QGroupBox("سفارشات نیازمند توجه")
        attention_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        attention_layout = QVBoxLayout(attention_group)
        self.attention_list = QListWidget()
        attention_layout.addWidget(self.attention_list)
        main_column.addWidget(attention_group, 1)

        # --- Sidebar (Right) ---
        sidebar_column = QVBoxLayout()
        content_layout.addLayout(sidebar_column, 3)

        performers_group = QGroupBox("برترین‌های ماه")
        performers_layout = QVBoxLayout(performers_group)
        sidebar_column.addWidget(performers_group)

        # Top Translators
        performers_layout.addWidget(QLabel("مترجم‌ها (بر اساس درآمد)"))
        self.top_translators_list = QListWidget()
        self.top_translators_list.setObjectName("performerList")
        performers_layout.addWidget(self.top_translators_list)

        # Top Clerks
        performers_layout.addWidget(QLabel("کارمندان (بر اساس تعداد فاکتور)"))
        self.top_clerks_list = QListWidget()
        self.top_clerks_list.setObjectName("performerList")
        performers_layout.addWidget(self.top_clerks_list)

        self.setStyleSheet(ADMIN_DASHBOARD_STYLES)

    def update_kpi_cards(self, data: KpiData):
        self.kpi_revenue_today.findChild(QLabel, "statValue").setText(to_persian_numbers(data.revenue_today))
        self.kpi_revenue_month.findChild(QLabel, "statValue").setText(to_persian_numbers(data.revenue_month))
        self.kpi_outstanding.findChild(QLabel, "statValue").setText(to_persian_numbers(data.outstanding))
        self.kpi_new_customers.findChild(QLabel, "statValue").setText(to_persian_numbers(data.new_customers))

    def populate_attention_queue(self, orders: list[AttentionQueueItem]):
        """Builds the rich, multi-line list items for the attention queue."""
        self.attention_list.clear()
        today = date.today()

        for order in orders:
            # --- 1. Construct the main text line with companion info ---
            main_text = order.customer_name
            if order.companion_count > 0:
                main_text += f" و {to_persian_numbers(order.companion_count)} همراه"

            # --- 2. Construct the secondary details line ---
            details = []
            # Delivery Status
            if order.delivery_date < today:
                details.append("<font color='#d9534f'> (دیرکرد)</font>")
            elif order.delivery_date == today:
                details.append("<font color='#f0ad4e'> (موعد امروز)</font>")
            else:  # Due tomorrow
                details.append(f" (موعد: {to_persian_jalali_string(order.delivery_date)})")

            # Payment Status
            if order.payment_status == 0:  # Unpaid
                remaining_amount = order.total_amount - (
                            order.final_amount - order.total_amount)  # A bit of _logic to get remaining
                details.append(
                    f"<font color='#d9534f'> (پرداخت نشده - {to_persian_numbers(f'{remaining_amount:,.0f}')} تومان)</font>")
            else:
                details.append("<font color='green'> (پرداخت شده)</font>")

            # --- 3. Combine into a single rich text string for the item ---
            # We use a QListWidgetItem and a custom widget to hold two labels for better alignment.
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(2)

            main_label = QLabel(main_text)
            # main_label.setFont(FontManager.get_font(size=11, bold=True))

            details_label = QLabel("".join(details))
            # details_label.setFont(FontManager.get_font(size=9))

            item_layout.addWidget(main_label)
            item_layout.addWidget(details_label)
            item_widget.setLayout(item_layout)

            list_item = QListWidgetItem(self.attention_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.attention_list.addItem(list_item)
            self.attention_list.setItemWidget(list_item, item_widget)

            # Set the color of the main text based on urgency
            if order.delivery_date < today:
                main_label.setStyleSheet("color: #d9534f;")
            elif order.delivery_date == today:
                main_label.setStyleSheet("color: #f0ad4e;")

    def populate_top_performers(self, performers_data: dict):
        self.top_translators_list.clear()
        self.top_clerks_list.clear()

        # Populate translators list
        for i, translator in enumerate(performers_data.get("translators", []), 1):
            icon = qta.icon('fa5s.trophy', color=['#FFD700', '#C0C0C0', '#CD7F32'][i - 1] if i <= 3 else '#808080')
            # --- FIX: Update text to show document count ---
            item_text = f"{translator.name} - {to_persian_numbers(int(translator.value))} سند"
            list_item = QListWidgetItem(icon, item_text)
            self.top_translators_list.addItem(list_item)

        # Populate clerks list
        for i, clerk in enumerate(performers_data.get("clerks", []), 1):
            icon = qta.icon('fa5s.medal', color=['#0078D7', '#17a2b8', '#5bc0de'][i - 1] if i <= 3 else '#808080')
            item_text = f"{clerk.name} - {to_persian_numbers(int(clerk.value))} فاکتور"
            list_item = QListWidgetItem(icon, item_text)
            self.top_clerks_list.addItem(list_item)
