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
import ttkwidgets.font  #type: ignore

from config import WahooConfig
from tooltip import ToolTip
from color_button import ColorButton

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
        ToolTip(btn1, text="Select the directory containing start list files "
        "that have been exported from Meet Manager")
        # row 2: write csv button
        btn2 = ttk.Button(self, text="Write dolphin_events.csv", command=self._handle_write_csv)
        btn2.grid(column=0, row=2, sticky="ew")
        ToolTip(btn2, text="Write a csv file with event information that can "
        "be imported into the Dolphin software")
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
        ToolTip(btn2, text="Choose the directory where the Dolphin software "
        "will write race results. The Dolphin software must be configured to use the .do4 format.")
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
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)
        self._color_swatch("1st place:", "place_1",
                           "Color of 1st place marker text").grid(column=0, row=0, sticky="es")
        self._lanes().grid(column=1, row=0, sticky="es")
        self._color_swatch("Text color:", "color_fg",
                           "Scoreboard foreground text color").grid(column=2, row=0, sticky="es")
        self._color_swatch("2nd place:", "place_2",
                           "Color of 2nd place marker text").grid(column=0, row=1, sticky="es")
        self._color_swatch("Background:", "color_bg",
                           "Scoreboard background color").grid(column=2, row=1, sticky="es")
        self._color_swatch("3rd place:", "place_3",
                           "Color of 3rd place marker text").grid(column=0, row=2, sticky="es")
        self._bg_brightness().grid(column=1, row=2, columnspan=2, sticky="es")
        self._bg_img().grid(column=0, row=3, columnspan=3, sticky="news")
        self._font_chooser("Normal font:", "normal_font",
            "Font for the scoreboard text").grid(column=0, row=4, columnspan=2, sticky="news")
        self._font_chooser("Time font:", "time_font",
            "Font for result times (recommend fixed width font)").grid(column=0,
            row=5, columnspan=2, sticky="news")
        self._font_scale().grid(column=2, row=4, sticky="es")

    def _color_swatch(self, label_text: str, config_item: str, tip_text: str = "") -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        label = ttk.Label(frame, text=label_text)
        label.grid(column=0, row=0, sticky="news")
        cbtn = ColorButton(frame, self._config, config_item)
        cbtn.grid(column=1, row=0, sticky="news")
        if tip_text != "":
            ToolTip(label, tip_text)
            ToolTip(cbtn, tip_text)
        return frame

    def _bg_img(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Background image:").grid(column=0, row=0, sticky="news")
        bgi_text=os.path.basename(self._config.get_str("image_bg"))
        if bgi_text == "":
            bgi_text = "-None-"
        self._set_btn = ttk.Button(frame, text=bgi_text, command=self._browse_bg_image)
        self._set_btn.grid(column=1, row=0, sticky="news")
        ToolTip(self._set_btn, "Set the scoreboard background image")
        clear_btn = ttk.Button(frame, text="Clear", command=self._clear_bg_image)
        clear_btn.grid(column=2, row=0, sticky="news")
        ToolTip(clear_btn, "Remove the scoreboard background image")
        return frame
    def _clear_bg_image(self):
        self._set_btn.configure(text="-None-")
        self._config.set_str("image_bg", "")
    def _browse_bg_image(self):
        image = filedialog.askopenfilename(filetypes=[("image", "*.gif *.jpg *.jpeg *.png")])
        if len(image) == 0:
            return
        image = os.path.normpath(image)
        self._config.set_str("image_bg", image)
        self._set_btn.configure(text=os.path.basename(image))
    def _bg_brightness(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Background image brightness:").grid(column=0, row=0, sticky="nes")
        self._bg_spin_var = StringVar(frame, value=str(self._config.get_float("image_bright")))
        self._bg_spin_var.trace_add("write", self._handle_bg_spin)
        spin = ttk.Spinbox(frame, from_=0, to=1, increment=0.05, width=5,
                           textvariable=self._bg_spin_var)
        spin.grid(column=1, row=0, sticky="news")
        ToolTip(spin, "Brightness of background image [0.0, 1.0]")
        return frame
    def _handle_bg_spin(self, *_arg):
        try:
            value = float(self._bg_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("image_bright", value)
        except ValueError:
            pass

    def _lanes(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Lane count:").grid(column=0, row=0, sticky="news")
        self._lane_spin_var = StringVar(frame, value=str(self._config.get_int("num_lanes")))
        self._lane_spin_var.trace_add("write", self._handle_lane_spin)
        spin = ttk.Spinbox(frame, from_=6, to=10, increment=1, width=3,
                           textvariable=self._lane_spin_var)
        spin.grid(column=1, row=0, sticky="news")
        ToolTip(spin, "Number of lanes to display on the scoreboard")
        return frame
    def _handle_lane_spin(self, *_arg):
        try:
            value = int(self._lane_spin_var.get())
            if 6 <= value <= 10:
                self._config.set_int("num_lanes", value)
        except ValueError:
            pass

    def _font_chooser(self, text, config_option, tooltip) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=0)
        ttk.Label(frame, text=text).grid(column=0, row=0, sticky="nws")
        def callback(fontname):
            self._config.set_str(config_option, fontname)
        dropdown = ttkwidgets.font.FontFamilyDropdown(frame, callback)
        dropdown.set(self._config.get_str(config_option))
        dropdown.grid(column=1, row=0, sticky="news")
        ToolTip(dropdown, tooltip)
        return frame

    def _font_scale(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Font scale:").grid(column=0, row=0, sticky="nes")
        self._font_spin_var = StringVar(frame, value=str(self._config.get_float("font_scale")))
        self._font_spin_var.trace_add("write", self._handle_font_spin)
        spin = ttk.Spinbox(frame, from_=0, to=1, increment=0.01, width=5,
                           textvariable=self._font_spin_var)
        spin.grid(column=1, row=0, sticky="news")
        ToolTip(spin, "Scale of font relative to line height [0.0, 1.0]")
        return frame
    def _handle_font_spin(self, *_arg):
        try:
            value = float(self._font_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("font_scale", value)
        except ValueError:
            pass

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
        ToolTip(test_btn, text="Display a mockup to show the current scoreboard style")
        run_btn = ttk.Button(fr6, text="Run scoreboard", command=self._handle_run_scoreboard_btn)
        run_btn.grid(column=1, row=0, sticky="news")
        ToolTip(run_btn, text="Start the scoreboard and watch for results")

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
    options = WahooConfig()
    settings = Settings(root, None, None, None, options)
    settings.grid(column=0, row=0, sticky="news")
    tk.mainloop()

if __name__ == '__main__':
    main()
