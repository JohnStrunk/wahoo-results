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

"""Fundamental timing types.

Times are represented as the `Time` type, which is an alias for `decimal.Decimal`. This allows for precise representation of times, including hundredths of a second. When creating instances of `Time`, you should use strings to avoid floating-point inaccuracies. Use of a float in the constructor will raise a `decimal.FloatOperation` exception.

>>> Time(1)  # int - ok
Decimal('1')
>>> Time("1.0")  # string - ok
Decimal('1.0')
>>> Time(1.0)  # float - raises decimal.FloatOperation
Traceback (most recent call last):
   ...
decimal.FloatOperation: [<class 'decimal.FloatOperation'>]
"""

import copy
import decimal
import re
from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from typing import Literal

# https://docs.python.org/3/library/decimal.html#signals
# Raise decimal.FloatOperation when Decimal and float are improperly mixed
decimal.getcontext().traps[decimal.FloatOperation] = True

Time = decimal.Decimal
"""A Time in seconds and hundredths of a second"""

ZERO_TIME = Time("0.00")


def format_time(time: Time | None) -> str:
    """Return a string representation of the time in mm:ss.hh format.

    Times are formatted as follows:

    - If the time is None, returns an empty string
    - If the time is less than 1 minute, return the time in ss.hh format
    - If the time is greater than or equal to 1 minute, return the time in
      m:ss.hh format
    - If the time is 100 minutes or greater, return '99:59.99'

    :param time: The time to format
    :returns: A string representation of the time in mm:ss.hh format

    Examples:
    >>> format_time(None)
    ''
    >>> format_time(Time("0.0"))
    '00.00'
    >>> format_time(Time("0.01"))
    '00.01'
    >>> format_time(Time("15.2"))
    '15.20'
    >>> format_time(Time("19.87"))
    '19.87'
    >>> format_time(Time("50"))
    '50.00'
    >>> format_time(Time("120.0"))
    '2:00.00'
    >>> format_time(Time("1800"))
    '30:00.00'
    >>> format_time(Time("9000"))
    '99:59.99'
    """
    if time is None:
        return ""
    sixty = Time("60")
    minutes = time // sixty
    seconds = time % sixty
    if minutes >= 100:  # noqa: PLR2004
        return "99:59.99"
    if minutes == 0:
        return f"{seconds:05.2f}"
    return f"{minutes}:{seconds:05.2f}"


def parse_time(time_str: str) -> Time | None:
    """Parse a string representation of a time in mm:ss.hh format.

    :param time_str: A string representation of the time in mm:ss.hh format
    :returns: A Time object representing the time

    Examples:
    >>> parse_time("")
    >>> parse_time("0.0")
    Decimal('0.0')
    >>> parse_time("00.01")
    Decimal('0.01')
    >>> parse_time("15.20")
    Decimal('15.20')
    >>> parse_time("2:00.00")
    Decimal('120.00')
    >>> parse_time("30:00.00")
    Decimal('1800.00')
    >>> parse_time("99:59.99")
    Decimal('5999.99')
    """
    if time_str == "":
        return None
    parts = time_str.split(":")
    if len(parts) == 1:
        # Just seconds (e.g., 1.23)
        return Time(parts[0])
    elif len(parts) == 2:  # noqa: PLR2004
        # Minutes and seconds (e.g., 01:23.45)
        return Time(parts[0]) * 60 + Time(parts[1])
    else:
        raise ValueError("Invalid minsec format")


def truncate_hundredths(time: Time) -> Time:
    """Truncate a Time to two decimal places.

    :param time: The time to truncate
    :returns: The truncated time

    >>> truncate_hundredths(Time("100.00"))
    Decimal('100.00')
    >>> truncate_hundredths(Time("99.999"))
    Decimal('99.99')
    >>> truncate_hundredths(Time("10.987"))
    Decimal('10.98')
    >>> truncate_hundredths(Time("100.123"))
    Decimal('100.12')
    >>> truncate_hundredths(Time("-2.127"))
    Decimal('-2.12')
    """
    return time.quantize(Time("0.01"), rounding=decimal.ROUND_DOWN)


