from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout, QLineEdit

class EditableTabWidget(QTabWidget):
    def __init__(self,*args,**kwargs):
        QTabWidget.__init__(self,*args,**kwargs)
        # Enable double-click renaming
        self.tabBarDoubleClicked.connect(self.edit_tab_name)
        self.tabBarClicked.connect(self.adjustWidgetWidth)
        # Temporary line edit for renaming
        self.line_edit = QLineEdit(self)
        self.line_edit.setHidden(True)
        self.line_edit.editingFinished.connect(self.rename_tab)

    def adjustWidgetWidth(self):
        parent = self.get_top_parent(self)
        parent.adjust_scrollarea_width()

    def edit_tab_name(self, index):
        """Enable editing when double-clicking a tab."""
        if index == -1:
            return

        # Get tab position and title
        rect = self.tabBar().tabRect(index)
        self.line_edit.setGeometry(rect)
        self.line_edit.setText(self.tabText(index))
        self.line_edit.setHidden(False)
        self.line_edit.setFocus()
        self.line_edit.selectAll()

        # Store current tab index
        self.current_editing_index = index

    def get_top_parent(self, widget):
        """Recursively find the top-most parent of a widget."""
        parent = widget.parent()
        if parent:
            return self.get_top_parent(parent)  # Continue up the chain
        return widget

    def rename_tab(self):
        """Rename the tab after editing is finished."""
        new_name = self.line_edit.text().strip()
        if new_name:
            self.setTabText(self.current_editing_index, new_name)
        self.line_edit.setHidden(True)  # Hide editor
        widget = self.get_top_parent(self)
        widget.datasets[self.current_editing_index].calc.plotsettings['dataName'] = new_name
        widget.redraw()
