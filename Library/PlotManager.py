from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFileDialog, QColorDialog, QMessageBox
from PyQt5.QtCore import Qt
from numpy import log, where, zeros, arange, diff, split, inf, nanargmax
import matplotlib
from matplotlib.axis import Axis
matplotlib.use("Qt5Agg")


class PlotManager:
    def __init__(self, parent_widget, curve_manager, main_window=None):
        self.parent_widget = parent_widget
        self.main_window = main_window  # Reference to main window for toolbar
        self.curve_manager = curve_manager
        self.curves = curve_manager.curves
        self.overlap = 0.75 # Default colors
        # Plot data storage
        self.errorbarlines = []
        self.vlines = []
        self.ax = []
        self.initialize_plot()

    def initialize_plot(self):
        """Initialize the matplotlib plot with proper layout and styling"""
        # Set up widget background
        p = self.parent_widget.palette()
        p.setColor(self.parent_widget.backgroundRole(), Qt.white)
        self.parent_widget.setPalette(p)

        # Create layout
        self.plot_layout = QVBoxLayout(self.parent_widget)

        # Create figure and axes
        self.figure, ax = plt.subplots(1)
        self.ax.append(ax)
        self.ax.append(ax.twinx())  # Second y-axis
        self.figure.patch.set_facecolor('none')
        self.figure.patch.set_alpha(0.0)
        self.figure.subplots_adjust(
            left=0.08,  # Left margin
            bottom=0.08,  # Bottom margin
            right=0.92,  # Right margin
            top=0.95,  # Top margin
            hspace=0  # Keep existing horizontal spacing
        )

        # Make axes transparent
        for ax in self.ax:
            ax.patch.set_facecolor('none')
            ax.patch.set_alpha(0.0)

        # Create canvas
        self.canvas = FigureCanvas(self.figure)
        #self.canvas.setAutoFillBackground(False)
        #self.canvas.setAttribute(Qt.WA_OpaquePaintEvent, False)
        #self.canvas.setAttribute(Qt.WA_NoSystemBackground, True)
        self.parent_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.parent_widget.setStyleSheet("background-color: transparent;")

        # Configure axes styling
        self._setup_axes_styling()

        # Add toolbar and canvas to layout
        self.toolbar = NavigationToolbar(self.canvas, self.parent_widget)
        
        # Add toolbar to main window if available, otherwise to layout
        if self.main_window and hasattr(self.main_window, 'addToolBar'):
            self.main_window.addToolBar(Qt.BottomToolBarArea, self.toolbar)
        else:
            self.plot_layout.addWidget(self.toolbar)
        self.plot_layout.addWidget(self.canvas)

    def _setup_axes_styling(self):
        """Configure the styling for both axes"""
        self.figure.subplots_adjust(hspace=-1)

        # Configure left axis (F14C/Age)
        self.ax[0].set_facecolor('none')
        self.ax[0].tick_params(axis='x', which='both', bottom=False)
        self.ax[0].set_ylabel('F$^{14}$C')
        self.ax[0].spines['bottom'].set_visible(False)

        # Configure right axis (Probability)
        self.ax[1].set_facecolor('none')
        self.ax[1].set_xlabel('calendaryear')
        self.ax[1].set_ylabel('probability density')
        self.ax[1].yaxis.set_label_position('right')
        self.ax[1].yaxis.tick_right()
        self.ax[1].spines['top'].set_visible(False)

    def clear_plot_elements(self):
        """Clear all plot elements before redrawing"""
        # Remove legend
        legend = self.ax[0].get_legend()
        if legend is not None:
            legend.remove()

        # Clear error bar lines
        for errorbar in self.errorbarlines:
            errorbar.set_label(None)
        self.errorbarlines = []

        # Remove vertical lines
        for vline in self.vlines:
            vline.remove()
        self.vlines = []

        # Clear all plot elements from both axes
        for ax in self.ax:
            # Remove lines
            for line in ax.lines[:]:
                try:
                    line.remove()
                except ValueError:
                    pass

            # Remove collections (fill_between, scatter, etc.)
            for collection in ax.collections[:]:
                try:
                    collection.remove()
                except ValueError:
                    pass

            # Remove containers (bar plots, error bars, etc.)
            for container in ax.containers[:]:
                for artist in list(container):
                    if isinstance(artist, tuple):
                        for item in artist:
                            try:
                                item.remove()
                            except ValueError:
                                pass
                    else:
                        try:
                            artist.remove()
                        except ValueError:
                            pass


    def plot_datasets(self, datasets):
        """Plot all datasets with error bars and probability distributions"""
        self.clear_plot_elements()

        # Initialize bounds
        maxy = -inf
        miny = inf

        # Plot error bars
        for data in datasets.get('errorbar', []):
            errorbar_plot = self.ax[0].errorbar(
                data['x'], data['y'], data['yerr'],
                label=data['label'], color=data['color'],
                fmt='x', alpha=0.8
            )
            self.errorbarlines.append(errorbar_plot)

        # Plot filled areas on left axis (calibration curves)
        for data in datasets.get('ax0fill', []):
            self.ax[0].fill_between(
                data['x'], data['y0'], data['y1'],
                label=data['label'], color=data['color'],
                alpha=0.6, lw=0
            )

        # Plot filled areas on right axis (probability distributions)
        for data in datasets.get('ax1fill', []):
            if max(data['y1']) > maxy:
                maxy = max(data['y1'])
            if min(data['y0']) < miny:
                miny = min(data['y0'])
            self.ax[1].fill_between(
                data['x'], data['y0'], data['y1'],
                label=data['label'], color=data['color'],
                alpha=0.6, lw=0
            )
        self.minx = datasets['minx']
        self.maxx = datasets['maxx']
        self.miny = datasets['miny']
        self.maxy = datasets['maxy']
        try:
            self.ax[1].set_xlim(left=self.minx, right=self.maxx)
        except:
            pass
        try:
            self.ax[0].set_ylim(bottom=self.miny, top=self.maxy)
        except:
            pass
        try:
            self.ax[1].set_ylim(bottom=0, top=maxy)
        except:
            pass
        self.overlap = 0.75
        ylim = self.ax[0].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[0].set_ylim(bottom=ylim[0] - dy * self.overlap, top=ylim[1])
        ylim = self.ax[1].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[1].set_ylim(bottom=ylim[0], top=ylim[1] + dy * self.overlap)
        dy = ylim[1] - ylim[0]
        self.ax[1].set_ylim(bottom=ylim[0], top=ylim[1] + dy * self.overlap)
        dy = ylim[1] + dy * self.overlap
        for data in datasets['lines']:
            self.ax[1].plot(data['x'], -0.01 * dy - 0.02 * data['y'] * dy, label=data['label'], color=data['color'],
                            lw=5, alpha=0.4)
        self.ax[1].set_ylim(bottom=-0.05 * dy)
        for data in datasets['axvline']:
            vline = self.ax[1].axvline(data['x'], ymax=data['ymax'], label=data['label'],color=data['color'])
            self.vlines.append(vline)
        if datasets['ageplot']:
            self.ax[0].set_ylabel('$^{14}$C age in years')
        else:
            self.ax[0].set_ylabel('F$^{14}$C')
        #self.setBounds()
        self.canvas.draw_idle()


    def setBounds(self):
        ax = self.ax
        n = len(ax)

        xlim = ax[0].get_xlim()
        xticks = ax[0].get_xticks()
        for i, x in enumerate(ax):
            ticks = x.get_yticks()
            dticks = ticks[1] - ticks[0]
            maxy = max(ticks)
            miny = min(ticks)
            dy = maxy - miny
            nonscaletotheight = n * dy
            totheight = nonscaletotheight - (n - 1) * self.overlap * dy
            top = maxy + i * (1 - self.overlap) * dy
            bottom = top - totheight
            ylabelheight = (miny - bottom + dy / 2) / totheight
            labelheight = (miny + 0.8 * dy - bottom) / totheight
            if i % 2 == 0:
                x.yaxis.tick_left()
                x.spines['left'].set_bounds((ticks[1], ticks[-2]))
                x.spines['right'].set_visible(False)
                Axis.set_label_coords(x.yaxis, 1.07, ylabelheight)
            else:
                x.yaxis.tick_right()
                x.spines['right'].set_bounds((ticks[1], ticks[-2]))
                x.spines['left'].set_visible(False)
                Axis.set_label_coords(x.yaxis, 1 + 0.05, ylabelheight)
            x.set_ylim(top=top, bottom=bottom)
            x.set_yticks(ticks[1:-1])
            x.spines['top'].set_visible(False)
            if i == 0:
                x.spines['bottom'].set_bounds((xticks[1], xticks[-2]))
            else:
                x.spines['bottom'].set_visible(False)


