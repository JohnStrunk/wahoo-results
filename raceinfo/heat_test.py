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

"""Tests for Heat."""

import copy
from datetime import datetime
from typing import Any

import pytest

from .lane_test import check_lane_is_similar
from .time import Heat, Lane, Time


def check_heat_is_similar(heat1: Heat, heat2: Heat, do_throw: bool = False) -> None:
    """
    Check if this heat is similar to another heat.

    Similarity is defined as having the same values for all fields where a
    field is not None. If a field is None, it is ignored in the comparison.

    Note: This method is mainly intended for testing purposes.

    :param other: The other heat to compare to
    :returns: True if the heats are similar, False otherwise
    """
    __tracebackhide__ = True

    def fail(field: str, val1: Any, val2: Any) -> None:
        __tracebackhide__ = True
        msg = f"Heats are not similar - {field} differs: {val1} vs. {val2}"
        if do_throw:
            raise ValueError(msg)
        else:
            pytest.fail(msg)

    # Compare the simple fields
    for var in [
        "event",
        "heat",
        "description",
        "meet_id",
        "race",
        "time_recorded",
        "numbering",
        "round",
    ]:
        if (
            getattr(heat1, var) is not None
            and getattr(heat2, var) is not None
            and getattr(heat2, var) != getattr(heat1, var)
        ):
            fail(var, getattr(heat1, var), getattr(heat2, var))
    # Compare the lanes
    for i in range(10):
        # We're directly indexing the lanes here so that we can compare the
        # lanes regardless of the lane numbering scheme.
        check_lane_is_similar(heat1._lanes[i], heat2._lanes[i], do_throw)  # type: ignore


class TestHeatValidation:
    """Tests for validation of Heat."""

    def test_negative_heat(self):
        """Invalid heat raises ValueError."""
        with pytest.raises(ValueError):
            Heat(heat=-1)

    def test_negative_race(self):
        """Invalid race raises ValueError."""
        with pytest.raises(ValueError):
            Heat(race=-1)

    def test_too_many_lanes(self):
        """Invalid lanes raise ValueError."""
        lanes = [Lane() for _ in range(11)]
        with pytest.raises(ValueError):
            Heat(lanes=lanes)

    def test_event(self):
        """Event names are upper case."""
        assert Heat(event="1").event == "1"
        assert Heat(event="1s").event == "1S"
        assert Heat(event="1Z").event == "1Z"
        assert Heat(event="aBc").event == "ABC"


