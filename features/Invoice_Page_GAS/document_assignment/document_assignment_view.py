# document_assignment_view.py
from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QLabel, QVBoxLayout,
    QHBoxLayout, QGroupBox, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager


MIME_TYPE = "application/x-invoice-item-assignment"


# ----------------------------------------------------------------------
# Helper Widget for Drag-and-Drop
# ----------------------------------------------------------------------
class TargetListWidget(QListWidget):
    """
    A list that allows items to be dropped ONTO it, and also dragged
    FROM it (to move them to another target or back to the source).
    """
    # Signal to notify the main widget that a change has occurred.
    items_changed = Signal()

    def __init__(self, person_name: str, parent=None):
        super().__init__(parent)
        self.person_name = person_name
        # This list allows both dragging and dropping.
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # Allows items to be moved, not just copied.
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        """Accepts the drop event if the data format is correct."""
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Handles the visual feedback during the drag."""
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Handles the actual drop of the item."""
        if event.mimeData().hasFormat(MIME_TYPE):
            # Take the item from the source widget.
            # The 'takeItem' method removes it from the source list.
            item = event.source().takeItem(event.source().currentRow())
            self.addItem(item)
            event.acceptProposedAction()
            # Notify the main widget that an update is needed.
            self.items_changed.emit()
        else:
            super().dropEvent(event)


# ----------------------------------------------------------------------
# The Main Assignment Widget
# ----------------------------------------------------------------------
class AssignmentWidget(QWidget):

    def __init__(self, state_manager: WorkflowStateManager):
        super().__init__()
        self.state_manager = state_manager
        self.people_lists: list[TargetListWidget] = []

        # --- UI Setup ---
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        # Left Panel: Unassigned Documents (The Source)
        unassigned_group = QGroupBox("اسناد تخصیص نیافته (برای تخصیص، آیتم را بکشید)")
        unassigned_layout = QVBoxLayout(unassigned_group)

        self.unassigned_list = QListWidget()
        self.unassigned_list.setDragEnabled(True)
        self.unassigned_list.setDefaultDropAction(Qt.MoveAction)

        unassigned_layout.addWidget(self.unassigned_list)

        # Right Panel: People (The Targets)
        people_group = QGroupBox("تخصیص به افراد")
        self.people_layout = QVBoxLayout(people_group)

        main_layout.addWidget(unassigned_group, 1)  # Stretch factor 1
        main_layout.addWidget(people_group, 2)  # Stretch factor 2

    def set_data(self, customer: Customer, all_items: list[InvoiceItem], previous_assignments: dict = None):
        """
        Populates the widget and restores previous state if provided.
        Fixes Problems 3B and 4.
        """
        # 1. Clear all previous UI elements safely.
        self.unassigned_list.clear()
        self._clear_layout(self.people_layout)
        self.people_lists.clear()

        # 2. Create the target drop zones for each person.
        all_people = [customer] + customer.companions
        for person in all_people:
            label = QLabel(f"<b>{person.name}</b>")
            person_list = TargetListWidget(person.name)
            person_list.items_changed.connect(self._on_assignment_changed)

            self.people_layout.addWidget(label)
            self.people_layout.addWidget(person_list)
            self.people_lists.append(person_list)
        self.people_layout.addStretch()

        # 3. Populate lists based on previous assignments (or default if none).
        if previous_assignments:
            assigned_item_ids = set()
            # Restore assigned items
            for person_list in self.people_lists:
                person_name = person_list.person_name
                if person_name in previous_assignments:
                    for item in previous_assignments[person_name]:
                        list_item = QListWidgetItem(f"{item.service.name} (نسخه ۱)")
                        list_item.setData(Qt.UserRole, item)
                        person_list.addItem(list_item)
                        assigned_item_ids.add(id(item))  # Track by object ID
            # Restore unassigned items
            for item in all_items:
                if id(item) not in assigned_item_ids:
                    list_item = QListWidgetItem(f"{item.service.name} (نسخه ۱)")
                    list_item.setData(Qt.UserRole, item)
                    self.unassigned_list.addItem(list_item)
        else:
            # Default: put all items in the unassigned list
            for item in all_items:
                list_item = QListWidgetItem(f"{item.service.name} (نسخه ۱)")
                list_item.setData(Qt.UserRole, item)
                self.unassigned_list.addItem(list_item)

        # Trigger an initial update to the state manager.
        self._on_assignment_changed()

    def _on_assignment_changed(self):
        """
        Gathers all data from all lists and updates the central state manager.
        """
        assignments = {}

        # Gather items from each person's target list
        for person_list in self.people_lists:
            person_items = []
            for i in range(person_list.count()):
                list_item = person_list.item(i)
                invoice_item = list_item.data(Qt.UserRole)
                person_items.append(invoice_item)
            assignments[person_list.person_name] = person_items

        # Gather any remaining items from the source list
        unassigned_items = []
        for i in range(self.unassigned_list.count()):
            list_item = self.unassigned_list.item(i)
            invoice_item = list_item.data(Qt.UserRole)
            unassigned_items.append(invoice_item)
        assignments["__unassigned__"] = unassigned_items

        # Update the central state manager with the new assignments
        self.state_manager.set_assignments(assignments)

    def _clear_layout(self, layout):
        """Helper function to safely clear all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
