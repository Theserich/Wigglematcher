from sys import argv, exit
from PyQt5.QtWidgets import QApplication
from Library.MainWindow import WidgetMain
from pyqtgraph.Qt import QtCore
from pathlib import Path
import matplotlib
import faulthandler
faulthandler.enable()
matplotlib.use("Qt5Agg")
from Library.EditableTabWidget import EditableTabWidget
#
if __name__ == '__main__':
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(argv)
        widget = WidgetMain(Path('Library/UIFiles/MainWindow.ui'))
        widget.show()
        #app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        # Set the application to use high DPI scaling
        #app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        app.setStyle('Fusion')
        exit(app.exec_())
    except Exception as e:
        print(f"\n An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
