# features/Admin_Panel/admin_dashboard/admin_dashboard_qss.py

ADMIN_DASHBOARD_STYLES = """
/* ===================================
   Admin Dashboard Styles
   =================================== */

/* Main Dashboard Container */
#DashboardContainer {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f8f9fa, stop:1 #e9ecef);
    border-radius: 8px;
}

/* ===================================
   Buttons
   =================================== */

QPushButton {
    background-color: #0078d7;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #005a9e;
}

QPushButton:pressed {
    background-color: #004578;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* ===================================
   KPI Stat Cards
   =================================== */

QWidget[objectName="statCard"] {
    background-color: white;
    border-radius: 10px;
    border: 1px solid #e0e0e0;
    padding: 15px;
    min-height: 100px;
}

QWidget[objectName="statCard"]:hover {
    border: 1px solid #b0b0b0;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

QLabel[objectName="statTitle"] {
    color: #6c757d;
    font-size: 13px;
    font-weight: bold;
    padding-bottom: 5px;
}

QLabel[objectName="statValue"] {
    font-size: 24px;
    font-weight: bold;
    color: #212529;
    padding-top: 5px;
}

/* ===================================
   Group Boxes
   =================================== */

QGroupBox {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 5px 15px;
    background-color: white;
    color: #495057;
    border-radius: 5px;
}

/* ===================================
   List Widgets
   =================================== */

QListWidget {
    background-color: #fafbfc;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 5px;
    outline: none;
}

QListWidget::item {
    background-color: white;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 8px;
    margin: 4px;
}

QListWidget::item:hover {
    background-color: #f1f3f5;
    border-color: #ced4da;
}

QListWidget::item:selected {
    background-color: #e7f3ff;
    border-color: #0078d7;
    color: #212529;
}

/* Performer Lists (Top Translators/Clerks) */
QListWidget[objectName="performerList"] {
    background-color: #f8f9fa;
    min-height: 150px;
}

QListWidget[objectName="performerList"]::item {
    background-color: white;
    font-size: 13px;
    padding: 10px;
    margin: 3px;
    border-left: 3px solid transparent;
}

QListWidget[objectName="performerList"]::item:hover {
    background-color: #e9ecef;
    border-left-color: #0078d7;
}

/* ===================================
   Labels
   =================================== */

QLabel {
    color: #212529;
    font-size: 13px;
}

QGroupBox > QVBoxLayout > QLabel {
    font-weight: bold;
    color: #495057;
    padding: 8px 5px 5px 5px;
    font-size: 12px;
}

/* ===================================
   Scrollbars
   =================================== */

QScrollBar:vertical {
    background: #f1f3f5;
    width: 12px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #adb5bd;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #868e96;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #f1f3f5;
    height: 12px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #adb5bd;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #868e96;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===================================
   Attention Queue Custom Styling
   =================================== */

/* Style for attention queue items with urgency colors */
QWidget[objectName="attentionItem"] {
    background-color: white;
    border-radius: 6px;
    padding: 5px;
}

/* ===================================
   Color Scheme Reference
   =================================== */

/*
Revenue Today Card: #28a745 (Green)
Revenue Month Card: #17a2b8 (Blue)
Outstanding Card: #ffc107 (Yellow/Warning)
New Customers Card: #6f42c1 (Purple)

Status Colors:
- Overdue: #d9534f (Red)
- Due Today: #f0ad4e (Orange)
- Paid: green
- Primary Action: #0078d7 (Blue)

Trophy Colors:
- Gold: #FFD700
- Silver: #C0C0C0
- Bronze: #CD7F32

Medal Colors:
- Blue: #0078D7
- Cyan: #17a2b8
- Light Blue: #5bc0de
*/

/* ===================================
   Responsive Adjustments
   =================================== */

/* Ensure proper spacing and sizing */
QWidget {
    selection-background-color: #0078d7;
    selection-color: white;
}

/* ===================================
   Animation-like Effects (Hover States)
   =================================== */

QPushButton,
QListWidget::item,
QGroupBox {
    /* Smooth transitions for hover effects */
    transition: all 0.2s ease-in-out;
}

/* ===================================
   Accessibility
   =================================== */

*:focus {
    outline: 2px solid #0078d7;
    outline-offset: 2px;
}
 """
