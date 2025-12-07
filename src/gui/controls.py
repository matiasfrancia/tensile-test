"""Control widgets for the application."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Optional, Dict


class ControlPanel(QWidget):
    """Main control panel with start/stop/analyze buttons."""

    # Signals
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Session controls group
        session_group = QGroupBox("Session Control")
        session_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Test")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.start_btn.clicked.connect(self.start_clicked.emit)

        self.stop_btn = QPushButton("Stop Test")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.stop_btn.setEnabled(False)

        session_layout.addWidget(self.start_btn)
        session_layout.addWidget(self.stop_btn)
        session_group.setLayout(session_layout)

        # Analysis controls group
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("Analyze Results")
        self.analyze_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        self.analyze_btn.clicked.connect(self.analyze_clicked.emit)
        self.analyze_btn.setEnabled(False)

        analysis_layout.addWidget(self.analyze_btn)
        analysis_group.setLayout(analysis_layout)

        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")

        layout.addWidget(session_group)
        layout.addWidget(analysis_group)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.setLayout(layout)

    def set_running_state(self, running: bool):
        """Update button states based on acquisition state."""
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.analyze_btn.setEnabled(not running)

        if running:
            self.status_label.setText("Status: Acquiring...")
            self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: green; }")
        else:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; color: red; }")


class MetricsDisplay(QWidget):
    """Display for calculated metrics."""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Real-time metrics
        rt_group = QGroupBox("Real-Time Metrics")
        self.rt_text = QTextEdit()
        self.rt_text.setReadOnly(True)
        self.rt_text.setMaximumHeight(150)
        rt_layout = QVBoxLayout()
        rt_layout.addWidget(self.rt_text)
        rt_group.setLayout(rt_layout)

        # Analysis results
        analysis_group = QGroupBox("Analysis Results")
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(250)
        analysis_layout = QVBoxLayout()
        analysis_layout.addWidget(self.analysis_text)
        analysis_group.setLayout(analysis_layout)

        layout.addWidget(rt_group)
        layout.addWidget(analysis_group)

        self.setLayout(layout)

    def update_realtime_metrics(
        self,
        current_force: float,
        current_displacement: float,
        current_stress: float,
        current_strain: float,
        youngs_modulus: Optional[float] = None
    ):
        """Update real-time metrics display."""
        text = f"""
Current Force: {current_force:.2f} N
Current Displacement: {current_displacement:.3f} mm
Current Stress: {current_stress:.2f} MPa
Current Strain: {current_strain:.4f}
"""
        if youngs_modulus is not None and not np.isnan(youngs_modulus):
            text += f"Young's Modulus: {youngs_modulus:.2f} GPa\n"

        self.rt_text.setText(text)

    def update_analysis_results(self, results: Dict):
        """Update analysis results display."""
        if 'error' in results:
            self.analysis_text.setText(f"Error: {results['error']}")
            return

        text = "=== ANALYSIS RESULTS ===\n\n"

        if 'elastic' in results:
            elastic = results['elastic']
            text += f"ELASTIC REGION:\n"
            text += f"  Young's Modulus: {elastic['youngs_modulus_GPa']:.2f} GPa\n"
            text += f"  R²: {elastic['r_squared']:.4f}\n\n"

        if 'yield' in results:
            yield_data = results['yield']
            if yield_data['stress_MPa'] is not None:
                text += f"YIELD POINT:\n"
                text += f"  Stress: {yield_data['stress_MPa']:.2f} MPa\n"
                text += f"  Strain: {yield_data['strain']:.4f}\n\n"

        if 'ultimate' in results:
            uts = results['ultimate']
            text += f"ULTIMATE TENSILE STRENGTH:\n"
            text += f"  Stress: {uts['stress_MPa']:.2f} MPa\n"
            text += f"  Strain: {uts['strain']:.4f}\n\n"

        if 'fracture' in results:
            fracture = results['fracture']
            text += f"FRACTURE:\n"
            text += f"  Stress: {fracture['stress_MPa']:.2f} MPa\n"
            text += f"  Strain: {fracture['strain']:.4f}\n\n"

        if 'plastic' in results:
            plastic = results['plastic']
            text += f"PLASTIC REGION:\n"
            text += f"  Strain Range: {plastic['strain_range']:.4f}\n"

        self.analysis_text.setText(text)

    def clear_analysis(self):
        """Clear analysis results."""
        self.analysis_text.clear()


# Import numpy for the metrics display
import numpy as np
