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

"""Tests for racetime"""

import pytest

from racetime import INCONSISTENT, NO_SHOW, NumericTime, TimeResolver, standard_resolver


class Test2030Resolver:
    @pytest.fixture(scope="class")
    def resolver(self):
        return standard_resolver(min_times=2, threshold=NumericTime("0.30"))

    def test_no_times_is_no_show(self, resolver: TimeResolver):
        assert resolver([]) == NO_SHOW

    def test_time_more_than_threshold_from_candidate_is_inconsistent(
        self, resolver: TimeResolver
    ):
        assert (
            resolver([NumericTime("60.00"), NumericTime("60.10"), NumericTime("60.50")])
            == INCONSISTENT
        )

    def test_median_with_even_number_is_avg_of_middle(self, resolver: TimeResolver):
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


def test_1030resolver_accepts_single_time() -> None:
    resolver1030 = standard_resolver(min_times=1, threshold=NumericTime("0.30"))
    assert resolver1030([NumericTime("65.43")]) == NumericTime("65.43")
