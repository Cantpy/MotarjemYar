# features/Admin_Panel/admin_dashboard_qss.py

ADMIN_DASHBOARD_STYLES = """
QMainWindow {
    background-color: #F0F2F5; /* A light grey background for the whole window */
}

QTabWidget::pane {
    border: none;
    border-top: 3px solid #0078D7; /* A blue line separating tabs from content */
}

QTabBar::tab {
    background: #E1E3E5;
    color: #333;
    padding: 12px 20px;
    margin-left: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    font-size: 10pt;
}

QTabBar::tab:selected {
    background: #0078D7; /* Blue background for the selected tab */
    color: white;
}

QTabBar::tab:hover {
    background: #C7CDD1;
}

QTabBar::tab:selected:hover {
    background: #005A9E; /* A darker blue on hover for the selected tab */
}

/* Style for our custom KPI Card Widget */
.KPIWidget {
    background-color: #FFFFFF;
    border-radius: 8px;
    padding: 15px;
}

/* Style for the main container in the dashboard */
#DashboardContainer {
    background-color: #F0F2F5; /* Match the main window background */
    border: none;
} """
