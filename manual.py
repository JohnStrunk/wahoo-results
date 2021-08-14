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

'''Wahoo! Results manual loading screen'''

import datetime
import os
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from PIL import Image  # type: ignore

from config import WahooConfig
import results
from settings import Preview
from tooltip import ToolTip
from scoreboardimage import ScoreboardImage

tkContainer = Any

def show_manual_chooser(root: tk.Tk, publish_fn: Callable[[Image.Image],None],
                        config: WahooConfig) -> None:
    """Show a modal window to manually choose a result to show."""
    def dismiss ():
        dlg.grab_release()
        dlg.destroy()

    dlg = tk.Toplevel(root)
    dlg.protocol("WM_DELETE_WINDOW", dismiss) # intercept close button
    dlg.transient(root)   # dialog window is related to main
    dlg.wait_visibility() # can't grab until window appears, so we wait
    dlg.grab_set()        # ensure all input goes to our window
    manual = _DolphinManual(dlg, dismiss, publish_fn, config)
    manual.grid()
    dlg.wait_window()     # block until window is destroyed

class _DolphinManual(ttk.Frame):  # pylint: disable=too-many-ancestors
    _img: Image.Image
    _result: results.Heat

    def __init__(self, container: tkContainer, dismissFn: Callable[[], None],
                 publish_fn: Callable[[Image.Image], None], config: WahooConfig):
        super().__init__(container, padding=2)
        self._config = config
        self._publish_fn = publish_fn
        row0 = ttk.Frame(self, padding=5)
        row0.grid(column=0, row=0, sticky="news")
        row0.columnconfigure(0, weight=0)
        row0.columnconfigure(1, weight=1)
        self._fc = _FileChooser(row0, config, self._file_cb)
        self._fc.grid(column=0, row=0, sticky="news")
        self._fi = _FileInfo(row0, self._spin_cb)
        self._fi.grid(column=1, row=0, sticky="news")

        self._preview = Preview(self)
        self._preview.grid(column=0, row=1, sticky="news")
        row2 = _BottomRow(self, dismissFn, self._publish)
        row2.grid(column=0, row=2, sticky="news")
    def _publish(self) -> None:
        self._publish_fn(self._img)
    def _file_cb(self) -> None:
        allow = not self._config.get_bool("inhibit_inconsistent")
        self._result = results.Heat(allow_inconsistent = allow)
        filename = self._fc.get_selected_file()
        self._result.load_do4(filename)
        self._fi.meet.set(0)
        self._fi.race.set(0)
        # Example .....016-129-005A-0055.do4
        match = re.match(r"^.*[^\d](\d+)-[^-]+-[^-]+-(\d+)\.do4$", filename)
        if match:
            self._fi.meet.set(int(match.group(1)))
            self._fi.race.set(int(match.group(2)))
        finfo = os.stat(filename)
        modified = datetime.datetime.fromtimestamp(finfo.st_mtime, tz=datetime.timezone.utc)
        self._fi.date.set(modified.date().isoformat())
        self._fi.time.set(modified.time().strftime("%I:%M:%S %p"))
        self._fi.event.set(self._result.event)
        self._fi.heat.set(self._result.heat)
        self._spin_cb()
    def _spin_cb(self) -> None:
        self._result.event = self._fi.event.get()
        self._result.heat = int(self._fi.heat.get())
        scb_file = f"E{self._result.event}.scb"
        scb_path = os.path.join(self._config.get_str("start_list_dir"), scb_file)
        try:
            self._result.load_scb(scb_path)
        except results.FileParseError:
            pass
        except FileNotFoundError:
            pass
        self._img = ScoreboardImage(self._result, (1280, 720), self._config).image
        self._preview.set_image(self._img)


