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

import copy
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
        # Header is event, heat, num_splits, round
        match = re.match(r"^(\d*);(\d+);(\d+);(\w+)$", header)
        if not match:
            raise ValueError("Unable to parse header")
        event = str(match.group(1))
        heat = int(match.group(2))
        num_splits = int(match.group(3))
        round_txt = str(match.group(4))
        round: Heat.Round
        if round_txt == "Prelim":
            round = "P"
        elif round_txt == "Final":
            round = "F"
        else:
            round = "A"

        lines = stream.readlines()
        # The number of lines in the file (w/o header) should be 1 + (num_splits * 10)
        if len(lines) != (1 + (num_splits * 10)):
            raise ValueError("Invalid number of lines in file")
        lanes: list[Lane] = [Lane(splits=[]) for _ in range(10)]
        min_lane = 1
        for line in lines[: len(lines) - 1]:  # skip last line (it's the checksum)
            match = re.match(r"^Lane(\d+);([\d\.]*);([\d\.]*);([\d\.]*)$", line)
            if not match:
                raise ValueError("Unable to parse times")
            lane_num = int(match.group(1))
            min_lane = min(min_lane, lane_num)
            lane_times: list[Time | None] = []
            for index in range(2, 5):
                time: Time | None = None
                match_txt = match.group(index)
                if match_txt != "":
                    time = Time(match_txt)
                    if time == ZERO_TIME:
                        time = None
                lane_times.append(time)
            lanes[lane_num - min_lane].backups = lane_times
            # We know the splits is a list from when it was initialized with Lane(splits=[]).
            lanes[lane_num - min_lane].splits.append(copy.deepcopy(lane_times))  # type: ignore
        if min_lane == 0:
            numbering: Heat.NumberingMode = "0-9"
        else:
            numbering = "1-10"
        return Heat(
            event=event, heat=heat, lanes=lanes, round=round, numbering=numbering
        )

    def encode(self, heat: Heat) -> str:  # noqa: D102
        start_lane = 1 if heat.numbering == "1-10" else 0
        # Find the number of splits in the heat as the lane with the most splits.
        num_splits = max(
            len(heat.lane(i).splits or [1]) for i in range(start_lane, start_lane + 10)
        )
        # The header is event, heat, num_splits, round
        round_txt: str
        if heat.round == "P":
            round_txt = "Prelim"
        elif heat.round == "F":
            round_txt = "Final"
        else:
            round_txt = "A"
        header = f"{heat.event or ''};{heat.heat or 1};{num_splits};{round_txt}"
        lines = [header]
        for lane in range(start_lane, start_lane + 10):
            splits = heat.lane(lane).splits or [[None, None, None]] * num_splits
            for group in splits:
                line = f"Lane{lane}"
                if group == [None, None, None]:
                    line += ";0;0;0"
                else:
                    for time in group:
                        if time is None:
                            line += ";"
                        else:
                            line += f";{time}"
                lines.append(line)
        # The last line is the checksum, and we don't know how to calculate it.
        lines.append("F" * 16)
        return "\n".join(lines)

    def write(self, filename: str, heat: Heat) -> None:  # noqa: D102
        super().write(filename, heat)

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
