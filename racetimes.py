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

'''The times (raw and calculated) from a race'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
import io
import re
from typing import List, Optional, Tuple

@dataclass
class Time:
    '''Class to represent a result time.'''
    value: Decimal  # The measured (or calculated) time to the hundredths
    is_valid: bool  # True if the time is valid/consistent/within bounds

def _truncate_hundredths(time: Decimal) -> Decimal:
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
    return time.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


class RaceTimes(ABC):
    def __init__(self, min_times: int, threshold: Decimal):
        self.min_times = min_times
        self.threshold = threshold

    @abstractmethod
    def raw_times(self, lane: int) -> List[Optional[Decimal]]:
        '''
        Retrieve the measured times from the specified lane.

        The returned List will always be of length 3, but one or more
        elements may be None if no time was reported.
        '''
        return [None, None, None]

    def times(self, lane: int) -> List[Optional[Time]]:
        '''
        Retrieve the measured times and their validity for the specified lane.

        The returned List will always be of length 3, but one or more
        elements may be None if no time was reported.
        '''
        final = self.final_time(lane)
        times: List[Optional[Time]] = []
        for t in self.raw_times(lane):
            if t is None:
                times.append(None)
            else:
                v = abs(t - final.value) <= self.threshold
                times.append(Time(t, v))
        return times

    def final_time(self, lane: int) -> Time:
        '''Retrieve the calculated final time for a lane'''
        times: List[Decimal] = []
        for t in self.raw_times(lane):
            if t is not None:
                times.append(t)

        if len(times) == 3:    # 3 times -> median
            times.sort()
            final = times[1]
        elif len(times) == 2:  # 2 times -> average
            final = _truncate_hundredths((times[0] + times[1]) / 2)
        elif len(times) == 1:  # 1 time -> take it
            final = times[0]
        else:
            return Time(Decimal(0), False)

        valid = True
        # If we don't have enough times, final is not valid
        if len(times) < self.min_times:
            valid = False
        # If any times are outside threshold, final is not valid
        for t in times:
            if abs(t - final) > self.threshold:
                valid = False
        return Time(final, valid)

    @property
    @abstractmethod
    def event(self) -> int:
        return 0

    @property
    @abstractmethod
    def heat(self) -> int:
        return 0

class D04(RaceTimes):
    def __init__(self, stream: io.TextIOBase, min_times: int, threshold: Decimal):
        '''
        Parse a text stream in D04 format into a RaceTimes object
        '''
        super().__init__(min_times, threshold)
        header = stream.readline()
        match = re.match(r"^(\d+);(\d+);\w+;\w+$", header)
        if not match:
            raise ValueError("Unable to parse header")
        self._event = int(match.group(1))
        self._heat = int(match.group(2))

        lines = stream.readlines()
        if len(lines) != 11:
            raise ValueError("Invalid number of lines in file")
        self._lanes: List[List[Optional[Decimal]]] = []
        for l in range(10):
            match = re.match(r"^Lane\d+;([\d\.]*);([\d\.]*);([\d\.]*)$", lines[l])
            if not match:
                raise ValueError("Unable to parse times")
            lane_times: List[Optional[Decimal]] = []
            for t in range(1,4):
                match_txt = match.group(t)
                time = Decimal(0)
                if match_txt != "":
                    time = Decimal(match_txt)
                if time > 0:
                    lane_times.append(time)
                else:
                    lane_times.append(None)
            self._lanes.append(lane_times)

    def raw_times(self, lane: int) -> List[Optional[Decimal]]:
        return self._lanes[lane-1]

    @property
    def event(self) -> int:
        return self._event

    @property
    def heat(self) -> int:
        return self._heat
