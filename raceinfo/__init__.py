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
- Time: Represents a swim time
- TimeResolver: A function that resolves the times from a Lane, integrating the
  primary and backup times. There is a standard_resolver that can be used for
  most cases to resolve the individual times into a single, final time.

The package also includes a number of modules that provide support for specific
data file types:

- parse_do4_file: Parses a Colorado Dolphin Timing System do4 results file into
  a Heat object containing the times for each lane in the heat.
- parse_scb_file: Parses a Colorado Time Systems (CTS) start list file into a
  list of Heat objects (StartList) containing the names and teams of the
  swimmers in each heat.
"""

from .colorado_scb import load_all_scb, parse_scb, parse_scb_file
from .dolphin_do4 import parse_do4, parse_do4_file
from .heat import Heat
from .lane import Lane
from .nameformat import NameMode, format_name
from .resolver import standard_resolver
from .startlist import StartList, startlists_to_csv
from .time import MIN_VALID_TIME, ZERO_TIME, Time, truncate_hundredths

__all__ = [
    "MIN_VALID_TIME",
    "ZERO_TIME",
    "Heat",
    "Lane",
    "NameMode",
    "StartList",
    "Time",
    "format_name",
    "load_all_scb",
    "parse_do4",
    "parse_do4_file",
    "parse_scb",
    "parse_scb_file",
    "standard_resolver",
    "startlists_to_csv",
    "truncate_hundredths",
]
