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

"""Tests for RaceResult"""

import pytest

from raceresult import RaceResult
from racetime import NumericTime


class TestRaceResult:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lane = RaceResult.Lane(
            times=[NumericTime(1.0)], is_dq=False, is_empty=False
        )
        self.race_result = RaceResult(
            event="1S",
            heat=1,
            description="Boys 100 Meter Freestyle",
            lanes=[self.lane],
        )

    def test_lane_init(self):
        assert self.lane.times == [NumericTime(1.0)]
        assert self.lane.is_dq == False
        assert self.lane.is_empty == False
        print(self.lane)

    def test_race_result_init(self):
        assert self.race_result.event == "1S"
        assert self.race_result.heat == 1
        assert self.race_result.description == "Boys 100 Meter Freestyle"
        assert len(self.race_result.lanes) == 10
        assert self.race_result.lanes[0] == self.lane

    def test_race_result_event_uppercase(self):
        assert self.race_result.event == "1S"

    def test_race_result_heat_greater_than_zero(self):
        with pytest.raises(ValueError):
            RaceResult(
                event="1S",
                heat=0,
                description="Boys 100 Meter Freestyle",
                lanes=[self.lane],
            )

    def test_race_result_max_lanes(self):
        with pytest.raises(ValueError):
            RaceResult(
                event="1S",
                heat=1,
                description="Boys 100 Meter Freestyle",
                lanes=[self.lane] * 11,
            )

    def test_lane_time_greater_than_zero(self):
        with pytest.raises(ValueError):
            RaceResult.Lane(times=[NumericTime(-1.0)], is_dq=False, is_empty=False)

    def test_lane_empty(self):
        lane = RaceResult.Lane()
        assert lane.is_empty == True
