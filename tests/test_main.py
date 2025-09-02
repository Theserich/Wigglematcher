import pytest
from src.MainWindow import WidgetMain

@pytest.fixture
def app(qtbot):
    """Fixture that provides the application instance."""
    test_app = WidgetMain()
    qtbot.addWidget(test_app)
    return test_app

def test_button_click(app, qtbot):
    """Test the button click functionality."""
    button = app.button

    # Assert initial button text
    assert button.text() == "Click Me"

    # Simulate button click
    qtbot.mouseClick(button, qtbot.LeftButton)

    # Assert button text after click
    assert button.text() == "Clicked!"
