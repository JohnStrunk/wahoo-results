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

from configparser import ConfigParser
import queue
from tkinter import BooleanVar, DoubleVar, IntVar, StringVar, Tk, Variable
from typing import Callable, Generic, List, Optional, Set, TypeVar
import uuid
import PIL.Image as PILImage
from racetimes import RaceTimes
from startlist import StartList
from imagecast import DeviceStatus

CallbackFn = Callable[[], None]

_INI_HEADING = "wahoo-results"

_T = TypeVar('_T')

class GVar(Variable, Generic[_T]):
    '''
    Create a generic variable in the flavor of StringVar, IntVar, etc.

    - master: the master widget.
    - value: the initial value for the variable
    '''
    def __init__(self, value:_T, master=None):
        super().__init__(master=master, value=0)
        self._value = value

    def get(self) -> _T:
        """Returns the value of the variable."""
        _x = super().get()
        return self._value

    def set(self, value:_T) -> None:
        """Sets the variable to a new value."""
        self._value = value
        super().set(super().get() + 1)

class ChromecastStatusVar(GVar[List[DeviceStatus]]):
    """Holds a list of Chromecast devices and whether they are enabled"""

class ImageVar(GVar[PILImage.Image]):
    """Value holder for PhotoImage variables."""

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

class StartListVar(GVar[List[StartList]]):
    '''An ordered list of start lists'''

class RaceResultListVar(GVar[List[RaceTimes]]):
    """Holds an ordered list of race results."""

class RaceResultVar(GVar[Optional[RaceTimes]]):
    '''A race result'''

class Model: # pylint: disable=too-many-instance-attributes,too-few-public-methods
    '''Defines the state variables (model) for the main UI'''

    ## Colors from USA-S visual identity standards
    PANTONE282_DKBLUE = "#041e42"         # Primary
    PANTONE200_RED = "#ba0c2f"            # Primary
    BLACK = "#000000"                     # Secondary
    PANTONE428_LTGRAY = "#c1c6c8"         # Secondary
    PANTONE877METALIC_MDGRAY = "#8a8d8f"  # Secondary
    PANTONE281_MDBLUE = "#00205b"         # Tertiary
    PANTONE306_LTBLUE = "#00b3e4"         # Tertiary
    PANTONE871METALICGOLD = "#85754e"     # Tertiary
    PANTONE4505FLATGOLD = "#b1953a"       # Tertiary

    _ENQUEUE_EVENT = "<<enqueue_event1>>"

    def __init__(self, root: Tk):
        self.root = root
        self._event_queue: queue.Queue[Callable[[], None]] = queue.Queue(0)
        root.bind(self._ENQUEUE_EVENT, self._dispatch_event)

        ########################################
        ## Dropdown menu items
        self.menu_export_template = CallbackList()
        self.menu_save_scoreboard = CallbackList()
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
        self.font_normal = StringVar()
        self.font_time = StringVar()
        self.text_spacing = DoubleVar()
        self.title = StringVar()
        # colors
        self.image_bg = StringVar()
        self.color_title = StringVar()
        self.color_event = StringVar()
        self.color_even = StringVar()
        self.color_odd = StringVar()
        self.color_first = StringVar()
        self.color_second = StringVar()
        self.color_third = StringVar()
        self.color_bg = StringVar()
        # features
        self.num_lanes = IntVar()
        self.min_times = IntVar()
        self.time_threshold = DoubleVar()
        # Preview
        self.appearance_preview = ImageVar(PILImage.Image())
        # Directories
        self.dir_startlist = StringVar()
        self.startlist_contents = StartListVar([])
        self.dir_results = StringVar()
        self.results_contents = RaceResultListVar([])
        # Run tab
        self.cc_status = ChromecastStatusVar([])
        self.scoreboard = ImageVar(PILImage.Image())
        self.latest_result = RaceResultVar(None)
        # misc
        self.client_id = StringVar()
        self.analytics = BooleanVar()
        self.version = StringVar()
        self.statustext = StringVar()
        self.statusclick = CallbackList()

    def load(self, filename: str) -> None:
        '''Load user's preferences'''
        config = ConfigParser()
        config.read(filename, encoding="utf-8")
        if _INI_HEADING not in config:
            return
        data = config[_INI_HEADING]
        # Calibri (sans serif) is standard since Vista
        # It's also part of USA-S visual identity standards
        # https://www.usaswimming.org/docs/default-source/marketingdocuments/usa-swimming-logo-standards-manual.pdf
        self.font_normal.set(data.get("font_normal", "Calibri"))
        # Consolas (monospace) is standard since Vista
        self.font_time.set(data.get("font_time", "Consolas"))
        self.text_spacing.set(data.getfloat("text_spacing", 1.1))
        self.title.set(data.get("title", "Wahoo! Results"))
        self.image_bg.set(data.get("image_bg", ""))
        self.color_title.set(data.get("color_title", self.PANTONE200_RED))
        self.color_event.set(data.get("color_event", self.PANTONE4505FLATGOLD))
        self.color_even.set(data.get("color_even", self.PANTONE877METALIC_MDGRAY))
        self.color_odd.set(data.get("color_odd", self.PANTONE428_LTGRAY))
        self.color_first.set(data.get("color_first", self.PANTONE306_LTBLUE))
        self.color_second.set(data.get("color_second", self.PANTONE200_RED))
        self.color_third.set(data.get("color_third", self.PANTONE4505FLATGOLD))
        self.color_bg.set(data.get("color_bg", self.BLACK))
        self.num_lanes.set(data.getint("num_lanes", 10))
        self.min_times.set(data.getint("min_times", 2))
        self.time_threshold.set(data.getfloat("time_threshold", 0.30))
        self.dir_startlist.set(data.get("dir_startlist", "C:\\swmeets8"))
        self.dir_results.set(data.get("dir_results", "C:\\CTSDolphin"))
        self.client_id.set(data.get("client_id", str(uuid.uuid4())))
        self.analytics.set(data.getboolean("analytics", True))

    def save(self, filename: str) -> None:
        '''Save user's preferences'''
        config = ConfigParser()
        config[_INI_HEADING] = {
            "font_normal": self.font_normal.get(),
            "font_time": self.font_time.get(),
            "text_spacing": str(self.text_spacing.get()),
            "title": self.title.get(),
            "image_bg": self.image_bg.get(),
            "color_title": self.color_title.get(),
            "color_event": self.color_event.get(),
            "color_even": self.color_even.get(),
            "color_odd": self.color_odd.get(),
            "color_first": self.color_first.get(),
            "color_second": self.color_second.get(),
            "color_third": self.color_third.get(),
            "color_bg": self.color_bg.get(),
            "num_lanes": str(self.num_lanes.get()),
            "min_times": str(self.min_times.get()),
            "time_threshold": str(self.time_threshold.get()),
            "dir_startlist": self.dir_startlist.get(),
            "dir_results": self.dir_results.get(),
            "client_id": self.client_id.get(),
            "analytics": str(self.analytics.get()),
        }
        with open(filename, "w", encoding="utf-8") as file:
            config.write(file)

    def enqueue(self, func: Callable[[], None]) -> None:
        '''Enqueue a function to be executed by the tkinter main thread'''
        self._event_queue.put(func)
        self.root.event_generate(self._ENQUEUE_EVENT, when="tail")

    def _dispatch_event(self, _event) -> None:
        try:
            func = self._event_queue.get_nowait()
            func()
            self._event_queue.task_done()
        except queue.Empty:
            pass