class _FileChooser(ttk.LabelFrame): # pylint: disable=too-many-ancestors
    def __init__(self, container: tkContainer, config: WahooConfig, file_cb: Callable[[], None]):
        super().__init__(container, padding=5, text="Race results")
        self._config = config
        self.chooser = tk.StringVar(self)
        # https://bytes.com/topic/python/answers/829768-tkinter-tab-focus-traversal-causes-listbox-selection-clear-ie-lose-selected-item
        self._lbox = tk.Listbox(self, listvariable=self.chooser, width=25, exportselection=0)
        self._lbox.grid(column=0, row=0, sticky="news")
        scr = ttk.Scrollbar(self, orient="vertical", command=self._lbox.yview)
        scr.grid(column=1, row=0, sticky="ns")
        self._lbox.configure(yscrollcommand=scr.set)
        entries = list(os.scandir(config.get_str("dolphin_dir")))
        # Only interested in .do4 files
        entries = [x for x in entries if x.name.endswith(".do4")]
        # Sort, most recent first
        entries.sort(key=lambda e: -e.stat().st_mtime)
        self._names = [x.name for x in entries]
        self.chooser.set(self._names) # type: ignore
        def file_selected(_):
            file_cb()
        self._lbox.bind("<<ListboxSelect>>", file_selected)
        self._lbox.selection_set(0)
        self._lbox.see(0)
    def get_selected_file(self) -> str:
        """Return the path to the currently selected result file"""
        file = self._names[self._lbox.curselection()[0]]
        return os.path.join(self._config.get_str("dolphin_dir"), file)


class _FileInfo(ttk.LabelFrame): # pylint: disable=too-many-ancestors
    def __init__(self, container: tkContainer, spin_cb: Callable[[], None]):
        super().__init__(container, padding=5, text="File information")
        self.columnconfigure(1, weight=1)
        for row in range(0, 7):
            self.rowconfigure(row, weight=1)
        self.meet = tk.IntVar(self)
        tk.Label(self, text="Meet:").grid(column=0, row=0, sticky="w")
        tk.Label(self, textvariable=self.meet).grid(column=1, row=0, sticky="w")
        self.race = tk.IntVar(self)
        tk.Label(self, text="Race:").grid(column=0, row=1, sticky="w")
        tk.Label(self, textvariable=self.race).grid(column=1, row=1, sticky="w")
        self.date = tk.StringVar(self)
        tk.Label(self, text="Date:").grid(column=0, row=2, sticky="w")
        tk.Label(self, textvariable=self.date).grid(column=1, row=2, sticky="w")
        self.time = tk.StringVar(self)
        tk.Label(self, text="Time:").grid(column=0, row=3, sticky="w")
        tk.Label(self, textvariable=self.time).grid(column=1, row=3, sticky="w")
        ttk.Separator(self, orient="horizontal").grid(column=0, row=4,
                      columnspan=2, sticky="ew")
        tk.Label(self, text="Event:").grid(column=0, row=5, sticky="w")
        self.event = tk.StringVar(self)
        ev_spin = ttk.Spinbox(self, increment=1, from_=1, to=999, width=4,
                              justify="right", textvariable=self.event,
                              command=spin_cb)
        ev_spin.grid(column=1, row=5, sticky="w")
        tk.Label(self, text="Heat:").grid(column=0, row=6, sticky="w")
        self.heat = tk.IntVar(self)
        h_spin = ttk.Spinbox(self, increment=1, from_=1, to=999, width=4,
                             justify="right",textvariable=self.heat,
                             command=spin_cb)
        h_spin.grid(column=1, row=6, sticky="w")

class _BottomRow(ttk.Frame):  # pylint: disable=too-many-ancestors
    def __init__(self, container: tkContainer, dismissFn: Callable[[], None],
                 publishFn: Callable[[],None]):
        super().__init__(container, padding=5)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        publishbtn = ttk.Button(self, text="Publish", command=publishFn)
        publishbtn.grid(column=1, row=0, sticky="news")
        ToolTip(publishbtn, text="Publish current preview to scoreboard")
        closebtn = ttk.Button(self, text="Close", command=dismissFn)
        closebtn.grid(column=2, row=0, sticky="news")



def _main():
    config = WahooConfig()

    root = tk.Tk()
    root.resizable(False, False)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    def exitfn() -> None:
        root.destroy()
    def publishfn(_: Image.Image) -> None:
        pass
    manual = _DolphinManual(root, exitfn, publishfn, config)
    manual.grid(column=0, row=0, sticky="news")
    tk.mainloop()

if __name__ == '__main__':
    _main()
