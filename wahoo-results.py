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
import threading
import time
from tkinter import font, StringVar, Tk, Widget
from tkinter import filedialog
from tkinter import ttk
from typing import Dict, List
import watchdog.events
import watchdog.observers

import results

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
    lines: List[str] = []
    for e in events:
        lines.append(f"{e.event},{e.event_desc},{e.num_heats},1,A\n")
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
            ev = results.Event()
            ev.from_scb(file.path)
            events.append(ev)
    events.sort(key=lambda e: e.event)
    csv_lines = eventlist_to_csv(events)
    outfile = os.path.join(directory, filename)
    csv = open(outfile, "w")
    csv.writelines(csv_lines)
    csv.close()
    if len(events) == 0:
        return "WARNING: No events were found. Check your directory."
    return f'Wrote {len(events)} events to {filename}'

class ScoreboardResults():
    event_number: StringVar
    event_desc: StringVar
    heat: StringVar
    lanes: List[Dict[str, StringVar]]
    font: font.Font
    num_lanes: int

    @classmethod
    def format_time(cls, time: float) -> str:
        """
        >>> ScoreboardResults.format_time(1.2)
        '01.20'
        >>> ScoreboardResults.format_time(9.87)
        '09.87'
        >>> ScoreboardResults.format_time(50)
        '50.00'
        >>> ScoreboardResults.format_time(120.0)
        '2:00.00'
        """
        minutes = int(time//60)
        seconds = time - minutes*60.0
        if minutes == 0:
            return f"{seconds:05.2f}"
        return f"{minutes}:{seconds:05.2f}"

    @classmethod
    def format_place(cls, place: int) -> str:
        """
        >>> ScoreboardResults.format_place(1)
        '1st'
        >>> ScoreboardResults.format_place(6)
        '6th'
        """
        if place == 0:
            return ""
        if place == 1:
            return "1st"
        if place == 2:
            return "2nd"
        if place == 3:
            return "3rd"
        return f"{place}th"

    def __init__(self):
        self.event_number = StringVar()
        self.event_desc = StringVar()
        self.heat = StringVar()
        self.lanes = []
        self.font = font.Font(family='Helvetica', size=12, weight='bold')
        for i in range(0, 10):
            lane = {"lane": StringVar(),
                    "place": StringVar(),
                    "name": StringVar(),
                    "team": StringVar(),
                    "time": StringVar()}
            lane["lane"].set(str(i+1))
            self.lanes.append(lane)

    def clear(self):
        """Clear the scoreboard."""
        self.event_number.set("")
        self.event_desc.set("")
        self.heat.set("")
        for i in range(0, 10):
            self.lanes[i]["lane"].set(str(i+1))
            for j in ["place", "name", "team", "time"]:
                self.lanes[i][j].set("")

    def _resize_font(self, event):
        widget = event.widget
        height = widget.winfo_height()
        self.font["size"] = int(-height * 0.5)

    def _sb_grid(self, container: Widget, options: configparser.ConfigParser) -> Widget:
        self.num_lanes = int(options[INI_HEADING]["num_lanes"])
        content = ttk.Frame(container, padding=5, style="Scoreboard.TFrame")
        for i in range(0, 7):
            content.columnconfigure(i, weight=1)
        for i in range(0, self.num_lanes + 4):
            if i not in (1, 3):
                content.rowconfigure(i, weight=10)
                content.rowconfigure(i, uniform="g1")
        content.rowconfigure(1, weight=1, uniform="sep")
        content.rowconfigure(3, weight=1, uniform="sep")

        levent = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                           textvariable=self.event_number, anchor="w", font=self.font)
        levent.grid(column=0, row=0, columnspan=2, sticky="news")
        lheat = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                          textvariable=self.heat, anchor="w", font=self.font)
        lheat.grid(column=2, row=0, columnspan=2, sticky="news")
        ledesc = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                          textvariable=self.event_desc, anchor="e", font=self.font)
        ledesc.grid(column=4, row=0, columnspan=3, sticky="news")

        llane = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                          text="Lane", anchor="center", font=self.font)
        llane.bind("<Configure>", self._resize_font)
        llane.grid(column=0, row=2, sticky="news")
        lplace = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                           text="Place", anchor="center", font=self.font)
        lplace.grid(column=1, row=2, sticky="news")
        lname = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                          text="Name", anchor="w", font=self.font)
        lname.grid(column=2, row=2, columnspan=4, sticky="news")
        # lteam = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
        #                   text="Team", anchor="w", font=self.font)
        # lteam.grid(column=5, row=2, sticky="news")
        ltime = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                          text="Time", anchor="e", font=self.font)
        ltime.grid(column=6, row=2, sticky="news")
        divider = ttk.Separator(content, orient="horizontal")
        divider.grid(column=0, row=3, columnspan=7, sticky="news")

        for i in range(0, self.num_lanes):
            llbl = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                             textvariable=self.lanes[i]["lane"], anchor="center", font=self.font)
            llbl.grid(column=0, row=i+4, sticky="news")
            plbl = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                             textvariable=self.lanes[i]["place"], anchor="center", font=self.font)
            plbl.grid(column=1, row=i+4, sticky="news")
            nlbl = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                             textvariable=self.lanes[i]["name"], anchor="w", font=self.font)
            nlbl.grid(column=2, row=i+4, columnspan=4, sticky="news")
            # tlbl = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
            #                  textvariable=self.lanes[i]["team"], anchor="w", font=self.font)
            # tlbl.grid(column=5, row=i+4, sticky="news")
            wlbl = ttk.Label(content, padding=5, style="Scoreboard.TLabel",
                             textvariable=self.lanes[i]["time"], anchor="e", font=self.font)
            wlbl.grid(column=6, row=i+4, sticky="news")
        return content

    def scoreboard(self, container: Tk, options: configparser.ConfigParser) -> Widget:
        """Render the scoreboard."""
        style = ttk.Style()
        style.configure("Scoreboard.TFrame",
                        background=options[INI_HEADING]["color_bg"],
                        foreground=options[INI_HEADING]["color_fg"])
        style.configure("Scoreboard.TLabel",
                        background=options[INI_HEADING]["color_bg"],
                        foreground=options[INI_HEADING]["color_fg"])

        # vertical
        content = ttk.Frame(container, padding=5, style="Scoreboard.TFrame")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        grid = self._sb_grid(content, options)
        grid.grid(column=0, row=0, sticky="news")

        self.clear()
        return content

    def display(self, heat: results.Heat) -> None:
        """
        Display the results of a heat.
        """
        self.clear()
        self.event_number.set(f"Event: {heat.event}")
        self.event_desc.set(heat.event_desc)
        self.heat.set(f"Heat: {heat.heat}")

        for i in range(0, self.num_lanes):
            if not heat.lanes[i].is_empty():
                self.lanes[i]["name"].set(heat.lanes[i].name)
                self.lanes[i]["team"].set(heat.lanes[i].team)
                if heat.lanes[i].times_are_valid():
                    self.lanes[i]["place"].set(ScoreboardResults.format_place(heat.place(i)))
                    self.lanes[i]["time"].set(ScoreboardResults.format_time(heat.lanes[i].final_time()))
                else:
                    self.lanes[i]["time"].set("--:--.--")
        heat.dump()

