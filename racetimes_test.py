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

from datetime import datetime
import io
import textwrap
import pytest

from racetimes import RaceTimes, DO4, Time, RawTime
from startlist import StartList

now = datetime.now()
meet_seven = "007"

@pytest.fixture
def do4_mising_one_time():
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
def do4_big_delta():
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

@pytest.fixture
def do4_one_time():
    """Lane w/ only 1 time"""
    return io.StringIO(textwrap.dedent("""\
        57;1;1;All
        Lane1;;55.92;
        Lane2;54.86;55.18;54.98
        Lane3;40.03;40.05;39.96
        Lane4;39.71;39.68;39.75
        Lane5;50.01;49.88;49.90
        Lane6;0;0;0
        Lane7;0;0;0
        Lane8;0;0;0
        Lane9;0;0;0
        Lane10;0;0;0
        9EF6F5121A02D2D5"""))

def test_can_parse_header(do4_mising_one_time) -> None:
    """Ensure we can parse the event/heat header"""
    race:RaceTimes = DO4(do4_mising_one_time, 2, RawTime(0.30), now, meet_seven)
    assert race.event == 69
    assert race.heat == 1

def test_resolve_times(do4_mising_one_time) -> None:
    """Ensure we can calculate final times correctly"""
    race:RaceTimes = DO4(do4_mising_one_time, 2, RawTime("0.30"), now, meet_seven)

    assert len(race.times(1)) == 3
    assert race.final_time(1).is_valid
    assert race.final_time(1).value == RawTime("143.37")

    assert len(race.times(3)) == 3
    assert race.final_time(3).is_valid
    assert race.final_time(3).value == RawTime("128.14")

def test_toofew_times(do4_mising_one_time) -> None:
    """Final time is invalid if too few raw times"""
    race:RaceTimes = DO4(do4_mising_one_time, 3, RawTime("0.30"), now, meet_seven)
    assert len(race.times(3)) == 3
    assert not race.final_time(3).is_valid
    assert race.final_time(3).value == RawTime("128.14")

def test_largedelta_times(do4_big_delta) -> None:
    """Final time is invalid if too few raw times"""

    race:RaceTimes = DO4(do4_big_delta, 2, RawTime("0.30"), now, meet_seven)
    assert len(race.times(1)) == 3
    assert not race.final_time(1).is_valid
    assert race.final_time(1).value == RawTime("130.63")

    times = race.times(1)
    assert times[0] == Time(RawTime("160.72"), False)
    assert times[1] == Time(RawTime("130.63"), True)
    assert times[2] == Time(RawTime("130.61"), True)

def test_one_zero_times(do4_one_time) -> None:
    """Ensure we can calculate final times correctly"""
    race:RaceTimes = DO4(do4_one_time, 2, RawTime("0.30"), now, meet_seven)

    assert race.times(1) == [None, Time(RawTime("55.92"), True), None]
    assert not race.final_time(1).is_valid
    assert race.final_time(1).value == RawTime("55.92")

    assert len(race.times(7)) == 3
    assert not race.final_time(7).is_valid
    assert race.final_time(7).value == RawTime("0")

def test_places() -> None:
    """Ensure we can calculate places correctly"""
    data = io.StringIO(textwrap.dedent("""\
        1;1;1;All
        Lane1;55.92;55.92;
        Lane2;54.86;54.86;
        Lane3;;39.96;39.96
        Lane4;39.71;;39.71
        Lane5;50.00;60.00;
        Lane6;;54.86;54.86
        Lane7;0;0;0
        Lane8;0;0;0
        Lane9;0;0;0
        Lane10;0;0;0
        9EF6F5121A02D2D5"""))
    race:RaceTimes = DO4(data, 2, RawTime("0.30"), now, meet_seven)
    assert race.place(4) == 1  # Lane 4 is 1st
    assert race.place(3) == 2  # Lane 3 is 2nd
    assert race.place(2) == 3  # Lane 2 tied for 3rd
    assert race.place(6) == 3  # Lane 6 tied for 3rd
    assert race.place(1) == 5  # No 4th place due to tie
    assert race.place(5) is None  # Lane 5 has invalid time
    assert race.place(8) is None  # Lane 8 is empty

class MockStartList(StartList):
    '''Mock StartList'''
    @property
    def event_name(self) -> str:
        '''Get the event name (description)'''
        return "Mock event name"
    def name(self, _heat: int, _lane: int) -> str:
        '''Retrieve the Swimmer's name for a heat/lane'''
        return f"Swimmer{_heat}:{_lane}"
    def team(self, _heat: int, _lane: int) -> str:
        '''Retrieve the Swimmer's team for a heat/lane'''
        return f"Team{_heat}:{_lane}"

def test_names(do4_one_time) -> None:
    race:RaceTimes = DO4(do4_one_time, 2, RawTime("0.30"), now, meet_seven)
    race.set_names(MockStartList())

    assert race.event_name == "Mock event name"
    assert race.name(4) == "Swimmer1:4"
    assert race.team(6) == "Team1:6"

def test_default_names(do4_one_time) -> None:
    race:RaceTimes = DO4(do4_one_time, 2, RawTime("0.30"), now, meet_seven)

    assert race.event_name == ""
    assert race.name(4) == ""
    assert race.team(6) == ""

def test_noshow(do4_one_time) -> None:
    race:RaceTimes = DO4(do4_one_time, 2, RawTime("0.30"), now, meet_seven)
    # We haven't loaded any names, so lanes w/o times should not be NS
    assert not race.is_noshow(1) # invalid, but not NS
    assert not race.is_noshow(2)
    assert not race.is_noshow(9)

    race.set_names(MockStartList())
    assert not race.is_noshow(1) # invalid, but not NS
    assert not race.is_noshow(2)
    assert race.is_noshow(9) # all lanes have names
