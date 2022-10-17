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
from typing import Callable, Optional
from tkinter import *
import tkinter.ttk as ttk
import ttkwidgets  #type: ignore
import ttkwidgets.font  #type: ignore

import widgets
import layouts

callback = Optional[Callable[[], None]]

class ViewModel:
    def __init__(self):
        ########################################
        ## Dropdown menu items
        self.on_menu_exit: callback = None
        self.do_menu_exit = lambda: self.on_menu_exit() if self.on_menu_exit is not None else None
        self.on_menu_docs: callback = None
        self.do_menu_docs = lambda: self.on_menu_docs() if self.on_menu_docs is not None else None
        self.on_menu_about: callback = None
        self.do_menu_about = lambda: self.on_menu_about() if self.on_menu_about is not None else None
        ########################################
        ## Buttons
        self.on_bg_import: callback = None
        self.do_bg_import = lambda: self.on_bg_import() if self.on_bg_import is not None else None
        self.on_bg_clear: callback = None
        self.do_bg_clear = lambda: self.on_bg_clear() if self.on_bg_clear is not None else None
        ########################################
        ## Entry fields
        self.main_text = StringVar()
        self.time_text = StringVar()
        self.text_spacing = DoubleVar()
        self.heading1 = StringVar()
        self.heading2 = StringVar()
        # colors
        self.color_heading = StringVar()
        self.color_event = StringVar()
        self.color_even = StringVar()
        self.color_odd = StringVar()
        self.color_first = StringVar()
        self.color_second = StringVar()
        self.color_third = StringVar()
        self.color_bg = StringVar()
        # features
        self.num_lanes = IntVar()
        self.inhibit = BooleanVar()
        # Preview
        self.appearance_preview = widgets.ImageVar()


class View(ttk.Frame):
    def __init__(self, root: Tk, vm: ViewModel):
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
        try:
            root.iconbitmap(icon_file)
        except TclError: # On linux, we can't set a Windows icon file
            pass
        # Insert ourselves into the main window
        self.pack(side="top", fill="both")
        self._build_menu()
        # App close button is same as Exit menu option
        root.protocol("WM_DELETE_WINDOW", vm.do_menu_exit)

        n = ttk.Notebook(self)
        n.pack(side="top", fill="both")
        n.add(_appearanceTab(n, self._vm), text="Appearance")
        n.add(_appearanceTab(n, self._vm), text="Configure")
        n.add(_appearanceTab(n, self._vm), text="Run")

    def _build_menu(self) -> None:
        '''Creates the dropdown menus'''
        self._root.option_add('*tearOff', FALSE) # We don't use tear-off menus
        menubar = Menu(self)
        self._root['menu'] = menubar
        # File menu
        file_menu = Menu(menubar)
        menubar.add_cascade(menu=file_menu, label='File', underline=0)
        file_menu.add_command(label='Exit', underline=1, command=self._vm.do_menu_exit)
        # Help menu
        help_menu = Menu(menubar)
        menubar.add_cascade(menu=help_menu, label='Help', underline=0)
        help_menu.add_command(label='Documentation', underline=0, command=self._vm.do_menu_docs)
        help_menu.add_command(label='About', underline=0, command=self._vm.do_menu_about)


