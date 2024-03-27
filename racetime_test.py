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

from racetime import INCONSISTENT, NO_SHOW, RawTime, StandardResolver


class Test2030Resolver:
    @pytest.fixture(scope="class")
    def resolver(self):
        return StandardResolver(min_times=2, threshold=RawTime("0.30"))

    def test_no_times_is_no_show(self, resolver):
        assert resolver.resolve([]) == NO_SHOW

    def test_fewer_than_2_times_is_inconsistent(self, resolver):
        assert resolver.resolve([RawTime("60.00")]) == INCONSISTENT

    def test_2_times_get_averaged(self, resolver):
        assert resolver.resolve([RawTime("60.00"), RawTime("60.50")]) == RawTime(
            "60.25"
        )

    def test_3_times_takes_the_median(self, resolver):
        assert resolver.resolve(
            [RawTime("60.00"), RawTime("60.10"), RawTime("60.15")]
        ) == RawTime("60.10")

    def test_time_more_than_threshold_from_candidate_is_inconsistent(self, resolver):
        assert (
            resolver.resolve([RawTime("60.00"), RawTime("60.10"), RawTime("60.50")])
            == INCONSISTENT
        )

    def test_median_with_even_number_is_avg_of_middle(self, resolver):
        assert resolver.resolve(
            [
                RawTime("60.09"),
                RawTime("60.19"),
                RawTime("60.20"),
                RawTime("60.30"),
                RawTime("60.40"),
                RawTime("60.47"),
            ]
        ) == RawTime("60.25")


def test_1030resolver_accepts_single_time() -> None:
    resolver1030 = StandardResolver(min_times=1, threshold=RawTime("0.30"))
    assert resolver1030.resolve([RawTime("65.43")]) == RawTime("65.43")
