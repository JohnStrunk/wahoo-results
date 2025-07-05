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

"""The main window."""

import os
import sys
from tkinter import FALSE, HORIZONTAL, Menu, StringVar, TclError, Tk, Widget, ttk

from PIL import ImageTk

import fonts
import raceinfo
import widgets
from model import DQMode, Model
from tooltip import ToolTip

_PADDING = 2
_TXT_X_PAD = 5
_TXT_Y_PAD = 1
_TXT_PAD = (_TXT_X_PAD, _TXT_Y_PAD)


class View(ttk.Frame):
    """Main window view definition."""

    def __init__(self, root: Tk, vm: Model):
        """Create the main window.

        :param root: The Tk root window
        :param vm: The application model
        """
        super().__init__(root)
        self._root = root
        self._vm = vm
        root.title("Wahoo! Results")
        # Common screen sizes: HD=1366x768 FHD=1920x1080
        # Fix the window to 1/2 the size of the screen so that it's manageable
        root.resizable(False, False)
        root.geometry(f"{int(1366 * 0.5)}x{int(768 * 0.5)}")
        bundle_dir = getattr(
            sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__))
        )
        icon_file = os.path.abspath(os.path.join(bundle_dir, "media", "wr-icon.ico"))
        root.iconphoto(True, ImageTk.PhotoImage(file=icon_file))  # type: ignore
        try:
            root.iconbitmap(icon_file)  # type: ignore
        except TclError:  # On linux, we can't set a Windows icon file
            pass
        # Insert ourselves into the main window
        self.pack(side="top", fill="both", expand=True)
        self._build_menu()
        # App close button is same as Exit menu option
        root.protocol("WM_DELETE_WINDOW", vm.menu_exit.run)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        book = ttk.Notebook(self)
        book.grid(column=0, row=0, sticky="news")
        book.add(
            _configTab(book, self._vm), text="Configuration", underline=0, sticky="news"
        )
        book.add(
            _dirsTab(book, self._vm), text="Directories", underline=0, sticky="news"
        )
        book.add(_runTab(book, self._vm), text="Run", underline=0, sticky="news")
        book.enable_traversal()  # So that Alt-<letter> switches tabs

        statusbar = ttk.Frame(self, padding=_PADDING)
        statusbar.grid(column=0, row=1, sticky="news")
        statusbar.columnconfigure(0, weight=1)
        ttk.Label(
            statusbar, textvariable=self._vm.version, justify="right", relief="sunken"
        ).grid(column=1, row=0, sticky="news")
        statustext = ttk.Label(
            statusbar,
            textvariable=self._vm.statustext,
            justify="left",
            relief="sunken",
            foreground="blue",
        )
        statustext.grid(column=0, row=0, sticky="news")
        statustext.bind("<Button-1>", lambda event: self._vm.statusclick.run())

        style = ttk.Style()
        style.configure("TCombobox", padding=_TXT_PAD)  # type: ignore
        style.configure("TMenuButton", padding=_TXT_PAD)  # type: ignore
        style.configure("TLabel", padding=_TXT_PAD)  # type: ignore
        style.configure("TEntry", padding=_TXT_PAD)  # type: ignore
        style.configure("TSpinbox", padding=_TXT_PAD)  # type: ignore
        style.configure("TButton", padding=_PADDING)  # type: ignore
        style.configure("TLabelframe", padding=_PADDING)  # type: ignore

    def _build_menu(self) -> None:
        """Create the dropdown menus."""
        # We don't use tear-off menus
        self._root.option_add("*tearOff", FALSE)  # type: ignore
        menubar = Menu(self)
        self._root["menu"] = menubar
        # File menu
        file_menu = Menu(menubar)
        menubar.add_cascade(menu=file_menu, label="File", underline=0)
        file_menu.add_command(
            label="Save scoreboard...",
            underline=0,
            command=self._vm.menu_save_scoreboard.run,
        )
        file_menu.add_command(
            label="Export template...",
            underline=0,
            command=self._vm.menu_export_template.run,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", underline=1, command=self._vm.menu_exit.run)
        # Help menu
        help_menu = Menu(menubar, name="help")
        menubar.add_cascade(menu=help_menu, label="Help", underline=0)
        help_menu.add_command(
            label="Documentation", underline=0, command=self._vm.menu_docs.run
        )
        help_menu.add_command(
            label="About", underline=0, command=self._vm.menu_about.run
        )


class _configTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, weight=1, uniform="same1")
        self.columnconfigure(1, weight=1, uniform="same1")
        # self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._appearance(self).grid(column=0, row=0, rowspan=2, sticky="news")
        self._options_frame(self).grid(column=1, row=0, sticky="news")
        self._preview(self).grid(column=1, row=1, sticky="news")

    def _appearance(self, parent: Widget) -> Widget:  # noqa: PLR0915
        mainframe = ttk.LabelFrame(parent, text="Appearance")

        txt_frame = ttk.Frame(mainframe)
        txt_frame.pack(side="top", fill="x")
        txt_frame.columnconfigure(1, weight=1)  # col 1 gets any extra space

        ttk.Label(txt_frame, text="Main font:", anchor="e").grid(
            column=0, row=0, sticky="news"
        )
        main_dd = ttk.Combobox(
            txt_frame,
            textvariable=self._vm.font_normal,
            values=sorted(fonts.font_names()),
        )
        main_dd.grid(column=1, row=0, sticky="news", pady=_PADDING)
        ToolTip(main_dd, "Main font used for scoreboard text")
        # Update dropdown if textvar is changed
        self._vm.font_normal.trace_add(
            "write", lambda var, idx, op: main_dd.set(self._vm.font_normal.get())
        )
        # Set initial value
        main_dd.set(self._vm.font_normal.get())

        ttk.Label(txt_frame, text="Time font:", anchor="e").grid(
            column=0, row=1, sticky="news"
        )
        time_dd = ttk.Combobox(
            txt_frame,
            textvariable=self._vm.font_time,
            values=sorted(fonts.font_names()),
        )
        time_dd.grid(column=1, row=1, sticky="news", pady=_PADDING)
        ToolTip(
            time_dd, "Font for displaying the times - Recommended: fixed-width font"
        )
        # Update dropdown if textvar is changed
        self._vm.font_time.trace_add(
            "write", lambda var, idx, op: time_dd.set(self._vm.font_time.get())
        )
        # Set initial value
        time_dd.set(self._vm.font_time.get())

        ttk.Label(txt_frame, text="Title:", anchor="e").grid(
            column=0, row=2, sticky="news"
        )
        hentry = ttk.Entry(txt_frame, textvariable=self._vm.title)
        hentry.grid(column=1, row=2, sticky="news", pady=_PADDING)
        ToolTip(hentry, "Title text to display")

        ttk.Label(txt_frame, text="Text spacing:", anchor="e").grid(
            column=0, row=3, sticky="news"
        )
        spspin = ttk.Spinbox(
            txt_frame,
            from_=0.8,
            to=2.0,
            increment=0.05,
            width=4,
            format="%0.2f",
            textvariable=self._vm.text_spacing,
        )
        spspin.grid(column=1, row=3, sticky="nws", pady=_PADDING)
        ToolTip(spspin, "Vertical space between text lines")

        ttk.Separator(mainframe, orient=HORIZONTAL).pack(side="top", fill="x", pady=10)

        colorframe = ttk.Frame(mainframe)
        colorframe.pack(side="top", fill="x")
        colorframe.columnconfigure(1, weight=1)
        colorframe.columnconfigure(3, weight=1)
        colorframe.columnconfigure(5, weight=1)
        # 1st col
        ttk.Label(colorframe, text="Heading:", anchor="e").grid(
            column=0, row=0, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_title).grid(
            column=1, row=0, sticky="nws", pady=_PADDING
        )
        ttk.Label(colorframe, text="Event:", anchor="e").grid(
            column=0, row=1, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_event).grid(
            column=1, row=1, sticky="nws", pady=_PADDING
        )
        # 2nd col
        ttk.Label(colorframe, text="1st place:", anchor="e").grid(
            column=2, row=0, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_first).grid(
            column=3, row=0, sticky="nws", pady=_PADDING
        )
        ttk.Label(colorframe, text="2nd place:", anchor="e").grid(
            column=2, row=1, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_second).grid(
            column=3, row=1, sticky="nws", pady=_PADDING
        )
        ttk.Label(colorframe, text="3rd place:", anchor="e").grid(
            column=2, row=2, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_third).grid(
            column=3, row=2, sticky="nws", pady=_PADDING
        )
        # 3rd col
        ttk.Label(colorframe, text="Odd rows:", anchor="e").grid(
            column=4, row=0, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_odd).grid(
            column=5, row=0, sticky="nws", pady=_PADDING
        )
        ttk.Label(colorframe, text="Even rows:", anchor="e").grid(
            column=4, row=1, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_even).grid(
            column=5, row=1, sticky="nws", pady=_PADDING
        )
        ttk.Label(colorframe, text="Background:", anchor="e").grid(
            column=4, row=2, sticky="news"
        )
        widgets.ColorButton2(colorframe, color_var=self._vm.color_bg).grid(
            column=5, row=2, sticky="nws", pady=_PADDING
        )

        ttk.Separator(mainframe, orient=HORIZONTAL).pack(side="top", fill="x", pady=10)

        bgframelabels = ttk.Frame(mainframe)
        bgframelabels.pack(side="top", fill="x")
        bgframelabels.columnconfigure(1, weight=1)
        ttk.Label(bgframelabels, text="Image brightness:", anchor="e").grid(
            column=0, row=0, sticky="news"
        )
        bg_bgight_spin = ttk.Spinbox(
            bgframelabels,
            from_=0,
            to=100,
            increment=5,
            width=4,
            textvariable=self._vm.brightness_bg,
        )
        bg_bgight_spin.grid(column=1, row=0, sticky="nws", pady=_PADDING)
        ToolTip(bg_bgight_spin, "Brightness of the background image (percent: 0-100)")
        ttk.Label(bgframelabels, text="Background image:", anchor="e").grid(
            column=0, row=1, sticky="news"
        )
        self._bg_img_label = StringVar()
        bg_img_label = ttk.Label(
            bgframelabels, textvariable=self._bg_img_label, anchor="w", relief="sunken"
        )
        bg_img_label.grid(column=1, row=1, sticky="news")
        ToolTip(bg_img_label, "Scoreboard background image - Recommended: 1280x720")
        self._vm.image_bg.trace_add(
            "write",
            lambda var, idx, op: self._bg_img_label.set(
                os.path.basename(self._vm.image_bg.get())[-20:]
            ),
        )
        self._vm.image_bg.set(self._vm.image_bg.get())

        bgframebtns = ttk.Frame(mainframe)
        bgframebtns.pack(side="top", fill="x")
        ttk.Button(bgframebtns, text="Import...", command=self._vm.bg_import.run).pack(
            side="left", fill="both", expand=1, padx=_PADDING, pady=_PADDING
        )
        ttk.Button(bgframebtns, text="Clear", command=self._vm.bg_clear.run).pack(
            side="left", fill="both", expand=1, padx=_PADDING, pady=_PADDING
        )
        return mainframe

    def _options_frame(self, parent: Widget) -> Widget:
        opt_frame = ttk.LabelFrame(parent, text="Options")

        ttk.Label(opt_frame, text="Lanes:", anchor="e").grid(
            column=0, row=0, sticky="news"
        )
        lspin = ttk.Spinbox(
            opt_frame,
            from_=6,
            to=10,
            increment=1,
            width=3,
            textvariable=self._vm.num_lanes,
        )
        lspin.grid(column=1, row=0, sticky="news", pady=_PADDING)
        ToolTip(lspin, "Number of lanes to display")

        ttk.Label(opt_frame, text="Minimum times:", anchor="e").grid(
            column=0, row=1, sticky="news"
        )
        tspin = ttk.Spinbox(
            opt_frame,
            from_=1,
            to=3,
            increment=1,
            width=3,
            textvariable=self._vm.min_times,
        )
        tspin.grid(column=1, row=1, sticky="news", pady=_PADDING)
        ToolTip(
            tspin,
            "Lanes with fewer than this number of raw times will"
            + " display dashes instead of a time",
        )

        ttk.Label(opt_frame, text="Time threshold:", anchor="e").grid(
            column=0, row=2, sticky="news"
        )
        thresh = ttk.Spinbox(
            opt_frame,
            from_=0.01,
            to=9.99,
            increment=0.1,
            width=4,
            textvariable=self._vm.time_threshold,
        )
        thresh.grid(column=1, row=2, sticky="news", pady=_PADDING)
        ToolTip(
            thresh,
            "Lanes with any raw times that differ from the final"
            + " time more than this amount will display dashes",
        )

        ttk.Label(opt_frame, text="DQ:", anchor="e").grid(
            column=3, row=0, sticky="news", padx=(15 * _PADDING, 0)
        )
        dq_dd = ttk.OptionMenu(
            opt_frame,
            self._vm.dq_mode,
            self._vm.dq_mode.get(),
            *DQMode.__members__.values(),
        )
        dq_dd.grid(column=4, row=0, sticky="news", pady=_PADDING)
        ToolTip(
            dq_dd,
            "Whether and how to display DQs on scoreboard",
        )

        ttk.Label(opt_frame, text="Autosave scoreboard:", anchor="e").grid(
            column=0, row=3, sticky="news"
        )
        as_cb = ttk.Checkbutton(
            opt_frame,
            variable=self._vm.autosave_scoreboard,
        )
        as_cb.grid(column=1, row=3, sticky="nws", pady=_PADDING)
        ToolTip(
            as_cb,
            "Automatically save the scoreboard image when a new result is processed",
        )

        ttk.Label(opt_frame, text="Autosave directory:", anchor="e").grid(
            column=0, row=4, sticky="news"
        )
        dirsel = widgets.DirSelection(opt_frame, self._vm.dir_autosave)
        dirsel.grid(column=1, row=4, columnspan=4, sticky="news", pady=_PADDING)
        ToolTip(dirsel, "Directory to automatically save scoreboard images to")

        return opt_frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        widgets.ImageView(frame, self._vm.appearance_preview).grid(column=0, row=0)
        ToolTip(frame, "Mockup of how the scoreboard will look")
        return frame


