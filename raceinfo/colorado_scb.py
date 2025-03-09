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

"""Functions to read CTS start list files."""

import io
import os
import re
from pathlib import PurePath

from .eventprocessor import EventProcessor, FullProgram
from .time import Heat, Lane


class ColoradoSCB(EventProcessor):
    """Read CTS start list files."""

    def find(self, directory: str, event_num: str, heat_num: int) -> Heat | None:  # noqa: D102
        # Note: The SCB format only supports numeric event numbers. We attempt
        # to convert the event_num str to an int. In the case of an event like
        # "1Z", this will throw a ValueError, resulting in a return of None.
        filename = os.path.join(directory, f"E{int(event_num):03}.scb")
        if not os.path.exists(filename):
            return None
        try:
            with open(filename, "r", encoding="cp1252") as file:
                heats = self._parse_scb(file)
        except ValueError:
            return None
        if heat_num > len(heats):
            return None
        return heats[heat_num - 1]

    def full_program(self, directory: str) -> FullProgram:  # noqa: D102
        program: FullProgram = {}
        files = os.scandir(directory)
        for file in files:
            if any(PurePath(file).match(pattern) for pattern in self.patterns):
                try:
                    with open(file.path, "r", encoding="cp1252") as f:
                        heats = self._parse_scb(f)
                        if heats[0].event is not None:
                            program[heats[0].event] = heats
                except ValueError:  # Problem parsing the file
                    pass
                except FileNotFoundError:  # File was deleted after we read the dir
                    pass
        return program

    @property
    def patterns(self) -> list[str]:  # noqa: D102
        return ["*.scb"]

    def _parse_scb(self, stream: io.TextIOBase) -> list[Heat]:
        """Construct a StartList from a text stream.

        CTS start lists support:
        - Event number
        - Event description
        - Heat number
        - Swimmer name
        - Swimmer team

        :param stream: The text stream to read
        :returns: A list of Heat objects, one for each heat in the start list
        :raises ValueError: If the data is not in the expected format
        """
        # The first line is the event number and description
        # Ex: #3 MIXED 10&U 100 FREE RELAY
        header = stream.readline()
        match = re.match(r"^#(\w+)\s+(.*)$", header)
        if not match:
            raise ValueError("Unable to parse header")
        event = match.group(1)
        description = match.group(2)

        # The rest of the file is the data for the lanes for all the heats
        # The format always has 10 lines (lanes) per heat
        lines = stream.readlines()
        if len(lines) % 10:
            raise ValueError("Length is not a multiple of 10")
        num_heats = (len(lines)) // 10

        # Reverse the lines because we're going to pop() them later and we
        # want to read them in order.
        lines.reverse()

        heatlist: list[Heat] = []
        for h_index in range(num_heats):
            lanes: list[Lane] = []
            for _lane in range(10):
                line = lines.pop()
                # Each entry is fixed length:
                #  - Swimmer name: 20 char
                #  - Literal: "--"
                #  - Swimmer team: 16 char
                # Total line length: 38 char
                # Excess area is space-filled
                match = re.match(r"^(.{20})--(.{16})$", line)
                if not match:
                    raise ValueError(f"Unable to parse line: '{line}'")
                lanes.append(
                    Lane(name=match.group(1).strip(), team=match.group(2).strip())
                )
            heatlist.append(
                Heat(
                    description=description, event=event, heat=h_index + 1, lanes=lanes
                )
            )
        return heatlist
