# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2020 - John D. Strunk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''Wahoo! Results scoreboard'''

import os
import platform
import sys
import time
import uuid
from tkinter import Tk, messagebox
from typing import Callable, List

from PIL import Image  # type: ignore
import sentry_sdk
from sentry_sdk.integrations.threading import ThreadingIntegration
import watchdog.events  #type: ignore
import watchdog.observers  #type: ignore

from imagecast import ImageCast
from config import WahooConfig
from manual import show_manual_chooser
import results
from scoreboardimage import ScoreboardImage, waiting_screen
from settings import Settings
from version import WAHOO_RESULTS_VERSION

# Sentry.io reporting token
SENTRY_DSN = "https://a7e34ba5d40140bfb1e65779585438fb@o948149.ingest.sentry.io/5897736"

FILE_WATCHER: watchdog.observers.Observer
IC: ImageCast

def eventlist_to_csv(events: List[results.Event]) -> List[str]:
    '''Converts a list of events into CSV format'''
    lines: List[str] = []
    for i in events:
        lines.append(f"{i.event_num},{i.event_desc},{i.num_heats},1,A\n")
    return lines

def generate_dolphin_csv(filename: str, directory: str) -> int:
    """
    Write the events from the scb files in the given directory into a CSV
    for Dolphin.
    """
    files = os.scandir(directory)
    events = []
    for file in files:
        if file.name.endswith(".scb"):
            event = results.Event()
            event.from_scb(file.path)
            events.append(event)
    events.sort(key=lambda e: e.event_num)
    csv_lines = eventlist_to_csv(events)
    outfile = os.path.join(directory, filename)
    with open(outfile, "w", encoding="cp1252") as csv:
        csv.writelines(csv_lines)
    return len(events)

class Do4Handler(watchdog.events.PatternMatchingEventHandler):
    '''Handler to process Dolphin .do4 files'''
    HeatCallback = Callable[[results.Heat], None]
    _options: WahooConfig

    def __init__(self, hcb: HeatCallback, options: WahooConfig):
        self._hcb = hcb
        self._options = options
        super().__init__(patterns=["*.do4"], ignore_directories=True)

    def on_created(self, event):
        time.sleep(1)
        with sentry_sdk.start_transaction(op="new_result", name="New race result") as txn:
            inhibit = self._options.get_bool("inhibit_inconsistent")
            txn.set_tag("inhibit_inconsistent", inhibit)
            heat = results.Heat(allow_inconsistent=not inhibit)
            try:
                heat.load_do4(event.src_path)
                scb_filename = f"E{heat.event_num}.scb"
                heat.load_scb(os.path.join(self._options.get_str("start_list_dir"), scb_filename))
            except results.FileParseError:
                pass
            except FileNotFoundError:
                pass
            txn.set_tag("has_discription", heat.event_desc != "")
            txn.set_tag("lanes", self._options.get_int("num_lanes"))
            self._hcb(heat)

