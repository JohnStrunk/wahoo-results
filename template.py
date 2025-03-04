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

"""A scoreboard template for previews and theming."""

from raceinfo import Heat, Lane, Time, standard_resolver
from raceinfo.time import MIN_VALID_TIME


def get_template() -> Heat:
    """
    Return template data to create a scoreboard mockup.

    >>> from scoreboard import format_time
    >>> t = get_template()
    >>> t.event
    '999'
    >>> t.lane(1).final_time
    Decimal('5990.99')
    >>> format_time(t.lane(1).final_time)
    '99:50.99'
    >>> t.lane(2).is_noshow
    True
    >>> t.lane(3).final_time is None
    True
    >>> t.lane(3).name
    'Brady, June A'
    >>> t.lane(3).team
    'TEAM'
    """
    basetime = Time("59.99") + Time("60") * Time("99")
    lt = [basetime + i - 10 for i in range(1, 11)]
    heat = Heat(
        event="999",
        heat=99,
        description="GIRLS 15&O 200 MEDLEY RELAY",
        lanes=[
            Lane(
                name="Hutchins, Lorraine O",
                team="TEAM",
                primary=lt[0],
                backups=[lt[0]],
            ),
            Lane(name="English, Cheryl M", team="TEAM"),
            Lane(name="Brady, June A", team="TEAM", backups=[MIN_VALID_TIME]),
            Lane(name="Sloan, Michelle T", team="TEAM", primary=lt[3], backups=[lt[3]]),
            Lane(name="Downing, Doreen S", team="TEAM", primary=lt[4], backups=[lt[4]]),
            Lane(name="Collier, Julie G", team="TEAM", primary=lt[5], backups=[lt[5]]),
            Lane(
                name="Chase, Constance H", team="TEAM", primary=lt[6], backups=[lt[6]]
            ),
            Lane(name="Clark, Leslie J", team="TEAM", primary=lt[7], backups=[lt[7]]),
            Lane(name="Jensen, Kelli N", team="TEAM", primary=lt[8], backups=[lt[8]]),
            Lane(name="Parsons, Marsha L", team="TEAM", primary=lt[9], backups=[lt[9]]),
        ],
    )
    resolver = standard_resolver(2, Time("0.30"))
    heat.resolve_times(resolver)
    return heat
