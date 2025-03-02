# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2025 - John D. Strunk
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

# pyright: strict
"""The data describing a heat."""

import re
from dataclasses import InitVar, dataclass, field
from datetime import datetime

from .lane import Lane
from .resolver import TimeResolver


@dataclass(kw_only=True)
class Heat:
    """
    Information describing a heat.

    Heat can be used for both heat information (e.g. from a start list) and for
    race results (e.g. times from a timing system). Each supported data source
    (start list file or timing system) will store its data in a Heat object. The
    merge() method can be used to combine the data from both sources into a
    single Heat object.

    All fields are optional. If a field is `None`, it is assumed to not be
    supported by the data source that generated this heat data.

    :param event: The event number
    :param heat: The heat number
    :param description: The name of the event
    :param meet_id: The meet ID
    :param race: The race number
    :param time_recorded: The time the results were recorded
    :param time_resolver: The function to resolve times for this heat
    :param lanes: The data for each lane
    :raises: ValueError if any of the parameters are invalid
    """

    # Heat information
    event: str | None = None
    """
    The an alphanumeric event number

    This is a string to handle events like '1S' or '1Z' in the case of swim-offs
    or initial splits.
    """
    heat: int | None = None
    """The heat number"""
    description: str | None = None
    """The name of the event (e.g. 'Girls 100 Freestyle')"""

    # Race data
    meet_id: str | None = None
    """The meet ID"""
    race: int | None = None
    """The race number"""
    time_recorded: datetime | None = None
    """The time the results were recorded"""

    # We hide the actual lane data and provide lane() to access it to avoid
    # confusion over the indexing of the array vs. the actual lane number.
    lanes: InitVar[list[Lane] | None] = field(default=None)
    """The data for each lane"""

    def __post_init__(self, lanes: list[Lane] | None):
        """Validate the heat data."""
        self._lanes = lanes if lanes is not None else []
        # Ensure that we have 10 lanes, even if they are empty
        if len(self._lanes) > 10:  # noqa: PLR2004
            raise ValueError("The maximum number of lanes is 10")
        while len(self._lanes) < 10:  # noqa: PLR2004
            self._lanes.append(Lane())
        if self.event is not None:
            self.event = self.event.upper()
        if self.heat is not None and self.heat < 1:
            raise ValueError("Heat number must be positive")
        if self.race is not None and self.race < 1:
            raise ValueError("The race number must be positive")

    def lane(self, lane_number: int) -> Lane:
        """
        Retrieve the lane object for a given lane number.

        :param lane_number: The lane number (1-10)
        :returns: The lane object
        :raises: ValueError if the lane number is invalid
        """
        if lane_number < 1 or lane_number > 10:  # noqa: PLR2004
            raise ValueError("Lane number must be between 1 and 10")
        return self._lanes[lane_number - 1]

    def place(self, lane_number: int) -> int | None:
        """
        Retrieve the place for a given lane number.

        The place is determined by the resolved time of the lane. If the lane is
        empty, disqualified, or has an indeterminate final time, None is
        returned.

        **Note:** Times must be resolved before calling this method.

        :param lane_number: The lane number (1-10)
        :returns: The place for the lane or None
        :raises: ValueError if the lane number is invalid
        """
        lane = self.lane(lane_number)
        if lane.is_dq or lane.is_empty or lane.final_time is None:
            return None
        place = 1
        for other_lane in self._lanes:
            other_time = other_lane.final_time
            if other_lane.is_empty or other_lane.is_dq or other_time is None:
                continue
            if other_time < lane.final_time:
                place += 1
        return place

    def resolve_times(self, resolver: TimeResolver) -> None:
        """
        Resolve the times for all lanes in this heat.

        :param resolver: The function to resolve times for this heat
        """
        for lane in self._lanes:
            resolver(lane)

    def has_names(self) -> bool:
        """
        Return True if any lane has a name.

        Examples::
        >>> heat = Heat(event="1", heat=1, lanes=[Lane(name="Alice")])
        >>> heat.has_names()
        True
        >>> heat = Heat(event="1", heat=1, lanes=[Lane()])
        >>> heat.has_names()
        False
        """
        return any(lane.name for lane in self._lanes)

    def merge(
        self,
        info_from: "Heat | None" = None,
        results_from: "Heat | None" = None,
    ) -> None:
        """
        Merge another Heat object into this one.

        Merging "info" will overwrite:
        - event, heat, description
        - Lanes: name, team, seed_time, age

        Merging "results" will overwrite:
        - meet_id, race, time_recorded, time_resolver
        - Lanes: times, is_dq, is_empty

        :param info_from: Merge the heat information into this one
        :param results_from: Merge the race results into this one
        """
        if info_from is not None:
            self.event = info_from.event
            self.heat = info_from.heat
            self.description = info_from.description
            for lane_number in range(1, 11):
                dest = self.lane(lane_number)
                dest.merge(info_from=info_from.lane(lane_number))

        if results_from is not None:
            self.meet_id = results_from.meet_id
            self.race = results_from.race
            self.time_recorded = results_from.time_recorded
            for lane_number in range(1, 11):
                dest = self.lane(lane_number)
                dest.merge(results_from=results_from.lane(lane_number))

    def __lt__(self, other: "Heat") -> bool:
        """
        Compare two Heat objects for sorting.

        Comparison is done by event number, then by heat number. For the cases
        where the event is a number followed by an optional string, the number
        is compared first, then the string. For example, '1Z' comes before
        '10S'. For events that don't match this pattern, string comparison is
        used.
        """
        # Treat None as empty/zero for the purposes of sorting.
        self_event = self.event or ""
        self_heat = self.heat or 0
        other_event = other.event or ""
        other_heat = other.heat or 0

        # The event number is a string, composed of a number and an optional
        # letter. Sort by the number first, then by the letter. For example,
        # '1Z' comes before '10S'
        pattern = r"^(\d+)([A-Z]*)$"
        self_match = re.match(pattern, self_event.upper())
        other_match = re.match(pattern, other_event.upper())
        if not self_match or not other_match:
            # Fallback to string comparison
            return self_event.upper() < other_event.upper()

        self_number = int(self_match.group(1))
        other_number = int(other_match.group(1))
        if self_number != other_number:
            return self_number < other_number
        self_letter = self_match.group(2)
        other_letter = other_match.group(2)
        if self_letter != other_letter:
            return self_letter < other_letter
        return self_heat < other_heat
