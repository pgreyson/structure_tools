# Structure Exporter

GUI application for selecting video ranges from 3D SBS segments and exporting clips to [Erogenous Tones Structure](https://www.erogenous-tones.com/modules/structure/) format (Eurorack video synthesis module).

## Remote Control

The app can be controlled remotely via signals or command file:

### Quick Helper Script
```bash
/Volumes/Workspace/Downloads/se <command>
```

Commands:
- `se s` or `se screenshot` - Take & open screenshot
- `se n` or `se next` - Next segment
- `se p` or `se prev` - Previous segment
- `se step 100` - Step 100 frames forward
- `se step -50` - Step 50 frames backward
- `se play` / `se pause` - Playback control
- `se i` / `se o` - Set IN/OUT points
- `se r` or `se restart` - Restart app
- `se pid` - Show app PID

### Via Signals
```bash
PID=$(cat /tmp/structure_exporter.pid)
kill -USR1 $PID  # Screenshot
kill -USR2 $PID  # Next segment
```

### Via Command File
```bash
echo "screenshot" > /tmp/structure_exporter_cmd
echo "next" > /tmp/structure_exporter_cmd
echo "step 240" > /tmp/structure_exporter_cmd
```

### Screenshot Files
- Timestamped: `/tmp/structure_exporter_HHMMSS.png`
- Latest: `/tmp/structure_exporter_latest.png`
- Path file: `/tmp/structure_exporter_screenshot_path.txt`

## Files
- `structure_exporter.py` - Main application
- `test_structure_exporter.py` - Backend/export tests (17 tests)
- `test_structure_exporter_ui.py` - UI tests (35+ tests)

## Running the App
```bash
python3 /Volumes/Workspace/Downloads/structure_exporter.py &
```

## Running Tests
```bash
# Backend tests
python3 /Volumes/Workspace/Downloads/test_structure_exporter.py

# UI tests
python3 /Volumes/Workspace/Downloads/test_structure_exporter_ui.py
```

## Screenshot & UI Verification
The app has a built-in screenshot feature:
- Press **S** to capture screenshot to `/tmp/structure_exporter_screenshot.png`
- Always open screenshot after capture to verify UI: `open /tmp/structure_exporter_screenshot.png`

## macOS Tkinter Issues & Solutions

### 1. Button Text Invisible (CRITICAL)
**Problem:** `ttk.Button` on macOS with aqua theme shows blank white buttons when window is focused.

**Solution:** Use `tk.Button` instead of `ttk.Button` for all buttons.
```python
# BAD - text disappears on macOS
ttk.Button(parent, text="Click", command=func)

# GOOD - text always visible
tk.Button(parent, text="Click", command=func)
```

### 2. Tap-to-Click Not Working
**Problem:** Trackpad tap-to-click doesn't trigger button commands on macOS.

**Solution:** Bind to `<ButtonRelease-1>` instead of using `command=`:
```python
btn = tk.Button(parent, text="Click")
btn.bind("<ButtonRelease-1>", lambda e: func())
```

### 3. Window Focus on Launch
**Problem:** Buttons don't respond until window is backgrounded/foregrounded.

**Solution:** Force focus on startup:
```python
root.lift()
root.focus_force()
root.attributes('-topmost', True)
root.update()
root.attributes('-topmost', False)
root.bind("<Button-1>", lambda e: root.focus_force())
```

### 4. Combobox/OptionMenu Issues
**Problem:** `ttk.Combobox` dropdown doesn't work with trackpad on macOS.

**Solution:** Use simple Label display with < > navigation buttons instead:
```python
self.segment_label = tk.Label(parent, textvariable=self.segment_var, ...)
prev_btn = tk.Button(parent, text=" < ", ...)
next_btn = tk.Button(parent, text=" > ", ...)
```

## Structure Export Format Requirements
- **Container:** MOV (.mov extension)
- **Codec:** MJPEG with tag `mjpa`
- **Streams:** Video only (no audio, data, or subtitle streams)
- **Resolutions:**
  - 640x480 (max 400 frames / ~16 seconds at 24fps)
  - 320x240 (max 1600 frames / ~66 seconds at 24fps)

## FFmpeg Export Command
```bash
ffmpeg -y -ss "START" -to "END" -i "INPUT" \
  -vf "scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v mjpeg -q:v 3 -tag:v mjpa \
  -an -dn -sn -map_metadata -1 -map 0:v:0 \
  "OUTPUT.mov"
```

## Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Left/Right | Step 1 frame |
| I | Set IN point |
| O | Set OUT point |
| M | Add marker |
| , | Previous marker |
| . | Next marker |
| S | Take screenshot |
| [ | Previous segment |
| ] | Next segment |

## Development Workflow
1. Make code changes
2. Kill existing app: `pkill -f "python3.*structure_exporter.py"`
3. Launch app: `python3 /Volumes/Workspace/Downloads/structure_exporter.py &`
4. Press S in app to screenshot
5. Open screenshot: `open /tmp/structure_exporter_screenshot.png`
6. Verify UI visually
7. Run tests to confirm functionality

## Known Issues
- Video preview shows black at frame 0 (first frame of some videos is black)
- Theme inconsistencies between tk and ttk widgets
