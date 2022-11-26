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
from tkinter import FALSE, Menu, TclError, Tk, Widget, ttk
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
        root.title("NEW - Wahoo! Results")
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

        book = ttk.Notebook(self)
        book.pack(side="top", fill="both", expand=True)
        book.add(_appearanceTab(book, self._vm), text="Appearance", sticky="news")
        book.add(_dirsTab(book, self._vm), text="Directories", sticky="news")
        book.add(_runTab(book, self._vm), text="Run", sticky="news")

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


class _appearanceTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        # super().__init__(parent, layouts.Orientation.VERTICAL)
        self._vm = vm
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._fonts(self).grid(column=0, row=0, sticky="news")
        self._colors(self).grid(column=0, row=1, sticky="news")
        self._features(self).grid(column=1, row=0, sticky="news")
        self._preview(self).grid(column=1, row=1, sticky="news")

    def _fonts(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Fonts")
        frame.columnconfigure(1, weight=1)  # col 1 gets any extra space
        ttk.Label(frame, text="Main font:", anchor="e").grid(column=0, row=0, sticky="news")
        main_dd = ttkwidgets.font.FontFamilyDropdown(frame, self._vm.main_text.set)
        main_dd.grid(column=1, row=0, sticky="news")
        # Update dropdown if textvar is changed
        self._vm.main_text.trace_add("write",
        lambda _a, _b, _c: main_dd.set(self._vm.main_text.get()))
        # Set initial value
        main_dd.set(self._vm.main_text.get())
        ttk.Label(frame, text="Time font:", anchor="e").grid(column=0, row=1, sticky="news")
        time_dd = ttkwidgets.font.FontFamilyDropdown(frame,  self._vm.time_text.set)
        time_dd.grid(column=1, row=1, sticky="news")
        # Update dropdown if textvar is changed
        self._vm.time_text.trace_add("write",
        lambda _a, _b, _c: time_dd.set(self._vm.time_text.get()))
        # Set initial value
        time_dd.set(self._vm.time_text.get())
        ttk.Label(frame, text="Text spacing:", anchor="e").grid(column=0, row=2, sticky="news")
        ttk.Spinbox(frame, from_=0.8, to=2.0, increment=0.05, width=4, format="%0.2f",
        textvariable=self._vm.text_spacing).grid(column=1, row=2, sticky="nws")
        return frame

    def _colors(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Text colors")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        # 1st col
        ttk.Label(frame, text="Heading:", anchor="e").grid(column=0, row=0, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_heading).grid(column=1,
        row=0, sticky="nws")
        ttk.Label(frame, text="Event:", anchor="e").grid(column=0, row=1, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_event).grid(column=1,
        row=1, sticky="nws")
        ttk.Label(frame, text="Odd rows:", anchor="e").grid(column=0, row=2, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_odd).grid(column=1,
        row=2, sticky="nws")
        ttk.Label(frame, text="Even rows:", anchor="e").grid(column=0, row=3, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_even).grid(column=1,
        row=3, sticky="nws")
        # 2nd col
        ttk.Label(frame, text="1st place:", anchor="e").grid(column=2, row=0, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_first).grid(column=3,
        row=0, sticky="nws")
        ttk.Label(frame, text="2nd place:", anchor="e").grid(column=2, row=1, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_second).grid(column=3,
        row=1, sticky="nws")
        ttk.Label(frame, text="3rd place:", anchor="e").grid(column=2, row=2, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_third).grid(column=3,
        row=2, sticky="nws")
        ttk.Label(frame, text="Background:", anchor="e").grid(column=2, row=3, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_bg).grid(column=3, row=3, sticky="nws")
        # Bottom
        bottom = ttk.Frame(frame)
        bottom.grid(column=0, row=4, columnspan=4, sticky="news")
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)
        ttk.Label(bottom, text="Background image:", anchor="e").grid(column=0, row=0, sticky="news")
        ttk.Button(bottom, text="Import...", command=self._vm.bg_import.run).grid(column=1,
        row=0, sticky="news")
        ttk.Button(bottom, text="Clear", command=self._vm.bg_clear.run).grid(column=2,
        row=0, sticky="news")
        return frame

    def _features(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard options")

        hc_frame = ttk.Frame(frame)
        hc_frame.pack(side="top", fill="both")
        ttk.Label(hc_frame, text="Heading color:", anchor="e").grid(column=0, row=0, sticky="news")
        widgets.ColorButton2(hc_frame, color_var=self._vm.color_heading).grid(column=1,
        row=0, sticky="nws")

        txt_frame = ttk.Frame(frame)
        txt_frame.pack(side="top", fill="both")
        txt_frame.columnconfigure(1, weight=1)
        ttk.Label(txt_frame, text="Heading 1:", anchor="e").grid(column=0, row=1, sticky="news")
        ttk.Entry(txt_frame, textvariable=self._vm.heading).grid(column=1, row=1, sticky="news")

        opt_frame = ttk.Frame(frame)
        opt_frame.pack(side="top", fill="both")
        opt_frame.columnconfigure(1, weight=1)
        opt_frame.columnconfigure(3, weight=1)
        ttk.Label(opt_frame, text="Lanes:", anchor="e").grid(column=0, row=0, sticky="news")
        ttk.Spinbox(opt_frame, from_=6, to=10, increment=1, width=3,
        textvariable=self._vm.num_lanes).grid(column=1, row=0, sticky="nws")
        ttk.Label(opt_frame, text="Suppress >0.3s:", anchor="e").grid(column=2,
        row=0, sticky="news")
        ttk.Checkbutton(opt_frame, variable=self._vm.inhibit).grid(column=3, row=0, sticky="nws")
        return frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        widgets.Preview(frame, self._vm.appearance_preview).grid(column=0, row=0, sticky="news")
        return frame

class _dirsTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: Model) -> None:
        super().__init__(parent)
        self._vm = vm
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._start_list(self).grid(column=0, row=0, sticky="news", padx=1, pady=1)
        self._race_results(self).grid(column=1, row=0, sticky="news", padx=1, pady=1)

    def _start_list(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text='Start lists')
        widgets.DirSelection(frame, self._vm.startlist_dir).grid(column=0, row=0,
        sticky="news", padx=1, pady=1)
        widgets.StartListTreeView(frame, self._vm.startlist_contents).grid(column=0,
        row=1, sticky="news", padx=1, pady=1)
        ttk.Button(frame, padding=(8, 0), text="Export events to Dolphin...",
        command=self._vm.dolphin_export.run).grid(column=0, row=2, padx=1, pady=1)
        frame.rowconfigure(1, weight=1)
        return frame

    def _race_results(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text='Race results')
        widgets.DirSelection(frame, self._vm.results_dir).grid(column=0, row=0,
        sticky="news", padx=1, pady=1)
        widgets.RaceResultTreeView(frame, self._vm.results_contents).grid(column=0,
        row=1, sticky="news", padx=1, pady=1)
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
        widgets.Preview(frame, self._vm.scoreboard_preview).grid(column=0, row=0, sticky="news")
        return frame
