"""HDF5 data logging for tensile test sessions."""

import h5py
import numpy as np
from datetime import datetime
from typing import Optional, Dict
import os


class HDF5Logger:
    """Manages HDF5 file logging for tensile test data."""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize logger.

        Args:
            base_dir: Base directory for data files
        """
        self.base_dir = base_dir
        self.file_path: Optional[str] = None
        self.file: Optional[h5py.File] = None
        self.session_group: Optional[h5py.Group] = None
        self.session_num = 0
        self.session_active = False

        # Create data directory if needed
        os.makedirs(base_dir, exist_ok=True)

        # Data buffers
        self.time_buffer = []
        self.ch0_voltage_buffer = []
        self.ch1_voltage_buffer = []
        self.force_buffer = []
        self.displacement_buffer = []
        self.stress_buffer = []
        self.strain_buffer = []

    def create_file(self, metadata: Optional[Dict] = None):
        """
        Create new HDF5 file with timestamp.

        Args:
            metadata: Optional metadata dictionary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(self.base_dir, f"tensile_test_{timestamp}.h5")

        self.file = h5py.File(self.file_path, 'w')

        # Store metadata
        if metadata:
            for key, value in metadata.items():
                self.file.attrs[key] = value

        self.file.attrs['creation_time'] = timestamp
        self.session_num = 0

        print(f"Created HDF5 file: {self.file_path}")

    def start_session(self, metadata: Optional[Dict] = None):
        """
        Start new session within the file.

        Args:
            metadata: Optional session metadata
        """
        if self.file is None:
            self.create_file()

        self.session_num += 1
        session_name = f"session_{self.session_num:03d}"
        self.session_group = self.file.create_group(session_name)

        # Store session metadata
        self.session_group.attrs['start_time'] = datetime.now().isoformat()
        if metadata:
            for key, value in metadata.items():
                self.session_group.attrs[key] = value

        # Create datasets (will be resizable)
        self.session_group.create_dataset(
            'time', (0,), maxshape=(None,), dtype='f8', chunks=True
        )

        # Raw data group
        raw_group = self.session_group.create_group('raw_data')
        raw_group.create_dataset('ch0_voltage', (0,), maxshape=(None,), dtype='f8', chunks=True)
        raw_group.create_dataset('ch1_voltage', (0,), maxshape=(None,), dtype='f8', chunks=True)

        # Processed data group
        proc_group = self.session_group.create_group('processed_data')
        proc_group.create_dataset('force_N', (0,), maxshape=(None,), dtype='f8', chunks=True)
        proc_group.create_dataset('displacement_mm', (0,), maxshape=(None,), dtype='f8', chunks=True)
        proc_group.create_dataset('stress_MPa', (0,), maxshape=(None,), dtype='f8', chunks=True)
        proc_group.create_dataset('strain', (0,), maxshape=(None,), dtype='f8', chunks=True)

        # Clear buffers
        self._clear_buffers()
        self.session_active = True

        print(f"Started session: {session_name}")

    def append_data(
        self,
        time: np.ndarray,
        ch0_voltage: np.ndarray,
        ch1_voltage: np.ndarray,
        force: np.ndarray,
        displacement: np.ndarray,
        stress: np.ndarray,
        strain: np.ndarray
    ):
        """
        Append data to current session.

        Args:
            time: Time array
            ch0_voltage: Channel 0 voltage
            ch1_voltage: Channel 1 voltage
            force: Force in N
            displacement: Displacement in mm
            stress: Stress in MPa
            strain: Strain (dimensionless)
        """
        if not self.session_active or self.session_group is None:
            return

        # Add to buffers
        self.time_buffer.extend(time)
        self.ch0_voltage_buffer.extend(ch0_voltage)
        self.ch1_voltage_buffer.extend(ch1_voltage)
        self.force_buffer.extend(force)
        self.displacement_buffer.extend(displacement)
        self.stress_buffer.extend(stress)
        self.strain_buffer.extend(strain)

        # Write to file every 100 samples
        if len(self.time_buffer) >= 100:
            self._flush_buffers()

    def _flush_buffers(self):
        """Write buffered data to HDF5 file."""
        if len(self.time_buffer) == 0:
            return

        # Convert buffers to arrays
        time_arr = np.array(self.time_buffer)
        ch0_arr = np.array(self.ch0_voltage_buffer)
        ch1_arr = np.array(self.ch1_voltage_buffer)
        force_arr = np.array(self.force_buffer)
        disp_arr = np.array(self.displacement_buffer)
        stress_arr = np.array(self.stress_buffer)
        strain_arr = np.array(self.strain_buffer)

        # Get current dataset sizes
        current_size = len(self.session_group['time'])
        new_size = current_size + len(time_arr)

        # Resize datasets
        self.session_group['time'].resize((new_size,))
        self.session_group['raw_data/ch0_voltage'].resize((new_size,))
        self.session_group['raw_data/ch1_voltage'].resize((new_size,))
        self.session_group['processed_data/force_N'].resize((new_size,))
        self.session_group['processed_data/displacement_mm'].resize((new_size,))
        self.session_group['processed_data/stress_MPa'].resize((new_size,))
        self.session_group['processed_data/strain'].resize((new_size,))

        # Append data
        self.session_group['time'][current_size:new_size] = time_arr
        self.session_group['raw_data/ch0_voltage'][current_size:new_size] = ch0_arr
        self.session_group['raw_data/ch1_voltage'][current_size:new_size] = ch1_arr
        self.session_group['processed_data/force_N'][current_size:new_size] = force_arr
        self.session_group['processed_data/displacement_mm'][current_size:new_size] = disp_arr
        self.session_group['processed_data/stress_MPa'][current_size:new_size] = stress_arr
        self.session_group['processed_data/strain'][current_size:new_size] = strain_arr

        # Flush to disk
        self.file.flush()

        # Clear buffers
        self._clear_buffers()

    def end_session(self, analysis_results: Optional[Dict] = None):
        """
        End current session and store analysis results.

        Args:
            analysis_results: Results from post-test analysis
        """
        if not self.session_active:
            return

        # Flush remaining data
        self._flush_buffers()

        # Store end time
        self.session_group.attrs['end_time'] = datetime.now().isoformat()

        # Store analysis results if provided
        if analysis_results and 'error' not in analysis_results:
            analysis_group = self.session_group.create_group('analysis')

            for region, data in analysis_results.items():
                region_group = analysis_group.create_group(region)
                for key, value in data.items():
                    region_group.attrs[key] = value

        self.session_active = False
        print(f"Ended session {self.session_num}")

    def close(self):
        """Close HDF5 file."""
        if self.file:
            self.file.close()
            self.file = None
            print("Closed HDF5 file")

    def _clear_buffers(self):
        """Clear all data buffers."""
        self.time_buffer = []
        self.ch0_voltage_buffer = []
        self.ch1_voltage_buffer = []
        self.force_buffer = []
        self.displacement_buffer = []
        self.stress_buffer = []
        self.strain_buffer = []
