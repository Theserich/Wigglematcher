from PyQt5.QtCore import pyqtSignal, QObject

class Signaller(QObject):
    signal = pyqtSignal()
    def __init__(self):
        super().__init__()

redrawSignal = Signaller()
