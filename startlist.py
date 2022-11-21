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

import io
import re
from dataclasses import dataclass
from typing import List

@dataclass
class Entry:
    '''Defines an entry in a start list'''
    name: str   # Swimmer's name
    team: str   # Swimmer's team

class StartList:
    '''Represents the start list for an event'''
    _event_name: str
    _event_num: int
    _heats: List[List[Entry]]

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
                heat.append(Entry(
                    name=match.group(1).strip(),
                    team=match.group(2).strip()
                    ))
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

    def entry(self, heat: int, lane: int) -> Entry:
        '''Retrieve the entry information for a heat/lane'''
        if heat > len(self._heats) or heat < 1 or lane > 10 or lane < 1:
            return Entry("", "")
        return self._heats[heat-1][lane-1]

    def is_empty_lane(self, heat: int, lane: int) -> bool:
        '''Returns true if the specified heat/lane has no name or team'''
        return self.entry(heat, lane) == Entry("", "")
