# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2022 - John D. Strunk
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

"""Tests for RaceTimes"""

from decimal import Decimal
import io
import textwrap
import pytest

from racetimes import RaceTimes, D04, Time

@pytest.fixture
def d04_mising_one_time():
    """A D04 that is missing a time in lane 3"""
    return io.StringIO(textwrap.dedent("""\
        69;1;1;All
        Lane1;143.37;143.37;143.39
        Lane2;135.15;135.39;135.20
        Lane3;;128.21;128.08
        Lane4;144.46;144.43;144.56
        Lane5;133.32;133.61;133.69
        Lane6;149.58;149.58;149.65
        Lane7;0;0;0
        Lane8;0;0;0
        Lane9;0;0;0
        Lane10;0;0;0
        731146ABD1866BB3"""))

@pytest.fixture
def d04_big_delta():
    """A D04 that has an outlier in 1"""
    return io.StringIO(textwrap.dedent("""\
        1;1;1;All
        Lane1;160.72;130.63;130.61
        Lane2;138.56;138.69;138.58
        Lane3;97.24;97.22;97.29
        Lane4;122.92;122.88;122.84
        Lane5;130.84;130.77;130.82
        Lane6;152.95;153.15;152.85
        Lane7;0;0;0
        Lane8;0;0;0
        Lane9;0;0;0
        Lane10;0;0;0
        2CBB478C916F0ADA"""))

def test_can_parse_header(d04_mising_one_time) -> None:
    """Ensure we can parse the event/heat header"""
    race:RaceTimes = D04(d04_mising_one_time, 2, Decimal(0.30))
    assert race.event == 69
    assert race.heat == 1

def test_resolve_times(d04_mising_one_time) -> None:
    """Ensure we can calculate final times correctly"""
    race:RaceTimes = D04(d04_mising_one_time, 2, Decimal("0.30"))

    assert len(race.times(1)) == 3
    assert race.final_time(1).is_valid
    assert race.final_time(1).value == Decimal("143.37")

    assert len(race.times(3)) == 3
    assert race.final_time(3).is_valid
    assert race.final_time(3).value == Decimal("128.14")

def test_toofew_times(d04_mising_one_time) -> None:
    """Final time is invalid if too few raw times"""
    race:RaceTimes = D04(d04_mising_one_time, 3, Decimal("0.30"))
    assert len(race.times(3)) == 3
    assert not race.final_time(3).is_valid
    assert race.final_time(3).value == Decimal("128.14")

def test_largedelta_times(d04_big_delta) -> None:
    """Final time is invalid if too few raw times"""

    race:RaceTimes = D04(d04_big_delta, 2, Decimal("0.30"))
    assert len(race.times(1)) == 3
    assert not race.final_time(1).is_valid
    assert race.final_time(1).value == Decimal("130.63")

    times = race.times(1)
    assert times[0] == Time(Decimal("160.72"), False)
    assert times[1] == Time(Decimal("130.63"), True)
    assert times[2] == Time(Decimal("130.61"), True)
