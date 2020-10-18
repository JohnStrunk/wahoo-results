'''Wahoo! Results scoreboard'''

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

import configparser
import os
import time
from tkinter import StringVar, Tk, Widget
from tkinter import filedialog
from tkinter import ttk
from typing import List
from PIL import Image  #type: ignore
from PIL.ImageEnhance import Brightness  #type: ignore
import watchdog.events  #type: ignore
import watchdog.observers  #type: ignore

import results
from scoreboard import Scoreboard

# Name of the configuration file
CONFIG_FILE = "wahoo-results.ini"
# Name of the section we use in the ini file
INI_HEADING = "wahoo-results"
# Configuration defaults if not present in the config file
CONFIG_DEFAULTS = {INI_HEADING: {
    "dolphin_dir": "c:\\CTSDolphin",
    "start_list_dir": "c:\\swmeets8",
    "num_lanes": "10",
    "color_bg": "black",
    "color_fg": "white",
}}
FILE_WATCHER: watchdog.observers.Observer

def config_load() -> configparser.ConfigParser:
    """Load values from the configuration file."""
    config = configparser.ConfigParser()
    config.read_dict(CONFIG_DEFAULTS)
    config.read(CONFIG_FILE)
    return config

def config_save(options: configparser.ConfigParser) -> None:
    """Save the configuration"""
    with open(CONFIG_FILE, 'w') as configfile:
        options.write(configfile)

def eventlist_to_csv(events: List[results.Event]) -> List[str]:
    '''Converts a list of events into CSV format'''
    lines: List[str] = []
    for i in events:
        lines.append(f"{i.event},{i.event_desc},{i.num_heats},1,A\n")
    return lines

def generate_dolphin_csv(directory: str) -> str:
    """
    Write the events from the scb files in the given directory into a CSV
    for Dolphin.
    """
    filename = "dolphin_events.csv"
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
    csv = open(outfile, "w")
    csv.writelines(csv_lines)
    csv.close()
    if len(events) == 0:
        return "WARNING: No events were found. Check your directory."
    return f'Wrote {len(events)} events to {filename}'

class Do4Handler(watchdog.events.PatternMatchingEventHandler):
    '''Handler to process Dolphin .do4 files'''
    _sb: Scoreboard
    _options: configparser.ConfigParser
    def __init__(self, scoreboard: Scoreboard, options: configparser.ConfigParser):
        self._sb = scoreboard
        self._options = options
        super().__init__(patterns=["*.do4"], ignore_directories=True)
    def on_created(self, event):
        print(f"Triggered by: {event.src_path}")
        time.sleep(1)
        heat = results.Heat()
        heat.load_do4(event.src_path)
        scb_filename = f"E{heat.event}.scb"
        heat.load_scb(os.path.join(self._options[INI_HEADING]["start_list_dir"], scb_filename))
        display(self._sb, heat)

def settings_start_list(container: Widget, options: configparser.ConfigParser) -> Widget:
    """Elements for the Start List portion of the settings screen."""

    # The directory containing the scb start lists
    scb_directory = StringVar(value=options[INI_HEADING]["start_list_dir"])
    # The status line
    csv_status = StringVar(value="")

    def handle_scb_browse():
        directory = filedialog.askdirectory()
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        options[INI_HEADING]["start_list_dir"] = directory
        scb_directory.set(options[INI_HEADING]["start_list_dir"])
        csv_status.set("") # clear status line if we change directory
    def handle_write_csv():
        csv_status.set(generate_dolphin_csv(scb_directory.get()))

    # labelframe to hold start list settings
    # lf_startlist is vertical
    lf_startlist = ttk.Labelframe(container, text='CTS Start list configuration', padding=5)
    lf_startlist.columnconfigure(0, weight=1)

    lbl1 = ttk.Label(lf_startlist, text="Directory for CTS Start List files:")
    lbl1.grid(column=0, row=0, sticky="ws")

    # f1 holds browse button & current dir
    # f1 is horizontal
    fr1 = ttk.Frame(lf_startlist)
    fr1.rowconfigure(0, weight=1)
    fr1.grid(column=0, row=1, sticky="news")

    scb_dir_label = ttk.Label(fr1, textvariable=scb_directory)
    scb_dir_label.grid(column=1, row=0, sticky="ew")

    btn1 = ttk.Button(fr1, text="Browse", command=handle_scb_browse)
    btn1.grid(column=0, row=0)

    btn2 = ttk.Button(lf_startlist, text="Write dolphin_events.csv", command=handle_write_csv)
    btn2.grid(column=0, row=2, sticky="ew")
    lbl2 = ttk.Label(lf_startlist, textvariable=csv_status, borderwidth=2,
                     relief="sunken", padding=2)
    lbl2.grid(column=0, row=3, sticky="news")
    return lf_startlist

