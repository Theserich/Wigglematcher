from PyQt5.QtWidgets import QAction, QTableWidget, QApplication



class CopySelectedCellsAction(QAction):
	def __init__(self, widget):
		super(CopySelectedCellsAction, self).__init__("Copy", widget)
		self.setShortcut('Ctrl+C')
		self.triggered.connect(self.copy_cells_to_clipboard)
		self.table_widget = widget.tableView


	def copy_cells_to_clipboard(self):
		table_widget = self.table_widget
		if len(table_widget.selectionModel().selectedIndexes()) > 0:
			# sort select indexes into rows and columns
			previous = table_widget.selectionModel().selectedIndexes()[0]
			columns = []
			rows = []
			for index in table_widget.selectionModel().selectedIndexes():
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
					print(r,c)
					clipboard += str(columns[r][c])
					if c != (ncols-1):
						clipboard += '\t'
				if r != (nrows - 1):
					clipboard += '\n'
			# copy to the system clipboard
			sys_clip = QApplication.clipboard()
			sys_clip.setText(clipboard)

def copy_cells_to_clipboard(table):
	if len(table.selectionModel().selectedIndexes()) > 0:
		# sort select indexes into rows and columns
		previous = table.selectionModel().selectedIndexes()[0]
		columns = []
		rows = []
		for index in table.selectionModel().selectedIndexes():
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
				if c != (ncols -1):
					clipboard += '\t'
			if r != (nrows - 1):
				clipboard += '\n'
		# copy to the system clipboard
		sys_clip = QApplication.clipboard()
		sys_clip.setText(clipboard)