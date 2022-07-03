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

"""
This file defines the result classes.
"""

import decimal
from enum import auto, Enum, unique
import re
from typing import List

Time = decimal.Decimal

class FileParseError(Exception):
    """Execption for when a file cannot be parsed."""
    def __init__(self, filename: str, error: str):
        """Create an exception."""
        self.filename = filename
        self.error = error
        super().__init__(self, filename, error)

def _truncate_hundredths(time: Time) -> Time:
    '''
    Truncates a Time to two decimal places.

    >>> _truncate_hundredths(Time('100.00'))
    Decimal('100.00')
    >>> _truncate_hundredths(Time('99.999'))
    Decimal('99.99')
    >>> _truncate_hundredths(Time('10.987'))
    Decimal('10.98')
    >>> _truncate_hundredths(Time('100.123'))
    Decimal('100.12')
    '''
    return time.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_DOWN)

class Event:
    """
    Event represents a swimming event.
    """
    event_num: str
    event_desc: str
    num_heats: int

    def from_scb(self, filename: str) -> None:
        '''Parse event information from an .scb file'''
        with open(filename, "r", encoding="cp1252") as file:
            lines = file.readlines()
        return self.from_lines(lines)

    def from_lines(self, lines: List[str]) -> None:
        '''Parse event information'''
        match = re.match(r"^#(\w+)\s+(.*)$", lines[0])
        if not match:
            raise FileParseError("", "Unable to parse header")
        self.event_num = match.group(1)
        self.event_desc = match.group(2)
        self.num_heats = (len(lines)-1)//10

    def event_number_portion(self) -> int:
        """Return the leading numeric portion of the event number"""
        match = re.match(r'^(\d+)(\w*)$', self.event_num)
        if not match:
            return 0
        return int(match.group(1))

    def event_letter_portion(self) -> str:
        """Return the trailing alphabetic portion of the event number"""
        match = re.match(r'^(\d+)(\w*)$', self.event_num)
        if not match:
            return ""
        return match.group(2)



class Lane:
    """
    Lane is the result for a single lane of the heat.
    """
    name: str  # Swimmer's name
    team: str  # Swimmer's team
    times: List[Time]  # List of individual measured times
    allow_inconsistent: bool # allow times w/ >0.3s spread

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.team = kwargs.get("team", "")
        self.times = kwargs.get("times", [])
        self.allow_inconsistent = kwargs.get("allow_inconsistent", False)

    def is_empty(self) -> bool:
        """
        Returns True if the lane is believed to be empty.

        >>> Lane(times=[7.34, 7.12, 7.20]).is_empty()
        False
        >>> Lane().is_empty()
        True
        >>> Lane(name="One, Some").is_empty()
        False
        """
        return self.name == "" and len(self.times) == 0

    def times_are_valid(self) -> bool:
        """
        Returns True if all times are within 0.3 seconds.

        >>> Lane(times=[7.34, 7.12, 7.20]).times_are_valid()
        True
        >>> Lane(times=[7.34, 7.02, 7.20]).times_are_valid()
        False
        >>> Lane(times=[7.34, 7.02, 7.20], allow_inconsistent=True).times_are_valid()
        True
        >>> Lane().times_are_valid()
        False
        >>> Lane(allow_inconsistent=True).times_are_valid()
        False
        """
        return len(self.times) > 0 and (
            max(self.times) - min(self.times) <= Time("0.3") or self.allow_inconsistent)

    def final_time(self) -> Time:
        """
        Calculates the final time based on the individual times according to
        USA-S rules.

        >>> Lane(times=[Time("7.0"), Time("4.0"), Time("6.2")]).final_time()
        Decimal('6.20')
        >>> Lane(times=[Time("7.0"), Time("6.2")]).final_time()
        Decimal('6.60')
        >>> Lane(times=[Time("9.1")]).final_time()
        Decimal('9.10')
        >>> Lane(times=[Time("7.13"), Time("6.1")]).final_time()
        Decimal('6.61')
        >>> Lane(times=[Time("139.19"), Time("139.17")]).final_time()
        Decimal('139.18')
        >>> Lane(times=[Time("154.37"), Time("154.29")]).final_time() # showed floating point errors
        Decimal('154.33')
        """
        if len(self.times) == 3:
            self.times.sort()
            return _truncate_hundredths(self.times[1])
        if len(self.times) == 2:
            return _truncate_hundredths((self.times[0] + self.times[1]) / 2)
        if len(self.times) == 1:
            return _truncate_hundredths(self.times[0])
        return _truncate_hundredths(Time("0"))

    def dump(self):
        """
        Dumps the lane data to the screen.
        """
        print(f"Name: {self.name}")
        print(f"Team: {self.team}")
        print(f"Times: {self.times}")
        print(f"Final: {self.final_time()}")
        print(f"Valid: {self.times_are_valid()}")
        print(f"Empty: {self.is_empty()}")

