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

'''Main window'''

import os
import sys
from tkinter import FALSE, HORIZONTAL, Menu, StringVar, TclError, Tk, Widget, ttk
import ttkwidgets  #type: ignore
import ttkwidgets.font  #type: ignore
from PIL import ImageTk

from model import Model
import widgets

class View(ttk.Frame):
    '''Main window view definition'''
    def __init__(self, root: Tk, vm: Model):
        super().__init__(root)
        self._root = root
        self._vm = vm
        root.title("Wahoo! Results")
        # Common screen sizes: HD=1366x768 FHD=1920x1080
        # Fix the window to 1/2 the size of the screen so that it's manageable
        root.resizable(False, False)
        root.geometry(f"{1366//2}x{768//2}")
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        icon_file = os.path.abspath(os.path.join(bundle_dir, 'media', 'wr-icon.ico'))
        root.iconphoto(True, ImageTk.PhotoImage(file=icon_file))  # type: ignore
        try:
            root.iconbitmap(icon_file)
        except TclError: # On linux, we can't set a Windows icon file
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
        book.add(_configTab(book, self._vm), text="Configuration", sticky="news")
        book.add(_dirsTab(book, self._vm), text="Directories", sticky="news")
        book.add(_runTab(book, self._vm), text="Run", sticky="news")

        statusbar = ttk.Frame(self)
        statusbar.grid(column=0, row=1, sticky="news")
        statusbar.columnconfigure(0, weight=1)
        ttk.Label(statusbar, textvariable=self._vm.version, justify="right",
        relief="sunken").grid(column=1, row=0, sticky="news")
        statustext = ttk.Label(statusbar, textvariable=self._vm.statustext,
        justify="left", relief="sunken", foreground="blue")
        statustext.grid(column=0, row=0, sticky="news")
        statustext.bind("<Button-1>", lambda *_: self._vm.statusclick.run())

    def _build_menu(self) -> None:
        '''Creates the dropdown menus'''
        self._root.option_add('*tearOff', FALSE) # We don't use tear-off menus
        menubar = Menu(self)
        self._root['menu'] = menubar
        # File menu
        file_menu = Menu(menubar)
        menubar.add_cascade(menu=file_menu, label='File', underline=0)
        file_menu.add_command(label='Exit', underline=1, command=self._vm.menu_exit.run)
        # Help menu
        help_menu = Menu(menubar)
        menubar.add_cascade(menu=help_menu, label='Help', underline=0)
        help_menu.add_command(label='Documentation', underline=0, command=self._vm.menu_docs.run)
        help_menu.add_command(label='About', underline=0, command=self._vm.menu_about.run)


