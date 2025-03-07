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

"""Tests for the Dolphin d04 file format."""

import io
import textwrap
from datetime import datetime

import pytest

from .dolphin_do4 import DolphinDo4
from .time import Time

_now = datetime.now()
_meet_seven = "007"
_parse = DolphinDo4().decode


class TestDolphinDo4:
    """Tests for the Dolphin do4 file format."""

    @pytest.fixture()
    def do4_missing_one_time(self):
        """Lane 3 is missing a time."""
        return io.StringIO(
            textwrap.dedent(
                """\
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
            731146ABD1866BB3"""
            )
        )

    @pytest.fixture
    def do4_one_time(self):
        """Lane 1 only has 1 time."""
        return io.StringIO(
            textwrap.dedent(
                """\
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
            9EF6F5121A02D2D5"""
            )
        )

    @pytest.fixture
    def do4_bad_header(self):
        """Invalid header."""
        return io.StringIO(
            textwrap.dedent(
                """\
            INVALIDHEADER
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
            9EF6F5121A02D2D5"""
            )
        )

    @pytest.fixture
    def do4_too_few_lines(self):
        """Invalid number of lines in file."""
        return io.StringIO(
            textwrap.dedent(
                """\
            57;1;1;All
            Lane1;;55.92;
            Lane2;54.86;55.18;54.98
            Lane7;0;0;0
            Lane8;0;0;0
            Lane9;0;0;0
            Lane10;0;0;0
            9EF6F5121A02D2D5"""
            )
        )

    @pytest.fixture
    def do4_corrupt_lane(self):
        """Lane6 has bad format."""
        return io.StringIO(
            textwrap.dedent(
                """\
            57;1;1;All
            Lane1;;55.92;
            Lane2;54.86;55.18;54.98
            Lane3;40.03;40.05;39.96
            Lane4;39.71;39.68;39.75
            Lane5;50.01;49.88;49.90
            Lane6;0=bad=0
            Lane7;0;0;0
            Lane8;0;0;0
            Lane9;0;0;0
            Lane10;0;0;0
            9EF6F5121A02D2D5"""
            )
        )

    @pytest.fixture
    def do4_no_event(self):
        """
        File with no event number.

        This is a valid do4 file, and happens when there are no events loaded
        into the Dolphin software. See:
        https://github.com/JohnStrunk/wahoo-results/issues/576
        """
        return io.StringIO(
            textwrap.dedent(
                """\
            ;1;1;All
            Lane1;45.37;;
            Lane2;41.82;;
            Lane3;40.04;;
            Lane4;38.99;;
            Lane5;42.58;;
            Lane6;44.68;;
            Lane7;0;0;0
            Lane8;0;0;0
            Lane9;0;0;0
            Lane10;0;0;0
            2D1675FF291271FB"""
            )
        )

    def test_can_parse_header(self, do4_missing_one_time: io.StringIO) -> None:
        """Ensure we can parse the event/heat header."""
        race = _parse(do4_missing_one_time)
        assert race.event == "69"
        assert race.heat == 1

    def test_invalid_header(self, do4_bad_header: io.StringIO) -> None:
        """Ensure we catch an invalid header."""
        with pytest.raises(ValueError):
            _parse(do4_bad_header)

    def test_invalid_number_of_lines(self, do4_too_few_lines: io.StringIO) -> None:
        """Ensure we catch an invalid number of lines."""
        with pytest.raises(ValueError):
            _parse(do4_too_few_lines)

    def test_invalid_lane_data(self, do4_corrupt_lane: io.StringIO) -> None:
        """Ensure we catch a corrupt lane."""
        with pytest.raises(ValueError):
            _parse(do4_corrupt_lane)

    def test_handle_missing_times(
        self, do4_missing_one_time: io.StringIO, do4_one_time: io.StringIO
    ) -> None:
        """Ensure we can handle lanes that are missing times."""
        missingt1l3 = _parse(do4_missing_one_time)
        assert missingt1l3.lane(3).backups == [
            None,
            Time("128.21"),
            Time("128.08"),
        ]

        one_time = _parse(do4_one_time)
        assert one_time.lane(1).backups == [
            None,
            Time("55.92"),
            None,
        ]

    def test_no_description(self, do4_one_time: io.StringIO) -> None:
        """DO4 files don't have an event description."""
        no_desc = _parse(do4_one_time)
        assert no_desc.description is None

    def test_parse_no_event(self, do4_no_event: io.StringIO) -> None:
        """Ensure we can parse a file with no event number."""
        no_event = _parse(do4_no_event)
        # Since there's no event number, we just get an empty string
        assert no_event.event == ""
        # Ensure the rest of the data is correct
        assert no_event.heat == 1
        assert no_event.lane(2).backups == [
            Time("41.82"),
            None,
            None,
        ]
