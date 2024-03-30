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
            # Mark the lane as empty if there are no times
            if not self.times:
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

    description: str
    """Text description of the event such as 'Boys 100 Meter Freestyle'"""

    lanes: list[Lane] = field(default_factory=list)
    """The results for each lane"""

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
