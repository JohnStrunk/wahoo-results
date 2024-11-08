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
from typing import List

from .heatdata import HeatData
from .startlist import StartList


def parse_scb(stream: io.TextIOBase) -> StartList:
    """
    Construct a StartList from a text stream (file).

    :param stream: The text stream to read
    :returns: A list of HeatData objects, one for each heat in the start list
    :raises ValueError: If the data is not in the expected format

    Example usage::
    .. code-block:: python
        with open(filename, "r", encoding="cp1252") as file:
            try:
                heat_list = parse_scb(file)
            except ValueError as err:  # Parse error
                ...
    """
    header = stream.readline()
    match = re.match(r"^#(\w+)\s+(.*)$", header)
    if not match:
        raise ValueError("Unable to parse header")
    event = match.group(1)
    description = match.group(2)

    # The format always has 10 lines (lanes) per heat
    lines = stream.readlines()
    if len(lines) % 10:
        raise ValueError("Length is not a multiple of 10")
    num_heats = (len(lines)) // 10

    # Reverse the lines because we're going to pop() them later and we
    # want to read them in order.
    lines.reverse()

    heatlist: List[HeatData] = []
    for h_index in range(num_heats):
        lanes: List[HeatData.Lane] = []
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
                HeatData.Lane(name=match.group(1).strip(), team=match.group(2).strip())
            )
        heatlist.append(
            HeatData(
                description=description, event=event, heat=h_index + 1, lanes=lanes
            )
        )
    return heatlist


def parse_scb_file(file_path: str) -> StartList:
    """
    Read a CTS start list file.

    :param file_path: The path to the file to read
    :returns: A list of HeatData objects, one for each heat in the start list
    :raises ValueError: If the data is not in the expected format
    :raises FileNotFoundError: If the file does not exist
    """
    with open(file_path, "r", encoding="cp1252") as file:
        return parse_scb(file)


def load_all_scb(directory: str) -> List[StartList]:
    """Load all the start list .scb files from a directory.

    :param directory: The directory to scan for .scb files
    :returns: A list of StartList objects, one for each .scb file found
    """
    files = os.scandir(directory)
    startlists: List[StartList] = []
    for file in files:
        if file.name.endswith(".scb"):
            try:
                startlist = parse_scb_file(file.path)
                startlists.append(startlist)
            except ValueError:  # Problem parsing the file
                pass
            except FileNotFoundError:  # File was deleted after we read the dir
                pass
    startlists.sort(key=lambda x: x[0])
    return startlists
