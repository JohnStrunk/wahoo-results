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
from tkinter import filedialog, ttk, BooleanVar, StringVar
from typing import Any, Callable, List, Optional
from uuid import UUID
from PIL import Image, ImageTk #type: ignore

import ttkwidgets  #type: ignore
import ttkwidgets.font  #type: ignore

from config import WahooConfig
from tooltip import ToolTip
from widgets import ColorButton
import wh_version
import wh_analytics
from version import WAHOO_RESULTS_VERSION

tkContainer = Any

# Dolphin CSV generator callback
# num_events = CSVGenFn(outfile, dir_to_process)
CSVGenFn = Callable[[str, str], int]

NoneFn = Callable[[], None]

# Chromecast selection callback
# SelectionFn(enabled_uuids)
SelectionFn = Callable[[List[UUID]], None]

WatchdirFn = Callable[[str], None]

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
            wh_analytics.set_cts_directory(False)
            return
        directory = os.path.normpath(directory)
        self._config.set_str("start_list_dir", directory)
        self._scb_directory.set(directory)
        self._csv_status.set("") # clear status line if we change directory
        wh_analytics.set_cts_directory(True)

    def _handle_write_csv(self) -> None:
        outfile = "dolphin_events.csv"
        num_events = self._csv_cb(outfile, self._scb_directory.get())
        if num_events == 0:
            self._csv_status.set("WARNING: No events were found. Check your directory.")
        else:
            self._csv_status.set(f"Wrote {num_events} events to {outfile}")
        wh_analytics.wrote_dolphin_csv(num_events)


class _DolphinSettings(ttk.Labelframe):  # pylint: disable=too-many-ancestors
    '''Settings for Dolphin'''
    def __init__(self, container: tkContainer, watchdir_cb: WatchdirFn, config: WahooConfig):
        super().__init__(container, text="CTS Dolphin configuration", padding=5)
        self._config = config
        self._watchdir_cb = watchdir_cb
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
            wh_analytics.set_do4_directory(False)
            return
        directory = os.path.normpath(directory)
        self._config.set_str("dolphin_dir", directory)
        self._dolphin_directory.set(directory)
        if self._watchdir_cb is not None:
            self._watchdir_cb(directory)
        wh_analytics.set_do4_directory(True)

