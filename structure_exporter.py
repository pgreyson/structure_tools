#!/usr/bin/env python3
"""
Structure Exporter - GUI tool for selecting video ranges and exporting to Erogenous Tones Structure format

Remote control via signals:
  kill -USR1 <pid>  # Take screenshot
  kill -USR2 <pid>  # Next segment

Or via command file:
  echo "screenshot" > /tmp/structure_exporter_cmd
  echo "next" > /tmp/structure_exporter_cmd
  echo "prev" > /tmp/structure_exporter_cmd
  echo "step 24" > /tmp/structure_exporter_cmd
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk, ImageGrab
import subprocess
import os
import threading
import time
import signal
import numpy as np

# Syphon for video output
try:
    import syphon
    from syphon.utils.numpy import copy_image_to_mtl_texture
    from syphon.utils.raw import create_mtl_texture
    SYPHON_AVAILABLE = True
except ImportError:
    SYPHON_AVAILABLE = False
    print("Warning: syphon-python not installed. Run: pip install syphon-python")

# AVFoundation for hardware-accelerated video
try:
    import AVFoundation
    import CoreMedia
    import Quartz
    AVFOUNDATION_AVAILABLE = True
except ImportError:
    AVFOUNDATION_AVAILABLE = False
    print("Note: AVFoundation not available, using OpenCV")

# Configuration
SEGMENT_DIR = "/Volumes/Workspace/Downloads/3d_rarities_output"
OUTPUT_DIR = "/Volumes/Workspace/Downloads/3d_rarities_structure"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
STRUCTURE_SD = "/Volumes/STRUCT_SD/clips"

# Syphon output: 3840x1080 (side-by-side stereo for Viture glasses)
SYPHON_WIDTH = 3840
SYPHON_HEIGHT = 1080
EYE_WIDTH = 1920  # Each eye panel


class SyphonOutput:
    """Sends frames to Syphon for display by external client"""

    def __init__(self):
        self.server = None
        self.texture = None
        self.enabled = False
        self._output_buffer = None
        self._tex_width = 0
        self._tex_height = 0

    def toggle(self):
        """Toggle Syphon output on/off"""
        if self.enabled:
            self.disable()
        else:
            self.enable()

    def enable(self):
        """Start Syphon server"""
        if not SYPHON_AVAILABLE:
            print("Syphon not available")
            return False

        try:
            self.server = syphon.SyphonMetalServer("Structure Exporter")
            self.enabled = True
            print("Syphon server started: 'Structure Exporter'")
            return True
        except Exception as e:
            print(f"Error starting Syphon: {e}")
            return False

    def disable(self):
        """Stop Syphon server"""
        if self.server:
            try:
                self.server.stop()
            except:
                pass
            self.server = None
            self.texture = None
            self._output_buffer = None
        self.enabled = False
        print("Syphon server stopped")

    def send_frame(self, frame_bgr):
        """Send frame to Syphon with 16:9 letterboxing per eye"""
        if not self.enabled or not self.server:
            return

        try:
            h, w = frame_bgr.shape[:2]
            eye_w = w // 2  # Width of each eye in source

            # Initialize texture at 3840x1080 for Viture (two 1920x1080 panels)
            if self._tex_width != SYPHON_WIDTH:
                self.texture = create_mtl_texture(self.server.device, SYPHON_WIDTH, SYPHON_HEIGHT)
                self._output_buffer = np.zeros((SYPHON_HEIGHT, SYPHON_WIDTH, 4), dtype=np.uint8)
                self._output_buffer[:, :, 3] = 255  # Alpha always 255
                self._tex_width = SYPHON_WIDTH
                self._tex_height = SYPHON_HEIGHT
                print(f"Syphon texture: {SYPHON_WIDTH}x{SYPHON_HEIGHT}")

            # Calculate letterbox position for each eye (center in 1920x1080)
            pad_x = (EYE_WIDTH - eye_w) // 2
            pad_y = (SYPHON_HEIGHT - h) // 2

            # Clear buffer (black letterbox)
            self._output_buffer[:, :, :3] = 0

            # Left eye -> left panel (BGR to RGB)
            left_eye = frame_bgr[:, :eye_w]
            self._output_buffer[pad_y:pad_y+h, pad_x:pad_x+eye_w, 0] = left_eye[:, :, 2]
            self._output_buffer[pad_y:pad_y+h, pad_x:pad_x+eye_w, 1] = left_eye[:, :, 1]
            self._output_buffer[pad_y:pad_y+h, pad_x:pad_x+eye_w, 2] = left_eye[:, :, 0]

            # Right eye -> right panel
            right_eye = frame_bgr[:, eye_w:]
            rx = EYE_WIDTH + pad_x
            self._output_buffer[pad_y:pad_y+h, rx:rx+eye_w, 0] = right_eye[:, :, 2]
            self._output_buffer[pad_y:pad_y+h, rx:rx+eye_w, 1] = right_eye[:, :, 1]
            self._output_buffer[pad_y:pad_y+h, rx:rx+eye_w, 2] = right_eye[:, :, 0]

            # Flip and send
            flipped = np.ascontiguousarray(self._output_buffer[::-1])
            copy_image_to_mtl_texture(flipped, self.texture)
            self.server.publish_frame_texture(self.texture)
        except Exception as e:
            print(f"Syphon send error: {e}")


class VideoPlayer:
    def __init__(self, canvas, time_label, slider):
        self.canvas = canvas
        self.time_label = time_label
        self.slider = slider
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 24
        self.playing = False
        self.photo = None
        self.duration = 0
        self.frame_callback = None  # Called with raw BGR frame for Syphon
        self._updating_slider = False  # Prevent slider callback during playback
        # Decode thread
        self._decode_thread = None
        self._decode_running = False
        self._last_frame_time = 0
        # Scrub state
        self._was_playing_before_scrub = False
        self._scrub_timer = None

    def load(self, path):
        # Remember if we were playing
        was_playing = self.playing

        # Stop decode thread first
        self._decode_running = False
        self.playing = False
        if self._decode_thread and self._decode_thread.is_alive():
            self._decode_thread.join(timeout=1)
        self._decode_thread = None

        if self.cap:
            self.cap.release()
        # Use AVFoundation backend for hardware decoding on macOS
        self.cap = cv2.VideoCapture(path, cv2.CAP_AVFOUNDATION)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 24
        self.duration = self.total_frames / self.fps
        self.current_frame = 0
        self.slider.configure(to=self.total_frames - 1)
        self.seek(0)

        # Resume playback if was playing
        if was_playing:
            self.play()

    def seek(self, frame_num, scrubbing=False):
        if not self.cap:
            return

        # Pause playback during seek
        if self.playing:
            if scrubbing:
                self._was_playing_before_scrub = True
            self._decode_running = False
            self.playing = False
            if self._decode_thread and self._decode_thread.is_alive():
                self._decode_thread.join(timeout=0.5)
            self._decode_thread = None

        frame_num = max(0, min(frame_num, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        self.current_frame = frame_num
        self.show_frame()

    def scrub_ended(self):
        """Called when scrubbing stops - restore playback if was playing"""
        if self._was_playing_before_scrub:
            self._was_playing_before_scrub = False
            self.play()

    def show_frame(self, reset_position=True):
        """Show single frame (for scrubbing, not playback)"""
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if ret:
            # Send to Syphon
            if self.frame_callback:
                try:
                    self.frame_callback(frame)
                except Exception as e:
                    print(f"Frame callback error: {e}")

            # Update time label
            current_time = self.current_frame / self.fps
            self.time_label.config(text=f"{self.format_time(current_time)} / {self.format_time(self.duration)}")

            # Reset read position for scrubbing
            if reset_position:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

            # Reset position for scrubbing (not needed during continuous playback)
            if reset_position:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{m}:{s:02d}.{ms:02d}"

    def get_current_time(self):
        return self.current_frame / self.fps

    def play(self):
        self.playing = True
        self._decode_running = True
        self._last_frame_time = time.time()
        self._decode_thread = threading.Thread(target=self._decode_loop, daemon=True)
        self._decode_thread.start()
        self._update_ui_loop()

    def pause(self):
        self.playing = False
        self._decode_running = False

    def _decode_loop(self):
        """Decode and send frames in background thread"""
        frame_duration = 1.0 / self.fps
        next_frame_time = time.perf_counter()

        while self._decode_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame += 1
                    if self.current_frame >= self.total_frames:
                        self.current_frame = 0
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                    # Send to Syphon
                    if self.frame_callback:
                        self.frame_callback(frame)

                # Wait for next frame time (absolute timing, no drift)
                next_frame_time += frame_duration
                sleep_time = next_frame_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -frame_duration:
                    # Too far behind, reset timing
                    next_frame_time = time.perf_counter()
            except Exception as e:
                print(f"Decode loop error: {e}")
                import traceback
                traceback.print_exc()
                break

    def _update_ui_loop(self):
        """Update UI elements (runs in main thread)"""
        if self.playing:
            # Update slider
            self._updating_slider = True
            self.slider.set(self.current_frame)
            self._updating_slider = False

            # Update time label
            current_time = self.current_frame / self.fps
            self.time_label.config(text=f"{self.format_time(current_time)} / {self.format_time(self.duration)}")

            # Schedule next UI update (10 times per second is enough)
            self.time_label.after(100, self._update_ui_loop)

    def release(self):
        self._decode_running = False
        self.playing = False
        if self._decode_thread and self._decode_thread.is_alive():
            self._decode_thread.join(timeout=1)
        if self.cap:
            self.cap.release()


CMD_FILE = "/tmp/structure_exporter_cmd"
PID_FILE = "/tmp/structure_exporter.pid"


class StructureExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Structure Exporter")
        self.root.geometry("700x350")

        self.in_point = 0
        self.out_point = 0

        # Write PID file for remote control
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        # Setup signal handlers
        signal.signal(signal.SIGUSR1, self._handle_sigusr1)
        signal.signal(signal.SIGUSR2, self._handle_sigusr2)

        # Start command file polling
        self._poll_commands()

        # macOS focus fix - keep event loop pumping
        self.root.bind("<FocusIn>", self._on_focus_in)
        self._pump_events()

        self.current_segment = None

        # Syphon output for stereo glasses (starts automatically)
        self.syphon = SyphonOutput()
        self.syphon.enable()
        self.player = None  # Will be set in setup_ui

        self.setup_ui()
        self.load_segments()

        # Frame callback will be set when Viture is enabled
        # (disabled by default to avoid any overhead)

    def make_button(self, parent, text, command, **kwargs):
        """Create a button with tap feedback"""
        btn = tk.Button(parent, text=text, command=command,
                       activebackground="#4a90d9", activeforeground="white",
                       **kwargs)
        return btn

    def setup_ui(self):

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section - Segment selector
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="Segment:").pack(side=tk.LEFT)
        self.prev_btn = self.make_button(top_frame, " < ", self.prev_segment,
                                        font=("Helvetica", 14, "bold"))
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.segment_var = tk.StringVar(value="(no segments)")
        self.segment_values = []
        self.segment_label = tk.Label(top_frame, textvariable=self.segment_var,
                                       font=("Courier", 11), width=35, anchor="w",
                                       relief="sunken", padx=5, pady=3)
        self.segment_label.pack(side=tk.LEFT, padx=5)
        self.segment_var.trace("w", self.on_segment_changed)

        self.next_btn = self.make_button(top_frame, " > ", self.next_segment,
                                        font=("Helvetica", 14, "bold"))
        self.next_btn.pack(side=tk.LEFT, padx=2)

        open_btn = tk.Button(top_frame, text="Open File...", command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=5)

        # Placeholder for canvas (not displayed, kept for compatibility)
        self.canvas = tk.Frame(main_frame)  # Dummy frame

        # Time display
        self.time_label = ttk.Label(main_frame, text="0:00.00 / 0:00.00", font=("Courier", 12))
        self.time_label.pack()

        # Slider
        self.slider = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider)
        self.slider.pack(fill=tk.X, pady=5)

        # Transport controls
        transport_frame = ttk.Frame(main_frame)
        transport_frame.pack(pady=5)

        self.make_button(transport_frame, "<< -10s", lambda: self.step(-240)).pack(side=tk.LEFT, padx=2)
        self.make_button(transport_frame, "< -1s", lambda: self.step(-24)).pack(side=tk.LEFT, padx=2)
        self.make_button(transport_frame, "< -1f", lambda: self.step(-1)).pack(side=tk.LEFT, padx=2)

        self.play_btn = self.make_button(transport_frame, "PLAY", self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=10)

        self.make_button(transport_frame, "+1f >", lambda: self.step(1)).pack(side=tk.LEFT, padx=2)
        self.make_button(transport_frame, "+1s >", lambda: self.step(24)).pack(side=tk.LEFT, padx=2)
        self.make_button(transport_frame, "+10s >>", lambda: self.step(240)).pack(side=tk.LEFT, padx=2)


        # In/Out points
        points_frame = ttk.Frame(main_frame)
        points_frame.pack(fill=tk.X, pady=10)

        self.make_button(points_frame, "Set IN [I]", self.set_in_point).pack(side=tk.LEFT, padx=5)
        self.in_label = ttk.Label(points_frame, text="IN: --:--", font=("Courier", 11))
        self.in_label.pack(side=tk.LEFT, padx=10)

        self.make_button(points_frame, "Set OUT [O]", self.set_out_point).pack(side=tk.LEFT, padx=5)
        self.out_label = ttk.Label(points_frame, text="OUT: --:--", font=("Courier", 11))
        self.out_label.pack(side=tk.LEFT, padx=10)

        self.duration_label = ttk.Label(points_frame, text="Duration: --:--", font=("Courier", 11, "bold"))
        self.duration_label.pack(side=tk.LEFT, padx=20)

        self.make_button(points_frame, "Go IN", self.goto_in).pack(side=tk.LEFT, padx=5)
        self.make_button(points_frame, "Go OUT", self.goto_out).pack(side=tk.LEFT, padx=5)

        # Export options
        export_frame = ttk.LabelFrame(main_frame, text="Export to Structure", padding="10")
        export_frame.pack(fill=tk.X, pady=10)

        row1 = ttk.Frame(export_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Resolution:").pack(side=tk.LEFT)
        self.resolution_var = tk.StringVar(value="640")
        ttk.Radiobutton(row1, text="640x480 (max 16 sec)", variable=self.resolution_var, value="640").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(row1, text="320x240 (max 66 sec)", variable=self.resolution_var, value="320").pack(side=tk.LEFT, padx=10)

        row2 = ttk.Frame(export_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="Output name:").pack(side=tk.LEFT)
        self.output_name_var = tk.StringVar(value="clip_01")
        self.output_entry = ttk.Entry(row2, textvariable=self.output_name_var, width=30)
        self.output_entry.pack(side=tk.LEFT, padx=5)

        self.copy_to_sd_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="Copy to Structure SD", variable=self.copy_to_sd_var).pack(side=tk.LEFT, padx=20)

        self.export_btn = tk.Button(row2, text="EXPORT", command=self.export_clip,
                                      font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.export_btn.pack(side=tk.RIGHT, padx=5)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W)

        # Initialize video player
        self.player = VideoPlayer(self.canvas, self.time_label, self.slider)

        # Connect Syphon output to player
        self.player.frame_callback = self.syphon.send_frame

        # Key bindings
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Left>", lambda e: self.step(-1))
        self.root.bind("<Right>", lambda e: self.step(1))
        self.root.bind("<i>", lambda e: self.set_in_point())
        self.root.bind("<o>", lambda e: self.set_out_point())
        self.root.bind("<I>", lambda e: self.set_in_point())
        self.root.bind("<O>", lambda e: self.set_out_point())
        self.root.bind("<s>", lambda e: self.take_screenshot())
        self.root.bind("<S>", lambda e: self.take_screenshot())
        self.root.bind("<bracketleft>", lambda e: self.prev_segment())
        self.root.bind("<bracketright>", lambda e: self.next_segment())

    def load_segments(self):
        segments = []
        if os.path.isdir(SEGMENT_DIR):
            for f in sorted(os.listdir(SEGMENT_DIR)):
                if f.startswith("segment_") and f.endswith(".mp4"):
                    path = os.path.join(SEGMENT_DIR, f)
                    # Get duration
                    try:
                        result = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                                               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
                                              capture_output=True, text=True)
                        dur = float(result.stdout.strip())
                        dur_str = f"{int(dur//60)}:{int(dur%60):02d}"
                    except:
                        dur_str = "??:??"
                    segments.append(f"{f} ({dur_str})")

        self.segment_values = segments

        if segments:
            self.segment_var.set(segments[0])

    def on_segment_changed(self, *args):
        """Called when segment_var changes"""
        selection = self.segment_var.get()
        if selection and selection != "(no segments)" and selection.startswith("segment_"):
            filename = selection.split(" ")[0]
            path = os.path.join(SEGMENT_DIR, filename)
            self.load_video(path)

    def get_current_segment_index(self):
        """Get current segment index"""
        current = self.segment_var.get()
        if current in self.segment_values:
            return self.segment_values.index(current)
        return -1

    def prev_segment(self):
        """Go to previous segment"""
        if not self.segment_values:
            return
        current = self.get_current_segment_index()
        if current > 0:
            self.segment_var.set(self.segment_values[current - 1])

    def next_segment(self):
        """Go to next segment"""
        if not self.segment_values:
            return
        current = self.get_current_segment_index()
        if current < len(self.segment_values) - 1:
            self.segment_var.set(self.segment_values[current + 1])

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mov *.avi"), ("All files", "*.*")]
        )
        if path:
            self.load_video(path)

    def load_video(self, path):
        self.current_segment = path
        self.player.load(path)
        self.in_point = 0
        self.out_point = self.player.duration
        self.update_point_labels()
        self.status_var.set(f"Loaded: {os.path.basename(path)}")
        self.update_output_name()
        # Update play button to match player state
        if self.player.playing:
            self.play_btn.config(text="PAUSE")
        else:
            self.play_btn.config(text="PLAY")

    def format_time_compact(self, seconds):
        """Format time as m-ss for filenames (no colons)"""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}-{s:02d}"

    def update_output_name(self):
        """Update suggested output name based on source and in/out points"""
        if not self.current_segment:
            return
        basename = os.path.splitext(os.path.basename(self.current_segment))[0]
        in_str = self.format_time_compact(self.in_point)
        out_str = self.format_time_compact(self.out_point)
        self.output_name_var.set(f"{basename}_{in_str}_to_{out_str}")

    def on_slider(self, value):
        if self.player.cap and not self.player._updating_slider:
            frame = int(float(value))
            self.player.seek(frame, scrubbing=True)
            # Update play button
            self.play_btn.config(text="PLAY" if not self.player.playing else "PAUSE")
            # Set timer to detect scrub end and restore playback
            if self.player._scrub_timer:
                self.root.after_cancel(self.player._scrub_timer)
            self.player._scrub_timer = self.root.after(300, self._on_scrub_end)

    def _on_scrub_end(self):
        """Called when scrubbing stops"""
        self.player._scrub_timer = None
        self.player.scrub_ended()
        self.play_btn.config(text="PLAY" if not self.player.playing else "PAUSE")

    def step(self, frames):
        if self.player.cap:
            new_frame = self.player.current_frame + frames
            new_frame = max(0, min(new_frame, self.player.total_frames - 1))
            self.slider.set(new_frame)
            self.player.seek(new_frame)

    def toggle_play(self):
        if self.player.playing:
            self.player.pause()
            self.play_btn.config(text="PLAY")
        else:
            self.player.play()
            self.play_btn.config(text="PAUSE")

    def toggle_syphon(self):
        """Toggle Syphon output for stereo glasses"""
        self.syphon.toggle()
        if self.syphon.enabled:
            self.player.frame_callback = self.syphon.send_frame
        else:
            self.player.frame_callback = None

    def set_in_point(self):
        self.in_point = self.player.get_current_time()
        self.update_point_labels()
        self.update_output_name()

    def set_out_point(self):
        self.out_point = self.player.get_current_time()
        self.update_point_labels()
        self.update_output_name()

    def goto_in(self):
        if self.player.cap:
            frame = int(self.in_point * self.player.fps)
            self.slider.set(frame)
            self.player.seek(frame)

    def goto_out(self):
        if self.player.cap:
            frame = int(self.out_point * self.player.fps)
            self.slider.set(frame)
            self.player.seek(frame)

    def update_point_labels(self):
        self.in_label.config(text=f"IN: {self.format_time(self.in_point)}")
        self.out_label.config(text=f"OUT: {self.format_time(self.out_point)}")

        duration = self.out_point - self.in_point
        self.duration_label.config(text=f"Duration: {self.format_time(abs(duration))}")

        # Warning for too long
        res = self.resolution_var.get()
        max_dur = 16 if res == "640" else 66
        if duration > max_dur:
            self.duration_label.config(foreground="red")
        else:
            self.duration_label.config(foreground="green")

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{m}:{s:02d}.{ms:02d}"

    def export_clip(self):
        if not self.current_segment:
            messagebox.showerror("Error", "No video loaded")
            return

        if self.out_point <= self.in_point:
            messagebox.showerror("Error", "OUT point must be after IN point")
            return

        output_name = self.output_name_var.get().strip()
        if not output_name:
            messagebox.showerror("Error", "Please enter an output name")
            return

        duration = self.out_point - self.in_point
        res = self.resolution_var.get()
        max_dur = 16 if res == "640" else 66

        if duration > max_dur:
            if not messagebox.askyesno("Warning",
                f"Duration ({duration:.1f}s) exceeds recommended max ({max_dur}s).\nStructure may not load all frames.\n\nContinue anyway?"):
                return

        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mov")

        # Format times for ffmpeg
        in_time = f"{int(self.in_point//60)}:{self.in_point%60:06.3f}"
        clip_duration = self.out_point - self.in_point

        resolution = "640:480" if res == "640" else "320:240"

        self.status_var.set("Exporting...")
        self.export_btn.config(state="disabled")
        self.root.update()

        # Run export in thread
        def do_export():
            try:
                cmd = [
                    FFMPEG, "-y",
                    "-ss", in_time,
                    "-i", self.current_segment,
                    "-t", str(clip_duration),
                    "-vf", f"scale={resolution}:force_original_aspect_ratio=decrease,pad={resolution}:(ow-iw)/2:(oh-ih)/2:black",
                    "-c:v", "mjpeg", "-q:v", "3", "-tag:v", "mjpa",
                    "-an", "-dn", "-sn", "-map_metadata", "-1", "-map", "0:v:0",
                    output_path
                ]

                print(f"IN: {self.in_point:.3f}s, OUT: {self.out_point:.3f}s, Duration: {clip_duration:.3f}s")
                print(f"Export command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed:\n{result.stderr}"))
                    self.root.after(0, lambda: self.status_var.set("Export failed"))
                else:
                    # Copy to SD if requested
                    copied = False
                    if self.copy_to_sd_var.get() and os.path.isdir(STRUCTURE_SD):
                        import shutil
                        shutil.copy(output_path, os.path.join(STRUCTURE_SD, f"{output_name}.mov"))
                        copied = True

                    msg = f"Exported: {output_path}"
                    if copied:
                        msg += f"\nCopied to: {STRUCTURE_SD}"

                    self.root.after(0, lambda: messagebox.showinfo("Success", msg))
                    self.root.after(0, lambda: self.status_var.set("Export complete"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Export failed"))
            finally:
                self.root.after(0, lambda: self.export_btn.config(state="normal"))

        threading.Thread(target=do_export, daemon=True).start()

    def take_screenshot(self):
        """Capture screenshot of the app window"""
        self.root.update()
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        # Capture the window region
        screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))

        # Save to file with timestamp
        timestamp = time.strftime("%H%M%S")
        screenshot_path = f"/tmp/structure_exporter_{timestamp}.png"
        screenshot.save(screenshot_path)

        # Also save as "latest" for easy access
        latest_path = "/tmp/structure_exporter_latest.png"
        screenshot.save(latest_path)

        # Save path to a file so scripts can find it
        with open("/tmp/structure_exporter_screenshot_path.txt", "w") as f:
            f.write(screenshot_path)

        # Also save window geometry for testing
        with open("/tmp/structure_exporter_geometry.txt", "w") as f:
            f.write(f"{x},{y},{w},{h}\n")

        self.status_var.set(f"Screenshot: {screenshot_path}")
        print(f"Screenshot saved: {screenshot_path}")

    def _handle_sigusr1(self, signum, frame):
        """Handle SIGUSR1 - take screenshot"""
        self.root.after(0, self.take_screenshot)

    def _handle_sigusr2(self, signum, frame):
        """Handle SIGUSR2 - next segment"""
        self.root.after(0, self.next_segment)

    def _poll_commands(self):
        """Poll for commands from file"""
        if os.path.exists(CMD_FILE):
            try:
                with open(CMD_FILE, "r") as f:
                    cmd = f.read().strip()
                os.remove(CMD_FILE)

                if cmd:
                    self._execute_command(cmd)
            except:
                pass

        # Poll again in 100ms
        self.root.after(100, self._poll_commands)

    def _on_focus_in(self, event):
        """Restore event handling when window regains focus (macOS Sonoma Tk 8.6.12 bug fix)"""
        # Workaround: slightly move the window to reset event handling
        # This simulates the manual "drag window" fix for the Tcl/Tk bug
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"+{x+1}+{y}")
        self.root.after(50, lambda: self.root.geometry(f"+{x}+{y}"))

    def _pump_events(self):
        """Keep event loop responsive on macOS"""
        try:
            self.root.update_idletasks()
        except:
            pass
        self.root.after(50, self._pump_events)

    def _execute_command(self, cmd):
        """Execute a remote command"""
        parts = cmd.split()
        action = parts[0].lower()

        print(f"Remote command: {cmd}")

        if action == "screenshot":
            self.take_screenshot()
        elif action == "next":
            self.next_segment()
        elif action == "prev":
            self.prev_segment()
        elif action == "step" and len(parts) > 1:
            try:
                frames = int(parts[1])
                self.step(frames)
            except:
                pass
        elif action == "play":
            if not self.player.playing:
                self.toggle_play()
        elif action == "pause":
            if self.player.playing:
                self.toggle_play()
        elif action == "setin":
            self.set_in_point()
        elif action == "setout":
            self.set_out_point()
        elif action == "gotoin":
            self.goto_in()
        elif action == "gotoout":
            self.goto_out()
        elif action == "seek" and len(parts) > 1:
            try:
                frame = int(parts[1])
                self.player.seek(frame)
                self.slider.set(frame)
            except:
                pass
        elif action == "syphon":
            self.toggle_syphon()

    def on_closing(self):
        # Clean up Syphon output
        if self.syphon.enabled:
            self.syphon.disable()
        # Clean up PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        self.player.release()
        self.root.destroy()


def main():
    root = tk.Tk()

    # macOS: Use default theme for better native behavior
    style = ttk.Style()
    style.theme_use('aqua')

    # macOS focus fix
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)

    app = StructureExporter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Bind click anywhere to ensure focus
    root.bind("<Button-1>", lambda e: root.focus_force())

    root.mainloop()


if __name__ == "__main__":
    main()