class _configTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, weight=1, uniform="same1")
        self.columnconfigure(1, weight=1, uniform="same1")
        self.rowconfigure(0, weight=1)
        self._appearance(self).grid(column=0, row=0, rowspan=2, sticky="news")
        self._options_frame(self).grid(column=1, row=0, sticky="news")
        self._preview(self).grid(column=1, row=1, sticky="news")

    def _appearance(self, parent: Widget) -> Widget:  # pylint: disable=too-many-statements
        mainframe = ttk.LabelFrame(parent, text="Appearance")

        txt_frame = ttk.Frame(mainframe)
        txt_frame.pack(side="top", fill="x")
        txt_frame.columnconfigure(1, weight=1)  # col 1 gets any extra space

        ttk.Label(txt_frame, text="Main font:", anchor="e").grid(column=0, row=0, sticky="news")
        main_dd = ttkwidgets.font.FontFamilyDropdown(txt_frame, self._vm.font_normal.set)
        main_dd.grid(column=1, row=0, sticky="news")
        # Update dropdown if textvar is changed
        self._vm.font_normal.trace_add("write",
        lambda *_: main_dd.set(self._vm.font_normal.get()))
        # Set initial value
        main_dd.set(self._vm.font_normal.get())

        ttk.Label(txt_frame, text="Time font:", anchor="e").grid(column=0, row=1, sticky="news")
        time_dd = ttkwidgets.font.FontFamilyDropdown(txt_frame,  self._vm.font_time.set)
        time_dd.grid(column=1, row=1, sticky="news")
        # Update dropdown if textvar is changed
        self._vm.font_time.trace_add("write",
        lambda *_: time_dd.set(self._vm.font_time.get()))
        # Set initial value
        time_dd.set(self._vm.font_time.get())

        ttk.Label(txt_frame, text="Heading:", anchor="e").grid(column=0, row=2, sticky="news")
        ttk.Entry(txt_frame, textvariable=self._vm.title).grid(column=1, row=2, sticky="news")

        ttk.Label(txt_frame, text="Text spacing:", anchor="e").grid(column=0, row=3, sticky="news")
        ttk.Spinbox(txt_frame, from_=0.8, to=2.0, increment=0.05, width=4, format="%0.2f",
        textvariable=self._vm.text_spacing).grid(column=1, row=3, sticky="nws")

        ttk.Separator(mainframe, orient=HORIZONTAL).pack(side="top", fill="x", pady=10)

        colorframe = ttk.Frame(mainframe)
        colorframe.pack(side="top", fill="x")
        colorframe.columnconfigure(1, weight=1)
        colorframe.columnconfigure(3, weight=1)
        # 1st col
        ttk.Label(colorframe, text="Heading:", anchor="e").grid(column=0, row=0, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_title).grid(column=1,
        row=0, sticky="nws")
        ttk.Label(colorframe, text="Event:", anchor="e").grid(column=0, row=1, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_event).grid(column=1,
        row=1, sticky="nws")
        ttk.Label(colorframe, text="Odd rows:", anchor="e").grid(column=0, row=2, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_odd).grid(column=1,
        row=2, sticky="nws")
        ttk.Label(colorframe, text="Even rows:", anchor="e").grid(column=0, row=3, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_even).grid(column=1,
        row=3, sticky="nws")
        # 2nd col
        ttk.Label(colorframe, text="1st place:", anchor="e").grid(column=2, row=0, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_first).grid(column=3,
        row=0, sticky="nws")
        ttk.Label(colorframe, text="2nd place:", anchor="e").grid(column=2, row=1, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_second).grid(column=3,
        row=1, sticky="nws")
        ttk.Label(colorframe, text="3rd place:", anchor="e").grid(column=2, row=2, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_third).grid(column=3,
        row=2, sticky="nws")
        ttk.Label(colorframe, text="Background:", anchor="e").grid(column=2, row=3, sticky="news")
        widgets.ColorButton2(colorframe, color_var=self._vm.color_bg).grid(column=3,
        row=3, sticky="nws")

        ttk.Separator(mainframe, orient=HORIZONTAL).pack(side="top", fill="x", pady=10)

        bgframelabels = ttk.Frame(mainframe)
        bgframelabels.pack(side="top", fill="x")
        ttk.Label(bgframelabels, text="Background image:", anchor="e").pack(side="left",
        fill="both")
        self._bg_img_label = StringVar()
        ttk.Label(bgframelabels, textvariable=self._bg_img_label, anchor="w",
        relief="sunken").pack(side="left", fill="both", expand=1)
        self._vm.image_bg.trace_add("write", lambda *_:
            self._bg_img_label.set(os.path.basename(self._vm.image_bg.get())[-20:]))
        self._vm.image_bg.set(self._vm.image_bg.get())

        bgframebtns = ttk.Frame(mainframe)
        bgframebtns.pack(side="top", fill="x")
        ttk.Button(bgframebtns, text="Import...", command=self._vm.bg_import.run).pack(side="left",
        fill="both", expand=1)
        ttk.Button(bgframebtns, text="Clear", command=self._vm.bg_clear.run).pack(side="left",
        fill="both", expand=1)
        return mainframe

    def _options_frame(self, parent: Widget) -> Widget:
        opt_frame = ttk.LabelFrame(parent, text="Options")

        ttk.Label(opt_frame, text="Lanes:", anchor="e").grid(column=0, row=0, sticky="news")
        ttk.Spinbox(opt_frame, from_=6, to=10, increment=1, width=3,
        textvariable=self._vm.num_lanes).grid(column=1, row=0, sticky="news")

        ttk.Label(opt_frame, text="Minimum times:", anchor="e").grid(column=0, row=1, sticky="news")
        ttk.Spinbox(opt_frame, from_=1, to=3, increment=1, width=3,
        textvariable=self._vm.min_times).grid(column=1, row=1, sticky="news")

        ttk.Label(opt_frame, text="Time threshold:", anchor="e").grid(column=0, row=2,
        sticky="news")
        ttk.Spinbox(opt_frame, from_=0.01, to=9.99, increment=0.1, width=4,
        textvariable=self._vm.time_threshold).grid(column=1, row=2, sticky="news")

        return opt_frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        widgets.Preview(frame, self._vm.appearance_preview).grid(column=0, row=0)
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
        frame = ttk.LabelFrame(parent, text='Start lists')
        widgets.DirSelection(frame, self._vm.dir_startlist).grid(column=0, row=0,
        sticky="news", padx=1, pady=1)
        widgets.StartListTreeView(frame, self._vm.startlist_contents).grid(column=0,
        row=1, sticky="news", padx=1, pady=1)
        ttk.Button(frame, padding=(8, 0), text="Export events to Dolphin...",
        command=self._vm.dolphin_export.run).grid(column=0, row=2, padx=1, pady=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        return frame

    def _race_results(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text='Race results')
        widgets.DirSelection(frame, self._vm.dir_results).grid(column=0, row=0,
        sticky="news", padx=1, pady=1)
        widgets.RaceResultTreeView(frame, self._vm.results_contents).grid(column=0,
        row=1, sticky="news", padx=1, pady=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        return frame

class _runTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._cc_selector(self).grid(column=1, row=0, sticky="news")
        self._preview(self).grid(column=1, row=1, sticky="news")

    def _cc_selector(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Available Chromecasts")
        frame.columnconfigure(0, weight=1)
        widgets.ChromcastSelector(frame, self._vm.cc_status).grid(column=0, row=0, sticky="news")
        return frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        widgets.Preview(frame, self._vm.scoreboard).grid(column=0, row=0)
        return frame