def settings_window(root: Tk, options: WahooConfig) -> None:
    '''Display the settings window'''
    # Settings window is fixed size
    root.state("normal")
    root.overrideredirect(False)  # show titlebar
    root.resizable(False, False)
    root.geometry("")  # allow automatic size

    settings: Settings

    def clear_cb():
        image = waiting_screen((1280, 720), options)
        settings.set_preview(image)
        IC.publish(image)

    def test_cb() -> None:
        heat = results.Heat(allow_inconsistent = not options.get_bool("inhibit_inconsistent"))
        #pylint: disable=protected-access
        heat._parse_do4("""432;1;1;All
Lane1;991.03;991.02;
Lane2;48.00;48.00;
Lane3;600.20;600.20;
Lane4;0;0;0
Lane5;312.34;312.34;
Lane6;678.12;679.12;
Lane7;1000.03;1000.03;
Lane8;1000.03;1000.03;
Lane9;1010.03;1010.03;
Lane10;1000.03;1000.03;
F679E29E3D8A4CC4""".split("\n"))
        # Names from https://www.name-generator.org.uk/
        #pylint: disable=protected-access
        heat._parse_scb("""#432 GIRLS 13&O 1650 FREE
MILLER, STEPHANIE   --TEAM1           
DAVIS, SARAH        --TEAM1           
GARCIA, ASHLEY      --TEAM1           
WILSON, JESSICA     --TEAM1           
                    --                
MOORE, SAMANTHA     --TEAM1           
JACKSON, AMBER      --TEAM1           
TAYLOR, MELISSA     --TEAM1           
ANDERSON, RACHEL    --TEAM1           
WHITE, MEGAN        --TEAM1           """.split("\n"))
        heat_cb(heat)

    def selection_cb(enabled_uuids: List[uuid.UUID]) -> None:
        for status in IC.get_devices():
            if status["uuid"] in enabled_uuids:
                IC.enable(status["uuid"], True)
            else:
                IC.enable(status["uuid"], False)

    def watchdir_cb(_dir: str) -> None:
        FILE_WATCHER.unschedule_all()
        path = options.get_str("dolphin_dir")
        if os.path.exists(path):
            FILE_WATCHER.schedule(do4_handler, path)

    def heat_cb(heat: results.Heat) -> None:
        sbi = ScoreboardImage(heat, (1280, 720), options)
        settings.set_preview(sbi.image)
        IC.publish(sbi.image)

    def cast_discovery_cb() -> None:
        items = {}
        for status in IC.get_devices():
            items[status["uuid"]] = {
                "name": status["name"],
                "enabled": status["enabled"]
            }
        settings.set_items(items)

    def manual_publish(img: Image.Image) -> None:
        settings.set_preview(img)
        IC.publish(img)

    def manual_btn_cb() -> None:
        show_manual_chooser(root, manual_publish, options)

    do4_handler = Do4Handler(heat_cb, options)
    path = options.get_str("dolphin_dir")
    if os.path.exists(path):
        FILE_WATCHER.schedule(do4_handler, path)

    settings = Settings(root, generate_dolphin_csv, clear_cb, test_cb,
                        selection_cb, watchdir_cb, manual_btn_cb, options)
    settings.grid(column=0, row=0, sticky="news")

    IC.set_discovery_callback(cast_discovery_cb)
    IC.start()
    clear_cb()

def main():
    '''Runs the Wahoo! Results scoreboard'''
    global FILE_WATCHER  # pylint: disable=global-statement
    global IC  # pylint: disable=global-statement

    # logging.basicConfig(
    #     filename=f'wahoo-results.log',
    #     level=logging.DEBUG,
    #     format='%(asctime)s - %(levelname)s - %(module)s:%(filename)s:%(lineno)d - %(message)s',
    #     )

    # Determine if running as a PyInstaller exe bundle
    dsn = None
    execution_environment = "source"
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        execution_environment = "executable"
        dsn = SENTRY_DSN  # only report if in executable mode

    # Initialize Sentry crash reporting
    sentry_sdk.init(
        dsn=dsn,
        sample_rate=1.0,
        traces_sample_rate=1.0,
        environment=execution_environment,
        release=f"wahoo-results@{WAHOO_RESULTS_VERSION}",
        with_locals=True,
        integrations=[ThreadingIntegration(propagate_hub=True)],
        debug=False,
    )
    uname = platform.uname()
    sentry_sdk.set_tag("os_system", uname.system)
    sentry_sdk.set_tag("os_release", uname.release)
    sentry_sdk.set_tag("os_version", uname.version)
    sentry_sdk.set_tag("os_machine", uname.machine)
    config = WahooConfig()
    sentry_sdk.set_user({
        "id": config.get_str("client_id"),
        "ip_address": "{{auto}}",
    })
    hub = sentry_sdk.Hub.current
    hub.start_session(session_mode="application")

    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

    root = Tk()

    screen_size = f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}"
    sentry_sdk.set_context("display", {
        "size": screen_size,
    })

    root.title("Wahoo! Results")
    icon_file = os.path.abspath(os.path.join(bundle_dir, 'wahoo-results.ico'))
    root.iconbitmap(icon_file)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    FILE_WATCHER = watchdog.observers.Observer()
    FILE_WATCHER.start()

    IC = ImageCast(8011)

    settings_window(root, config)

    # Intercept the close button so we can save the config before destroying
    # the main window and exiting the event loop in case we need to display an
    # error dialog.
    def close_cb():
        try:
            config.save()
        except PermissionError as err:
            messagebox.showerror(title="Error saving configuration",
                message=f'Unable to write configuration file "{err.filename}". {err.strerror}',
                detail="Please ensure the working directory is writable.")
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", close_cb)

    root.mainloop()

    FILE_WATCHER.stop()
    FILE_WATCHER.join()
    IC.stop()

if __name__ == "__main__":
    main()
