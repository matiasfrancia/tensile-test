"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSplitter
)
from PyQt6.QtCore import QTimer, Qt
import numpy as np
import yaml
from typing import Optional

from ..acquisition.mcc_daq import MCCDataAcquisition
from ..processing.calibration import CalibrationManager
from ..processing.mechanics import MechanicsCalculator
from ..processing.analysis import RegionAnalysis
from ..logging.hdf5_logger import HDF5Logger
from ..utils.buffers import RollingBuffer
from .plots import ForcePlot, DisplacementPlot, StressStrainPlot, YoungsModulusPlot
from .controls import ControlPanel, MetricsDisplay


class MainWindow(QMainWindow):
    """Main application window for tensile testing platform."""

    def __init__(self, config_path: str):
        super().__init__()

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize components
        self.calibration = CalibrationManager(self.config)
        self.mechanics = MechanicsCalculator(
            cross_section_area=self.config['specimen']['cross_section_area'],
            gauge_length=self.config['specimen']['gauge_length']
        )
        self.analysis = RegionAnalysis()
        self.logger = HDF5Logger()

        # Initialize DAQ
        acq_config = self.config['acquisition']
        self.daq = MCCDataAcquisition(
            board_num=acq_config['board_num'],
            low_chan=acq_config['channels']['load'],
            high_chan=acq_config['channels']['displacement'],
            sample_rate=acq_config['sample_rate'],
            buffer_size=acq_config['buffer_size'],
            voltage_range=acq_config['voltage_range']
        )
        self.daq.set_data_callback(self._on_new_data)

        # Data storage
        display_time = 120  # 120 seconds display window
        buffer_size = acq_config['sample_rate'] * display_time
        self.display_buffer = RollingBuffer(maxlen=buffer_size)

        # Full session data (for analysis)
        self.session_time = []
        self.session_ch0 = []
        self.session_ch1 = []
        self.session_force = []
        self.session_displacement = []
        self.session_stress = []
        self.session_strain = []
        self.session_youngs = []

        self._init_ui()

        # Update timer for GUI refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_plots)
        self.update_timer.start(50)  # 20 Hz update rate

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Tensile Testing Platform")
        self.setGeometry(100, 100, 1600, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left side: plots
        plot_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top row plots
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        self.force_plot = ForcePlot()
        self.displacement_plot = DisplacementPlot()
        top_layout.addWidget(self.force_plot.plot_widget)
        top_layout.addWidget(self.displacement_plot.plot_widget)

        # Bottom row plots
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        self.stress_strain_plot = StressStrainPlot()
        self.youngs_plot = YoungsModulusPlot()
        bottom_layout.addWidget(self.stress_strain_plot.plot_widget)
        bottom_layout.addWidget(self.youngs_plot.plot_widget)

        plot_splitter.addWidget(top_widget)
        plot_splitter.addWidget(bottom_widget)

        # Right side: controls and metrics
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        self.control_panel = ControlPanel()
        self.control_panel.start_clicked.connect(self._on_start)
        self.control_panel.stop_clicked.connect(self._on_stop)
        self.control_panel.analyze_clicked.connect(self._on_analyze)

        self.metrics_display = MetricsDisplay()

        right_layout.addWidget(self.control_panel)
        right_layout.addWidget(self.metrics_display)

        # Add to main layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(plot_splitter)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 3)  # Plots take 75% of width
        main_splitter.setStretchFactor(1, 1)  # Controls take 25%

        main_layout.addWidget(main_splitter)

    def _on_start(self):
        """Handle start button click."""
        # Clear previous data
        self.display_buffer.clear()
        self.session_time = []
        self.session_ch0 = []
        self.session_ch1 = []
        self.session_force = []
        self.session_displacement = []
        self.session_stress = []
        self.session_strain = []
        self.session_youngs = []

        # Clear plots
        self.force_plot.clear()
        self.displacement_plot.clear()
        self.stress_strain_plot.clear()
        self.youngs_plot.clear()
        self.metrics_display.clear_analysis()

        # Start logger session
        metadata = {
            'material': self.config['specimen'].get('material', 'Unknown'),
            'cross_section_area_mm2': self.config['specimen']['cross_section_area'],
            'gauge_length_mm': self.config['specimen']['gauge_length'],
            'sample_rate_Hz': self.config['acquisition']['sample_rate']
        }
        self.logger.start_session(metadata)

        # Start acquisition
        self.daq.start()
        self.control_panel.set_running_state(True)

    def _on_stop(self):
        """Handle stop button click."""
        # Stop acquisition
        self.daq.stop()
        self.control_panel.set_running_state(False)

        # End logger session (will be analyzed later if user clicks analyze)
        self.logger.end_session()

    def _on_analyze(self):
        """Handle analyze button click - perform post-test analysis."""
        if len(self.session_stress) < 50:
            self.metrics_display.analysis_text.setText("Insufficient data for analysis")
            return

        # Convert to numpy arrays
        stress = np.array(self.session_stress)
        strain = np.array(self.session_strain)
        force = np.array(self.session_force)

        # Perform analysis
        results = self.analysis.analyze(stress, strain, force)

        # Display results
        self.metrics_display.update_analysis_results(results)

        # Add markers to stress-strain plot
        if 'error' not in results:
            self.stress_strain_plot.add_region_markers(results, strain)

    def _on_new_data(self, time: np.ndarray, ch0: np.ndarray, ch1: np.ndarray):
        """
        Callback for new data from DAQ.

        Args:
            time: Time array
            ch0: Channel 0 voltage (load cell)
            ch1: Channel 1 voltage (displacement)
        """
        # Convert to engineering units
        force = self.calibration.convert_load(ch0)
        displacement = self.calibration.convert_displacement(ch1)

        # Calculate stress and strain
        stress = self.mechanics.calculate_stress(force)
        strain = self.mechanics.calculate_strain(displacement)

        # Calculate Young's modulus (rolling)
        if len(self.session_stress) > 0:
            combined_stress = np.concatenate([self.session_stress, stress])
            combined_strain = np.concatenate([self.session_strain, strain])
            youngs = self.mechanics.calculate_youngs_modulus(
                combined_stress, combined_strain, window_size=100
            )
            # Only keep the new values
            youngs = youngs[-len(stress):]
        else:
            youngs = np.full(len(stress), np.nan)

        # Store in session data
        self.session_time.extend(time)
        self.session_ch0.extend(ch0)
        self.session_ch1.extend(ch1)
        self.session_force.extend(force)
        self.session_displacement.extend(displacement)
        self.session_stress.extend(stress)
        self.session_strain.extend(strain)
        self.session_youngs.extend(youngs)

        # Update display buffer
        self.display_buffer.extend(time, force, displacement)

        # Log data
        self.logger.append_data(
            time, ch0, ch1, force, displacement, stress, strain
        )

    def _update_plots(self):
        """Update all plots with current data (called by timer)."""
        if len(self.session_time) == 0:
            return

        # Get display buffer data
        time, force, displacement = self.display_buffer.get_arrays()

        if len(time) > 0:
            # Update time-series plots
            self.force_plot.update(time, force)
            self.displacement_plot.update(time, displacement)

        # Update stress-strain and Young's modulus with session data
        if len(self.session_stress) > 0:
            stress_arr = np.array(self.session_stress)
            strain_arr = np.array(self.session_strain)
            time_arr = np.array(self.session_time)
            youngs_arr = np.array(self.session_youngs)

            self.stress_strain_plot.update(strain_arr, stress_arr)
            self.youngs_plot.update(time_arr, youngs_arr)

            # Update real-time metrics
            current_idx = -1
            youngs_val = youngs_arr[current_idx] if not np.isnan(youngs_arr[current_idx]) else None

            self.metrics_display.update_realtime_metrics(
                current_force=self.session_force[current_idx],
                current_displacement=self.session_displacement[current_idx],
                current_stress=stress_arr[current_idx],
                current_strain=strain_arr[current_idx],
                youngs_modulus=youngs_val
            )

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop acquisition if running
        if self.daq.is_running():
            self.daq.stop()

        # Close logger
        self.logger.close()

        event.accept()
