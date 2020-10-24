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

'''Wahoo! Results settings screen'''

import os
import tkinter as tk
from tkinter import filedialog, ttk, StringVar
from typing import Any, Callable

from config import WahooConfig

tkContainer = Any

# Dolphin CSV generator callback
# num_events = CSVGenFn(outfile, dir_to_process)
CSVGenFn = Callable[[str, str], int]
NoneFn = Callable[[], None]

class _StartList(ttk.LabelFrame):   # pylint: disable=too-many-ancestors
    '''The "start list" portion of the settings'''
    def __init__(self, container: tkContainer, csv_cb: CSVGenFn, config: WahooConfig):
        super().__init__(container, padding=5, text="CTS Start list configuration")
        self._config = config
        self._scb_directory = StringVar(value=self._config.get_str("start_list_dir"))
        self._csv_status = StringVar(value="")
        self._csv_cb = csv_cb
        # self is a vertical container
        self.columnconfigure(0, weight=1)
        # row 0: label
        lbl1 = ttk.Label(self, text="Directory for CTS Start List files:")
        lbl1.grid(column=0, row=0, sticky="ws")
        # row 1: browse button & current directory
        # fr1 is horizontal
        fr1 = ttk.Frame(self)
        fr1.grid(column=0, row=1, sticky="news")
        fr1.rowconfigure(0, weight=1)
        scb_dir_label = ttk.Label(fr1, textvariable=self._scb_directory)
        scb_dir_label.grid(column=1, row=0, sticky="ew")
        btn1 = ttk.Button(fr1, text="Browse", command=self._handle_scb_browse)
        btn1.grid(column=0, row=0)
        # row 2: write csv button
        btn2 = ttk.Button(self, text="Write dolphin_events.csv", command=self._handle_write_csv)
        btn2.grid(column=0, row=2, sticky="ew")
        # row 3: status line
        lbl2 = ttk.Label(self, textvariable=self._csv_status, borderwidth=2,
                         relief="sunken", padding=2)
        lbl2.grid(column=0, row=3, sticky="news")


    def _handle_scb_browse(self) -> None:
        directory = filedialog.askdirectory()
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        self._config.set_str("start_list_dir", directory)
        self._scb_directory.set(directory)
        self._csv_status.set("") # clear status line if we change directory

    def _handle_write_csv(self) -> None:
        outfile = "dolphin_events.csv"
        num_events = self._csv_cb(outfile, self._scb_directory.get())
        if num_events == 0:
            self._csv_status.set("WARNING: No events were found. Check your directory.")
        else:
            self._csv_status.set(f"Wrote {num_events} events to {outfile}")


class _DolphinSettings(ttk.Labelframe):  # pylint: disable=too-many-ancestors
    '''Settings for Dolphin'''
    def __init__(self, container: tkContainer, config: WahooConfig):
        super().__init__(container, text="CTS Dolphin configuration", padding=5)
        self._config = config
        self._dolphin_directory = StringVar(value=self._config.get_str("dolphin_dir"))
        # self is a vertical container
        self.columnconfigure(0, weight=1)
        # row 0:
        lbl = ttk.Label(self, text="Directory for CTS Dolphin do4 files:")
        lbl.grid(column=0, row=0, sticky="ws")
        # row 1: browse button & current data dir
        # fr2 is horizontal
        fr2 = ttk.Frame(self)
        fr2.rowconfigure(0, weight=1)
        fr2.grid(column=0, row=1, sticky="news")
        btn2 = ttk.Button(fr2, text="Browse", command=self._handle_do4_browse)
        btn2.grid(column=0, row=0)
        dolphin_dir_label = ttk.Label(fr2, textvariable=self._dolphin_directory)
        dolphin_dir_label.grid(column=1, row=0, sticky="ew")

    def _handle_do4_browse(self) -> None:
        directory = filedialog.askdirectory()
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        self._config.set_str("dolphin_dir", directory)
        self._dolphin_directory.set(directory)

class _GeneralSettings(ttk.LabelFrame):  # pylint: disable=too-many-ancestors
    '''Miscellaneous settings'''
    def __init__(self, container: tkContainer, config: WahooConfig):
        super().__init__(container, text="General Settings", padding=5)
        self._config = config
        self.columnconfigure(0, weight=1)
        lbl3 = ttk.Label(self, text="more stuff here...")
        lbl3.grid(column=0, row=0, sticky="ws")

class Settings(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Main settings window'''

    # pylint: disable=too-many-arguments
    def __init__(self, container: tkContainer, csv_cb: CSVGenFn,
                 scoreboard_run_cb: NoneFn, test_run_cb: NoneFn, config: WahooConfig):
        super().__init__(container, padding=5)
        self._config = config
        self._scoreboard_run_cb = scoreboard_run_cb
        self._test_run_cb = test_run_cb
        self.grid(column=0, row=0, sticky="news")
        self.columnconfigure(0, weight=1)
        # Odd rows are empty filler to distribute vertical whitespace
        for i in [1, 3, 5]:
            self.rowconfigure(i, weight=1)
        # row 0: Start list settings
        startlist = _StartList(self, csv_cb, self._config)
        startlist.grid(column=0, row=0, sticky="news")
        # row 2: Dolphin settings
        dolphin = _DolphinSettings(self, self._config)
        dolphin.grid(column=0, row=2, sticky="news")
        # row 4: General settings
        general = _GeneralSettings(self, self._config)
        general.grid(column=0, row=4, sticky="news")
        # row 6: run button(s)
        fr6 = ttk.Frame(self)
        fr6.grid(column=0, row=6, sticky="news")
        fr6.rowconfigure(0, weight=1)
        fr6.columnconfigure(0, weight=0)
        fr6.columnconfigure(1, weight=1)
        test_btn = ttk.Button(fr6, text="Test", command=self._handle_test_btn)
        test_btn.grid(column=0, row=0, sticky="news")
        run_btn = ttk.Button(fr6, text="Run scoreboard", command=self._handle_run_scoreboard_btn)
        run_btn.grid(column=1, row=0, sticky="news")

    def _handle_run_scoreboard_btn(self) -> None:
        self.destroy()
        self._scoreboard_run_cb()

    def _handle_test_btn(self) -> None:
        self.destroy()
        self._test_run_cb()

def main():
    '''testing'''
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.resizable(False, False)
    root.geometry("400x300")
    options = WahooConfig()
    settings = Settings(root, None, None, None, options)
    settings.grid(column=0, row=0, sticky="news")
    tk.mainloop()

if __name__ == '__main__':
    main()
