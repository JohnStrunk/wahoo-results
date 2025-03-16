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

"""Generic file sharing format."""

import copy
import io
import os
import re
from datetime import datetime

from .time import Heat, Lane, Time, combine_times
from .timingsystem import TimingSystem


class Generic(TimingSystem):
    """Generic file sharing format."""

    def read(self, filename: str) -> Heat:  # noqa: D102
        meet_id = "001"
        race_number = 1
        # Generic files are named like "DDD-EEE-HHRNNNN.ge[2n]"
        # - DDD is the dataset number (meet_id)
        # - EEE is the event number (event_num), and for alphanumeric events, the
        #   letter replaces the dash before the heat number
        # - HH is the heat number
        # - R is the round (P, S, or F)
        # - NNNN is the race number
        # We're only parsing the items from the file name that we can't get from
        # the file contents.
        matcher = re.match(r"^(\d+)-\d+(\w|-)\d+\w(\d+)\.", os.path.basename(filename))
        if matcher is not None:
            meet_id = int(matcher.group(1))
            race_number = int(matcher.group(3))
        stinfo = os.stat(filename)
        mtime = datetime.fromtimestamp(stinfo.st_mtime)
        with open(filename, "r", encoding="cp1252") as file:
            data = self.decode(file)
        data.meet_id = str(meet_id)
        data.race = race_number
        data.time_recorded = mtime
        return data

    def decode(self, stream: io.TextIOBase) -> Heat:  # noqa: D102
        header = stream.readline()
        # Header is event;heat;num_splits;round;file_version;creator;creator_version
        match = re.match(r"^(\d+\w*);(\d+);(\d+);(\w);.*;.*;.*$", header)
        if not match:
            raise ValueError("Unable to parse header: " + header)
        event = str(match.group(1))
        heat = int(match.group(2))
        num_splits = int(match.group(3))
        round_txt = str(match.group(4))
        round: Heat.Round = round_txt if round_txt in ("P", "S", "A") else "F"

        lines = stream.readlines()
        # The number of lines in the file (w/o header) should be 12 since the
        # format supports 12 lanes.
        if len(lines) != 12:  # noqa: PLR2004
            raise ValueError("Invalid number of lines in file")
        lanes: list[Lane] = [Lane(splits=[]) for _ in range(10)]
        for i, line in enumerate(lines[:10]):  # we only use 10 lanes
            fields = line.split(";")
            if len(fields) != num_splits + 8:
                raise ValueError("Invalid number of fields in line: " + line)
            # The first field is the place, which we don't need to parse, but it does indicate a DQ
            lanes[i].is_dq = fields[0] == "Q"
            # The next num_splits fields are the splits
            lanes[i].splits = []
            for split in fields[1 : num_splits + 1]:
                if split == "":
                    time = None
                else:
                    time = Time(split)
                lanes[i].splits.append([time])  # type: ignore
            # The next 3 fields are the backups
            lanes[i].backups = []
            for backup in fields[num_splits + 1 : num_splits + 4]:
                if backup == "":
                    time = None
                else:
                    time = Time(backup)
                lanes[i].backups.append(time)  # type: ignore
            # The next 4 fields are the reaction times, which we don't parse
        return Heat(event=event, heat=heat, lanes=lanes, round=round)

    def encode(self, heat: Heat) -> str:  # noqa: D102
        # We're going to modify the heat object, so make a copy of it.
        heat = copy.deepcopy(heat)
        start_lane = 0 if heat.numbering == "0-9" else 1
        # The header is event, heat, num_splits, round, file_version, creator, creator_version
        event = heat.event or "1"
        heat_num = heat.heat or 1
        # Find the number of splits in the heat as the lane with the most splits.
        num_splits = max(
            len(heat.lane(i).splits or [1]) for i in range(start_lane, start_lane + 10)
        )
        round = heat.round or "F"
        round = "F" if round == "A" else round
        file_version = 100
        creator = "Wahoo! Results"
        creator_version = "1.0.0"
        header = f"{event};{heat_num};{num_splits};{round};{file_version};{creator};{creator_version}"
        lines = [header]

        for lane_num in range(start_lane, start_lane + 10):
            lane = heat.lane(lane_num)
            splits = lane.splits or []
            while len(splits) < num_splits:
                splits.append([None])
            # Ensure we only have 1 time for each split
            simple_splits = [combine_times(split) for split in splits]
            split_strings = [str(split or "") for split in simple_splits]
            # Ensure final_time is set so we can call place()
            if lane.final_time is None:
                lane.final_time = max(
                    [split for split in simple_splits if split is not None],
                    default=None,
                )
            place = str(heat.place(lane_num, ignore_dq=False) or "0")
            if lane.is_dq:
                place = "Q"
            line = f"{place};" + ";".join(split_strings)
            backup_times = lane.backups or []
            # Ensure we have 3 times
            while len(backup_times) < 3:  # noqa: PLR2004
                backup_times.append(None)
            backup_strings = [str(time or "") for time in backup_times]
            line += ";" + ";".join(backup_strings)
            # We don't track reaction times, so we just add blanks
            line += ";;;;"
            lines.append(line)
        # The file format supports 12 lanes, but we only use 10, so we need to add
        # 2 empty lanes to the end of the file.
        for _ in range(2):
            lines.append("0" + ";" * (num_splits + 7))
        return "\n".join(lines)

    def write(self, filename: str, heat: Heat) -> None:  # noqa: D102
        super().write(filename, heat)

    def filename(self, heat: Heat) -> str | None:  # noqa: D102
        round = heat.round or "F"
        round = "F" if round == "A" else round
        dataset = int(heat.meet_id or 1) % 1000
        event_num = (heat.event_num or 1) % 1000
        # Both None and "" will be converted to "-"
        event_letter = heat.event_alpha or "-"
        heat_num = (heat.heat or 1) % 100
        race_num = (heat.race or 1) % 10000
        return f"{dataset:03}-{event_num:03}{event_letter}{heat_num:02}{round}{race_num:04}.gen"

    @property
    def patterns(self) -> list[str]:  # noqa: D102
        # The spec says the extension is .ge2, but the files are actually .gen
        return ["*.gen", "ge2"]
