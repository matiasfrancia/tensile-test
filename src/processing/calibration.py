"""Calibration and unit conversion for sensors."""

import numpy as np


class SensorCalibration:
    """Handles voltage to engineering unit conversions."""

    def __init__(self, slope: float, offset: float, unit: str = ""):
        """
        Initialize calibration.

        Args:
            slope: Conversion factor (units per volt)
            offset: Offset in engineering units
            unit: Unit name (e.g., "N", "mm")
        """
        self.slope = slope
        self.offset = offset
        self.unit = unit

    def convert(self, voltage: np.ndarray) -> np.ndarray:
        """Convert voltage to engineering units."""
        return voltage * self.slope + self.offset

    def inverse(self, value: np.ndarray) -> np.ndarray:
        """Convert engineering units back to voltage."""
        return (value - self.offset) / self.slope


class CalibrationManager:
    """Manages all sensor calibrations."""

    def __init__(self, config: dict):
        """
        Initialize from config dictionary.

        Args:
            config: Configuration dict with calibration parameters
        """
        # Load cell calibration (voltage -> force in N)
        load_config = config['calibration']['load_cell']
        self.load_cell = SensorCalibration(
            slope=load_config['slope'],
            offset=load_config['offset'],
            unit='N'
        )

        # Displacement calibration (voltage -> displacement in mm)
        disp_config = config['calibration']['displacement']
        self.displacement = SensorCalibration(
            slope=disp_config['slope'],
            offset=disp_config['offset'],
            unit='mm'
        )

    def convert_load(self, voltage: np.ndarray) -> np.ndarray:
        """Convert load cell voltage to force (N)."""
        return self.load_cell.convert(voltage)

    def convert_displacement(self, voltage: np.ndarray) -> np.ndarray:
        """Convert displacement sensor voltage to displacement (mm)."""
        return self.displacement.convert(voltage)
