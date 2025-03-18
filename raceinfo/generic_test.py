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

"""Tests for the generic file format."""

import io
import os
import pathlib
import textwrap

import pytest

from .dolphin_test import check_heat_is_similar, round_trip
from .generic import Generic
from .time import Heat, Lane, Time, parse_time

_parse = Generic().decode
_testdata_dir = os.path.join(os.path.dirname(__file__), "testdata-generic")


def _unused(num: int, num_splits: int = 1) -> list[Lane]:
    """Return a list of num unused lanes."""
    splits: list[list[Time | None]] = []
    for _ in range(num_splits):
        splits.append([None])
    return [
        Lane(
            backups=[None, None, None],
            splits=splits,
            is_dq=False,
            is_empty=False,
        )
        for _ in range(num)
    ]


class TestGeneric:
    """Tests for the Generic file format."""

    @pytest.fixture()
    def spec_sample(self):
        """Sample data from the specification."""
        return io.StringIO(
            textwrap.dedent(
                """\
            21;3;4;F;110;Timer Name;1.0.0.0
            7;32.18;77.87;95.67;126.83;126.99;127.01;126.77;+0.78;;;
            4;31.01;76.68;97.36;125.72;125.49;;125.55;+0.63;;;
            5;31.36;77.13;;126.11;126.03;126.12;126.20;+0.88;;;
            3;30.34;76.24;97.81;125.35;125.38;125.40;125.32;+;;;
            6;31.85;77.51;96.22;126.45;126.44;126.50;126.57;+0.60;;;
            2;29.88;75.71;98.22;124.96;;124.88;124.82;+0.77;;;
            Q;32.52;78.25;95.16;127.18;127.40;127.45;127.38;+0.92;;;
            1;27.46;75.20;98.54;124.58;;124.67;;+0.69;;;
            0;;;;;;;;;;;
            0;;;;;;;;;;;
            0;;;;;;;;;;;
            0;;;;;;;;;;;"""
            )
        )

    def test_can_parse_header(self, spec_sample: io.StringIO) -> None:
        """Ensure we can parse the file header."""
        race = _parse(spec_sample)
        assert race.event == "21"
        assert race.heat == 3  # noqa: PLR2004
        assert race.round == "F"

    def test_filename(self) -> None:
        """Ensure we can generate a filename from a heat."""
        heat = Heat(meet_id="73", event="32", heat=41, race=432)
        assert Generic().filename(heat) == "073-032-41F0432.gen"
        heat.round = "P"
        assert Generic().filename(heat) == "073-032-41P0432.gen"
        heat.event = "32A"
        assert Generic().filename(heat) == "073-032A41P0432.gen"

    def test_similarity(self, tmp_path: pathlib.Path) -> None:
        """Test parsing the sample file."""
        actual = Heat(
            event="21",
            heat=3,
            meet_id="5",
            race=2,
            round="F",
            lanes=[
                Lane(
                    backups=[Time("126.99"), Time("127.01"), Time("126.77")],
                    splits=[
                        [Time("32.18")],
                        [Time("77.87")],
                        [Time("95.67")],
                        [Time("126.83")],
                    ],
                    is_dq=False,
                ),
                Lane(
                    backups=[Time("125.49"), None, Time("125.55")],
                    splits=[
                        [Time("31.01")],
                        [Time("76.68")],
                        [Time("97.36")],
                        [Time("125.72")],
                    ],
                    is_dq=False,
                ),
                Lane(
                    backups=[Time("126.03"), Time("126.12"), Time("126.20")],
                    splits=[[Time("31.36")], [Time("77.13")], [None], [Time("126.11")]],
                    is_dq=False,
                ),
                Lane(
                    backups=[Time("125.38"), Time("125.40"), Time("125.32")],
                    splits=[
                        [Time("30.34")],
                        [Time("76.24")],
                        [Time("97.81")],
                        [Time("125.35")],
                    ],
                    is_dq=False,
                ),
                Lane(
                    backups=[Time("126.44"), Time("126.50"), Time("126.57")],
                    splits=[
                        [Time("31.85")],
                        [Time("77.51")],
                        [Time("96.22")],
                        [Time("126.45")],
                    ],
                    is_dq=False,
                ),
                Lane(
                    backups=[None, Time("124.88"), Time("124.82")],
                    splits=[
                        [Time("29.88")],
                        [Time("75.71")],
                        [Time("98.22")],
                        [Time("124.96")],
                    ],
                    is_dq=False,
                ),
                Lane(
                    backups=[Time("127.40"), Time("127.45"), Time("127.38")],
                    splits=[
                        [Time("32.52")],
                        [Time("78.25")],
                        [Time("95.16")],
                        [Time("127.18")],
                    ],
                    is_dq=True,
                ),
                Lane(
                    backups=[None, Time("124.67"), None],
                    splits=[
                        [Time("27.46")],
                        [Time("75.20")],
                        [Time("98.54")],
                        [Time("124.58")],
                    ],
                    is_dq=False,
                ),
                *_unused(2, num_splits=4),
            ],
        )
        filename = Generic().filename(actual) or ""
        assert filename == "005-021-03F0002.gen"
        gen = Generic().read(os.path.join(_testdata_dir, filename))
        check_heat_is_similar(actual, gen)
        gen_rt = round_trip(actual, Generic(), tmp_path)
        check_heat_is_similar(actual, gen_rt)


