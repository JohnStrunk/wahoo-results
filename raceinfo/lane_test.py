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

# pyright: strict
"""Tests for Lane."""

import pytest

from .lane import Lane
from .time import Time


class TestLaneValidation:
    """Tests for Lane validation."""

    def test_invalid_seed_time(self):
        """Invalid seed time raises ValueError."""
        with pytest.raises(ValueError):
            Lane(seed_time=Time(-1.0))

    def test_invalid_age(self):
        """Invalid age raises ValueError."""
        with pytest.raises(ValueError):
            Lane(age=-1)

    def test_invalid_primary(self):
        """Invalid primary time raises ValueError."""
        with pytest.raises(ValueError):
            Lane(primary=Time(-1.0))

    def test_invalid_final_time(self):
        """Invalid final time raises ValueError."""
        with pytest.raises(ValueError):
            Lane(primary=Time(1.0), final_time=Time(-1.0))

    def test_invalid_backups(self):
        """Invalid backups raise ValueError."""
        with pytest.raises(ValueError):
            Lane(backups=[[Time(-1.0)]])

    def test_invalid_splits(self):
        """Invalid splits raise ValueError."""
        with pytest.raises(ValueError):
            Lane(splits=[Time(-1.0)])


class TestLaneMerge:
    """Tests for Lane merging."""

    @pytest.fixture()
    def lane1(self):
        """Fixture for lane1."""
        return Lane(
            name="Alice",
            team="Apples",
            seed_time=Time(1.0),
            age=7,
            primary=Time(54.32),
            final_time=Time(54.54),
            backups=[[Time(1.0), Time(2.0), Time(3.0)], [Time(4.0)]],
            splits=[Time(14.0), Time(15.0), Time(16.0)],
            is_dq=True,
            is_empty=False,
        )

    @pytest.fixture()
    def lane2(self):
        """Fixture for lane2."""
        return Lane(
            name="Bob",
            team="Bananas",
            seed_time=Time(2.0),
            age=8,
            primary=Time(64.32),
            final_time=Time(64.54),
            backups=[[Time(5.0), Time(6.0), Time(7.0)], [Time(8.0)]],
            splits=[Time(24.0), Time(25.0), Time(26.0)],
            is_dq=False,
            is_empty=False,
        )

    def test_merge_info(self, lane1: Lane, lane2: Lane):
        """Test merging info from lane2 into lane1."""
        lane1.merge(lane2)
        # Info from lane2
        assert lane1.name == "Bob"
        assert lane1.team == "Bananas"
        assert lane1.seed_time == Time(2.0)
        assert lane1.age == 8  # noqa: PLR2004
        # Results from lane1
        assert lane1.primary == Time(54.32)
        assert lane1.final_time == Time(54.54)
        assert lane1.backups == [[Time(1.0), Time(2.0), Time(3.0)], [Time(4.0)]]
        assert lane1.splits == [Time(14.0), Time(15.0), Time(16.0)]
        assert lane1.is_dq is True
        assert lane1.is_empty is False
        # None values are merged
        lane2.seed_time = None
        lane1.merge(lane2)
        assert lane1.seed_time is None

    def test_merge_results(self, lane1: Lane, lane2: Lane):
        """Test merging results from lane2 into lane1."""
        lane1.merge(results_from=lane2)
        # Info from lane1
        assert lane1.name == "Alice"
        assert lane1.team == "Apples"
        assert lane1.seed_time == Time(1.0)
        assert lane1.age == 7  # noqa: PLR2004
        # Results from lane2
        assert lane1.primary == Time(64.32)
        assert lane1.final_time == Time(64.54)
        assert lane1.backups == [[Time(5.0), Time(6.0), Time(7.0)], [Time(8.0)]]
        assert lane1.splits == [Time(24.0), Time(25.0), Time(26.0)]
        assert lane1.is_dq is False
        assert lane1.is_empty is False
        # None values are merged
        lane2.splits = None
        lane1.merge(results_from=lane2)
        assert lane1.splits is None


class TestLaneSimilarity:
    """Tests of the similarity method on Lane."""

    def test_empty_lanes_are_similar(self):
        """Two empty lanes are similar."""
        lane1 = Lane()
        lane2 = Lane()
        assert lane1.is_similar_to(lane2)

    def test_similar_checks_simple_fields(self):
        """Two lanes with the same name and team are similar."""
        lane1 = Lane(
            name="A",
            team="B",
            seed_time=Time(1.0),
            age=7,
            primary=Time(4.32),
            final_time=Time(4.54),
            is_dq=True,
            is_empty=False,
        )
        lane2 = Lane(
            name="A",
            team="B",
            seed_time=Time(1.0),
            age=7,
            primary=Time(4.32),
            final_time=Time(4.54),
            is_dq=True,
            is_empty=False,
        )
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)
        lane2.name = "C"
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        lane2.name = None
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)

    def test_similar_checks_splits(self):
        """Similarity checks splits."""
        # matching splits are similar
        lane1 = Lane(splits=[Time(1.0), Time(2.0), Time(3.0)])
        lane2 = Lane(splits=[Time(1.0), Time(2.0), Time(3.0)])
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)
        # different splits are not similar
        lane2.splits = [Time(1.0), Time(2.0), Time(4.0)]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # different number of splits are not similar
        lane2.splits = [Time(1.0), Time(2.0)]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # missing splits are not similar
        lane2.splits = []
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # not supported splits are similar
        lane2.splits = None
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)

    def test_similar_checks_backups(self):
        """Similarity checks backups."""
        # matching backups are similar
        lane1 = Lane(backups=[[Time(1.0), Time(2.0), Time(3.0)]])
        lane2 = Lane(backups=[[Time(1.0), Time(2.0), Time(3.0)]])
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)
        # different backups are not similar
        lane2.backups = [[Time(1.0), Time(2.0), Time(4.0)]]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # different number of backups are not similar
        lane2.backups = [[Time(1.0), Time(2.0)]]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        lane2.backups = [[Time(1.0), Time(2.0), Time(3.0)], [Time(4.0)]]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # missing backups are not similar
        lane2.backups = []
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        lane2.backups = [[]]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        lane2.backups = [[Time(1.0), Time(2.0), Time(3.0)], []]
        assert not lane1.is_similar_to(lane2)
        assert not lane2.is_similar_to(lane1)
        # not supported backups are similar
        lane2.backups = None
        assert lane1.is_similar_to(lane2)
        assert lane2.is_similar_to(lane1)
