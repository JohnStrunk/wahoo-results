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

"""
A scoreboard template for previews and theming
"""

from raceinfo import HeatData, NumericTime, standard_resolver


def get_template() -> HeatData:
    """
    Returns template data to create a scoreboard mockup

    >>> from scoreboard import format_time
    >>> from raceinfo import NO_SHOW, INCONSISTENT
    >>> t = get_template()
    >>> t.event
    '999'
    >>> isinstance(t.lane(1).time(), NumericTime)
    True
    >>> format_time(t.lane(1).time())
    '99:50.99'
    >>> t.lane(2).time() == NO_SHOW
    True
    >>> t.lane(3).time() == INCONSISTENT
    True
    >>> t.lane(3).name
    'Brady, June A'
    >>> t.lane(3).team
    'TEAM'
    """
    basetime = NumericTime("59.99") + NumericTime("60") * NumericTime("99")
    lt = [basetime + i - 10 for i in range(1, 11)]
    return HeatData(
        event="999",
        heat=99,
        description="GIRLS 15&O 200 MEDLEY RELAY",
        lanes=[
            HeatData.Lane(
                name="Hutchins, Lorraine O",
                team="TEAM",
                times=[lt[0], lt[0], lt[0]],
            ),
            HeatData.Lane(name="English, Cheryl M", team="TEAM", times=[]),
            HeatData.Lane(name="Brady, June A", team="TEAM", times=[NumericTime(1)]),
            HeatData.Lane(
                name="Sloan, Michelle T", team="TEAM", times=[lt[3], lt[3], lt[3]]
            ),
            HeatData.Lane(
                name="Downing, Doreen S", team="TEAM", times=[lt[4], lt[4], lt[4]]
            ),
            HeatData.Lane(
                name="Collier, Julie G", team="TEAM", times=[lt[5], lt[5], lt[5]]
            ),
            HeatData.Lane(
                name="Chase, Constance H", team="TEAM", times=[lt[6], lt[6], lt[6]]
            ),
            HeatData.Lane(
                name="Clark, Leslie J", team="TEAM", times=[lt[7], lt[7], lt[7]]
            ),
            HeatData.Lane(
                name="Jensen, Kelli N", team="TEAM", times=[lt[8], lt[8], lt[8]]
            ),
            HeatData.Lane(
                name="Parsons, Marsha L", team="TEAM", times=[lt[9], lt[9], lt[9]]
            ),
        ],
        time_resolver=standard_resolver(2, NumericTime(0.30)),
    )
