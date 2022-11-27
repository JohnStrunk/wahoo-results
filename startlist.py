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

'''Manipulation of CTS Start Lists'''

from abc import ABC
from enum import Enum, auto, unique
import io
import os
import re
from typing import Dict, List

class StartList(ABC):
    '''Represents the start list for an event'''
    @property
    def heats(self) -> int:
        '''The number of heats in the event'''
        return 0

    @property
    def event_name(self) -> str:
        '''Get the event name (description)'''
        return ""

    @property
    def event_num(self) -> int:
        '''Get the event number'''
        return 0

    def name(self, _heat: int, _lane: int) -> str:
        '''Retrieve the Swimmer's name for a heat/lane'''
        return ""

    def team(self, _heat: int, _lane: int) -> str:
        '''Retrieve the Swimmer's team for a heat/lane'''
        return ""

    def is_empty_lane(self, heat: int, lane: int) -> bool:
        '''Returns true if the specified heat/lane has no name or team'''
        return self.name(heat, lane) == "" and self.team(heat, lane) == ""

class CTSStartList(StartList):
    '''Implementation of StartList based on the CTS file format'''
    _event_name: str
    _event_num: int
    _heats: List[List[Dict[str,str]]]

    def __init__(self, stream: io.TextIOBase):
        '''
        Construct a StartList from a text stream (file)

        Example:
            with open(filename, "r", encoding="cp1252") as file:
                try:
                    slist = StartList(file)
                except ValueError as err: # Parse error
                    ...
        '''
        super().__init__()
        # The following assumes event numbers are always numeric. I believe
        # this is ok given that we are parsing SCB format start lists. MM
        # won't export start lists for event numbers containing letters (e.g.,
        # 10X or 10S)
        header = stream.readline()
        match = re.match(r"^#(\d+)\s+(.*)$", header)
        if not match:
            raise ValueError("Unable to parse header")
        self._event_num = int(match.group(1))
        self._event_name = match.group(2)

        # The format always has 10 lines (lanes) per heat
        lines = stream.readlines()
        if len(lines) % 10:
            raise ValueError("Length is not a multiple of 10")
        heats = (len(lines))//10

        # Reverse the lines because we're going to pop() them later and we
        # want to read them in order.
        lines.reverse()
        self._heats = []
        for _h in range(heats):
            heat = []
            for _lane in range(10):
                line = lines.pop()
                # Each entry is fixed length:
                #  - Swimmer name: 20 char
                #  - Literal: "--"
                #  - Swimmer team: 16 char
                # Total line length: 38 char
                # Excess area is space-filled
                match = re.match(r"^(.{20})--(.{16})$", line)
                if not match:
                    raise ValueError(f"Unable to parse line: '{line}'")
                heat.append({
                    "name": match.group(1).strip(),
                    "team": match.group(2).strip(),
                })
            self._heats.append(heat)

    @property
    def heats(self) -> int:
        '''Get the number of heats in the event'''
        return len(self._heats)

    @property
    def event_name(self) -> str:
        '''Get the event name (description)'''
        return self._event_name

    @property
    def event_num(self) -> int:
        '''Get the event number'''
        return self._event_num

    def name(self, heat: int, lane: int) -> str:
        '''Retrieve the Swimmer's name for a heat/lane'''
        if heat > len(self._heats) or heat < 1 or lane > 10 or lane < 1:
            return ""
        return self._heats[heat-1][lane-1]["name"]

    def team(self, heat: int, lane: int) -> str:
        '''Retrieve the Swimmer's team for a heat/lane'''
        if heat > len(self._heats) or heat < 1 or lane > 10 or lane < 1:
            return ""
        return self._heats[heat-1][lane-1]["team"]

@unique
class NameMode(Enum):
    """Formatting options for swimmer names"""
    NONE = auto()
    """Verbatim as in the start list file"""
    FIRST = auto()
    """Format name as: First"""
    FIRST_LAST = auto()
    """Format name as: First Last"""
    FIRST_LASTINITIAL = auto()
    """Format name as: First L"""
    LAST_FIRST = auto()
    """Format name as: Last, First"""
    LAST_FIRSTINITIAL = auto()
    """Format name as: Last, F"""
    LAST = auto()
    """Format name as: Last"""

