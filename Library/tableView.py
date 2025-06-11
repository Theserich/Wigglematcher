from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableView, QAbstractItemView)
from PyQt5.QtGui import  QKeySequence, QClipboard, QStandardItem
from PyQt5.QtWidgets import QMenu, QAction,QHeaderView
from PyQt5.QtCore import Qt, QItemSelectionModel


class MyTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        tri_header =  TriStateHeader(Qt.Horizontal, self)
        self.setHorizontalHeader(tri_header)
        self.setEditTriggers(QTableView.DoubleClicked | QTableView.SelectedClicked)
        self.customContextMenuRequested.connect(self.openContextMenu)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copySelection()
        elif event.matches(QKeySequence.Paste):
            self.pasteSelection()
        else:
            super().keyPressEvent(event)

    def copySelection(self):
        # sort select indexes into rows and columns
        previous = self.selectionModel().selectedIndexes()[0]
        columns = []
        rows = []
        for index in self.selectionModel().selectedIndexes():
            if previous.row() != index.row():
                columns.append(rows)
                rows = []
            rows.append(index.data(role=1))
            previous = index
        columns.append(rows)
        clipboard = ""
        ncols = len(columns[0])
        nrows = len(columns)
        for r in range(nrows):
            for c in range(ncols):
                clipboard += str(columns[r][c])
                if c != (ncols - 1):
                    clipboard += '\t'
            if r != (nrows - 1):
                clipboard += '\n'
        sys_clip = QApplication.clipboard()
        sys_clip.setText(clipboard)

    def pasteSelection(self):
        model = self.model()
        clipboard = QApplication.clipboard()
        data = clipboard.text()
        if not data:
            return

        data = data.rstrip("\n")
        selected_indexes = self.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        selected_indexes.sort(key=lambda i: (i.row(), i.column()))
        start_row = selected_indexes[0].row()
        start_col = selected_indexes[0].column()

        rows = data.split('\n')
        num_rows = len(rows)
        model_rows = model.rowCount()
        if start_row + num_rows > model_rows:
            extra_rows = (start_row + num_rows) - model_rows
            model.insertRows(model_rows, extra_rows)
        model_cols = model.columnCount()

        pasted_indexes = []
        success = True

        for r, row_data in enumerate(rows):
            cols = row_data.split('\t')
            for c, value in enumerate(cols):
                print(value,r,c)
                model_index = model.index(start_row + r, start_col + c)
                print(value)
                if model_index.isValid():
                    print(value)
                    model.setData(model_index, value, recalc=False)
                    #if not success:
                    #    break
                    pasted_indexes.append(model_index)
            if not success:
                break
        model.sort_column = -1
        model.sort(model.sort_column, model.order)
        model.calc.recalc_wiggledata(fm=model.fmcalc)
        model.parent.recalcFlag = True
        model.parent.recalcIndex = model.tabIndex
        model.parent.redraw()


    def deleteRows(self):
        selected_indexes = self.selectionModel().selectedIndexes()
        if not selected_indexes:
            return
        model = self.model()
        rows = sorted(set(index.row() for index in selected_indexes), reverse=True)
        for row in rows:
            model.removeRows(row)
        widget = self.get_top_parent(self)
        widget.redraw()

    def get_top_parent(self, widget):
        """Recursively find the top-most parent of a widget."""
        parent = widget.parent()
        if parent:
            return self.get_top_parent(parent)  # Continue up the chain
        return widget

    def openContextMenu(self, position):
        menu = QMenu(self)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copySelection)
        menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.pasteSelection)
        menu.addAction(paste_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.deleteRows)
        menu.addAction(delete_action)

        # Optional: Add more actions here (e.g., Clear, Delete Row, etc.)
        # Example:
        # clear_action = QAction("Clear", self)
        # clear_action.triggered.connect(self.clearSelection)
        # menu.addAction(clear_action)

        menu.exec_(self.viewport().mapToGlobal(position))

class TriStateHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._sort_state = {}  # column: state (0=none, 1=asc, 2=desc)

    def mousePressEvent(self, event):
        logical_index = self.logicalIndexAt(event.pos())
        old_state = self._sort_state.get(logical_index, 0)
        new_state = (old_state + 1) % 3

        self._sort_state[logical_index] = new_state

        # Clear all other columns' sort state
        for key in list(self._sort_state):
            if key != logical_index:
                self._sort_state[key] = 0

        if new_state == 0:
            # No sort
            self.setSortIndicator(-1, Qt.AscendingOrder)
            self.parent().model().layoutAboutToBeChanged.emit()
            self.parent().model().sort(-1, Qt.AscendingOrder)
            self.parent().model().layoutChanged.emit()
        elif new_state == 1:
            self.setSortIndicator(logical_index, Qt.AscendingOrder)
            self.parent().sortByColumn(logical_index, Qt.AscendingOrder)
        else:
            self.setSortIndicator(logical_index, Qt.DescendingOrder)
            self.parent().sortByColumn(logical_index, Qt.DescendingOrder)

        super().mousePressEvent(event)



