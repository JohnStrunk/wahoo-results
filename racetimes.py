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

"""The times (raw and calculated) from a race"""

import copy
import io
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from typing import List, Optional

from startlist import StartList

RawTime = Decimal


@dataclass
class Time:
    """Class to represent a result time."""

    value: RawTime  # The measured (or calculated) time to the hundredths
    is_valid: bool  # True if the time is valid/consistent/within bounds


def _truncate_hundredths(time: RawTime) -> RawTime:
    """
    Truncates a Time to two decimal places.

    >>> _truncate_hundredths(RawTime('100.00'))
    Decimal('100.00')
    >>> _truncate_hundredths(RawTime('99.999'))
    Decimal('99.99')
    >>> _truncate_hundredths(RawTime('10.987'))
    Decimal('10.98')
    >>> _truncate_hundredths(RawTime('100.123'))
    Decimal('100.12')
    """
    return time.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


class RaceTimes(ABC):
    """
    Abstract class representing the times from a race.

    This should be instantiated from a derived class based on a particular
    race result data format (e.g., DO4 for .do4 files). The RaceTimes can then
    be augmented with names, teams, and event description by calling
    set_names() with a StartList. Once the StartList has been added, the
    RaceTimes object should be sufficient to render the scoreboard information
    for the heat.
    """

    def __init__(self, min_times: int, threshold: RawTime):
        """
        Parameters:
        - min_times: The minimum number of times required for the lane time to
          be considered "valid"
        - threshold: The maximum allowable difference between the calculated
          final time and each measured time in order for the final time to be
          considered valid. Any individual times outside teh threshold are
          also marked invalid.
        """
        self.min_times = min_times
        self.threshold = threshold
        self._startlist = StartList()
        self._has_names = False

    def set_names(self, start_list: StartList) -> None:
        """Set the names/teams for the race"""
        self._startlist = copy.deepcopy(start_list)
        self._has_names = True

    def name(self, lane: int) -> str:
        """The Swimmer's name"""
        return self._startlist.name(self.heat, lane)

    def team(self, lane: int) -> str:
        """The Swimmer's team"""
        return self._startlist.team(self.heat, lane)

    @property
    def event_name(self) -> str:
        """The event description"""
        return self._startlist.event_name

    def is_noshow(self, lane: int) -> bool:
        """True if a swimmer should be in the lane, but no time was recorded"""
        return (
            not self._startlist.is_empty_lane(self.heat, lane)
            and self.final_time(lane).value == 0
        )

    @abstractmethod
    def raw_times(self, lane: int) -> List[Optional[RawTime]]:
        """
        Retrieve the measured times from the specified lane.

        The returned List will always be of length 3, but one or more
        elements may be None if no time was reported.
        """
        return [None, None, None]

    def times(self, lane: int) -> List[Optional[Time]]:
        """
        Retrieve the measured times and their validity for the specified lane.

        The returned List will always be of length 3, but one or more
        elements may be None if no time was reported.
        """
        final = self.final_time(lane)
        times: List[Optional[Time]] = []
        for time in self.raw_times(lane):
            if time is None:
                times.append(None)
            else:
                valid = abs(time - final.value) <= self.threshold
                times.append(Time(time, valid))
        return times

    def final_time(self, lane: int) -> Time:
        """Retrieve the calculated final time for a lane"""
        times: List[RawTime] = []
        for time in self.raw_times(lane):
            if time is not None:
                times.append(time)

        if len(times) == 3:  # 3 times -> median
            times.sort()
            final = times[1]
        elif len(times) == 2:  # 2 times -> average
            final = _truncate_hundredths((times[0] + times[1]) / 2)
        elif len(times) == 1:  # 1 time -> use it
            final = times[0]
        else:
            return Time(RawTime(0), False)

        valid = True
        # If we don't have enough times, final is not valid
        if len(times) < self.min_times:
            valid = False
        # If any times are outside threshold, final is not valid
        for time in times:
            if abs(time - final) > self.threshold:
                valid = False
        return Time(final, valid)

    def place(self, lane: int) -> Optional[int]:
        """
        Returns the finishing place within the heat for a given lane.

        - A lane whose time is considered not valid will not be assigned a
          place. These will return "None".
        - Two lanes with identical times will receive the same place, and the
          subsequent place will not be awarded. For example, 2 lanes tie for
          2nd: both will receive a place of "2", and no lanes will receive a
          "3". The next will be awarded "4".
        """
        this_lane = self.final_time(lane)
        if not this_lane.is_valid:
            # Invalid times don't get a place
            return None
        # Place is determined by how many times are strictly faster than ours
        faster = 0
        for index in range(1, 11):
            candidate = self.final_time(index)
            if candidate.is_valid and candidate.value < this_lane.value:
                faster += 1
        return faster + 1

    @property
    def has_names(self) -> bool:
        """Whether this race has name/team information"""
        return self._has_names

    @property
    @abstractmethod
    def event(self) -> int:
        """Event number for this race"""
        return 0

    @property
    @abstractmethod
    def heat(self) -> int:
        """Heat number for this race"""
        return 0

    @property
    @abstractmethod
    def time_recorded(self) -> datetime:
        """The time when this race result was recorded"""
        return datetime.now()

    @property
    @abstractmethod
    def meet_id(self) -> str:
        """Identifier for the meet to which this result belongs"""
        return "0"


