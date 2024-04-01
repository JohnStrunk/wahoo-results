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

"""Functions to read results from a Colorado Dolphin timing system"""


import io
import os
import re
from datetime import datetime
from typing import List

from heatdata import HeatData
from racetime import NumericTime


def parse_do4_file(file_path: str) -> HeatData:
    """
    Parse a DO4 file from a Colorado Dolphin timing system

    Args:
        file_path: The path to the DO4 file

    Returns:
        A RaceResult object that represents the parsed data

    Raises:
        ValueError: If the data is not in the expected format
    """

    meet_id = "???"
    race_number = 1
    matcher = re.match(r"^(\d+)-\d+-\d+\w-(\d+)\.", os.path.basename(file_path))
    if matcher is not None:
        meet_id = matcher.group(1)
        race_number = int(matcher.group(2))
    stinfo = os.stat(file_path)
    mtime = datetime.fromtimestamp(stinfo.st_mtime)
    with open(file_path, "r", encoding="cp1252") as file:
        data = parse_do4(file)
    data.meet_id = meet_id
    data.race = race_number
    data.time_recorded = mtime
    return data


def parse_do4(stream: io.TextIOBase) -> HeatData:
    """
    Parse a DO4 file from a Colorado Dolphin timing system

    Args:
        stream: A file-like object that contains the DO4 data
        when: The time the race was completed
        meet_id: The ID/number of the meet

    Returns:
        A RaceResult object that represents the parsed data

    Raises:
        ValueError: If the data is not in the expected format
    """
    header = stream.readline()
    match = re.match(r"^(\d+);(\d+);\w+;\w+$", header)
    if not match:
        raise ValueError("Unable to parse header")
    event = match.group(1)
    heat = int(match.group(2))

    lines = stream.readlines()
    if len(lines) != 11:
        raise ValueError("Invalid number of lines in file")
    lanes: List[HeatData.Lane] = []
    for lane in range(10):
        match = re.match(r"^Lane\d+;([\d\.]*);([\d\.]*);([\d\.]*)$", lines[lane])
        if not match:
            raise ValueError("Unable to parse times")
        lane_times: List[NumericTime] = []
        for index in range(1, 4):
            match_txt = match.group(index)
            time = NumericTime("0")
            if match_txt != "":
                time = max(NumericTime(match_txt), time)
            lane_times.append(time)
        lanes.append(HeatData.Lane(times=lane_times))
    return HeatData(event=event, heat=heat, lanes=lanes)
