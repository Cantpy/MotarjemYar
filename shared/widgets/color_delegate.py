from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QPainter, QBrush


class PriorityColorDelegate(QStyledItemDelegate):
    """Custom delegate for applying priority-based colors."""

    def __init__(self, priority_column: int = -1):
        super().__init__()
        self.priority_column = priority_column
        self.priority_colors = {
            'urgent': QColor(255, 200, 200),
            'needs_attention': QColor(255, 220, 150),
            'normal': QColor(255, 255, 255)
        }

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """Custom paint method to apply priority colors."""
        # Get the priority from the model (you'd need to store this)
        priority = index.data(Qt.ItemDataRole.UserRole)

        if priority in self.priority_colors:
            option.backgroundBrush = self.priority_colors[priority]

        super().paint(painter, option, index)


class PriorityColorDelegateNoRole(QStyledItemDelegate):
    """Delegate that colors cells based on displayed priority text."""

    def __init__(self, priority_map, parent=None):
        super().__init__(parent)
        self.priority_map = priority_map  # dict[row_index] = QColor()

    def paint(self, painter, option, index):
        row = index.row()
        if row in self.priority_map:
            color = self.priority_map[row]
            option.backgroundBrush = QBrush(color)
        super().paint(painter, option, index)
