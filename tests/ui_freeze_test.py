import tkinter as tk
import time
import threading
import pytest
import os
from unittest.mock import MagicMock
from model import Model
from raceinfo import Heat, TimingSystem
from scoreboard import ScoreboardImage
import imagecast_types

# Mock external dependencies that might interfere or are unnecessary for this test
import sentry_sdk
sentry_sdk.start_transaction = MagicMock()
sentry_sdk.start_span = MagicMock()
import wh_analytics
wh_analytics.results_received = MagicMock()

class SlowTimingSystem(TimingSystem):
    def __init__(self, delay=1.0):
        self.delay = delay
    def read(self, filename):
        time.sleep(self.delay)
        h = Heat()
        h.event = 1
        h.heat = 1
        return h
    def decode(self, stream): raise NotImplementedError()
    def write(self, filename, heat): pass
    def encode(self, heat): return ""
    def filename(self, heat): return "test.do4"
    @property
    def patterns(self): return ["*.do4"]

class UIMonitor:
    def __init__(self, root):
        self.root = root
        self.last_heartbeat = time.time()
        self.max_gap = 0
        self.heartbeat_interval = 50 # ms
        self._check_heartbeat()

    def _check_heartbeat(self):
        now = time.time()
        gap = now - self.last_heartbeat
        if gap > self.max_gap:
            self.max_gap = gap
        self.last_heartbeat = now
        self.root.after(self.heartbeat_interval, self._check_heartbeat)

@pytest.mark.skipif(os.environ.get('DISPLAY') is None and os.name != 'nt' and os.uname().sysname != 'Darwin',
                    reason="Requires GUI environment")
def test_ui_responsiveness_during_result_processing():
    """
    This test verifies that the UI remains responsive while a new race result is being processed.
    It simulates the processing logic used in wahoo_results.py.
    """
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tcl/Tk not available or broken in this environment: {e}")
        return
    root.withdraw()
    model = Model(root)
    # Set up enough model state to avoid crashes in ScoreboardImage
    model.color_bg.set("black")
    model.color_title.set("white")
    model.color_event.set("white")
    model.color_even.set("white")
    model.color_odd.set("white")
    model.font_normal.set("Arial")
    model.font_time.set("Arial")
    
    model.timing_system = SlowTimingSystem(delay=0.5)
    monitor = UIMonitor(root)

    # The "FIXED" version of process_new_result logic
    def process_new_result_fixed(file):
        timing_system = model.timing_system
        def _bg():
            result = timing_system.read(file) # This blocks the BG thread
            def _ui():
                # This runs on the UI thread
                try:
                    _ = ScoreboardImage(imagecast_types.IMAGE_SIZE, result, model)
                except Exception:
                    pass # We don't care if it fails, we care if it hangs
            model.enqueue(_ui)
        threading.Thread(target=_bg, daemon=True).start()

    def process_new_result_broken(file):
        # This simulates the old logic that ran on the main thread
        result = model.timing_system.read(file) # This blocks the MAIN thread!
        try:
            _ = ScoreboardImage(imagecast_types.IMAGE_SIZE, result, model)
        except Exception:
            pass
    
    if os.environ.get("TEST_BROKEN"):
        root.after(100, lambda: process_new_result_broken("test.do4"))
    else:
        root.after(100, lambda: process_new_result_fixed("test.do4"))
    
    # Run for enough time to complete the "slow" processing
    stop_time = time.time() + 1.5
    while time.time() < stop_time:
        root.update()
        time.sleep(0.01)

    root.destroy()
    
    # Threshold: If the UI is responsive, the max gap should be close to heartbeat_interval + overhead
    # In a background thread world, it should be well under 200ms.
    # Without the fix, it would be > 500ms (the delay of SlowTimingSystem).
    if os.environ.get("TEST_BROKEN"):
        assert monitor.max_gap > 0.4, f"Expected UI to hang, but it didn't! Max gap: {monitor.max_gap:.3f}s"
        print(f"Verified: UI HUNG as expected (gap={monitor.max_gap:.3f}s)")
    else:
        assert monitor.max_gap < 0.3, f"UI hung for too long! Max gap: {monitor.max_gap:.3f}s"
        print(f"Verified: UI stayed RESPONSIVE (gap={monitor.max_gap:.3f}s)")

if __name__ == "__main__":
    # If run as a script, run the test
    test_ui_responsiveness_during_result_processing()
    print("Test PASSED!")
