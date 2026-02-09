#!/usr/bin/env python3
"""
Click Simulation Tests for Structure Exporter
Uses pyautogui to simulate actual mouse clicks
"""

import subprocess
import time
import sys
import os

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1  # Small pause between actions
except ImportError:
    print("ERROR: pyautogui not installed. Run: pip3 install pyautogui")
    sys.exit(1)

import tkinter as tk

APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "structure_exporter.py")
SCREENSHOT_PATH = "/tmp/structure_exporter_screenshot.png"


def find_window_position():
    """Find the Structure Exporter window position from geometry file"""
    geometry_file = "/tmp/structure_exporter_geometry.txt"

    # First, trigger a screenshot to update the geometry file
    print("Press S in the app to update window geometry, or...")

    if os.path.exists(geometry_file):
        try:
            with open(geometry_file, "r") as f:
                parts = f.read().strip().split(',')
                return {
                    'x': int(parts[0]),
                    'y': int(parts[1]),
                    'width': int(parts[2]),
                    'height': int(parts[3])
                }
        except:
            pass

    return None


def click_at_offset(win, x_offset, y_offset, description=""):
    """Click at an offset from window origin"""
    x = win['x'] + x_offset
    y = win['y'] + y_offset
    print(f"  Clicking at ({x}, {y}): {description}")
    pyautogui.click(x, y)
    time.sleep(0.3)


def test_button_clicks():
    """Test clicking buttons with pyautogui"""
    print("=" * 60)
    print("Structure Exporter Click Simulation Test")
    print("=" * 60)
    print()
    print("IMPORTANT: Keep the Structure Exporter window visible!")
    print("Move mouse to screen corner to abort (failsafe)")
    print()

    # Find window
    print("Looking for Structure Exporter window...")
    win = find_window_position()

    if not win:
        print("ERROR: Could not find window position.")
        print("Make sure Structure Exporter is running and frontmost.")
        return False

    print(f"Window found at: ({win['x']}, {win['y']}) size: {win['width']}x{win['height']}")
    print()

    # Calculate button positions based on typical layout
    # These are approximate - adjust based on actual UI

    # Segment navigation buttons (top area)
    prev_btn_x = 55
    prev_btn_y = 35
    next_btn_x = 430
    next_btn_y = 35

    # Transport buttons (middle area, roughly y=430 based on screenshot)
    transport_y = 350  # Approximate
    transport_buttons = [
        (95, "<< -10s"),
        (175, "< -1s"),
        (245, "< -1f"),
        (330, "PLAY"),
        (420, "+1f >"),
        (490, "+1s >"),
        (570, "+10s >>"),
    ]

    print("Testing segment navigation...")
    print("-" * 40)

    # Test > button (next segment)
    click_at_offset(win, next_btn_x, next_btn_y, "Next segment (>)")
    time.sleep(0.5)

    # Test < button (prev segment)
    click_at_offset(win, prev_btn_x, prev_btn_y, "Prev segment (<)")
    time.sleep(0.5)

    print()
    print("Testing transport controls...")
    print("-" * 40)

    # Test a few transport buttons
    for x_offset, name in transport_buttons[:3]:
        click_at_offset(win, x_offset, transport_y, name)

    print()
    print("Taking screenshot to verify state...")
    pyautogui.press('s')  # Press S for screenshot
    time.sleep(0.5)

    print()
    print("Opening screenshot...")
    subprocess.run(['open', SCREENSHOT_PATH])

    print()
    print("=" * 60)
    print("Click test complete. Check the screenshot to verify buttons worked.")
    print("=" * 60)

    return True


if __name__ == "__main__":
    print("Starting in 3 seconds - make sure Structure Exporter is frontmost...")
    time.sleep(3)
    test_button_clicks()