#pylint: disable=too-many-return-statements
def arrange_name(how: NameMode, name: str) -> str:
    """
    Change the format of a name from a start list.

    >>> arrange_name(NameMode.NONE, "Last, First M       ")
    'Last, First M'
    >>> arrange_name(NameMode.LAST_FIRST, "Last, First M       ")
    'Last, First'
    >>> arrange_name(NameMode.LAST_FIRSTINITIAL, "Last, First M       ")
    'Last, F'
    >>> arrange_name(NameMode.FIRST, "Last, First M       ")
    'First'
    >>> arrange_name(NameMode.FIRST_LAST, "Last, First M       ")
    'First Last'
    >>> arrange_name(NameMode.FIRST_LASTINITIAL, "Last, First M       ")
    'First L'
    >>> arrange_name(NameMode.LAST, "Last, First M       ")
    'Last'
    >>> arrange_name(NameMode.NONE, "Last, First")
    'Last, First'
    >>> arrange_name(NameMode.LAST_FIRST, "Last, First         ")
    'Last, First'
    >>> arrange_name(NameMode.FIRST_LAST, "Last, First         ")
    'First Last'
    >>> arrange_name(NameMode.LAST, "Last, First         ")
    'Last'
    """
    # This regex match is terribly ugly... here's how it works:
    # - Match groups are named via (?P<name>...)
    # - Last name is required to be present. The end of the last name is
    # demarcated by a comma
    # - The separation between Last and First is a comma and 1 or more space
    # characters. The First name portion goes until the next whitespace
    # character, if any.
    # - The middle (initial) is any remaining non-whitespace in the name
    # - The CTS start list names are placed into a 20-character field, so we
    # need to be able to properly parse w/ ws at the end (or not).
    match = re.match(r'^(?P<l>(?P<li>[^,])[^,]*)(,\s+(?P<f>(?P<fi>\w)\w*)(\s+(?P<m>\w+))?)?', name)
    if not match:
        return name.strip()
    if how == NameMode.FIRST:
        return f"{match.group('f')}"
    if how == NameMode.FIRST_LAST:
        return f"{match.group('f')} {match.group('l')}"
    if how == NameMode.FIRST_LASTINITIAL:
        return f"{match.group('f')} {match.group('li')}"
    if how == NameMode.LAST_FIRST:
        return f"{match.group('l')}, {match.group('f')}"
    if how == NameMode.LAST_FIRSTINITIAL:
        return f"{match.group('l')}, {match.group('fi')}"
    if how == NameMode.LAST:
        return f"{match.group('l')}"
    # default is NameMode.NONE
    return name.strip()

def format_name(how: NameMode, name: str) -> List[str]:
    """
    Returns a name formatted according to "how", along w/ shorter variants in
    case the requested format doesn't fit in the alloted space on the
    scoreboard.

    >>> format_name(NameMode.NONE, "Last, First M")
    ['Last, First M', 'Last, First', 'Last, F', 'Last', 'Las', 'La', 'L', '']
    >>> format_name(NameMode.LAST_FIRST, "Last, First M")
    ['Last, First', 'Last, F', 'Last', 'Las', 'La', 'L', '']
    >>> format_name(NameMode.FIRST_LAST, "Last, First M")
    ['First Last', 'First L', 'First', 'Firs', 'Fir', 'Fi', 'F', '']
    """
    variants = []
    if how == NameMode.FIRST_LAST:
        variants = format_name(NameMode.FIRST_LASTINITIAL, name)
    if how == NameMode.FIRST_LASTINITIAL:
        variants = format_name(NameMode.FIRST, name)
    if how == NameMode.FIRST:
        variants = _shorter_strings(arrange_name(how, name))
    if how == NameMode.NONE:
        variants = format_name(NameMode.LAST_FIRST, name)
    if how == NameMode.LAST_FIRST:
        variants = format_name(NameMode.LAST_FIRSTINITIAL, name)
    if how == NameMode.LAST_FIRSTINITIAL:
        variants = format_name(NameMode.LAST, name)
    if how == NameMode.LAST:
        variants = _shorter_strings(arrange_name(how, name))
    return [arrange_name(how, name)] + variants

def _shorter_strings(string: str) -> List[str]:
    """
    >>> _shorter_strings("foobar")
    ['fooba', 'foob', 'foo', 'fo', 'f', '']
    """
    if len(string) > 0:
        shortened = string[:-1]
        return [shortened] + _shorter_strings(shortened)
    return []

def from_scb(filename: str) -> StartList:
    '''Create a StartList from a CTS startlist (.SCB) file'''
    with open(filename, "r", encoding="cp1252") as file:
        return CTSStartList(file)

def events_to_csv(startlists: List[StartList]) -> List[str]:
    '''Convert a list of StartLists to a CSV for the CTS Dolphin'''
    csv = []
    for slist in startlists:
        csv.append(f"{slist.event_num},{slist.event_name},{slist.heats},1,A\n")
    return csv

def load_all_scb(directory: str) -> List[StartList]:
    '''Load all the start list .scb files from a directory'''
    files = os.scandir(directory)
    startlists: List[StartList] = []
    for file in files:
        if file.name.endswith(".scb"):
            try:
                startlist = from_scb(file.path)
                startlists.append(startlist)
            except ValueError:
                pass
    startlists.sort(key=lambda l: l.event_num)
    return startlists
