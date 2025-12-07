# Quick Start Guide

## Initial Setup (One-time)

### 1. Create Virtual Environment

```bash
cd tensile_test

# Create venv
python3 -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python test_installation.py
```

This will check all dependencies and test simulation mode.

### 4. Configure Specimen Settings

Edit `config/specimen.yaml`:

```yaml
specimen:
  cross_section_area: 50.0  # YOUR specimen area in mm²
  gauge_length: 100.0       # YOUR gauge length in mm
  material: "Steel"

calibration:
  load_cell:
    slope: 1000.0    # YOUR calibration (N/V)
    offset: 0.0
  displacement:
    slope: 10.0      # YOUR calibration (mm/V)
    offset: 0.0
```

## Running Tests

### Option 1: With Hardware (Windows)

1. Connect MCC USB-1608FS to computer
2. Connect load cell to Channel 0
3. Connect displacement sensor (via IA-1000) to Channel 1
4. Run InstaCal to verify DAQ detected
5. Start application:

```bash
python main.py
```

### Option 2: Simulation Mode (Any OS)

Works without hardware for testing:

```bash
python main.py
```

## Using the Application

### Basic Workflow

1. **Start Test**
   - Click "Start Test" button
   - Plots will begin updating in real-time
   - Data automatically logged to `data/` folder

2. **Monitor Test**
   - Watch real-time plots
   - Check current metrics in right panel
   - Plots auto-scale to show all data

3. **Stop Test**
   - Click "Stop Test" when test complete
   - Data flushed to HDF5 file

4. **Analyze Results**
   - Click "Analyze Results"
   - View detected regions and metrics
   - Markers added to stress-strain plot

### Understanding the Plots

1. **Load vs Time** (top left)
   - Shows force from load cell over time
   - Units: Newtons (N)

2. **Deformation vs Time** (top right)
   - Shows displacement from sensor over time
   - Units: millimeters (mm)

3. **Stress-Strain Curve** (bottom left)
   - Primary analysis plot
   - Shows material behavior
   - Regions marked after analysis

4. **Young's Modulus vs Time** (bottom right)
   - Rolling calculation of stiffness
   - Units: GPa

### Analyzing Saved Data

List sessions in a file:
```bash
python analyze_data.py data/tensile_test_20250107_143022.h5 list
```

Plot a specific session:
```bash
python analyze_data.py data/tensile_test_20250107_143022.h5 plot session_001
```

Export to CSV:
```bash
python analyze_data.py data/tensile_test_20250107_143022.h5 export session_001
```

## Calibration Guide

### Load Cell Calibration

1. Apply known weight (e.g., 100 N)
2. Record voltage output
3. Calculate slope: `slope = force / voltage`
4. Update `config/specimen.yaml`

Example:
- Applied force: 100 N
- Measured voltage: 0.5 V
- Slope = 100 / 0.5 = 200 N/V

### Displacement Sensor Calibration

1. Use calibrated gauge or micrometer
2. Apply known displacement (e.g., 10 mm)
3. Record voltage output
4. Calculate slope: `slope = displacement / voltage`
5. Update `config/specimen.yaml`

Example:
- Applied displacement: 10 mm
- Measured voltage: 2.0 V
- Slope = 10 / 2.0 = 5 mm/V

## Troubleshooting

### Application won't start
- Check Python version: `python --version` (need 3.8+)
- Verify dependencies: `python test_installation.py`
- Check config file exists: `config/specimen.yaml`

### No data showing
- In simulation mode: Should see synthetic data immediately
- With hardware: Check DAQ connections and InstaCal setup
- Check console for error messages

### Buffer overrun warnings
- Reduce sample rate in config
- Increase buffer size
- Close other applications

### Analysis shows errors
- Need at least 50 data points
- Check if test reached elastic region
- Verify calibration values reasonable

## Tips for Best Results

1. **Sample Rate**
   - Tensile tests: 100-1000 Hz usually sufficient
   - Higher rates for impact/dynamic tests
   - Lower rates reduce data file size

2. **Test Duration**
   - Display shows last 2 minutes
   - All data saved to file
   - Stop when specimen fractures or test complete

3. **Analysis**
   - Perform analysis after test complete
   - Elastic region detection requires clear linear portion
   - Yield detection uses 0.2% offset method (standard)

4. **Data Management**
   - Files saved to `data/` folder automatically
   - Name includes timestamp for uniqueness
   - Use `analyze_data.py` for post-processing

## Next Steps

- Modify `config/specimen.yaml` with your calibration values
- Run a test with simulation mode to familiarize yourself
- Connect hardware and perform calibration tests
- Run actual tensile tests and analyze results

## Support

Check README.md for full documentation and troubleshooting.
