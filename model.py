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

"""Wahoo! Results data model."""

import logging
import queue
import sys
import tkinter
import uuid
from collections.abc import Callable
from configparser import ConfigParser
from enum import StrEnum, unique
from tkinter import BooleanVar, DoubleVar, IntVar, StringVar, Tk, Toplevel, Variable
from typing import Generic, TypeVar

import PIL.Image as PILImage

from imagecast_types import DeviceStatus
from raceinfo import FullProgram, Heat
from raceinfo.dolphin_do4 import DolphinDo4
from raceinfo.timingsystem import TimingSystem

CallbackFn = Callable[[], None]

_INI_HEADING = "wahoo-results"

_T = TypeVar("_T")

logger = logging.getLogger(__name__)


class GVar(Variable, Generic[_T]):
    """A generic variable in the flavor of StringVar, IntVar, etc."""

    def __init__(self, value: _T, master: "tkinter.Misc | None" = None):
        """
        Create a generic variable in the flavor of StringVar, IntVar, etc.

        :param value: the initial value for the variable
        :param master: the master widget
        """
        super().__init__(master=master, value=0)  # type: ignore
        self._value = value

    def get(self) -> _T:
        """Return the value of the variable."""
        # We call get() to ensure that variable watches get triggered
        _x = super().get()  # type: ignore
        return self._value

    def set(self, value: _T) -> None:
        """Set the variable to a new value."""
        self._value = value
        super().set(super().get() + 1)  # type: ignore


class ChromecastStatusVar(GVar[list[DeviceStatus]]):
    """A list of Chromecast devices and whether they are enabled."""


class ImageVar(GVar[PILImage.Image]):
    """Value holder for PhotoImage variables."""


class CallbackList:
    """A list of callback functions."""

    _callbacks: set[CallbackFn]

    def __init__(self):
        """Initialize a set of callback functions."""
        self._callbacks = set()

    def run(self) -> None:
        """Invoke all registered callback functions."""
        for func in self._callbacks:
            func()

    def add(self, callback: CallbackFn) -> None:
        """Add a callback function to the set.

        :param callback: the function to add
        """
        self._callbacks.add(callback)

    def remove(self, callback: CallbackFn) -> None:
        """Remove a callback function from the set.

        :param callback: the function to remove
        """
        self._callbacks.discard(callback)


class StartListVar(GVar[FullProgram]):
    """An ordered list of start lists."""


class RaceResultListVar(GVar[list[Heat]]):
    """Holds an ordered list of race results."""


class RaceResultVar(GVar[Heat | None]):
    """A race result."""


@unique
class DQMode(StrEnum):
    """DQ mode for the scoreboard."""

    IGNORE = "Ignore"
    """Ignore DQs, treating them as normal results."""
    DQ_TIME = "DQ w/ time"
    """Show DQs, but still show the time."""
    DQ_NOTIME = "DQ hides time"
    """Show DQs, but hide the time."""


