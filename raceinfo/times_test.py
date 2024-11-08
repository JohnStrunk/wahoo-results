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

"""Tests for times."""

import pytest

from .times import (
    INCONSISTENT,
    NO_SHOW,
    NumericTime,
    TimeResolver,
    is_special_time,
    standard_resolver,
)


class Test2030Resolver:
    """Tests for the min times 2, threshold 0.30 resolver."""

    @pytest.fixture(scope="class")
    def resolver(self):
        """Return the standard resolver."""
        return standard_resolver(min_times=2, threshold=NumericTime("0.30"))

    def test_no_times_is_no_show(self, resolver: TimeResolver):
        """If there are no times, the result is NO_SHOW."""
        resolved = resolver([])
        assert resolved == NO_SHOW
        assert is_special_time(resolved)

    def test_time_more_than_threshold_from_candidate_is_inconsistent(
        self, resolver: TimeResolver
    ):
        """If a time is more than the threshold away from the candidate final time, the result is INCONSISTENT."""
        assert (
            resolver([NumericTime("60.00"), NumericTime("60.10"), NumericTime("60.50")])
            == INCONSISTENT
        )

    def test_median_with_even_number_is_avg_of_middle(self, resolver: TimeResolver):
        """If there are an even number of times, the median is the average of the two middle times."""
        assert resolver(
            [
                NumericTime("60.09"),
                NumericTime("60.19"),
                NumericTime("60.20"),
                NumericTime("60.30"),
                NumericTime("60.40"),
                NumericTime("60.47"),
            ]
        ) == NumericTime("60.25")

    def test_average_with_quantization(self, resolver: TimeResolver):
        """The average should always be rounded down to the nearest hundredth."""
        assert resolver(
            [
                NumericTime("1.00"),
                NumericTime("1.03"),
            ]
        ) == NumericTime("1.01")

    def test_fewer_than_min_times_is_inconsistent(self, resolver: TimeResolver):
        """If there are fewer than the minimum number of times, the result is INCONSISTENT."""
        resolved = resolver([NumericTime("60.00")])
        assert resolved == INCONSISTENT
        assert is_special_time(resolved)


def test_1030resolver_accepts_single_time() -> None:
    """The 1, 0.30 resolver should accept a single time."""
    resolver1030 = standard_resolver(min_times=1, threshold=NumericTime("0.30"))
    assert resolver1030([NumericTime("65.43")]) == NumericTime("65.43")