class _appearanceTab(ttk.Frame):
    def __init__(self, parent: Widget, vm: ViewModel) -> None:
        super().__init__(parent)
        # super().__init__(parent, layouts.Orientation.VERTICAL)
        self._vm = vm
        self.columnconfigure(0, weight=1, uniform='appCols')
        self.columnconfigure(1, weight=1, uniform='appCols')
        self.rowconfigure(0, weight=1, uniform='appRows')
        self.rowconfigure(1, weight=1, uniform='appRows')
        self._fonts(self).grid(column=0, row=0, sticky="news")
        self._colors(self).grid(column=0, row=1, sticky="news")
        self._features(self).grid(column=1, row=0, sticky="news")
        self._preview(self).grid(column=1, row=1, sticky="news")
        # self.append(self._fonts(self), sticky="news")
        # self.append(self._colors(self), sticky="news")
        # self.append(self._features(self), sticky="news")
        # self.append(self._preview(self), sticky="news")

    def _fonts(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Fonts")
        frame.columnconfigure(1, weight=1)  # col 1 gets any extra space
        ttk.Label(frame, text="Main font:", anchor="e").grid(column=0, row=0, sticky="news")
        ttkwidgets.font.FontFamilyDropdown(frame, lambda f: self._vm.main_text.set(f)).grid(column=1, row=0, sticky="news")
        ttk.Label(frame, text="Time font:", anchor="e").grid(column=0, row=1, sticky="news")
        ttkwidgets.font.FontFamilyDropdown(frame,  lambda f: self._vm.time_text.set(f)).grid(column=1, row=1, sticky="news")
        ttk.Label(frame, text="Text spacing:", anchor="e").grid(column=0, row=2, sticky="news")
        ttk.Spinbox(frame, from_=0, to=1, increment=0.01, width=4, textvariable=self._vm.text_spacing).grid(column=1, row=2, sticky="nws")
        return frame

    def _colors(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Text colors")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        # 1st col
        ttk.Label(frame, text="Heading:", anchor="e").grid(column=0, row=0, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_heading).grid(column=1, row=0, sticky="nws")
        ttk.Label(frame, text="Event:", anchor="e").grid(column=0, row=1, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_event).grid(column=1, row=1, sticky="nws")
        ttk.Label(frame, text="Odd rows:", anchor="e").grid(column=0, row=2, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_odd).grid(column=1, row=2, sticky="nws")
        ttk.Label(frame, text="Even rows:", anchor="e").grid(column=0, row=3, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_even).grid(column=1, row=3, sticky="nws")
        # 2nd col
        ttk.Label(frame, text="1st place:", anchor="e").grid(column=2, row=0, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_first).grid(column=3, row=0, sticky="nws")
        ttk.Label(frame, text="2nd place:", anchor="e").grid(column=2, row=1, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_second).grid(column=3, row=1, sticky="nws")
        ttk.Label(frame, text="3rd place:", anchor="e").grid(column=2, row=2, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_third).grid(column=3, row=2, sticky="nws")
        ttk.Label(frame, text="Background:", anchor="e").grid(column=2, row=3, sticky="news")
        widgets.ColorButton2(frame, color_var=self._vm.color_bg).grid(column=3, row=3, sticky="nws")
        # Bottom
        bottom = ttk.Frame(frame)
        bottom.grid(column=0, row=4, columnspan=4, sticky="news")
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)
        ttk.Label(bottom, text="Background image:", anchor="e").grid(column=0, row=0, sticky="news")
        ttk.Button(bottom, text="Import...", command=self._vm.do_bg_import).grid(column=1, row=0, sticky="news")
        ttk.Button(bottom, text="Clear", command=self._vm.do_bg_clear).grid(column=2, row=0, sticky="news")
        return frame

    def _features(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard options")

        hc_frame = ttk.Frame(frame)
        hc_frame.pack(side="top", fill="both")
        ttk.Label(hc_frame, text="Heading color:", anchor="e").grid(column=0, row=0, sticky="news")
        widgets.ColorButton2(hc_frame, color_var=self._vm.color_heading).grid(column=1, row=0, sticky="nws")

        txt_frame = ttk.Frame(frame)
        txt_frame.pack(side="top", fill="both")
        txt_frame.columnconfigure(1, weight=1)
        ttk.Label(txt_frame, text="Heading 1:", anchor="e").grid(column=0, row=1, sticky="news")
        ttk.Entry(txt_frame, textvariable=self._vm.heading1).grid(column=1, row=1, sticky="news")
        ttk.Label(txt_frame, text="Heading 2:", anchor="e").grid(column=0, row=2, sticky="news")
        ttk.Entry(txt_frame, textvariable=self._vm.heading2).grid(column=1, row=2, sticky="news")

        opt_frame = ttk.Frame(frame)
        opt_frame.pack(side="top", fill="both")
        opt_frame.columnconfigure(1, weight=1)
        opt_frame.columnconfigure(3, weight=1)
        ttk.Label(opt_frame, text="Lanes:", anchor="e").grid(column=0, row=0, sticky="news")
        ttk.Spinbox(opt_frame, from_=6, to=10, increment=1, width=3, textvariable=self._vm.num_lanes).grid(column=1, row=0, sticky="nws")
        ttk.Label(opt_frame, text="Suppress >0.3s:", anchor="e").grid(column=2, row=0, sticky="news")
        ttk.Checkbutton(opt_frame, variable=self._vm.inhibit).grid(column=3, row=0, sticky="nws")
        return frame

    def _preview(self, parent: Widget) -> Widget:
        frame = ttk.LabelFrame(parent, text="Scoreboard preview")
        frame.columnconfigure(0, weight=1)
        widgets.Preview(frame, self._vm.appearance_preview).grid(column=0, row=0, sticky="news")
        return frame
