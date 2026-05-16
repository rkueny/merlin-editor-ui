"""Custom QTreeWidget that handles drag-and-drop:
- Internal moves: reorder/move stories and folders, with model sync.
- External file drops: emit a signal so the main window can convert+insert.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem

from .playlist import Node

NODE_ROLE = Qt.UserRole + 1


class MerlinTree(QTreeWidget):
    """Tree that owns model-aware drag-and-drop."""

    files_dropped = Signal(list, object)
    node_moved = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_node: Node | None = None
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def set_root(self, root: Node | None) -> None:
        self.root_node = root

    # ---------- drag events ----------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        # External file drop (from Finder)
        if event.mimeData().hasUrls():
            paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            if not paths:
                event.ignore()
                return
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            target_item = self.itemAt(pos)
            self.files_dropped.emit(paths, target_item)
            event.acceptProposedAction()
            return

        # Internal move: do it on the model, then refresh the tree
        if self.root_node is None:
            event.ignore()
            return

        source_item = self.currentItem()
        if source_item is None:
            super().dropEvent(event)
            return
        source_node: Node = source_item.data(0, NODE_ROLE)
        if source_node is None or source_node.parent is None:
            event.ignore()
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        target_item = self.itemAt(pos)
        indicator = self.dropIndicatorPosition()

        new_parent, new_index = self._resolve_drop_target(
            target_item, indicator, source_node
        )
        if new_parent is None:
            event.ignore()
            return

        if _is_descendant(new_parent, source_node):
            event.ignore()
            return

        if source_node.is_story and not new_parent.is_folder:
            event.ignore()
            return

        # Detach
        old_parent = source_node.parent
        old_index = old_parent.children.index(source_node)
        old_parent.children.pop(old_index)

        # Adjust index if moving within same parent and moving forward
        if old_parent is new_parent and old_index < new_index:
            new_index -= 1

        new_parent.children.insert(new_index, source_node)
        source_node.parent = new_parent

        self.node_moved.emit(source_node)
        event.acceptProposedAction()

    def _resolve_drop_target(
        self,
        target_item: QTreeWidgetItem | None,
        indicator: QAbstractItemView.DropIndicatorPosition,
        source_node: Node,
    ) -> tuple[Node | None, int]:
        # Drop in empty area → end of root
        if target_item is None:
            return self.root_node, len(self.root_node.children)

        target_node: Node = target_item.data(0, NODE_ROLE)
        if target_node is None:
            return None, 0

        if indicator == QAbstractItemView.OnItem:
            if target_node.is_folder:
                return target_node, len(target_node.children)
            # Dropping onto a story → insert next to it
            parent = target_node.parent
            return parent, parent.children.index(target_node) + 1

        # Above / below an item → insert as sibling
        parent = target_node.parent
        if parent is None:
            return self.root_node, 0
        idx = parent.children.index(target_node)
        if indicator == QAbstractItemView.AboveItem:
            return parent, idx
        return parent, idx + 1


def _is_descendant(maybe_descendant: Node, ancestor: Node) -> bool:
    """True if maybe_descendant is ancestor itself or any of its descendants."""
    node = maybe_descendant
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False
