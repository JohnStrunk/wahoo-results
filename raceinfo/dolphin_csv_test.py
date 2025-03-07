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

"""Dolphin CSV tests."""

from .dolphin_csv import DolphinCSV
from .eventprocessor import FullProgram
from .time import Heat


class TestDolphinCSV:
    """Tests for DolphinCSV."""

    def test_csv(self):
        """Test writing a CSV file."""
        dolphin = DolphinCSV()
        program: FullProgram = {
            "1": [
                Heat(event="1", description="Event 1", heat=1),
                Heat(event="1", description="Event 1", heat=2),
            ],
            "11": [
                Heat(event="11", description="Event 11", heat=1),
                Heat(event="11", description="Event 11", heat=2),
                Heat(event="11", description="Event 11", heat=3),
            ],
            "2": [
                Heat(event="2", description="Event 2", heat=1),
            ],
        }
        csv = dolphin._prog_to_csv(program)  # type: ignore
        assert csv == [
            "1,Event 1,2,1,A\n",
            "2,Event 2,1,1,A\n",
            "11,Event 11,3,1,A\n",
        ]
