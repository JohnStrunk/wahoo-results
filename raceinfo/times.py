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

"""
Primitives for handling times from a race.

The top-level type is `Time`, which is subdivided into:

- `NumericTime`: An actual numeric "time", in seconds (e.g., 28.03).
- `SpecialTime`: These are special values to handle cases such as
  disqualifications, no-shows, etc.
"""

from decimal import ROUND_DOWN, Decimal
from enum import Enum
from typing import Callable, List, Union


class SpecialTime(Enum):
    """Special (non-numeric) values for a time"""

    DQ = "DQ"
    INCONSISTENT = "Inconsistent"
    NO_SHOW = "NoShow"
    NT = "NT"


DQ = SpecialTime.DQ
"""Indicates that a swimmer was disqualified from a race"""

INCONSISTENT = SpecialTime.INCONSISTENT
"""Indicates that a final time could not be automatically resolved"""

NO_SHOW = SpecialTime.NO_SHOW
"""Indicates that a swimmer did not show up for an event"""

NT = SpecialTime.NT
"""Indicates that a swimmer does not have a seed time for an event"""

NumericTime = Decimal
"""NumericTimes are retrieved from a timing system"""

Time = Union[NumericTime, SpecialTime]
"""A Time is either a NumericTime or a special time designator"""

ZERO_TIME = NumericTime("0.00")
"""A time of zero seconds"""


def is_special_time(time: Time) -> bool:
    """Returns True if the time is a special time designator"""
    return isinstance(time, SpecialTime)


def _truncate_hundredths(time: NumericTime) -> NumericTime:
    """
    Truncates a Time to two decimal places.

    >>> _truncate_hundredths(NumericTime("100.00"))
    Decimal('100.00')
    >>> _truncate_hundredths(NumericTime("99.999"))
    Decimal('99.99')
    >>> _truncate_hundredths(NumericTime("10.987"))
    Decimal('10.98')
    >>> _truncate_hundredths(NumericTime("100.123"))
    Decimal('100.12')
    """
    return time.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


TimeResolver = Callable[[List[NumericTime]], Time]
"""
A TimeResolver converts a list of NumericTimes into a final time.

It takes a list of NumericTimes and combines them into a single Time
(NumericTime or SpecialTime) by some resolution method.
"""


def standard_resolver(min_times: int, threshold: NumericTime) -> TimeResolver:
    """
    This returns a TimeResolver that implements the time resolution method used
    by Wahoo Results. It is based on the time resolution rules of USA Swimming
    (see rule 102.23.4).

    The times are resolved based on 2 thresholds:

    - The minimum number of times required
    - The maximum allowable time difference

    Resolution proceeds as follows:

    - If no times are reported, the result is a NO_SHOW
    - If fewer than the minimum number of times are reported, the result is
      INCONSISTENT
    - A candidate final time is calculated:

      - If 3 or more times are reported, the median is used
      - If 2 times are reported, the average is used
      - If 1 time is reported, it is used

    - If any of the RawTimes differ from the candidate final time by more than
      the maximum allowable time difference, the result is INCONSISTENT
    - Otherwise, the candidate final time is returned
    """

    def resolver(times: List[NumericTime]) -> Time:
        # Filter out any times that are less than or equal to zero
        real_times = [time for time in times if time > 0]
        num_times = len(real_times)
        # If no times are reported, the result is a NO_SHOW
        if num_times == 0:
            return NO_SHOW
        # If fewer than the minimum number of times are reported, the result is
        # INCONSISTENT
        if num_times < min_times:
            return INCONSISTENT
        # Calculate the candidate final time
        real_times.sort()
        if num_times >= 3:  # noqa: PLR2004
            if num_times % 2 == 0:
                final = (
                    real_times[num_times // 2 - 1] + real_times[num_times // 2]
                ) / 2
            else:
                final = real_times[num_times // 2]
        elif num_times == 2:  # noqa: PLR2004
            final = (real_times[0] + real_times[1]) / 2
        else:
            final = real_times[0]
        # If any of the RawTimes differ from the candidate final time by more
        # than the maximum allowable time difference, the result is INCONSISTENT
        for time in real_times:
            if abs(time - final) > threshold:
                return INCONSISTENT
        return _truncate_hundredths(final)

    return resolver
