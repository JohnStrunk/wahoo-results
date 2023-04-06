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

from datetime import datetime
from typing import List, Optional

from racetimes import RaceTimes, RawTime
from startlist import StartList


def get_template() -> RaceTimes:
    """
    Returns template data to create a scoreboard mockup

    >>> from scoreboard import format_time
    >>> t = get_template()
    >>> t.event
    999
    >>> t.final_time(1).is_valid
    True
    >>> format_time(t.final_time(1).value)
    '99:50.99'
    >>> t.final_time(2).is_valid
    False
    >>> t.final_time(3).is_valid
    False
    >>> t.name(3)
    'BRADY, JUNE A'
    >>> t.team(3)
    'TEAM'
    """
    race = _TemplateRace(2, RawTime("0.30"))
    race.set_names(_TemplateStartList())
    return race


class _TemplateRace(RaceTimes):
    @property
    def event(self) -> int:
        return 999

    @property
    def heat(self) -> int:
        return 99

    def raw_times(self, lane: int) -> List[Optional[RawTime]]:
        if lane == 2:
            return [None, None, None]  # no-show
        if lane == 3:
            return [RawTime("1"), None, None]  # Too few times -> invalid
        time = RawTime("59.99") + RawTime("60") * RawTime("99")
        time = time + lane - 10
        return [time, time, time]

    @property
    def time_recorded(self) -> datetime:
        return datetime.now()

    @property
    def meet_id(self) -> str:
        return "000"


class _TemplateStartList(StartList):
    @property
    def event_name(self) -> str:
        return "GIRLS 15&O 200 MEDLEY RELAY"

    def name(self, _heat: int, lane: int) -> str:
        # https://randomwordgenerator.com/name.php
        names = (
            "Hutchins, Lorraine O",
            "English, Cheryl M",
            "Brady, June A",
            "Sloan, Michelle T",
            "Downing, Doreen S",
            "Collier, Julie G",
            "Chase, Constance H",
            "Clark, Leslie J",
            "Jensen, Kelli N",
            "Parsons, Marsha L",
        )
        return names[lane - 1].upper()

    def team(self, _heat: int, _lane: int) -> str:
        return "TEAM"