class TestHeat:
    """Tests for Heat."""

    def test_get_lane(self):
        """Test the string representation of a Heat object."""
        heat = Heat(lanes=[Lane(name="one"), Lane(name="two")])
        assert heat.lane(1).name == "one"
        assert heat.lane(2).name == "two"
        with pytest.raises(ValueError):
            heat.lane(0)
        with pytest.raises(ValueError):
            heat.lane(87)

    def test_place(self):
        """Test the place method."""
        heat = Heat(
            lanes=[
                Lane(final_time=Time(150)),
                Lane(final_time=Time(200)),
                Lane(final_time=Time(150)),
                Lane(final_time=None),
                Lane(final_time=Time(50), is_dq=True),
                Lane(final_time=Time(100)),
            ]
        )
        assert heat.place(1) == 2  # noqa: PLR2004
        assert heat.place(2) == 4  # noqa: PLR2004
        assert heat.place(3) == 2  # noqa: PLR2004
        assert heat.place(4) is None
        assert heat.place(5) is None
        assert heat.place(6) == 1

    def test_names(self):
        """Test the has_names method."""
        heat = Heat(lanes=[Lane(name="one"), Lane(name="two")])
        assert heat.has_names() is True
        heat = Heat(lanes=[Lane(), Lane()])
        assert heat.has_names() is False
        heat = Heat(lanes=[Lane(), Lane(name="two")])
        assert heat.has_names() is True

    def test_resolve_times(self):
        """Test the resolve_times method."""
        heat = Heat(
            lanes=[
                Lane(primary=Time(1.0)),
                Lane(primary=Time(4.0)),
            ]
        )

        def assign_final_time(lane: Lane):
            lane.final_time = lane.primary

        heat.resolve_times(assign_final_time)
        assert heat.lane(1).final_time == Time(1.0)
        assert heat.lane(2).final_time == Time(4.0)
        assert heat.lane(3).final_time is None

    def test_merge(self):
        """Test the merge method."""
        heat1 = Heat(
            event="1",
            heat=1,
            description="d1",
            meet_id="id-one",
            race=11,
            time_recorded=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            lanes=[Lane(name="one", primary=Time(100.00))],
        )
        heat2 = Heat(
            event="2",
            heat=2,
            description="d2",
            meet_id="id-two",
            race=12,
            time_recorded=datetime.strptime("2025-02-02", "%Y-%m-%d"),
            lanes=[Lane(name="two", primary=Time(200.00))],
        )
        m1 = copy.deepcopy(heat1)
        m1.merge(heat2)
        assert m1.event == "2"
        assert m1.heat == 2  # noqa: PLR2004
        assert m1.description == "d2"
        assert m1.meet_id == "id-one"
        assert m1.race == 11  # noqa: PLR2004
        assert m1.time_recorded == datetime.strptime("2025-01-01", "%Y-%m-%d")
        assert m1.lane(1).name == "two"
        assert m1.lane(1).primary == Time(100.00)

        m2 = copy.deepcopy(heat1)
        m2.merge(results_from=heat2)
        assert m2.event == "1"
        assert m2.heat == 1
        assert m2.description == "d1"
        assert m2.meet_id == "id-two"
        assert m2.race == 12  # noqa: PLR2004
        assert m2.time_recorded == datetime.strptime("2025-02-02", "%Y-%m-%d")
        assert m2.lane(1).name == "one"
        assert m2.lane(1).primary == Time(200.00)

    def test_sorting(self):
        """Test sorting of Heat objects."""
        e1h1 = Heat(event="1", heat=1)
        e1h2 = Heat(event="1", heat=2)
        e2h1 = Heat(event="2", heat=1)
        e2h2 = Heat(event="2", heat=2)
        assert e1h1 < e1h2
        assert e1h2 > e1h1
        assert e1h1 < e2h1
        assert e1h2 < e2h1
        assert e1h2 < e2h2
        e6a = Heat(event="6a", heat=1)
        e11a = Heat(event="11A", heat=1)
        assert e6a < e11a
        assert e11a > e6a
        habc = Heat(event="ABC", heat=1)
        assert e6a < habc
        assert habc > e6a
        e6b = Heat(event="6b", heat=1)
        assert e6a < e6b
        assert e6b > e6a

    def test_similarity(self):
        """Test similarity of Heat objects."""
        heat1 = Heat(
            event="1",
            heat=1,
            description="d1",
            meet_id="id-one",
            lanes=[
                Lane(name="one", primary=Time(100.00)),
                Lane(name="two", primary=Time(200.00)),
            ],
        )
        # Identical is similar
        heat2 = copy.deepcopy(heat1)
        check_heat_is_similar(heat1, heat2)
        # Different heats are not similar
        heat2.heat = 2
        with pytest.raises(ValueError):
            check_heat_is_similar(heat1, heat2, do_throw=True)
        # None values are ignored during comparison
        heat2.heat = None
        check_heat_is_similar(heat1, heat2)
        heat2.lane(1).primary = None
        check_heat_is_similar(heat1, heat2)
        # Different lanes are not similar
        heat2.lane(1).primary = Time(999.00)
        with pytest.raises(ValueError):
            check_heat_is_similar(heat1, heat2, do_throw=True)

    def test_numbering(self):
        """Test lane numbering."""
        heat = Heat(
            lanes=[
                Lane(name="first"),
                Lane(name="second"),
            ]
        )
        # Default lane numbering is 1-10
        assert heat.lane(1).name == "first"
        assert heat.lane(2).name == "second"
        with pytest.raises(ValueError):
            heat.lane(0)
        with pytest.raises(ValueError):
            heat.lane(11)
        heat.numbering = "0-9"
        assert heat.lane(0).name == "first"
        assert heat.lane(1).name == "second"
        with pytest.raises(ValueError):
            heat.lane(-1)
        with pytest.raises(ValueError):
            heat.lane(10)
        heat.numbering = "1-10"
        assert heat.lane(1).name == "first"
        assert heat.lane(2).name == "second"
        heat.numbering = "unsupported-scheme"  # type: ignore
        with pytest.raises(ValueError):
            heat.lane(5)