def combine_times(times: list[Time | None]) -> Time | None:
    """Combine a list of times into a single time.

    The times will be combined in the following way:
    - None values are ignored
    - If the list is empty, return None
    - If the list contains only one value, return that value
    - If the list contains two values, return the average of the two
    - If the list contains three or more values, return the median of the values

    :param times: The individual times
    :returns: The combined time or None if no times are present

    Examples::
    >>> combine_times([])
    >>> combine_times([None])
    >>> combine_times([None, Time(100)])
    Decimal('100.00')
    >>> combine_times([Time(100)])
    Decimal('100.00')
    >>> combine_times([Time(100), Time(200)])
    Decimal('150.00')
    >>> combine_times([Time(200), Time(100), Time(300)])
    Decimal('200.00')
    >>> combine_times([Time(300), Time(100), Time(200), Time(400)])
    Decimal('250.00')
    >>> combine_times([Time("10.25"), Time("10.00")])
    Decimal('10.12')
    """
    valid_times = [time for time in times if time is not None]
    num_times = len(valid_times)
    if num_times == 0:
        return None

    sorted_times = sorted(valid_times)
    if num_times % 2 == 0:
        candidate = (
            sorted_times[num_times // 2 - 1] + sorted_times[num_times // 2]
        ) / 2
    else:
        candidate = sorted_times[num_times // 2]

    return truncate_hundredths(candidate)


type TimeResolver = Callable[[Lane], None]
"""
A function that resolves times for a `Lane`.

The resolver should use a combination of the `primary`, `backups`, and `splits`
attributes to determine a final time for the lane. That final time should be set in
the `final_time` attribute of the `Lane`.
"""


@dataclass(kw_only=True)
class Lane:
    """
    The per-lane information for a heat.

    All fields are optional. If a field is not present, it is assumed to not be
    supported by the timing system that generated this lane data. For example,
    an empty ("") `team` name indicates that the system supports team names, but
    the it was not provided for this lane. This is different than a `None`
    value, which indicates that the system does not support team names at all.
    The same logic applies to `backups` and `splits`. An empty `list` is
    different than `None`.

    :param name: The name of the swimmer
    :param team: The name of the swimmer's team
    :param seed_time: The swimmer's seed time
    :param age: The swimmer's age
    :param primary: The primary (pad) time for this lane
    :param backups: The backup times for this lane
    :param splits: The split times for this lane
    :param is_dq: True if the swimmer was disqualified
    :param is_empty: True if the lane is marked empty
    :raises: ValueError if any of the parameters are invalid
    """

    # Swimmer information
    name: str | None = None
    """The name of the swimmer"""
    team: str | None = None
    """The name of the swimmer's team"""
    seed_time: Time | None = None
    """The swimmer's seed time"""
    age: int | None = None
    """The swimmer's age"""

    # Race data
    primary: Time | None = None
    """The primary (pad) time"""
    backups: list[Time | None] | None = None
    """The list of backup times.

    - If backups is None, the timing system does not support backup times.
    - If an entry in the list is None, the timing system did not capture a
      backup time for that particular slot.
    """
    splits: list[list[Time | None]] | None = None
    """The list of cumulative split times.

    - For timing systems that support splits, the final split is the total time
      for the race (i.e., the split from the full race distance).
    - This is a list of lists because some timing systems (e.g., Dolphin)
      generate multiple times for each split distance.
    """
    final_time: Time | None = None
    """The resolved final time for this lane, if available

    This value is not set by the timing system, but is generated by a resolver
    that integrates the primary, backup, and potentially split times.
    """

    # Flags
    is_dq: bool | None = None
    """True if the swimmer was disqualified"""
    is_empty: bool | None = None
    """True if the lane is marked empty"""

    def __post_init__(self):
        """Validate the lane data."""
        if self.age is not None and self.age < 0:
            raise ValueError("Age must be non-negative")
        if self.seed_time is not None and self.seed_time < ZERO_TIME:
            raise ValueError("Seed time must be non-negative")
        if self.primary is not None and self.primary < ZERO_TIME:
            raise ValueError("Primary time must be non-negative")
        if self.final_time is not None and self.final_time < ZERO_TIME:
            raise ValueError("Final time must be non-negative")
        for backup in self.backups or []:
            if backup is not None and backup < ZERO_TIME:
                raise ValueError("Backup times must be non-negative")
        for splitgroup in self.splits or []:
            for split in splitgroup:
                if split is not None and split < ZERO_TIME:
                    raise ValueError("Splits must be non-negative")

    @property
    def is_noshow(self) -> bool:
        """
        Check if the lane is a no-show.

        A lane is considered a no-show if it doesn't have any valid primary,
        backup, or split times.
        """
        if self.primary is not None:
            return False
        if self.backups is not None and any(
            backup is not None for backup in self.backups
        ):
            return False
        if self.splits is not None:
            for splitgroup in self.splits:
                if any(split is not None for split in splitgroup):
                    return False
        return True

    def merge(
        self,
        info_from: "Lane | None" = None,
        results_from: "Lane | None" = None,
    ) -> None:
        """
        Merge another Lane object into this one.

        Merging "info" will overwrite:
        - name, team, seed_time, age

        Merging "results" will overwrite:
        - primary, backups, splits, is_dq, is_empty

        :param info_from: Merge the heat information into this one
        :param results_from: Merge the race data into this one
        """
        if info_from is not None:
            self.name = info_from.name
            self.team = info_from.team
            self.seed_time = info_from.seed_time
            self.age = info_from.age

        if results_from is not None:
            self.primary = results_from.primary
            self.backups = copy.deepcopy(results_from.backups)
            self.splits = copy.deepcopy(results_from.splits)
            self.final_time = results_from.final_time
            self.is_dq = results_from.is_dq
            self.is_empty = results_from.is_empty


@dataclass(kw_only=True)
class Heat:
    """Information describing a heat.

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
    :param lanes: The data for each lane
    :param numbering: The lane numbering scheme (1-10 or 0-9)
    :raises: ValueError if any of the parameters are invalid
    """

    # Heat information
    event: str | None = None
    """The an alphanumeric event number

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
    type Round = Literal["A", "P", "F", "S"]
    round: Round | None = None
    """The round of the event (A=All, P=Prelim, F=Final)"""
    type NumberingMode = Literal["1-10", "0-9"]
    numbering: NumberingMode | None = None

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

    @property
    def event_num(self) -> int | None:
        """Return the numeric part of the event identifier."""
        pattern = r"^(\d+)[A-Z]*$"
        match = re.match(pattern, self.event or "")
        if not match:
            return None
        return int(match.group(1))

    @property
    def event_alpha(self) -> str | None:
        """Return the alpha part of the event identifier.

        This is the part after the numeric part of the event identifier.
        """
        pattern = r"^\d+([A-Z]*)$"
        match = re.match(pattern, self.event or "")
        if not match:
            return None
        return match.group(1)

    def lane(self, lane_number: int) -> Lane:
        """Retrieve the lane object for a given lane number.

        :param lane_number: The lane number (1-10 or 0-9)
        :returns: The lane object
        :raises: ValueError if the lane number is invalid
        """
        if self.numbering is None or self.numbering == "1-10":
            if lane_number < 1 or lane_number > 10:  # noqa: PLR2004
                raise ValueError("Lane number must be between 1 and 10")
            return self._lanes[lane_number - 1]
        if self.numbering == "0-9":
            if lane_number < 0 or lane_number > 9:  # noqa: PLR2004
                raise ValueError("Lane number must be between 0 and 9")
            return self._lanes[lane_number]
        raise ValueError("Invalid lane numbering scheme")

    def place(self, lane_number: int, ignore_dq: bool = False) -> int | None:
        """Retrieve the place for a given lane number.

        The place is determined by the resolved time of the lane. If the lane is
        empty, disqualified, or has an indeterminate final time, None is
        returned.

        **Note:** Times must be resolved before calling this method.

        :param lane_number: The lane number (1-10)
        :param ignore_dq: If True, disqualified lanes are assigned places
        :returns: The place for the lane or None
        :raises: ValueError if the lane number is invalid
        """
        lane = self.lane(lane_number)
        if (lane.is_dq and not ignore_dq) or lane.is_empty or lane.final_time is None:
            return None
        place = 1
        for other_lane in self._lanes:
            other_time = other_lane.final_time
            if (
                other_lane.is_empty
                or (other_lane.is_dq and not ignore_dq)
                or other_time is None
            ):
                continue
            if other_time < lane.final_time:
                place += 1
        return place

    def resolve_times(self, resolver: TimeResolver) -> None:
        """Resolve the times for all lanes in this heat.

        :param resolver: The function to resolve times for this heat
        """
        for lane in self._lanes:
            resolver(lane)

    def has_names(self) -> bool:
        """Return True if any lane has a name.

        Examples::
        >>> heat = Heat(event="1", heat=1, lanes=[Lane(name="Alice")])
        >>> heat.has_names()
        True
        >>> heat = Heat(event="1", heat=1, lanes=[Lane(), Lane(name="Bob")])
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
        """Merge another Heat object into this one.

        Merging "info" will overwrite:
        - event, heat, description
        - Lanes: name, team, seed_time, age

        Merging "results" will overwrite:
        - meet_id, race, time_recorded, round, numbering
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
            self.round = results_from.round
            self.numbering = results_from.numbering
            for lane_number in range(1, 11):
                dest = self.lane(lane_number)
                dest.merge(results_from=results_from.lane(lane_number))

    def to_text(self) -> str:
        """Convert the heat to a text representation.

        :returns: A text representation of the heat
        """
        lines: list[str] = []
        lines.append(f"Event: {self.event or '-None-'}")
        lines.append(f"Description: {self.description or '-None-'}")
        lines.append(f"Heat: {self.heat or '-None-'}")
        lines.append(f"Meet ID: {self.meet_id or '-None-'}")
        lines.append(f"Race #: {self.race or '-None-'}")
        lines.append(f"Time Recorded: {self.time_recorded or '-None-'}")
        lines.append(f"Round: {self.round or '-None-'}")
        lines.append(f"Numbering: {self.numbering}")
        for lane_number in range(1, 11):
            lane = self.lane(lane_number)
            lines.append(f"Lane {lane_number}:")
            lines.append(
                f"  N: {lane.name or '-None-'}  T: {lane.team or '-None-'}  A: {lane.age or '-None-'}  S: {lane.seed_time or '-None-'}"
            )
            lines.append(
                f"  P: {lane.primary or '-None-'}  F: {lane.final_time or '-None-'}  DQ: {lane.is_dq or '-None-'}  E: {lane.is_empty or '-None-'}"
            )
            if lane.backups is not None:
                lines.append(f"  Backups: {', '.join(str(b) for b in lane.backups)}")
            if lane.splits is not None:
                lines.append(
                    f"  Splits: {'; '.join(', '.join(str(s) for s in split) for split in lane.splits)}"
                )
        return "\n".join(lines)

    def __lt__(self, other: "Heat") -> bool:
        """Compare two Heat objects for sorting.

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

        if self_event != other_event:
            return self._event_lt(self_event, other_event)
        return self_heat < other_heat

    @classmethod
    def _event_lt(cls, event1: str | None, event2: str | None) -> bool:
        """Compare two event numbers for sorting.

        Comparison is done by event number. For the cases where the event is a
        number followed by an optional string, the number is compared first,
        then the string. For example, '1Z' comes before '10S'. For events that
        don't match this pattern, string comparison is used.

        :param event1: The first event number
        :param event2: The second event number
        :returns: True if event1 is less than event2

        Examples:
        >>> Heat._event_lt("1", "2")
        True
        >>> Heat._event_lt("2", "1")
        False
        >>> Heat._event_lt("1Z", "1S")
        False
        >>> Heat._event_lt("1S", "1Z")
        True
        >>> Heat._event_lt("1Z", "2S")
        True
        >>> Heat._event_lt("1Z", "10")
        True
        >>> Heat._event_lt("abc", "bbb")
        True
        >>> Heat._event_lt("bbb", "abc")
        False
        """
        # Treat None as empty/zero for the purposes of sorting.
        event1 = event1 or ""
        event2 = event2 or ""

        # The event number is a string, composed of a number and an optional
        # letter. Sort by the number first, then by the letter. For example,
        # '1Z' comes before '10S'
        pattern = r"^(\d+)([A-Z]*)$"
        match1 = re.match(pattern, event1.upper())
        match2 = re.match(pattern, event2.upper())
        if not match1 or not match2:
            # Fallback to string comparison
            return event1.upper() < event2.upper()

        number1 = int(match1.group(1))
        number2 = int(match2.group(1))
        if number1 != number2:
            return number1 < number2
        letter1 = match1.group(2)
        letter2 = match2.group(2)
        if letter1 != letter2:
            return letter1 < letter2
        return event1.upper() < event2.upper()
