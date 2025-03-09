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

"""Tests for the Dolphin file formats."""

import os
import pathlib

from raceinfo.timingsystem import TimingSystem

from .dolphin_do4 import DolphinDo4
from .heat_test import check_heat_is_similar
from .time import Heat, Lane, Time

testdata_dir = os.path.join(os.path.dirname(__file__), "testdata-dolphin")


def unused(num: int, num_splits: int = 1) -> list[Lane]:
    """Return a list of num unused lanes."""
    splits: list[list[Time | None]] = []
    for _ in range(num_splits):
        splits.append([None, None, None])
    return [
        Lane(
            backups=[None, None, None],
            splits=splits,
            is_dq=False,
            is_empty=False,
        )
        for _ in range(num)
    ]


def round_trip(heat: Heat, system: TimingSystem, path: pathlib.Path) -> Heat:
    """Round trip a heat, writing it to a file and reading it back.

    :param heat: The heat to write
    :param system: The timing system to use for writing & reading
    :param path: The directory to write the file to
    :returns: The heat read back from the file
    """
    filename = system.filename(heat) or "outfile"
    system.write(str(path / filename), heat)
    return system.read(str(path / filename))


class TestDolphin:
    """Tests for the Dolphin file formats."""

    def test_m8r1(self, tmp_path: pathlib.Path):
        """Meet 8, Race 1: Missing times."""
        actual = Heat(
            event="1",
            heat=1,
            description="Missing times",
            meet_id="008",
            race=1,
            round="A",
            lanes=[
                Lane(
                    backups=[Time("25.88"), Time("25.88"), Time("25.88")],
                    splits=[[Time("25.88"), Time("25.88"), Time("25.88")]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    backups=[None, Time("43.42"), Time("43.41")],
                    splits=[[None, Time("43.42"), Time("43.41")]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    backups=[Time("50.57"), None, Time("50.58")],
                    splits=[[Time("50.57"), None, Time("50.58")]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    backups=[Time("54.45"), Time("54.46"), None],
                    splits=[[Time("54.45"), Time("54.46"), None]],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(6),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)
        DolphinDo4().write(do4_filename, actual)

    def test_m8r2(self, tmp_path: pathlib.Path):
        """Meet 8, Race 2: Missing times."""
        actual = Heat(
            event="1",
            heat=2,
            description="Missing times",
            meet_id="008",
            race=2,
            round="A",
            lanes=[
                Lane(
                    backups=[Time("9.80"), None, None],
                    splits=[[Time("9.80"), None, None]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    backups=[None, Time("11.52"), None],
                    splits=[[None, Time("11.52"), None]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    backups=[None, None, Time("13.40")],
                    splits=[[None, None, Time("13.40")]],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(7),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r3(self, tmp_path: pathlib.Path):
        """Meet 8, Race 3: Empty and DQ markings."""
        actual = Heat(
            event="2",
            heat=1,
            description="Empty and DQ markings",
            meet_id="008",
            race=3,
            round="A",
            lanes=[
                Lane(is_dq=False, is_empty=False),
                Lane(
                    backups=[None, Time("31.23"), None],
                    splits=[[None, Time("31.23"), None]],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    is_dq=False,
                    is_empty=True,
                ),
                Lane(
                    backups=[Time("52.87"), Time("53.38"), Time("53.91")],
                    splits=[[Time("52.87"), Time("53.38"), Time("53.91")]],
                    is_dq=False,
                    is_empty=True,
                ),
                Lane(
                    is_dq=True,
                    is_empty=False,
                ),
                Lane(
                    backups=[Time("75.84"), Time("76.15"), Time("76.92")],
                    splits=[[Time("75.84"), Time("76.15"), Time("76.92")]],
                    is_dq=True,
                    is_empty=False,
                ),
                *unused(4),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r4(self, tmp_path: pathlib.Path):
        """Meet 8, Race 4: One intermediate split."""
        actual = Heat(
            event="3",
            heat=1,
            description="One intermediate split",
            meet_id="008",
            race=4,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("21.01"), Time("21.00"), Time("21.00")],
                        [Time("33.35"), Time("33.43"), Time("33.35")],
                    ],
                    backups=[Time("33.35"), Time("33.43"), Time("33.35")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[
                        [Time("50.58"), None, Time("50.57")],
                        [Time("61.63"), None, Time("61.62")],
                    ],
                    backups=[Time("61.63"), None, Time("61.62")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[
                        [Time("91.08"), Time("91.08"), None],
                        [Time("102.89"), Time("102.88"), None],
                    ],
                    backups=[Time("102.89"), Time("102.88"), None],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(7, num_splits=2),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r5(self, tmp_path: pathlib.Path):
        """Meet 8, Race 5: Two intermediate splits."""
        actual = Heat(
            event="4",
            heat=1,
            description="Two intermediate splits",
            meet_id="008",
            race=5,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("15.42"), Time("15.46"), Time("15.41")],
                        [Time("25.41"), Time("25.44"), Time("25.43")],
                        [Time("35.09"), Time("35.14"), Time("35.09")],
                    ],
                    backups=[Time("35.09"), Time("35.14"), Time("35.09")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[
                        [None, None, Time("58.58")],
                        [None, None, Time("71.42")],
                        [None, None, Time("81.47")],
                    ],
                    backups=[None, None, Time("81.47")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[
                        [None, Time("101.58"), None],
                        [None, Time("112.18"), None],
                        [None, Time("123.20"), None],
                    ],
                    backups=[None, Time("123.20"), None],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(7, num_splits=3),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r6(self, tmp_path: pathlib.Path):
        """Meet 8, Race 6: Three intermediate splits."""
        actual = Heat(
            event="5",
            heat=1,
            description="Three intermediate splits",
            meet_id="008",
            race=6,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("15.20"), Time("15.19"), Time("15.18")],
                        [Time("22.98"), Time("23.01"), Time("22.99")],
                        [Time("31.43"), Time("31.45"), Time("31.42")],
                        [Time("40.51"), Time("40.53"), Time("40.51")],
                    ],
                    backups=[Time("40.51"), Time("40.53"), Time("40.51")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(1, num_splits=4),
                Lane(
                    splits=[
                        [None, Time("106.54"), None],
                        [None, Time("113.70"), None],
                        [None, Time("120.46"), None],
                        [None, Time("127.65"), None],
                    ],
                    backups=[None, Time("127.65"), None],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(7, num_splits=4),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r7(self, tmp_path: pathlib.Path):
        """Meet 8, Race 7: Chars - && in event name."""
        actual = Heat(
            event="6",
            heat=1,
            description="Chars - && in event name",
            meet_id="008",
            race=7,
            round="A",
            lanes=[
                *unused(2),
                Lane(
                    splits=[[Time("15.20"), Time("15.23"), Time("15.22")]],
                    backups=[Time("15.20"), Time("15.23"), Time("15.22")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(7),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r8(self, tmp_path: pathlib.Path):
        """Meet 8, Race 8: Round Prelim."""
        actual = Heat(
            event="7",
            heat=1,
            description="Round Prelim",
            meet_id="008",
            race=8,
            round="P",
            lanes=[
                Lane(
                    splits=[[Time("12.29"), Time("12.28"), Time("12.28")]],
                    backups=[Time("12.29"), Time("12.28"), Time("12.28")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r9(self, tmp_path: pathlib.Path):
        """Meet 8, Race 9: Round Final."""
        actual = Heat(
            event="8",
            heat=1,
            description="Round Final",
            meet_id="008",
            race=9,
            round="F",
            lanes=[
                Lane(
                    splits=[[Time("11.89"), Time("11.92"), Time("11.92")]],
                    backups=[Time("11.89"), Time("11.92"), Time("11.92")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r10(self, tmp_path: pathlib.Path):
        """Meet 8, Race 10: No events loaded."""
        actual = Heat(
            event="",
            heat=1,
            description="",
            meet_id="008",
            race=10,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("11.91"), Time("11.94"), Time("11.91")]],
                    backups=[Time("11.91"), Time("11.94"), Time("11.91")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r11(self, tmp_path: pathlib.Path):
        """Meet 8, Race 11: Numbering 0-9."""
        actual = Heat(
            event="10",
            heat=1,
            description="Numbering 0-9",
            meet_id="008",
            race=11,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("11.35"), Time("11.35"), Time("11.36")]],
                    backups=[Time("11.35"), Time("11.35"), Time("11.36")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[[Time("21.62"), Time("21.63"), Time("21.62")]],
                    backups=[Time("21.62"), Time("21.63"), Time("21.62")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(8),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m8r12(self, tmp_path: pathlib.Path):
        """Meet 8, Race 12: Numbering 0-9."""
        actual = Heat(
            event="10",
            heat=2,
            description="Numbering 0-9",
            meet_id="008",
            race=12,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("12.16"), Time("12.18"), Time("12.15")]],
                    backups=[Time("12.16"), Time("12.18"), Time("12.15")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(8),
                Lane(
                    splits=[[None, None, Time("19.19")]],
                    backups=[None, None, Time("19.19")],
                    is_dq=False,
                    is_empty=False,
                ),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r1(self, tmp_path: pathlib.Path):
        """Meet 9, Race 1: No events loaded."""
        actual = Heat(
            event="",
            heat=1,
            description="",
            meet_id="009",
            race=1,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("11.16"), Time("11.17"), Time("11.16")]],
                    backups=[Time("11.16"), Time("11.17"), Time("11.16")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r2(self, tmp_path: pathlib.Path):
        """Meet 9, Race 2: No events loaded."""
        actual = Heat(
            event="",
            heat=1,
            description="",
            meet_id="009",
            race=2,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("7.30"), Time("7.31"), Time("7.30")]],
                    backups=[Time("7.30"), Time("7.31"), Time("7.30")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r3(self, tmp_path: pathlib.Path):
        """Meet 9, Race 3: No events loaded."""
        actual = Heat(
            event="",
            heat=4,
            description="",
            meet_id="009",
            race=3,
            round="A",
            lanes=[
                Lane(
                    splits=[[Time("10.60"), Time("10.60"), Time("10.59")]],
                    backups=[Time("10.60"), Time("10.60"), Time("10.59")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r4(self, tmp_path: pathlib.Path):
        """Meet 9, Race 4: Extra splits."""
        actual = Heat(
            event="4",
            heat=1,
            description="Extra splits",
            meet_id="009",
            race=4,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("11.85"), Time("11.89"), Time("11.83")],
                        [Time("20.18"), Time("20.19"), Time("20.19")],
                    ],
                    backups=[Time("20.18"), Time("20.19"), Time("20.19")],
                    is_dq=False,
                    is_empty=False,
                ),
                Lane(
                    splits=[
                        [Time("33.90"), Time("33.91"), Time("33.91")],
                        [Time("50.27"), Time("50.28"), Time("50.28")],
                    ],
                    backups=[Time("50.27"), Time("50.28"), Time("50.28")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(8, num_splits=2),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r5(self, tmp_path: pathlib.Path):
        """Meet 9, Race 5: Extra splits."""
        actual = Heat(
            event="",
            heat=1,
            description="Extra splits",
            meet_id="009",
            race=5,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("3.84"), None, None],
                        [Time("14.99"), None, None],
                    ],
                    backups=[Time("14.99"), None, None],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9, num_splits=2),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)

    def test_m9r6(self, tmp_path: pathlib.Path):
        """Meet 9, Race 6: Extra splits."""
        actual = Heat(
            event="",
            heat=1,
            description="Extra splits",
            meet_id="009",
            race=6,
            round="A",
            lanes=[
                Lane(
                    splits=[
                        [Time("8.67"), Time("16.13"), Time("16.12")],
                        [Time("30.73"), Time("30.76"), Time("30.73")],
                    ],
                    backups=[Time("30.73"), Time("30.76"), Time("30.73")],
                    is_dq=False,
                    is_empty=False,
                ),
                *unused(9, num_splits=2),
            ],
        )
        do4_filename = DolphinDo4().filename(actual) or ""
        do4 = DolphinDo4().read(os.path.join(testdata_dir, do4_filename))
        check_heat_is_similar(actual, do4)
        do4_rt = round_trip(actual, DolphinDo4(), tmp_path)
        check_heat_is_similar(actual, do4_rt)