class Do4Handler(watchdog.events.PatternMatchingEventHandler):
    _sb: ScoreboardResults
    _options: configparser.ConfigParser
    def __init__(self, scoreboard: ScoreboardResults, options: configparser.ConfigParser):
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
        self._sb.display(heat)

file_watcher: watchdog.observers.Observer
do4_handler: Do4Handler
sb: ScoreboardResults

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

    l1 = ttk.Label(lf_startlist, text="Directory for CTS Start List files:")
    l1.grid(column=0, row=0, sticky="ws")

    # f1 holds browse button & current dir
    # f1 is horizontal
    f1 = ttk.Frame(lf_startlist)
    f1.rowconfigure(0, weight=1)
    f1.grid(column=0, row=1, sticky="news")

    scb_dir_label = ttk.Label(f1, textvariable=scb_directory)
    scb_dir_label.grid(column=1, row=0, sticky="ew")

    b1 = ttk.Button(f1, text="Browse", command=handle_scb_browse)
    b1.grid(column=0, row=0)

    b2 = ttk.Button(lf_startlist, text="Write dolphin_events.csv", command=handle_write_csv)
    b2.grid(column=0, row=2, sticky="ew")
    l2 = ttk.Label(lf_startlist, textvariable=csv_status, borderwidth=2, relief="sunken", padding=2)
    l2.grid(column=0, row=3, sticky="news")
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
    l2 = ttk.Label(lf_dolphin, text="Directory for CTS Dolphin do4 files:")
    l2.grid(column=0, row=0, sticky="ws")

    # f2 holds browse button & current data dir
    # f2 is horizontal
    f2 = ttk.Frame(lf_dolphin)
    f2.rowconfigure(0, weight=1)
    f2.grid(column=0, row=1, sticky="news")
    b2 = ttk.Button(f2, text="Browse", command=handle_do4_browse)
    b2.grid(column=0, row=0)
    dolphin_dir_label = ttk.Label(f2, textvariable=dolphin_directory)
    dolphin_dir_label.grid(column=1, row=0, sticky="ew")
    return lf_dolphin

def settings_general(container: Widget, options: configparser.ConfigParser) -> Widget:
    """General settings portion of the settings screen."""
    # labelframe to hold general settings
    # lf_general is vertical
    lf_general = ttk.LabelFrame(container, text="General settings", padding=5)
    lf_general.columnconfigure(0, weight=1)
    l3 = ttk.Label(lf_general, text="This is too complicated")
    l3.grid(column=0, row=0, sticky="ws")
    return lf_general

def settings_window(root: Tk, options: configparser.ConfigParser) -> Widget:
    # don't watch for new results while in settings menu
    file_watcher.unschedule_all()

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
    content = sb.scoreboard(root, options)
    content.grid(column=0, row=0, sticky="news")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(0, weight=1)

    def return_to_settings(_) -> None:
        content.destroy()
        root.unbind('<Double-1>')
        root.state('normal') # Un-maximize
        settings_window(root, options)
    root.bind('<Double-1>', return_to_settings)

    # Start watching for new results
    file_watcher.schedule(do4_handler, options[INI_HEADING]["dolphin_dir"])

    return content

def main():
    global sb
    global do4_handler
    global file_watcher

    config = config_load()

    root = Tk()
    root.title("Wahoo! Results")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    sb = ScoreboardResults()
    do4_handler = Do4Handler(sb, config)
    file_watcher = watchdog.observers.Observer()
    file_watcher.start()

    settings_window(root, config)

    root.mainloop()

    config_save(config)
    file_watcher.stop()
    file_watcher.join()

if __name__ == "__main__":
    main()