class DO4(RaceTimes):
    """
    Implementation of RaceTimes class for CTS Dolphin w/ Splits (.do4 files).
    """

    def __init__(
        self,
        stream: io.TextIOBase,
        min_times: int,
        threshold: RawTime,  # pylint: disable=too-many-arguments
        when: datetime,
        meet_id: str,
    ):
        """
        Parse a text stream in D04 format into a RaceTimes object
        """
        super().__init__(min_times, threshold)
        header = stream.readline()
        match = re.match(r"^(\d+);(\d+);\w+;\w+$", header)
        if not match:
            raise ValueError("Unable to parse header")
        self._event = int(match.group(1))
        self._heat = int(match.group(2))
        self._time_recorded = when
        self._meet_id = meet_id

        lines = stream.readlines()
        if len(lines) != 11:
            raise ValueError("Invalid number of lines in file")
        self._lanes: List[List[Optional[RawTime]]] = []
        for lane in range(10):
            match = re.match(r"^Lane\d+;([\d\.]*);([\d\.]*);([\d\.]*)$", lines[lane])
            if not match:
                raise ValueError("Unable to parse times")
            lane_times: List[Optional[RawTime]] = []
            for index in range(1, 4):
                match_txt = match.group(index)
                time = RawTime(0)
                if match_txt != "":
                    time = RawTime(match_txt)
                if time > 0:
                    lane_times.append(time)
                else:
                    lane_times.append(None)
            self._lanes.append(lane_times)

    def raw_times(self, lane: int) -> List[Optional[RawTime]]:
        return self._lanes[lane - 1]

    @property
    def event(self) -> int:
        return self._event

    @property
    def heat(self) -> int:
        return self._heat

    @property
    def time_recorded(self) -> datetime:
        """The time when this race result was recorded"""
        return self._time_recorded

    @property
    def meet_id(self) -> str:
        return self._meet_id


def from_do4(filename: str, min_times: int, threshold: RawTime) -> RaceTimes:
    """Create a RaceTimes from a D04 race result file"""
    with open(filename, "r", encoding="cp1252") as file:
        meet_id = "???"
        meet_match = re.match(r"^(\d+)-", os.path.basename(filename))
        if meet_match is not None:
            meet_id = meet_match.group(1)
        stinfo = os.stat(filename)
        mtime = datetime.fromtimestamp(stinfo.st_mtime)
        return DO4(file, min_times, threshold, mtime, meet_id)
