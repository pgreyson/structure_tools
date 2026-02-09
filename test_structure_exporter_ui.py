#!/usr/bin/env python3
"""
UI Test Suite for Structure Exporter
Tests the GUI components programmatically
"""

import sys
import os
import tkinter as tk
from unittest.mock import Mock, patch
import tempfile

# Add the directory to path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass
from typing import List, Optional

from structure_exporter import SEGMENT_DIR


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str


class UITester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.root = None
        self.app = None

    def add_result(self, name: str, passed: bool, message: str = ""):
        result = TestResult(name, passed, message)
        self.results.append(result)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed and message:
            print(f"         {message}")

    def setup(self):
        """Create the app instance for testing"""
        print("  Setting up test environment...")
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests

        # Import and create app
        from structure_exporter import StructureExporter
        self.app = StructureExporter(self.root)

        # Give tkinter time to initialize
        self.root.update()

    def teardown(self):
        """Clean up"""
        if self.app:
            self.app.player.release()
        if self.root:
            self.root.destroy()

    def run_all_tests(self):
        """Run all UI tests"""
        print("=" * 60)
        print("Structure Exporter UI Test Suite")
        print("=" * 60)
        print()

        try:
            print("[1/7] Setup...")
            self.setup()
            self.add_result("app initializes", True, "")

            print("\n[2/7] Testing Segment Loading...")
            self.test_segment_loading()

            print("\n[3/7] Testing Video Loading...")
            self.test_video_loading()

            print("\n[4/7] Testing IN/OUT Points...")
            self.test_in_out_points()

            print("\n[5/7] Testing Time Formatting...")
            self.test_time_display()

            print("\n[6/7] Testing Transport Controls...")
            self.test_transport_controls()

            print("\n[7/7] Testing Export Validation...")
            self.test_export_validation()

        except Exception as e:
            self.add_result("test execution", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.teardown()

        self.print_report()
        return all(r.passed for r in self.results)

    # =========================================================================
    # Test: Segment Loading
    # =========================================================================
    def test_segment_loading(self):
        """Test that segments are loaded into dropdown"""
        segment_values = self.app.segment_values

        # Check segments were loaded
        has_segments = len(segment_values) > 0
        self.add_result("segments loaded into dropdown", has_segments,
                       f"Found {len(segment_values)} segments" if has_segments else "No segments found")

        # Check format includes duration
        if has_segments:
            first = segment_values[0]
            has_duration = "(" in first and ")" in first
            self.add_result("segment shows duration", has_duration,
                           f"Format: '{first}'")

            # Check segments are sorted
            is_sorted = segment_values == sorted(segment_values)
            self.add_result("segments are sorted", is_sorted, "")

            # Test selection programmatically
            self.app.segment_var.set(first)
            self.root.update()
            selected = self.app.segment_var.get()
            self.add_result("segment selection works", selected == first,
                           f"Selected: '{selected}'")

            # Test selecting different segment
            if len(segment_values) > 1:
                self.app.segment_var.set(segment_values[1])
                self.root.update()
                second_selected = self.app.segment_var.get()
                self.add_result("can change segment selection", second_selected == segment_values[1],
                               f"Selected: '{second_selected}'")

                # Test that selection triggers video load
                self.root.update()
                video_loaded = self.app.current_segment is not None
                self.add_result("segment selection loads video", video_loaded,
                               f"Current segment: {self.app.current_segment}")

            # Test get_current_segment_index
            self.app.segment_var.set(first)
            self.root.update()
            idx = self.app.get_current_segment_index()
            self.add_result("get_current_segment_index works", idx == 0,
                           f"Expected 0, got {idx}")

            # Test prev/next segment buttons
            if len(segment_values) > 1:
                # Go to first segment
                self.app.segment_var.set(segment_values[0])
                self.root.update()

                # Test next_segment
                self.app.next_segment()
                self.root.update()
                after_next = self.app.get_current_segment_index()
                self.add_result("next_segment button works", after_next == 1,
                               f"Expected index 1, got {after_next}")

                # Test prev_segment
                self.app.prev_segment()
                self.root.update()
                after_prev = self.app.get_current_segment_index()
                self.add_result("prev_segment button works", after_prev == 0,
                               f"Expected index 0, got {after_prev}")

                # Test prev at boundary (should stay at 0)
                self.app.prev_segment()
                self.root.update()
                at_boundary = self.app.get_current_segment_index()
                self.add_result("prev_segment respects start boundary", at_boundary == 0,
                               f"Expected index 0, got {at_boundary}")

                # Test next at end boundary
                self.app.segment_var.set(segment_values[-1])
                self.root.update()
                self.app.next_segment()
                self.root.update()
                at_end = self.app.get_current_segment_index()
                self.add_result("next_segment respects end boundary", at_end == len(segment_values) - 1,
                               f"Expected index {len(segment_values) - 1}, got {at_end}")

    # =========================================================================
    # Test: Video Loading
    # =========================================================================
    def test_video_loading(self):
        """Test video loading functionality"""
        test_segment = os.path.join(SEGMENT_DIR, "segment_01.mp4")

        if not os.path.exists(test_segment):
            self.add_result("video loading", False, "No test segment available")
            return

        # Load video
        self.app.load_video(test_segment)
        self.root.update()

        # Check video was loaded
        has_cap = self.app.player.cap is not None
        self.add_result("video capture opened", has_cap, "")

        if has_cap:
            # Check frame count
            has_frames = self.app.player.total_frames > 0
            self.add_result("frame count detected", has_frames,
                           f"{self.app.player.total_frames} frames")

            # Check FPS
            has_fps = self.app.player.fps > 0
            self.add_result("FPS detected", has_fps,
                           f"{self.app.player.fps} fps")

            # Check duration
            has_duration = self.app.player.duration > 0
            self.add_result("duration calculated", has_duration,
                           f"{self.app.player.duration:.1f} seconds")

            # Check current segment path stored
            path_stored = self.app.current_segment == test_segment
            self.add_result("segment path stored", path_stored, "")

    # =========================================================================
    # Test: IN/OUT Points
    # =========================================================================
    def test_in_out_points(self):
        """Test IN/OUT point functionality"""
        test_segment = os.path.join(SEGMENT_DIR, "segment_01.mp4")
        if not os.path.exists(test_segment):
            self.add_result("in/out points", False, "No test segment available")
            return

        # Ensure video is loaded
        if not self.app.player.cap:
            self.app.load_video(test_segment)
            self.root.update()

        # Test setting IN point
        self.app.player.seek(100)  # Go to frame 100
        self.root.update()
        self.app.set_in_point()

        expected_in = 100 / self.app.player.fps
        in_point_set = abs(self.app.in_point - expected_in) < 0.1
        self.add_result("IN point set correctly", in_point_set,
                       f"Expected ~{expected_in:.2f}s, got {self.app.in_point:.2f}s")

        # Test setting OUT point
        self.app.player.seek(200)  # Go to frame 200
        self.root.update()
        self.app.set_out_point()

        expected_out = 200 / self.app.player.fps
        out_point_set = abs(self.app.out_point - expected_out) < 0.1
        self.add_result("OUT point set correctly", out_point_set,
                       f"Expected ~{expected_out:.2f}s, got {self.app.out_point:.2f}s")

        # Test duration calculation
        expected_duration = self.app.out_point - self.app.in_point
        duration_text = self.app.duration_label.cget("text")
        has_duration = "Duration:" in duration_text
        self.add_result("duration label updated", has_duration,
                       f"Label: '{duration_text}'")

        # Test goto IN
        self.app.player.seek(0)
        self.app.goto_in()
        self.root.update()
        at_in = abs(self.app.player.current_frame - 100) < 2
        self.add_result("goto IN works", at_in,
                       f"Expected frame ~100, at {self.app.player.current_frame}")

        # Test goto OUT
        self.app.goto_out()
        self.root.update()
        at_out = abs(self.app.player.current_frame - 200) < 2
        self.add_result("goto OUT works", at_out,
                       f"Expected frame ~200, at {self.app.player.current_frame}")

    # =========================================================================
    # Test: Time Display
    # =========================================================================
    def test_time_display(self):
        """Test time formatting in display"""
        # Test format_time function
        test_cases = [
            (0, "0:00.00"),
            (30, "0:30.00"),
            (60, "1:00.00"),
            (90.5, "1:30.50"),
            (125.75, "2:05.75"),
        ]

        all_correct = True
        for seconds, expected in test_cases:
            result = self.app.format_time(seconds)
            if result != expected:
                all_correct = False
                print(f"         {seconds}s: expected '{expected}', got '{result}'")

        self.add_result("time formatting correct", all_correct, "")

        # Test time label updates
        if self.app.player.cap:
            self.app.player.seek(0)
            self.app.player.show_frame()
            self.root.update()

            time_text = self.app.time_label.cget("text")
            has_slash = "/" in time_text
            self.add_result("time label shows current/total", has_slash,
                           f"Label: '{time_text}'")

    # =========================================================================
    # Test: Transport Controls
    # =========================================================================
    def test_transport_controls(self):
        """Test transport control buttons"""
        test_segment = os.path.join(SEGMENT_DIR, "segment_01.mp4")
        if not os.path.exists(test_segment):
            self.add_result("transport controls", False, "No test segment available")
            return

        if not self.app.player.cap:
            self.app.load_video(test_segment)
            self.root.update()

        # Start at frame 500
        self.app.player.seek(500)
        self.root.update()

        # Test step forward 1 frame
        self.app.step(1)
        self.root.update()
        stepped_forward = self.app.player.current_frame == 501
        self.add_result("step +1 frame", stepped_forward,
                       f"Expected 501, got {self.app.player.current_frame}")

        # Test step backward 1 frame
        self.app.step(-1)
        self.root.update()
        stepped_back = self.app.player.current_frame == 500
        self.add_result("step -1 frame", stepped_back,
                       f"Expected 500, got {self.app.player.current_frame}")

        # Test step forward 24 frames (1 second)
        self.app.step(24)
        self.root.update()
        stepped_1s = self.app.player.current_frame == 524
        self.add_result("step +1 second (24 frames)", stepped_1s,
                       f"Expected 524, got {self.app.player.current_frame}")

        # Test step backward 240 frames (10 seconds)
        self.app.player.seek(500)
        self.app.step(-240)
        self.root.update()
        stepped_10s = self.app.player.current_frame == 260
        self.add_result("step -10 seconds (240 frames)", stepped_10s,
                       f"Expected 260, got {self.app.player.current_frame}")

        # Test boundary - can't go below 0
        self.app.player.seek(10)
        self.app.step(-100)
        self.root.update()
        at_zero = self.app.player.current_frame == 0
        self.add_result("step respects lower boundary", at_zero,
                       f"Expected 0, got {self.app.player.current_frame}")

        # Test play/pause state
        initial_state = self.app.player.playing
        self.app.toggle_play()
        self.root.update()
        toggled = self.app.player.playing != initial_state
        self.app.toggle_play()  # Stop it
        self.root.update()
        self.add_result("play/pause toggles", toggled, "")

    # =========================================================================
    # Test: Export Validation
    # =========================================================================
    def test_export_validation(self):
        """Test export validation logic"""
        test_segment = os.path.join(SEGMENT_DIR, "segment_01.mp4")
        if not os.path.exists(test_segment):
            self.add_result("export validation", False, "No test segment available")
            return

        if not self.app.player.cap:
            self.app.load_video(test_segment)
            self.root.update()

        # Test: OUT must be after IN
        self.app.in_point = 10
        self.app.out_point = 5  # Invalid - before IN

        # Mock messagebox to capture error
        with patch('tkinter.messagebox.showerror') as mock_error:
            self.app.export_clip()
            error_shown = mock_error.called
            self.add_result("validates OUT > IN", error_shown,
                           "Error shown for invalid range")

        # Test: Output name required
        self.app.in_point = 5
        self.app.out_point = 10
        self.app.output_name_var.set("")  # Empty name

        with patch('tkinter.messagebox.showerror') as mock_error:
            self.app.export_clip()
            error_shown = mock_error.called
            self.add_result("validates output name required", error_shown,
                           "Error shown for empty name")

        # Test: Duration warning for 640x480
        self.app.output_name_var.set("test_clip")
        self.app.in_point = 0
        self.app.out_point = 20  # 20 seconds > 16 second limit
        self.app.resolution_var.set("640")

        with patch('tkinter.messagebox.askyesno', return_value=False) as mock_warn:
            self.app.export_clip()
            warning_shown = mock_warn.called
            self.add_result("warns when 640x480 > 16 seconds", warning_shown,
                           "Warning shown for long duration")

        # Test: Resolution variable works
        self.app.resolution_var.set("320")
        is_320 = self.app.resolution_var.get() == "320"
        self.app.resolution_var.set("640")
        is_640 = self.app.resolution_var.get() == "640"
        self.add_result("resolution selector works", is_320 and is_640, "")

        # Test: Copy to SD checkbox
        self.app.copy_to_sd_var.set(True)
        is_checked = self.app.copy_to_sd_var.get() == True
        self.app.copy_to_sd_var.set(False)
        is_unchecked = self.app.copy_to_sd_var.get() == False
        self.add_result("copy to SD checkbox works", is_checked and is_unchecked, "")

    def print_report(self):
        """Print final test report"""
        print()
        print("=" * 60)
        print("UI TEST REPORT")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal: {total} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print()

        if failed > 0:
            print("Failed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ✗ {r.name}: {r.message}")
            print()

        if failed == 0:
            print("✓ All UI tests passed!")
        else:
            print(f"✗ {failed} UI test(s) failed.")

        print("=" * 60)


def main():
    tester = UITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
