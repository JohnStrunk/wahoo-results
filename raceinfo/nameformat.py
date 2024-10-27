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

"""Functions for (re)-formatting names"""

import re
from enum import Enum, auto, unique
from typing import List


@unique
class NameMode(Enum):
    """Formatting options for swimmer names"""

    NONE = auto()
    """Verbatim as in the start list file"""
    FIRST = auto()
    """Format name as: First"""
    FIRST_LAST = auto()
    """Format name as: First Last"""
    FIRST_LASTINITIAL = auto()
    """Format name as: First L"""
    LAST_FIRST = auto()
    """Format name as: Last, First"""
    LAST_FIRSTINITIAL = auto()
    """Format name as: Last, F"""
    LAST = auto()
    """Format name as: Last"""


def arrange_name(how: NameMode, name: str) -> str:  # noqa: PLR0911
    """
    Change the format of a name from a start list.

    >>> arrange_name(NameMode.NONE, "Last, First M       ")
    'Last, First M'
    >>> arrange_name(NameMode.LAST_FIRST, "Last, First M       ")
    'Last, First'
    >>> arrange_name(NameMode.LAST_FIRSTINITIAL, "Last, First M       ")
    'Last, F'
    >>> arrange_name(NameMode.FIRST, "Last, First M       ")
    'First'
    >>> arrange_name(NameMode.FIRST_LAST, "Last, First M       ")
    'First Last'
    >>> arrange_name(NameMode.FIRST_LASTINITIAL, "Last, First M       ")
    'First L'
    >>> arrange_name(NameMode.LAST, "Last, First M       ")
    'Last'
    >>> arrange_name(NameMode.NONE, "Last, First")
    'Last, First'
    >>> arrange_name(NameMode.LAST_FIRST, "Last, First         ")
    'Last, First'
    >>> arrange_name(NameMode.FIRST_LAST, "Last, First         ")
    'First Last'
    >>> arrange_name(NameMode.LAST, "Last, First         ")
    'Last'
    """
    # This regex match is terribly ugly... here's how it works:
    # - Match groups are named via (?P<name>...)
    # - Last name is required to be present. The end of the last name is
    # demarcated by a comma
    # - The separation between Last and First is a comma and 1 or more space
    # characters. The First name portion goes until the next whitespace
    # character, if any.
    # - The middle (initial) is any remaining non-whitespace in the name
    # - The CTS start list names are placed into a 20-character field, so we
    # need to be able to properly parse w/ ws at the end (or not).
    match = re.match(
        r"^(?P<l>(?P<li>[^,])[^,]*)(,\s+(?P<f>(?P<fi>\w)\w*)(\s+(?P<m>\w+))?)?", name
    )
    if not match:
        return name.strip()
    if how == NameMode.FIRST:
        return f"{match.group('f')}"
    if how == NameMode.FIRST_LAST:
        return f"{match.group('f')} {match.group('l')}"
    if how == NameMode.FIRST_LASTINITIAL:
        return f"{match.group('f')} {match.group('li')}"
    if how == NameMode.LAST_FIRST:
        return f"{match.group('l')}, {match.group('f')}"
    if how == NameMode.LAST_FIRSTINITIAL:
        return f"{match.group('l')}, {match.group('fi')}"
    if how == NameMode.LAST:
        return f"{match.group('l')}"
    # default is NameMode.NONE
    return name.strip()


def format_name(how: NameMode, name: str) -> List[str]:
    """
    Returns a name formatted according to "how", along w/ shorter variants in
    case the requested format doesn't fit in the alloted space on the
    scoreboard.

    >>> format_name(NameMode.NONE, "Last, First M")
    ['Last, First M', 'Last, First', 'Last, F', 'Last', 'Las', 'La', 'L', '']
    >>> format_name(NameMode.LAST_FIRST, "Last, First M")
    ['Last, First', 'Last, F', 'Last', 'Las', 'La', 'L', '']
    >>> format_name(NameMode.FIRST_LAST, "Last, First M")
    ['First Last', 'First L', 'First', 'Firs', 'Fir', 'Fi', 'F', '']
    """
    variants = []
    if how == NameMode.FIRST_LAST:
        variants = format_name(NameMode.FIRST_LASTINITIAL, name)
    if how == NameMode.FIRST_LASTINITIAL:
        variants = format_name(NameMode.FIRST, name)
    if how == NameMode.FIRST:
        variants = _shorter_strings(arrange_name(how, name))
    if how == NameMode.NONE:
        variants = format_name(NameMode.LAST_FIRST, name)
    if how == NameMode.LAST_FIRST:
        variants = format_name(NameMode.LAST_FIRSTINITIAL, name)
    if how == NameMode.LAST_FIRSTINITIAL:
        variants = format_name(NameMode.LAST, name)
    if how == NameMode.LAST:
        variants = _shorter_strings(arrange_name(how, name))
    return [arrange_name(how, name), *variants]


def _shorter_strings(string: str) -> List[str]:
    """
    >>> _shorter_strings("foobar")
    ['fooba', 'foob', 'foo', 'fo', 'f', '']
    """
    if len(string) > 0:
        shortened = string[:-1]
        return [shortened, *_shorter_strings(shortened)]
    return []
