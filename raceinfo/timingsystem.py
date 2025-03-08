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

"""Base class for all timing systems."""

import io
from abc import ABC, abstractmethod

from .time import Heat


class TimingSystem(ABC):
    """Define the interface to timing system data files.

    This class defines the interface for accessing timing system data files. It
    provides methods for reading and writing data, as well as a method to
    describe the filename patterns that are used by the timing system.

    For reading timing data, subclasses should, at a minimum, implement the
    `decode` method to parse the data into a `Heat` object. The `read` method
    may also be overridden, paritcularly if properties of the file, such as its
    name, are needed to fully build the `Heat` object.

    For writing timing data, subclasses should implement the `encode` method and
    optionally the `write` method.
    """

    @abstractmethod
    def read(self, filename: str) -> Heat:
        """Create a Heat from a timing system's data file.

        :param filename: The name of the file to read
        :returns: A Heat object that represents the parsed data
        :raises FileNotFoundError: If the file does not exist
        :raises NotImplementedError: If the `decode()` method is not implemented
        :raises ValueError: If the data is not in the expected format
        """
        with open(filename, "r", encoding="cp1252") as file:
            return self.decode(file)

    @abstractmethod
    def decode(self, stream: io.TextIOBase) -> Heat:
        """Create a Heat from a text stream containing timing system data.

        :param stream: A file-like object that contains the DO4 data
        :returns: A Heat object that represents the parsed data
        :raises ValueError: If the data is not in the expected format
        :raises NotImplementedError: If the method is not implemented
        """
        raise NotImplementedError("decode() is not implemented")

    @abstractmethod
    def write(self, filename: str, heat: Heat) -> None:
        """Write the timing system data file.

        :param filename: The name of the file to write
        :param heat: The Heat object to write
        :raises NotImplementedError: If the `encode()` method is not implemented
        """
        data = self.encode(heat)
        with open(filename, "w", encoding="cp1252") as file:
            file.write(data)

    @abstractmethod
    def encode(self, heat: Heat) -> str:
        """Export the timing system data file.

        :param heat: The Heat object to write
        :returns: The data to write to the file
        :raises NotImplementedError: If the method is not implemented
        """
        raise NotImplementedError("encode() is not implemented")

    @abstractmethod
    def filename(self, heat: Heat) -> str | None:
        """Return the filename for the given Heat.

        :param heat: The Heat object to get the filename for
        :returns: The filename for the Heat object or None if a filename cannot
            be determined from the Heat data
        """
        raise NotImplementedError("filename() is not implemented")

    @property
    @abstractmethod
    def patterns(self) -> list[str]:
        """A list of file name patterns for this timing system."""
        raise NotImplementedError("patterns is not implemented")
