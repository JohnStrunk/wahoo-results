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

"""RaceResult class"""

from dataclasses import dataclass, field
from datetime import datetime

from racetime import NumericTime


@dataclass
class RaceResult:
    """
    A RaceResult is the internal representation of the timing results from a
    single race

    Raises: ValueError
    - if the number of lanes is more than 10
    - if the heat number is less than 1
    - if any times any less than zero
    """

    @dataclass
    class Lane:
        """The result for a single lane"""

        times: list[NumericTime] = field(default_factory=list)
        """The raw times for this lane"""

        is_dq: bool = False
        """True if the swimmer was disqualified"""

        is_empty: bool = False
        """True if the lane is marked empty"""

        def __post_init__(self):
            # Mark the lane as empty if there are no times or all times are zero
            if all(time == NumericTime(0) for time in self.times):
                self.is_empty = True
            # Individual times must be greater or equal to zero
            for time in self.times:
                if time < 0:
                    raise ValueError("Time must be greater than or equal to zero")

    event: str
    """
    The event number.

    This is a string to handle events like '1S' or '1Z' in the case of swim-offs
    or initial splits.
    """

    heat: int
    """The heat number"""

    lanes: list[Lane] = field(default_factory=list)
    """The results for each lane"""

    time_recorded: datetime = field(default_factory=datetime.now)

    meet_id: str = ""
    """The meet ID"""

    def __post_init__(self):
        # Ensure that we have 10 lanes
        if len(self.lanes) > 10:
            raise ValueError("The maximum number of lanes is 10")
        while len(self.lanes) < 10:
            self.lanes.append(self.Lane(is_empty=True))
        # Event number should be uppercase
        self.event = self.event.upper()
        # Heat number must be greater than zero
        if self.heat < 1:
            raise ValueError("Heat number must be greater than zero")

    def lane(self, lane_number: int) -> Lane:
        """Retrieve the lane object for a given lane number"""
        if lane_number < 1 or lane_number > 10:
            raise ValueError("Lane number must be between 1 and 10")
        return self.lanes[lane_number - 1]