class _dirsTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, weight=1, uniform="same1")
        self.columnconfigure(1, weight=1, uniform="same1")
        self.rowconfigure(0, weight=1)
        self._start_list(self).grid(column=0, row=0, sticky="news", padx=1, pady=1)
        self._race_results(self).grid(column=1, row=0, sticky="news", padx=1, pady=1)

    def _start_list(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Start lists")
        dirsel = widgets.DirSelection(frame, self._vm.dir_startlist)
        dirsel.grid(column=0, row=0, sticky="news", padx=1, pady=1)
        ToolTip(dirsel, "Directory where start list (*.scb) files are located")
        sltv = widgets.StartListTreeView(frame, self._vm.startlist_contents)
        sltv.grid(column=0, row=1, sticky="news", padx=1, pady=1)
        ToolTip(sltv, "List of events found in the start list directory")
        expbtn = ttk.Button(
            frame,
            padding=(8, 0),
            text="Export events to Dolphin...",
            command=self._vm.dolphin_export.run,
        )
        expbtn.grid(column=0, row=2, padx=1, pady=1)
        ToolTip(
            expbtn,
            'Create "dolphin_events.csv" event list for import'
            + " into CTS Dolphin software",
        )
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        return frame

    def _race_results(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Race results")
        res_fmt_frame = ttk.Frame(frame, padding=_PADDING)
        res_fmt_frame.grid(column=0, row=0, sticky="news", padx=1, pady=1)
        res_fmt_label = ttk.Label(res_fmt_frame, text="Data format:", anchor="e")
        res_fmt_label.grid(column=0, row=0, sticky="news", padx=1, pady=1)
        res_fmt = ttk.OptionMenu(
            res_fmt_frame,
            self._vm.result_format,
            self._vm.result_format.get(),
            *sorted(raceinfo.timing_systems.keys()),
        )
        ToolTip(res_fmt, "Select the race result file format")
        res_fmt.grid(column=1, row=0, sticky="news", padx=1, pady=1)
        res_fmt_frame.columnconfigure(1, weight=1)
        widgets.DirSelection(frame, self._vm.dir_results).grid(
            column=0, row=1, sticky="news", padx=1, pady=1
        )
        ToolTip(frame, "Directory where race result files are located")
        widgets.RaceResultTreeView(frame, self._vm.results_contents).grid(
            column=0, row=2, sticky="news", padx=1, pady=1
        )
        ToolTip(frame, "List of completed races found in the results directory")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        return frame


class _runTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, uniform="same1", weight=1)
        self.columnconfigure(1, uniform="same1", weight=1)
        self.rowconfigure(0, weight=1)
        self._lcolumn(self).grid(column=0, row=0, sticky="news")
        self._rcolumn(self).grid(column=1, row=0, sticky="news")

    def _lcolumn(self, parent: Widget) -> Widget:
        frame = ttk.Frame(parent)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.columnconfigure(0, weight=1)
        latestres = widgets.RaceResultView(
            frame, self._vm.latest_result, time_threshold_var=self._vm.time_threshold
        )
        latestres.grid(column=0, row=0, sticky="news")
        ToolTip(latestres, "Raw data from the latest race result")
        self._lcolumn_buttonrow(frame).grid(column=0, row=1, sticky="news")
        return frame

    def _lcolumn_buttonrow(self, parent: Widget) -> Widget:
        frame = ttk.Frame(parent)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        swindow_btn = ttk.Button(
            frame,
            text="Scoreboard window",
            command=self._vm.show_scoreboard_window.run,
        )
        swindow_btn.grid(column=0, row=1, padx=1, pady=1)
        ToolTip(swindow_btn, "Toggle the visibility of the scoreboard window")
        clear_btn = ttk.Button(
            frame,
            text="Clear scoreboard",
            command=self._vm.clear_scoreboard.run,
        )
        clear_btn.grid(column=1, row=1, padx=1, pady=1)
        ToolTip(clear_btn, "Clear the scoreboard")
        return frame

    def _rcolumn(self, parent: Widget) -> Widget:
        frame = ttk.Frame(parent)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        self._cc_selector(frame).grid(column=0, row=0, sticky="news")
        self._preview(frame).grid(column=0, row=1, sticky="news")
        return frame

    def _cc_selector(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Available Chromecasts")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        ccs = widgets.ChromcastSelector(frame, self._vm.cc_status)
        ccs.grid(column=0, row=0, sticky="news")
        ToolTip(ccs, "Chromecasts that have been detected. Click to toggle.")
        return frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        widgets.ImageView(frame, self._vm.scoreboard).grid(column=0, row=0)
        ToolTip(frame, "Current contents of the scoreboard")
        return frame
