# Data Visualization Application

A PyQt5-based desktop application for data visualization and analysis with interactive plotting capabilities.

## Features

- Interactive data plotting using PyQtGraph and Matplotlib
- Tabbed interface with editable tabs
- Data management and manipulation
- Excel data import/export functionality
- Customizable plot curves and visualization
- High DPI display support
- Modern Fusion UI style

## Requirements

- Python 3.13.0+
- PyQt5
- PyQtGraph
- Matplotlib
- Additional dependencies listed in requirements.txt

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:
```bash
python main.py
```
.
├── main.py                 # Main application entry point
├── Library/                # Core application modules
│   ├── MainWindow.py      # Main application window
│   ├── EditableTabWidget.py # Custom tab widget implementation
│   ├── PLotWindow.py      # Plot window functionality
│   ├── tableView.py       # Data table view components
│   ├── dataMager.py       # Data management utilities
│   ├── ExcelWorker.py     # Excel file handling
│   ├── CurveManager.py    # Plot curve management
│   ├── UIFiles/           # UI definition files
│   ├── Data/              # Data storage
│   ├── Settings/          # Application settings
│   └── SaveFolder/        # Save directory
├── tests/                 # Test files
└── pytest.ini            # Pytest configuration