class TestGenericSamples:
    """Tests for Generic using sample data files."""

    def test_024_0008(self, tmp_path: pathlib.Path) -> None:
        """Test parsing the sample file."""
        actual = Heat(
            event="102",
            heat=6,
            meet_id="24",
            race=8,
            round="F",
            description="Mixed 200 Meter Freestyle Finals",
            lanes=[
                *_unused(1, num_splits=2),
                Lane(
                    splits=[
                        [parse_time("1:19.33")],
                        [parse_time("2:45.05")],
                    ],
                    backups=[
                        parse_time("2:45.13"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:12.48")],
                        [parse_time("2:34.96")],
                    ],
                    backups=[
                        parse_time("2:35.05"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:14.08")],
                        [parse_time("2:40.15")],
                    ],
                    backups=[
                        parse_time("2:40.15"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:15.57")],
                        [parse_time("2:37.88")],
                    ],
                    backups=[
                        parse_time("2:37.98"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                *_unused(2, num_splits=2),
                Lane(
                    splits=[
                        [parse_time("1:19.18")],
                        [parse_time("2:48.42")],
                    ],
                    backups=[
                        parse_time("2:48.44"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:18.49")],
                        [parse_time("2:43.47")],
                    ],
                    backups=[
                        parse_time("2:43.47"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:24.29")],
                        [parse_time("2:54.78")],
                    ],
                    backups=[
                        parse_time("2:54.78"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
            ],
        )
        filename = Generic().filename(actual) or ""
        assert filename == "024-102-06F0008.gen"
        gen = Generic().read(os.path.join(_testdata_dir, filename))
        check_heat_is_similar(actual, gen)
        gen_rt = round_trip(actual, Generic(), tmp_path)
        check_heat_is_similar(actual, gen_rt)

    def test_024_0019(self, tmp_path: pathlib.Path) -> None:
        """Test parsing the sample file."""
        actual = Heat(
            event="103",
            heat=1,
            meet_id="24",
            race=19,
            round="F",
            description="Mixed 100 Meter Backstroke Finals",
            lanes=[
                Lane(
                    splits=[
                        [parse_time("1:12.88")],
                    ],
                    backups=[
                        parse_time("1:12.98"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:13.06")],
                    ],
                    backups=[
                        None,
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:06.68")],
                    ],
                    backups=[
                        parse_time("1:06.68"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:06.44")],
                    ],
                    backups=[
                        parse_time("1:06.44"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:02.55")],
                    ],
                    backups=[
                        parse_time("1:02.56"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:04.39")],
                    ],
                    backups=[
                        parse_time("1:04.54"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:08.85")],
                    ],
                    backups=[
                        parse_time("1:08.77"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:08.79")],
                    ],
                    backups=[
                        parse_time("1:09.00"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:11.40")],
                    ],
                    backups=[
                        parse_time("1:11.54"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
                Lane(
                    splits=[
                        [parse_time("1:12.25")],
                    ],
                    backups=[
                        parse_time("1:12.34"),
                        None,
                        None,
                    ],
                    is_dq=False,
                ),
            ],
        )
        filename = Generic().filename(actual) or ""
        assert filename == "024-103-01F0019.gen"
        gen = Generic().read(os.path.join(_testdata_dir, filename))
        check_heat_is_similar(actual, gen)
        gen_rt = round_trip(actual, Generic(), tmp_path)
        check_heat_is_similar(actual, gen_rt)
