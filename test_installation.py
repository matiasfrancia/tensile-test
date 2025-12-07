"""Test installation and verify dependencies."""

import sys

def check_imports():
    """Check if all required packages can be imported."""
    print("Checking dependencies...\n")

    required = {
        'numpy': 'NumPy',
        'scipy': 'SciPy',
        'yaml': 'PyYAML',
        'h5py': 'HDF5 support',
        'pyqtgraph': 'PyQtGraph',
        'PyQt6': 'PyQt6'
    }

    optional = {
        'mcculw': 'MCC Universal Library (Windows only)'
    }

    all_ok = True

    # Check required packages
    print("Required packages:")
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT FOUND")
            all_ok = False

    # Check optional packages
    print("\nOptional packages:")
    for module, name in optional.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ⚠ {name} - Not installed (simulation mode only)")

    return all_ok


def test_config():
    """Test configuration file."""
    import os
    import yaml

    print("\n\nChecking configuration...")
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'specimen.yaml')

    if not os.path.exists(config_path):
        print(f"  ✗ Config file not found: {config_path}")
        return False

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        print(f"  ✓ Config file loaded")
        print(f"    - Cross-section area: {config['specimen']['cross_section_area']} mm²")
        print(f"    - Gauge length: {config['specimen']['gauge_length']} mm")
        print(f"    - Sample rate: {config['acquisition']['sample_rate']} Hz")
        return True
    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False


def test_simulation():
    """Test simulation mode."""
    print("\n\nTesting simulation mode...")

    try:
        from src.acquisition.mcc_daq import MCCDataAcquisition
        import time

        data_received = []

        def callback(t, ch0, ch1):
            data_received.append((t, ch0, ch1))

        daq = MCCDataAcquisition(sample_rate=100, buffer_size=500)
        daq.set_data_callback(callback)
        daq.start()

        time.sleep(0.5)
        daq.stop()

        if len(data_received) > 0:
            print(f"  ✓ Simulation mode working")
            print(f"    - Received {len(data_received)} data chunks")
            return True
        else:
            print(f"  ✗ No data received")
            return False

    except Exception as e:
        print(f"  ✗ Error in simulation: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Tensile Testing Platform - Installation Test")
    print("="*60)

    results = []

    # Test imports
    results.append(("Dependencies", check_imports()))

    # Test config
    results.append(("Configuration", test_config()))

    # Test simulation
    results.append(("Simulation", test_simulation()))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:20s} {status}")

    if all(r[1] for r in results):
        print("\n✓ All tests passed! Ready to run the application.")
        print("\nTo start the application:")
        print("  python main.py")
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")

    print("="*60)


if __name__ == '__main__':
    main()