class Model:
    """Defines the state variables (model) for the main UI."""

    ## Colors from USA-S visual identity standards
    PANTONE282_DKBLUE = "#041e42"  # Primary
    PANTONE200_RED = "#ba0c2f"  # Primary
    BLACK = "#000000"  # Secondary
    PANTONE428_LTGRAY = "#c1c6c8"  # Secondary
    PANTONE877METALIC_MDGRAY = "#8a8d8f"  # Secondary
    PANTONE281_MDBLUE = "#00205b"  # Tertiary
    PANTONE306_LTBLUE = "#00b3e4"  # Tertiary
    PANTONE871METALICGOLD = "#85754e"  # Tertiary
    PANTONE4505FLATGOLD = "#b1953a"  # Tertiary

    def __init__(self, root: Tk):
        """Initialize the state variables (model) for the main UI.

        :param root: the root Tkinter window
        """
        self.root = root

        # Initialize the event queue and start the dispatch loop
        self._event_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        root.after_idle(self._dispatch_event)

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
        self.show_scoreboard_window = CallbackList()
        self.scoreboard_window: Toplevel | None = None
        self.clear_scoreboard = CallbackList()
        ########################################
        ## Entry fields
        self.font_normal = StringVar(name="font_normal")
        self.font_time = StringVar(name="font_time")
        self.text_spacing = DoubleVar(name="text_spacing")
        self.title = StringVar(name="title")
        # colors
        self.image_bg = StringVar(name="image_bg")
        self.color_title = StringVar(name="color_title")
        self.color_event = StringVar(name="color_event")
        self.color_even = StringVar(name="color_even")
        self.color_odd = StringVar(name="color_odd")
        self.color_first = StringVar(name="color_first")
        self.color_second = StringVar(name="color_second")
        self.color_third = StringVar(name="color_third")
        self.color_bg = StringVar(name="color_bg")
        self.brightness_bg = IntVar(name="brightness_bg")
        # features
        self.num_lanes = IntVar(name="num_lanes")
        self.min_times = IntVar(name="min_times")
        self.time_threshold = DoubleVar(name="time_threshold")
        self.dq_mode = StringVar(name="dq_mode")
        # Preview
        self.appearance_preview = ImageVar(PILImage.Image())
        # Directories
        self.dir_startlist = StringVar(name="dir_startlist")
        self.startlist_contents = StartListVar({})
        self.result_format = StringVar(name="result_format")
        # The timing system will get updated/set properly before use
        self.timing_system: TimingSystem = DolphinDo4()
        self.dir_results = StringVar(name="dir_results")
        self.results_contents = RaceResultListVar([])
        # Run tab
        self.cc_status = ChromecastStatusVar([])
        self.scoreboard = ImageVar(PILImage.Image())
        self.latest_result = RaceResultVar(None)
        # misc
        self.client_id = StringVar(name="client_id")
        self.analytics = BooleanVar(name="analytics")
        self.version = StringVar(name="version")
        self.statustext = StringVar(name="statustext")
        self.statusclick = CallbackList()

    def load(self, filename: str) -> None:
        """Load the user's preferences.

        :param filename: the name of the file to load
        """
        config = ConfigParser(interpolation=None)
        config.read(filename, encoding="utf-8")
        if _INI_HEADING not in config:
            config.add_section(_INI_HEADING)
        data = config[_INI_HEADING]
        # Calibri (sans serif) is standard since Vista
        # It's also part of USA-S visual identity standards
        # https://www.usaswimming.org/docs/default-source/marketingdocuments/usa-swimming-logo-standards-manual.pdf
        # macos doesn't have Calibri installed by default, so we use Helvetica
        default_font_normal = ""
        if sys.platform == "win32":
            default_font_normal = "Calibri"
        elif sys.platform == "darwin":
            default_font_normal = "Helvetica"
        else:
            default_font_normal = "Times"
        self.font_normal.set(data.get("font_normal", default_font_normal))
        # Consolas (monospace) is standard since Vista
        # macos doesn't have Consolas installed by default, so we use Courier
        default_font_time = ""
        if sys.platform == "win32":
            default_font_time = "Consolas"
        elif sys.platform == "darwin":
            default_font_time = "Courier"
        else:
            default_font_time = "Arial"
        self.font_time.set(data.get("font_time", default_font_time))
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
        self.brightness_bg.set(data.getint("brightness_bg", 100))
        self.num_lanes.set(data.getint("num_lanes", 10))
        self.min_times.set(data.getint("min_times", 2))
        self.time_threshold.set(data.getfloat("time_threshold", 0.30))
        self.dq_mode.set(data.get("dq_mode", DQMode.IGNORE))
        self.dir_startlist.set(data.get("dir_startlist", "C:\\swmeets8"))
        self.result_format.set(data.get("result_format", "Dolphin - do4"))
        self.dir_results.set(data.get("dir_results", "C:\\CTSDolphin"))
        client_id = data.get("client_id")
        if client_id is None or len(client_id) == 0:
            client_id = str(uuid.uuid4())
        try:
            uuid.UUID(client_id)
        except ValueError:
            client_id = str(uuid.uuid4())
        self.client_id.set(client_id)
        self.analytics.set(data.getboolean("analytics", True))

    def save(self, filename: str) -> None:
        """Save the user's preferences.

        :param filename: the name of the file to save
        """
        config = ConfigParser(interpolation=None)
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
            "brightness_bg": str(self.brightness_bg.get()),
            "num_lanes": str(self.num_lanes.get()),
            "min_times": str(self.min_times.get()),
            "time_threshold": str(self.time_threshold.get()),
            "dq_mode": self.dq_mode.get(),
            "dir_startlist": self.dir_startlist.get(),
            "result_format": self.result_format.get(),
            "dir_results": self.dir_results.get(),
            "client_id": self.client_id.get(),
            "analytics": str(self.analytics.get()),
        }
        with open(filename, "w", encoding="utf-8") as file:
            config.write(file)

    def enqueue(self, func: Callable[[], None]) -> None:
        """Enqueue a function to be executed by the tkinter main thread.

        :param func: the function to enqueue
        """
        self._event_queue.put(func)

    def _dispatch_event(self) -> None:
        try:
            func = self._event_queue.get_nowait()
            logger.debug("Dispatching function from queue: %s", func.__name__)
            func()
            self._event_queue.task_done()
            # Give tkinter a chance to process events
            self.root.after_idle(self._dispatch_event)
        except queue.Empty:
            # No more events to process, check again later
            self.root.after(10, self._dispatch_event)
