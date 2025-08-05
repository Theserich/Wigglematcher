import sys
from PyQt5.QtWidgets import QApplication, QWidget, QRadioButton, QVBoxLayout, QLabel

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QRadioButton Click Example")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        self.label = QLabel("Select an option:")

        self.radio1 = QRadioButton("Option 1")
        self.radio2 = QRadioButton("Option 2")

        # Connect the toggled signals
        self.radio1.toggled.connect(self.on_radio_button_toggled)
        self.radio2.toggled.connect(self.on_radio_button_toggled)

        layout.addWidget(self.label)
        layout.addWidget(self.radio1)
        layout.addWidget(self.radio2)

        self.setLayout(layout)

    def on_radio_button_toggled(self):
        # Check which radio button is checked
        print('asdasd')
        if self.radio1.isChecked():
            self.label.setText("Option 1 selected")
        elif self.radio2.isChecked():
            self.label.setText("Option 2 selected")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
