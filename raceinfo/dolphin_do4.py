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

"""Colorado Dolphin timing system.

https://coloradotime.com/products/dolphin-wireless-stopwatch-swim-timing
"""

import io
import os
import re
from datetime import datetime

from .time import ZERO_TIME, Heat, Lane, Time
from .timingsystem import TimingSystem


class DolphinDo4(TimingSystem):
    """Colorado Dolphin Wireless Stopwatch - DO4 format."""

    def read(self, filename: str) -> Heat:  # noqa: D102
        meet_id = "???"
        race_number = 1
        # do4 files are named like "001-002-003A-0004.do4"
        # 001 is the meet id, 002 is the event number, 003 is the heat number, 0004
        # is the race number
        # We're only parsing the items from the file name that we can't get from
        # the file contents.
        matcher = re.match(r"^(\d+)-\d+-\d+\w-(\d+)\.", os.path.basename(filename))
        if matcher is not None:
            meet_id = matcher.group(1)
            race_number = int(matcher.group(2))
        stinfo = os.stat(filename)
        mtime = datetime.fromtimestamp(stinfo.st_mtime)
        with open(filename, "r", encoding="cp1252") as file:
            data = self.decode(file)
        data.meet_id = meet_id
        data.race = race_number
        data.time_recorded = mtime
        return data

    def decode(self, stream: io.TextIOBase) -> Heat:  # noqa: D102
        header = stream.readline()
        match = re.match(r"^(\d*);(\d+);\w+;\w+$", header)
        if not match:
            raise ValueError("Unable to parse header")
        event = match.group(1)
        heat = int(match.group(2))

        lines = stream.readlines()
        if len(lines) != 11:  # noqa: PLR2004
            raise ValueError("Invalid number of lines in file")
        lanes: list[Lane] = []
        for lane in range(10):
            match = re.match(r"^Lane\d+;([\d\.]*);([\d\.]*);([\d\.]*)$", lines[lane])
            if not match:
                raise ValueError("Unable to parse times")
            lane_times: list[Time | None] = []
            for index in range(1, 4):
                time: Time | None = None
                match_txt = match.group(index)
                if match_txt != "":
                    time = Time(match_txt)
                    if time == ZERO_TIME:
                        time = None
                lane_times.append(time)
            lanes.append(Lane(backups=lane_times))
        return Heat(event=event, heat=heat, lanes=lanes)

    def encode(self, heat: Heat) -> str:  # noqa: D102
        raise NotImplementedError("encode() is not implemented")

    def write(self, filename: str, heat: Heat) -> None:  # noqa: D102
        raise NotImplementedError("write() is not implemented")

    def filename(self, heat: Heat) -> str | None:  # noqa: D102
        round = heat.round or "A"
        try:
            # When no event is specified, the event number is 0 in the filename.
            event = int(heat.event or 0)
            return f"{int(heat.meet_id):03}-{event:03}-{int(heat.heat):03}{round}-{int(heat.race):04}.do4"  # type: ignore
        except TypeError:  # Tried to convert None to int
            return None
        except ValueError:  # Tried to convert a non-numeric string to int
            return None

    @property
    def patterns(self) -> list[str]:  # noqa: D102
        return ["*.do4"]
