from PySide6.QtWidgets import QStyledItemDelegate


class ColorDelegate(QStyledItemDelegate):
    def __init__(self, colors_dict, parent=None):
        super().__init__(parent)
        self.colors_dict = colors_dict

    def paint(self, painter, option, index):
        key = (index.row(), index.column())
        if key in self.colors_dict:
            color = self.colors_dict[key]
            painter.save()
            painter.fillRect(option.rect, color)
            painter.restore()

        super().paint(painter, option, index)