class Heat:
    """
    Heat is the result of a single heat.

    Usage:
        # Create a Result object
        res = Result()
        # Load the CTS Dolphin timing results
        res.load_do4("016-129-004A-0054.do4")
        # Load the scoreboard data
        res.load_scb("E129.scb")
    """
    event_num: str  # Event number
    event_desc: str # Event description
    heat_num: int  # Heat number
    lanes: List[Lane]  # Lane information
    allow_inconsistent: bool  # Permit times w/ >0.3s spread

    def __init__(self, **kwargs):
        self.event_num = kwargs.get("event", "")
        self.event_desc = kwargs.get("event_desc","")
        self.heat_num = kwargs.get("heat", 0)
        self.allow_inconsistent = kwargs.get("allow_inconsistent", False)
        self.lanes = kwargs.get("lanes", [
            Lane(allow_inconsistent=self.allow_inconsistent) for _ in range(0, 10)])

    def load_do4(self, filename: str) -> None:
        """
        Loads event results from a CTS Dolphin *.do4 file.
        """
        with open(filename, "r", encoding="cp1252") as file:
            lines = file.readlines()
        try:
            self._parse_do4(lines)
        except FileParseError as err:
            raise FileParseError(filename, err.error) from err

    def _parse_do4(self, lines) -> None:
        # Ensure the file is the expected number of lines
        if len(lines) != 12:
            raise FileParseError("", "Unexpected number of lines")
        # Ensure the checksum is present
        if not re.match(r'^[0-9A-F]{16}$', lines[-1]):
            raise FileParseError("", "EOF checksum not found")
        # Extract the event & heat from the header
        match = re.match(r'^([^;]*);(\d+);1;.+$', lines[0])
        if not match:
            raise FileParseError("", "Unable to parse header")
        self.event_num = match.group(1)
        self.heat_num = int(match.group(2))
        # Parse the lane results
        for i in range(1, 11):
            fields = lines[i].strip().split(';')
            times = [Time(x) for x in fields[1:] if x not in ('', '0')]
            self.lanes[i-1].times = times

    def load_scb(self, filename: str) -> None:
        """
        Loads event data from a CTS start list *.scb file.
        Note: Heat should be set before calling this method.
        """
        for i in range(0, 10):
            self.lanes[i].name = ""
            self.lanes[i].team = ""
        with open(filename, "r", encoding="cp1252") as file:
            lines = file.readlines()
        try:
            self._parse_scb(lines)
        except FileParseError as err:
            raise FileParseError(filename, err.error) from err

    def _parse_scb(self, lines) -> None:
        # Ensure file has the expected # of lines
        if (len(lines)-1) % 10 or len(lines) <= self.heat_num * 10:
            raise FileParseError("", "Unexpected number of lines in file")
        # Extract event name
        match = re.match(r'^#\w+\s+(.*)$', lines[0])
        if not match:
            raise FileParseError("", "Unable to parse event name")
        self.event_desc = match.group(1)
        # Parse heat names/teams
        heat_start = (self.heat_num - 1) * 10 + 1
        for i in range(0, 10):
            match = re.match(r'^(.*)--(.*)$', lines[heat_start + i])
            if not match:
                raise FileParseError("", "Unable to parse name/team")
            self.lanes[i].name = match.group(1).strip()
            self.lanes[i].team = match.group(2).strip()

    def num_expected_times(self) -> int:
        """
        Return the number of individual times that should be expected.
        """
        # We expect all lanes to have the same number of times, so return the
        # maximum across all lanes.
        return max(len(l.times) for l in self.lanes)

    def place(self, lane: int) -> int:
        """
        Return the place (1-n) for a given lane.
        """
        if not self.lanes[lane].times_are_valid():
            return 0
        time = self.lanes[lane].final_time()
        place = 1
        for i in self.lanes:
            if i.times_are_valid() and i.final_time() < time:
                place += 1
        return place

    def dump(self):
        """Dump the results to the screen."""
        print(f"Event: {self.event_num}")
        print(f"Event desc: {self.event_desc}")
        print(f"Heat: {self.heat_num}")
        for i in self.lanes:
            i.dump()

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
