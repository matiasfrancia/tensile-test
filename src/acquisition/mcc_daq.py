"""MCC USB-1608FS data acquisition interface."""

import threading
import time
import numpy as np
from typing import Optional, Callable
try:
    from mcculw import ul
    from mcculw.enums import ScanOptions, FunctionType, Status, ULRange
    from mcculw.ul import ULError
    MCC_AVAILABLE = True
except ImportError:
    MCC_AVAILABLE = False
    print("WARNING: mcculw not available. Running in simulation mode.")


class MCCDataAcquisition:
    """Manages continuous data acquisition from MCC USB-1608FS."""

    def __init__(
        self,
        board_num: int = 0,
        low_chan: int = 0,
        high_chan: int = 1,
        sample_rate: int = 1000,
        buffer_size: int = 5000,
        voltage_range: float = 10.0
    ):
        """
        Initialize MCC DAQ.

        Args:
            board_num: Board number (default 0)
            low_chan: First channel to scan
            high_chan: Last channel to scan
            sample_rate: Sampling rate in Hz per channel
            buffer_size: Size of circular buffer in samples
            voltage_range: Voltage range (±V)
        """
        if not MCC_AVAILABLE:
            print("Running in SIMULATION mode - no real DAQ")

        self.board_num = board_num
        self.low_chan = low_chan
        self.high_chan = high_chan
        self.num_channels = high_chan - low_chan + 1
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.total_count = buffer_size * self.num_channels

        # Set voltage range
        if MCC_AVAILABLE:
            if voltage_range == 10.0:
                self.ul_range = ULRange.BIP10VOLTS
            elif voltage_range == 5.0:
                self.ul_range = ULRange.BIP5VOLTS
            elif voltage_range == 2.0:
                self.ul_range = ULRange.BIP2VOLTS
            else:
                self.ul_range = ULRange.BIP10VOLTS
        else:
            self.ul_range = None

        self.memhandle = None
        self.running = False
        self.thread = None
        self.prev_count = 0
        self.prev_index = 0
        self.data_callback: Optional[Callable] = None

        # Simulation mode variables
        self.sim_time = 0.0
        self.sim_counter = 0

    def set_data_callback(self, callback: Callable):
        """Set callback function for new data. Callback signature: callback(time, ch0_data, ch1_data)"""
        self.data_callback = callback

    def start(self):
        """Start continuous acquisition in background thread."""
        if self.running:
            print("Acquisition already running")
            return

        if MCC_AVAILABLE:
            # Allocate buffer
            self.memhandle = ul.scaled_win_buf_alloc(self.total_count)

            # Configure scan options
            scan_options = (
                ScanOptions.BACKGROUND |
                ScanOptions.CONTINUOUS |
                ScanOptions.SCALEDATA
            )

            # Start background scan
            ul.a_in_scan(
                self.board_num,
                self.low_chan,
                self.high_chan,
                self.total_count,
                self.sample_rate,
                self.ul_range,
                self.memhandle,
                scan_options
            )

        self.running = True
        self.prev_count = 0
        self.prev_index = 0
        self.sim_time = 0.0
        self.sim_counter = 0

        # Start monitoring thread
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()
        print(f"Acquisition started: {self.sample_rate} Hz, {self.num_channels} channels")

    def stop(self):
        """Stop acquisition and free resources."""
        if not self.running:
            return

        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        if MCC_AVAILABLE and self.memhandle:
            try:
                ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
                ul.win_buf_free(self.memhandle)
            except ULError as e:
                print(f"Error stopping acquisition: {e}")

        self.memhandle = None
        print("Acquisition stopped")

    def _acquisition_loop(self):
        """Background thread that monitors buffer and extracts data."""
        while self.running:
            if MCC_AVAILABLE:
                self._process_real_data()
            else:
                self._process_simulated_data()

            time.sleep(0.05)  # 20 Hz monitoring rate

    def _process_real_data(self):
        """Extract new data from MCC circular buffer."""
        try:
            # Get current status
            status, curr_count, curr_index = ul.get_status(
                self.board_num, FunctionType.AIFUNCTION
            )

            # Calculate new data count
            new_data_count = curr_count - self.prev_count

            if new_data_count > 0:
                # Check for buffer overrun
                if new_data_count > self.buffer_size * self.num_channels:
                    print(f"WARNING: Buffer overrun! Lost {new_data_count - self.buffer_size} samples")
                    new_data_count = self.buffer_size * self.num_channels

                # Extract data from buffer
                data_array = ul.scaled_win_buf_to_array(self.memhandle)

                # Calculate sample count per channel
                samples_per_chan = new_data_count // self.num_channels

                if samples_per_chan > 0:
                    # Extract data for each channel
                    ch0_data = []
                    ch1_data = []

                    for i in range(samples_per_chan):
                        index = (self.prev_index + i * self.num_channels) % len(data_array)
                        ch0_data.append(data_array[index])
                        ch1_data.append(data_array[index + 1])

                    ch0_data = np.array(ch0_data)
                    ch1_data = np.array(ch1_data)

                    # Generate time array
                    start_sample = self.prev_count // self.num_channels
                    time_array = (start_sample + np.arange(samples_per_chan)) / self.sample_rate

                    # Call callback
                    if self.data_callback:
                        self.data_callback(time_array, ch0_data, ch1_data)

                    # Update tracking
                    self.prev_count = curr_count
                    self.prev_index = (self.prev_index + new_data_count) % len(data_array)

        except ULError as e:
            print(f"Error reading data: {e}")
            self.running = False

    def _process_simulated_data(self):
        """Generate simulated data for testing without hardware."""
        # Generate 50 samples at a time (50ms at 1kHz)
        samples = 50
        dt = 1.0 / self.sample_rate

        time_array = self.sim_time + np.arange(samples) * dt

        # Simulate tensile test: increasing load and displacement
        # Simple ramp with some noise
        ch0_data = (self.sim_counter / 100.0) + np.random.normal(0, 0.01, samples)  # Load
        ch1_data = (self.sim_counter / 200.0) + np.random.normal(0, 0.005, samples)  # Displacement

        self.sim_time += samples * dt
        self.sim_counter += samples

        # Call callback
        if self.data_callback:
            self.data_callback(time_array, ch0_data, ch1_data)

    def is_running(self) -> bool:
        """Check if acquisition is running."""
        return self.running
