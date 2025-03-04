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

"""Fundamental timing types."""

import decimal

# https://docs.python.org/3/library/decimal.html#signals
# Raise decimal.FloatOperation when Decimal and float are improperly mixed
decimal.DefaultContext.traps[decimal.FloatOperation] = True

Time = decimal.Decimal
"""A Time in seconds and hundredths of a second"""

ZERO_TIME = Time("0.00")
MIN_VALID_TIME = Time("10.00")
"""The minimum valid race or split time."""


def truncate_hundredths(time: Time) -> Time:
    """
    Truncate a Time to two decimal places.

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
