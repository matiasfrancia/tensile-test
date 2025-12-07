"""Utility script to analyze saved HDF5 data files."""

import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def list_sessions(filepath):
    """List all sessions in HDF5 file."""
    with h5py.File(filepath, 'r') as f:
        print(f"\nFile: {filepath}")
        print(f"Creation time: {f.attrs.get('creation_time', 'Unknown')}")
        print("\nSessions:")

        sessions = [key for key in f.keys() if key.startswith('session_')]
        for session_name in sorted(sessions):
            session = f[session_name]
            print(f"\n  {session_name}:")
            print(f"    Start: {session.attrs.get('start_time', 'Unknown')}")
            print(f"    End: {session.attrs.get('end_time', 'Unknown')}")
            print(f"    Samples: {len(session['time'])}")

            # Show analysis results if available
            if 'analysis' in session:
                print(f"    Analysis results available:")
                for region in session['analysis'].keys():
                    print(f"      - {region}")


def plot_session(filepath, session_name='session_001'):
    """Plot data from a specific session."""
    with h5py.File(filepath, 'r') as f:
        if session_name not in f:
            print(f"Session '{session_name}' not found")
            return

        session = f[session_name]

        # Load data
        time = session['time'][:]
        force = session['processed_data/force_N'][:]
        displacement = session['processed_data/displacement_mm'][:]
        stress = session['processed_data/stress_MPa'][:]
        strain = session['processed_data/strain'][:]

        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'{session_name} - {session.attrs.get("start_time", "")}', fontsize=14)

        # Force vs Time
        axes[0, 0].plot(time, force, 'b-', linewidth=1)
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Force (N)')
        axes[0, 0].set_title('Load vs Time')
        axes[0, 0].grid(True, alpha=0.3)

        # Displacement vs Time
        axes[0, 1].plot(time, displacement, 'g-', linewidth=1)
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Displacement (mm)')
        axes[0, 1].set_title('Deformation vs Time')
        axes[0, 1].grid(True, alpha=0.3)

        # Stress-Strain Curve
        axes[1, 0].plot(strain, stress, 'r-', linewidth=2)
        axes[1, 0].set_xlabel('Strain')
        axes[1, 0].set_ylabel('Stress (MPa)')
        axes[1, 0].set_title('Stress-Strain Curve')
        axes[1, 0].grid(True, alpha=0.3)

        # Add region markers if analysis exists
        if 'analysis' in session:
            analysis = session['analysis']

            if 'elastic' in analysis:
                idx = analysis['elastic'].attrs.get('end_index', 0)
                if idx < len(strain):
                    axes[1, 0].axvline(strain[idx], color='green', linestyle='--', label='Elastic limit')

            if 'yield' in analysis:
                yield_strain = analysis['yield'].attrs.get('strain', None)
                if yield_strain is not None:
                    axes[1, 0].axvline(yield_strain, color='orange', linestyle='--', label='Yield')

            if 'ultimate' in analysis:
                idx = analysis['ultimate'].attrs.get('index', 0)
                if idx < len(strain):
                    axes[1, 0].axvline(strain[idx], color='red', linestyle='--', label='UTS')

            axes[1, 0].legend()

        # Statistics table
        axes[1, 1].axis('off')
        stats_text = f"""
        SESSION STATISTICS

        Duration: {time[-1]:.2f} s
        Samples: {len(time)}

        Maximum Force: {np.max(force):.2f} N
        Maximum Displacement: {np.max(displacement):.3f} mm
        Maximum Stress: {np.max(stress):.2f} MPa
        Maximum Strain: {np.max(strain):.4f}
        """

        if 'analysis' in session:
            stats_text += "\n        ANALYSIS RESULTS\n"

            if 'elastic' in analysis:
                E = analysis['elastic'].attrs.get('youngs_modulus_GPa', 0)
                R2 = analysis['elastic'].attrs.get('r_squared', 0)
                stats_text += f"\n        Young's Modulus: {E:.2f} GPa"
                stats_text += f"\n        R²: {R2:.4f}"

            if 'yield' in analysis:
                yield_stress = analysis['yield'].attrs.get('stress_MPa', None)
                if yield_stress is not None:
                    stats_text += f"\n\n        Yield Stress: {yield_stress:.2f} MPa"

            if 'ultimate' in analysis:
                uts = analysis['ultimate'].attrs.get('stress_MPa', 0)
                stats_text += f"\n        UTS: {uts:.2f} MPa"

        axes[1, 1].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                       verticalalignment='center')

        plt.tight_layout()
        plt.show()


def export_to_csv(filepath, session_name='session_001', output_path=None):
    """Export session data to CSV."""
    if output_path is None:
        output_path = filepath.replace('.h5', f'_{session_name}.csv')

    with h5py.File(filepath, 'r') as f:
        if session_name not in f:
            print(f"Session '{session_name}' not found")
            return

        session = f[session_name]

        # Load data
        time = session['time'][:]
        ch0_voltage = session['raw_data/ch0_voltage'][:]
        ch1_voltage = session['raw_data/ch1_voltage'][:]
        force = session['processed_data/force_N'][:]
        displacement = session['processed_data/displacement_mm'][:]
        stress = session['processed_data/stress_MPa'][:]
        strain = session['processed_data/strain'][:]

        # Stack and save
        data = np.column_stack([time, ch0_voltage, ch1_voltage, force, displacement, stress, strain])
        header = 'time_s,ch0_voltage_V,ch1_voltage_V,force_N,displacement_mm,stress_MPa,strain'

        np.savetxt(output_path, data, delimiter=',', header=header, comments='')
        print(f"Exported to: {output_path}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze_data.py <hdf5_file> [command] [session]")
        print("\nCommands:")
        print("  list              - List all sessions (default)")
        print("  plot [session]    - Plot session data")
        print("  export [session]  - Export session to CSV")
        print("\nExample:")
        print("  python analyze_data.py data/tensile_test_20250107_143022.h5 plot session_001")
        return

    filepath = sys.argv[1]

    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        return

    command = sys.argv[2] if len(sys.argv) > 2 else 'list'
    session = sys.argv[3] if len(sys.argv) > 3 else 'session_001'

    if command == 'list':
        list_sessions(filepath)
    elif command == 'plot':
        plot_session(filepath, session)
    elif command == 'export':
        export_to_csv(filepath, session)
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