class _GeneralSettings(ttk.LabelFrame):  # pylint: disable=too-many-ancestors,too-many-instance-attributes
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
        self.rowconfigure(6, weight=1)
        self._color_swatch("1st place:", "place_1",
                           "Color of 1st place marker text").grid(column=0, row=0, sticky="es")
        self._lanes().grid(column=1, row=0, sticky="es")
        self._color_swatch("Text color:", "color_fg",
                           "Scoreboard foreground text color").grid(column=2, row=0, sticky="es")
        self._color_swatch("2nd place:", "place_2",
                           "Color of 2nd place marker text").grid(column=0, row=1, sticky="es")
        self._inhibit().grid(column=1, row=1, sticky="es")
        self._color_swatch("Background:", "color_bg",
                           "Scoreboard background color").grid(column=2, row=1, sticky="es")
        self._color_swatch("3rd place:", "place_3",
                           "Color of 3rd place marker text").grid(column=0, row=2, sticky="es")
        self._color_swatch("Title color:", "color_ehd",
            "Scoreboard event, heat, and description text color").grid(column=2, row=2, sticky="es")
        self._bg_img().grid(column=0, row=3, columnspan=3, sticky="news")
        self._bg_brightness().grid(column=0, row=4, columnspan=2, sticky="ws")
        self._bg_scale().grid(column=2, row=4, sticky="news")
        self._font_chooser("Normal font:", "normal_font",
            "Font for the scoreboard text").grid(column=0, row=5, columnspan=2, sticky="news")
        self._font_scale().grid(column=2, row=5, sticky="es")
        self._font_chooser("Time font:", "time_font",
            "Font for result times (recommend fixed width font)").grid(column=0,
            row=6, columnspan=2, sticky="news")

    def _color_swatch(self, label_text: str, config_item: str, tip_text: str = "") -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label_text).grid(column=0, row=0, sticky="news")
        ColorButton(frame, self._config, config_item).grid(column=1, row=0, sticky="news")
        if tip_text != "":
            ToolTip(frame, tip_text)
        return frame

    def _bg_img(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Background image:").grid(column=0, row=0, sticky="news")
        bgi_text=os.path.basename(self._config.get_str("image_bg"))
        if bgi_text == "":
            bgi_text = "-None-"
        self._set_btn = ttk.Button(frame, text=bgi_text[0:20], command=self._browse_bg_image)
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
        self._set_btn.configure(text=os.path.basename(image)[0:20])
    def _bg_brightness(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Image brightness:").grid(column=0, row=0, sticky="nes")
        self._bg_spin_var = StringVar(frame, value=str(self._config.get_float("image_bright")))
        self._bg_spin_var.trace_add("write", self._handle_bg_spin)
        ttk.Spinbox(frame, from_=0, to=1, increment=0.05, width=5,
                    textvariable=self._bg_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Brightness of background image [0.0, 1.0]")
        return frame
    def _handle_bg_spin(self, *_arg):
        try:
            value = float(self._bg_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("image_bright", value)
        except ValueError:
            pass
    def _bg_scale(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Scale:").grid(column=0, row=0, sticky="nes")
        self._bg_scale_var = StringVar(frame, value=str(self._config.get_str("image_scale")))
        self._bg_scale_var.trace_add("write", self._handle_bg_scale)
        ttk.Combobox(frame, state="readonly", textvariable=self._bg_scale_var,
                     values=["none", "cover", "fit", "stretch"],
                     width=7).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "How to scale the background image\nnone: as-is\n"
            "cover: cover screen\nfit: fit within screen\nstretch: stretch all dimensions")
        return frame
    def _handle_bg_scale(self, *_arg):
        self._config.set_str("image_scale", self._bg_scale_var.get())

    def _lanes(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Lane count:").grid(column=0, row=0, sticky="news")
        self._lane_spin_var = StringVar(frame, value=str(self._config.get_int("num_lanes")))
        self._lane_spin_var.trace_add("write", self._handle_lane_spin)
        ttk.Spinbox(frame, from_=6, to=10, increment=1, width=3,
                    textvariable=self._lane_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Number of lanes to display on the scoreboard")
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
        ToolTip(frame, tooltip)
        return frame

    def _font_scale(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Font scale:").grid(column=0, row=0, sticky="nes")
        self._font_spin_var = StringVar(frame, value=str(self._config.get_float("font_scale")))
        self._font_spin_var.trace_add("write", self._handle_font_spin)
        ttk.Spinbox(frame, from_=0, to=1, increment=0.01, width=5,
                           textvariable=self._font_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Scale of font relative to line height [0.0, 1.0]")
        return frame
    def _handle_font_spin(self, *_arg):
        try:
            value = float(self._font_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("font_scale", value)
        except ValueError:
            pass

    def _inhibit(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Suppress >0.3s:").grid(column=0, row=0, sticky="nes")
        self._inhibit_var = BooleanVar(frame, value=self._config.get_bool("inhibit_inconsistent"))
        ttk.Checkbutton(frame, variable=self._inhibit_var,
            command=self._handle_inhibit).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Select to suppress final time if times differ by more than 0.3s")
        return frame
    def _handle_inhibit(self, *_arg):
        self._config.set_bool("inhibit_inconsistent", self._inhibit_var.get())

class _CCChooser(ttk.LabelFrame):  # pylint: disable=too-many-ancestors
    def __init__(self, container: tkContainer, selection_cb: SelectionFn):
        super().__init__(container, padding=5, text="Chromecast devices")
        cc_chooser = ttk.Treeview(self, selectmode="extended", show="tree")
        cc_chooser.grid(column=0, row=0, sticky="news")
        self._chooser = cc_chooser
        self._selection_cb = selection_cb
        ToolTip(self, "Select which Chromecast devices should display the "
                "scoreboard. Use <ctrl> or <shift> to select multiple devices.")

    def set_items(self, items):
        '''Set the list of chromecast devices and indicate whether they are enabled'''
        # items is dict[uuid]-> {"name": str, "enabled": bool}
        for existing in self._chooser.get_children():
            self._chooser.delete(existing)
        for uuid, prop in items.items():
            self._chooser.insert("", 'end', uuid, text=prop["name"], tags="item")
            if prop["enabled"]:
                self._chooser.selection_add(uuid)
        self._chooser.tag_bind("item", "<<TreeviewSelect>>", self._handle_selection)

    def _handle_selection(self, *_arg):
        selected = [UUID(u) for u in self._chooser.selection()]
        if self._selection_cb is not None:
            self._selection_cb(selected)

class Preview(ttk.LabelFrame):  # pylint: disable=too-many-ancestors
    """A widget that displays a scoreboard preview image"""
    WIDTH = 320
    HEIGHT = 180
    _pimage: Optional[ImageTk.PhotoImage]
    def __init__(self, container: tkContainer):
        super().__init__(container, padding=5, text="Scoreboard preview")
        canvas = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT)
        canvas.grid(column=0, row=0, padx=3, pady=3)
        self._canvas = canvas
        self._pimage = None
        ToolTip(self, "Current contents of the scoreboard")

    def set_image(self, image: Image.Image) -> None:
        '''Set the preview image'''
        self._canvas.delete("all")
        scaled = image.resize((self.WIDTH, self.HEIGHT))
        # Note: In order for the image to display on the canvas, we need to
        # keep a reference to it, so it gets assigned to _pimage even though
        # it's not used anywhere else.
        self._pimage = ImageTk.PhotoImage(scaled)
        self._canvas.create_image(0, 0, image=self._pimage, anchor="nw")

class Settings(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Main settings window'''

    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
    def __init__(self, container: tkContainer, csv_cb: CSVGenFn,
                 clear_cb: NoneFn, test_cb: NoneFn, selection_cb: SelectionFn,
                 watchdir_cb: WatchdirFn, manual_btn_cb: NoneFn, config: WahooConfig):
        '''
        Main settings window

        Parameters:
            - container: The tk widget that will hold the settings window
            - csv_cb: Callback function to generate the Dolphin csv
            - clear_cb: Callback function to clear the scoreboard
            - test_cb: Callback function to put test data on the scoreboard
            - selection_cb: Callback function to indicate a change in enabled
              Chromecast devices
            - watchdir_cb: Callback function to indicate the do4 data dir
              has changed.
            - manual_btn_cb: Callback function when load button is pressed.
            - config: WahooConfig configuration object
        '''
        super().__init__(container, padding=5)
        self._config = config
        self._clear_cb = clear_cb
        self._test_cb = test_cb
        self._manual_btn_cb = manual_btn_cb
        self.grid(column=0, row=0, sticky="news")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        lcol = ttk.Frame(self)
        lcol.grid(column=0, row=0, sticky="news")
        lcol.columnconfigure(0, weight=1)
        # row 0: Start list settings
        startlist = _StartList(lcol, csv_cb, self._config)
        startlist.grid(column=0, row=0, sticky="news", padx=3, pady=3)
        # row 1: spacer
        lcol.rowconfigure(1, weight=1)
        # row 2: Dolphin settings
        dolphin = _DolphinSettings(lcol, watchdir_cb, self._config)
        dolphin.grid(column=0, row=2, sticky="news", padx=3, pady=3)

        rcol = ttk.Frame(self)
        rcol.grid(column=1, row=0, sticky="news")
        rcol.columnconfigure(0, weight=1)
        # row 0: General settings
        general = _GeneralSettings(rcol, self._config)
        general.grid(column=0, row=0, sticky="news", padx=3, pady=3)

        # row 1: left side: preview window
        canv = Preview(self)
        canv.grid(column=0, row=1, padx=3, pady=3, sticky="news")
        self._preview = canv

        # row 1: right side: cc chooser
        cc_chooser = _CCChooser(self, selection_cb)
        cc_chooser.grid(column=1, row=1, sticky="news", padx=3, pady=3)
        self._cc_chooser = cc_chooser

        # row 2, left side: run button(s)
        fr6 = ttk.Frame(self)
        fr6.grid(column=0, row=2, sticky="news", padx=3, pady=3)
        fr6.rowconfigure(0, weight=1)
        fr6.columnconfigure(0, weight=0)
        fr6.columnconfigure(1, weight=1)
        test_btn = ttk.Button(fr6, text="Test", command=self._handle_test_btn)
        test_btn.grid(column=0, row=0, sticky="news")
        ToolTip(test_btn, text="Display a mockup to show the current scoreboard style")
        clear_btn = ttk.Button(fr6, text="Clear scoreboard", command=self._handle_clear_btn)
        clear_btn.grid(column=1, row=0, sticky="news")
        ToolTip(clear_btn, text="Clear the scoreboard")
        load_btn = ttk.Button(fr6, text="Load...", command=self._handle_load_btn)
        load_btn.grid(column=2, row=0, sticky="news")
        ToolTip(clear_btn, text="Clear the scoreboard")
        # row 2, right side: doc link and version
        fr8 = ttk.Frame(self)
        fr8.grid(column=1, row=2, sticky="news", padx=3, pady=3)
        fr8.rowconfigure(0, weight=1)
        fr8.columnconfigure(0, weight=1)
        fr8.columnconfigure(1, weight=0)
        query_params = "&".join([
            "utm_source=wahoo_results",
            "utm_medium=config_screen",
            "utm_campaign=docs_link",
            f"ajs_uid={config.get_str('client_id')}",
        ])
        link_label = ttkwidgets.LinkLabel(fr8,
            text="Documentation: https://wahoo-results.readthedocs.io/",
            link="https://wahoo-results.readthedocs.io/?" + query_params,
            relief="sunken",
            padding=[5, 2])
        # interpose event tracking on click of docs link
        def _doc_click_interposer(*args):
            wh_analytics.documentation_link()
            link_label.open_link(args)
        link_label.bind("<Button-1>", _doc_click_interposer)
        link_label.grid(column=0, row=0, sticky="news")
        version_label = ttk.Label(fr8, text=wh_version.git_semver(WAHOO_RESULTS_VERSION),
            justify="right", padding=(5, 2), relief="sunken")
        version_label.grid(column=1, row=0, sticky="nes")
        # row 3: update info
        highest_version = wh_version.latest()
        if (highest_version is not None and
            not wh_version.is_latest_version(highest_version, WAHOO_RESULTS_VERSION)):
            fr10 = ttk.Frame(self)
            fr10.columnconfigure(0, weight=1)
            fr10.grid(column=0, row=3, sticky="news", columnspan=2, padx=3)
            update_text = f"New version available. Click to download: {highest_version.tag}"
            update_label = ttkwidgets.LinkLabel(fr10, text=update_text,
                link=highest_version.url,
                justify="left", padding=[5, 2], relief="sunken")
            update_label.grid(column=0, row=0, sticky="news")
            # interpose event tracking on click of update link
            def _update_click_interposer(*args):
                wh_analytics.update_link()
                update_label.open_link(args)
            update_label.bind("<Button-1>", _update_click_interposer)

    def _handle_clear_btn(self) -> None:
        if self._clear_cb is not None:
            self._clear_cb()

    def _handle_test_btn(self) -> None:
        if self._test_cb is not None:
            self._test_cb()

    def _handle_load_btn(self) -> None:
        if self._manual_btn_cb is not None:
            self._manual_btn_cb()

    def set_items(self, items) -> None:
        '''Set the list of chromecast devices and indicate whether they are enabled'''
        # items is dict[uuid]-> {"name": str, "enabled": bool}
        self._cc_chooser.set_items(items)

    def set_preview(self, image: Image.Image) -> None:
        '''Set the scoreboard preview image'''
        self._preview.set_image(image)




def _main():
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.resizable(False, False)
    options = WahooConfig()

    def sel_cb(items):
        print(items)

    settings = Settings(root, None, None, None, sel_cb, None, None, options)
    settings.grid(column=0, row=0, sticky="news")
    root.update()
    print(f"Root window: {root.winfo_width()}x{root.winfo_height()}")
    items = {}
    items["abc"] = {"name": "cc1", "enabled": True}
    items["def"] = {"name": "cc2", "enabled": False}
    items["ghi"] = {"name": "cc1.5", "enabled": True}
    settings.set_items(items)
    root.update()
    image = Image.open("file.png")
    settings.set_preview(image)
    tk.mainloop()

if __name__ == '__main__':
    _main()
