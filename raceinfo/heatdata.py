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

"""Information describing a heat"""

import re
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from typing import Optional

from .times import NT, ZERO_TIME, NumericTime, Time, TimeResolver, is_special_time


@dataclass(kw_only=True)
class HeatData:
    """
    Information describing a heat

    HeatData can be used for both heat information (e.g. from a start list) and
    for race results (e.g. times from a timing system). Each supported data
    source (start list file or timing system) will store its data in a HeatData
    object. The merge() method can be used to combine the data from both sources
    into a single HeatData object.

    Parameters:
    - event: The event number
    - heat: The heat number
    - description: The name of the event
    - meet_id: The meet ID
    - race: The race number
    - time_recorded: The time the results were recorded
    - time_resolver: The function to resolve times for this heat
    - lanes: The data for each lane

    Raises: ValueError if any of the parameters are invalid
    """

    @dataclass(kw_only=True)
    class Lane:
        """The per-lane information for a heat"""

        # Swimmer information
        name: str = ""
        """The name of the swimmer"""
        team: str = ""
        """The name of the swimmer's team"""
        seed_time: Time = ZERO_TIME
        """The swimmer's seed time (0 if not available)"""
        age: int = 0
        """The swimmer's age (0=unknown)"""

        # Race data
        times: list[NumericTime] = field(default_factory=list)
        """The raw times for this lane"""
        is_dq: bool = False
        """True if the swimmer was disqualified"""
        is_empty: bool = False
        """True if the lane is marked empty"""

        resolver: Optional[TimeResolver] = field(init=False, default=None)

        def __post_init__(self):
            if self.age < 0:
                raise ValueError("Age must be non-negative")
            if (
                not isinstance(self.seed_time, NumericTime)
                and self.seed_time != NT
                or isinstance(self.seed_time, NumericTime)
                and self.seed_time < 0
            ):
                raise ValueError("Seed time must be non-negative or NT")
            # Mark the lane as empty if there are no times or all times are zero
            # and there's no name or team
            if (
                all(time == NumericTime(0) for time in self.times)
                and not self.name
                and not self.team
            ):
                self.is_empty = True
            # Individual times must be greater or equal to zero
            for time in self.times:
                if time < 0:
                    raise ValueError("Times must be greater or equal to zero")

        def time(self) -> Time:
            """Resolve the time for this lane"""
            if not self.resolver:
                raise ValueError("No time resolver set")
            return self.resolver(self.times)

    # Heat information
    event: str = ""
    """
    The event number

    This is a string to handle events like '1S' or '1Z' in the case of swim-offs
    or initial splits.
    """
    heat: int = 1
    """The heat number"""
    description: str = ""
    """The name of the event (e.g. 'Girls 100 Freestyle')"""

    # Race data
    meet_id: str = ""
    """The meet ID"""
    race: int = 1
    """The race number"""
    time_recorded: datetime = field(default_factory=datetime.now)
    """The time the results were recorded"""

    # We hide the actual lane data and provide lane() to access it to avoid
    # confusion over the indexing of the array vs. the actual lane number.
    lanes: InitVar[list[Lane]]
    """The data for each lane"""

    # The time resolver is also hidden behind a getter/setter to ensure that it
    # is passed down to the lane objects
    time_resolver: InitVar[Optional[TimeResolver]] = None
    _resolver: Optional[TimeResolver] = field(init=False, default=None)

    @property
    def resolver(self) -> Optional[TimeResolver]:
        """The time resolver that will be used to resolve times for this heat"""
        return self._resolver

    @resolver.setter
    def resolver(self, value: Optional[TimeResolver]) -> None:
        self._resolver = value
        for lane in self._lanes:
            lane.resolver = value

    def __post_init__(self, lanes: list[Lane], time_resolver: Optional[TimeResolver]):
        self._lanes = lanes
        # Ensure that we have 10 lanes, even if they are empty
        if len(self._lanes) > 10:  # noqa: PLR2004
            raise ValueError("The maximum number of lanes is 10")
        while len(self._lanes) < 10:  # noqa: PLR2004
            self._lanes.append(self.Lane(is_empty=True))
        self.event = self.event.upper()
        if self.heat < 1:
            raise ValueError("Heat number must be positive")
        if self.race < 1:
            raise ValueError("The race number must be positive")
        self.resolver = time_resolver

    def lane(self, lane_number: int) -> Lane:
        """Retrieve the lane object for a given lane number"""
        if lane_number < 1 or lane_number > 10:  # noqa: PLR2004
            raise ValueError("Lane number must be between 1 and 10")
        return self._lanes[lane_number - 1]

    def place(self, lane_number: int) -> Optional[int]:
        """Retrieve the place for a given lane number"""
        if self.resolver is None:
            raise ValueError("No time resolver set")
        lane = self.lane(lane_number)
        time = lane.time()
        if lane.is_empty or lane.is_dq or is_special_time(time):
            return None
        assert isinstance(time, NumericTime)  # checked via is_special_time
        place = 1
        for other_lane in self._lanes:
            other_time = other_lane.time()
            if other_lane.is_empty or other_lane.is_dq or is_special_time(other_time):
                continue
            assert isinstance(other_time, NumericTime)  # checked via is_special_time
            if other_time < time:
                place += 1
        return place

    def has_names(self) -> bool:
        """
        Returns True if any lane has a name.

        Example:
        >>> heat = HeatData(event="1", heat=1, lanes=[HeatData.Lane(name="Alice")])
        >>> heat.has_names()
        True
        >>> heat = HeatData(event="1", heat=1, lanes=[HeatData.Lane()])
        >>> heat.has_names()
        False
        """
        return any(lane.name for lane in self._lanes)

    def merge(
        self,
        info_from: Optional["HeatData"] = None,
        results_from: Optional["HeatData"] = None,
    ) -> None:
        """
        Merge another HeatData object into this one.

        Merging "info" will overwrite:
        - event, heat, description
        - Lanes: name, team, seed_time, age

        Merging "results" will overwrite:
        - meet_id, race, time_recorded, time_resolver
        - Lanes: times, is_dq, is_empty

        Parameters:
        - info_from: Merge the heat information into this one
        - results_from: Merge the race results into this one
        """
        if info_from is not None:
            self.event = info_from.event
            self.heat = info_from.heat
            self.description = info_from.description

        if results_from is not None:
            self.meet_id = results_from.meet_id
            self.race = results_from.race
            self.time_recorded = results_from.time_recorded
            self.resolver = results_from.resolver

        for lane_number in range(1, 11):
            dest = self.lane(lane_number)
            if info_from is not None:
                src = info_from.lane(lane_number)
                dest.name = src.name
                dest.team = src.team
                dest.seed_time = src.seed_time
                dest.age = src.age
            if results_from is not None:
                src = results_from.lane(lane_number)
                dest.times = src.times
                dest.is_dq = src.is_dq
                dest.is_empty = src.is_empty

    def __lt__(self, other: "HeatData") -> bool:
        """
        Compare two HeatData objects for sorting

        >>> e5h1 = HeatData(event="5", heat=1, lanes=[])
        >>> e5h2 = HeatData(event="5", heat=2, lanes=[])
        >>> e5Sh1 = HeatData(event="5S", heat=1, lanes=[])
        >>> e6h1 = HeatData(event="6", heat=1, lanes=[])
        >>> e6h2 = HeatData(event="6", heat=2, lanes=[])
        >>> abcd = HeatData(event="ABCD", heat=1, lanes=[])
        >>> defg = HeatData(event="defg", heat=1, lanes=[])
        >>> sorted([e6h2, e6h1, e5Sh1, e5h1, e5h2]) == [e5h1, e5h2, e5Sh1, e6h1, e6h2]
        True
        >>> sorted([abcd, e5h1, defg]) == [e5h1, abcd, defg]
        True
        """
        # Sort by event then by heat
        # The event number is a string, composed of a number and an optional
        # letter. Sort by the number first, then by the letter. For example,
        # '1Z' comes before '10S'
        pattern = r"^(\d+)([A-Z]*)$"
        self_match = re.match(pattern, self.event.upper())
        other_match = re.match(pattern, other.event.upper())
        if not self_match or not other_match:
            return (
                self.event.upper() < other.event.upper()
            )  # Fallback to string comparison
        self_number = int(self_match.group(1))
        other_number = int(other_match.group(1))
        if self_number != other_number:
            return self_number < other_number
        self_letter = self_match.group(2)
        other_letter = other_match.group(2)
        if self_letter != other_letter:
            return self_letter < other_letter
        return self.heat < other.heat
