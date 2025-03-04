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

"""Test time resolver(s)."""

import pytest

from .lane import Lane
from .resolver import TimeResolver, standard_resolver
from .time import Time


class TestStandardResolver:
    """Tests for the standard resolver."""

    @pytest.fixture(scope="class")
    def resolver_2_030(self):
        """Return the standard resolver."""
        return standard_resolver(min_times=2, threshold=Time("0.30"))

    def test_no_times(self, resolver_2_030: TimeResolver):
        """No times means no final time."""
        lane = Lane()
        resolver_2_030(lane)
        assert lane.final_time is None

    def test_primary_no_backups(self, resolver_2_030: TimeResolver):
        """The primary time can't be supported if there are no backups."""
        lane = Lane(primary=Time("60.00"))
        resolver_2_030(lane)
        assert lane.final_time is None

    def test_supported_primary(self, resolver_2_030: TimeResolver):
        """The primary time is used if it is supported by at least one backup time."""
        lane = Lane(
            primary=Time("60.00"),
            backups=[Time("60.10"), Time("99.99")],
        )
        resolver_2_030(lane)
        assert lane.final_time == Time("60.00")

    def test_backups_are_combined(self, resolver_2_030: TimeResolver):
        """Backup times are combined into a final time."""
        # 2 times get averaged
        lane = Lane(
            primary=None,
            backups=[Time("60.10"), Time("60.20")],
        )
        resolver_2_030(lane)
        assert lane.final_time == Time("60.15")
        # 3 times get median
        lane = Lane(
            primary=None,
            backups=[Time("60.10"), Time("60.20"), Time("60.30")],
        )
        resolver_2_030(lane)
        assert lane.final_time == Time("60.20")
        # 1 time is ignored (less than min_times)
        lane = Lane(
            primary=None,
            backups=[Time("60.10")],
        )
        resolver_2_030(lane)
        assert lane.final_time is None

    def test_backups_are_ignored_if_not_supported(self, resolver_2_030: TimeResolver):
        """Backup times are ignored if they are not supported."""
        lane = Lane(
            primary=None,
            backups=[Time("60.10"), Time("60.00"), Time("99.99")],
        )
        resolver_2_030(lane)
        assert lane.final_time is None

    def test_backups_are_used_if_primary_not_supported(
        self, resolver_2_030: TimeResolver
    ):
        """Backup times are used if the primary time is not supported."""
        lane = Lane(
            primary=Time("60.00"),
            backups=[Time("70.10"), Time("70.00")],
        )
        resolver_2_030(lane)
        assert lane.final_time == Time("70.05")

    def test_times_must_be_more_than_min(self, resolver_2_030: TimeResolver):
        """Times must be more than the min threshold."""
        lane = Lane(
            primary=Time("2.00"),
            backups=[Time("2.10")],
        )
        resolver_2_030(lane)
        assert lane.final_time is None
        lane = Lane(backups=[Time("2.10"), Time("2.20")])
        resolver_2_030(lane)
        assert lane.final_time is None
