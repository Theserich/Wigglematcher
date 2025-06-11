import pytest
from unittest.mock import patch, mock_open, MagicMock
from Library.CurveManager import CurveManager
import json
import numpy as np

# Sample JSON data structure that resembles your curve files
mock_curve_data = {
    "calendaryear": [1000, 1010, 1020],
    "bp": [950, 940, 930],
    "fm": [0.95, 0.94, 0.93],
    "fm_sig": [0.01, 0.01, 0.01]
}

@pytest.fixture
def mock_curve_files(tmp_path):
    """Create a temporary curve file."""
    folder = tmp_path / "Library" / "Data" / "Curves"
    folder.mkdir(parents=True)
    filepath = folder / "intcal20.json"
    with open(filepath, "w") as f:
        json.dump(mock_curve_data, f)
    return str(tmp_path)

@patch("Library.CurveManager.pathlib.Path.glob")
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(mock_curve_data))
def test_load_all_curves(mock_file, mock_glob):
    # Setup: simulate the presence of one .json file
    fake_file = MagicMock()
    fake_file.stem = "intcal20"
    mock_glob.return_value = [fake_file]

    cm = CurveManager()

    assert "intcal20" in cm.data
    assert isinstance(cm.data["intcal20"]["bp"], np.ndarray)
    assert cm.data["intcal20"]["bp"][0] == 950
