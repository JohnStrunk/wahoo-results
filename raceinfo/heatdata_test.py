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

"""Tests for HeatData object."""

# ruff: noqa: PLR2004 - Ignore magic numbers

import pytest

from .heatdata import HeatData
from .times import NO_SHOW, NT, NumericTime, Time


class TestHeatData:
    """Tests for HeatData object."""

    @pytest.fixture(scope="class")
    def setup_startlist(self) -> HeatData:
        """Create a HeatData object that is a startlist."""
        return HeatData(
            description="100 Fly",
            event="123Z",
            heat=3,
            lanes=[
                HeatData.Lane(
                    name="Alice",
                    team="Team A",
                    seed_time=NumericTime(1.0),
                    age=10,
                )
            ]
            + [
                HeatData.Lane(
                    name="Charlie",
                    team="Team B",
                    seed_time=NumericTime(2.0),
                    age=99,
                )
                for _ in range(9)
            ],
        )

    def test_startlist_init(self, setup_startlist: HeatData):
        """Initialization of HeatData object."""
        assert setup_startlist.description == "100 Fly"
        assert setup_startlist.event == "123Z"
        assert setup_startlist.heat == 3

    def test_startlist_lane_init(self, setup_startlist: HeatData):
        """Initialization of Lane object."""
        lane = setup_startlist.lane(1)
        assert lane.name == "Alice"
        assert lane.team == "Team A"
        assert lane.seed_time == NumericTime(1.0)
        assert lane.age == 10
        lane = setup_startlist.lane(2)
        assert lane.name == "Charlie"
        assert lane.team == "Team B"
        assert lane.seed_time == NumericTime(2.0)
        assert lane.age == 99

    def test_startlist_max_lanes(self):
        """Ensure we can't have more than 10 lanes."""
        with pytest.raises(ValueError):
            HeatData(
                description="200 Freestyle",
                event="123S",
                heat=99,
                lanes=[HeatData.Lane() for _ in range(11)],
            )

    def test_startlist_negative_age(self):
        """Ensure we can't have a negative age."""
        with pytest.raises(ValueError):
            HeatData.Lane(
                name="Alice",
                team="Team A",
                seed_time=NumericTime(1.0),
                age=-1,
            )

    def test_startlist_negative_seed_time(self):
        """Ensure we can't have a negative seed time."""
        with pytest.raises(ValueError):
            HeatData.Lane(
                name="Alice",
                team="Team A",
                seed_time=NumericTime(-1.0),
                age=10,
            )

    def test_startlist_seed_time_nt(self):
        """Start list seed time can be NT."""
        lane = HeatData.Lane(
            name="Alice",
            team="Team A",
            seed_time=NT,
            age=10,
        )
        assert lane.seed_time == NT

    def test_startlist_invalid_seed_time(self):
        """Ensure we can't have an invalid seed time."""
        with pytest.raises(ValueError):
            HeatData.Lane(
                name="Alice",
                team="Team A",
                seed_time=NO_SHOW,
                age=10,
            )

    def test_results_init(self):
        """Initialization of HeatData object that is a race result."""
        lane = HeatData.Lane(times=[NumericTime(1.0)], is_dq=False, is_empty=False)
        data = HeatData(
            event="1S",
            heat=2,
            race=3,
            meet_id="123",
            lanes=[lane],
        )
        assert data.event == "1S"
        assert data.heat == 2
        assert data.race == 3
        assert data.meet_id == "123"
        assert data.lane(1) == lane
        assert data.lane(2).is_empty

    def test_lane_empty(self):
        """Test if a lane is empty."""
        empty_lane = HeatData.Lane()  # No times
        assert empty_lane.is_empty
        marked_empty = HeatData.Lane(
            times=[NumericTime(0.0), NumericTime(0.0)], is_empty=True
        )
        assert marked_empty.is_empty
        not_empty = HeatData.Lane(times=[NumericTime(0.0), NumericTime(1.0)])
        assert not not_empty.is_empty

    def test_lane_dq(self):
        """Test if a lane is DQ."""
        dq_lane = HeatData.Lane(times=[NumericTime(1.0)], is_dq=True)
        assert dq_lane.is_dq
        not_dq = HeatData.Lane(times=[NumericTime(1.0)], is_dq=False)
        assert not not_dq.is_dq
        default = HeatData.Lane(times=[NumericTime(1.0)])
        assert not default.is_dq

    def test_neg_lane_time(self):
        """Ensure we can't have a negative time."""
        with pytest.raises(ValueError):
            HeatData.Lane(times=[NumericTime(-1.0)])
        with pytest.raises(ValueError):
            HeatData.Lane(times=[NumericTime(1.0), NumericTime(-1.0)])

    def test_heat_range(self):
        """Ensure we can't have a heat number less than 1."""
        with pytest.raises(ValueError):
            HeatData(event="23", heat=0, lanes=[])
        with pytest.raises(ValueError):
            HeatData(event="23", heat=-1, lanes=[])

    def test_race_range(self):
        """Ensure we can't have a race number less than 1."""
        with pytest.raises(ValueError):
            HeatData(event="23", race=0, heat=1, lanes=[])
        with pytest.raises(ValueError):
            HeatData(event="23", race=-1, heat=1, lanes=[])

    def test_lane_range(self):
        """Ensure we can't have a lane number less than 1 or greater than 10."""
        with pytest.raises(ValueError):
            HeatData(event="23", heat=1, lanes=[]).lane(0)
        with pytest.raises(ValueError):
            HeatData(event="23", heat=1, lanes=[]).lane(11)
        HeatData(event="23", heat=1, lanes=[]).lane(5)  # Ok

    def test_resolver(self):
        """Test the time resolver function."""
        resolver_calls = 0

        def take_first(times: list[NumericTime]) -> Time:
            nonlocal resolver_calls
            resolver_calls += 1
            return times[0]

        lane = HeatData.Lane(
            times=[NumericTime(1.0), NumericTime(1.2), NumericTime(1.4)]
        )
        data = HeatData(event="23", heat=1, lanes=[lane])
        assert data.resolver is None  # No default resolver
        with pytest.raises(ValueError):
            data.lane(1).time()  # No resolver set

        data.resolver = take_first
        assert data.lane(1).time() == NumericTime(1.0)
        assert resolver_calls == 1

    @pytest.fixture(scope="class")
    def result(self):
        """Create a Heat with results."""
        result1 = HeatData.Lane(times=[NumericTime(1.0), NumericTime(1.2)])
        result2 = HeatData.Lane(times=[NumericTime(1.4), NumericTime(1.6)])
        return HeatData(
            event="23", heat=1, meet_id="8", race=321, lanes=[result1, result2]
        )

    @pytest.fixture(scope="class")
    def info(self):
        """Create a Heat with start list info."""
        info1 = HeatData.Lane(
            name="Alice", team="Team A", seed_time=NumericTime(10.0), age=10
        )
        info2 = HeatData.Lane(
            name="Bob", team="Team B", seed_time=NumericTime(20.0), age=20
        )
        return HeatData(event="230", heat=10, lanes=[info1, info2])

    def test_merge_ri(self, result: HeatData, info: HeatData):
        """Test merging info into results."""
        result.merge(info_from=info)
        assert result.event == "230"
        assert result.heat == 10
        assert result.meet_id == "8"
        assert result.lane(1).name == "Alice"
        assert result.lane(2).age == 20
        assert result.lane(1).seed_time == NumericTime(10.0)
        assert result.lane(2).times == [
            NumericTime(1.4),
            NumericTime(1.6),
        ]

    def test_merge_ir(self, result: HeatData, info: HeatData):
        """Test merging results into info."""
        info.merge(results_from=result)
        assert info.event == "230"
        assert info.heat == 10
        assert info.meet_id == "8"
        assert info.lane(1).name == "Alice"
        assert info.lane(2).age == 20
        assert info.lane(1).seed_time == NumericTime(10.0)
        assert info.lane(2).times == [
            NumericTime(1.4),
            NumericTime(1.6),
        ]


class TestHeatDataPlace:
    """Tests for HeatData.place()."""

    @pytest.fixture(scope="class")
    def result(self):
        """Create a Heat with results."""

        # Simple time resolver that takes the first time
        def take_first(times: list[NumericTime]) -> Time:
            if not times:
                return NO_SHOW
            return times[0]

        return HeatData(
            event="23",
            heat=1,
            meet_id="8",
            race=321,
            lanes=[
                HeatData.Lane(times=[NumericTime(1.4), NumericTime(1.6)]),
                HeatData.Lane(times=[NumericTime(1.8), NumericTime(2.0)]),
                HeatData.Lane(times=[]),
                HeatData.Lane(times=[NumericTime(1.0), NumericTime(1.2)]),
            ],
            time_resolver=take_first,
        )

    def test_place(self, result: HeatData):
        """Test the place() method."""
        assert result.place(1) == 2
        assert result.place(2) == 3
        assert result.place(3) is None
        assert result.place(4) == 1
