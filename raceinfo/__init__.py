# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2024 - John D. Strunk
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

"""
Package for interfacing with swimming data files.

This package abstracts the details of various swimming-related data file types
into a standard interface.

The primary classes/types are:

- Heat: Encapsulates all information about a single heat of a swim meet. Heat
  objects are used to represent both the start list for a heat as well as the
  results of a heat. The Heat.merge() method can be used to combine the data
  from both sources.
- Lane: Represents a single lane in a heat, containing the swimmer's name, team,
  and times.
- Time: Represents a swim time
- TimeResolver: A function that resolves the times from a Lane, integrating the
  primary and backup times. A TimeResolver is responsible for determining which
  individual times are valid and which time should be used as the official time
  (`Lane.final_time`).

The package also includes a number of modules that provide support for specific
data file types:

- TimingSystem is the base class for all timing system data file types. Current
  implementations include:

  - DolphinDo4: Colorado Dolphin Timing System do4 results files

- MeetProgram is the base class for all meet program data file types. Current
  implementations include:

  - ColoradoSCB: Colorado Time Systems (CTS) start list files (read-only)
  - DolphinCSV: Colorado Dolphin Timing System CSV start list files (write-only)
"""

from .colorado_scb import ColoradoSCB
from .dolphin_csv import DolphinCSV
from .dolphin_do4 import DolphinDo4
from .dolphin_event import DolphinEvent
from .eventprocessor import EventProcessor, FullProgram
from .nameformat import NameMode, format_name
from .time import (
    ZERO_TIME,
    Heat,
    Lane,
    Time,
    TimeResolver,
    format_time,
    parse_time,
    truncate_hundredths,
)
from .timingsystem import TimingSystem

timing_systems: dict[str, type[TimingSystem]] = {
    "Dolphin - do4": DolphinDo4,
    "Dolphin - csv": DolphinCSV,
}
"""A dictionary of timing system classes, keyed by their friendly names."""

__all__ = [
    "ZERO_TIME",
    "ColoradoSCB",
    "DolphinCSV",
    "DolphinDo4",
    "DolphinEvent",
    "EventProcessor",
    "FullProgram",
    "Heat",
    "Lane",
    "NameMode",
    "Time",
    "TimeResolver",
    "TimingSystem",
    "format_name",
    "format_time",
    "parse_time",
    "timing_systems",
    "truncate_hundredths",
]
