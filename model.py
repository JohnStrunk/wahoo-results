# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2022 - John D. Strunk
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

'''Data model'''

from tkinter import BooleanVar, DoubleVar, IntVar, StringVar
from typing import Callable, Set
import PIL.Image as PILImage

import widgets

CallbackFn = Callable[[], None]

class CallbackList:
    '''A list of callback functions'''
    _callbacks: Set[CallbackFn]
    def __init__(self):
        self._callbacks = set()
    def run(self) -> None:
        '''Invoke all registered callback functions'''
        for func in self._callbacks:
            func()
    def add(self, callback) -> None:
        '''Add a callback function to the set'''
        self._callbacks.add(callback)
    def remove(self, callback) -> None:
        '''Remove a callback function from the set'''
        self._callbacks.discard(callback)

class Model: # pylint: disable=too-many-instance-attributes,too-few-public-methods
    '''Defines the state variables (model) for the main UI'''

    ## Colors from USA-S visual identity standards
    PANTONE282_DKBLUE = "#041e42"         # Primary
    PANTONE200_RED = "#ba0c2f"            # Primary
    BLACK = "#000000"                     # Secondary
    PANTONE428_LTGRAY = "#c1c6c8"         # Secondary
    PANTONE877METALIC_MDGRAY = "#8a8d8f"  # Secondary
    PANTONE281_MDBLUE = "#00205b"
    PANTONE306_LTBLUE = "#00b3e4"
    PANTONE871METALICGOLD = "#85754e"
    PANTONE4505FLATGOLD = "#b1953a"

    def __init__(self):
        ########################################
        ## Dropdown menu items
        self.menu_exit = CallbackList()
        self.menu_docs = CallbackList()
        self.menu_about = CallbackList()
        ########################################
        ## Buttons
        self.bg_import = CallbackList()
        self.bg_clear = CallbackList()
        self.dolphin_export = CallbackList()
        ########################################
        ## Entry fields
        # Calibri (sans serif) is standard since Vista
        # https://learn.microsoft.com/en-us/typography/font-list/calibri
        # Also part of USA-S visual identity standards
        # https://www.usaswimming.org/docs/default-source/marketingdocuments/usa-swimming-logo-standards-manual.pdf
        self.main_text = StringVar(value="Calibri")
        # Consolas (monospace) is standard since Vista
        # https://learn.microsoft.com/en-us/typography/font-list/consolas
        self.time_text = StringVar(value="Consolas")
        self.text_spacing = DoubleVar(value=1.1)
        self.heading = StringVar()
        # colors
        self.bg_image = StringVar()
        self.color_heading = StringVar(value=self.PANTONE200_RED)
        self.color_event = StringVar(value=self.PANTONE4505FLATGOLD)
        self.color_even = StringVar(value=self.PANTONE877METALIC_MDGRAY)
        self.color_odd = StringVar(value=self.PANTONE428_LTGRAY)
        self.color_first = StringVar(value=self.PANTONE306_LTBLUE)
        self.color_second = StringVar(value=self.PANTONE200_RED)
        self.color_third = StringVar(value=self.PANTONE4505FLATGOLD)
        self.color_bg = StringVar(value=self.BLACK)
        # features
        self.num_lanes = IntVar(value=10)
        self.inhibit = BooleanVar(value=True)
        # Preview
        self.appearance_preview = widgets.ImageVar(PILImage.Image())
        # Directories
        self.startlist_dir = StringVar()
        self.startlist_contents = widgets.StartListVar([])
        self.results_dir = StringVar()
        self.results_contents = widgets.RaceResultVar([])
        # Run tab
        self.cc_status = widgets.ChromecastStatusVar([])
        self.scoreboard_preview = widgets.ImageVar(PILImage.Image())

    def load(self, filename: str) -> None:
        '''Load user's preferences'''
        pass

    def save(self, filename: str) -> None:
        '''Save user's preferences'''
        pass
