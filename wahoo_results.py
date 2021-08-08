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
import sys
import time
import uuid
from tkinter import Tk
from typing import Callable, List

import sentry_sdk
from sentry_sdk.integrations.threading import ThreadingIntegration
import watchdog.events  #type: ignore
import watchdog.observers  #type: ignore

import analytics
from imagecast import ImageCast
from config import WahooConfig
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
        lines.append(f"{i.event},{i.event_desc},{i.num_heats},1,A\n")
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
    events.sort(key=lambda e: e.event)
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
        heat = results.Heat(allow_inconsistent=not self._options.get_bool("inhibit_inconsistent"))
        try:
            heat.load_do4(event.src_path)
            scb_filename = f"E{heat.event}.scb"
            heat.load_scb(os.path.join(self._options.get_str("start_list_dir"), scb_filename))
        except results.FileParseError:
            pass
        except FileNotFoundError:
            pass
        self._hcb(heat)

def settings_window(root: Tk, options: WahooConfig) -> None:
    '''Display the settings window'''
    analytics.screen_view("settings_window")

    # Settings window is fixed size
    root.state("normal")
    root.overrideredirect(False)  # show titlebar
    root.resizable(False, False)
    root.geometry("")  # allow automatic size

    settings: Settings

    def clear_cb():
        analytics.send_event("clear_screen")
        image = waiting_screen((1280, 720), options)
        settings.set_preview(image)
        IC.publish(image)

    def test_cb() -> None:
        analytics.send_event("test_screen")
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
        FILE_WATCHER.schedule(do4_handler, options.get_str("dolphin_dir"))

    def heat_cb(heat: results.Heat) -> None:
        num_cc = len([x for x in IC.get_devices() if x["enabled"]])
        analytics.send_event("race_result", {
            "has_description": int(heat.event_desc != ""),
            "lanes": options.get_int("num_lanes"),
            "inhibit": int(options.get_bool("inhibit_inconsistent")),
            "devices": num_cc,
        })
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

    do4_handler = Do4Handler(heat_cb, options)
    FILE_WATCHER.schedule(do4_handler, options.get_str("dolphin_dir"))

    settings = Settings(root, generate_dolphin_csv, clear_cb, test_cb,
                        selection_cb, watchdir_cb, options)
    settings.grid(column=0, row=0, sticky="news")

    IC.set_discovery_callback(cast_discovery_cb)
    IC.start()
    clear_cb()

def main():
    '''Runs the Wahoo! Results scoreboard'''
    global FILE_WATCHER  # pylint: disable=global-statement
    global IC  # pylint: disable=global-statement

    # Determine if running as a PyInstaller exe bundle
    execution_environment = "source"
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        execution_environment = "executable"

    # pylint: disable=abstract-class-instantiated
    # https://github.com/getsentry/sentry-python/issues/1081
    # Initialize Sentry crash reporting
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        sample_rate=1.0,
        traces_sample_rate=1.0,
        environment=execution_environment,
        release=f"wahoo-results@{WAHOO_RESULTS_VERSION}",
        with_locals=True,
        integrations=[ThreadingIntegration(propagate_hub=True)],
        #debug=True,
    )
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
    analytics.send_application_start(config, screen_size)

    root.title("Wahoo! Results")
    icon_file = os.path.abspath(os.path.join(bundle_dir, 'wahoo-results.ico'))
    root.iconbitmap(icon_file)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    FILE_WATCHER = watchdog.observers.Observer()
    FILE_WATCHER.start()

    IC = ImageCast(8011)

    settings_window(root, config)
    root.mainloop()

    config.save()
    FILE_WATCHER.stop()
    FILE_WATCHER.join()
    IC.stop()
    analytics.send_application_stop()

if __name__ == "__main__":
    main()
