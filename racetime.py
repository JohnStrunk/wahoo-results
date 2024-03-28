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

"""Primitives for handling times from a race"""

from decimal import Decimal
from enum import Enum
from typing import Callable, List, Union


class SpecialTime(Enum):
    """Special (non-numeric) values for a resolved time"""

    NO_SHOW = "NoShow"
    INCONSISTENT = "Inconsistent"


# A special time designator to indicate that a swimmer did not show up for an
# event
NO_SHOW = SpecialTime.NO_SHOW
# A special time designator to indicate that a final time could not be
# automatically resolved from the raw times
INCONSISTENT = SpecialTime.INCONSISTENT

# NumericTimes are retrieved from a timing system
NumericTime = Decimal
# A Time is either a NumericTime or a special time designator
Time = Union[NumericTime, SpecialTime]

# A TimeResolver converts a list of NumericTimes into a final time
TimeResolver = Callable[[List[NumericTime]], Time]


def standard_resolver(min_times: int, threshold: NumericTime) -> TimeResolver:
    """
    This returns a TimeResolver that implements the time resolution method used
    by Wahoo Results. It is based on the time resolution rules of USA Swimming.

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
        num_times = len(times)
        # If no times are reported, the result is a NO_SHOW
        if num_times == 0:
            return NO_SHOW
        # If fewer than the minimum number of times are reported, the result is
        # INCONSISTENT
        if num_times < min_times:
            return INCONSISTENT
        # Calculate the candidate final time
        times.sort()
        if num_times >= 3:
            if num_times % 2 == 0:
                final = (times[num_times // 2 - 1] + times[num_times // 2]) / 2
            else:
                final = times[num_times // 2]
        elif num_times == 2:
            final = (times[0] + times[1]) / 2
        else:
            final = times[0]
        # If any of the RawTimes differ from the candidate final time by more
        # than the maximum allowable time difference, the result is INCONSISTENT
        for time in times:
            if abs(time - final) > threshold:
                return INCONSISTENT
        return final

    return resolver
