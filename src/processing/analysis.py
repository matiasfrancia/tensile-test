"""Post-test analysis for region detection and characterization."""

import numpy as np
from scipy import stats
from scipy.signal import find_peaks
from typing import Dict, Optional, Tuple


class RegionAnalysis:
    """Analyzes stress-strain data to identify test regions."""

    def __init__(self):
        self.regions = {}

    def analyze(
        self,
        stress: np.ndarray,
        strain: np.ndarray,
        force: np.ndarray,
        offset_strain: float = 0.002  # 0.2% offset for yield
    ) -> Dict:
        """
        Perform complete region analysis on test data.

        Args:
            stress: Stress array in MPa
            strain: Strain array (dimensionless)
            force: Force array in N
            offset_strain: Strain offset for yield point detection (default 0.2%)

        Returns:
            Dictionary with region information and metrics
        """
        if len(stress) < 50:
            return {"error": "Insufficient data for analysis"}

        results = {}

        # Find elastic region
        elastic_idx, youngs_modulus, r_squared = self._find_elastic_region(stress, strain)
        results['elastic'] = {
            'end_index': elastic_idx,
            'youngs_modulus_GPa': youngs_modulus,
            'r_squared': r_squared
        }

        # Find yield point using 0.2% offset method
        yield_idx, yield_stress, yield_strain = self._find_yield_point(
            stress, strain, youngs_modulus * 1000, offset_strain
        )
        results['yield'] = {
            'index': yield_idx,
            'stress_MPa': yield_stress,
            'strain': yield_strain
        }

        # Find ultimate tensile strength
        uts_idx = np.argmax(stress)
        results['ultimate'] = {
            'index': uts_idx,
            'stress_MPa': stress[uts_idx],
            'strain': strain[uts_idx]
        }

        # Find fracture point (significant load drop)
        fracture_idx = self._find_fracture_point(force, uts_idx)
        if fracture_idx is not None:
            results['fracture'] = {
                'index': fracture_idx,
                'stress_MPa': stress[fracture_idx],
                'strain': strain[fracture_idx]
            }

        # Calculate plastic region if exists
        if yield_idx is not None and uts_idx > yield_idx:
            results['plastic'] = {
                'start_index': yield_idx,
                'end_index': uts_idx,
                'strain_range': strain[uts_idx] - strain[yield_idx]
            }

        return results

    def _find_elastic_region(
        self,
        stress: np.ndarray,
        strain: np.ndarray,
        min_r_squared: float = 0.98
    ) -> Tuple[int, float, float]:
        """
        Find elastic region by identifying longest linear portion.

        Args:
            stress: Stress array
            strain: Strain array
            min_r_squared: Minimum R² for linearity

        Returns:
            (end_index, Young's modulus in GPa, R²)
        """
        best_end = 50  # Minimum points for elastic region
        best_youngs = 0.0
        best_r2 = 0.0

        # Try progressively longer regions
        for end_idx in range(50, len(stress), 10):
            strain_region = strain[:end_idx]
            stress_region = stress[:end_idx]

            # Linear fit
            slope, intercept, r_value, _, _ = stats.linregress(strain_region, stress_region)
            r_squared = r_value ** 2

            # Check if still linear
            if r_squared < min_r_squared:
                break

            best_end = end_idx
            best_youngs = slope / 1000.0  # Convert to GPa
            best_r2 = r_squared

        return best_end, best_youngs, best_r2

    def _find_yield_point(
        self,
        stress: np.ndarray,
        strain: np.ndarray,
        youngs_modulus_MPa: float,
        offset: float = 0.002
    ) -> Tuple[Optional[int], Optional[float], Optional[float]]:
        """
        Find yield point using offset method.

        Args:
            stress: Stress array
            strain: Strain array
            youngs_modulus_MPa: Young's modulus in MPa
            offset: Offset strain (default 0.002 for 0.2%)

        Returns:
            (index, yield stress, yield strain) or (None, None, None)
        """
        # Create offset line: stress = E * (strain - offset)
        offset_line = youngs_modulus_MPa * (strain - offset)

        # Find intersection (where stress curve crosses offset line)
        # Look for first crossing after initial linear region
        start_idx = 50

        for i in range(start_idx, len(stress)):
            if stress[i] >= offset_line[i]:
                return i, stress[i], strain[i]

        return None, None, None

    def _find_fracture_point(
        self,
        force: np.ndarray,
        uts_idx: int,
        drop_threshold: float = 0.3
    ) -> Optional[int]:
        """
        Find fracture point by detecting significant load drop after UTS.

        Args:
            force: Force array
            uts_idx: Index of ultimate tensile strength
            drop_threshold: Fractional drop to detect (default 30%)

        Returns:
            Index of fracture or None
        """
        if uts_idx >= len(force) - 10:
            return None

        max_force = force[uts_idx]
        threshold = max_force * (1 - drop_threshold)

        # Search after UTS for significant drop
        for i in range(uts_idx + 10, len(force)):
            if force[i] < threshold:
                return i

        return None

    def get_region_masks(
        self,
        data_length: int,
        results: Dict
    ) -> Dict[str, np.ndarray]:
        """
        Generate boolean masks for each region.

        Args:
            data_length: Length of data arrays
            results: Results from analyze()

        Returns:
            Dictionary of boolean masks for each region
        """
        masks = {}

        if 'elastic' in results:
            elastic_mask = np.zeros(data_length, dtype=bool)
            elastic_mask[:results['elastic']['end_index']] = True
            masks['elastic'] = elastic_mask

        if 'plastic' in results:
            plastic_mask = np.zeros(data_length, dtype=bool)
            start = results['plastic']['start_index']
            end = results['plastic']['end_index']
            plastic_mask[start:end] = True
            masks['plastic'] = plastic_mask

        return masks
