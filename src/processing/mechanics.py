"""Mechanical property calculations for tensile testing."""

import numpy as np
from scipy import stats


class MechanicsCalculator:
    """Calculates stress, strain, and mechanical properties."""

    def __init__(self, cross_section_area: float, gauge_length: float):
        """
        Initialize calculator with specimen geometry.

        Args:
            cross_section_area: Cross-sectional area in mm²
            gauge_length: Gauge length in mm
        """
        self.area = cross_section_area  # mm²
        self.gauge_length = gauge_length  # mm

    def calculate_stress(self, force: np.ndarray) -> np.ndarray:
        """
        Calculate engineering stress.

        Args:
            force: Force in N

        Returns:
            Stress in MPa
        """
        return force / self.area

    def calculate_strain(self, displacement: np.ndarray) -> np.ndarray:
        """
        Calculate engineering strain.

        Args:
            displacement: Displacement in mm

        Returns:
            Strain (dimensionless)
        """
        return displacement / self.gauge_length

    def calculate_youngs_modulus(
        self,
        stress: np.ndarray,
        strain: np.ndarray,
        window_size: int = 100
    ) -> np.ndarray:
        """
        Calculate Young's modulus using rolling linear regression.

        Args:
            stress: Stress array in MPa
            strain: Strain array (dimensionless)
            window_size: Number of points for rolling window

        Returns:
            Array of Young's modulus values in GPa
        """
        if len(stress) < window_size:
            # Not enough data yet
            return np.array([np.nan] * len(stress))

        youngs = np.full(len(stress), np.nan)

        for i in range(window_size, len(stress)):
            # Get window of data
            strain_window = strain[i - window_size:i]
            stress_window = stress[i - window_size:i]

            # Linear regression
            slope, _, r_value, _, _ = stats.linregress(strain_window, stress_window)

            # Young's modulus in GPa (stress in MPa, strain dimensionless)
            youngs[i] = slope / 1000.0  # Convert MPa to GPa

        return youngs

    def calculate_instantaneous_youngs(
        self,
        stress: np.ndarray,
        strain: np.ndarray
    ) -> float:
        """
        Calculate Young's modulus from current data (assuming elastic region).

        Args:
            stress: Stress array in MPa
            strain: Strain array (dimensionless)

        Returns:
            Young's modulus in GPa
        """
        if len(stress) < 10:
            return np.nan

        # Use all available data
        slope, _, r_value, _, _ = stats.linregress(strain, stress)

        # Convert to GPa
        return slope / 1000.0
