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

"""Base class for all meet program parsers."""

import abc

from .time import Heat

type FullProgram = dict[str, list[Heat]]
"""Describe the full meet program.

The meet program is a dictionary where the keys are the event numbers, and the
values are a (sorted) list of Heats for that event.
"""


class EventProcessor(abc.ABC):
    """Define the interface to meet program data files."""

    def find(self, directory: str, event_num: str, heat_num: int) -> Heat | None:
        """Find a meet program file and return the heat data.

        :param directory: The directory to search
        :param event_num: The event number (e.g., "102S")
        :param heat_num: The heat number
        :returns: A Heat object that represents the parsed data or None if the
            requested heat is not found
        :raises ValueError: If the data is not in the expected format
        """
        raise NotImplementedError("find() is not implemented")

    def full_program(self, directory: str) -> FullProgram:
        """Return the full meet program.

        The meet program is returned as a dictionary where the keys are the
        event numbers, and the values are a (sorted) list of Heats for that
        event.

        :param directory: The directory to search
        :returns: A dictionary of event numbers to lists of Heat objects
        :raises ValueError: If the data is not in the expected format
        """
        raise NotImplementedError("full_program() is not implemented")

    def write(self, path: str, program: FullProgram) -> None:
        """Write a meet program to a file or directory.

        :param path: The name of the file or directory to write to
        :param program: The full meet program to write
        :raises OSError: If there is a problem writing the file
        """
        raise NotImplementedError("write() is not implemented")

    @property
    def patterns(self) -> list[str]:
        """Return the filename pattern for meet program files."""
        raise NotImplementedError("patterns is not implemented")
