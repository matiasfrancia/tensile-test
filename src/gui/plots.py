"""Plot widgets for real-time data visualization."""

import pyqtgraph as pg
import numpy as np
from typing import Optional


class RealTimePlot:
    """Base class for real-time plots with auto-scaling."""

    def __init__(self, title: str, xlabel: str, ylabel: str):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle(title, color='k', size='12pt')
        self.plot_widget.setLabel('bottom', xlabel, color='k')
        self.plot_widget.setLabel('left', ylabel, color='k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Set axis colors to black
        self.plot_widget.getAxis('bottom').setPen('k')
        self.plot_widget.getAxis('left').setPen('k')

        # Create plot curve
        self.curve = self.plot_widget.plot(pen=pg.mkPen('b', width=2))

        # Data storage
        self.x_data = np.array([])
        self.y_data = np.array([])

        # Region markers
        self.region_lines = []
        self.region_labels = []

    def update(self, x: np.ndarray, y: np.ndarray):
        """Update plot with new data."""
        self.x_data = x
        self.y_data = y
        self.curve.setData(self.x_data, self.y_data)

    def clear(self):
        """Clear plot data."""
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.curve.setData(self.x_data, self.y_data)
        self._clear_markers()

    def add_vertical_marker(self, x_pos: float, color: str = 'r', label: str = ""):
        """Add vertical line marker at x position."""
        line = pg.InfiniteLine(
            pos=x_pos,
            angle=90,
            pen=pg.mkPen(color, width=2, style=pg.QtCore.Qt.PenStyle.DashLine)
        )
        self.plot_widget.addItem(line)
        self.region_lines.append(line)

        if label:
            text = pg.TextItem(label, color=color, anchor=(0, 1))
            text.setPos(x_pos, self.plot_widget.viewRange()[1][1])
            self.plot_widget.addItem(text)
            self.region_labels.append(text)

    def _clear_markers(self):
        """Remove all markers."""
        for line in self.region_lines:
            self.plot_widget.removeItem(line)
        for label in self.region_labels:
            self.plot_widget.removeItem(label)
        self.region_lines = []
        self.region_labels = []


class ForcePlot(RealTimePlot):
    """Force vs Time plot."""

    def __init__(self):
        super().__init__(
            title="Load vs Time",
            xlabel="Time (s)",
            ylabel="Force (N)"
        )


class DisplacementPlot(RealTimePlot):
    """Displacement vs Time plot."""

    def __init__(self):
        super().__init__(
            title="Deformation vs Time",
            xlabel="Time (s)",
            ylabel="Displacement (mm)"
        )


class StressStrainPlot(RealTimePlot):
    """Stress-Strain curve plot."""

    def __init__(self):
        super().__init__(
            title="Stress-Strain Curve",
            xlabel="Strain",
            ylabel="Stress (MPa)"
        )

    def add_region_markers(self, analysis_results: dict, strain: np.ndarray):
        """Add markers for different test regions."""
        self._clear_markers()

        if 'elastic' in analysis_results:
            idx = analysis_results['elastic']['end_index']
            if idx < len(strain):
                self.add_vertical_marker(strain[idx], 'g', "Elastic Limit")

        if 'yield' in analysis_results and analysis_results['yield']['index'] is not None:
            yield_strain = analysis_results['yield']['strain']
            self.add_vertical_marker(yield_strain, 'orange', "Yield")

        if 'ultimate' in analysis_results:
            idx = analysis_results['ultimate']['index']
            if idx < len(strain):
                self.add_vertical_marker(strain[idx], 'r', "UTS")

        if 'fracture' in analysis_results:
            idx = analysis_results['fracture']['index']
            if idx < len(strain):
                self.add_vertical_marker(strain[idx], 'purple', "Fracture")


class YoungsModulusPlot(RealTimePlot):
    """Young's Modulus vs Time plot."""

    def __init__(self):
        super().__init__(
            title="Young's Modulus vs Time",
            xlabel="Time (s)",
            ylabel="Young's Modulus (GPa)"
        )

    def update(self, x: np.ndarray, y: np.ndarray):
        """Update plot, filtering out NaN values."""
        # Only plot non-NaN values
        mask = ~np.isnan(y)
        if np.any(mask):
            super().update(x[mask], y[mask])
