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

"""Functions for manipulating Startlists"""

from .heatdata import HeatData

StartList = list[HeatData]
"""
A StartList is a list of HeatData objects, one for each heat in an event.

They should:

- All have the same event number
- Be in order by heat number
"""


def is_valid(startlist: StartList) -> bool:
    """
    Check if a StartList is valid

    Parameters:
        - startlist: The StartList to check

    Returns:
        True if the StartList is valid, False otherwise

    Example:
        if not is_valid(startlist):
            ...
    """
    if not startlist:
        return False
    event = startlist[0].event
    heatnum = 0
    for heat in startlist:
        if heat.event != event:
            return False
        if heat.heat <= heatnum:
            return False
        heatnum = heat.heat
    return True


def startlists_to_csv(startlists: list[StartList]) -> list[str]:
    """
    Convert a list of StartLists to a list of CSV strings

    Parameters:
        - startlists: The list of StartLists to convert

    Returns:
        A list of CSV strings, one for each StartList

    Example:
        csv_strings = startlists_to_csv(startlists)
    """
    csv: list[str] = []
    for slist in startlists:
        if not is_valid(slist):
            continue
        event = slist[0].event
        name = slist[0].description
        heats = len(slist)
        csv.append(f"{event},{name},{heats},1,A\n")
    return csv