def settings_dolphin(container: Widget, options: configparser.ConfigParser) -> Widget:
    """Dolphin configuration portion of the settings screen."""
    dolphin_directory = StringVar(value=options[INI_HEADING]["dolphin_dir"])
    def handle_do4_browse():
        directory = filedialog.askdirectory()
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        options[INI_HEADING]["dolphin_dir"] = directory
        dolphin_directory.set(options[INI_HEADING]["dolphin_dir"])

    # labelframe to hold Dolphin settings
    # lf_dolphin is vertical
    lf_dolphin = ttk.Labelframe(container, text='CTS Dolphin configuration', padding=5)
    lf_dolphin.columnconfigure(0, weight=1)
    lbl2 = ttk.Label(lf_dolphin, text="Directory for CTS Dolphin do4 files:")
    lbl2.grid(column=0, row=0, sticky="ws")

    # f2 holds browse button & current data dir
    # f2 is horizontal
    fr2 = ttk.Frame(lf_dolphin)
    fr2.rowconfigure(0, weight=1)
    fr2.grid(column=0, row=1, sticky="news")
    btn2 = ttk.Button(fr2, text="Browse", command=handle_do4_browse)
    btn2.grid(column=0, row=0)
    dolphin_dir_label = ttk.Label(fr2, textvariable=dolphin_directory)
    dolphin_dir_label.grid(column=1, row=0, sticky="ew")
    return lf_dolphin

def settings_general(container: Widget, _: configparser.ConfigParser) -> Widget:
    """General settings portion of the settings screen."""
    # labelframe to hold general settings
    # lf_general is vertical
    lf_general = ttk.LabelFrame(container, text="General settings", padding=5)
    lf_general.columnconfigure(0, weight=1)
    lbl3 = ttk.Label(lf_general, text="This is too complicated")
    lbl3.grid(column=0, row=0, sticky="ws")
    return lf_general

def settings_window(root: Tk, options: configparser.ConfigParser) -> Widget:
    '''Display the settings window'''
    # don't watch for new results while in settings menu
    FILE_WATCHER.unschedule_all()

    # Settings window is fixed size
    root.resizable(False, False)
    root.geometry("400x300")

    # Invisible container that holds all content
    content = ttk.Frame(root, padding=5)
    content.grid(column=0, row=0, sticky="news")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(1, weight=1)
    content.rowconfigure(3, weight=1)
    content.rowconfigure(5, weight=1)

    startlist = settings_start_list(content, options)
    startlist.grid(column=0, row=0, sticky="news")

    dolphin = settings_dolphin(content, options)
    dolphin.grid(column=0, row=2, sticky="news")

    general = settings_general(content, options)
    general.grid(column=0, row=4, sticky="news")

    def handle_scoreboard() -> None:
        content.destroy()
        scoreboard_window(root, options)

    scoreboard = ttk.Button(content, text="Run scoreboard", command=handle_scoreboard)
    scoreboard.grid(column=0, row=6, sticky="news")

    return content

def scoreboard_window(root: Tk, options: configparser.ConfigParser) -> Widget:
    """Displays the scoreboard window."""
    # Scoreboard is varible size
    root.resizable(True, True)
    content = Scoreboard(root)
    content.grid(column=0, row=0, sticky="news")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(0, weight=1)
    image = Image.open('rsa2.png')
    content.bg_image(Brightness(image).enhance(0.25), "fit")
    content.set_lanes(int(options[INI_HEADING]["num_lanes"]))

    def return_to_settings(_) -> None:
        root.unbind('<Double-1>')
        content.destroy()
        root.state('normal') # Un-maximize
        settings_window(root, options)
    root.bind('<Double-1>', return_to_settings)

    # Start watching for new results
    do4_handler = Do4Handler(content, options)
    FILE_WATCHER.schedule(do4_handler, options[INI_HEADING]["dolphin_dir"])

    return content

def display(board: Scoreboard, heat: results.Heat) -> None:
    """
    Display the results of a heat.
    """
    board.clear()
    board.event(heat.event, heat.event_desc)
    board.heat(heat.heat)

    for i in range(0, 10):
        if not heat.lanes[i].is_empty():
            ftime = heat.lanes[i].final_time()
            place = heat.place(i)
            if not heat.lanes[i].times_are_valid():
                ftime = -ftime
                place = 0
            board.lane(i+1, heat.lanes[i].name, heat.lanes[i].team, ftime, place)
    heat.dump()

def main():
    '''Runs the Wahoo! Results scoreboard'''
    global FILE_WATCHER  # pylint: disable=W0603

    config = config_load()

    root = Tk()
    root.title("Wahoo! Results")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    FILE_WATCHER = watchdog.observers.Observer()
    FILE_WATCHER.start()

    settings_window(root, config)
    root.mainloop()

    config_save(config)
    FILE_WATCHER.stop()
    FILE_WATCHER.join()

if __name__ == "__main__":
    main()
