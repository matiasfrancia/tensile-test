# Tensile Testing Platform

Real-time data acquisition and visualization platform for tensile testing using MCC USB-1608FS DAQ.

## System Components

- **Sensor**: Keyence IA-100 (displacement/deformation)
- **Amplifier**: Keyence IA-1000
- **DAQ**: MCC USB-1608FS (2 channels)
  - Ch 0: Load cell (force)
  - Ch 1: Displacement sensor
- **Platform**: Windows (MCC UL library requirement)

## Features

- Real-time data acquisition (up to 50 kS/s)
- Live plotting (4 synchronized plots):
  - Load vs Time
  - Deformation vs Time
  - Stress-Strain Curve
  - Young's Modulus vs Time
- Auto-scaling plots
- Post-test region analysis:
  - Elastic region with Young's modulus
  - Yield point (0.2% offset method)
  - Ultimate tensile strength
  - Fracture detection
- Continuous HDF5 data logging
- Session-based data management

## Installation

### Prerequisites

1. **Windows OS** (required for MCC DAQ drivers)
2. **Python 3.8+**
3. **InstaCal** software (from MCC): Required for DAQ configuration
   - Download from: https://www.mccdaq.com/Software-Downloads

### Setup Virtual Environment

```bash
cd tensile_test

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

For MCC DAQ library (Windows only):
```bash
pip install mcculw
```

## Configuration

Edit `config/specimen.yaml` to set:

1. **Specimen geometry**:
   - `cross_section_area`: Cross-sectional area in mm²
   - `gauge_length`: Gauge length in mm

2. **Sensor calibration**:
   - Load cell: `slope` (N/V) and `offset` (N)
   - Displacement: `slope` (mm/V) and `offset` (mm)

3. **Acquisition settings**:
   - `sample_rate`: Sampling rate in Hz
   - `buffer_size`: Buffer size in samples
   - `channels`: DAQ channel assignments

### Calibration

To calibrate sensors:

1. **Load cell**: Apply known weights, measure voltage, calculate slope
2. **Displacement**: Use calibrated displacement gauge, measure voltage

## Usage

### Running the Application

```bash
cd tensile_test
python main.py
```

### Workflow

1. **Configure** specimen parameters in `config/specimen.yaml`
2. **Connect** sensors and DAQ to computer
3. **Start application**
4. **Click "Start Test"** to begin acquisition
5. Monitor real-time plots during test
6. **Click "Stop Test"** when test complete
7. **Click "Analyze Results"** for post-test analysis
8. Data automatically saved to `data/tensile_test_<timestamp>.h5`

### Without Hardware (Simulation Mode)

The application includes simulation mode for testing without hardware:
- Automatically activates if `mcculw` not installed
- Generates synthetic tensile test data
- Useful for GUI development and testing

## Data Format

Data saved in HDF5 format with structure:

```
tensile_test_<timestamp>.h5
├── session_001/
│   ├── time                    # Time array (s)
│   ├── raw_data/
│   │   ├── ch0_voltage        # Load cell voltage (V)
│   │   └── ch1_voltage        # Displacement voltage (V)
│   ├── processed_data/
│   │   ├── force_N            # Force (N)
│   │   ├── displacement_mm    # Displacement (mm)
│   │   ├── stress_MPa         # Stress (MPa)
│   │   └── strain             # Strain (dimensionless)
│   └── analysis/              # Post-test analysis results
│       ├── elastic/
│       ├── yield/
│       ├── ultimate/
│       └── fracture/
```

## Architecture

### Threading Model
- **Acquisition Thread**: Continuous DAQ monitoring
- **Processing Thread**: Real-time calculations (implicit via callbacks)
- **GUI Thread**: Plot updates at 20 Hz
- **Logging Thread**: HDF5 file writing

### Data Flow
```
MCC DAQ → Acquisition → Calibration → Mechanics → GUI + Logger
```

## Troubleshooting

### DAQ Not Detected
- Ensure InstaCal is installed
- Check DAQ connection and driver installation
- Verify board number in config matches InstaCal

### Buffer Overruns
- Reduce sample rate
- Increase buffer size
- Check system performance

### Import Errors
- Verify all dependencies installed: `pip list`
- Ensure Python 3.8+ being used

## Development

### Project Structure
```
tensile_test/
├── config/
│   └── specimen.yaml
├── src/
│   ├── acquisition/     # DAQ interface
│   ├── processing/      # Calibration, mechanics, analysis
│   ├── logging/         # HDF5 logging
│   ├── gui/            # PyQtGraph GUI
│   └── utils/          # Buffers, utilities
├── main.py
└── requirements.txt
```

### Adding New Metrics

1. Add calculation to `src/processing/mechanics.py`
2. Update `_on_new_data()` in `main_window.py`
3. Add plot or display in GUI

## License

MIT License - see LICENSE file

## Contact

For issues or questions, contact the development team.
# tensile-test
