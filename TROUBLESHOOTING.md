# Troubleshooting Guide

## Buttons Not Clickable on Windows

### Step 1: Run Simple GUI Test

First, verify that basic PyQt6 functionality works:

```bash
python test_gui_simple.py
```

**Expected behavior:**
- Window opens with a button
- Button is clickable
- Counter increments when clicked
- Console shows "Button clicked!" messages

**If this doesn't work:** PyQt6 installation issue
- Reinstall: `pip uninstall PyQt6 && pip install PyQt6`
- Check Python version: `python --version` (need 3.8+)

### Step 2: Run Main Application with Debug Output

```bash
python main.py
```

**Watch the console output carefully.** You should see:

```
=== Initializing Tensile Testing Platform ===
Loading config from: ...
Config loaded successfully
...
Connecting control panel signals...
Start button enabled: True
UI initialized
Starting update timer...
=== Initialization complete ===
```

### Step 3: Click the Start Button

**What you should see in console:**
```
Start button clicked in ControlPanel
>>> START button clicked <<<
Acquisition started: ...
```

### Common Issues & Solutions

#### Issue 1: No Console Output When Clicking
**Symptom:** Click buttons but nothing prints to console

**Possible causes:**
1. **Application frozen/hung**
   - Check if window can be moved/resized
   - Look for error messages in console
   - Check Task Manager for CPU usage

2. **Event loop blocked**
   - An operation is blocking the main thread
   - Look for errors during initialization

**Solution:**
- Close and restart application
- Check for errors in console
- Try simple GUI test first

#### Issue 2: Buttons Grayed Out
**Symptom:** Buttons appear disabled (grayed out)

**Cause:** Button state not set correctly

**Check:**
```python
# In console output, look for:
Start button enabled: True  # Should be True
```

**Solution:** Check if initialization completed without errors

#### Issue 3: Console Shows Click But No Action
**Symptom:** Console prints "Start button clicked" but nothing happens

**Possible causes:**
1. Error in `_on_start()` method
2. DAQ initialization failing
3. Exception being caught silently

**Solution:** Look for error messages after the "START button clicked" message

#### Issue 4: Application Freezes When Starting
**Symptom:** Click Start, application becomes unresponsive

**Cause:** DAQ initialization blocking main thread

**Solutions:**
1. Check MCC DAQ connection in InstaCal
2. Verify DAQ board number matches config (usually 0)
3. Disconnect hardware and run in simulation mode

### Simulation Mode Fallback

If hardware issues persist, run without MCC library:

```bash
# Temporarily rename mcculw to force simulation mode
pip uninstall mcculw

# Run application
python main.py

# Should see: "Running in SIMULATION mode"
```

In simulation mode, buttons should work and you'll see synthetic data.

### Check PyQt6 Installation

```python
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

Should print: `PyQt6 OK`

If error, reinstall:
```bash
pip install --upgrade --force-reinstall PyQt6
```

### Check All Dependencies

```bash
python test_installation.py
```

Should show all green checkmarks.

### Hardware-Specific Issues

#### MCC DAQ Not Responding

1. **Open InstaCal**
   - Verify DAQ appears in device list
   - Run "Test" to verify communication
   - Note the board number (usually 0)

2. **Check board number in config**
   ```yaml
   acquisition:
     board_num: 0  # Must match InstaCal
   ```

3. **Check channels**
   ```yaml
   channels:
     load: 0          # Verify correct channel
     displacement: 1  # Verify correct channel
   ```

### Windows-Specific Issues

#### Missing DLL Errors

**Error:** `ImportError: DLL load failed`

**Solution:**
1. Install Visual C++ Redistributable
2. Reinstall PyQt6: `pip install --force-reinstall PyQt6`

#### Permission Errors

**Error:** Permission denied accessing DAQ

**Solution:** Run CMD/PowerShell as Administrator

### Debug Mode

Add more verbose output by editing main.py:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Still Not Working?

1. **Collect information:**
   - Python version: `python --version`
   - OS version: `winver` (in Run dialog)
   - PyQt6 version: `pip show PyQt6`
   - Full console output
   - Screenshot of window

2. **Try minimal test:**
   ```bash
   python test_gui_simple.py
   ```
   If this works but main.py doesn't, the issue is application-specific.

3. **Check for conflicting software:**
   - Other Qt applications running
   - Antivirus blocking Python
   - Firewall blocking local connections

### Emergency Reset

If all else fails:

```bash
# Delete virtual environment
rm -rf venv  # or on Windows: rmdir /s venv

# Recreate
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Test again
python test_gui_simple.py
python main.py
```

## Getting Help

When reporting issues, include:
1. Output from `python test_installation.py`
2. Full console output when running `python main.py`
3. Output when clicking buttons (console messages)
4. Windows version
5. Python version
6. Whether `test_gui_simple.py` works
